#!/usr/bin/env python3
"""M347 headroom rotation: move the settled B26 block VERBATIM out of NAMED.md.

Scope is EXACTLY the B26 block: from its heading to the NEXT `## ` heading
(which is `## M327`), not to `## B27` -- an earlier revision of this script
moved M327 and M329 along with B26 and dropped their headings from the
registry; `--verify` now asserts those headings are still present.

  python3 scripts/m347_named_rotate.py            # do the move (idempotent)
  python3 scripts/m347_named_rotate.py --verify    # sha1 + registry headings
"""
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-b26-governing.md")
EXPECT_SHA1 = "543c1243f00c45151eef21dcba9fc4836c1ad7cd"
START = "## B26 (s299 BUILD + PR #328 review remediation"
KEEP = ("## M327", "## M329", "## B27")
ROTATED = "ROTATED by s324-chain2"
HEADER = ("# NAMED archive - M347 headroom rotation (s324-chain2): the B26 block VERBATIM\n"
          "(moved by `scripts/m347_named_rotate.py`; the region's sha1 is pinned to "
          "`%s` - run\n`--verify` after any edit. Scope = the B26 block only; M327 and "
          "M329 stay in NAMED.md.\nB26 is settled: merged #328, superseded by B27-B31; "
          "its long-form rows are in\n`docs/named-archive-b26-rows.md`.)\n\n" % EXPECT_SHA1)

STUB = """## B26 (s299 BUILD + PR #328 review remediation; settled, ROTATED by s324-chain2) — the composed run crosses a SAVE/LOAD boundary: the container is LOADED, not just written, and the non-carry is counted, not declared away. ACCEPT `PASS 10/10` + harness 19/19 scored + 1 declared NO-OP + selftest 8/8 + entry identity 2/2, anchor `ae43e0ab9c8cfc3d`. FULL-LENGTH BLOCK VERBATIM at `docs/named-archive-b26-governing.md` (sha1 `%s`); long-form reasoning at `docs/named-archive-b26-rows.md`; this stub governs

| claim | conf |
|---|---|
| the boundary is a fresh decode checked against an independent second parse: 69/69 unit tiles and 20/20 base records field-wise | V (archived row 1) |
| UNMODELED / OPEN (B26's own): the non-carry is measured on ONE mid-gesture configuration; in-progress turn state beyond the budget not modeled; whole-record growth INFERRED; `found_units` 69 -> 0 while `n_units_img` stays 70/71 (printed, NOT gated); smuggler owner 1 vs 2 UNKNOWN; zero box time | lead |
""" % EXPECT_SHA1[:12]


def region(text):
    i = text.index(START)
    j = text.index("\n## ", i + 5) + 1
    return i, j, text[i:j]


def main():
    text = open(NAMED, encoding="utf-8").read()
    if ROTATED not in text and START in text:
        i, j, blob = region(text)
        got = hashlib.sha1(blob.encode()).hexdigest()
        if got != EXPECT_SHA1:
            print("MOVE ABORTED: block sha1 %s != pinned %s" % (got[:12], EXPECT_SHA1[:12]))
            return 1
        new = text[:i] + STUB + text[j:]
        with open(ARCHIVE, "w", encoding="utf-8") as f:
            f.write(HEADER + blob)
        with open(NAMED, "w", encoding="utf-8") as f:
            f.write(new)
        print("moved %d B to %s ; NAMED %d -> %d B"
              % (len(blob), os.path.basename(ARCHIVE), len(text), len(new)))
    else:
        print("NAMED.md already rotated (stub in place)")
    arch = open(ARCHIVE, encoding="utf-8").read()
    got = hashlib.sha1(arch[arch.index(START):].encode()).hexdigest()
    named = open(NAMED, encoding="utf-8").read()
    keep = [h for h in KEEP if h not in named]
    ok = got == EXPECT_SHA1 and not keep
    print("archive sha1 %s == pinned %s : %s ; registry headings kept: %s"
          % (got[:12], EXPECT_SHA1[:12], got == EXPECT_SHA1, not keep))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
