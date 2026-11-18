#!/usr/bin/env python3
"""sim.composedturn - rung B23: the queue's PER-TURN progress composed through
the WRITER (B11's law in the written container, not in memory).

BUILD_SPINE.md rung B23 (s280 authored this rung from main, as B14-B22 did).

B12 ran the per-boundary visits of `evidence/trace_m56_build_20261026_145157.jsonl`
(terran.exe's own 10-boundary run on Korolev Center (29,42), head 2, price 9)
IN MEMORY over parsed snapshot dicts. B23 makes the container carry that progress:
the queue state (storage +0x40, mirror +0x98, pending +0x4c, ten slot dwords
+0x50) lives in a .SAV-shaped image composed by `sim.savewriter`, and every
boundary's visit reads its inputs OUT OF THE RELOADED IMAGE, writes its results
BACK THROUGH THE WRITER, and the next boundary re-parses. Nothing feeds a later
turn except image bytes. The unit array grows through the same writer (B22's
one-append path) when the r0 visit pays.

Recorded laws used as data (declared, not modeled): the visit-time d0 (+0xd0)
is the game's own per-visit recompute (M57/M58: "moves with the garrison"), read
from the trace's round_after sample; the pop's visibility law (M58: the pay
executes with pending STILL 1, pending reads popped at the NEXT boundary) - the
container is written popped, so pending parity is asserted against the recorded
round_before samples; price = 9 is the recorded per-base price (M58/M72 law,
never a recomputed price_of). f30 (+0x30) bit evolution and +0xd0 are spans the
model does NOT claim; they never gate a verdict in this fixture (f30 & 2 is
never set in any sample, recorded or composed).

`python3 -m sim.selftest --b23 <sav> [trace]` relays THIS module's claims;
`python3 -m sim.composedturn --sav <sav> --trace <tr> [--out f]` prints them.
NO /proc, NO gdb, NO Wine, NO game-binary load.
"""
import argparse
import hashlib
import json
import os
import struct
import sys
import tempfile

from . import queue as soq
from . import production as soprod
from . import save as sosave
from . import savewriter as sow

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(REPO, "evidence")
DEFAULT_TRACE = os.path.join(EVID, "trace_m56_build_20261026_145157.jsonl")

KOR = (29, 42)          # Korolev Center's tile - locate by COORDS, never index
PRICE_RECORDED = 9      # the recorded per-base price (M58: live state, given)
MIRROR_OFF = 0x98       # +0x98 mirrors storage one store after the pay (M57-4)
ST_OFF, D0_OFF, F30_OFF = 0x40, 0xd0, 0x30


def parse_image(img):
    """sim.save.parse() is path-based; round-trip through a temp file (B22 pattern)."""
    fd, path = tempfile.mkstemp(prefix="b23_", suffix=".SAV")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(img)
        return sosave.parse(path)
    finally:
        os.unlink(path)


def load_boundaries(trace_path):
    """The trace's 10 (round_before, round_after) Korolev records + globals."""
    rows = []
    with open(trace_path, encoding="utf-8") as fh:
        evs = [json.loads(ln) for ln in fh if ln.strip()]

    def kor(snap):
        for v in snap["bases"]:
            if v.get("name") == "Korolev Center":
                return bytes.fromhex(v["hex"])
        raise AssertionError("Korolev Center absent from snapshot")
    br = {e["r"]: kor(e["snap"]) for e in evs if e["event"] == "round_before"}
    ar = {e["r"]: kor(e["snap"]) for e in evs if e["event"] == "round_after"}
    nu = {e["r"]: (e["snap"]["globals"]["n_units"], e["snap"]["globals"]["n_bases"])
          for e in evs if e["event"] == "round_before"}
    for r in range(len(br)):
        rows.append({"r": r, "before": br[r], "after": ar[r], "globals": nu[r]})
    return rows


