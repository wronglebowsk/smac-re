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


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sim.selftest")
    ap.add_argument("--map", action="append", default=[], help="a .MP file (repeatable)")
    ap.add_argument("--rules", help="path to data/alpha.json")
    ap.add_argument("--sav")
    ap.add_argument("--replay")
    args = ap.parse_args(argv)

    results = []
    if args.replay:
        if not os.path.exists(args.replay):
            return fail("replay trace not found: %s" % args.replay)
        run_replay(args.replay, results)
        bad = [n for n, ok in results if not ok]
        for name, ok in results:
            print(("  ok   " if ok else "  BAD  ") + name)
        if bad:
            return fail("B3: %d/%d gates failed: %s" % (
                len(bad), len(results), "; ".join(bad)))
        print("PASS B3: %d/%d gates on %s — the turn engine reproduces the recorded "
              "sequence" % (len(results), len(results), os.path.basename(args.replay)))
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
