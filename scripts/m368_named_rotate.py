#!/usr/bin/env python3
"""m368_named_rotate.py — rotate three settled NAMED.md blocks VERBATIM into
`docs/named-archive-m368-rows.md` and leave a mechanical stub carrying the block's sha1.

Why: NAMED.md stood at 248,819 B (1,181 B under the 250,000 FAIL cap — under the 5 kB
ROTATE trigger) before `## M368` was added.  `## M352`, `## M353` and `## M355` are settled
(a merged PR each) and are referenced by NEXT_PROMPT.md only through their own one-line rows.

The archive keeps every byte; each stub is MECHANICAL (header + provenance line + sha1),
never a summary.  The rotation is idempotent: a stub is never rotated again, and --verify
re-hashes the archived bytes and cross-checks the stub's quoted sha1/byte count.

    python3 scripts/m368_named_rotate.py            # rotate; a 2nd run is a no-op
    python3 scripts/m368_named_rotate.py --verify   # sha1 + byte-count check only
"""
import argparse
import hashlib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs/named-archive-m368-rows.md")
TARGETS = ["## M352 ", "## M353 ", "## M355 "]
HEAD = ("# NAMED.md `## M352`, `## M353`, `## M355` — ROTATED VERBATIM\n"
        "(byte-exact, by `scripts/m368_named_rotate.py`)\n")


def block_of(text, head):
    i = text.index(head)
    j = text.index("\n## ", i + 3)
    return text[i:j], i, j


def stub(head, sha, n):
    return ("%s— VERBATIM at `docs/named-archive-m368-rows.md` (sha1 `%s`, %d B)\n"
            % (head, sha, n))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    named = open(NAMED, encoding="utf-8").read()
    arch = open(ARCHIVE, encoding="utf-8").read() if os.path.exists(ARCHIVE) else HEAD
    for head in TARGETS:
        if head not in named:
            print("%-10s STUBBED (absent)" % head.strip())
            continue
        blk, i, j = block_of(named, head)
        if "docs/named-archive-m368-rows.md" in blk.splitlines()[0]:
            print("%-10s STUBBED (already rotated)" % head.strip())
            continue  # idempotent: a rotation stub is never rotated again
        sha = hashlib.sha1(blk.encode()).hexdigest()[:16]
        if not a.verify:
            arch = arch.rstrip("\n") + "\n\n<!-- %s sha1 %s len %d -->\n%s" % (
                head.strip(), sha, len(blk), blk) + "\n"
            named = named[:i] + stub(head, sha, len(blk)) + named[j + 1:]
        print("%-10s %s sha1 %s" % (head.strip(), "ROTATED" if not a.verify else "PRESENT", sha))
    if not a.verify:
        open(ARCHIVE, "w", encoding="utf-8").write(arch if arch.endswith("\n") else arch + "\n")
        open(NAMED, "w", encoding="utf-8").write(named)
    bad = 0
    for head in TARGETS:
        m = [l for l in arch.splitlines() if l.startswith("<!-- %s sha1 " % head.strip())]
        if not m:
            print("%-10s NOT IN ARCHIVE" % head.strip())
            bad += 1
            continue
        sha = m[0].split("sha1 ")[1].split(" ")[0]
        n = int(m[0].split("len ")[1].split(" ")[0])
        k = arch.index(m[0]) + len(m[0]) + 1
        blk = arch[k:k + n]
        ok = hashlib.sha1(blk.encode()).hexdigest()[:16] == sha
        line = [l for l in named.splitlines() if l.startswith(head)]
        stub_ok = bool(line) and ("sha1 `%s`" % sha) in line[0] and ("%d B" % n) in line[0]
        ok = ok and stub_ok
        bad += 0 if ok else 1
        print("%-10s sha1 %s %s" % (head.strip(), sha, "OK" if ok else "SHA/STUB MISMATCH"))
    print("NAMED.md %d B, archive %d B, mismatches %d"
          % (os.path.getsize(NAMED), os.path.getsize(ARCHIVE), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
