#!/usr/bin/env python3
"""M56/M59: the production PREDICTION rule, pinned by cases against a mock /proc/mem.

The rule (M59 restatement, 2026-10-26, static + one controlled poke):
  a unit ARRIVES at the round boundary iff
      the base is OURS (0x91b5b4; another faction's head slot is re-picked by its
      own visit at 0x4ef87e before its price gate, so its head is not predictable)
      AND queue head (base+0x50) is a unit type (0..0x3f)
      AND the owner is in the event mask (0x985b10)
      AND mineral storage (base+0x40) + this round's income >= price,
          price = cost_multiplier(owner) * type_cost(+41)
  PENDING (base+0x4c) IS NOT A TERM.  It gates only the POP (FUN_004ef5d0 returns
  at 0x4ef5f4 when pending == 0), which ADVANCES the queue: with pending 0 the head
  slot is never consumed, so the base keeps buying the same type whenever it can
  pay.  Measured by scripts/m59_head.py: Korolev Center pending 0 head 2, minerals
  poked 0 -> 9 (University Base untouched at 0) -> one turn later minerals 0, a
  type-2 unit on the base tile (5 -> 6), pending still 0, income 0 -> -1.
  (The pre-M59 rule required pending > 0; that is what made session 97's
  "unexplained arrival at pending 0" look impossible.)
  M58: cost_multiplier is FUN_004e40a0(owner,1,-1) RE-IMPLEMENTED and read live
  (mask 0x985b10 low byte, era table 0x68cbb8, difficulty scalars 0x92a294 / 0x92ada8,
  the government switch at 0x94d6a0+owner*0x20bc).  It is 10 only when [0x92ada8] >= 2;
  with [0x92ada8] == 1 — the current box — it is 9, which is the edi the tracer read at
  0x4efa52 twice.  The old "price = 10 * +41" was one game's difficulty state, not a rule.
  M57 refines the storage term: the queue processor runs inside the base visit AFTER
  the income add, so the storage it compares includes this round's income (+0xd0) —
  `predict(..., income_first=True)` is the UI-queued shape; the M56 armed run
  (storage poked to 100, income 0) is identical under both models.
  The progress accumulator (+0x3c) and the rate (+0xcc) do NOT gate it: the armed
  base had net income 0 and the unit arrived on the very next boundary with
  progress 32 < any accumulation model's requirement.

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

    def __init__(self, bases, costs, mask=0x0000fd08, era=2, a294=10, ada8=2,
                 era_table=(13, 12, 11, 10, 8, 7), our=3):
        blob = {}
        self.blob = blob
        def put(a, fmt, v):
            blob[a] = struct.pack(fmt, v)
        put(0x985AF4, "<I", len(bases))
        put(0x985B10, "<I", mask)
        # M59: predict() reads WHO WE ARE (0x91b5b4) to scope predictions to our own
        # bases — another faction's head slot is re-picked by its own visit at
        # 0x4ef87e (FUN_004e5ae0 -> FUN_004f6030 -> FUN_004e5560) BEFORE the price
        # gate, so its head at our snapshot is not the head its visit will price.
        put(0x91B5B4, "<I", our)
        put(0x985AEC, "<i", era)
        # M58: the price multiplier's inputs, served like the live image does.
        # Defaults are the session-56 game's state (docs/sessions/sessions-56-56.md:
        # 0x92a290/0x92a294 = 10/10, 0x92ada8 = 2, government field 0 -> x10 = 100%),
        # so every pre-M58 case keeps the numbers it had.  The era table is the
        # {13,12,11,10,8,7} of sessions-64-64.md.
        put(0x92A294, "<i", a294)
        put(0x92ADA8, "<i", ada8)
        for e, v in enumerate(era_table):
            put(B.ERA_TABLE + e * 4, "<i", v)
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
    check("head -30 -> no unit prediction at all (facility arrival is a bitmap, not a unit)",
          len(p) == 0, p)

    print("case 6: an out-mask owner is not floored (price model open) -> not predicted")
    mm = MockMem([base(0, fac=4, pending=1, queue=[2] + [B.EMPTY_S] * 9, minerals=500)],
                 {2: 1}, mask=0x0000fd08, our=4)
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

    print("case 12: M58 — [0x92ada8] == 1 rescales the multiplier 10 -> 9 (the live box)")
    mm = MockMem([base(0, pending=1, queue=[2] + [B.EMPTY_S] * 9, minerals=8, income=1)],
                 {2: 1}, ada8=1)
    p = B.predict(mm, B.all_prod(mm), income_first=True)
    check("ada8 1 -> factor 9, price 9, and 8 + income 1 ARRIVES (what the price-10 "
          "model printed as 'queue held — minerals 8 vs price 10')",
          len(p) == 1 and p[0]["factor"] == 9 and p[0]["price"] == 9
          and p[0]["predict_arrive"], p)

    print("case 13: ONE variable moved — ada8 0 vs 2 on an identical base")
    mm0 = MockMem([base(0, pending=1, queue=[2] + [B.EMPTY_S] * 9, minerals=7, income=1)],
                  {2: 1}, ada8=0)
    mm2 = MockMem([base(0, pending=1, queue=[2] + [B.EMPTY_S] * 9, minerals=7, income=1)],
                  {2: 1}, ada8=2)
    p0 = B.predict(mm0, B.all_prod(mm0), income_first=True)
    p2 = B.predict(mm2, B.all_prod(mm2), income_first=True)
    check("same minerals 7 + income 1: ada8 0 -> price 8 -> ARRIVE; ada8 2 -> price 10 "
          "-> not predicted",
          p0[0]["price"] == 8 and p0[0]["predict_arrive"]
          and p2[0]["price"] == 10 and not p2[0]["predict_arrive"], (p0, p2))

    print("case 14: M59 — PENDING IS NOT THE GATE. pending 0, head 2, minerals 9, "
          "ada8 1 -> price 9 -> ARRIVE (the pre-M59 rule predicted nothing)")
    mm = MockMem([base(0, pending=0, queue=[2] + [B.EMPTY_S] * 9, minerals=9, income=0)],
                 {2: 1}, ada8=1)
    p = B.predict(mm, B.all_prod(mm))
    check("pending 0 affordable head predicts the arrival, and no pop is expected",
          len(p) == 1 and p[0]["predict_arrive"] and p[0]["price"] == 9
          and p[0]["pending"] == 0 and p[0]["pop_expected"] is False, p)

    print("case 15: the M59 measured shape (scripts/m59_head.py): pending 0, head 2, "
          "minerals 8 + income 1 reaches price 9 only with income_first")
    mm = MockMem([base(0, pending=0, queue=[2] + [B.EMPTY_S] * 9, minerals=8, income=1)],
                 {2: 1}, ada8=1)
    p_no = B.predict(mm, B.all_prod(mm), income_first=False)
    p_yes = B.predict(mm, B.all_prod(mm), income_first=True)
    check("8 + 1 = 9 >= 9 -> ARRIVE under income_first, not under plain storage",
          not p_no[0]["predict_arrive"] and p_yes[0]["predict_arrive"], (p_no, p_yes))

    print("case 16: M59 scope — another faction's base is NOT predicted (its own visit "
          "re-picks its head at 0x4ef87e before its price gate)")
    mm = MockMem([base(0, fac=7, pending=1, queue=[2] + [B.EMPTY_S] * 9, minerals=500)],
                 {2: 1}, ada8=1)
    p = B.predict(mm, B.all_prod(mm))
    check("fac 7 base with our_player 3 -> no prediction row", len(p) == 0, p)

    print("case 17: ONE variable moved — pending 1 vs pending 0 on identical affordable "
          "bases: same arrival, only the pending one expects the pop")
    mm0 = MockMem([base(0, pending=0, queue=[2] + [B.EMPTY_S] * 9, minerals=9)], {2: 1}, ada8=1)
    mm1 = MockMem([base(0, pending=1, queue=[2] + [B.EMPTY_S] * 9, minerals=9)], {2: 1}, ada8=1)
    p0 = B.predict(mm0, B.all_prod(mm0))
    p1 = B.predict(mm1, B.all_prod(mm1))
    check("arrival identical, pop_expected 0 -> False, 1 -> True",
          p0[0]["predict_arrive"] == p1[0]["predict_arrive"] == True
          and p0[0]["pop_expected"] is False and p1[0]["pop_expected"] is True, (p0, p1))

    print()
    if FAILS:
        print(f"FAILED: {len(FAILS)} — {', '.join(FAILS)}")
        return 1
    print("PASS 17/17 production-prediction cases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
