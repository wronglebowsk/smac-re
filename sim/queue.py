#!/usr/bin/env python3
"""sim.queue - rung B11: the production-queue mechanics leg (R2's "build" slice).

BUILD_SPINE.md rung B11. The M68-M72 queue law, executable, parity-checked against
the game's OWN recorded queue states (evidence/m69_cursor.jsonl,
m70_cursor_events.jsonl, m71pop_seq.jsonl, m71pop3_seq.jsonl, m72gate4_seq.jsonl,
m72gate5_seq.jsonl - the game's bytes, not a model's guesses).

The law (settled, skill references/production-queue.md sections M68-M72; offsets in
the 304-B base record, identical in memory and in the save - M282/M285):

  * INSERT is queue[pos] = item with pos = the queue widget's cursor row
    (*(int *)(0x6a9480 + 0x3ff5c), M69): the shift runs from
    min(9, max(pending+1, cursor)) DOWN to cursor+1 (slot AT pending+1 moves,
    slots above keep stale values - M70), the store uses the ORIGINAL cursor,
    pending++ only when pending < 9 (cap 9). The enqueue tail then parks the
    cursor at rows+1 (0x417e3b), and the 0x4d00 handler zeroes it (0x4194b3) -
    so a post-INSERT read-back reads 0, not rows+1 (M70).
  * a duplicate id is REFUSED (M68: a second INSERT of 193 left pending and every
    slot unchanged).
  * a negative slot value is the TYPE's, not a bad click: 195 -> -3, 196 -> -6
    for recordless ids (M68/M69). The mapping table is OPEN (stride disagreement),
    so the model stores values VERBATIM; the recorded pairs are DATA, not a rule.
  * the head sentinel is 0xffffffd9 = -39 (M68), not -38.
  * a completion's POP pops ONE item when the new head validates; the shard
    "each iteration shifts only 0..pending_j-1 and pending shrinks" composes to
    for k in range(pending): slots[k] = slots[k+1]; pending -= 1 - so
    queue[pending] keeps its STALE id: the measured [2,193,192,0] -> [193,192,192,0]
    (a duplicate no instruction wrote). The completion writes the cursor ZERO times.
  * affordability on the visit is the visitor's OWN product at 0x4efa5e
    (cmp [base+0x40],edi; bail 0x4efa63), NOT price_of: head 193 wants 27 where
    price_of says 18 (M72). The gate takes the recorded edi as its cost.

The rung's acceptance (sim.selftest --b11 <sav>) replays the recorded evidence and
requires byte-for-byte slot/pending/cursor equality at every armed event, with two
RIVALS that FAIL the same fit (shift-left-by-K pop; price_of affordability).
The M282 G5 found-event SCHEDULING frontier is DECLARED, not modeled: B11 replays
recorded queue states, it does not predict which turns found/write.
NO /proc, NO gdb, NO Wine.
"""
import argparse
import hashlib
import json
import os
import struct
import sys

from . import save as so

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(REPO, "evidence")

# --- the law's constants ---
CAP = 9                 # pending cap: pending++ only when pending < 9
SENTINEL = -39          # 0xffffffd9, the empty-head sentinel (M68; NOT -38)
PENDING_OFF = 0x4c      # pending dword in the 304-B base record (M285 live read)
HEAD_OFF = 0x50         # slot 0 (head) dword in the base record (M285 live read)
SLOT_STRIDE = 4
SLOTS_IN_RECORD = 10    # head + 9 queued slots occupy +0x50..+0x77

NEG_TYPE = {195: -3, 196: -6}   # recorded data (M68/M69); mapping rule OPEN


class Queue:
    """The production-queue model. slots[0] is the head; live slots are 0..pending-1;
    slots[pending] is STALE by the M71 law. The cursor is separate state."""

    def __init__(self, slots=None, pending=0, cursor=0):
        if slots is None:
            slots = [SENTINEL] + [0] * (SLOTS_IN_RECORD - 1)
        self.slots = list(slots)
        self.pending = int(pending)
        self.cursor = int(cursor)

    # -- readers mirroring the recorded field names -------------------------
    def head(self):
        return self.slots[0]

    def live(self):
        return list(self.slots[:self.pending])

    def snapshot(self):
        return {"pending": self.pending, "cursor": self.cursor,
                "slots": list(self.slots)}

    # -- the writers --------------------------------------------------------
    def row_click(self, row):
        """0x40aae5: cursor = min(clicked_row, rows + 1); the widget's row count
        is the base's pending (M70 measured both equal in the armed window)."""
        self.cursor = min(int(row), self.pending + 1)

    def insert(self, item):
        """M69/M70 INSERT: shift min(9, max(pending+1, cursor))..cursor+1 up one,
        store at the ORIGINAL cursor, pending++ when pending < 9, then the
        enqueue tail parks the cursor at rows+1. A duplicate id is refused."""
        if item in self.slots[:self.pending]:
            return False                      # M68 duplicate refusal
        hi = min(CAP, max(self.pending + 1, self.cursor))
        for k in range(hi, self.cursor, -1):
            self.slots[k] = self.slots[k - 1]
        self.slots[self.cursor] = item
        if self.pending < CAP:
            self.pending += 1
        self.cursor = self.pending + 1        # enqueue tail (0x417e3b)
        return True

    def clear_cursor(self):
        """0x4194b3 (the 0x4d00 message handler): zeroes the cursor."""
        self.cursor = 0

    def pop_once(self):
        """M71 completion POP - ONE item. for k in range(pending): slots[k] = slots[k+1]
        then pending -= 1; slots[pending] keeps its STALE id. Returns the popped id."""
        if self.pending <= 0:
            return None
        head = self.slots[0]
        for k in range(self.pending):
            self.slots[k] = self.slots[k + 1]
        self.pending -= 1
        return head

    def visit(self, storage, cost):
        """M72 affordability - the visitor's OWN cost product (0x4efa5e), not
        price_of. storage >= cost -> pay (storage -= cost), create the head, then
        pop exactly one. Returns ('pay', storage_after) or ('bail', storage)."""
        if storage < cost:
            return ("bail", storage)          # 0x4efa63 BAILAFF
        made = self.pop_once()                # create the head (CREATE), then POP
        return ("pay", storage - cost, made)


