#!/usr/bin/env python3
"""M68: READ-ONLY dump of the live type records, so the sort-key candidate set is
defined by measured bytes and not by a guess.

M67 settled that INSERT sorts by the type-record PLAN byte (+42) descending and refuted
the cost byte (+41), but it could NOT separate +42 from the other type-record bytes that
happen to rank its ids the same way (NAMED.md M67 block: "several name bytes
(+0,+1,+3,+4,+6,+15..+18), +37, and +43 read ASCENDING").  This script reads the whole
52-byte record for every id the chooser offers plus the ids sitting in the queues, so the
candidate byte set for the M68 run is written down from bytes before anything is clicked.

It also prints, for the baseline queue region of --base-name, for EACH byte offset which
of the four insert conventions (descending/ascending x ties after/before) would put a new
id in the SAME slot the plan-descending rule predicts: those offsets are the ones an
enqueue of that id cannot separate, and the ones it can.

Read-only: opens /proc/<pid>/mem, clicks nothing, pokes nothing.
"""
import argparse
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as sp  # noqa: E402
import m66_insert_slot as mi  # noqa: E402

TYPE_REC, TYPE_SZ = 0x98AD88, 52
NAME_LEN = 34  # NAMED.md M53f / production-queue.md: name at +0, 34 bytes


def rec(f, tid):
    b = sp.rd(f, TYPE_REC + tid * TYPE_SZ, TYPE_SZ)
    name = b[:NAME_LEN].split(b"\0")[0].decode("latin-1", "replace")
    return b, name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", default="0,1,2,192,193,194,195",
                    help="comma-separated type ids (the chooser ids plus the queue ids)")
    ap.add_argument("--base-name", default=None,
                    help="also dump this base's queue region and score every byte offset "
                         "against plan_desc_after for --item-a/--item-b")
    ap.add_argument("--item-a", type=int, default=1)
    ap.add_argument("--item-b", type=int, default=194)
    ap.add_argument("--out", default="evidence/m68_typebytes.jsonl")
    a = ap.parse_args()

    ids = [int(x) for x in a.ids.split(",") if x.strip() != ""]
    pid, f = sp.mem()
    rows = []

    def rec_row(tag, **kw):
        row = dict(tag=tag, **kw)
        rows.append(row)
        print(json.dumps(row), flush=True)

    recs = {}
    for tid in ids:
        b, name = rec(f, tid)
        recs[tid] = b
        rec_row("type_rec", id=tid, name=name, cost=b[41], plan=b[42],
                hex=b.hex(" "))

    if a.base_name:
        mine = sp.own_bases_named(f, 3)
        hits = [b for b in mine if b["name"] == a.base_name]
        if len(hits) != 1:
            print(f"FAIL: base {a.base_name!r} matched {len(hits)} of our bases: "
                  f"{[(b['idx'], b['name']) for b in mine]}")
            return 1
        old_slots = mi.SLOTS
        mi.SLOTS = 12
        r = mi.base_rec(f, hits[0]["idx"])
        mi.SLOTS = old_slots
        s, p = r["queue"], r["pending"]
        region = s[1:p + 1]
        rec_row("base", name=r["name"], idx=r["i"], pending=p, slots=s,
                minerals=r["minerals"], d0=r["d0"])
        rec_row("chooser_closed", cand=mi.cand(f)[:16])

        def byte_key(off):
            def k(tid):
                if tid not in recs:
                    return -1
                return recs[tid][off]
            return k

        involved = sorted(set([a.item_a, a.item_b] + region))
        for tid in involved:
            if tid not in recs:
                b, name = rec(f, tid)
                recs[tid] = b
        rec_row("co_order", base=r["name"], pending=p, region=region,
                item_a=a.item_a, item_b=a.item_b,
                bytes_by_pred={})
        # For each offset and convention, predict BOTH inserts from the baseline only.
        # pa = the slots after insert A under that rule (needed for insert B's prediction).
        table = {}
        for off in range(TYPE_SZ):
            key = byte_key(off)
            for direction in ("desc", "asc"):
                for tie in ("after", "before"):
                    ia = mi.key_insert_index(s, p, a.item_a, key, direction, tie)
                    sa = list(s)
                    sa.insert(ia, a.item_a)
                    sa = sa[:12]
                    ib = mi.key_insert_index(sa, p + 1, a.item_b, key, direction, tie)
                    table[f"{off}:{direction}:{tie}"] = [ia, ib]
        plan_a = mi.key_insert_index(s, p, a.item_a, byte_key(42), "desc", "after")
        sa = list(s)
        sa.insert(plan_a, a.item_a)
        sa = sa[:12]
        plan_b = mi.key_insert_index(sa, p + 1, a.item_b, byte_key(42), "desc", "after")
        same = {k: v for k, v in table.items() if v == [plan_a, plan_b]}
        rec_row("plan_desc_after_pred", item_a=a.item_a, item_b=a.item_b,
                pred=[plan_a, plan_b],
                co_ordering_rules=sorted(same),
                co_ordering_offsets=sorted({int(k.split(":")[0]) for k in same}),
                n_rules_total=len(table), n_co_ordering=len(same))
        with open(a.out, "w") as fh:
            fh.write("".join(json.dumps(r) + "\n" for r in rows))
        print(f"wrote {a.out} ({len(rows)} rows)")
    else:
        with open(a.out, "w") as fh:
            fh.write("".join(json.dumps(r) + "\n" for r in rows))
        print(f"wrote {a.out} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
