#!/usr/bin/env python3
"""M345 headroom rotation: move the settled M339 block VERBATIM out of NAMED.md.

NAMED.md sat at 245,824 B (4,176 B under its 250,000 B cap -- inside the
kickoff's 5 KB rotate-first trigger), so the M339 block (settled s320-chain2;
its last OPEN, the `[obj+0xa40]` writer, was closed by M343) moves byte-exactly
into `docs/named-archive-m339-rows.md`.  NAMED.md keeps a stub: the ACCEPT
header with its gates/digests plus ONE LINE PER CLAIM with the same cites and
mutant names.  The moved region's sha1 is PINNED and `--verify` re-asserts it.

  python3 scripts/m345_named_rotate.py            # do the move (no-op once done)
  python3 scripts/m345_named_rotate.py --verify   # re-assert sha1 + stub presence
"""
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-m339-rows.md")
EXPECT_SHA1 = "9a93e8acca0a99ac0779babaa63a94ae5afca934"
START = "## M339 (s320-chain2, pick (x6) \"callee 0x5f1394\""
END = "## M341 (s321-chain2"
MARK = "<!-- m345-rotation: M339 verbatim -->"
STUB = """## M339 (s320-chain2, STATIC 7/7, review #359 hardened) — 0x5f1394 = the modal SCREEN RUNNER; its return is the screen OBJECT's `+0xa40` result cell, and the difficulty dialog writes that return into `ds:0x985aec` + all 8 faction blocks. FULL TABLE VERBATIM at `docs/named-archive-m339-rows.md` (`%s`); this stub governs, one line per claim

| claim (one line) | evidence | conf |
|---|---|---|
| FUN_005f1394 = 11,207 B / 2,235 insns, `ret 0x8`, SEH 0x66f786, `sub esp,0x38c`; vtable lane {15c,160,164,16c,170} | `:1`, `:42-43` | V MU1,MU2,MU9 |
| 7 exits all through the ONE SEH-restore label; `[obj+0xa40]` read ONCE, written 0x; +0xa44 never read | `:43-44` | V MU3,MU7,ALG_A1 |
| 94 direct thiscall sites: 76 `lea ecx,[ebp-…]`, 14 pointer slots, 3 register, 1 global 0x9210a8; none receiverless | `:45` | V MU4,MU10 |
| FUN_004ddaa0: seed 0x985aec -> obj+0xa44, `call 0x5f1394`, `test eax`/`jge`, store-back + 8-iteration faction loop (0x20bc) | `:46` | V MU5,MU6,MU8,MU11,MU12 |
| rivals dead: runner is not the chooser (0 refs in 2,235 insns); return is not a dialog ID (only -1/0 immediates) | `:47` | V MU7 |
| ACCEPT `scripts/m339_modal_runner.py` -> `PASS M339: 7/7` `d76a5e83770b77bb` x2; harness 13/13; `--selftest` 3/3 | `evidence/m339_mutate.txt:17` | V |
| OPEN at s320: writer of `[screen+0xa40]` — CLOSED by M343 (3 dialog-family methods) | - | lead |
""" % EXPECT_SHA1


def region(text):
    i = text.find("\n" + START)
    if i < 0:
        return None, None, None
    j = text.find("\n" + END)
    if j < 0:
        return None, None, None
    blk = text[i + 1:j + 1]
    if "| claim | line | kind |" not in blk:      # this is the STUB, not the block
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
        h = arch.find("## M339 VERBATIM", k)
        start = arch.find("\n\n", h) + 2
        nxt = arch.find("\n## ", start)
        moved = (arch[start:] if nxt < 0 else arch[start:nxt]).rstrip("\n") + "\n"
        got = hashlib.sha1(moved.encode()).hexdigest()
        ok = got == EXPECT_SHA1
        print("%s M339 region sha1 %s (pinned %s); full block still in NAMED.md: %s"
              % ("ok  " if ok else "BAD ", got, EXPECT_SHA1, blk is not None))
        return 0 if ok and blk is None else 1
    if blk is None:
        print("no-op: the M339 block is already rotated (stub present)")
        return 0
    got = hashlib.sha1((blk.rstrip("\n") + "\n").encode()).hexdigest()
    if got != EXPECT_SHA1:
        print("REFUSING: region sha1 %s != pinned %s" % (got, EXPECT_SHA1))
        return 1
    with open(ARCHIVE, "a", encoding="utf-8") as f:
        f.write("\n%s\n## M339 VERBATIM (moved by `scripts/m345_named_rotate.py`, sha1 `%s`)\n\n"
                % (MARK, EXPECT_SHA1))
        f.write(blk.rstrip("\n") + "\n")
    new = named[:i + 1] + STUB + named[j + 1:]
    open(NAMED, "w", encoding="utf-8").write(new)
    print("rotated: M339 -> %s (sha1 %s); NAMED.md %d -> %d B"
          % (os.path.basename(ARCHIVE), EXPECT_SHA1, len(named.encode()), len(new.encode())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
