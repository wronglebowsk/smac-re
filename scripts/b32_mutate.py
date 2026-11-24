#!/usr/bin/env python3
"""b32_mutate.py - the mutation harness for rung B32 (`sim/unitoracle.py`).

Each mutant patches ONE law in a freshly reloaded module and the harness compares the set of
gate labels that STOP passing against the mutant's DECLARED set. A declared set that comes out
empty is a vacuous gate (trap 24) and the run is red: an assertion that cannot fail on a real
state is a defect, not a gate.

`python3 -u scripts/b32_mutate.py` -> `PASS HARNESS B32: n/n` (digest) or a red list.
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

MU_IDS = ("MU1", "MU2", "MU3", "MU4", "MU5", "MU6", "MU7", "MU8", "MU9", "MU10", "MU11",
          "MU12", "MU13")

GATE = re.compile(r"^(ok  |FAIL) (G\d+[a-z]?) (.*)$")

NAMES = ("MU1_rows_anchor", "MU2_head_off", "MU3_all_facility", "MU4_floor_shift",
         "MU5_after_head", "MU6_byte_shift", "MU7_swap_mapper", "MU8_nondet",
         "MU9_drop_losses", "MU10_selfcheck", "MU11_m349_table", "MU12_noop",
         "MU13_same_sample")


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
    m = importlib.import_module("sim.unitoracle")
    m = importlib.reload(m)
    declared = set()
    if name == "MU1_rows_anchor":           # the pinned rows anchor drifts
        m.ROWS_ANCHOR = "0000000000000000"
        declared = {"G10"}
    elif name == "MU2_head_off":            # read the head from the wrong dword
        m.HEAD_OFF = 0x54
        declared = {"G1", "G2", "G3", "G6", "G7", "G8", "G10"}
    elif name == "MU3_all_facility":        # the unit decode never happens (B31's reading)
        m.decode = lambda head: ("FACILITY", head) if head >= 0 else ("FACILITY", -head)
        declared = {"G2", "G3", "G6", "G7", "G8", "G10"}
    elif name == "MU4_floor_shift":         # divide by 8 with a FLOOR, not truncation
        m.trunc8 = lambda item: item // 8
        declared = {"G5", "G10"}
    elif name == "MU5_after_head":          # the rival shape becomes the law
        orig = m.score
        m.score = lambda rows, head_col=4: orig(rows, 4)
        declared = {"G4"}
    elif name == "MU6_byte_shift":          # decode the bitmap one byte late
        m.FBASE = 0x8d
        declared = {"G1", "G6", "G7", "G10"}
    elif name == "MU7_swap_mapper":         # swapped byte/mask orientation becomes the law
        m.mapper = m.mapper_swapped
        declared = {"G3", "G5", "G6", "G7", "G8", "G10"}
    elif name == "MU8_nondet":              # a non-deterministic digest
        orig = m._sha
        state = {"n": 0}

        def wobble(rows):
            state["n"] += 1
            return orig(rows)[:-2] + "%02x" % (state["n"] & 0xff)
        m._sha = wobble
        declared = {"G9", "G10"}
    elif name == "MU9_drop_losses":         # the losses vanish from the rows
        orig = m.measure

        def lossy(samples=None):
            return [r[:15] + ((),) + r[16:] for r in orig(samples)]
        m.measure = lossy
        declared = {"G8", "G10"}
    elif name == "MU10_selfcheck":          # the replay compares the prediction to itself
        def rigged(rows):
            out = []
            for r in rows:
                pred = r[16] if r[9] is None else None
                out.append((r[0], r[2], r[6], r[7], pred, pred, ()))
            return out
        m.replay = rigged
        declared = {"G6", "G7"}
    elif name == "MU11_m349_table":         # the imported M349 table is not M349's
        class Fake:
            UNIVERSE = [-2]

            @staticmethod
            def decode(h):
                return ("FACILITY", h)
        m.m349_table = lambda: Fake
        declared = {"G2"}
    elif name == "MU13_same_sample":        # before and after read the same sample
        orig = m.measure

        def same(samples=None):
            return [r[:17] + (r[16],) for r in orig(samples)]
        m.measure = same
        declared = {"G1", "G6", "G7", "G10"}
    elif name == "MU12_noop":               # the control: nothing is broken
        declared = set()
    else:
        raise SystemExit("unknown mutant %r" % name)
    return m, declared


def main():
    base_m, _ = mutate("MU12_noop")
    rc0, p0, _f0, _o0 = run(base_m)
    if rc0 != 0:
        print("FAIL HARNESS B32: the baseline does not pass")
        return 1
    assert len(MU_IDS) == len(NAMES), "the lint id table drifted from the mutant list"
    rows, bad = [], []
    for nm in NAMES:
        m, declared = mutate(nm)
        rc, passed, failed, out = run(m)
        went_red = sorted(p0 - passed)
        ok = set(went_red) == declared and rc != 0
        if nm == "MU12_noop":
            ok = went_red == [] and rc == 0
        rows.append((nm, sorted(declared), went_red, rc, ok))
        print("%-18s declared=%-34s red=%-34s rc=%d %s"
              % (nm, "{" + ",".join(sorted(declared)) + "}", "{" + ",".join(went_red) + "}",
                 rc, "OK" if ok else "MISMATCH"))
        if not ok:
            bad.append(nm)
    digest = hashlib.sha256(repr(rows).encode()).hexdigest()[:16]
    print("")
    print("DIGEST %s mutants=%d" % (digest, len(rows)))
    if bad:
        print("FAIL HARNESS B32: %d/%d mutants" % (len(rows) - len(bad), len(rows)))
        for nm in bad:
            print("  red: %s" % nm)
        return 1
    print("PASS HARNESS B32: %d/%d" % (len(rows), len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
