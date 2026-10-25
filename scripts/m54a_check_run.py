#!/usr/bin/env python3
"""M54a: read a driver trace and print the acceptance numbers for one unattended run.

    python3 scripts/m54a_check_run.py evidence/trace_m54a_<ts>.jsonl [--timeout 150]

What it asserts (the milestone's second acceptance line):
  * every turn record advanced, and mission year moved by EXACTLY +1 per turn;
  * no STUCK turn ran longer than 2x the per-turn timeout;
  * the run wrote a header line carrying the seed + start state, and every turn record
    carries its action log (`handled`) and its before/after state delta.

M54c added `--min-orders` (orders whose `+17` delta the memory confirmed) and M54d added
`--min-moves` (orders whose unit then WALKED: after the year flips the record sits on the
tile its own leg array named, with `+40` movement spent). Both read what the trace says —
the trace is written from memory, so this still needs no game.
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trace")
    ap.add_argument("--timeout", type=float, default=150.0)
    ap.add_argument("--expect", type=int, default=0,
                    help="assert at least this many advanced turns (0 = header's turns)")
    ap.add_argument("--min-orders", type=int, default=0, dest="min_orders",
                    help="S3/M54c: assert at least this many VERIFIED orders (records "
                         "carrying the memory-confirmed byte delta) in the run")
    ap.add_argument("--min-our-bases", type=int, default=0, dest="min_our_bases",
                    help="floor on OUR bases at the end of the run (M54f: a run that loses "
                         "the position must not print PASS)")
    ap.add_argument("--min-moves", type=int, default=0, dest="min_moves",
                    help="S3/M54d: assert at least this many VERIFIED WALKS — an order "
                         "whose unit, after the year flipped, sits on the destination its "
                         "own leg array named with movement spent at +40")
    ap.add_argument("--min-own-base-arrivals", type=int, default=0,
                    dest="min_own_base_arrivals",
                    help="M54i: assert at least this many LANDED walks end on a tile "
                         "holding one of OUR bases and NOT on the tile the unit started "
                         "from (the destination is the leg array of the record the "
                         "keypress changed — see diff_order_records)")
    a = ap.parse_args()

    path = a.trace if os.path.isabs(a.trace) else os.path.join(ROOT, a.trace)
    lines = [json.loads(l) for l in open(path) if l.strip()]
    if not lines:
        sys.exit("empty trace")
    hdr = lines[0] if lines[0].get("type") == "start" else None
    turns = [l for l in lines if l.get("type") != "start"]
    if hdr is None:
        print("FAIL no run header line (seed + start state)")
        return 1
    want = a.expect or hdr.get("turns") or len(turns)

    print(f"trace      {os.path.basename(path)}")
    print(f"seed       {hdr.get('seed')}  argv {' '.join(hdr.get('argv', []))}")
    print(f"start      {json.dumps(hdr.get('state'), sort_keys=True)}")
    print(f"turns      {len(turns)} records, header asked for {hdr.get('turns')}")

    adv = [t for t in turns if t.get("advanced")]
    stuck = [t for t in turns if t.get("stuck")]
    attempts = [o for t in turns for o in t.get("orders", [])]
    orders = [o for o in attempts if o.get("verified")]
    mv_attempts = [m for t in turns for m in t.get("moves", [])]
    moves = [m for m in mv_attempts if m.get("landed")]
    own_arrivals = [m for m in moves if m.get("dest_is_own_base")
                    and list(m.get("frm")) != list(m.get("dest"))]
    oturns = sorted({t["turn"] for t in turns if t.get("orders_verified")})
    msec = round(sum(t.get("move_seconds", 0) for t in turns), 1)
    deltas = {}
    for t in turns:
        d = (t.get("year_after") or 0) - (t.get("year_before") or 0)
        deltas[d] = deltas.get(d, 0) + 1
    bad_year = [t["turn"] for t in turns if (t["year_after"] - t["year_before"]) != 1]
    over = [t["turn"] for t in stuck if t.get("dt", 0) > 2 * a.timeout]
    missing = [t["turn"] for t in turns
               if "handled" not in t or "state_after" not in t or "delta" not in t]

    hist = {}
    for t in turns:
        for k in t.get("handled", []):
            base = k.split("@")[0].split(":")[0]
            hist[base] = hist.get(base, 0) + 1
    panes = {k: v for k, v in hist.items() if k in ("vote-yea", "bar", "hive-bribe",
                                                    "dest-chooser-ok")}
    maxdt = max((t.get("dt", 0) for t in turns), default=0)

    print(f"advanced   {len(adv)}/{len(turns)}   year deltas {deltas}")
    print(f"stuck      {len(stuck)} (turns {[t['turn'] for t in stuck]})  "
          f"max dt {maxdt}s  over 2x{a.timeout}s: {over}")
    print(f"pane hits  {panes or '{}'}")
    print(f"actions    {json.dumps(hist, sort_keys=True)}")
    osecs = round(sum(t.get("order_seconds", 0) for t in turns), 1)
    print(f"orders     {len(orders)} VERIFIED of {len(attempts)} attempted, on turns "
          f"{oturns}, {osecs}s spent ordering")
    if orders:
        keys = {}
        for o in orders:
            # M54g: the colonist founding writes NO order byte — its proof is the base
            # array — so label that entry by what it did instead of by a byte.
            lbl = "founded" if o.get("label") == "found-base" else f"byte{o.get('order_after')}"
            k = f"{o['key']}->{lbl}"
            keys[k] = keys.get(k, 0) + 1
        print(f"order mix  {json.dumps(keys, sort_keys=True)}  "
              f"energy spent {sum(o.get('energy_delta', 0) for o in orders)}")
    print(f"moves      {len(moves)} LANDED of {len(mv_attempts)} ordered walks "
          f"(record on the tile its own leg named, +40 movement spent)"
          + (f", on turns {sorted({t['turn'] for t in turns if t.get('moves_verified')})}"
             if moves else ""))
    if moves:
        detail = "; ".join("t%s->%s mp+%s" % (m["frm"], m["dest"], m["mp_after"])
                           for m in moves[:6])
        print(f"           {detail}   ({msec}s of move checks)")
    if a.min_own_base_arrivals or own_arrivals:
        print(f"           {len(own_arrivals)} landed on a tile holding ONE OF OUR BASES "
              f"and not the unit's start tile"
              + (f" (floor {a.min_own_base_arrivals})" if a.min_own_base_arrivals else ""))
    print(f"end        {json.dumps(turns[-1].get('state_after'), sort_keys=True)}")
    end_state = turns[-1].get("state_after") or {}
    ours, our_units = end_state.get("bases_ours"), end_state.get("units_ours")
    print(f"ours       bases_ours {ours}  units_ours {our_units}"
          + (f"   floor {a.min_our_bases}" if a.min_our_bases
             else "   (no floor: --min-our-bases catches a defeat)"))

    fails = []
    if len(adv) < want:
        fails.append(f"only {len(adv)} of {want} turns advanced")
    if bad_year:
        fails.append(f"year did not move +1 on turns {bad_year[:8]}")
    if over:
        fails.append(f"STUCK longer than 2x timeout on turns {over}")
    if missing:
        fails.append(f"records without action log / state delta: {missing[:8]}")
    if len(orders) < a.min_orders:
        fails.append(f"only {len(orders)} VERIFIED orders, milestone wants {a.min_orders}")
    if len(moves) < a.min_moves:
        fails.append(f"only {len(moves)} VERIFIED walks, milestone wants {a.min_moves}")
    if len(own_arrivals) < a.min_own_base_arrivals:
        fails.append(f"only {len(own_arrivals)} walks LANDED ON OUR OWN BASE (not the "
                     f"start tile), milestone wants {a.min_own_base_arrivals}")
    if a.min_our_bases and (not isinstance(ours, int) or ours < a.min_our_bases):
        fails.append(f"our faction holds {ours} bases at the end, floor is {a.min_our_bases}")
    if fails:
        print("FAIL " + "; ".join(fails))
        return 1
    print(f"PASS {len(adv)} turns advanced, year +1 each, no STUCK over "
          f"{2 * a.timeout:.0f}s, per-turn state deltas present"
          + (f", {len(orders)} verified orders" if a.min_orders else "")
          + (f", {len(moves)} verified walks" if a.min_moves else "")
          + (f", {len(own_arrivals)} onto our own base" if a.min_own_base_arrivals else "")
          + (f", we still hold {ours} bases" if a.min_our_bases else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
