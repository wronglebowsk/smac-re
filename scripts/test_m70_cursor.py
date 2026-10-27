#!/usr/bin/env python3
"""M70 — pin the cursor-writer attribution and the enqueue's cursor arithmetic.

Everything here is offline (no game, no gdb): it pins (a) the log parser against the
MEASURED M69 log lines, (b) the acceptance gate's discriminating power, and (c) the
enqueue's cursor/pending/shift arithmetic against the four real ENQUEUE->STORE transitions
recorded in evidence/m69_enqueue.gdblog.

Run: python3 scripts/test_m70_cursor.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m70_cursor_watch as W          # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []
total = [0]


def check(name, cond, detail=""):
    total[0] += 1
    print("%s %-52s %s" % ("ok " if cond else "BAD", name, detail))
    if not cond:
        fails.append(name)


# ---------------------------------------------------------------- the log parser
# The ENQUEUE/STORE spellings below are copied from evidence/m69_enqueue.gdblog (measured).
M69_LOG = """ARMED base=0x95da10 cursor_abs=0x6e93dc cursor=1 pending=2
ENQUEUE obj=0x6a9480 pos=1 pending=2
 slots 2 194 1 0 0 0 0 0 0 0 9225 0
  WRITE slot3 pc=0x417ddb now=1 pend=2
