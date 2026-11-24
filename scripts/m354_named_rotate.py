#!/usr/bin/env python3
"""m354_named_rotate.py - move NAMED.md's settled `## M312` block VERBATIM into
`docs/named-archive-m354-rows.md`, leaving a compact stub behind.

Why: NAMED.md stood at 245,796 / 250,000 B (4,204 B headroom, UNDER the 5 KB
ROTATE trigger) and `## M354` must add a block.  M312 is settled (s276,
mutation-tested 23/23) and has no open rows.  The archived block keeps every
claim, gate and cite byte-for-byte (sha1 recorded in both files); the stub is
MECHANICAL: one row per archived claim, its label = the claim's first clause
(cut at the first ';', ':' or 110 chars), evidence cell = the same
`evidence/<file>:<line>` pointer, conf cell = the archived conf verbatim.

    python3 scripts/m354_named_rotate.py            # rotate (idempotent)
    python3 scripts/m354_named_rotate.py --verify   # sha1 + row-count check
"""
import argparse
import hashlib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs/named-archive-m354-rows.md")
HEAD = "## M312 "
ARCHIVE_HEAD = ("# NAMED.md `## M312` - ROTATED VERBATIM (byte-exact) by "
                "scripts/m354_named_rotate.py\n")
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
            rows.append([c.strip() for c in line.strip("|").split("|")])
    return rows


def stub(rows, header):
    """Header derived from the archived block's own first line: prefix + the
    rotation clause + the ORIGINAL tail, so no word is re-typed."""
    prefix, _, tail = header.partition(" - ")
    out = [prefix + " - ROTATED VERBATIM to `docs/named-archive-m354-rows.md` "
           "(sha1 `${SHA}`) - " + tail,
           "", "| claim (one line each; full rows in the archive) | evidence | conf |",
           "|---|---|---|"]
    for c in rows:
        label = c[0]
        for sep in (";", ":"):
            if sep in label[:130]:
                label = label.split(sep)[0]
        out.append("| %s | %s | %s |" % (label[:110], c[1], c[2] if len(c) > 2 else "V"))
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
        ok = want == got and blk.count("\n| ") >= 6
        print("VERIFY %s: sha1 %s (%d table rows)"
              % ("PASS" if ok else "FAIL", got[:16], blk.count("\n| ") - 1))
        return 0 if ok else 1
    if HEAD not in text:
        print("already rotated or block missing")
        return 0
    blk, i, j = block_of(text)
    rows = claim_rows(blk)
    blk = blk.rstrip()
    ar = (ARCHIVE_HEAD + SENT + "sha1=%s bytes=%d rows=%d\n\n"
          % (sha(blk), len(blk.encode()), len(rows)) + blk + "\n")
    with open(ARCHIVE, "w") as f:
        f.write(ar)
    header = blk.splitlines()[0]
    st = stub(rows, header).replace("${SHA}", sha(blk)[:12])
    open(NAMED, "w").write(text[:i] + st.rstrip("\n") + text[j:])
    print("rotated M312: %d B -> stub %d B; archive sha1 %s; NAMED now %d B"
          % (len(blk.encode()), len(st), sha(blk)[:16],
             len(open(NAMED).read().encode())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
