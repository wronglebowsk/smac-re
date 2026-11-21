#!/usr/bin/env python3
"""Rotate old sessions out of SESSION_NOTES.md so the per-session read stays small.

    python3 scripts/session_rotate.py            # dry run: what would move
    python3 scripts/session_rotate.py --apply    # move oldest sections to docs/sessions/

Keeps the preamble and the newest N session sections in SESSION_NOTES.md, writes the removed
ones to docs/sessions/sessions-<first>-<last>.md, and leaves an index line behind. Nothing is
deleted: SESSION_NOTES.md is the hot set, docs/sessions/ is the warm set, git is the cold set.
"""

import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTES = os.path.join(ROOT, "SESSION_NOTES.md")
ARCHIVE = os.path.join(ROOT, "docs", "sessions")
HEADER_RE = re.compile(r"^## Session\b", re.M)
INDEX_RE = re.compile(r"^Older sessions: .*$", re.M)


def split(text):
    starts = [m.start() for m in HEADER_RE.finditer(text)]
    if not starts:
        return text, []
    preamble, sections = text[:starts[0]], []
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else len(text)
        sections.append(text[s:e].rstrip() + "\n")
    return preamble, sections


def label(section):
    return section.splitlines()[0].removeprefix("## ").strip()


def index_line(fname, labels, first_kept):
    """The hot file's pointer to the warm set. The boundary is a FILE POSITION, not a session
    number: chain1 and chain2 number their sessions independently, so a moved section can carry
    a HIGHER number than the first kept one — the #347 review caught the old wording calling
    sessions-298-296 (which holds Session 298) "before Session 297"."""
    return (f"Older sessions: `{fname}` ({len(labels)} sessions: "
            f"{', '.join(labels)}). The split is by FILE POSITION, not by number — a moved id can "
            f"be numerically newer than the first kept one, so grep the archive for an id before "
            f"deciding it is still hot. The hot file starts at {first_kept}.\n")


def fix_index():
    """Re-emit the hot pointer from the archives ON DISK (F7: a pointer written by the old
    generator mis-states which sessions moved; this re-derives it instead of hand-editing)."""
    text = open(NOTES, encoding="utf-8").read()
    preamble, sections = split(text)
    assert sections, "no sessions in the hot file"
    spans = {}
    for nm in os.listdir(ARCHIVE):
        m = re.fullmatch(r"sessions-(\d+)-(\d+)\.md", nm)
        if m:
            spans[nm] = (int(m.group(1)), int(m.group(2)))
    assert spans, "no archives to point at"
    # Retarget the archive the hot file ALREADY cites (never silently move a pointer to a
    # different warm file); only a hot file with no pointer falls back to the newest span.
    old_line = INDEX_RE.search(text)
    cited = re.search(r"`docs/sessions/([^`]+)`", old_line.group(0)) if old_line else None
    if cited:
        nm = cited.group(1)
        assert nm in spans, "the hot pointer cites an archive that is not on disk: " + nm
    else:
        nm = max(spans, key=lambda o: spans[o])
    labels = [ln.removeprefix("## ").split("(")[0].strip()
              for ln in open(os.path.join(ARCHIVE, nm), encoding="utf-8").read().splitlines()
              if ln.startswith("## Session")]
    assert labels, f"no sessions found inside {nm}"
    line = index_line(f"docs/sessions/{nm}", labels, label(sections[0]).split("(")[0].strip())
    body = re.sub(INDEX_RE, "", preamble).rstrip() + "\n\n" + line + "\n" + "\n".join(sections)
    if not body.endswith("\n"):
        body += "\n"
    open(NOTES, "w", encoding="utf-8").write(body)
    print("index line rewritten from %d archive headers: %s" % (len(labels), line.strip()[:180] + " …"))
    return 0


