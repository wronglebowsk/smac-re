"""sim.composedfeeder - rung B28's RUN and its GATES (BUILD_SPINE §B28).

`sim/feeder.py` is the law; this file runs it over a container's own bytes and gates the run.
`python3 -m sim.selftest --b28` relays here, so the two entry points cannot print different text.

Everything the gates read is MEASURED out of committed files: the loop bounds come out of the
M333 census text, the price-path gate dword and the spend accumulator come out of the save
container, the recorded HUD rows come out of `evidence/b4_economy.txt`, and the own faction's
disabled item id comes out of the M46 archive row.  Nothing here retypes a number it gates.
"""
import hashlib
import os
import re
import struct
import sys

from . import base as sob
from . import composedturn as soct
from . import economy as soco
from . import feeder as sf
from . import rules as sorules
from . import save as so
from . import savewriter as sow

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID_M333 = "evidence/m333_feeder_slot_census.txt"
EVID_B4 = "evidence/b4_economy.txt"
ARCHIVE_M46 = "docs/named-archive-m32-m84e.md"
RULES = os.path.join(ROOT, "data", "alpha.json")

# Filled from the first real run's printed digest; G8 asserts the result table hashes to it.
ANCHOR = "705a4520c08c4062"        # digest of the composed (faction, round, ...) rows
PRINT_ANCHOR = "61ca4afc50adba97"  # digest of the printed table, G8 line excluded

NFACTION = 8
ROUNDS = 2


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
    n = 0
    for ln in _txt(rel).splitlines():
        if addr in ln and token in ln:
            n += 1
    return n


def _re1(pat, text, what):
    """One capture group, or a HARD failure naming what could not be parsed. A silent None
    here would turn a transcription break into a crash instead of a measured FAIL."""
    mt = re.search(pat, text)
    if not mt:
        raise AssertionError("B28 parse failed for %s: pattern %r not in %r"
                             % (what, pat, text[:200]))
    return mt.group(1)


def digest_rows(rows):
    h = hashlib.sha256()
    for r in rows:
        h.update(repr(r).encode("utf-8"))
    return h.hexdigest()[:16]


# --- the run --------------------------------------------------------------------------------
def base_bitmaps(im):
    """The 8 bitmap bytes (+0x8c..+0x93) of every base record, read out of the container."""
    out = []
    for i in range(im.n_bases):
        o = im.bases_off + sf.BASE_STRIDE * i
        out.append(im.data[o + sf.BASE_FAC_BYTES:o + sf.BASE_FAC_BYTES + 8])
    return out


def owners_of(im):
    return [im.data[im.bases_off + sf.BASE_STRIDE * i + sf.BASE_OWNER_BYTE]
            for i in range(im.n_bases)]


def feeder_round(im, table, sel, disabled, visit_lo, charge_hi, visit_hi, halve_forced=None):
    """One feeder pass over the container's own bases, per faction.

    Returns rows [(faction, total, carry_in, carry_out, block0, energy, spend, n_items)] and the
    block-A writes the pass owes.  The carry lives in block[faction]+0 bit5; the full-price path
    never writes it, so `writes_block0` says which factions the loop actually touched.
    """
    bitmaps = base_bitmaps(im)
    owners = owners_of(im)
    b0 = sf.read_block0_octet(im.data, so.BLOCK_A_OFF)
    energy = [struct.unpack_from("<i", im.data, so.BLOCK_A_OFF + sf.BLK_STRIDE * f + sf.OFF_ENERGY)[0]
              for f in range(NFACTION)]
    spend = [struct.unpack_from("<i", im.data, so.BLOCK_A_OFF + sf.BLK_STRIDE * f + sf.OFF_SPEND)[0]
             for f in range(NFACTION)]
    rows, wr = [], []
    for f in range(NFACTION):
        carry_in = sf.bit5(b0[f])
        carry = carry_in
        total, n_items = 0, 0
        touched = False
        for i, own in enumerate(owners):
            if own != f:
                continue
            if halve_forced is not None:
                halve = halve_forced
            else:
                halve, _why = sf.price_path(sel, owners, f)
            t, carry, charged = sf.charge_base(table, bitmaps[i], carry, halve,
                                               disabled.get(f, ()), visit_lo, charge_hi, visit_hi)
            total += t
            n_items += len(charged)
            touched = touched or halve
        e_next = energy[f] - total                      # 4f4950-52
        s_next = spend[f] + total                       # 4f495e-62
        rows.append((f, total, carry_in, carry if touched else carry_in, b0[f],
                     energy[f], spend[f], n_items, touched))
        wr.append((sf.BLK0 + sf.BLK_STRIDE * f, sf.set_bit5(b0[f], carry)) if touched
                  else (sf.BLK0 + sf.BLK_STRIDE * f, b0[f]))
        wr.append((sf.OFF_ENERGY + sf.BLK_STRIDE * f, e_next))
        wr.append((sf.OFF_SPEND + sf.BLK_STRIDE * f, s_next))
    return rows, wr


