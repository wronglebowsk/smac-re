#!/usr/bin/env python3
"""sim.composedsave - rung B26: the composed run crosses a SAVE/LOAD BOUNDARY.

BUILD_SPINE.md rung B26 (s299 authored this rung from main cd6f2f5, as B14-B25 did).

B21 wrote the log-driven run and resumed it; B24 made the founder leg and the queue
leg share one container; B25 made the MOVE leg read its own start tile out of the
container. None of them ever THREW THE MODEL AWAY. Every rung so far keeps its Python
objects alive across the whole run and merely adds writes, so a value that survives
only because the object survived is indistinguishable from a value the container
carries. This rung loads: phase A runs the founder leg (the recorded m289 op stream
through the writer, the last-slot destroy included) and the move leg (B7/B25's press
on every unit present), appends B12 arrivals whose tile is READ FROM THE IMAGE, then
at a round-aligned BOUNDARY writes the image, discards ledger/units/engine/arrivals
and rebuilds them from `parse_image` of the written bytes alone. Phase B runs the same
laws, and - because that is what a load does - the writer now composes from the LOADED
container instead of from the original save.

Three laws are at stake:
  CARRY      every field the resumed run uses equals a fresh decode of the boundary
             bytes, never a retained variable (G3);
  CONFLUENCE an uneventful boundary is invisible: the boundary run's final container
             is byte-identical to the uninterrupted run's (G4);
  NON-CARRY  at a MID-GESTURE boundary the per-round MP budget cannot cross (it is
             model state, B25's declared line), so the resumed run MUST diverge - and
             the divergence is counted per unit and per byte (G5), with a control run
             that smuggles the budget across and diverges by exactly nothing.

The falsifier poisons IN THE BOUNDARY IMAGE ONLY, between the write and the rebuild:
one unit's x, and the parent base record's x/y/own4 - which phase B's arrival is
composed from. Every run that reads the container at a round head - the smuggler
included - therefore SEES it; what the smuggler does not do is rebuild its objects from
it, and G6 measures both halves separately (PR #328 F1 retracted the earlier "the
smuggler is blind to the poison", which was only ever true because the shipped
instrument never handed the poison to the smuggler).

`python3 -u -m sim.selftest --b26` relays THIS module's claims;
`python3 -u -m sim.composedsave [--out f]` prints them. NO /proc, NO gdb, NO Wine,
NO game-binary load.
"""
import argparse
import hashlib
import os
import struct
import sys

from . import basefound as sobf
from . import composedlive as socl
from . import composedmove as socev
from . import composedrun as socr
from . import composedturn as soct
from . import production as soprod
from . import save as sosave
from . import savewriter as sow
from . import turn as soturn
from . import units as sounits

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "evidence")
DEFAULT_SAV = os.path.join(ROOT, "programs", "saves", "m54b_clean.SAV")
DEFAULT_MAP = os.path.join(ROOT, "programs", "maps", "planet.MP")
DEFAULT_LOG = os.path.join(EVID, "m289_gdb_raw.log")
DEFAULT_TRACE = os.path.join(EVID, "trace_m289_20261110_071759.jsonl")

RA, RB = 4, 2                 # rounds before / after the boundary (round-aligned)
PRESSES = 3                   # B7/B25's gesture shape: 2 accepts + 1 refuse per round
DIR_EAST = 1                  # the M27 trace's only direction
BOUNDARY = RA                 # the round index at which the model is thrown away
ARRIVAL_TYPE = 2              # declared fixture head id (B24's SEED_SLOTS value)
PARENT_OP = 1                 # the founding whose record feeds every arrival: op 1 of
                              # the recorded stream, i.e. index 19 - MEASURED to
                              # survive op 3's last-slot destroy (G2 note, not assumed)
PARENT_TILE = (63, 51)        # the log's own tile for op 1 (printed, never used as
PARENT_FAC = 6                #   truth: the arrival reads its tile out of the image)

# the falsifier, applied IN THE BOUNDARY IMAGE ONLY
POISON_UNIT = 0
POISON_X = 7                  # in-bounds under the container's modulus
POISON_TILE = (1447, 1448)    # out-of-grid on purpose: the decoder must SEE it
POISON_OWN4 = 0x5A

MODES = ("container", "smuggle", "model", "nowrite", "late", "lift", "frozen",
         "split", "budgetcarry", "uninterrupted")

# MEASURED literals pinned inside the gates (updated from the run's own printed rows;
# a gate that could pass on an unmeasured state is a defect, not a gate - trap 24).
ACCEPT_PIN = "ae43e0ab9c8cfc3d"     # table G's ACCEPT anchor, pinned by G9. It MOVED
                                    #   from 1721afbdd1439ec1 because PR #328 F1 added the
                                    #   smuggler's unexposed control to the run set, which
                                    #   the anchor digests by name - the measured ROWS did
                                    #   not move (container digest abbd009eb9130792, same
                                    #   as the shipped evidence).
UNITS_SPLIT = 69                     # G5: units whose final tile diverges at a split
BYTES_SPLIT = 69                     # G5: bytes the split run's final image differs by
SPLIT_HIST = (69, 0, 0, 0, 0, 0)    # G5: where a mid-gesture split's final image differs
                                    #   from the uninterrupted one, by record offset:
                                    #   (x_lo, x_hi, y, other_in_record, header, outside)
                                    #   - MEASURED: every byte is the LOW byte of x
UNITS_POISONED = 3                  # G6: units whose final tile the poison moved
OWN4_HITS = (2, 0)                  # G6: FINAL-image unit records whose owner byte ==
                                    #   POISON_OWN4, container vs clean (measured)
REF_SAVE_PIN = (67, 67, 67, 67)     # G1: B26's SAVE-unit refusals, per round of the
                                    #   shared prefix - equal to B25's, measured
LEDGER_FIELDS = (20, 20, 20)        # G3: rebuilt ledger == third parse, FIELD-WISE:
                                    #   (records matching, ledger length, parsed count)
SMUGGLE_SEES = 2                    # G6: units whose FINAL tile the smuggler moved once
                                    #   it is actually handed the image-only poison
                                    #   (measured: units 0 and 69).
                                    #   PR #328 F1: this is the number that kills the old
                                    #   "the smuggler is blind" prose - smuggle used to be
                                    #   run WITHOUT the poison, so its equality with the
                                    #   clean run measured object reuse, not blindness.
OWN4_SMUGGLE = 1                    # G6: same census on the exposed smuggler's FINAL
                                    #   image - one of the two owner-poisoned arrivals,
                                    #   not the container's two (measured, listed in
                                    #   table E; WHY it is one and not two is DECLARED
                                    #   OPEN, not explained)
SIZE_LAW = ((304, 304), (304, 304), (356, 356), (-252, -252), (356, 356), (356, 356))
                                    # G10 (F2): per-round (size_delta, 304*Dbases +
                                    #   52*Dunits) of the container run - printed AND
                                    #   gated, 6/6 equal. Round 3 is the recorded
                                    #   DESTROY: -252 = 52*1 - 304*1, one unit in, one
                                    #   base out, in ONE round of arithmetic.
ENGINE_STATE = (3, 0, 2155)         # G5: the mid-gesture pre-split engine's own state
                                    #   (cur, tf, year); the rebuilt one is pinned equal
                                    #   to it, so the F5 install fix's magnitude on this
                                    #   fixture is a printed number, not a hope.
