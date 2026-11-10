#!/usr/bin/env python3
"""sim.production - rung B12: the completion CREATE leg (R2's "build lands a
unit" slice).

BUILD_SPINE.md rung B12. The M56/M59/M61 completion law, executable:
when the visit's gate passes the game runs, in the measured order,
PAY -> CREATE -> POP (production-queue.md; m72gate5: PAYA then CREATE then
the pop stores LATER in the same visit):

  * GATE  storage + income >= price. The income add is INSIDE the same visit
    (M56) - the gate compares minerals+this-round's-income against price.
    price is the recorded per-base price (the visitor's own product `edi`,
    M72), never a recomputed `price_of`.
  * PAY   storage = storage + income - price.
  * CREATE  a NEW 52-B unit record appended at the END of the unit array
    (units_off, stride UNIT_LEN, count n_units): x/y = the base tile's x/y,
    flag(+4 u32) = 0, type(+10 u16) = the queue head id, owner(+14 u8) = the
    base faction, order(+17 u8) = 0, nlegs(+18 u8) = 0. A produced unit
    arrives order 0 ON its base tile (M56 accounting law: count arrivals as
    a multiset delta on (x,y,type,owner); never index, never order - an idle
    order-0 unit becomes order 1 at the boundary). The record's remaining
    bytes are DECLARED unmodeled - the model composes them as zero plus the
    named fields and the written image's re-parse proves the span.
  * POP   exactly one via B11's law (slots shift pending times, stale tail
    kept, cursor untouched).

Parity: the acceptance replays `evidence/trace_m56_build_20261026_145157.jsonl`
- the ORIGINAL terran.exe's own 10-boundary run on Korolev Center (29,42)
head 2 - and requires the created record tuple (x,y,type,owner,order) to
match the recorded net arrival delta exactly: +1 (29,42,2,3,0) at r0 (the
new record occupies the array's LAST slot), and NONE on r1..r9. RIVALS that
fail the same fit: a create at the wrong tile, at the idle order 2, or a
gate without the income term (8 >= 9 bails r0 against a recorded arrival).

NO /proc, NO gdb, NO Wine.
"""
import argparse
import hashlib
import json
import os
import struct
import sys

from . import save as so
from . import queue as soq

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(REPO, "evidence")

# --- the law's constants (unit-record field spans, save.py-compatible) ----
UNIT_X, UNIT_Y = 0, 2                  # u16 x, u16 y
UNIT_FLAG = 4                          # u32
UNIT_TYPE = 10                         # u16 type
UNIT_OWNER = 14                        # u8 owner
UNIT_ORDER = 17                        # u8 order (m26_poke; produced = 0)
UNIT_NLEGS = 18                        # u8 nlegs
ORDER_NEW = 0                          # produced unit arrives order 0 (M56)


def create_record(x, y, head, owner, new_order=ORDER_NEW):
    """Compose the 52-B created unit record. Modeled fields at the law's
    spans; every other byte is DECLARED unmodeled (composed as zero)."""
    rec = bytearray(so.UNIT_LEN)
    struct.pack_into("<H", rec, UNIT_X, int(x) % 0x10000)
    struct.pack_into("<H", rec, UNIT_Y, int(y) % 0x10000)
    struct.pack_into("<I", rec, UNIT_FLAG, 0)
    struct.pack_into("<H", rec, UNIT_TYPE, int(head) % 0x10000)
    rec[UNIT_OWNER] = int(owner) % 256
    rec[UNIT_ORDER] = int(new_order) % 256
    rec[UNIT_NLEGS] = 0
    return bytes(rec)


def visit(q, x, y, fac, storage, income, price, tile=None, new_order=ORDER_NEW):
    """The completion visit. q is a sim.queue.Queue. Returns
    ('bail', storage) when storage + income < price (gate 0x4efa5e);
    else ('pay', storage_after, record) with the recorded order PAY ->
    CREATE -> POP. tile= overrides the created record's tile (RIVAL);
    new_order= overrides the created order (RIVAL)."""
    if storage + income < price:
        return ("bail", storage)
    storage_after = storage + income - price
    tx, ty = (tile if tile is not None else (x, y))
    head = q.slots[0]
    record = create_record(tx, ty, head, fac, new_order=new_order)
    made = q.pop_once()                       # the POP (B11 law, one item)
    return ("pay", storage_after, record, made)


