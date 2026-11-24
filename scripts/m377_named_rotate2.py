#!/usr/bin/env python3
"""m377_named_rotate.py - move NAMED.md's settled `## M362` block VERBATIM into
`docs/named-archive-m377-m362-rows.md` and leave a one-line pointer stub.

M377 must add a block and NAMED.md carried only 1,735 B of headroom (248,265 B against
the 250,000 B FAIL) - under the 5 KB rotation trigger.  M362 (the 0x4db1xx relations
page: its +0x15a0 group is 13 checkboxes whose ids ARE the relations bits) is settled
and is not re-read by anything since M375.  The rotated text is byte-for-byte what
NAMED carried.

    python3 scripts/m377_named_rotate2.py           # rotate (idempotent)
    python3 scripts/m377_named_rotate2.py --verify  # archive sha1 == the NAMED stub sha1
"""
import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-m377-m362-rows.md")
HEAD = "## M362"
ARCHIVE_HEAD = ("# NAMED.md `## M362` - ROTATED VERBATIM (byte-exact) by "
                "scripts/m377_named_rotate.py\n\n")


def block(text, head=HEAD):
    lines = text.splitlines(keepends=True)
    s = next(i for i, ln in enumerate(lines) if ln.startswith(head))
    e = next((i for i in range(s + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return "".join(lines[s:e]), "".join(lines[:s]), "".join(lines[e:])


def main():
    verify = "--verify" in sys.argv
    if verify:
        # idempotent: the archive body's sha1 must equal the sha1 the NAMED stub records
        body = open(ARCHIVE).read().split("\n\n", 1)[1]
        got = hashlib.sha1(body.encode()).hexdigest()[:16]
        stub = next(ln for ln in open(NAMED).read().splitlines()
                    if ln.startswith(HEAD) and "VERBATIM" in ln)
        want = re.search(r"sha1 `([0-9a-f]+)`", stub).group(1)
        print(f"archive sha1 {got}  stub sha1 {want}  bytes {len(body)}")
        ok = got == want
        print("VERIFY", "PASS" if ok else "FAIL")
        return 0 if ok else 1

    text = open(NAMED).read()
    body, pre, post = block(text)
    sha = hashlib.sha1(body.encode()).hexdigest()
    open(ARCHIVE, "w").write(ARCHIVE_HEAD + body)
    stub = (f"## M362 - VERBATIM at `docs/named-archive-m377-m362-rows.md` "
            f"(sha1 `{sha[:16]}`, {len(body)} B): the 0x4db1xx sibling IS the FACTION "
            f"RELATIONS page; its +0x15a0 group = 13 checkboxes whose ids ARE the bits. "
            f"ev `evidence/m362_sibling.txt:100`\n")
    open(NAMED, "w").write(pre + stub + post)
    print(f"rotated M362 ({len(body)} B, sha1 {sha[:16]}) -> {os.path.relpath(ARCHIVE, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
