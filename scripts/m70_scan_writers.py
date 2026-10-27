#!/usr/bin/env python3
"""M70 static pass: find every code site that reads the type-record PLAN byte (+42)
or the COST byte (+41), and every site that WRITES the queue widget's cursor field.

Docs/NAMED.md say the enqueue path (0x417dbf-0x417e04) reads NO type byte, so any other
reader of +41/+42 is a candidate for the queue widget's LIST order.  The cursor field is
[0x6a9480 + 0x3ff5c]; a writer site is a `mov dword ptr [reg+0x3ff5c], reg` (or [abs]).

Reads scratch/m574/text.txt (whole .text objdump, gitignored) and prints only the
matching addresses + a small context window.  Never prints the file.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")

# type record: 0x98ad88 + tid*52 + off  ->  scale 0x34, disp 0x98ad88+off
TYPE_BASE = 0x98AD88
OFFS = {41: "COST+41", 42: "PLAN+42"}
CURSOR_ABS = 0x6A9480 + 0x3FF5C


def main():
    if not os.path.isfile(TEXT):
        raise SystemExit(f"missing {TEXT}")

    # patterns for a scaled-index load with base 0x98ad88 (plan/cost reads)
    re_scaled = re.compile(r"mov\s+[a-z0-9]+,\s*DWORD PTR \[([a-z0-9]+)\*0x34[a-z]*\+0x([0-9a-f]+)\]",
                           re.I)
    # cursor writes: any store whose displacement is 0x3ff5c
    re_cur_store = re.compile(r"mov\s+DWORD PTR \[([^]]*)\+0x3ff5c\]", re.I)
    re_cur_load = re.compile(r"mov\s+[a-z0-9]+,\s*DWORD PTR \[([^]]*)\+0x3ff5c\]", re.I)

    lines = open(TEXT, "r", errors="ignore").readlines()
    # index addresses so we can print a small window around a hit
    addr_of = {}
    for i, ln in enumerate(lines):
        m = re.match(r"\s*([0-9a-f]{6,8}):", ln)
        if m:
            addr_of[m.group(1)] = i

    hits = {"plan": [], "cost": [], "cur_store": [], "cur_load": []}
    for i, ln in enumerate(lines):
        if len(ln) > 200:
            continue
        m = re_scaled.search(ln)
        if m:
            disp = int(m.group(2), 16)
            low = disp - TYPE_BASE
            if low in (-2 ** 31, 41) or 0 <= low <= 51:
                hits["plan" if low == 42 else ("cost" if low == 41 else "other")].append((i, m.group(1), low))
            continue
        if re_cur_store.search(ln) and not re_cur_load.fullmatch(ln.strip()):
            hits["cur_store"].append(i)
        elif re_cur_load.search(ln):
            hits["cur_load"].append(i)

    for key in ("cost", "plan"):
        rows = hits[key]
        print(f"== type-record byte reads: {OFFS[41 if key == 'cost' else 42]} "
              f"(scale 0x34, base 0x{TYPE_BASE:x}) — {len(rows)} site(s)")
        for i, scale_reg, low in rows:
            a = re.match(r"\s*([0-9a-f]{6,8}):", lines[i]).group(1)
            print(f"  0x{a}  {lines[i].strip()[:110]}")
        print()

    print(f"== cursor-field [0x6a9480+0x3ff5c = 0x{CURSOR_ABS:x}] WRITES — {len(hits['cur_store'])}")
    for i in hits["cur_store"]:
        print(f"  {lines[i].strip()[:120]}")
    print(f"\n== cursor-field READS — {len(hits['cur_load'])}")
    for i in hits["cur_load"]:
        print(f"  {lines[i].strip()[:120]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
