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
    ("m54a/quit_prompt.png",    "quit-prompt", "M54a: \"Do you really want to quit?\" over the HUD — was `title`, which stopped a 40-turn run"),
    ("m54c/comm_pane.png",      "comm",        "M54c: faction COMMUNICATION ('X - MOOD' banner + quoted demand) — click ITS OK bar (y 347); the y-560 console row under it is NOT a close bar"),
    ("m54d/m54d_move_afterg.png", "dest-chooser", "M54d: the `g` chooser (SELECT DESTINATION + a base row + its own OK/CANCEL row at y 162) — was `hud`, so it swallowed 10 keypresses with zero order bytes"),
    ("m54d/synth_chooser.png",  "dest-chooser", "M54d: the same chooser over a unit off its base; the listed Distance is the CURSOR's, not the unit's"),
    ("m54d/peek_stuck.png",     "artwork-close", "M54d: full-screen scene panel with its own red CLOSE bar (y 579-599, x 596-799) — was `movie`, whose only answer is the gated Escape; two runs froze on it"),
    ("m54e/chooser_live.png",   "dest-chooser", "M54e: the chooser as the LIVE loop caught it (unit off its base, HUD news pane under it) — session 81's run classified its live chooser frame `unknown`, so the driver must answer this pane and not fall through to Return"),
    ("m54g/newbase_pane.png",   "name-pane", "M54g: NEWBASE name entry (`b` on a class-8 unit on a legal tile) — caption at y 102 over a still-drawn HUD, so it read `hud` and ate the founding; answer is Return (the base record exists 0.1 s later)"),
    ("m54h/chooser_g60b.png",   "dest-chooser", "M54h: the `g` chooser with TWO destination rows (Korolev Center y 132, University Base y 151) and its five-button row at y 181 — the two-row layout the loop now clicks a ROW in"),
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
