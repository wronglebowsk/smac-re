#!/usr/bin/env python3
"""b34_named_rotate.py - move NAMED.md's settled `## B22` block VERBATIM into
`docs/named-archive-b22-rows.md` and leave a one-line-per-claim stub in NAMED.

B34 must add a block and NAMED.md is 247,680 B against a 250,000 B FAIL (2,320 B of
headroom, under the 5 KB trigger).  B22 is a settled BUILD rung (its R2 growth leg is
superseded by B24-B33 and its retraction already lives in the archive byte-exactly).
The rotated text is byte-for-byte what NAMED carried; the stub repeats every claim on one
line with the same evidence pointer, so a grep of NAMED still lands on a file:line.

    python3 scripts/b34_named_rotate.py            # rotate (idempotent if already done)
    python3 scripts/b34_named_rotate.py --verify   # sha1 byte-exactness + claim tokens
"""
import argparse
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-b22-rows.md")
HEAD = "## B22 (s273"
ARCHIVE_HEAD = "# NAMED.md `## B22` - ROTATED VERBATIM (byte-exact) by scripts/b34_named_rotate.py\n"

STUB = """## B22 (s273, BUILD 12/12, zero box) - ROTATED VERBATIM to `docs/named-archive-b22-rows.md` (sha1 `%s`): BOTH save record arrays grow in ONE writer call and the CREATE leg reads its ARGUMENTS out of the reloaded image. One line per claim.
- ONE WRITE GROWS BOTH ARRAYS: +1572 B = 5x304 + 52 over the untouched save; bands `[units 3484][new unit 52][bases 5472][grown 1520][tail 10800]` each byte-equal to its source; the uniform-lift draft was FALSE - V (`evidence/b22_composedgrowth.txt:8`)
- THE SHAPE LOCATOR CANNOT SEE A FOUNDED BASE: 18 of 23 named bases confirm; an empty name span fails `_base_ok`; growth is locatable by COUNT, `units_off` is DERIVED from `bases_off` - V (`:6,9`)
- COUNT AND SHAPE AGREE on all three containers; RETRACTED: the first draft's 52-B disagreement was a 68-vs-67 unit count (Greptile P1 #286) - V (`:9`)
- INBOUND HALF via ONE producer `record_from_image`: B12's CREATE leg takes tile+faction from the RELOADED base[22]; FALSIFIER - corrupted image bytes (1447,1448, fac 5A) are carried - V (`:7,13`)
- THE FALSIFIER IS LOAD-BEARING every run: rebinding the leg to the MODEL collapses G9 onto G3; G3 is DECLARED blind in this fixture - V (`:15`)
- HEADER DIFF IS EXACTLY 3 BYTES (0x44 n_units, 0x48 n_bases, 0x54 year), not the decorated 4 - V (`:11`)
- RE-PARSE CLOSES: 67->68 units, 23 bases, originals byte-identical, new record at the array END, tail +1572 B - V (`:12`)
- RIVALS FAIL: unit-only growth re-derives 18 bases; idle order-2 record is not the produced one; a perturbed stride mis-places the tail (244245 != 244111) - V (`:14`)
- ACCEPTANCE `python3 -m sim.selftest --b22` -> PASS B22: 12/12, image sha256 f7d90eb77ca7abac, two runs identical - V (`:15-20`)
- UNMODELED (declared): WHICH base ran the completion (fixture); the created record's unmodeled bytes; the founding's economy/research - lead
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
            raise SystemExit("FAIL: no sha1 in the B22 stub")
        if sha1(body) != m.group(1):
            raise SystemExit("FAIL: archived block sha1 != stub sha1 (%s vs %s)"
                             % (sha1(body), m.group(1)))
        claims = [ln for ln in body.splitlines()
                  if ln.startswith("| ") and not ln.startswith("|---") and "| claim |" not in ln]
        bullets = [ln for ln in stub.splitlines() if ln.startswith("- ")]
        if len(bullets) != len(claims):
            raise SystemExit("FAIL: stub carries %d claim bullets for %d archived rows"
                             % (len(bullets), len(claims)))
        refs = sorted({r for c in claims for r in re.findall(r"`?:([0-9][0-9,\-]*)", c)})
        missing = [r for r in refs if (":%s" % r) not in stub]
        if missing:
            raise SystemExit("FAIL: stub drops the archived line cites %s" % missing)
        print("PASS b34_named_rotate --verify: sha1 %s, %d archived claim rows == %d stub bullets, "
              "%d line cites carried" % (m.group(1), len(claims), len(bullets), len(refs)))
        return 0

    body = block(named, HEAD)
    if not body.strip():
        raise SystemExit("FAIL: `## B22` block not found in NAMED.md")
    s = sha1(body)
    with open(ARCHIVE, "w", encoding="utf-8") as fh:
        fh.write(ARCHIVE_HEAD + "\n" + body)
    stub = STUB % s
    new = named.replace(body, stub)
    if new == named:
        raise SystemExit("FAIL: replacement was a no-op")
    if len(new.encode("utf-8")) >= len(named.encode("utf-8")):
        raise SystemExit("FAIL: rotation did not shrink NAMED.md (%d -> %d B)"
                         % (len(named.encode("utf-8")), len(new.encode("utf-8"))))
    with open(NAMED, "w", encoding="utf-8") as fh:
        fh.write(new)
    print("rotated `## B22` (%d B) -> docs/named-archive-b22-rows.md  sha1 %s" % (len(body), s))
    print("NAMED.md %d -> %d B" % (len(named.encode("utf-8")), len(new.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
