#!/usr/bin/env python3
"""M54i: the walk's destination must come from the record the keypress CHANGED.

`diff_order_records` is the attribution rule behind `issue_order_for_unit`. Its proof
of a FRESH order is the through-the-click watcher's own samples on the CANDIDATE's
record slot (a 0 -> 0x18 transition seen THERE); the destination is the leg array of
that same record, and only if its legs CHANGED against the pre-press value and no
indistinguishable rival on the same tile got a fresh order we did not watch land.

The rules the cases below pin down:
  * identity is the watched record slot, never an index carried across a turn — an
    index is re-used by a different unit the moment one is built or dies (session 85
    read legs naming bases nobody ordered off exactly such a re-used index);
  * stale legs are not evidence — the leg arrays survive the pump, so a record ordered
    on an EARLIER turn already carries a route;
  * a record that already carried the byte (a live 0x18 walker) is not a fresh order;
  * two indistinguishable records (same type, same tile) both freshly ordered =
    CONFOUNDED = nothing attributed.

    python3 scripts/test_walk_diff.py
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as sp  # noqa: E402

FAILS = []
W = {0x18}


def raw(x=28, y=42, typ=2, order=0, legs=(), mp=0, owner=3):
    b = bytearray(52)
    b[0:2] = struct.pack("<h", x)
    b[2:4] = struct.pack("<h", y)
    b[10:12] = struct.pack("<H", typ)
    b[14] = owner
    b[17] = order
    b[40] = mp
    # the game terminates the leg arrays with -1 (ORDERS.md §4); a zero would decode
    # as a real (0,0) leg, so the test fixture must too
    for k in range(4):
        b[20 + k * 2:22 + k * 2] = struct.pack("<h", -1)
        b[28 + k * 2:30 + k * 2] = struct.pack("<h", -1)
    for k, (lx, ly) in enumerate(legs):
        b[20 + k * 2:22 + k * 2] = struct.pack("<h", lx)
        b[28 + k * 2:30 + k * 2] = struct.pack("<h", ly)
    return bytes(b)


def row(idx, **kw):
    r = raw(**kw)
    return dict(idx=idx, x=struct.unpack("<h", r[0:2])[0],
                y=struct.unpack("<h", r[2:4])[0],
                type=struct.unpack("<H", r[10:12])[0], order=r[17], mp=r[40],
                legs=sp.legs_of(r))


def samples(*steps):
    """(ms, order, legs) triples -> the watcher's (raw, ms, byte) list."""
    return [(raw(x=28, y=42, order=o, legs=l), ms, o) for ms, o, l in steps]


def check(name, cond, detail=""):
    print(f"  {'ok  ' if cond else 'FAIL'} {name}" + (f"  [{detail}]" if not cond else ""))
    if not cond:
        FAILS.append(name)


