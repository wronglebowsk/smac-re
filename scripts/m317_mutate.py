#!/usr/bin/env python3
"""M317 mutation harness: prove every census gate is LOAD-BEARING.

Family 1 (expectation): rewrite ONE instrument literal in a scratch copy,
require the named gate to go red. Family 2 (code): M317_PATCH rewrites real
parsed instructions before measurement - an instrument that never looks at
the bytes cannot survive these. MU16 is a DECLARED NO-OP (prologue register
no gate reads): it must stay GREEN, proving the harness detects decoration.

Scoring: baseline must be green first. RED = rc!=0, final exception is an
AssertionError carrying the declared message (a crash is NOT a red). GREEN
on a scored mutant = FAIL. NO-OP = GREEN required. Digest hashes
name+verdict+detail (labels-only hashing is decoration, #299).

    python3 -u scripts/m317_mutate.py   # stdout -> evidence/m317_mutate.txt
"""
import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "scripts", "m317_engine_decides.py")
COPY = os.path.join(ROOT, "scratch", "_m317_mutant.py")
ENV = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "scripts"))

# (id, family, anchor-or-patch, replacement, expected gate message substring)
MUTANTS = [
    ("MU1", "exp", "SIZE = 14349", "SIZE = 14350", "size drift"),
    ("MU2", "exp", "N_INSNS = 4235", "N_INSNS = 4236", "index n_insns drift"),
    ("MU3", "exp", '{0x52094F: "FUN_005208f0", 0x59DD43: "FUN_0059ce10"}',
     '{0x52094F: "FUN_005208f0"}', "caller set drift"),
    ("MU4", "exp", "N_CALLEES = 41", "N_CALLEES = 40", "distinct callee count"),
    ("MU5", "exp", '{0x557FDF: "0x8",', '{0x557FDF: "0x9",', "M250 site 0x557fdf value drift"),
    ("MU6", "exp", "assert len(stores) == 358", "assert len(stores) == 359", "len(stores) == 359"),
    ("MU7", "exp", "== len(jcc) == 605", "== len(jcc) == 604", "len(jcc) == 604"),
    ("MU8", "exp", '0x556A4A: "0x29",', '0x556A4A: "0x28",', "kind drift at 0x556a4a"),
    ("MU9", "exp", "assert len(back) == 44", "assert len(back) == 43", "len(back) == 43"),
    ("MU10", "exp", '("cmp", "ecx,0x80")', '("cmp", "ecx,0x7f")', "M274 region bound drift"),
    ("MU11", "code", "0x556a4a|call 0x56d690", None, "== 7"),
    ("MU12", "code", "0x557fdf|mov BYTE PTR [ebx+ecx*1+0x94eda8],0x7", None,
     "M250 site 0x557fdf value drift"),
    ("MU13", "code", "0x558b1c|cmp ecx,0x81", None, "M274 region bound drift"),
    ("MU14", "code", "0x556a47|push 0x2a", None, "kind drift at 0x556a4a"),
    ("MU15", "code", "0x558b25|jl 0x558b30", None, "len(back) == 44"),
    ("MU16", "noop", "0x556690|push ebx", None, None),
]


def run(cmd_args, env):
    p = subprocess.run(cmd_args, cwd=ROOT, env=env, capture_output=True, text=True, timeout=300)
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
    for mid, fam, anchor, repl, expect in MUTANTS:
        if fam == "exp":
            assert src.count(anchor) == 1, "%s anchor not unique: %r" % (mid, anchor)
            open(COPY, "w").write(src.replace(anchor, repl))
            rc, out = run([sys.executable, "-u", COPY], ENV)
        else:
            rc, out = run([sys.executable, "-u", SRC], dict(ENV, M317_PATCH=anchor))
            assert "patches applied: 1/1" in out, "%s patch did not land (vacuous)" % mid
        verdict, detail = classify(out, rc, expect)
        if fam == "noop":
            ok = verdict == "GREEN"
            want = "GREEN (declared NO-OP)"
        else:
            ok = verdict == "RED"
            want = "RED"
        rows.append((mid, verdict, detail))
        print("%-5s %-8s want=%-22s %s" % (mid, verdict, want, "OK" if ok else "FAIL"))
        if not ok:
            fails.append(mid)
    if os.path.exists(COPY):
        os.remove(COPY)
    digest = hashlib.sha256("".join("%s|%s|%s\n" % r for r in rows).encode()).hexdigest()[:16]
    scored = len(MUTANTS) - 1
    print("\n== M317 mutate: %d/%d scored + 1 declared NO-OP, digest %s =="
          % (scored - len(fails), scored, digest))
    if fails:
        print("FAILED mutants: %s" % " ".join(fails))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())