def spans_of(rec):
    """The modeled queue span of a 304-B record as a comparable tuple."""
    return {
        "st": struct.unpack_from("<i", rec, ST_OFF)[0],
        "pen": struct.unpack_from("<i", rec, soq.PENDING_OFF)[0],
        "slots": list(struct.unpack_from("<10i", rec, soq.HEAD_OFF)),
        "mirror": struct.unpack_from("<i", rec, MIRROR_OFF)[0],
        "f30": struct.unpack_from("<I", rec, F30_OFF)[0],
        "d0": struct.unpack_from("<i", rec, D0_OFF)[0],
    }


def read_state(im, idx):
    """THE image->state leg: every field the next visit consumes is read OUT OF
    THE PARSED IMAGE. Both the fold and the falsifier call this single leg."""
    off = im.bases_off + sosave.BASE_LEN * idx
    rec = im.data[off:off + sosave.BASE_LEN]
    sp = spans_of(rec)
    b = im.base(idx)
    q = soq.Queue(slots=sp["slots"], pending=sp["pen"])
    return q, sp["st"], sp["mirror"], sp["f30"], b


def fold(sv, bounds, mode="container", corrupt=None, pos=False,
         overrides_fn=None, d0s=None, price=None, seed_rec=None, tile_at=None,
         slot_i=None, prior_units=None, start_img=None, passthrough=False):
    """Run the 10 boundaries. mode: 'container' = re-parse the image every turn;
    'memory' = rival that never re-reads the container (carries model state);
    'noadd' / 'price10' / 'nopop' / 'zerotail' / 'nomirror' / 'frontinsert' =
    rivals that mutate ONE law each; 'addalways' / 'price' / 'locate' = the
    rivals rung B24 drives (sim/composedlive.py): the ADD gate dropped, an
    explicit price, and a tile-locator used against a corrupted tile.
    corrupt(r, rec_bytes)->rec_bytes is the
    falsifier hook, applied to the IMAGE bytes between turns (never to model
    state), so only a fold that READS the container can see it.
    pos=True locates the grown slot BY POSITION (needed when the falsifier
    corrupts the tile itself, so a coord lookup must not be the locator).
    B24 hooks (defaults keep this module's OWN rung B23 claims byte-identical):
    overrides_fn(records)->bases_override list (the writer input every turn;
    B23 keeps _all_overrides), d0s = per-boundary visit-time d0 (default: read
    from the trace's after-samples), price = the price law's value (default
    PRICE_RECORDED), seed_rec = the seed record bytes (default: the trace's r0
    before-sample - B24 seeds a FOUNDER's 304-B record instead).
    Returns (verdicts, images, arrivals, final_img)."""
    bounds_n = len(bounds)
    seed_rec = bytearray(bounds[0]["before"]) if seed_rec is None else \
        bytearray(seed_rec)
    ovf = _all_overrides if overrides_fn is None else overrides_fn
    d0_at = (lambda r: spans_of(bounds[r]["after"])["d0"]) if d0s is None \
        else (lambda r: d0s[r])
    price_v = PRICE_RECORDED if price is None else price
    # B24 hook: the array slot the positioned fold addresses. Default = the
    # LAST grown slot (rung B23's shape). B24's visited record is grown MID-
    # ARRAY (a later logged op appends after it, and the last-slot destroy
    # removes THAT one), so it must name its own slot - "by position" cannot
    # silently mean "by last".
    # seed: the grown slot carries the seed record VERBATIM (a declared seed:
    # B23 uses the trace's r0 round_before record re-hosted in the container;
    # B24 uses the founder leg's own 304-B record bytes) - parity is then
    # demanded of the run's EVOLUTION, not of the seed.
    kor_i = sv.n_bases  # grown slot index (locate by coords in the image anyway)
    slot_at = kor_i if slot_i is None else slot_i
    overrides = []      # only the Korolev slot is overridden per turn
    # B24 hook: arrivals already grown by EARLIER windows of the same run. The
    # fold accumulates them and re-writes them on every turn's image, so a
    # window-per-visit driver keeps the whole unit array instead of only its
    # own window's arrivals (default [] == rung B23's single-window behavior).
    appended = list(prior_units) if prior_units else []
    images = []
    verdicts = []
    qmem = None         # 'memory' rival carries a model Queue instead
    st_mem = None
    for r in range(bounds_n):
        # ---- inputs come from the container (or from the model, rival) ----
        img_prev = images[-1] if images else None
        if corrupt and img_prev is not None:
            im_c = parse_image(img_prev)
            off = im_c.bases_off + sosave.BASE_LEN * slot_at
            mut = bytearray(img_prev)
            newrec = corrupt(r, bytearray(mut[off:off + sosave.BASE_LEN]))
            mut[off:off + sosave.BASE_LEN] = newrec
            img_prev = bytes(mut)
        if mode == "memory":
            if qmem is None:
                sp = spans_of(seed_rec)
                qmem = soq.Queue(slots=sp["slots"], pending=sp["pen"])
                st_mem = sp["st"]
            q, st, mirror, f30, b = qmem, st_mem, None, spans_of(seed_rec)["f30"], \
                {"x": struct.unpack_from("<H", seed_rec, 0)[0],
                 "y": struct.unpack_from("<H", seed_rec, 2)[0],
                 "own4": seed_rec[4]}
        else:
            if img_prev is None:
                seed0 = bytearray(seed_rec)
                if corrupt:                 # r0 container: poison the SEED bytes
                    seed0 = corrupt(0, seed0)
                # B24 hook: the caller may hand in the image as it now stands
                # (its own composition's last write) instead of letting this
                # engine recompose it - the fold then READS those bytes.
                img0 = (start_img if start_img is not None else
                        sow.build_image(sv, bases_override=ovf(
                            sv, kor_i, seed0, {}, appended)))
            else:
                img0 = img_prev
            im = parse_image(img0)
            if mode == "locate":            # rival (B24): locate BY TILE, even
                if tile_at is None:         # after the tile is corrupted. A
                    raise AssertionError(   # locate rival without a locator is
                        "locate rival needs tile_at")  # a defect, not a verdict
                idx = _find_tile(im, tile_at())
            else:
                idx = slot_at if pos else _find_kor(im)
            q, st, mirror, f30, b = read_state(im, idx)
            if mode == "frozenargs":        # rival: creation args frozen to seed-open
                b = {"x": struct.unpack_from("<H", seed_rec, 0)[0],
                     "y": struct.unpack_from("<H", seed_rec, 2)[0],
                     "own4": seed_rec[4]}
        d0_v = d0_at(r)                     # visit-time d0 (recorded / declared)
        price = price_v if mode != "price10" else 10
        if mode == "price":                 # rival (B24): a different price law
            price = price_v
        # ---- the visit, B12's law (gate storage+d0 >= price; PAY; CREATE;
        # ---- POP via B11). The income ADD is gated d0>0, head != sentinel,
        # ---- !(f30 & 2) (M57-2). rivals switch ONE term each:
        add = 0 if mode == "noadd" or not (
            d0_v > 0 and q.head() != soq.SENTINEL and not (f30 & 2)) else d0_v
        if mode == "addalways":             # rival (B24): the ADD gate dropped
            add = d0_v
        if mode == "nopop":
            q0 = soq.Queue(slots=list(q.slots), pending=q.pending)  # local copy
            made = None
            if st + add >= price:
                made = soprod.create_record(b["x"], b["y"], q.head(), b["own4"])
                st = st + add - price
            verdict = "pay" if made is not None else "bail"
            q = q0                                   # pending/slots NEVER move
        else:
            res = soprod.visit(q, b["x"], b["y"], b["own4"], st + add, 0, price)
            # st + add already folded; visit() compares storage + income(0)
            if res[0] == "pay":
                st, made = res[1], res[2]
                if mode == "zerotail":
                    q.slots[q.pending] = 0           # rival: pop zeroes the tail
                verdict = "pay"
            else:
                st, made, verdict = res[1], None, "bail"
        if made is not None:
            if mode == "frontinsert":
                appended.insert(0, made)
            else:
                appended.append(made)
        if mode == "memory":
            qmem, st_mem = q, st
        # ---- write the result back through the WRITER ----
        qspan = {"st": st, "pen": q.pending, "slots": list(q.slots),
                 "mirror": st if mode != "nomirror" else mirror,
                 "d0": None}
        del mirror  # parity table reads the written image, below
        img = sow.build_image(sv, bases_override=ovf(
            sv, kor_i, seed_rec, qspan, appended), append_units=appended)
        if passthrough:            # B24's locate rival: the fold must keep
            img = img0             # reading the CALLER's image - re-composing
                                   # it would restore the model's clean bytes
                                   # and hide the very corruption under test
                                   # (measured: the rival PASSED, i.e. was
                                   # decoration, until this was fixed)
        images.append(img)
        verdicts.append({"r": r, "verdict": verdict, "made": made is not None,
                         "st_after": st, "pen_after": q.pending})
    return verdicts, images, appended, images[-1]


