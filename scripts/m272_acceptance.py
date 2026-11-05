#!/usr/bin/env python3
"""M272 acceptance gate - OFFLINE over the recorded evidence/m272w9.gdblog (no box time).

Re-parses the shipped log with the harness parser (whitelist fixed post-run: [LWP n exited] chatter
was the run's only unparsed residue) and asserts the milestone's numbers:
  STARTUP window: 7 CTRL events, all 0x5791c0 (process-start setup; ret 0x579eaf) -> the bp
  machinery is LIVE; 0 GEN events (the generator had already run before the attach - not a claim).
  LOAD window (validity: ROUND sentinel -39 -> 50 read back, counts == the m104 image):
  2 CTRL events - the .SAV opener FUN_00597ee0 (ret 0x5992f2) AT round=-39 (inside MY sentinel,
  so the load opened the file with the poke live), then the read wrapper 0x64cc00 CONDITIONED on
  dest 0x927590 (the 8x1436 faction array) at round=50, ret 0x596edb = inside FUN_00596850 -
  the in-place .SAV body loader IS the restore path (the M106 chain, live);
  0 events at the generator, its 4 call sites, and all 4 caller entries => NO, FUN_0057ecf0 does
  NOT run on a LOAD (and neither do FUN_005b2970 / FUN_0057c550).
Window offsets (arm@660, ready@1404) are the byte offsets the live harness recorded in its run.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import m272_gen_load_watch as H  # noqa: E402

ROOT = os.path.dirname(HERE)
LOG = os.path.join(ROOT, "evidence", "m272w9.gdblog")
ARM_OFF, READY_OFF = 660, 1404

text = open(LOG, "r", errors="replace").read()
ev, bad = H.parse(text)
boot = [e for e in ev if ARM_OFF <= e["_off"] < READY_OFF]
load = [e for e in ev if e["_off"] >= READY_OFF]
gates = []


def gate(name, ok, detail):
    gates.append((name, bool(ok), detail))


gate("G1-parser-clean", not bad, "%d unparsed %s" % (len(bad), bad[:3]))
gate("G2-startup-7-setup-ctrl", len(boot) == 7 and all(
    e["kind"] == "CTRL" and e["pc"] == 0x5791c0 and e["ret"] == 0x579eaf for e in boot),
     "%d STARTUP events: %s" % (len(boot), sorted({(e["kind"], hex(e["pc"]), hex(e["ret"]))
                                                   for e in boot})))
gate("G3-load-window-controls", len(load) == 2
     and (load[0]["pc"], load[0]["ret"], load[0]["round"]) == (0x597ee0, 0x5992f2, -39)
     and (load[1]["pc"], load[1]["ret"], load[1]["round"]) == (0x64cc00, 0x596edb, 50),
     "LOAD events: %s" % [(e["kind"], hex(e["pc"]), hex(e["ret"]), e["round"]) for e in load])
watched = set(H.ENTRIES) | set(H.SITES)
gate("G4-zero-gen-or-caller-events", not [e for e in ev if e["pc"] in watched],
     "0 events at GEN+4 callers+4 sites across both windows (of %d total)" % len(ev))
gate("G5-total-9-events", len(ev) == 9, "%d parsed events" % len(ev))
print("ACCEPTANCE M272 %s %d/%d" % ("PASS" if all(o for _, o, _ in gates) else "FAIL",
                                    sum(1 for _, o, _ in gates if o), len(gates)))
for name, ok, detail in gates:
    print("  %-28s %s  %s" % (name, "PASS" if ok else "FAIL", detail))
sys.exit(0 if all(o for _, o, _ in gates) else 1)
