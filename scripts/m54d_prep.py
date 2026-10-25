#!/usr/bin/env python3
"""M54d: make the position the milestone needs, and print the census line.

MEASURED, not assumed: the fresh game this harness can start contains ZERO class-9 records
anywhere — `scripts/m54d_census.py` on a 2101 fresh game prints `units_ours=2 class9=0`,
a Colony Pod (type 0, class 8) and a Scout Patrol (type 2, class 3) both standing on the
faction's single base — and the base's own starting queue produces Scout Patrols
("University Base builds ScoutPatrol", `evidence/m54d/base_pane.png`). Formers come from
production, which is S1. So the class-9 position is MADE here, by a documented poke of one
record: type 2 -> 1 (Formers, class 9, the class the game reads at DAT_0098adb2[type*52]),
one tile off our own base (the case `g` will queue a MOVE for — M54c proved it refuses a
unit ON its base), order cleared and movement unspent.

Everything the milestone then claims is the game's own: the keypress, the chooser, the
`+17` byte, the leg-array route, and the walk after the year flips.

    python3 scripts/m54d_prep.py [--unit N] [--json out.json]
"""
import argparse, json, os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P
import m54d_census as C


def poke(f, idx, off, val, n):
    P.wr(f, P.UNIT_ARR + idx * 52 + off, struct.pack("<" + {1: "B", 2: "h", 4: "i"}[n], val))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit", type=int, default=None, help="record to convert (default: first)")
    ap.add_argument("--dx", type=int, default=1)
    ap.add_argument("--dy", type=int, default=0)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    pid, f = P.mem()
    st = P.state()
    me = st["player"]
    bases = [b for b in C.base_rows(f) if b["faction"] == me]
    if not bases:
        print("no base of ours — cannot make an off-base Former")
        return 1
    bx, by = bases[0]["x"], bases[0]["y"]
    rows = [u for u in C.unit_rows(f) if u["owner"] == me and (u["x"], u["y"]) == (bx, by)]
    if not rows:
        print("no unit of ours standing on our base")
        return 1
    cand = next((u for u in rows if a.unit is None or u["idx"] == a.unit), rows[0])
    nx, ny = bx + a.dx, by + a.dy
    poke(f, cand["idx"], 10, 1, 2)        # +10 type -> 1 = Formers (class 9)
    poke(f, cand["idx"], 0, nx, 2)        # +0  x, one tile off the base
    poke(f, cand["idx"], 2, ny, 2)        # +2  y
    poke(f, cand["idx"], 17, 0, 1)        # +17 order -> none (clear the sticky sentry)
    poke(f, cand["idx"], 40, 0, 1)        # +40 movement unspent
    after = P.unit_rec(f, cand["idx"])
    print(f"POKE rec{cand['idx']}: type {cand['type']}(cls {cand['cls']}) -> 1 (cls "
          f"{P.unit_class(f, 1)}) at ({bx},{by}) -> ({nx},{ny}), order 0, mp 0")
    print(f"     record now: {after}")
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(dict(state=st, unit=cand["idx"],
                           after={k: v for k, v in after.items() if k != "raw"},
                           base=(bx, by)), fh)
    return 0


if __name__ == "__main__":
    sys.exit(main())
