#!/usr/bin/env python3
"""M64: run-layer fixtures for the ARRIVAL-ATTRIBUTION rule, built from real traces.

M61 built its pair (scratch/m61/fixture_defer_ok.json, scratch/m61/fixture_beat_visit.json)
from the PASS trace evidence/trace_m56_build_20261026_160325.jsonl and made ds:0x8f0d60
— the current-base pointer — the ONLY difference between them: pointer names another base
-> the deferral is attributed; pointer names THIS base -> a model gap, run must FAIL.

Session 103 measured that the pointer is not evidence.  evidence/trace_m56_build_20261026_182354.jsonl
r7: Korolev Center paid 7 -> 0 (7 + income 2 - price 9 = 0) with ds:0x8f0d60 naming
Korolev Center and 2 of our units on (29,42), while r8's before-snapshot — the SAME ROUND
read later, y2159 rnd59 — has 3 on the tile.  M64 therefore attributes by the PAYMENT
(PAY 0x4efedd and CREATE 0x4eff4e are one visit invocation, evidence/m61a_seq.jsonl) and
requires the unit to READ BACK, so the old pair's discriminator is gone: under the new
rule the original beat_visit PASSES, because its payment is visible and its unit reads
back at r1's before-snapshot.  That is reported, not hidden.

What this writes (scratch/ is gitignored; this script is the artifact):

  scratch/m64/fixture_paid_readback.json     must exit 0
      r7 + r8 of evidence/trace_m56_build_20261026_182354.jsonl VERBATIM — the exact
      window pair session 103's run 3 failed on: Korolev Center predicted (minerals 7
      + income 2 = gate 9 >= price 9), paid (storage 0 at the r7 after-snapshot), no
      unit in that read, the unit present at r8's before-snapshot.
  scratch/m64/fixture_paid_no_readback.json  must exit 1
      the same two windows, ONE variable: the unit Korolev paid for is absent from
      EVERY read (r7-after, r8-before, r8-after).  The payment is still visible, so a
      paid window whose unit never reads back is the guard-suppressed shape, not a race.
  scratch/m61/fixture_beat_visit.json        must exit 1 (rebuilt in place, same path,
      same expectation, new discriminator)
      r0 + r1 of evidence/trace_m56_build_20261026_160325.jsonl with Korolev's paid
      unit absent from every read; the pointer still names Korolev Center, and that is
      now decoration — the surviving distinction is the read-back.

  python3 scripts/m64_mkfixture.py
"""
import copy, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def events(path):
    ev = {}
    with open(os.path.join(ROOT, path)) as fh:
        for line in fh:
            d = json.loads(line)
            ev.setdefault(d["event"], []).append(d)
    return ev


def pick(lst, r):
    for x in lst:
        if x["r"] == r:
            return x
    raise SystemExit(f"no row for r={r}")


def window(ev, r):
    """One boundary window, copied verbatim out of a recorded run."""
    b, a = pick(ev["round_before"], r), pick(ev["round_after"], r)
    tl = [x for x in ev.get("timeline", []) if x["r"] == r]
    return dict(r=r, before=copy.deepcopy(b["snap"]), prod_before=copy.deepcopy(b["prod"]),
                predictions=copy.deepcopy(b["predictions"]),
                after=copy.deepcopy(a["snap"]), prod_after=copy.deepcopy(a["prod"]),
                timeline=copy.deepcopy(tl[0]["rows"]) if tl else [],
                cur_base_after=copy.deepcopy(a.get("cur_base")))


def produced_unit(ev, r_lo, r_hi, tile, owner, utype):
    """The freshly produced record: the order-0 unit on `tile` whose key-count grew
    between the two reads.  NOT an index lookup — the unit array compacts between reads
    (measured in evidence/trace_m56_build_20261026_182354.jsonl: the two Korolev garrisons
    read idx 54/62 at r7-before, 53/61 at r7-after and 52/60/73 at r8-after, because 7
    records died in the round), and the driver's `h` re-orders the produced unit from 0
    to 2, so neither idx nor order survives a read."""
    key = (tile[0], tile[1], utype, owner)
    def cnt(s):
        return sum(1 for u in s["units"] if (u["x"], u["y"], u["type"], u["owner"]) == key)
    hi = pick(ev["round_before"], r_hi)["snap"]
    cands = [u for u in hi["units"]
             if (u["x"], u["y"], u["type"], u["owner"]) == key and u["order"] == 0]
    assert cnt(hi) > cnt(pick(ev["round_before"], r_lo)["snap"]), "no growth"
    assert len(cands) == 1, [u["idx"] for u in cands]
    return cands[0], key


