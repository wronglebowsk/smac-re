#!/usr/bin/env python3
"""One-shot screen probe for the SMAC Wine harness — see what the driver would DO.

Prints classify()'s verdict for the CURRENT screen plus the OCR words (with coords),
without touching the game. This is the tool the C2 falsification test needed: the last
session the game process vanished right after the driver started, and the only way to
tell "the classifier doesn't know a loaded-save HUD" from "the game crashed" is to ask
the classifier directly, before it acts.

Usage:
  python3 scripts/smac_probe.py                 # verdict + words for the live screen
  python3 scripts/smac_probe.py --tag m15       # also save evidence/m15_screen.png
  python3 scripts/smac_probe.py --watch 10      # verdict every ~2 s for 30 s
  python3 scripts/smac_probe.py --click 610,344 # click first (windowfocus handled)
  python3 scripts/smac_probe.py --key Return    # key first (needs focus; smac_play does it)
"""
import argparse, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P    # reuse the verified capture/OCR/classify pipeline


def probe(tag="probe"):
    png = P.freeze(tag)
    words = P.ocr_fast(png)
    nc = P.region_colors(png)
    kind = P.classify(words, nc, png)
    return png, words, nc, kind


def show(png, words, nc, kind, save=None):
    print(f"screen={kind}  ncolors={nc}  words={len(words)}  png={png}")
    for t, cx, cy, w, h in words:
        print(f"  {t!r:26s} x={cx:6.1f} y={cy:6.1f} w={w:5.1f} h={h:5.1f}")
    if save:
        os.makedirs(os.path.dirname(save), exist_ok=True)
        import shutil
        shutil.copy(png, save)
        print(f"saved: {save}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="probe")
    ap.add_argument("--save", default=None, help="copy the png here")
    ap.add_argument("--watch", type=int, default=0, help="N probes, ~2 s apart")
    ap.add_argument("--click", default=None, help="x,y before probing")
    ap.add_argument("--key", default=None)
    ap.add_argument("--quiet", action="store_true", help="verdict only, no word dump")
    a = ap.parse_args()

    P.WIN = P.find_window()
    if not P.WIN:
        sys.exit("game window not found")
    if a.click:
        x, y = (int(v) for v in a.click.split(","))
        P.click((x, y)); print(f"clicked ({x},{y})"); time.sleep(1.0)
    if a.key:
        P.key(a.key); print(f"key {a.key}"); time.sleep(1.0)

    n = max(1, a.watch)
    for i in range(n):
        png, words, nc, kind = probe(a.tag if n == 1 else f"{a.tag}{i}")
        print(f"[{time.strftime('%H:%M:%S')}]", end=" ")
        if a.quiet:
            print(f"screen={kind} ncolors={nc} words={len(words)} png={png}")
        else:
            show(png, words, nc, kind, save=a.save if i == 0 else None)
        if i < n - 1:
            time.sleep(2.0)


if __name__ == "__main__":
    main()
