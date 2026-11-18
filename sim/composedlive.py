#!/usr/bin/env python3
"""sim.composedlive - rung B24: the queue leg visiting a base FOUNDED BY THE
FOUNDER LEG IN THE WRITTEN CONTAINER.

BUILD_SPINE.md rung B24 (s287 authored this rung from main, as B14-B23 did).

B22 proved the CREATE leg reads a tile that was ALREADY in the save; B23 folded
a queue on a record the model SEEDED from a recorded trace. Neither ever folded
a queue on a record that exists in the container ONLY BECAUSE the founder leg
wrote it there during the run, and neither ran the op stream (foundings AND
destroys) against the WRITTEN base array while a queue leg consumed it.

This rung composes them through one writer:
  * the recorded m289 op stream (evidence/m289_gdb_raw.log: 7 FOUND + 2 DESTROY)
    applied to the base array IN THE IMAGE through sim.savewriter (B10's ledger,
    M282's record bytes, B13's last-slot destroy law as sim/composedrun.py
    applies it);
  * the B21 turn schedule (sim/composedrun.py feasible_schedules over the
    recorded n_bases curve of evidence/trace_m289_20261110_071759.jsonl) decides
    WHICH turn each logged op lands on - not invented here;
  * the B11/B12 queue law run through the SAME fold engine rung B23 uses
    (sim/composedturn.py fold(), parameterized for this rung; B23's own replay
    is re-run as gate G1 and its committed evidence is byte-identical through
    the parameterization);
  * the visited base is the record FOUNDED by op6 of the log (fac 1, tile
    (27,29)), seeded with a DECLARED fixture queue; its completions arrive as
    52-B units through the same writer, and the creation tile/owner are READ
    FROM THE IMAGE at every visit.

The falsifier poisons the founded record's tile/owner BYTES IN THE IMAGE ONLY
(the hook writes image bytes between boundaries and is never applied to model
state), so the LATER arrival carries the corrupted tile while the model-fed fold
is BLIND - and on the uncorrupted run the two folds are BYTE-IDENTICAL (G5),
which is what makes the blindness a measurement rather than rhetoric.

`python3 -m sim.selftest --b24 programs/saves/m54b_clean.SAV` relays THIS
module's claims; `python3 -m sim.composedlive --sav <sav> [--out f]` prints
them. NO /proc, NO gdb, NO Wine, NO game-binary load.
"""
import argparse
import hashlib
import os
import struct
import sys

from . import basefound as sobf
from . import composedrun as socr
from . import composedturn as soct
from . import production as soprod
from . import queue as soq
from . import save as sosave
from . import savewriter as sow

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(REPO, "evidence")
DEFAULT_SAV = os.path.join(REPO, "programs", "saves", "m54b_clean.SAV")
DEFAULT_LOG = os.path.join(EVID, "m289_gdb_raw.log")
DEFAULT_TRACE = os.path.join(EVID, "trace_m289_20261110_071759.jsonl")

# The visited base: op index 6 of the logged stream (fac 1, tile (27,29)).
# It survives BOTH logged destroys under B13's last-slot law - MEASURED by G4,
# not assumed - so its ledger index is stable for the whole fold window.
TARGET_OP = 6
TARGET = (27, 29)
TARGET_FAC = 1
# Declared fixture queue on the founded record. The SEED is a fixture (the log
# records fac/x/y/cnt only); the LAW is B11/B12's, executed verbatim by the
# fold engine - the same declaration style B23 made for its Korolev seed.
SEED_ST = 0
SEED_PEN = 4
SEED_SLOTS = [2, 2, 2] + [soq.SENTINEL] * 7
D0_DECL = 4          # declared per-visit income (fixture; B12's gate consumes it)
PRICE_DECL = 9       # declared price (B23/M58's recorded value for head 2, M72)
N_VISITS = 8         # visits: the founding turn and the seven following turns.
                     # MEASURED, not chosen to fit: the B21 schedule puts the
                     # founding at turn 22 and the SECOND logged destroy at turn
                     # 29, so an 8-visit window is the shortest one in which a
                     # completion crosses a compaction in the written container.
POISON_FROM = 6      # the poison is applied from this read on (persistently)
# Review #307 (rival law-isolation), MEASURED: these are the modes whose fold
# re-reads the CONTAINER, so for them the composition must feed the fold the
# container's bytes (target_raw / cont_read), exactly as the rung's own leg
# does. 'memory' is excluded by definition (its blindness is the claim);
# 'unfounded' never reaches the fold. Without this the locate rival's own write
# re-composed the record from the FOUNDER's clean constants, wiping the image
# poison before the tile walk ran - so the rival completed 0 arrivals and G8
# passed on the wrong mechanism (all eight pre_tile reads were (27,29)).
CONTAINER_READING_MODES = ("container", "frozenargs", "locate")
POISON = (1447, 1448, 0x5A)     # same corruption triple B23's G11 used
ST_POISON_VISIT = 4      # the second falsifier shape: storage poisoned at one
ST_POISON_VALUE = 12     # container read (the next visit must pay with it)
ST_OFF, MIRROR_OFF = 0x40, 0x98


def _target_index(ops, applied):
    """The ledger index the TARGET record occupies after the first `applied`
    ops, under B13's last-slot law (destroy removes the LAST record). Computed
    from the op stream, never hardcoded. None before the target is founded."""
    idx = 0
    for i in range(applied):
        if ops[i]["kind"] == "found":
            if i == TARGET_OP:
                return idx
            idx += 1
        elif idx > 0:
            idx -= 1
    return None


