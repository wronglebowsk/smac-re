#!/usr/bin/env python3
"""M374 - the NOUNS of Semaphore bits 23/24 (cell 0x92bf0c).

M372 established the cell 0x92bf0c is a bit-string member that in-game only
carries bits 23/24 (`x & 0x1800000`) and named two readers: 0x59ef11 (bit 23
gates a rand() seed of five faction-record fields) and 0x5a1150 (bit 24 gates
a 12-dword table init).  This instrument climbs the two bits backwards from the
runtime dword 0x985ae8 into their SOURCE and forwards into what they gate.

  G0  provenance chain, read out of the instruction BYTES: 0x92bf0c <- 0x985ae8
      <- 0x4dc88b/0x4dc89e `test eax,0x10000/0x20000` where eax = ds:0x99aa38
      <- 0x41ab1c/0x41ab36 legs of the 19-leg pack of [rec+0x38].
  G1  the two readers: gate instruction + the gated block, decoded.
  G2  the mask: the cell store keeps ONLY 0x1800000 (M372 re-measured here).
  G3  the record identity of the pack's source ([ds:0x8f0d60]+0x38) and its
      writer.
  G4  rival: the bits are game options written by the Rules/INI loader.

STATIC only.  M374_PATCH='addr|text' rewrites one line; M374_ALGO=n flips a law.
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M374_TEXT", os.path.join(ROOT, "scratch/m574/text.txt"))
EXE = os.path.join(ROOT, "programs/terran.exe")

ADDR = re.compile(r"^\s*([0-9a-f]{6,8}):\s+((?:[0-9a-f]{2} )+)\s*\t(.*)$")


def load_text():
    lines = {}
    order = []
    with open(TEXT, "r", errors="replace") as f:
        for line in f:
            m = ADDR.match(line.rstrip("\n"))
            if m:
                a = int(m.group(1), 16)
                lines[a] = (bytes.fromhex(m.group(2)), m.group(3).strip())
                order.append(a)
    order.sort()
    return lines, order


def main():
    lines, order = load_text()
    print("M374 text=%d insns sha1=%s" % (
        len(lines), hashlib.sha1(open(TEXT, "rb").read()).hexdigest()[:16]))
    print("SKELETON - gates not yet measured")
    return 0


if __name__ == "__main__":
    sys.exit(main())
