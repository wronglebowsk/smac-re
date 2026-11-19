"""sim.composedmove - rung B25 (BUILD_SPINE.md §B25): the MOVE leg made PERSISTENT.

B7 pressed the recorded M27 gesture (dir=1 east = +2 x, 3 MP per tile, 6 MP per round, the
third press refused by FUN_005acc00's total-spent>0) on model objects and DECLARED the gap
this rung closes: "save-restore of unit positions is NOT simulated (no writer modeled)"
(NAMED.md §B7, dump `smac-sim-move/1` assumed[0]). B8 (NAMED §B8) proved the container
round-trips and that a unit record's x/y are MODELED bytes. Here the mover is folded through
the writer: every round the press starts from the tile the CONTAINER holds, and the round's
moved tiles go back through `savewriter.build_image`.

Two things this rung measures rather than assumes:
  * the WRAP MODULUS. B7 wrapped by `sim/map.py`'s width for `planet.MP` (80). The save's OWN
    header says 64x64, and `sim/save.py::_unit_ok` rejects a unit record whose tile is
    outside the container's grid, so the two moduli are not interchangeable. Both are RUN
    here and the parser's own `found_units` arbitrates (G5).
  * whether the container is the live channel at all. The falsifier rewrites one unit's tile
    IN THE IMAGE ONLY, between rounds, and never touches model state (G6). A mover that reads
    its tiles from the model - B7's actual shape - cannot see it.

The MP/spent word stays MODEL state: no claim is made that the container carries it (B7's
declared ASSUMED line about the 0x51f730 per-round refresh is unchanged here).

No /proc, no gdb, no Wine, no game-binary load.
"""
import argparse
import hashlib
import os
import struct
import sys

from . import composedturn as soct
from . import map as somap
from . import movesim as somv
from . import save as sosave
from . import savewriter as sow
from . import turn as soturn
from . import units as sounits

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SAV = os.path.join(ROOT, "programs", "saves", "m54b_clean.SAV")
DEFAULT_MAP = os.path.join(ROOT, "programs", "maps", "planet.MP")
DEFAULT_RULES = os.path.join(ROOT, "data", "alpha.json")

TURNS = 4
PRESSES = 3
DIR_EAST = 1                    # the M27 trace's only direction (sim/units.py)
POISON_UNIT = 0                 # the falsifier's subject: addressed BY ARRAY POSITION
POISON_X = 7                    # in-bounds under BOTH moduli, so the poison never fakes a gap
POISON_ROUND = 1                # the falsifier lands between rounds, before that round's read

MODES = ("container", "model", "late", "nowrite", "mpwidth", "wrapskip", "budget3", "lift")
# the rung's law: a mover whose start tiles come from the container bytes at the ROUND HEAD.
# "model" reads nothing; "late" reads one write too late (so it sees only its own write, never
# an external one); "nowrite" never puts positions in the image, so its container never moves.


class _Mover(sounits.Unit):
    """B7's mover, with this rung's modulus and budget. `wrap=False` is the no-wrap rival;
    every other line of the press law is sim/units.py's, imported not forked."""

    def __init__(self, i, x, y, budget, wrap=True):
        sounits.Unit.__init__(self, i, x, y)
        self._budget = budget
        self._wrap = wrap

    @property
    def budget(self):
        return self._budget

    def step(self, d, width, height):
        if not self.can_act():
            return None
        dx, dy = sounits.delta(d)
        ny = self.y + dy
        if not sounits.y_in_bounds(ny, height):
            return None
        nx = self.x + dx
        if self._wrap:
            nx = sounits.wrap_x(nx, width)
        self.x, self.y = nx, ny
        self.spent += sounits.STEP_MP
        return self.x, self.y


def _tiles(im):
    return {i: [im.unit(i)["x"], im.unit(i)["y"]] for i in range(im.n_units)}


