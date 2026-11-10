"""sim.selftest — the runnable acceptance for the R1 build track (BUILD_SPINE.md).

    python3 -m sim.selftest --map programs/maps/planet.MP --rules data/alpha.json   # B1
    python3 -m sim.selftest --sav <save>                                            # B2 (later rung)

B1 gates, in order. Every one is a comparison against an independent source
(scripts/decode_map.py's own numbers, the header's own land-cell word, the JSON the
parser produced) — nothing here is graded against a value this file invented.

    1  sim.map's dims/cells/size/offsets == decode_map.py's for the same file
    2  both shipped dimensions (80x80 and 128x128) were actually checked
    3  every tile's terrain index is < TERRAIN_CARDINALITY and the used set has no gaps
    4  every tile's owner nibble is 0..7 or 0xf
    5  land cells (cell+7 == 0xff) == header word 5, per map
    6  every alpha.json section loaded with a non-zero record count

Exit 0 and print PASS only if every gate passes on the real bytes.
"""

import argparse
import os
import sys

from . import map as somap
from . import rules as sorules

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import decode_map  # noqa: E402  (allowed by BUILD_SPINE grading rule 4)

EXPECTED_DIMS = {(80, 80), (128, 128)}
SIBLING = {"planet.MP": "planetx.MP", "planetx.MP": "planet.MP"}


def fail(msg):
    print("FAIL " + msg)
    return 1


def check_map(path, results):
    """Gates 1, 3, 4, 5 for one map file; returns the dims it checked."""
    m = somap.parse(path)
    ref = decode_map.parse(path)
    mine = (m.width, m.height, m.cells, m.size, m.grid_off, m.trailer_len, m.version)
    theirs = (ref["width"], ref["height"], ref["cells"], ref["size"],
              ref["grid_offset"], ref["trailer_len"], ref["version"])
    results.append(("parity %-16s sim=%s decode_map=%s" % (os.path.basename(path), mine, theirs),
                    mine == theirs))
    st = m.stats()
    used = st["terrain_used"]
    contiguous = used == list(range(len(used)))
    results.append(("terrain-range %-12s used=%d..%d (%d values) out_of_range=%d gaps=%s" % (
        os.path.basename(path), used[0], used[-1], len(used), st["terrain_out_of_range"],
        "none" if contiguous else "YES"),
        st["terrain_out_of_range"] == 0 and contiguous and used[-1] < somap.TERRAIN_CARDINALITY))
    results.append(("owner-nibble %-11s hist=%s invalid=%d" % (
        os.path.basename(path), sorted(st["owner_hist"].items()), st["owner_invalid"]),
        st["owner_invalid"] == 0))
    results.append(("land-count %-14s cells+7=0xff:%d header word5:%d" % (
        os.path.basename(path), st["land_cells"], st["header_land_cells"]),
        st["land_cells"] == st["header_land_cells"]))
    # informational, not graded: the cell+0 structure this rung measured (see the
    # B1 block in NAMED.md - the file's cat field is NOT the live rec[0]&0xe0 category)
    print("  info byte0-structure %-12s cat(byte0>>5) cells/land=%s low5-distinct=%s" % (
        os.path.basename(path), st["byte0_cat"], st["byte0_low5"]))
    return (m.width, m.height)


HOME_BASES = {"University Base": 3, "Gaia's Landing": 1, "The Hive": 2,
              "Morgan Industries": 4, "Sparta Command": 5, "New Jerusalem": 6,
              "U.N. Headquarters": 7}          # SAVE_FORMAT.md live base table
TRACED_80 = (273660, 279848, 291096, 301896)  # units/bases/tail/size, SAVE_FORMAT.md read trace


