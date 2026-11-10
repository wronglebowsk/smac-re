"""sim.basefound - rung B10: the M282 base-array ledger (founder and destroyer) and
the golden n_bases curve pairing on the B3 turn engine.

Founder/destroyer semantics are M282's census result:
  founder   FUN_004e47d0(faction, x, y) - the ONLY live base-array creator.  Guard
            count less than 0x200 (512 slots); a new 304-B record is appended at
            array start + old_count*0x130 (x u16 at +0, y u16 at +2, faction bytes
            at +4 and +5); count = count + 1 at 0x4e484a.  The per-faction counter
            DAT_0094e488[faction * 0x82f] += 1 rides the same body.
  destroyer FUN_004e4e10 - count-1 at 0x4e515d with COMPACTION: the LAST record is
            moved into the freed slot (the m46e "base array reorders during a
            watch" law).
The ledger is a mutable record list in the same shape sim.save reads
(own4/fac/x/y - own4 and fac are separate bytes: a captured base differs),
so a founded record reads exactly like a loaded one and savewriter (rung B8)
can write a grown ledger back to a .SAV image.

The pairing presses the B3 engine the recorded trace's own turn count and applies
the trace's OWN per-turn n_bases delta (derived from the rows, never hardcoded)
through the founder/destroyer between presses.  Rung B9 proved the no-leg shape
keeps n_bases const at the save's count; this rung is the leg that makes the
recorded 18-to-26 growth recoverable, with the -1 at turn 23 running through the
destroyer (recorded events: t8 +1, t9 +1, t17 +1, t22 +2, t23 -1, t27 +1, t32 +2,
t34 +1).  Faction and coordinates for each founding are ASSUMED (fewest-bases AI
faction, first unoccupied in-bounds tile): the trace records n_bases only, and the
and the dispatch question was later CLOSED by M289/M290 (merged #241/#242: the HUB vector, own-tile-gated, founder args = the pod record); these two rules remain placeholders inside this rung - the executable law is sim/hubfound.py (rung B13).

No /proc, no gdb, no Wine.  Deterministic: two runs give identical report sha256.
"""
import argparse
import hashlib
import json
import os
import struct
import sys
from collections import Counter

from . import save as sosave
from . import turn as soturn

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_TRACE = os.path.join(ROOT, "evidence",
                             "trace_m54b40b_20261024_212833.jsonl")

BASE_LEN = sosave.BASE_LEN          # 304 = 0x130 (the M282 record stride)
CAP = 0x200                         # 512 slots (M282 G1/G6)
X_OFF, Y_OFF = 0, 2
FAC_OFF = 4                         # faction bytes at +4/+5 (M282 G2)


def record_bytes(d):
    """The 304-B record bytes M282's founder writes: x u16 +0, y u16 +2,
    faction bytes +4/+5, everything else zero."""
    rec = bytearray(BASE_LEN)
    struct.pack_into("<H", rec, X_OFF, int(d["x"]) % 0x10000)
    struct.pack_into("<H", rec, Y_OFF, int(d["y"]) % 0x10000)
    rec[FAC_OFF] = d["own4"] % 256
    rec[FAC_OFF + 1] = d["fac"] % 256
    return bytes(rec)


class Ledger:
    """The mutable base-record array (DAT_0095da10 + DAT_00985af4)."""
    def __init__(self, records=None):
        self.records = list(records) if records is not None else []

    def __len__(self):
        return len(self.records)

    def found(self, faction, x, y):
        """FUN_004e47d0: append a fresh (faction, x, y) record; the 0x200 guard
        REFUSES a founding past the cap.  Returns True iff the record landed."""
        if len(self.records) >= CAP:
            return False
        self.records.append({"own4": int(faction) % 256, "fac": int(faction) % 256,
                             "x": int(x), "y": int(y)})
        return True

    def destroy(self, k):
        """FUN_004e4e10: compaction - the LAST record moves into the freed slot,
        count-1.  Returns the moved record (None if refused)."""
        if not 0 <= k < len(self.records):
            return None
        moved = self.records[-1]
        self.records[k] = moved
        self.records.pop()
        return moved


def from_save(sv):
    """Seed the ledger from a loaded save's base records (same shape)."""
    return Ledger([{"own4": b["own4"], "fac": b["fac"], "x": b["x"], "y": b["y"]}
                   for b in sv.bases])


def events_from_trace(path):
    """Per-turn n_bases deltas from the recorded rows (never hardcoded)."""
    ev = {}
    with open(path) as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("type") == "start":
                continue
            d = r["state_after"]["n_bases"] - r["state_before"]["n_bases"]
            if d:
                ev[r["turn"]] = d
    return ev


def _ai_faction(led, human):
    """ASSUMED: the AI faction with the fewest bases (ties: lowest id)."""
    tall = Counter(r["fac"] for r in led.records)
    return min((f for f in range(8) if f != human),
               key=lambda f: (tall.get(f, 0), f))


def _tile(led, w, h):
    """ASSUMED placeholder: the first in-bounds tile no base occupies
    (row-major).  M290 REFUTED this as the real rule (the recorded foundings
    rank 542-1691 of 2146 unoccupied land tiles in this order; the founding
    tile is the POD's tile - see sim/hubfound.py, rung B13).  Kept so rung
    B10's recorded curve acceptance stays reproducible."""
    occ = {(r["x"], r["y"]) for r in led.records}
    for x in range(1, w - 1):
        for y in range(1, h - 1):
            if (x, y) not in occ:
                return x, y
    return 0, 0


def pair(sav_path, trace_path, apply_events=True, schedule=None):
    """Press the B3 engine the trace's turn count; between presses apply the
    recorded per-turn delta through the founder/destroyer.  Returns
    (sv, engine, ledger, report, blob)."""
    sv = sosave.parse(sav_path)
    rows = [json.loads(l) for l in open(trace_path)]
    turns = len(rows) - 1
    ev = events_from_trace(trace_path) if schedule is None else dict(schedule)
    eng = soturn.Engine(sv.year, human=sv.own_player)
    led = from_save(sv)
    snaps = []
    for tr in rows[1:]:
        t = tr["turn"]
        d = ev.get(t, 0)
        if apply_events:
            for _ in range(abs(d)):
                if d > 0:
                    fx, fy = _tile(led, sv.width, sv.height)
                    led.found(_ai_faction(led, sv.own_player), fx, fy)
                else:
                    led.destroy(len(led) - 1)
        eng.press()
        snaps.append((t, tr["state_after"]["n_bases"], len(led)))
    report = {"events": ev,
              "snapshots": snaps,
              "final": {"recorded": rows[-1]["state_after"]["n_bases"],
                        "model": len(led)},
              "year": eng.year, "turns": turns}
    return sv, eng, led, report, json.dumps(report, sort_keys=True)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sim.basefound")
    ap.add_argument("--sav", required=True)
    ap.add_argument("--trace", default=DEFAULT_TRACE)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-events", action="store_true")
    a = ap.parse_args(argv)
    sv, eng, led, report, blob = pair(a.sav, a.trace, apply_events=not a.no_events)
    with open(a.out, "w") as fh:
        fh.write(blob + "\n")
    print("events %s | final recorded %d model %d | year %d | sha256 %s"
          % (report["events"], report["final"]["recorded"],
             report["final"]["model"], eng.year,
             hashlib.sha256(blob.encode()).hexdigest()[:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
