#!/usr/bin/env python3
"""m371_named_rotate.py - move NAMED.md's `## M318` block VERBATIM into
`docs/named-archive-m371-rows.md` and leave a mechanical stub with its sha1 + byte count.

NAMED.md stands at 246,175 B against the 250,000 B cap (3,825 B of headroom, inside the
5 KB ROTATE trigger) before `## M371` is added.  `## M318` is a settled side-track answer
(the selection-refresh pair): no governing text reads it, and its own ACCEPT evidence stays
in `evidence/m318_refresh_pair.txt`.  The archive keeps every byte.

    python3 scripts/m371_named_rotate.py            # rotate (idempotent)
    python3 scripts/m371_named_rotate.py --verify   # sha1 + byte-count check only
"""
import argparse
import hashlib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs/named-archive-m371-rows.md")
HEAD = "## M318 (s289"
STUB_HEAD = "## M318 "
ARCH = "docs/named-archive-m371-rows.md"
TITLE = ("# NAMED.md `## M318` - ROTATED VERBATIM (byte-exact) by scripts/m371_named_rotate.py\n")


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
        # rotated form: re-hash the archived block and compare to the stub
        import re
        stub = next((l for l in named.splitlines() if l.startswith(STUB_HEAD)), None)
        if stub is None:
            raise SystemExit("M318 block absent from NAMED.md")
        m = re.search(r"sha1 `([0-9a-f]+)`, (\d+) B", stub)
        if not m:
            raise SystemExit("stub carries no sha1/len")
        blk, _, _ = block_of(arch, HEAD)
        if blk.endswith("\n"):
            blk = blk[:-1]          # the archive writer's terminal newline
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
    arch = arch.rstrip("\n") + "\n\n<!-- ## M318 sha1 %s len %d -->\n%s\n" % (sha, n, blk)
    stub = ("## M318 — VERBATIM at `%s` (sha1 `%s`, %d B); this stub governs: the selection-REFRESH "
            "PAIR = FUN_004e8d60 (selected-base unit-support census) then FUN_004e78e0 (pane refresh)\n"
            % (ARCH, sha, n))
    named = named[:i] + stub + "\n" + named[j + 1:]
    open(ARCHIVE, "w", encoding="utf-8").write(arch if arch.endswith("\n") else arch + "\n")
    open(NAMED, "w", encoding="utf-8").write(named)
    print("ROTATED  ## M318 sha1 %s len %d -> %s" % (sha, n, ARCH))


if __name__ == "__main__":
    main()
