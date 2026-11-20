#!/usr/bin/env python3
"""M329 headroom rotation: move the settled `## M255 ... ## M258` block of NAMED.md VERBATIM
into docs/named-archive-m255-m258.md, leaving a cite-preserving one-line-per-claim stub.

Why this block: s201-s202 work, already superseded in-place by M273-M276/M277 (the region-row
fold, the 94-slot capacity, the sibling-array spill) and by M281 — nothing here is load-bearing
for the live pick, and its rows all point at `evidence/m253_region_categories.txt` /
`evidence/m256_worth_operands.txt`, which stay where they are.

Byte-exactness is asserted two ways: the block's sha1 must equal the recorded digest, and the
archive file must contain the block as a byte substring. Refuses to run twice.
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCH = os.path.join(ROOT, "docs", "named-archive-m255-m258.md")
SHA1 = "9111d3b24758"                      # measured: see SESSION_NOTES s307
HEAD = "## M255 (s201, PASS 8/8)"
STUB = r"""## M255-M258 (s201-s202, PASS 8/8) - ROTATED VERBATIM to `docs/named-archive-m255-m258.md`
Hygiene rotation at s307 (M329 headroom): 36 lines, 6,734 B, sha1 `9111d3b24758`, asserted byte-exact by `scripts/m329_named_rotate.py`; the archive holds the full rows, git history is the trail. One line per claim, gates and cites unchanged:

| claim | evidence | conf |
|---|---|---|
| `FUN_005b2970` has exactly 4 call sites, one per caller: `0x4e1151`, `0x4e122b`, `0x57d2a0`, `0x57f1ec` | G6, `evidence/m253_region_categories.txt:6` | V |
| the 4 callers' gates: `57c550`'s skipped by `je`/`jne 0x57d2a5` on `ds:0x9264d8` (written only `0x57e495`=1, `0x57e900`=0) + `bl & 2`; `57ecf0`'s ungated and preceded by 6 stores to the world-dim globals `ds:0x92ad??`; `4e10c0` ORs `0x80` into `ds:0x985ae8`, `4e11b0` ANDs `0x7f` | G6, `:6` | V |
| modes from literals: `57ecf0` = {FACTIONS, WORLDSIZE, SCENARIO, INTRO} + 2x alpha-section opener `FUN_005ea431`; `57c550` = {RULES, USERULES, RELOADFAC, DIFFICULTY, CUSTOMNAMES, FACTION}, 0 openers; caller sets `512b40`/`516b80` (pair), `57e890`/`57f740` (`57c550`), `522850`/`57f740` (`57ecf0`) | G7, `:7` | V |
| **exactly ONE caller satisfies ungated + world-dim stores + alpha reads + scenario literals: `FUN_0057ecf0` = NEW GAME**; `57c550` = scenario/MAP-FILE load; `4e10c0`/`4e11b0` = menu/editor REGENERATE pair (accept vs retry-vote) | G8, `:8` | V (discriminators), INFERRED (naming) |
| M256: the worth test deciding 7 vs 8 is `cmp edx,ecx`@`0x5584b4` (`jle`->0) + leg2 `cmp eax,ecx`@`0x5584d8`, legs ANDed, `or eax,ecx`@`0x5584eb` with the 4-bit reason word, `sete dl`@`0x55850e` | G1-G2, `evidence/m256_worth_operands.txt:5-6` | V |
| M256: LHS = `2 * ((DWORD[block+0x94d810] - DWORD[block+0x94d818] + [ebp-0x60]) * [ebp-0x3c])` (loads `0x55848f`/`0x558495`/`0x55849b`, `imul` `0x5584a2`, `shl 1` `0x5584a8`); `[ebp-0x3c]` = BYTE[block+region+0x94e5a8] | G3/G5, `:7,9` | V |
| M256: `[ebp-0x60]`'s live def at the test is `0x558424` = 3 + (ds:0x985afc > 75) + `FUN_00531090(ds:0x985b30,0)` + (BYTE[block+region+0x94eca8] < 4 ? 1 : 0) + the fold count; reason word = bit3 of WORD[0x94e7a8+row] \| mult>=0x14 \| WORD[0x94eaa8+row]-WORD[0x94eba8+row]<4 \| (mult!=0 and 0x94eca8 byte<2) | G3/G4, `:7-8` | V (chain), OPEN (why the fold sum is overwritten) |
| M257: RHS = WORD[0x94eaa8 + 2*region] (`0x5584aa`) + WORD[0x94eaa8 + esi] (`0x558452`), summed `0x5584b2` after `xor ecx,ecx` `0x5584a0`; region loop `[ebp-0x10]` 1..127 (`inc/cmp 0x80/jl` `0x558b1b`-`0x558b25`); 0x94eaa8 refs image-wide = 4 | G4-G5, `:8-9` | V |
| M257: `esi = [ebp-0x18]` = the row slot - **superseded by M273-M276**: the fold is `2*region + 8380*arg` (not 188), the live region count is 91 < the 94-slot row, and the scaled reads of regions 94..127 land INSIDE the sibling verdict array at `0x94eba8` (gap 256) | `evidence/m273w3.gdblog`, `scripts/m273_rowstride_watch.py --replay` 7/7, M274 G2/G6 | CLOSED (was OPEN) |
| M258: `0x94e4a8, 0x94e5a8, 0x94e628, 0x94e6a8, 0x94e7a8, 0x94e8a8, 0x94e9a8, 0x94eaa8, 0x94eba8, 0x94eca8, 0x94ed28, 0x94eda8` (end `0x94ee28`) = 12 per-region arrays, every gap 0x80 (byte) or 0x100 (word), ZERO dword accesses, 128 entries each | G8, `:11` | V |
| M258: **RETRACTION of the s201 row** "0x94e7a8 flag bytes" - it is a per-region WORD array (whole-word ops `0x5577e9`/`0x5577f8`/`0x5580d6`/`0x5580ed`, 28 refs to the +1 high byte), gap 0x100 | G8, `:11` | V |
| M258: the 8-slot fold (`0x558075`-`0x5583ac`) walks WORD[0x950764 + 2*region] and BYTE[0x950664 + region] stepped by the faction stride `0x20bc`, doubling the pair per set bit of BYTE[block+0x94d44c]; accumulators `[ebp-0x60]`/`[ebp-0x6c]`, count `[ebp-0x68]` | G6, `:10` | V |
| M258: the fold's second row is 0x200 below (`mov bx,[eax-0x200]` `0x558082` = `0x950564 + 2*region`); `0x950564` is its own table base (`lea esi,[esi*2+0x950564]` `0x4f7a0a`); both tables lie past the 3,067,904-B file image (ends VA `0x6ed000`) | G7, `:11` | V (pcs), OPEN (extents) |

