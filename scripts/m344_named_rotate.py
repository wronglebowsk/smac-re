#!/usr/bin/env python3
"""M344 headroom rotation: move the settled M340 block VERBATIM out of NAMED.md.

NAMED.md sat at 246,305 B (3,695 B under its 250,000 B cap - inside the kickoff's 5 KB
rotate-first trigger) after M344 added its block, so the M340 block (settled s320, static,
7/7 + 12/12) moves byte-exactly into `docs/named-archive-m340-rows.md` (appended after the
M332 region that file already holds).  NAMED.md keeps a stub: the ACCEPT header with digest
and harness counts, plus ONE LINE PER CLAIM with the same cites and mutants.
The moved region's sha1 is PINNED and `--verify` re-asserts it, so an edit to either copy
fails loudly instead of forking the registry.

  python3 scripts/m344_named_rotate.py            # do the move (no-op once done)
  python3 scripts/m344_named_rotate.py --verify   # re-assert sha1 + the full block's absence
"""
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-m340-rows.md")
EXPECT_SHA1 = "dceab1fc162b3b519d1abce76800c81bb5bb4bd4"
START = "## M340 (s320-chain1, pick (x6) residual"
END = "## M342 (s322-chain1"
MARK = "<!-- m344-rotation: M340 verbatim -->"
STUB = """## M340 (s320-chain1, pick (x6) residual = M338's #1 lead, STATIC 7/7, review #358 hardened) — FUN_0058e7f0 ADMITS a `Difficulty` pref >= 6: no bound anywhere in the read -> parse -> store chain, so index 6 reaches `0x94d2c4`, one dword past the six-row ladder. FULL TABLE VERBATIM at `docs/named-archive-m340-rows.md` (`%s`); this stub governs, one line per claim

| claim (one line) | evidence | conf |
|---|---|---|
| 18 `call edi` sites, each with a 6-push window holding one `push 0x100` (argc-6); exactly ONE key `0x692718` = PE `"Difficulty"` (`0x58e8a1`), lpDefault push IS the itoa(0) buffer `0x997120`; its store `ds:0x92bde8` @`0x58e8c6` is the only store to that cell | `:3-8` | V MU1,MU10,MU11 |
| `0x58e8a9..0x58e8c6` is 10 straight-line insns (0 jcc/jmp/ret), two stores (`ds:0x996be8` cursor, `ds:0x92bde8`) | `:6-18` | V MU2,MU7 |
| the stored eax IS `0x6287e2`'s return: both wrappers branch-free, no eax write after their call | `:19-21` | V MU2,MU3,MU9 |
| the parse chain compares CHARACTER CLASSES only; constants ∩ {2,3,4,5,6} EMPTY | `:22-42` | V MU4,ALG1 |
| POSITIVE CONTROL, same function: `Language`'s consumer has `cmp [ebp-0x4],0x4; ja` — no such bound on the Difficulty path | `:44-58` | V MU5 |
| ladder endpoints MEASURED (`0x94d2ac..0x94d2c4`), 6 rows from `cmp esi,0x6`; k=5 -> `0x94d2c0`, k=6 -> `0x94d2c4` | `:61-65` | V MU8 |
| the three pref-fed readers (`0x48678f`/`0x44a1c8`/`0x599405`) index TABLE at scale 4 from a memory-loaded index, def-use gap 0/0/2 insns with no branch | `:67-76` | V MU6 |
| ACCEPT `python3 -u scripts/m340_pref_admission.py` -> `PASS M340: 7/7 gates`, rows `1cc44d0146a8b419`; `scripts/m340_mutate.py` -> `12/12`, NO-OP `[]`, `a2a1726721114b4d` | `evidence/m340_mutate.txt:16` | V |
| OPEN: what `0x94d2c4` holds at runtime (box read); whether `0x57c7b0`'s paired write supplies a bounded value | - | lead |
""" % EXPECT_SHA1


def region(text):
    i = text.find("\n" + START)
    if i < 0:
        return None, None, None
    j = text.find("\n" + END)
    if j < 0:
        return None, None, None
    blk = text[i + 1:j + 1]
    if "| claim | evidence | conf |" not in blk:      # this is the STUB, not the full block
        return None, None, None
    return i, j, blk


def main(argv=None):
    verify = "--verify" in (argv or sys.argv[1:])
    named = open(NAMED, encoding="utf-8").read()
    i, j, blk = region(named)
    if verify:
        arch = open(ARCHIVE, encoding="utf-8").read()
        k = arch.find(MARK)
        if k < 0:
            print("VERIFY FAIL: rotation marker missing from %s" % ARCHIVE)
            return 1
        h = arch.find("## M340 VERBATIM", k)
        start = arch.find("\n\n", h) + 2
        moved = arch[start:].rstrip("\n") + "\n"
        got = hashlib.sha1(moved.encode()).hexdigest()
        ok = got == EXPECT_SHA1
        print("%s M340 region sha1 %s (pinned %s); full block still in NAMED.md: %s"
              % ("ok  " if ok else "BAD ", got, EXPECT_SHA1, blk is not None))
        return 0 if ok and blk is None else 1
    if blk is None:
        print("no-op: the M340 block is already rotated (stub present)")
        return 0
    got = hashlib.sha1((blk.rstrip("\n") + "\n").encode()).hexdigest()
    if got != EXPECT_SHA1:
        print("REFUSING: region sha1 %s != pinned %s" % (got, EXPECT_SHA1))
        return 1
    with open(ARCHIVE, "a", encoding="utf-8") as f:
        f.write("\n%s\n## M340 VERBATIM (moved by `scripts/m344_named_rotate.py`, sha1 `%s`)\n\n"
                % (MARK, EXPECT_SHA1))
        f.write(blk.rstrip("\n") + "\n")
    new = named[:i + 1] + STUB + named[j + 1:]
    open(NAMED, "w", encoding="utf-8").write(new)
    print("rotated: M340 -> %s (sha1 %s); NAMED.md %d -> %d B"
          % (os.path.basename(ARCHIVE), EXPECT_SHA1, len(named.encode()), len(new.encode())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
