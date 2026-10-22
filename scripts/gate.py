#!/usr/bin/env python3
"""Mechanical merge gate for the SMAC RE repo.

Runs the same checks locally and in CI. Exit 0 = the change is eligible to merge.

    python3 scripts/gate.py                # against local main
    python3 scripts/gate.py --base origin/main
    python3 scripts/gate.py --docs-only    # docs/CI-only change: skip checkpoint checks

Checks (HARD unless marked WARN):
  1. no game binaries or generated trees tracked
  2. no tracked file over MAX_BYTES (warn over WARN_BYTES)
  3. a milestone PR touches SESSION_NOTES.md AND NEXT_PROMPT.md, and adds a new
     "## Session" section
  4. every evidence/<file>:<line> citation in changed Markdown resolves
  5. relative Markdown links in changed files resolve
  6. no conflict markers in changed text files
  7. skill/SKILL.md matches the live agent skill (local only, WARN)
  8. branch name looks like milestone/<id> (WARN)
"""

import argparse
import fnmatch
import os
import re
import subprocess
import sys

MAX_BYTES = 25 * 1024 * 1024
WARN_BYTES = 5 * 1024 * 1024

FORBIDDEN_EXT = (".exe", ".dll", ".iso", ".sav", ".cvr", ".flc")
FORBIDDEN_TREES = ("programs/", "glsmac/", "ghidra_out/", "ghidra_proj/",
                   "flc_out/", "png/", "png_flic/", "scratch/")

CITE_RE = re.compile(r"(evidence/[A-Za-z0-9_./-]+\.(?:log|txt|gdb|json|png|csv)):(\d+)(?:-(\d+))?")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
CONFLICT_RE = re.compile(r"^(<{7}|={7}|>{7})( |$)", re.M)

results = []  # (level, name, message)


def run(*args):
    return subprocess.run(args, capture_output=True, text=True)


def git(*args):
    p = run("git", *args)
    if p.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{p.stderr.strip()}")
    return p.stdout


def report(level, name, message):
    results.append((level, name, message))


def diff_names(base):
    out = git("diff", "--name-only", f"{base}...HEAD")
    return [l for l in out.splitlines() if l.strip()]


def check_blobs():
    tracked = git("ls-files").splitlines()
    bad = []
    for f in tracked:
        if f.endswith(FORBIDDEN_EXT) or any(f.startswith(t) for t in FORBIDDEN_TREES):
            bad.append(f)
    if bad:
        report("FAIL", "no game binaries tracked", ", ".join(bad[:8]))
    else:
        report("PASS", "no game binaries tracked", f"{len(tracked)} files")


def check_sizes():
    tracked = [f for f in git("ls-files").splitlines() if os.path.isfile(f)]
    big, warn = [], []
    for f in tracked:
        size = os.path.getsize(f)
        if size > MAX_BYTES:
            big.append(f"{f} ({size // 1048576} MB)")
        elif size > WARN_BYTES:
            warn.append(f"{f} ({size // 1048576} MB)")
    if big:
        report("FAIL", "tracked file size", "over 25 MB: " + ", ".join(big[:5]))
    elif warn:
        report("WARN", "tracked file size", "large (consider gitignoring): " + ", ".join(warn[:5]))
    else:
        report("PASS", "tracked file size", "all under 5 MB")


def session_sections(text):
    return re.findall(r"^## Session\b.*$", text, re.M)


def check_checkpoint(base, docs_only):
    changed = diff_names(base)
    if docs_only:
        report("PASS", "milestone checkpoint", "skipped (--docs-only)")
        return
    missing = [f for f in ("SESSION_NOTES.md", "NEXT_PROMPT.md") if f not in changed]
    if missing:
        # Tooling/documentation changes (no evidence, no milestone driver) are not milestones.
        looks_like_tooling = not any(
            f.startswith("evidence/") or re.match(r"scripts/m\d+[a-z]?_drive\.py$", f)
            for f in changed
        )
        if looks_like_tooling:
            report("WARN", "milestone checkpoint",
                   "not a milestone PR (no SESSION_NOTES/NEXT_PROMPT change)")
            return
        report("FAIL", "milestone checkpoint", "not updated: " + ", ".join(missing))
        return
    head = open("SESSION_NOTES.md", encoding="utf-8").read()
    try:
        old = git("show", f"{base}:SESSION_NOTES.md")
    except SystemExit:
        old = ""
    new_sections = len(session_sections(head)) - len(session_sections(old))
    if new_sections < 1:
        report("FAIL", "milestone checkpoint", "SESSION_NOTES.md has no new '## Session' section")
    else:
        report("PASS", "milestone checkpoint", f"{new_sections} new session section(s)")

    if "NAMED.md" in changed:
        report("PASS", "address registry", "NAMED.md updated")
    else:
        report("WARN", "address registry", "NAMED.md untouched (fine if no addresses changed)")


