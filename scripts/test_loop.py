#!/usr/bin/env python3
"""Exercise the gate against real repositories in throwaway worktrees.

Every rule here is one that actually mattered: a game binary slipping into git, a citation
pointing past the end of a log, or a milestone PR that updates no notes. Run before changing
gate.py — a gate that silently stops firing is worse than no gate.

    python3 scripts/test_loop.py          # ~15 s
"""

import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []
# Test whatever is checked out: run this on your feature branch, before submitting.
BASE = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT,
                      capture_output=True, text=True).stdout.strip() or "main"


def git(cwd, *args):
    return subprocess.run(["git"] + list(args), cwd=cwd, capture_output=True, text=True, check=True).stdout


def gate(cwd, base=None):
    base = base or BASE
    p = subprocess.run([sys.executable, "scripts/gate.py", "--base", base], cwd=cwd,
                       capture_output=True, text=True)
    return p.returncode, p.stdout


def check(name, cond, detail=""):
    print(f"  {'ok  ' if cond else 'FAIL'} {name}" + (f"  [{detail}]" if not cond and detail else ""))
    if not cond:
        FAILS.append(name)


def worktree(tmp, name, branch=None):
    path = os.path.join(tmp, name)
    if branch:
        git(ROOT, "branch", "-f", branch, BASE)
        git(ROOT, "worktree", "add", "-f", path, branch)
    else:
        git(ROOT, "worktree", "add", "-f", "--detach", path, BASE)
    return path


def main():
    tmp = tempfile.mkdtemp(prefix="loopsim-", dir=os.path.expanduser("~/.hermes/cache/scratch"))
    try:
        print("case 1: a clean tree passes")
        wt = worktree(tmp, "clean")
        rc, out = gate(wt)
        check("clean tree is GREEN", rc == 0 and "GATE GREEN" in out, out.strip().splitlines()[-1])

        print("case 2: a game binary is refused")
        wt = worktree(tmp, "binary")
        open(os.path.join(wt, "programs", "fake.exe"), "wb").write(b"MZ" + b"\0" * 64) \
            if os.path.isdir(os.path.join(wt, "programs")) else None
        if not os.path.isdir(os.path.join(wt, "programs")):
            os.makedirs(os.path.join(wt, "programs"))
            open(os.path.join(wt, "programs", "fake.exe"), "wb").write(b"MZ" + b"\0" * 64)
        git(wt, "add", "-f", "programs/fake.exe")
        git(wt, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "binary")
        rc, out = gate(wt)
        check("tracked .exe is RED", rc != 0 and "game binaries" in out, out.strip().splitlines()[-1])

        print("case 3: a bad citation is refused")
        wt = worktree(tmp, "cite", branch="test/cite")
        with open(os.path.join(wt, "SESSION_NOTES.md"), "a", encoding="utf-8") as f:
            f.write('\n## Session 99 (test) — citation probe\n\n- claim (`evidence/cite_probe.log:99`)\n')
        with open(os.path.join(wt, "evidence", "cite_probe.log"), "w") as f:
            f.write("one line\n")
        with open(os.path.join(wt, "NEXT_PROMPT.md"), "a") as f:
            f.write("\nprobe\n")
        git(wt, "add", "-A")
        git(wt, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "milestone probe")
        rc, out = gate(wt)
        check("out-of-range citation is RED", rc != 0 and "citations" in out, out.strip().splitlines()[-1])

        print("case 4: the same milestone with a valid citation passes")
        with open(os.path.join(wt, "SESSION_NOTES.md"), encoding="utf-8") as f:
            body = f.read().replace("cite_probe.log:99", "cite_probe.log:1")
        with open(os.path.join(wt, "SESSION_NOTES.md"), "w", encoding="utf-8") as f:
            f.write(body)
        # Identity flags are mandatory: a clean CI runner has no user.name/email,
        # and `git commit` exits 128 there (caught by CI on PR #8).
        git(wt, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qam", "fix citation")
        rc, out = gate(wt)
        check("valid milestone is GREEN", rc == 0 and "GATE GREEN" in out, out.strip().splitlines()[-1])
        print("case 5: a committed endpoint is refused")
        wt = worktree(tmp, "endpoint")
        with open(os.path.join(wt, "docs", "endpoint_probe.md"), "w", encoding="utf-8") as f:
            f.write("the model listens on " + "192." + "168.1.12:8080" + "\n")
        git(wt, "add", "-A")
        git(wt, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "endpoint probe")
        rc, out = gate(wt)
        check("committed private IPv4 is RED", rc != 0 and "committed endpoints" in out,
              out.strip().splitlines()[-1])

    finally:
        for name in ("clean", "binary", "cite", "endpoint"):
            subprocess.run(["git", "worktree", "remove", "--force", os.path.join(tmp, name)],
                           cwd=ROOT, capture_output=True)
        subprocess.run(["git", "branch", "-D", "test/cite"], cwd=ROOT, capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if FAILS:
        print(f"FAILED: {len(FAILS)} — {', '.join(FAILS)}")
        return 1
    print("all gate behaviours hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
