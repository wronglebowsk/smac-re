#!/usr/bin/env python3
"""m387_named_rotate.py - move NAMED.md's settled `## M335` block VERBATIM into
`docs/named-archive-m387-m335-rows.md` and leave a one-line pointer stub.

M387 must add a block and NAMED.md carried only 2,713 B of headroom (247,287 B against the
250,000 B FAIL) - under the 5 KB rotation trigger.  M335 (the alpha #DIFF ladder, s317-chain2,
7/7) is settled: 0 other mentions anywhere in NAMED.md, 0 mentions in NEXT_PROMPT.md /
SESSION_NOTES.md, and its subject (the difficulty name table) does not touch the relations
matrix this milestone works on.  The rotated text is byte-for-byte what NAMED carried.

    python3 scripts/m387_named_rotate.py            # rotate (idempotent)
    python3 scripts/m387_named_rotate.py --verify   # archive body sha1 vs the stub's sha1
"""
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-m387-m335-rows.md")
HEAD = "## M335"
ARCHIVE_HEAD = ("# NAMED.md `## M335` - ROTATED VERBATIM (byte-exact) by "
                "scripts/m387_named_rotate.py\n\n")


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
        want = ln.split("sha1 `")[1].split("`")[0] if "sha1 `" in ln else ""
        good = bool(want) and (want.startswith(got) or got.startswith(want))
        print(f"archive {got[:16]}... stub {want[:16] if want else '(none)'}... "
              f"{'PASS' if good else 'FAIL'}")
        return 0 if good else 1
    body, pre, post = split_block(text)
    if "--force" not in sys.argv and "FULL rows VERBATIM" in body and len(body) < 900:
        print("already rotated (the head is the pointer stub); use --force to re-do")
        return 0
    sha = hashlib.sha1(body.encode()).hexdigest()
    if os.path.exists(ARCHIVE) and open(ARCHIVE).read().split("\n\n", 1)[1] == body:
        print(f"already rotated, sha1 {sha}")
        return 0
    open(ARCHIVE, "w").write(ARCHIVE_HEAD + body)
    first = body.splitlines()[0]
    stub = (f"{first} - FULL rows VERBATIM at `docs/named-archive-m387-m335-rows.md` "
            f"(sha1 `{sha}`, {len(body.encode())} B); this stub governs.\n")
    open(NAMED, "w").write(pre + stub + post)
    print(f"rotated {len(body.encode())} B, sha1 {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