def _overrides(sv, led, target_idx, qspan, target_raw=None):
    """bases_override for one turn's write: the save's originals verbatim, then
    every grown ledger record as the founder's OWN bytes (M282). For the VISITED
    record there is a third source once the run has written it: `target_raw`,
    the bytes READ BACK OUT OF THE CONTAINER. Composing it from the founder's
    model bytes every turn would be the model-fed fold wearing a writer costume
    - the whole point of the rung is that the record the fold visits is the one
    the CONTAINER holds (its tile, its owner, its queue span, its corruption)."""
    ov = [{"identity": True} for _ in range(sv.n_bases)]
    for i in range(sv.n_bases, len(led.records)):
        r = led.records[i]
        ent = {"raw": sobf.record_bytes(r), "x": r["x"], "y": r["y"],
               "own4": r["own4"], "fac": r["fac"]}
        if target_idx is not None and i == target_idx:
            if target_raw is not None:
                ent["raw"] = bytearray(target_raw)
                b = soct.parse_image  # (kept local-import-free; fields below)
                ent["x"] = struct.unpack_from("<H", target_raw, 0)[0]
                ent["y"] = struct.unpack_from("<H", target_raw, 2)[0]
                ent["own4"] = target_raw[4]
                ent["fac"] = target_raw[5]
            ent["queue"] = dict(qspan)
        ov.append(ent)
    return ov


def _model_step(q, st, d0, price, args, drop_gate=False):
    """ONE visit of B11/B12's law, mirrored from sim/composedturn.fold (which
    owns the engine); used for the model-side fold G5 compares against."""
    add = d0 if (drop_gate or (d0 > 0 and q.head() != soq.SENTINEL)) else 0
    if st + add >= price:
        res = soprod.visit(q, args[0], args[1], args[2], st + add, 0, price)
        return res[1], res[2], "pay"
    return st + add, None, "bail"