# --- replay of the recorded evidence -----------------------------------------
def replay_m70():
    """m70_cursor_events.jsonl: armed(0,0) -> rowclick 3 -> cursor 1; insert 193
    at 1 -> pend 1, tail 2; insert 192 at 2 -> pend 2, tail 3; 0x4d00 -> cursor 0.
    Returns the model's event states for gating."""
    q = Queue(cursor=0, pending=0)
    out = []
    q.row_click(3)
    out.append(("rowclick", (q.cursor, q.pending)))
    q.insert(193)
    out.append(("insert193", (q.slots[1], q.pending, q.cursor)))
    q.insert(192)
    out.append(("insert192", (q.slots[2], q.pending, q.cursor)))
    q.clear_cursor()
    out.append(("clear", q.cursor))
    return out


def replay_m69():
    """m69_cursor.jsonl: before pending 4 [2,192,194,1,193,...] (193 is STALE at
    index 4), cursor poked to 4, INSERT item 0 -> landing [4,0], pending 5,
    slots [2,192,194,1,0,193,...], cursor_after 6."""
    before = [2, 192, 194, 1, 193, 0, 0, 0, 0, 0]
    q = Queue(slots=before, pending=4, cursor=4)
    q.insert(0)
    return q.snapshot()


def replay_pop(evidence, storage):
    """m71pop_seq / m71pop3_seq: VISIT(head) PAYA(edi) CREATE(id) then POP -
    [2,193,192,0] -> [193,192,192,0], pending 2 -> 1. Returns final snapshot."""
    with open(os.path.join(EVID, evidence), encoding="utf-8") as fh:
        rows = [json.loads(ln) for ln in fh if ln.strip()]
    q = Queue(pending=2)
    q.slots = [2, 193, 192, 0, 0, 0, 0, 0, 0, 0]
    for r in rows:
        if r["tag"] == "PAYA":
            assert storage == r["storage"] and r["edi"] == 9   # recorded operands
            res = q.visit(storage, r["edi"])
            storage = res[1] if res[0] == "bail" else res[1]
        elif r["tag"] == "CREATE":
            pass                       # the create is the pop_once inside visit
    return q.snapshot()


def replay_m72(evidence, rival_cost=None):
    """m72gate4_seq (storage 18, edi 27 -> BAIL x2, queue untouched) or
    m72gate5_seq (storage 27, edi 27 -> PAY once, storage 0). Returns
    (verdicts, final_snapshot, storage_left). rival_cost swaps the visitor's
    own edi for a rival cost (e.g. price_of 18) - the FAILS-THE-SAME-FIT probe."""
    with open(os.path.join(EVID, evidence), encoding="utf-8") as fh:
        rows = [json.loads(ln) for ln in fh if ln.strip()]
    storage = rows[0]["storage"]
    q = Queue(pending=1)
    q.slots = [193, 192, 0, 0, 0, 0, 0, 0, 0, 0]
    states = []
    for r in rows:
        if r["tag"] == "POSAFF":
            cost = r["edi"] if rival_cost is None else rival_cost
            res = q.visit(storage, cost)
            states.append(res)
            if res[0] == "pay":
                storage = res[1]
    return states, q.snapshot(), storage


def evidence_sha256(*paths):
    h = hashlib.sha256()
    for p in paths:
        with open(os.path.join(EVID, p), "rb") as fh:
            h.update(fh.read())
        h.update(b"\x00")
    return h.hexdigest()


# --- recorded-queue write composition (gate 6) -------------------------------
def queue_bytes(q, record):
    """Compose the pending/slots dwords of a 304-B base record from the model.
    q has .pending and .slots; record is the original record bytearray."""
    struct.pack_into("<i", record, PENDING_OFF, int(q.pending))
    for k in range(SLOTS_IN_RECORD):
        struct.pack_into("<i", record, HEAD_OFF + SLOT_STRIDE * k, int(q.slots[k]))
    return record


# --- module CLI ---------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(prog="sim.queue")
    ap.add_argument("--sav", required=True, help="a .SAV to load the base array from")
    ap.add_argument("--out", help="write the replay report JSON here")
    args = ap.parse_args(argv)
    sv = so.parse(args.sav)
    report = {
        "rung": "B11",
        "m70": replay_m70(),
        "m69_after": replay_m69(),
        "m71_after": replay_pop("m71pop_seq.jsonl", 9),
        "m71p3_after": replay_pop("m71pop3_seq.jsonl", 10),
        "m72_bail": replay_m72("m72gate4_seq.jsonl"),
        "m72_pay": replay_m72("m72gate5_seq.jsonl"),
        "n_bases": sv.n_bases,
    }
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
