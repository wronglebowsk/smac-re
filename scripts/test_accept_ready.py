#!/usr/bin/env python3
"""Unit cases for accept_ready.decide() — no game, no /proc, pure function.

Each case is a shape the M61 session actually hit, or a shape the oracle must refuse.
A case failing here means the oracle would have sent a session down a dead end.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import accept_ready as A


def base(i=0, name="Korolev Center", minerals=0, credit=0, pending=0, price=9, head=2):
    return dict(i=i, name=name, x=0, y=0, minerals=minerals, credit=credit,
                pending=pending, head=head, price=price, horizon=[head, 0, 0, 0, 0, 0])


CASES = [
    #  name                          args                                     ready  must-mention
    ("accrues to the gate",        dict(bases=[base(minerals=3, credit=2, pending=1)]),            True,  "round(s)"),
    ("arrival in the first window", dict(bases=[base(minerals=8, credit=1, pending=1)]),            True,  "first window"),
    ("pending 0 is not UI-queued", dict(bases=[base(minerals=8, credit=1, pending=0)]),             False, "m57_ui_enqueue"),
    ("credit 0 cannot accrue",     dict(bases=[base(minerals=2, credit=0, pending=1)]),             False, "reload"),
    ("completion already armed",   dict(bases=[base(minerals=9, credit=2, pending=1)]),             False, "ARMED"),
    ("gdb attached",              dict(bases=[base(minerals=3, credit=2, pending=1)], gdb_n=1),      False, "m57_credit.py --stop"),
    ("evidence at the wall",       dict(bases=[base(minerals=3, credit=2, pending=1)], budget_mb=29.5), False, "audit"),
    ("no base of ours",            dict(bases=[]),                                                  False, "reload"),
    ("negative credit",            dict(bases=[base(minerals=2, credit=-1, pending=1)]),            False, "NEVER accrue"),
    ("one dead base, one live",    dict(bases=[base(minerals=0, credit=0, pending=1),
                                               base(i=18, name="University Base", minerals=5, credit=2, pending=1)]),
                                                                                                    True,  "University Base"),
    # the M61 killer: a modal over the BUILD pane, even on an otherwise perfect box
    ("dialog swallows clicks",     dict(bases=[base(minerals=8, credit=2, pending=1)], screen="dialog"),
                                                                                                    False, "Return"),
    ("open pane needs Escape",     dict(bases=[base(minerals=8, credit=2, pending=1)], screen="base"),
                                                                                                    False, "Escape"),
    ("hud does not block",         dict(bases=[base(minerals=8, credit=2, pending=1)], screen="hud"),
                                                                                                    True,  "first window"),
    ("tight horizon is flagged",   dict(bases=[base(minerals=1, credit=1, pending=1)], boundaries=5),
                                                                                                    True,  "TIGHT"),
    ("roomy horizon is not",       dict(bases=[base(minerals=1, credit=1, pending=1)], boundaries=20),
                                                                                                    True,  "round(s)"),
]

bad = 0
for name, kw, want, needle in CASES:
    r = A.decide(**kw)
    ok = (r["ready"] == want)
    blob = " ".join(r["reasons"]) + " " + (r.get("fix") or "")
    if ok and needle not in blob:
        ok = False
    if not ok:
        bad += 1
        print(f"BAD  {name}: ready={r['ready']} want={want} fix={r.get('fix')!r}")
print(f"PASS {len(CASES) - bad}/{len(CASES)} readiness cases" if not bad
      else f"FAIL {bad}/{len(CASES)} readiness cases")
sys.exit(1 if bad else 0)