def run_save(target, results):
    """B2 gates. Parity sources: scripts/decode_save.py, the state header's own counts,
    SAVE_FORMAT.md's live base table, and the recorded 80x80 read trace. Nothing here is
    graded against a number this function invented."""
    import contextlib
    import glob
    import io
    import decode_save
    from . import map as somap
    from . import save as sosave

    if not os.path.exists(target):
        return fail("save file not found: %s" % target)
    s = sosave.parse(target)
    ref = decode_save.parse(target)
    mine = (s.size, s.version, s.year)
    theirs = (ref["size"], ref["version"], ref["year"])
    results.append(("decode-save parity   sim=%s decode_save=%s" % (mine, theirs),
                    mine == theirs))

    files = sorted(glob.glob(os.path.join(REPO, "programs/saves/**/*.SAV"), recursive=True))
    bad, mids, tails = [], set(), set()
    for p in files:
        try:
            t = sosave.parse(p)
        except sosave.SaveError as exc:
            bad.append("%s: %s" % (os.path.basename(p), exc))
            continue
        if (t.n_units, t.n_bases) != (t.found_units, t.found_bases):
            bad.append("%s: header (%d,%d) != shape scan (%d,%d)"
                       % (os.path.basename(p), t.n_units, t.n_bases, t.found_units,
                          t.found_bases))
        if t.units_off + sosave.UNIT_LEN * t.n_units != t.bases_off:
            bad.append("%s: unit array does not end at the base array" % os.path.basename(p))
        if t.tail_len != sosave.TAIL_LEN:
            bad.append("%s: tail %d != %d" % (os.path.basename(p), t.tail_len, sosave.TAIL_LEN))
        if not t.closes:
            bad.append("%s: walk predicts units@%d bases@%d tail@%d, content says %d/%d/%d "
                       "(size %d)" % (os.path.basename(p), t.units_pred, t.bases_pred,
                                      t.tail_pred, t.units_off, t.bases_off, t.tail_off, t.size))
        if not t.owner_ids or max(t.owner_ids) >= t.mask_factions:
            bad.append("%s: owners %s vs mask %d" % (os.path.basename(p), t.owner_ids,
                                                     t.mask_factions))
        mids.add(t.count_len)
        tails.add(t.tail_len)
    results.append(("header-counts      %d saves, header unit/base counts match the shape scan; "
                    "tails=%s, count-prefix=%s, bad=%s"
                    % (len(files), sorted(tails), sorted(mids), bad or "none"), not bad))
    results.append(("walk-closure     count u32@%d=%d -> units %d (content %d) -> bases %d "
                    "(content %d) -> tail %d+%d=EOF %d, closes=%s on all %d saves"
                    % (s.count_off, s.count_len, s.units_pred, s.units_off, s.bases_pred,
                       s.bases_off, s.tail_off, s.tail_len, s.size, s.closes, len(files)),
                    s.closes and not any(not t.closes for t in
                                         [sosave.parse(p) for p in files])))

    agree = (s.faction_slots == s.mask_factions == len(s.owner_ids))
    results.append(("faction-count      block-A slots=%d (67040/8380), mask byte %#x popcount=%d, "
                    "distinct record owners=%d %s"
                    % (s.faction_slots, s.faction_mask, s.mask_factions, len(s.owner_ids),
                       s.owner_ids), agree))

    got = {b["name"]: b for b in s.bases}
    wrong = [n for n, f in sorted(HOME_BASES.items()) if got.get(n, {}).get("fac") != f]
    split = [b["i"] for b in s.bases if b["fac"] != b["own4"]]
    results.append(("home-base-faction  %d names from the SAVE_FORMAT.md live table checked at "
                    "rec+5; mismatches=%s; rec+4 != rec+5 on %s"
                    % (len(HOME_BASES), wrong or "none", split), not wrong))

    w, h = s.width, s.height
    ident = oor = 0
    terr = set()
    for y in range(h):
        for x in range(w):
            o = s.grid_off + (y * w + x) * 22
            cell = s.data[o:o + 22]
            if s.tile(x, y) == cell:
                ident += 1
            v = cell[0] & 0x0F
            terr.add(v)
            oor += v >= somap.TERRAIN_CARDINALITY
    land = sum(1 for i in range(w * h) if s.data[s.grid_off + i * 22 + 7] == 0xFF)
    w5 = int.from_bytes(s.data[sosave.MAP_HDR_OFF + 20:sosave.MAP_HDR_OFF + 24], "little")
    results.append(("embedded-map       %dx%d: 44-B record view == 22-B cell view on %d/%d tiles, "
                    "terrain %s out_of_range=%d"
                    % (w, h, ident, w * h, sorted(terr), oor), ident == w * h and oor == 0))
    print("  info save-map-word5    header word 5=%d, land cells (cell+7=0xff)=%d, (W/2)*H "
          "records=%d -> the .MP 'word5 == land cells' law does NOT hold in a save"
          % (w5, land, (w // 2) * h))

    traced_mid = 4 + 328 + 3584 + 26624 + 4096
    u = sosave.MAP_HDR_OFF + 2724 + 80 * 80 * 22 + 128 + 16000 + traced_mid
    calc = (u, u + 52 * 119, u + 52 * 119 + 304 * 37,
            u + 52 * 119 + 304 * 37 + sosave.TAIL_LEN)
    results.append(("recorded-80x80     sim arithmetic on the traced 80x80 save (n=119 m=37 "
                    "count=328) -> %s vs SAVE_FORMAT.md %s" % (list(calc), list(TRACED_80)),
                    calc == TRACED_80))

    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            decode_save.walk(ref["data"])
        ref_note = "decode_save --sections ran: %s" % buf.getvalue().strip().splitlines()[-1]
    except SystemExit as exc:
        ref_note = ("decode_save --sections RAISES on this file: %s (its section table is the "
                    "80x80 one - the record region solves to 0 B on a 64x64 save)" % exc)
    print("  info reference-walk    %s" % ref_note)
    return None


def run_replay(path, results):
    """B3 gates (BUILD_SPINE.md:55): the turn engine must reproduce the recorded
    (cur, tf, year) sequence of evidence/m30_turn_trace.jsonl, matched=N/N, no tolerance.

    The trace is a 0.2 s SAMPLE of a fast state machine (scripts/turn_trace.py:59 logs one
    row per change-set of (year, cur, tf)), so parity is an ORDERED SUBSEQUENCE: every
    recorded row must be a state the engine reaches, in order; states the sampler skipped
    are the collapsed AI phases.  Model + rationale: sim/turn.py's module docstring."""
    import itertools
    import json
    from . import turn
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    if not rows:
        return fail("replay: no rows in %s" % path)
    rec = [(r["cur"], r["tf"], r["year"]) for r in rows]
    body = rec[1:]
    own = sorted({r["own"] for r in rows})
    tf0 = [i for i, s in enumerate(rec) if s[1] == 0]
    bad = ([i for i, s in enumerate(rec) if not 0 <= s[0] < turn.SLOTS]
           + [i for i, s in enumerate(rec) if s[1] not in (0, turn.TF_CYCLE)]
           + [i for i in tf0 if rec[i][0] != turn.HUMAN])
    same = [i for i in range(1, len(rec)) if rec[i] == rec[i - 1]]
    cycles = len(tf0) - 1
    results.append((
        "trace-wellformed rows=%d own=%s tf==0_rows=%d(all cur==3) out_of_range=%d "
        "unchanged_rows=%d cycles=%d year %d->%d(+%d)" % (
            len(rec), own, len(tf0), len(bad), len(same), cycles,
            rec[0][2], rec[-1][2], rec[-1][2] - rec[0][2]),
        own == [turn.HUMAN] and not bad and not same and cycles == 20
        and rec[-1][2] - rec[0][2] == cycles))

    eng = turn.Engine(rec[0][2])
    init = eng.state()
    emitted = []
    for _ in range(cycles):
        emitted.extend(eng.press())
    matched, missing, _used = turn.match(emitted, body)
    n_ok = (1 if init == rec[0] else 0) + matched
    results.append((
        "replay-parity matched=%d/%d rows (initial 1 + transitions %d/%d) unmatched=%d "
        "emitted=%d collapsed_by_sampler=%d final=%s recorded_last=%s" % (
            n_ok, len(rec), matched, len(body), len(missing), len(emitted),
            len(emitted) - matched, eng.state(), rec[-1]),
        n_ok == len(rec) and not missing and eng.state() == rec[-1]))

    # gate 3: at which edge may the new year first be visible? all 8 candidates.
    edge = {}
    for ya in range(turn.SLOTS):
        _e, s = turn.replay(rec[0][2], cycles, year_after=ya)
        edge[ya] = turn.match(s, body)[0]
    best = sorted(k for k, v in edge.items() if v == len(body))
    results.append((
        "year-edge pinned=%s runner_up=%s (witness row 22: %s)" % (
            best, sorted(edge.items(), key=lambda kv: -kv[1])[:4], rows[22]),
        best == [7]))
    # gate 4: is (cur==3, tf==2) at the end of the walk a real state, or is tf cleared in
    # the same step cur is written?  Discriminate by removing it from the model.
    n_merged = turn.match(turn.replay(rec[0][2], cycles, merge_landing=True)[1], body)[0]
    n_nopress = turn.match(turn.replay(rec[0][2], cycles, emit_press=False)[1], body)[0]
    results.append((
        "landing-state required: merged_landing=%d/%d vs baseline %d/%d; press-transition "
        "unobservable: no_press=%d/%d (OPEN)" % (
            n_merged, len(body), matched, len(body), n_nopress, len(body)),
        n_merged < len(body) and matched == len(body) and n_nopress == len(body)))

    # gate 5: how many candidate models reproduce the trace at all?  The engine is a cyclic
    # walk order over the 8 slots plus the edge at which the year fires: 7! orders of the
    # non-human slots x 8 positions for the human x 8 edges = 322,560 models.
    ai = [s for s in range(turn.SLOTS) if s != turn.HUMAN]
    tested = 0
    hits = []
    for perm in itertools.permutations(ai):
        for hp in range(turn.SLOTS):
            order = list(perm)
            order.insert(hp, turn.HUMAN)
            for ya in order:
                tested += 1
                _e, s = turn.replay(rec[0][2], cycles, order=order, year_after=ya)
                if turn.match(s, body)[0] != len(body):
                    continue
                hits.append((tuple(order), ya))
    # a model is (successor-of-each-slot, year edge); intersect over the ones that pass to
    # see which parts of it the trace actually pins down.
    forms = []
    for order, ya in hits:
        pos = {s: i for i, s in enumerate(order)}
        forms.append((tuple(order[(pos[s] + 1) % turn.SLOTS] for s in range(turn.SLOTS)), ya))
    shared = None
    for succ, ya in forms:
        shared = list(succ) + [ya] if shared is None else [
            a if a == b else -1 for a, b in zip(shared, list(succ) + [ya])]
    det = sorted((s, shared[s]) for s in range(turn.SLOTS) if shared[s] >= 0)
    cyclic = set()
    for order, _ya in hits:
        i3 = order.index(turn.HUMAN)
        cyclic.add(tuple(order[i3:] + order[:i3]))
    results.append((
        "model-space tested=%d reproduce=%d (%.4f%%) distinct_cyclic_orders=%d "
        "edges_shared_by_all=%s year_edge_shared_by_all=%s" % (
            tested, len(hits), 100.0 * len(hits) / tested, len(cyclic), det, shared[8]),
        bool(hits) and shared[8] == 7
        and det == [(0, 1), (1, 2), (2, 3), (7, 0)]))

    # gate 6: cycle accounting against the trace's own counters.
    seq_all = [init] + emitted
    bumps = sum(1 for a, b in zip(seq_all, seq_all[1:]) if a[2] != b[2])
    clears = sum(1 for s in emitted if s[1] == 0)
    results.append((
        "cycle-accounting presses=%d emissions_per_cycle=%d year_bumps=%d tf_clears=%d "
        "final=%s" % (cycles, len(emitted) // cycles, bumps, clears, eng.state()),
        len(emitted) == 11 * cycles and bumps == cycles and clears == cycles
        and eng.state() == (turn.HUMAN, 0, rec[-1][2])))
    return None


OUR_FAC = 3                     # the human faction: both harnesses hardcode owner == 3
M46_TRACE = "evidence/m46e_econ.json"   # recorded post-founding state B4's HUD parity uses
DISABLED_OURS = frozenset({8})  # Network Node, recorded live (m32-m84e.md:272)


def _ocr_zero(tok):
    """A HUD value token the OCR read as zero: 'Olturn'/'Ofturn'/'Oturn' are '0/turn'."""
    return bool(tok) and tok[0] in "O0" and tok.lower().endswith("turn") \
        and not any(c in "123456789" for c in tok)


def run_economy_replay(trace, results):
    """B4 gates 1-3 (BUILD_SPINE.md:62): reproduce the 12 idle rounds of
    evidence/m44d_idle.json -- our faction energy flat at 15, net 0 on every round -- and the
    HUD triple (gross, upkeep, net) as M46's sums: SUM base+0xfc, SUM upkeep, difference.

    The trace samples at start-of-our-turn, i.e. after the round's upkeep phase has already
    landed, so a transition is `next = apply(net of the round that just ran)`. Our faction owns
    no base in any of the 12 rounds (gate 1 asserts that from the trace's own owners map), so
    the model is alignment-insensitive here: every candidate alignment nets 0.
    """
    from . import economy as soecon
    from . import rules as sorules
    import os

    rounds = trace["rounds"]
    table = soecon.upkeep_table(sorules.load(os.path.join(REPO, "data/alpha.json")))
    years = [r["year"] for r in rounds]
    e3 = [r["energy"][str(OUR_FAC)] for r in rounds]
    nours = [r["owners"].get(str(OUR_FAC), {}).get("bases", 0) for r in rounds]
    results.append((
        "trace-wellformed rounds=%d years %d..%d consecutive=%s cur==%d on all=%s "
        "point-set=%s our_energy=%s our_bases_per_round=%s harness deltas.energy3=%s" % (
            len(rounds), years[0], years[-1], years == list(range(years[0], years[-1] + 1)),
            OUR_FAC, all(r["cur"] == OUR_FAC for r in rounds),
            sorted({r.get("point") for r in rounds}), sorted(set(e3)), sorted(set(nours)),
            trace.get("deltas_per_round", {}).get("energy3")),
        len(rounds) == 12 and years == list(range(years[0], years[-1] + 1))
        and all(r["cur"] == OUR_FAC for r in rounds)
        and {r.get("point") for r in rounds} == {"start-of-our-turn"}
        and len(set(e3)) == 1 and set(nours) == {0}
        and trace.get("deltas_per_round", {}).get("energy3") == 0.0))

    states, seq = [], [e3[0]]
    for i, r in enumerate(rounds):
        bases = [soecon.base_from_trace(b) for b in r.get("bases", []) if b["owner"] == OUR_FAC]
        st = soecon.faction_round(OUR_FAC, bases, table, DISABLED_OURS)
        states.append(st)
        if i + 1 < len(rounds):
            seq.append(soecon.apply_round(seq[-1], st["net"]))
    matched = sum(1 for a, b in zip(seq, e3) if a == b)
    for i, r in enumerate(rounds):
        st = states[i]
        print("  round %2d year %d our_bases=%d gross=%d upkeep=%d net=%d energy sim=%d "
              "recorded=%d delta=%d" % (i, r["year"], st["n_bases"], st["gross"], st["upkeep"],
                                        st["net"], seq[i], e3[i], seq[i] - e3[i]))
    results.append((
        "idle-replay matched=%d/%d states (initial 1 + transitions %d/%d) nets=%s "
        "nonzero_net=%d sim_sequence=%s" % (
            matched, len(rounds), sum(1 for a, b in zip(seq[1:], e3[1:]) if a == b),
            len(rounds) - 1, sorted({s["net"] for s in states}),
            sum(1 for s in states if s["net"]), seq),
        matched == len(rounds) and all(s["net"] == 0 for s in states)))

    triple = (states[-1]["gross"], states[-1]["upkeep"], states[-1]["net"])
    legible = zeros = 0
    for r in rounds:
        toks = r.get("hud_econ_ocr") or []
        vals = {}
        for label in ("Income:", "Costs:", "INCOME:"):
            if label in toks and toks.index(label) + 1 < len(toks):
                vals[label] = toks[toks.index(label) + 1]
        if len(vals) == 3:
            legible += 1
            zeros += all(_ocr_zero(v) for v in vals.values())
    results.append((
        "hud-triple-idle engine=(gross %d, upkeep %d, net %d) == (SUM base+0xfc, SUM upkeep, "
        "difference) on %d bases; recorded economy-pane OCR legible on %d/12 rounds, all three "
        "rows read 0/turn on %d of them (evidence/m44d_idle.json:150)" % (
            triple[0], triple[1], triple[2], states[-1]["n_bases"], legible, zeros),
        triple == (0, 0, 0) and legible >= 1 and zeros == legible))
    return states


PINNED_ITEMS = {1: ("Headquarters", 0), 3: ("Recycling Tanks", 0), 6: ("Recreation Commons", 1),
                7: ("Energy Bank", 1), 8: ("Network Node", 1)}  # live table read, m32-m84e.md:270-272
LATER_ITEMS = {"Fusion Lab": 4, "Quantum Lab": 3, "Nanoreplicator": 4, "Quantum Converter": 6}


def run_economy_hud(results):
    """B4 gates 4-9: the record decoder against a recorded 304-B live read and against every
    .SAV in the repo, then the economy model against the globals the GAME itself computed in the
    recorded post-founding state (gross evidence/m46e_econ.json:56, per-base upkeep :102,
    item counts :61).  Nothing here is graded against a number this file invented."""
    import glob
    import json
    import os

    from . import base as sobase
    from . import economy as soecon
    from . import rules as sorules
    from . import save as sosave

    rules = sorules.load(os.path.join(REPO, "data/alpha.json"))
    table = soecon.upkeep_table(rules)
    m46 = json.load(open(os.path.join(REPO, M46_TRACE), encoding="utf-8"))
    m46_rounds = m46["rounds"]

    live = [b for b in m46_rounds[0]["bases"] if "full" in b][0]
    dec = sobase.decode_dwords(live["full"])
    want = {"owner": live["owner"], "pop": live["pop"], "growth": live["growth"],
            "storage": live["minerals"], "c4": live["c4"], "d4": live["d4"], "e4": live["e4"],
            "f4": live["f4"], "gross": live["prod_fc"], "b100": live["prod_energy"],
            "b104": live["prod_104"], "b108": live["prod_108"], "name": live["name"]}
    got = {k: dec[k] for k in want}
    results.append((
        "record-decode-parity %d/%d fields of the recorded %d-dword base record %r reproduce "
        "the harness's own reads (mismatch=%s)" % (
            sum(1 for k in want if got[k] == want[k]), len(want), len(live["full"]),
            want["name"], {k: (want[k], got[k]) for k in want if got[k] != want[k]} or "none"),
        got == want))

    saves = sorted(glob.glob(os.path.join(REPO, "programs/saves/**/*.SAV"), recursive=True))
    bad, nrec, owners, withfac, withgross = [], 0, set(), 0, 0
    maxfac, neg, nonterm, maxlen = -1, 0, 0, 0
    for p in saves:
        s = sosave.parse(p)
        for b in sobase.from_save(s):
            seam = s.base(b["i"])
            nrec += 1
            if (b["i"], b["off"], b["owner"], b["name"]) != (seam["i"], seam["off"],
                                                             seam["own4"], seam["name"]):
                bad.append("%s#%d" % (os.path.basename(p), b["i"]))
            win = s.data[b["off"] + sobase.NAME_OFF:b["off"] + sobase.NAME_OFF + sobase.NAME_LEN]
            nonterm += b"\0" not in win
            maxfac = max([maxfac] + b["facilities"])
            maxlen = max(maxlen, len(b["name"]))
            neg += b["storage"] < 0
            owners.add(b["owner"])
            withfac += bool(b["facilities"])
            withgross += b["gross"] > 0
    results.append((
        "save-records %d saves %d base records decoded; sim.base vs sim.save seam mismatches=%s; "
        "owners=%s max_facility_id=%d(<%d) storage_negative=%d name_window_without_NUL=%d "
        "longest_name=%d bases_with_facilities=%d bases_with_gross=%d" % (
            len(saves), nrec, bad or "none", sorted(owners), maxfac, sobase.FAC_MAX, neg,
            nonterm, maxlen, withfac, withgross),
        not bad and maxfac < sobase.FAC_MAX and set(owners) <= set(range(8))
        and not neg and not nonterm and maxlen > 20))

    bases = [soecon.base_from_trace(b) for b in m46_rounds[0]["bases"]]
    per = [(r, soecon.faction_round(OUR_FAC, [soecon.base_from_trace(b) for b in r["bases"]],
                                    table, DISABLED_OURS)) for r in m46_rounds]
    got3 = [(s["gross"], s["upkeep"], s["net"]) for _r, s in per]
    rec3 = [(r["scratch"]["gross_745734"],
             r["scratch"]["upkeep_744f28"], r["scratch"]["net_7457dc"]) for r in m46_rounds]
    e = [r["fac"][str(OUR_FAC)][0] for r in m46_rounds]
    pred = [e[0]]
    for _r, s in per[:-1]:
        pred.append(soecon.apply_round(pred[-1], s["net"]))
    final = soecon.apply_round(pred[-1], per[-1][1]["net"])
    results.append((
        "hud-triple-postfound engine=%s recorded_game_globals=%s on %d rounds; energy %s -> "
        "predicted %s final %s recorded_final %s" % (
            got3, rec3, len(per), e, pred, final, m46["final"]["energy"][str(OUR_FAC)]),
        got3 == rec3 and all(t == (2, 2, 0) for t in rec3) and pred == e
        and final == m46["final"]["energy"][str(OUR_FAC)]))

    r0, s0 = per[0]
    pb_ok = s0["per_base_upkeep"] == r0["scratch"]["per_base_upkeep_744f2c"]
    ic_ok = s0["item_counts"] == r0["scratch"]["item_counts_745738"]
    r1, s1 = per[1]
    results.append((
        "aggregator-arrays per_base_upkeep %d entries == recorded 0x744f2c %s (engine nonzero %s); "
        "item_counts %d entries == recorded 0x745738 (nonzero %s); round2 same=%s" % (
            len(s0["per_base_upkeep"]), [(i, v) for i, v in enumerate(
                r0["scratch"]["per_base_upkeep_744f2c"]) if v],
            [(i, v) for i, v in enumerate(s0["per_base_upkeep"]) if v], len(s0["item_counts"]),
            [(i, v) for i, v in enumerate(s0["item_counts"]) if v],
            s1["per_base_upkeep"] == r1["scratch"]["per_base_upkeep_744f2c"]
            and s1["item_counts"] == r1["scratch"]["item_counts_745738"]),
        pb_ok and ic_ok and s1["per_base_upkeep"] == r1["scratch"]["per_base_upkeep_744f2c"]
        and s1["item_counts"] == r1["scratch"]["item_counts_745738"]))

    ours_fac = dec["facilities"]
    raw = sum(table[i] for i in ours_fac)
    adj = sum(soecon.item_upkeep(table, i, DISABLED_OURS) for i in ours_fac)
    names = {i: soecon.item_name(rules, i) for i in PINNED_ITEMS}
    wrong = [i for i in PINNED_ITEMS if (names[i], table[i]) != PINNED_ITEMS[i]]
    results.append((
        "upkeep-table base %r facilities %s; alpha #FACILITIES upkeep at (runtime id - 1) == the "
        "five live-pinned (id, name, cost) rows %s mismatches=%s; raw sum %d, with the recorded "
        "disabled list %d == recorded 0x744f28 %d" % (
            want["name"], ours_fac, sorted(PINNED_ITEMS.items()), wrong or "none", raw, adj,
            r0["scratch"]["upkeep_744f28"]),
        not wrong and ours_fac == sorted(PINNED_ITEMS) and raw == 3 and adj == 2
        and adj == r0["scratch"]["upkeep_744f28"]))

    variants = {
        "A gross=SUM base+0xfc, upkeep with the recorded disabled list": got3[0],
        "B no disabled list": soecon.faction_round(OUR_FAC, bases, table, frozenset()),
        "C gross=SUM base+0x100": soecon.faction_round(
            OUR_FAC, [dict(b, gross=b.get("b100", 0)) for b in bases], table, DISABLED_OURS),
        "D runtime id == alpha line (no +1)": soecon.faction_round(
            OUR_FAC, bases, soecon.upkeep_table(rules, shift=0), DISABLED_OURS),
    }
    tri = lambda s: (s["gross"], s["upkeep"], s["net"])
    variants = {k: tri(v) if isinstance(v, dict) else v for k, v in variants.items()}
    hits = sorted(k for k, v in variants.items() if v == rec3[0])
    results.append((
        "model-discrimination recorded=(%d,%d,%d); candidates %s; matching=%d %s" % (
            rec3[0][0], rec3[0][1], rec3[0][2],
            {k: v for k, v in sorted(variants.items())}, len(hits), hits),
        hits == ["A gross=SUM base+0xfc, upkeep with the recorded disabled list"]))

    for name, recorded in sorted(LATER_ITEMS.items()):
        line = rules.find_by_first_field(soecon.FACILITIES, name)
        upk = int(rules.field(soecon.FACILITIES, line, soecon.UPKEEP_COL))
        print("  info table-later       %-20s alpha line %d upkeep %d vs M46 live read %d %s"
              % (name, line, upk, recorded,
                 "==" if upk == recorded else "DIFFERS (OPEN: runtime row order is not alpha order)"))
    return None


M27_LOGS = ("evidence/m27_solowrap.log", "evidence/m27_solowrap2.log")
# turn_driver.md §M25/§M27: all 8 survivors were stacked on (41,11); §M27 item 4 records where
# they were found afterwards. §M27 item 1 records one Right on rec117 before the trace window.
M27_PRE = {i: (41, 11) for i in range(116, 124)}
M27_POST = {117: (45, 11), 118: (45, 11), 119: (43, 11), 120: (43, 11),
            121: (41, 11), 122: (41, 11), 123: (41, 11)}


def run_m27_replay(results):
    """B5: replay the recorded M27 arrow-key moves through sim.units (BUILD_SPINE rung B5)."""
    from . import units as sounits
    paths = [os.path.join(REPO, p) for p in M27_LOGS]
    for p in paths:
        if not os.path.exists(p):
            results.append(("trace %s found" % os.path.basename(p), False))
            return
    logs = [sounits.moves(sounits.parse_trace(p)) for p in paths]
    mv = logs[0] + logs[1]

    shape = (len(logs[0]) == 1 and len(logs[1]) == 3
             and all(m["dir"] == 1 and m["exec"] == (m["idx"], 1, 3) and m["dest"]
                     and m["sentinel"][0] == (m["idx"], -2, -2) for m in mv))
    results.append(("trace-shape %d presses idx=%s all dir=1, EXEC mode=3, own (-2,-2) "
                    "stamp first" % (len(mv), [m["idx"] for m in mv]), shape))

    dest = {m["idx"]: m["dest"][-1][1:] for m in mv}
    got = [dest.get(i) for i in (117, 118, 119, 120)]
    want = [M27_POST[i] for i in (117, 118, 119, 120)]
    results.append(("destinations %s == turn_driver §M27 post-state %s" % (got, want),
                    got == want))

    # the one start the trace itself proves: rec117 is re-stamped at (43,11) inside the first
    # log's move, before its own press in the second log.
    proven = [s for s in logs[0][0]["restamp"] if s[0] == 117]
    u117 = sounits.Unit(117, proven[0][1], proven[0][2]) if proven else None
    pred = u117.step(1, 80, 80) if u117 else None
    results.append(("dir1-delta %s from the trace-proven start %s -> %s == recorded (45,11)"
                    % (sounits.delta(1), proven, pred),
                    sounits.delta(1) == (2, 0) and pred == (45, 11)
                    and dest.get(117) == (45, 11)))

    ring_ok = all(sounits.delta(d) == sounits.ring(d) for d in range(8)) and \
        all((dx + dy) % 2 == 0 for dx, dy in zip(sounits.DIR_DX, sounits.DIR_DY)) and \
        set(sounits.DIR_DX and list(zip(sounits.DIR_DX, sounits.DIR_DY))) == \
        set(sounits.RING_CENTRE_FIRST) - {(0, 0)}
    results.append(("ring-identity 8 dirs == the 0x6784a0 ring read at m248:3 shifted one "
                    "index, == the 0x67850c ring at m248:2 minus (0,0), all %d pairs preserve "
                    "(x+y) parity" % 8, ring_ok))

    r = sorules.load(os.path.join(REPO, "data/alpha.json"))
    scale = sounits.mp_scale(r)
    econ = (scale == 3 and sounits.STEP_MP == scale and sounits.MP_PER_TURN == 6
            and sounits.MOVES_PER_TURN == 2)
    results.append(("mp-economy alpha #RULES[0]=%s == STEP_MP=%d, MP_PER_TURN=%d == %d moves "
                    "== FUN_005ac550's scale*moves" % (scale, sounits.STEP_MP,
                                                       sounits.MP_PER_TURN,
                                                       sounits.MOVES_PER_TURN), econ))

    u = sounits.Unit(121, 41, 11)
    seq = [(u.can_act(), u.step(1, 80, 80), u.spent) for _ in range(3)]
    gate_ok = [seq[0][0], seq[1][0], seq[2][0]] == [True, True, False] and \
        [seq[0][1], seq[1][1], seq[2][1]] == [(43, 11), (45, 11), None] and \
        [s[2] for s in seq] == [3, 6, 6] and u.x == 45
    results.append(("can-act-gate total-spent>0 admits steps at spent 0 and 3, refuses the "
                    "third (spent stays %d, x stays %d)" % (u.spent, u.x), gate_ok))

    m = somap.parse(os.path.join(REPO, "programs/maps/planet.MP"))
    raw = open(os.path.join(REPO, "programs/maps/planet.MP"), "rb").read()
    tiles = [(43, 11), (45, 11), (sounits.wrap_x(79 + 2, 80), 11),
             (sounits.wrap_x(0 - 2, 80), 11)]
    view_ok = True
    for x, y in tiles:
        rec, half = sounits.tile_record(x, y, m.width)
        off = m.grid_off + 44 * rec + 22 * half
        view_ok = view_ok and raw[off:off + 22] == m.cell(x, y) == \
            raw[m.grid_off + m.cell_index(x, y) * 22:][:22]
    wr = (sounits.wrap_x(79 + 2, 80), sounits.wrap_x(0 - 2, 80))
    edge = sounits.Unit(122, 79, 11).step(1, 80, 80)
    south = sounits.Unit(123, 41, 79).step(3, 80, 80)
    wrap_ok = view_ok and wr == (1, 78) and edge == (1, 11) and south is None
    results.append(("wrap-and-cell-view x wraps %d+%d->%d and %d-%d->%d on the 80-wide map, "
                    "y=79+2 refused, %d tile views agree between my (w/2)*y+(x>>1)+x&1 index, "
                    "sim.map's cell_index and the packed 44-B record"
                    % (79, 2, wr[0], 0, 2, wr[1], len(tiles)), wrap_ok))

    held = {i: list(M27_PRE[i]) for i in M27_PRE}
    units = {i: sounits.Unit(i, *M27_PRE[i]) for i in M27_PRE}
    units[117].step(1, 80, 80)                      # §M27 item 1, before the trace window
    held[117] = [43, 11]
    for i in units:
        units[i].spent = 0                          # §M37: REFRESH zeroes spent each round
    restamp_bad, checked = [], 0
    for group in logs:
        for mm in group:
            u = units.get(mm["idx"])
            stepped = u.step(mm["dir"], 80, 80) if u else None
            if stepped:
                held[mm["idx"]] = list(stepped)
            for i, x, y in mm["restamp"]:
                checked += 1
                if held.get(i) != [x, y]:
                    restamp_bad.append((mm["idx"], i, (x, y), held.get(i)))
    results.append(("restamps-agree %d re-stamps of other units all match the position the "
                    "replay holds for them (mismatches %s)" % (checked, restamp_bad),
                    checked >= 5 and not restamp_bad))

    steps_from_pre = {i: (M27_POST[i][0] - M27_PRE[i][0]) // 2 for i in (117, 118, 119, 120)}
    exact = all((M27_POST[i][0] - M27_PRE[i][0]) % 2 == 0 and M27_POST[i][1] == M27_PRE[i][1]
                for i in steps_from_pre)
    afford = {i: steps_from_pre[i] * sounits.STEP_MP for i in steps_from_pre}
    results.append(("displacement-from-(41,11) %s tiles -> %d MP each, every one <= the %d-MP "
                    "round budget, no off-axis move"
                    % (steps_from_pre, max(afford.values()), sounits.MP_PER_TURN),
                    exact and all(v <= sounits.MP_PER_TURN for v in afford.values())
                    and min(steps_from_pre.values()) >= 1))
    print("  info rec118's logged press covers 2 tiles (41->45): one of its %d steps is outside "
          "the committed trace window; the model lands it at %s"
          % (steps_from_pre[118], tuple(held[118])))
    print("  info ASSUMED: %s | %s" % sounits.ASSUMED)


def run_b6(sav_path, map_path, turns, results):
    """Rung B6: two in-process headless runs -> identical bytes, plus the run's own gates."""
    import hashlib
    import tempfile
    from . import headless as sohead
    if not (os.path.exists(sav_path) and os.path.exists(map_path)):
        return fail("B6: missing input: %s / %s" % (sav_path, map_path))
    sv1, eng1, st1, blob1 = sohead.simulate(sav_path, map_path, sohead.DEFAULT_RULES, turns)
    sv2, eng2, st2, blob2 = sohead.simulate(sav_path, map_path, sohead.DEFAULT_RULES, turns)
    for name, ok, detail in sohead.validate(sv1, eng1, st1, turns):
        results.append((name + " " + detail, ok))
    sha1 = hashlib.sha256(blob1.encode()).hexdigest()
    sha2 = hashlib.sha256(blob2.encode()).hexdigest()
    results.append(("two-runs-identical-sha256 %s (%d B)" % (sha1[:16], len(blob1)),
                    sha1 == sha2))
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        fh.write(blob1)
        dpath = fh.name
    rc = sohead.main(["--sav", sav_path, "--map", map_path, "--turns", str(turns),
                      "--dump", dpath])
    results.append(("command-exit-0 rc=%d" % rc, rc == 0))
    os.unlink(dpath)
    bad = [n for n, ok in results if not ok]
    for name, ok in results:
        print(("  ok   " if ok else "  BAD  ") + name)
    if bad:
        return fail("B6: %d/%d gates failed: %s" % (len(bad), len(results), "; ".join(bad)))
    print("PASS B6: %d/%d gates - headless run over %s: %d turns, year %d -> %d, "
          "two runs sha256 %s (no box time, no /proc, no gdb)"
          % (len(results), len(results), os.path.basename(sav_path), turns, sv1.year,
             eng1.year, sha1[:16]))
    return 0


def run_b7(sav_path, map_path, turns, results):
    """Rung B7: two in-process move-slice runs -> identical bytes, plus the slice's gates."""
    import hashlib
    import tempfile
    from . import movesim as somv
    if not (os.path.exists(sav_path) and os.path.exists(map_path)):
        return fail("B7: missing input: %s / %s" % (sav_path, map_path))
    sv1, mp1, eng1, us1, st1, blob1 = somv.simulate(sav_path, map_path, somv.DEFAULT_RULES,
                                                    turns, 3)
    sv2, mp2, eng2, us2, st2, blob2 = somv.simulate(sav_path, map_path, somv.DEFAULT_RULES,
                                                    turns, 3)
    for name, ok, detail in somv.validate(sv1, mp1, eng1, us1, st1, turns, 3):
        results.append((name + " " + detail, ok))
    sha1 = hashlib.sha256(blob1.encode()).hexdigest()
    sha2 = hashlib.sha256(blob2.encode()).hexdigest()
    results.append(("two-runs-identical-sha256 %s (%d B)" % (sha1[:16], len(blob1)),
                    sha1 == sha2))
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        fh.write(blob1)
        dpath = fh.name
    rc = somv.main(["--sav", sav_path, "--map", map_path, "--turns", str(turns),
                    "--dump", dpath])
    results.append(("command-exit-0 rc=%d" % rc, rc == 0))
    os.unlink(dpath)
    bad = [n for n, ok in results if not ok]
    for name, ok in results:
        print(("  ok   " if ok else "  BAD  ") + name)
    if bad:
        return fail("B7: %d/%d gates failed: %s" % (len(bad), len(results), "; ".join(bad)))
    print("PASS B7: %d/%d gates - the move slice over %s: %d units x %d turns x 3 presses, "
          "year %d -> %d, two runs sha256 %s (no box time, no /proc, no gdb)"
          % (len(results), len(results), os.path.basename(sav_path), sv1.n_units, turns,
             sv1.year, eng1.year, sha1[:16]))
    return 0

def run_b8(sav_path, map_path, turns, results):
    """Rung B8: the save-WRITE leg - identity round-trip, decoder re-read, mutation lands,
    rivals fail the same fit, determinism + CLI. No box, no /proc, no gdb."""
    import hashlib
    import os as _os
    import subprocess
    import tempfile
    import struct
    from . import savewriter as sow
    from . import save as sosave
    from . import turn as soturn
    from . import map as somap
    if not (_os.path.exists(sav_path) and _os.path.exists(map_path)):
        return fail("B8: missing input: %s / %s" % (sav_path, map_path))
    sv = sosave.parse(sav_path)
    mp = somap.parse(map_path)
    img = sow.build_image(sv)
    # the SAV's own map-header dims are modeled and arbitrated by the identity gate below;
    # the shipped .MP is the OTHER size family (m54b_clean is 64x64, planet.MP is 80x80 -
    # the B6/B7 pairing uses the .MP for terrain rules, not dims), so cross-file dims
    # equality would be a false premise. What must hold: the written image carries the
    # model's dims back at the map-header struct, and both files parsed independently.
    dims2 = struct.unpack_from("<II", img, sosave.MAP_HDR_OFF)
    results.append(("written map-header dims re-read %dx%d == model %dx%d (%s parses %dx%d)"
                    % (dims2[0], dims2[1], sv.width, sv.height, _os.path.basename(map_path),
                       mp.width, mp.height),
                    dims2 == (sv.width, sv.height)
                    and sv.width * sv.height * sosave.CELL_LEN == sv.grid_len))
    results.append(("identity-roundtrip byte-exact on %d B" % len(sv.data), img == sv.data))
    # the repo's own decoder re-reads the written image
    with tempfile.NamedTemporaryFile("wb", suffix=".SAV", delete=False) as fh:
        fh.write(img)
        wpath = fh.name
    try:
        def sec(pth):
            r = subprocess.run([sys.executable, "scripts/decode_save.py", pth,
                                "--sections", "--anchors"],
                               capture_output=True, text=True, cwd=REPO)
            return r.stdout.replace(pth, "<F>") if r.returncode == 0 else "rc=%d" % r.returncode
        results.append(("decode_save sections+anchors identical", sec(sav_path) == sec(wpath)))
    finally:
        _os.unlink(wpath)
    # mutation: press the B3 engine `turns` times and write the model out
    eng = soturn.Engine(sv.year, human=sv.own_player)
    for _ in range(turns):
        eng.press()
    img2 = sow.build_image(sv, year=eng.year, cur=eng.cur, tf=eng.tf)
    rep = sosave.Save("written", img2)
    results.append(("mutation year %d->%d re-parses" % (sv.year, eng.year),
                    rep.year == eng.year and rep.n_units == sv.n_units
                    and rep.n_bases == sv.n_bases))
    out_of_model = sow.modeled_diff_check(sv.data, img2)
    # x/y of the moved unit records are modeled too: add their spans
    dset = sow.diff_offsets(sv.data, img2)
    xspans = set()
    for i in range(sv.n_units):
        o = sv.units_off + sosave.UNIT_LEN * i
        xspans |= {o, o + 1, o + 2, o + 3}
    unmodeled = [i for i in out_of_model if i not in xspans]
    results.append(("mutation diff confined to modeled bytes (%d diffs)" % len(dset),
                    not unmodeled and sow._u32(img2, sow.OFF_CUR) == eng.cur))
    # a single unit move lands in exactly its two x-bytes
    u0 = sv.units[0]
    img3 = sow.build_image(sv, moves={0: (u0["x"] + 2, u0["y"])})
    d3 = sow.diff_offsets(sv.data, img3)
    o0 = sv.units_off
    import struct as _st
    x2 = u0["x"] + 2
    expected3 = {o0 + k for k in range(2)
                 if u0["x"].to_bytes(2, "little")[k] != x2.to_bytes(2, "little")[k]}
    results.append(("move x->x+2 lands in exactly record 0's bytes %s==%s"
                    % (sorted(d3), sorted(expected3)), d3 == expected3))
    # rival 1: the pure re-emitter passes identity but FAILS the year mutation
    rival = sow.build_image(sv, year=eng.year, cur=eng.cur, tf=eng.tf, lift_all=True)
    results.append(("RIVAL pure-reemitter fails year mutation (carries %d)"
                    % sosave.Save("r", rival).year,
                    rival == sv.data and sosave.Save("r", rival).year != eng.year))
    # rival 2: a writer with UNIT_LEN perturbed by 4 FAILS the identity
    rival2 = sow.build_image(sv, unit_len=sosave.UNIT_LEN + 4)
    results.append(("RIVAL UNIT_LEN+4 fails identity (len %d vs %d)"
                    % (len(rival2), len(sv.data)), rival2 != sv.data))
    # determinism + the module CLI
    sha = [hashlib.sha256(sow.build_image(sv)).hexdigest() for _ in range(2)]
    results.append(("two-runs-identical-sha256 %s (%d B)" % (sha[0][:16], len(img)),
                    sha[0] == sha[1] and img == sv.data))
    with tempfile.NamedTemporaryFile("wb", suffix=".SAV", delete=False) as fh:
        cpath = fh.name
    rc = sow.main(["--sav", sav_path, "--out", cpath])
    cli_ok = rc == 0 and open(cpath, "rb").read() == sv.data
    _os.unlink(cpath)
    results.append(("command python3 -m sim.savewriter exit-0 + byte-exact rc=%d" % rc, cli_ok))
    bad = [n for n, ok in results if not ok]
    for name, ok in results:
        print(("  ok   " if ok else "  BAD  ") + name)
    if bad:
        return fail("B8: %d/%d gates failed: %s" % (len(bad), len(results), "; ".join(bad)))
    print("PASS B8: %d/%d gates - save WRITE leg on %s: identity round-trip %d B, year %d -> "
          "%d written through the B3 engine, rivals fail the same fit, sha256 %s (no box time, "
          "no /proc, no gdb)" % (len(results), len(results), _os.path.basename(sav_path),
                                 len(sv.data), sv.year, eng.year, sha[0][:16]))
    return 0



def run_b9(sav_path, trace_path, results):
    """Rung B9: the R3 golden-trace pairing - press the B3 engine the recorded
    trace's OWN turn count and pair every recorded snapshot (before(0)+40 after)
    against the emitted sequence. No box, no /proc, no gdb."""
    import os as _os
    from . import parity as sop
    if trace_path is None:
        trace_path = sop.DEFAULT_TRACE
    if not (_os.path.exists(sav_path) and _os.path.exists(trace_path)):
        return fail("B9: missing input: %s / %s" % (sav_path, trace_path))
    p1 = sop.pair(sav_path, trace_path)
    _, _, _, blob2, _ = sop.pair(sav_path, trace_path)
    sv, eng, report, blob, g = p1
    # two independent parses -> identical blob (determinism inside the harness)
    import hashlib
    sha = hashlib.sha256(blob.encode()).hexdigest()
    results.append(("trace-shape-40-turn-rows + pair-chain (before(0)==save start,"
                    " before(t)==after(t-1) all 40)", g["trace-shape"] and g["pair-chain"]))
    for k in ("snapshots-covered", "year-before", "rival-reversed",
              "rival-year-edge", "frontier-declared"):
        results.append((k, g[k]))
    results.append(("two-runs-identical-sha256 %s" % sha[:16],
                    sha == hashlib.sha256(blob2.encode()).hexdigest()
                    and report["missing"] == []))
    bad = [n for n, ok in results if not ok]
    for name, ok in results:
        print(("  ok   " if ok else "  BAD  ") + name)
    print("  info frontier n_bases model=%d recorded=%d->%d delta=%d (not modeled)"
          % (report["frontier_n_bases"]["model_const"],
             report["frontier_n_bases"]["recorded_first"],
             report["frontier_n_bases"]["recorded_last"],
             report["frontier_n_bases"]["delta"]))
    if bad:
        return fail("B9: %d/%d gates failed: %s"
                    % (len(bad), len(results), "; ".join(bad)))
    print("PASS B9: %d/%d gates - %d-turn golden trace pairs %d/%d snapshots on %s, "
          "final %s, both rivals miss, sha256 %s (no box time, no /proc, no gdb)"
          % (len(results), len(results), report["turns"],
             report["snapshots"] - len(report["missing"]), report["snapshots"],
             _os.path.basename(sav_path), list(eng.state()), sha[:16]))
    return 0




def run_b10(sav_path, trace_path, results):
    """Rung B10: the M282 base-founder/destroyer leg on the B3 engine - founder
    semantics, destroyer compaction, the 0x200 guard, the recorded n_bases curve
    (18->26), the written-image round-trip, determinism and the CLI.
    No box, no /proc, no gdb."""
    import hashlib
    import os as _os
    import subprocess
    import tempfile
    from . import basefound as sobf
    from . import savewriter as sow
    from . import save as sosave
    from . import parity as sop
    if trace_path is None:
        trace_path = sobf.DEFAULT_TRACE
    if not (_os.path.exists(sav_path) and _os.path.exists(trace_path)):
        return fail("B10: missing input: %s / %s" % (sav_path, trace_path))
    sv = sosave.parse(sav_path)
    # 1 constants and the founder write law
    results.append(("constants CAP 0x200 BASE_LEN 304 offsets 0/2/4",
                    sobf.CAP == 0x200 and sobf.BASE_LEN == 304 == sosave.BASE_LEN
                    and (sobf.X_OFF, sobf.Y_OFF, sobf.FAC_OFF) == (0, 2, 4)))
    led = sobf.Ledger()
    led.found(2, 30, 41)
    rb = sobf.record_bytes(led.records[0])
    results.append(("found() appends 304-B record x@0 y@2 fac@4/5 rest zero",
                    len(led) == 1 and rb[0:2] == (30).to_bytes(2, "little")
                    and rb[2:4] == (41).to_bytes(2, "little")
                    and rb[4] == 2 and rb[5] == 2 and rb[6:] == bytes(298)))
    # 2 destroyer compaction
    seed = [{"own4": i, "fac": i, "x": i, "y": i} for i in range(5)]
    ld2 = sobf.Ledger(seed)
    moved = ld2.destroy(1)
    results.append(("destroy(1) compacts LAST into slot 1 (count-1)",
                    moved == seed[4]
                    and ld2.records == [seed[0], seed[4], seed[2], seed[3]]
                    and len(ld2) == 4))
    results.append(("destroy out-of-range refused",
                    ld2.destroy(9) is None and len(ld2) == 4))
    # 3 the 0x200 guard
    ld3 = sobf.Ledger([{"own4": 1, "fac": 1, "x": 1, "y": 1}
                       for _ in range(sobf.CAP)])
    results.append(("0x200 guard refuses the 513th founding, count stays 512",
                    ld3.found(1, 2, 2) is False and len(ld3) == sobf.CAP))
    # 4 the golden n_bases curve
    sv, eng, ledm, report, blob = sobf.pair(sav_path, trace_path)
    ev = report["events"]
    results.append(("events derived from the trace (t8 +1 t9 +1 t17 +1 t22 +2 "
                    "t23 -1 t27 +1 t32 +2 t34 +1)",
                    ev == {8: 1, 9: 1, 17: 1, 22: 2, 23: -1, 27: 1, 32: 2, 34: 1}))
    bad = [(t, rc, mc) for (t, rc, mc) in report["snapshots"] if rc != mc]
    results.append(("all %d snapshots agree on n_bases (model %d, recorded %d)"
                    % (len(report["snapshots"]), report["final"]["model"],
                       report["final"]["recorded"]),
                    bad == [] and report["final"]["model"] == 26
                    and report["final"]["recorded"] == 26))
    results.append(("year pairing through B3 unchanged (%d)" % eng.year,
                    eng.year == sv.year + report["turns"]))
    _, _, _, r2, _ = sobf.pair(sav_path, trace_path, apply_events=False)
    bad2 = sum(1 for (t, rc, mc) in r2["snapshots"] if rc != mc)
    results.append(("RIVAL no-leg (B9 shape) keeps 18, %d snapshots diverge"
                    % bad2, bad2 == 32 and r2["final"]["model"] == 18))
    tot = sum(ev.values())
    _, _, _, r3, _ = sobf.pair(sav_path, trace_path, schedule={0: tot})
    results.append(("RIVAL all-events-on-turn-0 diverges at t0 (model %d vs "
                    "recorded %d)" % (r3["snapshots"][0][2],
                                      r3["snapshots"][0][1]),
                    r3["snapshots"][0][2] == 18 + tot
                    and r3["snapshots"][0][2] != r3["snapshots"][0][1]))
    svp, engp, repp, blobp, gp = sop.pair(sav_path, trace_path)
    results.append(("B9 pairing still green on the same trace (%d missing)"
                    % len(repp["missing"]), repp["missing"] == []))
    # 5 the written founded image
    bo = sv.bases_off
    ledg = sobf.from_save(sv)
    ledg.found(3, 30, 41)
    img = sow.build_image(sv, bases_override=ledg.records,
                          orig_n_bases=sv.n_bases)
    rec18 = img[bo + 304 * 18:bo + 304 * 19]
    pre_diffs = [i for i in range(bo) if img[i] != sv.data[i]]
    results.append(("founded image == original + one 304-B record (only the "
                    "bases-count dword changes in the prefix %s, record bytes "
                    "and tail byte-identical)" % (pre_diffs,),
                    len(img) == len(sv.data) + 304 and pre_diffs == [72]
                    and img[bo:bo + 304 * 18] == sv.data[bo:bo + 304 * 18]
                    and rec18 == sobf.record_bytes(ledg.records[18])
                    and img[bo + 304 * 19:] == sv.data[bo + 304 * 18:]))
    imgid = sow.build_image(sv, bases_override=ledg.records[:18],
                            orig_n_bases=18)
    results.append(("override path with no growth is byte-exact identity",
                    imgid == sv.data))
    rp = sosave.Save("written", img)
    b18 = rp.base(18)
    results.append(("written image re-parses (n_bases 19, record 18 x/y/own4/"
                    "fac read back, shape-found 18 declared)",
                    rp.n_bases == 19 and rp.found_bases == 18
                    and b18["x"] == 30 and b18["y"] == 41
                    and b18["own4"] == 3 and b18["fac"] == 3))
    with tempfile.NamedTemporaryFile("wb", suffix=".SAV", delete=False) as fh:
        fh.write(img)
        wpath = fh.name
    try:
        dr = subprocess.run([sys.executable, "scripts/decode_save.py", wpath,
                             "--sections"], capture_output=True, text=True,
                            cwd=REPO)
        dr0 = subprocess.run([sys.executable, "scripts/decode_save.py", sav_path,
                              "--sections"], capture_output=True, text=True,
                             cwd=REPO)
        def _norm(s):
            return s[s.find("  year"):]          # strip path/size/version header lines
        same_view = (dr.returncode == dr0.returncode
                     and _norm(dr.stdout.replace(wpath, "<F>"))
                     == _norm(dr0.stdout.replace(sav_path, "<F>")))
        results.append(("decode_save's 64x64 walk sees the grown image exactly "
                        "like the original (rc %d == rc %d; the walk hardcodes "
                        "the 80x80 map-trailer count offset and pre-splits on "
                        "64x64 saves, so --sections fails on both - B8's sec "
                        "equality still holds)" % (dr.returncode, dr0.returncode),
                        same_view))
    finally:
        _os.unlink(wpath)
    # 6 determinism + the module CLI
    _, _, _, _, blob2 = sobf.pair(sav_path, trace_path)
    sha = hashlib.sha256(blob.encode()).hexdigest()
    results.append(("two-runs-identical-sha256 %s" % sha[:16],
                    sha == hashlib.sha256(blob2.encode()).hexdigest()))
    with tempfile.NamedTemporaryFile("wb", suffix=".json", delete=False) as fh:
        op = fh.name
    rc = sobf.main(["--sav", sav_path, "--trace", trace_path, "--out", op])
    cli_ok = rc == 0 and _os.path.getsize(op) > 0
    _os.unlink(op)
    results.append(("command python3 -m sim.basefound exit-0 + report rc=%d"
                    % rc, cli_ok))
    # 7 the flooded 512-cap image
    ld5 = sobf.Ledger([{"own4": 1, "fac": 1, "x": 1, "y": 1}
                       for _ in range(sobf.CAP)])
    img5 = sow.build_image(sv, bases_override=ld5.records,
                           orig_n_bases=sv.n_bases)
    results.append(("flooded 512-cap image grows by 494 records, tail "
                    "byte-identical",
                    len(img5) == len(sv.data) + 304 * (sobf.CAP - 18)
                    and img5[bo + 304 * sobf.CAP:] == sv.data[bo + 304 * 18:]))
    bad = [n for n, ok in results if not ok]
    for name, ok in results:
        print(("  ok   " if ok else "  BAD  ") + name)
    if bad:
        return fail("B10: %d/%d gates failed: %s"
                    % (len(bad), len(results), "; ".join(bad)))
    print("PASS B10: %d/%d gates - the M282 founder/destroyer leg: record "
          "semantics, compaction, the 0x200 guard, the recorded 18-to-26 n_bases "
          "curve (%d/41 snapshots), a written founded image with a byte-exact "
          "tail, flooded to the cap, sha256 %s (no box time, no /proc, no gdb)"
          % (len(results), len(results), len(report["snapshots"]), sha[:16]))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sim.selftest")
    ap.add_argument("--map", action="append", default=[], help="a .MP file (repeatable)")
    ap.add_argument("--rules", help="path to data/alpha.json")
    ap.add_argument("--sav")
    ap.add_argument("--replay")
    ap.add_argument("--replay-m27", action="store_true",
                    help="rung B5: replay evidence/m27_solowrap*.log through sim.units")
    ap.add_argument("--b6", nargs="+", metavar=("SAV", "MAP"),
                    help="rung B6: headless run twice, compare dump sha256 (turns via --turns)")
    ap.add_argument("--b7", nargs="+", metavar=("SAV", "MAP"),
                    help="rung B7: the move slice twice, compare dump sha256")
    ap.add_argument("--b8", nargs="+", metavar=("SAV", "MAP"),
                    help="rung B8: the save WRITE leg (identity, mutation, rivals)")
    ap.add_argument("--b9", nargs="+", metavar=("SAV", "TRACE"),
                    help="rung B9: the R3 golden-trace pairing (turn spine on the recorded trace)")
    ap.add_argument("--b10", nargs="+", metavar=("SAV", "TRACE"),
                    help="rung B10: funder/destroyer leg acceptance")
    ap.add_argument("--turns", type=int, default=10)
    args = ap.parse_args(argv)

    results = []
    if args.b6:
        return run_b6(args.b6[0], args.b6[1], args.turns, results)
    if args.b7:
        return run_b7(args.b7[0], args.b7[1], args.turns, results)
    if args.b8:
        return run_b8(args.b8[0], args.b8[1], args.turns, results)
    if args.b9:
        tr = args.b9[1] if len(args.b9) > 1 else None
        return run_b9(args.b9[0], tr, results)
    if args.b10:
        tr = args.b10[1] if len(args.b10) > 1 else None
        return run_b10(args.b10[0], tr, results)
    if args.replay_m27:
        from . import units as su_b5
        run_m27_replay(results)
        bad = [n for n, ok in results if not ok]
        for name, ok in results:
            print(("  ok   " if ok else "  BAD  ") + name)
        if bad:
            return fail("B5: %d/%d gates failed: %s" % (len(bad), len(results),
                                                        "; ".join(bad)))
        print("PASS B5: %d/%d gates on %s — %s" % (
            len(results), len(results), " + ".join(M27_LOGS),
            "one lattice step of %s per press at %d MP, %d MP per unit per round, x wrapped "
            "by the map width, y bounds-checked (no box time, no /proc, no gdb)"
            % (su_b5.DIR_DX, su_b5.STEP_MP, su_b5.MP_PER_TURN)))
        return 0
    if args.replay:
        if not os.path.exists(args.replay):
            return fail("replay trace not found: %s" % args.replay)
        import json
        rung = None
        try:
            doc = json.loads(open(args.replay, encoding="utf-8").read())
        except ValueError:
            doc = None
        if isinstance(doc, dict) and "rounds" in doc:      # an economy trace (m44d/m46 shape)
            run_economy_replay(doc, results)
            run_economy_hud(results)
            rung = "B4"
        else:                                              # a turn trace (m30 .jsonl)
            run_replay(args.replay, results)
            rung = "B3"
        bad = [n for n, ok in results if not ok]
        for name, ok in results:
            print(("  ok   " if ok else "  BAD  ") + name)
        if bad:
            return fail("%s: %d/%d gates failed: %s" % (
                rung, len(bad), len(results), "; ".join(bad)))
        print("PASS %s: %d/%d gates on %s — %s" % (
            rung, len(results), len(results), os.path.basename(args.replay),
            "the economy model reproduces the recorded idle rounds and the game's own HUD triple"
            if rung == "B4" else "the turn engine reproduces the recorded sequence"))
        return 0
    if args.sav and not args.map:
        run_save(args.sav, results)
        bad = [n for n, ok in results if not ok]
        for name, ok in results:
            print(("  ok   " if ok else "  BAD  ") + name)
        if bad:
            return fail("B2: %d/%d gates failed: %s" % (len(bad), len(results), "; ".join(bad)))
        print("PASS B2: %d/%d gates on %s" % (len(results), len(results),
                                              os.path.basename(args.sav)))
        return 0
    maps = list(args.map)
    if len(maps) == 1:
        sibs = SIBLING.get(os.path.basename(maps[0]))
        if sibs:
            cand = os.path.join(os.path.dirname(maps[0]), sibs)
            if os.path.exists(cand):
                maps.append(cand)
                print("note: --map expanded to %s (rung B1 requires parity for both "
                      "the 80x80 and the 128x128 grid)" % cand)
    if not maps:
        return fail("no --map given")
    dims = set()
    for p in maps:
        if not os.path.exists(p):
            return fail(f"map file not found: {p}")
        dims.add(check_map(p, results))

    # gate 2: both shipped dimensions must have been checked
    results.append(("dims-checked %s covers %s" % (sorted(dims), sorted(EXPECTED_DIMS)),
                    EXPECTED_DIMS.issubset(dims)))

    # gate 6: rules tables
    if args.rules:
        if not os.path.exists(args.rules):
            return fail(f"rules file not found: {args.rules}")
        r = sorules.load(args.rules)
        raw = sorules.json.load(open(args.rules, encoding="utf-8"))
        results.append(("rules-sections %s sections=%d records=%d empty=%s" % (
            os.path.basename(args.rules), len(r.counts), r.total_records, r.empty_sections),
            len(r.counts) == len(raw) and not r.empty_sections
            and all(r.counts[k] == len(raw[k]) for k in raw)))
    else:
        results.append(("rules-sections (no --rules given; B1 acceptance requires it)", False))

    bad = [n for n, ok in results if not ok]
    for name, ok in results:
        print(("  ok   " if ok else "  BAD  ") + name)
    if bad:
        return fail("B1: %d/%d gates failed: %s" % (len(bad), len(results), "; ".join(bad)))
    print("PASS B1: %d/%d gates on %s" % (len(results), len(results),
                                          ", ".join(os.path.basename(p) for p in maps)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
