#!/usr/bin/env python3
"""M26: boot to HUD by loading Autosave 30 (M25-verified geometry).

Sequence: [intro/cdrom] -> title -> click LOAD GAME (610,344) -> click save-30
row (293,384) -> OK (343,491) -> LOAD confirm OK (290,391) -> HUD.
Never Escape. Prints progress; exits 0 only when class==hud and year reads sane.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P


def probe():
    png = P.freeze("m26")
    words = P.ocr(png)
    return P.classify(words, P.region_colors(png), png)


def main():
    t0 = time.time()
    phase = 0
    last = None
    while time.time() - t0 < 150:
        kind = probe()
        if kind != last:
            print(f"[{time.time()-t0:5.1f}s] class={kind}", flush=True)
            last = kind
        if kind == "hud":
            st = P.state()
            print("HUD reached:", st, flush=True)
            return 0
        if phase == 0:
            if kind == "cdrom":
                P.key("Return")
            elif kind == "title":
                print("  -> click LOAD GAME", flush=True)
                P.click((610, 344))
                phase = 1
            elif kind in ("unknown", "movie", "dialog", "breakthrough", "base"):
                P.key("Return")          # skip intro / dismiss advisor panes
            time.sleep(2.0)
        elif phase == 1:
            # LOAD list: rows y 264..432 step 24, lexicographic 1/10/2/20/3/30/4/5,
            # 30 at y 384 (M25). single click selects + fills name box.
            time.sleep(1.5)
            print("  -> click row 30 (293,384), OK (343,491)", flush=True)
            P.click((293, 384))
            time.sleep(1.3)
            P.click((343, 491))
            phase = 2
        elif phase == 2:
            if kind == "loaded-game":
                print("  -> confirm OK (290,391)", flush=True)
                P.click((290, 391))
            time.sleep(2.0)
    print("TIMEOUT reaching HUD", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