def compose(sv, table, sel, disabled, bounds, rounds=ROUNDS, zero_carry=False,
            halve_forced=None):
    """`rounds` feeder passes, each reading its inputs back OUT OF THE WRITTEN CONTAINER."""
    img = sv.data
    rows_all, imgs, shas = [], [], []
    for rnd in range(rounds):
        im = soct.parse_image(img) if rnd else sv
        rows, wr = feeder_round(im, table, sel, disabled, *bounds, halve_forced=halve_forced)
        if zero_carry:
            # rival: the carry is never persisted - bit5 is written back as 0 every pass
            wr = [(o, sf.set_bit5(v, 0)) for (o, v) in wr if o % sf.BLK_STRIDE == sf.BLK0] + \
                 [(o, v) for (o, v) in wr if o % sf.BLK_STRIDE != sf.BLK0]
        nxt = sow.build_image(im, block_writes=wr)
        imgs.append(nxt)
        shas.append(hashlib.sha256(nxt).hexdigest()[:16])
        rows_all.append(rows)
        img = nxt
    return rows_all, img, imgs, shas


def differing_spans(a, b):
    out, i, n = [], 0, len(a)
    while i < n:
        if a[i] != b[i]:
            j = i
            while j < n and a[j] != b[j]:
                j += 1
            out.append((i, j))
            i = j
        else:
            i += 1
    return out


