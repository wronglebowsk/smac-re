#!/usr/bin/env python3
"""m391_named_rotate.py - move NAMED.md's settled `## M301` block VERBATIM into
`docs/named-archive-m391-m301-rows.md` and leave a one-line pointer stub.

M391 must add a block and, once M389/M390 landed on origin/main, NAMED.md measured
250,838 B against the 250,000 B FAIL.  M301 (s256, STATIC zero box) is settled, is a
FULL block (guarded: the script refuses a block whose head or body already points at
an archive or calls itself a stub), and nothing in NEXT_PROMPT / SESSION_NOTES /
pick-archive points at it as live.  The rotated text is byte-for-byte what NAMED carried.

    python3 scripts/m391_named_rotate.py            # rotate (idempotent)
    python3 scripts/m391_named_rotate.py --verify   # archive body sha1 vs the stub's sha1
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-m391-m301-rows.md")
HEAD = "## M301"
ARCHIVE_HEAD = ("# NAMED.md `## M301` - ROTATED VERBATIM (byte-exact) by "
                "scripts/m391_named_rotate.py\n\n")


def split_block(text):
    lines = text.splitlines(keepends=True)
    s = next(i for i, ln in enumerate(lines) if ln.startswith(HEAD))
    e = next((i for i in range(s + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return "".join(lines[s:e]), "".join(lines[:s]), "".join(lines[e:])


def main():
    text = open(NAMED).read()
    if "--verify" in sys.argv:
        body = open(ARCHIVE).read().split("\n\n", 1)[1]
        got = hashlib.sha1(body.encode()).hexdigest()
        ln = next((ln for ln in text.splitlines() if ln.startswith(HEAD)), None)
        if ln is None:
            print("MISSING stub")
            return 1
        m = re.search(r'sha1 `([0-9a-f]+)`', ln)
        want = m.group(1) if m else ""
        ok = bool(want) and (want.startswith(got) or got.startswith(want))
        print(f"archive {got[:16]}... stub {want[:16]}... {'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1
    body, pre, post = split_block(text)
    if "STUB" in body.splitlines()[0] or "VERBATIM at `docs/" in body.splitlines()[0] \
            or "ROTATED VERBATIM" in body:
        print("REFUSED: that block is already a stub/pointer - pick a FULL block")
        return 2
    sha = hashlib.sha1(body.encode()).hexdigest()
    if os.path.exists(ARCHIVE) and open(ARCHIVE).read().split("\n\n", 1)[1] == body:
        print(f"already rotated, sha1 {sha}")
        return 0
    open(ARCHIVE, "w").write(ARCHIVE_HEAD + body)
    first = body.splitlines()[0]
    stub = (f"{first} - ROTATED VERBATIM at `docs/named-archive-m391-m301-rows.md` "
            f"(sha1 `{sha}`, {len(body)} B); this stub governs.\n")
    open(NAMED, "w").write(pre + stub + post)
    print(f"rotated {len(body)} B, sha1 {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
