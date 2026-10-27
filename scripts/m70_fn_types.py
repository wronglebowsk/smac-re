#!/usr/bin/env python3
"""M70 static pass 2: locate the function containing a given address and list the
type-record accesses (any addressing form) inside it.

Forms matched:
  * base+disp immediates: 0x98ad88, 0x98ad89..0x98adbb (base + 0..51)
  * scaled index with the type base folded in: [reg*0x34+0x98adXX]
  * explicit multiply by 0x34 (52) near a 0x98adXX base load
Usage: python3 scripts/m70_fn_types.py 0x40aa22 [--span 0x40a000 0x40b200]
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
TYPE_BASE = 0x98AD88


def load():
    """(list of (addr, text), sorted) for the whole .text — cheap enough (400k lines)."""
    rows = []
    ap = re.compile(r"\s*([0-9a-f]{5,8}):\t([0-9a-f ]{2,24})\t(.*)$")
    with open(TEXT, "r", errors="ignore") as fh:
        for ln in fh:
            m = ap.match(ln)
            if m:
                rows.append((int(m.group(1), 16), m.group(3).rstrip()))
    return rows


def fn_bounds(rows, addr):
    """Function bounds from the int3/nop padding that separates functions in this objdump:
    walk back to the last padding run before `addr`, forward to the next padding run after."""
    idx = None
    for i, (a, _) in enumerate(rows):
        if a >= addr:
            idx = i
            break
    if idx is None:
        raise SystemExit(f"address 0x{addr:x} not found")

    def pad(j):
        t = rows[j][1]
        return t.startswith("int3") or t.startswith("nop") or t.startswith("lea ") is False and False

    lo = 0
    for j in range(idx, 0, -1):
        if pad(j) and pad(j - 1):
            lo = j + 1 if j + 1 <= idx else idx
            break
    hi = len(rows) - 1
    for j in range(idx, len(rows) - 1):
        if pad(j) and pad(j + 1):
            hi = j - 1 if j - 1 >= idx else idx
            break
    return lo, hi


def main():
    target = int(sys.argv[1], 16)
    rows = load()
    lo, hi = fn_bounds(rows, target)
    print(f"function window 0x{rows[lo][0]:x} .. 0x{rows[hi][0]:x} "
          f"({hi - lo + 1} instrs) containing 0x{target:x}")

    re_disp = re.compile(r"0x(98ad[0-9a-f]{2})\b", re.I)
    re_mul = re.compile(r"\bimul?\b.*0x34\b")
    seen = {}
    for i in range(lo, hi + 1):
        a, t = rows[i]
        m = re_disp.search(t)
        if m:
            disp = int(m.group(1), 16)
            off = disp - TYPE_BASE
            if 0 <= off <= 51:
                seen.setdefault(off, []).append((a, t))
            else:
                seen.setdefault("other", []).append((a, t))
        elif re_mul.search(t):
            seen.setdefault("mul52", []).append((a, t))

    for off in sorted([k for k in seen if isinstance(k, int)]):
        rowsx = seen[off]
        label = {0: "NAME+0", 41: "COST+41", 42: "PLAN+42"}.get(off, f"+{off}")
        print(f"  byte {label}: {len(rowsx)} access(es)")
        for a, t in rowsx[:6]:
            print(f"    0x{a:x}  {t[:100]}")
    for k in ("mul52", "other"):
        if k in seen:
            print(f"  {k}: {len(seen[k])}")
            for a, t in seen[k][:8]:
                print(f"    0x{a:x}  {t[:100]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
