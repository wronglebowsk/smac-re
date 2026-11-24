#!/usr/bin/env python3
"""m363_named_rotate.py - move NAMED.md's settled `## B27` block VERBATIM into
`docs/named-archive-b27-rows.md` and leave a one-line-per-claim stub in NAMED.

M363 must add a block and NAMED.md is 247,217 B against a 250,000 B FAIL (2,783 B of
headroom, under the 5 KB trigger).  B27 is a settled BUILD rung (s309; B28-B34 carry the
later rounds and the rung's own retraction of the flat idle print is inside its block, so
it moves byte-exactly with it).  The stub repeats every claim on one line with the same
gates/mutants/evidence cites, so a grep of NAMED still lands on a file:line.

    python3 scripts/m363_named_rotate.py            # rotate (idempotent if already done)
    python3 scripts/m363_named_rotate.py --verify   # sha1 byte-exactness + claim tokens
"""
import argparse
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-b27-rows.md")
HEAD = "## B27 (s309"
ARCHIVE_HEAD = ("# NAMED.md `## B27` - ROTATED VERBATIM (byte-exact) by "
                "scripts/m363_named_rotate.py\n\n")

STUB = """## B27 (s309 BUILD, zero box) - ROTATED VERBATIM to `docs/named-archive-b27-rows.md` (sha1 `%s`): the ENERGY round EXECUTABLE and CARRIED (`sim/energy.py` = the law, `sim/composedenergy.py` = the run; spine §B27). One line per claim; `:N` = a line of `evidence/b27_selftest.txt`.
- THE CONTAINER CARRIES THE LEDGER: ENERGY `[10,28,112,69,229,60,102,37]`, `+300 [0,1,1,0,1,0,1,1]`, `+224` all 0, both offset tables == the M325/M326/M330 censuses' printed rows - V; MU8 MU9 (`:14-18`, gate `:70`)
- THE LEDGER LAW holds 8/8 + 8/8 predicted through `sim.energy.ledger`; three rivals 1/3/1 of 8 - V; MU1 MU2 (`:20-21`, gate `:71`)
- REFUND = `trunc(k*spend/3)` residue kept: sweep 40,002 cases 0 violations, k-table `[0,0,0,0,1,2,2,2,2,2]` from the switch tuples, both rivals measured AND the branch shape gated - V; MU5 MU16, MU3 MU4 redden G5 (`:23-25`, gates `:73` `:74`)
- THE ORDERING IS A NUMBER: snapshot == post-settle clamped pool 3/3 discriminating; both legs MEASURED INERT 0/8, not a stub (still 0/8 at k=1/k=2) - V; MU6 MU7 (`:26-32` `:36`, gate `:75`)
- B4 REUSE not fork: 3 replay gates green in-process; post-found row reproduces through THIS pipeline; RETRACTED s309 F6: the flat 12-round idle 12/12 is a legs-zero consistency print, it gates nothing - V; MU3 MU4 (`:33` `:35-38`, gate `:72`)
- THE WRITER MODELS BLOCK A FOR THE FIRST TIME: identity True, 40 spans, 9 bytes differ, 0 outside modeled spans, carry violations all 0 per round - V; MU10 MU11 (`:55-59`, gate `:76`)
- FALSIFIER +77 on faction 4 reaches the container for faction 4 alone; the ledger-keeping smuggler is blind, counted poisoned 1 vs 0 - V; MU12 MU13 (`:60-61`, gate `:77`)
- ACCEPT `python3 -u -m sim.selftest --b27` -> **PASS B27: 10/10** (2 runs identical), harness **17/17** `181d99d9ac000044`, NO-OP `[]`, `--selftest` 4/4 - V; MU1-MU17 (`:56` `:79`, `b27_mutate.txt:18-22`)
- UNMODELED: `+2fc/+308/+3f8` entry-zeroed, mid-round writer OPEN (M330); income-vs-feeder order unpinned; 48 rows computed, 13 printed - lead (spine §B27, `:54`)
"""

CLAIM_TOKENS = ["THE CONTAINER CARRIES", "LEDGER LAW", "REFUND", "ORDERING", "B4 REUSE",
                "WRITER MODELS", "FALSIFIER", "ACCEPT", "UNMODELED", "181d99d9ac000044"]


def block(text):
    m = re.search(r"(?ms)^## B27 \(s309.*?(?=^## |\Z)", text)
    return m.group(0) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    text = open(NAMED, encoding="utf-8").read()
    b = block(text)
    if a.verify:
        if b is not None and "ROTATED VERBATIM to `docs/named-archive-b27-rows.md`" not in b:
            print("FAIL: NAMED still carries the full ## B27 block")
            return 1
        arch = open(ARCHIVE, encoding="utf-8").read()
        body = arch[len(ARCHIVE_HEAD):]
        sha = hashlib.sha1(body.encode("utf-8")).hexdigest()
        m2 = re.search(r"(?ms)^## B27 .*?(?=^## |\Z)", text)
        stub = m2.group(0) if m2 else ""
        m = re.search(r"sha1 `([0-9a-f]{8,40})`", stub)
        ok = bool(m and m.group(1) and sha.startswith(m.group(1)) and len(body) > 4000)
        toks = [t for t in CLAIM_TOKENS if t in stub]
        print("archive bytes=%d sha1=%s stub_sha1=%s claims=%d/%d"
              % (len(body.encode()), sha[:12], m.group(1) if m else "-", len(toks), len(CLAIM_TOKENS)))
        missing = [t for t in CLAIM_TOKENS if t not in stub]
        if missing:
            print("FAIL: stub lost claims %s" % missing)
        print("%s  %s  NAMED bytes=%d" % ("PASS" if ok and not missing else "FAIL", ARCHIVE,
                                          len(text.encode())))
        return 0 if (ok and not missing) else 1

    if b is None or "ROTATED VERBATIM to `docs/named-archive-b27-rows.md`" in b:
        print("already rotated (stub present); nothing to do")
        return 0
    if not os.path.exists(ARCHIVE):
        with open(ARCHIVE, "w", encoding="utf-8") as f:
            f.write(ARCHIVE_HEAD)
            f.write(b)
    else:
        with open(ARCHIVE, encoding="utf-8") as f:
            old = f.read()
        if old[len(ARCHIVE_HEAD):] != b:
            print("FAIL: archive exists with different bytes; refusing to clobber")
            return 1
    sha = hashlib.sha1(b.encode("utf-8")).hexdigest()
    new = text.replace(b, STUB % sha, 1)
    with open(NAMED, "w", encoding="utf-8") as f:
        f.write(new)
    print("rotated %d B -> stub %d B; sha1 %s" % (len(b.encode()), len((STUB % sha).encode()), sha))
    print("NAMED %d -> %d B" % (len(text.encode()), len(new.encode())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
