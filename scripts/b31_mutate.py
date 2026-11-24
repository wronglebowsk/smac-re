#!/usr/bin/env python3
"""b31_mutate.py - the mutation harness for rung B31 (`sim/facoracle.py`).

Each mutant patches ONE law in a freshly reloaded module and the harness compares the set of
gate labels that STOP passing against the mutant's DECLARED set. A declared set that comes
out empty is a vacuous gate (trap 24) and the run is red: an assertion that cannot fail on a
real state is a defect, not a gate.

`python3 -u scripts/b31_mutate.py` -> `PASS HARNESS B31: n/n` (digest) or a red list.
"""
import contextlib
import hashlib
import importlib
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# The lint's id table: sim/facoracle's gates are covered by exactly these mutants (the
# descriptive keys in mutate() map 1:1, in order). The harness asserts the counts agree.
MU_IDS = ("MU1", "MU2", "MU3", "MU4", "MU5", "MU6", "MU7", "MU8", "MU9", "MU10")

GATE = re.compile(r"^(ok  |FAIL) (G\d+[a-z]?) (.*)$")


def run(mod):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = mod.main([])
    out = buf.getvalue()
    passed, failed = set(), set()
    for ln in out.splitlines():
        mt = GATE.match(ln)
        if mt:
            (passed if mt.group(1) == "ok  " else failed).add(mt.group(2))
    return rc, passed, failed, out


def mutate(name):
    """Return (module, declared_red) - a fresh module with ONE law broken."""
    m = importlib.import_module("sim.facoracle")
    m = importlib.reload(m)
    declared = set()
    if name == "MU1_bitmap_off":          # decode the wrong byte of the bitmap window
        m.FAC_OFF = 0x8d
        declared = {"G3", "G5", "G7"}
    elif name == "MU2_head_off":          # read the head from the wrong dword
        m.HEAD_OFF = 0x54
        declared = {"G3", "G7"}
    elif name == "MU3_price10":           # the spend by a constant 10, not the recorded 9
        orig = m.transaction
        m.transaction = lambda rec, price=10, add=m.ADD, stamp=True, order="spend-stamp-pop": \
            orig(rec, price=price, add=add, stamp=stamp, order=order)
        declared = {"G4a", "G4c", "G4d", "G4e", "G6c"}
    elif name == "MU4_noadd":             # the round adds nothing
        orig = m.transaction
        m.transaction = lambda rec, price=m.PRICE, add=0, stamp=True, order="spend-stamp-pop": \
            orig(rec, price=price, add=add, stamp=stamp, order=order)
        declared = {"G4a", "G4c", "G4d", "G4e", "G6c"}
    elif name == "MU5_stamp_always":      # stamp the recorded negative (the B30 assumption)
        orig = m.transaction
        m.transaction = lambda rec, price=m.PRICE, add=m.ADD, stamp=False, order="spend-stamp-pop": \
            orig(rec, price=price, add=add, stamp=True, order=order)
        declared = {"G4e"}
    elif name == "MU6_pop_first":         # the rival order becomes the law
        orig = m.transaction
        m.transaction = lambda rec, price=m.PRICE, add=m.ADD, stamp=True, order="spend-stamp-pop": \
            orig(rec, price=price, add=add, stamp=stamp, order="pop-first")
        declared = {"G4d", "G6c"}
    elif name == "MU7_monotonic":         # pretend the bitmap only ever grows
        orig = m.deltas
        m.deltas = lambda samples: [r for r in orig(samples) if not r[8]]
        declared = {"G2", "G3", "G6b", "G7"}
    elif name == "MU8_write_shift":       # the writer writes the bitmap one byte late
        orig = m.apply_bitmap

        def shifted(idx, target_bits, sav=m.SAV):
            sv, b, raw, writes, ov = orig(idx, target_bits, sav)
            return sv, b, raw, [(p, off + 1, v) for (p, off, v) in writes], ov
        m.apply_bitmap = shifted
        declared = {"G5", "G7"}
    elif name == "MU9_nondet":            # a non-deterministic digest
        orig = m._sha
        state = {"n": 0}

        def wobble(rows):
            state["n"] += 1
            return orig(rows)[:-2] + "%02x" % (state["n"] & 0xff)
        m._sha = wobble
        declared = {"G6d", "G7"}
    elif name == "MU10_noop":             # the control: nothing is broken
        declared = set()
    else:
        raise SystemExit("unknown mutant %r" % name)
    return m, declared


def main():
    base_m, _ = mutate("MU10_noop")
    rc0, p0, _f0, _o0 = run(base_m)
    if rc0 != 0:
        print("FAIL HARNESS B31: the baseline does not pass")
        return 1
    names = ["MU1_bitmap_off", "MU2_head_off", "MU3_price10", "MU4_noadd", "MU5_stamp_always",
             "MU6_pop_first", "MU7_monotonic", "MU8_write_shift", "MU9_nondet", "MU10_noop"]
    assert len(MU_IDS) == len(names), "the lint id table drifted from the mutant list"
    rows, bad = [], []
    for nm in names:
        m, declared = mutate(nm)
        rc, passed, failed, out = run(m)
        went_red = sorted(p0 - passed)
        ok = set(went_red) == declared and rc != 0
        if nm == "MU10_noop":
            ok = went_red == [] and rc == 0
        rows.append((nm, sorted(declared), went_red, rc, ok))
        print("%-18s declared=%-28s red=%-28s rc=%d %s"
              % (nm, "{" + ",".join(sorted(declared)) + "}", "{" + ",".join(went_red) + "}",
                 rc, "OK" if ok else "MISMATCH"))
        if not ok:
            bad.append(nm)
            print("  tail: %s" % " | ".join(out.splitlines()[-4:]))
    digest = hashlib.sha256(repr(rows).encode()).hexdigest()[:16]
    print("")
    if bad:
        print("FAIL HARNESS B31: %d/%d mutants match their declared sets: %s"
              % (len(rows) - len(bad), len(rows), bad))
        return 1
    print("PASS HARNESS B31: %d/%d mutants redden exactly their declared sets (NO-OP []), "
          "digest %s" % (len(rows), len(rows), digest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