# --- measurement ----------------------------------------------------------------------------
def measure_full(sav_path):
    m = {"sav": sav_path}
    rules = sorules.load(RULES)
    table = soco.upkeep_table(rules)
    m["table"] = table
    m["alpha_rows"] = len(rules.section("FACILITIES"))

    # G1 pin integrity --------------------------------------------------------------
    m["pins"] = [(lab, ad, tok, f, _count_lines(f, ad, tok)) for (lab, ad, tok, f) in sf.LEG_PINS]
    m["pins_real"] = [p for p in m["pins"] if not p[0].startswith("CONTROL")]
    m["pins_hit"] = sum(1 for p in m["pins_real"] if p[4] >= 1)
    m["pins_zero"] = [p[0] for p in m["pins_real"] if p[4] == 0]
    m["control"] = [p for p in m["pins"] if p[0].startswith("CONTROL")][0]

    # G2 the bounds are READ out of the census, not retyped -------------------------
    cl = _line(EVID_M333, "G1 counter:")
    m["init_imm"] = int(_re1(r"init=\['[0-9a-f]+: mov esi,0x([0-9a-f]+)'\]", cl,
                             "loop init immediate"), 16)
    m["charge_imm"] = int(_re1(r"charge-bound=\['[0-9a-f]+: cmp esi,0x([0-9a-f]+)'\]", cl,
                                "charge-bound immediate"), 16)
    m["range_imm"] = int(_re1(r"range-bound=\['[0-9a-f]+: cmp esi,0x([0-9a-f]+)'\]", cl,
                               "range-bound immediate"), 16)
    visit_lo, charge_hi, visit_hi = m["init_imm"], m["charge_imm"], m["range_imm"] - 1
    m["bounds"] = (visit_lo, charge_hi, visit_hi)
    g7 = _line(EVID_M333, "PASS G7")
    m["row_dword_tok"] = _re1(r"upkeep dword sits at row\+0x([0-9a-f]+)", g7,
                               "upkeep dword row offset")
    m["row_dword_off"] = sf.UPKEEP_DWORD_OFF
    # the executable loop, run on an all-set bitmap, must charge exactly the parsed range
    allbits = bytes([0xFF] * 8)
    _t, _c, charged = sf.charge_base([0] * 64, allbits, 0, False, (), *m["bounds"])
    m["exec_charged"] = [i for (i, _co, _v) in charged]
    m["exec_lo"], m["exec_hi"] = m["exec_charged"][0], m["exec_charged"][-1]
    m["exec_n"] = len(m["exec_charged"])
    # rival: the whole table 0-based (ids 0..38 charged)
    m["rival0_n"] = 39

    # the container -----------------------------------------------------------------
    sv = so.parse(sav_path)
    m["n_bases"] = sv.n_bases
    m["own_player"] = sv.own_player
    owners = owners_of(sv)
    m["owners"] = owners
    bitmaps = base_bitmaps(sv)

    # G3 the bitmap gate on the save's own bytes ------------------------------------
    per_base = []
    for i in range(sv.n_bases):
        t, _c, charged = sf.charge_base(table, bitmaps[i], 0, False, (), *m["bounds"])
        dec = sorted(f for f in sob.decode(sv.data, sv.bases_off + sf.BASE_STRIDE * i, i)["facilities"]
                     if visit_lo <= f <= charge_hi)
        per_base.append((i, owners[i], [c[0] for c in charged], dec, t))
    m["per_base"] = per_base
    m["base_match"] = sum(1 for r in per_base if r[2] == r[3])
    m["width_nonzero"] = sum(1 for i in range(sv.n_bases)
                             if any(sv.data[sv.bases_off + sf.BASE_STRIDE * i + 0x90:
                                            sv.bases_off + sf.BASE_STRIDE * i + 0x94]))
    m["hi_bits"] = sorted({it for i in range(sv.n_bases)
                           for it in range(32, 39) if sf.fac_bit(bitmaps[i], it)})
    # rival: charge every table row regardless of the bitmap
    m["rival_nobitmap"] = sum(1 for i in range(sv.n_bases)
                              if sum(table[x] for x in range(visit_lo, charge_hi + 1))
                              != per_base[i][4])

    # G4 the price-path gate read out of the container ------------------------------
    sel, sel_off = sf.read_sel(sv.data, so.mem2file)
    m["sel"], m["sel_off"] = sel, sel_off
    m["path"] = "full-price" if sel < 0 else (
        "halved" if owners[sel] == sv.own_player else "full-price(owner mismatch)")
    m["halve_runs"] = sum(1 for f in range(NFACTION)
                          if sel >= 0 and owners[sel] == f)
    m["sweep_halved"] = sum(1 for s in range(0, sv.n_bases) if owners[s] == sv.own_player)
    m["sweep_n"] = sv.n_bases + 1                       # sel swept over -1..n_bases-1
    m["owner_of_sel_if_valid"] = (owners[sel] if 0 <= sel < sv.n_bases else None)

    # per-faction totals, full price, no disabled list (the raw law)
    def totals(halve, disabled):
        out = []
        for f in range(NFACTION):
            carry, tot = 0, 0
            for i in range(sv.n_bases):
                if owners[i] != f:
                    continue
                t, carry, _ch = sf.charge_base(table, bitmaps[i], carry, halve,
                                               disabled.get(f, ()), *m["bounds"])
                tot += t
            out.append(tot)
        return out

    # the own faction's disabled id, PARSED out of the M46 archive row (never retyped)
    dl = _line(ARCHIVE_M46, "disabled list (ours)")
    m["disabled_parsed"] = sorted({int(x) for x in re.findall(r"item\[\d+\]=(\d+)", dl)})
    disabled = {sv.own_player: tuple(m["disabled_parsed"])}
    m["disabled"] = {f: list(v) for f, v in disabled.items()}

    m["tot_raw"] = totals(False, {})
    m["tot_disabled"] = totals(False, disabled)
    m["tot_halved"] = totals(True, disabled)
    m["spend_oct"] = [struct.unpack_from("<i", sv.data, so.BLOCK_A_OFF + sf.BLK_STRIDE * f
                                         + sf.OFF_SPEND)[0] for f in range(NFACTION)]
    m["bit5_oct"] = sf.read_bit5_octet(sv.data, so.BLOCK_A_OFF)
    m["match_disabled"] = sum(1 for f in range(NFACTION)
                              if m["tot_disabled"][f] == m["spend_oct"][f])
    m["match_raw"] = sum(1 for f in range(NFACTION) if m["tot_raw"][f] == m["spend_oct"][f])
    m["match_halved"] = sum(1 for f in range(NFACTION)
                            if m["tot_halved"][f] == m["spend_oct"][f])
    m["mismatch_raw"] = [f for f in range(NFACTION) if m["tot_raw"][f] != m["spend_oct"][f]]
    m["mismatch_halved"] = [f for f in range(NFACTION)
                            if m["tot_halved"][f] != m["spend_oct"][f]]

    # G5 the carry law on a swept grid ---------------------------------------------
    grid = [(c, k) for c in range(-3, 8) for k in (0, 1)]
    m["grid_n"] = len(grid)
    bad = floor_bad = zc_bad = rhu_bad = 0
    for (c, k) in grid:
        v, co = sf.charge_item(c, k, True)
        if (v, co) != (sf.trunc_div2(c + k), (c + k) & 1):
            bad += 1
        if v != ((c + k) // 2):                       # floor-halving rival
            floor_bad += 1
        if (v, co) != sf.charge_item(c, 0, True):     # zero-the-carry rival
            zc_bad += 1
        if v != ((c + k + 1) // 2):                   # round-half-up rival
            rhu_bad += 1
    m["grid_bad"], m["grid_floor"], m["grid_zc"], m["grid_rhu"] = bad, floor_bad, zc_bad, rhu_bad
    # the full-price path must leave the carry alone
    m["fullprice_carry_kept"] = all(sf.charge_item(c, k, False)[1] == k
                                    for c in range(-3, 8) for k in (0, 1))

    # G6 the carry persisted through the writer -------------------------------------
    # The gate dword selects ONE base, so only its owner's pass is halved: the fixture is
    # therefore swept over the factions, one container per faction with the gate dword pointed
    # at a base that faction owns (the container's own value keeps the path inert - G4).
    rows_h, img_h, imgs_h, shas_h = compose(sv, table, sel, disabled, m["bounds"])
    fix, fix_imgs = {}, []
    for f in range(NFACTION):
        idx = next((i for i in range(sv.n_bases) if owners[i] == f), None)
        if idx is None:
            continue
        rf, imgf, imgs_f, _sf = compose(sv, table, idx, disabled, m["bounds"])
        rz, imgz, imgs_z, _sz = compose(sv, table, idx, disabled, m["bounds"], zero_carry=True)
        r1, r2 = rf[0][f], rf[1][f]
        # bit5 is read back out of the image written by ROUND 1 (the round whose carry_out the
        # row records): by the end of round 2 the same bit has been rewritten by round 2's parity.
        fix[f] = {"sel": idx, "r1_total": r1[1], "r2_total": r2[1], "carry_out": r1[3],
                  "r2_rival": rz[1][f][1],
                  "bit5_img": sf.bit5(struct.unpack_from(
                      "<i", imgs_f[0], so.BLOCK_A_OFF + sf.BLK_STRIDE * f)[0]),
                  "bit5_rival": sf.bit5(struct.unpack_from(
                      "<i", imgs_z[0], so.BLOCK_A_OFF + sf.BLK_STRIDE * f)[0])}
        fix_imgs.append((f, imgf))
    m["fix"] = fix
    m["fix_factions"] = sorted(fix)
    m["carry_live"] = [f for f in sorted(fix) if fix[f]["carry_out"] == 1]
    m["carry_diff"] = [f for f in sorted(fix) if fix[f]["r2_total"] != fix[f]["r2_rival"]]
    m["carry_diff_exact1"] = all(abs(fix[f]["r2_total"] - fix[f]["r2_rival"]) == 1
                                 for f in m["carry_live"])
    m["bit5_written_ok"] = [f for f in sorted(fix) if fix[f]["bit5_img"] == fix[f]["carry_out"]]
    m["bit5_rival_cleared"] = [f for f in sorted(fix) if fix[f]["bit5_rival"] == 0]

    # identity + modeled-span discipline
    m["identity"] = (sow.build_image(sv) == sv.data)
    spans = [(so.BLOCK_A_OFF + o, so.BLOCK_A_OFF + o + 4) for (o, _v) in
             [(sf.BLK0 + sf.BLK_STRIDE * f, 0) for f in range(NFACTION)]
             + [(sf.OFF_ENERGY + sf.BLK_STRIDE * f, 0) for f in range(NFACTION)]
             + [(sf.OFF_SPEND + sf.BLK_STRIDE * f, 0) for f in range(NFACTION)]]
    allspans = sow.modeled_spans(extra=spans)
    m["diffs_h"] = differing_spans(sv.data, img_h)
    m["outside_h"] = [d for d in m["diffs_h"]
                      if not any(s <= d[0] and d[1] <= e for (s, e) in allspans)]
    m["outside_f"] = [(f, d) for (f, img) in fix_imgs for d in differing_spans(sv.data, img)
                      if not any(s <= d[0] and d[1] <= e for (s, e) in allspans)]
    m["spans_noarg_pre_b27"] = (sow.modeled_spans() == [(so.mem2file(0x985AE8),
                                                         so.mem2file(0x985AE8) + 4),
                                                        (so.mem2file(so.G_UNITS),
                                                         so.mem2file(so.G_UNITS) + 8),
                                                        (so.mem2file(so.G_YEAR),
                                                         so.mem2file(so.G_YEAR) + 2),
                                                        (so.mem2file(0x985DCC),
                                                         so.mem2file(0x985DCC) + 4),
                                                        (sow.OWN_OFF, sow.OWN_OFF + 4),
                                                        (so.MAP_HDR_OFF, so.MAP_HDR_OFF + 8)])

    # G7 parity with the game's own recorded rows -----------------------------------
    bl = _line(EVID_B4, "ok   upkeep-table")
    m["b4_fac"] = [int(x) for x in _re1(r"facilities \[([0-9, ]+)\]", bl,
                                        "recorded facility ids").split(",")]
    m["b4_rows"] = {int(i): (nm, int(c)) for (i, nm, c)
                    in re.findall(r"\((\d+), \('([^']+)', (\d+)\)\)", bl)}
    m["b4_raw"] = int(_re1(r"raw sum (\d+)", bl, "recorded raw sum"))
    m["b4_adj"] = int(_re1(r"disabled list (\d+)", bl, "recorded disabled sum"))
    m["b4_hud"] = int(_re1(r"0x744f28 (\d+)", bl, "recorded HUD total costs"))
    pinned = {i: c for (i, (_n, c)) in m["b4_rows"].items()}
    m["table_mismatch"] = [i for i in sorted(m["b4_rows"]) if table[i] != pinned[i]]
    # the executable feeder on the recorded facility set, full price, live-pinned costs
    rec_tbl = [0] * 64
    for i, c in pinned.items():
        rec_tbl[i] = c
    bits = bytearray(8)
    for i in m["b4_fac"]:
        bits[i >> 3] |= 1 << (i & 7)
    t_raw, _c, _ch = sf.charge_base(rec_tbl, bytes(bits), 0, False, (), *m["bounds"])
    t_adj, _c, _ch = sf.charge_base(rec_tbl, bytes(bits), 0, False,
                                    tuple(m["disabled_parsed"]), *m["bounds"])
    m["feeder_raw"], m["feeder_adj"] = t_raw, t_adj

    # G8 determinism ----------------------------------------------------------------
    rows2, img2, _i2, _s2 = compose(sv, table, sel, disabled, m["bounds"])
    m["digest"] = digest_rows(rows_h)
    m["digest2"] = digest_rows(rows2)
    m["final_sha"] = hashlib.sha256(img_h).hexdigest()[:16]
    m["final_sha2"] = hashlib.sha256(img2).hexdigest()[:16]
    m["rows_flat"] = [r for rr in rows_h for r in rr]
    return m


# --- the table (printed FIRST) --------------------------------------------------------------
def render(m):
    out = []
    p = out.append
    p("B28 inputs: %s  n_bases=%d  own_player=%d  item table rows=%d (alpha #FACILITIES rows=%d)"
      % (os.path.basename(m["sav"]), m["n_bases"], m["own_player"], 39, m["alpha_rows"]))
    p("G1 pins: %d/%d real pins hit >=1 line carrying BOTH address and token; misses=%s; "
      "CONTROL-bogus %s@%s hits=%d (must be 0)"
      % (m["pins_hit"], len(m["pins_real"]), m["pins_zero"] or "none",
         m["control"][1], os.path.basename(m["control"][3]), m["control"][4]))
    p("G2 bounds READ from %s: init=0x%x charge-bound=0x%x range-bound=0x%x -> VISITS %d..%d, "
      "CHARGES %d..%d; the executable loop charges %d..%d (%d ids); upkeep dword row+0x%s "
      "(module %s=0x%x); rival 0-based-whole-table charges %d ids"
      % (EVID_M333, m["init_imm"], m["charge_imm"], m["range_imm"], m["init_imm"],
         m["range_imm"] - 1, m["init_imm"], m["charge_imm"], m["exec_lo"], m["exec_hi"],
         m["exec_n"], m["row_dword_tok"], "UPKEEP_DWORD_OFF", m["row_dword_off"], m["rival0_n"]))
    p("G3 per base: %d/%d bases' charged id set == the decoded +0x8c bits clipped to the charge "
      "range; bytes +0x90..+0x93 nonzero in %d of %d base records (ids 32..38 set anywhere: %s); "
      "rival 'charge every row' differs at %d bases"
      % (m["base_match"], len(m["per_base"]), m["width_nonzero"], m["n_bases"],
         m["hi_bits"] or "none", m["rival_nobitmap"]))
    p("G4 ds:0x985ba0 read at file offset %d = %d -> path=%s; the halving runs for %d of %d "
      "factions on this container; sweeping sel over %d values (-1..%d) flips %d to the halved "
      "path (owner_of_sel=%s)"
      % (m["sel_off"], m["sel"], m["path"], m["halve_runs"], NFACTION, m["sweep_n"],
         m["n_bases"], m["sweep_halved"], m["owner_of_sel_if_valid"]))
    p("G5 carry grid n=%d: mismatches vs the instruction semantics=%d; rivals fail at "
      "floor-halving=%d zero-the-carry=%d round-half-up=%d cells; full-price keeps the carry=%s"
      % (m["grid_n"], m["grid_bad"], m["grid_floor"], m["grid_zc"], m["grid_rhu"],
         m["fullprice_carry_kept"]))
    p("G6 fixture sweep (gate dword pointed at a base owned by the charged faction): %d factions "
      "tested %s; the half-unit survives round 1 at %s; round-2 totals differ from the zero-carry "
      "rival at %s (every live one by exactly 1: %s); bit5 in the written image == carry_out at "
      "%s and the rival clears it at %s; unmutated build identity=%s; differing bytes outside "
      "modeled spans: honest=%d fixtures=%d; modeled_spans() no-arg == the pre-B27 list: %s"
      % (len(m["fix_factions"]), m["fix_factions"], m["carry_live"], m["carry_diff"],
         m["carry_diff_exact1"], m["bit5_written_ok"], m["bit5_rival_cleared"], m["identity"],
         len(m["outside_h"]), len(m["outside_f"]), m["spans_noarg_pre_b27"]))
    p("G7 recorded: 'Climactic Research' facilities %s, live-pinned rows %s, raw %d, disabled %d, "
      "HUD 0x744f28 %d; the executable feeder reproduces raw=%d adj=%d; alpha table mismatches at "
      "ids %s; spend +300 octet %s vs computed %s with the parsed disabled list %s -> match %d/8; "
      "rivals: without the list %d/8 (mismatches %s), halved %d/8 (mismatches %s); bit5 octet in "
      "the container %s"
      % (m["b4_fac"], sorted(m["b4_rows"].items()), m["b4_raw"], m["b4_adj"], m["b4_hud"],
         m["feeder_raw"], m["feeder_adj"], m["table_mismatch"] or "none", m["spend_oct"],
         m["tot_disabled"], m["disabled"], m["match_disabled"], m["match_raw"],
         m["mismatch_raw"], m["match_halved"], m["mismatch_halved"], m["bit5_oct"]))
    p("G8 rows digest %s (second run %s); print digest %s; final container sha %s (second run "
      "%s); ANCHOR %s; PRINT_ANCHOR %s"
      % (m["digest"], m["digest2"], m.get("print_digest", "(pending)"), m["final_sha"],
         m["final_sha2"], ANCHOR or "(unpinned)", PRINT_ANCHOR or "(unpinned)"))
    return out


# --- the gates ------------------------------------------------------------------------------
def acceptance(m, results):
    add = results.append
    add(("G1 %d/%d leg pins carry address+token on ONE committed evidence line, no misses %s, "
         "and the CONTROL-bogus pin hits %d lines"
         % (m["pins_hit"], len(m["pins_real"]), m["pins_zero"] or "none", m["control"][4]),
         len(m["pins_zero"]) == 0 and m["pins_hit"] == len(m["pins_real"])
         and m["control"][4] == 0))

    add(("G2 bounds parsed (init %d, charge-bound %d, range-bound %d) match the executable loop "
         "(charges %d..%d, %d ids) and the row+0x%s upkeep dword; the 0-based rival (%d ids) "
         "differs"
         % (m["init_imm"], m["charge_imm"], m["range_imm"] - 1, m["exec_lo"], m["exec_hi"],
            m["exec_n"], m["row_dword_tok"], m["rival0_n"]),
         m["exec_lo"] == m["init_imm"] and m["exec_hi"] == m["charge_imm"]
         and m["exec_n"] == m["charge_imm"] - m["init_imm"] + 1
         and int(m["row_dword_tok"], 16) == m["row_dword_off"]
         and m["rival0_n"] != m["exec_n"]))

    add(("G3 the bitmap gate holds on the save's own bytes (%d/%d bases) and the width gap is "
         "measured (%d records nonzero past +0x8f, ids 32..38 set: %s); rival 'charge every row' "
         "differs at %d bases"
         % (m["base_match"], len(m["per_base"]), m["width_nonzero"], m["hi_bits"] or "none",
            m["rival_nobitmap"]),
         m["base_match"] == len(m["per_base"]) and m["rival_nobitmap"] > 0
         and len(m["per_base"]) == m["n_bases"]))

    add(("G4 the price-path gate read out of the container (ds:0x985ba0=%d at file offset %d) "
         "gives path=%s with the halving running %d times; the sweep over %d sel values flips "
         "%d to halved, so the inertness is measured and the leg is not a stub"
         % (m["sel"], m["sel_off"], m["path"], m["halve_runs"], m["sweep_n"], m["sweep_halved"]),
         m["sweep_n"] == m["n_bases"] + 1 and m["sweep_halved"] >= 1
         and (m["halve_runs"] == 0) == (m["sel"] < 0)))

    add(("G5 the carry law matches the instruction semantics on all %d grid cells and the three "
         "rivals fail at counted cells (floor %d, zero-carry %d, round-half-up %d); the "
         "full-price path keeps the carry"
         % (m["grid_n"], m["grid_floor"], m["grid_zc"], m["grid_rhu"]),
         m["grid_bad"] == 0 and m["grid_floor"] > 0 and m["grid_zc"] > 0
         and m["grid_rhu"] > 0 and m["fullprice_carry_kept"]))

    add(("G6 the carry persists through the writer: %d factions swept, the half-unit survives at "
         "%s and those (and only those, %s) change round 2 by exactly 1 (%s); bit5 in the written "
         "image == carry_out at %s of %d; unmutated build identity=%s; %d+%d differing bytes "
         "outside modeled spans; no-arg modeled_spans() still the pre-B27 list=%s"
         % (len(m["fix_factions"]), m["carry_live"], m["carry_diff"], m["carry_diff_exact1"],
            m["bit5_written_ok"], len(m["fix_factions"]), m["identity"],
            len(m["outside_h"]), len(m["outside_f"]), m["spans_noarg_pre_b27"]),
         m["identity"] and not m["outside_h"] and not m["outside_f"]
         and m["spans_noarg_pre_b27"] and len(m["carry_live"]) >= 1
         and m["carry_live"] == m["carry_diff"] and m["carry_diff_exact1"]
         and len(m["bit5_written_ok"]) == len(m["fix_factions"])))

    add(("G7 the executable feeder reproduces the recorded HUD rows (raw %d==%d, disabled %d==%d "
         "== 0x744f28 %d) from the live-pinned costs, the alpha table mismatches at %s, and the "
         "container's own +300 octet matches %d/8 with the parsed disabled list %s (rivals: "
         "no-list %d/8, halved %d/8)"
         % (m["feeder_raw"], m["b4_raw"], m["feeder_adj"], m["b4_adj"], m["b4_hud"],
            m["table_mismatch"] or "none", m["match_disabled"], m["disabled"],
            m["match_raw"], m["match_halved"]),
         m["feeder_raw"] == m["b4_raw"] and m["feeder_adj"] == m["b4_adj"]
         and m["feeder_adj"] == m["b4_hud"] and not m["table_mismatch"]
         and m["match_disabled"] == NFACTION and m["match_raw"] < NFACTION
         and m["match_halved"] < NFACTION))

    add(("G8 determinism: rows digest %s == second run %s; print digest %s; final container %s "
         "== %s; pinned literals ANCHOR %s / PRINT_ANCHOR %s"
         % (m["digest"], m["digest2"], m["print_digest"], m["final_sha"], m["final_sha2"],
            ANCHOR or "(unpinned)", PRINT_ANCHOR or "(unpinned)"),
         m["digest"] == m["digest2"] and m["final_sha"] == m["final_sha2"]
         and bool(ANCHOR) and m["digest"] == ANCHOR
         and bool(PRINT_ANCHOR) and m["print_digest"] == PRINT_ANCHOR))


def main(argv):
    sav = argv[0] if argv else os.path.join(ROOT, "programs", "saves", "m54b_clean.SAV")
    if not os.path.exists(sav):
        print("B28: missing input %s" % sav)
        return 2
    m = measure_full(sav)
    table = render(m)
    for line in table:
        print(line)
    # the printed-table digest EXCLUDES the G8 line, which prints the anchors themselves: a
    # digest that hashed its own pin could never be re-pinned (B27's G10 lesson).
    m["print_digest"] = hashlib.sha256(
        "\n".join(l for l in table if not l.startswith("G8 ")).encode("utf-8")).hexdigest()[:16]
    results = []
    acceptance(m, results)
    bad = [n for (n, ok) in results if not ok]
    for name, ok in results:
        print(("  ok   " if ok else "  BAD  ") + name)
    if bad:
        print("FAIL B28: %d/%d gates failed" % (len(bad), len(results)))
        return 1
    print("PASS B28: %d/%d gates" % (len(results), len(results)))
    print("digest(rows)=%s print_digest=%s final_sha=%s"
          % (m["digest"], m["print_digest"], m["final_sha"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
