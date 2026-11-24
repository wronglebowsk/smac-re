#!/usr/bin/env python3
"""m385_named_rotate.py - move NAMED.md's settled `## M364` block VERBATIM into
`docs/named-archive-m385-m364-rows.md` and leave a one-line pointer stub.

M385 must add a block and NAMED.md carries only 2,713 B of headroom against the
250,000 B FAIL - under the 5 KB rotation trigger.  M364 (the relations-bit nouns)
is settled and already superseded in its own text (its 0x8 = AT WAR row was
RETRACTED by M369; M371 named 0x10).  The rotated text is byte-for-byte what
NAMED carried.

    python3 scripts/m385_named_rotate.py            # rotate (idempotent)
    python3 scripts/m385_named_rotate.py --verify   # archive body sha1 vs stub sha1
"""
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-m385-m364-rows.md")
HEAD = "## M364"
ARCHIVE_HEAD = ("# NAMED.md `## M364` - ROTATED VERBATIM (byte-exact) by "
                "scripts/m385_named_rotate.py\n\n")


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
        print("archive %s... stub %s... %s" % (got[:16], want[:16],
              "PASS" if want.startswith(got) or got.startswith(want) else "FAIL"))
        return 0 if (want.startswith(got) or got.startswith(want)) else 1
    body, pre, post = split_block(text)
    if "VERBATIM at `docs/named-archive-m385-m364-rows.md`" in body:
        print("already rotated")
        return 0
    sha = hashlib.sha1(body.encode()).hexdigest()
    open(ARCHIVE, "w").write(ARCHIVE_HEAD + body)
    first = body.splitlines()[0].rstrip("\n")
    stub = (first + " - FULL rows VERBATIM at `docs/named-archive-m385-m364-rows.md` "
            "(sha1 `%s`, %d B); this stub governs.\n" % (sha, len(body)))
    open(NAMED, "w").write(pre + stub + post)
    print("rotated %d B, sha1 %s" % (len(body), sha))
    return 0


if __name__ == "__main__":
    sys.exit(main())