# the per-round signature the rival table compares (mode label excluded, trap 24).
# ref_save (the SAVE-only refusal half G1 compares against B25) is deliberately NOT
# added here: it would change digest(B26 measured rows) - and so the pin G9 holds -
# for a print-format reason, not a run reason. G1 compares it explicitly instead.
SIGKEYS = ("round", "n_units_img", "n_bases_img", "ops", "arrivals", "acc_save",
           "acc_arr", "refused", "unit_bytes", "grown_bytes", "hdr_bytes",
           "size_delta", "year", "found_units", "found_bases", "sha")


def _u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def _ledger_fields(led, img):
    """F6 (PR #328): does the REBUILT ledger actually hold what the bytes say?
    Field-for-field (own4, fac, x, y) against a THIRD independent parse of the same
    container. NOT circular: the ledger is built from one parse, checked against
    another. Returns (records matching, ledger length, parse's n_bases)."""
    if led is None:
        return (0, 0, 0)
    im3 = soct.parse_image(img)
    n = min(len(led.records), im3.n_bases)
    same = 0
    for i in range(n):
        a, b = led.records[i], im3.bases[i]
        if all(a.get(k) == b.get(k) for k in ("own4", "fac", "x", "y")):
            same += 1
    return (same, len(led.records), im3.n_bases)


def _diff_hist(a, b, span):
    """F4 (PR #328): classify every differing byte of two containers by its offset
    inside the unit array, so 'the non-carry is the x byte' is a counted statement
    about record layout and not an adjective. span = (units_off, bases_off)."""
    da, db = bytes(a), bytes(b)
    n = min(len(da), len(db))
    ulo, uhi = span
    h = {"x_lo": 0, "x_hi": 0, "y": 0, "rec_other": 0, "header": 0, "outside": 0,
         "total": 0, "len_diff": abs(len(da) - len(db))}
    for d in range(n):
        if da[d] == db[d]:
            continue
        h["total"] += 1
        if d < ulo:
            h["header"] += 1
        elif d >= uhi:
            h["outside"] += 1
        else:
            k = (d - ulo) % sosave.UNIT_LEN
            h["x_lo" if k == 0 else "x_hi" if k == 1 else
               "y" if k in (2, 3) else "rec_other"] += 1
    return h


def _size_law(rows, sv):
    """G10 (PR #328 F2): the container's growth is record arithmetic, and it is a GATE
    now, not a decoration. For every round of the honest run,
        size_delta == 304 * (n_bases delta) + 52 * (n_units delta)
    with the deltas taken against the previous round's post-write image (the save for
    round 0). render() prints the list this returns and gates() asserts it, so the line
    cited from the evidence is the same object the gate reads - the reason F2 was filed
    is precisely that the shipped G7 checks byte PROVENANCE, never this arithmetic."""
    out = []
    for i, r in enumerate(rows):
        pb, pu = ((sv.n_bases, sv.n_units) if i == 0
                  else (rows[i - 1]["n_bases_img"], rows[i - 1]["n_units_img"]))
        out.append((r["size_delta"],
                    sosave.BASE_LEN * (r["n_bases_img"] - pb)
                    + sosave.UNIT_LEN * (r["n_units_img"] - pu)))
    return out


def own4_records(im):
    """G6's byte-level base-channel census, as RECORDS and not only a count: every
    FINAL-image unit record whose owner byte (sim/production.py:54, UNIT_OWNER = +14 -
    the +4 the first probe scanned is UNIT_FLAG, and reading the wrong offset is how this
    claim nearly shipped untested) equals the falsifier's own4. With the array index and
    the tile printed next to it, so the gate's number is the length of a list the report
    shows and not a second, unprintable implementation."""
    out = []
    for i in range(im.n_units):
        off = im.units_off + sosave.UNIT_LEN * i
        if (off + soprod.UNIT_OWNER < len(im.data)
                and im.data[off + soprod.UNIT_OWNER] == POISON_OWN4):
            out.append((i, im.unit(i)["x"], im.unit(i)["y"]))
    return out


def own4_census(im):
    """G6's count, derived from own4_records so the two can never disagree."""
    return len(own4_records(im))


def _tiles(im):
    return {i: [im.unit(i)["x"], im.unit(i)["y"]] for i in range(im.n_units)}


def _ov(base, led):
    """bases_override relative to the container `base`: every record the container
    already holds passes through as its OWN bytes (identity), every record the ledger
    holds beyond the container composes as the founder's bytes (M282). In phase B the
    container is the LOADED image, so an image-only poison survives the re-write -
    which is exactly what a real load does and what B24's from-sv0 recomposition could
    not do without feeding the visited record back from the container by hand."""
    ov = [{"identity": True} for _ in range(base.n_bases)]
    for i in range(base.n_bases, len(led.records)):
        r = led.records[i]
        ov.append({"raw": sobf.record_bytes(r), "x": r["x"], "y": r["y"],
                   "own4": r["own4"], "fac": r["fac"]})
    return ov


def _apply_op(led, op, applied):
    """One op of the recorded stream, by the B10/B13 laws the founder leg owns."""
    pre = len(led)
    if op["kind"] == "found":
        landed = led.found(op["fac"], op["x"], op["y"])
    else:
        landed = led.destroy(len(led) - 1) is not None   # B13's last-slot law
    applied.append({"pre": pre, "post": len(led), "kind": op["kind"], "landed": landed})
    return landed


def _rec(im, i):
    off = im.bases_off + sosave.BASE_LEN * i
    return im.data[off:off + sosave.BASE_LEN]


def _census(img, im2, sv0, led, eng, parent_idx, poison, edits, mode):
    """THE CARRY census: every field the resumed run is about to use, compared with an
    INDEPENDENT second parse of the same bytes. Nothing here reads a model object for
    its expected value, so 'the bytes carry it' is a claim about the bytes."""
    im = soct.parse_image(img)
    t1, t2 = _tiles(im), _tiles(im2)
    return {"round": None, "bytes": len(img), "edits": len(edits),
            "year": (im.year, im2.year),
            "cur": (_u32(img, sow.OFF_CUR), _u32(bytes(im2.data), sow.OFF_CUR)),
            "tf": (_u32(img, sow.OFF_TF), _u32(bytes(im2.data), sow.OFF_TF)),
            "n_units": (im.n_units, im2.n_units),
            "n_bases": (im.n_bases, im2.n_bases),
            "tiles": sum(1 for i in range(im.n_units) if t1[i] == t2[i]),
            "tile_n": im.n_units,
            "grown": sum(1 for i in range(sv0.n_bases, im.n_bases)
                         if _rec(im, i) == _rec(im2, i)),
            "grown_n": max(0, im.n_bases - sv0.n_bases),
            "rebuilt_ledger": (len(led.records) if led is not None else None,
                               im2.n_bases),
            # F6 (PR #328): a LENGTH equality proves the ledger was allocated, not that
            # it holds what the bytes say. Field-for-field, against a THIRD independent
            # parse of the same container: (records matching, ledger length, parse count)
            "ledger_fields": _ledger_fields(led, img),
            "parent_from_image": (_rec(im2, parent_idx)[0:4]
                                  == struct.pack("<HH", *POISON_TILE)
                                  if poison and parent_idx is not None
                                  and mode not in ("smuggle", "uninterrupted")
                                  else None)}