def run(sv, ops, earliest, mode="container", poison=True, st_poison=False):
    """The composed 30-turn run. Ops land at the B21 schedule's turns; the four
    visits land right after the founding. mode:
      'container'  the rung: the fold re-parses the WRITTEN image every visit;
      'memory'     the fold fed from model state, never re-reading a container;
      'unfounded'  rival: the founder ops grow the model but NEVER the image;
      'frozenargs'/'addalways'/'price'/'locate'  fold-engine rivals.
    REVIEW #307 P2 (rival law-isolation): the image poison is applied in EVERY
    mode that reads the container except 'memory' (blind by definition) and
    'unfounded' (no visited record exists). The locate rival keeps the engine's
    passthrough: measured, WITHOUT it the rival completes all three arrivals,
    because the engine re-composes its r0 from clean seed bytes - the channel is
    what exposes it to the poisoned container. Returns a dict of everything the
    gates read."""
    price = 100 if mode == "price" else PRICE_DECL
    T = len(earliest)
    led = sobf.from_save(sv)
    k = 0
    found_turn = None
    target_idx = None
    img = None
    arrivals = []
    visits = []
    oprows = []
    target_raw = None      # the visited record's bytes AS THE CONTAINER HOLDS THEM
    for t in range(T):
        upto = earliest[t]
        pre_ops = []
        while k < upto:
            op = ops[k]
            pre = len(led)
            if op["kind"] == "found":
                landed = led.found(op["fac"], op["x"], op["y"])
                if k == TARGET_OP:
                    found_turn = t
                    target_idx = len(led) - 1
                pre_ops.append((op["kind"], pre, landed))
            else:
                moved = led.destroy(len(led) - 1)   # B13's last-slot law
                pre_ops.append((op["kind"], pre, moved is not None))
            k += 1
        seeding = found_turn is not None and t >= found_turn
        visit_no = (t - found_turn) if seeding and \
            (t - found_turn) < N_VISITS else None
        # ORDER MATTERS, and it is the rung's whole point: the container is
        # read BEFORE the turn's write composes it, otherwise every turn would
        # overwrite the record with the model's idea of it and the fold would
        # never see its own previous write (that ordering bug was caught by the
        # instrument: the container span stayed at the seed value forever).
        # THE FALSIFIER'S HAND, on the composition's own bytes: the turn the
        # visit counter reaches POISON_FROM, the VISITED RECORD's tile/owner are
        # REWRITTEN IN THE IMAGE (addressed BY LEDGER POSITION, never by tile,
        # so no tile lookup can ever hide the corruption). This happens BETWEEN
        # turns, on the bytes the game's next read is about to consume - model
        # state is never touched, so only a fold that READS THE CONTAINER can
        # see it. (Ordering, learned the hard way: applying it after the turn's
        # write would land it one boundary late and the falsifier would be
        # decoration.)
        # REVIEW #307 P2: the poison is applied to EVERY mode that reads the
        # container, not just 'container'. It was gated on mode=="container"
        # while two rivals were CALLED with poison=True - so `frozenargs`
        # received clean bytes a correct fold would also produce, and the
        # tile-locating `locate` rival died for a reason unrelated to its own
        # law. Excluded are only the two modes that must stay blind by
        # definition: 'memory' (never re-reads the container - the whole point
        # of the blindness claim) and 'unfounded' (the founder never writes the
        # array at all, so there is no visited record to poison).
        # Second falsifier shape: an INCOME/STORAGE corruption. It proves the
        # read-back loop (the container's st is the next visit's input), which
        # the tile/owner corruption alone cannot - that one only moves the
        # CREATED RECORD's bytes, never a gate (declared in G7, measured here).
        if (mode == "container" and st_poison and img is not None and seeding and
                visit_no is not None and visit_no == ST_POISON_VISIT):
            _ims = soct.parse_image(img)
            if target_idx < _ims.n_bases:
                mut = bytearray(img)
                offs = _ims.bases_off + sosave.BASE_LEN * target_idx
                struct.pack_into("<i", mut, offs + ST_OFF, ST_POISON_VALUE)
                img = bytes(mut)
        if (poison and mode in CONTAINER_READING_MODES and img is not None
                and seeding and visit_no is not None
                and visit_no >= POISON_FROM):
            _im0 = soct.parse_image(img)
            if target_idx < _im0.n_bases:
                mut = bytearray(img)
                off0 = _im0.bases_off + sosave.BASE_LEN * target_idx
                struct.pack_into("<HH", mut, off0, POISON[0], POISON[1])
                mut[off0 + 4] = POISON[2]
                img = bytes(mut)
        cont_read = None
        if mode in CONTAINER_READING_MODES and seeding and img is not None:
            imp_r = soct.parse_image(img)
            # BOUNDS, not turn numbers: the founding turn's "previous image"
            # predates the array slot, and reading off the end of the base
            # array yields TAIL BYTES - that was the instrument's bug (the seed
            # span got overwritten with zeros before it was ever written).
            if target_idx < imp_r.n_bases:
                off_r = imp_r.bases_off + sosave.BASE_LEN * target_idx
                cont_read = imp_r.data[off_r:off_r + sosave.BASE_LEN]
        if not seeding:
            qspan = {}
        elif cont_read is not None:
            target_raw = cont_read
            spx = soct.spans_of(cont_read)
            qspan = {"st": spx["st"], "pen": spx["pen"],
                     "slots": spx["slots"], "mirror": spx["mirror"]}
        elif visit_no == 0 or visits == [] and mode == "unfounded":
            qspan = {"st": SEED_ST, "pen": SEED_PEN, "slots": list(SEED_SLOTS),
                     "mirror": SEED_ST}
        elif mode == "unfounded":
            qspan = visits[-1]["span_after"]
        else:
            qspan = visits[-1]["span_after"]
        if mode == "unfounded":
            # rival: the founder NEVER writes the array - the image keeps the
            # save's ORIGINAL base count while the ledger grows.
            img_next = img if img is not None else sv.data
            oprows.append({"t": t, "ops": pre_ops, "led_n": len(led),
                           "img_n": soct.parse_image(img_next).n_bases,
                           "size": len(img_next)})
            img = img_next
            continue
        img_next = sow.build_image(sv, bases_override=_overrides(
            sv, led, target_idx if seeding else None, qspan,
            target_raw if seeding else None),
            append_units=arrivals or None)
        imp = soct.parse_image(img_next)
        oprows.append({"t": t, "ops": pre_ops, "led_n": len(led),
                       "img_n": imp.n_bases, "size": len(img_next)})
        img = img_next
        if visit_no is None:
            continue
        # ---- the visit, run by B23's fold engine on a ONE-boundary window ----
        # The record the visit operates on. THE CONTAINER'S OWN BYTES, not the
        # model's idea of them - rebuilding it from TARGET's constants would
        # (and did, first pass) silently erase any corruption the container
        # carries, making the falsifier decoration. Only the founding turn,
        # where no container copy exists yet, composes it from the founder's
        # bytes plus the declared fixture span.
        if target_raw is not None and mode != "memory":
            seed_rec = bytearray(target_raw)
        else:
            seed_rec = bytearray(sobf.record_bytes({"x": TARGET[0], "y": TARGET[1],
                                                    "own4": TARGET_FAC,
                                                    "fac": TARGET_FAC}))
        struct.pack_into("<i", seed_rec, ST_OFF, qspan["st"])
        struct.pack_into("<i", seed_rec, soq.PENDING_OFF, qspan["pen"])
        for kk, vv in enumerate(qspan["slots"]):
            struct.pack_into("<i", seed_rec, soq.HEAD_OFF + 4 * kk, vv)
        struct.pack_into("<i", seed_rec, MIRROR_OFF, qspan["mirror"])

        def ovs(_sv, _ki, _seed, qspan2, _app, _led=led, _ti=target_idx):
            sq = dict(qspan2) if qspan2 else dict(qspan)
            return _overrides(_sv, _led, _ti, sq, target_raw)

        # hand the fold the image as it now STANDS (poison included), so its
        # first read is the container's bytes, not a fresh composition
        bnds = [{"r": 0, "before": seed_rec, "after": seed_rec}]
        vv, ii, aa, fin = soct.fold(
            sv, bnds, mode=mode,
            pos=True, overrides_fn=ovs, d0s=[D0_DECL], price=price,
            seed_rec=seed_rec, tile_at=lambda: TARGET, slot_i=target_idx,
            prior_units=arrivals, start_img=img,
            passthrough=(mode == "locate"))  # REVIEW #307 P2 asked to drop this
        # from the locate rival ("preserve queue writes so only the claimed law
        # differs"). MEASURED, the suggestion was wrong: without the channel the
        # rival COMPLETES ALL THREE ARRIVALS (locate=PASS, G8 red) because the
        # engine re-composes its r0 from the CLEAN seed bytes and the tile walk
        # never sees the container's poisoned bytes. passthrough is therefore
        # not a second law - it is the rival's READ SOURCE, what makes it look
        # at the same poisoned container the rung's fold looks at. Law-isolation
        # argument: every mode here already re-writes the image from the fold's
        # own in-window state (the rung's 'container' leg included), so
        # passthrough does not suppress anything the clean run keeps; and the
        # channel is load-bearing in the harness (MU6 removes it and G8 goes red
        # at exactly the rival the review said was confounded).
        v = vv[0]
        # The fold APPENDS to the list object it was handed (it accumulates
        # its own arrivals); we passed a COPY, so aa is the complete, ordered
        # arrival list for the run so far - adopt it, do not re-append it.
        arrivals = list(aa)
        # re-read the visited record FROM THE IMAGE THE FOLD WROTE: the next
        # turn's write, and the poison's survival, ride on these bytes
        target_raw = imf0_raw = None
        _im = soct.parse_image(fin)
        _off = _im.bases_off + sosave.BASE_LEN * target_idx
        target_raw = _im.data[_off:_off + sosave.BASE_LEN]
        del imf0_raw
        # read the WRITTEN span back out of the image the fold produced
        imf = soct.parse_image(fin)
        off = imf.bases_off + sosave.BASE_LEN * target_idx
        spw = soct.spans_of(imf.data[off:off + sosave.BASE_LEN])
        visits.append({
            "visit": visit_no, "t": t, "verdict": v["verdict"],
            "made": v["made"], "pre": soct.spans_of(seed_rec),
            "span_after": {"st": spw["st"], "pen": spw["pen"],
                           "slots": spw["slots"], "mirror": spw["mirror"]},
            "pre_tile": (struct.unpack_from("<H", seed_rec, 0)[0],
                         struct.unpack_from("<H", seed_rec, 2)[0],
                         seed_rec[4]),
            "target_idx_in_img": target_idx, "img_n_bases": imf.n_bases,
            "img_n_units": imf.n_units, "final_img": fin})
        img = fin
    # model-side single pass with the same declared fixture: the BLIND fold
    qq = soq.Queue(slots=list(SEED_SLOTS), pending=SEED_PEN)
    st = SEED_ST
    marrivals, mvisits = [], []
    for j in range(N_VISITS):
        st2, made_v, verdict = _model_step(qq, st, D0_DECL, PRICE_DECL,
                                           (TARGET[0], TARGET[1], TARGET_FAC))
        if made_v is not None:
            marrivals.append(made_v)
        mvisits.append({"visit": j, "verdict": verdict, "made": made_v is not None,
                        "span_after": {"st": st2, "pen": qq.pending,
                                       "slots": list(qq.slots), "mirror": st2}})
        st = st2
    return {"visits": visits, "mvisits": mvisits, "arrivals": arrivals,
            "marrivals": marrivals, "oprows": oprows, "led": led, "k": k,
            "found_turn": found_turn, "target_idx": target_idx,
            "final_img": img, "price": price}


