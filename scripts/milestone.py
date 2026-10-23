#!/usr/bin/env python3
"""Milestone lifecycle for the SMAC RE repo.

    python3 scripts/milestone.py status          # repo state + open PRs + next tasks
    python3 scripts/milestone.py start M51a      # branch milestone/m51a off main
    python3 scripts/milestone.py check           # run the gate against main
    python3 scripts/milestone.py submit          # commit, push, open PR (needs green gate)
    python3 scripts/milestone.py merge 12        # merge a PR whose gate is green
    python3 scripts/milestone.py brief           # one-screen brief for a new session

The loop this supports is documented in AGENTS.md / docs/WORKFLOW.md.
"""

import argparse
import json
import os
import re
import subprocess
import sys

BASE = "main"


def run(*args, check=True):
    p = subprocess.run(args, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise SystemExit(f"$ {' '.join(args)}\n{p.stdout}{p.stderr}")
    return p


def git(*args, check=True):
    return run("git", *args, check=check).stdout


def gh_json(*args):
    p = run("gh", *args)
    try:
        return json.loads(p.stdout or "null")
    except json.JSONDecodeError:
        return None


def branch():
    return git("rev-parse", "--abbrev-ref", "HEAD").strip()


def dirty():
    out = git("status", "--porcelain").strip()
    return [l for l in out.splitlines() if l]


def latest_session():
    text = open("SESSION_NOTES.md", encoding="utf-8").read() if os.path.exists("SESSION_NOTES.md") else ""
    heads = re.findall(r"^## (Session .*)$", text, re.M)
    return heads[-1] if heads else "(none)"


def next_tasks(limit=6):
    if not os.path.exists("NEXT_PROMPT.md"):
        return []
    text = open("NEXT_PROMPT.md", encoding="utf-8").read()
    m = re.search(r"^## Milestone options.*?$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not m:
        return []
    return [l.strip("- ").strip() for l in m.group(1).splitlines() if l.startswith("- ")]


def gate(base=f"origin/{BASE}"):
    if run("git", "rev-parse", "--verify", base, check=False).returncode != 0:
        base = BASE
    p = run(sys.executable, "scripts/gate.py", "--base", base, check=False)
    return p.returncode == 0, (p.stdout + p.stderr).strip()


def open_prs():
    prs = gh_json("pr", "list", "--state", "open", "--json",
                  "number,title,headRefName,url,isDraft,mergeable,mergeStateStatus,statusCheckRollup")
    return prs or []


def pr_verdict(pr):
    checks = pr.get("statusCheckRollup") or []
    states = [c.get("conclusion") or c.get("state") for c in checks]
    red = [s for s in states if s in ("FAILURE", "ERROR", "CANCELLED", "TIMED_OUT")]
    pending = [s for s in states if s in (None, "PENDING", "IN_PROGRESS", "QUEUED", "EXPECTED")]
    if red:
        return "RED", f"{len(red)} failing check(s)"
    if pending:
        return "PENDING", f"{len(pending)} check(s) running"
    if pr.get("mergeable") == "CONFLICTING":
        return "CONFLICT", "merge conflict with main"
    if pr.get("isDraft"):
        return "DRAFT", "draft PR"
    if not checks:
        return "NO-CI", "no status checks reported"
    return "GREEN", "all checks passed"


def cmd_status(_args):
    print(f"branch: {branch()}")
    d = dirty()
    print(f"worktree: {'clean' if not d else str(len(d)) + ' modified file(s)'}")
    for line in d[:10]:
        print(f"  {line}")
    print(f"last checkpoint: {latest_session()}")
    print()

    prs = open_prs()
    if not prs:
        print("open PRs: none")
    else:
        print(f"open PRs: {len(prs)}")
        for pr in prs:
            verdict, why = pr_verdict(pr)
            print(f"  #{pr['number']} [{verdict}] {pr['title']}")
            print(f"    {pr['headRefName']} — {why} — {pr['url']}")
    print()

    ok, out = gate()
    print("gate vs main:", "GREEN" if ok else "RED")
    if not ok:
        for line in out.splitlines():
            if line.startswith("[FAIL]"):
                print("  " + line)
    print()

    tasks = next_tasks()
    if tasks:
        print("next milestone options (from NEXT_PROMPT.md):")
        for t in tasks:
            print(f"  - {t}")
    return 0


def cmd_brief(_args):
    print("SMAC RE — session brief")
    print("=" * 40)
    print(f"last checkpoint : {latest_session()}")
    print(f"branch          : {branch()}")
    ev = run(sys.executable, "scripts/evidence.py", "budget", check=False)
    for line in ev.stdout.splitlines():
        if line.startswith(("always loaded", "lookups", "evidence/")):
            print(f"budget          : {line.strip()}")
    prs = open_prs()
    if prs:
        print("\nACTION: there are open PRs — assess and land them before starting new work.")
        for pr in prs:
            verdict, why = pr_verdict(pr)
            print(f"  #{pr['number']} [{verdict}] {pr['title']} ({why})")
    else:
        print("\nNo open PRs — start the next milestone.")
    tasks = next_tasks()
    if tasks:
        print("\nQueue:")
        for t in tasks:
            print(f"  - {t}")
    print("\nRead: NEXT_PROMPT.md (footing + queued test), then skill_view('smac-cvr-format').")
    return 0


def cmd_start(args):
    if dirty():
        raise SystemExit("worktree dirty — commit or stash before starting a milestone")
    git("fetch", "origin", "--quiet")
    git("checkout", BASE, "--quiet")
    git("pull", "--ff-only", "--quiet")
    name = args.milestone.lower().replace(" ", "-")
    br = f"milestone/{name}"
    if run("git", "rev-parse", "--verify", br, check=False).returncode == 0:
        raise SystemExit(f"branch {br} already exists")
    git("checkout", "-b", br)
    print(f"branch {br} ready (from {BASE})")
    print("\nFooting: NEXT_PROMPT.md — read it in full before touching the game.")
    tasks = next_tasks()
    for t in tasks:
        if name in t.lower() or args.milestone.lower() in t.lower():
            print(f"this milestone: {t}")
            break
    return 0


def cmd_check(_args):
    ok, out = gate()
    print(out)
    return 0 if ok else 1


def milestone_id():
    br = branch()
    m = re.match(r"^milestone/(.+)$", br)
    return m.group(1).upper() if m else br


def build_body(mid):
    commits = git("log", "--oneline", f"{BASE}..HEAD").strip()
    diff = git("diff", "--stat", f"{BASE}...HEAD").strip()
    cites = sorted(set(re.findall(r"evidence/[A-Za-z0-9_./-]+\.(?:log|txt|gdb|json|png|csv):\d+(?:-\d+)?",
                                  git("diff", f"{BASE}...HEAD"))))
    cite_block = "\n".join(f"- `{c}`" for c in cites[:15]) or "- (no line citations added)"
    return f"""## Milestone
{mid}

## What changed
```
{commits}
```

```
{diff}
```

## Evidence
{cite_block}

## Verified vs inferred
<!-- state which claims are live-verified and which remain open -->

## Checklist
- [x] one milestone only
- [x] SESSION_NOTES.md has a new dated section
- [x] NEXT_PROMPT.md rewritten for the next session
- [x] evidence committed and line citations resolve
- [x] no game binaries or large generated artifacts staged
"""


def cmd_submit(args):
    # Check the branch FIRST: committing before this guard leaves a stray
    # "<id>: checkpoint" commit on main (happened once, 2026-10-22).
    br = branch()
    if br == BASE:
        raise SystemExit("on main — start a milestone branch first (milestone.py start <ID>)")
    rotate_sessions()
    ok, out = gate()
    if not ok:
        print(out)
        raise SystemExit("gate is RED — fix the failures above before submitting")
    if dirty():
        mid = milestone_id()
        git("add", "-A")
        git("commit", "-m", args.message or f"{mid}: checkpoint")
    git("push", "-u", "origin", br, "--quiet")
    mid = milestone_id()
    existing = gh_json("pr", "list", "--head", br, "--state", "open", "--json", "number,url")
    if existing:
        print(f"PR already open: {existing[0]['url']}")
        return 0
    body = build_body(mid)
    path = ".git/PR_BODY.md"
    open(path, "w", encoding="utf-8").write(body)
    p = run("gh", "pr", "create", "--base", BASE, "--head", br,
            "--title", f"{mid}: {args.title or latest_session()}",
            "--body-file", path)
    print(p.stdout.strip())
    print("\nCI will run the same gate. Land it with: milestone.py merge <number>")
    return 0


def cmd_merge(args):
    pr = gh_json("pr", "view", str(args.pr), "--json",
                 "number,title,url,mergeable,mergeStateStatus,isDraft,statusCheckRollup,headRefName")
    if not pr:
        raise SystemExit(f"PR {args.pr} not found")
    verdict, why = pr_verdict(pr)
    print(f"#{pr['number']} {pr['title']}")
    print(f"verdict: {verdict} — {why}")
    if verdict != "GREEN" and not args.force:
        raise SystemExit("not ready to merge (use --force only for a human override)")
    run("gh", "pr", "merge", str(args.pr), "--squash", "--delete-branch")
    git("checkout", BASE, "--quiet")
    git("pull", "--ff-only", "--quiet")
    print(f"merged #{pr['number']}; {BASE} is up to date")
    if not args.no_index:
        rebuild_index()
    return 0


def rotate_sessions(target=60_000):
    """Archive old sessions before the gate runs: a checkpoint that pushes SESSION_NOTES.md
    over budget should rotate, not fail. Fail-soft — never block a submit on housekeeping."""
    script = os.path.join("scripts", "session_rotate.py")
    if not os.path.isfile(script):
        return
    p = subprocess.run([sys.executable, script, "--apply", "--target", str(target)],
                       capture_output=True, text=True)
    if p.returncode != 0:
        print("sessions: rotation skipped — " + (p.stderr.strip().splitlines() or ["unknown"])[-1])
        return
    line = [l for l in p.stdout.splitlines() if "SESSION_NOTES.md:" in l]
    if line:
        print("sessions: " + line[0].strip())


def rebuild_index(timeout=240):
    """Index is derived data — never let a flaky embedding endpoint block a landed milestone."""
    if not os.path.isfile(os.path.join("scripts", "index.py")):
        return
    print("index: rebuilding (incremental) ...")
    try:
        p = subprocess.run([sys.executable, os.path.join("scripts", "index.py"), "build"],
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"index: timed out after {timeout}s — previous index kept")
        return
    if p.returncode != 0:
        last = (p.stderr.strip().splitlines() or p.stdout.strip().splitlines() or ["unknown error"])[-1]
        print(f"index: skipped — {last}")
        return
    print("index: " + (p.stdout.strip().splitlines() or ["ok"])[-1])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    sub.add_parser("brief").set_defaults(fn=cmd_brief)
    sub.add_parser("check").set_defaults(fn=cmd_check)
    s = sub.add_parser("start")
    s.add_argument("milestone")
    s.set_defaults(fn=cmd_start)
    s = sub.add_parser("submit")
    s.add_argument("--title")
    s.add_argument("--message")
    s.set_defaults(fn=cmd_submit)
    s = sub.add_parser("merge")
    s.add_argument("pr")
    s.add_argument("--force", action="store_true")
    s.add_argument("--no-index", action="store_true", help="skip the post-merge index rebuild")
    s.set_defaults(fn=cmd_merge)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