def _poison_hand(img, parent_idx):
    """THE FALSIFIER'S HAND, on the composition's own bytes, applied BETWEEN the
    boundary's write and the rebuild: one unit's x and the PARENT BASE RECORD's
    x/y/own4, both addressed BY ARRAY POSITION. Model state is never touched, so
    only a run that rebuilds from the bytes can see either."""
    mut = bytearray(img)
    im0 = soct.parse_image(bytes(mut))
    off_u = im0.units_off + sosave.UNIT_LEN * POISON_UNIT
    struct.pack_into("<H", mut, off_u, POISON_X)
    off_b = im0.bases_off + sosave.BASE_LEN * parent_idx
    struct.pack_into("<HH", mut, off_b, *POISON_TILE)
    mut[off_b + 4] = POISON_OWN4
    edits = [k for k, (a, b) in enumerate(zip(img, bytes(mut))) if a != b]
    return bytes(mut), edits


def run(sav_path, map_path, mode="container", rounds=(RA, RB), presses=PRESSES,
        poison=True, boundary_at=BOUNDARY, ops=None):
    """One run. Prints nothing; every gate reads what this returns.

    mode: 'container' the rung (read the container every round, rebuild from the bytes
    at the boundary, and compose every later write from the LOADED image);
    'uninterrupted' the same legs with NO boundary (the confluence partner);
    'smuggle' writes and re-reads but keeps its model objects across the boundary;
    'model' takes start tiles from the model dict, never from the container;
    'nowrite' never puts tiles/records in the image; 'late' rebuilds from the
    container as it stood one write earlier; 'lift' lift-everything writer; 'frozen'
    composes the arrival's parent tile from the founder's MODEL constants;
    'split'/'budgetcarry' put the boundary MID-GESTURE (after press 1 of the boundary
    round) - the second one smuggling the spent word across, the control that makes
    G5's divergence causal rather than incidental."""
    sv0 = sosave.parse(sav_path)
    split = mode in ("split", "budgetcarry")
    total = rounds[0] + rounds[1]
    budget = sounits.MP_PER_TURN
    eng = soturn.Engine(sv0.year, human=sv0.own_player)
    led = sobf.from_save(sv0)
    img = sv0.data
    base_im = sv0                     # the container the WRITER composes from
    model = {u["i"]: [u["x"], u["y"]] for u in sv0.units}
    arrivals = []                     # records appended since base_im's own array
    spent = {}                        # per-round MP: model state, B25's declared gap
    applied, rows, carry, arr_rows, digest_rows, byte_rows = [], [], [], [], [], []
    boundary = {}
    parent_idx = None
    edits = []
    prev_n_u = prev_n_b = sv0.n_units, sv0.n_bases
    late_img = sv0.data               # 'late': the container one write too old
    for r in range(total):
        img_at_start = img            # what THIS round read; 'late' reads the previous one
        spent = {}                    # the per-round refresh (0x51f730 zeroes mpused)
        # -------------------------------------------------------- THE BOUNDARY
        if r == boundary_at and mode != "uninterrupted":
            # PR #328 F1: the smuggler used to be EXCLUDED from the poison, which made
            # G6's "the smuggler is blind" a tautology - it was never handed the bytes.
            # It is handed them now, and G6 measures what it does with them. Only 'late'
            # stays excluded: it rebuilds from late_img (the container one write too
            # old), so a poison fired on the fresh image would be invisible by
            # construction and the run would measure nothing but its own bookkeeping.
            if mode != "late" and poison and parent_idx is not None:
                img, edits = _poison_hand(img, parent_idx)
            im2 = soct.parse_image(img)
            if mode == "smuggle":
                cen = _census(img, im2, sv0, led, eng, parent_idx, poison, edits, mode)
            elif mode == "late":
                cen = _census(late_img, im2, sv0, led, eng, parent_idx, poison, edits,
                              mode)
                led = sobf.Ledger([{"own4": b["own4"], "fac": b["fac"], "x": b["x"],
                                    "y": b["y"]} for b in soct.parse_image(late_img).bases])
                model = _tiles(soct.parse_image(late_img))
                eng = soturn.Engine(soct.parse_image(late_img).year, human=sv0.own_player)
                base_im = soct.parse_image(late_img)
                arrivals = []
            elif mode == "model":
                # the rival that never consults the container: no rebase, no rebuild -
                # the boundary is nothing to it, which is exactly the claim G8 reads
                cen = _census(img, im2, sv0, led, eng, parent_idx, poison, edits, mode)
            else:
                # THE LOAD: every model object is discarded and rebuilt from the bytes.
                im = im2
                led = sobf.Ledger([{"own4": b["own4"], "fac": b["fac"], "x": b["x"],
                                    "y": b["y"]} for b in im.bases])
                model = _tiles(im)
                spent = {i: spent.get(i, 0) for i in model} if split and mode == \
                    "budgetcarry" else {}
                eng = soturn.Engine(im.year, human=im.own_player)
                arrivals = []
                base_im = im
                cen = _census(img, im2, sv0, led, eng, parent_idx, poison, edits, mode)
            cen["round"] = r
            carry.append(cen)
            boundary = dict(cen)
            boundary["edits_list"] = edits[:8]
        # ----------------------------------------------------------- the ops
        ops_this = []
        if ops and r < len(ops):
            op = ops[r]
            ops_this = [op["kind"]]
            _apply_op(led, op, applied)
            if op["kind"] == "found" and r == PARENT_OP:
                parent_idx = len(led) - 1
        # ------------------------------- read the container, BEFORE the write
        cont = soct.parse_image(img)
        if mode == "late":
            cont = soct.parse_image(late_img)
        head = _tiles(cont)
        if mode == "model":
            start = {i: list(model[i]) for i in model}
            src = "model"
        elif mode == "late":
            start = {i: list(head[i]) for i in model if i in head}
            src = "image-one-write-late"
        else:
            start = {i: list(head[i]) for i in model if i in head}
            src = "image-at-round-head"
        # -------------------------------------------- the press (B7/B25 law)
        n_press = 1 if (split and r == boundary_at) else presses
        acc_save = acc_arr = ref_tot = ref_save = 0
        for i in sorted(start):
            m = socev._Mover(i, start[i][0], start[i][1], budget, wrap=True)
            m.spent = spent.get(i, 0)
            acc = 0
            for _p in range(n_press):
                if m.step(DIR_EAST, sv0.width, sv0.height) is None:
                    ref_tot += 1
                    if i < sv0.n_units:
                        ref_save += 1      # the SAVE-only half, for the B25 comparison
                else:
                    acc += 1
            model[i] = [m.x, m.y]
            spent[i] = m.spent
            if i < sv0.n_units:
                acc_save += acc
            else:
                acc_arr += acc
        # ----------------------------------------- the arrival (B12's CREATE)
        arr_this_round = None
        if parent_idx is not None and r > PARENT_OP:
            if mode == "frozen":
                px, py, pown, psrc = PARENT_TILE[0], PARENT_TILE[1], PARENT_FAC, \
                    "model-constants"
            else:
                pread = cont.data[cont.bases_off + sosave.BASE_LEN * parent_idx:
                                  cont.bases_off + sosave.BASE_LEN * (parent_idx + 1)]
                px, py = struct.unpack_from("<HH", pread, 0)
                pown = pread[4]
                psrc = "image-at-round-head"
            rec_arr = soprod.create_record(px, py, ARRIVAL_TYPE, pown)
            new_idx = base_im.n_units + len(arrivals)
            arrivals.append((new_idx, rec_arr))
            model[new_idx] = [px, py]
            arr_this_round = new_idx          # B12's order: presses, then CREATE
            arr_rows.append({"round": r, "src": psrc, "tile": [px, py], "own4": pown,
                             "sha": hashlib.sha256(rec_arr).hexdigest()[:12]})
        # ------------------------------------------------------- the write(s)
        eng.press()
        img, im_w, unit_bytes, grown_bytes, hdr_bytes, size_delta = _write(
            base_im, img, model, led, eng, arrivals, mode)
        n_u, n_b = im_w.n_units, im_w.n_bases
        rows.append(_row(r, mode, src, len(ops_this), len(arrivals), acc_save, acc_arr,
                         ref_tot, ref_save, unit_bytes, grown_bytes, hdr_bytes, im_w,
                         size_delta))
        digest_rows.append("|".join(str(rows[-1][k]) for k in SIGKEYS))
        byte_rows.append({"round": r, "rec_offsets": []})
        late_img, prev_n_u, prev_n_b = img_at_start, n_u, n_b
        if split and r == boundary_at:
            # the MID-GESTURE boundary: one write in, model discarded, the rest of the
            # round pressed by the REBUILT state. Only 'budgetcarry' keeps the spent
            # word - and that control is what proves the divergence below is the
            # budget's, not the boundary's.
            im2 = soct.parse_image(img)
            imn = im2
            mdict = _tiles(imn)
            e2 = soturn.Engine(imn.year, human=imn.own_player)
            # THE MID-GESTURE RELOAD INSTALLS THE ENGINE TOO. Before this fix the split
            # built e2 from the loaded image, used it only for the mid write, and let
            # every LATER round drive the PRE-split engine again - so "model, ledger,
            # engine and arrival list are discarded" was true of the first three and
            # false of the fourth (PR #328 F5). eng_states holds (pre-split state,
            # rebuilt state) and is printed in table D and pinned in G5: whether the
            # defect had a magnitude on this run is a MEASURED fact, not a hope.
            # No second Engine.press(): the round's year edge already fired, and the
            # rebuilt engine reads the year the write put in the header.
            eng_states = (eng.state(), e2.state())
            carry.append({"round": r, "bytes": len(img), "edits": 0, "mid": True,
                          "year": (e2.year - 1, imn.year), "cur": (0, 0), "tf": (0, 0),
                          "n_units": (imn.n_units, imn.n_units),
                          "n_bases": (imn.n_bases, imn.n_bases),
                          "tiles": len(mdict), "tile_n": len(mdict), "grown": 0,
                          "grown_n": 0, "rebuilt_ledger": (imn.n_bases, imn.n_bases),
                          "rebuilt_tiles": len(mdict), "parent_from_image": True,
                          "eng_states": eng_states})
            led2 = sobf.Ledger([{"own4": b["own4"], "fac": b["fac"], "x": b["x"],
                                 "y": b["y"]} for b in imn.bases])
            md = mdict
            sp2 = dict(spent) if mode == "budgetcarry" else {}
            for _p in range(presses - 1):
                for i in sorted(md):
                    if i == arr_this_round:
                        continue      # a unit created this round is pressed NEXT round
                    m = socev._Mover(i, md[i][0], md[i][1], budget, wrap=True)
                    m.spent = sp2.get(i, 0)
                    if m.step(DIR_EAST, sv0.width, sv0.height) is not None:
                        md[i] = [m.x, m.y]
                        sp2[i] = m.spent
            img, im_w, ub, gb, hb, sd = _write(imn, img, md, led2, e2, [], mode)
            rows[-1]["unit_bytes"] += ub
            rows[-1]["grown_bytes"] += gb
            rows[-1]["hdr_bytes"] += hb
            rows[-1]["n_units_img"] = im_w.n_units
            rows[-1]["n_bases_img"] = im_w.n_bases
            rows[-1]["sha"] = hashlib.sha256(img).hexdigest()[:16]
            base_im, model, led, arrivals = imn, md, led2, []
            eng = e2               # the mid-gesture reload installs the rebuilt engine
                                   # for every LATER round too (PR #328 F5)
    final = soct.parse_image(img)
    return {"rows": rows, "carry": carry, "boundary": boundary, "arr_rows": arr_rows,
            "img": img, "final_tiles": _tiles(final), "final_units": final.n_units,
            "own4_final": own4_census(final), "own4_recs": own4_records(final),
            "final_bases": final.n_bases, "final_sha": hashlib.sha256(img).hexdigest(),
            "parent_idx": parent_idx, "applied": applied, "edits": len(edits),
            "digest_rows": digest_rows,
            "digest": hashlib.sha256("\n".join(digest_rows).encode()).hexdigest()[:16],
            "unit_span": (final.units_off, final.bases_off),
            "base_span": (final.bases_off,
                          final.bases_off + sosave.BASE_LEN * final.n_bases)}


