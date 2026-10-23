# Session notes archive — sessions 47-47

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 47 (2026-10-22) — M49a: THE GROWTH-COST QUESTION DISSOLVES — edi at COMPLET is the base's SWEEP-ENTRY INDEX, not a cost; esi=8 is the event-mask bit-test result; M48d's "Scout Patrol cost 10" RETRACTED

`scripts/m49a_drive.py` (copy of m48d_drive.py: COMPLET print extended with pop/fc/cap/d0/cc/3c/
e0/f0/c0 + stack scratch [ebp−0x1c..−0x2c]; new bp `ST1C` 0x4efae5 with its own `$ns` counter;
self-pkill fix — see pitfalls). Runs: `evidence/m49a_{watch.gdb,watch.log,run.log}` (1 round,
2347→2348, 0 OCR), `evidence/m49c_*` (1 round, 2348→2349, 43 OCR passes — COMM-pane chain, below).
Static: clean 32-bit disasm via `gdb -batch -ex "file programs/terran.exe" -ex "x/Ni ADDR"` (the
PE loads as a mapped target; NO attach, TracerPid stays 0).

**VERIFIED (disasm chain + 3 live runs): the SPENDA subtract operand `edi` is the base record's
SWEEP-ENTRY INDEX, not any cost formula.**
- `0x520540` per-base loop passes the base INDEX as a STACK arg: `push ebx; call 0x4f5a70`
  (0x5206d2-6d3; ebx = index, dec ebx + sub edi,0x130 on compaction slides 0x5206df-e0).
- `0x4f5a70(arg0=index)`: `mov ebx,[ebp+0x8]` → `mov edi,edx` at 0x4f5aa9 (edx = owner byte
  0x4f5a9c) — edi := index just before `call 0x4ef6d0` (0x4f5adc). Ghidra's
  `FUN_004f5a70(iVar1)` confirms arg-in-stack.
- Pipeline `0x4ef6d0`: the pop-growth path (QGATE 0x4ef88b → 0x4efadc store [ebp−0x1c] →
  class≠8 `jne 0x4efe41` / pop≤1 `jne` / `0x4efb0f` event test → ... → `cmp eax,2;
  jge 0x4efe41` 0x4efdb4) contains **NO edi write** (only 0x4ef8e2/0x4efa4b on the negative-queue
  branch). So COMPLET sees edi = the index.
- SPENDA 0x4efed8: `esi = storage − edi; storage := esi` ⇒ **storage −= entry-index** at every
  completion. Live: ours 200→190 three times (m48d2/m49a/m49c; edi=10 = our index-at-entry; the
  CURRENT idx drifts 71→69→60 as the array slides — the invariant is edi == index-at-sweep-entry).
- AI lines fit the same model: edi == their index-at-visit-entry (e.g. 44 recurs across years
  while current idx drifts 25→29→54/60).
- **esi at COMPLET entry is path residue, not a budget**: on the pop-growth path esi = result of
  `0x48ee00` (message/pane formatter, scratch 0x997120) preceded by `0x4e40a0(owner,1,−1)` =
  `(1<<owner)&mask` = **8 for us** — the very value the CLAMP1 gate uses (m2c=0x8 = same bit).
  Facility-path COMPLET lines carry pointer-looking esi (type-record scratch `ebx*60+0x98ad88`)
  because the callee chain 0x4e8d60→…→0x4eaa10 (runs only when ebx≥0x40) clobbers edi/esi.
- **pop at COMPLET is ALWAYS the pre-completion value** (growth lands after; attrition re-drops):
  m49c located pop=5 pre-poke, OURBASE showed pop 4 at 2349 (NOSUPPORT disband), COMPLET printed
  pop=4. ⇒ pop can never disambiguate a formula; the M49a test design was void, and all three
  candidates (2×pop, cap−fc, (d0+fc)×4) were coincidences on pop=4/fc=2/cap=10/d0∈{0,−1}.

**Corrected mineral model (supersedes M48d's cost story)**: per round `storage += d0` unclamped;
at every completion `storage −= entry_index` (0x4efee0), then event-owner clamp
`storage := max(0, min(d0, cap))` (0x4eff20/23). Pop-growth units are effectively FREE (the "cost"
is the index quirk); the 26-year backlog is explained by storage clamped to 0 ⇒ the index-subtract
always takes the shortfall branch (4efee4) — not by unaffordable unit costs. Whether real per-unit
mineral costs exist anywhere in the pipeline is OPEN (M48d's PROGDIV/QDRAIN never fire in solo;
`0x4f26e0` runs right after 0x4ef6d0 in 0x4f5a70 and is the next candidate).

**NOSUPPORT disband live again**: pop 5→4 across 2348 (m49c OURBASE line 178), d0=−1 at the visit
— disband fires while d0<0 (M48d rule holds).

**Pitfalls found (this session):**
- `pkill -INT -f "[m]49a_drive"` matches the DRIVER'S OWN cmdline → the driver SIGINTs itself at
  startup (KeyboardInterrupt inside subprocess.run). The bracket trick only protects pkill's own
  shell, not a python driver whose argv contains the tag. m49a_drive.py now kills stale copies via
  pgrep + os.kill skipping os.getpid().
- COMM OFFICER pane has a 3-row variant ("Yes, switch to main viewscreen." / "No, close the
  channel." / "Display faction leader profile."). The colour row-click (bar_y−25) can land the
  selection on "Display faction leader profile" → UNIVERSITY INTELLIGENCE FILES table whose
  CLOSE/DATALINKS bars sit at y≈345-360 — outside find_ok_bar (430-520) and hit by the
  rightmost_blue_run row-click+bar cycle; chain took ~8 min / 43 OCR passes to drain (DATALINKS →
  diplomacy pane OK bar ≈y 345 → back). Driver did self-recover; faster fix = click the specific
  row by OCR y, or click bar_y−25 twice before the bar.
- objdump CAN disassemble this PE after all: `-b binary -m i386:x86-64 -D --adjust-vma=0x400000
  --start-address/--stop-address` (file offset = VA − 0x400000 identity) — but 64-bit decoding
  MISALIGINS on SEH blocks (the COMPLET region decoded as garbage/movabs). Clean 32-bit recipe:
  `gdb -batch -nx -ex "set architecture i386" -ex "set disassembly-flavor intel" -ex "file
  programs/terran.exe" -ex "x/Ni 0xADDR"` — gdb maps the PE image; read-only, no attach.

Next (M49/M50 options): real unit/facility mineral cost — instrument 0x4f26e0 (runs after the
pipeline in 0x4f5a70) + watch storage across a facility completion on a high-index base; pipeline
early-stop mechanism (sweep caller ordering + year-store interrupt); production-rate cc source
(0x4eaa10 / 0x4e92c0 candidates — note 0x4eaa10 loops 7× over faction stride 0x20bc writing
faction+0xc4 = research pool); the 2320 +4 credit; faction NAME mapping; ledger writers on a
spending round.