def trim_key(rd, side, key, keep):
    """Drop this key's records down to `keep` — the produced unit, preferring the
    order-0 record (a produced unit arrives order 0; M55 #5 cargo arrives nonzero)."""
    us = rd[side]["units"]
    removed = 0
    while sum(1 for u in us if (u["x"], u["y"], u["type"], u["owner"]) == key) > keep:
        for i, u in enumerate(us):
            k = (u["x"], u["y"], u["type"], u["owner"])
            if k == key and u["order"] == 0:
                del us[i]; removed += 1; break
        else:
            for i, u in enumerate(us):
                if (u["x"], u["y"], u["type"], u["owner"]) == key:
                    del us[i]; removed += 1; break
    return removed


def count_key(snap, key):
    return sum(1 for u in snap["units"] if (u["x"], u["y"], u["type"], u["owner"]) == key)


def write(path, fx):
    p = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as fh:
        json.dump(fx, fh)
    return p


def main():
    # 1 + 2: the measured run-3 pair, and the same pair with the read-back removed.
    T3 = "evidence/trace_m56_build_20261026_182354.jsonl"
    ev3 = events(T3)
    ui3 = copy.deepcopy(ev3["ui_queue"][0])
    empty3 = bool(ev3["natural_state"][0]["all_queues_empty"])
    produced, key = produced_unit(ev3, 7, 8, (29, 42), 3, 2)
    keep3 = count_key(pick(ev3["round_before"], 7)["snap"], key)

    p1 = write("scratch/m64/fixture_paid_readback.json",
               dict(natural_queues_empty=empty3, armed=None, ui_queue=ui3, writes=0,
                    rounds=[window(ev3, 7), window(ev3, 8)]))
    rd7, rd8 = window(ev3, 7), window(ev3, 8)
    cut3 = [(rd7, "after"), (rd8, "before"), (rd8, "after")]
    rm3 = [trim_key(rd, side, key, keep3) for rd, side in cut3]
    p2 = write("scratch/m64/fixture_paid_no_readback.json",
               dict(natural_queues_empty=empty3, armed=None, ui_queue=ui3, writes=0,
                    rounds=[rd7, rd8]))

    # 3: M61's beat_visit, rebuilt so its single variable is the read-back.
    T16 = "evidence/trace_m56_build_20261026_160325.jsonl"
    ev16 = events(T16)
    produced16, key16 = produced_unit(ev16, 0, 1, (29, 42), 3, 2)
    keep16 = count_key(pick(ev16["round_before"], 0)["snap"], key16)
    rd0, rd1 = window(ev16, 0), window(ev16, 1)
    rm16 = [trim_key(rd0, "after", key16, keep16), trim_key(rd1, "before", key16, keep16),
            trim_key(rd1, "after", key16, keep16)]
    fx16 = dict(natural_queues_empty=False, armed=None, writes=0, rounds=[rd0, rd1])
    if ev16.get("ui_queue"):
        fx16["ui_queue"] = copy.deepcopy(ev16["ui_queue"][0])
    p3 = write("scratch/m61/fixture_beat_visit.json", fx16)

    cuts3 = {f"r{rd['r']}:{side}": n for (rd, side), n in zip(cut3, rm3)}
    print(f"{T3}: produced unit idx {produced['idx']} key {key} order {produced['order']}; "
          f"key-count without it {keep3}; records removed per read {cuts3}")
    print(f"{T16}: produced unit idx {produced16['idx']} key {key16}; key-count without it "
          f"{keep16}; records removed {rm16}")
    print(f"beat_visit r0 cur_base_after (kept, decoration now): "
          f"{(rd0.get('cur_base_after') or {}).get('name')}")
    for p in (p1, p2, p3):
        print("wrote", os.path.relpath(p, ROOT))


if __name__ == "__main__":
    main()
