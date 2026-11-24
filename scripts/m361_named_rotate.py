#!/usr/bin/env python3
"""M361: rotate the settled `## M360` block out of NAMED.md VERBATIM, then add `## M361`.

The NAMED.md cap is 250,000 B and headroom before this session was 2,320 B, under the
5 KB trigger — so one settled block moves to docs/ first and the new block takes its place.
The archive records the sha1 of the removed bytes and the script re-reads the archive to
prove the move was byte-exact.

    python3 scripts/m361_named_rotate.py            # dry run (prints sizes + sha1)
    python3 scripts/m361_named_rotate.py --apply
"""
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs/named-archive-m360-rows.md")
BLOCK_ID = "## M360"
CAP = 250000

NEW = """## M361 (s333-c2) — the A/V radio flags: widget+0xa18 of 4 rows at 0x12cbc+k*0xb4c; readers = relabel 0x493ec0 + commit 0x492940 + aggregate 0x492030 + seed 0x4930e0; the relabel ends in the GENERIC set-label 0x5fa1e8. ev `evidence/m361_radio_flags.txt:160`
| claim | ev | conf |
|---|---|---|
| flags 0x136d4/0x14220/0x14d6c/0x158b8 = widget+0xa18; widgets 0x12cbc+k*0xb4c (ctor 0x48fed0 zeroes 4); 3 children are vtable objects, master is not | `:75-85` | V MU7-9,MU23 |
| dispatcher 0x493ec0: table 0x493fe0 maps cmd 0x4b..0x4e -> those flags x {0x12cbc,0x13808,0x14354,0x14ea0}; guard cmd-0x4b/cmp 3 | `:58-74` | V MU3-6,MU26 |
| relabel = flag picks 1 of 2 ids in [0x997b20+0x10e0..0x10fc] -> 0x61482f -> 0x5fa1e8 stores at widget+0xa7c; 0x5fa1e8 has no flag, 10 sites/4 fns | `:66-74,:120-126` | V MU5,MU19-21 |
| commit 0x492940: 0x14d6c->+0xa50\\|0x4000, 0x14220->+0xa4c\\|0x400, 0x158b8->+0xa4c\\|0x800 (def-use); master never committed | `:93-101` | V MU11-13 |
| aggregate 0x492030: master := 0, then 1 per child!=0 (OR); toggle 0x493ff0: master-off clears all 4 + (ch,0xf3)/(ah,0xbf) on 0x985ab8/0x985abc; children ON -> master | `:102-119` | V MU14-18 |
| seed 0x4930e0: 3 flags from +0xa50 bits, each store paired with its own relabel cmd | `:140-147` | V MU24,25 |
| census 16/15/12/12 = 55 sites: 17 reads in 4 fns, 38 writes; 3 loner sites are BYTE stores in other classes | `:4-57,:86-92` | V MU1,2,10,22,27 |
| INF: rows are the A/V radio group's pending state (label text resolves at runtime; the image's .data is not in the file) | - | INF |
"""


def split_named(s):
    i = s.index(BLOCK_ID)
    j = s.index("\n## ", i) + 1
    return i, j, s[i:j]


def main(apply):
    s = open(NAMED, encoding="utf-8").read()
    i, j, blk = split_named(s)
    sha = hashlib.sha1(blk.encode()).hexdigest()
    print("NAMED.md %d B (cap %d, headroom %d)" % (len(s.encode()), CAP, CAP - len(s.encode())))
    print("rotating %s: %d B, %d table rows, sha1 %s" % (BLOCK_ID, len(blk.encode()), blk.count("\n|"), sha))
    arch = ("# NAMED.md `%s` - ROTATED VERBATIM (byte-exact) by scripts/m361_named_rotate.py\n"
            "<!-- block: every byte below is the original NAMED.md block -->\n\n"
            "sha1 %s  rows %d\n\n%s" % (BLOCK_ID, sha, blk.count("\n|"), blk))
    out = s[:i] + NEW + s[j:]
    print("after: %d B (headroom %d); new block %d B" % (len(out.encode()), CAP - len(out.encode()),
                                                         len(NEW.encode())))
    if not apply:
        print("dry run - pass --apply")
        return 0
    open(ARCHIVE, "w", encoding="utf-8").write(arch)
    back = open(ARCHIVE, encoding="utf-8").read()
    if blk not in back:
        print("FAIL: archive does not contain the block byte-exactly")
        return 1
    open(NAMED, "w", encoding="utf-8").write(out)
    s2 = open(NAMED, encoding="utf-8").read()
    ok = (BLOCK_ID + " ") not in s2 and NEW.strip() in s2
    print("[%s] block moved byte-exactly to %s and ## M361 installed"
          % ("PASS" if ok else "FAIL", os.path.relpath(ARCHIVE, ROOT)))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main("--apply" in sys.argv))
