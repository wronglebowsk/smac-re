#!/usr/bin/env python3
"""M53m helper: read/poke/restore unit records + read globals via /proc/pid/mem."""
import json, os, struct, subprocess, sys

BASE_UNIT = 0x933278
REC = 52
TERRAIN = 0x92ae14
GLOBALS = [0x8f0c6c, 0x8f0c70, 0x8f0c34, 0x8f0c38]
ORIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "evidence", "m53m_orig.json")

def pid():
    out = subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True, text=True).stdout.split()
    return int(out[0])

def mem(mode):
    return open(f"/proc/{pid()}/mem", mode)

def urec_addr(idx):
    return BASE_UNIT + idx * REC

def fields(d):
    return dict(
        x=struct.unpack_from("<H", d, 0)[0],
        y=struct.unpack_from("<H", d, 2)[0],
        typ=struct.unpack_from("<H", d, 10)[0],
        fac=d[14], order=d[17], hp12=d[12], b38=d[38],
        abase=struct.unpack_from("<H", d, 46)[0],
        px20=struct.unpack_from("<H", d, 20)[0],
        py28=struct.unpack_from("<H", d, 28)[0],
    )

def tile_scan(xlo, xhi, ylo, yhi, bx=45, by=11):
    m = mem("rb"); cands = []
    for y in range(ylo, yhi + 1):
        for x in range(xlo, xhi + 1):
            if (x, y) == (bx, by):
                continue
            ti = y * 40 + (x >> 1)
            m.seek(TERRAIN + ti * 0x2c)
            r = m.read(0x2c)
            ok = (r[8] & 1) == 0 or (r[2] & 0xf) > 7
            cands.append(dict(x=x, y=y, ti=ti, r8=r[8], r2lo=r[2] & 0xf, ok=ok,
                              dist=abs(x - bx) + abs(y - by)))
    m.close()
    return cands

def cmd_read():
    m = mem("rb"); out = {}
    for idx in (279, 300):
        m.seek(urec_addr(idx)); d = m.read(REC)
        out[idx] = d.hex()
        print(f"u{idx} @0x{urec_addr(idx):x} {d.hex()}")
        print("  ", fields(d))
    for idx in (124, 126, 218, 224, 237, 247, 264):
        m.seek(urec_addr(idx)); d = m.read(REC)
        print(f"cand u{idx}", fields(d))
    m.close()
    json.dump(out, open(ORIG_FILE, "w"))

def cmd_scan(a):
    lo_x, hi_x, lo_y, hi_y = map(int, a)
    cands = tile_scan(lo_x, hi_x, lo_y, hi_y)
    oks = [c for c in cands if c["ok"]]
    oks.sort(key=lambda c: c["dist"])
    for c in cands:
        if c["ok"]:
            print("OKTILE", c)
    print("NOK", len(oks), "BEST", oks[0] if oks else None)

def cmd_poke(a):
    # a = x y  (chosen tile for u300)
    tx, ty = int(a[0]), int(a[1])
    m = mem("r+b")
    def poke(idx, patches):
        addr = urec_addr(idx)
        m.seek(addr); d = bytearray(m.read(REC))
        for off, size, val in patches:
            fmt = {1: "<B", 2: "<H"}[size]
            struct.pack_into(fmt, d, off, val)
        m.seek(addr); m.write(bytes(d)); m.flush()
        m.seek(addr); back = m.read(REC)
        print(f"POKED u{idx} match={back == bytes(d)} fields={fields(back)}")
        print(f"  bytes: {back.hex()}")
    poke(300, [(0, 2, tx), (2, 2, ty), (10, 2, 5), (17, 1, 3), (38, 1, 0),
               (46, 2, 70), (20, 2, tx), (28, 2, ty)])
    poke(279, [(10, 2, 5), (17, 1, 3), (38, 1, 1), (46, 2, 73)])
    m.close()

def cmd_globals():
    m = mem("rb")
    for g in GLOBALS:
        m.seek(g); v = struct.unpack("<i", m.read(4))[0]
        print(f"0x{g:x} = {v}")
    m.close()

def cmd_restore():
    orig = json.load(open(ORIG_FILE))
    m = mem("r+b")
    allok = True
    for idx, hx in orig.items():
        idx = int(idx); want = bytes.fromhex(hx)
        addr = urec_addr(idx)
        m.seek(addr); m.write(want); m.flush()
        m.seek(addr); back = m.read(REC)
        ok = back == want
        allok &= ok
        print(f"RESTORE u{idx} ok={ok} fields={fields(back)}")
    m.close()
    print("RESTORE_ALL", "OK" if allok else "FAIL")

if __name__ == "__main__":
    c = sys.argv[1]
    {"read": cmd_read, "scan": lambda: cmd_scan(sys.argv[2:]),
     "poke": lambda: cmd_poke(sys.argv[2:]), "globals": cmd_globals,
     "restore": cmd_restore}[c]()
