# Static store census + table reads (terran.exe)

For "who writes field X" and "what does this table mean" questions. No tracer needed: everything below
runs on the file image plus read-only `/proc/<pid>/mem` preads (TracerPid 0).

## 1. Whole-image linear disassembly (the census tool)

```bash
cd ~/reverse/smac
objdump -d -M intel --section=.text programs/terran.exe > evidence/<id>_text_disasm.txt   # ~40 MB
```

- Printed addresses are **VAs** (`.text` file offset = VA − 0x400000, identity mapping), printed
  WITHOUT the common leading zeros (`4eec30:`, not `004eec30:`).
- **Parsing the dump in Python:** many saved copies carry the opcode/mnemonic separator as the two
  literal characters `\t`, not a tab. Normalize first (`line.replace("\\t", "  ")`) and anchor instruction
  lines with `^\s+([0-9a-f]{6,8}):` — a window printer whose regex demands a real tab after the colon
  returns an EMPTY function body and looks like "this address is not a function start".
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
- **Grep the disassembly case-sensitively.** objdump prints `BYTE PTR` / `WORD PTR` / `DWORD PTR` in
  UPPERCASE, so a lowercase `ptr [` pattern reports **zero** stores for a field that has 101 and the
  empty result reads like proof of no writer. Before trusting any census regex, run it once against a
  line you already know exists and require a match.

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
- **Enumerate BOTH print forms before calling a writer set complete.** A store that reaches the field
  through a record POINTER (`mov WORD PTR [eax+0x30],dx` with `add eax,0x34` in the loop) never prints
  the table's absolute address, so a grep for `0x98adb8` misses it while a grep for the displacement
  `+0x30]` finds it. Run both greps, then filter the displacement hits down to real stores: exclude
  `cmp`/`test`/`lea`, and remember most `+0x30]` hits in a function prologue region are stack locals at
  `-0x30`.

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
   the hit line so before-and-after arrive in one row.** Where the site's register holds the **bare index**
   (a visit-time check, e.g. the queue head at the affordability gate), reach the field by multiplying by
   the stride — `$ebx * 0x34 + 0x98adb8`; a `*4` there reads a neighbouring record and prints 0, which is
   misread as "the flag is clear". The condition is literally "the target address is record+field", so it cannot mis-attribute
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
   watch ended (point 5) — and only then report an uninstrumented writer. Arm at least one **control
   breakpoint whose hit is guaranteed** in the window (the visit gate conditioned on the armed base) and
   require its rows in the log: zero writer rows together with zero control rows is an instrument verdict,
   never a finding about the game.
9. **Prove the event you are watching for was possible BEFORE attaching.** For a WHEN question, read the
   precondition back from memory first: the armed id is the queue head, `pending >= 1`, and storage exceeds
   the largest value the gate can demand. Re-read the same fields after the run. A window whose read-backs
   show the event never happened (`pending 0 -> 0`, head unchanged, storage unchanged) answers nothing —
   report an unusable window and re-arm (enqueue, then read `pending` back), never "no writer fired during a
   completion". Read a stale queue tail as nothing queued: `pending` is the only proof an id is in the queue.
10. **A gdb command-list printf takes expressions as ARGUMENTS, never inside the format string.**
    `idx=($ebx/52)` typed into the string prints ITSELF, so a log parser looking for `idx=<digits>`
    drops every row and reports zero events on a window that has them. `%.20s` on an inferior pointer
    makes gdb error, abort the batch script and DETACH mid-window. In a two-branch `re` alternation
    `group(1)` is the WHOLE match — branch on a group from inside the taken branch, or a good log
    crashes the parser. Never judge watchpoint arming from one early read of the gdb log: poll for the
    ARMED line (a 3 s single read failed a run that had armed all four watchpoints).
