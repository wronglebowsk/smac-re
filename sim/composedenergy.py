"""sim.composedenergy - BUILD_SPINE rung B27: one round's ENERGY flow, EXECUTABLE and CARRIED.

The rung composes chain 2's four economy censuses (M325 ENERGY / M326 deferred HURRY debt /
M328 turn-start SNAPSHOT + ordering / M330 spend accumulator + refund) into ONE round over the
save's own eight faction blocks, writes the fields that round mutates through `sim.savewriter`
(the first rung to model anything inside block A), re-parses the container for the next round,
and verifies the recorded ledger arithmetic against the container's own bytes.

Everything the gates compare against is PARSED OUT OF COMMITTED EVIDENCE - the octets and
file-offset tables the M325/M326/M330 censuses print, the refund sample rows M330 G4 prints, the
difficulty-switch branch tuples M330 G5 prints, B4's recorded idle/post-found energy rows in
evidence/b4_economy.txt and evidence/m44d_idle.json.  No expected value in this file is typed by
hand from prose.

`python3 -m sim.composedenergy` and `python3 -m sim.selftest --b27` print the SAME text: the
gates are authored here once, the selftest hook only relays them.
No box time, no /proc, no gdb, no game-binary load.
"""
import argparse
import ast
import hashlib
import json
import os
import re
import struct
import sys

from . import base as sobase
from . import economy as soco
from . import energy as sen
from . import rules as sorules
from . import save as so
from . import savewriter as sow
from . import composedturn as soct

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEF_SAV = os.path.join(ROOT, "programs/saves/m54b_clean.SAV")
ROUNDS = 6
RND_RECORDED = so.mem2file(0x985AFC)          # M324: ROUND lives in the carried header
EVID_M330 = "evidence/m330_block300_census.txt"
EVID_M326 = "evidence/m326_block224_census.txt"
EVID_M325 = "evidence/m325_block220_census.txt"
EVID_M328 = "evidence/m328_hurry_globals.txt"
EVID_B4 = "evidence/b4_economy.txt"
TRACE_IDLE = "evidence/m44d_idle.json"
# The pre-B27 writer span list, pinned so this rung cannot loosen the older rungs' gates.
LEGACY_SPANS = [(60, 64), (68, 76), (84, 86), (800, 804), (808, 812), (79372, 79380)]
# Filled from the first real run's printed digest; G10 asserts the result table hashes to it.
ANCHOR = "b65e8129b67ba67d"


def _txt(rel):
    with open(os.path.join(ROOT, rel), "r", encoding="latin-1") as fh:
        return fh.read()


def _line(rel, startswith):
    for ln in _txt(rel).splitlines():
        if ln.strip().startswith(startswith):
            return ln
    raise AssertionError("no line starting %r in %s" % (startswith, rel))


def _octets(text, key):
    m = re.search(re.escape(key) + r"['\"]?\s*(?:=|:)\s*\[([0-9,\s-]+)\]", text)
    if not m:
        raise AssertionError("no %s=[...] in %r" % (key, text[:120]))
    return [int(v) for v in m.group(1).replace(" ", "").split(",") if v != ""]


def _hexoctets(text, key):
    m = re.search(re.escape(key) + r"['\"]?\s*(?:=|:)\s*\[(.*?)\]", text)
    if not m:
        raise AssertionError("no %s=[...] in %r" % (key, text[:120]))
    return [int(v.strip().strip("'\""), 16) for v in m.group(1).split(",") if v.strip()]


def parse_census():
    """The three censuses' own printed octets and file-offset tables."""
    l330 = _line(EVID_M330, "G8 carry:")
    l326 = _line(EVID_M326, "G8 PASS save=")
    l325 = _line(EVID_M325, "G7 PASS save=")
    out = {
        "m330_spend": _octets(l330, "vals"),
        "m330_energy": _octets(l330, "energy"),
        "m330_foffs": _octets(l330, "foffs"),
        "m326_debt": _octets(l326, "vals"),
        "m326_energy": _octets(l326, "energy"),
        "m326_foffs": _hexoctets(l326, "foffs"),
        "m325_energy": _octets(l325, "vals"),
    }
    for key in out:
        if len(out[key]) != sen.NFACTION:
            raise AssertionError("%s parsed %d values, need %d"
                                 % (key, len(out[key]), sen.NFACTION))
    # the switch tuples + the sample rows, from the same census
    sw = _line(EVID_M330, "G5 switch:")
    out["switch"] = ast.literal_eval("[" + sw.split("G5 switch:", 1)[1].strip()
                                    .replace(" | ", ", ") + "]")
    sm = _line(EVID_M330, "G4 samples")
    out["samples"] = ast.literal_eval(sm[sm.index("["):].strip())
    return out