# --- replay of the recorded golden trace -----------------------------------
def trace_rows(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(ln) for ln in fh if ln.strip()]


def units_net_delta(before_units, after_units):
    """Multiset delta over (x, y, type, owner, order) - the M56 accounting
    law's key. Returns the Counter of NEW tuples in after not in before."""
    from collections import Counter
    cb = Counter((u["x"], u["y"], u["type"], u["owner"], u["order"])
                 for u in before_units)
    ca = Counter((u["x"], u["y"], u["type"], u["owner"], u["order"])
                 for u in after_units)
    return ca - cb


def replay(trace_path, tile=None, new_order=ORDER_NEW, income_term=True,
           gate_base=None):
    """Run the model over the trace's round_before rows for every in-mask
    prediction. Returns (rounds, created_by_round, recorded_delta_by_round,
    model_after_by_round). created_by_round[r] = set of created
    (x,y,type,owner,order) tuples; recorded_delta_by_round[r] = the recorded
    net unit-array delta keyed by (x,y,type,owner,order); model_after[r] =
    {storage_after, pend_after, slots_after} of the LAST in-mask base visit.
    tile=/new_order= are the RIVAL switches; gate_base= limits the model to
    ONE base (for the rivals' fit checks)."""
    rows = trace_rows(trace_path)
    befores = {r["r"]: r for r in rows if r.get("event") == "round_before"}
    afters = {r["r"]: r for r in rows if r.get("event") == "round_after"}
    rounds, created_by, recorded_by, model_after = [], {}, {}, {}
    for r in sorted(befores):
        rb = befores[r]
        after = afters[r]["snap"]
        before_units = rb["snap"]["units"]
        after_units = after["units"]
        recorded_by[r] = dict(units_net_delta(before_units, after_units))
        created = set()
        mstate = None
        for p in rb.get("predictions", []):
            if not p.get("in_mask"):
                continue
            if gate_base is not None and p.get("base") != gate_base:
                continue
            q = soq.Queue(slots=list(p["queue"]), pending=p["pending"])
            storage = p["minerals"]
            income = p["income"] if income_term else 0
            price = p["price"]
            res = visit(q, p["x"], p["y"], p["fac"], storage, income, price,
                        tile=tile, new_order=new_order)
            mstate = dict(storage_after=(res[1] if res[0] == "pay" else None),
                          pend_after=q.pending,
                          slots_after=list(q.slots[:5]))
            if res[0] == "pay":
                created.add((struct.unpack_from("<H", res[2], 0)[0],
                             struct.unpack_from("<H", res[2], 2)[0],
                             struct.unpack_from("<H", res[2], UNIT_TYPE)[0],
                             res[2][UNIT_OWNER], res[2][UNIT_ORDER]))
        created_by[r] = created
        model_after[r] = mstate
        rounds.append(r)
    return rounds, created_by, recorded_by, model_after


# --- written-image composition (the grow leg) --------------------------------
def compose_grown(sav_path, x, y, head, owner, new_order=ORDER_NEW):
    """Append ONE created record to the save's unit array and write the grown
    image: return (image_bytes, new_n_units). The state header's units-count
    dword and the appended record are the ONLY modeled changes (the B10
    founded-image shape, for units)."""
    from . import savewriter as sow
    sv = so.parse(sav_path)
    append = [create_record(x, y, head, owner, new_order=new_order)]
    img = sow.build_image(sv, append_units=append)
    return bytes(img), sv.n_units + len(append)


# --- module CLI ---------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(prog="sim.production")
    ap.add_argument("--sav", required=True, help="a .SAV (for the write leg)")
    ap.add_argument("--trace", required=True,
                    help="the recorded m56 golden trace (evidence/...)")
    ap.add_argument("--out", help="write the replay report JSON here")
    args = ap.parse_args(argv)
    rounds, created_by, recorded_by, model_after = replay(args.trace)
    img, n_units = compose_grown(args.sav, 29, 42, 2, 3)
    sha = hashlib.sha256(bytes(img)).hexdigest()[:16]
    report = {
        "rung": "B12",
        "rounds": rounds,
        "created_by_round": {str(k): sorted(v)
                             for k, v in created_by.items()},
        "recorded_delta_round0": {str(k): v for k, v in recorded_by.get(0, {}).items()},
        "created_r0": sorted(created_by.get(0, set())),
        "model_after_r0": model_after.get(0),
        "n_units_grown": n_units,
        "written_sha256": sha,
    }
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