def _write(base_im, img, model, led, eng, arrivals, mode):
    """One writer call. The writer composes from `base_im`, so the moves are relative
    to THAT container's own tiles - passing only the ones that differ from some other
    view silently reverts every earlier move (measured, first draft of this rung)."""
    bt = _tiles(base_im)
    if mode == "nowrite":
        return img, soct.parse_image(img), 0, 0, 0, 0
    mv = {i: tuple(model[i]) for i in model
          if i < base_im.n_units and list(model[i]) != bt.get(i, [None])}
    app = []
    for idx, rec in arrivals:
        b = bytearray(rec)
        if idx in model and not (mode == "lift"):
            struct.pack_into("<HH", b, 0, model[idx][0] % 0x10000,
                             model[idx][1] % 0x10000)
        app.append(bytes(b))
    nxt = sow.build_image(base_im, year=eng.year, cur=eng.cur, tf=eng.tf,
                          moves=mv or None, bases_override=_ov(base_im, led),
                          append_units=app or None, lift_all=(mode == "lift"))
    im_w = soct.parse_image(nxt)
    u_lo, u_hi = im_w.units_off, im_w.bases_off
    same = len(img) == len(nxt)
    diffs = sow.diff_offsets(img, nxt) if same else set()
    unit_bytes = sum(1 for d in diffs if u_lo <= d < u_hi)
    grown_bytes = sum(1 for d in diffs if d >= im_w.bases_off
                      and d < im_w.bases_off + sosave.BASE_LEN * im_w.n_bases)
    hdr_bytes = sum(1 for d in diffs if d < u_lo)
    size_delta = len(nxt) - len(img)
    if not same:
        unit_bytes = grown_bytes = hdr_bytes = -1     # position-wise diff is meaningless
    return nxt, im_w, unit_bytes, grown_bytes, hdr_bytes, size_delta


def _row(r, mode, src, nops, narr, acc_save, acc_arr, ref, ref_sav, ub, gb, hb,
         im_w, sd):
    return {"round": r, "mode": mode, "src": src, "ops": nops, "arrivals": narr,
            "acc_save": acc_save, "acc_arr": acc_arr, "refused": ref,
            "ref_save": ref_sav, "unit_bytes": ub,
            "grown_bytes": gb, "hdr_bytes": hb, "size_delta": sd, "year": im_w.year,
            "n_units_img": im_w.n_units, "n_bases_img": im_w.n_bases,
            "found_units": im_w.found_units, "found_bases": im_w.found_bases,
            "sha": hashlib.sha256(bytes(im_w.data)).hexdigest()[:16]}


