#!/usr/bin/env python3
"""M54g prep: stand ONE of ours on a founding-legal tile as a class-8 colonist.

Two pokes, both PREP (the ORDER itself is issued by the loop, not here):
  +10 (type)  -> 0 = Colony Pod/Conestoga, the class-8 record `b` requires
                 (shard_012.c:2852 NEEDCOLONISTS; data/alpha.json UNITS row 1 = count row)
  +0/+2 (x,y) -> a REAL neighbour of our base tile that passes founding_gate()
                 (the same delta tables the game's BASETOONEAR scan walks, so the tile is
                 a neighbour by the game's own definition — (bx+1,by) is not one)

Why a poke and not a walk: a garrisoned unit cannot be ordered OFF its own base tile on
this build — `g` refuses the unit-on-its-own-base case (M54c) and Shift+arrow queued
nothing on a type-0 unit standing at (28,42) (scratch/m54g_walk.py: +17 stayed 0). The
same position poke is what m54e_prep does. Every poke is read back here; the founding
itself is proven later in the BASE ARRAY by the loop.

    python3 scripts/m54g_prep.py [--unit N] [--json out.json]
"""
import argparse, json, os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit", type=int, default=None, help="record to convert (default: lowest ours)")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    jpath = args.json or os.path.join(root, "evidence", "m54g", "prep.json")

    pid, f = P.mem()
    st = P.state()
    me = st["player"]
    out = {"pid": pid, "state_before": st, "pokes": []}

    def poke(idx, off, val, n, label):
        P.wr(f, P.UNIT_ARR + idx * 52 + off, struct.pack("<" + {1: "B", 2: "h", 4: "i"}[n], val))
        back = struct.unpack("<" + {1: "B", 2: "h", 4: "i"}[n],
                             P.rd(f, P.UNIT_ARR + idx * 52 + off, n))[0]
        out["pokes"].append(dict(unit=idx, off=off, want=val, readback=back, label=label))
        print(f"poke rec{idx} +{off} -> {val} ({label}), read back {back}", flush=True)
        return back

    tiles = sorted(P.own_base_tiles(f, me))
    if not tiles:
        print("we own no base — prep cannot run"); return 1
    bx, by = tiles[0]
    print(f"our base tile ({bx},{by}); own tiles {tiles}", flush=True)

    # the game's OWN neighbour set (the delta tables its BASETOONEAR scan walks)
    w = struct.unpack("<I", P.rd(f, 0x92A378, 4))[0]
    h = struct.unpack("<I", P.rd(f, 0x92A37C, 4))[0]
    nbrs = []
    for k in range(0, 32, 4):
        nx = struct.unpack("<i", P.rd(f, 0x6784A0 + k, 4))[0] + bx
        ny = struct.unpack("<i", P.rd(f, 0x6784C4 + k, 4))[0] + by
        if -1 < nx < w and -1 < ny < h:
            nbrs.append((nx, ny))
    print(f"real neighbours of ({bx},{by}) per the delta tables: {nbrs}", flush=True)

    cands = [c for c in P.find_actionable(f, me)]
    print("our actionable records:", [(c["idx"], c["x"], c["y"], c["type"], c["cls"])
                                      for c in cands], flush=True)
    unit = args.unit if args.unit is not None else (cands[0]["idx"] if cands else None)
    if unit is None:
        print("no actionable unit"); return 1

    # The unit is POKE-positioned (see the docstring), so the target only has to pass the
    # game's own founding gates — it does NOT have to be a delta-table neighbour, because
    # no pathfinding runs (the neighbour rule is a WALK constraint, M54e). Scan outward
    # from the base and take the nearest legal tile.
    legal = []
    for d in range(1, 5):
        for dy in range(-d, d + 1):
            for dx in range(-d, d + 1):
                if max(abs(dx), abs(dy)) != d:
                    continue
                nx, ny = bx + dx, by + dy
                if not (0 <= nx < w and 0 <= ny < h) or (nx, ny) in tiles:
                    continue
                if not P.founding_gate(f, nx, ny, 0):      # judged as the type we poke to
                    legal.append((nx, ny))
        if legal:
            break
    if not legal:
        print("NO legal founding tile within 4 of our base — report and stop"); return 1
    tx, ty = legal[0]
    print(f"legal founding tiles at distance {max(abs(tx-bx),abs(ty-by))}: {legal[:8]}; "
          f"target ({tx},{ty})", flush=True)

    poke(unit, 10, 0, 2, "type -> Colony Pod (class 8)")
    poke(unit, 0, tx, 2, "x -> founding tile")
    poke(unit, 2, ty, 2, "y -> founding tile")
    poke(unit, 17, 0, 1, "order byte cleared")

    r = P.unit_rec(f, unit)
    out["unit_after"] = {k: r[k] for k in ("x", "y", "type", "order", "mpused", "flags")}
    out["gate_after"] = P.founding_gate(f, r["x"], r["y"], r["type"])
    out["cls_after"] = P.unit_class(f, r["type"])
    out["own_tiles_after"] = sorted(P.own_base_tiles(f, me))
    out["energy"] = P.energy(f, me)
    print(f"rec{unit}: {out['unit_after']} class {out['cls_after']} "
          f"gates {out['gate_after'] or 'LEGAL'} own bases {out['own_tiles_after']} "
          f"energy {out['energy']}", flush=True)
    with open(jpath, "w") as fh:
        json.dump(out, fh, indent=1, default=lambda o: o.hex() if isinstance(o, bytes) else str(o))
    print("wrote", jpath)


if __name__ == "__main__":
    main()