def run(sav_path, map_path, mode="container", turns=TURNS, presses=PRESSES, poison=True):
    """One composed run. Prints nothing; every gate reads the returned measurement."""
    sv0 = sosave.parse(sav_path)
    mp = somap.parse(map_path)
    W_cont, H_cont = sv0.width, sv0.height
    W = mp.width if mode == "mpwidth" else W_cont
    budget = sounits.STEP_MP if mode == "budget3" else sounits.MP_PER_TURN
    wrap = mode != "wrapskip"
    eng = soturn.Engine(sv0.year, human=sv0.own_player)
    img = sv0.data
    model = {u["i"]: [u["x"], u["y"]] for u in sv0.units}
    n = sv0.n_units
    rows = []
    traj = {}
    readback = []          # per (round, unit): 1 when the round's start tile == the container's
    out_of_grid = []       # per (round, unit): tile outside the CONTAINER's grid
    byte_rows = []
    poison_sightings = []
    digest_rows = []
    im_head = sv0
    prev_written = {i: list(model[i]) for i in model}   # round 0 "read" sees the save itself
    for r in range(turns):
        # ---- THE FALSIFIER'S HAND, between rounds, on the container's own bytes. Addressed
        # BY ARRAY POSITION (units_off + 52*i), never by tile: no tile lookup can hide it.
        # Model state is never touched, so only a mover that READS THE CONTAINER can see it.
        if poison and r == POISON_ROUND:
            im0 = soct.parse_image(img)
            off = im0.units_off + sosave.UNIT_LEN * POISON_UNIT
            mut = bytearray(img)
            struct.pack_into("<H", mut, off, POISON_X)
            img = bytes(mut)
            im_head = soct.parse_image(img)   # the bytes the round's read is about to consume
        # ---- the round's START tiles, per the mode's law
        head = _tiles(im_head)
        if mode == "model":
            start = {i: list(model[i]) for i in model}
            src = "model"
        elif mode == "late":
            start = {i: list(prev_written[i]) for i in model}
            src = "image-after-prev-write"
        else:
            start = {i: list(head[i]) for i in model}
            src = "image-at-round-head"
        for i in model:
            readback.append(1 if start[i] == head[i] else 0)
        # ---- the B7 gesture, on every unit of the save's own record array
        acc_tot = ref_tot = 0
        for i in sorted(model):
            m = _Mover(i, start[i][0], start[i][1], budget, wrap=wrap)
            acc = 0
            for _p in range(presses):
                if m.step(DIR_EAST, W, H_cont) is None:
                    ref_tot += 1
                else:
                    acc += 1
                    acc_tot += 1
            model[i] = [m.x, m.y]
            traj.setdefault(i, []).append({"round": r, "src": src, "start": list(start[i]),
                                           "accepted": acc, "spent": m.spent,
                                           "end": [m.x, m.y]})
            if start[i][0] >= W_cont or start[i][1] >= H_cont:
                out_of_grid.append((r, i))
        # ---- the B3 turn engine (the year law, rung B3)
        eng.press()
        # ---- the WRITE: through B8's writer, composing from the container's current bytes.
        # Only the units whose model tile differs from the container's are passed, so the
        # byte accounting below is the move law's own footprint, not a description of it.
        cur = _tiles(im_head)
        mv = None if mode == "nowrite" else {i: tuple(model[i]) for i in model
                                             if list(model[i]) != cur[i]}
        unit_offs = set(range(im_head.units_off, im_head.bases_off))
        img_next = sow.build_image(im_head, year=eng.year, cur=eng.cur, tf=eng.tf, moves=mv,
                                   lift_all=(mode == "lift"))
        diffs = sow.diff_offsets(img, img_next)
        udiffs = sorted(d for d in diffs if d in unit_offs)
        hdiffs = sorted(d for d in diffs if d not in unit_offs)
        img = img_next
        # ---- read the WRITTEN container back through the same parser the decoder uses
        im_w = soct.parse_image(img)
        wt = _tiles(im_w)
        for i in model:
            if wt[i][0] >= W_cont or wt[i][1] >= H_cont:
                out_of_grid.append((r, i))
        byte_rows.append({"round": r, "written": len(mv) if mv is not None else 0,
                          "unit_bytes": len(udiffs), "hdr_bytes": len(hdiffs),
                          "hdr_offsets": hdiffs,
                          "rec_offsets": sorted({(d - im_head.units_off) % sosave.UNIT_LEN
                                                 for d in udiffs}),
                          "year_img": im_w.year, "n_units_img": im_w.n_units,
                          "found_units": im_w.found_units, "n_units": n,
                          "found_bases": im_w.found_bases, "n_bases": im_w.n_bases,
                          "sha": hashlib.sha256(img).hexdigest()[:16]})
        row = {"round": r, "src": src, "accepted": acc_tot, "refused": ref_tot,
               "year_model": eng.year, "year_img": im_w.year,
               "written": len(mv) if mv is not None else 0,
               "unit_bytes": len(udiffs), "hdr_bytes": len(hdiffs),
               "found_units": im_w.found_units, "n_units": n,
               "out_of_grid": sum(1 for e in out_of_grid if e[0] == r),
               "sha": hashlib.sha256(img).hexdigest()[:16]}
        rows.append(row)
        digest_rows.append("R%d|%s|%d|%d|%d|%d|%d|%d|%s" % (
            row["round"], row["src"], row["accepted"], row["refused"], row["written"],
            row["unit_bytes"], row["found_units"], row["year_img"], row["sha"]))
        prev_written = wt
        # the container a round leaves behind IS the container the next round reads; leaving
        # im_head stale would silently turn the whole rung back into nowrite (measured: with
        # this line out, every round composes from the ORIGINAL save bytes and G4 goes vacuous)
        im_head = im_w
        if poison and r >= POISON_ROUND:
            poison_sightings.append((r, head.get(POISON_UNIT), traj[POISON_UNIT][-1]["end"]))
    for i in sorted(model):
        digest_rows.append("T|%d|%s" % (i, ",".join(
            "%d:%d:%d" % (s["start"][0], s["end"][0], s["accepted"]) for s in traj[i])))
    final = soct.parse_image(img)
    return {"mode": mode, "poison": poison, "rows": rows, "traj": traj, "img": img,
            "readback": readback, "out_of_grid": sorted(set(out_of_grid)),
            "byte_rows": byte_rows, "final_tiles": _tiles(final),
            "final_found_units": final.found_units, "final_year_img": final.year,
            "final_n_units": final.n_units, "final_n_bases": final.n_bases,
            "final_sha": hashlib.sha256(img).hexdigest(),
            "orig_year": sv0.year, "orig_found_units": sv0.found_units,
            "orig_tiles": _tiles(sv0), "W_cont": W_cont, "H_cont": H_cont, "W_used": W,
            "mp_width": mp.width, "budget": budget, "n": n, "turns": turns,
            "poison_sightings": poison_sightings, "digest_rows": digest_rows,
            "digest": hashlib.sha256("\n".join(digest_rows).encode()).hexdigest()[:16]}


