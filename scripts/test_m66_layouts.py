#!/usr/bin/env python3
"""M66: the INSERT-layout scorer, pinned by cases — including the three runs the box gave us.

`m66_insert_slot.py` decides which queue slot the BUILD UI's INSERT writes by asking which of
six rules explains the two read-backs (baseline -> after INSERT A -> after INSERT B), with the
stored item id as a free variable and the cost read live from the type record (+41).  These
cases pin the scorer: each shape must select the rules that can explain it and no others; a
shape no rule explains must select none, so the run FAILs instead of claiming a layout.

Three cases are the measured session-106 read-backs (their traces are cited in SESSION_NOTES):
Korolev at pending 0 and University at pending 0 cannot separate "insert at the new pending
index" from "insert by descending cost" (an empty region makes them identical); the University
run at pending 2 can, and it is the one that refutes the pending-index rule.

    python3 scripts/test_m66_layouts.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m66_insert_slot as M  # noqa: E402

# type-record cost byte (+41) as read live off the box (m58_price.py reads the same byte);
# 7 and 9 are synthetic filler ids used by the eight-byte-entry case.
COST = {0: 3, 1: 2, 2: 1, 192: 2, 193: 2, 194: 3, 195: 2, 7: 2, 9: 2}
Z = [0] * 8

# (name, pending_before, baseline, after A, pending after A, after B, pending after B, rules)
CASES = [
    ("measured_korolev_pending0", 0, [2, 2] + Z[:6], [2, 194, 2] + Z[:5], 1,
     [2, 194, 195, 2] + Z[:4], 2,
     ["sorted_descending_cost", "insert_at_new_pending_index"]),
    ("measured_university_pending0", 0, [2] + Z[:7], [2, 193] + Z[:6], 1,
     [2, 193, 195] + Z[:5], 2,
     ["sorted_descending_cost", "insert_at_new_pending_index"]),
    ("measured_university_pending2", 2, [2, 193, 195] + Z[:5], [2, 194, 193, 195] + Z[:4], 3,
     [2, 194, 193, 195, 192] + Z[:3], 4, ["sorted_descending_cost"]),
    ("cost3_item_into_a_cost2_run", 4, [2, 194, 193, 195, 192] + Z[:3],
     [2, 194, 194, 193, 195, 192] + Z[:2], 5, [2, 194, 194, 193, 195, 192, 1] + Z[:1], 6,
     ["sorted_descending_cost"]),
    ("head_overwrite_nothing_moves", 0, [2] + Z[:7], [193] + Z[:7], 1,
     [193, 195] + Z[:6], 2, ["append_at_pending_before_index"]),
    ("head_and_next_slot_same_id", 0, [2] + Z[:7], [193, 193] + Z[:6], 1,
     [195, 195] + Z[:6], 2, ["write_head_and_next_slot"]),
    ("head_then_everything_shifts", 0, [2] + Z[:7], [193, 2] + Z[:6], 1,
     [195, 193, 2] + Z[:5], 2, ["write_head_and_shift_right"]),
    ("entry_is_8_bytes_wide", 0, [2] + Z[:7], [193, 7] + Z[:6], 1,
     [193, 7, 195, 9] + Z[:4], 2, ["eight_byte_entries"]),
    ("no_slot_moved", 0, [2] + Z[:7], [2] + Z[:7], 1, [2] + Z[:7], 2, []),
    # the shape the OLD single-item enqueue produced (every slot 2): two different rules explain
    # it, so it says nothing about WHERE the item went — which is why the instrument refuses to
    # enqueue an id the queue already holds twice.
    ("single_id_stale_tail_shape", 1, [2, 2] + Z[:6], [2, 2, 2] + Z[:5], 2,
     [2, 2, 2, 2] + Z[:4], 3,
     ["sorted_descending_cost", "insert_at_new_pending_index"]),
]


def main():
    fails = []
    for name, p0, s, a, pa, b, pb, want in CASES:
        ctx = dict(s=s, p0=p0, a=a, pa=pa, b=b, pb=pb, cost=lambda t, C=COST: C.get(t, 0))
        got = [rule for rule, fn in M.PREDICTIONS if fn(ctx)]
        ok = got == want
        print(f"{'ok ' if ok else 'BAD'} {name:30} matched={got} want={want}")
        if not ok:
            fails.append(name)
    reachable = {r for _, _, _, _, _, _, _, want in CASES for r in want}
    for rule, _ in M.PREDICTIONS:
        if rule not in reachable:
            print(f"BAD {rule}: no case produces it")
            fails.append(rule + "-unreachable")
    if fails:
        print(f"FAILED: {len(fails)} — {', '.join(fails)}")
        return 1
    print(f"PASS {len(CASES)}/{len(CASES)} m66-layout cases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