def check_citations(base):
    changed_md = [f for f in diff_names(base) if f.endswith(".md") and os.path.isfile(f)]
    # Only lines added by this change are held to the citation rule.
    bad, total = [], 0
    diff = git("diff", "-U0", f"{base}...HEAD", "--", *changed_md) if changed_md else ""
    added = [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
    for line in added:
        for m in CITE_RE.finditer(line):
            total += 1
            path, start, end = m.group(1), int(m.group(2)), m.group(3)
            if not os.path.isfile(path):
                bad.append(f"{path} (missing)")
                continue
            if path.endswith(".png"):
                continue
            with open(path, "rb") as fh:
                lines = sum(1 for _ in fh)
            last = int(end) if end else start
            if last > lines or start < 1:
                bad.append(f"{path}:{last} (file has {lines} lines)")
    if bad:
        report("FAIL", "evidence citations", "; ".join(sorted(set(bad))[:6]))
    else:
        report("PASS", "evidence citations", f"{total} cite(s) resolve")


def check_links(base):
    changed_md = [f for f in diff_names(base) if f.endswith(".md") and os.path.isfile(f)]
    bad = []
    for f in changed_md:
        for target in LINK_RE.findall(open(f, encoding="utf-8").read()):
            if re.match(r"^[a-z]+://|^#|^mailto:", target):
                continue
            path = target.split("#")[0]
            if not path:
                continue
            if not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(f), path))):
                bad.append(f"{f} -> {target}")
    if bad:
        report("WARN", "local links", "; ".join(bad[:5]))
    else:
        report("PASS", "local links", f"{len(changed_md)} file(s) checked")


def check_conflicts(base):
    changed = [f for f in diff_names(base)
               if f.endswith((".md", ".py", ".yml", ".yaml", ".json")) and os.path.isfile(f)]
    hits = [f for f in changed if CONFLICT_RE.search(open(f, encoding="utf-8", errors="ignore").read())]
    if hits:
        report("FAIL", "conflict markers", ", ".join(hits[:5]))
    else:
        report("PASS", "conflict markers", "none")


def check_skill_sync():
    live = os.path.expanduser("~/.hermes/skills/smac-cvr-format/SKILL.md")
    if not os.path.isfile(live) or not os.path.isfile("skill/SKILL.md"):
        report("WARN", "skill sync", "skipped (no live skill on this host)")
        return
    a, b = open(live, encoding="utf-8").read(), open("skill/SKILL.md", encoding="utf-8").read()
    if a == b:
        report("PASS", "skill sync", "skill/ matches live skill")
    else:
        report("FAIL", "skill sync", "skill/SKILL.md differs from ~/.hermes/skills copy — refresh it")


def check_branch():
    ref = os.environ.get("GITHUB_HEAD_REF") or git("rev-parse", "--abbrev-ref", "HEAD").strip()
    ok = re.match(r"^(milestone|workflow|docs|fix)/[a-z0-9._-]+$", ref)
    report("PASS" if ok else "WARN", "branch name",
           ref if ok else f"'{ref}' (expected milestone/<id>)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="main")
    ap.add_argument("--docs-only", action="store_true")
    args = ap.parse_args()

    base = args.base
    if not git("rev-parse", "--verify", base).strip():
        raise SystemExit(f"base {base} not found")

    check_blobs()
    check_sizes()
    check_checkpoint(base, args.docs_only)
    check_citations(base)
    check_links(base)
    check_conflicts(base)
    check_skill_sync()
    check_branch()

    fails = [r for r in results if r[0] == "FAIL"]
    for level, name, msg in results:
        print(f"[{level:4}] {name}: {msg}")
    print()
    if fails:
        print(f"GATE RED — {len(fails)} check(s) failed")
        return 1
    warns = sum(1 for r in results if r[0] == "WARN")
    print(f"GATE GREEN — ready to merge ({warns} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
