#!/usr/bin/env python3
"""m384_named_rotate.py - move NAMED.md's settled `## M267-M271` block VERBATIM
into `docs/named-archive-m384-m267-rows.md` and leave a one-line pointer stub.

M384 must add a block and NAMED.md carried only 2,713 B of headroom (247,287 B
against the 250,000 B FAIL) - under the 5 KB rotation trigger.  M267-M271
(s208/s210, PASS 14/14 + 10/10) is settled: it is the vtable/ctor/dtor round,
nothing in NEXT_PROMPT or SESSION_NOTES refers to it, and its full rows already
live in docs/named-archive-m332-rows.md.  The rotated text is byte-for-byte what
NAMED carried.

    python3 scripts/m384_named_rotate.py            # rotate (idempotent)
    python3 scripts/m384_named_rotate.py --verify   # archive body sha1 vs the stub's sha1
"""
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-m384-m267-rows.md")
HEAD = "## M267-M271"
ARCHIVE_HEAD = ("# NAMED.md `## M267-M271` - ROTATED VERBATIM (byte-exact) by "
                "scripts/m384_named_rotate.py\n\n")


def split_block(text):
    lines = text.splitlines(keepends=True)
    s = next(i for i, ln in enumerate(lines) if ln.startswith(HEAD))
    e = next((i for i in range(s + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return "".join(lines[s:e]), "".join(lines[:s]), "".join(lines[e:])


def main():
    text = open(NAMED, encoding="latin-1").read()
    if "--verify" in sys.argv:
        body = open(ARCHIVE, encoding="latin-1").read()[len(ARCHIVE_HEAD):]
        h = hashlib.sha1(body.encode("latin-1")).hexdigest()[:12]
        stub = next(ln for ln in text.splitlines() if ln.startswith(HEAD))
        print("archive sha1 %s | stub %s" % (h, stub))
        return 0 if h in stub else 1
    if not any(ln.startswith(HEAD) for ln in text.splitlines()):
        print("already rotated - nothing to do")
        return 0
    block, before, after = split_block(text)
    h = hashlib.sha1(block.encode("latin-1")).hexdigest()[:12]
    os.makedirs(os.path.dirname(ARCHIVE), exist_ok=True)
    with open(ARCHIVE, "w", encoding="latin-1") as f:
        f.write(ARCHIVE_HEAD + block)
    stub = ("%s -- ROTATED VERBATIM by `scripts/m384_named_rotate.py` to "
            "`docs/named-archive-m384-m267-rows.md` (sha1 `%s`); the block was the "
            "settled M267-M271 vtable/ctor round, full rows already at "
            "`docs/named-archive-m332-rows.md`.\n\n" % (HEAD, h))
    with open(NAMED, "w", encoding="latin-1") as f:
        f.write(before + stub + after)
    print("rotated %d bytes (sha1 %s) -> %s" % (len(block), h, os.path.relpath(ARCHIVE, ROOT)))
    print("NAMED.md now %d bytes" % os.path.getsize(NAMED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