def main():
    ours = [row(0, x=28, y=42), row(1, x=29, y=42)]

    print("case 1: the watcher saw no transition -> no claim")
    claim, rivals, att, conf = sp.diff_order_records(ours, 0, W, [], [])
    check("no samples -> nothing attributed", claim is None and not rivals and not att,
          f"{claim} {rivals}")

    print("case 2: 0 -> 0x18 on our slot with NEW legs -> claimed")
    smp = samples((0, 0, []), (80, 0x18, [(29, 42)]), (300, 0x18, [(29, 42)]))
    claim, rivals, att, conf = sp.diff_order_records(ours, 0, W, smp, [])
    check("attributed to the watched record, legs from the same samples",
          att and claim and claim["cand"] and claim["legs_after"] == [[29, 42]]
          and claim["landed_at_ms"] == 80 and not conf, f"{claim} {rivals}")

    print("case 3: the byte lands but the legs were ALREADY that (stale route)")
    smp = samples((0, 0, [(29, 42)]), (80, 0x18, [(29, 42)]))
    claim, rivals, att, conf = sp.diff_order_records(ours, 0, W, smp, [(29, 42)])
    check("unchanged legs -> nothing attributed", claim is None and not att,
          f"{claim} {rivals}")

    print("case 4: a walker ordered EARLIER on another tile is not a rival")
    before = [row(0, x=28, y=42), row(1, x=29, y=43, order=0x18, legs=[(29, 42)]),
              row(2, x=28, y=43, order=1, legs=[(22, 31)])]
    after = [row(0, x=28, y=42, order=0x18, legs=[(29, 42)]),
             row(1, x=29, y=42, order=0x18, legs=[(29, 42)], mp=3),   # it stepped
             row(2, x=28, y=43, order=1, legs=[(22, 31)])]
    smp = samples((0, 0, []), (90, 0x18, [(29, 42)]))
    claim, rivals, att, conf = sp.diff_order_records(before, 0, W, smp, [], after=after)
    check("only the watched order counts; the stepped walker is not a rival",
          att and claim and not rivals and not conf, f"{claim} {rivals}")

    print("case 5: TWO indistinguishable stacked units freshly ordered -> confounded")
    before = [row(0, x=28, y=42), row(1, x=28, y=42)]
    after = [row(0, x=28, y=42, order=0x18, legs=[(29, 42)]),
             row(1, x=28, y=42, order=0x18, legs=[(28, 43)])]
    smp = samples((0, 0, []), (90, 0x18, [(29, 42)]))
    claim, rivals, att, conf = sp.diff_order_records(before, 0, W, smp, [], after=after)
    check("the rival is named and nothing is attributed",
          claim and att is False and len(rivals) == 1 and conf, f"{claim} {rivals}")

    print("case 6: a stacked look-alike ordered on an EARLIER turn is not a rival")
    before = [row(0, x=28, y=42), row(1, x=28, y=42, order=0x18, legs=[(28, 43)])]
    after = [row(0, x=28, y=42, order=0x18, legs=[(29, 42)]),
             row(1, x=28, y=42, order=0x18, legs=[(28, 43)])]
    smp = samples((0, 0, []), (90, 0x18, [(29, 42)]))
    claim, rivals, att, conf = sp.diff_order_records(before, 0, W, smp, [], after=after)
    check("stale legs on the look-alike -> no rival, still attributed",
          att and claim and not rivals, f"{claim} {rivals}")

    print("case 7: a mid-run insert shifts the indices; rivals follow (type, tile)")
    before = [row(0, x=28, y=42), row(1, x=29, y=42)]
    after = [row(0, x=28, y=42), row(1, x=28, y=42, order=0x18, legs=[(29, 42)]),
             row(2, x=29, y=42)]     # the candidate, shifted by the insert, unchanged
    smp = samples((0, 0, []), (90, 0x18, [(29, 42)]))
    claim, rivals, att, conf = sp.diff_order_records(before, 1, W, smp, [], after=after)
    check("shifted AND stepped -> confounded, never a guessed destination",
          claim is not None and conf and not att and len(rivals) == 1, f"{claim} {rivals}")

    print("case 8: a byte that was never 0 before is not a FRESH order")
    smp = samples((0, 1, []), (80, 0x18, [(29, 42)]))
    claim, rivals, att, conf = sp.diff_order_records(ours, 0, W, smp, [])
    check("replacing an existing order claims nothing", claim is None and not att,
          f"{claim} {rivals}")

    print("case 9: the byte seen is not the byte the key may produce -> no claim")
    smp = samples((0, 0, []), (80, 0x19, [(29, 42)]))
    claim, rivals, att, conf = sp.diff_order_records(ours, 0, W, smp, [])
    check("a byte outside `want` is not this order", claim is None and not att,
          f"{claim} {rivals}")

    print("case 10: no rival scan without an after-snapshot, but the claim stands")
    smp = samples((0, 0, []), (90, 0x18, [(29, 42)]))
    claim, rivals, att, conf = sp.diff_order_records(ours, 0, W, smp, [], after=None)
    check("claim survives without the rival scan", att and claim and not rivals,
          f"{claim} {rivals}")

    # The BRACKET shape: the chooser answered by its default button (Return on an
    # `unknown` frame) means the watcher never ran — the two reads bracketing the
    # press are the samples. Same rules, and the moved-record case is the one that
    # must NOT false-confound: our own record on its new tile wears the signature we
    # watched (byte + route + end tile); only a row at ANOTHER index may rival it.
    print("case 11: bracket samples (watcher never ran), unit still on tile -> claimed")
    smp = samples((0, 0, []), (700, 0x18, [(29, 42)]))
    after = [row(0, x=28, y=42, order=0x18, legs=[(29, 42)]), row(1, x=29, y=42)]
    claim, rivals, att, conf = sp.diff_order_records(ours, 0, W, smp, [], after=after)
    check("bracket 0 -> byte with new legs attributes",
          att and claim and claim["legs_after"] == [[29, 42]] and not rivals,
          f"{claim} {rivals}")

    print("case 12: bracket samples, unit STEPPED off its tile -> still claimed")
    before = [row(0, x=28, y=42), row(1, x=29, y=42)]
    braw_before = raw(x=28, y=42, order=0)
    braw_after = raw(x=28, y=43, order=0x18, legs=[(28, 42)], mp=3)
    smp = [(braw_before, -1.0, 0), (braw_after, 1.0, 0x18)]
    after = [row(0, x=28, y=43, order=0x18, legs=[(28, 42)], mp=3),
             row(1, x=29, y=42)]
    claim, rivals, att, conf = sp.diff_order_records(before, 0, W, smp, [], after=after)
    check("our own moved record is not a rival of itself",
          att and claim and not rivals and not conf, f"{claim} {rivals}")

    print("case 13: bracket samples, unit stepped AND a twin wears the signature")
    before = [row(0, x=28, y=42), row(1, x=28, y=42)]
    after = [row(0, x=28, y=43, order=0x18, legs=[(28, 42)], mp=3),
             row(1, x=28, y=43, order=0x18, legs=[(28, 42)], mp=3)]
    claim, rivals, att, conf = sp.diff_order_records(before, 0, W, smp, [], after=after)
    check("indistinguishable twin -> confounded, nothing attributed",
          claim is not None and conf and not att and len(rivals) == 1,
          f"{claim} {rivals}")

    # ---------------- M54i2: the RETRY shape (`move_order_needs_retry`) -------------
    # Session 86's two live failure modes are DRIVER policy, not attribution rules: a
    # chooser OK that lands the byte with no route, and a `g` that fell through to the
    # cursor-tile handler (base screen). Both say "press again" — up to the cap.
    print("case 14: verified MOVE WITH legs -> no retry")
    o = dict(key="g", verified=True, dest=[29, 42], panes=["dest-chooser"])
    check("a routed move is done", sp.move_order_needs_retry(o, 0) is False)

    print("case 15: byte landed, LEGS EMPTY (run5 t3) -> retry once")
    o = dict(key="g", verified=True, dest=None, panes=["dest-chooser"],
             walk_diff=dict(attributed=False, confounded=False, claim=None, rivals=[]))
    check("legs-less OK re-raises", sp.move_order_needs_retry(o, 0) is True
          and sp.move_order_needs_retry(o, 1) is True
          and sp.move_order_needs_retry(o, 2) is False,
          "cap is MOVE_ORDER_RETRIES")

    print("case 16: `g` fell to the cursor handler (base screen) -> retry")
    o = dict(key="g", verified=False, dest=None, panes=["base", "unknown", "base", "base"])
    check("a dud base screen re-raises", sp.move_order_needs_retry(o, 0) is True
          and sp.move_order_needs_retry(o, 2) is False)

    print("case 17: a non-MOVE key never retries")
    o = dict(key="l", verified=True, dest=None, panes=["base"])
    check("sentry/hold/terraform land without a chooser",
          sp.move_order_needs_retry(o, 0) is False)

    print("case 18: unverified `g` with NO base screen does not retry")
    o = dict(key="g", verified=False, dest=None, panes=["unknown", "hud"])
    check("a dropped key is the turn's problem, not a re-press",
          sp.move_order_needs_retry(o, 0) is False)

    # ---------------- M54i2: the DESTINATION is the chooser's, not a leg -------------
    print("case 19: chooser named University Base, legs hold the FIRST STEP (11,17)")
    check("dest = the named base, not the waypoint",
          sp.resolve_move_dest({"base": [28, 42], "base_name": "University Base"},
                               [(11, 17)]) == [28, 42])

    print("case 20: no chooser row (queued without a pane) -> last leg is the fallback")
    check("legs still answer when the chooser never ran",
          sp.resolve_move_dest(None, [(29, 42)]) == [29, 42]
          and sp.resolve_move_dest({}, []) is None)

    # ------- M54i2: the step table preserves (x+y) parity — the oscillation cause ----
    # The 21 (dx,dy) pairs below are the LIVE read of 0x67850c/0x678990 at 2159
    # (pid 1110005, 2026-10-25); the adjacency loop bound 0x54/4 = 21 is
    # ghidra_out/shard_013.c:21868.
    TABLE = [(0, 0), (1, -1), (2, 0), (1, 1), (0, 2), (-1, 1), (-2, 0), (-1, -1),
             (0, -2), (2, -2), (2, 2), (-2, 2), (-2, -2), (1, -3), (3, -1), (3, 1),
             (1, 3), (-1, 3), (-3, 1), (-3, -1), (-1, -3)]

    print("case 21: every step in the measured table preserves (x+y) parity")
    check("no step changes parity, so a walk never changes class",
          all((dx + dy) % 2 == 0 for dx, dy in TABLE) and len(TABLE) == 21)

    print("case 22: (29,42) and (28,43) are NOT table-neighbours of (28,42)")
    nb = sp.table_neighbors(28, 42, TABLE)
    check("the run2/m54e oscillation tiles are not neighbours of the base",
          (29, 42) not in nb and (28, 43) not in nb
          and (29, 41) in nb and (27, 43) in nb and (26, 42) in nb)

    print("case 23: walk_parity_ok — University (28,42) reachable from (29,41), "
          "Korolev (29,42) not")
    check("the gate keeps the reachable base and drops the impossible one",
          sp.walk_parity_ok((29, 41), (28, 42)) is True
          and sp.walk_parity_ok((29, 41), (29, 42)) is False
          and sp.walk_parity_ok((29, 42), (28, 42)) is False)

    print("case 24: the oscillation the pump experiment measured is the parity rule")
    # scratch/m54i2_pump.py: the order-24 record walked (28,43) -> (29,42) in one
    # TURN COMPLETE cycle — a legal step ((+1,-1) in TABLE) — and both tiles are
    # the wrong parity for its destination (28,42); under the invariant it can
    # NEVER arrive, which is every M54h/M54i/M54i2 "walk did not land" so far.
    step = (29 - 28, 42 - 43)
    check("the measured step is in the table and the destination is unreachable",
          step in TABLE and not sp.walk_parity_ok((28, 43), (28, 42))
          and not sp.walk_parity_ok((29, 42), (28, 42)))

    # ------- M54j: re-activation of HELD walkers (the auto-sentry finding) ---------
    # run1 (evidence/trace_m54j_run1_20261025_155011.jsonl): the setup left EXACTLY
    # one actionable record at (20,42) (order 0, read back on a second handle); by
    # our phase it wore byte 1 (SENTRY) and had patrolled away — the game auto-sentries
    # an order-0 unit across the round boundary. Only byte 2 (HOLD) survives it, so
    # the order step re-activates a held walker IN-PHASE. These cases pin the picker.
    OWN = {(28, 42), (29, 42)}

    print("case 25: the (20,42) held walker IS eligible — even parity matches "
          "University (28,42), man 8")
    h20 = row(37, x=20, y=42, order=2)
    sel = sp.pick_reactivation([h20], OWN, TABLE)
    check("eligible, nearest same-parity own base named, not a one-stepper",
          len(sel) == 1 and sel[0]["idx"] == 37 and sel[0]["man"] == 8
          and sel[0]["on_step"] is False and sel[0]["reactivated"] is True)

    print("case 26: a held unit STANDING ON our base is not eligible (`g` there "
          "raises the BASE SCREEN — session 86 run5 t0)")
    check("own-base tiles are dropped from the pool",
          sp.pick_reactivation([row(3, x=28, y=42, order=2)], OWN, TABLE) == [])

    print("case 27: our bases are OPPOSITE parity (70 even / 71 odd), so every "
          "tile matches exactly one base — the dropped records are own-base "
          "garrisons, whatever their parity")
    check("(29,42) and (28,42) garrisons dropped; a Korolev-parity odd tile and a "
          "University-parity even tile far out are BOTH eligible — (49,33) at man 21",
          sp.pick_reactivation([row(9, x=29, y=42, order=2),     # own tile (odd)
                                row(3, x=28, y=42, order=2)],    # own tile (even)
                               OWN, TABLE) == []
          and [r["idx"] for r in
               sp.pick_reactivation([row(0, x=49, y=33, order=2)], OWN, TABLE)] == [0]
          and sp.pick_reactivation([row(0, x=49, y=33, order=2)], OWN, TABLE)[0]["man"] == 21
          and [r["idx"] for r in
               sp.pick_reactivation([row(7, x=31, y=41, order=2)], OWN, TABLE)] == [7]
          and sp.pick_reactivation([row(7, x=31, y=41, order=2)], OWN, TABLE)[0]["man"] == 3)

    print("case 28: a one-stepper sorts AFTER a real multi-leg route")
    sel = sp.pick_reactivation([row(41, x=26, y=42, order=2),   # on a step of (28,42)
                                row(37, x=20, y=42, order=2)],  # 8 out
                               OWN, TABLE)
    check("the 8-out walker leads the 2-out one-step arrival",
          [r["idx"] for r in sel] == [37, 41]
          and sel[0]["on_step"] is False and sel[1]["on_step"] is True)

    # ------- M54j: the walker, not a headcount — run4's false ARRIVED --------------
    # run4 turn 2 (evidence/trace_m54j_run4_*.jsonl): the order moved (49,33) -> (47,33)
    # — 2 of 21 tiles — and `verify_moves` printed ARRIVED because University Base
    # already holds six type-2 records and the count fallback passed on the delta.
    DEST = (28, 42)
    ROUTE = [[28, 42]]

    print("case 29: six garrisons on the destination are NOT the arrival")
    six = [row(i, x=28, y=42, order=2) for i in range(6)]      # no route worn
    check("walker_on_dest is False while the walker is 2 tiles out",
          sp.walker_on_dest(six, 2, DEST, ROUTE) is False)

    print("case 30: the record WEARING the ordered route, on the tile, IS the arrival")
    arrived = six + [row(70, x=28, y=42, order=0, legs=[(28, 42)], mp=3)]
    midwalk = six + [row(70, x=43, y=35, order=24, legs=[(28, 42)], mp=3)]
    check("arrival True, mid-walk (route worn, wrong tile) False",
          sp.walker_on_dest(arrived, 2, DEST, ROUTE) is True
          and sp.walker_on_dest(midwalk, 2, DEST, ROUTE) is False)

    print("case 31: a legs-less order (session 86 shape) keeps the type+tile reading")
    check("empty route falls back to type+tile",
          sp.walker_on_dest(six, 2, DEST, []) is True
          and sp.walker_on_dest(six, 2, (20, 42), []) is False)

    print()
    if FAILS:
        print(f"FAILED: {len(FAILS)} — {', '.join(FAILS)}")
        return 1
    print("PASS 31/31 attribution cases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
