#!/usr/bin/env python3
"""M67: the INSERT sort-KEY scorer, pinned by cases.

`m66_insert_slot.py --rules sort_key` decides WHICH type-record byte the BUILD UI's INSERT
sorts the queue by.  Eight rules share the insert machinery and differ only in the key byte
(cost +41 / plan +42) and the convention (descending/ascending x ties after/before); the run
pays only if the shape makes them predict DIFFERENT slots.  These cases pin both halves:

  * the scorer: each rule must be the ONLY one that explains a shape it produced, a shape no
    rule explains must select none (so the run FAILs instead of claiming a key), and every rule
    must be reachable;
  * the shape gate: the predictions are computed from the BASELINE alone, and a shape whose
    eight predictions all land in one slot earns nothing (the empty region is that shape).

Keys are the live type-record bytes read off the box (cost via m58_price.py's byte +41, plan
+42, the alpha Plan column): 194 Impact Infantry 3/1, 193 Synthmetal Garrison 2/2, 195 Impact
Battery 2/0, 192 Impact Squad 2/0, 1 Formers 2/9, 2 Scout Patrol 1/3, 0 Colony Pod 3/8.  Cost
and plan ORDER DIFFERENTLY here — 193 is cost-2/plan-2 while 195 and 192 are cost-2/plan-0 —
which is what makes a cost-vs-plan run possible at all.

    python3 scripts/test_m67_sort_keys.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m66_insert_slot as M  # noqa: E402

COST = {0: 3, 1: 2, 2: 1, 192: 2, 193: 2, 194: 3, 195: 2}
PLAN = {0: 8, 1: 9, 2: 3, 192: 0, 193: 2, 194: 1, 195: 0}
# the window has to be WIDER than the 10-slot queue array or the capped shift is invisible
# (the scorer sees no slot past the array and cannot tell capped from uncapped)
Z = [0] * 12


def rec_byte(tid, off):
    src = COST if off == M.COST_OFF else PLAN
    return src.get(tid, 0)


# (name, pending_before, baseline, after A, pa, after B, pb, rules that fit)
CASES = [
    # each shape below is what ONE rule produces when it inserts A then B into the baseline;
    # only that rule explains both read-backs, so the scorer would name it and nothing else.
    ("cost_desc_after", 1, [2, 194] + Z[2:], [2, 194, 193] + Z[3:], 2,
     [2, 194, 193, 195] + Z[4:], 3, ["cost_desc_after"]),
    ("cost_desc_before", 1, [2, 194] + Z[2:], [2, 194, 193] + Z[3:], 2,
     [2, 194, 195, 193] + Z[4:], 3, ["cost_desc_before"]),
    ("cost_asc_after", 1, [2, 194] + Z[2:], [2, 193, 194] + Z[3:], 2,
     [2, 193, 195, 194] + Z[4:], 3, ["cost_asc_after"]),
    ("cost_asc_before", 1, [2, 194] + Z[2:], [2, 193, 194] + Z[3:], 2,
     [2, 195, 193, 194] + Z[4:], 3, ["cost_asc_before"]),
    ("plan_desc_after", 1, [2, 195] + Z[2:], [2, 193, 195] + Z[3:], 2,
     [2, 193, 195, 192] + Z[4:], 3, ["plan_desc_after"]),
    ("plan_desc_before", 1, [2, 193] + Z[2:], [2, 193, 195] + Z[3:], 2,
     [2, 193, 192, 195] + Z[4:], 3, ["plan_desc_before"]),
    ("plan_asc_after", 1, [2, 193] + Z[2:], [2, 195, 193] + Z[3:], 2,
     [2, 195, 192, 193] + Z[4:], 3, ["plan_asc_after"]),
    ("plan_asc_before", 1, [2, 195] + Z[2:], [2, 195, 193] + Z[3:], 2,
     [2, 192, 195, 193] + Z[4:], 3, ["plan_asc_before"]),
    # 195 (cost 2, plan 0) landed IN FRONT of a cost-3 entry and B landed behind everything:
    # no key/direction/tie combination predicts that pair, so the run must FAIL, not guess.
    ("no_rule_explains_it", 2, [2, 194, 193] + Z[3:], [2, 195, 194, 193] + Z[4:], 3,
     [2, 195, 194, 193, 192] + Z[3:], 4, []),
    # THE MEASURED UNIVERSITY READ-BACKS (evidence/m67_sort_key.jsonl, 2026-10-26 21:55):
    # pending 6 -> 7 -> 8, INSERT 193 landed at region slot 1 AHEAD of two cost-3 entries,
    # INSERT 192 landed at the end.  The window is 12 wide and slot 10 holds 9225 — a field
    # past the queue array that did NOT move while slots 1..8 shifted, which is what proves the
    # shift is capped to the 10-slot queue array.  Exactly one rule explains both writes: the
    # plan byte descending, ties after.  (Under an uncapped shift these same arrays explain
    # NOTHING, which is how the first run of this instrument FAILED.)
    ("measured_university_insert193_then192", 6,
     [2, 194, 194, 193, 195, 192, 1, 0, 0, 0, 9225, 0],
     [2, 193, 194, 194, 193, 195, 192, 1, 0, 0, 9225, 0], 7,
     [2, 193, 194, 194, 193, 195, 192, 1, 192, 0, 9225, 0], 8,
     ["plan_desc_after"]),
    # THE MEASURED KOROLEV READ-BACKS (evidence/m67_sort_key_korolev.jsonl, 22:00): pending 2
    # -> 3 -> 4.  This is the shape that separates the capped shift from a region-bounded one:
    # the queue tail held a STALE id 2 at slot 3, and INSERT pushed it along to slot 4 and then
    # to slot 5 instead of overwriting it, while the dword at slot 10 (545) never moved.  Same
    # verdict: the plan byte descending, ties after — 193 (plan 2) went IN FRONT of 194 (plan 1)
    # and 192 (plan 0) went behind 195 (plan 0), ties staying ahead.
    ("measured_korolev_insert193_then192", 2,
     [2, 194, 195, 2, 0, 0, 0, 0, 0, 0, 545, 0],
     [2, 193, 194, 195, 2, 0, 0, 0, 0, 0, 545, 0], 3,
     [2, 193, 194, 195, 192, 2, 0, 0, 0, 0, 545, 0], 4,
     ["plan_desc_after"]),
]

# The acceptance shape, pinned from the box's University Base queue at pending 6 (read before
# any click): region [194, 194, 193, 195, 192, 1].  INSERT 193 (cost 2 / plan 2) must land in
# four DIFFERENT slots depending on the key, so this shape discriminates; the empty region does
# not.  (name, pending, baseline, item, {rule: predicted slot})
SHAPE_CASES = [
    ("university_pending6_insert193", 6, [2, 194, 194, 193, 195, 192, 1], 193,
     {"cost_desc_after": 7, "cost_desc_before": 3, "cost_asc_after": 1,
      "cost_asc_before": 1, "plan_desc_after": 1, "plan_desc_before": 1,
      "plan_asc_after": 6, "plan_asc_before": 3}),
    ("empty_region_insert193", 0, [2] + Z[1:], 193,
     {nm: 1 for nm, _off, _d, _t in M.KEY_RULES_SPEC}),
    # a cost-3 item into a queue whose region is all cost 2: every cost rule says slot 1 and
    # every plan rule says something else (2, 2, 1, 1) — the shape the M66 run used, re-checked
    # here as a shape that discriminates cost from plan (it cannot separate the tie direction).
    ("cost3_into_cost2_run", 3, [2, 193, 195, 192] + Z[4:], 194,
     {"cost_desc_after": 1, "cost_desc_before": 1, "cost_asc_after": 4,
      "cost_asc_before": 4, "plan_desc_after": 2, "plan_desc_before": 2,
      "plan_asc_after": 1, "plan_asc_before": 1}),
    # THE ACCEPTANCE SHAPE: Korolev Center's queue (pending 2, region [194 Impact Infantry
    # cost 3/plan 1, 195 Impact Battery cost 2/plan 0]) with INSERT 193 (cost 2/plan 2).  Cost
    # order says slot 3, plan-descending says slot 1, ascending-plan says 3 but the tie rules
    # split them three ways — three distinct slots, so the shape discriminates, and the second
    # insert (192, cost 2/plan 0) separates the four rules that agree on slot 1.
    ("korolev_pending2_insert193", 2, [2, 194, 195] + Z[3:], 193,
     {"cost_desc_after": 3, "cost_desc_before": 2, "cost_asc_after": 1,
      "cost_asc_before": 1, "plan_desc_after": 1, "plan_desc_before": 1,
      "plan_asc_after": 3, "plan_asc_before": 3}),
]


def main():
    fails = []
    for name, p0, s, a, pa, b, pb, want in CASES:
        ctx = dict(s=s, p0=p0, a=a, pa=pa, b=b, pb=pb,
                   cost=lambda t, C=COST: C.get(t, 0), rec_byte=rec_byte)
        got = [rule for rule, fn in M.SORT_KEY_RULES if fn(ctx)]
        ok = got == want
        print(f"{'ok ' if ok else 'BAD'} {name:22} matched={got} want={want}")
        if not ok:
            fails.append(name)
    reachable = {r for *_x, want in CASES for r in want}
    for rule, _fn in M.SORT_KEY_RULES:
        if rule not in reachable:
            print(f"BAD {rule}: no case produces it")
            fails.append(rule + "-unreachable")

    for name, p0, s, item, want in SHAPE_CASES:
        got = {}
        for nm, off, direction, tie in M.KEY_RULES_SPEC:
            kv = {t: rec_byte(t, off) for t in set(list(s[:p0 + 1]) + [item])}
            got[nm] = M.key_insert_index(s, p0, item, lambda t, kv=kv: kv[t],
                                         direction, tie)
        distinct = sorted(set(got.values()))
        ok = got == want
        print(f"{'ok ' if ok else 'BAD'} {name:28} predictions={got} "
              f"distinct={distinct} gate={'pass' if len(distinct) > 1 else 'FAIL'}")
        if not ok:
            fails.append(name)
        if (len(distinct) > 1) != (len(sorted(set(want.values()))) > 1):
            fails.append(name + "-gate")
    if fails:
        print(f"FAILED: {len(fails)} — {', '.join(fails)}")
        return 1
    print(f"PASS {len(CASES) + len(SHAPE_CASES)}/{len(CASES) + len(SHAPE_CASES)} "
          f"m67 sort-key cases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