def measure(sav_path, map_path, log_path, trace_path):
    sv, ops, pref, rows, n_sched, earliest = socl.build(sav_path, log_path, trace_path)
    del pref, rows, n_sched
    runs = {}
    runs["container"] = run(sav_path, map_path, "container", ops=ops)
    runs["clean"] = run(sav_path, map_path, "container", poison=False, ops=ops)
    runs["uninterrupted"] = run(sav_path, map_path, "uninterrupted", poison=False,
                                ops=ops)
    runs["smuggle"] = run(sav_path, map_path, "smuggle", ops=ops)
    # PR #328 F1: the smuggler's OWN unexposed control. Blindness is only a measurement
    # if the same rival is run both with and without the image-only poison; compared
    # against the clean CONTAINER run it measured object reuse, nothing more.
    runs["smuggle_clean"] = run(sav_path, map_path, "smuggle", poison=False, ops=ops)
    for m in ("model", "nowrite", "late", "lift", "frozen", "split", "budgetcarry"):
        runs[m] = run(sav_path, map_path, m, poison=(m not in ("split", "budgetcarry")),
                      ops=ops)
    runs["rerun"] = run(sav_path, map_path, "container", ops=ops)
    b25 = socev.measure(sav_path, map_path)
    b25g = socev.gates(b25)
    names = ",".join(sorted(runs))
    return {"runs": runs, "ops": ops, "earliest": earliest,
        "size_law": _size_law(runs["container"]["rows"], sv),
        "accept_digest": accept_digest(runs["container"]["digest_rows"], names),
        "accept_digest_rerun": accept_digest(runs["rerun"]["digest_rows"], names),
        "b25_rows": b25["runs"][
        "container"]["rows"], "b25_green": all(ok for _, ok in b25g),
        "b25_gates": [(lab.split(":")[0], ok) for lab, ok in b25g],
        "identity": sow.build_image(sv) == sv.data, "sv": sv}


def render(m):
    L = []
    L.append("B26 THE COMPOSED RUN ACROS A SAVE/LOAD BOUNDARY (sim/composedsave.py; "
             "zero box)")
    L.append("")
    L.append("== table A: per-round rows of the honest run (mode=container, poisoned "
             "at the boundary) ==")
    L.append("round src ops arrivals acc_save acc_arr refused ref_save unit_bytes grown "
             "hdr size_delta year n_units_img n_bases_img found_units found_bases sha16")
    for r in m["runs"]["container"]["rows"]:
        L.append("%5d %-22s %3d %8d %8d %7d %7d %8d %10d %5s %3s %10d %4d %11d %11d "
                 "%11d %9d %s"
                 % (r["round"], r["src"], r["ops"], r["arrivals"], r["acc_save"],
                    r["acc_arr"], r["refused"], r["ref_save"], r["unit_bytes"],
                    "-" if r["grown_bytes"] < 0 else r["grown_bytes"],
                    "-" if r["hdr_bytes"] < 0 else r["hdr_bytes"], r["size_delta"],
                    r["year"], r["n_units_img"], r["n_bases_img"], r["found_units"],
                    r["found_bases"], r["sha"]))
    # G10's own object, printed before it is asserted (a number only the print reads is
    # decoration - PR #328 F2). sosave.BASE_LEN/UNIT_LEN are the shipped record sizes,
    # so the law is stated in the same constants the writer grows by.
    L.append("the container grows only through the writer: size_delta per round vs "
             "%d*(n_bases delta) + %d*(n_units delta): %s (G10 asserts this list)"
             % (sosave.BASE_LEN, sosave.UNIT_LEN, m["size_law"]))
    L.append("")
    L.append("== table B: THE CARRY census at the boundary (this parse vs an "
             "INDEPENDENT second parse) ==")
    for c in m["runs"]["container"]["carry"]:
        L.append("round %d: bytes %d; edits applied by the falsifier's own hand %d; "
                 "year %s cur %s tf %s; n_units %s n_bases %s; tiles equal %d/%d; "
                 "grown 304-B records equal %d/%d; rebuilt ledger %d vs image %d "
                 "(field-for-field vs a THIRD parse: %d of %d records equal); "
                 "parent tile read FROM THE IMAGE == poison: %s"
                 % (c["round"], c["bytes"], c["edits"], c["year"], c["cur"], c["tf"],
                    c["n_units"], c["n_bases"], c["tiles"], c["tile_n"], c["grown"],
                    c["grown_n"], c["rebuilt_ledger"][0], c["rebuilt_ledger"][1],
                    c["ledger_fields"][0], c["ledger_fields"][1],
                    c["parent_from_image"]))
        if c.get("eng_states") is not None:
            L.append("   mid-gesture engine at the split: pre-split %s vs rebuilt-from-"
                     "image %s -> installed for every later round; equal: %s"
                     % (c["eng_states"][0], c["eng_states"][1],
                        c["eng_states"][0] == c["eng_states"][1]))
    L.append("boundary edit offsets (first 8): %s" % (m["runs"]["container"]["boundary"]
                                                      ["edits_list"],))
    L.append("")
    L.append("== table C: CONFLUENCE (round-aligned boundary, nothing external) ==")
    cc = sow.diff_offsets(m["runs"]["clean"]["img"], m["runs"]["uninterrupted"]["img"])
    L.append("clean-with-boundary final %s (%d B) | uninterrupted final %s (%d B) | "
             "differing bytes %d" % (m["runs"]["clean"]["final_sha"][:16],
                                     len(m["runs"]["clean"]["img"]),
                                     m["runs"]["uninterrupted"]["final_sha"][:16],
                                     len(m["runs"]["uninterrupted"]["img"]), len(cc)))
    L.append("size: %d vs %d (the save is %d B)" % (len(m["runs"]["clean"]["img"]),
                                                    len(m["runs"]["uninterrupted"]["img"]),
                                                    len(m["sv"].data)))
    L.append("")
    L.append("== table D: THE NON-CARRY, measured (mid-gesture boundary) ==")
    d1 = sow.diff_offsets(m["runs"]["split"]["img"], m["runs"]["uninterrupted"]["img"])
    tA = m["runs"]["split"]["final_tiles"]
    tB = m["runs"]["uninterrupted"]["final_tiles"]
    moved = sorted(i for i in tA if tA[i] != tB.get(i))
    span = m["runs"]["split"]["unit_span"]
    L.append("split-vs-uninterrupted: units whose FINAL tile differs %d of %d; "
             "differing bytes %d (unit-array %d, header %d); split sha %s"
             % (len(moved), len(tA), len(d1),
                sum(1 for d in d1 if span[0] <= d < span[1]),
                sum(1 for d in d1 if d < span[0]),
                m["runs"]["split"]["final_sha"][:16]))
    d2 = sow.diff_offsets(m["runs"]["budgetcarry"]["img"],
                          m["runs"]["uninterrupted"]["img"])
    L.append("CONTROL budgetcarry (the spent word smuggled across the same split): "
             "differing bytes %d, sha %s == uninterrupted %s: %s"
             % (len(d2), m["runs"]["budgetcarry"]["final_sha"][:16],
                m["runs"]["uninterrupted"]["final_sha"][:16],
                m["runs"]["budgetcarry"]["final_sha"] ==
                m["runs"]["uninterrupted"]["final_sha"]))
    L.append("first diverging units %s: split %s vs uninterrupted %s"
             % (moved[:3], [tA[i] for i in moved[:3]],
                [tB.get(i) for i in moved[:3]]))
    hist = _diff_hist(m["runs"]["split"]["img"], m["runs"]["uninterrupted"]["img"],
                      span)
    m["split_hist"] = hist
    L.append("WHERE those bytes sit (record offset of the unit array): x_lo(+0) %d "
             "x_hi(+1) %d y(+2/+3) %d other-in-record %d header %d outside-the-array %d "
             "- so the non-carry is exactly the x LOW byte of each unit, not a tile "
             "pair and not a header field"
             % (hist["x_lo"], hist["x_hi"], hist["y"], hist["rec_other"],
                hist["header"], hist["outside"]))
    for c in m["runs"]["split"]["carry"]:
        if c.get("eng_states") is not None:
            L.append("mid-gesture engine at the split: pre-split %s vs rebuilt-from-"
                     "image %s -> the rebuilt one is installed for EVERY later round; "
                     "states equal: %s"
                     % (c["eng_states"][0], c["eng_states"][1],
                        c["eng_states"][0] == c["eng_states"][1]))
    L.append("")
    L.append("== table E: THE FALSIFIER, both channels (poison in the boundary image "
             "only) ==")
    fc = m["runs"]["container"]
    fs = m["runs"]["smuggle"]
    fu = m["runs"]["uninterrupted"]
    L.append("unit channel: final x of unit %d container %d | smuggle %d | clean %d "
             "(poison value %d); units whose final tile differs container-vs-clean %d, "
             "smuggle-vs-clean %d"
             % (POISON_UNIT, fc["final_tiles"][POISON_UNIT][0],
                fs["final_tiles"][POISON_UNIT][0],
                m["runs"]["clean"]["final_tiles"][POISON_UNIT][0], POISON_X,
                len([i for i in fc["final_tiles"]
                     if fc["final_tiles"][i] != m["runs"]["clean"]["final_tiles"].get(i)]),
                len([i for i in fs["final_tiles"]
                     if fs["final_tiles"][i] != fu["final_tiles"].get(i)])))
    sc = m["runs"]["smuggle_clean"]
    sm_sees = [i for i in fs["final_tiles"]
               if fs["final_tiles"][i] != sc["final_tiles"].get(i)]
    L.append("smuggler, EXPOSED to the image-only poison vs the SAME rival UNEXPOSED: "
             "final sha %s vs %s -> equal %s, final tiles diverge on %d units %s. So it "
             "is NOT blind to the bytes (PR #328 F1 retracts the old prose: the shipped "
             "instrument never handed it the poison). What its equality with the CLEAN "
             "container run (%s vs %s: %s) does measure is OBJECT REUSE: with the same "
             "bytes unpoisoned, keeping its ledger/engine/writer-base across the boundary "
             "reproduces the honest rebuilt run byte for byte."
             % (fs["final_sha"][:16], sc["final_sha"][:16],
                fs["final_sha"] == sc["final_sha"], len(sm_sees), sm_sees[:3],
                sc["final_sha"][:16], m["runs"]["clean"]["final_sha"][:16],
                sc["final_sha"] == m["runs"]["clean"]["final_sha"]))
    L.append("base channel (arrival composed AFTER the rebuild): %s"
             % [(a["round"], a["src"], a["tile"], a["own4"]) for a in fc["arr_rows"]])
    L.append("base channel IN THE BYTES THE RUN LEAVES BEHIND: final-image unit records "
             "carrying own4 0x%02x at the unit record's owner offset (sim/production"
             ".py:54 UNIT_OWNER = +%d), as (index, x, y): container %s, clean %s, "
             "smuggler(exposed) %s. Counted from the FINAL image, so it is a statement "
             "about the bytes the run leaves behind, not the bytes the arrival leg read. "
             "The +4 the first probe scanned is UNIT_FLAG, not the owner - a census of "
             "the wrong byte would have passed this gate silently"
             % (POISON_OWN4, soprod.UNIT_OWNER, fc["own4_recs"],
                m["runs"]["clean"]["own4_recs"], fs["own4_recs"]))
    L.append("frozen rival's post-boundary arrivals: %s"
             % [(a["round"], a["src"], a["tile"], a["own4"])
                for a in m["runs"]["frozen"]["arr_rows"] if a["round"] >= BOUNDARY])
    L.append("")
    L.append("== table F: rival signatures (SIGKEYS minus the mode label) ==")
    sig = _sig(m["runs"]["container"])
    L.append("container rows=%d digest %s" % (len(sig), m["runs"]["container"]["digest"]))
    for k in sorted(m["runs"]):
        if k in ("container", "rerun"):
            continue
        s2 = _sig(m["runs"][k])
        L.append("%-14s differs=%-5s n_rows=%d/%d digest %s final_sha %s"
                 % (k, s2 != sig, len(s2), len(sig), m["runs"][k]["digest"],
                    m["runs"][k]["final_sha"][:16]))
    L.append("")
    L.append("== table G: modeled-span accounting + anchors ==")
    bad = outside_modeled(m["sv"], m["runs"]["container"]["img"])
    L.append("record-aligned accounting, original save vs final container: %s "
             "(grown unit records %d B, grown base records %d B are MODELED wholesale)"
             % (bad, bad["grown_units"], bad["grown_bases"]))
    L.append("container digest %s | rerun digest %s | equal=%s | final sha %s / %s | "
             "images equal=%s" % (m["runs"]["container"]["digest"],
                                  m["runs"]["rerun"]["digest"],
                                  m["runs"]["container"]["digest"] ==
                                  m["runs"]["rerun"]["digest"],
                                  m["runs"]["container"]["final_sha"][:16],
                                  m["runs"]["rerun"]["final_sha"][:16],
                                  m["runs"]["container"]["img"] == m["runs"]["rerun"]["img"]))
    L.append("digest(B26 measured rows) %s | rerun %s | G9 pins ACCEPT_PIN %s"
             % (m["accept_digest"], m["accept_digest_rerun"], ACCEPT_PIN))
    return L