def _find_kor(im):
    """Locate Korolev by TILE in the parsed image (the run's own law: base
    indices walk mid-game; coords are stable)."""
    for i in range(im.n_bases):
        bb = im.base(i)
        if (bb["x"], bb["y"]) == KOR:
            return i
    raise AssertionError("Korolev (29,42) not located in the image")


def _find_tile(im, tile):
    """B24 hook: the same locate-by-TILE law for an arbitrary tile (the rival
    that keeps using it after the tile itself has been corrupted)."""
    for i in range(im.n_bases):
        bb = im.base(i)
        if (bb["x"], bb["y"]) == tile:
            return i
    raise AssertionError("tile %s not located in the image" % (tile,))


def _all_overrides(sv, kor_i, seed_rec, qspan, appended):
    """Override list covering sv.n_bases originals (identity) + the grown
    Korolev slot. qspan={} keeps the seed record verbatim."""
    ov = [{"identity": True} for _ in range(sv.n_bases)]
    ent = {"raw": seed_rec, "x": struct.unpack_from("<H", seed_rec, 0)[0],
           "y": struct.unpack_from("<H", seed_rec, 2)[0],
           "own4": seed_rec[4], "fac": seed_rec[5]}
    if qspan:
        ent["queue"] = qspan
    ov.append(ent)
    del appended  # appended units ride build_image's append_units, not here
    return ov


