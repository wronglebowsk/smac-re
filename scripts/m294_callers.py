#!/usr/bin/env python3
"""M294-step2 static: exhaustive E8-call scan for FUN_0051dcb0 + al-def walk.

(1) image-wide scan of rel32 calls targeting 0x51dcb0 (same idiom as M292 G1,
    which shipped the caller-law pattern), each caller VA resolved to its
    containing function via ghidra_out/index.csv;
(2) every write to eax/ax/al inside the window 0x51df60..0x51dff3 (the al chain
    feeding `mov BYTE PTR [ecx],al` at 0x51dff3). edi = BYTE[rec+2]>>4 (0x51df85) when
    nonzero, ELSE the call 0x5aff90 result (0x51df9f); call 0x582cc0 @0x51dfa4 CONSUMES
    edi as arg and its RETURN IS DISCARDED (eax reloaded at 0x51dfac).
Static only - zero box contact.
"""
import os
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import m292_pod_movement as M292

TARGET = 0x51DCB0


def funcs():
    out = []
    with open(os.path.join(ROOT, "ghidra_out", "index.csv")) as f:
        for ln in f:
            p = ln.strip().split(",")
            if len(p) >= 3 and p[0].startswith("0x"):
                try:
                    out.append((int(p[0], 16), p[1], int(p[2], 0)))
                except ValueError:
                    pass
    out.sort()
    return out


def containing(funcs, va):
    lo = None
    for addr, name, size in funcs:
        if addr <= va < addr + max(size, 1):
            return name, addr
        if addr <= va:
            lo = (name, addr)
    return ("UNKNOWN" + str(lo), lo[1] if lo else 0)


def main():
    d, va0, vsize, raddr = M292.load_text()
    calls = []
    for va in range(va0, va0 + vsize - 5):
        i = raddr + (va - va0)
        if d[i] == 0xE8:
            rel = struct.unpack_from("<i", d, i + 1)[0]
            if (va + 5 + rel) == TARGET:
                calls.append(va)
    fs = funcs()
    print("CALLERS of %#x: %d e8-call sites" % (TARGET, len(calls)))
    for va in calls:
        name, base = containing(fs, va)
        print("  %#x in %s (%#x)" % (va, name, base))
    # any FF-style indirect? (jmp/call [..] cannot name it statically; report shape)
    print("\nAL-CHAIN (gdb-free, objdump window 0x51df60-0x51dff8):")
    p = subprocess.run(["python3", "scratch/m71/dis.py", "0x51df60", "0x51dff8"],
                       cwd=ROOT, capture_output=True, text=True)
    for ln in p.stdout.splitlines():
        low = ln.lower()
        if any(k in low for k in (" eax", " ax,", " al,", "al,[", "eax,",
                                  "0x5aff90", "0x582cc0", "0x94eca8", "BYTE PTR [ecx]")):
            print("  " + ln.strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