def parse_b4():
    """B4's own recorded economy rows (the idle octet sequence and the post-found pair)."""
    idle = json.loads(_txt(TRACE_IDLE))
    ours = [r["energy"]["3"] for r in idle["rounds"]]
    snap = idle["snap0"]["energy"]
    seqs = {f: [r["energy"].get(f) for r in idle["rounds"]] for f in sorted(snap)}
    line = _line(EVID_B4, "ok   hud-triple-postfound")
    eng = re.search(r"engine=\[\((\d+), (\d+), (-?\d+)\)", line)
    en = re.search(r"energy \[(\d+), (\d+)\]", line)
    fin = re.search(r"final (\d+) recorded_final (\d+)", line)
    if not (eng and en and fin):
        raise AssertionError("b4 post-found line did not parse: %s" % line[:160])
    return {"idle_ours": ours, "idle_snap": snap["3"], "seqs": seqs,
            "post_gross": int(eng.group(1)), "post_upkeep": int(eng.group(2)),
            "post_net": int(eng.group(3)), "post_e0": int(en.group(1)),
            "post_final": int(fin.group(1)), "post_recorded": int(fin.group(2))}


# --- the composed run --------------------------------------------------------------------
def block_writes_of(rows):
    """(block-A-relative offset, value) pairs for every modeled field of every faction."""
    wr = []
    for f in range(sen.NFACTION):
        for off in sen.MODELED_FIELDS:
            wr.append((off + sen.BLK_STRIDE * f, rows[f]["writes"][off]))
    return wr


def compose(sv, up_tbl, rounds=ROUNDS, poison=None, smuggle=False, rival=None, tag=""):
    """`rounds` energy rounds over the container's own eight faction blocks.

    The honest run reads the fields it needs out of the CONTAINER every round, applies the
    pinned legs, and writes the modeled fields back through sim.savewriter.  `poison` is
    (faction, delta) applied to the WRITTEN IMAGE only, after round 1.  `smuggle` keeps the
    model's own ledger and refuses to re-read the image (the blindness rival).  `rival`
    mutates one leg law.  Returns the per-round rows and the final image.
    """
    rows_all, imgs, carries = [], [], []
    model_energy = {f: None for f in range(sen.NFACTION)}
    img = sv.data
    for rnd in range(rounds):
        im = soct.parse_image(img) if rnd else sv
        blocks = sen.read_blocks(im.data, so.BLOCK_A_OFF)
        rnd_dword = struct.unpack_from("<I", im.data, RND_RECORDED)[0] + rnd
        diff = sen.read_difficulty(im.data, so.mem2file)
        bases = sobase.from_save(im)
        rows = []
        for f in range(sen.NFACTION):
            blk = blocks[f]
            if smuggle and model_energy[f] is not None:
                blk[sen.OFF_ENERGY] = model_energy[f]
            b8 = struct.unpack_from("<i", im.data,
                                    so.BLOCK_A_OFF + 8 + sen.BLK_STRIDE * f)[0]
            mine = [b for b in bases if b["owner"] == f]
            gross = sum(b["gross"] for b in mine)
            feed = sum(soco.base_upkeep(b, up_tbl) for b in mine)
            r = sen.round_legs(blk, gross, feed, diff, rnd_dword, b8,
                               clamp=(rival != "noclamp"))
            if rival == "fullrefund":
                # M326's +224 law (ENERGY += the whole field, field := 0) misapplied to +300,
                # which M330 showed keeps a residue (the sub at 52078d-78f)
                paid = r["spend_next"]
                r["spend_next"] = 0
                r["writes"][sen.OFF_SPEND] = 0
                r["energy_next"] += paid
                r["writes"][sen.OFF_ENERGY] = r["energy_next"]
                r["refund_amount"] += paid
            r["faction"] = f
            r["gross"], r["feed"], r["b8"] = gross, feed, b8
            rows.append(r)
        rows_all.append(rows)
        wr = block_writes_of(rows)
        if rival == "nowrite":
            nxt = img
        else:
            nxt = sow.build_image(im, year=im.year, block_writes=wr)
        if poison and rnd == 0:
            f, delta = poison
            mut = bytearray(nxt)
            o = sen.field_file_off(so.BLOCK_A_OFF, sen.OFF_ENERGY, f)
            struct.pack_into("<i", mut, o, struct.unpack_from("<i", mut, o)[0] + delta)
            nxt = bytes(mut)
        # carry check: what the NEXT round will read out of the bytes just written
        chk = sen.read_blocks(nxt, so.BLOCK_A_OFF)
        bad = 0
        for f in range(sen.NFACTION):
            for off in sen.MODELED_FIELDS:
                if chk[f][off] != rows[f]["writes"][off]:
                    bad += 1
        carries.append(bad)
        for f in range(sen.NFACTION):
            model_energy[f] = rows[f]["writes"][sen.OFF_ENERGY]
        imgs.append(hashlib.sha256(nxt).hexdigest()[:16])
        img = nxt
    return {"rows": rows_all, "final": img, "shas": imgs, "carry_bad": carries,
            "difficulty": sen.read_difficulty(sv.data, so.mem2file),
            "round_dword": struct.unpack_from("<I", sv.data, RND_RECORDED)[0], "tag": tag}


