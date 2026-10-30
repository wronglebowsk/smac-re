# Verify the OUTCOME, not the mechanism

Read this before writing or trusting any acceptance gate: a gate that counts the harness's own work can pass a
run that lost the game, and a PASS on a shape that cannot discriminate is not a PASS. Nothing here is loaded by
default — open it when you are choosing what a milestone's acceptance should assert.

## An acceptance script that counts its own work (year deltas, verified order bytes, landed
walks, STUCK) will happily pass a run that lost the game: a 40-turn run printed `PASS` with `40/40`
and 5 landed walks while the faction owned **zero** bases at the end.
The defeat was invisible because the trace carried only the map-wide base count, never
"how many bases do WE own".

- After every unattended run, re-read the position and assert the outcome out loud: bases of our
  faction, where our records stand, `turn_flags`. The plumbing exists — `scripts/smac_state.py
  --json` prints `bases_ours`/`units_ours`, `smac_play.py` carries both in every per-turn
  `state_before`/`state_after`, and `m54a_check_run.py --min-our-bases N` fails a run that loses
  the position. **Use the floor on every run that is supposed to keep what it has**; it fails
  closed, so a trace predating the fields FAILs instead of passing vacuously.
- **A record that vanishes after a position poke was probably parked on an impassable tile, not killed.**
  Read the tile's flag byte (record `+3` even x, `+7` odd x; bit `0x40` = impassable) first: the game
  deletes records standing on impassable tiles within seconds and it looks exactly like a combat loss
  in the census. Use the multiset-diff poller (`references/wine-operations.md`) to catch the tick.
- **Never write a handoff sentence about where the game ended up from the plan.** "The garrison is
  back on University Base" was inferred from the pre-run census plus the walk destinations, never
  read back, and was false. Read it, then quote the numbers.
