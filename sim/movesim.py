"""sim.movesim - rung B7: the move slice (BUILD_SPINE.md).

R2's first executable piece: a .SAV's OWN unit records walk the recorded M27 gesture (dir=1,
east, the trace's only direction) under the B5 economy (sim/units: 3 MP per tile, 6 MP per
round, FUN_005acc00 admits iff total-spent>0), while the B3 engine turns and the B4 economy
runs. The trace's unit indices 117-120 belong to a different save's record array, so parity
here is on the GESTURE SEMANTICS (delta, cost, refusal), not on those indices - stated in the
dump's `assumed`, not hidden.

NO /proc, NO gdb, NO Wine. Save-restore of unit positions across a load is NOT modeled
(no writer decoded) - declared ASSUMED.
"""
import argparse
import hashlib
import json
import os
import sys

from . import base as sobase
from . import economy as soecon
from . import map as somap
from . import rules as sorules
from . import save as sosave
from . import turn as soturn
from . import units as sounits

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_RULES = os.path.join(ROOT, "data", "alpha.json")
SCHEMA = "smac-sim-move/1"
ASSUMED = [
    "unit records come from the .SAV's own array (sim/save); a save-LOAD restoring positions is "
    "not modeled (the restore is a kernel write - M106 - no ring-3 writer to copy)",
    "the gesture is the M27 trace's dir=1 east press, applied to EVERY unit of the save (the "
    "trace's own units 117-120 exist in a different save with a larger record array)",
    "per-tile cost is uniform 3 MP and budget 6/round (sim.units ASSUMED, queued census picks)",
]


def simulate(sav_path, map_path, rules_path, turns, presses=3):
    sv = sosave.parse(sav_path)
    mp = somap.parse(map_path)
    rules = sorules.load(rules_path)
    table = soecon.upkeep_table(rules)
    bases = sobase.from_save(sv)
    energy = {f: 0 for f in sorted({b["owner"] for b in bases})}
    eng = soturn.Engine(sv.year, human=sv.own_player)
    us = {u["i"]: sounits.Unit(u["i"], u["x"], u["y"], faction=u["owner"])
          for u in sv.units}
    history = []
    for r in range(turns):
        seq = eng.press()
        econ = []
        for fac in sorted(energy):
            fr = soecon.faction_round(fac, bases, table)
            before = energy[fac]
            energy[fac] = soecon.apply_round(before, fr["net"])
            econ.append({"faction": fac, "gross": fr["gross"], "upkeep": fr["upkeep"],
                         "net": fr["net"], "energy_before": before,
                         "energy_after": energy[fac]})
        moves = []
        for i in sorted(us):
            u = us[i]
            u.spent = 0                      # REFRESH (0x51f730, M37) - ASSUMED in headless too
            for p in range(presses):
                if not u.can_act():
                    moves.append({"unit": i, "press": p, "accepted": False,
                                  "pos": [u.x, u.y], "spent": u.spent})
                    continue
                got = u.step(1, mp.width, mp.height)
                moves.append({"unit": i, "press": p, "accepted": got is not None,
                              "pos": [u.x, u.y] if got is None else list(got),
                              "spent": u.spent})
        history.append({"round": r, "engine_states": [list(s) for s in seq], "year": eng.year,
                        "economy": econ, "moves": moves})
    state = {"schema": SCHEMA,
             "inputs": {"sav": os.path.basename(sav_path), "map": os.path.basename(map_path),
                        "rules": os.path.basename(rules_path)},
             "map": {"width": mp.width, "height": mp.height},
             "save": {"year_start": sv.year, "own_player": sv.own_player,
                      "n_units": sv.n_units, "n_bases": sv.n_bases},
             "turns": turns, "presses_per_unit_per_round": presses,
             "gesture": {"dir": 1, "delta": list(sounits.delta(1)), "step_mp": sounits.STEP_MP,
                         "budget": sounits.MP_PER_TURN},
             "assumed": ASSUMED,
             "history": history,
             "final": {"cur": eng.cur, "tf": eng.tf, "year": eng.year,
                       "energy": {str(f): energy[f] for f in sorted(energy)},
                       "units": {str(i): [us[i].x, us[i].y, us[i].spent] for i in sorted(us)}},
             }
    blob = json.dumps(state, sort_keys=True, separators=(",", ":"))
    return sv, mp, eng, us, state, blob


def validate(sv, mp, eng, us, state, turns, presses):
    g = []
    g.append(("year-increments-per-B3", eng.year - sv.year == turns,
              "year %d -> %d over %d presses" % (sv.year, eng.year, turns)))
    g.append(("ends-in-human-phase", (eng.cur, eng.tf) == (sv.own_player, 0),
              "final (cur, tf) = (%d, %d)" % (eng.cur, eng.tf)))
    ok_delta, ok_budget, n_acc, n_ref = True, True, 0, 0
    for h in state["history"]:
        by_unit = {}
        for m in h["moves"]:
            by_unit.setdefault(m["unit"], []).append(m)
        for i, ms in by_unit.items():
            prev = None
            for m in ms:
                if m["accepted"]:
                    n_acc += 1
                    if prev is not None:
                        dx = (m["pos"][0] - prev[0]) % mp.width
                        if dx != 2:
                            ok_delta = False
                    prev = m["pos"]
                else:
                    n_ref += 1
            acc = sum(1 for m in ms if m["accepted"])
            spent_end = ms[-1]["spent"]
            want_acc = min(presses, sounits.MP_PER_TURN // sounits.STEP_MP)
            if not (acc == want_acc and spent_end == acc * sounits.STEP_MP):
                ok_budget = False
    g.append(("press-delta-is-trace-east", ok_delta,
              "%d accepted presses all moved by (+2,0) mod width %d" % (n_acc, mp.width)))
    g.append(("budget-exhausts-at-2-presses", ok_budget and n_ref > 0,
              "%d accepted / %d refused presses; every unit accepted exactly %d then refused "
              "(spent == 3*accepted)" % (n_acc, n_ref,
                                         sounits.MP_PER_TURN // sounits.STEP_MP)))
    return g


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sim.movesim")
    ap.add_argument("--sav", required=True)
    ap.add_argument("--map", dest="map_path", required=True)
    ap.add_argument("--rules", default=DEFAULT_RULES)
    ap.add_argument("--turns", type=int, default=5)
    ap.add_argument("--presses", type=int, default=3)
    ap.add_argument("--dump", default="sim_move_state.json")
    a = ap.parse_args(argv)
    sv, mp, eng, us, state, blob = simulate(a.sav, a.map_path, a.rules, a.turns, a.presses)
    bad = []
    for name, ok, detail in validate(sv, mp, eng, us, state, a.turns, a.presses):
        print("  %s %s  %s" % ("ok  " if ok else "BAD ", name, detail))
        if not ok:
            bad.append(name)
    if bad:
        print("FAIL B7: %d/%d gates failed: %s" % (len(bad), 4, "; ".join(bad)))
        return 1
    with open(a.dump, "w") as fh:
        fh.write(blob)
    sha = hashlib.sha256(blob.encode()).hexdigest()
    print("PASS B7: move slice %d turns x %d presses, units %d, year %d -> %d, dump %s "
          "(%d B, sha256 %s)" % (a.turns, a.presses, sv.n_units, sv.year, eng.year, a.dump,
                                 len(blob), sha[:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
