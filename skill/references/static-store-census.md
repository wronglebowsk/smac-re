# Static store census + table reads (terran.exe)

For "who writes field X" and "what does this table mean" questions. No tracer needed: everything below
runs on the file image plus read-only `/proc/<pid>/mem` preads (TracerPid 0).

## 1. Whole-image linear disassembly (the census tool)

```bash
cd ~/reverse/smac
objdump -d -M intel --section=.text programs/terran.exe > evidence/<id>_text_disasm.txt   # ~40 MB
```

- Printed addresses are **VAs** (`.text` file offset = VA − 0x400000, identity mapping).
- Grep it, never paste it. Extract the windows you cite into small files, then **delete the 40 MB dump**
  — it is regenerable and the size gate does not want it tracked.
- Map an address to its function by bisecting `ghidra_out/index.csv` (addr, name, size). Ghidra's
  `FUN_<addr>` names are verbatim addresses.

## 2. Reference census = one command, reported both ways

```bash
grep -n '98adb1' evidence/<id>_text_disasm.txt > evidence/<id>_refs.txt   # all references
grep -c 'BYTE PTR \[.*98adb1\],al' evidence/<id>_refs.txt                # the store count
```

Report "30 references / 1 store", not "the corpus shows one writer". A Ghidra store census is a
*rendering* census: it misses stores Ghidra cannot render as a `DAT_` write.

## 3. Store shapes to grep (offsets alone miss three of them)

| shape | Ghidra rendering | what to grep in the disasm |
|---|---|---|
| absolute store | `(&DAT_0098adb1)[i] = v` | `mov BYTE PTR [.*0x98adb1]` |
| indexed store | `*(x + 0x98ad88) = …` | `mov .*, \*4.*\+0x98ad` |
| **pointer-arithmetic store** | `*(char *)(p + -4)`, `*(char *)((int)p + -9)` | disp8 `mov … [reg+disp8]` where reg was loaded with a table/record base + constant |
| bulk copy | `memcpy`/loop | `rep movs` |

The pointer-arithmetic shape is what hides a section loader's tail fields: the loop cursor is a register
holding `record + 50` and the fields go to `[esi-0x8]`, `[esi-0x9]`, `[esi-0x4]`. Confirm the base from
the loop's stride (`add esi,0x34`) and the initial `mov esi, <base+50>`.

- **Operand width is a shape too.** A whole-width store sets or clears the bit you are hunting:
  `mov WORD PTR [esi+0x98adb8],0x105` writes the flags word and turns bit 2 on with no `or` anywhere.
  Census a field by grepping its ABSOLUTE base address with no operand-width filter, then classify each
  hit by width and by whether the immediate carries the bit. A `BYTE PTR`-filtered list reports two writers
  where the image holds eleven, and a "who sets this bit" answer built on it is incomplete before the run
  starts.

## 4. Jump tables: raw bytes, then bodies, before contradicting Ghidra

```python
img = open('programs/terran.exe', 'rb').read()
base = 0x595ab4 - 0x400000                      # table VA -> file offset
print([hex(struct.unpack_from('<I', img, base + 4*i)[0]) for i in range(10)])
```

- Entry count comes from the guard: `add eax,7` / `cmp eax,6` / `ja skip` ⇒ 7 entries, index = rule + 7.
- The dword after the last entry is code (`55 8b ec 8b` = a prologue) — that is the tell the table ended.
  Read the dwords; do not infer the count from the number of bodies you happened to find.
- Map every target to its body before deciding what an index means. Two indices may legitimately share a
  body; a body may exist that no index targets (dead code from a different compile).
- **A hand-decoded table that drops one entry yields a mapping that is shifted, self-consistent and
  wrong** — it looks exactly like "Ghidra's case labels are off by one". Only the raw dump (or live data)
  falsifies it, so dump before rewriting the model.

## 4b. Literal byte-pattern scan (is there a constant table?)

```python
img = open('programs/terran.exe', 'rb').read()
pat = b''.join(struct.pack('<I', v & 0xffffffff) for v in (0, -1, 7, 5, 4, -2))   # try rotations + windows
i = img.find(pat, 0x1000, 0x2703f4)                                              # .text only
```

- Pack negatives with `<I` / `<H` **after masking** (`v & 0xffffffff`, `v & 0xffff`): `struct.pack('<i', v)`
  raises `struct.error` on a sign-extended value and the scan dies at the first row.