"""


def main():
    t = open(NAMED, encoding="utf-8").read()
    if os.path.exists(ARCH):
        sys.exit("refusing: %s already exists (the rotation has run)" % os.path.relpath(ARCH, ROOT))
    i = t.index(HEAD)
    j = re.search(r"(?m)^## ", t[i + len(HEAD):]).start() + i + len(HEAD)
    blk = t[i:j]
    b = blk.encode("utf-8")
    got = hashlib.sha1(b).hexdigest()[:12]
    assert got == SHA1, "block sha1 %s != %s" % (got, SHA1)
    hdr = ("# NAMED.md archive - M255-M258 (rotated VERBATIM at s307, the M329 headroom rotation)\n\n"
           "Source: the `NAMED.md` block starting `## M255 (s201, PASS 8/8)` up to the next `## ` heading\n"
           "(`## B7`): %d lines, %d B, sha1 `%s` - asserted byte-exact by `scripts/m329_named_rotate.py`.\n"
           "`NAMED.md` keeps a one-line-per-claim stub with the same gates and cites.\n\n" % (blk.count("\n"), len(b), got))
    with open(ARCH, "w", encoding="utf-8") as f:
        f.write(hdr + blk)
    check = open(ARCH, "rb").read()
    assert b in check, "archive does not contain the block verbatim"
    with open(NAMED, "w", encoding="utf-8") as f:
        f.write(t[:i] + STUB + t[j:])
    after = len(open(NAMED, "rb").read())
    print("rotated %d B -> stub %d B; NAMED.md %d -> %d B" % (len(b), len(STUB.encode()), len(t.encode()), after))
    print("archive %s %d B, verbatim check PASS (sha1 %s)" % (os.path.relpath(ARCH, ROOT), len(check), got))


if __name__ == "__main__":
    main()
