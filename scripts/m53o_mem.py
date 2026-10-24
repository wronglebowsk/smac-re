#!/usr/bin/env python3
"""Read-only snapshot of the live SMAC memory the 4e78e0 recon needs.

    python3 scripts/m53o_mem.py            # refresh evidence/m53o_mem/ + print key globals
    python3 scripts/m53o_mem.py --show     # just print key globals from the snapshot

Never writes to /proc/<pid>/mem; only seeks+reads.
"""
import json
import os
import struct
import sys

DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evidence", "m53o_mem")
# name -> (addr, length)
BLOBS = [
    ("terrain", 0x40a6ba8, 3200 * 0x2c),   # VALUE at DAT_0092ae14; refreshed below
    ("bases", 0x95da10, 76 * 0x130),       # base record array (0x130 stride)
    ("facrec", 0x94d400, 0x95da10 - 0x94d400),
    ("g926", 0x926b00, 0x300),
    ("g92a", 0x92a200, 0x200),
    ("g91c", 0x91c600, 0x100),
    ("g985", 0x985a00, 0x500),
    ("g8f0", 0x8f0c00, 0x200),
    ("offs", 0x678400, 0x700),
    ("tech", 0x92fd00, 0x1400),
    ("units", 0x933200, 0x200),
]
KEYS = {
    "cur_base_ptr": 0x8f0d60, "budget": 0x8f0c68, "c6c": 0x8f0c6c, "c70": 0x8f0c70,
    "c44": 0x8f0c44, "c4c": 0x8f0c4c, "c30": 0x8f0c30, "cc8": 0x8f0cc8, "d30": 0x8f0d30,
    "d64": 0x8f0d64, "base_idx": 0x68cbb0, "mapw_mult": 0x692184, "terr_ptr": 0x92ae14,
    "map_w": 0x92a378, "map_h": 0x92a37c, "wind": 0x92a380, "wrap": 0x92a394,
    "k27c": 0x92a27c, "k29c": 0x92a29c, "k2a0": 0x92a2a0, "k2a4": 0x92a2a4,
    "t_cap0": 0x92a2c4, "t_cap1": 0x92a2c8, "t_cap2": 0x92a2cc, "t_imps": 0x92a31c,
    "g91c628": 0x91c628, "k85ac4": 0x985ac4, "nbases": 0x985af4, "k85afc": 0x985afc,
    "mask": 0x985b10, "k85b48": 0x985b48, "spec_base": 0x985ba8, "k85bc0": 0x985bc0,
    "k85db8": 0x985db8, "k85dc4": 0x985dc4, "listcount": 0x926ca8,
}


def pid():
    out = subprocess_check()
    return out


def subprocess_check():
    import subprocess
    r = subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True, text=True)
    pids = [int(x) for x in r.stdout.split()]
    if not pids:
        sys.exit("no terran.exe running")
    return pids[0]


def main():
    show = "--show" in sys.argv
    os.makedirs(DIR, exist_ok=True)
    p = pid()
    f = open(f"/proc/{p}/mem", "rb")

    def rd(a, n):
        f.seek(a)
        return f.read(n)

    def u32(a):
        return struct.unpack("<I", rd(a, 4))[0]

    terr = u32(KEYS["terr_ptr"])
    blobs = list(BLOBS)
    blobs[0] = ("terrain", terr, 3200 * 0x2c)
    if not show:
        for name, a, n in blobs:
            data = rd(a, n)
            assert len(data) == n, (name, len(data))
            with open(os.path.join(DIR, name + ".bin"), "wb") as g:
                g.write(data)
        meta = {"pid": p, "blobs": [[n, hex(a), nlen] for n, a, nlen in blobs],
                "keys": {k: hex(v) for k, v in KEYS.items()}}
        with open(os.path.join(DIR, "meta.json"), "w") as g:
            json.dump(meta, g, indent=1)
    gl = {k: u32(a) for k, a in KEYS.items()}
    # extra: per-base raw rows we care about
    rows = []
    for i in range(76):
        b = 0x95da10 + i * 0x130
        d = rd(b, 0x130)
        g = struct.unpack_from("<76i", d, 0)
        rows.append({"idx": i, "x": struct.unpack_from("<h", d, 0)[0], "y": struct.unpack_from("<h", d, 2)[0],
                     "fac": d[4], "pop": d[6], "d30": g[12], "d34": g[13], "d38": g[14],
                     "d48": g[18], "d50": struct.unpack_from("<h", d, 0x50)[0],
                     "d78": g[30], "d7c": g[31], "d80": g[32], "d84": g[33], "d88": g[34],
                     "d8c": g[35], "vec": g[47:52], "raw_ac": g[43:47]})
    with open(os.path.join(DIR, "rows.json"), "w") as h:
        json.dump({"globals": gl, "rows": rows}, h)
    print("pid", p)
    for k in sorted(KEYS):
        print(f"  {k:14s} {gl[k]:#x} ({gl[k]})" if gl[k] < 2 ** 31 else f"  {k:14s} {gl[k]:#x} ({gl[k] - 2**32})")
    print("scan status 8f0ccc:", [hex(v) for v in struct.unpack("<25i", rd(0x8f0ccc, 100))])
    print("list 926ca4..926d78:", [hex(v) for v in struct.unpack("<44i", rd(0x926ca4, 176))])
    for tid in (49, 59, 60, 62):
        a = 0x92fdd4 + tid * 0x2c
        nm = rd(a, 24).split(b"\0")[0].decode("latin1")
        print("tech", tid, repr(nm), [hex(v) for v in struct.unpack("<8i", rd(a, 32))])


if __name__ == "__main__":
    main()
