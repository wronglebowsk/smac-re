#!/usr/bin/env python3
"""M53b: dump the runtime unit/facility TYPE RECORD table at 0x98ad88 (stride 52).

Reads /proc/<pid>/mem (no tracer) and writes a TSV to
evidence/m53b_types.tsv with, per type id:
  name, ability(+32), domain(+36), b41(+0x29), class(+0x2a), b43(+0x2b),
  w48(+0x30), b44/b45/b46, tail(+0x34)
Stdout gets only a compact digest (counts + the rows where b41 != b43).
"""
import os, struct, subprocess, sys

BASE = 0x98AD88
STRIDE = 52
NREC = 700  # generous; valid rows are filtered by a printable name


def pid_of():
    out = subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True, text=True).stdout.split()
    if not out:
        sys.exit("terran.exe not running")
    return int(out[0])


def main():
    pid = pid_of()
    n = int(sys.argv[1]) if len(sys.argv) > 1 else NREC
    with open(f"/proc/{pid}/mem", "rb", 0) as f:
        f.seek(BASE)
        blob = f.read(n * STRIDE)
    rows = []
    for i in range(n):
        r = blob[i * STRIDE:(i + 1) * STRIDE]
        if len(r) < STRIDE:
            break
        nb = r[:34].split(b"\0")[0]
        try:
            name = nb.decode("ascii")
        except UnicodeDecodeError:
            name = ""
        printable = name.isprintable() and len(name) >= 3
        ability, domain = struct.unpack_from("<ii", r, 32)
        b41, cls, b43 = r[41], r[42], r[43]
        w48 = struct.unpack_from("<H", r, 48)[0]
        b44, b45, b46 = r[44], r[45], r[46]
        tail = struct.unpack_from("<H", r, 50)[0]
        rows.append((i, name, printable, ability, domain, b41, cls, b43, w48, b44, b45, b46, tail))

    outp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "evidence", "m53b_types.tsv")
    with open(outp, "w") as f:
        f.write("id\tname\tability\tdomain\tb41\tclass\tb43\tw48\tb44\tb45\tb46\ttail50\n")
        for (i, name, printable, ability, domain, b41, cls, b43, w48, b44, b45, b46, tail) in rows:
            if not printable:
                continue
            f.write(f"{i}\t{name}\t{ability}\t{domain}\t{b41}\t{cls}\t{b43}\t{w48}\t{b44}\t{b45}\t{b46}\t{tail}\n")
    valid = [r for r in rows if r[2]]
    print(f"pid={pid} records_read={len(rows)} printable={len(valid)} -> {outp}")
    lastid = valid[-1][0] if valid else -1
    print(f"last_printable_id={lastid}")
    # class histogram
    from collections import Counter, defaultdict
    hist = Counter(r[6] for r in valid)
    print("class histogram:", " ".join(f"{c}:{k}" for c, k in sorted(hist.items())))
    # b41 vs b43 agreement
    agree = sum(1 for r in valid if r[5] == r[7])
    print(f"b41==b43: {agree}/{len(valid)}")
    bycls = defaultdict(lambda: [0, 0])
    for r in valid:
        bycls[r[6]][0] += 1
        if r[5] == r[7]:
            bycls[r[6]][1] += 1
    for c in sorted(bycls):
        tot, eq = bycls[c]
        print(f"  class {c}: n={tot} b41==b43 {eq}")
    # ranges
    for label, idx in (("b41", 5), ("b43", 7), ("class", 6), ("w48", 8), ("ability", 3), ("domain", 4)):
        vals = sorted({r[idx] for r in valid})
        print(f"{label}: distinct={len(vals)} min={vals[0]} max={vals[-1]}")
    # zero rows
    z41 = [r for r in valid if r[5] == 0]
    z43 = [r for r in valid if r[7] == 0]
    print(f"b41==0: {len(z41)}   b43==0: {len(z43)}")


if __name__ == "__main__":
    main()
