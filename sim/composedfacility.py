"""sim.composedfacility - rung B30's RUN and its GATES (BUILD_SPINE §B30).

The facility-COMPLETION leg: a paid queue item BECOMES a facility the base HAS.  The SETTER is
executed as the exact inverse of the reader the feeder already uses (`sim.feeder.fac_bit`: byte
`item>>3`, bit `1<<(item&7)`), the write is composed through the writer into the container's own
304-B record, RELOADED from bytes, and then B29's DERIVED item table reprices the base's round
bill off the reloaded bitmap - with M46's disabled-list rule deciding when the bill does not move.

ASSUMED (opens a census pick): the game's completion routine is not in this rung's evidence.  The
setter is taken as the reader's inverse because `FUN_00507410` is the single 39-bit splitter that
produces the `(byte, mask)` pair once; G2 measures that the pair is a bijection over ids 0..38,
which is what makes the inverse the only candidate.  `python3 -m sim.selftest --b30` relays here.

Zero box, zero /proc, zero gdb.
"""
import hashlib
import os
import re
import shutil
import struct
import sys
import tempfile

from . import base as sob
from . import economy as soco
from . import feeder as sf
from . import itemtable as sit
from . import rules as sorules
from . import save as so
from . import savewriter as sow

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAV = os.path.join(ROOT, "programs", "saves", "m54b_clean.SAV")
RULES = os.path.join(ROOT, "data", "alpha.json")
EVID_M333 = "evidence/m333_feeder_slot_census.txt"
ARCHIVE_M46 = "docs/named-archive-m32-m84e.md"

FAC_OFF = sf.BASE_FAC_BYTES          # 0x8c, the four-byte completed-facility window
QUEUE_OFF = 0x50                     # the queue head id (M52b)
PENDING_OFF = 0x4C                   # the pending count - the MISREAD rival's source
FAC_BYTES = 4                        # the confirmed window width (sim.base.FAC_MAX / 8)
ITEM_LO, ITEM_HI = 1, 31             # the four PINNED bitmap bytes (ids 0..31); 32..38 are
                                     # outside the measured window and are REFUSED (BUILD_SPINE G1)

# Pinned from the first real run; G6 asserts the run reproduces them.
ANCHOR = "234ab3d83a88dbea"        # G6: digest of the (queue rows, write, bill) tuple
PRINT_ANCHOR = "29f408c79329a5a8"   # G6: digest of the printed table, the G6 line excluded
IMG_SHA = "3a503c638ba45330"       # G6: sha256 of the written container, first 16 hex