def main():
    ap = argparse.ArgumentParser()
    # Rotate by SIZE, not by section count: sessions vary from 2 k to 12 k chars, so "keep N"
    # either bloats the hot file or throws away context that still fits.
    ap.add_argument("--target", type=int, default=60_000, help="hot-file char budget")
    ap.add_argument("--min-keep", type=int, default=3)
    ap.add_argument("--max-keep", type=int, default=25)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--fix-index", action="store_true",
                    help="re-derive the hot file's Older-sessions pointer from the archives on disk")
    args = ap.parse_args()
    if args.fix_index:
        return fix_index()

    text = open(NOTES, encoding="utf-8").read()
    preamble, sections = split(text)
    total = len(preamble) + sum(len(s) for s in sections)
    if total <= args.target:
        print(f"{len(sections)} sessions, {total:,} chars <= {args.target:,} — nothing to rotate")
        return 0

    n_keep = len(sections)
    while n_keep > args.min_keep and n_keep > 0:
        kept = len(preamble) + sum(len(s) for s in sections[-n_keep:])
        if kept <= args.target or n_keep <= args.min_keep:
            break
        n_keep -= 1
    n_keep = min(n_keep, args.max_keep)
    old, keep = sections[:len(sections) - n_keep], sections[len(sections) - n_keep:]
    first = re.search(r"Session (\d+)", label(old[0]))
    last = re.search(r"Session (\d+)", label(old[-1]))
    span = f"{first.group(1) if first else 'x'}-{last.group(1) if last else 'y'}"
    os.makedirs(ARCHIVE, exist_ok=True)
    dest = os.path.join(ARCHIVE, f"sessions-{span}.md")

    # The hot file cites only the NEWEST archive, so every rotation would orphan the previous
    # one unless the new archive carries the onward pointer (found by the s292 review of #316).
    prev, lo = None, int(first.group(1)) if first else 0
    try:
        # Same (lo, hi) total order as scripts/s292_chain_fix.py: the archives on disk OVERLAP,
        # and "nearest strictly older" would skip the overlapping one and orphan it.
        spans = {}
        for nm in os.listdir(ARCHIVE):
            m = re.fullmatch(r"sessions-(\d+)-(\d+)\.md", nm)
            if m:
                spans[nm] = (int(m.group(1)), int(m.group(2)))
        older = [o for o, (olo, ohi) in spans.items() if (olo, ohi) < (lo, int(last.group(1) if last else lo))]
        prev = max(older, key=lambda o: spans[o]) if older else None
    except OSError:
        pass
    print(f"       onward pointer for the archive: {prev or '(none — oldest)'}")

    print(f"keep : {len(keep)} sessions ({label(keep[0])} …)")
    print(f"move : {len(old)} sessions ({label(old[0])} … {label(old[-1])})")
    print(f"       {sum(len(s) for s in old):,} chars → {os.path.relpath(dest, ROOT)}")
    if not args.apply:
        print("\ndry run — rerun with --apply")
        return 0

    body = (f"# Session notes archive — sessions {span}\n\n"
            f"Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot\n"
            f"file readable in one context window. Same evidence file paths apply.\n"
            + (f"\nOlder sessions: `docs/sessions/{prev}` — the hot file cites only THIS archive, so\n"
               f"the chain onward lives here; without this line the older archives are orphans (s292).\n"
               if prev else "")
            + "\n"
            + "\n".join(old))
    open(dest, "w", encoding="utf-8").write(body.rstrip() + "\n")

    # One code path for the pointer wording, so --fix-index and a real rotation can never drift.
    labels = [label(s).split("(")[0].strip() for s in old]
    index = index_line(f"docs/sessions/sessions-{span}.md", labels,
                       label(keep[0]).split("(")[0].strip()) + "\n"
    new_text = re.sub(INDEX_RE, "", preamble).rstrip() + "\n\n" + index + "\n".join(keep)
    if not new_text.endswith("\n"):
        new_text += "\n"
    open(NOTES, "w", encoding="utf-8").write(new_text)
    print(f"\nSESSION_NOTES.md: {len(text):,} → {len(new_text):,} chars "
          f"({len(new_text) / 4 / 262144 * 100:.1f}% of a 262k context)")
    print(f"archived to {os.path.relpath(dest, ROOT)} — commit both files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