def compute(sav_path, trace_path, falsify=True):
    sv = sosave.parse(sav_path)
    bounds = load_boundaries(trace_path)
    out = []          # (label, ok, detail)

    def g(label, ok, detail=""):
        out.append((label, bool(ok), detail))
        return bool(ok)

    verdicts, images, arrivals, img = fold(sv, bounds)
    im = parse_image(img)
    ki = _find_kor(im)

    # G1 seed round-trips through the writer: the grown record's modeled spans
    # equal the trace's r0 round_before spans; the 18 originals are byte-identical.
    sp0 = spans_of(bounds[0]["before"])
    sp_img = spans_of(im.data[im.bases_off + sosave.BASE_LEN * ki:
                             im.bases_off + sosave.BASE_LEN * (ki + 1)])
    # NOTE: images[-1] is POST-fold; G1 re-runs a seed-only write instead:
    img_seed = sow.build_image(sv, bases_override=_all_overrides(
        sv, sv.n_bases, bounds[0]["before"], {}, []))
    ims = parse_image(img_seed)
    kis = _find_kor(ims)
    seed_ok = spans_of(ims.data[ims.bases_off + sosave.BASE_LEN * kis:
                                ims.bases_off + sosave.BASE_LEN * (kis + 1)]) == sp0
    orig_ident = all(ims.data[ims.bases_off + sosave.BASE_LEN * i:
                              ims.bases_off + sosave.BASE_LEN * (i + 1)] ==
                     sv.data[sv.bases_off + sosave.BASE_LEN * i:
                             sv.bases_off + sosave.BASE_LEN * (i + 1)]
                     for i in range(sv.n_bases))
    g("G1 seed + originals through the writer",
      seed_ok and orig_ident and ims.n_bases == sv.n_bases + 1,
      "grown n_bases %d, seed spans equal %s, originals byte-identical %s"
      % (ims.n_bases, seed_ok, orig_ident))

    # G2 every boundary's container read equals the recorded round_before span.
    # Re-fold reading the image fresh each turn; compare per-turn reads.
    per_turn_read_ok = True
    for r in range(len(bounds)):
        imr = parse_image(images[r - 1]) if r else ims
        spx = spans_of(imr.data[imr.bases_off + sosave.BASE_LEN * _find_kor(imr):
                                imr.bases_off + sosave.BASE_LEN * (_find_kor(imr) + 1)])
        want = spans_of(bounds[r]["before"])
        for f in ("st", "pen", "slots"):
            if spx[f] != want[f]:
                per_turn_read_ok = False
        # pending uses the visibility law: after a pop, the CONTAINER shows the
        # popped pending while the game's after-sample still shows the old one.
        if r and verdicts[r - 1]["made"]:
            if spx["pen"] != want["pen"]:
                per_turn_read_ok = False
    g("G2 container reads == recorded before-spans (10 boundaries)",
      per_turn_read_ok)

    # G3 verdicts: pay at r0 only; arrivals attributed to exactly one boundary.
    g("G3 per-visit verdicts (pay r0, bail r1..r9)",
      [v["verdict"] for v in verdicts] == ["pay"] + ["bail"] * 9,
      "verdicts " + ",".join(v["verdict"][0] for v in verdicts))

    # G4 storage + mirror parity vs recorded round_after, every boundary.
    bad_st = bad_mir = 0
    for r in range(len(bounds)):
        spx = spans_of(images[r])           # what the fold WROTE is in images[r]
        # images[r] is written AFTER the visit; compare its st/mirror/slots to
        # the game's after-sample, pending EXCLUDED (M58 visibility law).
        want = spans_of(bounds[r]["after"])
        got = _spans_in_image(images[r])
        if got["st"] != want["st"]:
            bad_st += 1
        if got["mirror"] != want["mirror"]:
            bad_mir += 1
    g("G4 storage + mirror parity vs recorded afters (10/10)",
      bad_st == 0 and bad_mir == 0, "st mismatches %d, mirror %d" % (bad_st, bad_mir))

    # G5 slot parity: 10 dwords x 10 boundaries, stale tail included.
    slot_ok = all(_spans_in_image(images[r])["slots"] ==
                  spans_of(bounds[r]["after"])["slots"] for r in range(len(bounds)))
    g("G5 slot-array parity 100/100 dwords (stale tail kept)", slot_ok)

    # G6 pending visibility law: container pending == recorded AFTER samples on
    # the nine no-arrival boundaries, and == recorded BEFORE on the popped one.
    pen_ok = sum(_spans_in_image(images[r])["pen"] ==
                 spans_of(bounds[r]["after"])["pen"] for r in range(1, len(bounds)))
    pop_vis = _spans_in_image(images[0])["pen"] == 0 and \
        spans_of(bounds[0]["after"])["pen"] == 1 and \
        _spans_in_image(images[1])["pen"] == spans_of(bounds[1]["before"])["pen"]
    g("G6 pending visibility (9/9 afters + pop visible next before)",
      pen_ok == 9 and pop_vis, "afters %d/9, popped-then-visible %s" % (pen_ok, pop_vis))

    # G7 the arrival rides the container: n_units 67->68, the new record at the
    # array END, equal to B12's producer fed with IMAGE-read tile/owner.
    want_rec = soprod.create_record(KOR[0], KOR[1], sp0["slots"][0],
                                    bounds[0]["before"][4])
    tail_off = im.units_off + sosave.UNIT_LEN * (im.n_units - 1)
    tail_rec = im.data[tail_off:tail_off + sosave.UNIT_LEN]
    g("G7 arrival at array END from image fields, n_units %d->%d"
      % (sv.n_units, im.n_units),
      im.n_units == sv.n_units + 1 and tail_rec == want_rec and
      (im.unit(im.n_units - 1)["x"], im.unit(im.n_units - 1)["y"],
       im.unit(im.n_units - 1)["type"], im.unit(im.n_units - 1)["owner"]) ==
      (KOR[0], KOR[1], sp0["slots"][0], bounds[0]["before"][4]))

    # G8 fidelity bands: +304 bases +52 units exactly; unit originals and the
    # tail intact; header diff is the two count dwords ONLY.
    grew = len(img) - len(sv.data) == sosave.BASE_LEN + sosave.UNIT_LEN
    units_ident = all(img[sv.units_off + sosave.UNIT_LEN * i:
                          sv.units_off + sosave.UNIT_LEN * (i + 1)] ==
                      sv.data[sv.units_off + sosave.UNIT_LEN * i:
                              sv.units_off + sosave.UNIT_LEN * (i + 1)]
                      for i in range(sv.n_units))
    tail_ident = (img[len(img) - (len(sv.data) - sv.bases_off -
                                  sosave.BASE_LEN * sv.n_bases):] ==
                  sv.data[sv.bases_off + sosave.BASE_LEN * sv.n_bases:])
    refus = []
    for bad in (9, 11):
        try:
            sow.build_image(sv, bases_override=_all_overrides(
                sv, sv.n_bases, bounds[0]["before"],
                {"st": 0, "pen": 0, "slots": [0] * bad, "mirror": 0}, []))
        except ValueError:
            refus.append(bad)
    g("G8 grew exactly 304+52 B; originals + tail identical; writer refuses 9/11-slot lists",
      grew and units_ident and tail_ident and refus == [9, 11],
      "refused %s" % refus)

    # G9 rivals FAIL the same fit (each is the full fold, one law mutated).
    rivals = {}
    for mode, probe in (("noadd", "arrive"), ("price10", "arrive"),
                        ("nopop", "pen_after1"), ("zerotail", "slots"),
                        ("nomirror", "mirror")):
        vv, ii, aa, fin = fold(sv, bounds, mode=mode)
        if probe == "arrive":
            rivals[mode] = (len(aa) == 0)          # lost the recorded r0 arrival
        elif probe == "pen_after1":
            spx = _spans_in_image(ii[1])
            want = spans_of(bounds[1]["before"])
            rivals[mode] = (spx["pen"] != want["pen"])   # pending stuck at 1
        elif probe == "slots":
            rivals[mode] = (_spans_in_image(ii[0])["slots"] !=
                            spans_of(bounds[0]["after"])["slots"])
        elif probe == "mirror":
            rivals[mode] = (_spans_in_image(ii[0])["mirror"] !=
                            spans_of(bounds[0]["after"])["mirror"])
        elif probe == "tailpos":
            imf = parse_image(fin)
            u0 = imf.unit(imf.n_units - 1)
            rivals[mode] = (u0["x"], u0["y"], u0["type"]) != (KOR + (sp0["slots"][0],))
    g("G9 five rivals fail the same fit", all(rivals.values()),
      " ".join("%s=%s" % (k, "fail" if v else "PASS") for k, v in rivals.items()))

    # G10 THE FALSIFIER, load-bearing by construction: corrupt the CONTAINER
    # between turns (slots[0] := sentinel at r>=1) - the container fold's r1
    # verdict is unchanged (it would bail anyway) so instead corrupt st := 20
    # at r1: the container fold pays at r1 (20 >= 9) and produces TWO arrivals;
    # a model-fed fold is BLIND to the corruption and still matches the recorded
    # table. Both halves must hold or the falsifier is decoration.
    fm = gv = None
    if falsify:
        def corrupt20(r, rec):
            if r == 1:                      # exactly one poisoned container read
                struct.pack_into("<i", rec, ST_OFF, 20)
            return rec
        vv2, ii2, aa2, fin2 = fold(sv, bounds, corrupt=corrupt20)
        gv = [v["verdict"] for v in vv2] == ["pay", "pay", "pay"] + ["bail"] * 7 \
            and len(aa2) == 3
        vvm, iim, aam, finm = fold(sv, bounds, mode="memory", corrupt=corrupt20)
        fm = [v["verdict"] for v in vvm] == ["pay"] + ["bail"] * 9 and len(aam) == 1
    g("G10 corruption lands only through the container (falsifier bites)",
      (not falsify) or (gv and fm), "")

    # G11 THE CREATION SOURCE IS THE CONTAINER (Greptile P2 on #297): poison
    # tile+owner in the SEED CONTAINER BYTES at r0 - the created unit must
    # CARRY the corrupted bytes (1447,1448,owner 0x5a); the frozenargs rival
    # (creation args pinned to the seed-open values) FAILS the same fit.
    def corrupt_tile(r, rec):
        if r == 0:
            struct.pack_into("<H", rec, 0, 1447)
            struct.pack_into("<H", rec, 2, 1448)
            rec[4] = 0x5a
        return rec
    aa_p, fin_p = None, None
    _, _, aa_p, fin_p = fold(sv, bounds, corrupt=corrupt_tile, pos=True)
    imp = parse_image(fin_p)
    up = imp.unit(imp.n_units - 1)
    carried = ((up["x"], up["y"], up["owner"]) == (1447, 1448, 0x5A)
               and len(aa_p) == 1)
    vvm2, _, aa_f, fin_f = fold(sv, bounds, mode="frozenargs",
                                corrupt=corrupt_tile, pos=True)
    imf2 = parse_image(fin_f)
    upf = imf2.unit(imf2.n_units - 1)
    frozen_bad = (upf["x"], upf["y"], upf["owner"]) != (1447, 1448, 0x5A) \
        and (upf["x"], upf["y"], upf["owner"]) == (KOR[0], KOR[1], bounds[0]["before"][4])
    g("G11 corrupted tile/owner land in the created record; frozen-args rival fails",
      carried and frozen_bad,
      "carried=%s frozen-rival-fails=%s" % (carried, frozen_bad))
    # G12 determinism: a second independent compute reproduces image sha256 + table.
    return out, hashlib.sha256(img).hexdigest(), img


