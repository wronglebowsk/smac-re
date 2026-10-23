#!/usr/bin/env python3
"""Print one function's decompiled C out of the Ghidra batch export.

    scripts/fn.py 0x51e700          # exact address (any of 0x51e700 / 0051e700 / 5389568)
    scripts/fn.py e700              # unique suffix of an address
    scripts/fn.py FUN_0051e700      # exact function name
    scripts/fn.py --grep "turn"      # list functions whose NAME matches
    scripts/fn.py 0x51e700 --max 80  # cap the body at 80 lines

Why this exists: after `ExportAll.java` the whole corpus is on disk, so answering
"what does this function do" costs one grep instead of a ~205 s Ghidra session.
Headers in the shards look like:  // ==== FUN_0051e700 @ 0x51e700 size=402
"""
import argparse
import glob
import os
import re
import sys

OUT = os.environ.get("SMAC_OUT", os.path.expanduser("~/reverse/smac/ghidra_out"))
HDR = re.compile(r"^// ==== (\S+) @ (0x[0-9a-fA-F]+) size=(\d+)")


def index_rows():
    p = os.path.join(OUT, "index.csv")
    if not os.path.exists(p):
        return []
    with open(p) as f:
        head = f.readline().strip().split(",")
        # "#provenance ..." lines are export metadata stamped by scripts/ghidra_export.sh.
        return [dict(zip(head, line.rstrip("\n").split(","))) for line in f
                if line.strip() and not line.startswith("#")]


def resolve(tok):
    """Return (addr_int, name) for an address or an exact function name."""
    tok = tok.strip()
    rows = index_rows()
    if tok.lower().startswith("0x") or re.fullmatch(r"[0-9a-fA-F]{4,8}", tok):
        want = int(tok, 16) if not tok.lower().startswith("0x") else int(tok, 16)
        for r in rows:
            if int(r["addr"], 16) == want:
                return want, r["name"]
        # a 4-digit suffix such as e700
        hits = [r for r in rows if r["addr"].lower().endswith(tok.lower().lstrip("0x"))]
        if len(hits) == 1:
            return int(hits[0]["addr"], 16), hits[0]["name"]
        if len(hits) > 1:
            sys.exit("ambiguous address suffix: " + ", ".join(h["addr"] for h in hits[:8]))
        return want, None
    for r in rows:
        if r["name"] == tok:
            return int(r["addr"], 16), r["name"]
    sys.exit(f"no function named {tok}")


def body(addr, name, maxlines):
    want_addr = f"0x{addr:x}"
    out, on = [], False
    for shard in sorted(glob.glob(os.path.join(OUT, "shard_*.c"))):
        with open(shard, errors="replace") as f:
            for line in f:
                m = HDR.match(line)
                if m:
                    if on:
                        return out                      # next function starts
                    on = (int(m.group(2), 16) == addr)
                    if on:
                        out.append(line.rstrip())
                    continue
                if on:
                    out.append(line.rstrip())
                    if maxlines and len(out) >= maxlines:
                        return out
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("token", nargs="?", help="address or function name")
    ap.add_argument("--grep", help="list function names matching this regex")
    ap.add_argument("--max", type=int, default=0, help="max body lines (0 = all)")
    ap.add_argument("--index", action="store_true", help="print the index.csv row only")
    a = ap.parse_args()

    if a.grep:
        rows = index_rows()
        pat = re.compile(a.grep, re.I)
        hits = [r for r in rows if pat.search(r["name"])]
        print(f"{len(hits)} match(es)")
        for r in hits[:60]:
            print(f"  {r['addr']}  {r['name']:<28} size={r['size_bytes']:>6} "
                  f"callers={r['n_callers']:>3} insns={r['n_insns']}")
        return

    if not a.token:
        ap.error("need a token or --grep")

    addr, name = resolve(a.token)
    rows = [r for r in index_rows() if int(r["addr"], 16) == addr]
    if rows:
        r = rows[0]
        print("# " + ",".join(f"{k}={v}" for k, v in r.items()))
    if a.index:
        return
    lines = body(addr, name, a.max)
    if not lines:
        sys.exit(f"0x{addr:x} not found in the shards (export still running? see MANIFEST.txt)")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
