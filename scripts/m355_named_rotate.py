#!/usr/bin/env python3
"""m355_named_rotate.py — rotate NAMED.md's settled `## M293` block VERBATIM into
`docs/named-archive-m355-rows.md`, leaving a mechanical stub behind.

Why: NAMED.md stood at 245,230 B (4,770 B under the 250,000 cap — inside the 5 KB
ROTATE trigger) before `## M355` was added.  `## M293` is settled (MERGED #250, no
reference from NEXT_PROMPT.md / SESSION_NOTES.md / skill) and 10,450 B.

The archived block keeps every byte (sha1 recorded in both files).  The stub is
MECHANICAL, not authored: one line per top-level bullet of the archived block,
its text = that bullet's first line cut at 110 chars.

    python3 scripts/m355_named_rotate.py            # rotate; a 2nd run is a no-op + verify
    python3 scripts/m355_named_rotate.py --verify   # sha1 + row-count check
"""
import argparse
import hashlib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs/named-archive-m355-rows.md")
HEAD = "## M293 "
ARCHIVE_HEAD = ("# NAMED.md `## M293` - ROTATED VERBATIM (byte-exact) by "
                "scripts/m355_named_rotate.py\n")
SENT = "<!-- block: every byte below is the original NAMED.md block -->\n"


def block_of(text):
    i = text.index(HEAD)
    j = text.index("\n## ", i + 3)
    return text[i:j], i, j


def bullets(block):
    out = []
    for line in block.splitlines():
        if line.startswith("- "):
            out.append(line)
    return out


def stub(block, sha, n):
    out = ["## M293 (STUB - block VERBATIM: `docs/named-archive-m355-rows.md`, "
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
    if "## M293 (STUB" in text:
        # idempotency guard: a second run must NOT re-archive the stub
        print("## M293 already rotated (stub present) - nothing rewritten")
        return verify()
    blk, i, j = block_of(text)
    body = blk.rstrip("\n") + "\n"
    h = sha(body)
    n = len(bullets(body))
    arch = ARCHIVE_HEAD + SENT + "sha1 %s  rows %d\n\n" % (h, n) + body
    open(ARCHIVE, "w").write(arch)
    new = text[:i] + stub(body, h, 1) + text[j + 1:]
    open(NAMED, "w").write(new)
    print("rotated ## M293 (%d B, %d bullets) -> %s  sha1 %s"
          % (len(body), n, os.path.relpath(ARCHIVE, ROOT), h))
    print("NAMED.md now %d B" % len(new))


def verify():
    arch = open(ARCHIVE).read()
    rec = [l for l in arch.splitlines() if l.startswith("sha1 ")][0]
    h, n = rec.split()[1], int(rec.split()[3])
    body = arch.split(SENT, 1)[1].split("\n", 2)[2]
    ok = sha(body) == h and len(bullets(body)) == n
    named = open(NAMED).read()
    stub_rows = named.count("| archive:")
    ok2 = (stub_rows == n and "## M293 (STUB" in named
           and "## M293 (s240" not in named)
    print("archive sha1 %s %s (%d bullets declared, %d measured)"
          % (h, "OK" if sha(body) == h else "MISMATCH", n, len(bullets(body))))
    print("stub rows %d %s" % (stub_rows, "OK" if ok2 else "MISMATCH"))
    return 0 if ok and ok2 else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    raise SystemExit(verify() if a.verify else (rotate() or 0))
