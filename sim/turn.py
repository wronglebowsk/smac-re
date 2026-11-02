"""sim.turn — the C1 turn engine (M30) as executable code; rung B3 of BUILD_SPINE.md.

GROUND TRUTH  evidence/m30_turn_trace.jsonl — 67 sampled state changes.
scripts/turn_trace.py samples year@0x985B00, cur_player@0x985DCC, turn_flags@0x985AE8,
base-count@0x985AF4 and our faction@0x91B5B4 every 0.2 s while smac_play.py drives 20
turns, and (:59) logs a row only when one of (year, cur, tf) differs from the previous
sample.  Model prose: turn_driver.md §M30.

THE MODEL THIS FILE IMPLEMENTS
  state = (cur, tf, year);  8 faction slots 0..7, our faction is 3 (own == 3 in all 67
  rows; tf == 0 happens in no row whose cur != 3).
  1. the human phase is the state (cur == 3, tf == 0) and is the only state in which the
     driver's input does anything;
  2. pressing TURN COMPLETE sets tf |= 2 — the engine's "cycle in progress" gate;
  3. the engine then walks the remaining slots in ASCENDING index order, writing each
     one into cur_player as its phase runs;
  4. the YEAR increments after the last slot's phase and BEFORE cur_player is rewritten
     to 0.  The witness is row 22 (t=88.631) = (cur 7, tf 2, year 2221): the only row in
     the file in which a new year is seen while cur is still an AI slot.  A model that
     bumps the year at any other edge cannot produce that row;
  5. the walk ends by landing on 3 with tf STILL 2 (rows 5, 14, 23, 40) and only then
     clears tf — that clear is the next human phase.

WHY PARITY IS AN ORDERED SUBSEQUENCE, NOT AN EQUALITY
The trace is a *sampled* view: at 0.2 s a run of short AI phases appears as only the last
value in the window (turn_driver.md §M30: "sampling at 0.2 s catches 1-5 distinct AI
players per cycle ... treat 8 faction phases as the structure and the visible count as a
sampling artifact").  So the engine must reach every recorded (cur, tf, year) IN ORDER —
recorded rows may not be skipped, model rows may be extra (they are the phases the sampler
collapsed).  Zero tolerance on the recorded side: 67/67 or the rung is not built.

NOT SETTLED HERE: the press transition (3,0)->(3,2) is never separately sampled (all four
(3,2) rows follow an AI slot, never a (3,0) row), so whether the engine writes tf before
cur at TURN COMPLETE is OPEN; this model emits it as its own transition, which the
collapse tolerates either way.  `nb` (the base count) is not modelled by B3.
"""

SLOTS = 8
HUMAN = 3
TF_CYCLE = 2


class Engine:
    """The turn loop.  `press()` runs one round: TURN COMPLETE -> back to the human phase."""

    def __init__(self, year, order=None, year_after=None, human=HUMAN, tf=0, cur=None,
                 emit_press=True, merge_landing=False):
        self.order = list(range(SLOTS)) if order is None else list(order)
        if sorted(self.order) != list(range(SLOTS)):
            raise ValueError("order must be a permutation of the 8 faction slots")
        self.human = human
        self.year = year
        self.cur = HUMAN if cur is None else cur
        self.tf = tf
        # Slot after which the year counter fires.  The engine's cyclic order wraps at
        # order[-1] -> order[0], and that wrap is the year edge, so the default is the
        # last slot of the order (7 for the ascending order: the witness row 22 is
        # (cur 7, tf 2, year 2221)).  An enumeration over all 8 slots asks whether the
        # trace pins the edge down.
        self.year_after = self.order[-1] if year_after is None else year_after
        self.emit_press = emit_press
        self.merge_landing = merge_landing
        self.pos = {s: i for i, s in enumerate(self.order)}

    def state(self):
        return (self.cur, self.tf, self.year)

    def _successor(self, slot):
        return self.order[(self.pos[slot] + 1) % SLOTS]

    def press(self):
        """TURN COMPLETE from the human phase.  Returns the list of states the engine
        passes through, in order, ending at the next human phase (cur==human, tf==0)."""
        if not (self.cur == self.human and self.tf == 0):
            raise ValueError("press() is only legal in the human phase (cur==%d, tf==0); "
                             "state is %s" % (self.human, self.state()))
        out = []
        self.tf |= TF_CYCLE
        if self.emit_press:
            out.append(self.state())
        while True:
            prev = self.cur
            nxt = self._successor(prev)
            if prev == self.year_after:
                self.year += 1
                out.append(self.state())          # year fires while cur is still `prev`
            self.cur = nxt
            if nxt == self.human and self.merge_landing:
                self.tf = 0
                out.append(self.state())          # variant: land AND clear in one step
                return out
            out.append(self.state())
            if nxt == self.human:
                break
        self.tf = 0
        out.append(self.state())                  # the clear that opens the human phase
        return out


def replay(year, cycles, order=None, year_after=None, human=HUMAN, emit_press=True,
           merge_landing=False):
    """Run `cycles` rounds and return the full emitted transition sequence (excluding the
    initial state, which the caller compares separately)."""
    e = Engine(year, order=order, year_after=year_after, human=human,
               emit_press=emit_press, merge_landing=merge_landing)
    seq = []
    for _ in range(cycles):
        seq.extend(e.press())
    return e, seq


def match(emitted, recorded):
    """Greedy ordered-subsequence match of `recorded` (cur, tf, year) rows against the
    engine's emitted states.  Returns (matched_count, [indices of recorded rows that no
    emitted state supplies], [emitted indices that were consumed])."""
    consumed = []
    missing = []
    j = 0
    for i, r in enumerate(recorded):
        key = (r[0], r[1], r[2]) if len(r) == 3 else tuple(r[:3])
        while j < len(emitted) and emitted[j][:3] != key:
            j += 1
        if j < len(emitted):
            consumed.append(j)
            j += 1
        else:
            missing.append(i)
    return len(recorded) - len(missing), missing, consumed
