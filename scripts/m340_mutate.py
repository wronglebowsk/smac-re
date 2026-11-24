#!/usr/bin/env python3
"""M340 mutation harness: every VERIFIED row of `NAMED ## M340` names the mutant
that reddens it, and the declared gate sets are MEASURED in both directions.

Each mutant is applied by `scripts/m340_pref_admission.py` itself (env
M340_MUT, byte-faithful: bytes AND disassembly text change together;
M340_ALG=ALG1 is the classifier mutant: treat every cmp constant as a value
bound). One run per mutant, declared == measured, and every gate must be
reddened by at least one mutant.

    python3 -u scripts/m340_mutate.py             # score
    python3 -u scripts/m340_mutate.py --selftest   # patch/parser checks
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACC = os.path.join(ROOT, "scripts", "m340_pref_admission.py")
EVID = os.path.join(ROOT, "evidence", "m340_mutate.txt")

DECL = {
    "MU1": {"G1"},        # Difficulty key immediate -> Language's key
    "MU2": {"G2", "G3"}, # a jcc inside the store window
    "MU3": {"G3"},        # pop ebp -> pop eax on the return path
    "MU4": {"G4", "G5"},  # a value-space bound (5) appears in the atoi (G5 reads the classifier)
    "MU5": {"G5"},        # Language's bound 4 -> 2 (positive control dies)
    "MU6": {"G7"},        # pref-fed reader's table base displaced one dword
    "MU7": {"G1", "G2"},  # the pref store lands on 0x92bdec
    "MU8": {"G6"},        # the ladder's own loop bound 6 -> 7
    "MU9": {"G3"},        # the wrapper's downstream call retargeted (chain identity)
    "MU10": {"G1"},       # lpDefault moves off the itoa(0) buffer
    "MU11": {"G1"},       # the profile read's size argument leaves the argc-6 window
    "ALG1": {"G4", "G5"},  # classifier mutant: every cmp constant is a bound
}
GATES = ["G1", "G2", "G3", "G4", "G5", "G6", "G7"]


def run(mut=None, alg=None):
    env = dict(os.environ)
    env.pop("M340_MUT", None)
    env.pop("M340_ALG", None)
    if mut:
        env["M340_MUT"] = mut
    if alg:
        env["M340_ALG"] = alg
    env["M340_NO_EVID"] = "1"
    p = subprocess.run([sys.executable, "-u", ACC], capture_output=True,
                       text=True, env=env)
    rows = {}
    for m in re.finditer(r"^(G\d)\s+(PASS|FAIL)\b", p.stdout, re.M):
        rows[m.group(1)] = m.group(2)
    return rows, p


def main():
    out = []
    fails = []

    def say(s):
        print(s)
        out.append(s)

    base, p = run()
    if not base or any(v != "PASS" for v in base.values()):
        say("BASELINE NOT GREEN: %s" % base)
        say(p.stdout[-800:])
        return 1
    say("NO-OP      red=%s  (%s)" % (sorted(k for k, v in base.items() if v == "FAIL") or "[]",
                                    "all %d gates green" % len(base)))

    measured = {}
    for mut, want in DECL.items():
        rows, p2 = run(mut if not mut.startswith("ALG") else None,
                       alg=mut if mut.startswith("ALG") else None)
        red = sorted(k for k, v in rows.items() if v == "FAIL")
        measured[mut] = set(red)
        ok = set(red) == set(want)
        say("%-5s red=%-14s want=%-12s %s" % (mut, red, sorted(want), "OK" if ok else "MISMATCH"))
        if not ok:
            fails.append(mut)
            say(p2.stdout[-500:])

    covered = set()
    for s in measured.values():
        covered |= s
    missing = [g for g in GATES if g not in covered]
    say("coverage: gates reddened at least once = %d/%d %s"
        % (len(GATES) - len(missing), len(GATES), missing or ""))
    if missing:
        fails.append("COVERAGE")

    digest = __import__("hashlib").sha256(
        "|".join("%s:%s" % (m, ",".join(sorted(s))) for m, s in sorted(measured.items())).encode()
    ).hexdigest()[:16]
    say("digest mutants %s" % digest)
    if fails:
        say("FAIL HARNESS M340: %s" % fails)
        with open(EVID, "w") as f:
            f.write("\n".join(out) + "\n")
        return 1
    say("PASS HARNESS M340: %d/%d mutants, all %d gates covered, NO-OP []"
        % (len(DECL), len(DECL), len(GATES)))
    with open(EVID, "w") as f:
        f.write("\n".join(out) + "\n")
    return 0


def selftest():
    import importlib.util
    spec = importlib.util.spec_from_file_location("acc", ACC)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ins = mod.load()
    for mut in DECL:
        setattr(mod, "MUT", mut if not mut.startswith("ALG") else "")
        m2 = mod.apply_mut(mod.load())
        assert len(m2) == len(ins), mut
    print("SELFTEST OK: %d mutants applied over %d instructions" % (len(DECL), len(ins)))
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main())
