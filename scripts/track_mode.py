#!/usr/bin/env python3
"""track_mode.py — the build/analyse cadence verdict for the unattended loop.

Prints ONE actionable line, e.g.

    MODE=BUILD analyse_since_build=3 last_build=B0 next_rung=B1 — this fire BUILDS (read BUILD_SPINE.md §B1)
    MODE=ANALYSE analyse_since_build=1 last_build=B0 next_rung=B1 — this fire ANALYSES a census pick

Cadence (BUILD_SPINE.md): every 4th landed fire builds. A build fire starts once THREE
analyse milestones have landed since the newest build commit, so the cycle is
3 x analyse + 1 x build, counted in merged history only.

Why merged history and not a counter file: a state file can drift, be half-written, or
be dropped by a sibling's `git checkout`, while `git log` on origin/main cannot. The
verdict is derived, never stored — the same discipline the project uses for memory
readings (derive from the target, do not trust a cached note).

Subject conventions this script depends on:
  * build commits   -> subject starts with  B<n>       (B0, B1, B2, ... B12)
  * analyse commits -> subject starts with  M<n>       (M217, M222-M226, ...)
  * squash-merge suffixes such as " (#168)" are ignored.

Exit code is ALWAYS 0: the mode is in the output, never in rc, so a fire cannot mistake
a cadence reading for a failure. `--verbose` adds the commit list it counted.
"""

import argparse
import re
import subprocess
import sys

BUILD_RE = re.compile(r"^B(\d+)\b")
ANALYSE_RE = re.compile(r"^M(\d+)\b")
CADENCE = 3          # analyse milestones between build fires


def git_subjects(base: str, limit: int) -> list[tuple[str, str]]:
    """[(short_sha, subject)] newest first, following `base`."""
    out = subprocess.run(
        ["git", "log", f"--format=%h\t%s", f"-{limit}", base],
        capture_output=True, text=True, check=True,
    ).stdout
    rows = []
    for line in out.splitlines():
        if "\t" not in line:
            continue
        sha, subj = line.split("\t", 1)
        rows.append((sha.strip(), subj.strip()))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main", help="ref to read (default origin/main)")
    ap.add_argument("--limit", type=int, default=400, help="commits to scan (default 400)")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    base = a.base
    try:
        git_subjects(base, 1)
    except subprocess.CalledProcessError:
        base = "HEAD"          # offline clone or a branch-only checkout
        try:
            git_subjects(base, 1)
        except subprocess.CalledProcessError:
            print("MODE=ANALYSE analyse_since_build=0 last_build=none next_rung=B1 — git unreadable, treat as ANALYSE")
            return 0

    rows = git_subjects(base, a.limit)

    last_build = None          # (n, sha, subject)
    analyse_since = 0
    counted = []
    for sha, subj in rows:                     # newest -> oldest
        m = BUILD_RE.match(subj)
        if m:
            last_build = (int(m.group(1)), sha, subj)
            break
        if ANALYSE_RE.match(subj):
            analyse_since += 1
            counted.append((sha, subj))

    # next rung = highest build number ever landed + 1 (B0 is the setup commit, so B1 is first)
    highest = -1
    for sha, subj in rows:
        m = BUILD_RE.match(subj)
        if m:
            highest = max(highest, int(m.group(1)))
    next_rung = f"B{highest + 1}"

    mode = "BUILD" if analyse_since >= CADENCE else "ANALYSE"
    last = f"B{last_build[0]}" if last_build else "none"
    verb = "BUILDS (read BUILD_SPINE.md)" if mode == "BUILD" else "ANALYSES a census pick"
    print(f"MODE={mode} analyse_since_build={analyse_since} last_build={last} "
          f"next_rung={next_rung} — this fire {verb}")

    if a.verbose:
        for sha, subj in counted:
            print(f"  counted {sha} {subj[:110]}")
        if last_build:
            print(f"  last build {last_build[1]} {last_build[2][:110]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