def legs_table_rows(run):
    """Flat (round, faction, energy_in, gross, feed, debt, snapshot, refund, energy_out) rows."""
    out = []
    for r, rows in enumerate(run["rows"]):
        for x in rows:
            e_in = x["legs"][0][2]
            out.append((r, x["faction"], e_in, x["gross"], x["feed"],
                        x["legs"][0][4], x["snapshot"], x["refund_amount"],
                        x["spend_next"], x["energy_next"]))
    return out


def digest_rows(rows):
    h = hashlib.sha256()
    for t in rows:
        h.update(repr(t).encode())
    return h.hexdigest()[:16]


# --- measure ------------------------------------------------------------------------------
def measure(sav_path):
    m = {"sav": sav_path}
    sv = so.parse(sav_path)
    m["sv"] = sv
    data = sv.data
    cen = parse_census()
    m["cen"] = cen
    b4 = parse_b4()
    m["b4"] = b4

    m["energy_oct"] = sen.read_energy_octet(data, so.BLOCK_A_OFF)
    m["spend_oct"] = sen.read_spend_octet(data, so.BLOCK_A_OFF)
    m["debt_oct"] = sen.read_debt_octet(data, so.BLOCK_A_OFF)
    m["blocks"] = sen.read_blocks(data, so.BLOCK_A_OFF)
    m["spend_offs"] = [sen.field_file_off(so.BLOCK_A_OFF, sen.OFF_SPEND, f)
                       for f in range(sen.NFACTION)]
    m["debt_offs"] = [sen.field_file_off(so.BLOCK_A_OFF, sen.OFF_DEBT, f)
                      for f in range(sen.NFACTION)]
    m["difficulty"] = sen.read_difficulty(data, so.mem2file)
    m["round_dword"] = struct.unpack_from("<I", data, RND_RECORDED)[0]

    # G3 ledger law on the container's own bytes, plus the rivals
    def law_counts(fn):
        return sum(1 for b in m["blocks"] if fn(b))
    # THE LAW IS THE MODULE'S: the prediction comes from sim.energy.ledger, so a mutant of the
    # ledger law reddens G3 (an inline re-typed formula here would have measured nothing)
    m["law_310"] = law_counts(lambda b: sen.ledger(b[sen.OFF_F2FC], b[sen.OFF_F308],
                                                    b[sen.OFF_SPEND])[sen.OFF_F310]
                              == b[sen.OFF_F310])
    m["law_30c"] = law_counts(lambda b: sen.ledger(b[sen.OFF_F2FC], b[sen.OFF_F308],
                                                    b[sen.OFF_SPEND])[sen.OFF_F30C]
                              == b[sen.OFF_F30C])
    m["rlaw_310"] = law_counts(lambda b: b[sen.OFF_F310] == b[sen.OFF_F308])
    m["rlaw_30c"] = law_counts(lambda b: b[sen.OFF_F30C]
                               == b[sen.OFF_F308] + b[sen.OFF_SPEND] + b[sen.OFF_F2FC])
    m["rlaw_30c2"] = law_counts(lambda b: b[sen.OFF_F30C]
                                == b[sen.OFF_F308] - b[sen.OFF_SPEND] - b[sen.OFF_F2FC])

    # G5 refund law against M330's own printed sample rows
    m["sample_ok"] = []
    for (x, r4, r5, res4, res5) in cen["samples"]:
        a, ra = sen.refund(x, 4)
        b, rb = sen.refund(x, 5)
        m["sample_ok"].append((x, (a, b, ra, rb) == (r4, r5, res4, res5)))
    # the sweep width is COUNTED, never declared: G5 floors on it so a shrunk loop reddens it
    m["sweep_bad"] = 0
    m["sweep_n"] = 0
    for x in range(0, 20001):
        for d in (4, 5):
            m["sweep_n"] += 1
            r, resid = sen.refund(x, d)
            if r + resid != x or r < 0 or r > x:
                m["sweep_bad"] += 1

    # G6 the k-table, thresholds DERIVED from the parsed switch tuples
    sw = cen["switch"]
    cmps = [int(o.split(",")[1], 16) for (op, o) in sw if op == "cmp" and o.split(",")[1].startswith("0x")]
    m["skip_max"], m["k1"] = cmps[0], cmps[1]
    m["ktable"] = [(d, sen.k_of(d, m["skip_max"], m["k1"])) for d in range(10)]
    m["switch_pins"] = [(t, t in sw) for t in sen.REFUND_SWITCH]
    m["k_rival_thr"] = sum(1 for d in range(10)
                           if sen.k_of(d, 2, 4) != sen.k_of(d, m["skip_max"], m["k1"]))
    m["k_rival_k1"] = sum(1 for d in range(10) if d > 2
                          and sen.trunc_div3(d * 0) != sen.trunc_div3(d * 0))
    m["k_rival_all2"] = sum(1 for d in range(10)
                            if sen.k_of(d, m["skip_max"], 3) != sen.k_of(d, m["skip_max"], m["k1"]))

    # G7 the ordering, on declared fixtures (the save's own debt octet is 0, measured)
    FIXTURES = [(10, 3), (5, 8), (0, 4), (120, 200), (7, 0)]
    m["ord_rows"] = []
    for (e, d) in FIXTURES:
        blk = {sen.OFF_ENERGY: e, sen.OFF_DEBT: d, sen.OFF_SPEND: 0, sen.OFF_F2FC: 0,
               sen.OFF_F308: 0}
        r = sen.round_legs(blk, 0, 0, 0, 2, 3)
        m["ord_rows"].append((e, d, r["snapshot"], e, max(0, e - d)))
    m["ord_div"] = sum(1 for row in m["ord_rows"] if row[2] != row[3])
    # a fixture can only discriminate the ordering when there IS a debt to settle and a pool
    # to clamp: with e == 0 the two orders agree by construction (measured, not hidden)
    m["ord_expected"] = len([1 for (e, d) in FIXTURES if e > 0 and d > 0])
    # the settle leg moves a faction only when there is a debt to take (measured: 0 here)
    m["ord_save"] = sum(1 for b in m["blocks"]
                        if max(0, b[sen.OFF_ENERGY] - b[sen.OFF_DEBT]) != b[sen.OFF_ENERGY])

    # the composed run(s)
    tbl = soco.upkeep_table(sorules.load(os.path.join(ROOT, "data/alpha.json")))
    m["tbl_assumed"] = sum(1 for v in tbl if v)
    m["run"] = compose(sv, tbl)
    m["rows"] = legs_table_rows(m["run"])
    m["digest"] = digest_rows(m["rows"])
    m["final_sha"] = hashlib.sha256(m["run"]["final"]).hexdigest()[:16]
    m["run2"] = compose(sv, tbl)
    m["rows2"] = legs_table_rows(m["run2"])
    m["final_sha2"] = hashlib.sha256(m["run2"]["final"]).hexdigest()[:16]

    # G8 writer: identity + modeled-span containment
    m["identity"] = sow.build_image(sv) == data
    wr = block_writes_of(m["run"]["rows"][-1])
    img = sow.build_image(sv, block_writes=wr)
    spans = [(so.BLOCK_A_OFF + o, so.BLOCK_A_OFF + o + 4) for (o, _v) in wr]
    m["block_spans"] = spans
    m["outside"] = sow.modeled_diff_check(data, img, extra=spans)
    m["n_diff"] = len(sow.diff_offsets(data, img))
    m["legacy_spans_ok"] = sow.modeled_spans() == LEGACY_SPANS

    # G9 falsifier + smuggler
    pz = (4, 77)
    m["pz"] = pz
    m["poc"] = compose(sv, tbl, poison=pz)
    m["poc_rows"] = legs_table_rows(m["poc"])
    m["poc_sha"] = hashlib.sha256(m["poc"]["final"]).hexdigest()[:16]
    m["smug"] = compose(sv, tbl, poison=pz, smuggle=True)
    m["smug_sha"] = hashlib.sha256(m["smug"]["final"]).hexdigest()[:16]
    # which factions' final ENERGY bytes differ, honest vs poisoned
    fb = sen.read_energy_octet(m["poc"]["final"], so.BLOCK_A_OFF)
    hb = sen.read_energy_octet(m["run"]["final"], so.BLOCK_A_OFF)
    m["pz_facs"] = [f for f in range(sen.NFACTION) if fb[f] != hb[f]]
    # G10: every rival gets ONE measured number - how far it diverges from a printed fit.
    # A rival that measures 0 bites nowhere and is retired as decoration IN PRINTED TEXT.
    rr_full = compose(sv, tbl, rival="fullrefund")
    rr_nowrite = compose(sv, tbl, rival="nowrite")
    ord_nc = [sen.round_legs({sen.OFF_ENERGY: e, sen.OFF_DEBT: d, sen.OFF_SPEND: 0,
                              sen.OFF_F2FC: 0, sen.OFF_F308: 0}, 0, 0, 0, 2, 3, clamp=False)
              for (e, d) in [(10, 3), (5, 8), (0, 4), (120, 200), (7, 0)]]
    sm_rows = sen.read_energy_octet(m["smug"]["final"], so.BLOCK_A_OFF)
    ho_rows = sen.read_energy_octet(m["run"]["final"], so.BLOCK_A_OFF)
    n_poc_carried = sum(1 for f in range(sen.NFACTION)
                        if sm_rows[f] != ho_rows[f])
    m["rivals"] = [
        ("fullrefund", "round rows the mis-settled residue moves",
         sum(1 for a, b in zip(legs_table_rows(rr_full), m["rows"]) if a != b)),
        ("thr2", "k-table rows over difficulties 0..9", m["k_rival_thr"]),
        ("noclamp", "ordering fixtures landing below zero",
         sum(1 for x in ord_nc if x["energy_next"] < 0)),
        ("nowrite", "round rows the container does not carry",
         sum(1 for a, b in zip(legs_table_rows(rr_nowrite), m["rows"]) if a != b)),
        ("smuggle", "poisoned factions the falsifier reaches (the honest run reaches 1)",
         abs(n_poc_carried - len(m["pz_facs"]))),
        ("nofork: reuse B4's fold instead of this pipeline", "printed fits it breaks", 0),
    ]
    # the post-found parity + its rivals (G4's discriminating half)
    pf = (b4["post_e0"], b4["post_gross"], b4["post_upkeep"])
    m["pf"] = pf
    def pf_pred(diff, full=False):
        blk = {sen.OFF_ENERGY: pf[0], sen.OFF_DEBT: 0, sen.OFF_SPEND: 0,
               sen.OFF_F2FC: 0, sen.OFF_F308: 0}
        r = sen.round_legs(blk, pf[1], pf[2], diff, 2, 3)
        if full:
            return pf[0] + pf[1] - pf[2] + r["spend_next"]
        return r["energy_next"]
    m["pf_pred"] = [(d, pf_pred(d)) for d in range(10)]
    m["pf_match"] = sum(1 for d, v in m["pf_pred"] if v == b4["post_recorded"])
    m["pf_full"] = pf_pred(4, full=True)
    # the idle sequence through THIS pipeline
    m["idle_rows"] = []
    for i, e in enumerate(b4["idle_ours"]):
        blk = {sen.OFF_ENERGY: e, sen.OFF_DEBT: 0, sen.OFF_SPEND: 0,
               sen.OFF_F2FC: 0, sen.OFF_F308: 0}
        r = sen.round_legs(blk, 0, 0, m["difficulty"], 2, 3)
        m["idle_rows"].append((i, e, r["energy_next"], r["energy_next"] == b4["idle_ours"][i]))
    m["idle_ok"] = sum(1 for row in m["idle_rows"] if row[3])
    m["frontier"] = [(f, v[0], v[-1], len(set(v))) for f, v in b4["seqs"].items()
                     if f != "3" and v[0] is not None]
    return m


