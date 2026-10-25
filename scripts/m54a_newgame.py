#!/usr/bin/env python3
"""M54a support (session 78): walk START GAME to a live HUD (year 2100).

Session 78 could not drive a RESUMED game: every autosave left by session 77's run
resumes with `turn_flags` bit1 set, the main thread spinning at ~90 % CPU, the screen
static and input dead (see SESSION_NOTES session 78). A fresh game is the only
position the 40-turn assertion can be tested on right now.

Rows are located by OCR token, never by a phrase: `find()` matches one token
(`make`, `small`, `standard`), because tesseract splits the label rows.
Title rows measured live: START (580,111) SCENARIO (610,269) LOAD (579,344).
Wizard: START -> map select (MAKE RANDOM MAP) -> size (SMALL) -> level (TALENT,
same as the campaign) -> rules (STANDARD) -> intro text (Return) -> faction (first
row) -> planet generation -> HUD at 2100.
"""
import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P

TOKEN_ROWS = [("make", None), ("small", None), ("talent", None), ("standard", None)]
FACTIONS = ("hive", "circle", "academy", "smith", "dominion", "cult", "hermit", "gc")


def click_token(words, token):
    f = P.find(words, [token])
    if f:
        P.click((f[0], f[1]))
        return f
    return None


def main():
    P.WIN = P.find_window()
    if not P.WIN:
        print("no window", flush=True)
        return 3
    t0, last = time.time(), None
    done_tokens = set()
    while time.time() - t0 < 260:
        P.WIN = P.find_window()
        P.focus()
        st = P.state()
        if (st.get("year") or 0) >= 2100:
            print(f"GAME LIVE year={st['year']} cur_player={st.get('cur_player')} "
                  f"n_bases={st.get('n_bases')}", flush=True)
            return 0
        png = P.freeze("m54awiz")
        words = P.ocr(png)
        body = " ".join(w[0] for w in words).lower()
        kind = P.classify(words, P.region_colors(png), png)
        if kind != last:
            print(f"[{time.time()-t0:5.1f}s] {kind} {body[:60]}", flush=True)
            last = kind
        if "really" in body and "quit" in body:
            P.key("Escape")                      # Oops, no, wait!
        elif "substructure" in body or "electrons" in body or "monologue" in body:
            P.key("Return")                      # intro text pages
        elif "difficulty level" in body or "difficultylevel" in body:
            click_token(words, "talent") or P.key("Return")
        elif "size of planet" in body:
            click_token(words, "small") or click_token(words, "standard")
        elif "game rules" in body or "standard rules" in body:
            click_token(words, "standard") or P.key("Return")
        elif "random map" in body:
            click_token(words, "make") or click_token(words, "customize")
        elif "faction" in body or any(f in body for f in FACTIONS):
            hit = None
            for f in FACTIONS:
                hit = click_token(words, f)
                if hit:
                    print(f"  faction {f} at {hit[:2]}", flush=True)
                    break
            if not hit:
                P.key("Return")
        elif kind == "cdrom":
            P.key("Return")
        elif "start game" in body:
            click_token(words, "start")
        elif kind == "hud":
            print(f"HUD but year={st.get('year')}", flush=True)
        elif kind in ("movie", "unknown"):
            P.key("Return")
        time.sleep(2)
    print("wizard timeout", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
