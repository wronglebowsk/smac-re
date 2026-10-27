#!/usr/bin/env python3
"""M70: the brief's FIX — press Return until the screen reads 'hud'.

Prints one line per look: the classify() class, whether the status bar fired, and a
text head, so the dialog that was on screen is identifiable rather than silently cleared.
Stops as soon as accept_ready.screen_class() says 'hud'.
"""
import os, sys, time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import smac_play as P
import accept_ready as AR

P.WIN = P.find_window()
if not P.WIN:
    print("NO WINDOW")
    sys.exit(2)

MAX = int(os.environ.get("MAXRETURNS", "6"))
for i in range(MAX):
    kind, bar, txt = AR.look(tag="m70_fix")
    print(f"look {i}: class={kind} bar={'yes' if bar else 'no'} text={txt!r}", flush=True)
    if kind == "hud" or (bar and i > 0):
        print("READS hud")
        sys.exit(0)
    if kind not in ("dialog", "unknown"):
        print(f"NOT A DIALOG: class={kind!r} — do not keep pressing Return")
        sys.exit(1)
    P.key("Return")
    time.sleep(1.2)

kind, bar, txt = AR.look(tag="m70_fix")
print(f"after {MAX} Returns: class={kind} bar={'yes' if bar else 'no'} text={txt!r}")
sys.exit(0 if kind == "hud" else 1)
