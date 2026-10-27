#!/usr/bin/env python3
"""M66: the INSERT-layout scorer, pinned by cases before any live run scores them.

`m66_insert_slot.py` decides which queue slot the BUILD UI's INSERT writes by asking which
of five transformation rules explains the two read-backs (baseline -> after INSERT A -> after
INSERT B), with the stored item id as a free variable.  These cases pin that scorer: each
layout must select ITSELF and not the others, an observation no rule explains must select
none (the run then FAILs rather than claiming a layout), and the real session-106 read-backs
must select exactly one rule.

    python3 scripts/test_m66_layouts.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m66_insert_slot as M  # noqa: E402

Z = [0] * 8

# (name, baseline slots, after A, after B, pending after A, rules that must match)
CASES = [
    ("rule1_korolev_measured", [2, 2] + Z[:6], [2, 194, 2, 0, 0, 0, 0, 0],
     [2, 194, 195, 2, 0, 0, 0, 0], 1, ["insert_at_new_pending_index"]),
    ("rule1_clean_tail", [2] + Z[:7], [2, 193, 0, 0, 0, 0, 0, 0],
     [2, 193, 195, 0, 0, 0, 0, 0], 1, ["insert_at_new_pending_index"]),
    ("rule1_stale_tail", [2, 2, 2] + Z[:5], [2, 193, 2, 2, 0, 0, 0, 0],
     [2, 193, 195, 2, 2, 0, 0, 0], 1, ["insert_at_new_pending_index"]),
    ("rule1_nonzero_pending", [2, 194, 195, 2] + Z[:4], [2, 194, 195, 196, 2, 0, 0, 0],
     [2, 194, 195, 196, 197, 2, 0, 0], 3, ["insert_at_new_pending_index"]),
    ("rule2_head_overwrite", [2] + Z[:7], [193, 0, 0, 0, 0, 0, 0, 0],
     [193, 195, 0, 0, 0, 0, 0, 0], 1, ["append_at_pending_before_index"]),
    ("rule3_head_and_next", [2] + Z[:7], [193, 193, 0, 0, 0, 0, 0, 0],
     [195, 195, 0, 0, 0, 0, 0, 0], 1, ["write_head_and_next_slot"]),
    ("rule4_head_and_shift", [2] + Z[:7], [193, 2, 0, 0, 0, 0, 0, 0],
     [195, 193, 2, 0, 0, 0, 0, 0], 1, ["write_head_and_shift_right"]),
    ("rule5_eight_byte_entry", [2] + Z[:7], [193, 7, 0, 0, 0, 0, 0, 0],
     [193, 7, 195, 9, 0, 0, 0, 0], 1, ["eight_byte_entries"]),
    # the same-id-tail shape the OLD single-item enqueue produced: every slot held 2, so no
    # rule can identify the written index — that is why two DIFFERENT ids were needed.
    ("single_id_is_unidentifiable", [2, 2] + Z[:6], [2, 2, 2, 0, 0, 0, 0, 0],
     [2, 2, 2, 2, 0, 0, 0, 0], 1, []),
    # nothing moved: pending rose but the slots did not, so no layout may be claimed.
    ("no_slot_moved", [2] + Z[:7], [2, 0, 0, 0, 0, 0, 0, 0],
     [2, 0, 0, 0, 0, 0, 0, 0], 1, []),
]


def main():
    fails = []
    for name, s, a, b, pa, want in CASES:
        got = []
        for rule, fn in M.PREDICTIONS:
            ids = fn(s, pa, a, pa + 1, b)
            if ids:
                got.append(rule)
        ok = got == want
        print(f"{'ok ' if ok else 'BAD'} {name:26} matched={got} want={want}")
        if not ok:
            fails.append(name)
    # every rule must be reachable, or the scorer is not a discriminator
    reachable = {r for _, _, _, _, _, want in CASES for r in want}
    missing = [r for r, _ in M.PREDICTIONS if r not in reachable]
    for r in missing:
        print(f"BAD {r}: no case produces it")
        fails.append(r + "-unreachable")
    if fails:
        print(f"FAILED: {len(fails)} — {', '.join(fails)}")
        return 1
    print(f"PASS {len(CASES)}/{len(CASES)} m66-layout cases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