def build(sav_path, log_path, trace_path):
    sv = sosave.parse(sav_path)
    start, rows = socr.load_curve(trace_path)
    ops, pref = socr.op_stream(log_path, sv.n_bases)
    after_t = [r["nb_a"] for r in rows]
    n_sched, earliest = socr.feasible_schedules(pref, after_t)
    if earliest is None:
        raise SystemExit("B24: no schedule reproduces the recorded curve")
    return sv, ops, pref, rows, n_sched, earliest


def compute(sav_path, log_path, trace_path, b23_line):
    sv, ops, pref, rows, n_sched, earliest = build(sav_path, log_path, trace_path)
    out = []

    def g(label, ok, detail=""):
        out.append((label, bool(ok), detail))
        return bool(ok)

    clean = run(sv, ops, earliest, mode="container", poison=False)
    pois = run(sv, ops, earliest, mode="container", poison=True)
    mem = run(sv, ops, earliest, mode="memory")
    ft, tix = clean["found_turn"], clean["target_idx"]

    # G1 - rung B23 re-runs green IN-PROCESS (the composition did not fork it)
    g("G1 rung B23 replay green (engine reused, not forked)",
      b23_line.startswith("PASS B23"), b23_line)

    # G2 - every logged op's recorded pre-count matches the ledger, and at
    # EVERY turn the WRITTEN image's parsed n_bases equals the ledger count.
    cnt = sv.n_bases
    fid2 = 0
    for o in ops:
        fid2 += 1 if o["pre"] == cnt else 0
        cnt += 1 if o["kind"] == "found" else -1
    mism = sum(1 for r in clean["oprows"] if r["led_n"] != r["img_n"])
    g("G2 ops %d/%d recorded pre-counts; every turn image n_bases == ledger"
      % (fid2, len(ops)),
      fid2 == len(ops) and len(ops) == 9 and mism == 0 and clean["k"] == 9,
      "pre-count fidelity %d/%d, per-turn container mismatches %d/%d turns, "
      "ops applied %d/%d, schedule choices %d"
      % (fid2, len(ops), mism, len(clean["oprows"]), clean["k"], len(ops),
         n_sched))

    # G3 - every grown record in the FINAL image is the founder's own bytes
    # (except the visited one, whose tile/owner the poison rewrote and whose
    # queue span the fold wrote), and the array grew through the writer only.
    fin = soct.parse_image(pois["final_img"])
    led = clean["led"]
    grown_ok, grown_rows = True, []
    for i in range(sv.n_bases, fin.n_bases):
        r = led.records[i]
        rec = fin.data[fin.bases_off + sosave.BASE_LEN * i:
                       fin.bases_off + sosave.BASE_LEN * (i + 1)]
        want = sobf.record_bytes(r)
        if i == tix:
            sp_f = soct.spans_of(rec)
            want_sp = pois["visits"][-1]["span_after"]   # what the last fold wrote
            ok = (rec[4] == POISON[2] and rec[5] == r["fac"] and   # +4 owner, +5 fac
                  tuple(struct.unpack_from("<HH", rec, 0)) == POISON[:2] and
                  all(sp_f[k] == want_sp[k] for k in ("st", "pen", "slots",
                                                      "mirror")))
            why = "poisoned tile/owner + queue span == the fold's last write %s" % (
                {k: sp_f[k] for k in ("st", "pen")},)
        else:
            ok = rec == want
            why = "founder bytes verbatim"
        grown_rows.append((i, r["fac"], r["x"], r["y"], ok, why))
        grown_ok &= ok
    grew = (fin.n_bases == len(led.records) and
            len(pois["final_img"]) - len(sv.data) ==
            sosave.BASE_LEN * (fin.n_bases - sv.n_bases) +
            sosave.UNIT_LEN * len(pois["arrivals"]))
    g("G3 grown records in the image == the founder's bytes; array grew via writer",
      grown_ok and grew,
      "%d grown records all-identical=%s (%s); final n_bases %d == ledger %d; "
      "size delta %d B = %d*304 + %d*52"
      % (len(grown_rows), all(x[4] for x in grown_rows),
         "; ".join("idx %d fac %d (%d,%d) %s: %s" % x for x in grown_rows),
         fin.n_bases, len(led.records),
         len(pois["final_img"]) - len(sv.data),
         fin.n_bases - sv.n_bases, len(pois["arrivals"])))

    # G4 - the two logged DESTROYS executed IN THE WRITTEN ARRAY, measured at
    # their turns (which slot, which record, how the image shrank); the visited
    # record SURVIVES both and its slot NEVER MOVES; its fold-written queue span
    # survives the compaction unchanged; the FINAL destroy lands AFTER the last
    # visit, so the fold itself never has to re-locate a moved record.
    # RETRACTION of this rung's first draft: it claimed the compaction MOVES the
    # fold's target. Measured FALSE - under B13's last-slot law the victim is
    # always the newest slot, and every record the log destroyed was founded
    # after the visited one. What is NOT trivial, and what this gate measures,
    # is that the destroy happens between two FOLD turns' writes and the visited
    # record's bytes (tile, owner, queue span) come through it intact.
    destroy_idx = [i for i, o in enumerate(ops) if o["kind"] == "destroy"]
    tix_seq = [v["target_idx_in_img"] for v in clean["visits"]]
    nb_seq = [r["img_n"] for r in clean["oprows"]]
    sz_seq = [r["size"] for r in clean["oprows"]]
    # which ledger slot each destroy removed and WHAT that record held
    victims, led3, k3 = [], sobf.from_save(sv), 0
    for t3 in range(len(earliest)):
        while k3 < earliest[t3]:
            if ops[k3]["kind"] == "found":
                led3.found(ops[k3]["fac"], ops[k3]["x"], ops[k3]["y"])
            else:
                slot = len(led3) - 1
                r3 = led3.records[slot]
                victims.append((t3, slot, r3["fac"], r3["x"], r3["y"]))
                led3.destroy(slot)
            k3 += 1
    # the span written before the t=29 compaction, and read back after it
    v_before = [v for v in clean["visits"] if v["t"] < 29]
    v_at = [v for v in clean["visits"] if v["t"] >= 29]
    span_survived = (bool(v_at) and
                     {k: v_at[-1]["pre"][k] for k in ("st", "pen", "slots")} ==
                     {k: v_before[-1]["span_after"][k] for k in ("st", "pen", "slots")})
    # per-destroy size measurement: expected = the same turn's size WITHOUT the
    # op applied (the record the last-slot destroy removed is the one founded
    # last) - it is NOT enough to compare two turns, because the unit array
    # grows in between and both offsets move together (first pass read that as
    # "no shrink": max(sz) was taken from a LATER, unit-grown image).
    # Two ledgers, SAME turn: one where the logged destroys were applied, one
    # where they were skipped (only the founds). The image's size difference is
    # the number of records the destroys removed x 304 B - that is the array
    # shrinking IN THE CONTAINER, measured at the turn it happened, with the
    # unit array's own growth cancelled out because BOTH ledgers see it.
    led4, led5, k4 = sobf.from_save(sv), sobf.from_save(sv), 0
    shrink_ok, exp = True, []
    for t4, r4 in enumerate(clean["oprows"]):
        while k4 < earliest[t4]:
            if ops[k4]["kind"] == "found":
                led4.found(ops[k4]["fac"], ops[k4]["x"], ops[k4]["y"])
                led5.found(ops[k4]["fac"], ops[k4]["x"], ops[k4]["y"])
            else:
                led4.destroy(len(led4) - 1)      # the law: last slot removed
            k4 += 1
        if any(o[0] == "destroy" for o in r4["ops"]):
            n_app = sum(1 for v in clean["visits"]
                        if v["t"] <= t4 and v["made"])
            want4 = (len(sv.data)
                     + sosave.BASE_LEN * (len(led4.records) - sv.n_bases)
                     + sosave.UNIT_LEN * n_app)
            missing = (len(led5.records) - len(led4.records)) * sosave.BASE_LEN
            exp.append((t4, r4["size"], want4, missing))
            if r4["size"] != want4 or missing < sosave.BASE_LEN:
                shrink_ok = False
    shrink = (shrink_ok and len(exp) == 2 and
              nb_seq[-1] == 23 and fin.n_bases == 23)
    cond4 = {"2 destroys": len(destroy_idx) == 2,
             "2 victims measured": len(victims) == 2,
             "no victim at the visited slot": all(x[1] != tix for x in victims),
             "visited index stable": all(x == tix for x in tix_seq),
             "shrunk at both turns": shrink,
             "span survives": span_survived,
             "a visit at/after t29": bool(v_at),
             "last victim = slot 23": victims[-1][1] == 23}
    g("G4 destroys run IN THE IMAGE: array -304 B at t=29, visited slot + span intact",
      all(cond4.values()),
      "destroys at op idx %s removed %s (visited slot %d); target index per "
      "visit %s (founding turn %d); image n_bases peak %d -> final %d; "
      "image size at the destroy turns (size, size implied by the applied "
      "ledger, bytes the skipped-destroy ledger would add) %s; conditions %s"
      % (destroy_idx, ["t%d slot%d fac%d (%d,%d)" % v for v in victims],
         tix, tix_seq, ft, max(nb_seq), nb_seq[-1],
         exp,
         {k: v for k, v in cond4.items() if not v} or "ALL"))

    # G5 - uncorrupted run: the CONTAINER fold and the MODEL fold agree
    # verdict-for-verdict, span-for-span, arrival-for-arrival. This is what
    # makes G7's divergence under an image-only poison a measurement.
    same_verdict = [v["verdict"] for v in clean["visits"]] == \
        [v["verdict"] for v in mem["visits"]]
    same_span = all(c["span_after"] == m["span_after"]
                    for c, m in zip(clean["visits"], mem["visits"]))
    same_arr = clean["arrivals"] == mem["arrivals"]
    sha_c = hashlib.sha256(clean["final_img"]).hexdigest()
    g("G5 uncorrupted: container fold == model fold (verdicts, spans, arrivals)",
      same_verdict and same_span and same_arr and
      len(clean["arrivals"]) == 3,
      "verdicts %s; spans equal %s; arrivals equal %s (n=%d); clean image sha %s"
      % (",".join(v["verdict"][0] for v in clean["visits"]), same_span,
         same_arr, len(clean["arrivals"]), sha_c[:16]))

    # G6 - the three arrivals ride the container at the units array END, in
    # order, each equal to B12's producer fed with the tile/owner READ FROM THE
    # IMAGE at that visit (clean founded values on the uncorrupted run).
    im0 = soct.parse_image(clean["final_img"])
    arr_slice = im0.data[im0.units_off + sosave.UNIT_LEN * sv.n_units:
                         im0.units_off + sosave.UNIT_LEN * (sv.n_units + 3)]
    want_clean = [soprod.create_record(TARGET[0], TARGET[1], SEED_SLOTS[j],
                                       TARGET_FAC) for j in range(3)]
    got = [arr_slice[sosave.UNIT_LEN * j: sosave.UNIT_LEN * (j + 1)]
          for j in range(3)]
    g("G6 three arrivals at the units array END from IMAGE fields, n_units %d->%d"
      % (sv.n_units, im0.n_units),
      got == clean["arrivals"] == want_clean and im0.n_units == sv.n_units + 3,
      "arrival j==%d carries tile/owner from the image (%d,%d fac %d, head %d); "
      "image n_units %d->%d"
      % (0, TARGET[0], TARGET[1], TARGET_FAC, SEED_SLOTS[0], sv.n_units,
         im0.n_units))

    # G7 - THE FALSIFIER: the poison lives ONLY in the container bytes, applied
    # between the fifth and the sixth visit - i.e. AFTER the second arrival and
    # BEFORE the third, which the third completion therefore CARRIES. The
    # model-fed fold (same laws, same fixture, never re-reading the image)
    # stays BLIND: its third arrival keeps the founded tile. The VERDICT
    # SEQUENCE IS DECLARED IDENTICAL on purpose - the poison moves the tile,
    # not the gate - so the gate is byte-level, not verdict-level.
    pv, mv = pois["visits"], mem["visits"]
    n_arr = len(pois["arrivals"])
    carried = n_arr == 3 and \
        pois["arrivals"][2][0:4] == struct.pack("<HH", POISON[0], POISON[1]) and \
        pois["arrivals"][2][14] == POISON[2]
    blind = len(mem["arrivals"]) == 3 and \
        mem["arrivals"][2][0:4] == struct.pack("<HH", TARGET[0], TARGET[1]) and \
        mem["arrivals"][2][14] == TARGET_FAC
    # The tile/owner corruption moves the CREATED RECORD's bytes, NOT the queue
    # span or the verdict (the poison never touches +0x40/+0x4c/+0x50) - so
    # spans and verdicts are DECLARED equal here, and the load-bearing half of
    # "the container is read back" is proved by the storage-poison probe below.
    spans_equal = all(p["span_after"] == m["span_after"] for p, m in zip(pv, mv))
    stp = run(sv, ops, earliest, mode="container", poison=False, st_poison=True)
    st_verdicts = [v["verdict"] for v in stp["visits"]]
    # Measured, not assumed: at this fixture's shape (3 queued items, income 4,
    # price 9) an inflated storage cannot manufacture a 4th completion - the
    # queue runs dry. What the storage poison DOES move is the VERDICT TABLE and
    # therefore WHICH visit each completion lands on, plus the arrival count
    # among the visits that were bails on the clean run.
    st_pos_clean = [v["t"] for v in clean["visits"] if v["made"]]
    st_pos_pois = [v["t"] for v in stp["visits"] if v["made"]]
    st_diverge = (st_verdicts != [v["verdict"] for v in clean["visits"]] and
                  st_pos_pois != st_pos_clean and
                  # REVIEW #307 P2: this filter read the RUN TURN (`t` is 22..29)
                  # against a VISIT INDEX (4), so it selected no rows and all()
                  # passed on an empty list - a decorative half-condition. It now
                  # filters by visit index and compares every promised span
                  # field, not just storage.
                  all((v["span_after"]["st"], v["span_after"]["pen"],
                       v["span_after"]["slots"], v["span_after"]["mirror"])
                      == (m["span_after"]["st"], m["span_after"]["pen"],
                          m["span_after"]["slots"], m["span_after"]["mirror"])
                      for v, m in zip(stp["visits"], clean["visits"])
                      if v["visit"] < ST_POISON_VISIT) and
                  any(v["visit"] >= ST_POISON_VISIT for v in stp["visits"]))
    verdicts_same = [v["verdict"] for v in pv] == [v["verdict"] for v in mv]
    want3p = soprod.create_record(POISON[0], POISON[1], SEED_SLOTS[2], POISON[2])
    third_in_img = (fin.data[fin.units_off + sosave.UNIT_LEN * (sv.n_units + 2):
                             fin.units_off + sosave.UNIT_LEN * (sv.n_units + 3)]
                    == want3p)
    arr2_of_pois = fin.data[fin.units_off + sosave.UNIT_LEN * (sv.n_units + 2):
                            fin.units_off + sosave.UNIT_LEN * (sv.n_units + 3)]
    first_two_clean = all(
        fin.data[fin.units_off + sosave.UNIT_LEN * (sv.n_units + j):
                  fin.units_off + sosave.UNIT_LEN * (sv.n_units + j + 1)][:4] ==
        struct.pack("<HH", TARGET[0], TARGET[1]) for j in (0, 1))
    g("G7 falsifier bites: image-only poison carried by the THIRD arrival; model fold blind",
      carried and blind and spans_equal and verdicts_same and
      pois["arrivals"][2] == want3p and third_in_img and
      arr2_of_pois == want3p and first_two_clean and st_diverge,
      "verdicts container==model %s (declared identical); arrival3 carries the "
      "poison %s and is the image's last unit record %s; model arrival3 stays "
      "clean %s; queue spans DECLARED equal %s (the poison moves the created "
      "record, never a gate); the image's own 3rd unit record carries it %s "
      "while its first two stay clean %s; storage poison at visit %d DOES move "
      "the verdict table (%s vs %s) and moves the completion turns %s -> %s, "
      "while every visit before the poison is untouched"
      % (verdicts_same, carried, third_in_img, blind, spans_equal,
         arr2_of_pois == want3p, first_two_clean, ST_POISON_VISIT,
         ",".join(v[0] for v in st_verdicts),
         ",".join(v["verdict"][0] for v in clean["visits"]),
         st_pos_clean, st_pos_pois))

    # G8 - rivals FAIL the same fit (each is the same composed run with ONE law
    # or ONE source mutated).
    rivals = {}
    pr = run(sv, ops, earliest, mode="price", poison=False)
    rivals["price100"] = len(pr["arrivals"]) == 0
    na = run(sv, ops, earliest, mode="noadd", poison=False)
    rivals["noadd"] = len(na["arrivals"]) == 0
    np_ = run(sv, ops, earliest, mode="nopop", poison=False)
    # REVIEW #307 P2: the old form ORed two half-conditions, so a rival that
    # accidentally popped NORMALLY (3 arrivals AND a pending sequence identical
    # to the clean run) still scored as a failed rival. Both halves are now
    # REQUIRED to be false for a clean queue: arrivals must not be 3, and the
    # pending sequence must actually DIFFER. (Repaired by mutation, not by
    # reading: MU6b restores normal popping in the engine's nopop branch and
    # reddens G8 - see scripts/b24_mutate.py.)
    np_pen = [v["span_after"]["pen"] for v in np_["visits"]]
    clean_pen = [v["span_after"]["pen"] for v in clean["visits"]]
    rivals["nopop"] = len(np_["arrivals"]) != 3 and np_pen != clean_pen
    # (frontinsert is NOT claimed as a rival here: measured on this driver it
    # PASSES - the engine's append order only shows up in the fold's own image,
    # which the composition replaces every turn. A rival that cannot fail is
    # decoration (trap 24), so it is dropped, not kept.
    # frozenargs is RETIRED THE SAME WAY, and by the SAME law - review #307's
    # demand that every container-reading rival be fed the CONTAINER'S bytes
    # (rather than the founder's constants, which is what made it fail before)
    # MEASURED it degenerate: at this rung's ONE-BOUNDARY-per-visit granularity
    # the engine freezes the creation args to the seed record, which is the
    # window-open container copy, and nothing inside the window moves the
    # tile/owner - so the rival reproduces the true fit exactly (arrivals=3,
    # arrival 3 carrying the poisoned tile (1447,1448)/owner 0x5a, identical to
    # the rung's poisoned leg). A cached-identity fold is indistinguishable from
    # a re-reading fold at this granularity: the claim that creation args are
    # read from the container is carried instead by G7 (the third arrival
    # carries what the CONTAINER held at that visit) and by MU2. Measured
    # outcome printed in the detail so the retirement is falsifiable.)
    fzr = run(sv, ops, earliest, mode="frozenargs", poison=True)
    frozen_note = ("frozenargs retired: reproduces the fit (arrivals=%d, a3=%s)"
                   % (len(fzr["arrivals"]),
                      struct.unpack("<HH", fzr["arrivals"][2][0:4]).__str__()
                      if len(fzr["arrivals"]) == 3 else "-"))
    unf = run(sv, ops, earliest, mode="unfounded")
    rivals["unfounded"] = unf["visits"] == [] and \
        unf["oprows"][-1]["img_n"] == sv.n_bases and \
        unf["oprows"][-1]["led_n"] == 23
    # REVIEW #307 P2 asked whether the locate rival's failure came from its own
    # law or from the passthrough channel. MEASURED: with the channel removed
    # the rival COMPLETES 3 ARRIVALS (locate=PASS, G8 red) - the channel is what
    # shows it the poisoned container, and the image poison now reaches this
    # mode at all. So the answer is the review's own criterion: with the read
    # SOURCE identical to the rung's, the only difference left is WHERE the fold
    # looks for the record, and that difference is decisive - the tile walk
    # raises "not located" and the record cannot be addressed. The mode of
    # failure is printed in the gate detail, not hidden behind "arrivals<3".
    loc_note = "?"
    try:
        lr = run(sv, ops, earliest, mode="locate", poison=True)
        loc_note = "ran, arrivals=%d" % len(lr["arrivals"])
        rivals["locate"] = len(lr["arrivals"]) < 3
    except AssertionError as e:
        loc_note = "cannot address the record (%s)" % str(e)[:46]
        rivals["locate"] = True
    g("G8 five rivals fail the same fit (sixth, frozenargs, measured DEGENERATE)",
      all(rivals.values()),
      " ".join("%s=%s" % (kk2, "fail" if vv else "PASS")
               for kk2, vv in rivals.items()) + " | " + frozen_note
      + " | nopop arrivals=%d pending %s vs clean %s | locate: %s"
      % (len(np_["arrivals"]), np_pen, clean_pen, loc_note))
    return out, sha_c, clean, pois, mem, rivals


