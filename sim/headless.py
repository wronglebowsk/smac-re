"""sim.headless - rung B6: the headless run (BUILD_SPINE.md).

Loads a .SAV + a .MP + the alpha rules, presses TURN COMPLETE N times through the B3 engine
(sim.turn), runs the B4 economy (sim.economy) once per round for every faction that owns
bases, and dumps a canonical state document. NO /proc, NO gdb, NO Wine, NO game binary.

The round model is deliberately the SETTLED machinery only:
  * the turn walk and the year edge are B3 (67/67 on the recorded trace);
  * gross/upkeep/net and the energy floor are B4 (9/9 on the recorded idle trace);
  * units re-charge their movement budget each round (0x51f730 REFRESH, live-proven M37)
    and never move: R1 has no AI. That is an ASSUMED marker, not a silent omission.

Acceptance (BUILD_SPINE B6): the command exits 0, writes a stable dump, increments the
year per the B3 model, and is deterministic - two runs, identical sha256.
"""
import argparse
import hashlib
import json
import os
import sys

from . import base as sobase
from . import map as somap
from . import economy as soecon
from . import rules as sorules
from . import save as sosave
from . import turn as soturn

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_RULES = os.path.join(ROOT, "data", "alpha.json")
SCHEMA = "smac-sim-state/1"
ASSUMED = [
    "initial per-faction energy = 0 (the .SAV faction-energy read is not pinned by a trace)",
    "units re-charge the 6-MP budget every round (0x51f730 REFRESH, M37) and never move: R1 has no AI",
    "research/gift/terraform ledger = 0 every round (the idle-round shape B4 verified)",
]


def simulate(sav_path, map_path, rules_path, turns):
    sv = sosave.parse(sav_path)
    mp = somap.parse(map_path)
    rules = sorules.load(rules_path)
    table = soecon.upkeep_table(rules)
    bases = sobase.from_save(sv)
    energy = {f: 0 for f in sorted({b["owner"] for b in bases})}
    eng = soturn.Engine(sv.year, human=sv.own_player)
    spent = {u["i"]: 0 for u in sv.units}
    history = []
    for r in range(turns):
        seq = eng.press()
        econ = []
        for fac in sorted(energy):
            fr = soecon.faction_round(fac, bases, table)
            before = energy[fac]
            energy[fac] = soecon.apply_round(before, fr["net"])
            econ.append({"faction": fac, "gross": fr["gross"], "upkeep": fr["upkeep"],
                         "net": fr["net"], "energy_before": before, "energy_after": energy[fac]})
        spent = {i: 0 for i in spent}                      # REFRESH (ASSUMED, see module doc)
        history.append({"round": r, "engine_states": [list(s) for s in seq],
                        "year": eng.year, "economy": econ})
    state = {"schema": SCHEMA,
            "inputs": {"sav": os.path.basename(sav_path), "map": os.path.basename(map_path),
                       "rules": os.path.basename(rules_path)},
            "map": {"width": mp.width, "height": mp.height},
            "save": {"year_start": sv.year, "own_player": sv.own_player,
                     "n_units": sv.n_units, "n_bases": sv.n_bases,
                     "width": sv.width, "height": sv.height},
            "turns": turns,
            "engine": {"human": eng.human, "order": eng.order, "year_after": eng.year_after},
            "assumed": ASSUMED,
            "history": history,
            "final": {"cur": eng.cur, "tf": eng.tf, "year": eng.year,
                      "energy": {str(f): energy[f] for f in sorted(energy)},
                      "mp_spent": {str(i): spent[i] for i in sorted(spent)}},
            }
    blob = json.dumps(state, sort_keys=True, separators=(",", ":"))
    return sv, eng, state, blob


def validate(sv, eng, state, turns):
    g = []
    g.append(("year-increments-per-B3",
              eng.year - sv.year == turns,
              "year %d -> %d over %d presses (delta %d)" % (sv.year, eng.year, turns,
                                                             eng.year - sv.year)))
    g.append(("ends-in-human-phase", (eng.cur, eng.tf) == (sv.own_player, 0),
              "final (cur, tf) = (%d, %d), human = %d" % (eng.cur, eng.tf, sv.own_player)))
    owners = sorted({b["owner"] for b in sobase.from_save(sv)})
    g.append(("economy-every-round-per-faction",
              all(len(h["economy"]) == len(owners) for h in state["history"]),
              "%d factions x %d rounds" % (len(owners), turns)))
    g.append(("energy-floor-zero",
              all(e["energy_after"] >= 0 for h in state["history"] for e in h["economy"]),
              "apply_round floors at 0 (0x5208f0 tail)"))
    return g


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sim.headless")
    ap.add_argument("--sav", required=True)
    ap.add_argument("--map", dest="map_path", required=True)
    ap.add_argument("--rules", default=DEFAULT_RULES)
    ap.add_argument("--turns", type=int, default=10)
    ap.add_argument("--dump", default="sim_state.json")
    a = ap.parse_args(argv)
    sv, eng, state, blob = simulate(a.sav, a.map_path, a.rules, a.turns)
    bad = []
    for name, ok, detail in validate(sv, eng, state, a.turns):
        print("  %s %s  %s" % ("ok  " if ok else "BAD ", name, detail))
        if not ok:
            bad.append(name)
    if bad:
        print("FAIL B6: %d/%d gates failed: %s" % (len(bad), 4, "; ".join(bad)))
        return 1
    with open(a.dump, "w") as fh:
        fh.write(blob)
    sha = hashlib.sha256(blob.encode()).hexdigest()
    print("PASS B6: headless run %d turns, year %d -> %d, dump %s (%d B, sha256 %s)"
          % (a.turns, sv.year, eng.year, a.dump, len(blob), sha[:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
