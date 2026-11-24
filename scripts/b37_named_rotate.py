#!/usr/bin/env python3
"""b37_named_rotate.py - move NAMED.md's settled `## B19` block VERBATIM into
`docs/named-archive-b19-rows.md` and leave a one-line-per-claim stub in NAMED.

B37 must add a block and NAMED.md is 248,265 B against a 250,000 B FAIL (1,735 B of headroom,
under the 5 KB trigger).  B19 is a settled BUILD rung - the visit-counter model is superseded by
B20-B37 and its lead is already archived.  The rotated text is byte-for-byte what NAMED carried;
the stub repeats every claim on one line with the same evidence pointer, so a grep of NAMED still
lands on a file:line.

    python3 scripts/b37_named_rotate.py            # rotate (idempotent if already done)
    python3 scripts/b37_named_rotate.py --verify   # sha1 byte-exactness + claim tokens
"""
import argparse
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-b19-rows.md")
HEAD = "## B19 (s257"
ARCHIVE_HEAD = "# NAMED.md `## B19` - ROTATED VERBATIM (byte-exact) by scripts/b37_named_rotate.py\n"

STUB = """## B19 (s257, BUILD 10/10) - ROTATED VERBATIM to `docs/named-archive-b19-rows.md` (sha1 `%s`): the slot [+4] visit counter is executable (`sim/visitcounter.py`). One line per claim, each with its full `path:line`.
- GATED INC: `[0x989ce8+28*site+4]++` IFF `FUN_005832b0(x,y) != 0`@0x51dffd; inc block 0x51e00d-0x51e01b entered ONLY by fall-through (`je 0x51e11d`); field DECODES to MAX +4 on the pinned 28-B esi; two agreeing impls + the recorded 36/36 theorem - V (`evidence/b19_visitcounter.txt:10`, `evidence/b19_visitcounter.txt:13`, `evidence/m299_visitgate.txt:5`, `evidence/m299_visitgate.txt:52`)
- REPLAY 2321 rows: sites {1:2253, 9:68} == B18 anchor; census {'branchA':1099,'rung1':1222}; 1222 CERTAIN-refuse / 0 accept / 1099 possible; baseline = 20 eax=2, 1079 undecided; eax=1 STRUCTURAL-ONLY (0 rows) - V law, LIVE side OPEN (`evidence/b19_visitcounter.txt:5-9`, `evidence/b19_visitcounter.txt:17-18`)
- M300/M301 re-graded in-sim: 21/2/1 and 17/1/6, one IN-WRITER 0x51dffd line-for-line, 0 backward edges - V (`evidence/b19_visitcounter.txt:15-16`, `evidence/m300_callers.txt`, `evidence/m301_ebxtable.txt`)
- DECLARED UNMODELED: live ds:0x92a380 / 0x69220c / 0x692210 / 0x985ac4-bit2000; counter-table CONTENTS; 0x51e02c 0x94ed28; which REACHES callers run - lead (`evidence/m299_visitgate.txt:175-178`, `evidence/b19_visitcounter.txt:14`, `evidence/b19_visitcounter.txt:18`)
- ACCEPTANCE `python3 -m sim.selftest --b19 programs/saves/m54b_clean.SAV` -> **PASS B19: 10/10**, two runs byte-identical - V (`evidence/b19_visitcounter.txt:20`)
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
            raise SystemExit("FAIL: no sha1 in the B19 stub")
        if sha1(body) != m.group(1):
            raise SystemExit("FAIL: archived block sha1 != stub sha1 (%s vs %s)"
                             % (sha1(body), m.group(1)))
        claims = [ln for ln in body.splitlines()
                  if ln.startswith("| ") and not ln.startswith("|---") and "| claim |" not in ln]
        bullets = [ln for ln in stub.splitlines() if ln.startswith("- ")]
        if len(bullets) != len(claims):
            raise SystemExit("FAIL: stub carries %d claim bullets for %d archived rows"
                             % (len(bullets), len(claims)))
        refs = sorted({"%s:%s" % (f, ln) for c in claims
                       for f, ln in re.findall(r"([\w/\.\-]+\.txt):([0-9]+(?:-[0-9]+)?)", c)})
        missing = [r for r in refs if r not in stub]
        if missing:
            raise SystemExit("FAIL: stub drops the archived full citations %s" % missing)
        bare = re.findall(r"`:(?:\d[0-9,\-]*)`", stub)
        if bare:
            raise SystemExit("FAIL: stub carries bare section-relative cites %s" % bare)
        print("PASS b37_named_rotate --verify: sha1 %s, %d archived claim rows == %d stub bullets, "
              "%d full path:line cites carried, 0 bare"
              % (m.group(1), len(claims), len(bullets), len(refs)))
        return 0

    body = block(named, HEAD)
    if "ROTATED VERBATIM" in body:
        raise SystemExit("B19 already rotated (stub present)")
    if not body.strip():
        raise SystemExit("FAIL: `## B19` block not found in NAMED.md")
    s = sha1(body)
    with open(ARCHIVE, "w", encoding="utf-8") as fh:
        fh.write(ARCHIVE_HEAD + "\n" + body)
    new = named.replace(body, STUB % s)
    if new == named:
        raise SystemExit("FAIL: replacement was a no-op")
    if len(new.encode("utf-8")) >= len(named.encode("utf-8")):
        raise SystemExit("FAIL: rotation did not shrink NAMED.md (%d -> %d B)"
                         % (len(named.encode("utf-8")), len(new.encode("utf-8"))))
    with open(NAMED, "w", encoding="utf-8") as fh:
        fh.write(new)
    print("rotated `## B19` (%d B) -> docs/named-archive-b19-rows.md  sha1 %s" % (len(body), s))
    print("NAMED.md %d -> %d B" % (len(named.encode("utf-8")), len(new.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