def b23_replay(sav_path):
    """Run rung B23's own acceptance IN-PROCESS. The SAVE is the caller's (the
    fixture both rungs share); the TRACE is always B23's own m56 queue trace -
    this gate proves the ENGINE was reused, not forked, so it must not inherit
    this rung's m289 trace. REVIEW #307 P2: it used to hardcode
    composedlive.DEFAULT_SAV, so a caller pointing --sav elsewhere ran B23's
    replay against a file it never chose. Returns its summary line."""
    res = []
    soct.acceptance(sav_path, soct.DEFAULT_TRACE, res)
    bad = [n for n, ok in res if not ok]
    line = "PASS B23 %d/%d" % (len(res) - len(bad), len(res)) if not bad else \
        "FAIL B23 %d bad: %s" % (len(bad), bad[0][:60])
    return line, res


def measure_digest(rows, clean, pois, mem):
    """MD5 over the MEASUREMENTS (gate detail strings + every per-visit row of
    all three legs), never over labels alone - a digest of labels passes twice
    while all the numbers move (skill: mutation-harness scoring)."""
    h = hashlib.md5()
    for lbl, ok, dt in rows:
        h.update(("%s|%s|%s\n" % (lbl.split(" - ")[0], ok, dt)).encode())
    for leg in (clean["visits"], pois["visits"], mem["visits"]):
        for v in leg:
            h.update(repr(sorted((k, str(x)) for k, x in v.items()
                                  if k != "final_img")).encode())
    for key in ("arrivals", "marrivals"):
        h.update(repr([bytes(a).hex() for a in clean.get(key, [])]).encode())
    return h.hexdigest()[:16]


