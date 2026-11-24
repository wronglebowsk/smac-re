#!/usr/bin/env python3
"""m364_named_rotate.py - rotate settled NAMED.md blocks VERBATIM to make room for `## M364`.

NAMED.md stood at 247,217 B, i.e. 2,783 B under the 250,000 cap - inside the 5 kB ROTATE
trigger.  Selection is COMPUTED, never authored: a block is eligible when
  * its id string appears nowhere in NEXT_PROMPT.md, SESSION_NOTES.md, skill/SKILL.md or in
    any other NAMED.md row,
  * it is at least MIN bytes long, and
  * it is not ITSELF a rotation stub (body carries no "named-archive" provenance) - rotating a
    stub would nest provenance instead of moving evidence.
The picks move byte-exactly to `docs/named-archive-m364-rows.md`; each leaves a MECHANICAL
stub (header + sha1 + byte count), never a summary.  Re-running is a rebuild: the archive is
undone into NAMED.md first, then re-selected, so the script is self-correcting.

    python3 scripts/m364_named_rotate.py            # (re)rotate
    python3 scripts/m364_named_rotate.py --verify   # sha1 + byte-count check of every stub
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
MIN = 250
WANT = 4
PROV = "  — VERBATIM at `docs/named-archive-m364-rows.md` (sha1 `{}`, {} B); this stub governs.\n"
IDRE = re.compile(r"^## (M\d{3})")
STUB_RX = re.compile(r"^  — VERBATIM at `docs/named-archive-m364-rows\.md` \(sha1 `([0-9a-f]{12})`,"
                     r" (\d+) B\); this stub governs\.$")


def blocks(text):
    out = []
    idx = [m.start() for m in re.finditer(r"^## ", text, re.M)]
    for k, i in enumerate(idx):
        j = idx[k + 1] if k + 1 < len(idx) else len(text)
        out.append((text[i:text.index("\n", i)], text[i:j], i, j))
    return out


def archive_blocks():
    if not os.path.exists(ARCHIVE):
        return []
    txt = open(ARCHIVE).read()
    out = []
    for k, seg in enumerate(re.split(r"(?m)^## ", txt)[1:]):
        out.append("## " + seg)
    return [b.rstrip("\n") + "\n" for b in out]


def undo(text):
    """put every archived block back in place of its stub (header line + provenance line)"""
    n = 0
    for body in archive_blocks():
        header = body[:body.index("\n")]
        for head, blk, i, j in blocks(text):
            if head != header:
                continue
            lines = blk.splitlines(True)
            if len(lines) >= 2 and STUB_RX.match(lines[1].strip("\n")):
                text = text[:i] + body + text[j:]
                n += 1
            break
    return text, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    text = open(NAMED).read()

    if a.verify:
        bad = 0
        arch = archive_blocks()
        seen = 0
        for k, line in enumerate(text.splitlines()):
            m = STUB_RX.match(line)
            if not m:
                continue
            header = text.splitlines()[k - 1]
            sha, size = m.group(1), int(m.group(2))
            body = next((b for b in arch if b.startswith(header + "\n")), None)
            if body is None:
                print(f"VERIFY FAIL  stub not archived: {header[:70]}")
                bad += 1
                continue
            h = hashlib.sha1(body.encode()).hexdigest()[:12]
            ok = h == sha and len(body) == size
            print(f"VERIFY {'ok  ' if ok else 'FAIL'}  {header[:52]}  sha1 {h} ({len(body)} B)")
            bad += not ok
            seen += 1
        print(f"\n{'PASS' if not bad else 'FAIL'} m364_named_rotate --verify "
              f"({seen} stubs checked, {bad} bad)")
        return 0 if not bad else 1

    text, undone = undo(text)
    print(f"undo: restored {undone} archived block(s) into NAMED.md")
    refs = ""
    for p in REFS:
        if os.path.exists(p):
            refs += open(p, errors="replace").read()
    picked = []
    for head, body, i, j in blocks(text):
        mid = IDRE.match(body)
        if not mid or len(body) < MIN or "named-archive" in body:
            continue
        mid = mid.group(1)
        if re.search(r"\b%s\b" % mid, refs):
            continue
        if re.search(r"\b%s\b" % mid, text[:i] + text[j:]):
            continue
        picked.append((mid, head, body))
        if len(picked) == WANT:
            break
    if len(picked) < 2:
        print(f"only {len(picked)} eligible blocks - nothing rotated")
        return 1
    arch = ["# NAMED.md blocks ROTATED VERBATIM by `scripts/m364_named_rotate.py`\n"
            "(byte-exact; each stub in NAMED.md carries the block's sha1 and byte count)\n\n"]
    for mid, head, body in picked:
        body = body.rstrip("\n") + "\n"
        sha = hashlib.sha1(body.encode()).hexdigest()[:12]
        arch.append(body + "\n")
        text = text.replace(body, head + "\n" + PROV.format(sha, len(body)) + "\n", 1)
        print(f"rotated {mid}: {len(body)} B sha1 {sha}")
    open(ARCHIVE, "w").write("".join(arch))
    open(NAMED, "w").write(text)
    print(f"NAMED.md now {len(text)} B")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
