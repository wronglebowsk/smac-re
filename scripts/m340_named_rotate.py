#!/usr/bin/env python3
"""M340 headroom rotation: move the settled M332 block VERBATIM out of NAMED.md.

NAMED.md sat at 249,287 B (713 B under its 250,000 B cap) and this round must add a
block, so the M332 block (settled: merged #347, its review round closed) moves
byte-exactly into `docs/named-archive-m340-rows.md` and NAMED.md keeps a stub with ONE
LINE PER CLAIM, same gates, mutants and cites.  The moved region's sha1 is PINNED here
and `--verify` re-asserts it, so a later edit to either copy fails loudly instead of
forking the registry.

  python3 scripts/m340_named_rotate.py            # do the move (idempotent no-op once done)
  python3 scripts/m340_named_rotate.py --verify   # re-assert sha1 + the stub's cite resolves
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-m340-rows.md")
EXPECT_SHA1 = "3ef265e11acaed3922475b59c8abe97063a0036f"
START = "## M332 (s311-chain1"
END = "## M331 (s310-chain2"
HEADER = ("# NAMED archive - M340 headroom rotation (s320): the M332 block VERBATIM\n"
          "(moved by `scripts/m340_named_rotate.py`; the region's sha1 is pinned to `%s` -\n"
          "run `--verify` after any edit; NAMED.md's stub keeps one line per claim)\n\n" % EXPECT_SHA1)

STUB = """## M332 (s311-chain1, pick (x2), STATIC 8/8) — `ds:0x985aec` is the RUNTIME MIRROR of the game's own `Difficulty` preference; its master `ds:0x92bde8` is the win-INI key `Difficulty`, read by FUN_0058e7f0 and written back by FUN_0058f0d0 (REFINES `## M308`). FULL-LENGTH TABLE VERBATIM at `docs/named-archive-m340-rows.md:5` (sha1 `3ef265e11aca`); this stub governs, one line per claim

| claim | evidence | conf |
|---|---|---|
| 68 refs to 0x985aec = 4 store / 40 load / 24 cmp / 0 RMW; cmp arms exactly {1,2,3,4} immediate AND exactly {ebx}, the ebx cmp unique at 0x4f9b5a; a byte-level LE scan of the .text cache finds the SAME 68 and 0 address materialisations. SCOPE (s312/#346 P1): a store through a runtime-computed register pointer is invisible to both scans | `evidence/m332_difficulty_census.txt:101` + G9.1 `:80-81` | V MU1-3,17,21 |
| store set exact {0x4ddcf1, 0x57c5af, 0x57c7b5, 0x57f006}, every one `a3 ec 5a 98 00` (moffs) | `evidence/m332_difficulty_census.txt:102` | V MU1-3 |
| 0x4ddcf1 has no fall-in; `jge 0x4ddcf1` at 0x4ddb5a takes callee 0x5f1394's eax (G9.2), 0 eax writes before the jge, 0 jump tables anywhere => M308's "0x4ddcf1 UNATTRIBUTED" CLOSED; 0x5f1394's own semantics OPEN | `:103` + G9.2 `:82-83` | V MU1-3,8,16,18 |
| clean-copy map among {0x92bde8, 0x985aec, 0x8f0c11, 0x8f0090} = 5 directions over 6 pairs, each pinned to site AND window (G9.4: 0 redefinitions, 0 writes between); no 0x985aec->0x92bde8 copy => direction is master -> runtime | `:104` + G9.4 `:87-93` | V MU2-7,14,19 |
| the pref table: 11 key-exclusive 6-arg profile reads in FUN_0058e7f0, an INJECTIVE name->field map, `Difficulty`@0x58e8a1 -> 0x92bde8@0x58e8c6, paired with the writeback load@0x58f11d; API identity measured (G9.5): 18 read / 8 write calls through `edi` == Ghidra's counts; 6/6 three-way names agree (s312 P2 correction) | `:105-107` + `:51-53`, `:68`, G9.5 `:94-97` | V MU4-15 |
| siblings the same map names: 0x92bdf4 = `Map Type`, 0x92bdf8 = `Top Menu`, 0x92bdec = `Faction` (what `## M328` called "92bdf8 mode global") | `:106-107` | V MU9,13 |
| RIVAL KILLED: 0x92bde8 is BOTH the end of the 4x0xd4 record array at 0x92ba98 (G9.6 reads the loops) AND a scalar pref cell (2 stores, 6 loads) - "sentinel only" fails on 0 stores | `:108` + G9.6 `:98-100` | V MU4,6,10,12,20 |
| ACCEPT digest(table) `d2691dc5abb39240`, `PASS M332: 9/9`; harness 20 scored + 1 NO-OP, digest `a9a944201849d026` | `evidence/m332_mutate.txt:25` | V |
| OPEN: the difficulty INDEX->label order is now ALPHA `#DIFF` file order (M335: 4=Thinker, 5=Transcend); the 0x8f0090 consumer is a player-record difficulty byte (M336); a pref >=6 is ADMITTED verbatim (M340, 7/7). Still open: 0x5f1394's semantics (chain 2), the other writers of the 0x92bde8..0x92bf14 block | - | lead |
"""


def region(text):
    L = text.split("\n")
    i = next(k for k, l in enumerate(L) if l.startswith(START))
    j = next(k for k, l in enumerate(L) if l.startswith(END))
    return L, i, j


def main():
    text = open(NAMED).read()
    L, i, j = region(text)
    moved = "\n".join(L[i:j]) + "\n"
    sha = hashlib.sha1(moved.encode()).hexdigest()
    if "--verify" in sys.argv:
        arch = open(ARCHIVE).read() if os.path.exists(ARCHIVE) else ""
        aL = arch.split("\n") if START in arch else []
        pos = arch.index(START) if START in arch else 0
        asha = hashlib.sha1(arch[pos:].encode()).hexdigest() if aL else ""
        ok = (asha == EXPECT_SHA1 and STUB.split("\n")[0] in text)
        print("archive region sha1 %s expect %s  stub_present=%s"
              % (asha, EXPECT_SHA1, STUB.split("\n")[0] in text))
        print("VERIFY %s" % ("PASS" if ok else "FAIL"))
        return 0 if ok else 1
    if sha != EXPECT_SHA1:
        print("region sha1 %s != pinned %s - refusing to move" % (sha, EXPECT_SHA1))
        return 1
    if STUB.split("\n")[0] in text:
        print("already rotated (stub present); archive sha1 %s" % sha)
        return 0
    with open(ARCHIVE, "w") as f:
        f.write(HEADER + moved)
    new = "\n".join(L[:i]) + "\n" + STUB + "\n" + "\n".join(L[j:])
    with open(NAMED, "w") as f:
        f.write(new)
    print("moved %d B (sha1 %s) to %s:5; NAMED now %d B"
          % (len(moved), sha, os.path.relpath(ARCHIVE, ROOT), len(new)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