def _sig(res):
    return [tuple(str(r[k]) for k in SIGKEYS) for r in res["rows"]]


def accept_digest(rows, names):
    """The ACCEPT anchor render() PRINTS and G9 PINS (B25's law: a digest only cited
    in prose is a digest no mutant can break)."""
    return hashlib.sha256(("\n".join(rows) + "|" + names).encode()).hexdigest()[:16]


def outside_modeled(sv, img):
    """G7's accounting, RECORD-ALIGNED (a raw index diff of two images whose arrays
    grew is a shift artifact, not a measurement - that artifact is what the first
    draft of this rung printed as '2254 bytes outside a modeled span').

    Regions: everything before the unit array (index-aligned, the writer's modeled
    header fields excepted); the units array record by record (only a record's x/y
    pair +0..+3 may differ, B8's law); the base array record by record (only +0..+4,
    x/y/own4 - the founder's and the falsifier's fields); the tail, aligned to EOF."""
    fin = soct.parse_image(img)
    spans = list(sow.modeled_spans())
    out = {"header": 0, "unit_xy": 0, "unit_other": 0, "base_id": 0, "base_other": 0,
           "tail": 0, "grown_units": 0, "grown_bases": 0}
    hi = min(sv.units_off, fin.units_off)
    out["header"] = sum(1 for o in range(hi)
                        if sv.data[o] != img[o]
                        and not any(lo <= o < hi2 for lo, hi2 in spans))
    for i in range(sv.n_units):
        a = sv.units_off + sosave.UNIT_LEN * i
        b = fin.units_off + sosave.UNIT_LEN * i
        for k in range(sosave.UNIT_LEN):
            if sv.data[a + k] == img[b + k]:
                continue
            out["unit_xy" if k < 4 else "unit_other"] += 1
    for i in range(sv.n_bases):
        a = sv.bases_off + sosave.BASE_LEN * i
        b = fin.bases_off + sosave.BASE_LEN * i
        for k in range(sosave.BASE_LEN):
            if sv.data[a + k] == img[b + k]:
                continue
            out["base_id" if k < 5 else "base_other"] += 1
    out["grown_units"] = (fin.n_units - sv.n_units) * sosave.UNIT_LEN
    out["grown_bases"] = (fin.n_bases - sv.n_bases) * sosave.BASE_LEN
    tl = min(len(sv.data) - sv.tail_off, len(img) - fin.tail_off)
    out["tail"] = sum(1 for k in range(tl)
                      if sv.data[sv.tail_off + k] != img[fin.tail_off + k])
    return out


