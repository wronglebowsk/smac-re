#!/usr/bin/env python3
"""M68: the INSERT key IDENTIFIER, pinned by cases.

`m68_key_run.py` scores a multi-INSERT sequence against EVERY single-byte key of the 52-byte
type record (52 offsets x descending/ascending x ties after/before = 208) plus the four
whole-name lexicographic rules = 212 candidate rules, and pays only if exactly ONE of them
explains every write.  These cases pin both halves of that instrument:

  * the identifier: for each shape, the EXACT set of candidate rules that explains the
    read-backs, and therefore the set of KEYS (byte offsets, or the name string) that does.
    The run pays on KEYS, not on rules: two conventions of ONE key is a PASS whose tie
    direction was not tested, while two different keys fitting is no claim at all.
    The three M67 read-backs are in here on purpose: they fit 11, 17 and 15 of the 212 rules
    across 4-6 different keys — M67 named `+42 desc after` but its two-item shapes could not
    tell it from the name bytes, which is exactly the gap M68 exists to close;
  * the shape gate: the predictions come from the BASELINE alone, and the run refuses a shape
    where a DIFFERENT KEY predicts the landing sequence it is testing (the empty region is
    that shape, and so is today's Korolev Center queue with two items, where three different
    bytes predict the same two slots).

Keys are the LIVE type records read off the box on 2026-10-26 (`scripts/m68_typebytes.py`,
`evidence/m68_typebytes.jsonl`): the 52 bytes of ids 0, 1, 2, 192, 193, 194, 195, verbatim.
Cost is byte +41 and plan byte +42; the name is the 34-byte string at +0.  The names are
DISPUTED (NAMED.md CONFLICT line: the M33-era table calls 193 Scout Rover and 195 Laser Squad)
— nothing here depends on which list is right, only on the bytes.

    python3 scripts/test_m68_key_rules.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m66_insert_slot as M  # noqa: E402

# the live 52-byte type records, verbatim from evidence/m68_typebytes.jsonl (2026-10-26)
HEX = {
    0: ("43 6f 6c 6f 6e 79 20 50 6f 64 00 00 00"
       "00 00 00 00 00 00 00 00 00 00 00 00 00"
       "00 00 00 00 00 00 00 00 00 00 00 0e 00"
       "01 00 03 08 28 00 ff ff 00 01 00 ff ff"),
    1: ("46 6f 72 6d 65 72 73 00 00 00 00 00 00"
       "00 00 00 00 00 00 00 00 00 00 00 00 00"
       "00 00 00 00 00 00 00 00 00 00 00 0f 00"
       "01 00 02 09 29 00 ff ff 00 01 00 06 00"),
    2: ("53 63 6f 75 74 20 50 61 74 72 6f 6c 00"
       "00 00 00 00 00 00 00 00 00 00 00 00 00"
       "00 00 00 00 00 00 00 00 00 00 00 00 00"
       "01 00 01 03 0a 00 ff ff 00 01 00 ff ff"),
    192: ("49 6d 70 61 63 74 20 53 71 75 61 64 00"
       "00 00 00 00 00 00 00 00 00 00 00 00 00"
       "00 00 00 00 00 00 00 00 00 00 00 02 00"
       "01 00 02 00 03 00 08 ff 00 01 00 00 00"),
    193: ("53 79 6e 74 68 6d 65 74 61 6c 20 47 61"
       "72 72 69 73 6f 6e 00 00 00 00 00 00 00"
       "00 00 00 00 00 00 00 00 00 00 00 00 01"
       "01 00 02 02 02 00 08 ff 00 01 00 00 00"),
    194: ("49 6d 70 61 63 74 20 49 6e 66 61 6e 74"
       "72 79 00 00 00 00 00 00 00 00 00 00 00"
       "00 00 00 00 00 00 00 00 00 00 00 02 01"
       "01 00 03 01 03 00 08 ff 00 01 00 00 00"),
    195: ("49 6d 70 61 63 74 20 42 61 74 74 65 72"
       "79 00 00 00 00 00 00 00 00 00 00 00 00"
       "00 00 00 00 00 00 00 80 00 00 00 02 00"
       "01 00 02 00 01 00 08 ff 00 41 00 00 00"),
}
REC = {tid: bytes.fromhex(h.replace(" ", "")) for tid, h in HEX.items()}
assert all(len(b) == 52 for b in REC.values()), "a pinned type record is not 52 bytes"
NAME_LEN = 34


def rec_bytes(tid):
    return REC.get(tid, b"\xff" * 52)


def rec_name(tid):
    return rec_bytes(tid)[:NAME_LEN].split(b"\0")[0].decode("latin-1", "replace")


def key_of(off):
    if off is None:
        return rec_name
    return lambda tid: rec_bytes(tid)[off]


SPECS = M.key_rule_specs()
RULE_KEY = {nm: off for nm, off, _d, _t in SPECS}
ITEMS = [2, 193, 194, 195, 1, 192]        # six ids: the shape the gate was designed on
ACCEPT_ITEMS = [2, 1, 194, 192, 193]      # the shape the run actually uses: 195 writes -3 (see
                                          # scripts/m68_cellprobe.py), and a poisoned queue entry
                                          # breaks the engine's own insert
EMPTY = [2] + [0] * 11                    # a fresh base's queue: head slot 2, empty region
KOR_TODAY = [2, 193, 193, 194, 195, 192, 192, 2, 0, 0, 545, 0]   # Korolev Center, pending 6


def sim(items, off, d, t, base, p):
    """the read-backs ONE rule produces when the items are inserted, in order, into `base`."""
    k = key_of(off)
    cur, pp, steps = list(base), p, []
    for it in items:
        i = M.key_insert_index(cur, pp, it, k, d, t)
        after = list(cur)
        after.insert(i, it)
        after = after[:M.QUEUE_CAP] + cur[M.QUEUE_CAP:]
        steps.append((list(cur), pp, after, pp + 1))
        cur, pp = after, pp + 1
    return steps


def fits(steps):
    return [nm for nm, off, d, t in SPECS if M.score_key_sequence(steps, key_of(off), d, t)]


def fit_keys(steps):
    """the verdict the run makes: the distinct KEYS (byte offsets, or None for the name string)
    that explain every write.  Two conventions of one key is a PASS with the tie direction
    untested; two keys is no claim."""
    return sorted({str(RULE_KEY[nm]) for nm in fits(steps)})


# (name, steps, the candidate rules that explain every write)
CASES = [
    # THE THREE M67 READ-BACKS (evidence/m67_sort_key{,_korolev,_accept}.jsonl, 2026-10-26).
    # They pin why M68 exists: the shape M67 paid on explains 11-17 of the 212 candidate
    # rules — the plan byte +42 desc/after is in every set, but so are the name bytes.
    ("m67_university_two_inserts",
     [([2, 194, 194, 193, 195, 192, 1, 0, 0, 0, 9225, 0], 6,
       [2, 193, 194, 194, 193, 195, 192, 1, 0, 0, 9225, 0], 7),
      ([2, 193, 194, 194, 193, 195, 192, 1, 0, 0, 9225, 0], 7,
       [2, 193, 194, 194, 193, 195, 192, 1, 192, 0, 9225, 0], 8)],
     ["1:desc:after", "3:desc:after", "4:desc:after", "5:asc:after", "6:desc:after",
      "8:asc:after", "15:desc:after", "16:desc:after", "17:desc:after", "18:desc:after",
      "42:desc:after"]),
    ("m67_korolev_two_inserts",
     [([2, 194, 195, 2, 0, 0, 0, 0, 0, 0, 545, 0], 2,
       [2, 193, 194, 195, 2, 0, 0, 0, 0, 0, 545, 0], 3),
      ([2, 193, 194, 195, 2, 0, 0, 0, 0, 0, 545, 0], 3,
       [2, 193, 194, 195, 192, 2, 0, 0, 0, 0, 545, 0], 4)],
     ["0:desc:after", "1:desc:after", "2:asc:after", "3:desc:after", "4:desc:after",
      "5:asc:after", "6:desc:after", "8:asc:after", "8:asc:before", "13:desc:before",
      "15:desc:after", "16:desc:after", "17:desc:after", "18:desc:after", "37:asc:after",
      "42:desc:after", "43:asc:after"]),
    ("m67_korolev_accept_two_inserts",
     [([2, 193, 194, 195, 192, 2, 0, 0, 0, 0, 545, 0], 4,
       [2, 193, 193, 194, 195, 192, 2, 0, 0, 0, 545, 0], 5),
      ([2, 193, 193, 194, 195, 192, 2, 0, 0, 0, 545, 0], 5,
       [2, 193, 193, 194, 195, 192, 192, 2, 0, 0, 545, 0], 6)],
     ["0:desc:after", "1:desc:after", "2:asc:after", "3:desc:after", "4:desc:after",
      "5:asc:after", "6:desc:after", "8:asc:after", "15:desc:after", "16:desc:after",
      "17:desc:after", "18:desc:after", "37:asc:after", "42:desc:after", "43:asc:after"]),
    # THE ACCEPTANCE SHAPE SIMULATED: six different ids into a fresh base's empty queue, in the
    # click order the run uses.  Each row is the read-backs ONE rule produces; the want-list is
    # what the identifier must return.  Twelve of these are UNIQUE — including the plan byte in
    # all four conventions and the cost byte in all four (so the acceptance shape separates
    # cost from plan from the tie direction in one run).
    ("produced_by_42_desc_after", sim(ITEMS, 42, "desc", "after", EMPTY, 0), ["42:desc:after"]),
    ("produced_by_42_desc_before", sim(ITEMS, 42, "desc", "before", EMPTY, 0), ["42:desc:before"]),
    ("produced_by_42_asc_after", sim(ITEMS, 42, "asc", "after", EMPTY, 0), ["42:asc:after"]),
    ("produced_by_42_asc_before", sim(ITEMS, 42, "asc", "before", EMPTY, 0), ["42:asc:before"]),
    ("produced_by_41_desc_after", sim(ITEMS, 41, "desc", "after", EMPTY, 0), ["41:desc:after"]),
    ("produced_by_41_desc_before", sim(ITEMS, 41, "desc", "before", EMPTY, 0), ["41:desc:before"]),
    ("produced_by_41_asc_after", sim(ITEMS, 41, "asc", "after", EMPTY, 0), ["41:asc:after"]),
    ("produced_by_41_asc_before", sim(ITEMS, 41, "asc", "before", EMPTY, 0), ["41:asc:before"]),
    # the two bytes that co-predicted with the plan byte on today's Korolev Center queue: on
    # the six-item shape each is the UNIQUE explanation of its own writes.
    ("produced_by_10_asc_after", sim(ITEMS, 10, "asc", "after", EMPTY, 0), ["10:asc:after"]),
    ("produced_by_13_asc_after", sim(ITEMS, 13, "asc", "after", EMPTY, 0), ["13:asc:after"]),
    # these co-predict on the acceptance shape and the test says so: +37 asc and +0 desc are
    # the same order over these six ids, and the name bytes +15..+18 are one order, and a
    # WHOLE-NAME comparison is indistinguishable from the byte +7 (which happens to rank these
    # six names exactly as the strings do).  A run whose writes matched these would print
    # "N rules fit" and FAIL rather than name one byte.
    ("produced_by_37_asc_after", sim(ITEMS, 37, "asc", "after", EMPTY, 0),
     ["0:desc:after", "37:asc:after"]),
    ("produced_by_0_desc_after", sim(ITEMS, 0, "desc", "after", EMPTY, 0),
     ["0:desc:after", "37:asc:after"]),
    ("produced_by_15_desc_after", sim(ITEMS, 15, "desc", "after", EMPTY, 0),
     ["15:desc:after", "16:desc:after", "17:desc:after", "18:desc:after"]),
    ("produced_by_name_str_desc", sim(ITEMS, None, "desc", "after", EMPTY, 0),
     ["7:desc:after", "7:desc:before", "name_str:desc:after", "name_str:desc:before"]),
    ("produced_by_name_str_asc", sim(ITEMS, None, "asc", "after", EMPTY, 0),
     ["7:asc:after", "7:asc:before", "name_str:asc:after", "name_str:asc:before"]),
    # THE ACCEPTANCE SHAPE (five ids: 195 is left out because at this base it writes -3 into
    # the queue — scripts/m68_cellprobe.py — and a queue entry with no type record breaks the
    # engine's own insert).  The plan byte's writes are explained by the plan byte ONLY (its
    # two descending conventions agree because nothing in this shape ties at plan, so the tie
    # direction is NOT tested here — M67 settled it in PR #65); the cost byte's writes are
    # explained by the cost byte only; and the name-side candidates each co-predict with other
    # bytes, which is why a run whose writes matched them prints "no key claim is made".
    ("accept_produced_by_42_desc", sim(ACCEPT_ITEMS, 42, "desc", "after", EMPTY, 0),
     ["42:desc:after", "42:desc:before"]),
    ("accept_produced_by_41_desc", sim(ACCEPT_ITEMS, 41, "desc", "after", EMPTY, 0),
     ["41:desc:after"]),
    ("accept_produced_by_1_desc", sim(ACCEPT_ITEMS, 1, "desc", "after", EMPTY, 0),
     ["1:desc:after"]),
    ("accept_produced_by_43_asc", sim(ACCEPT_ITEMS, 43, "asc", "after", EMPTY, 0),
     ["43:asc:after"]),
    ("accept_produced_by_0_desc", sim(ACCEPT_ITEMS, 0, "desc", "after", EMPTY, 0),
     ["0:desc:after", "37:asc:after"]),
    ("accept_produced_by_10_asc", sim(ACCEPT_ITEMS, 10, "asc", "after", EMPTY, 0),
     ["8:asc:after", "8:asc:before", "10:asc:after"]),
    ("accept_produced_by_15_desc", sim(ACCEPT_ITEMS, 15, "desc", "after", EMPTY, 0),
     ["15:desc:after", "16:desc:after", "17:desc:after", "18:desc:after"]),
    ("accept_produced_by_name_str", sim(ACCEPT_ITEMS, None, "desc", "after", EMPTY, 0),
     ["0:desc:before", "2:asc:before", "7:desc:after", "7:desc:before", "37:asc:before",
      "name_str:desc:after", "name_str:desc:before"]),
    # the plan byte's writes with the LAST write moved from region slot 6 to slot 3: no
    # convention predicts that, so the run must FAIL, not name a byte.
    ("no_rule_explains_it",
     sim(ITEMS[:5], 42, "desc", "after", EMPTY, 0)
     + [([2, 1, 2, 193, 194, 195, 0, 0, 0, 0, 545, 0], 5,
         [2, 1, 2, 192, 193, 194, 195, 0, 0, 0, 545, 0], 6)],
     []),
    # the acceptance shape's plan-descending writes with the last item (193, plan 2) written at
    # region slot 4 instead of slot 3: nothing predicts it.
    ("accept_no_rule_explains_it",
     sim(ACCEPT_ITEMS[:4], 42, "desc", "after", EMPTY, 0)
     + [([2, 1, 2, 194, 192, 0, 0, 0, 0, 0, 9225, 0], 4,
         [2, 1, 2, 194, 193, 192, 0, 0, 0, 0, 9225, 0], 5)],
     []),
]

# (name, baseline, pending, items, expected landing, the rules predicting THAT sequence,
#  number of distinct prediction sequences, size of the largest group)
GATE_CASES = [
    # (name, baseline, pending, items, expected landing, the rules predicting it, the KEYS
    #  predicting it, distinct prediction sequences, largest group)
    ("acceptance_shape", EMPTY, 0, ITEMS,
     [1, 2, 3, 4, 1, 6], ["42:desc:after"], ["42"], 76, 47),
    # THE SHAPE THE RUN USES: five ids, no 195.  Only the plan byte predicts its landing
    # sequence (its two descending conventions, because nothing ties at plan in this shape),
    # so the key gate passes; 12 of the 53 keys are decidable on it at all.
    ("run_acceptance_shape", EMPTY, 0, ACCEPT_ITEMS,
     [1, 1, 3, 4, 3], ["42:desc:after", "42:desc:before"], ["42"], 50, 57),
    # today's Korolev Center queue (pending 6) with the two items that fit there: three rules
    # predict the same pair of slots, so the gate REFUSES the shape and no claim is earned —
    # this is the measurement that says two inserts are not enough (evidence/m68_typebytes.jsonl)
    # three rules predict the same pair of slots and they read THREE different bytes, so the
    # gate refuses the shape and no claim is earned — this is the measurement that says two
    # inserts are not enough (evidence/m68_typebytes.jsonl)
    ("korolev_today_two_items", KOR_TODAY, 6, [1, 194],
     [1, 5], ["10:asc:after", "13:asc:after", "42:desc:after"], ["10", "13", "42"], 18, 65),
    ("empty_region_one_item", EMPTY, 0, [193], [1],
     [nm for nm, _o, _d, _t in SPECS],
     sorted({str(RULE_KEY[nm]) for nm, _o, _d, _t in SPECS}), 1, 212),
]


def main():
    fails = []
    if len(SPECS) != 212:
        print(f"BAD candidate set has {len(SPECS)} rules, want 212")
        fails.append("count")
    if len({nm for nm, _o, _d, _t in SPECS}) != 212:
        print("BAD candidate set has duplicate rule names")
        fails.append("names")
    for name, steps, want in CASES:
        got = fits(steps)
        ok = got == want
        print(f"{'ok ' if ok else 'BAD'} {name:30} fits={len(got):<3} want={len(want):<3} "
              f"keys={fit_keys(steps)}{'' if ok else ' GOT ' + str(got)}")
        if not ok:
            fails.append(name)
    for name, base, p, items, want_lands, want_same, want_keys, want_groups, want_largest \
            in GATE_CASES:
        preds = M.key_shape_predictions(base, p, items, key_of)
        lands, same, groups, largest, keys = M.key_shape_gate(preds, "42:desc:after")
        got_keys = sorted(str(k) for k in keys)
        ok = (list(lands) == want_lands and same == sorted(want_same)
              and got_keys == sorted(want_keys) and groups == want_groups
              and largest == want_largest)
        diff = "" if got_keys == sorted(want_keys) else f" GOT keys {got_keys[:8]}"
        print(f"{'ok ' if ok else 'BAD'} {name:28} lands={list(lands)} same={len(same)} "
              f"keys={got_keys} groups={groups} largest={largest}{diff}")
        if not ok:
            fails.append(name)
    # every rule must be EVALUATED on the acceptance shape (the run scores all 212)
    preds = M.key_shape_predictions(EMPTY, 0, ITEMS, key_of)
    if len(preds) != 212:
        print(f"BAD the shape gate evaluated {len(preds)} rules, want 212")
        fails.append("evaluated")
    if fails:
        print(f"\nFAIL: {len(fails)} bad case(s): {fails}")
        return 1
    print(f"\nPASS {len(CASES) + len(GATE_CASES) + 3}/"
          f"{len(CASES) + len(GATE_CASES) + 3} m68 key-identifier cases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
