# -*- coding: utf-8 -*-
"""M337 NAMED headroom rotation (s318-chain1): move `## M277` VERBATIM to
`docs/named-archive-m337-rows.md` (§rotation-1).  NAMED.md was 2.6 KB under the 250,000 fail line
and this session must add a block, so the oldest settled small block moves first (same law as
`docs/named-archive-b28-rows.md` §rotation-1/2 and `scripts/b28_named_rotate2.py`).

Every row moves byte-for-byte; the stub keeps the gate count, the M278 refinement note and the
pointer with its own sha1.

    python3 scripts/m337_named_rotate.py            # perform the move (refuses if already archived)
    python3 scripts/m337_named_rotate.py --verify   # re-hash the archived region, re-check the stub
"""
import argparse
import hashlib
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARC = os.path.join(ROOT, "docs", "named-archive-m337-rows.md")

START = "## M277 (s218, PASS 6/6)"
END = "## M278 (s219, PASS 7/7)"
MARK = "§rotation-1 (M277, s318-chain1 headroom rotation)"
TERMINATOR = "(§rotation-1 ends; nothing below it belongs to this region.)"
SPINE = ("M277 (s218, PASS 6/6) - the scaled read is the permanent block-0 view; M274 G2's spill "
         "landing is arithmetically dead")
STUB = ("## " + SPINE + " — FULL rows VERBATIM at `docs/named-archive-m337-rows.md:ARC_LINE` "
        "(§rotation-1 marker at `:MARKLINE`, s318-chain1 headroom rotation, sha1 `SHA12` — the "
        "region is bounded by its own terminator line, its line number AND the full digest "
        "re-asserted by `scripts/m337_named_rotate.py --verify`); this stub governs. Every row is "
        "V; the M278 refinement (the player-index-0 real row) is archived with them.")
HEADER = ("# NAMED archive — M337 rotation\n\n"
          "Verbatim rows moved out of `NAMED.md` to keep it under the 250,000 B fail line.\n"
          "Each region keeps its original `## <id>` heading and table bytes.\n\n")


def read(p):
    return io.open(p, encoding="utf-8").read()


def sha12(region):
    return hashlib.sha1(region.encode("utf-8")).hexdigest()[:12]


def region_of(txt):
    i = txt.find(START)
    j = txt.find(END)
    if i < 0 or j < 0 or j <= i:
        raise SystemExit("region not found (start=%d end=%d)" % (i, j))
    return txt[i:j]


def region_arc(txt):
    i = txt.find(START)
    j = txt.find(TERMINATOR)
    if i < 0 or j < 0 or j <= i:
        raise SystemExit("archived region not found (start=%d end=%d)" % (i, j))
    return txt[i:j]


def verify():
    named, arc = read(NAMED), read(ARC)
    region = region_arc(arc)
    s = sha12(region)
    lines = arc.splitlines()
    mark = next((n for (n, l) in enumerate(lines, 1) if l.startswith(MARK)), None)
    if mark is None:
        raise SystemExit("VERIFY FAIL: marker absent")
    if region in named:
        raise SystemExit("VERIFY FAIL: the archived region is still present in NAMED.md")
    sl = next((l for l in named.splitlines() if l.startswith("## " + SPINE)), None)
    if sl is None:
        raise SystemExit("VERIFY FAIL: stub line absent")
    m = re.search(r"m337-rows\.md:(\d+)", sl)
    if not m:
        raise SystemExit("VERIFY FAIL: stub has no archive line cite")
    arc_line = int(m.group(1))
    if not lines[arc_line - 1].startswith(START):
        raise SystemExit("VERIFY FAIL: cite %d does not start the region" % arc_line)
    if sl.find(s) < 0:
        raise SystemExit("VERIFY FAIL: stub sha1 != archived region sha1 %s" % s)
    if TERMINATOR not in arc:
        raise SystemExit("VERIFY FAIL: terminator absent")
    print("VERIFY PASS: region sha1 %s, marker :%d, region :%d, %d lines"
          % (s, mark, arc_line, len(region.splitlines())))


def move():
    if not os.path.exists(ARC):
        io.open(ARC, "w", encoding="utf-8").write(HEADER)
    named, arc = read(NAMED), read(ARC)
    region = region_of(named)
    s = sha12(region)
    if MARK in arc:
        raise SystemExit("REFUSING: %r already archived" % MARK)
    head = arc if arc.endswith("\n") else arc + "\n"
    new_arc = head + "\n" + MARK + "\n" + region + TERMINATOR + "\n"
    lines = new_arc.splitlines()
    mark = next((n for (n, l) in enumerate(lines, 1) if l.startswith(MARK)))
    arc_line = next((n for (n, l) in enumerate(lines, 1) if l.startswith(START)))
    stub = STUB.replace("ARC_LINE", str(arc_line)).replace("MARKLINE", str(mark)).replace("SHA12", s)
    io.open(ARC, "w", encoding="utf-8").write(new_arc)
    io.open(NAMED, "w", encoding="utf-8").write(named.replace(region, stub + "\n", 1))
    print("MOVED %d lines (%d B), sha1 %s -> archive :%d, stub cites :%d"
          % (len(region.splitlines()), len(region.encode()), s, arc_line, arc_line))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    verify() if a.verify else move()