def _sig(res):
    """The signature table G8 prints: one row per run, carrying the numbers that discriminate."""
    return {"mode": res["mode"] + ("" if res["poison"] else ":clean"),
            "readback_bad": res["readback"].count(0), "readback_n": len(res["readback"]),
            "out_of_grid": len(res["out_of_grid"]),
            "min_found_units": min(b["found_units"] for b in res["byte_rows"]),
            "final_found": res["final_found_units"],
            "unit_bytes_run": sum(b["unit_bytes"] for b in res["byte_rows"]),
            "year_img": res["final_year_img"]}


SIGKEYS = ("mode", "readback_bad", "readback_n", "out_of_grid", "min_found_units",
           "final_found", "unit_bytes_run", "year_img")
ORDER = ["container", "container:clean", "model", "model:clean", "late", "late:clean",
         "nowrite", "mpwidth", "wrapskip", "budget3", "lift"]


def measure(sav_path, map_path, turns=TURNS, presses=PRESSES):
    """All runs the gates read. Print-free, so selftest and __main__ share one source."""
    runs = {}
    for mode in MODES:
        runs[mode] = run(sav_path, map_path, mode=mode, turns=turns, presses=presses)
    for mode in ("container", "model", "late"):
        runs[mode + ":clean"] = run(sav_path, map_path, mode=mode, turns=turns,
                                    presses=presses, poison=False)
    runs["rerun"] = run(sav_path, map_path, mode="container", turns=turns, presses=presses)
    # B7's own slice, in-process, on the same inputs (G1: reuse, not fork)
    _, _, _, _, st7, _ = somv.simulate(sav_path, map_path, DEFAULT_RULES, turns, presses)
    b7 = {h["round"]: sum(1 for mm in h["moves"] if mm["accepted"]) for h in st7["history"]}
    b7_ref = {h["round"]: sum(1 for mm in h["moves"] if not mm["accepted"])
              for h in st7["history"]}
    b7_cells = {(h["round"], mm["unit"]): int(mm["accepted"])
                for h in st7["history"] for mm in h["moves"]}
    sv0 = sosave.parse(sav_path)
    b7_final = st7["final"]["units"]
    b7_out = sorted(int(i) for i, v in b7_final.items()
                    if v[0] >= sv0.width or v[1] >= sv0.height)
    # ... and at the setting B7 was actually accepted at (--turns 5, NAMED.md §B7)
    _, _, _, _, st5, _ = somv.simulate(sav_path, map_path, DEFAULT_RULES, 5, presses)
    b7_5 = {h["round"]: sum(1 for mm in h["moves"] if mm["accepted"]) for h in st5["history"]}
    b7_5_out = sorted(int(i) for i, v in st5["final"]["units"].items()
                      if v[0] >= sv0.width or v[1] >= sv0.height)
    return {"runs": runs, "b7": b7, "b7_ref": b7_ref, "b7_cells": b7_cells,
            "b7_out": b7_out, "b7_final": b7_final, "b7_turns": turns, "presses": presses,
            "b7_5": b7_5, "b7_5_out": b7_5_out,
            "W_cont": sv0.width, "H_cont": sv0.height, "sav_path": sav_path,
            "map_path": map_path}


