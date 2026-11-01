#!/usr/bin/env python3
"""M235-M237: three record/vtable questions, one instrument, static + read-only /proc.

M235  what class is vtable 0x679f98 (extent, its 2 installs, its shared slots with 0x6717cc /
      0x671d94, the strings its slot functions reference, and who dispatches its slots)
M236  who ALLOCATES and fills the 11-dword records' +4 buffer and the 0x7543d8 table entries'
      -0x40*i blocks (the +8=9 record signature census, the allocator call sites, the filler)
M237  the last route to FUN_005f5a11: are the three fields 0x2210/0x2224/0x2234 read at all
      (both addressing forms), is there a call [reg+0x22XX] site, a register-held adjustor,
      or a bulk copy over the window (the block-copy falsifier M223 pre-registered)

  sudo -n python3 scripts/m235_m237_records.py > evidence/m235_m237_records.txt

Skeleton commit first (artifact before measurement); logic filled in after.
"""
import os
import sys

GATES = []


def m235():
    pass


def m236():
    pass


def m237():
    pass


def main():
    print("# M235-M237 skeleton (no logic yet)")
    print("SUMMARY M235/M236/M237: 0/0 gates PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
