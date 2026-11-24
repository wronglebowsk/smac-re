#!/usr/bin/env python3
"""M343 headroom rotation: move the settled M341 block VERBATIM out of NAMED.md.

M343 added its block and NAMED.md dropped under the kickoff's 5 KB rotate-first
trigger (250,000 B cap), so the M341 block (settled: s321-chain2, static, zero
box, 11/11 + harness 19/19, cited only by its own session) moves byte-exactly
into `docs/named-archive-m343-rows.md`; NAMED.md keeps a stub with the ACCEPT
header and ONE LINE PER CLAIM.  The moved region's sha1 is PINNED and
`--verify` re-asserts it.

  python3 scripts/m343_named_rotate.py            # do the move (no-op once done)
  python3 scripts/m343_named_rotate.py --verify   # re-assert sha1 + full block absence
"""
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-m343-rows.md")
EXPECT_SHA1 = "bcf9ba24a3eb4efb55182f0b655fcf5f72ab2ad3"
START = "## M341 (s321-chain2, STATIC 10/10)"
END = "## M343 (s323-chain2"
HEADER = ("# NAMED archive - M343 headroom rotation (s323-chain2): the M341 block VERBATIM\n"
          "(moved by `scripts/m343_named_rotate.py`; the region's sha1 is pinned to `%s` -\n"
          "run `--verify` after any edit; NAMED.md's stub keeps the ACCEPT header + one line per claim)\n\n")

STUB = """## M341 (s321-chain2, STATIC 10/10; ACCEPT `python3 -u scripts/m341_hof_window.py` -> `PASS M341: 11/11`, `digest=1cfdea39295dadce`, 2 runs identical; harness `scripts/m341_mutate.py` 19/19 `e1c003e81552f53f`) - the HoF record window is `5*n - 5 + s`: THREE .text sites decode to the same law, so the 35 records at 0x983a10 are 7 blocks x 5 rows and page index 8 lands on the terminator. FULL-LENGTH TABLE VERBATIM at `docs/named-archive-m343-rows.md:5` (sha1 `%s`); this stub governs, one line per claim

| # | claim (one line) | conf |
|---|---|---|
| 1 | SITE A 0x449793/96 = `5*[obj+0x59f4] + [obj+0xa918] - 5`, 0 other ebx defs | V |
| 2 | SITE B 0x44af9b/9e = `5*[obj+0xa4c] + slot - 5`; `[obj+0xa4c]` <- `ds:0x91b5b4` at 0x44aed9 | V |
| 3 | SITE C 0x44b5a7..b9 insert-shift: dst = src + 0x8c, k in {0..3} | V |
| 4 | extent: base 0x983a10 / stride 0x8c / 35 records = 7x5 / index 35 = terminator 0x984d34 | V |
| 5 | NO CLAMP: the only direct 0x59f4 ref in 781,379 insns is the load 0x44970f | V |
| 6 | the 6-probe loop tests COLUMNS of ONE record (reload 0x449982), 6 != rows | V |
| 7 | OPEN: +0x59f4's writer (lead: a control at obj+0x5970); page 1..7 = faction block is INFERRED | lead |
"""

def region(lines):
    """The FULL block, never the stub: the stub is identified by the same START prefix, so the
    block only counts when it still carries the original claim table header."""
    try:
        i = next(k for k, l in enumerate(lines) if l.startswith(START))
        j = next(k for k, l in enumerate(lines) if k > i and l.startswith(END))
    except StopIteration:
        return None, None, None
    block = lines[i:j]
    if "| claim | evidence | conf |" not in block:
        return None, None, None
    return i, j, "".join(l + "\n" for l in block)


def main(argv):
    verify = "--verify" in argv
    text = open(NAMED, encoding="utf-8").read()
    lines = text.split("\n")
    i, j, blob = region(lines)
    arch = open(ARCHIVE, encoding="utf-8").read() if os.path.exists(ARCHIVE) else None
    if verify:
        assert arch is not None, "archive missing"
        k = arch.find(START)
        assert k >= 0, "archive does not carry the M341 region"
        moved = arch[k:]
        moved = moved[:moved.find(END)] if END in moved else moved
        got = hashlib.sha1(moved.encode()).hexdigest()
        assert got == EXPECT_SHA1, "archive sha1 drift: %s" % got
        assert blob is None, "the FULL block is still in NAMED.md"
        assert len(text.encode()) < 250000, "NAMED.md over cap"
        print("VERIFY ok: archive sha1 %s, full block absent from NAMED.md, NAMED %d B"
              % (EXPECT_SHA1[:16], len(text.encode())))
        return 0
    if blob is None:
        print("already rotated (stub in place, archive %s)" % ("present" if arch else "MISSING"))
        return 0 if arch else 1
    sha = hashlib.sha1(blob.encode()).hexdigest()
    moved = HEADER % sha + blob
    if arch:
        moved = arch + "\n" + blob
    open(ARCHIVE, "w", encoding="utf-8").write(moved)
    stub = STUB % sha[:16]
    new = "".join(l + "\n" for l in lines[:i]) + stub + "".join(l + "\n" for l in lines[j:])
    open(NAMED, "w", encoding="utf-8").write(new)
    print("moved M341 (%d B) to %s, sha1 %s; NAMED %d -> %d B"
          % (len(blob), os.path.relpath(ARCHIVE, ROOT), sha, len(text.encode()), len(new.encode())))
    print("NOTE: pin EXPECT_SHA1 in this script to %s before --verify" % sha)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