11. **For a WHO-CALLS / WHEN claim, read the return address off the stack and assert the chain from the
    log, not from pseudocode adjacency.** Breakpoint the callee's FIRST instruction and print
    `*(int *)$esp` — the return address names the caller with no backtrace (arguments are
    `*(int *)($esp + 4)`, `+ 8`, … because the bp sits before `push ebp; mov ebp,esp`). One hit matching
    the predicted site proves A caller; require **every** entry row to carry that same return address
    before writing "the only caller" — the pair that proves exclusivity is a single `call 0x…` in the
    whole-image grep AND an all-rows match, and a gate that passes on zero rows proves nothing. Then gate
    the trigger too: require each entry row to be immediately preceded, in log (program) order, by the row
    the static reading says gates it — e.g. the branch whose compared register holds the value a named
    callee returned, printed at the instruction right after that call. Locate that producer from the
    disassembly, not from pseudocode line order (`references/code-atlas.md`), and let the scorer print the
    distinct values the callee actually returned: a run where the sentinel never appeared is an unusable
    window, not a negative answer about the caller.

## 10. "Why does this site never fire": its gates, its common exit, who sets the gate global

Answer reachability STATICALLY before arming anything: a site behind a mode gate logs zero hits in the
other mode, and the run then reads like an instrument failure when it is already the answer.

1. **List the jumps that skip the site.** Disassemble the block AHEAD of it (`scratch/<id>/dis.py
   <block_start> <site>`) and collect every `je`/`jne`/`jg`/`ja`/`jmp` whose target lands past the site.
   Each is a gate: name the tested global or register. A site whose gates test a GLOBAL is a MODE question,
   not a WHEN question — no window choice makes it fire.
2. **Find the block's COMMON EXIT.** Several gates usually jump to the SAME instruction. A breakpoint at or
   after that shared landing point fires on the ordinary path too, so a hit there proves the BLOCK ran, not
   that the gated branch ran. Zero hits at the gated site together with hits at its common-exit neighbour is
   fully explained by the gates — report the pairing, because it is what separates "dead path" from "the
   breakpoint never armed".
3. **Who writes a bare global: comma = store.** objdump's Intel output prints the DESTINATION first, so a
   comma immediately after the address means the global is being written:
   `grep -n 'ds:0x920434,' evidence/<id>_text_disasm.txt` → every `mov DWORD PTR ds:…,reg`.
   Run a SECOND grep for the source-less read-modify-write forms, which carry no comma:
   `grep -nE '(inc|dec|add|sub|and|or|xor|shl) +(DWORD|BYTE) PTR ds:0x920434'`.
   Loads (`mov reg,DWORD PTR ds:…`) and tests (`cmp DWORD PTR ds:…,0x0`) match neither, so "all N references
   are reads" is only true after BOTH greps come back empty.
4. **Pair each pseudocode write with its owning function, then name the mode from that function's strings:**
   ```bash
   grep -rn -B80 'DAT_00920434 = ' ghidra_out/*.c | grep -E '// ==== FUN_|DAT_00920434 = '
   sed -n '<fn_start>,<fn_end>p' ghidra_out/shard_NNN.c | grep -oE 's_[A-Za-z0-9_]+_[0-9a-f]+' | sort -u
   ```
   The export prints a `// ==== FUN_<name> @ 0x<addr> size=` banner per function, so `-B80` piped through a
   banner grep attributes every assignment to a function in ONE call. The UPPER_CASE string tokens a function
   references name the screen it belongs to (`INTRO`/`SCENARIO`/`TOPMENU`/`MULTIMENU`/`*_pcx` = the opening
   movie and its menus), which is how a mode gets identified without a live probe.
5. **Report the mode, not the miss.** If the flag is written 1 by exactly one function and 0 by every other
   writer, and the live value is 0, the gated path is dead in the current mode: name the owning mode, keep
   the acceptance FAIL with its numbers, and make the next milestone ONE variable (poke the gate global, or
   enter the mode that sets it) rather than another window on the same state. A path with no live instance
   (`references/code-atlas.md` vptr scan) and a path behind a mode flag are the same finding shape.

## 11. Capture/publish brackets, byte-field captures, and the x8380 fold (s176, M191-M193)

- **A field CAPTURE can be `movsx reg, BYTE PTR [..+disp]`.** A load census filtered on `mov` drops the
  byte fields, so a capture/publish pair looks asymmetric (16 loads / 8 displacements against 18 stores
  / 9) and the extra published field reads like an unexplained write. Count `movzx`/`movsx` with the
  loads before comparing the two runs.