def run_all(sav_path, log_path=None, trace_path=None):
    log_path = log_path or DEFAULT_LOG
    trace_path = trace_path or DEFAULT_TRACE
    line, _ = b23_replay(sav_path)
    rows, sha, clean, pois, mem, rivals = compute(sav_path, log_path, trace_path,
                                                  line)
    d1 = measure_digest(rows, clean, pois, mem)
    rows2, sha2, clean2, pois2, mem2, _ = compute(sav_path, log_path, trace_path,
                                                  line)
    d2 = measure_digest(rows2, clean2, pois2, mem2)
    # REVIEW #307 P2: this compared LABELS + verdicts + the final image only, so
    # a second run whose details and intermediate tables moved while its final
    # bytes happened to match would still have passed. It now compares the FULL
    # rows (labels, verdicts AND details) plus a digest over every per-visit
    # row of all three legs - the tables the spine actually promises.
    det = (sha2 == sha and rows2 == rows and d2 == d1)
    rows = rows + [
        ("G9 two runs -> identical FULL table (labels + verdicts + DETAILS + "
         "all three per-visit tables) + clean image sha %s" % sha[:16], det,
         "table equal=%s digest %s==%s sha equal=%s" % (rows2 == rows, d1, d2,
                                                        sha2 == sha))]
    return rows, sha, clean, pois, mem