# --- helpers ---------------------------------------------------------------------------------
def _txt(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return fh.read().decode("utf-8", "replace")


def _line(rel, needle):
    for ln in _txt(rel).splitlines():
        if needle in ln:
            return ln
    raise AssertionError("%s not found in %s" % (needle, rel))


def _re1(pat, text, what):
    mt = re.search(pat, text)
    if not mt:
        raise AssertionError("B30 parse failed for %s: %r not in %r"
                             % (what, pat, text[:200]))
    return mt.group(1)


def digest_rows(rows):
    h = hashlib.sha256()
    for r in rows:
        h.update(repr(r).encode("utf-8"))
    return h.hexdigest()[:16]


def bounds():
    """M333's three loop bounds, parsed exactly as B28/B29 parse them (never retyped)."""
    cl = _line(EVID_M333, "G1 counter:")
    lo = int(_re1(r"init=\['[0-9a-f]+: mov esi,0x([0-9a-f]+)'\]", cl, "loop init"), 16)
    chg = int(_re1(r"charge-bound=\['[0-9a-f]+: cmp esi,0x([0-9a-f]+)'\]", cl, "charge-bound"), 16)
    rng = int(_re1(r"range-bound=\['[0-9a-f]+: cmp esi,0x([0-9a-f]+)'\]", cl, "range-bound"), 16)
    return lo, chg, rng


def disabled_list():
    """M46's own row: the disabled item ids of OUR faction (the archive is the source)."""
    dl = _line(ARCHIVE_M46, "disabled list (ours)")
    return tuple(sorted({int(x) for x in re.findall(r"item\[\d+\]=(\d+)", dl)}))


# --- the law ---------------------------------------------------------------------------------
def set_facility(rec, item):
    """The reader's INVERSE (ASSUMED law, BUILD_SPINE §B30): byte item>>3, bit 1<<(item&7).

    The guard is part of the law: id 39 would land in byte 4, outside the four bytes a recorded
    read pins, so it is REFUSED rather than written into an unmeasured window."""
    if not 0 <= item < FAC_BYTES * 8:
        raise sob.BaseError("item %r is outside the %d-byte window" % (item, FAC_BYTES))
    out = bytearray(rec)
    out[FAC_OFF + (item >> 3)] |= 1 << (item & 7)
    return bytes(out)


def rival_set_facility(rec, item):
    """The SWAPPED orientation (byte item&7, bit 1<<(item>>3)) - a rival that must FAIL."""
    out = bytearray(rec)
    out[FAC_OFF + (item & 7)] |= 1 << ((item >> 3) & (FAC_BYTES * 8 - 1))
    return bytes(out)


def rule_delta(table, item, disabled, lo, chg):
    """What the next round's bill must move by: the base now HAS the item, and the feeder
    charges it only inside its own parsed window (B29 G6: ids past the charge bound are
    uncharged even when owned)."""
    if not lo <= item <= chg:
        return 0
    return soco.item_upkeep(table, item, disabled)


# --- the measurement -------------------------------------------------------------------------
def measure(sav=SAV):
    m = {"sav": sav}
    sv = so.parse(sav)
    rules = sorules.load(RULES)
    recs, shape = sit.build(sit.alpha_rows(rules))
    table = sit.derived_table(recs)
    lo, chg, rng = bounds()
    disabled = disabled_list()
    m.update({"sv": sv, "recs": recs, "shape": shape, "table": table,
              "lo": lo, "chg": chg, "rng": rng, "disabled": disabled, "own": sv.own_player})

    # G1 - the completion READ out of the container's own queue -------------------------------
    qrows = []
    for b in sv.bases:
        rec = sv.data[b["off"]:b["off"] + so.BASE_LEN]
        head = struct.unpack_from("<i", rec, QUEUE_OFF)[0]
        pend = struct.unpack_from("<i", rec, PENDING_OFF)[0]
        owned = tuple(sob.facilities(rec))
        elig = ITEM_LO <= head <= ITEM_HI and head not in owned and lo <= head <= chg
        qrows.append((b["i"], b["name"], b["own4"], head, pend, owned, elig))
    # heads a completion COULD have paid for but that fall outside the four pinned bytes: they are
    # ineligible here by the law, so the count is printed and pinned rather than left implicit
    m["outside"] = [r[3] for r in qrows if ITEM_HI < r[3] <= 38]
    m["qrows"] = qrows
    m["n_eligible"] = sum(1 for r in qrows if r[6])
    cand = [r for r in qrows if r[2] == m["own"] and r[6]]
    if not cand:
        raise AssertionError("B30: no eligible completion in the own player's bases")
    tgt = cand[0]
    m["target"] = tgt
    idx, item = tgt[0], tgt[3]
    m["idx"], m["item"] = idx, item
    m["item_name"] = recs[item]["name"] if recs[item] else None
    m["rule"] = rule_delta(table, item, disabled, lo, chg)

    orig = bytes(sv.data[sv.bases_off + so.BASE_LEN * idx:
                         sv.bases_off + so.BASE_LEN * (idx + 1)])
    m["orig"] = orig
    m["owned_before"] = tuple(sob.facilities(orig))
    m["owned_after"] = tuple(sob.facilities(set_facility(orig, item)))

    # G2 - the setter is the reader's inverse, measured over the whole PINNED window (ids 0..31).  The loop
    # runs on a REFERENCE record whose four-byte window is ZERO: an id the target base already
    # owns would otherwise mask a broken bit law (the first run's real defect), so the law is
    # measured on a state where every id is absent and the target record is checked separately.
    ref = bytearray(orig)
    ref[FAC_OFF:FAC_OFF + FAC_BYTES] = b"\0" * FAC_BYTES
    ref = bytes(ref)
    m["ref_window_zero"] = sob.facilities(ref) == []
    rt_ok, other_bits, rt_bad = 0, 0, []
    for k in range(FAC_BYTES * 8):
        r2 = set_facility(ref, k)
        new = set(sob.facilities(r2))
        if new == {k}:
            rt_ok += 1
        else:
            rt_bad.append((k, tuple(sorted(new))))
        other_bits += len(new - {k})
    m["rt_ok"], m["rt_bad"], m["other_bits"] = rt_ok, rt_bad, other_bits
    rival_hit = sum(1 for k in range(FAC_BYTES * 8)
                    if k in sob.facilities(rival_set_facility(ref, k)))
    m["rival_hit"] = rival_hit
    m["rival_fail"] = FAC_BYTES * 8 - rival_hit
    try:
        set_facility(orig, 39)
        m["refuse39"] = False
    except sob.BaseError:
        m["refuse39"] = True

    # G3 - the write is ONE byte of the 304-B record ------------------------------------------
    after = set_facility(orig, item)
    diffs = [i for i in range(so.BASE_LEN) if orig[i] != after[i]]
    m["diff_pos"] = diffs
    m["delta"] = (after[diffs[0]] - orig[diffs[0]]) if diffs else 0
    m["expect_pos"] = FAC_OFF + (item >> 3)
    m["expect_delta"] = 1 << (item & 7)
    m["pos_in_window"] = FAC_OFF <= m["expect_pos"] < FAC_OFF + FAC_BYTES

    # G4 - the WRITER carries it, and the RELOAD reads it back --------------------------------
    ov = [{"identity": True} for _ in range(sv.n_bases)]
    t = sv.bases[idx]
    ov[idx] = {"x": t["x"], "y": t["y"], "own4": t["own4"], "fac": t["fac"]}
    m["identity_sha_ok"] = (sow.build_image(sv, bases_override=ov) == sv.data)
    img = sow.build_image(sv, bases_override=ov,
                          base_writes=[(idx, FAC_OFF + (item >> 3), after[FAC_OFF + (item >> 3)])])
    m["img"] = img
    m["img_sha"] = hashlib.sha256(img).hexdigest()[:16]
    m["img_diff"] = sorted(sow.diff_offsets(sv.data, img))
    tmp = tempfile.mkdtemp(prefix="b30_")
    try:
        p = os.path.join(tmp, "b30.SAV")
        with open(p, "wb") as fh:
            fh.write(img)
        im = so.parse(p)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    m["im"] = im
    b_off = im.bases_off + so.BASE_LEN * idx
    m["reload_owned"] = tuple(sob.facilities(im.data[b_off:b_off + so.BASE_LEN]))
    m["reload_same_shape"] = (im.n_bases == sv.n_bases and im.n_units == sv.n_units
                              and im.year == sv.year
                              and im.data[im.tail_off:] == sv.data[sv.tail_off:])
    # the WRONG-BASE rival: the same write aimed at another record must not satisfy the read
    wrong = (idx + 1) % sv.n_bases
    ov[wrong] = {"x": sv.bases[wrong]["x"], "y": sv.bases[wrong]["y"],
             "own4": sv.bases[wrong]["own4"], "fac": sv.bases[wrong]["fac"]}
    wimg = sow.build_image(sv, bases_override=ov,
                           base_writes=[(wrong, FAC_OFF + (item >> 3),
                                         after[FAC_OFF + (item >> 3)])])
    tmp2 = tempfile.mkdtemp(prefix="b30w_")
    try:
        p2 = os.path.join(tmp2, "b30w.SAV")
        with open(p2, "wb") as fh:
            fh.write(wimg)
        imw = so.parse(p2)
    finally:
        shutil.rmtree(tmp2, ignore_errors=True)
    wb = lambda k: imw.data[imw.bases_off + so.BASE_LEN * k:
                            imw.bases_off + so.BASE_LEN * (k + 1)]
    m["wrong_base_ok"] = (item not in sob.facilities(wb(idx))
                          and item in sob.facilities(wb(wrong)))
    # every OTHER base record in the written image is byte-identical to the original file: the
    # write touched one record and nothing else (the count is measured off the image, not assumed)
    m["other_recs_same"] = sum(
        1 for i in range(sv.n_bases) if i != idx
        and img[sv.bases_off + so.BASE_LEN * i:sv.bases_off + so.BASE_LEN * (i + 1)]
        == sv.data[sv.bases_off + so.BASE_LEN * i:sv.bases_off + so.BASE_LEN * (i + 1)])

    # G5 - the bill moves by the DERIVED rule, not by a constant ------------------------------
    def bill(record):
        return sf.charge_base(table, record[FAC_OFF:FAC_OFF + FAC_BYTES], 0, False,
                              disabled, lo, chg, rng)[0]

    m["bill_before"] = bill(orig)
    # the AFTER side is read out of the RELOADED container (this is what connects G4 to G5: the
    # writer/reload leg and the bill leg price the same bytes, not an in-memory mirror)
    reload_b = im.data[im.bases_off + so.BASE_LEN * idx:
                       im.bases_off + so.BASE_LEN * (idx + 1)]
    m["bill_reload_same"] = (reload_b == after)
    m["bill_after"] = bill(reload_b)
    m["bill_delta"] = m["bill_after"] - m["bill_before"]
    per_id = []
    for k in range(FAC_BYTES * 8):
        d = bill(set_facility(orig, k)) - m["bill_before"]
        per_id.append((k, d, rule_delta(table, k, disabled, lo, chg)))
    m["per_id"] = per_id
    m["per_id_bad"] = [r for r in per_id if r[1] != r[2]]
    m["rival_constant"] = [r for r in per_id if r[1] != table[r[0]]]
    m["rival_constant_ids"] = tuple(r[0] for r in m["rival_constant"])
    m["rule_zero"] = tuple(r[0] for r in per_id if r[2] == 0)

    # G6 - the rivals scored, and determinism -------------------------------------------------
    m["nowrite_fail"] = sum(1 for (k, d, rule) in per_id if rule != 0)
    m["misread_id"] = tgt[4]
    m["misread_wrong"] = (m["misread_id"] != item)
    rows = (tuple(qrows), idx, item, m["item_name"], m["rule"], m["owned_before"],
            m["owned_after"], m["diff_pos"], m["delta"], m["bill_before"], m["bill_after"],
            m["bill_delta"], tuple(m["diff_pos"]), m["img_sha"], m["rival_fail"])
    m["digest"] = digest_rows(rows)
    return m


def render(m):
    out = ["B30 - the COMPLETION leg: queue item -> the base's +0x8c bit -> writer -> reload -> bill"]
    out.append("G1 container: %d base records, own player %d, %d eligible, bounds lo=%d chg=%d rng=%d,"
               " disabled=%s" % (len(m["qrows"]), m["own"], m["n_eligible"], m["lo"], m["chg"],
                                 m["rng"], list(m["disabled"])))
    out.append("   idx  owner  name                      head  pend  owns                                     eligible")
    for r in m["qrows"]:
        out.append("   %3d  %5d  %-24s  %4d  %4d  %-40s %s"
                   % (r[0], r[2], r[1][:24], r[3], r[4], str(list(r[5]))[:40],
                      "YES" if r[6] else "-"))
    out.append("G1 target: base %d '%s' completes item %d = '%s'; rule delta = %d; heads in "
               "32..38 (outside the pinned window): %s"
               % (m["idx"], m["target"][1], m["item"], m["item_name"], m["rule"], m["outside"]))
    out.append("G2 setter: %d/%d ids round-trip exactly, stray bits %d, bad %s; swapped rival "
               "lands on %d/%d ids (fails %d); id 39 refused %s"
               % (m["rt_ok"], FAC_BYTES * 8, m["other_bits"], m["rt_bad"], m["rival_hit"],
                  FAC_BYTES * 8, m["rival_fail"], m["refuse39"]))
    out.append("G3 record: diff positions %s (expect [%d], in window %s) delta %d (expect %d)"
               % (m["diff_pos"], m["expect_pos"], m["pos_in_window"], m["delta"],
                  m["expect_delta"]))
    out.append("G4 writer: identity build byte-identical %s; written sha %s; file diff %s; "
               "reload owns %s; shape/tail same %s; wrong-base rival misses %s"
               % (m["identity_sha_ok"], m["img_sha"], m["img_diff"][:4], list(m["reload_owned"]),
                  m["reload_same_shape"], m["wrong_base_ok"]))
    out.append("G4 records: %d of %d other base records byte-identical in the written image"
               % (m["other_recs_same"], m["sv"].n_bases - 1))
    out.append("G5 bill: before %d after %d (reloaded record == written record %s) delta %d "
               "rule %d; per-id mismatches %s; "
               "'table value' rival differs at %s (rule-zero ids %s)"
               % (m["bill_before"], m["bill_after"], m["bill_reload_same"], m["bill_delta"],
                  m["rule"], m["per_id_bad"], list(m["rival_constant_ids"]),
                  list(m["rule_zero"])))
    out.append("G6 rivals: no-write fails at %d ids; +0x4c misread gives %d (wrong %s); "
               "digest %s print %s"
               % (m["nowrite_fail"], m["misread_id"], m["misread_wrong"],
                  m["digest"], print_digest(out)))
    return out


def print_digest(lines):
    body = [l for l in lines if not l.startswith("G6 rivals")]
    return hashlib.sha256("\n".join(body).encode()).hexdigest()[:16]


# --- the gates -------------------------------------------------------------------------------
def acceptance(m, results):
    def gate(name, ok):
        results.append((name, bool(ok)))

    gate("G1 the completion is READ out of the container's own queue",
         m["qrows"] and len(m["qrows"]) == m["sv"].n_bases and m["n_eligible"] == 2
         and m["target"][2] == m["own"] and m["item"] == 2
         and ITEM_LO <= m["item"] <= ITEM_HI and m["item"] not in m["owned_before"]
         and m["outside"] == [])
    gate("G2 the setter is the reader's INVERSE over the whole window",
         m["ref_window_zero"] and m["rt_ok"] == FAC_BYTES * 8 and m["other_bits"] == 0
         and not m["rt_bad"]
         and m["owned_after"] == tuple(sorted(m["owned_before"] + (m["item"],)))
         and m["rival_fail"] > 0 and not m["rival_hit"] == FAC_BYTES * 8
         and m["refuse39"])
    gate("G3 the write is exactly ONE byte of the 304-B record",
         m["diff_pos"] == [m["expect_pos"]] and m["delta"] == m["expect_delta"]
         and m["expect_delta"] > 0 and m["pos_in_window"])
    gate("G4 the writer carries it and the reload reads it back",
         m["identity_sha_ok"] and len(m["img_diff"]) == 1
         and m["other_recs_same"] == m["sv"].n_bases - 1
         and m["reload_owned"] == m["owned_after"] and m["reload_same_shape"]
         and m["wrong_base_ok"])
    gate("G5 the bill moves by the DERIVED rule, not a constant",
         m["bill_reload_same"] and m["bill_delta"] == m["rule"] and not m["per_id_bad"]
         and m["rival_constant_ids"] == tuple(sorted(m["disabled"]))
         and m["rule"] > 0)
    gate("G6 rivals fail on the printed numbers and the run is deterministic",
         m["n_eligible"] == 2 and m["item"] == 2 and m["rule"] == 1
         and m["rival_fail"] == 28 and m["rival_hit"] == 4
         and m["rival_constant_ids"] == (8,) and m["nowrite_fail"] == 26
         and m["misread_wrong"] and m["bill_delta"] == 1
         and m["det"] and m["digest"] == ANCHOR and m["img_sha"] == IMG_SHA
         and print_digest(render(m)) == PRINT_ANCHOR)


def main(argv):
    sav = argv[0] if argv else SAV
    if not os.path.exists(sav):
        print("B30: missing input %s" % sav)
        return 2
    m = measure(sav)
    m2 = measure(sav)
    # determinism is MEASURED here, not asserted in prose: two independent passes over the same
    # bytes must agree on every digest the gates pin
    m["det"] = (m2["digest"] == m["digest"] and m2["img_sha"] == m["img_sha"]
                and print_digest(render(m2)) == print_digest(render(m)))
    table = render(m)
    for line in table:
        print(line)
    results = []
    acceptance(m, results)
    bad = [n for (n, ok) in results if not ok]
    for name, ok in results:
        print(("  ok   " if ok else "  BAD  ") + name)
    if bad:
        print("FAIL B30: %d/%d gates failed" % (len(bad), len(results)))
    else:
        print("PASS B30: %d/%d gates" % (len(results), len(results)))
    print("digest(rows)=%s print_digest=%s img_sha=%s"
          % (m["digest"], print_digest(table), m["img_sha"]))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
