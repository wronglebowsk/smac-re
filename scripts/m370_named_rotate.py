#!/usr/bin/env python3
"""m370_named_rotate.py - move NAMED.md's `## M332` block VERBATIM into
`docs/named-archive-m370-rows.md` and leave a one-line-per-claim stub in NAMED.

M370 must add a block and NAMED.md is 248,819 B against the 250,000 B cap (1,181 B of
headroom, under the 5 KB trigger).  M332 is the predecessor question: its last row is the
OPEN lead "the other writers of the 0x92bde8..0x92bf14 block", which M370 now answers, so
the block is rotated and its stub carries the refinement.  The rotated text is byte-for-byte
what NAMED carried.

    python3 scripts/m370_named_rotate.py            # rotate (refuses a non-shrinking run)
    python3 scripts/m370_named_rotate.py --verify   # sha1 byte-exactness + claim tokens
"""
import argparse
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-m370-rows.md")
HEAD = "## M332 (s311-chain1"
ARCHIVE_HEAD = ("# NAMED.md `## M332` - ROTATED VERBATIM (byte-exact) by "
                "scripts/m370_named_rotate.py\n")

STUB = """## M332 (s311-chain1, ROTATED VERBATIM to `docs/named-archive-m370-rows.md` sha1 `%s`; the block's OPEN lead is ANSWERED by `## M370`) - `ds:0x985aec` is the RUNTIME MIRROR of the INI `Difficulty` pref; one line per claim.
- 68 refs = 4 store / 40 load / 24 cmp, cmp arms exactly {1,2,3,4}; scope: a store through a runtime-computed pointer is invisible to both scans - V (`:101` + G9.1 `:80-81`)
- store set exact {0x4ddcf1,0x57c5af,0x57c7b5,0x57f006}, every one a moffs `a3` - V (`:102`)
- 0x4ddcf1 has no fall-in; `jge` at 0x4ddb5a takes 0x5f1394's eax -> M308's UNATTRIBUTED CLOSED - V (`:103` + G9.2 `:82-83`)
- clean-copy map = 5 directions over 6 pairs, each pinned to site AND window; master -> runtime - V (`:104` + G9.4 `:87-93`)
- the pref table: 11 key-exclusive 6-arg reads in FUN_0058e7f0, an INJECTIVE name->field map, `Difficulty`@0x58e8a1 -> 0x92bde8@0x58e8c6 - V (`:105-107` + `:51-53`, `:68`, G9.5 `:94-97`)
- siblings named by the same map: 0x92bdf4 = `Map Type`, 0x92bdf8 = `Top Menu`, 0x92bdec = `Faction` - V (`:106-107`)
- RIVAL KILLED: 0x92bde8 is BOTH the end of the 4x0xd4 array at 0x92ba98 AND a scalar pref cell - V (`:108` + G9.6 `:98-100`)
- ACCEPT `PASS M332: 9/9` digest `d2691dc5abb39240` (`evidence/m332_difficulty_census.txt:110-111`); harness 20 scored + 1 NO-OP `a9a944201849d026` (`evidence/m332_mutate.txt:25`) - V
- OPEN, now ANSWERED by `## M370`: the other writers of the 0x92bde8..0x92bf14 block (11 cells, 43 stores, 32 non-loader); 0x5f1394's semantics stay chain-2's - lead
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
            raise SystemExit("FAIL: no sha1 in the M332 stub")
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
        print("PASS m370_named_rotate --verify: sha1 %s, %d archived claim rows == %d stub bullets, "
              "%d line cites carried" % (m.group(1), len(claims), len(bullets), len(refs)))
        return 0

    body = block(named, HEAD)
    if not body.strip():
        raise SystemExit("FAIL: `## M332` block not found in NAMED.md")
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
    print("rotated `## M332` (%d B) -> docs/named-archive-m370-rows.md  sha1 %s"
          % (len(body.encode("utf-8")), s))
    print("NAMED.md %d -> %d B" % (len(named.encode("utf-8")), len(new.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
