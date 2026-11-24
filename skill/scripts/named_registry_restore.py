#!/usr/bin/env python3
"""Repair NAMED.md after a squash merge dropped registry sections.

A squash takes the BRANCH's copy of NAMED.md, so a branch cut before other merges can
silently delete dozens of `## <ID>` blocks while the size-only gate stays GREEN. Run this
from the repo root after every merge whose base moved under the branch.

    python3 scripts/named_registry_restore.py <base-rev>          # dry run: list dropped blocks
    python3 scripts/named_registry_restore.py <base-rev> --write  # restore them VERBATIM

Identity is the FULL heading line, not its first token: the registry carries repeated
`## (ARCHIVE) ...` markers whose first token is identical, and a first-token key silently
collapses one of them (a real bug hit while repairing a 34-block loss).

Sections present in the working copy are kept byte-for-byte (a legitimate stub or a newly
added block survives); only sections absent from it are re-inserted, each before the next
source-order heading that still exists. Refuses to write when the result would breach the
cap, so it can never turn a repair into a gate failure.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

ROOT = os.environ.get("SMAC_REPO", "/home/paul/reverse/smac")
TARGET = "NAMED.md"
HEADING = re.compile(r"^## .+", re.M)
CAP_DEFAULT = 250_000


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def sections(text: str) -> list[tuple[str, int, int]]:
    """[(full heading line, start, end)] in file order; duplicates kept."""
    matches = list(HEADING.finditer(text))
    out = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((m.group(0).rstrip(), m.start(), end))
    return out


def split(text: str) -> tuple[str, list[tuple[str, str]]]:
    secs = sections(text)
    preamble = text[: secs[0][1]] if secs else text
    return preamble, [(h, text[a:b]) for h, a, b in secs]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("base_rev", help="commit the registry was whole at (e.g. the pre-merge main)")
    ap.add_argument("--write", action="store_true", help="apply the repair (default: dry run)")
    ap.add_argument("--cap", type=int, default=CAP_DEFAULT, help=f"hard byte cap (default {CAP_DEFAULT})")
    args = ap.parse_args()

    os.chdir(ROOT)
    src = git("show", f"{args.base_rev}:{TARGET}")
    with open(TARGET, encoding="utf-8") as fh:
        cur = fh.read()

    _, src_secs = split(src)
    cur_pre, cur_secs = split(cur)
    cur_heads = {h for h, _ in cur_secs}
    cur_by_head = {h: body for h, body in cur_secs}

    src_order = [h for h, _ in src_secs]
    missing = [h for h in src_order if h not in cur_heads]
    print(f"base {args.base_rev}: {len(src_secs)} headings / {len(src.encode())} B")
    print(f"working:        {len(cur_secs)} headings / {len(cur.encode())} B")
    if not missing:
        print("registry intact: every base heading is present")
        return 0
    print(f"DROPPED ({len(missing)}):")
    for h in missing:
        print("  " + h[:120])
    if not args.write:
        print("dry run - re-run with --write to restore them verbatim")
        return 1

    pending: dict[str | None, list[str]] = {}
    for idx, head in enumerate(src_order):
        if head in cur_heads:
            continue
        anchor = next((later for later in src_order[idx + 1 :] if later in cur_heads), None)
        pending.setdefault(anchor, []).append(dict(src_secs)[head])

    out = [cur_pre]
    for head, body in cur_secs:
        out.extend(pending.pop(head, []))
        out.append(body)
    if pending.get(None):
        out.extend(pending.pop(None))
    leftover = [a for a in pending if a is not None]
    if leftover:
        sys.exit(f"internal: unreachable insert anchors: {leftover}")

    new = "".join(out)
    still = [h for h in src_order if h not in {h for h, _ in split(new)[1]}]
    if still:
        sys.exit(f"refusing to write: still missing {len(still)} heading(s): {still[:3]}")
    size = len(new.encode())
    if size > args.cap:
        sys.exit(f"refusing to write: {size} B exceeds cap {args.cap}")

    tmp = TARGET + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(new)
    os.replace(tmp, TARGET)
    print(f"restored {len(missing)} section(s): {len(cur.encode())} -> {size} B")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
