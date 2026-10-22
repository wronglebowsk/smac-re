#!/usr/bin/env python3
"""M33: scan the live unit array for candidate order targets.

Reads the unit array (0x933278 x 52 B), the type class table (0x98adb2, stride 52,
class 9 = Former), the selected-unit global (0x91b5bc) and orders-mode (0x91b5b8)
straight through /proc/<pid>/mem. Prints every live unit owned by us with its class,
position, order byte, mp and stack chain — the picker the driver needs to choose a
Former for a terraform order.

Usage:
  python3 scripts/m33_scan.py            # our units, sorted
  python3 scripts/m33_scan.py --all      # every live unit
  python3 scripts/m33_scan.py --json     # machine-readable
"""
import argparse, json, os, struct, subprocess, sys

UNIT_ARR = 0x933278
MAX_UNITS = 300          # count ceiling; dead slots have owner=0xff
CLASS_TBL = 0x98ADB2     # type*52 -> class dword (9 Former, 10 sea, 12 transport, 7 carrier)
DOMAIN_TBL = 0x98ADAC    # type*52 -> domain byte
SEL = 0x91B5BC
ORDERS_MODE = 0x91B5B8
PENDING = 0x91B5C4
PLAYER = 0x91B5B4
YEAR = 0x985B00


def pid():
    out = subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True, text=True).stdout.split()
    if not out:
        sys.exit("terran.exe not running")
    return int(out[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    p = pid()
    with open(f"/proc/{p}/mem", "rb", 0) as m:
        def rd(addr, n):
            m.seek(addr); return m.read(n)
        sel = struct.unpack("<i", rd(SEL, 4))[0]
        omode = struct.unpack("<I", rd(ORDERS_MODE, 4))[0]
        pend = struct.unpack("<I", rd(PENDING, 4))[0]
        me = struct.unpack("<I", rd(PLAYER, 4))[0]
        year = struct.unpack("<I", rd(YEAR, 4))[0]
        units = rd(UNIT_ARR, MAX_UNITS * 52)
        classes = rd(CLASS_TBL, 1024 * 52)    # type*52 -> class dword at +0
        domains = rd(DOMAIN_TBL, 1024 * 52)
    rows = []
    for i in range(MAX_UNITS):
        d = units[i * 52:(i + 1) * 52]
        owner = d[14]
        if owner == 0xFF:
            continue
        typ = struct.unpack("<H", d[10:12])[0]
        # class = LOW BYTE of the runtime type record's +0 dword at type*52
        # (verified live 2026-10-21: type 1 -> 0xff002909 class 9 = Former, matching
        #  alpha.txt #UNITS field5; types >= 64 are per-faction built variants whose
        #  class byte is preserved, e.g. type 194 -> 0x9000202 class 2)
        cls = struct.unpack("<I", classes[typ * 52:typ * 52 + 4])[0] & 0xFF
        dom = domains[typ * 52] & 0xFF
        r = dict(
            idx=i, x=struct.unpack("<h", d[0:2])[0], y=struct.unpack("<h", d[2:4])[0],
            flags=struct.unpack("<I", d[4:8])[0], type=typ, owner=owner,
            order=d[17], nlegs=d[18], leg=d[19],
            dx=struct.unpack("<h", d[20:22])[0], dy=struct.unpack("<h", d[28:30])[0],
            mpused=d[40], dir=d[41], watchdog=d[42],
            home=struct.unpack("<h", d[46:48])[0],
            prev=struct.unpack("<h", d[48:50])[0], next=struct.unpack("<h", d[50:52])[0],
            cls=cls, dom=dom, own=(owner == me), sel=(i == sel),
        )
        rows.append(r)
    if a.json:
        print(json.dumps(dict(pid=p, year=year, me=me, sel=sel, orders_mode=omode,
                              pending=pend, units=rows), indent=1))
        return
    print(f"pid={p} year={year} me={me} sel={sel} orders_mode={omode:#x} pending={pend:#x}")
    print(f"{'idx':>4} {'x':>3} {'y':>3} {'own':>3} {'cls':>3} {'typ':>4} {'ord':>4} {'mp':>3} "
          f"{'flags':>10} {'dx':>3} {'dy':>3} {'legs':>4} {'home':>4} {'prev':>4} {'next':>4} note")
    for r in rows:
        if not a.all and not r["own"]:
            continue
        note = []
        if r["sel"]: note.append("SELECTED")
        if r["cls"] == 9: note.append("FORMER")
        if r["flags"] & 0x4: note.append("f4")
        if r["flags"] & 0x4000: note.append("explore")
        if r["order"]: note.append(f"order={r['order']:#x}")
        if r["mpused"]: note.append(f"mp={r['mpused']}")
        print(f"{r['idx']:>4} {r['x']:>3} {r['y']:>3} {r['owner']:>3} {r['cls']:>3} {r['type']:>4} "
              f"{r['order']:>4} {r['mpused']:>3} {r['flags']:>#10x} {r['dx']:>3} {r['dy']:>3} "
              f"{r['nlegs']}/{r['leg']:<3} {r['home']:>4} {r['prev']:>4} {r['next']:>4} "
              + " ".join(note))


if __name__ == "__main__":
    main()
