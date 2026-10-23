#!/usr/bin/env python3
"""Turn ghidra_out/index.csv into COVERAGE.md — the map of the corpus.

Answers, without opening Ghidra:
  * how much of terran.exe is decompiled, and how big is it really
  * which functions are the hubs (most callers) and the monsters (most code)
  * which functions are already written up in this repo (dumps / findings)
  * what to read next, ranked

    scripts/coverage.py                 # writes ~/reverse/smac/COVERAGE.md
    scripts/coverage.py --top 40 --print
"""
import argparse
import csv
import glob
import os
import re
import time

ROOT = os.path.expanduser("~/reverse/smac")
FUN_RE = re.compile(r"FUN_([0-9a-fA-F]{8})")


def load(path):
    with open(path) as f:
        # The trailing "#provenance ..." line is export metadata stamped by
        # scripts/ghidra_export.sh, not a function row.
        return [r for r in csv.DictReader(f) if not (r["addr"] or "").startswith("#")]


def known_functions():
    """Addresses we already have a Ghidra dump or a writeup line for."""
    have = set()
    for p in glob.glob(os.path.join(ROOT, "*.pseudocode.txt")) + glob.glob(os.path.join(ROOT, "*.asm.txt")):
        for m in FUN_RE.finditer(os.path.basename(p)):
            have.add(int(m.group(1), 16))
        try:
            with open(p, errors="replace") as f:
                for line in f:
                    for m in FUN_RE.finditer(line):
                        have.add(int(m.group(1), 16))
        except OSError:
            pass
    return have


def bucket(n, edges):
    for lo, hi, label in edges:
        if lo <= n < hi:
            return label
    return "?"


SIZE_EDGES = [(0, 16, "tiny <16B"), (16, 64, "16-63B"), (64, 256, "64-255B"),
              (256, 1024, "256B-1K"), (1024, 4096, "1-4K"), (4096, 10 ** 9, ">4K")]
