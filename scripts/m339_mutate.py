#!/usr/bin/env python3
"""M339 mutation harness — every VERIFIED row of `## M339` names a mutant here.

    python3 -u scripts/m339_mutate.py            # score every mutant
    python3 -u scripts/m339_mutate.py --selftest # 3 self-checks of the scorer

A mutant is SCORED when the run's red-gate set CONTAINS the gates the row cites
(isolation is printed, not required: a byte that moves a cell legitimately
changes two gates). MISMATCH = the mutant ran but none of its cited gates went
red. CRASH = the byte patch did not apply (the old-bytes assert fired).
"""
import hashlib
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(HERE, "m339_modal_runner.py")

MUTANTS = [
    ("MU1", ["G1"], "vtbl+0x170 -> +0x174 (the prepare slot)"),
    ("MU2", ["G1"], "jne after the prepare test -> je (the -1 path is skipped)"),
    ("MU3", ["G2", "G3"], "result cell obj+0xa40 -> obj+0xa44 (the seeded field)"),
    ("MU4", ["G4"], "ret 0x8 -> ret 0x4 (arity disagrees with the caller pushes)"),
    ("MU5", ["G5"], "the jge store target 0x985aec -> 0x985af0"),
    ("MU6", ["G5"], "faction stride 0x20bc -> 0x20b8 (bound arithmetic breaks)"),
    ("MU7", ["G6"], "plant ds:0x985aec inside the runner (0x698d0c -> 0x985aec)"),
    ("MU8", ["G5"], "seed slot obj+0xa44 -> obj+0xa40 (seed == result cell)"),
    ("MU9", ["G0"], "2-byte xor re-cut as a 5-byte mov (extent / overlap)"),
    ("MU10", ["G4"], "one call site retargeted (0x5f1394 -> 0x5f1395): census 93"),
    ("MU11", ["G5"], "the faction store's base ecx -> edx (store not gated by arithmetic)"),
    ("MU12", ["G5"], "the seeded object is no longer the call's receiver"),
    ("ALG_A1", ["G2"], "classifier mutant: ignore the fallthrough exit"),
]

RED = re.compile(r"red: (\[[^\]]*\])")


def run(env_extra):
    env = dict(os.environ)
    env.update(env_extra)
    p = subprocess.run([sys.executable, "-u", MAIN], capture_output=True, text=True, env=env)
    out = p.stdout
    m = RED.search(out)
    red = eval(m.group(1)) if m else []
    verdict = [ln for ln in out.splitlines() if ln.startswith(("PASS M339", "FAIL M339",
                                                              "Traceback", "AssertionError"))]
    crash = p.returncode != 0 and not m
    digest = [ln for ln in out.splitlines() if ln.startswith("digest=")]
    return {"rc": p.returncode, "red": red, "crash": crash, "out": out,
            "verdict": verdict[-1] if verdict else "(no verdict)",
            "digest": digest[-1] if digest else "(no digest)"}


def main():
    if "--selftest" in sys.argv:
        # 1 the scorer reads a red list, 2 it is set-based, 3 a clean run is empty
        a = {"x": "FAIL M339: 6/7 gates (red: ['G3'])"}
        assert eval(RED.search(a["x"]).group(1)) == ["G3"]
        assert set(["G2", "G3"]) & set(eval(RED.search(a["x"]).group(1)))
        assert not eval(RED.search("1/1 gates (red: [])").group(1))
        print("SELFTEST 3/3: scorer reads red lists, matches on sets, empty red = pass")
        return 0

    base = run({})
    print("NO-OP  %s  %s" % (base["verdict"], base["digest"]))
    ok0 = base["rc"] == 0 and base["red"] == []
    rows, bad = [], []
    for mid, want, desc in MUTANTS:
        key = "M339_ALG" if mid.startswith("ALG") else "M339_MUT"
        r = run({key: mid.split("_", 1)[1] if "_" in mid else mid})
        scored = (not r["crash"]) and set(want) <= set(r["red"])
        rows.append((mid, "SCORED" if scored else ("CRASH" if r["crash"] else "MISMATCH"),
                     want, r["red"], desc))
        if not scored:
            bad.append(mid)
        print("%-4s %-8s want=%s red=%s  %s" % (mid, rows[-1][1], want, r["red"], desc))
    blob = "\n".join("%s %s %s %s" % (r[0], r[1], r[2], r[3]) for r in rows)
    dg = hashlib.sha256(blob.encode()).hexdigest()[:16]
    print("\nscored %d/%d  MISMATCH %d CRASH %d  digest=%s" %
          (len(rows) - len(bad), len(rows), len([r for r in rows if r[1] == "MISMATCH"]),
           len([r for r in rows if r[1] == "CRASH"]), dg))
    if not ok0 or bad:
        print("HARNESS FAIL: noop_ok=%s bad=%s" % (ok0, bad))
        return 1
    print("HARNESS PASS: %d/%d scored" % (len(rows), len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