def report_lines(sav_path, log_path=None, trace_path=None):
    rows, sha, clean, pois, mem = run_all(sav_path, log_path, trace_path)
    lines = []
    lines.append("== B24 composedlive  save=%s ==" % os.path.basename(sav_path))
    lines.append("founding turn %d; visited record index %d; price %d; d0 %d; "
                 "seed st %d pen %d slots %s"
                 % (clean["found_turn"], clean["target_idx"], PRICE_DECL, D0_DECL,
                    SEED_ST, SEED_PEN, SEED_SLOTS))
    lines.append("-- per-visit table (container fold, uncorrupted) --")
    for v in clean["visits"]:
        lines.append("visit %d t=%2d verdict=%-4s pre(st=%d pen=%d slots=%s) "
                     "after(st=%d pen=%d slots=%s mirror=%d) idx=%d n_units=%d"
                     % (v["visit"], v["t"], v["verdict"], v["pre"]["st"],
                        v["pre"]["pen"], v["pre"]["slots"][:4],
                        v["span_after"]["st"], v["span_after"]["pen"],
                        v["span_after"]["slots"][:4], v["span_after"]["mirror"],
                        v["target_idx_in_img"], v["img_n_units"]))
    lines.append("-- same visits under the image-only poison (tile/owner in the "
                 "CONTAINER from visit %d on) --" % POISON_FROM)
    for v in pois["visits"]:
        lines.append("visit %d t=%2d verdict=%-4s pre-tile=%s after(st=%d pen=%d "
                     "slots=%s) n_bases=%d"
                     % (v["visit"], v["t"], v["verdict"],
                        (v["pre"]["x"] if "x" in v["pre"] else
                         "%d,%d" % (v["pre_tile"][0], v["pre_tile"][1])
                         if "pre_tile" in v else "?"),
                        v["span_after"]["st"], v["span_after"]["pen"],
                        v["span_after"]["slots"][:4], v["img_n_bases"]))
    lines.append("-- same visits, model-fed fold (blind) --")
    for v in mem["visits"]:
        lines.append("visit %d      verdict=%-4s after(st=%d pen=%d slots=%s)"
                     % (v["visit"], v["verdict"], v["span_after"]["st"],
                        v["span_after"]["pen"], v["span_after"]["slots"][:4]))
    lines.append("-- turns where a logged op landed (of %d turns) --"
                 % len(clean["oprows"]))
    for r in clean["oprows"]:
        if r["ops"]:
            lines.append("t=%2d ops=%s ledger=%d image=%d size=%d"
                         % (r["t"], [(o[0][:3], o[1]) for o in r["ops"]],
                            r["led_n"], r["img_n"], r["size"]))
    lines.append("-- gates --")
    for lbl, ok, dt in rows:
        lines.append("%-78s %s %s" % (lbl, "OK " if ok else "FAIL", dt))
    allok = all(o for _, o, _ in rows)
    lines.append("== B24: %s (%d/%d), clean image sha256 %s =="
                 % ("PASS" if allok else "FAIL",
                    sum(1 for _, o, _ in rows if o), len(rows), sha))
    return lines, allok


