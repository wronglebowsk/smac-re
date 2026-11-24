#!/usr/bin/env python3
"""m357_named_rotate.py — rotate NAMED.md's settled `## M272` and `## M273` blocks
VERBATIM into `docs/named-archive-m357-rows.md`, leaving mechanical stubs behind.

Why: NAMED.md stood at 245,616 B (4,384 B under the 250,000 cap - inside the 5 KB
ROTATE trigger) before `## M357` was added.  Both blocks are settled (M272 s211,
M273 s213; neither is referenced from NEXT_PROMPT.md, SESSION_NOTES.md or skill/).

The archived blocks keep every byte (sha1 recorded in both files).  Each stub is
MECHANICAL, not authored: one row per top-level bullet, text = that bullet's first
line cut at 110 chars.

    python3 scripts/m357_named_rotate.py            # rotate; a 2nd run is a no-op + verify
    python3 scripts/m357_named_rotate.py --verify   # sha1 + row-count check
"""
import argparse
import hashlib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs/named-archive-m357-rows.md")
TARGETS = ["## M272 ", "## M273 "]
ARCHIVE_HEAD = ("# NAMED.md `## M272` + `## M273` - ROTATED VERBATIM (byte-exact) by "
                "scripts/m357_named_rotate.py\n")
SENT = "<!-- block: every byte below is the original NAMED.md block -->\n"


def block_of(text, head):
    i = text.index(head)
    j = text.index("\n## ", i + 3)
    return text[i:j], i, j


def bullets(block):
    out = []
    for l in block.splitlines():
        if l.startswith("- "):
            out.append(l)
        elif l.startswith("| ") and set(l) - set("|- :"):
            out.append(l)
    return out


def stub(head, block, sha, n, tag):
    out = ["%s(STUB - block VERBATIM: `docs/named-archive-m357-rows.md`, sha1 `%s`)"
           % (head, sha[:16]), "| claim | ev | conf |", "|---|---|---|"]
    for line in bullets(block):
        label = line[2:].strip() if line.startswith("- ") else line.strip(" |")
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
    if "## M272 (STUB" in text and "## M273 (STUB" in text:
        print("both blocks already rotated (stubs present) - nothing rewritten")
        return verify()
    parts, records = [], []
    for head in sorted(TARGETS, key=lambda h: -text.index(h)):
        blk, i, j = block_of(text, head)
        body = blk.rstrip("\n") + "\n"
        h = sha(body)
        n = len(bullets(body))
        records.append((head.strip(), body, h, n))
        text = text[:i] + stub(head, body, h, n, 1) + text[j + 1:]
    records.reverse()
    arch = ARCHIVE_HEAD
    for name, body, h, n in records:
        arch += "%s\nsha1 %s  rows %d\n\n" % (SENT, h, n) + body
    open(ARCHIVE, "w").write(arch)
    open(NAMED, "w").write(text)
    for name, body, h, n in records:
        print("rotated %-8s (%d B, %d bullets) sha1 %s" % (name, len(body), n, h))
    print("NAMED.md now %d B" % len(text))
    return verify()


def verify():
    arch = open(ARCHIVE).read()
    ok = True
    for chunk in arch.split(SENT)[1:]:
        head = [l for l in chunk.splitlines() if l.startswith("## ")][0]
        rec = [l for l in chunk.splitlines() if l.startswith("sha1 ")][0]
        h, n = rec.split()[1], int(rec.split()[3])
        body = chunk.split("\n\n", 1)[1]
        m = sha(body) == h and len(bullets(body)) == n
        print("%s sha1 %s %s (%d declared, %d measured)"
              % (head or "?", h[:16], "OK" if m else "MISMATCH", n, len(bullets(body))))
        ok &= m
    named = open(NAMED).read()
    for head in TARGETS:
        tag = head.replace("## ", "## ") + "(STUB"
        present = tag in named
        print("stub %-8s %s" % (head.strip(), "OK" if present else "MISSING"))
        ok &= present
    got = 0
    for head in TARGETS:
        i = named.index(head + "(STUB")
        j = named.index("\n## ", i + 3)
        got += named[i:j].count("| archive:")
    want = sum(int(c.split("rows ")[1].split()[0]) for c in arch.split(SENT)[1:])
    print("stub rows %d (declared %d) %s" % (got, want, "OK" if got == want else "MISMATCH"))
    ok &= got == want
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    raise SystemExit(verify() if a.verify else (rotate() or 0))
