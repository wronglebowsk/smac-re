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

    print()
    if FAILS:
        print(f"FAILED: {len(FAILS)} — {', '.join(FAILS)}")
        return 1
    print("PASS 20/20 attribution cases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
