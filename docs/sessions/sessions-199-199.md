# Session notes archive — sessions 199-199

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 199 (2026-11-01, BUILD fire) — **B3: the C1 turn engine is executable and replays M30's trace 67/67**

**Acceptance.** `python3 -m sim.selftest --replay evidence/m30_turn_trace.jsonl` → `PASS B3:
6/6 gates on m30_turn_trace.jsonl`, rc=0, real 22.3 s, **ONE invocation** (no threshold set or
moved after the run) → `evidence/b3_turn_replay.txt`. New model file `sim/turn.py`, gates in
`sim/selftest.py::run_replay`.

**Why parity is an ORDERED SUBSEQUENCE, not an equality.** The trace is a 0.2 s SAMPLE:
`scripts/turn_trace.py:59` logs a row only when one of (year, cur, tf) differs from the previous
sample, so a run of short AI phases appears as its LAST value only (turn_driver.md §M30 says the
same: 1–5 of the 8 phases are visible per cycle). The engine must reach every recorded row in
order — 67/67, zero tolerance — and the 154 emissions the matcher consumed as "extra" are exactly
the phases the sampler collapsed (220 emissions, 11 per cycle).

**What the trace pins down (G1-G6).**
- The walk is ASCENDING over the 8 faction slots and our slot is 3: `tf == 0` appears in 21/67
  rows and every one of them has `cur == 3`; `own == 3` in all 67.
- **The year counter fires on the 7→0 edge, while `cur` is still 7** — not at the press, not at
  the human landing. Witness row 22 `t=88.631 (cur 7, tf 2, year 2221)` is the only row where a
  new year is visible behind an AI slot. All 8 candidate edges: cur==7 → 66/66, cur 0/1 → 22/66,
  cur 2 → 10/66, cur 6 → 6/66, cur 3/4/5 → 0/66.
- **`tf` is cleared ONE STEP AFTER `cur_player` is written to 3**: deleting the (3, tf=2) landing
  state from the model drops parity to 5/66. Four rows are (3,2) — 5, 14, 23, 40 — each following
  an AI slot, never a (3,0) row. **RETRACTION (M30 claim 3):** "cur_player is **never 3** while
  `turn_flags & 2`" is false in its own data — those four rows ARE that state. The correct rule is
  that the walk ENDS on slot 3 with tf still set, and tf is cleared one step later.
- Model space = cyclic walk order (7! orders × 8 positions for the human) × 8 year edges =
  **322,560 candidates, 48 (0.0149 %) reproduce the trace**, forming 6 distinct cyclic orders × 8
  rotations. All 48 share the edges 0→1, 1→2, 2→3, 7→0 and the year edge 7; the ONLY freedom is
  the relative order of slots {4,5,6} — no cycle ever shows two of them in the same leg.
- 20 presses → 20 year bumps → 20 tf clears; year 2213→2233; final state (3, 0, 2233) = last row.

**OPEN.** The press transition (3,0)→(3,2) is never separately sampled — dropping it keeps 66/66
— so whether the engine writes `turn_flags` before `cur_player` at TURN COMPLETE is unsettled;
the internal order of {4,5,6} needs a denser or longer trace. `nb` (base count @0x985AF4) moves
51→58 with one decrease (row 28, 57→56) and is not modelled by B3. No box time: no /proc, no gdb.