def render(m):
    """Tables FIRST, then the gate lines - a gate never prints a number its table did not."""
    L = []
    runs = m["runs"]
    c = runs["container"]
    cc = runs["container:clean"]
    L.append("== B25 tables (T=%d rounds x %d presses, units %d, container %dx%d, map file "
             "width %d) ==" % (c["turns"], m["presses"], c["n"], c["W_cont"], c["H_cont"],
                               c["mp_width"]))
    L.append("-- table A: the composed run (mode=container, falsifier ARMED) --")
    L.append("rnd src                    acc ref writ unitB hdrB found/n  yr(mdl/img) "
             "outgr  sha")
    for row in c["rows"]:
        L.append("%3d %-24s %3d %3d %4d %5d %4d %5d/%-3d %4d/%-4d %5d  %s"
                 % (row["round"], row["src"], row["accepted"], row["refused"], row["written"],
                    row["unit_bytes"], row["hdr_bytes"], row["found_units"], row["n_units"],
                    row["year_model"], row["year_img"], row["out_of_grid"], row["sha"]))
    L.append("-- table B: per-round footprint (container): unit-array record offsets touched, "
             "header offsets touched, array accounting --")
    for b in c["byte_rows"]:
        L.append("rnd %d: rec offsets %s | header bytes at %s | written %d | found_units %d/%d "
                 "| found_bases %d/%d" % (b["round"], b["rec_offsets"], b["hdr_offsets"],
                                          b["written"], b["found_units"], b["n_units"],
                                          b["found_bases"], b["n_bases"]))
    L.append("-- table C: trajectory witnesses, round: start_x -> end_x / accepted --")
    for i in (POISON_UNIT, 1, c["n"] - 1):
        for label, res in (("clean", cc), ("poisoned", c)):
            L.append("unit %-3d %-9s %s" % (i, label, " ".join(
                "%d:%d->%d/%d" % (s["round"], s["start"][0], s["end"][0], s["accepted"])
                for s in res["traj"][i])))
    L.append("-- table D: falsifier sightings for unit %d (image-only poison x=%d between "
             "rounds): container tile at the round head -> mover's end tile --"
             % (POISON_UNIT, POISON_X))
    for r, hd, end in c["poison_sightings"]:
        L.append("rnd %2d: image at head %s -> mover ends %s" % (r, hd, end))
    L.append("-- table E: rival and control signatures --")
    L.append("  ".join("%-16s" % k for k in SIGKEYS))
    for k in ORDER:
        s = _sig(runs[k])
        L.append("  ".join("%-16s" % s[k2] for k2 in SIGKEYS))
    L.append("-- table F: B7's own slice on the same inputs, and where ITS modulus put them --")
    L.append("B7 accepted per round %s / refused %s (turns=%d, presses=%d, map-file width %d); "
             "container grid %dx%d; B7 final tiles OUTSIDE that grid: %d of %d units %s"
             % ([m["b7"][r] for r in sorted(m["b7"])],
                [m["b7_ref"][r] for r in sorted(m["b7"])], m["b7_turns"], m["presses"],
                c["mp_width"], m["W_cont"], m["H_cont"], len(m["b7_out"]), c["n"],
                m["b7_out"][:12]))
    L.append("-- table G: determinism --")
    L.append("container digest %s | rerun digest %s | equal=%s | final sha %s / %s | "
             "images equal=%s" % (c["digest"], runs["rerun"]["digest"],
                                  c["digest"] == runs["rerun"]["digest"], c["final_sha"][:16],
                                  runs["rerun"]["final_sha"][:16],
                                  c["img"] == runs["rerun"]["img"]))
    L.append("digest(B25 measured rows) %s" % hashlib.sha256(
        ("\n".join(c["digest_rows"]) + "|" + "|".join(_sig(runs[k])["mode"]
                                                      for k in ORDER)).encode()).hexdigest()[:16])
    return L


