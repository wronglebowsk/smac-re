#!/usr/bin/env python3
"""Name a global by its access pattern: every instruction that touches it, the function that contains it, and
whether the access READS, WRITES, or TESTS.

    scripts/name_global.py 0x920434                 # absolute global
    scripts/name_global.py 0x98adee --width 2       # a WORD
    scripts/name_global.py 0x94d78c --disp          # a per-record DISPLACEMENT (esi+0x94d78c), any base register

Why: "ds:0x920434 != 0 gates the 0x4d00 post" is a fact about one site; the NAME of the global is a fact about all
of them, and it is decided by who writes it and what they compute, not by the one reader that mattered.
Containment comes from ghidra_out/index.csv; the text comes from the objdump dump (scratch/m574/text.txt).
"""
import argparse
import bisect
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
INDEX = os.path.join(ROOT, "ghidra_out/index.csv")

READ = re.compile(r"^(mov|movzx|movsx|push|cmp|test|add|sub|imul|lea|and|or|xor|inc|dec)\b")
WRITE = re.compile(r"^mov\s+(dword ptr |word ptr |byte ptr )?[^,]*0x{0}(?![0-9a-f])", re.I)


def load_index():
    rows = []
    with open(INDEX) as f:
        head = f.readline().strip().split(",")
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            d = dict(zip(head, line.rstrip("\n").split(",")))
            rows.append((int(d["addr"], 16), d["name"], int(d["size_bytes"])))
    rows.sort()
    return rows


def instructions():
    for line in open(TEXT, errors="replace"):
        m = re.match(r"\s*([0-9a-f]{6,8}):\s", line)
        if not m:
            continue
        p = line.rstrip("\n").split("\t")
        yield int(m.group(1), 16), (p[2].strip() if len(p) > 2 else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("addr")
    ap.add_argument("--width", type=int, default=4)
    ap.add_argument("--disp", action="store_true", help="treat addr as a [reg+disp] displacement, not ds:addr")
    ap.add_argument("--max", type=int, default=40)
    a = ap.parse_args()
    tgt = int(a.addr, 16) if a.addr.lower().startswith("0x") else int(a.addr, 16)
    lit = "0x%x" % tgt
    ix = load_index()
    starts = [r[0] for r in ix]

    def contains(pc):
        i = bisect.bisect_right(starts, pc) - 1
        if i >= 0:
            s, n, sz = ix[i]
            if pc < s + sz:
                return n, s
        return None, None

    txt = "0x%x" % tgt
    hits = []
    for pc, ins in instructions():
        low = ins.lower()
        if a.disp:
            if not re.search(r"\[[^\]]*\+%s\]" % txt, low):
                continue
        else:
            if not re.search(r"(ds:|,|\s)%s(?![0-9a-f])" % txt, low) or "+%s]" % txt in low:
                continue
        hits.append((pc, ins))
    print("%s — %d referencing instructions%s" % (txt, len(hits), " (as a displacement)" if a.disp else ""))
    by_fn = {}
    for pc, ins in hits:
        fn, base = contains(pc)
        by_fn.setdefault(fn or "?", []).append((pc, ins))
    for fn, rows in sorted(by_fn.items(), key=lambda kv: -len(kv[1])):
        wr = [r for r in rows if re.match(r"^mov\s+.*%s(?![0-9a-f])" % txt, r[1].lower())
              and r[1].lower().split(",")[0].strip().endswith(txt)]
        print("\n%s  (%d refs, %d writes)" % (fn, len(rows), len(wr)))
        for pc, ins in rows[:a.max]:
            tag = "W" if (pc, ins) in wr else ("T" if ins.lower().startswith("test") or ins.lower().startswith("cmp") else "R")
            print("   %s %06x  %s" % (tag, pc, ins[:66]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
