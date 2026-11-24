#!/usr/bin/env python3
"""m364_named_rotate.py - rotate settled NAMED.md blocks VERBATIM to make room for `## M364`.

NAMED.md stood at 247,217 B, i.e. 2,783 B under the 250,000 cap - inside the 5 kB ROTATE
trigger.  Selection is COMPUTED, never authored: a block is eligible when its id string does
not appear in NEXT_PROMPT.md, SESSION_NOTES.md, skill/SKILL.md, or anywhere else in NAMED.md,
and it is at least MIN bytes long.  The four oldest eligible blocks move byte-exactly to
`docs/named-archive-m364-rows.md`; each leaves a MECHANICAL stub (header + sha1 + byte count),
never a summary.

    python3 scripts/m364_named_rotate.py            # rotate; a 2nd run is a no-op
    python3 scripts/m364_named_rotate.py --verify   # sha1 + byte-count check only
"""
import argparse
import hashlib
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs/named-archive-m364-rows.md")
REFS = [os.path.join(ROOT, p) for p in ("NEXT_PROMPT.md", "SESSION_NOTES.md",
                                        "skill/SKILL.md")]
MIN = 400
WANT = 4
HEAD = ("# NAMED.md blocks ROTATED VERBATIM by `scripts/m364_named_rotate.py`\n"
        "(byte-exact; each stub in NAMED.md carries the block's sha1 and byte count)\n\n")
IDRE = re.compile(r"^## (M\d{3})")


def blocks(text):
    """[(id, header_line, start, end)] for every `## M###` block."""
    out = []
    idx = [m.start() for m in re.finditer(r"^## ", text, re.M)]
    for k, i in enumerate(idx):
        j = idx[k + 1] if k + 1 < len(idx) else len(text)
        m = IDRE.match(text[i:])
        if m:
            out.append((m.group(1), text[i:text.index("\n", i)], i, j))
    return out


def stub(header, sha, n):
    return ("%s\n  — VERBATIM at `docs/named-archive-m364-rows.md` (sha1 `%s`, %d B);"
            " this stub governs.\n" % (header, sha, n))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    text = open(NAMED).read()
    bl = blocks(text)

    if a.verify:
        if not os.path.exists(ARCHIVE):
            print("VERIFY FAIL  archive missing")
            return 1
        arch = open(ARCHIVE).read()
        bad = 0
        for m in re.finditer(r"^## (M\d+) .*?sha1 `([0-9a-f]{12})`, (\d+) B", text, re.M):
            mid, sha, n = m.group(1), m.group(2), int(m.group(3))
            i = arch.find("## %s " % mid)
            if i < 0:
                print(f"VERIFY FAIL  {mid}: not in the archive")
                bad += 1
                continue
            j = arch.find("\n## ", i + 3)
            body = arch[i:j if j > 0 else len(arch)]
            h = hashlib.sha1(body.encode()).hexdigest()[:12]
            ok = h == sha and len(body) == n
            print(f"VERIFY {'ok  ' if ok else 'FAIL'}  {mid} sha1 {h} ({len(body)} B)")
            bad += not ok
        print(f"\n{'PASS' if not bad else 'FAIL'} m364_named_rotate --verify ({bad} bad)")
        return 0 if not bad else 1

    # already rotated?
    if os.path.exists(ARCHIVE) and "m364-rows" in open(ARCHIVE).read():
        print("archive exists - no-op (rotate is idempotent)")
        return 0

    refs = ""
    for p in REFS:
        if os.path.exists(p):
            refs += open(p, errors="replace").read()
    rest = text
    picked = []
    for mid, head, i, j in bl:
        body = text[i:j]
        if len(body) < MIN or mid in picked:
            continue
        if re.search(r"\b%s\b" % mid, refs):
            continue
        others = rest[:i] + rest[j:]
        if re.search(r"\b%s\b" % mid, others):
            continue          # referenced by another NAMED row
        picked.append((mid, head, body))
        if len(picked) == WANT:
            break
    if len(picked) < WANT:
        print(f"only {len(picked)} eligible blocks - nothing rotated")
        return 1
    arch = [HEAD]
    for mid, head, body in picked:
        sha = hashlib.sha1(body.encode()).hexdigest()[:12]
        arch.append(body if body.endswith("\n") else body + "\n")
        arch.append("")          # a blank line keeps the next `## ` on its own line
        text = text.replace(body, stub(head, sha, len(body)) + "\n", 1)
        print(f"rotated {mid}: {len(body)} B sha1 {sha}")
    open(ARCHIVE, "w").write("\n".join(arch))
    open(NAMED, "w").write(text)
    print(f"NAMED.md now {len(text)} B (-{sum(len(b) for _, _, b in picked)} B "
          f"+ {sum(len(stub(h, '0'*12, len(b))) for _, h, b in picked)} B of stubs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
