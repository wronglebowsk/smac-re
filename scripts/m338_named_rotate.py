#!/usr/bin/env python3
"""M338 NAMED headroom rotation (s319-chain2): move `## M326` VERBATIM to
`docs/named-archive-m338-rows.md` (§rotation-1) before adding the M338 block.
Same law as `scripts/m337_named_rotate.py`: the oldest settled chain-2 block
moves byte-for-byte, the stub keeps its claims one line and the pointer's sha1.

    python3 scripts/m338_named_rotate.py            # perform the move
    python3 scripts/m338_named_rotate.py --verify   # re-hash the archived region
"""
import argparse
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARC = os.path.join(ROOT, "docs", "named-archive-m338-rows.md")

START = "## M326 (s301-chain2, STATIC 10/10, review #332 hardened)"
END = "## M325 (s299-chain2)"
MARK = "§rotation-1 (M326, s319-chain2 headroom rotation)"
TERMINATOR = "(§rotation-1 ends; nothing below it belongs to this region.)"
EXPECT_SHA = "a882ee40851d"   # pinned constant (not read back from the archive, so an
                             # edit to the archive cannot re-bless itself)


def region():
    txt = open(NAMED, encoding="utf-8").read()
    a = txt.find(START)
    b = txt.find(END)
    if a < 0 or b < 0 or b < a:
        return txt, None
    return txt[:a] + txt[b:], txt[a:b]


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
            print("VERIFY FAIL: markers missing"); return 1
        body = arc[a + len(MARK) + 1:b]
        pinned = EXPECT_SHA
        d = digest(body)
        named = open(NAMED, encoding="utf-8").read()
        stub = "FULL rows VERBATIM at `docs/named-archive-m338-rows.md" in named
        gone = "27 accesses, 0 sibling-into-224" not in named
        ok = d == pinned and stub and gone
        print("VERIFY %s: archived-region sha1 %s == pinned %s; stub=%s; rows gone=%s"
              % ("PASS" if ok else "FAIL", d, pinned, stub, gone))
        return 0 if ok else 1
    txt = open(NAMED, encoding="utf-8").read()
    if START not in txt:
        print("already rotated (heading absent)"); return 0
    a = txt.find(START)
    b = txt.find(END)
    body = txt[a:b]
    if b < 0 or not body.startswith(START):
        print("FAIL: region not found"); return 1
    new_named = txt[:a] + "@@STUB@@" + txt[b:]
    d = digest(body)
    stub = (START + " — FULL rows VERBATIM at `docs/named-archive-m338-rows.md:7` "
            "(§rotation-1 marker at `:6`, s319-chain2 headroom rotation, sha1 `%s` — the region "
            "is bounded by its own terminator line and its digest is re-asserted by "
            "`scripts/m338_named_rotate.py --verify`); this stub governs. block+224 = the "
            "per-faction DEFERRED HURRY-PRODUCTION PAYMENT (energy debt), settled at upkeep; "
            "hurry defer-vs-pay flag chain 920434&91c62c, readers = AVAILABLE (220-224), "
            "reset 59f0bf/c1, save carry [0]*8.\n\n" % d)
    hdr = ("# NAMED archive — M338 rotation\n\n"
           "Verbatim rows moved out of `NAMED.md` to keep it under the 250,000 B fail line.\n"
           "Each region keeps its original `## <id>` heading and table bytes.\n\n\n"
           + MARK + "\n")
    open(ARC, "w", encoding="utf-8").write(hdr + body + "\n" + TERMINATOR + "\n")
    open(NAMED, "w", encoding="utf-8").write(new_named.replace("@@STUB@@", stub, 1))
    print("rotated M326 -> docs/named-archive-m338-rows.md (%d B, sha1 %s); NAMED %d -> %d B"
          % (len(body), d, len(txt), len(new_named)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