- **Change one variable per prep poke.** Emptying a destination tile and moving the walker off a
  half-tile offset in one poke produced a confident, wrong root cause (that tile's occupancy)
  which the run's own trace later refuted. Split the poke, or label the cause unattributed.
- **A harness that raises AFTER the measurement window is a harness bug, not a failed shape.** The events
  are already in the evidence log: read the log, fix the harness, and re-run the SAME shape on a fresh box
  state. Never read a piped acceptance's exit code as its verdict — `… | tail` masks the failure, so a
  Traceback in the captured output means FAIL even when every interesting line printed.
- **Record index is not identity, and the unit array GROWS mid-run** — a base building a unit
  shifts every index after it, so an index carried across a turn (or read a fraction of a second
  after the order lands) can name a different unit's record. It also COMPACTS mid-turn — a queued MOVE
  can execute inside our phase and every flip re-shuffles the slots, so even a byte read seconds after
  the keypress can name a different record. During any burst, re-read WHO wears the byte
  (scan all records for the transition against the pre-press snapshot), not who sits at the slot. Snapshot ALL our records (type, x, y,
  `+17`, legs) before the keypress and diff after; take the field from the record that actually
  changed, and report how many changed — two changed means the result is confounded. **Across a round
  boundary even the BYTES are not identity**: upkeep/compaction decrements the u16 index references at
  `+28/+48/+50` inside idle records, so diff record sets on (x, y, type, owner, order) and report byte
  rewrites as a feature (`references/solo-round-boundary.md`).** The 304-byte BASE array
    reorders and compacts too — pair a base across snapshots by NAME (or `(x,y)`), never by remembered
    index, and treat `--ui-queued <index>` as a start index only.
- **Attributing a field to one keypress: the through-the-click watcher on the subject's own slot
  is the only proof.** A read taken after the click proves the field changed somewhere, not on
  which record — pair the byte and the field from the SAME sample. Use the post-click array snapshot
  only to look for RIVALS (the pump may have consumed the byte; a unit build shifts every index).
  A destination counts as this order's only when
  `+17` went 0 -> the byte on the watched slot, the leg arrays CHANGED against that record's own
  pre-press value (stale legs survive the pump and name somebody else's trip), and no rival — a
  same-type/same-tile look-alike freshly ordered, a record wearing the watched signature under a
  shifted index, or a subject that left its tile — exists.
  Any of those: report the walk UNATTRIBUTED / CONFOUNDED with the rival records quoted; a guessed
  destination poisons the next session's footing.
- **A position claim needs a DELTA, not a match.** "A record of this type sits on the destination
  tile" is true before the walk starts when look-alike units are parked there. Require the count
  of that type to rise at the destination and fall at the origin against a baseline captured at
  order time, and re-read an unfinished walk on later turns (an ordered move can cost more
  movement than one turn gives it). When the confound is your own decoys, park them FIRST: poke
  `+17` to a standing order (SENTRY) and read it back, so exactly one subject can move.
- **Click a pane button at its measured centre, never at the merged midpoint of the bars in a
  y-range.** A chooser that grows rows drags its button band down and its row bars merge into the
  same y-window; the  midpoint of that span is a Sort button — clicking it re-sorts instead of answering. Derive the button band
  (equal-width groups on an even pitch), index it (OK fourth, CANCEL last), and fall back to the
  midpoint only when no button band was measured.
- **Make a test fixture of the 52-byte record match the FORMAT, not just the fields you assert
  on** — pre-fill the leg arrays with the `-1` terminators. A zero-filled fixture decodes as extra
  real legs `(0,0)`, which silently inverts legs-changed comparisons and makes a correct rule look
  broken (or a broken rule look correct).
- **`f.seek(off) or f.read(1)[0]` returns the OFFSET, not the byte.** `seek()` returns the new
  position, so `or` short-circuits for every non-zero offset and a `/proc/<pid>/mem` reader written
  that way silently hands back the ADDRESS — which can cost a run its discriminating check. Read in two
  statements, and log the value next to the offset it came from so
  a reader bug cannot impersonate a measurement.
- **Grep every consumer call site before changing a helper's sample/return shape** — probe scripts
  and hand-rolled fixtures keep the old shape, and tuple-index bugs surface only in the shard you
  did not re-run (a `(raw, ms, byte)` watcher whose readers still index `s[1]` silently never
  matches). In a comprehension, a variable used in the key or filter must be introduced by an
  earlier `for` clause.
- **Write the attribution/verification rule's CASE LIST before coding it against a unit test**:
  one line per case — before-state, after-state, expected verdict (claimed / confounded /
  unattributed). Semantics designed by repeatedly failing a test rewrite function and test
  together for dozens of tool calls; the checkpoint commit fires at the first green test, not at
  the end of that churn.
- **Pick the box state that makes the rival hypotheses DISAGREE before you run — a PASS on a state
  where they predict the same result proves nothing.** Write every rival rule down first, then choose
  the state that separates them (an empty queue region makes "writes slot `4*pending`" and "inserts by
  a sort key" predict identical slots; a region holding unequal key values does not; two sort keys that
  happen to rank the same ids identically — cost `+41` vs plan `+42` — need an item whose two orders
  DISAGREE), and make the scorer print
  FAIL when more than one rule fits rather than picking one. **A null model built from the same term is
  not a null**: if model and null agree on every candidate the run cannot discriminate — print the split
  count and refuse the shape (`references/instrument-laws.md`: a cat-7-only null over a cat-7 block
  re-certifies itself green). This is the case-list discipline applied
  to the STATE: a green run on an undiscriminating state is refuted by the next run, and the refutation
  looks like a contradiction in your own ledger.
- **A gate certificate is about the RULES, not about the game.** A pre-click gate can certify "only
  key K predicts this landing sequence" and the run can still come back with a landing that NOTHING
  in your model explains, because the mechanism you modelled was not running at all: five clicks
  wrote consecutive slots (one append per click) where the gate had certified a sort-key sequence,
  and "append in click order" is predicted by dozens of candidate keys at once (every byte constant
  over the involved ids), so the run names no key. Read that FAIL as "no claim", never as "the key
  is wrong", and never let it overwrite a live read-back from another state — record the two states
  side by side and write CONFOUNDED. The next move is not another state or another click order: it
  is a breakpoint at the write site (entry of the enqueue, the index it computes, the value it
  stores) plus a hardware watch on the first element, which answers "sorted scan or append" and
  "where the odd value came from" in one run.
- **Read the structure PLUS ONE SLOT PAST ITS END, and treat the read model as fallible.** A write
  location is only interpretable if you can see where the array stops: SMAC's queue is 10 dwords
  (`base+0x50..+0x74`) and the dword after it is a different field that never moves, so an 8-slot
  read window hid the boundary and a correct insert scored as "no rule explains this" twice. When
  measured bytes fit NO model you wrote, suspect the MODEL (shift bounded by the window? by the
  region? by the array's capacity?), not the game. A read model is not a hypothesis about the game:
  fix it, say which shapes each version predicted, and re-accept on a shape you have not used yet. The same
  applies to a record COUNT carried in from an earlier census (and to a file chunk: a helper handed a
  buffer that was ALREADY sliced from some base must index it RELATIVE to the slice — re-adding the base
  offset runs past the end and crashes the harness before the first measurement); before arming anything,
  read the whole
  `stride × count` region straight from `/proc/<pid>/mem` (no gdb — the cheapest measurement available)
  and group it by the band the code's own index arithmetic computes. A "256-record" type table was really
  8 × 64, and every index above the assumed bound was an ordinary record of another faction.
- **Make the value you are locating distinguishable from what the structure already holds.** A
  write-location question (which slot did the game write?) is unanswerable when the written value
  equals a value already sitting in the array — enqueue or poke an id the structure does not hold, and
  never trust the empty marker: unused slots can read 0 while the documented empty code is a different
  number, and 0 may itself be a legal item id. Two rules fitting a duplicate-value shape is the signal
  that the experiment, not the rule, needs a different value.
- **Read a widget's backing array only after the widget is open, and confirm the click landed.** A
  paint rebuilds and re-sorts list data (the build chooser's candidate array changed order between a
  pre-open read and the open chooser), so a cell→item map taken before the open is stale; after the
  click read the widget's own selection field, then the array entry at that index, and credit the
  stored value only against the read taken at click time. **Cells past the first row can silently
  not take**: a click can leave the selection field on the PREVIOUS value and the commit button then
  does nothing, so re-assert `selection == intended cell` AND `entry_at_cell == intended item` before
  every commit click. Look for the cause in the WIDGET STATE before blaming the pixel pitch — the same
  cell 4 / cell 6 coordinates that failed three times registered first try once the pane open was
  FORCED: a stale-open check (`if pane_base_idx != idx: open`) passes while the pane is CLOSED whenever
  the index happens to equal 0, so always press the open key, click the row, and confirm the chooser
  populated (candidate count > 0). A NEGATIVE code stored instead of the item id is the TYPE's, not the
  click's: one click whose selection verified stored -6 for an all-zero record and another -3, both
  with `selection == cell` — read a negative as "this id has no real record" and keep such ids out of
  any shape.
- **Before a diff counts as evidence that one of two similar arrays moved, check the addresses are
  disjoint.** Two byte arrays a few hundred bytes apart indexed with the same
  `base + stride*owner + id` formula OVERLAP — at a 512 B separation, `low[512+id]` IS `high[id]` — so
  sampling one index in each can "confirm" the same byte twice. Diff whole rows and subtract addresses.
- A `turn_flags` bit that survives a year flip means the box is wedged mid-round, not that the
  click failed — hand that over explicitly and start the next session from a known-good save.

## Publishing rule: one instrument is a lead, never a finding

Every instrument here lies in a plausible way, and always the same way: its failure mode looks like its
success mode. `gdb -batch` detaches after 3 events and prints a clean end. A conditioned breakpoint that
ever fires prints nothing at all. A census whose byte sum over-runs its own file still prints a total. A poke
whose target was mis-derived prints a clean zero. So a structural claim goes out only when two instruments
that can fail DIFFERENTLY agree, and the harness states the state it left behind.

- **Pair the claim with an instrument that cannot share its failure.** A byte sum closes to the file, or a
  poke lands in memory: only the second survives a wrong offset model. A log says the loader ran, a live
  count says the save is in the game. A register print names the writer, a `/proc` read-back names the value.
  When the two disagree, the INTERESTING one is the one that does not depend on your arithmetic.
- **Assert the state an instrument leaves behind, not its exit code.** After any instrumented run the box
  must be provably clean (`TracerPid: 0`, no stale gdb, counts still the loaded save's) and the run's own
  precondition must be printed in the log (armed count, filter value, prediction table). An exit code of 0
  is a rumour about the process; `TracerPid` is a fact about the box. **And make the exit code MEAN its verdict — a
  measured NEGATIVE exits 0.** Encode the states apart: 0 = the site/effect was measured (it fired or it did not),
  4 = the site was never reached (inconclusive, no claim), 5 = the window was a wedge / the driver did no work (no
  measurement at all), 8 = the box was left dirty. Encoding "reached N times and never taken" as a failure makes a
  milestone's own finding look like a broken run, and encoding a wedge as "never reached" converts a driver problem
  into a claim about the game; both directions mislead the next reader, so name the states in the harness header.
- **Pre-register the predictions AND the falsifier before the run.** Write the two or three candidate
  numbers the models predict, and the sentence you will retract if none matches. A run where every
  prediction fails is a result (it retires the shape); a run that "looks plausible" with nothing
  pre-registered is a lead that will be quoted later as fact.
- **Retract in place, in the sentence that asserted it.** When a later measurement refutes a claim, edit the
  block that made it and add one line saying which part died and what replaced it. Appending a correction
  below a still-standing wrong sentence leaves the next session reading whichever it hits first — and a
  merged PR title is the first thing anyone reads.
