# Session notes archive — sessions 53-53

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 53 (2026-10-23) — M53a: the base+0x50 queue record end to end — it is a 10-slot ITEM ARRAY (+0x4c = last index, +0x44 = mirror), unit/facility completion is PAYMENT-DRIVEN with NO progress counter, negative values are secret projects −(39+idx) registered in the 33-dword table 0x985b3c

**Run:** `scripts/m51a_drive.py --tag m53a --rounds 3 --budget 1100` — 3 rounds 2363→2366, **0 OCR
passes**, clean detach (`evidence/m53a_watch.log:1134`); two new NAME-conditioned sites in GDB_TMPL
(`QPIPE` @ 0x4ef6d0, `QCOMPLET` @ 0x4efe41; identity = dwords "Clim"@+0x13 + "acti"@+0x17 through
`*(int*)0x8f0d60`, slide-proof). Static: `evidence/m53a_queue_disasm.txt` (0x4ef9b3+340i),
`evidence/m53a_qgate_disasm.txt` (0x4ef880+80i), `evidence/m53a_fn_disasm.txt` (whole FUN_004ef6d0,
2600i), `evidence/m53a_fn4ef6d0_pseudocode.txt`.

**1. The queue is an ARRAY, not a dword** (VERIFIED static + live). 10 item slots at
`base+0x50 .. +0x73`; **+0x4c = last used index** (UI caps it at 9 → 10 entries: `case 3: <9 → +1`
and `= 9`, `ghidra_out/shard_001.c:9432-9437`; the FUN_004f4060 drain iterates `[+0x4c]+1` dwords
from +0x50 and decrements the per-player item counts at `0x94de84 + owner·0x20bc + id` —
`shard_012.c:23044-23060`). Live: **f4c=0 = one entry**, f68=0 = slot 6 never written
(`m53a_watch.log:392`). The pipeline only ever processes slot 0 (+0x50); grep of the whole-function
disassembly finds **no +0x50 writer** — reads only (`fn_disasm.txt:67,118,200,223,1316`).
**+0x44 = active-item mirror**: `FUN_004f5a70` copies `+0x50 → +0x44` on every visit
(`shard_012.c:24185`, short*-alias `+0x22 := +0x28`), and the ownership-transfer block clears BOTH
to −38 (`shard_012.c:23065-23068`). Live: f44 == f50 == 2 at every QPIPE
(`m53a_watch.log:392,769,1115`). Also `[base+0x98] := storage` snapshot at the same sites
(`shard_012.c:24184`; in-pipeline `pseudocode:302,823`).

**2. Encoding** (VERIFIED static, `m53a_qgate_disasm.txt:5-55` = 0x4ef88b-0x4ef938): `−38
(0xffffffda)` = empty → NOQUEUE; `≥ 0` = item id (unit `< 0x40`, facility `≥ 0x40`); `< 0` = `|q|`
with scratch `[ebp-0x1c] = |q|−39` if `|q| ≥ 39` else −1 (`:12-17`), `[ebp-0x20] = [|q| ≥ 34]`
(`:18-23`); negative cost = `0x4e40a0(owner,1,−1) × dword[0x984d44 + 48·|q|]` (M46 upkeep table)
(`:30-35`). M52b's "`[ebp-0x1c] = |q|−39`" is the NEGATIVE branch only; on the positive path
0x4efae5 overwrites it with `52·id` (`m53a_queue_disasm.txt:61-64`) — live m1c=104 = 52·2 ✓
(`m53a_watch.log:397`). `[ebp-0x2c] = 1<<owner` set unconditionally at 0x4ef815
(`fn_disasm.txt:81`) — live m2c=8 = 1<<3 ✓.

**3. Negative values are SECRET PROJECTS** (registry VERIFIED static; project identity INFERRED).
`0x4f0d83: 0x985b3c[|q|−39] := base index` (`fn_disasm.txt:1480`); the table is **33 dwords**
(`FUN_005305f0(&DAT_00985b3c, 0x84, …)` — `shard_013.c:15670`) = 33 secret projects;
`FUN_0051f730` (per-player refresh) reads `registry[project]` → owner(base[registry])
(`shard_013.c:11119-11120`); 0x4f0819-0x4f0837 formats the builder's base NAME from the registry
(`fn_disasm.txt:1146`). So `|q| = 39 + project_idx`; the "another base already queues this" check
compares `other+0x50 == our+0x50` (`fn_disasm.txt:1315-1316`, esi = base+4).

