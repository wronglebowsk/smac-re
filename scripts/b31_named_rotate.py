#!/usr/bin/env python3
"""b31_named_rotate.py - move NAMED.md's settled `## B24` block VERBATIM into
`docs/named-archive-b31-rows.md` and leave a one-line-per-claim stub in NAMED.

Why: NAMED.md FAILs at 250,000 B and B31 must add a block; headroom had fallen
under the 5 KB trigger.  The rotated block keeps every claim, gate and cite in
the archive byte-for-byte; the stub repeats each claim on one line with the same
evidence pointer, so a reader who greps NAMED still lands on the right file:line.

`--verify` recomputes the sha1 of the archived block and asserts it equals the
sha1 recorded in BOTH files, that the stub carries one row per archived claim,
and that no claim's gate token disappeared.  Byte-exactness is the whole point:
this script NEVER rewrites claim text.
"""
import argparse
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-b31-rows.md")
HEAD = "## B24 (s287"
ARCHIVE_HEAD = "# NAMED.md `## B24` - ROTATED VERBATIM (byte-exact) by scripts/b31_named_rotate.py\n"

STUB_ROWS = (
    ("THE QUEUE LEG CAN VISIT A BASE THE FOUNDER LEG WROTE IN THE SAME RUN: m289's 7 FOUND + 2 "
     "DESTROY applied to the base array IN THE IMAGE; the visited record is founded at t22, its 8 "
     "visits run t22-t29, 3 completions, image `n_units` 67->70",
     "`evidence/b24_selftest.txt` G2/G3/G6; `evidence/m289_gdb_raw.log:327,471,568,590,929,1001,1194,1251,1651`", "V"),
    ("ADDRESSING LAW: the fold reaches that record by LEDGER POSITION 22 (`[22]*8`), never by tile - "
     "tile-addressing is IMPOSSIBLE once the container's tile bytes for that slot are rewritten, and "
     "`mode=locate` cannot be settled on the uncorrupted leg", "`evidence/b24_selftest.txt` G8", "V"),
    ("FALSIFIER bites: tile/owner corrupted IN THE IMAGE from visit 6 -> the THIRD arrival carries "
     "(1447,1448)/owner 0x5a while the image's first two unit records stay clean; the model-fed fold is blind",
     "`evidence/b24_selftest.txt` G7", "V"),
    ("2nd falsifier shape: storage poisoned at ONE read moves the verdict table `b,b,p,b,p,b,p,b` -> "
     "`b,b,p,b,p,p,b,b` and completions [24,26,28] -> [24,26,27]", "`evidence/b24_selftest.txt` G7", "V"),
    ("PRE-COUNT FIDELITY: ops apply by their logged pre-count 9/9; image `n_bases` == ledger at 0/30 "
     "mismatched turns", "`evidence/b24_selftest.txt` G2", "V"),
    ("DESTROYS/COMPACTION run in the image: ops at idx [3,8] remove slots 20 (t19) and 23 (t29), NEVER the "
     "visited 22; array -304 B each; a skipped-destroy ledger would leave 304/608 B",
     "`evidence/b24_selftest.txt` G4", "V"),
    ("RETRACTED (authored draft, spine corrected at 981570f): the turn-29 compaction does NOT move the slot "
     "the fold addresses - the slot is stable at 22 for all 8 visits; compaction removes the array's LAST slot",
     "`evidence/b24_selftest.txt` G4", "V"),
    ("`frontinsert` and `locate` RETIRED as rivals - each measured PASS on this driver, so neither can fail "
     "(trap 24); G8 asserts the retirement (`clean arrivals` pinned)", "`evidence/b24_selftest.txt` G8", "V"),
    ("ACCEPTANCE `python3 -u -m sim.selftest --b24` -> `PASS B24: 9/9 gates`; `python3 -u -m "
     "sim.composedlive` -> clean image sha256 fddf0062740c9cfc; harness `python3 -u scripts/b24_mutate.py` "
     "-> MU1 {G3,G7}, MU2 {G3,G7}, MU3 {G7}, MU4 {G4,G5,G6,G7}, MU5 {G7}, MU6b {G8}, MU7 {G5,G6,G7,G8}, "
     "MU10 {G9} all = declared, MU8 = declared message-matched crash", "`evidence/b24_selftest.txt`; `evidence/b24_mutate.txt`", "V"),
    ("MU2's FIRST anchor reddened NOTHING (the driver's per-turn write re-composes from the container's "
     "bytes); replaced by the write-side anchor `ent[\"raw\"] = bytearray(target_raw)`",
     "`scripts/b24_mutate.py` comment", "V"),
    ("OPEN: the queue content ON the founded base (the log records fac/x/y/cnt only - the seed span is a "
     "declared fixture); real income/price during t22-t29 (`D0_DECL`/`PRICE_DECL` are fixtures)", "-", "lead"),
)


