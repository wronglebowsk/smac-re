#!/usr/bin/env python3
"""M56: the production PREDICTION rule, pinned by cases against a mock /proc/mem.

The rule (settled by the 2026-10-25 controlled poke, base 17 Korolev Center):
  a unit ARRIVES at the round boundary iff
      pending (base+0x4c) > 0
      AND queue head (base+0x50) is a unit type (0..0x3f)
      AND the owner is in the event mask (0x985b10)
      AND mineral storage (base+0x40) >= price, price = 10 * type_cost(+41)
  M57 refines the last term: the queue processor runs inside the base visit AFTER the
  income add, so the storage it compares includes this round's income (+0xd0) —
  `predict(..., income_first=True)` is the UI-queued shape; the M56 armed run
  (storage poked to 100, income 0) is identical under both models.
  The progress accumulator (+0x3c) and the rate (+0xcc) do NOT gate it: the armed
  base had net income 0 and the unit arrived on the very next boundary with
  progress 32 < any accumulation model's requirement. An empty queue (pending 0,
  head -38) predicts NOTHING — that is why seven war rounds built nothing.

    python3 scripts/test_m56_predict.py
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m56_build as B  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ok  {name}")
    else:
        print(f"  BAD {name} {detail}")
        FAILS.append(name)


class MockMem:
    """Serves exactly the addresses m56_build reads, from a tiny sparse map."""

    def __init__(self, bases, costs, mask=0x0000fd08, era=2):
        blob = {}
        self.blob = blob
        def put(a, fmt, v):
            blob[a] = struct.pack(fmt, v)
        put(0x985AF4, "<I", len(bases))
        put(0x985B10, "<I", mask)
        put(0x985AEC, "<i", era)
        for t, c in costs.items():
            blob[B.TYPE_ARR + t * B.TYPE_STRIDE + 41] = bytes([c])
        for i, b in enumerate(bases):
            rec = bytearray(304)
            rec[0:2] = struct.pack("<H", b["x"]); rec[2:4] = struct.pack("<H", b["y"])
            rec[4] = b["fac"]
            rec[19:51] = b.get("name", "Base").encode("latin-1")[:32] + b"\0"
            struct.pack_into("<i", rec, 0x4c, b.get("pending", 0))
            for k in range(10):
                struct.pack_into("<i", rec, 0x50 + 4 * k,
                                 b.get("queue", [B.EMPTY_S] * 10)[k]
                                 if k < len(b.get("queue", [])) else B.EMPTY_S)
            struct.pack_into("<i", rec, 0x40, b.get("minerals", 0))
            struct.pack_into("<i", rec, 0x3c, b.get("progress", 0))
            struct.pack_into("<i", rec, 0xcc, b.get("rate", 0))
            struct.pack_into("<i", rec, 0xd0, b.get("income", 0))
            self.blob[B.BASE_ARR + b["i"] * B.BASE_SZ] = bytes(rec)
        self.blob = blob

    def seek(self, a): self.pos = a

    def read(self, n):
        out = bytearray()
        pos = self.pos
        while len(out) < n:
            chunk = self.blob.get(pos)
            if chunk is not None:
                out += chunk
                pos += len(chunk)
            else:
                out += b"\0"; pos += 1
        return bytes(out[:n])


def base(i, x=29, y=42, fac=3, **kw):
    return dict(i=i, x=x, y=y, fac=fac, **kw)


def main():
    print("case 1: the natural state — pending 0, head -38 everywhere -> no predictions")
    mm = MockMem([base(0, pending=0, queue=[B.EMPTY_S] * 10, minerals=0, income=0),
                  base(1, x=52, y=12, fac=7, pending=0, queue=[B.EMPTY_S] * 10)], {2: 1})
    preds = B.predict(mm, B.all_prod(mm))
    check("empty queues predict nothing", preds == [], preds)

    print("case 2: the controlled-poke shape — pending 1, head 2, minerals 100 >= 10 -> ARRIVE")
    mm = MockMem([base(0, pending=1, queue=[2] + [B.EMPTY_S] * 9, minerals=100,
                       progress=32, rate=1, income=0)], {2: 1})
    p = B.predict(mm, B.all_prod(mm))
    check("armed base predicts arrival", len(p) == 1 and p[0]["predict_arrive"]
          and p[0]["price"] == 10 and p[0]["unit_type"] == 2, p)

    print("case 3: minerals below price -> no arrival predicted (gate 0x4f0a3d)")
    mm = MockMem([base(0, pending=1, queue=[2] + [B.EMPTY_S] * 9, minerals=9,
                       progress=99, rate=5, income=0)], {2: 1})
    p = B.predict(mm, B.all_prod(mm))
    check("9 minerals < price 10 -> not predicted even with progress 99",
          len(p) == 1 and not p[0]["predict_arrive"], p)

    print("case 4: progress/rate do NOT gate — minerals 10, progress 0, rate 0 -> ARRIVE")
    mm = MockMem([base(0, pending=1, queue=[2] + [B.EMPTY_S] * 9, minerals=10,
                       progress=0, rate=0, income=0)], {2: 1})
    p = B.predict(mm, B.all_prod(mm))
    check("minerals == price -> predicted (>=, not >)",
          len(p) == 1 and p[0]["predict_arrive"], p)

    print("case 5: a non-unit head (facility/project id < 0) predicts no UNIT")
    mm = MockMem([base(0, pending=1, queue=[-30] + [B.EMPTY_S] * 9, minerals=500)], {2: 1})
    p = B.predict(mm, B.all_prod(mm))
    check("head -30 -> predict_arrive False (facility arrival is a bitmap, not a unit)",
          len(p) == 1 and not p[0]["predict_arrive"] and p[0]["unit_type"] is None, p)

    print("case 6: an out-mask owner is not floored (price model open) -> not predicted")
    mm = MockMem([base(0, fac=4, pending=1, queue=[2] + [B.EMPTY_S] * 9, minerals=500)],
                 {2: 1}, mask=0x0000fd08)
    p = B.predict(mm, B.all_prod(mm))
    check("fac 4 out of mask 0xfd08 -> predict_arrive False",
          len(p) == 1 and not p[0]["predict_arrive"] and not p[0]["in_mask"], p)

    print("case 7: price scales with the type cost (alpha #UNITS +41)")
    mm = MockMem([base(0, pending=1, queue=[3] + [B.EMPTY_S] * 9, minerals=29),
                  base(1, x=10, y=10, pending=1, queue=[3] + [B.EMPTY_S] * 9, minerals=30)],
                 {3: 3})
    p = B.predict(mm, B.all_prod(mm))
    check("cost 3 -> price 30: 29 minerals no, 30 minerals yes",
          len(p) == 2 and not p[0]["predict_arrive"] and p[1]["predict_arrive"], p)

    print("case 8: pending > 1 queues more than one arrival over successive boundaries "
          "(the predictor re-reads the fields every round)")
    mm = MockMem([base(0, pending=3, queue=[2, 2, 2] + [B.EMPTY_S] * 7, minerals=100)], {2: 1})
    p = B.predict(mm, B.all_prod(mm))
    check("one prediction per base per round (pending 3 -> this round: 1 arrival)",
          len(p) == 1 and p[0]["predict_arrive"] and p[0]["pending"] == 3, p)

    print("case 9: M57 — the gate compares storage AFTER the income add (income_first)")
    mm = MockMem([base(0, pending=1, queue=[2] + [B.EMPTY_S] * 9, minerals=8, income=2)], {2: 1})
    p_no = B.predict(mm, B.all_prod(mm), income_first=False)
    p_yes = B.predict(mm, B.all_prod(mm), income_first=True)
    check("minerals 8 + income 2 = 10 >= price 10 -> ARRIVE only when income_first",
          len(p_no) == 1 and not p_no[0]["predict_arrive"]
          and len(p_yes) == 1 and p_yes[0]["predict_arrive"], (p_no, p_yes))

    print("case 10: income_first is not a licence — 8 + 1 = 9 < 10 still predicts nothing")
    mm = MockMem([base(0, pending=1, queue=[2] + [B.EMPTY_S] * 9, minerals=8, income=1)], {2: 1})
    p = B.predict(mm, B.all_prod(mm), income_first=True)
    check("8 + 1 < 10 -> not predicted", len(p) == 1 and not p[0]["predict_arrive"], p)

    print("case 11: the M56 armed shape is unchanged by the new flag (regression)")
    mm = MockMem([base(0, pending=1, queue=[2] + [B.EMPTY_S] * 9, minerals=100, income=0)], {2: 1})
    p0 = B.predict(mm, B.all_prod(mm), income_first=False)
    p1 = B.predict(mm, B.all_prod(mm), income_first=True)
    check("minerals 100, income 0 -> ARRIVE under both models",
          p0[0]["predict_arrive"] and p1[0]["predict_arrive"], (p0, p1))

    print()
    if FAILS:
        print(f"FAILED: {len(FAILS)} — {', '.join(FAILS)}")
        return 1
    print("PASS 11/11 production-prediction cases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
