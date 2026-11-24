#!/usr/bin/env python3
"""b33_named_rotate.py - move NAMED.md's settled `## M333` block VERBATIM into
`docs/named-archive-b33-rows.md` and leave a one-line-per-claim stub in NAMED.

Why: NAMED.md is 245,616 B against a 250,000 B FAIL and B33 must add a block; the
headroom was under the 5 KB trigger.  The rotated text is byte-for-byte what NAMED
carried; the stub repeats every claim on one line with the same gate/mutant tokens and
the same evidence pointer, so a grep of NAMED still lands on a file:line.

    python3 scripts/b33_named_rotate.py            # rotate (idempotent if already done)
    python3 scripts/b33_named_rotate.py --verify   # sha1 byte-exactness + claim tokens
"""
import argparse
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-b33-rows.md")
HEAD = "## M333 (s314"
ARCHIVE_HEAD = "# NAMED.md `## M333` - ROTATED VERBATIM (byte-exact) by scripts/b33_named_rotate.py\n"
SHA = "__SHA__"          # filled on the first run, then verified

STUB = """## M333 (s314, STATIC, zero box) - ROTATED VERBATIM to `docs/named-archive-b33-rows.md` (sha1 `%s`): the 34 feeder slots `0x984d48+48*item` - the slot NOUN = a facility the base HAS; bit5 of faction block+0 is a CARRIED HALF-UNIT exclusive to FUN_004f47f0. This stub governs, one line per claim.
- ACCEPT `scripts/m333_feeder_slot_census.py` 8/8 `70376694feec5815`; harness 18/18 `dee04978a5b5dd09`; selftest 6/6 (`evidence/m333_feeder_slot_census.txt:58-59`, `evidence/m333_mutate.txt:20-21`).
- G1+G7 (MU1/MU2/MU5/MU6/MU14/ME1): the loop counter `esi` IS the item id; the top test skips 35..38, the back-edge charges 1..34; the x48 fold is SHAPE-pinned.
- G3 (MU8/MU12/ME1): a slot is charged only when its bitmap bit is set - and the bit is the mapper's mask for THIS item, so the slot noun is a facility the base HAS.
- G4 (MU3/MU4/MU10/MU13/ME2): bit5 of `block[owner]+0` is a CARRIED HALF-UNIT, added to the cost; `sar 1` is the charge and the parity is written back.
- G5+RIVAL-R2 (MU3/MU4/ME2/ME3): FUN_004f47f0 is the ONLY function reading AND writing bit5 of a block+0 value.
- G6 (MU7/MU11): `ds:0x985ba0` has no writer in .text (noun INFERRED); QUALIFIED by B28 - the dword IS carried (save header 244, `-1`) so the halving is measured INERT.
- G2 (MU9/ME1): FUN_004f4760(item, faction) is the SAME law standalone.
- OPEN LEAD: the removal path (`0x4f49b6`, bit-clear `0x4f49e1`, 3 stores `block+0x220`) - pick (x7).
"""


def block(text, head):
    lines = text.splitlines(keepends=True)
    start = next(i for i, ln in enumerate(lines) if ln.startswith(head))
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return "".join(lines[start:end])


def sha1(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args(argv)
    named = open(NAMED, encoding="utf-8").read()

    if args.verify:
        arch = open(ARCHIVE, encoding="utf-8").read()
        body = arch.split("\n", 2)[2]
        stub = block(named, HEAD)
        m = re.search(r"sha1 `([0-9a-f]{40})`", stub)
        if not m:
            raise SystemExit("FAIL: no sha1 in the M333 stub")
        if sha1(body) != m.group(1):
            raise SystemExit("FAIL: archived block sha1 != stub sha1 (%s vs %s)"
                             % (sha1(body), m.group(1)))
        tokens = set(re.findall(r"(G[1-9]\+?G?[0-9]*|MU[0-9]+|ME[0-9]+|RIVAL-R2)", body))
        missing = sorted(t for t in tokens if t not in named)
        if missing:
            raise SystemExit("FAIL: stub drops claim tokens %s" % missing)
        if not named.count("## M333 "):
            raise SystemExit("FAIL: stub missing")
        print("OK bytes=%d sha1=%s tokens=%d" % (len(body.encode()), m.group(1), len(tokens)))
        return 0

    if "ROTATED VERBATIM to `docs/named-archive-b33-rows.md`" in named:
        print("already rotated; run --verify")
        return 0
    body = block(named, HEAD)
    digest = sha1(body)
    with open(ARCHIVE, "w", encoding="utf-8") as fh:
        fh.write(ARCHIVE_HEAD + "\n" + body)
    named = named.replace(body, STUB % digest, 1)
    with open(NAMED, "w", encoding="utf-8") as fh:
        fh.write(named)
    print("rotated %d B -> %s (sha1 %s); NAMED now %d B"
          % (len(body.encode()), os.path.relpath(ARCHIVE, ROOT), digest, len(named.encode())))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
