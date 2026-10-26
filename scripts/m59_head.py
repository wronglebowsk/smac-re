#!/usr/bin/env python3
"""M59 — is the QUEUE HEAD, not PENDING, what gates the next production?

Static finding (scratch/m59/queue_census.py + scratch/m59/dom.py over
scratch/m574/text.txt): in the per-base visit FUN_004ef6d0 the pay gate
0x4efa5e `cmp DWORD PTR [ecx+0x40], edi; jge 0x4efadc` compares mineral storage
against the price of the value in the HEAD SLOT [base+0x50]; the pay store 0x4efedd
and the create-unit call 0x5ab650 @ 0x4eff4e are BOTH dominated by that pay block
(removing it makes 0x4eff4e unreachable from the entry and from the gate), and no
instruction between the gate and the create reads [base+0x4c] pending.  The pop
FUN_004ef5d0 (pending != 0 -> left-shift the slots, pending--) is called LATER in the
same visit (0x4f037b / 0x4f0f46) and only ADVANCES the queue.

This script is the memory test.  ONE variable: mineral storage on one named base.
The other named base is the control (untouched).

  stage=poke : hold our units, write storage=<value> to --base, read back
  stage=read : re-read everything (run after one turn has flipped)

Prints, for each named base: minerals, income, pending, head slot, queue, record+0x10
(the create guard at 0x4eff32), the derived price, and the per-tile unit multiset.
"""
import argparse, json, os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m55_boundary as M
import m56_build as B

NAMES = ["Korolev Center", "University Base"]


def find_pid():
    pid = os.environ.get("SMAC_PID")
    if pid:
        return int(pid)
    return M.find_pid()


def named(m, want):
    n = max(0, min(B.rd32(m, 0x985AF4), 64))
    for i in range(n):
        b = B.prod_fields(m, i)
        if b["name"] == want:
            return b
    raise SystemExit(f"base {want!r} not among {n} bases")


def tile_units(m, x, y):
    nu = max(0, min(B.rd32(m, M.G["n_units"][0]), 200))
    out = []
    for i in range(nu):
        u = M.parse_unit(i, M.rd(m, M.UNIT_ARR + i * M.UNIT_SZ, M.UNIT_SZ))
        if u["type"] >= M.MAX_TYPES:
            continue
        if (u["x"], u["y"]) == (x, y):
            out.append(dict(idx=i, type=u["type"], owner=u["owner"], order=u["order"]))
    return out


def report(m, tag):
    rows = []
    for want in NAMES:
        b = named(m, want)
        rec = M.rd(m, M.BASE_ARR + b["i"] * M.BASE_SZ, M.BASE_SZ)
        off0x10 = struct.unpack("<i", rec[0x10:0x14])[0]
        pr = B.price_of(m, b["fac"], b["queue"][0] & 0xFF)
        rows.append(dict(tag=tag, i=b["i"], name=b["name"], x=b["x"], y=b["y"],
                         fac=b["fac"], minerals=b["minerals"], income=b["income"],
                         pending=b["pending"], head=b["queue"][0],
                         queue=b["queue"], rec10=off0x10,
                         price=pr["price"], factor=pr["factor"], cost=pr["cost"],
                         ada8=pr["ada8"], in_mask=pr["in_mask"],
                         units_on_tile=tile_units(m, b["x"], b["y"])))
    tl = M.timeline_row(m)
    print(json.dumps(dict(year=tl["year"], round=tl["round"],
                          cur_player=tl["cur_player"], bases=rows), indent=1))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["poke", "read"], required=True)
    ap.add_argument("--base", default="Korolev Center")
    ap.add_argument("--minerals", type=int, default=None)
    ap.add_argument("--hold", action="store_true")
    a = ap.parse_args()
    pid = find_pid()
    with open(f"/proc/{pid}/mem", "rb+", 0) as m:
        if a.hold:
            trace = []
            poked = M.poke_hold(m, trace)
            ok = trace[0]["all_held"]
            print(f"poke_hold: {len(poked)} units poked, all_held={ok}")
            if not ok:
                raise SystemExit("poke_hold readback failed")
        if a.stage == "poke":
            if a.minerals is None:
                raise SystemExit("--minerals required for stage=poke")
            b = named(m, a.base)
            addr = M.BASE_ARR + b["i"] * M.BASE_SZ + 0x40
            before = b["minerals"]
            m.seek(addr)
            m.write(struct.pack("<i", a.minerals))
            back = struct.unpack("<i", M.rd(m, addr, 4))[0]
            print(f"POKE {a.base!r} idx {b['i']} +0x40: {before} -> {a.minerals} "
                  f"(read back {back}) {'OK' if back == a.minerals else 'MISMATCH'}")
            if back != a.minerals:
                raise SystemExit("poke readback mismatch")
        report(m, a.stage)


if __name__ == "__main__":
    main()
