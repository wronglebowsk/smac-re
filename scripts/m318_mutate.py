#!/usr/bin/env python3
"""M318 mutation harness: prove every refresh-pair gate is LOAD-BEARING.

Family 1 (expectation): rewrite ONE instrument literal in a per-invocation
scratch copy. Family 2 (code): M318_PATCH rewrites real parsed instructions
before measurement. MU13 is a DECLARED NO-OP (A's prologue register, which
no gate reads). Baseline must be green first; RED = rc!=0 with an
AssertionError carrying the declared message (a crash is NOT a red);
digest hashes name+verdict+detail.

    python3 -u scripts/m318_mutate.py   # stdout -> evidence/m318_mutate.txt
"""
import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "scripts", "m318_refresh_pair.py")
COPY = os.path.join(ROOT, "scratch", "_m318_mutant_%d.py" % os.getpid())
ENV = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "scripts"))

MUTANTS = [
    ("MU1", "exp", "(A, 1331, 408)", "(A, 1332, 408)", "index row drift"),
    ("MU2", "exp", "(B, 5237, 1589)", "(B, 5237, 1590)", "index row drift"),
    ("MU3", "exp", "== [5] * 12", "== [5] * 11 + [6]", "pair not back-to-back"),
    ("MU4", "exp", '"FUN_004f5a70"}', '}', "owner set drift"),
    ("MU5", "exp", "PAIR_REACH = 17", "PAIR_REACH = 10", "memo store missing before a pair site"),
    ("MU6", "code", "0x4e927e|add esi,0x35", None, "A structure drift at 0x4e927e"),
    ("MU7", "code", "0x4e8e2b|mov edi,DWORD PTR ds:0x68cbb4", None, "A structure drift at 0x4e8e2b"),
    ("MU8", "code", "0x4e90d8|or edx,0x20", None, "A structure drift at 0x4e90d8"),
    ("MU9", "code", "0x4e78e9|call 0x4e63b1", None, "B callee multiset drift"),
    ("MU10", "code", "0x4e79b3|push 0x1e", None, "B structure drift at 0x4e79b3"),
    ("MU11", "code", "0x4e7656|mov DWORD PTR ds:0x8f0cc8,0x1", None, "case-3 effect drift"),
    ("MU12", "code", "0x4e799b|mov ecx,DWORD PTR [eax*4+0x94dc38]", None, "B structure drift at 0x4e799b"),
    ("MU13", "noop", "0x4e8d60|push ebx", None, None),
]


def run(args, env):
    p = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, text=True, timeout=300)
    return p.returncode, p.stdout + p.stderr


def classify(out, rc, expect):
    if rc == 0:
        return "GREEN", "exit 0"
    last = [l for l in out.strip().splitlines() if l.strip()][-1]
    if last.startswith("AssertionError") and (expect is None or expect in out):
        return "RED", last[:120]
    return "CRASH", last[:120]


def main():
    src = open(SRC).read()
    rc, out = run([sys.executable, "-u", SRC], ENV)
    assert rc == 0, "baseline not green - refusing to score:\n" + out[-2000:]
    print("baseline: GREEN (precondition)")
    rows, fails = [], []
    try:
        for mid, fam, anchor, repl, expect in MUTANTS:
            if fam == "exp":
                assert src.count(anchor) == 1, "%s anchor not unique: %r" % (mid, anchor)
                open(COPY, "w").write(src.replace(anchor, repl))
                rc, out = run([sys.executable, "-u", COPY], ENV)
            else:
                rc, out = run([sys.executable, "-u", SRC], dict(ENV, M318_PATCH=anchor))
                assert "patches applied: 1/1" in out, "%s patch did not land (vacuous)" % mid
            verdict, detail = classify(out, rc, expect)
            if fam == "noop":
                ok, want = verdict == "GREEN", "GREEN (declared NO-OP)"
            else:
                ok, want = verdict == "RED", "RED"
            rows.append((mid, verdict, detail))
            print("%-5s %-8s want=%-22s %s" % (mid, verdict, want, "OK" if ok else "FAIL"))
            if not ok:
                fails.append(mid)
    finally:
        if os.path.exists(COPY):
            os.remove(COPY)
    digest = hashlib.sha256("".join("%s|%s|%s\n" % r for r in rows).encode()).hexdigest()[:16]
    scored = len(MUTANTS) - 1
    print("\n== M318 mutate: %d/%d scored + 1 declared NO-OP, digest %s =="
          % (scored - len(fails), scored, digest))
    if fails:
        print("FAILED mutants: %s" % " ".join(fails))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())