#!/usr/bin/env python3
"""m376_named_rotate.py - move NAMED.md's settled `## M286` block VERBATIM into
`docs/named-archive-m376-rows.md` and leave a mechanical stub with its sha1 +
byte count.

NAMED.md stands at 248,265 B against the 250,000 B cap (1,735 B of headroom,
inside the 5 KB ROTATE trigger) before `## M376` is added.  `## M286` is a
settled static/live NEGATIVE whose live half is already marked
INSTRUMENT-INVALID by M293; nothing governs from it and its evidence stays in
the repo.  The archive keeps every byte.

    python3 scripts/m376_named_rotate.py            # rotate (idempotent)
    python3 scripts/m376_named_rotate.py --verify   # sha1 + byte-count check
"""
import argparse
import hashlib
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs/named-archive-m376-rows.md")
HEAD = "## M286 (s231"
STUB_HEAD = "## M286 "
ARCH = "docs/named-archive-m376-rows.md"
TITLE = ("# NAMED.md `## M286` - ROTATED VERBATIM (byte-exact) by scripts/m376_named_rotate.py\n")


def block_of(text, head):
    i = text.index(head)
    try:
        j = text.index("\n## ", i + 3)
    except ValueError:
        j = len(text)
    return text[i:j], i, j


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    named = open(NAMED, encoding="utf-8").read()
    arch = open(ARCHIVE, encoding="utf-8").read() if os.path.exists(ARCHIVE) else TITLE + "\n"
    if HEAD not in named and STUB_HEAD in named:
        stub = next((l for l in named.splitlines() if l.startswith(STUB_HEAD)), None)
        if stub is None:
            raise SystemExit("M286 block absent from NAMED.md")
        m = re.search(r"sha1 `([0-9a-f]+)`, (\d+) B", stub)
        if not m:
            raise SystemExit("stub carries no sha1/len")
        blk, _, _ = block_of(arch, HEAD)
        if blk.endswith("\n"):
            blk = blk[:-1]
        sha = hashlib.sha1(blk.encode()).hexdigest()
        ok = sha == m.group(1) and len(blk.encode()) == int(m.group(2))
        print("VERIFY   %s sha1 %s len %d (stub %s/%s B)"
              % ("PASS" if ok else "FAIL", sha, len(blk.encode()), m.group(1), m.group(2)))
        return 0 if ok else 1
    blk, i, j = block_of(named, HEAD)
    sha = hashlib.sha1(blk.encode()).hexdigest()
    n = len(blk.encode())
    if a.verify:
        print("PRESENT  sha1 %s len %d" % (sha, n))
        return 0
    arch = arch.rstrip("\n") + "\n\n<!-- ## M286 sha1 %s len %d -->\n%s\n" % (sha, n, blk)
    stub = ("## M286 \u2014 VERBATIM at `%s` (sha1 `%s`, %d B); this stub governs: the REALLYQUIT "
            "message dialog is family 0x67164c but does NOT dispatch +0x4c on clicks (static 5/5); "
            "the LIVE half is INSTRUMENT-INVALID per M293\n" % (ARCH, sha, n))
    named = named[:i] + stub + "\n" + named[j + 1:]
    open(ARCHIVE, "w", encoding="utf-8").write(arch if arch.endswith("\n") else arch + "\n")
    open(NAMED, "w", encoding="utf-8").write(named)
    print("ROTATED  ## M286 sha1 %s len %d -> %s" % (sha, n, ARCH))


if __name__ == "__main__":
    main()