- Scan the section range, not the whole file, and try every rotation plus a wider sliding window before
  concluding — a table can be stored in a different order or with interleaved fields.
- **A clean negative is the answer, not a failure to find it.** When a set of constants appears only as
  immediates at separate call sites, there is no contiguous table: say so and go read the call sites
  (grep the factory/dispatcher for the immediate) instead of widening the scan.

## 5. Rewriting a model that already matched live memory

- Keep the old model reachable: `--legacy` (or a variant int) reproducing the superseded semantics
  **including its quirks** (wrong field offset, skipped branch). The new model's mismatch list must be a
  subset of the old one's; a new mismatch means the rewrite broke something.
- Fit the unknown intermediate rather than guessing variants: per mismatch row compute everything except
  the one unknown internal value, then enumerate that value and read off which reproduces live.
- Delegate variant fitting to a subagent ("implement this pseudocode, diff against live memory, report
  match count and <=10 mismatch lines"). Five failed variants in the main thread cost the session.
- When delegating a read of a big pseudocode or disassembly dump, put every **known rendering artifact**
  in the child's context up front — pointer element-type scaling (`short *` halves the printed offsets),
  `DAT_` name splitting, loop cursors that start at `array + 4`, destructor-block noise. A child that
  inherits the artifact reports a self-consistent wrong answer; correct a running child with
  `delegate_task(action='steer')` rather than re-running it.

## 6. Is the row even a record?

Before treating a live mismatch as a model failure, histogram the discriminator fields over the whole
table (reactor/owner/flag bytes, plus chassis/weapon/armor indices vs the shipped `#CHASSIS`/`#WEAPONS`/
`#DEFENSES` row counts). Rows with out-of-range indices or impossible values are stale/unallocated
records — separate them in the check output so the mismatch count means only real failures.

## 7. Live read template (no tracer)

```python
pid = terminal("pgrep -x terran.exe")["output"].strip()
with open(f"/proc/{pid}/mem", "rb", 0) as f:
    f.seek(0x98aaf4); blob = f.read(28 * 24)
```

**Read with `f.seek(a); f.read(n)`** — the repo's reader helpers all do it that way; `os.pread` on the
same fd returns EIO on this host and reads like an unmapped page, which sends you hunting for a mapping
problem you do not have. One read settles any stride / table-field / multiplier claim that three static
inferences would only suggest. Cross-check tables against `data/alpha.json` (`scripts/parse_alpha.py`) — the alpha comment
headers name the columns of bare-data sections. **Read the neighbours too**: a candidate array's slots
that hold a value you already attribute elsewhere (year, `n_bases`, the faction mask) prove the array
starts somewhere else.

## 8. Pinning a table's real base and extent (when Ghidra splits it into `DAT_` names)

A table indexed with a constant offset folded into the displacement gets rendered under several names,
and the name that appears most often is not necessarily the base. Establish base and extent from the
code, in this order:

1. **Who takes the address.** `lea reg,[ds:0x985b3c]` / `local_8 = &DAT_00985b3c` in a walker is a base
   pointer; a name that only ever appears inside an indexed access is a folded displacement, not a base.
2. **The loop bound.** `while ((int)piVar < 0x985bc0)` with `piVar++` gives the END; extent = end − base
   in records. Check it against the domain (33 slots for the 33 projects 39..71 is a match; 72 is not).
3. **A branch on the pointer ADDRESS rather than the value** — `if ((int)piVar < 0x985b3c) { test the
   bitmap } else { compare *piVar to the current index }` — proves the flat range spans two different
   things, and the threshold dword is where one array really starts.
4. **The index math in machine code**: `neg ecx; cmp ecx,0x27; jl → -1; lea edx,[ecx-0x27]` says the
   stride-4 index is `idx − 0x27`, so the store `[edx*4+0x985b3c]` and the read
   `*(int *)(&DAT_00985aa0 + idx*4)` are the same slot. Confirm the guard (`test reg,reg; jl skip`) — it
   is what limits which keys have a slot at all.
5. **Live contents** (§7). Slots whose values are known globals, or that fall outside the field's legal
   range, are not entries; a real sub-array reads as a clean set (all −1 or all in range).

Then re-census the whole window `[base−slack, base+extent)` classified by operand shape — a writer that
only shows up under the folded name is still a writer. A store list built from one `DAT_` name is
incomplete; a store list built from the window plus the shape filter is the census.

## 9. From a static census to a live enumeration (proving you caught EVERY writer)

When the question is "is this the complete list of writers of field X, and in what order", the static
census is step one and the proof is a replay against live memory.

1. **Census the whole image, then filter by call-graph reachability — not by which callees you
   recognise.** Parse the `objdump` listing once: map every instruction to its owning function by
   bisecting `ghidra_out/index.csv`, collect `call 0x…` targets as edges, BFS to depth ~4 from the
   function that actually performs the operation. Find that DRIVER first by grepping the disasm for
   `call <best-known-callee>` and reading the caller's block — the caller is where the record address is
   computed and where the per-visit marker lives, and the callee set alone misses the sibling calls that
   also write the field. Report both numbers ("65 stores in the image / 23 reachable"). Reachability
   over-includes cheaply and never drops a callee you forgot; the breakpoint condition does the precise
   filtering.
2. **Audit the shapes the store regex cannot see before claiming completeness**: every
   `lea reg,[reg2+<disp>]` of that displacement (list them and prove no store runs through the resulting
   register — they are usually `[esp+…]` stack locals), `rep movs` bulk copies, and stores through a
   register that already holds `record + field`.
3. **Breakpoint AT the store instruction, conditioned on the address THAT INSTRUCTION'S OWN ENCODING computes.
   Read the machine code, not the pseudocode: `[reg*4+0x98adb8]` means the register holds
   `(index*stride)/4` — for the 52-byte type record, `tid*13` — while `[reg+0x98adb8]` means it holds the
   record BYTE address, `tid*52`. A condition that compares such a register to the bare index can never
   match, and the run then reports "no writer fired" while the census shows the field flipped. Build the
   condition and the printed tid from the SAME arithmetic (`$reg == tid*13` paired with `$reg / 13`;
   `$reg == 0x98adb8 + tid*52` paired with `($reg - 0x98adb8) / 52`), and print the field's current byte in
   the hit line so before-and-after arrive in one row.** The condition is literally "the target address is record+field", so it cannot mis-attribute
   the same offset in another struct, and it fires only when the store executes, so guarded writes are
   counted as executed-or-not rather than guessed. Instrument the whole reachable list — a breakpoint
   whose condition never matches costs nothing measurable, and the completeness claim needs the breadth.
4. **Take the after value from the store's own source operand**, not by stepping (`si` in a commands list
   ends `gdb -batch`: `references/wine-operations.md`). For `mov [reg+disp],src` the source operand IS
   the value the field takes; print it and let the sampler prove it.