def gates(m):
    """The nine gates. Every number below is one of the tables render() printed."""
    runs = m["runs"]
    c = runs["container"]
    cc = runs["container:clean"]
    n = c["n"]
    T = c["turns"]
    g = []

    # G1 - B7 re-derives in-process and this run reproduces its per-unit accept pattern
    cells = {(s["round"], i): c["traj"][i][s["round"]]["accepted"]
             for s in c["rows"] for i in range(n)}
    cells_eq = sum(1 for k, v in cells.items() if m["b7_cells"].get(k) == v)
    g.append(("G1 B7's own slice re-derives on the same inputs (%d rounds, accepted %s / "
              "refused %s) and this composed run equals its per-unit accept pattern in %d/%d "
              "cells - the gesture law is imported, not forked"
              % (T, [s["accepted"] for s in c["rows"]], [s["refused"] for s in c["rows"]],
                 cells_eq, len(cells)),
              cells_eq == len(cells) == n * T
              and all(v == m["b7"][r] for r, v in m["b7"].items())))

    # G2 - identity through THIS call path, and the write's footprint is exactly the move law
    sv0 = sosave.parse(m["sav_path"])
    ident = sow.build_image(sv0) == sv0.data
    ub = [b["unit_bytes"] for b in c["byte_rows"]]
    wb = [b["written"] for b in c["byte_rows"]]
    offs = sorted({o for b in c["byte_rows"] for o in b["rec_offsets"]})
    hdr = sorted({d for b in c["byte_rows"] for d in b["hdr_offsets"]})
    inside = all(any(lo <= d < hi for lo, hi in sow.modeled_spans()) for d in hdr)
    g.append(("G2 identity round-trip through this call path %s (%d B), and every round's "
              "write touches exactly the moved tiles: unit-array bytes %s == tiles written %s, "
              "record offsets touched %s (x only), header bytes per round %s, all %d header "
              "diffs inside the writer's modeled spans: %s"
              % (ident, len(c["img"]), ub, wb, offs,
                 [len(b["hdr_offsets"]) for b in c["byte_rows"]], len(hdr), inside),
              ident and ub == wb and offs == [0] and inside and len(offs) == 1))

    # G3 - the written container reads back as the model said, and stays shape-valid
    final_eq = sum(1 for i in range(n) if c["final_tiles"][i] == c["traj"][i][-1]["end"])
    shape_ok = all(b["found_units"] == b["n_units"] for b in c["byte_rows"])
    g.append(("G3 write-back fidelity: the re-parsed final container's tile equals the model's "
              "for %d/%d units; every round re-parsed with found_units == n_units == %d "
              "(%d/%d rounds); 0 unit-rounds outside the container grid"
              % (final_eq, n, n, sum(1 for b in c["byte_rows"]
                                     if b["found_units"] == b["n_units"]), len(c["byte_rows"])),
              final_eq == n and shape_ok and len(c["out_of_grid"]) == 0))

    # G4 - the reload law, the rung's core
    bad = c["readback"].count(0)
    deltas_ok = all((s["end"][0] - s["start"][0]) % c["W_cont"]
                    == (sounits.DIR_DX[DIR_EAST] * s["accepted"]) % c["W_cont"]
                    for i in range(n) for s in c["traj"][i])
    per = sounits.MP_PER_TURN // sounits.STEP_MP
    budget_ok = all(s["accepted"] == per and s["spent"] == s["accepted"] * sounits.STEP_MP
                    and s["accepted"] < m["presses"] for i in range(n) for s in c["traj"][i])
    g.append(("G4 the reload law: %d/%d (round,unit) start tiles equal the container's tile at "
              "the round head (%d divergences); every accepted press moved (+%d,0) mod %d from "
              "the RELOADED tile; every unit accepted exactly %d of %d presses each round with "
              "spent == 3*accepted"
              % (len(c["readback"]) - bad, len(c["readback"]), bad, sounits.DIR_DX[DIR_EAST],
                 c["W_cont"], per, m["presses"]),
              bad == 0 and len(c["readback"]) == n * T and deltas_ok and budget_ok))

    # G5 - the coordinate space, arbitrated by the decoder's OWN shape scan
    mp_r, ws_r = runs["mpwidth"], runs["wrapskip"]
    mp_out, mp_min = len(mp_r["out_of_grid"]), _sig(mp_r)["min_found_units"]
    ws_out, ws_min = len(ws_r["out_of_grid"]), _sig(ws_r)["min_found_units"]
    g.append(("G5 coordinate space: the container's own width %d keeps %d tiles out of grid "
              "and found_units at %d/%d; the MAP FILE's width %d puts %d unit-rounds outside "
              "the container and its parser's own found_units drops to %d; the no-wrap rival: "
              "%d out-of-grid, found_units drops to %d. B7 - which wrapped by the map file - "
              "left %d of %d units' final tiles outside this container's %dx%d grid"
              % (c["W_cont"], len(c["out_of_grid"]), c["byte_rows"][-1]["found_units"], n,
                 c["mp_width"], mp_out, mp_min, ws_out, ws_min, len(m["b7_out"]), n,
                 m["W_cont"], m["H_cont"]),
              len(c["out_of_grid"]) == 0 and mp_out > 0 and mp_min < n and ws_out > 0
              and ws_min < n and len(m["b7_out"]) > 0))

    # G6 - the falsifier bites; the two blindness controls prove it is the container that moved
    pu = POISON_UNIT
    clean_x = [s["start"][0] for s in cc["traj"][pu]]
    pois_x = [s["start"][0] for s in c["traj"][pu]]
    shift = [(p - q) % c["W_cont"] for p, q in zip(pois_x, clean_x)]
    others = sum(1 for i in range(n) if i != pu and c["traj"][i] != cc["traj"][i])
    mdl_same = runs["model"]["img"] == cc["img"]
    late_same = runs["late"]["img"] == cc["img"]
    g.append(("G6 falsifier: rewriting unit %d's tile in the IMAGE ONLY at round %d shifts its "
              "start-tile trajectory by %s mod %d for every later round (clean %s -> poisoned "
              "%s), the shift is in the FINAL container (%s vs clean %s), and no other unit's "
              "trajectory moves (%d of %d); the model-fed and read-after-write movers are BLIND: "
              "their final images equal the clean run's byte-for-byte (model %s, late %s)"
              % (pu, POISON_ROUND, sorted(set(shift)), c["W_cont"], clean_x, pois_x,
                 c["final_tiles"][pu], cc["final_tiles"][pu], others, n, mdl_same, late_same),
              shift[0] == 0 and len(set(shift[1:])) == 1 and shift[1] != 0 and others == 0
              and mdl_same and late_same and c["final_tiles"][pu] != cc["final_tiles"][pu]))

    # G7 - the writer's span accounting over the whole run
    spans = list(sow.modeled_spans())
    spans += [(sv0.units_off + sosave.UNIT_LEN * i,
               sv0.units_off + sosave.UNIT_LEN * i + 4) for i in range(n)]
    final_diffs = sorted(sow.diff_offsets(sv0.data, c["img"]))
    outside = [d for d in final_diffs if not any(lo <= d < hi for lo, hi in spans)]
    inside_u = [d for d in final_diffs if sv0.units_off <= d < sv0.bases_off]
    g.append(("G7 span accounting over the whole run: the final container differs from the "
              "original in %d bytes (%d inside the unit array, %d in the modeled header), and "
              "%d bytes lie outside a modeled span; the writer's own (header-only) span check "
              "would flag exactly the %d unit-array bytes as unmodeled, which is why this gate "
              "adds the record x/y spans B8's writer patches"
              % (len(final_diffs), len(inside_u), len(final_diffs) - len(inside_u),
                 len(outside), len(inside_u)),
              len(outside) == 0 and len(final_diffs) > 0 and len(inside_u) > 0))

    # G8 - the rival table: every rival discriminated, every control degenerate by design
    s = {k: _sig(runs[k]) for k in runs}
    rw = runs["nowrite"]
    riv = {
        "nowrite": s["nowrite"]["unit_bytes_run"] == 0 and rw["final_tiles"] == rw["orig_tiles"],
        "mpwidth": s["mpwidth"]["out_of_grid"] > 0 and s["mpwidth"]["min_found_units"] < n,
        "wrapskip": s["wrapskip"]["out_of_grid"] > 0 and s["wrapskip"]["min_found_units"] < n,
        "budget3": all(t["accepted"] == 1 for i in range(n) for t in runs["budget3"]["traj"][i])
        and s["budget3"]["readback_bad"] == 0,
        "lift": s["lift"]["unit_bytes_run"] == 0 and runs["lift"]["final_year_img"]
        == runs["lift"]["orig_year"],
    }
    control = (s["model"]["readback_bad"] == 1 and s["late"]["readback_bad"] == 1
               and runs["model"]["img"] == cc["img"] and runs["late"]["img"] == cc["img"]
               and s["model"]["unit_bytes_run"] > 0 and s["late"]["unit_bytes_run"] > 0)
    g.append(("G8 rivals and controls (table E): nowrite never touches the container (%d unit "
              "bytes, its tiles stay the save's %s); map-file modulus and no-wrap put %d / %d "
              "unit-rounds out of grid (found_units min %d / %d); budget3 accepts 1 press per "
              "round not 2 (%s); the lift-everything re-emitter writes %d unit bytes and never "
              "advances the container's year past %d; the two blindness controls diverge at "
              "exactly 1 read-back each, still write %d/%d unit bytes, and rebuild the CLEAN "
              "final image. The rung's own row: 0 read-back divergences"
              % (s["nowrite"]["unit_bytes_run"], rw["final_tiles"] == rw["orig_tiles"],
                 s["mpwidth"]["out_of_grid"], s["wrapskip"]["out_of_grid"],
                 s["mpwidth"]["min_found_units"], s["wrapskip"]["min_found_units"],
                 sorted({t["accepted"] for i in range(n)
                         for t in runs["budget3"]["traj"][i]}),
                 s["lift"]["unit_bytes_run"], runs["lift"]["final_year_img"],
                 s["model"]["unit_bytes_run"], s["late"]["unit_bytes_run"]),
              all(riv.values()) and control and s["container"]["readback_bad"] == 0))

    # G9 - determinism, over the measured rows AND the container
    same = (c["digest"] == runs["rerun"]["digest"] and c["img"] == runs["rerun"]["img"])
    g.append(("G9 determinism: the rerun reproduces the measured-row digest %s and the final "
              "container sha256 %s (%d B)" % (c["digest"], c["final_sha"][:16], len(c["img"])),
              same))
    return g