def gates(m):
    g = []
    c = m["runs"]["container"]
    cl = m["runs"]["clean"]
    un = m["runs"]["uninterrupted"]
    sm = m["runs"]["smuggle"]
    # G1 engine reuse. The comparison is HALF-WISE BY MEASUREMENT (PR #328 F3): this
    # run presses the appended arrival units too, so its TOTAL refusals are B25's plus
    # the arrivals (measured [67,67,67,68] against B25's [67,67,67,67] - the +1 is the
    # round-2 arrival). The SAVE-unit half, which is what the two runs have in common,
    # is what must be equal; both lists are printed so the +1 is visible, not hidden.
    acc_b26 = [r["acc_save"] for r in c["rows"][:RA]]
    acc_b25 = [r["accepted"] for r in m["b25_rows"][:RA]]
    ref_b26 = [r["ref_save"] for r in c["rows"][:RA]]
    ref_b25 = [r["refused"] for r in m["b25_rows"][:RA]]
    ok1 = (m["b25_green"] and acc_b26 == acc_b25 and ref_b26 == ref_b25 ==
           list(REF_SAVE_PIN))
    g.append(("G1 B25's own composed-move run is GREEN in-process (%s) and this run's "
              "per-round SAVE-unit accepted AND refused press counts equal its rows over "
              "the %d shared rounds: accepted %s == %s, refused %s == %s (pin %s); "
              "totals differ from B25 by the arrival units only (%s)"
              % (m["b25_gates"], RA, acc_b26, acc_b25, ref_b26, ref_b25,
                 list(REF_SAVE_PIN), [r["refused"] for r in c["rows"][:RA]]), ok1))

    # G2 identity + the recorded op stream applied
    ap = c["applied"]
    nops_run = min(len(m["ops"]), len(c["rows"]))
    rec_pre = [(o["pre"], o["pre"] + (1 if o["kind"] == "found" else -1))
               for o in m["ops"][:nops_run]]      # the LOG's own counts, never a guess
    ok2 = (m["identity"] and len(ap) == nops_run and
           all(a["landed"] for a in ap) and
           [a["kind"] for a in ap] == [o["kind"] for o in m["ops"][:nops_run]] and
           [(a["pre"], a["post"]) for a in ap] == rec_pre)
    g.append(("G2 a zero-op/zero-press/zero-append build equals the original save "
              "byte-for-byte, and the recorded m289 stream applied through the ledger "
              "lands %d/%d ops (the run's rounds) with kinds %s and the log's OWN "
              "pre->post counts %s == recorded %s"
              % (sum(1 for a in ap if a["landed"]), nops_run,
                 "".join(a["kind"][0] for a in ap),
                 [(a["pre"], a["post"]) for a in ap], rec_pre), ok2))

    # G3 carry
    cb = c["boundary"]
    # G3 carry. The ledger half is FIELD-WISE, not a length: F6 (PR #328) showed a
    # length equality passes on a ledger allocated from the wrong source entirely.
    ok3 = (cb["year"][0] == cb["year"][1] and cb["cur"] == cb["cur"] and
           cb["tf"] == cb["tf"] and cb["n_units"] == cb["n_units"] and
           cb["n_bases"] == cb["n_bases"] and cb["tiles"] == cb["tile_n"] and
           cb["grown"] == cb["grown_n"] and
           cb["rebuilt_ledger"][0] == cb["rebuilt_ledger"][1] and
           tuple(cb["ledger_fields"]) == LEDGER_FIELDS and
           cb["parent_from_image"] is True and cb["edits"] > 0)
    g.append(("G3 CARRY: at the boundary year/cur/tf/n_units/n_bases agree with an "
              "independent second parse, %d/%d unit tiles and %d/%d grown 304-B "
              "records equal it, the rebuilt ledger holds the image's bases FIELD-WISE "
              "(%d of %d records == a third parse, and %d == the image's count, pin %s), "
              "and the parent base's tile read FROM THE IMAGE is the poison "
              "(%d edits landed): %s"
              % (cb["tiles"], cb["tile_n"], cb["grown"], cb["grown_n"],
                 cb["ledger_fields"][0], cb["ledger_fields"][1],
                 cb["rebuilt_ledger"][0], list(LEDGER_FIELDS),
                 cb["edits"],
                 [cb["year"], cb["cur"], cb["tf"], cb["n_units"], cb["n_bases"]]),
             ok3))

    # G4 confluence
    d = sow.diff_offsets(cl["img"], un["img"])
    ok4 = (len(d) == 0 and cl["final_sha"] == un["final_sha"] and
           len(cl["img"]) == len(un["img"]))
    g.append(("G4 CONFLUENCE: with nothing external at the boundary the loaded run's "
              "final container is byte-identical to the uninterrupted run's (%d B, "
              "sha %s, differing bytes %d)" % (len(cl["img"]), cl["final_sha"][:16],
                                               len(d)), ok4))

    # G5 the non-carry is a number
    d1 = sow.diff_offsets(m["runs"]["split"]["img"], un["img"])
    d2 = sow.diff_offsets(m["runs"]["budgetcarry"]["img"], un["img"])
    span = m["runs"]["split"]["unit_span"]
    tA = m["runs"]["split"]["final_tiles"]
    tB = un["final_tiles"]
    moved = [i for i in tA if tA[i] != tB.get(i)]
    hist = _diff_hist(m["runs"]["split"]["img"], un["img"], span)
    m["split_hist"] = hist                      # table D prints this same dict
    est = [x["eng_states"] for x in m["runs"]["split"]["carry"]
           if x.get("eng_states") is not None]
    ok5 = (len(d1) > 0 and len(d2) == 0 and len(moved) == UNITS_SPLIT and
           len(d1) == BYTES_SPLIT == hist["total"] == hist["x_lo"] and
           (hist["x_hi"], hist["y"], hist["rec_other"], hist["header"],
            hist["outside"]) == SPLIT_HIST[1:] and
           sum(1 for x in d1 if x < span[0]) == 0 and
           m["runs"]["budgetcarry"]["final_sha"] == un["final_sha"] and
           len(est) == 1 and est[0][0] == est[0][1] == ENGINE_STATE)
    g.append(("G5 NON-CARRY MEASURED AND LOCALISED: a MID-GESTURE boundary diverges "
              "from the uninterrupted run in %d units and %d bytes, and the byte "
              "histogram by record offset is x_lo %d / x_hi %d / y %d / other-in-record "
              "%d / header %d / outside %d (pin %s) - the non-carry is the x LOW byte of "
              "every unit, nothing else; the control that smuggles the spent word across "
              "diverges by %d bytes and reproduces its sha; the split's rebuilt engine is "
              "installed for the later rounds and its state equals the pre-split one %s"
              % (len(moved), len(d1), hist["x_lo"], hist["x_hi"], hist["y"],
                 hist["rec_other"], hist["header"], hist["outside"],
                 list(SPLIT_HIST), len(d2), est[0][0] if est else None), ok5))

    # G6 the falsifier, both channels
    fc_t, fu_t = c["final_tiles"], cl["final_tiles"]   # vs the CLEAN run: the poison is
    # the only difference between them, so this counts what the falsifier moved
    ch_units = [i for i in fc_t if fc_t[i] != fu_t.get(i)]
    arr_c = [a for a in c["arr_rows"] if a["round"] >= BOUNDARY]
    arr_f = [a for a in m["runs"]["frozen"]["arr_rows"] if a["round"] >= BOUNDARY]
    sc = m["runs"]["smuggle_clean"]
    sm_sees = [i for i in sm["final_tiles"]
               if sm["final_tiles"][i] != sc["final_tiles"].get(i)]
    ok6 = (fc_t[POISON_UNIT][0] != fu_t[POISON_UNIT][0] and
           len(ch_units) == UNITS_POISONED and
           all(a["tile"] == list(POISON_TILE) for a in arr_c) and
           all(a["own4"] == POISON_OWN4 for a in arr_c) and
           len(arr_c) > 0 and
           all(a["tile"] != list(POISON_TILE) for a in arr_f) and
           (c["own4_final"], cl["own4_final"]) == OWN4_HITS and
           sm["own4_final"] == OWN4_SMUGGLE and
           len(sm_sees) == SMUGGLE_SEES and
           sc["final_sha"] == cl["final_sha"] and
           sm["final_sha"] != cl["final_sha"])
    g.append(("G6 FALSIFIER, BOTH CHANNELS AND BOTH WAYS: the unit poison reaches the "
              "final container (unit %d x: poisoned %d vs clean %d) and shifts %d units; "
              "the base poison reaches phase B's arrival through the container "
              "(round/src/tile/own4 %s) AND is counted in the bytes the run leaves "
              "behind - %d final unit "
              "records carry own4 0x%02x at the owner offset UNIT_OWNER +%d (pin %s), "
              "against %d in the clean run and %d in the exposed smuggler (pinned "
              "OWN4_SMUGGLE=%d: one of the container's two, and WHY one and not two is "
              "DECLARED OPEN, not explained); the EXPOSED smuggler "
              "diverges from the UNEXPOSED one (sha %s vs %s, %d units' final tiles "
              "moved - it is NOT blind, PR #328 F1) while the unexposed one reproduces "
              "the clean rebuilt run exactly (%s == %s), which is what OBJECT REUSE means "
              "here; the frozen rival's arrivals stay at %s"
              % (POISON_UNIT, fc_t[POISON_UNIT][0], fu_t[POISON_UNIT][0],
                 len(ch_units), [(a["tile"], a["own4"]) for a in arr_c],
                 c["own4_final"], POISON_OWN4, soprod.UNIT_OWNER, list(OWN4_HITS),
                 cl["own4_final"], sm["own4_final"], OWN4_SMUGGLE,
                 sm["final_sha"][:16], sc["final_sha"][:16],
                 len(sm_sees), sc["final_sha"][:16], cl["final_sha"][:16],
                 [(a["tile"], a["own4"]) for a in arr_f]), ok6))

    # G7 modeled spans
    bad = outside_modeled(m["sv"], c["img"])
    g.append(("G7 every differing byte between the original save and the final "
              "container lies in a MODELED span - header %d outside the writer's "
              "fields, unit records outside their x/y pair %d, base records outside "
              "+0..+4 %d, tail %d, while %d grown unit B and %d grown base B are "
              "modeled wholesale"
              % (bad["header"], bad["unit_other"], bad["base_other"], bad["tail"],
                 bad["grown_units"], bad["grown_bases"]),
              bad["header"] + bad["unit_other"] + bad["base_other"] + bad["tail"] == 0))

    # G8 rivals fail the same fit
    sig = _sig(c)
    fails = {}
    for k in sorted(m["runs"]):
        if k in ("container", "rerun"):
            continue
        fails[k] = _sig(m["runs"][k]) != sig
    ok8 = all(fails[k] for k in RIVAL_KEYS) and all(
        len(m["runs"][k]["rows"]) == len(sig) for k in RIVAL_KEYS)
    g.append(("G8 RIVALS fail the same fit, measured - %s (all differ from the "
              "container signature; every one of them still prints %d rows)"
              % ({k: fails[k] for k in RIVAL_KEYS}, len(sig)), ok8))

    # G9 determinism
    same = (c["digest"] == m["runs"]["rerun"]["digest"] and
            c["img"] == m["runs"]["rerun"]["img"] and
            c["final_sha"] == m["runs"]["rerun"]["final_sha"])
    pinned = (m["accept_digest"] == m["accept_digest_rerun"] == ACCEPT_PIN)
    g.append(("G9 determinism: the rerun reproduces the measured-row digest %s and the "
              "final container sha256 %s (%d B); the ACCEPT anchor of table G is %s "
              "(rerun %s), pinned to the literal %s"
              % (c["digest"], c["final_sha"][:16], len(c["img"]), m["accept_digest"],
                 m["accept_digest_rerun"], ACCEPT_PIN), same and pinned))

    # G10 the size law: arithmetic that was only printed (PR #328 F2)
    law = [tuple(x) for x in m["size_law"]]
    ok10 = (len(law) == len(c["rows"]) and all(a == b for a, b in law) and
            tuple(law) == SIZE_LAW)
    g.append(("G10 SIZE LAW, GATED NOT PRINTED (PR #328 F2): every round of the "
              "container run grows by exactly %d*(n_bases delta) + %d*(n_units delta) - "
              "observed/predicted %s, %d/%d rounds equal, list pinned to %s (the "
              "record sizes are sim/save.py's own BASE_LEN/UNIT_LEN, not literals in "
              "this gate)"
              % (sosave.BASE_LEN, sosave.UNIT_LEN, law,
                 sum(1 for a, b in law if a == b), len(law), list(SIZE_LAW)), ok10))

    return g