def acceptance(sav_path, results, log_path=None, trace_path=None):
    """relay entry: selftest --b24 appends these (name, ok) rows - the module
    authors every claim, the hook cannot disagree with the module."""
    rows, sha, _, _, _ = run_all(sav_path, log_path, trace_path)
    for lbl, ok, dt in rows:
        results.append(("rung B24 %s%s" % (lbl, (" - " + dt) if dt else ""), ok))
    return sha


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sim.composedlive")
    ap.add_argument("--sav", default=DEFAULT_SAV,
                    help="the fixture both rungs share; it is ALSO handed to "
                         "the in-process rung B23 replay (review #307 P2)")
    ap.add_argument("--log", default=DEFAULT_LOG)
    ap.add_argument("--trace", default=DEFAULT_TRACE)
    ap.add_argument("--b23-trace", default=soct.DEFAULT_TRACE,
                    help="rung B23's OWN trace (never this rung's --trace)")
    ap.add_argument("--out", help="write the report here")
    a = ap.parse_args(argv)
    # REVIEW #307 P2: a caller who moved a fixture failed deep inside B23's
    # replay with an OSError instead of a one-line answer.
    for what, path in (("save", a.sav), ("log", a.log), ("trace", a.trace),
                       ("b23 trace", a.b23_trace)):
        if not os.path.exists(path):
            sys.stderr.write("missing %s fixture: %s\n" % (what, path))
            return 2
    soct.DEFAULT_TRACE = a.b23_trace
    lines, allok = report_lines(a.sav, a.log, a.trace)
    txt = "\n".join(lines) + "\n"
    sys.stdout.write(txt)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(txt)
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
