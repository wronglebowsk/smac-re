#!/usr/bin/env python3
"""m379_named_rotate.py - move NAMED.md's settled `## M311` and `## M305`
blocks VERBATIM into `docs/named-archive-m379-m311-m305-rows.md` and leave
one-line pointer stubs.

M379 adds a block and NAMED.md carried only 2,176 B of headroom (247,824 B
against the 250,000 B FAIL; <5 KB rotation trigger).  M311 (0x68cbb0 record
index) and M305 (FUN_0051dcb0 rebuild) are settled and referenced by neither
NEXT_PROMPT.md nor SESSION_CURSOR.md.  Rotated text is byte-for-byte what
NAMED carried.

    python3 scripts/m379_named_rotate.py            # rotate (guarded against re-rotation)
    python3 scripts/m379_named_rotate.py --verify   # archive sha1 vs stubs
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-m379-m311-m305-rows.md")
HEADS = ["## M311", "## M305"]
ARCHIVE_HEAD = ("# NAMED.md `## M311` + `## M305` - ROTATED VERBATIM (byte-exact) by "
                "scripts/m379_named_rotate.py\n\n")


def spans(text):
    lines = text.splitlines(keepends=True)
    out = {}
    for head in HEADS:
        s = next(i for i, ln in enumerate(lines) if ln.startswith(head))
        e = next((i for i in range(s + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
        out[head] = (s, e, "".join(lines[s:e]))
    return out


def main():
    verify = "--verify" in sys.argv
    if verify:
        ok = True
        body = open(ARCHIVE).read().split("\n\n", 1)[1]
        named = open(NAMED).read()
        for head in HEADS:
            s = body.index(head + " ")
            e = body.find("\n## ", s + 1)
            blk = body[s:e + 1 if e >= 0 else len(body)]
            got = hashlib.sha1(blk.encode()).hexdigest()[:16]
            stub = next(ln for ln in named.splitlines()
                        if ln.startswith(head) and "VERBATIM" in ln)
            want = re.search(r"sha1 `([0-9a-f]+)`", stub).group(1)
            print(f"{head} archive sha1 {got} stub {want} bytes {len(blk)}")
            ok &= got == want
        print("VERIFY", "PASS" if ok else "FAIL")
        return 0 if ok else 1

    text = open(NAMED).read()
    for head in HEADS:
        ln = next(l for l in text.splitlines() if l.startswith(head + " "))
        if "VERBATIM" in ln:
            raise SystemExit(f"{head} is already a rotation stub - refusing to re-rotate "
                             "(the archive is the source of truth; use --verify)")
    sp = spans(text)
    lines = text.splitlines(keepends=True)
    stubs = {}
    chunks = []
    for head in HEADS:
        s, e, body = sp[head]
        sha = hashlib.sha1(body.encode()).hexdigest()
        first = body.splitlines()[0]
        noun = first.split(" - ", 1)[1] if " - " in first else ""
        if len(noun) > 90:
            noun = noun[:90].rsplit(" ", 1)[0] + "..."
        stubs[head] = (f"{head} - VERBATIM at `docs/named-archive-m379-m311-m305-rows.md` "
                       f"(sha1 `{sha[:16]}`, {len(body)} B); noun: {noun}\n")
        chunks.append(body)
    open(ARCHIVE, "w").write(ARCHIVE_HEAD + "".join(chunks))

    out = []
    i = 0
    while i < len(lines):
        head = next((h for h in HEADS if i == sp[h][0]), None)
        if head:
            out.append(stubs[head])
            i = sp[head][1]
        else:
            out.append(lines[i])
            i += 1
    open(NAMED, "w").write("".join(out))
    for head in HEADS:
        print(f"rotated {head} ({len(sp[head][2])} B) -> {os.path.relpath(ARCHIVE, ROOT)}")
    print("NAMED.md now", len("".join(out)), "B")
    return 0


if __name__ == "__main__":
    sys.exit(main())
