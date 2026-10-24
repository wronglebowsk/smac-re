#!/usr/bin/env python3
"""Census of a m53p recon run: per-field mismatch counts + full-match base list.

    python3 evidence/m53p_swap_census.py evidence/m53p_swap_baseline.txt
    python3 evidence/m53p_swap_census.py NEW.txt evidence/m53p_swap_baseline.txt   # diff rows

Reads the `idx ...` / `  bc model=.. obs=.. delta=..` blocks printed by the recon.
Also emits a deltas TSV (idx fac pop field model obs delta) next to the report when
called with --tsv PATH.
"""
import re
import sys

NAMES = ["bc", "c0", "c4", "c8"]


def parse(path):
    rows = {}
    cur = None
    for ln in open(path):
        m = re.match(r"^idx (\d+) fac (\d+) pop (\d+)", ln)
        if m:
            cur = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
            rows[cur] = {}
            continue
        m = re.match(r"^\s+(bc|c0|c4|c8) model=(-?\d+)\s+obs=(-?\d+)\s+delta=(-?\d+)", ln)
        if m and cur:
            rows[cur][m.group(1)] = (int(m.group(2)), int(m.group(3)), int(m.group(4)))
    return rows


def census(rows):
    bad = {f: 0 for f in NAMES}
    full = []
    for k, v in sorted(rows.items()):
        d = [v[f][2] for f in NAMES if f in v]
        for f in NAMES:
            if f in v and v[f][2]:
                bad[f] += 1
        if all(v[f][2] == 0 for f in NAMES if f in v):
            full.append(k[0])
    return bad, full


def main():
    a = sys.argv[1:]
    tsv = None
    if "--tsv" in a:
        i = a.index("--tsv")
        tsv = a[i + 1]
        a = a[:i] + a[i + 2:]
    base = parse(a[0])
    bbad, bfull = census(base)
    new = base if len(a) < 2 else parse(a[1])
    print("A %s: mismatch/field %s  full %d/%d" % (a[0], bbad, len(bfull), len(base)))
    print("A full-match:", bfull)
    if len(a) > 1:
        new = parse(a[1])
        nbad, nfull = census(new)
        print("B %s: mismatch/field %s  full %d/%d" % (a[1], nbad, len(nfull), len(new)))
        print("B full-match:", nfull)
        print("gained:", sorted(set(nfull) - set(bfull)))
        print("lost  :", sorted(set(bfull) - set(nfull)))
        keys = sorted(set(base) | set(new))
        print("row deltas changed (idx fac pop field A->B):")
        for k in keys:
            for f in NAMES:
                av = base.get(k, {}).get(f)
                bv = new.get(k, {}).get(f)
                if av and bv and av[2] != bv[2]:
                    print("  %d %d %d %s %d->%d" % (k[0], k[1], k[2], f, av[2], bv[2]))
    if tsv:
        with open(tsv, "w") as g:
            for k, v in sorted(new.items()):
                for f in NAMES:
                    if f in v and v[f][2]:
                        g.write("%d\t%d\t%d\t%s\t%d\t%d\t%d\n" % (k[0], k[1], k[2], f,
                                                                  v[f][0], v[f][1], v[f][2]))


if __name__ == "__main__":
    main()
