#!/usr/bin/env python3
"""M53m poller: value-change log for the 8 watched dwords (+ window edges),
read-only via /proc/pid/mem, no ptrace, safe while gdb is attached."""
import struct, subprocess, sys, time, os

def pid():
    return int(subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True,
                              text=True).stdout.split()[0])

ADDRS = [0x8f0c30, 0x8f0c34, 0x8f0c38, 0x8f0c3c,
         0x8f0c68, 0x8f0c6c, 0x8f0c70, 0x8f0c74,
         0x962d90, 0x962e08, 0x962e0c, 0x962e10, 0x962e14, 0x962e1c]
LO1, HI1 = 0x8f0c30, 0x8f0c78
LO2, HI2 = 0x962d90, 0x962e20
YEAR, CUR = 0x985b00, 0x985dcc

def main():
    dur = float(sys.argv[1]) if len(sys.argv) > 1 else 420.0
    t0 = time.time()
    m = open(f"/proc/{pid()}/mem", "rb")
    def rd(a, n):
        m.seek(a); return m.read(n)
    def snap():
        v = {}
        b1 = rd(LO1, HI1 - LO1); b2 = rd(LO2, HI2 - LO2)
        for a in ADDRS:
            if LO1 <= a < HI1: off = a - LO1
            else: off = a - LO2
            v[a] = struct.unpack_from("<i", (b1 if a < HI1 else b2), off)[0]
        return v
    prev = snap()
    y0 = struct.unpack("<i", rd(YEAR, 4))[0]
    print(f"POLL start year={y0} t={time.strftime('%H:%M:%S')}", flush=True)
    for a in sorted(prev): print(f"  BASELINE 0x{a:x} = {prev[a]}", flush=True)
    while time.time() - t0 < dur:
        try:
            cur = snap()
        except (OSError, ValueError):
            time.sleep(0.2); continue
        now = time.time() - t0
        for a in sorted(cur):
            if cur[a] != prev[a]:
                print(f"CHG t={now:7.2f} 0x{a:x} {prev[a]} -> {cur[a]}", flush=True)
                prev[a] = cur[a]
        y = struct.unpack("<i", rd(YEAR, 4))[0]
        if y != y0:
            print(f"YEARCHG t={now:7.2f} {y0} -> {y}", flush=True)
            y0 = y
            time.sleep(3)   # let the round's bookkeeping settle, keep logging
        time.sleep(0.1)
    print("POLL end", flush=True)

if __name__ == "__main__":
    main()