5. **Acceptance is a replay, not a timestamp alignment.** Start from the field value read before
   attaching, walk the recorded stores in order and require:
   - each store's `before` equals the replayed current value — a mismatch is a write at a site you did
     not instrument;
   - the sampler's distinct-value sequence is a **subsequence** of the replayed sequence (a sampler that
     misses the interval between two writes legitimately skips intermediate values, so subsequence is the
     right test and equality is too strict);
   - at each anchor (every boundary, and the last good sample) `start + sum(deltas of stores whose wall
     time <= anchor)` equals the value observed at the anchor. Equal anchors two rows in a row make the
     per-boundary sums follow, so cut windows on the sampler's own timestamps and never on a post-detach
     read-back (the game keeps playing after the last event you recorded).
6. **Make the log parseable by construction.** Label tokens inside a hit line must contain no spaces —
   `site=visit.pay(sub edi)` silently defeats a `site=(\S+)` regex, and a hit line your parser dropped
   looks exactly like an unattributed write at the next store. Before trusting any accounting, grep the
   raw log for the hit-counter sequence and require it gap-free.
7. **Re-verify the subject's identity every sample.** Record arrays reorder/compact mid-run, which turns
   a baked address into a different object without any write happening; read the name (or another
   identity field) at the address each sample and end the watch at the change instead of splicing two
   objects into one trace.
8. **When a store census reports zero hits, or does not account for an observed jump, the instrument is
   the suspect, not the game**: check in order — the condition's address arithmetic (point 3: a scaled
   register compared to a bare index never fires; a whole-width store filtered out of the census never got
   a breakpoint), a dropped log line (point 6), the subject having moved (point 7), the anchor taken after the
   watch ended (point 5) — and only then report an uninstrumented writer.
