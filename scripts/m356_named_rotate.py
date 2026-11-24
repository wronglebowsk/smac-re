#!/usr/bin/env python3
"""m356_named_rotate.py - rotate NAMED.md's settled `## M298` block VERBATIM into
`docs/named-archive-m356-rows.md`, leaving a mechanical stub behind.

Why: NAMED.md stood at 245,616 B (4,384 B under the 250,000 cap - inside the
5 KB ROTATE trigger) before `## M356` was added.  `## M298` (s251, STATIC,
2,396 B) is settled (merged, no reference from NEXT_PROMPT.md /
SESSION_NOTES.md / skill / pick-archive).

The archived block keeps every byte (sha1 recorded in both files).  The stub is
MECHANICAL, not authored: one line per top-level bullet of the archived block,
its text = that bullet's first line cut at 110 chars.

    python3 scripts/m356_named_rotate.py            # rotate; a 2nd run is a no-op + verify
    python3 scripts/m356_named_rotate.py --verify   # sha1 + row-count check
"""
import argparse
import hashlib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs/named-archive-m356-rows.md")
HEAD = "## M298 "
ARCHIVE_HEAD = ("# NAMED.md `## M298` - ROTATED VERBATIM (byte-exact) by "
                "scripts/m356_named_rotate.py\n")
SENT = "<!-- block: every byte below is the original NAMED.md block -->\n"


def block_of(text):
    i = text.index(HEAD)
    j = text.index("\n## ", i + 3)
    return text[i:j], i, j


def bullets(block):
    """Top-level rows of a block: markdown table rows (M298 is a table block)
    or `- ` bullets, whichever the block uses."""
    rows = [l for l in block.splitlines()
            if l.startswith("| ") and not set(l) <= set("|-: ")]
    if rows:
        return [r for r in rows if not r.startswith("| claim ")]
    return [line for line in block.splitlines() if line.startswith("- ")]


def stub(block, sha, n):
    out = ["## M298 (STUB - block VERBATIM: `docs/named-archive-m356-rows.md`, "
           "sha1 `%s`)" % sha[:16],
           "| claim | ev | conf |", "|---|---|---|"]
    for line in bullets(block):
        label = line[2:].strip()
        for sep in (";", " - ", ": "):
            if sep in label[:130]:
                label = label.split(sep)[0]
        out.append("| %s | archive:%d | archived |" % (label[:110].replace("|", "/"), n))
        n += 1
    return "\n".join(out) + "\n"


def sha(b):
    return hashlib.sha1(b.encode()).hexdigest()


def rotate():
    text = open(NAMED).read()
    if "## M298 (STUB" in text:
        # idempotency: repair a stub whose row count does not match the archive
        arch = open(ARCHIVE).read()
        body = arch.split(SENT, 1)[1].split("\n", 2)[2]
        n = len(bullets(body))
        h = sha(body)
        fixed_arch = ARCHIVE_HEAD + SENT + "sha1 %s  rows %d\n\n" % (h, n) + body
        if fixed_arch != arch:
            open(ARCHIVE, "w").write(fixed_arch)
            print("archive header repaired (rows %d)" % n)
        cur = section(text)
        new_stub = stub(body, h, 1)
        if cur.count("| archive:") != n:
            open(NAMED, "w").write(text.replace(cur, new_stub))
            print("stub repaired from the archive (%d rows)" % n)
        print("## M298 already rotated - verify:")
        return verify()
    blk, i, j = block_of(text)
    body = blk.rstrip("\n") + "\n"
    h = sha(body)
    n = len(bullets(body))
    arch = ARCHIVE_HEAD + SENT + "sha1 %s  rows %d\n\n" % (h, n) + body
    open(ARCHIVE, "w").write(arch)
    new = text[:i] + stub(body, h, 1) + text[j + 1:]
    open(NAMED, "w").write(new)
    print("rotated ## M298 (%d B, %d rows) -> %s  sha1 %s"
          % (len(body), n, os.path.relpath(ARCHIVE, ROOT), h))
    print("NAMED.md now %d B" % len(new))


def section(text, head="## M298 (STUB"):
    i = text.index(head)
    j = text.find("\n## ", i + 3)
    return text[i:] if j < 0 else text[i:j]


def verify():
    arch = open(ARCHIVE).read()
    rec = [l for l in arch.splitlines() if l.startswith("sha1 ")][0]
    h, n = rec.split()[1], int(rec.split()[3])
    body = arch.split(SENT, 1)[1].split("\n", 2)[2]
    ok = sha(body) == h and len(bullets(body)) == n
    named = open(NAMED).read()
    stub_rows = section(named).count("| archive:")
    ok2 = (stub_rows == n and "## M298 (STUB" in named
           and "## M298 (s251" not in named)
    print("archive sha1 %s %s (%d rows declared, %d measured)"
          % (h, "OK" if sha(body) == h else "MISMATCH", n, len(bullets(body))))
    print("stub rows %d %s" % (stub_rows, "OK" if ok2 else "MISMATCH"))
    return 0 if ok and ok2 else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    raise SystemExit(verify() if a.verify else (rotate() or 0))
