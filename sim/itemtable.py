"""sim.itemtable - the runtime ITEM TABLE DERIVED from alpha through the M337 loader law (B29).

`sim.economy.upkeep_table` maps runtime id -> upkeep with `ALPHA_SHIFT = 1`, an assumption B4
inherited from `m32-m84e.md:270` and could only spot-check at five live-pinned ids (it printed two
`table-later` rows that DIFFER under it and declared the runtime row order OPEN).  M337 pinned the
order statically: the loader at `0x57a7ef..0x57a899` opens the `FACILITIES` section, walks
`esi = record+0xc` from record 1 by 0x30 to record 72, reads ONE line per iteration and switches
to the 11-token path exactly at alpha's first 11-token row (index 38 -> record 39); the consumer
bound is 39 (`cmp esi,0x27` @`0x4f4a35`), not the array size.

This module executes that loader over `data/alpha.json` and nothing else: `build()` replays the
loop (record i = alpha row i-1, record 0 the placeholder it never writes), `upkeep_at()` reads the
priced field (+0x10), and `run_gates()` measures the derivation against the committed censuses and
against B28's own run.  Every number a gate asserts is parsed out of a committed file or computed
from `data/alpha.json`; none is retyped here.

No box time, no /proc, no gdb, no game-binary load.
"""
import hashlib
import json
import os
import re
import sys
import tempfile

from . import composedfeeder as scf
from . import economy as soco
from . import rules as sorules

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES = os.path.join(ROOT, "data", "alpha.json")
EVID_M337 = "evidence/m337_item_order.txt"
EVID_M333 = "evidence/m333_feeder_slot_census.txt"
EVID_B4 = "evidence/b4_economy.txt"
EVID_B28 = "evidence/b28_feeder_exec.txt"
ARCHIVE_M46 = "docs/named-archive-m32-m84e.md"
SAV = os.path.join(ROOT, "programs", "saves", "m54b_clean.SAV")

# --- geometry, all of it owned by a committed census (G1 proves each address+token pair) -----
ROW0 = 0x984D38          # M337: the 72-record array
STRIDE = 0x30            # M337 G1
FIELD_UPKEEP = 0x10      # M337 G6: the dword the feeder prices
RECORDS = 72             # M337: 1 + 71 iterations
CONSUMER_BOUND = 39      # M337 G2: `cmp esi,0x27` @ 0x4f4a35
ITEM_COUNT = 39          # sim.base.ITEM_COUNT: the runtime view is the consumer's bound

# --- leg pins: (label, address-as-printed, FIELD TOKEN, committed evidence file) ------------
# G1 requires ONE evidence line to carry BOTH the address and the token claimed for it.
LEG_PINS = (
    ("view-field", "0x984d38", "stride 0x30", EVID_M337),
    ("loader-open", "0x57a7ef", '"FACILITIES"', EVID_M337),
    ("cursor-start", "0x984d74", "(rec 1)", EVID_M337),
    ("cursor-branch", "0x985494", "(rec 39)", EVID_M337),
    ("cursor-end", "0x985ac4", "(rec 72)", EVID_M337),
    ("consumer-bound", "4f4a35", "cmp esi,0x27", EVID_M333),
    ("back-edge", "0x57a866", "skips all 5 trailing stores", EVID_M337),
    ("store-3-landing", "0x984d48", "store #3 lands at rec+0x10", EVID_M337),
    # the deliberately-bogus CONTROL pin ships inside the same list so it is measured in the
    # same pass: it must hit NOTHING (an evidence grep that cannot fail greps nothing).
    ("CONTROL-bogus", "0x57a8ff", "zzz-not-a-real-token-zzz", EVID_M337),
)

# Filled from the first real run's printed digests; G8 asserts the table hashes to them.
ANCHOR = "e4b1c98e68ff8685"        # digest of the (rec, alpha_idx, name, cost, upkeep, nf) rows
PRINT_ANCHOR = "377094bc16aa8f27"  # digest of the printed table, the G8 line excluded
ALPHA_SHA = "bac04f33eb692085e9f3dc016ef215cc8ab98a82ae2ce2241c2827be1fee5c72"  # data/alpha.json


