#!/usr/bin/env python3
"""M33: dump the pre/post state the order experiment is measured against.

Writes JSON: our Former candidates, faction energy (0x94d650[player*0x82f]), the
selected-unit global, and the full 0x2c tile record under the target unit
(0x92ae14 + (40*y + x>>1)*0x2c). Run BEFORE arming gdb (tracer holds the process)
and again after `kill -CONT`.

Usage: python3 scripts/m33_state.py evidence/m33_pre.json [unit_idx]
"""
import json, struct, subprocess, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "evidence/m33_state.json"
    want = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].strip() else None
    pid, f = P.mem()
    st = P.state()
    me = st["player"]
    sel = struct.unpack("<i", P.rd(f, P.SEL_G, 4))[0]
    cands = P.find_former(f, me)
    tgt = want if want is not None else next((c["idx"] for c in cands if c["order"] == 0),
                                             cands[0]["idx"] if cands else None)
    rec = dict(t=__import__("time").strftime("%H:%M:%S"), pid=pid, year=st["year"],
               player=me, cur_player=st["cur_player"], sel=sel,
               orders_mode=struct.unpack("<I", P.rd(f, P.ORDERS_MODE_G, 4))[0],
               pending=struct.unpack("<I", P.rd(f, 0x91B5C4, 4))[0],
               energy=struct.unpack("<i", P.rd(f, P.ENERGY_G + me * P.ENERGY_STRIDE * 4, 4))[0],
               formers=cands, target=tgt)
    if tgt is not None:
        u = P.unit_rec(f, tgt)
        rec["unit"] = {k: (v.hex() if k == "raw" else v) for k, v in u.items()}
        a, t = P.tile_recs(f, u["x"], u["y"])
        rec["tile_addr"] = hex(a)
        rec["tile"] = t.hex()
        # 8 neighbours (parity delta tables 0x6784a0/0x6784c4 via the same formula)
        nb = {}
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)]:
            a2, t2 = P.tile_recs(f, u["x"] + dx, u["y"] + dy)
            nb[f"{u['x']+dx},{u['y']+dy}"] = t2.hex()
        rec["neighbours"] = nb
    with open(out_path, "w") as fh:
        json.dump(rec, fh, indent=1)
    print(json.dumps({k: v for k, v in rec.items() if k not in ("formers", "neighbours")}, indent=1))
    print("saved:", out_path)


if __name__ == "__main__":
    main()
