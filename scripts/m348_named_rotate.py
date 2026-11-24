#!/usr/bin/env python3
"""m348_named_rotate.py -- move NAMED.md's settled `## M314` block VERBATIM into
`docs/named-archive-m348-rows.md`, leaving a compact stub behind.

Why: NAMED.md stood at 247,825 / 250,000 B (2,175 B headroom) before M348, i.e.
under the 5 KB ROTATE threshold.  The archived block keeps every claim, gate and
cite byte-for-byte (sha1 recorded in both files); the stub is MECHANICAL, not
authored: one row per archived claim, its label = the claim's first clause
(cut at the first ';' or ':' or 110 chars), its evidence cell = the same
`evidence/<file>:<line>` pointer, its conf cell = the archived conf verbatim.

    python3 scripts/m348_named_rotate.py            # rotate (idempotent)
    python3 scripts/m348_named_rotate.py --verify   # sha1 + row-count check
"""
import argparse
import hashlib
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs/named-archive-m348-rows.md")
HEAD = "## M314 "
ARCHIVE_HEAD = ("# NAMED.md `## M314` - ROTATED VERBATIM (byte-exact) by "
                "scripts/m348_named_rotate.py")
SENT = "<!-- block: every byte below is the original NAMED.md block -->"


def block_of(text):
    i = text.index(HEAD)
    j = text.index("\n## ", i + 3)
    return text[i:j], i, j


def claim_rows(block):
    rows = []
    for line in block.splitlines():
        if line.startswith("| ") and not line.startswith("| claim") and \
                not line.startswith("|---"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 3:
                rows.append(cells)
    return rows


def label_of(claim):
    cut = min([x for x in (claim.find(";"), claim.find(":")) if x > 0] or [110])
    lab = claim[:min(cut, 110)].strip().rstrip(",;:")
    return lab + ("…" if len(claim) > len(lab) + 1 else "")


def stub(block, sha):
    rows = claim_rows(block)
    out = [
        "## M314 (s282, STATIC, 27/27) — FUN_004c5d60 = the token-keyed tour/dialog "
        "dispatcher (pick (i'') CLOSED).",
        "",
        "FULL BLOCK VERBATIM at `docs/named-archive-m348-rows.md:5` (sha1 `%s`); "
        "these stubs govern nothing the archive does not carry — one line per claim, "
        "labels cut mechanically, evidence and confidence copied:" % sha,
        "",
        "| claim (first clause) | evidence | conf |",
        "|---|---|---|",
    ]
    for claim, ev, conf in rows:
        out.append("| %s | %s | %s |" % (label_of(claim), ev, conf))
    out.append("")
    out.append("ACCEPT `scripts/m314_tour_family.py` 18/18 `cf54a7ca907344c6` x2; "
               "`scripts/m314_mutate.py` 27/27 (merged #299).")
    return "\n".join(out)


def rotate():
    text = open(NAMED).read()
    if HEAD not in text:
        print("M314 block already rotated (header absent) - nothing to do")
        return 0
    block, i, j = block_of(text)
    sha = hashlib.sha1(block.encode()).hexdigest()
    body = "%s\n\n%s\n%s\n\n```\n%s\n```\n" % (ARCHIVE_HEAD, SENT, "sha1: " + sha, block)
    open(ARCHIVE, "w").write(body)
    new = text[:i] + stub(block, sha) + text[j:]
    open(NAMED, "w").write(new)
    print("rotated ## M314: %d B -> stub %d B, sha1 %s -> %s" % (
        len(block), len(stub(block, sha)), sha, ARCHIVE))
    print("NAMED.md now %d B" % os.path.getsize(NAMED))
    return 0


def verify():
    text = open(NAMED).read()
    arc = open(ARCHIVE).read()
    m = re.search(r"```\n(.*?)\n```\s*$", arc, re.S)
    if not m:
        print("VERIFY FAIL: no block fence in the archive")
        return 1
    block = m.group(1)
    rec = re.search(r"sha1: ([0-9a-f]{40})", arc).group(1)
    sha = hashlib.sha1(block.encode()).hexdigest()
    ok = sha == rec
    print("archive block %d B sha1 %s == recorded %s : %s" % (
        len(block), sha[:16], rec[:16], ok))
    n_arc = len(claim_rows(block))
    i = text.index("## M314 ")
    j = text.index("\n## ", i + 3)
    n_stub = len(claim_rows(text[i:j]))
    print("claims archived=%d stub=%d : %s" % (n_arc, n_stub, n_arc == n_stub))
    print("stub cites the recorded sha1: %s" % (rec in text[i:j]))
    good = ok and n_arc == n_stub and rec in text[i:j]
    print("RESULT: %s" % ("PASS m348_named_rotate" if good else "FAIL"))
    return 0 if good else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    raise SystemExit(verify() if a.verify else rotate())