def _spans_in_image(img):
    im = parse_image(img)
    ki = _find_kor(im)
    return spans_of(im.data[im.bases_off + sosave.BASE_LEN * ki:
                            im.bases_off + sosave.BASE_LEN * (ki + 1)])


def run_all(sav_path, trace_path):
    """The single source of the rung's claims: compute twice (the second run
    without the falsifier half) and append G11. Returns rows (label, ok, detail)."""
    out, sha, _ = compute(sav_path, trace_path)
    out2, sha2, _ = compute(sav_path, trace_path, falsify=False)
    det = (sha2 == sha and out2 == out)   # FULL rows: label, verdict AND detail
    return out + [("G12 two runs -> identical FULL table + image sha %s" % sha[:16],
                   det, "")]


def acceptance(sav_path, trace_path, results):
    """relay entry: selftest --b23 appends these (name, ok) rows - the module
    authors every claim, the hook cannot disagree with the module."""
    for lbl, ok, dt in run_all(sav_path, trace_path):
        results.append(("rung B23 %s%s" % (lbl, (" - " + dt) if dt else ""), ok))


def report_lines(sav_path, trace_path):
    rows = run_all(sav_path, trace_path)
    lines = ["%-58s %s %s" % (lbl, "OK " if ok else "FAIL", dt)
             for lbl, ok, dt in rows]
    return lines, all(o for _, o, _ in rows)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sim.composedturn")
    ap.add_argument("--sav", required=True)
    ap.add_argument("--trace", default=DEFAULT_TRACE)
    ap.add_argument("--out", help="write the report here")
    a = ap.parse_args(argv)
    lines, allok = report_lines(a.sav, a.trace)
    txt = "\n".join(lines) + "\n== B23: %s ==\n" % ("PASS" if allok else "FAIL")
    sys.stdout.write(txt)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(txt)
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