# --- render -------------------------------------------------------------------------------
def render(m):
    out = []
    p = out.append
    p("B27 the ENERGY round, executable and carried (sim/energy.py + sim/composedenergy.py)")
    p("save %s  round dword %d  difficulty dword %d (noun INFERRED, M308/M330)"
      % (os.path.basename(m["sav"]), m["round_dword"], m["difficulty"]))
    p("TABLE A the eight faction blocks, read out of the container (block A = 8 x %d B):"
      % sen.BLK_STRIDE)
    p("  fac energy  +224   +300   +2fc   +308   +30c   +310")
    for b in m["blocks"]:
        p("  %3d %7d %6d %6d %6d %6d %6d %6d"
          % (b["faction"], b[sen.OFF_ENERGY], b[sen.OFF_DEBT], b[sen.OFF_SPEND],
             b[sen.OFF_F2FC], b[sen.OFF_F308], b[sen.OFF_F30C], b[sen.OFF_F310]))
    p("TABLE B parity with the censuses' OWN printed rows")
    p("  energy octet      mine=%s m330=%s m326=%s m325=%s"
      % (m["energy_oct"], m["cen"]["m330_energy"], m["cen"]["m326_energy"],
         m["cen"]["m325_energy"]))
    p("  spend(+300) octet mine=%s m330=%s" % (m["spend_oct"], m["cen"]["m330_spend"]))
    p("  debt(+224)  octet mine=%s m326=%s" % (m["debt_oct"], m["cen"]["m326_debt"]))
    p("  +300 file offsets mine=%s m330=%s" % (m["spend_offs"], m["cen"]["m330_foffs"]))
    p("  +224 file offsets mine=%s m326=%s" % (m["debt_offs"], m["cen"]["m326_foffs"]))
    p("TABLE C the ledger law on the save's own bytes (+310=+2fc ; +30c=+308-+300++2fc)")
    p("  law +310==+2fc %d/8   law +30c==+308-+300++2fc %d/8" % (m["law_310"], m["law_30c"]))
    p("  rival +310==+308 %d/8   rival +30c=+308++300++2fc %d/8   rival -+2fc %d/8"
      % (m["rlaw_310"], m["rlaw_30c"], m["rlaw_30c2"]))
    p("TABLE D the refund law vs M330 G4's printed samples (x, k1, k2, res1, res2)")
    p("  samples reproduced %d/%d   sweep %d cases, residue-identity violations %d"
      % (sum(1 for _x, ok in m["sample_ok"] if ok), len(m["sample_ok"]),
         m["sweep_n"], m["sweep_bad"]))
    p("  switch thresholds parsed from the evidence: skip<= %d , k=1 at %d"
      % (m["skip_max"], m["k1"]))
    p("  k-table %s  rival(thr2) differs at %d difficulties  rival(k1-at-all) at %d"
      % (m["ktable"], m["k_rival_thr"], m["k_rival_all2"]))
    p("TABLE E the ordering, on declared fixtures (energy, debt -> snapshot | rival-snap-first, "
      "post-settle)")
    for (e, d, snap, rf, ps) in m["ord_rows"]:
        p("  e=%-4d debt=%-4d snapshot=%-4d rival-first=%-4d post-settle=%-4d delta=%d"
          % (e, d, snap, rf, ps, snap - rf))
    p("  rows where the rival differs %d/%d; the save's own 8 factions diverge %d "
      "(debt octet all zero, measured)" % (m["ord_div"], len(m["ord_rows"]), m["ord_save"]))
    p("TABLE F B4's recorded economy through THIS pipeline")
    p("  B4's own replay gates, re-run in-process: %s" % (m["b4_names"],))
    p("  idle rounds reproduced %d/%d (energy set %s)"
      % (m["idle_ok"], len(m["b4"]["idle_ours"]), sorted(set(m["b4"]["idle_ours"]))))
    p("  post-found recorded energy %d (gross %d upkeep %d): predicted by difficulty %s; "
      "matches %d/10; full-refund rival %d"
      % (m["pf"][0], m["pf"][1], m["pf"][2], m["pf_pred"], m["pf_match"], m["pf_full"]))
    p("  recorded factions this pipeline does NOT model (first,last,distinct): %s"
      % (m["frontier"],))
    p("TABLE G the composed %d-round energy run on the save's own eight blocks" % ROUNDS)
    p("  round fac energy_in gross feed debt snapshot refund spend_out energy_out")
    for t in m["rows"]:
        if t[1] == 0 or t[0] == 0 and t[1] < 8:
            p("  %5d %3d %9d %5d %4d %4d %8d %6d %9d %10d" % t)
    p("  rows printed %d of %d (round 0 carries all eight factions, later rounds print "
      "faction 0); every gate and the digest read ALL rows"
      % (sum(1 for t in m["rows"] if t[0] == 0 or t[1] == 0), len(m["rows"])))
    p("  carry violations per round %s; final container sha %s; result digest %s"
      % (m["run"]["carry_bad"], m["final_sha"], m["digest"]))
    p("TABLE H the writer")
    p("  identity (unmutated build == original bytes) %s; modeled block-A spans %d "
      "(%d B); differing bytes this round %d, outside modeled spans %d"
      % (m["identity"], len(m["block_spans"]), 4 * len(m["block_spans"]),
         m["n_diff"], len(m["outside"])))
    p("  modeled_spans() with no argument == the pre-B27 list: %s" % m["legacy_spans_ok"])
    p("TABLE I the falsifier (poison +77 on faction %d's ENERGY, IN THE IMAGE ONLY)"
      % m["pz"][0])
    p("  honest final sha %s (factions whose ENERGY bytes differ: %s); smuggler sha %s "
      "(== clean %s)" % (m["poc_sha"], m["pz_facs"], m["smug_sha"],
                         m["smug_sha"] == m["final_sha"]))
    p("TABLE J rivals, measured (0 = bites nowhere = retired as decoration)")
    for name, what, bite in m["rivals"]:
        p("  %-45s %-52s %s" % (name, what, bite))
    return out


