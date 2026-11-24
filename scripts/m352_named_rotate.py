#!/usr/bin/env python3
"""m352_named_rotate.py — move NAMED.md's settled `## M350` block VERBATIM into
`docs/named-archive-m352-rows.md`, leaving a compact stub behind.

Why: after adding `## M352` NAMED.md stood at 245,059 / 250,000 B (under the
5 KB ROTATE threshold; M352 had already corrected M350's OPEN row in place).
The archived block keeps every claim, gate and cite byte-for-byte (sha1
recorded in both files); the stub is MECHANICAL, not authored: one row per
archived claim, its label = the claim's first clause (cut at the first ';',
':' or 110 chars), its evidence cell = the same `evidence/<file>:<line>`
pointer, its conf cell = the archived conf verbatim.

    python3 scripts/m352_named_rotate.py            # rotate (idempotent)
    python3 scripts/m352_named_rotate.py --verify   # sha1 + row-count check
"""
import argparse
import hashlib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs/named-archive-m352-rows.md")
HEAD = "## M350 "
ARCHIVE_HEAD = ("# NAMED.md `## M350` - ROTATED VERBATIM (byte-exact) by "
                "scripts/m352_named_rotate.py\n")
SENT = "<!-- block: every byte below is the original NAMED.md block -->\n"


def block_of(text):
    i = text.index(HEAD)
    j = text.index("\n## ", i + 3)
    return text[i:j], i, j


def claim_rows(block):
    rows = []
    for line in block.splitlines():
        if line.startswith("| ") and not line.startswith("| claim") \
                and not line.startswith("|---"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            rows.append(cells)
    return rows


def stub(rows):
    out = ["# M350 (STUB — rows VERBATIM: `docs/named-archive-m352-rows.md`)",
           "| claim | ev | conf |", "|---|---|---|"]
    for c in rows:
        label = c[0]
        for sep in (";", ":"):
            if sep in label[:130]:
                label = label.split(sep)[0]
        out.append("| %s | %s | %s |" % (label[:110], c[1], c[2]))
    return "\n".join(out) + "\n"


def sha(b):
    return hashlib.sha1(b.encode()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    text = open(NAMED).read()
    if a.verify:
        if not os.path.exists(ARCHIVE):
            print("VERIFY FAIL: archive missing")
            return 1
        ar = open(ARCHIVE).read()
        body = ar.split(SENT)[1]
        i = body.index(HEAD)
        j = body.find("\n## ", i + 3)
        blk = (body[i:j] if j > 0 else body[i:]).rstrip()
        claimed = [ln for ln in ar.splitlines() if ln.startswith("sha1=")]
        if not claimed:
            print("VERIFY FAIL: no sha1 line")
            return 1
        want = claimed[0].split("=", 1)[1].split()[0]
        got = sha(blk)
        ok = want == got and blk.count("| ") >= 6
        print("VERIFY %s: sha1 %s (%d table rows)" %
              ("PASS" if ok else "FAIL", got[:16], blk.count("\n| ") - 1))
        return 0 if ok else 1
    if HEAD not in text:
        print("already rotated or block missing")
        return 0
    blk, i, j = block_of(text)
    rows = claim_rows(blk)
    blk = blk.rstrip()
    ar = (ARCHIVE_HEAD + SENT + "sha1=%s bytes=%d rows=%d\n\n" %
          (sha(blk), len(blk.encode()), len(rows)) + blk + "\n")
    with open(ARCHIVE, "w") as f:
        f.write(ar)
    open(NAMED, "w").write(text[:i] + stub(rows).rstrip("\n") + text[j:])
    print("rotated M350: %d B -> stub %d B; archive sha1 %s" %
          (len(blk.encode()), len(stub(rows)), sha(blk)[:16]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
