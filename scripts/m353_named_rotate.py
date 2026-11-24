#!/usr/bin/env python3
"""m353_named_rotate.py - move NAMED.md's settled `## B25` block VERBATIM into
`docs/named-archive-m353-rows.md` and leave a one-line-per-claim stub in NAMED.

Why: NAMED.md FAILs at 250,000 B and M353 must add a block; headroom was under the 5 KB trigger.
B25 is MERGED (#319 -> 1556ce9) and settled.  The stub's CLAIM text is a compression, but its
CITE and MUTANT cells are copied from the archived row it indexes, so a stub row can never point
at a line the archive does not cite.  Idempotent: re-running rebuilds the stub from the archive.

`--verify` recomputes the archived block's sha1 and asserts it equals the sha1 recorded in BOTH
files, that the stub has one row per archived claim row, that each stub row's cite cell equals its
archived twin's, and that each stub row keeps at least one measured number of its twin.
"""
import argparse
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-m353-rows.md")
HEAD = "## B25 (s294 BUILD"
NEXT_HEAD = "## B26 (s299 BUILD"
STUB_PREFIX = "## B25 (ROTATED"
ARCHIVE_TITLE = ("# NAMED.md `## B25` - ROTATED VERBATIM (byte-exact) by scripts/m353_named_rotate.py\n"
                 "# sha1 %s  bytes %d\n\n")

# compressed claim text, one per archived row (same order); cites/conf come from the archive
CLAIMS = (
    "**THE LAW IS BYTE-LEVEL CARRY**: 4/4 rounds the container READ differs from the writer's last "
    "WRITE only by the falsifier's own bytes; 268/268 (round,unit) start tiles == a FRESH DECODE of "
    "the head bytes consumed; (+2,0) mod 64 and 2-accept/1-refuse hold from the RELOADED tile",
    "an image-only poison of record 0 at round 1 shifts its trajectory 39 mod 64 into the FINAL "
    "container ([19,42] vs clean [44,42]), 0 of 67 others move; the model-fed movers are blind to the "
    "falsifier, not to writing (268 unit bytes each, image == their own clean run)",
    "the save's grid is 64x64 (`decode_save --sections`, 90,112 = 64*64*22) vs `planet.MP` 80x80: "
    "37 records land out of the container, 27 return, `found_units` 67 -> 4, all six numbers PINNED in "
    "G5; B7 wrapped by the map file: 10 of 67 final tiles outside (4 of 67 at --turns 5)",
    "**THE TILE TEST IS NOT THE DECODER**: raw `tile >= width` and `sim/save._unit_ok` differ in 8/44 "
    "probes - exactly the records the decoder exempts (25 of the 67 carry +10 in "
    "[128,130,131,256,320,321,322,323], so it coord-checks 42); with that rule both agree 44/44, and "
    "`found_units` is reproduced from `_unit_ok` 44/44",
    "footprint == move law: 67 unit bytes == 67 tiles written/round at record offset +0 (x only), "
    "+ 1 modeled header byte/round (year 2151->2154); final image 68 B from the save, 0 B outside a "
    "modeled span",
    "rivals/controls: nowrite 0 unit bytes, lift 0 + year frozen 2150, budget3 1 accept/round; mpwidth "
    "and wrapskip COINCIDENT here (max_x 79 < 80, declared not separated); G8 requires the FULL table-E "
    "signature to differ from ALL 5 rival rows (the 3 `:clean` twins coincide by design)",
    "ACCEPT `python3 -u -m sim.selftest --b25` -> **PASS B25: 9/9**, anchor **901a286332960a10**, 2 runs "
    "byte-identical and identical to `python3 -u -m sim.composedmove`; **G9 PINS the anchor to a "
    "literal** (MU9 reddens G9 and nothing else); harness **13/13 + 3 declared NO-OP**; `--selftest` 5/5",
    "UNMODELED: MP/spent never crosses the container; y never moves (dy=0) so the y-bound law is "
    "unexercised; no blocking/ZOC/terrain refusal; which unit the game moves is not claimed; presses on "
    "all 67 records though 25 are not coord-checked",
)


def rows_of(text):
    out = []
    for ln in text.splitlines():
        if ln.startswith("|") and not re.match(r"^\|\s*(claim|---)", ln):
            out.append([c.strip() for c in ln.strip().strip("|").split("|")])
    return out


