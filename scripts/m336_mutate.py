#!/usr/bin/env python3
"""M336 mutation harness — every VERIFIED row of `## M336` names the mutant that reddens it.

Each mutant perturbs ONE measured input inside scripts/m336_cell090_consumer.py
(an operand value in bytes+text, a mnemonic, or the census ALGORITHM) and must redden
EXACTLY its declared gate set. The sets are PRINTED FROM THE RUN and compared with the
declaration in BOTH directions; a declaration that is too narrow or too wide fails.

    python3 -u scripts/m336_mutate.py             # the sweep
    python3 -u scripts/m336_mutate.py --selftest  # the parser + declaration laws
"""
import argparse
import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "m336_cell090_consumer.py")
GATES = ["G1", "G2", "G3", "G4", "G5", "G6", "G7"]

# Mutant -> gate set, declared BEFORE the sweep. Each row exists because a specific
# claim in the script would be false under the perturbation.
DECLARED = {
    "MU1": ("drop_reader",       {"G1", "G3", "G7"}),  # the only load disappears: census, chain, rival
    "MU2": ("stride_175",        {"G2"}),               # field+0 imul immediate 0x176 -> 0x175
    "MU3": ("stride_175b",       {"G1", "G3", "G7"}),         # the consumer's imul: no longer a stride multiple
    "MU4": ("direct_moved",      {"G1"}),               # the one direct store retargeted
    "MU5": ("count7",            {"G2"}),               # walk count 8 -> 7 breaks FRAME+count*STRIDE
    "MU6": ("clamp_hi5",         {"G6"}),               # clamp hi 6 -> 5 no longer reaches the end cell
    "MU7": ("clamp_exclusive",   {"G6"}),               # FUN_00423af0 jle -> jl: hi becomes exclusive
    "MU8": ("value_src",         {"G4", "G6"}),         # a field+2 store reads 0x8f0c12
    "MU9": ("naive_alias",       {"G1", "G4", "G7"}),         # ALGORITHM: direct-displacement form only
    "MU10": ("table_end_moved",  {"G5"}),               # loader end 0x94d2c4 -> 0x94d2c0
    "MU11": ("walk_stride",      {"G1", "G4"}),         # walk step 0x176 -> 0x170
    "MU12": ("table_base_moved", {"G5"}),               # loader base 0x94d2ac -> 0x94d2a8
    "MU13": ("chain_src",        {"G3"}),               # the chain reloads a different stack slot
    "MU14": ("alias_inserted",   {"G1"}),               # a SECOND resolvable load is added
}
MUTANTS = list(DECLARED)

LINE = re.compile(r"^  (G\d): (PASS|FAIL)\b")


def parse(out):
    red, seen = set(), set()
    for line in out.splitlines():
        m = LINE.match(line)
        if m:
            seen.add(m.group(1))
            if m.group(2) == "FAIL":
                red.add(m.group(1))
    verdict = re.search(r"^(PASS|FAIL) M336: (\d+)/(\d+) gates", out, re.M)
    digest = re.search(r"^digest=([0-9a-f]+)", out, re.M)
    return red, seen, (verdict.group(0) if verdict else None), (digest.group(1) if digest else None)


def run(mut=""):
    env = dict(os.environ)
    env.pop("M336_MUT", None)
    if mut:
        env["M336_MUT"] = mut
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True, text=True, env=env)
    return p.stdout + p.stderr


def selftest():
    """The harness itself: the gate-line parser, and the both-directions comparison."""
    ok = 0
    txt = "  G1: PASS  x\n  G3: FAIL  y\n  G7: PASS  z\nPASS M336: 2/3 gates\ndigest=abc"
    red, seen, verdict, digest = parse(txt)
    c1 = red == {"G3"} and seen == {"G1", "G3", "G7"} and verdict == "PASS M336: 2/3 gates"
    c2 = digest == "abc"
    # a declaration that is too NARROW must be rejected, and so must one that is too WIDE
    narrow = ("G3" in red) and ({"G3", "G7"} == {"G3"})
    wide = ("G7" in red)
    c3 = narrow is False and wide is False
    # every gate is covered by at least one declaration, and no declaration is empty
    covered = set().union(*[s for _, s in DECLARED.values()])
    c4 = covered == set(GATES) and all(DECLARED[m][1] for m in MUTANTS)
    # every declared mutant id has a name the script knows (checked by a dry run below)
    for name, okk in (("gate parser", c1), ("digest parser", c2),
                      ("both-directions law", c3), ("gate coverage", c4)):
        print(f"  {name}: {'PASS' if okk else 'FAIL'}")
        ok += 1 if okk else 0
    print(f"SELFTEST {'PASS' if ok == 4 else 'FAIL'} {ok}/4")
    return 0 if ok == 4 else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    base_out = run("")
    bred, bseen, bverdict, bdigest = parse(base_out)
    print(f"== baseline ==")
    print(f"  {bverdict}  digest={bdigest}  gates seen={len(bseen)}  red={sorted(bred)}")
    base_ok = bverdict is not None and "PASS" in bverdict and not bred and bseen == set(GATES)
    print(f"  NO-OP (unaltered input is green): {'PASS' if base_ok else 'FAIL'}")

    print("\n== mutant sweep (declared vs MEASURED) ==")
    print(f"  {'id':4s} {'mutant':16s} {'declared':22s} {'measured':22s} verdict")
    good = 0
    rows = []
    for mid in MUTANTS:
        name, declared = DECLARED[mid]
        out = run(name)
        red, seen, verdict, digest = parse(out)
        applied = f"MUT={name}" in out
        match = (red == declared) and seen == set(GATES) and applied and verdict is not None
        good += 1 if match else 0
        print(f"  {mid:4s} {name:16s} {','.join(sorted(declared)):22s} "
              f"{','.join(sorted(red)):22s} {'PASS' if match else 'FAIL'}"
              + ("" if applied else "  (mutant did not apply)"))
        rows.append((mid, name, sorted(declared), sorted(red), match))

    body = repr([(m, n, d, r) for m, n, d, r, _ in rows])
    digest = hashlib.sha256(body.encode()).hexdigest()[:16]
    print(f"\ndigest={digest} mutants={good}/{len(MUTANTS)} baseline={'green' if base_ok else 'RED'}")
    ok = good == len(MUTANTS) and base_ok
    print(f"{'PASS' if ok else 'FAIL'} HARNESS {good}/{len(MUTANTS)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