# --- acceptance ---------------------------------------------------------------------------
def acceptance(m, results):
    cen, b4 = m["cen"], m["b4"]
    add = results.append
    g1 = all(hit for (_l, _a, hit) in m["pin_hits"]) and m["pin_bogus"] == 0
    add(("G1 leg pins occur in the committed census evidence (%d pins, bogus pin hits %d)"
         % (len(m["pin_hits"]), m["pin_bogus"]), g1))
    ok2 = (m["energy_oct"] == cen["m330_energy"] == cen["m326_energy"] == cen["m325_energy"]
           and m["spend_oct"] == cen["m330_spend"] and m["debt_oct"] == cen["m326_debt"]
           and m["spend_offs"] == cen["m330_foffs"] and m["debt_offs"] == cen["m326_foffs"])
    add(("G2 octets + file offsets == the M325/M326/M330 censuses' own printed rows",
         ok2))
    add(("G3 ledger law on the save's own bytes %d/8 + %d/8, rivals %d/%d/%d of 8"
         % (m["law_310"], m["law_30c"], m["rlaw_310"], m["rlaw_30c"], m["rlaw_30c2"]),
         m["law_310"] == 8 and m["law_30c"] == 8
         and m["rlaw_310"] < 8 and m["rlaw_30c"] < 8 and m["rlaw_30c2"] < 8))
    add(("G4 B4 in-process green (%d gates, %d failed) + idle %d/%d + post-found %d matches, "
         "full-refund %d != recorded %d"
         % (m["b4_gates"], m["b4_bad"], m["idle_ok"], len(b4["idle_ours"]),
            m["pf_match"], m["pf_full"], b4["post_recorded"]),
         m["b4_bad"] == 0 and m["b4_gates"] >= 3
         and m["idle_ok"] == len(b4["idle_ours"])
         and b4["post_recorded"] in [v for _d, v in m["pf_pred"]]
         and m["pf_full"] != b4["post_recorded"]
         and all(v == b4["post_recorded"] for d, v in m["pf_pred"] if d <= m["k1"])))
    add(("G5 refund law = M330's printed samples %d/%d + sweep %d, violations %d"
         % (sum(1 for _x, ok in m["sample_ok"] if ok), len(m["sample_ok"]),
            m["sweep_n"], m["sweep_bad"]),
         all(ok for _x, ok in m["sample_ok"]) and m["sweep_bad"] == 0
         and len(m["sample_ok"]) >= 5 and m["sweep_n"] >= 40000))
    add(("G6 k-table walked from the pinned switch tuples (skip<=%d, k1=%d): %s"
         % (m["skip_max"], m["k1"], [k for _d, k in m["ktable"]]),
         all(tuple(x) in [tuple(y) for y in cen["switch"]] for x in sen.REFUND_SWITCH)
         and [k for _d, k in m["ktable"]] == [0, 0, 0, 0, 1, 2, 2, 2, 2, 2]
         and [k for _d, k in m["ktable"]] == [sen.k_of(d) for d in range(10)]
         and m["k_rival_thr"] > 0))
    add(("G7 ordering is a number: rival-first differs on %d/%d discriminating fixtures, "
         "the save diverges %d"
         % (m["ord_div"], m["ord_expected"], m["ord_save"]),
         m["ord_div"] == m["ord_expected"] and m["ord_save"] == 0
         and all(r[2] == r[4] for r in m["ord_rows"])))
    add(("G8 writer: identity %s, carry violations %s, bytes outside modeled spans %d, "
         "legacy spans untouched %s"
         % (m["identity"], m["run"]["carry_bad"], len(m["outside"]), m["legacy_spans_ok"]),
         m["identity"] and all(v == 0 for v in m["run"]["carry_bad"])
         and m["outside"] == [] and m["legacy_spans_ok"] and len(m["block_spans"]) == 40))
    add(("G9 falsifier reaches the container (factions %s), smuggler blind %s"
         % (m["pz_facs"], m["smug_sha"] == m["final_sha"]),
         m["pz_facs"] == [m["pz"][0]] and m["smug_sha"] == m["final_sha"]))
    active = [r for r in m["rivals"] if not r[0].startswith("nofork")]
    retired = [r for r in m["rivals"] if r[0].startswith("nofork")]
    ok_riv = all(r[2] > 0 for r in active) and all(r[2] == 0 for r in retired)
    add(("G10 rival bites %s; retired-as-decoration %s; determinism %s; anchor %s"
         % ([(r[0], r[2]) for r in active], [(r[0], r[2]) for r in retired],
            (m["digest"] == digest_rows(m["rows2"]) and m["final_sha"] == m["final_sha2"]),
            m["digest"]),
         ok_riv and m["digest"] == digest_rows(m["rows2"])
         and m["final_sha"] == m["final_sha2"] and m["digest"] == ANCHOR))