**4. No build-progress counter for units/facilities — completion IS payment** (VERIFIED live).
QCOMPLET fired exactly once in 3 rounds — only the round with storage 200 ≥ cost 10
(`m53a_watch.log:397`); rounds 2-3 st=0 → 0 hits (`:769,1115`). Gate: `cmp [ecx+0x40],edi; jge`
0x4efa5e-61 (`queue_disasm.txt:39-40`). PROGDIV 0x4efd49 is NOT an accumulator: it is the ETA
string `(factor×(pop+1) − [base+0x3c]) / [base+0xcc]` clamped 0..10007, gated `[base+0xcc] > 0` —
ours is −3, hence "PROGDIV never fires in solo" (`queue_disasm.txt:193-207`). Consequence,
PREDICTED: a payable head re-completes every round (matches M45's units 1→6 from one standing
queue). The only per-base progress accumulator remains +0x3c/+0xcc (pop-growth, M52a; and per
`fn_disasm.txt:1334-1343` the project path compares `other[+0xcc]+other[+0x3c]` vs the project
cost — projects also accrue in +0x3c).

**5. COMPLET 0x4efe41 dispatch** (VERIFIED static, `queue_disasm.txt:250-291`): `ebx < 0x40` unit →
`[ebp-0x20] := 0` → SPENDA (`:288-291`); `ebx ≥ 0x40` facility → set bit 2 of word
`[0x98adb8 + 52·id]` (built flag) and if newly set → repoint `0x8f0d60` + the rebuild chain
0x4e8d60/0x4e78e0/0x4e92c0/0x4e93f0/0x4eaa10 (`:252-287`). Third trigger: class-8 Colony Pod ∧
pop==1 ∧ `0x94d438[p] > 1` → ABANDONBASE confirm via `0x48ee00(SCRIPT,…)`, answer ≥ 2 → COMPLET
(`queue_disasm.txt:215-226`, `pseudocode:204-245`). Downstream of CLAMP: `[+0x98]:=[+0x40]`
(`pseudocode:302`) → spawn helper `0x5ab650` returns the new unit index, unit flags set in
`0x93327c + idx·52` (`pseudocode:307-320`; INFERRED unit creation — bp not armed) → PRODUCE /
PRODUCEPROTO announcement pane with per-domain unit icon (`pseudocode:440-530`).

**6. IADD gate CLOSED** (VERIFIED): `storage += d0` iff `d0 ≥ 0 ∧ queue ≠ −38 ∧ (f30 & 2) == 0`
(`fn_disasm.txt:65-69` + `pseudocode:110-113`) — explains M48d's "2 hits in 3 rounds": the gate is
queue non-emptiness, not randomness. Live both hits d0=0 no-ops (`m53a_watch.log:393,1116`).

**7. cc recomputes PER-VISIT, not per-round**: the +0xcc=1 poke was already −3 at the first
pipeline print (`m53a_watch.log:392`) — 0x4f5a70 runs the recompute chain before calling the
pipeline. d0 likewise (poke 200 → live 0/−1/0, `:392,769,1115`).

**8. Opens.** (a) **Dequeue/shift after a POSITIVE completion is not done by the pipeline** — tail
clear is negative-only (`pseudocode:1476-1478`: `queue == −|q| ∧ [base+0x4c]==0 → +0x50 := −38`);
full-clear writers that zero BOTH +0x44 and +0x50: `FUN_00507ef0` (`shard_012.c:34739-34740`) and
`FUN_005437d0` (`shard_013.c:30426-30427`), plus enqueue-side `FUN_00417ee0`
(`shard_001.c:9452`, writes the raw command incl. `< −38` project ids → `0x446250`). Live: f50
stayed 2 all run. (b) `base+0xc0` printed a constant 7 == our pop every round — semantics unresolved.
(c) Negative-value semantics beyond the registry (34/38 band) unprobed — 0 NEGPATH hits again.

Next: **M53b** (unchanged queue: +41 production weight vs +43 autocalculated cost across all
`#UNITS` rows), or **M53c** (the dequeue writer: arm 0x507ef0/0x5437d0/0x417ee0 and complete a
payable round with a 2-item queue). Footing rewritten in NEXT_PROMPT.md (session 54).
