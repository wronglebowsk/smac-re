#!/usr/bin/env python3
"""M347 headroom rotation: move the settled B26 build block VERBATIM out of NAMED.md.

NAMED.md sat at 247,779 B (2,221 B under its 250,000 B cap) and this round adds a
V block, so the B26 block (settled: merged #328, superseded by B27-B31; its own
long-form rows already live in docs/named-archive-b26-rows.md) moves byte-exactly
into `docs/named-archive-b26-governing.md` and NAMED.md keeps a stub with the
acceptance numbers and the one still-OPEN row.

  python3 scripts/m347_named_rotate.py            # do the move (idempotent)
  python3 scripts/m347_named_rotate.py --verify    # sha1 + archive presence
"""
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-b26-governing.md")
EXPECT_SHA1 = "2b800e500b8c2b95958e48fe42ad6f88e8134989"
START = "## B26 (s299 BUILD + PR #328 review remediation"
END = "## B27 (s309 BUILD"
ROTATED = "ROTATED by s324-chain2"
HEADER = ("# NAMED archive - M347 headroom rotation (s324-chain2): the B26 "
          "governing block VERBATIM\n"
          "(moved by `scripts/m347_named_rotate.py`; the region's sha1 is pinned "
          "to `%s` -\n"
          "run `--verify` after any edit. B26 is settled: merged #328, superseded "
          "by B27-B31;\n"
          "its long-form rows were already in `docs/named-archive-b26-rows.md`.)\n\n"
          % EXPECT_SHA1)

STUB = """## B26 (s299 BUILD + PR #328 review remediation; settled, ROTATED by s324-chain2) — the composed run crosses a SAVE/LOAD boundary (container LOADED, not just written; the non-carry is counted, not declared away). ACCEPT `PASS 10/10` + harness `19/19` scored + 1 declared NO-OP + selftest `8/8` + entry identity `2/2`, anchor `ae43e0ab9c8cfc3d`. FULL-LENGTH GOVERNING TABLE VERBATIM at `docs/named-archive-b26-governing.md` (sha1 `%s`); long-form reasoning at `docs/named-archive-b26-rows.md`; this stub governs\n\n| claim | conf |\n|---|---|\n| the boundary is a fresh decode checked against an independent second parse (69/69 unit tiles, 20/20 base records field-wise) | V (archived row 1) |\n| B26 is superseded by B27-B31; the only OPEN row left is what the 19 record bits MEAN (4 published, 15 stay) and who fills the scratch +0x00..+0x18 | OPEN |\n""" % EXPECT_SHA1[:12]


def main():
    verify_only = "--verify" in sys.argv
    text = open(NAMED, encoding="utf-8").read()
    if ROTATED not in text and START in text:
        i = text.index(START)
        j = text.index(END)
        blob = text[i:j]
        got = hashlib.sha1(blob.encode()).hexdigest()
        if got != EXPECT_SHA1:
            print("MOVE ABORTED: block sha1 %s != pinned %s" % (got[:12], EXPECT_SHA1[:12]))
            return 1
        new = text[:i] + (STUB if STUB.endswith("\n\n") else STUB + "\n") + text[j:]
        with open(ARCHIVE, "w", encoding="utf-8") as f:
            f.write(HEADER + blob)
        if not verify_only:
            with open(NAMED, "w", encoding="utf-8") as f:
                f.write(new)
            print("moved %d B to %s ; NAMED %d -> %d B"
                  % (len(blob), os.path.basename(ARCHIVE), len(text), len(new)))
    else:
        print("NAMED.md already rotated (stub in place)")
    arch = open(ARCHIVE, encoding="utf-8").read()
    got = hashlib.sha1(arch[arch.index(START):].encode()).hexdigest()
    ok = got == EXPECT_SHA1
    print("archive sha1 %s == pinned %s : %s" % (got[:12], EXPECT_SHA1[:12], ok))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
