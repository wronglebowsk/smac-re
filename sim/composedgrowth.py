#!/usr/bin/env python3
"""sim.composedgrowth - rung B22: BOTH save record arrays grown in ONE write, with
the CREATE leg fed by the RELOADED base record.

BUILD_SPINE.md rung B22 (s273 authored it from main). B21 proved the OUTBOUND half of
the save round-trip (the model's fields survive INTO the image). B12 proved the CREATE
law's BYTES in memory. Neither tested the INBOUND half: does a base record written
through the B8 writer still DELIVER the fields a later leg consumes as ARGUMENTS?

This rung closes that loop. B21's composed run is written once more, now growing BOTH
arrays in a single `build_image(bases_override=..., append_units=...)` call, and the new
unit's tile + faction are read from `sim.save.parse(image).base(i)` - container bytes,
not model objects. G10's falsifier corrupts the base tile IN THE IMAGE and shows the
created record follows the image: proof the leg reads the container, not the model.

No box time, no /proc, no gdb, no game-binary load.
"""
import argparse
import hashlib
import os
import struct
import sys
import tempfile

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sim import basefound as sobf          # noqa: E402  (304-B record layout)
from sim import composedrun as socrun      # noqa: E402  (B21: the composed run)
from sim import production as soprod       # noqa: E402  (B12: the CREATE law)
from sim import save as sosave             # noqa: E402
from sim import savewriter as sow          # noqa: E402  (B8: the writer)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SAV = os.path.join(ROOT, "programs/saves/m54b_clean.SAV")
DEFAULT_LOG = os.path.join(ROOT, "evidence/m289_gdb_raw.log")
DEFAULT_TRACE = os.path.join(ROOT, "evidence/trace_m289_20261110_071759.jsonl")

GROW_BASES = 5 * sosave.BASE_LEN           # 1520 = the grown 304-B records
GROW_UNITS = sosave.UNIT_LEN               # 52   = the one new unit record
GROW_TOTAL = GROW_BASES + GROW_UNITS       # 1572


def parse_bytes(blob):
    """sim.save.parse() is path-based; the image is in memory. Round-trip through a
    temp file so the SAME parser/locator the decoder uses reads our bytes."""
    fd, path = tempfile.mkstemp(prefix="b22_", suffix=".SAV")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(blob)
        return sosave.parse(path)
    finally:
        os.unlink(path)


def _rec_bytes(sv, kind, i):
    stride = sosave.BASE_LEN if kind == "base" else sosave.UNIT_LEN
    off = sv.bases_off if kind == "base" else sv.units_off
    return sv.data[off + stride * i: off + stride * (i + 1)]