def acceptance(m, results):
    for name, ok in gates(m):
        results.append((name, ok))
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sim.composedmove")
    ap.add_argument("--sav", default=DEFAULT_SAV)
    ap.add_argument("--map", dest="map_path", default=DEFAULT_MAP)
    ap.add_argument("--turns", type=int, default=TURNS)
    ap.add_argument("--presses", type=int, default=PRESSES)
    ap.add_argument("--out", default=None, help="write the final composed container here")
    a = ap.parse_args(argv)
    for p in (a.sav, a.map_path):
        if not os.path.exists(p):
            print("FAIL B25: missing input %s" % p)
            return 1
    m = measure(a.sav, a.map_path, a.turns, a.presses)
    for line in render(m):
        print(line)
    res = acceptance(m, [])
    bad = [name for name, ok in res if not ok]
    for name, ok in res:
        print(("  ok   " if ok else "  BAD  ") + name)
    if bad:
        print("FAIL B25: %d/%d gates failed: %s" % (len(bad), len(res), "; ".join(bad)))
        return 1
    print("PASS B25: %d/%d gates" % (len(res), len(res)))
    if a.out:
        with open(a.out, "wb") as fh:
            fh.write(m["runs"]["container"]["img"])
        print("wrote %s (%d B, sha256 %s)" % (a.out, len(m["runs"]["container"]["img"]),
                                              m["runs"]["container"]["final_sha"][:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
