#!/usr/bin/env python3
"""M70 static pass 3: find every site that computes a TYPE-RECORD address and what it
reads from that record.

Measured idiom (disasm 0x40ad88-0x40ad92, inside the queue-row click handler):
    ecx = lea(eax, [eax+eax*2])      ; *3
    edx = lea(eax, [eax+ecx*4])      ; *13
    eax = lea(eax, [edx*4 + 0x98ad88]) ; *52 + base   -> the type record
(pushes may sit between the three, so we search a WINDOW, not adjacency.)

For each site we print the window and flag any later read whose displacement is a small
record offset (we list the offsets actually used, so +41 cost / +42 plan are visible).

The negative-id branch at 0x40ada2 computes 0x984d38 + (-id)*256 instead — reported too.

Usage: python3 scripts/m70_type_sites.py [--only 0x40a,0x40b] [--back 8] [--fwd 18]
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
RE_LINE = re.compile(r"\s*([0-9a-f]{5,8}):\t(.*)$")
RE_LEA_BASE = re.compile(r"\blea\s+([a-z0-9]+),\s*\[[a-z0-9]+\*4\s*\+\s*0x98ad88\s*\]", re.I)
RE_MUL13 = re.compile(r"\blea\s+([a-z0-9]+),\s*\[[a-z0-9]+\s*\+\s*[a-z0-9]+\*[23]\s*\]|\bimul\s+([a-z0-9]+),\s*[a-z0-9]+,\s*0xd\b", re.I)
RE_READ = re.compile(r"\bmov\s+[a-z0-9]+,\s*(BYTE|DWORD|WORD)\s*PTR\s*\[([a-z0-9]+)(\s*\+\s*(0x[0-9a-f]+|\d+))?\]", re.I)
RE_NEGTBL = re.compile(r"\bmov\s+[a-z0-9]+,\s*DWORD\s*PTR\s*\[([a-z0-9]+)\s*\+\s*0x984d38\s*\]", re.I)


def load():
    rows = []
    with open(TEXT, "r", errors="ignore") as fh:
        for ln in fh:
            m = RE_LINE.match(ln)
            if m:
                rows.append((int(m.group(1), 16), m.group(2).rstrip()))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="comma list of addr prefixes, e.g. 0x40a,0x41")
    ap.add_argument("--back", type=int, default=8)
    ap.add_argument("--fwd", type=int, default=18)
    ap.add_argument("--max", type=int, default=40)
    a = ap.parse_args()
    prefixes = tuple(p.strip().lower().replace("0x", "") for p in a.only.split(",") if p.strip())

    rows = load()
    sites = [i for i, (_, t) in enumerate(rows) if RE_LEA_BASE.search(t)]
    kept = []
    for i in sites:
        if not any(RE_MUL13.search(t) for _, t in rows[max(0, i - a.back):i]):
            continue
        if prefixes and not any(f"{rows[i][0]:x}".startswith(p) for p in prefixes):
            continue
        kept.append(i)
    print(f"type-record address sites (52-byte idiom): {len(kept)} of {len(sites)} lea-base hits")

    reg_of = {}
    for i in kept:
        m = RE_LEA_BASE.search(rows[i][1])
        reg_of[i] = m.group(1).lower()

    shown = 0
    for i in kept:
        if shown >= a.max:
            break
        shown += 1
        rec_reg = reg_of[i]
        print(f"\n== 0x{rows[i][0]:x}  {rows[i][1][:80]}")
        for j in range(i, min(len(rows), i + 1 + a.fwd)):
            aa, tt = rows[j]
            m = RE_READ.search(tt)
            note = ""
            if m and m.group(2).lower() == rec_reg:
                disp = m.group(4)
                off = int(disp, 16) if disp and disp.startswith("0x") else (int(disp) if disp else 0)
                label = {0: "NAME+0", 41: "COST+41", 42: "PLAN+42", 15: "+15", 37: "+37"}.get(off, f"+{off}")
                note = f"   <== record read {label}"
            elif RE_NEGTBL.search(tt):
                note = "   <== negative-id table [reg*256+0x984d38]"
            print(f"  0x{aa:x}\t{tt[:88]}{note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