- **A whole-width store into a flag dword is not automatically a producer.** When the stored value comes
  from a stack slot with exactly ONE writer - fed by that same field's own load a few instructions after
  the frame was set up - and exactly ONE reader, which is the instruction right before the store, the
  site is the PUBLISH half of a snapshot bracket and the write is value-preserving: the field keeps the
  value it had on entry. Check the slot's writer/reader count before naming which function sets a bit.
- **The faction-block base has a canonical shape**: `mov r,S; shl r,6; add r,S; lea r,[S+r*2]; shl r,4;
  sub r,S; add r,C; shl r,2` = `8380*S + 4*C` (2095 dwords folded to bytes, plus a 4*C dword sub-index).
  Match it by mnemonic-and-immediate shape plus the seed register, then prove two sites address the SAME
  block by following S and C: on the publish side they are usually reloaded from spill slots - verify
  each such slot has exactly one writer (the capture-time register) and that nothing writes those
  registers between the spill and the use.
- **A "publish primitive" can have >1000 call sites.** Before calling a 0x626xxx routine a save emitter,
  count its call sites: `0x6267a5` (tagged writer, 18 sites / 17 functions) vs `0x626634` (1584 / 190) -
  the fan-out separates a serializer from a general publish. A publish takes a slot index plus optional
  values, where a sentinel (-1) means "use the shared staging globals", so the staging record can be one
  slot of a table whose other slots are indexed (`0x99a01c + 10*256 == 0x99aa1c`).

  ## 12. Pointer-or-flags, consumer census, and the 6-digit global (s177, M194-M196)

  - **A scaled-index displacement is not an array census.** `mov reg,[ix*4+0x94d448]` and `mov reg,[bx+0x94d448]`
  are the SAME family when `ix` is a folded block index: attribute the index register's definition chain (walk
  back in the function to the last write of that register; if it is `add reg,<sub-index>` preceded by a >=3-op
  fold chain on the same register, the address is `base + stride*S + 4*C`, a record field, not element `fac`).
  In SMAC 365 of 466 `0x94d448` scaled sites are block fields; a "per-faction pointer array" reading that
  ignores the fold is wrong before the first gate runs.
  - **Classify a bit-field test by MNEMONIC + popcount, never by operand magnitude.** All 297 tests of that field
  are `test <dword>,mask` with ZERO `cmp` and the widest mask carries 5 bits - not one compares the dword
  against a value, let alone a pointer. A size filter (`imm >= 0x400000`) flags `0x800000`, `0x1000000`,
  `0x2000000` as "address-sized" when each is a single bit. Pair the census with a tracerless `/proc/<pid>/mem`
  read of BOTH readings (`+4*i` and `+stride*f`): if no value lies in the mapped user range, it holds flags.
  - **`lea reg,[mem]` right before `mov [reg],val` is Ghidra's store-through alias, not a tagged pointer.** The
  clamp idiom `mov edx,[ix*4+abs]; lea eax,[ix*4+abs]; cmp edx,ecx; ...; mov [eax],ecx` writes the very dword
  the lea computed; reading such a pair as "it stores addresses" cost a retraction (M190 -> M196).
  - **A table whose slots are PASSED is consumed elsewhere.** Counting `push 0x99a01c` as a "read" made M191
  report "26 reader functions"; 93 of the 113 sites in the window push the base or a slot address into a
  callee, so the consumers are the 16 callees (mostly the C string layer: two short thunks, `_strlen`,
  `_strcmp`, `_strncpy`, the 0x7efefeff append-copy) plus the two formatters that index the table themselves.
  Attribute each push to the following `call`, classify the callee, and read the live slot contents - they name
  the channel ('disciplined'/'Provost'/'Zakharov'/'University'/'Mission Year 2150' = one faction's sentence
  parts). A slot with publishers but zero address-pushes is write-only.
  - **Data globals print as SIX hex digits** (`ds:0x920700`, `0x99aa1c`). A census regex written as
  `0x9[0-9a-f]{6}` matches none of them and prints an empty store set that reads like "this function writes no
  globals". Match `0x[0-9a-f]{6}` and filter by value range.

## 12. Naming a function from its own strings, and walking a string pool (s178, M197-M200)

