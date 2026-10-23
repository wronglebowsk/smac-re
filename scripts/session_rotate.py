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


def main():
    ap = argparse.ArgumentParser()
    # Rotate by SIZE, not by section count: sessions vary from 2 k to 12 k chars, so "keep N"
    # either bloats the hot file or throws away context that still fits.
    ap.add_argument("--target", type=int, default=60_000, help="hot-file char budget")
    ap.add_argument("--min-keep", type=int, default=3)
    ap.add_argument("--max-keep", type=int, default=25)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

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

    print(f"keep : {len(keep)} sessions ({label(keep[0])} …)")
    print(f"move : {len(old)} sessions ({label(old[0])} … {label(old[-1])})")
    print(f"       {sum(len(s) for s in old):,} chars → {os.path.relpath(dest, ROOT)}")
    if not args.apply:
        print("\ndry run — rerun with --apply")
        return 0

    body = (f"# Session notes archive — sessions {span}\n\n"
            f"Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot\n"
            f"file readable in one context window. Same evidence file paths apply.\n\n"
            + "\n".join(old))
    open(dest, "w", encoding="utf-8").write(body.rstrip() + "\n")

    index = (f"Older sessions: `docs/sessions/sessions-{span}.md` "
             f"({len(old)} sessions). Read it only when a question reaches back before "
             f"session {keep[0].split('(')[0].strip()}.\n\n")
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