# --- helpers --------------------------------------------------------------------------------
def _txt(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return fh.read().decode("utf-8", "replace")


def _line(rel, needle):
    for ln in _txt(rel).splitlines():
        if needle in ln:
            return ln
    raise AssertionError("%s not found in %s" % (needle, rel))


def _count_lines(rel, addr, token):
    """How many lines of `rel` carry BOTH the address and the field token (G1's unit)."""
    return sum(1 for ln in _txt(rel).splitlines() if addr in ln and token in ln)


def _re1(pat, text, what):
    m = re.search(pat, text)
    if not m:
        raise AssertionError("cannot parse %s out of %r" % (what, text[:120]))
    return m.group(1)


def _re2(pat, text, what):
    m = re.search(pat, text)
    if not m:
        raise AssertionError("cannot parse %s out of %r" % (what, text[:120]))
    return m.group(1), m.group(2)


def alpha_rows(rules=None):
    rules = rules if rules is not None else sorules.load(RULES)
    return rules.section("FACILITIES")


# --- the law: M337's loader, executable ------------------------------------------------------
def build(rows):
    """Replay `0x57a7ef..0x57a899` over the alpha `#FACILITIES` rows.

    One line read + one record step per iteration, records 1..len(rows) written, record 0 the
    placeholder the loop never touches.  The 11-token branch is not a switch in the OUTPUT order
    (it adds columns to the same row) - it is recorded so the shape can be gated.
    """
    recs = [None] * (len(rows) + 1)          # 0 placeholder .. len(rows) last
    widths = {}
    branch = None
    for i, row in enumerate(rows):
        f = row["fields"]
        nf = len(f)
        widths[nf] = widths.get(nf, 0) + 1
        if branch is None and nf >= 11:
            branch = i + 1                   # record number the 11-token path starts at
        recs[i + 1] = {"rec": i + 1, "alpha_index": i, "name": f[0],
                       "cost": int(f[1]), "upkeep": int(f[2]), "nf": nf}
    shape = {"start": 1, "branch": branch, "end": len(rows) + 1, "iterations": len(rows),
             "widths": widths, "records": len(rows) + 1}
    return recs, shape


def upkeep_at(recs, item):
    """The +0x10 view (M337 G6): `48*item + 0x984d48` == recs[item]['upkeep']."""
    if item < 0 or item >= len(recs) or recs[item] is None:
        return 0
    return recs[item]["upkeep"]


def derived_table(recs, n=ITEM_COUNT):
    return [upkeep_at(recs, i) for i in range(n)]


def digest_rows(recs):
    h = hashlib.sha256()
    for r in recs:
        if r is None:
            h.update(b"0|placeholder\n")
        else:
            h.update(("%d|%d|%s|%d|%d|%d\n" % (r["rec"], r["alpha_index"], r["name"],
                                               r["cost"], r["upkeep"], r["nf"])).encode())
    return h.hexdigest()[:16]


def render(recs, shape):
    out = ["B29 - the item table derived from alpha through M337's loader law",
           "geometry: row0=0x%x stride=0x%x +0x%x records=%d consumer-bound=%d"
           % (ROW0, STRIDE, FIELD_UPKEEP, shape["records"], CONSUMER_BOUND),
           "rec  a_idx  nf  cost upk  name"]
    for r in recs:
        if r is None:
            out.append("%3d  %5s  %2s  %4s %3s  <placeholder: the loop never writes record 0>"
                       % (0, "-", "-", "-", "-"))
        else:
            out.append("%3d  %5d  %2d  %4d %3d  %s"
                       % (r["rec"], r["alpha_index"], r["nf"], r["cost"], r["upkeep"],
                          r["name"]))
    return out


def print_digest(recs, shape):
    """Digest of the printed table (the G8 line is not part of it: it carries the pins)."""
    return hashlib.sha256("\n".join(render(recs, shape)).encode()).hexdigest()[:16]


# --- the measurement -------------------------------------------------------------------------
def measure(sav=SAV):
    m = {"sav": sav}
    rules = sorules.load(RULES)
    rows = alpha_rows(rules)
    recs, shape = build(rows)
    m["rows"], m["recs"], m["shape"] = rows, recs, shape

    # G1 pin integrity
    m["pins"] = [(lab, ad, tok, f, _count_lines(f, ad, tok)) for (lab, ad, tok, f) in LEG_PINS]
    m["pins_real"] = [p for p in m["pins"] if not p[0].startswith("CONTROL")]
    m["pins_hit"] = sum(1 for p in m["pins_real"] if p[4] >= 1)
    m["pins_zero"] = [p[0] for p in m["pins_real"] if p[4] == 0]
    m["control"] = [p for p in m["pins"] if p[0].startswith("CONTROL")][0]

    # G2 the window and the token census are READ out of the M337 evidence
    g2 = _line(EVID_M337, "PASS G2 window:")
    m["c_rec_lo"], m["c_rec_hi"] = (int(x) for x in
                                    _re2(r"records (\d+)\.\.(\d+)", g2, "record window"))
    m["c_branch"] = int(_re1(r"branch=rec(\d+)", g2, "branch record"))
    m["c_end"] = int(_re1(r"end=rec(\d+)", g2, "end record"))
    m["c_iter"] = int(_re1(r"iterations=(\d+)", g2, "iterations"))
    m["c_bound"] = int(_re1(r"consumer-bound=(\d+)", g2, "consumer bound"))
    g3 = _line(EVID_M337, "PASS G3 alpha row count")
    m["c_rows"] = int(_re1(r"rows=(\d+)", g3, "alpha row count"))
    m["c_w6"] = int(_re1(r'"6": (\d+)', g3, "6-token count"))
    m["c_w7"] = int(_re1(r'"7": (\d+)', g3, "7-token count"))
    m["c_w11"] = int(_re1(r'"11": (\d+)', g3, "11-token count"))
    # the builder's own shape, from data/alpha.json
    m["b_rec_lo"], m["b_rec_hi"] = shape["start"], shape["iterations"]
    m["b_branch"], m["b_end"], m["b_iter"] = shape["branch"], shape["end"], shape["iterations"]
    m["b_rows"] = len(rows)
    m["b_w6"], m["b_w7"], m["b_w11"] = (shape["widths"].get(6, 0), shape["widths"].get(7, 0),
                                        shape["widths"].get(11, 0))
    # rival: the array is the consumer's 39 records
    m["rival39_end"] = CONSUMER_BOUND

    # G3 the derived table vs the sim's own table
    derived = derived_table(recs)
    simt = soco.upkeep_table(rules)
    m["derived"], m["sim_table"] = derived, simt
    m["ids"] = list(range(1, ITEM_COUNT))
    m["upk_eq"] = sum(1 for i in m["ids"] if derived[i] == simt[i])
    m["name_eq"] = sum(1 for i in m["ids"] if soco.item_name(rules, i) == recs[i]["name"])
    shift0 = soco.upkeep_table(rules, shift=0)
    m["shift0_diff"] = sum(1 for i in m["ids"] if shift0[i] != derived[i])
    m["shift0_diff_ids"] = [i for i in m["ids"] if shift0[i] != derived[i]]
    m["shift0_name_diff"] = sum(1 for i in m["ids"]
                                if soco.item_name(rules, i, shift=0) != recs[i]["name"])

    # G4 the five live-pinned rows + the recorded sums, all parsed out of b4_economy.txt
    b4 = _line(EVID_B4, "upkeep-table")
    m["pinned"] = [(int(a), b, int(c)) for (a, b, c) in
                   re.findall(r"\((\d+), \('([^']+)', (\d+)\)\)", b4)]
    m["fac_set"] = [int(x) for x in
                    re.findall(r"\d+", re.search(r"facilities \[([0-9, ]+)\]", b4).group(1))]
    m["rec_raw"] = int(_re1(r"raw sum (\d+)", b4, "raw sum"))
    m["rec_dis"] = int(_re1(r"recorded disabled list (\d+)", b4, "disabled sum"))
    m["rec_hud"] = int(_re1(r"0x744f28 (\d+)", b4, "recorded 0x744f28"))
    m["pin_match"] = sum(1 for (i, nm, up) in m["pinned"]
                         if recs[i]["upkeep"] == up and recs[i]["name"] == nm)
    m["der_raw"] = sum(recs[i]["upkeep"] for i in m["fac_set"])
    dl = _line(ARCHIVE_M46, "disabled list (ours)")
    m["disabled"] = sorted({int(x) for x in re.findall(r"item\[\d+\]=(\d+)", dl)})
    m["der_dis"] = sum(0 if i in m["disabled"] else recs[i]["upkeep"] for i in m["fac_set"])
    m["der_dis_nolist"] = sum(recs[i]["upkeep"] for i in m["fac_set"])
    # rivals on the same numbers.  A VALUE-only rival does NOT discriminate here (the five pinned
    # upkeeps are 0,0,1,1,1 and the neighbouring rows carry the same values) - the NAME is the
    # discriminator, so it is measured separately rather than hidden in a passed assertion.
    m["pin_atidx_name_ok"] = sum(1 for (i, nm, _up) in m["pinned"]
                                 if recs[i - 1] is not None and recs[i - 1]["name"] == nm)
    m["pin_atidx_val_ok"] = sum(1 for (i, _nm, up) in m["pinned"]
                                if upkeep_at(recs, i - 1) == up)
    m["pin_rev_name_ok"] = sum(1 for (i, nm, _up) in m["pinned"]
                               if recs[ITEM_COUNT - 1 - i] is not None
                               and recs[ITEM_COUNT - 1 - i]["name"] == nm)

    # G5 B4's two DIFFERS rows: one id convention must not explain both sets
    m["later"] = []
    for ln in _txt(EVID_B4).splitlines():
        mm = re.search(r"info table-later\s+(.+?)\s+alpha line (\d+) upkeep (\d+) "
                       r"vs M46 live read (\d+) DIFFERS", ln)
        if mm:
            m["later"].append((mm.group(1).strip(), int(mm.group(2)), int(mm.group(3)),
                               int(mm.group(4))))
    m["later_atidx"] = [(nm, idx, m46, upkeep_at(recs, idx)) for (nm, idx, _up, m46) in m["later"]]
    m["later_plus1"] = [(nm, idx, m46, upkeep_at(recs, idx + 1)) for (nm, idx, _up, m46) in m["later"]]
    m["later_atidx_ok"] = sum(1 for (_nm, _i, m46, v) in m["later_atidx"] if m46 == v)
    m["later_plus1_ok"] = sum(1 for (_nm, _i, m46, v) in m["later_plus1"] if m46 == v)
    m["later_b4_ok"] = sum(1 for (_nm, _i, up, _m) in m["later"]
                           if upkeep_at(recs, _i + 1) == up)

    # G6 the boundary: what the consumer can reach vs what the loader wrote
    m["past_branch"] = [r for r in recs if r is not None and r["rec"] >= shape["branch"]]
    m["past_branch_n"] = len(m["past_branch"])
    lo, hi = _feeder_bounds()
    m["f_lo"], m["f_hi"] = lo, hi
    m["chargeable"] = [i for i in range(1, shape["records"]) if lo <= i <= hi]
    m["chargeable_past"] = [i for i in m["chargeable"] if i >= shape["branch"]]
    m["uncharged_in_branch"] = [i for i in range(1, shape["branch"]) if not (lo <= i <= hi)]
    m["bound_eq_branch"] = (CONSUMER_BOUND == shape["branch"] and m["c_bound"] == shape["branch"])

    # G7 B28's own run, fed by the DERIVED table, reproduces its pinned anchors
    b28 = _txt(EVID_B28).strip().splitlines()[-1]
    m["a28_rows"] = _re1(r"digest\(rows\)=([0-9a-f]+)", b28, "B28 rows digest")
    m["a28_print"] = _re1(r"print_digest=([0-9a-f]+)", b28, "B28 print digest")
    m["a28_sha"] = _re1(r"final_sha=([0-9a-f]+)", b28, "B28 final sha")
    orig = soco.upkeep_table
    try:
        soco.upkeep_table = lambda _rules, shift=1: derived       # the substitution under test
        bm = scf.measure_full(sav)
    finally:
        soco.upkeep_table = orig
    m["b28_table_is_derived"] = (bm["table"] is derived)
    m["b28_rows"] = bm["digest"]
    m["b28_sha"] = bm["final_sha"]
    lines = scf.render(bm)
    m["b28_print"] = hashlib.sha256("\n".join(l for l in lines if not l.startswith("G8 "))
                                    .encode()).hexdigest()[:16]
    m["b28_touch"] = bm.get("real_touched", [])

    # G8 determinism + rivals summarised
    recs2, shape2 = build(alpha_rows(sorules.load(RULES)))
    m["digest"] = digest_rows(recs)
    m["digest2"] = digest_rows(recs2)
    m["table_sha"] = hashlib.sha256(repr(derived).encode()).hexdigest()[:16]
    m["table_sha2"] = hashlib.sha256(repr(derived_table(recs2)).encode()).hexdigest()[:16]
    m["alpha_sha"] = hashlib.sha256(open(RULES, "rb").read()).hexdigest()
    costs = [r["cost"] for r in recs[1:shape["branch"]]]
    m["cost_inversions"] = sum(1 for a, b in zip(costs, costs[1:]) if b < a)
    # Five rival CLAIMS, each refuted by the number it is refuted by.  Two are claims about the
    # ARRAY (its extent, its row ORDER), three about the TABLE's indexing - none is a proxy for
    # another: extent 39 vs the census end 72; file order carries 13 cost inversions (so "sorted
    # by cost" is out); the table is not alpha's without the +1; it is not reversed; it is not
    # read at the alpha index.  G8 prints each number next to its claim.
    m["rivals"] = {
        "array-extent-39 (census end %d)" % m["c_end"]: m["rival39_end"] != m["c_end"],
        "table=alpha-without-+1 (%d ids)" % m["shift0_diff"]: m["shift0_diff"] > 0,
        "order=reversed (%d/5 names)" % m["pin_rev_name_ok"]: m["pin_rev_name_ok"] == 0,
        "order=cost-sorted (%d inversions)" % m["cost_inversions"]: m["cost_inversions"] > 0,
        "table=read-at-alpha-index (%d/5 names)" % m["pin_atidx_name_ok"]:
            m["pin_atidx_name_ok"] == 0,
    }
    m["print_sha"] = print_digest(recs, shape)

    # G9 the file is READ: a mutated alpha.json WRITTEN TO DISK and RELOADED through
    # sim.rules.load moves exactly one cell (the in-memory version of this test would prove
    # nothing about the file read, so it is a real file on the scratch volume).
    data = json.loads(open(RULES, encoding="utf-8").read())
    m["mut_row"] = 5
    data["FACILITIES"][m["mut_row"]]["fields"][2] = str(
        int(data["FACILITIES"][m["mut_row"]]["fields"][2]) + 1)
    fd, tmp = tempfile.mkstemp(prefix="b29_alpha_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        mut_rows = alpha_rows(sorules.load(tmp))
        m["mut_sha"] = hashlib.sha256(open(tmp, "rb").read()).hexdigest()[:16]
    finally:
        os.unlink(tmp)
    m["mut_sha_differs"] = (m["mut_sha"] != m["alpha_sha"][:16])
    mrecs, _mshape = build(mut_rows)
    mderived = derived_table(mrecs)
    m["mut_diff_ids"] = [i for i in m["ids"] if mderived[i] != derived[i]]
    m["mut_cell"] = (m["mut_row"] + 1, derived[6], mderived[6])
    return m


def _feeder_bounds():
    """M333's three loop bounds, parsed exactly as B28 parses them (never retyped)."""
    cl = _line(EVID_M333, "G1 counter:")
    init = int(_re1(r"init=\['[0-9a-f]+: mov esi,0x([0-9a-f]+)'\]", cl, "loop init"), 16)
    chg = int(_re1(r"charge-bound=\['[0-9a-f]+: cmp esi,0x([0-9a-f]+)'\]", cl,
                   "charge-bound"), 16)
    rng = int(_re1(r"range-bound=\['[0-9a-f]+: cmp esi,0x([0-9a-f]+)'\]", cl,
                   "range-bound"), 16)
    return init, chg


# --- the gates -------------------------------------------------------------------------------
def acceptance(m, results):
    add = results.append
    sh = m["shape"]
    add(("G1 %d/%d leg pins carry address+token on ONE committed evidence line (misses %s), and "
         "the CONTROL-bogus pin hits %d lines"
         % (m["pins_hit"], len(m["pins_real"]), m["pins_zero"] or "none", m["control"][4]),
         m["pins_hit"] == len(m["pins_real"]) and m["pins_zero"] == []
         and m["control"][4] == 0))

    add(("G2 the loader window parsed out of the census (records %d..%d, branch %d, end %d, "
         "iterations %d, bound %d) is REPRODUCED by the builder over alpha (records %d..%d, "
         "branch %d, end %d, iterations %d) and the token census %d/%d/%d == %d/%d/%d; the "
         "39-record rival would end at %d"
         % (m["c_rec_lo"], m["c_rec_hi"], m["c_branch"], m["c_end"], m["c_iter"], m["c_bound"],
            m["b_rec_lo"], m["b_rec_hi"], m["b_branch"], m["b_end"], m["b_iter"],
            m["b_w6"], m["b_w7"], m["b_w11"], m["c_w6"], m["c_w7"], m["c_w11"],
            m["rival39_end"]),
         (m["b_rec_lo"], m["b_rec_hi"], m["b_branch"], m["b_end"], m["b_iter"]) ==
         (m["c_rec_lo"], m["c_rec_hi"], m["c_branch"], m["c_end"], m["c_iter"])
         and (m["b_w6"], m["b_w7"], m["b_w11"]) == (m["c_w6"], m["c_w7"], m["c_w11"])
         and m["b_rows"] == m["c_rows"]
         and m["rival39_end"] != m["c_end"]))

    add(("G3 the DERIVED table equals the sim's table on %d/%d chargeable ids by upkeep and "
         "%d/%d by name, so ALPHA_SHIFT=1 is a consequence of the loader and no longer an "
         "assumption; the shift-0 rival differs at %d ids %s"
         % (m["upk_eq"], len(m["ids"]), m["name_eq"], len(m["ids"]), m["shift0_diff"],
            m["shift0_diff_ids"][:6]),
         m["upk_eq"] == len(m["ids"]) and m["name_eq"] == len(m["ids"])
         and m["shift0_name_diff"] == len(m["ids"]) and m["shift0_diff"] > 0))

    add(("G4 the %d live-pinned (id, name, upkeep) rows are reproduced by the DERIVED table "
         "(%d/%d), the facility set %s gives raw %d == recorded %d and disabled %d == recorded "
         "%d == 0x744f28 %d (the parsed disabled list is %s and the no-list sum %d differs by "
         "exactly 1); by NAME the at-alpha-index rival matches %d/5 "
         "and the reversed order %d/5 - and the rival's VALUE-only score is %d/5, so the value "
         "alone would not discriminate and the name is the measured discriminator"
         % (len(m["pinned"]), m["pin_match"], len(m["pinned"]), m["fac_set"], m["der_raw"],
            m["rec_raw"], m["der_dis"], m["rec_dis"], m["rec_hud"], m["disabled"],
            m["der_dis_nolist"], m["pin_atidx_name_ok"], m["pin_rev_name_ok"],
            m["pin_atidx_val_ok"]),
         m["pin_match"] == len(m["pinned"]) and len(m["pinned"]) == 5
         and m["der_raw"] == m["rec_raw"] and m["der_dis"] == m["rec_dis"] == m["rec_hud"]
         and m["disabled"] == [8] and m["der_dis_nolist"] - m["der_dis"] == 1
         and m["pin_atidx_name_ok"] == 0 and m["pin_rev_name_ok"] == 0
         and m["pin_atidx_val_ok"] >= 1))

    add(("G5 B4's four DIFFERS rows are the alpha-index convention, not a different order: read at "
         "the alpha INDEX the derived table reproduces %d/4 M46 values %s, read at index+1 (B4's "
         "own column) %d/4 %s, while the same at-index convention puts the WRONG facility name at "
         "%d/5 pinned ids - so one convention cannot explain both sets"
         % (m["later_atidx_ok"], [(n, a, b) for (n, a, b, _v) in m["later_atidx"]],
            m["later_plus1_ok"], [(n, a, b) for (n, a, b, _v) in m["later_plus1"]],
            m["pin_atidx_name_ok"]),
         len(m["later"]) == 4 and m["later_atidx_ok"] == 4 and m["later_plus1_ok"] == 0
         and m["later_b4_ok"] == 4 and m["pin_atidx_name_ok"] == 0))

    add(("G6 the boundary is a number: the loader writes %d records past the branch (recs %d..%d) "
         "and the feeder's bounds %d..%d reach %d of them; %d in-branch ids %s stay uncharged by "
         "M333's charge bound, and the consumer bound %d == the branch %d"
         % (m["past_branch_n"], m["past_branch"][0]["rec"], m["past_branch"][-1]["rec"],
            m["f_lo"], m["f_hi"], len(m["chargeable_past"]), len(m["uncharged_in_branch"]),
            m["uncharged_in_branch"], CONSUMER_BOUND, sh["branch"]),
         m["past_branch_n"] == sh["records"] - sh["branch"] and m["chargeable_past"] == []
         and m["uncharged_in_branch"] == list(range(m["f_hi"] + 1, sh["branch"]))
         and m["bound_eq_branch"]))

    add(("G7 B28's run fed by the DERIVED table reproduces its pinned anchors: rows %s == %s, "
         "print %s == %s, container %s == %s (table is the derived object: %s); the honest pass "
         "still touches %s, so nothing was loosened"
         % (m["b28_rows"], m["a28_rows"], m["b28_print"], m["a28_print"], m["b28_sha"],
            m["a28_sha"], m["b28_table_is_derived"], m["b28_touch"] or []),
         m["b28_table_is_derived"] and m["b28_rows"] == m["a28_rows"]
         and m["b28_print"] == m["a28_print"] and m["b28_sha"] == m["a28_sha"]
         and (m["b28_touch"] or []) == []))

    add(("G8 rivals fail on the printed numbers %s; two passes give rows %s == %s, table %s == %s, "
         "alpha sha %s"
         % ({k: v for (k, v) in m["rivals"].items()}, m["digest"], m["digest2"], m["table_sha"],
            m["table_sha2"], m["alpha_sha"][:16]),
         all(m["rivals"].values()) and m["digest"] == m["digest2"]
         and m["table_sha"] == m["table_sha2"]
         and bool(ANCHOR) and m["digest"] == ANCHOR
         and bool(PRINT_ANCHOR) and m["print_sha"] == PRINT_ANCHOR
         and bool(ALPHA_SHA) and m["alpha_sha"] == ALPHA_SHA))

    add(("G9 the builder READS alpha: %d rows with widths %d/%d/%d equal the census, and a "
         "mutated alpha.json WRITTEN TO DISK (sha %s != file sha %s) and RELOADED through "
         "sim.rules.load moves exactly %d derived cell %s and reddens G3 at %d id(s)"
         % (m["b_rows"], m["b_w6"], m["b_w7"], m["b_w11"], m["mut_sha"], m["alpha_sha"][:16],
            len(m["mut_diff_ids"]), m["mut_cell"], len(m["mut_diff_ids"])),
         (m["b_w6"], m["b_w7"], m["b_w11"]) == (m["c_w6"], m["c_w7"], m["c_w11"])
         and m["mut_sha_differs"] and m["mut_diff_ids"] == [6] and m["mut_cell"] == (6, m["derived"][6],
                                                            m["derived"][6] + 1)))


def main(argv):
    sav = argv[0] if argv else SAV
    if not os.path.exists(sav):
        print("B29: missing input %s" % sav)
        return 2
    m = measure(sav)
    table = render(m["recs"], m["shape"])
    for line in table:
        print(line)
    # the printed-table digest EXCLUDES the G8 line, which prints the pins themselves: a digest
    # that hashed its own pin could never be re-pinned (B27's G10 lesson).
    results = []
    acceptance(m, results)
    bad = [n for (n, ok) in results if not ok]
    for name, ok in results:
        print(("  ok   " if ok else "  BAD  ") + name)
    if bad:
        print("FAIL B29: %d/%d gates failed" % (len(bad), len(results)))
        print("digest(rows)=%s print_digest=%s table_sha=%s alpha_sha=%s"
              % (m["digest"], m["print_sha"], m["table_sha"], m["alpha_sha"][:16]))
        return 1
    print("PASS B29: %d/%d gates" % (len(results), len(results)))
    print("digest(rows)=%s print_digest=%s table_sha=%s alpha_sha=%s"
          % (m["digest"], m["print_sha"], m["table_sha"], m["alpha_sha"][:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
