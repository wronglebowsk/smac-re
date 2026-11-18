#!/usr/bin/env python3
"""sim.composedlive - rung B24: the queue leg visits a base FOUNDED BY THE FOUNDER
LEG IN THE WRITTEN CONTAINER.

SKELETON (authored before probing, per the loop's branch-then-probe law). The
rung text is BUILD_SPINE.md **B24**; the gates below are the claims it must
print, and NOTHING is measured yet — this file prints no PASS until implemented.

Composition (all laws already landed; nothing here re-derives a rule):
  * the founder/destroyer op stream + B21's log-driven turn schedule
    (sim/composedrun.py: op_stream / feasible_schedules / press_run);
  * the record bytes the founder writes (sim/basefound.py record_bytes, M282)
    and B22's one-writer both-array growth (sim/composedgrowth.py,
    sim/savewriter.build_image);
  * the per-boundary queue visit law and the container fold
    (sim/composedturn.py B23; sim/queue.py B11; sim/production.py B12);
  * the compaction law: destroyer moves the LAST record into the freed slot
    (M282; NAMED B10/B13).

The load-bearing interface: the visited base is NOT Korolev and NOT in the save.
It is the record WRITTEN INTO THE IMAGE by a logged FOUND (fac=1 (27,29) in
evidence/m289_gdb_raw.log) — found BEFORE op8 DESTROY (18)->19, which compacts
whatever last record there is into the freed slot. At every later boundary the
fold must read its queue inputs from the RELOADED image at the record's
POST-COMPACTION position, and the completion's unit record must carry that
base's tile/owner read out of the container. A fold that keeps the model's
in-memory index visits the wrong base after the destroy and the arrival carries
a different tile — that is what makes this rung's falsifier non-vacuous.

python3 -m sim.selftest --b24 <sav>   relays compute(); no box, no /proc.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def compute(sav_path):
    raise SystemExit("B24: not implemented yet (skeleton)")


def acceptance(sav_path, results):
    raise SystemExit("B24: not implemented yet (skeleton)")


if __name__ == "__main__":
    raise SystemExit("B24: not implemented yet (skeleton)")