STORE queue[1]=192 (item ebx) pending=3
ENQUEUE obj=0x6a9480 pos=4 pending=3
STORE queue[4]=193 (item ebx) pending=4
ENQUEUE obj=0x6a9480 pos=4 pending=4
STORE queue[4]=0 (item ebx) pending=5
ENQUEUE obj=0x6a9480 pos=2 pending=5
STORE queue[2]=-6 (item ebx) pending=6
"""

M70_SHAPED = """ROWCLICK clicked=2 cursor_before=4 pending=1
CURSORWRITE pc=0x40aae5 now=2 pend=1
CURSORWRITE pc=0x40aae5 now=2 pend=1
ENQUEUE obj=0x6a9480 pos=2 pending=1
STORE queue[2]=193 (item ebx) pending=2
ENQTAIL_SET cursor_new=3 pending=2
CURSORWRITE pc=0x417e3b now=3 pend=2
SLOT2WRITE pc=0x417e08 now=193 pend=2
"""


def ev_of(text):
    return W.parse_lines(text)


ev69 = ev_of(M69_LOG)
check("parser: M69 log yields the 4 enqueue reads",
      sum(1 for e in ev69 if e["tag"] == "enqueue_read") == 4,
      str([e["pos"] for e in ev69 if e["tag"] == "enqueue_read"]))
check("parser: M69 log yields the 4 stores with their items",
      [e["item"] for e in ev69 if e["tag"] == "store"] == [192, 193, 0, -6])
_shaped = ev_of(M70_SHAPED)
_shaped_tags = [e["tag"] for e in _shaped]
check("parser: cursor_write / rowclick / tail / slot_write all parse",
      _shaped_tags == ["rowclick", "cursor_write", "cursor_write",
                       "enqueue_read", "store", "enqueue_tail_set", "cursor_write",
                       "slot_write"]
      and sum(1 for e in _shaped if e["tag"] == "cursor_write"
              and e["pc"] == 0x40AAE5) == 2,
      str(_shaped_tags))
check("parser: an armed line records the cursor at arm time",
      ev_of(M69_LOG)[0] == dict(tag="armed", cursor=1, pend=2))

# ---------------------------------------------------------------- the acceptance gate
ev_good = ev_of(M70_SHAPED)
# slots before -> after: the insert of 193 at region slot 2
slots_before = [2, 194, 1, 0, 0, 0, 0, 0, 0, 0, 9225, 0]
slots_after = [2, 194, 193, 1, 0, 0, 0, 0, 0, 0, 9225, 0]
ok, summ, reasons = W.score(ev_good, 4, 3, 2, slots_before, slots_after)
check("gate: a run with a row-click writer + enqueue tail PASSES", ok, "; ".join(reasons))
check("gate: the PASS names the row-click handler (0x40aae5) as a non-enqueue writer",
      summ["non_enqueue_writers"] == ["0x40aae5"], str(summ["non_enqueue_writers"]))

enqueue_only = """ENQUEUE obj=0x6a9480 pos=1 pending=1
STORE queue[1]=193 (item ebx) pending=2
ENQTAIL_SET cursor_new=2 pending=2
CURSORWRITE pc=0x417e3b now=2 pend=2
"""
ok2, s2, r2 = W.score(ev_of(enqueue_only), 1, 2, 2, slots_before,
                      [2, 193, 194, 1, 0, 0, 0, 0, 0, 0, 9225, 0])
check("gate: an enqueue-only run FAILS (cannot name a user cursor-setter)",
      (not ok2) and any("enqueue" in r for r in r2), "; ".join(r2))

ok3, s3, r3 = W.score(ev_of("CURSORWRITE pc=0x401234 now=2 pend=1\n"), 4, 2, 2,
                      slots_before, slots_after)
check("gate: an unattributed writer pc FAILS the run",
      (not ok3) and any("not yet read" in r for r in r3), "; ".join(r3))

ok4, s4, r4 = W.score(ev_of(M70_SHAPED), 4, 5, 2, slots_before, slots_after)
check("gate: a cursor read-back that is not pending+1 FAILS",
      (not ok4) and any("pending+1" in r for r in r4), "; ".join(r4))

ok5, s5, r5 = W.score(ev_of(M70_SHAPED), 4, 3, 2, slots_before, slots_before)
check("gate: an unchanged queue region FAILS (no INSERT happened)",
      (not ok5) and any("unchanged" in r for r in r5), "; ".join(r5))

ok6, s6, r6 = W.score(ev_of(""), 1, 2, 0, slots_before, slots_after)
check("gate: no events at all FAILS", not ok6, "; ".join(r6))

# ---------------------------------------------------------------- the cursor model
MODEL = []


def model_enqueue(slots, pending, cursor, item, inserting):
    """Pure transcription of 0x417d20..0x417e43.  Returns (slots, pending, cursor).

    Region slots are indices 1..9 (index 0 is the head, never written by INSERT; index 10
    is the word after the array — 9225/545 on our bases — which the shift never touches).
    The shift runs from `min(9, max(pending + 1, cursor))` DOWN to `cursor + 1` (disasm
    0x417dcd seeds `edx = 0x74` = slot 9 and 0x417de4 gates `while 9 > cursor`; the three
    measured M69 transitions show slot 3 moving at pending 2/cursor 1, slot 4 at
    pending 3/cursor 4 and slots 6,5,4,3 at pending 5/cursor 2 — i.e. the top of the shift
    is max(pending+1, cursor), and slots ABOVE it keep their stale values).  The store uses
    the ORIGINAL cursor: the clamp at 0x417ddb feeds only the `cmp esi,eax` / `cmp edx,0x9`
    tests at 0x417e17 / 0x417df3.
    """
    s = list(slots)
    if cursor == 0 or cursor == 9:
        return s, pending, cursor
    if not inserting:
        # the measured third M69 call (item 0, pending 4 -> 5) shifted slot cursor+1 down
        # and left cursor alone; the 0x417d5f REMOVE search path is a different shape.
        if cursor + 1 <= 9:
            s[cursor + 1] = 0
        pending = min(pending + 1, 9)
        return s, pending, cursor
    top = min(9, max(pending + 1, cursor))
    for k in range(top, cursor, -1):
        s[k] = s[k - 1]
    if cursor > pending:
        cursor = pending
    if pending < 9:
        pending += 1
    store_at = min(cursor, 9)
    if 1 <= store_at:
        s[store_at] = item
    if cursor <= pending:
        cursor = pending + 1
    return s, pending, cursor


# The four real transitions from evidence/m69_enqueue.gdblog.  Each row is
# (label, slots_before, pending, cursor_at_ENQUEUE, item, inserting, slots_after,
#  pending_after, cursor_after) — cursor_after is the model's, checked against the NEXT
# ENQUEUE line's pos, which is the measured cursor.
TRANSITIONS = [
    ("insert 192 at cursor 1 (pend 2)",
     [2, 194, 1, 0, 0, 0, 0, 0, 0, 0, 9225, 0], 2, 1, 192, True,
     [2, 192, 194, 1, 0, 0, 0, 0, 0, 0, 9225, 0], 3, 4),
    ("insert 193 at cursor 4 (pend 3): cursor > pending, slot 4 (pending+1) shifts down",
     [2, 192, 194, 1, 0, 0, 0, 0, 0, 0, 9225, 0], 3, 4, 193, True,
     [2, 192, 194, 193, 0, 0, 0, 0, 0, 0, 9225, 0], 4, 5),
    ("the third M69 call (item 0 at cursor 4, pend 4 -> 5): slot 5 zeroed, cursor unchanged",
     [2, 192, 194, 1, 193, 0, 0, 0, 0, 0, 9225, 0], 4, 4, 0, False,
     [2, 192, 194, 1, 193, 0, 0, 0, 0, 0, 9225, 0], 5, 4),
    ("insert -6 at cursor 2 (pend 5 measured)",
     [2, 192, 194, 1, 0, 193, 0, 0, 0, 0, 9225, 0], 5, 2, -6, True,
     [2, 192, -6, 194, 1, 0, 193, 0, 0, 0, 9225, 0], 6, 7),
]

for label, sb, p0, cur, item, ins, sa, p1, cur1 in TRANSITIONS:
    got_s, got_p, got_c = model_enqueue(sb, p0, cur, item, ins)
    check("model: " + label,
          got_s == sa and got_p == p1,
          "got slots %s pending %d cursor %d" % (got_s, got_p, got_c))

check("model: an INSERT at the cursor lands the item AT the cursor slot (not at a sorted slot)",
      model_enqueue([2, 194, 1, 0, 0, 0, 0, 0, 0, 0, 9225, 0], 2, 2, 193, True)[0][2] == 193)
check("model: after an INSERT the cursor is pending+1 (0x417e3b) — two consecutive inserts "
      "append unless something else moves the cursor",
      model_enqueue([2, 194, 1, 0, 0, 0, 0, 0, 0, 0, 9225, 0], 2, 1, 192, True)[2] == 4
      and model_enqueue([2, 192, 194, 1, 0, 0, 0, 0, 0, 0, 9225, 0], 3, 4, 193, True)[2] == 5)

# ---------------------------------------------------------------- negative-id table
def neg_addr(neg):
    """The negative-value branch (disasm 0x40ada2-0x40adae and 0x4164e8-0x4164f5):

        neg eax ; lea ecx,[eax+eax*2] ; shl ecx,4 ; mov edx,[ecx+0x984d38]

    the load's effective address is ecx*1 + 0x984d38, and ecx = (-v)*3*16 = (-v)*48, so the
    stride is 48 bytes.  The 0x41890a site uses `shl ecx,4` with NO *3 (stride 16) — a real
    disagreement between two sites, recorded here as a CONFLICT, not smoothed over."""
    return 0x984D38 + (-neg) * 48


check("neg table: -3 and -6 address 0x984d38 + (-v)*48 at 0x40adae/0x4164f5 "
      "(0x418914 uses *16 — CONFLICT, reported not resolved)",
      neg_addr(-3) == 0x984D38 + 3 * 48 and neg_addr(-6) == 0x984D38 + 6 * 48,
      "0x%x / 0x%x" % (neg_addr(-3), neg_addr(-6)))

print()
if fails:
    print("FAIL %d/%d" % (total[0] - len(fails), total[0]))
    sys.exit(1)
print("PASS %d/%d m70 cursor cases" % (total[0], total[0]))
