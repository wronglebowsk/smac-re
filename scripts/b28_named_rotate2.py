# -*- coding: utf-8 -*-
"""B28 review-round NAMED rotation #2 (s316-chain1): move `## M250`..`## M254` VERBATIM to
`docs/named-archive-b28-rows.md` (§rotation-2).

The #351 merge pulled M334's block in from main and took NAMED.md to 251,910 B - OVER the
250,000 fail line - so a settled region had to move before this session could close (the same
law that produced §rotation-1 last fire).

Victim: M250-M254 (s200-s201, all V rows but M254's bit-naming row), the oldest settled block
of the region-verdict era.  Every row moves byte-for-byte; the stub keeps the pass counts, the
INFERRED caveat and the pointer with its own sha1.

    python3 scripts/b28_named_rotate2.py            # perform the move (guarded, refuses if done)
    python3 scripts/b28_named_rotate2.py --verify   # re-hash the archived region + re-pin the stub
    python3 scripts/b28_named_rotate2.py --restub   # rewrite the stub line from the STUB template
"""
import argparse
import hashlib
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARC = os.path.join(ROOT, "docs", "named-archive-b28-rows.md")

START = "## M250 (s200, PASS 7/7)"
END = "## M255-M258 (s201-s202, PASS 8/8)"
MARK = "§rotation-2 (M250-M254, s316-chain1 review-round headroom rotation)"
TERMINATOR = "(§rotation-2 ends; anything above belongs to §rotation-1.)"
SPINE = ("M250-M254 (s200-s201; PASS 7/7 + 7/7 + 7/7 + 8/8 + 8/8) — the region generator, the "
         "per-faction per-region verdict byte, the coarse map's single consumer, the four verdict "
         "codes, and the contact bits")
STUB = ("## " + SPINE + " — FULL rows VERBATIM at `docs/named-archive-b28-rows.md:ARC_LINE` "
        "(§rotation-2 marker at `:MARKLINE`, s316-chain1 review-round headroom rotation #2, sha1 "
        "`SHA12` — the region is bounded by its own terminator line, its line number AND the full "
        "digest re-asserted by `scripts/b28_named_rotate2.py --verify`); this stub governs. "
        "M254's bit-naming row stays INFERRED (named); every other row is V.")


def read(p):
    return io.open(p, encoding="utf-8").read()


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


def sha12(region):
    return hashlib.sha1(region.encode("utf-8")).hexdigest()[:12]


def verify():
    named, arc = read(NAMED), read(ARC)
    region = region_arc(arc)
    s = sha12(region)
    lines = arc.splitlines()
    mark = next((n for (n, l) in enumerate(lines, 1) if l.startswith(MARK)), None)
    if mark is None:
        raise SystemExit("VERIFY FAIL: marker %r absent from archive" % MARK)
    stub = region_of(named) if START in named else None
    if stub is not None:
        raise SystemExit("VERIFY FAIL: region still present in NAMED.md")
    sl = next((l for l in named.splitlines() if l.startswith("## " + SPINE)), None)
    if sl is None:
        raise SystemExit("VERIFY FAIL: stub line absent from NAMED.md")
    m = re.search(r"b28-rows\.md:(\d+)", sl)
    if not m:
        raise SystemExit("VERIFY FAIL: stub carries no archive line cite")
    arc_line = int(m.group(1))
    if lines[arc_line - 1].startswith(START) is False:
        raise SystemExit("VERIFY FAIL: cite %d does not start the archived region" % arc_line)
    if sl.find(s) < 0:
        raise SystemExit("VERIFY FAIL: stub sha1 %s does not match the archived region %s"
                         % (s, ""))
    if TERMINATOR not in arc:
        raise SystemExit("VERIFY FAIL: terminator absent")
    print("VERIFY PASS: region sha1 %s, marker :%d, region :%d, %d lines"
          % (s, mark, arc_line, len(region.splitlines())))


def restub():
    named, arc = read(NAMED), read(ARC)
    region = region_arc(arc)
    lines = arc.splitlines()
    mark = next((n for (n, l) in enumerate(lines, 1) if l.startswith(MARK)))
    arc_line = next((n for (n, l) in enumerate(lines, 1) if l.startswith(START)))
    stub = STUB.replace("ARC_LINE", str(arc_line)).replace("MARKLINE", str(mark)) \
               .replace("SHA12", sha12(region))
    out = []
    seen = False
    for l in named.splitlines(True):
        if l.startswith("## " + SPINE):
            out.append(stub + "\n")
            seen = True
        else:
            out.append(l)
    if not seen:
        raise SystemExit("stub line not found in NAMED.md")
    io.open(NAMED, "w", encoding="utf-8").write("".join(out))
    print("RESTUB done")


def move():
    named, arc = read(NAMED), read(ARC)
    region = region_of(named)
    s = sha12(region)
    if MARK in arc:
        raise SystemExit("REFUSING: %r already archived - use --restub" % MARK)
    head = arc if arc.endswith("\n") else arc + "\n"
    new_arc = head + "\n" + MARK + "\n" + region + TERMINATOR + "\n"
    lines = new_arc.splitlines()
    mark = next((n for (n, l) in enumerate(lines, 1) if l.startswith(MARK)))
    arc_line = next((n for (n, l) in enumerate(lines, 1) if l.startswith(START)))
    stub = STUB.replace("ARC_LINE", str(arc_line)).replace("MARKLINE", str(mark)) \
               .replace("SHA12", s)
    io.open(ARC, "w", encoding="utf-8").write(new_arc)
    io.open(NAMED, "w", encoding="utf-8").write(named.replace(region, stub + "\n", 1))
    print("MOVED %d lines (%d B), sha1 %s -> archive :%d, stub cites :%d"
          % (len(region.splitlines()), len(region.encode()), s, arc_line, arc_line))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--restub", action="store_true")
    a = ap.parse_args()
    if a.verify:
        verify()
    elif a.restub:
        restub()
    else:
        move()
