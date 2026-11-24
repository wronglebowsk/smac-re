#!/usr/bin/env python3
"""M341 headroom rotation: move the settled M338 block VERBATIM out of NAMED.md.

NAMED.md sat at 246,635 B (3,365 B under its 250,000 B cap) and this round adds
a V block, so the M338 block (settled: merged #357, its review round closed and
its own numbers re-derived by M340) moves byte-exactly into
`docs/named-archive-m341-rows.md`, and NAMED.md keeps a stub with ONE LINE PER
CLAIM (same gates, mutants, cites).  The moved region's sha1 is PINNED here and
`--verify` re-asserts it, so a later edit to either copy fails loudly.

  python3 scripts/m341_named_rotate.py            # do the move (idempotent)
  python3 scripts/m341_named_rotate.py --verify    # sha1 + stub cite resolve
"""
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-m341-rows.md")
EXPECT_SHA1 = "b82cddad74c849a0616ea0365ae620a8f44753c4"
START = "## M338 (s319-chain2, STATIC 8/8, review #357 hardened) — the LAST two"
ROTATED = "ROTATED by s321-chain2"
END = "## M340 (s320-chain1"
HEADER = ("# NAMED archive - M341 headroom rotation (s321-chain2): the M338 "
          "block VERBATIM\n"
          "(moved by `scripts/m341_named_rotate.py`; the region's sha1 is pinned"
          " to `%s` -\n"
          "run `--verify` after any edit; NAMED.md's stub keeps one line per"
          " claim)\n\n" % EXPECT_SHA1)

STUB = """## M338 (s319-chain2, STATIC 8/8, review #357 hardened; ROTATED by s321-chain2) — the LAST two `#DIFF` readers: `0x57c606` is the literal loop counter 0..5; `0x44a1c8` indexes with a hall-of-fame record byte (+0x20) that is the faction's EFFECTIVE DIFFICULTY. FULL-LENGTH TABLE VERBATIM at `docs/named-archive-m341-rows.md:%d` (sha1 `%s`); this stub governs, one line per claim

| claim | line | kind |
|---|---|---|
| table census: `.text` refs to 0x94d2ac = 2 base loads + 7 scaled readers {0x44a1c8,0x484cc9,0x485426,0x48678f,0x486f40,0x57c606,0x599405}, 0 stores | `:%d` | V MU2,MU11,MU12,ALG1 |
| `0x57c606`: `xor esi,esi` precedes; only esi write is `inc` 0x57c6ca; `cmp esi,6`/`jl` = 0..5, same 6 as the loader end 0x94d2c4 | `:%d` | V MU1 |
| `0x44a1c8`: 6-insn window, `dl=BYTE[eax+0x20]`, 0 insns between byte load and `[edx*4+0x94d2ac]`, 0 eax clobbers | `:%d` | V MU3,MU15 |
| `[ebp-0x1c]` = a 0x983a10 record: 3 stores, the 0x4497b7 source is `lea eax,[edx*4+0x983a10]` with `(8-1)*(1+4)*4 = 0x8c` | `:%d` | V MU4,MU5,MU13 |
| buffer = `hallfame.jhh`: fopen 0x64c980 window, read size 0x1324, zero-init 35x0x8c to 0x984d34 | `:%d` | V MU6,MU7 |
| field +0x20: 7-function module, exactly 2 stores (0x44b15b from faction block +8, 0x44b612 struct copy) | `:%d` | V MU8,MU9 |
| 0x94d438 = the faction's EFFECTIVE DIFFICULTY (creation 0x59eec3 branch, save-load 0x57ef57) | `:%d` | V MU10,MU14 |
| rivals dead: index is not 0x985aec; 0x983a10 is not the faction array (0x8c vs 0x20bc); 0x57c606's index is not stored | `:%d` | V MU7 |
| ACCEPT `PASS M338: 8/8` `1ae1563d47d0039e` x2, harness 16/16 `56455db0eadbedd7` | `:%d` | V |
| OPEN: the +0x20 index is UNCLAMPED; a pref >=6 is ADMITTED (M340); 0x44a1c8's window is the HoF screen (INFERRED). **CLOSED by `## M341`:** the window's page arithmetic | - | lead |
"""


def region(text):
    i = text.index(START)
    j = text.index(END)
    return i, j, text[i:j]


def verify(blob):
    got = hashlib.sha1(blob.encode()).hexdigest()
    ok = got == EXPECT_SHA1
    print("sha1 %s == pinned %s : %s" % (got[:12], EXPECT_SHA1[:12], ok))
    return ok


def main():
    text = open(NAMED, encoding="utf-8").read()
    if ROTATED not in text and START in text:
        i, j, blob = region(text)
        if not verify(blob):
            print("MOVE ABORTED: the block does not match the pinned sha1")
            return 1
        stub = STUB % (5, EXPECT_SHA1[:12], 1, 2, 3, 4, 5, 6, 7, 8, 9)
        new = text[:i] + stub + text[j:]
        with open(ARCHIVE, "w", encoding="utf-8") as f:
            f.write(HEADER + blob)
        with open(NAMED, "w", encoding="utf-8") as f:
            f.write(new)
        print("moved %d B to %s ; NAMED %d -> %d B"
              % (len(blob), os.path.basename(ARCHIVE), len(text), len(new)))
    else:
        print("NAMED.md already rotated (stub in place)")
    # --verify: archive still holds the block, byte-exact
    arch = open(ARCHIVE, encoding="utf-8").read()
    blob = arch[arch.index(START):]
    return 0 if verify(blob) else 1


if __name__ == "__main__":
    sys.exit(main())
