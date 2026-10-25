#!/usr/bin/env python3
"""M54e: make the position a WALK can actually LAND in, then print the census line.

M54d's prep stood the made Former at (base+1, base) and M54d's walk never arrived. Two
reasons, both measured on this build with `scripts/m54e_probe.py` (2026-10-25):

1. THE GAME WILL NOT PATH INTO A TILE OUR OWN UNITS OCCUPY. With four of ours on
   University Base (6,12) the walker oscillated (6,13)<->(7,12) across three TURN
   COMPLETEs and never arrived; the same order landed the instant the base tile was
   emptied. `g` can only ever name a BASE tile as its destination (`FUN_004d6fb0`: the
   0x18 branch copies `base[piVar21].x/y` into `+20/+28`), so a walk needs our own base
   tile to be FREE.
2. (bx+1, by) IS NOT A NEIGHBOUR. The map packs two columns per tile record
   (`FUN_004d6fb0` indexes `DAT_0092ae14 + (mapw/2*y + x>>1)*0x2c`, even x at +0, odd at
   +3), and `FUN_00502c40`'s delta table for even x (`0x67850c`/`0x678990`) steps
   (+2,0) — live-proven both ways by our own Scout Patrol taking (6,12)->(4,12) on one
   `Left` and the made Former walking (4,12)->(6,12) on one `g`.

So this script pokes the position the walk needs: every unit of ours standing on our base
tile moves to the neighbour tile (bx-2, by), and one of them becomes a Formers record
(+10 type 2 -> 1, class 9 — the same poke m54d_prep documents) with order, movement and
legs cleared. Everything the milestone then claims is the game's own: the keypress, the
chooser, the `+17` byte, the leg-array route and the walk.

    python3 scripts/m54e_prep.py [--unit N] [--dx -2] [--dy 0] [--json out.json]
    python3 scripts/m54d_census.py            # the acceptance line
"""
import argparse
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P      # noqa: E402
import m54d_census as C    # noqa: E402


def poke(f, idx, off, val, n):
    P.wr(f, P.UNIT_ARR + idx * 52 + off, struct.pack("<" + {1: "B", 2: "h", 4: "i"}[n], val))


def clear_walk_fields(f, idx):
    """+17 order, +40 movement and the +20/+28 leg arrays back to 'nothing queued'."""
    base = P.UNIT_ARR + idx * 52
    d = bytearray(P.rd(f, base, 52))
    d[17] = 0
    d[40] = 0
    for k in range(4):
        struct.pack_into("<h", d, 20 + k * 2, -1)
        struct.pack_into("<h", d, 28 + k * 2, -1)
    P.wr(f, base, bytes(d))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit", type=int, default=None,
                    help="record to convert to a Former (default: first on the base tile)")
    ap.add_argument("--dx", type=int, default=-2,
                    help="x offset of the neighbour tile (default -2: even-x delta (+2,0))")
    ap.add_argument("--dy", type=int, default=0)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    pid, f = P.mem()
    st = P.state()
    me = st["player"]
    bases = [b for b in C.base_rows(f) if b["faction"] == me]
    if not bases:
        print("no base of ours — a `g` walk has no destination")
        return 1
    bx, by = bases[0]["x"], bases[0]["y"]
    nx, ny = bx + a.dx, by + a.dy
    on_base = [u for u in C.unit_rows(f) if u["owner"] == me and (u["x"], u["y"]) == (bx, by)]
    if not on_base:
        print(f"our base tile ({bx},{by}) is already empty")
    moved = []
    for u in on_base:
        poke(f, u["idx"], 0, nx, 2)
        poke(f, u["idx"], 2, ny, 2)
        moved.append(u["idx"])
    # the walker: one of them (or --unit) becomes a Formers record, order/movement cleared
    walker = a.unit if a.unit is not None else (moved[0] if moved else None)
    if walker is None:
        ours = [u for u in C.unit_rows(f) if u["owner"] == me]
        walker = ours[0]["idx"] if ours else None
    if walker is None:
        print("no unit of ours to convert")
        return 1
    poke(f, walker, 10, 1, 2)              # +10 type -> 1 = Formers (class 9)
    poke(f, walker, 0, nx, 2)
    poke(f, walker, 2, ny, 2)
    clear_walk_fields(f, walker)
    after = P.unit_rec(f, walker)
    print(f"POKE base ({bx},{by}) -> empty; garrison {moved} -> ({nx},{ny})")
    print(f"POKE rec{walker}: type -> 1 (cls {P.unit_class(f, 1)}) at ({nx},{ny}), "
          f"order 0, mp 0, legs cleared")
    print(f"     record now: { {k: v for k, v in after.items() if k != 'raw'} }")
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(dict(state=st, walker=walker, base=(bx, by), stand=(nx, ny),
                           garrison=moved,
                           after={k: v for k, v in after.items() if k != "raw"}), fh)
    return 0


if __name__ == "__main__":
    sys.exit(main())