def compute(sav_path, log_path, trace_path, second_run=True):
    """Run the rung and return every measured number (print-free)."""
    r = socrun.pipeline(sav_path, log_path, trace_path, do_print=False)
    sv, img, led = r["sv"], r["img"], r["led"]
    W = []

    # G1 - B21's own legs still hold (this rung builds ON them, not beside them)
    g1 = (r["curve_match"] == r["T"] and r["hits_model"] == r["n_ops"]
          and len(r["new_recs"]) == GROW_BASES // sosave.BASE_LEN and r["reload_eq"])
    n_new = len(r["new_recs"])
    W.append(("G1 B21's composed run re-derives green on this input (curve %d/%d, op "
              "fidelity %d/%d, %d grown 304-B records, reload equal), so B22 builds ON "
              "it" % (r["curve_match"], r["T"], r["hits_model"], r["n_ops"],
                      len(r["new_recs"])), g1))

    # G2 - the B21 image re-parses, and the shape locator's verdict is MEASURED: it
    # confirms only the 18 NAMED bases, because the founded records carry M282's EMPTY
    # name span and sim/save._base_ok demands `[ -~]{3,30}\x00` at +19.
    sv1 = parse_bytes(img)
    idx = sv.n_bases + n_new - 1                 # the LAST surviving founding (fixture)
    b1 = sv1.base(idx)                            # READ FROM THE CONTAINER
    fac, tx, ty = b1["own4"], b1["x"], b1["y"]
    head = 2                                      # a queue head id, VERBATIM per B11/M68
    rec = soprod.create_record(tx, ty, head, fac)
    g2 = (sv1.n_bases == len(led.records) == 23 and sv1.n_units == sv.n_units
          and sv1.year == r["year_written"] and sv1.found_units == sv1.n_units
          and sv1.found_bases == sv.n_bases
          and len(led.records) - sv1.found_bases == n_new)
    W.append(("G2 the B21 image re-parses: n_bases %d (== the model's %d), n_units %d "
              "unchanged, year %d - and the shape scan CONFIRMS ONLY %d of them, "
              "recovering exactly the %d original bases: the %d founded records fail "
              "_base_ok (M282's empty name span), so a grown base is locatable by COUNT, "
              "never by SHAPE" % (sv1.n_bases, len(led.records), sv1.n_units, sv1.year,
                                  sv1.found_bases, sv.n_bases, n_new), g2))

    # G3 - the CREATE leg's INPUTS come from the reloaded record (container bytes)
    model = led.records[-1]
    same_model = (tx, ty, fac) == (model["x"], model["y"], model["own4"])
    canon = rec == soprod.create_record(model["x"], model["y"], head, model["own4"])
    g3 = same_model and canon and len(rec) == sosave.UNIT_LEN
    W.append(("G3 the unit record is composed from fields read OUT OF THE IMAGE "
              "(base[%d] at (%d,%d) fac %d, queue head %d) and is byte-equal to B12's "
              "own create_record for the same fields (%d B, no re-implementation)"
              % (idx, tx, ty, fac, head, len(rec)), g3))

    # G4 - ONE write grows BOTH arrays; the writer's fidelity is measured BAND BY BAND
    # at the MEASURED layout (sow.build_image emits originals then grown records and
    # re-anchors the tail after them, so "everything shifted by one amount" is FALSE -
    # the earlier version of this gate asserted exactly that and was wrong):
    #   [unit originals][the ONE new unit][base originals][the grown bases][tail]
    img2 = sow.build_image(sv, year=r["eng"].year, cur=r["eng"].cur, tf=r["eng"].tf,
                           bases_override=led.records, append_units=[rec])
    B, U, BB = sv.data, sosave.UNIT_LEN, sosave.BASE_LEN
    u_end = sv.units_off + U * sv.n_units        # original base-array anchor
    u_end_n = u_end + U                          # unit array end, grown
    b_end_n = u_end_n + BB * len(led.records)    # base array end, grown
    tail_src = sv.bases_off + BB * sv.n_bases    # original tail start
    grown_bytes = b"".join(sobf.record_bytes(x) for x in led.records[sv.n_bases:])
    sv2 = parse_bytes(img2)
    bands = [("unit originals", img2[sv.units_off:u_end] == B[sv.units_off:u_end],
              U * sv.n_units),
             ("the ONE new unit", img2[u_end:u_end_n] == rec, U),
             ("base originals", img2[u_end_n:u_end_n + BB * sv.n_bases] ==
              B[sv.bases_off:sv.bases_off + BB * sv.n_bases], BB * sv.n_bases),
             ("the grown bases", img2[u_end_n + BB * sv.n_bases:b_end_n] ==
              grown_bytes, BB * n_new),
             ("the tail", img2[b_end_n:] == B[tail_src:], len(B) - tail_src)]
    g4 = all(ok for _, ok, _ in bands) and len(img) - len(B) == GROW_BASES \
        and len(img2) - len(B) == GROW_TOTAL
    W.append(("G4 both arrays grew in ONE call (+%d B = %dx%d + %d; B21's bases-only "
              "image grew +%d B) and every band of the measured layout reproduces its "
              "source byte-for-byte: %s"
              % (GROW_TOTAL, n_new, BB, U, GROW_BASES,
                 ", ".join("%s %d B" % (nm, ln) for nm, ok, ln in bands if ok)
                 if all(ok for _, ok, _ in bands) else
                 ", ".join("%s %s" % (nm, "ok" if ok else "MISMATCH")
                           for nm, ok, ln in bands)), g4))

    # G5 - the save is located TWO ways and they DISAGREE by exactly one unit record on
    # the B21 image (measured, reported, not smoothed): its header counts put the base
    # array at units_off + 52*68, the shape scan anchors it at the originals' own spot.
    count_pos = sv.units_off + U * (sv.n_units + 1)
    g5 = (count_pos - sv1.bases_off == GROW_UNITS and sv1.bases_off == sv.bases_off
          and parse_bytes(img2).bases_off == count_pos)
    W.append(("G5 the two location methods DISAGREE on the B21 image by exactly the "
              "unit growth: its header counts put the base array at %d, the shape scan "
              "anchors it at %d (the originals' own spot %d); on the doubly-grown image "
              "the scan lands on the count position %d - so for a container that grew "
              "only one array, count and shape must not be trusted together"
              % (count_pos, sv1.bases_off, sv.bases_off, parse_bytes(img2).bases_off),
             g5))

    # G6 - byte -> field on the base array
    orig_match = all(_rec_bytes(sv1, "base", i) == _rec_bytes(sv, "base", i)
                     for i in range(sv.n_bases))
    grown_match = all(_rec_bytes(sv1, "base", sv.n_bases + k)
                      == sobf.record_bytes(led.records[-n_new + k])
                      for k in range(n_new))
    fields_match = all((sv1.base(sv.n_bases + k)["x"], sv1.base(sv.n_bases + k)["y"],
                        sv1.base(sv.n_bases + k)["own4"])
                       == (md["x"], md["y"], md["own4"])
                       for k, md in enumerate(led.records[-n_new:]))
    g6 = orig_match and grown_match and fields_match
    W.append(("G6 byte->field round-trip on the base array: all %d ORIGINAL records "
              "byte-identical, all %d GROWN records byte-equal to the founder's own "
              "record bytes (M282: x u16 +0, y u16 +2, faction +4/+5, rest zero), and "
              "each grown record's parsed (x, y, own4) equal the model's founding tuple"
              % (sv.n_bases, n_new), g6))

    # G7 - the header diff, MEASURED not predicted. The modeled spans that can move are
    # the counts dword pair (0x44 units, 0x48 bases) and the year WORD (0x54); cur/tf
    # already hold their recorded values in this save, so the honest count is 3 bytes -
    # asserting 4 "one per modeled field" is the decoration this repo's law bans.
    HDR_MODELED = {0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4A, 0x4B, 0x54, 0x55}
    diff_pre = [o for o in range(sv.units_off) if img2[o] != B[o]]
    g7 = (diff_pre == [0x44, 0x48, 0x54] and all(o in HDR_MODELED for o in diff_pre)
          and struct.unpack_from("<I", img2, 0x44)[0] == sv.n_units + 1
          and struct.unpack_from("<I", img2, 0x48)[0] == len(led.records)
          and struct.unpack_from("<H", img2, 0x54)[0] == r["year_written"])
    W.append(("G7 the header diff is EXACTLY the %d bytes %s: the units dword (now %d), "
              "the bases dword (now %d) and the year word (now %d), every one inside a "
              "modeled span - no other byte before the unit array moved"
              % (len(diff_pre), [hex(o) for o in diff_pre], sv.n_units + 1,
                 len(led.records), r["year_written"]), g7))

    # G8 - the doubly-grown image re-parses and the new record survives at the END
    orig_units_same = all(_rec_bytes(sv2, "unit", i) == _rec_bytes(sv, "unit", i)
                          for i in range(sv.n_units))
    new_at_end = _rec_bytes(sv2, "unit", sv2.n_units - 1) == rec
    u2 = sv2.unit(sv2.n_units - 1)
    closed = (u2["x"], u2["y"]) == (tx, ty) and u2["type"] == head and u2["owner"] == fac
    g7 = (sv2.n_units == sv.n_units + 1 and sv2.n_bases == len(led.records)
          and orig_units_same and new_at_end and closed
          and sv2.units_off == sv.units_off
          and sv2.bases_off - sv.bases_off == GROW_UNITS
          and sv2.tail_off - sv.tail_off == GROW_TOTAL)
    W.append(("G8 the doubly-grown image re-parses (n_units %d -> %d, n_bases %d): the "
              "%d original unit records byte-identical, the new record AT THE ARRAY END, "
              "units_off unmoved / bases_off +%d B / tail +%d B, and its parsed x/y/type/"
              "owner equal the base tile read from the FIRST reload - the image->field->"
              "record->image chain is closed"
              % (sv.n_units, sv2.n_units, sv2.n_bases, sv.n_units, GROW_UNITS,
                 GROW_TOTAL), g7))

    # G9 - falsifier: corrupt the base tile IN THE IMAGE; the record follows the image
    BAD = 0x5A7
    blob = bytearray(img2)
    struct.pack_into("<HH", blob, sv2.bases_off + sosave.BASE_LEN * idx, BAD, BAD + 1)
    sv3 = parse_bytes(bytes(blob))
    b3 = sv3.base(idx)
    rec_bad = soprod.create_record(b3["x"], b3["y"], head, b3["own4"])
    g8 = (b3["x"] == BAD and _rec_bytes(sv3, "base", idx) !=
          _rec_bytes(sv2, "base", idx) and rec_bad != rec and
          soprod.create_record(b3["x"], b3["y"], head, b3["own4"])[
              soprod.UNIT_X:soprod.UNIT_Y + 2] == struct.pack("<HH", BAD, BAD + 1))
    W.append(("G9 FALSIFIER: corrupting that base record's tile IN THE IMAGE (%d,%d) and "
              "re-composing from the reloaded record MOVES the created unit to the "
              "corrupted tile (record differs from G3's at the x/y span) - the leg reads "
              "CONTAINER bytes, not the model" % (BAD, BAD + 1), g8))

    # G10 - rivals fail the same fit
    img_noBases = sow.build_image(sv, year=r["eng"].year, cur=r["eng"].cur,
                                  tf=r["eng"].tf, append_units=[rec])
    sv_noB = parse_bytes(img_noBases)
    rec_idle = soprod.create_record(tx, ty, head, fac, new_order=2)   # B12's idle order
    stride54 = sow.build_image(sv, year=r["eng"].year, cur=r["eng"].cur,
                               tf=r["eng"].tf, bases_override=led.records,
                               append_units=[rec], unit_len=54)
    g9 = (sv_noB.n_bases == sv.n_bases and len(img_noBases) == len(sv.data) + GROW_UNITS
          and rec_idle != rec and len(stride54) != len(img2))
    W.append(("G10 rivals fail the same fit: growing ONLY the unit array re-derives "
              "n_bases %d and loses the %d grown records (image %d B, not %d); the idle "
              "order-2 record is NOT the produced record; and the perturbed unit stride "
              "mis-places the tail (len %d != %d)"
              % (sv_noB.n_bases, n_new, len(img_noBases), len(img2), len(stride54),
                 len(img2)), g9))

    aux = {"img2_sha": hashlib.sha256(img2).hexdigest(),
           "n_units_new": sv2.n_units, "n_bases": sv2.n_bases, "img2": img2,
           "n_grown": n_new}
    digest = hashlib.sha256(("|".join([str(ok) for _, ok in W] + [aux["img2_sha"],
                                       "%d" % sv2.n_units, "%d" % sv2.n_bases])
                             ).encode()).hexdigest()
    aux["digest"] = digest

    # G11 - determinism: a second independent compute() reproduces BOTH the written
    # image bytes and the digest. (A rung that cannot be re-run to the same answer has
    # not been measured twice, it has been asserted once.)
    W2, aux2 = (compute(sav_path, log_path, trace_path, second_run=False)
                if second_run else (W, aux))
    # The comparison is over the TEN substantive verdicts, not over W's own tail: G11's
    # verdict is False inside the second (second_run=False) invocation BY CONSTRUCTION,
    # so comparing full verdict lists would compare an artefact of the guard, not a fact.
    g11 = (second_run and [ok for _, ok in W2][:10] == [ok for _, ok in W][:10]
           and aux2["img2_sha"] == aux["img2_sha"])
    W.append(("G11 a SECOND run reproduces the written image byte-for-byte (sha256 %s) "
              "and the same gate verdicts, so the whole rung is deterministic"
              % aux["img2_sha"][:16], g11))
    return W, aux


def acceptance(sav_path, log_path, trace_path, results):
    """Table-first, then the gates, in the shape sim/selftest.py consumes: (label, ok)
    pairs appended to `results`.  The module keeps sole authorship of the claims -
    selftest only relays and summarises, so the two entry points can never disagree."""
    W, aux = compute(sav_path, log_path, trace_path)
    for name, ok in W:
        results.append((name, ok))
    return aux


def render(sav_path, log_path, trace_path):
    W, aux = compute(sav_path, log_path, trace_path)
    lines = ["B22 composedgrowth - rung: both save record arrays grown in ONE write, "
             "the CREATE leg fed by the RELOADED base record",
             "sav=%s log=%s trace=%s" % (os.path.basename(sav_path),
                                          os.path.basename(log_path),
                                          os.path.basename(trace_path)),
             "no box time, no /proc, no gdb, no game-binary load", ""]
    for name, ok in W:
        lines.append(("  ok   " if ok else "  BAD  ") + name)
    bad = [n for n, ok in W if not ok]
    lines.append("")
    lines.append("written doubly-grown image sha256 %s" % aux["img2_sha"][:16])
    lines.append("report digest %s" % aux["digest"][:16])
    if bad:
        lines.append("RESULT: FAIL (%d/%d gates bad: %s)"
                     % (len(bad), len(W), "; ".join(bad)))
        return "\n".join(lines), 1, aux
    lines.append("PASS B22: %d/%d gates - the save's TWO record arrays grow in ONE "
                 "writer call (image +%d B = %dx%d + %d, header diff 3 B) and the B12 "
                 "CREATE leg demonstrably takes its tile and faction from the RELOADED "
                 "image's base record (corrupting that record in the image moves the "
                 "created unit), so a base written by the B8 writer can feed a later "
                 "leg's ARGUMENTS - the inbound half of the round-trip (no box time, no "
                 "/proc, no gdb)"
                 % (len(W) - len(bad), len(W), GROW_TOTAL, aux["n_grown"],
                    sosave.BASE_LEN, sosave.UNIT_LEN))
    return "\n".join(lines), 0, aux


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python3 -m sim.composedgrowth")
    ap.add_argument("--sav", default=DEFAULT_SAV)
    ap.add_argument("--log", default=DEFAULT_LOG)
    ap.add_argument("--trace", default=DEFAULT_TRACE)
    ap.add_argument("--out", default=None)
    ap.add_argument("--image", default=None, help="also write the doubly-grown image")
    a = ap.parse_args(argv)
    text, rc, aux = render(a.sav, a.log, a.trace)
    print(text)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    if a.image:
        with open(a.image, "wb") as fh:
            fh.write(aux["img2"])
    return rc


if __name__ == "__main__":
    sys.exit(main())
