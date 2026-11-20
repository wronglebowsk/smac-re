#!/usr/bin/env python3
"""s309 cap trim: NEXT_PROMPT.md crossed 12,309 B over the 12,000 B warn cap after the (x)
OPEN-LEADS pick list landed. Retire the M328/M330 one-liner rows (they duplicate `NAMED ## M328`
and `## M330`, which govern) VERBATIM into docs/pick-archive.md §trim-s309-chain1, asserting the
sha1 and the byte-substring after the append. FAILS (rc=1) if the head is still over 12,000 B.
"""
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NP = os.path.join(ROOT, "NEXT_PROMPT.md")
ARC = os.path.join(ROOT, "docs", "pick-archive.md")
CAP = 12000
RETIRE = [
    "M328 (s304-chain2): 91c64c=turn-start ENERGY snapshot; 920434='multi' session flag "
    "(noun INFERRED, lifecycle V). HURRY story closed. 14/14 030a6fc12e4a7cd7 x2; 38/38 "
    "(37+1 NO-OP) 36259eee0736d9c1; ST 5/5. NAMED ## M328.",
    "M330 (s307-chain2): block+300=UPKEEP SPEND ACCUMULATOR — entry-zeroed, feeder 4f47f0 "
    "(ROUND>1, conditional halving), refund trunc(kx/3) k=1 diff4/2 diff>=5, mask gate VACUOUS "
    "(cl=8). 13/13 470d844054b1b101 x2; 31/31+1 NO-OP cf85092dea6baa93. NAMED ## M330.",
]
HEAD = "\n## §trim-s309-chain1 (s309, NEXT_PROMPT cap trim; `NAMED ## M328`/`## M330` govern)\n\n"


def main():
    np_src = open(NP, encoding="utf-8").read()
    arc = open(ARC, encoding="utf-8").read()
    for line in RETIRE:
        if np_src.count(line) != 1:
            print("FAIL: retire candidate occurs %d times in NEXT_PROMPT.md: %r"
                  % (np_src.count(line), line[:60]))
            return 1
        if line in arc:
            print("FAIL: already archived, refusing to duplicate: %r" % line[:60])
            return 1
    block = HEAD + "".join("- %s\n" % l for l in RETIRE)
    digests = [(l[:40], hashlib.sha1(l.encode()).hexdigest()[:12]) for l in RETIRE]
    with open(ARC, "a", encoding="utf-8") as fh:
        fh.write(block)
    after = open(ARC, encoding="utf-8").read()
    for l in RETIRE:
        if l not in after:
            print("FAIL: appended text is not a byte-substring of the archive")
            return 1
    for label, dg in digests:
        print("archived sha1 %s %s" % (dg, label))
    new = np_src
    for l in RETIRE:
        new = new.replace(l + "\n", "")
    if len(new.encode()) > CAP:
        print("FAIL: NEXT_PROMPT.md still %d B > %d B cap" % (len(new.encode()), CAP))
        return 1
    open(NP, "w", encoding="utf-8").write(new)
    print("PASS trim-s309: NEXT_PROMPT.md %d -> %d B (cap %d); archive +%d B"
          % (len(np_src.encode()), len(new.encode()), CAP, len(block.encode())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
