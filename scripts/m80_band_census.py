#!/usr/bin/env python3
"""M80 — census the WHOLE type-record array (0..511), not just 0..255.

Read-only /proc/pid/mem read of the stride-52 record array at 0x98ad88, grouped into
64-record bands, because the production scan FUN_00573a90 computes its record index as
`param_1*64 + (counter & 0x3f)` (bytes 0x573b..) and the sweep call at 0x5741fe passes that
index in esi.  The old census covered 0..255 only, so bands 4..7 were never read.

Fields per record (bytes): name +0, triple +0x24/25/26, owner mask +0x2c, cost +0x29,
plan +0x2a, flags WORD +0x30 (bit0 validator test, bit2 markup-off, bit8 sweep marker).

Usage: python3 scripts/m80_band_census.py [--detail LO HI] [--json]
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m55_boundary as M

REC_BASE = 0x98AD88
STRIDE = 52
COUNT = 512


def census(m, count=COUNT):
    m.seek(REC_BASE)
    blob = m.read(STRIDE * count)
    out = []
    for i in range(count):
        r = blob[i * STRIDE:(i + 1) * STRIDE]
        z = r.find(b"\0")
        name = r[:z if z >= 0 else 16]
        printable = all(32 <= b < 127 for b in name)
        flags = r[0x30] | (r[0x31] << 8)
        out.append(dict(
            i=i, band=i // 64, slot=i % 64,
            name=name.decode("latin1") if (printable and name) else "",
            raw=list(r[:z if z >= 0 else 8]),
            owner=r[0x2c], cost=r[0x29], plan=r[0x2a],
            t24=r[0x24], t25=r[0x25], t26=r[0x26],
            flags=flags))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--detail", nargs=2, type=int, metavar=("LO", "HI"))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    pid = os.environ.get("SMAC_PID") or M.find_pid()
    if not pid:
        print("no terran.exe")
        return 1
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        recs = census(m)
    if a.json:
        print(json.dumps(recs))
        return 0
    print(f"pid {pid}  array 0x{REC_BASE:x} stride {STRIDE} count {COUNT}")
    for b in range(8):
        band = recs[b * 64:(b + 1) * 64]
        named = [r for r in band if r["name"]]
        masks = sorted({r["owner"] for r in band if r["owner"]})
        fl = sorted({hex(r["flags"]) for r in band if r["flags"]})
        print(f"band {b} ({b*64}..{b*64+63}): named {len(named):3d}  owner-masks {masks[:6]} "
              f"flagwords {fl[:8]}")
        for r in named[:4]:
            print(f"   [{r['i']:3d}] {r['name'][:22]:22s} own 0x{r['owner']:02x} cost {r['cost']:3d} "
                  f"plan {r['plan']:3d} triple {r['t24']}/{r['t25']}/{r['t26']} flags 0x{r['flags']:04x}")
    if a.detail:
        lo, hi = a.detail
        print(f"--- detail {lo}..{hi} ---")
        for r in recs[lo:hi]:
            tag = "named" if r["name"] else ("bytes" if any(r["raw"]) else "zero")
            print(f"[{r['i']:3d}] {tag:5s} {r['name'][:20]:20s} own 0x{r['owner']:02x} "
                  f"cost {r['cost']:3d} plan {r['plan']:3d} triple {r['t24']:3d}/{r['t25']:3d}/"
                  f"{r['t26']:3d} flags 0x{r['flags']:04x}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
