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

One pread settles any stride / table-field / multiplier claim that three static inferences would only
suggest. Cross-check tables against `data/alpha.json` (`scripts/parse_alpha.py`) — the alpha comment
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
