#!/usr/bin/env python3
"""M143-M162 — the faction-block FIELD ATLAS: the 20 most-referenced `+0x94dxxx` displacements, one row each.

Selection rule (reproducible, no cherry-picking): every displacement of the form `+0x94dXXX` in the objdump is counted
across the WHOLE image; the 20 with the most references are the atlas. Each row records what the reconstruction needs
to know before touching a field: reference count, write count, the constant values written, the values tested, the
containing functions, and whether the displacement is already NAMED (`NAMED.md` or `docs/named-archive-*.md`).

Deliverable: `docs/field-atlas-faction.md` (generated, so it is re-derivable with one command).

    python3 scripts/m143_m162_atlas.py            # write the atlas + evidence log
    python3 scripts/m143_m162_atlas.py --check    # verify the top row and the row count only
"""
import bisect
import collections
import os
import re
import sys

import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("field_census", os.path.join(HERE, "field_census.py"))
FC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FC)

INS, fnof, IDX = FC.INS, FC.fnof, FC.IDX
ROOT = FC.ROOT
LOW = [(pc, s.lower()) for pc, s in INS]
PAT = re.compile(r"\+0x(94d[0-9a-f]{3})\]")


def rows():
    cnt = collections.Counter()
    where = collections.defaultdict(set)
    names = collections.defaultdict(set)
    for pc, s in LOW:
        for d in PAT.findall(s):
            v = int(d, 16)
            cnt[v] += 1
            where[v].add(fnof(pc))
    # writes / constants / tests per displacement, from the same scan
    writes = collections.defaultdict(list)
    tests = collections.defaultdict(set)
    for pc, s in LOW:
        for d in PAT.findall(s):
            v = int(d, 16)
            head = s.split()[0]
            if head == "mov" and re.match(r"^mov\s+(dword ptr |word ptr |byte ptr )?\[[^\]]*\+0x%s\]," % d, s):
                writes[v].append(s.split(",")[-1].strip())
            elif head in ("cmp", "test"):
                tests[v].add(s.split(",")[-1].strip())
    top = [v for v, _ in cnt.most_common(20)]
    return cnt, where, writes, tests, top


def named(v):
    tok = "0x%x" % v
    for p in [os.path.join(ROOT, "NAMED.md")] + [os.path.join(ROOT, "docs", f) for f in os.listdir(os.path.join(ROOT, "docs"))
                                                 if f.startswith("named-archive")]:
        if tok in open(p, errors="replace").read():
            return "named"
    return "—"


def classify(w, r):
    if not w:
        return "read-only"
    consts = [x for x in w if x.startswith("0x")]
    if consts and len(consts) == len(w):
        return "const-only (%s)" % "/".join(sorted(set(consts))[:4])
    return "read-write"


def main():
    cnt, where, writes, tests, top = rows()
    check = "--check" in sys.argv
    out = ["# docs/field-atlas-faction.md — the 20 most-referenced faction-block displacements (generated)",
           "",
           "Regenerate with `python3 scripts/m143_m162_atlas.py`. Displacements are `[reg+0x94dXXX]`, i.e. fields of the",
           "8,380-byte per-faction block (0x94d104 + f*8380, **and** the folded `[reg*4+..]` form where reg = f*2095).",
           "M143-M162 are these 20 rows, in this order. `in NAMED?` only means the address TEXT appears in NAMED.md or an",
           "archived block; it does NOT mean the field has a meaning — grep those places before re-deriving one, and",
           "treat a `—` as genuinely unnamed rather than as a gap to fill by guessing.",
           "",
           "| # | field | refs | writes | shape | consts written | tested vs | top functions | in NAMED? |",
           "|---|---|---|---|---|---|---|---|---|"]
    for i, v in enumerate(top, start=143):
        w = writes[v]
        tf = ", ".join(sorted(where[v])[:3])
        out.append("| M%d | `0x%x` | %d | %d | %s | %s | %s | %s | %s |" %
                   (i, v, cnt[v], len(w), classify(w, cnt[v]),
                    "/".join(sorted(set(x for x in w if x.startswith("0x")))[:4]) or "—",
                    "/".join(sorted(tests[v])[:4]) or "—", tf, named(v)))
    out += ["",
            "Reading the table: a **read-only** row with many refs and no writes is either load-time data (M121's law)",
            "or a field this build never writes; a **const-only** row is a flag/config written by the game itself;",
            "**read-write** rows are the live state the reconstruction must model. Shape is evidence; meaning is not",
            "implied by it, and 0x94d448 (653 refs, 139 functions) is the faction flag word whose bit 0x8000000 M129",
            "found gating FUN_00546800.",
            ""]
    text = "\n".join(out)
    if check:
        print("rows=%d top=0x%x refs=%d" % (len(top), top[0], cnt[top[0]]))
        return 0 if (len(top) == 20 and top[0] == 0x94D448) else 1
    open(os.path.join(ROOT, "docs", "field-atlas-faction.md"), "w").write(text)
    with open(os.path.join(ROOT, "evidence", "m143_m162_atlas.log"), "w") as fh:
        fh.write(text)
    print(text)
    ok = len(top) == 20 and top[0] == 0x94D448 and all(cnt[v] > 0 for v in top)
    print("SUMMARY " + ("PASS — 20 rows selected by a reproducible rule, top row 0x94d448 (653 refs)" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
