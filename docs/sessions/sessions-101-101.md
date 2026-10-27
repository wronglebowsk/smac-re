# Session notes archive — sessions 101-101

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 101 (2026-10-26) — M62: **INSTRUMENTS, NOT RESEARCH. The box's dead shapes are now decided in one read, the brief is generated, and the evidence audit found that no trace could ever count as cited. NO prediction PASS this session — the one live run FAILED and the reason is now half-explained.**

**THE READINESS ORACLE (`scripts/accept_ready.py`, 15/15 unit cases).** Read-only; exit 0 = one of
our bases can carry the UI-queued acceptance, exit 1 = BLOCKED with the single cheapest fix, in
this order: screen class (a modal swallows every click AND every turn-end key) -> running gdb ->
evidence headroom (29 MB) -> per base `pending > 0`, `minerals < price`, `credit > 0` (the income
add is gated `d0 > 0`, so `credit <= 0` never accrues) -> TIGHT horizon when the gate is more than
`boundaries-2` rounds away. Proven on the live box in three states, one command each:
`BLOCKED … FIX: screen is 'dialog': press Return …` (an Operations Director "…not sufficient to
support Scout Patrol…" modal was up and had just swallowed two enqueues) -> `BLOCKED … FIX: enqueue
on University Base (idx 0)` -> after `m57_ui_enqueue.py --base-index 0 --cell-item 2 --inserts 1`
(`after INSERT 1 (try 1): pending=1 head=2 minerals=1 d0=1`) -> **`READY … RUN: scripts/m56_build.py
--ui-queued 0 --boundaries 10 …`, exit 0**. Rule cases: `python3 scripts/test_accept_ready.py` ->
**`PASS 15/15 readiness cases`**.

**THE LIVE RUN FAILED — recorded, not hidden.** `python3 scripts/m56_build.py --ui-queued 0
--boundaries 10 --timeout 400 --no-poke-hold` -> **FAIL**, `positive predictions 1/2 verified;
boundaries 10/10`, exit 1 (`evidence/trace_m56_build_20261026_165917.jsonl`). Three rows carry it:
r2 "predicted … observed net 0 of that tuple on the base tile"; r3 `pending 1 -> 0` with the slot
array `[2,2,0,0]` unchanged; r4 "queue held — head 2->384" while a second base read `386` in the
same window. Across every trace, **38/303** of our rows and **2804** rows overall hold a slot
outside `0..23` — so a queue slot is NOT reliably a type id and no global floor may demand it. The
run also lost University Base (`bases_ours` 2 -> 1, `units_ours` 9 -> 5); base death and the queue
anomaly share the same windows, so this is **CONFOUNDED**, written as such in NAMED.md.

**A LATENT BUG IN THE GATE'S CITATION CHECKER.** `evidence.load_cites()` matched
`png|log|gdb|txt|json|csv` — not `.jsonl` — so **no trace could ever count as cited**, and the
alternation order (`json` before `jsonl`) hid the first fix. After both fixes the audit reports
10 uncited files / 0.1 MB where it had claimed 578 files / 12.7 MB. New command
`python3 scripts/evidence.py audit [--delete]` (cites = docs AND `scripts/*.py`, so classifier
frames are safe): **deleted 396 uncited files, 27.7 -> 22.8 MB**, and `test_classify.py` still
**PASS 17/17** afterwards.

**FIXTURE TRACES NO LONGER POLLUTE EVIDENCE.** `m56_build.py --fixture X` writes to `$TMPDIR`
(`scratch/fixture_trace_*.jsonl`); evidence jsonl count 174 before and after the three fixture
cases (`defer_ok` 0, `beat_visit` 1, `bad` 1).

**THE BRIEF IS GENERATED (`scripts/session_brief.py`, ≤4 KB, `--write` -> `BRIEF.md`).** Verdict +
both bases + the tagged CONFLICTs + next pick + first commands + uncited evidence. `NAMED.md` now
carries three **`CONFLICT:`** lines (year store `0x51f554` vs `0x51f54f`; queued-count byte
`0x94dc84` vs `0x94de84`; pay `0x4f0ca6` vs the measured `0x4efedd`) which the brief prints
verbatim. Measured on the 125B for the fixed-cost argument: **596 tok -> 1.83 s prefill, 44,446 tok
-> 15.4 s** (0.345 ms/token) — the footing's size is not the problem, stumbling is.

**Open.** (1) What writes 384/386 into `+0x50` (two bases in one window). (2) Whether a dead/stale
base record is what those reads are. (3) The pop's real operand — pending decrements, slots do not
move, in two independent sessions now. (4) The support-disband path can eat a created unit, so
READY ≠ PASS (not modelled). (5) Box drifted: 1 base, 5 units, year 2174 r74 — reload before the
next acceptance. (6) `session_brief.py` prints only the FIRST line of each multi-line CONFLICT (the
wrapped continuation lines are not joined).

**Next pick (M63):** what writes 384/386 into `base+0x50`, and what the pop does to the slots —
reload first, then pop breakpoint + a watchpoint on one named base's `+0x50..+0x74`, two-three
boundaries, one variable per run.