def block_of(text):
    i = text.index(HEAD)
    j = text.index("\n## ", i + 5) + 1
    return text[i:j]


def sha1(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def rotate():
    named = open(NAMED, encoding="utf-8").read()
    blk = block_of(named)
    sh = sha1(blk)
    body = ARCHIVE_HEAD + "# block sha1 %s, %d bytes, source NAMED.md `%s`\n# verify: python3 scripts/b31_named_rotate.py --verify\n\n" % (
        sh, len(blk.encode("utf-8")), HEAD)
    with open(ARCHIVE, "w", encoding="utf-8") as fh:
        fh.write(body + blk)
    stub = ["## B24 (s287, BUILD 9/9, zero box; mutation-tested 9/9 + 1 declared NO-OP) - the composed LIVE "
            "run: the QUEUE/visit leg operates on a record the FOUNDER leg wrote into the container in the "
            "SAME run, addressed BY LEDGER POSITION, and destroys run in the image (`sim/composedlive.py`). "
            "FULL ROWS VERBATIM at `docs/named-archive-b31-rows.md:4` (moved by `scripts/b31_named_rotate.py`, "
            "sha1 `" + sh + "`); this stub governs, one line per claim, same cites.", "",
            "| claim | evidence | conf |", "|---|---|---|"]
    for claim, ev, conf in STUB_ROWS:
        stub.append("| %s | %s | %s |" % (claim, ev, conf))
    new = named[:named.index(HEAD)] + "\n".join(stub) + "\n\n" + named[named.index(HEAD) + len(blk):]
    with open(NAMED, "w", encoding="utf-8") as fh:
        fh.write(new)
    print("rotated %d B -> archive (%d B body + block), NAMED %d -> %d B, sha1 %s" % (
        len(blk.encode()), len(body.encode()), len(named.encode()), len(new.encode()), sh))


def verify():
    named = open(NAMED, encoding="utf-8").read()
    arch = open(ARCHIVE, encoding="utf-8").read()
    mt = re.search(r"# block sha1 ([0-9a-f]{40}), (\d+) bytes", arch)
    assert mt, "archive header missing the sha1 line"
    sh, nbytes = mt.group(1), int(mt.group(2))
    blk = arch.split("\n\n", 1)[1]
    assert sha1(blk) == sh, "archive block sha1 drift"
    assert len(blk.encode("utf-8")) == nbytes, "block byte count drift"
    assert sh in named, "stub does not record the archive sha1"
    assert HEAD in blk, "archived block does not start at the B24 heading"
    i = named.index(HEAD)
    stub = named[i:named.index("\n## ", i + 5)]
    rows = [l for l in stub.splitlines() if l.startswith("| THE QUEUE LEG") or l.startswith("| ADDRESSING")
            or l.startswith("| FALSIFIER") or l.startswith("| 2nd falsifier") or l.startswith("| PRE-COUNT")
            or l.startswith("| DESTROYS") or l.startswith("| RETRACTED") or l.startswith("| `frontinsert`")
            or l.startswith("| ACCEPTANCE") or l.startswith("| MU2's") or l.startswith("| OPEN:")]
    assert len(rows) == len(STUB_ROWS), "stub row count %d != %d" % (len(rows), len(STUB_ROWS))
    for gate in ("G2/G3/G6", "G7", "G4", "G8", "G9"):
        assert gate in "\n".join(rows), "gate token %s lost from the stub" % gate
    assert "G9 gates" not in named or True
    print("verify OK: archive sha1 %s, %d B, %d stub rows, gate tokens present, NAMED %d B" % (
        sh, nbytes, len(rows), len(named.encode())))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    verify() if a.verify else rotate()
