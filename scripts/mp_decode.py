#!/usr/bin/env python3
"""Decode a block of an SMAC .MP/.SAV file with the routine at 0x596540.

Transcribed from the disassembly of FUN_00596540 (terran.exe), not guessed from the
decompiled C, because the decompiler hides two things:

  * the signature is (dest, nbytes, count, file) — `param_2 * param_3` is size x count
  * the pair is **swapped** on output: dest[0] = decode(src[1]), dest[1] = decode(src[0])

Per 2-byte pair, with counters starting at 0x80:
    c1 = 0x80 + i          (i = pair index)
    c2 = 0x80 - i
    b0 = src[0]; b1 = src[1]
    out[0] = b1 ^ c1   unless b1 == 0 or (b1 ^ c1) == 0, in which case b1
    out[1] = b0 ^ c2   unless b0 == 0 or (b0 ^ c2) == 0, in which case b0
A zero source byte is therefore never transformed (escape), and a byte that would
decode to 0 is left alone.

    scripts/mp_decode.py <file> <offset> <length> [--stats] [--out out.bin]
"""
import argparse
import collections
import math


def decode_block(src: bytes) -> bytes:
    n = len(src) + (len(src) & 1)
    buf = bytes(src) + (b"\x00" if len(src) & 1 else b"")
    out = bytearray(n)
    c1 = 0x80
    c2 = 0x80
    for i in range(0, n, 2):
        b0 = buf[i]
        b1 = buf[i + 1]
        d1 = b1
        if b1 != 0:
            t = b1 ^ c1
            if t != 0:
                d1 = t
        d0 = b0
        if b0 != 0:
            t = b0 ^ c2
            if t != 0:
                d0 = t
        out[i] = d1
        out[i + 1] = d0
        c1 = (c1 + 1) & 0xFF
        c2 = (c2 - 1) & 0xFF
    return bytes(out)


def entropy(b: bytes) -> float:
    if not b:
        return 0.0
    c = collections.Counter(b)
    n = len(b)
    return -sum((v / n) * math.log2(v / n) for v in c.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("offset", type=lambda s: int(s, 0))
    ap.add_argument("length", type=lambda s: int(s, 0))
    ap.add_argument("--out")
    ap.add_argument("--stats", action="store_true", default=True)
    a = ap.parse_args()

    data = open(a.file, "rb").read()
    src = data[a.offset:a.offset + a.length]
    if len(src) != a.length:
        raise SystemExit(f"only {len(src)} bytes available at {a.offset:#x}")
    out = decode_block(src)

    if a.out:
        open(a.out, "wb").write(out)
        print(f"wrote {a.out} ({len(out)} bytes)")

    print(f"src  {len(src):>6} B  entropy {entropy(src):.2f}  distinct {len(set(src)):>3}")
    print(f"out  {len(out):>6} B  entropy {entropy(out):.2f}  distinct {len(set(out)):>3}")
    hist = collections.Counter(out).most_common(8)
    print("top out bytes:", " ".join(f"{b:02x}x{n}" for b, n in hist))
    print("first 48 out:", out[:48].hex(" "))


if __name__ == "__main__":
    main()