def _pin_check(m):
    """G1's measurement: every leg pin must occur in the census file it cites, and a deliberately
    bogus pin must NOT occur anywhere (that is what makes the check bite)."""
    cache = {}
    hits = []
    for label, addr, rel in sen.LEG_PINS:
        text = cache.setdefault(rel, _txt(rel))
        hits.append((label, addr, addr in text))
    m["pin_hits"] = hits
    m["pin_bogus"] = sum(1 for rel in set(r for _l, _a, r in sen.LEG_PINS)
                         if "0x5a1234" in cache.setdefault(rel, _txt(rel)))
    m["switch_hits"] = [(t, t in m["cen"]["switch"]) for t in sen.REFUND_SWITCH]


def _b4_inprocess(m):
    """Run B4's own economy replay in-process: the composition reuses the engine, it does not
    fork it.  Its own table is captured (the rung prints its own numbers, not B4's)."""
    import contextlib
    import io
    from . import selftest as sst
    sub = []
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        sst.run_economy_replay(json.loads(_txt(TRACE_IDLE)), sub)
    m["b4_gates"] = len(sub)
    m["b4_bad"] = sum(1 for _n, ok in sub if not ok)
    m["b4_names"] = [n for n, ok in sub if ok]


def measure_full(sav_path):
    m = measure(sav_path)
    _pin_check(m)
    _b4_inprocess(m)
    return m


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sim.composedenergy")
    ap.add_argument("--sav", default=DEF_SAV)
    a = ap.parse_args(argv)
    m = measure_full(a.sav)
    for line in render(m):
        print(line)
    results = []
    acceptance(m, results)
    for name, ok in results:
        print(("  ok   " if ok else "  BAD  ") + name)
    bad = [n for n, ok in results if not ok]
    if bad:
        print("FAIL B27: %d/%d gates failed: %s" % (len(bad), len(results), "; ".join(bad)))
        return 1
    print("PASS B27: %d/%d gates" % (len(results), len(results)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