RIVAL_KEYS = ("model", "nowrite", "late", "lift", "frozen", "smuggle", "split",
              "budgetcarry")
# 'uninterrupted' is NOT a rival and was dropped from this set (PR #328 F10): it is the
# CONFLUENCE control G4 measures for byte-identity, and its signature differs from the
# container's only because the container is poisoned - counting it as a defect model
# proved nothing. 'clean' and 'smuggle_clean' are controls too, and 'rerun' is G9's.


def acceptance(m, results):
    """B21-B25's convention: the gates are APPENDED to the caller's list, and only
    sim/composedsave.py authors their text - `--b26` relays, it cannot disagree."""
    for name, ok in gates(m):
        results.append((name, ok))
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sim.composedsave")
    ap.add_argument("--sav", default=DEFAULT_SAV)
    ap.add_argument("--map", dest="map_path", default=DEFAULT_MAP)
    ap.add_argument("--log", default=DEFAULT_LOG)
    ap.add_argument("--trace", default=DEFAULT_TRACE)
    ap.add_argument("--out", default=None, help="write the final composed container here")
    a = ap.parse_args(argv)
    for p in (a.sav, a.map_path, a.log, a.trace):
        if not os.path.exists(p):
            print("FAIL B26: missing input %s" % p)
            return 1
    m = measure(a.sav, a.map_path, a.log, a.trace)
    lines = render(m)
    for line in lines:
        print(line)
    res = acceptance(m, [])
    bad = [name for name, ok in res if not ok]
    for name, ok in res:
        print(("  ok   " if ok else "  BAD  ") + name)
    if bad:
        print("FAIL B26: %d/%d gates failed: %s" % (len(bad), len(res), "; ".join(bad)))
        return 1
    print("PASS B26: %d/%d gates" % (len(res), len(res)))
    if a.out:
        with open(a.out, "wb") as fh:
            fh.write(m["runs"]["container"]["img"])
        print("wrote %s (%d B, sha256 %s)" % (a.out, len(m["runs"]["container"]["img"]),
                                              m["runs"]["container"]["final_sha"][:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
