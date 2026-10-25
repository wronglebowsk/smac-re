#!/usr/bin/env python3
"""M54a: read a driver trace and print the acceptance numbers for one unattended run.

    python3 scripts/m54a_check_run.py evidence/trace_m54a_<ts>.jsonl [--timeout 150]

What it asserts (the milestone's second acceptance line):
  * every turn record advanced, and mission year moved by EXACTLY +1 per turn;
  * no STUCK turn ran longer than 2x the per-turn timeout;
  * the run wrote a header line carrying the seed + start state, and every turn record
    carries its action log (`handled`) and its before/after state delta.

Exit 0 = all of that holds. The file is read, never re-derived: this needs no game.
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
    oturns = sorted({t["turn"] for t in turns if t.get("orders_verified")})
    osecs = round(sum(t.get("order_seconds", 0) for t in turns), 1)
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
    panes = {k: v for k, v in hist.items() if k in ("vote-yea", "bar", "hive-bribe")}
    maxdt = max((t.get("dt", 0) for t in turns), default=0)

    print(f"advanced   {len(adv)}/{len(turns)}   year deltas {deltas}")
    print(f"stuck      {len(stuck)} (turns {[t['turn'] for t in stuck]})  "
          f"max dt {maxdt}s  over 2x{a.timeout}s: {over}")
    print(f"pane hits  {panes or '{}'}")
    print(f"actions    {json.dumps(hist, sort_keys=True)}")
    print(f"orders     {len(orders)} VERIFIED of {len(attempts)} attempted, on turns "
          f"{oturns}, {osecs}s spent ordering")
    if orders:
        keys = {}
        for o in orders:
            keys[f"{o['key']}->byte{o['order_after']}"] = keys.get(f"{o['key']}->byte{o['order_after']}", 0) + 1
        print(f"order mix  {json.dumps(keys, sort_keys=True)}  "
              f"energy spent {sum(o.get('energy_delta', 0) for o in orders)}")
    print(f"end        {json.dumps(turns[-1].get('state_after'), sort_keys=True)}")

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
    if fails:
        print("FAIL " + "; ".join(fails))
        return 1
    print(f"PASS {len(adv)} turns advanced, year +1 each, no STUCK over "
          f"{2 * a.timeout:.0f}s, per-turn state deltas present"
          + (f", {len(orders)} verified orders" if a.min_orders else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
