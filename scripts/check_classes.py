#!/usr/bin/env python3
"""Offline classifier regression: run classify() over saved evidence frames.

No game needed — tesseract on a saved PNG is deterministic, so this is the cheap way to
prove a new screen class fires on the frame that motivated it AND that the old classes
still classify their own frames the same way.

Usage: python3 scripts/check_classes.py [frame.png=expected ...]
Default frames are the M14 evidence set in evidence/.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "evidence")

DEFAULT = [
    # the frame,            expected class,  why this frame exists
    ("m15_boot.png",            "cdrom",       "CD-ROM nag (title in its caption) — was `title`"),
    ("m15_loaded_words.png",    "loaded-game", "LOAD confirm pane over title art — was `unknown`"),
    ("m15_hud.png",             "hud",         "live HUD after answering that pane"),
    ("m15_stuck_screen.png",    "dialog",      "OPERATIONS DIRECTOR WITH ARTWORK — was `hud`"),
    ("m15_mainmenu.png",        "unknown",     "main menu: unchanged, still unknown (not clickable)"),
    ("m15_autolist.png",        "unknown",     "LOAD file browser: unchanged"),
    ("m54a/live_hud.png",       "hud",         "M54a: HUD whose message pane prints 'nutrients' (355,438) — was `base`, so TURN COMPLETE was never clicked"),
    ("m45a_post.png",           "base",        "real base screen: MENU/tabs, no TURN COMPLETE row — must STAY base (Escape, never click)"),
    ("m25_t7.png",              "hud",         "plain HUD, TURN COMPLETE at (697,416)"),
]


def main():
    frames = DEFAULT
    if len(sys.argv) > 1:
        frames = []
        for spec in sys.argv[1:]:
            f, want = spec.split("=")
            frames.append((f, want, ""))
    P.WIN = "0"          # ocr/freeze need no window for a saved png
    bad = 0
    for name, want, note in frames:
        png = name if os.path.exists(name) else os.path.join(EVID, name)
        if not os.path.exists(png):
            print(f"SKIP  {name} (no such file)")
            continue
        words = P.ocr(png)
        got = P.classify(words, P.region_colors(png), png)
        ok = got == want
        bad += 0 if ok else 1
        extra = ""
        if want == "loaded-game":
            c = P.caption_center(words)
            if c:
                extra = f"  -> OK click at ({int(c[0]-108)},{int(c[1]+194)})"
        print(f"{'PASS' if ok else 'FAIL'}  {name}: got={got} want={want}{extra}"
              + (f"   [{note}]" if note else ""))
    print("frames:", len(frames), "failures:", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