CALL_EDGES = [(0, 1, "0 callers"), (1, 3, "1-2"), (3, 10, "3-9"),
              (10, 50, "10-49"), (50, 200, "50-199"), (200, 10 ** 9, "200+")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default=os.path.join(ROOT, "ghidra_out/index.csv"))
    ap.add_argument("--out", default=os.path.join(ROOT, "COVERAGE.md"))
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--print", action="store_true")
    a = ap.parse_args()

    if not os.path.exists(a.index):
        raise SystemExit(f"no index at {a.index} — the export has not finished yet")

    rows = load(a.index)
    for r in rows:
        for k in ("size_bytes", "n_insns", "n_callers", "n_callees", "n_strings"):
            r[k] = int(r[k])
        r["addr_i"] = int(r["addr"], 16)
    ok = [r for r in rows if r["ok"] == "1"]
    known = known_functions()
    manifest = {}
    mp = os.path.join(os.path.dirname(a.index), "MANIFEST.txt")
    if os.path.exists(mp):
        for line in open(mp):
            if ":" in line:
                k, v = line.split(":", 1)
                manifest[k.strip()] = v.strip()

    def cls(r):
        n = r["name"]
        if n.startswith("thunk_"):
            return "thunk"
        if n.startswith("FUN_"):
            return "unnamed (FUN_)"
        if n in ("entry", "_WinMainCRTStartup") or n.startswith("__"):
            return "runtime/CRT"
        return "named"

    by_cls = {}
    for r in rows:
        by_cls[cls(r)] = by_cls.get(cls(r), 0) + 1
    by_size, by_call = {}, {}
    for r in rows:
        by_size[bucket(r["size_bytes"], SIZE_EDGES)] = by_size.get(bucket(r["size_bytes"], SIZE_EDGES), 0) + 1
        by_call[bucket(r["n_callers"], CALL_EDGES)] = by_call.get(bucket(r["n_callers"], CALL_EDGES), 0) + 1

    # Compiler runtime helpers (__security_check_cookie, _ftol2, _chkstk, ...) have
    # hundreds-to-thousands of callers and a few dozen bytes: they top any in-degree
    # ranking and mean nothing about the game. Separate them out explicitly.
    helpers = sorted([r for r in rows if r["n_callers"] >= 300 and r["size_bytes"] < 400],
                     key=lambda r: -r["n_callers"])
    hub_pool = [r for r in rows if r not in helpers and r["size_bytes"] >= 64]
    hubs = sorted(hub_pool, key=lambda r: (-r["n_callers"], -r["n_insns"]))[: a.top]
    monsters = sorted(rows, key=lambda r: -r["size_bytes"])[:20]
    ranked = sorted(rows, key=lambda r: -(2 * r["n_callers"] + r["n_insns"] / 40 + 3 * r["n_strings"]))[: a.top]

    L = []
    add = L.append
    add("# COVERAGE — terran.exe")
    add("")
    add(f"Generated {time.strftime('%Y-%m-%d %H:%M')} by `scripts/coverage.py` from "
        f"`ghidra_out/index.csv`.")
    add("")
    add("## Corpus")
    add(f"- functions in database: **{len(rows)}**")
    add(f"- decompiled cleanly: **{len(ok)}** ({100.0 * len(ok) / max(len(rows), 1):.1f}%)")
    add(f"- total decompiled C: **{sum(r['size_bytes'] for r in rows) / 1e6:.2f} M bytes of code** "
        f"({sum(r['n_insns'] for r in rows)} instructions)")
    add(f"- shards: {manifest.get('shards', '?')} (`ghidra_out/shard_NNN.c`, 250 functions each)")
    add(f"- mentioned in an existing dump/writeup (upper bound, text search): "
        f"**{len([r for r in rows if r['addr_i'] in known])}** functions")
    add("")
    add("## By name class")
    for k, v in sorted(by_cls.items(), key=lambda kv: -kv[1]):
        add(f"- {k}: {v}")
    add("")
    add("## Size distribution")
    for lo, hi, label in SIZE_EDGES:
        add(f"- {label}: {by_size.get(label, 0)}")
    add("")
    add("## Caller distribution (in-degree: how much code depends on it)")
    for lo, hi, label in CALL_EDGES:
        add(f"- {label}: {by_call.get(label, 0)}")
    add("")
    add(f"### Compiler/runtime helpers excluded from rankings ({len(helpers)} found)")
    add("")
    for r in helpers[:12]:
        add(f"- {r['addr']} {r['name']} — {r['n_callers']} callers, {r['size_bytes']} B")
    add("")
    add(f"## Top {a.top} hubs by caller count (helpers excluded)")
    add("")
    add("| addr | name | callers | insns | size | strings |")
    add("|---|---|---|---|---|---|")
    for r in hubs:
        mark = " *" if r["addr_i"] in known else ""
        add(f"| {r['addr']} | {r['name']}{mark} | {r['n_callers']} | {r['n_insns']} | "
            f"{r['size_bytes']} | {r['n_strings']} |")
    add("")
    add("`*` = already has a dump/writeup in this repo.")
    add("")
    add("## Largest functions")
    add("")
    add("| addr | name | size | insns | callers |")
    add("|---|---|---|---|---|")
    for r in monsters:
        add(f"| {r['addr']} | {r['name']} | {r['size_bytes']} | {r['n_insns']} | {r['n_callers']} |")
    add("")
    add(f"## Read next (score = 2*callers + insns/40 + 3*string-refs)")
    add("")
    add("| addr | name | score | callers | insns | strings |")
    add("|---|---|---|---|---|---|")
    for r in ranked:
        score = 2 * r["n_callers"] + r["n_insns"] / 40 + 3 * r["n_strings"]
        add(f"| {r['addr']} | {r['name']} | {score:.0f} | {r['n_callers']} | {r['n_insns']} | {r['n_strings']} |")
    add("")
    add("## How to read code from here on")
    add("```")
    add("scripts/fn.py 0x51e700            # decompiled C for one function")
    add("scripts/fn.py --grep 'turn'       # find functions by name")
    add("scripts/fn.py 0x51e700 --max 80   # just the top of a big function")
    add("```")
    add("Shards are ordered by address; a function body runs until the next `// ==== ` header.")

    text = "\n".join(L) + "\n"
    with open(a.out, "w") as f:
        f.write(text)
    print(f"wrote {a.out}: {len(rows)} functions, {len(ok)} decompiled, {len(hubs)} hubs listed")
    if a.print:
        print(text)


if __name__ == "__main__":
    main()
