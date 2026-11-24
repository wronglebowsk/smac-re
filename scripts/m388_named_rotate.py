#!/usr/bin/env python3
"""m388_named_rotate.py - move NAMED.md's settled `## M330` block VERBATIM into
`docs/named-archive-m388-rows.md` and leave a mechanical stub with its sha1 + size.

NAMED.md stands at 247,287 B against the 250,000 B cap (2,713 B of headroom, inside the
5 KB ROTATE trigger) before `## M388` is added.  `## M330` is a merged, settled chain-2
census (13/13 + 31/31, both OPEN items answered by M331/M332) that nothing governs from;
its evidence stays in the repo and the archive keeps every byte.

    python3 scripts/m388_named_rotate.py            # rotate (idempotent)
    python3 scripts/m388_named_rotate.py --verify   # sha1 + byte-count check
"""
import argparse
import hashlib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs/named-archive-m388-rows.md")
HEAD = "## M330 (s307-chain2"
STUB = "## M330 \u2014 VERBATIM at `docs/named-archive-m388-rows.md` (sha1 `%s`, %d B); this stub governs.\n"
TITLE = ("# NAMED.md `## M330` \u2014 ROTATED VERBATIM (byte-exact) by scripts/m388_named_rotate.py\n\n")


def block_of(text):
    i = text.index(HEAD)
    try:
        j = text.index("\n## ", i + 3)
    except ValueError:
        j = len(text)
    return text[i:j], i, j


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    text = open(NAMED, encoding="utf-8").read()
    if a.verify:
        stub = [ln for ln in text.splitlines() if ln.startswith("## M330 \u2014 VERBATIM at `docs/named-archive-m388-rows.md`")]
        if not stub:
            print("VERIFY FAIL: no stub")
            return 1
        import re as _re
        m = _re.search(r"sha1 `([0-9a-f]+)`, ([0-9]+) B", stub[0])
        sha, size = m.group(1), int(m.group(2))
        arc = open(ARCHIVE, encoding="utf-8").read()
        body = arc[len(TITLE):] if arc.startswith(TITLE) else arc
        got = hashlib.sha1(body.encode()).hexdigest()[:16]
        print("VERIFY archive sha1 %s size %d -> %s" % (got, len(body.encode()), "OK" if (got == sha and len(body.encode()) == size) else "MISMATCH"))
        return 0 if got == sha and len(body.encode()) == size else 1
    if HEAD not in text:
        print("already rotated (no live block)")
        return 0
    body, i, j = block_of(text)
    sha = hashlib.sha1(body.encode()).hexdigest()[:16]
    size = len(body.encode())
    with open(ARCHIVE, "w", encoding="utf-8") as f:
        f.write(TITLE + body)
    out = text[:i] + (STUB % (sha, size)) + text[j:].lstrip("\n")
    open(NAMED, "w", encoding="utf-8").write(out)
    print("rotated %d B sha1 %s; NAMED now %d B" % (size, sha, len(out.encode())))


if __name__ == "__main__":
    raise SystemExit(main())
