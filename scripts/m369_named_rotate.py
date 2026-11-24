#!/usr/bin/env python3
"""m369_named_rotate.py — rotate two settled NAMED.md blocks VERBATIM into
`docs/named-archive-m369-rows.md` and leave a mechanical stub with the block's sha1.

Why: NAMED.md stands at 248,819 B (1,181 B under the 250,000 cap — inside the 5 kB ROTATE
trigger) before `## M369` is added.  `## M361` (A/V radio flags) and `## M363` (audio
callees) are settled side-track rows: no governing text, no instrument, nothing in
NEXT_PROMPT.md's pick list reads them.

The archive keeps every byte; each stub is MECHANICAL (header + provenance + sha1 + length).

    python3 scripts/m369_named_rotate.py            # rotate; a 2nd run is a no-op
    python3 scripts/m369_named_rotate.py --verify   # sha1 + byte-count check only
"""
import argparse
import hashlib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs/named-archive-m369-rows.md")
TARGETS = ["## M361 ", "## M363 "]
HEAD = ("# NAMED.md `## M361`, `## M363` — ROTATED VERBATIM\n"
        "(byte-exact, by `scripts/m369_named_rotate.py`)\n")


def block_of(text, head):
    i = text.index(head)
    j = text.index("\n## ", i + 3)
    return text[i:j], i, j


def stub(head, sha, n):
    return ("%s— VERBATIM at `docs/named-archive-m369-rows.md` (sha1 `%s`, %d B)\n"
            % (head, sha, n))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    named = open(NAMED, encoding="utf-8").read()
    arch = open(ARCHIVE, encoding="utf-8").read() if os.path.exists(ARCHIVE) else HEAD
    for head in TARGETS:
        if head not in named:
            print("%-10s STUBBED (absent)" % head.strip())
            continue
        blk, i, j = block_of(named, head)
        if "docs/named-archive-m369-rows.md" in blk.splitlines()[0]:
            print("%-10s STUBBED (already rotated)" % head.strip())
            continue  # idempotent: a rotation stub is never rotated again
        sha = hashlib.sha1(blk.encode()).hexdigest()[:16]
        if not a.verify:
            arch = arch.rstrip("\n") + "\n\n<!-- %s sha1 %s len %d -->\n%s" % (
                head.strip(), sha, len(blk), blk) + "\n"
            named = named[:i] + stub(head, sha, len(blk)) + named[j + 1:]
        print("%-10s %s sha1 %s" % (head.strip(), "ROTATED" if not a.verify else "PRESENT", sha))
    if not a.verify:
        open(ARCHIVE, "w", encoding="utf-8").write(arch if arch.endswith("\n") else arch + "\n")
        open(NAMED, "w", encoding="utf-8").write(named)
    print("NAMED.md now %d B" % len(open(NAMED, encoding="utf-8").read()))


if __name__ == "__main__":
    main()