- **"This function contains no string literals" is a FALSE result if you grepped for a quote char.** Ghidra renders
  a referenced literal as a named symbol (`s_PROPOSALMENU_00690a84`, `LAB_…`, `PTR_…`) that contains no `"`. Census a
  body with `\bs_[A-Za-z0-9]+_(00[0-9a-f]{6})\b` and READ the bytes at each address (file offset = VA − 0x400000 over
  .text/.rdata/.data): the tokens often name the function better than its disassembly does.
- **A .data string pool is 4-aligned, NUL-terminated, NUL-padded to the next multiple of 4, and the pool is
  terminated by 0xFFFFFFFF.** Walk forward with `next = va + len + 1 + pad`; walk backward by "the LONGEST 4-aligned
  padded string whose bytes END exactly at va" (fragments of it start later, so the earliest match is the real
  entry). A fixed-stride walk is wrong — entries are variable-length, and a 16-byte slot assumption truncates or
  misaligns the run.
- **Keys and sentences share the pool.** Classify every entry (one word = a lookup KEY, contains a space = a message
  line) instead of stopping at the first multi-word entry, or your "table extent" is really "the first sentence".
- **Receiving a text pointer does not make a function a formatter.** Prove substitution from what it calls: 0 `0x25`
  immediates, 0 printf-family calls and 0 calls to the function that indexes the text table means it copies
  VERBATIM. Census the vmethod offsets used through a global handle (`(**(code **)(*DAT_handle + 0xNN))` renders in
  the C) to tell whether two functions are the same kind of object.
- **`local_20 = <code address>; call X();` is usually the SEH resume cookie, not an argument.** When Ghidra assigns
  both small integers and in-function addresses to the same pseudo-local, it is modelling the exception-state chain:
  do not read the calling convention from those lines.

## 13. Vtable model + "who dispatches slot +0xNN" (s182, M209-M212)

- **Build the vtable map from the image, not from Ghidra** (index.csv is functions only): a base is the imm32 of
  `mov dword ptr [reg+disp],imm32` in the data range whose own first dword is a code address; extent = consecutive
  code-pointer dwords, **capped at the next candidate base** (188 bases in terran.exe). Walking code pointers in
  both directions without the cap merges neighbouring vtables into one 645-slot run and every offset you then
  report is wrong.
- **"Who dispatches slot +0xa8" is TWO questions.** (a) which vtables IMPLEMENT it — one slot had 33 distinct
  implementations over 188 vtables, so naming a dispatcher means naming the class; (b) for each `call [reg+0xNN]`
  site, what class the register holds. Resolve a site by the containing function's vtable membership: scan the
  image for the dword == &fn and map each hit to (base, byte offset). A function in no vtable with 0 direct
  `call` sites is dead-or-table-reached; a function IN a vtable is a vmethod, so its `call [*this + 0xNN]` is a
  SELF-dispatch of its own class's implementation of that slot — which is how the pick's "6-site candidate"
  FUN_0043a4e0 turned out to dispatch a different class's +0xa8 (0x673498 -> FUN_004394e0).
- **Three dispatch shapes to name explicitly:** an ADJUSTOR THUNK (tiny fn, `sub ecx,<delta>` or
  `mov eax,[reg-delta]` for the outer vtable — resolve the outer class from the ctor that installs the subobject
  vtable at `[reg+delta]`); a COMPOSITE (FUN_004bb900 = +0xa8 of 8 vtables, forwards to `[this+0x3c]`, returns
  the constant 0x14 when the child is null — a callee of the slot, not a caller of it); a GLOBAL-HANDLE forwarder
  (`if (ds:0x9977f0) (*(*ds:0x9977f0 + 0xa8))(arg1)` — census that global's writers: 2 stores, both inside the
  pump, means the pump publishes the live modal object).
- **A `push`-argument census starts one instruction BEFORE the call site** — walking back from the site itself
  hits the `call` first and every argument reads as unknown. And `cmp eax,esi` is not a constant compare: split
  cmp-imm from cmp-reg before claiming "N sites compare against a constant".
- **An `INSTALLS` displacement string from `mov dword ptr [esi+0xa14],imm` has no closing `]`** — test
  `endswith("+0xa14")`; demanding `"+0xa14]"` fails a gate whose data is right.
