#!/usr/bin/env python3
"""M54d: census the LIVE position — what units we own, their CLASS, and where they stand.

    python3 scripts/m54d_census.py [--json out.json]

M54d's first acceptance line is "a saved position that contains at least one class-9 unit
owned by us (print the census line)". This prints that claim and its evidence: every live
record we own, its class as the GAME reads it (`DAT_0098adb2[type*52] & 0xff`, the same
class gate FUN_004d44d0 uses — ORDERS.md §2), its tile, its movement byte, and whether it
is standing on one of OUR bases (the gate that makes `g` refuse to queue a MOVE —
ORDERS.md §4 0x18, measured in `evidence/m54c_probe.txt`).

Offsets: units 0x933278 x 52 B (x@0, y@2, flags@4, frozen@9, type@10, owner@14, order@17,
mp-used@40 — SAVE_FORMAT.md 155-182); bases 0x95DA10 x 304 B (x@0, y@2, faction@4), count
at 0x985AF4 (SAVE_FORMAT.md 150-160: that global is a BASE count, not a faction count).
Reads /proc/pid/mem; never pokes, never clicks.
"""
import argparse, json, os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P

UNIT_N = 300
BASE_ARR, BASE_SZ = 0x95DA10, 304
BASE_COUNT_G = 0x985AF4


def unit_rows(f, n=UNIT_N):
    arr = P.rd(f, P.UNIT_ARR, n * 52)
    out = []
    for i in range(n):
        d = arr[i * 52:(i + 1) * 52]
        owner = d[14]
        typ = struct.unpack("<H", d[10:12])[0]
        if owner == 0xFF or typ == 0xFFFF:
            continue
        out.append(dict(idx=i, x=struct.unpack("<h", d[0:2])[0],
                        y=struct.unpack("<h", d[2:4])[0],
                        flags=struct.unpack("<I", d[4:8])[0], frozen=d[9], type=typ,
                        cls=P.unit_class(f, typ), owner=owner, order=d[17], mpused=d[40],
                        legs=[struct.unpack("<h", d[20 + k * 2:22 + k * 2])[0] for k in range(4)],
                        legs_y=[struct.unpack("<h", d[28 + k * 2:30 + k * 2])[0] for k in range(4)]))
    return out


def base_rows(f):
    n = struct.unpack("<I", P.rd(f, BASE_COUNT_G, 4))[0]
    n = max(0, min(n, 64))
    b = P.rd(f, BASE_ARR, n * BASE_SZ)
    out = []
    for i in range(n):
        r = b[i * BASE_SZ:(i + 1) * BASE_SZ]
        # SAVE_FORMAT.md 150-160: the 304-byte record's +4/+5 pair is the faction nibble
        # duplicated (`0x0505 (faction 5)`), so the faction index is the LOW byte.
        out.append(dict(idx=i, x=struct.unpack("<H", r[0:2])[0], y=struct.unpack("<H", r[2:4])[0],
                        faction=r[4], faction_word=struct.unpack("<H", r[4:6])[0],
                        name=r[19:51].split(b"\0")[0].decode("latin-1", "replace")))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None, help="write the full census here")
    ap.add_argument("--owner", type=int, default=None, help="census this faction (default: us)")
    a = ap.parse_args()
    pid, f = P.mem()
    st = P.state()
    me = st.get("player") if a.owner is None else a.owner
    units = unit_rows(f)
    bases = base_rows(f)
    ours = [u for u in units if u["owner"] == me]
    c9 = [u for u in ours if u["cls"] == 9]
    ownbase = {(b["x"], b["y"]) for b in bases if b["faction"] == me}
    bycls = {}
    for u in ours:
        bycls[u["cls"]] = bycls.get(u["cls"], 0) + 1
    print(f"CENSUS pid={pid} year={st.get('year')} turn_no={st.get('turn_no')} "
          f"player={me} cur_player={st.get('cur_player')} units_ours={len(ours)} "
          f"class9={len(c9)} bases_total={len(bases)} bases_ours={len(ownbase)} "
          f"class_mix={json.dumps(bycls, sort_keys=True)}")
    for u in ours:
        tag = "CLASS9" if u["cls"] == 9 else "      "
        print(f"  {tag} rec{u['idx']:3d} type {u['type']:3d} cls {u['cls']:2d} "
              f"({u['x']:2d},{u['y']:2d}) order {u['order']:3d} mp {u['mpused']} "
              f"frozen {u['frozen']} flags {u['flags']:#x} "
              f"on_own_base={((u['x'],u['y']) in ownbase)} legs={u['legs']} legs_y={u['legs_y']}")
    for b in bases:
        if b["faction"] == me:
            print(f"  BASE   rec{b['idx']:3d} ({b['x']:2d},{b['y']:2d}) {b['name']!r}")
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(dict(state=st, units=units, bases=bases), fh)
        print(f"wrote census -> {a.json}")
    return 0 if c9 else 1


if __name__ == "__main__":
    sys.exit(main())
