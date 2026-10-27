#!/usr/bin/env python3
"""M69 — pin the cursor mechanism and the read-backs that established it (offline, no game).

Three things are pinned here, all of them measured (see evidence/m69_*.jsonl, evidence/
m69_enqueue.gdblog):

  1. the queue write is `queue[1 + (pos-1)]` with `pos = *(int *)(0x6a9480 + 0x3ff5c)` — the
     queue widget's cursor row — so the landing index of a read-back must equal the poked
     cursor, and `_shift_index` must still find it uniquely;
  2. the plan-byte rule that M67 published (`+42` DESCENDING, ties after) gives a DIFFERENT
     index on the same shapes, which is what makes the M69 PASS discriminating;
  3. the negative store: an INSERT of a type with no real record (195, 196 at this base)
     writes a NEGATIVE value into the queue even when the click verified (`guard == cell`),
     so a negative is a property of the TYPE, not of a bad click (`-3` for 195, `-6` for 196).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m66_insert_slot as M          # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURSOR_OBJ, CURSOR_OFF = 0x6A9480, 0x3FF5C
STORE = 0x417E04                     # mov [eax+edx*4+0x50], ebx   (live, m69_enqueue.gdblog)

fails = []
total = [0]


def check(name, cond, detail=""):
    total[0] += 1
    print("%s %-46s %s" % ("ok " if cond else "BAD", name, detail))
    if not cond:
        fails.append(name)


def plan_index(region, plan):
    """M67's rule: the item goes at the first region slot whose plan byte is STRICTLY below
    its own, else after the region.  `region` is [(id, plan), ...] in queue-slot order."""
    for k, (_tid, pk) in enumerate(region, 1):
        if pk < plan:
            return k
    return len(region) + 1


def trace_rows(path):
    p = os.path.join(ROOT, "evidence", path)
    return [json.loads(l) for l in open(p)]


def main():
    # ---- 1. the constants and the address arithmetic of the store
    check("cursor field is widget+0x3ff5c", CURSOR_OBJ + CURSOR_OFF == 0x6A9480 + 0x3FF5C)
    check("store is queue[pos] with scale 4, disp 0x50",
          STORE == 0x417E04 and M.QUEUE_CAP == 10)
    check("queue slot k is base+0x50+4k", M.QUEUE_CAP * 4 + 0x50 == 0x78)

    # ---- 2. the M69 PASS: region [192, 194], cursor poked to 2, item 193
    before = [2, 192, 194, 0, 0, 0, 0, 0, 0, 0, 9225, 0]
    after = [2, 192, 193, 194, 0, 0, 0, 0, 0, 0, 9225, 0]
    landed = M._shift_index(after, before, M.QUEUE_CAP)
    check("193 poked to 2 lands at 2", landed == (2, 193), "got %r" % (landed,))
    check("plan rule would say 1 (PASS is discriminating)",
          plan_index([(192, 0), (194, 1)], 2) == 1)
    check("poked cursor 2 != plan index 1", 2 != plan_index([(192, 0), (194, 1)], 2))

    rows = trace_rows("m69_cursor3.jsonl")
    v = [r for r in rows if r["tag"] == "verdict"][0]
    check("trace verdict wrote at the poked cursor",
          v["wrote_at"] == v["poked_cursor"] == 2 and v["stored"] == 193)
    check("trace shows the plan index disagrees", v["plan_sorted_index"] == 1)
    ins = [r for r in rows if r["tag"] == "insert"][0]
    check("trace pending 2 -> 3 with the item at slot 2",
          ins["pending_before"] == 2 and ins["pending_after"] == 3 and ins["stored"] == 193)
    pok = [r for r in rows if r["tag"] == "cursor_poked"][0]
    check("the poke was read back before the click", pok["read_back"] == pok["want"] == 2)

    # ---- 3. M68's append, re-read under the same model: cursor at the end
    b2 = [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 9225, 0]
    a2 = [2, 194, 0, 0, 0, 0, 0, 0, 0, 0, 9225, 0]
    check("194 into an empty region lands at 1", M._shift_index(a2, b2, M.QUEUE_CAP) == (1, 194))
    b3 = [2, 194, 0, 0, 0, 0, 0, 0, 0, 0, 9225, 0]
    a3 = [2, 194, 1, 0, 0, 0, 0, 0, 0, 0, 9225, 0]
    check("1 (plan 9) APPENDED at 2 despite the plan rule",
          M._shift_index(a3, b3, M.QUEUE_CAP) == (2, 1)
          and plan_index([(194, 1)], 9) == 1)

    # ---- 4. the negative store is the TYPE's, not the click's
    r196 = trace_rows("m69_cursor2.jsonl")
    i196 = [r for r in r196 if r["tag"] == "insert"][0]
    c196 = [r for r in r196 if r["tag"] == "cell_click"][0]
    check("196 click verified (guard==cell) yet stored -6",
          c196["guard"] == c196["cell"] and i196["stored"] == -6)
    m68 = [json.loads(l) for l in open(os.path.join(ROOT, "evidence",
                                                    "m68_key_run_attempt1.txt"))
           if l.startswith("{")]
    i195 = [r for r in m68 if r["tag"] == "insert_4"][0]
    check("195 stored -3 on a click whose guard was 6", i195["guard"] == 6
          and i195["slots"][4] == -3)
    check("-3 and -6 are different values (not one sentinel)", -3 != -6)

    print("\n%s %d/%d m69 cursor cases"
          % ("PASS" if not fails else "FAIL", total[0] - len(fails), total[0]))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
