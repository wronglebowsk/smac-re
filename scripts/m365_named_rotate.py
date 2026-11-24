#!/usr/bin/env python3
"""m365_named_rotate.py — rotate two settled NAMED.md blocks VERBATIM into
`docs/named-archive-m365-rows.md` and leave a mechanical stub with the block's sha1.

Why: NAMED.md stood at 247,217 B (2,783 B under the 250,000 cap — inside the 5 kB ROTATE
trigger) before `## M365` was added.  `## M299` and `## M300` are settled and referenced by
nothing in NEXT_PROMPT.md, SESSION_NOTES.md, skill/ or docs/pick-archive.md.

The archive keeps every byte.  Each stub is MECHANICAL: header + one line of provenance and
sha1, never a summary.

    python3 scripts/m365_named_rotate.py            # rotate; a 2nd run is a no-op
    python3 scripts/m365_named_rotate.py --verify   # sha1 + byte-count check only
"""
import argparse
import hashlib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs/named-archive-m365-rows.md")
TARGETS = ["## M299 ", "## M300 "]
HEAD = ("# NAMED.md `## M299`, `## M300` — ROTATED VERBATIM\n"
        "(byte-exact, by `scripts/m365_named_rotate.py`)\n")


def block_of(text, head):
    i = text.index(head)
    j = text.index("\n## ", i + 3)
    return text[i:j], i, j


def stub(head, sha, n):
    return ("%s— VERBATIM at `docs/named-archive-m365-rows.md` (sha1 `%s`, %d B)\n"
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
        if "docs/named-archive-m365-rows.md" in blk.splitlines()[0]:
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
            continue
        sha = m[0].split("sha1 ")[1].split(" ")[0]
        n = int(m[0].split("len ")[1].split(" ")[0])
        k = arch.index(m[0]) + len(m[0]) + 1
        blk = arch[k:k + n]
        ok = hashlib.sha1(blk.encode()).hexdigest()[:16] == sha
        # the NAMED stub must quote the same sha1 and byte count, else the provenance is
        # one-sided (the archive could be right while the pointer at the stub is wrong)
        line = [l for l in named.splitlines() if l.startswith(head)]
        stub_ok = bool(line) and ("sha1 `%s`" % sha) in line[0] and ("%d B" % n) in line[0]
        ok = ok and stub_ok
        bad += 0 if ok else 1
        print("%-10s sha1 %s %s" % (head.strip(), sha,
                                    "OK" if ok else "SHA/STUB MISMATCH"))
    print("NAMED.md %d B, archive %d B, mismatches %d"
          % (os.path.getsize(NAMED), os.path.getsize(ARCHIVE), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
