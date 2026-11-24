#!/usr/bin/env python3
"""M339 NAMED headroom rotation (s320-chain2): move `## M308` VERBATIM to
`docs/named-archive-m339-rows.md` (§rotation-1) before adding the M339 block.
Same law as `scripts/m338_named_rotate.py`: the oldest settled chain block moves
byte-for-byte, the stub keeps its claims one line and the pointer's sha1.

Why M308: it is the block that left `0x4ddcf1 UNATTRIBUTED` — M339 closes that
edge (nonzero `jge` = the runner returned the screen's result cell), so the block
is both settled and due a pointer.

    python3 scripts/m339_named_rotate.py            # perform the move
    python3 scripts/m339_named_rotate.py --verify   # re-hash the archived region
"""
import argparse
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARC = os.path.join(ROOT, "docs", "named-archive-m339-rows.md")

START = "## M308 (s268"
END = "## M309 ("
MARK = "§rotation-1 (M308, s320-chain2 headroom rotation)"
TERMINATOR = "(§rotation-1 ends; nothing below it belongs to this region.)"
EXPECT_SHA = "07cec1770614"   # pinned constant (never read back from the archive)


def digest(s):
    return hashlib.sha1(s.encode()).hexdigest()[:12]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    if args.verify:
        arc = open(ARC, encoding="utf-8").read()
        a = arc.find(MARK + "\n")
        b = arc.find("\n" + TERMINATOR)
        if a < 0 or b < 0:
            print("VERIFY FAIL: markers missing")
            return 1
        body = arc[a + len(MARK) + 1:b]
        d = digest(body)
        named = open(NAMED, encoding="utf-8").read()
        stub = "docs/named-archive-m339-rows.md" in named
        gone = "## M308 (s268, STATIC, zero box; s269 review round" not in named
        ok = d == EXPECT_SHA and stub and gone
        print("VERIFY %s: archived-region sha1 %s == pinned %s; stub=%s; rows gone=%s"
              % ("PASS" if ok else "FAIL", d, EXPECT_SHA, stub, gone))
        return 0 if ok else 1
    txt = open(NAMED, encoding="utf-8").read()
    if START not in txt:
        print("already rotated (heading absent)")
        return 0
    a = txt.find(START)
    b = txt.find(END)
    body = txt[a:b]
    if b < 0 or not body.startswith(START):
        print("FAIL: region not found")
        return 1
    d = digest(body)
    stub = (START + ", STATIC, zero box; s269 review) — FULL rows VERBATIM at "
            "`docs/named-archive-m339-rows.md:8` (§rotation-1 marker at `:7`, s320-chain2 "
            "headroom rotation, sha1 `%s`; re-asserted by `scripts/m339_named_rotate.py "
            "--verify`); this stub governs. `0x4ddcf1`'s UNATTRIBUTED edge is CLOSED by "
            "`## M339`: nonzero `jge` = callee 0x5f1394's result cell `[obj+0xa40]`.\n\n" % d)
    hdr = ("# NAMED archive — M339 rotation\n\n"
           "Verbatim rows moved out of `NAMED.md` to keep it under the 250,000 B fail line.\n"
           "Each region keeps its original `## <id>` heading and table bytes.\n\n\n"
           + MARK + "\n")
    open(ARC, "w", encoding="utf-8").write(hdr + body + "\n" + TERMINATOR + "\n")
    open(NAMED, "w", encoding="utf-8").write(txt[:a] + stub + txt[b:])
    print("rotated M308 -> docs/named-archive-m339-rows.md (%d B, sha1 %s); NAMED %d -> %d B"
          % (len(body), d, len(txt), len(open(NAMED, encoding="utf-8").read())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