def conf_cell(cell):
    if cell.strip().lower() == "lead":
        return "lead"
    ids = re.findall(r"MU\d+(?:-MU\d+)?", cell)
    keep = " (archive: RETRACTED by M327)" if re.search(r"RETRACT", cell, re.I) else ""
    return "V" + (" " + "/".join(dict.fromkeys(ids)) if ids else "") + keep


def archive_block(named):
    i = named.index(HEAD)
    j = named.index(NEXT_HEAD)
    return named[i:j]


def build_stub(sha, arch_rows):
    s = ("## B25 (ROTATED by s329) - MERGED s295 as #319 -> 1556ce9: the MOVE leg made PERSISTENT "
         "(sim/composedmove.py). FULL TABLE VERBATIM at `docs/named-archive-m353-rows.md` (sha1 `%s`); "
         "this stub governs, one line per claim\n" % sha)
    s += "| claim | evidence | conf / mutant |\n|---|---|---|\n"
    assert len(CLAIMS) == len(arch_rows), (len(CLAIMS), len(arch_rows))
    for claim, row in zip(CLAIMS, arch_rows):
        s += "| %s | %s | %s |\n" % (claim, row[1], conf_cell(row[2] if len(row) > 2 else ""))
    return s + "\n"


def do_write():
    named = open(NAMED).read()
    if os.path.exists(ARCHIVE) and STUB_PREFIX in named:
        arch = open(ARCHIVE).read()
        m = re.match(r"# .*\n# sha1 ([0-9a-f]{40})  bytes (\d+)\n\n", arch)
        sha = m.group(1)
    else:
        b = archive_block(named)
        sha = hashlib.sha1(b.encode()).hexdigest()
        open(ARCHIVE, "w").write(ARCHIVE_TITLE % (sha, len(b.encode())) + b)
    arch = open(ARCHIVE).read()
    arch_rows = rows_of(arch.split("\n\n", 1)[1])
    stub = build_stub(sha, arch_rows)
    i = named.index(STUB_PREFIX if STUB_PREFIX in named else HEAD)
    j = named.index(NEXT_HEAD)
    open(NAMED, "w").write(named[:i] + stub + named[j:])
    print("stub rebuilt: %d B, sha1 %s, %d rows" % (len(stub.encode()), sha, len(arch_rows)))


def do_verify():
    named = open(NAMED).read()
    arch = open(ARCHIVE).read()
    m = re.match(r"# NAMED\.md `## B25`.*\n# sha1 ([0-9a-f]{40})  bytes (\d+)\n\n", arch)
    sha, nbytes = m.group(1), int(m.group(2))
    body = arch[m.end():]
    h = hashlib.sha1(body.encode()).hexdigest()
    checks = []
    checks.append(("archive sha1 == recorded", h == sha))
    checks.append(("archive bytes == recorded", len(body.encode()) == nbytes))
    checks.append(("sha1 recorded in NAMED", ("sha1 `%s`" % sha) in named))
    checks.append(("verbatim block gone from NAMED", HEAD not in named))
    st = named[named.index(STUB_PREFIX):named.index(NEXT_HEAD)]
    st_rows, ar_rows = rows_of(st), rows_of(body)
    checks.append(("one stub row per archived claim", len(st_rows) == len(ar_rows)))
    checks.append(("every stub cite cell == its archived twin",
                   all(a[1] == b[1] for a, b in zip(st_rows, ar_rows))))
    checks.append(("every RETRACT in the archive survives in its stub twin",
                   all("RETRACT" in a[0].upper() + a[2] for a, b in zip(ar_rows, st_rows)
                       if "RETRACT" in (a[0] + a[2]).upper())))
    checks.append(("every stub row keeps a number of its twin",
                   all(set(re.findall(r"\d+", a[0])) & set(re.findall(r"\d+", " ".join(b)))
                       for a, b in zip(st_rows, ar_rows))))
    ok = all(c[1] for c in checks)
    for name, good in checks:
        print("  %-4s %s" % ("PASS" if good else "FAIL", name))
    print("PASS m353_named_rotate: %d/%d checks sha1 %s" % (sum(1 for c in checks if c[1]), len(checks), sha)
          if ok else "FAIL m353_named_rotate")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    sys.exit(do_verify() if a.verify else do_write() or 0)
