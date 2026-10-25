#!/usr/bin/env python3
"""M54a support (session 78): get the game from title (or wedged) to a LIVE HUD.

Session 77 ended with the game parked at the title menu, so the driver had no session
to drive (state reader: n_bases 0, cur_player 0).

Measured live on the LOAD browser (evidence/m54a/load_browser.png, root capture ==
window coords): NAME field (406,527), OK bar (330,552), CANCEL bar (482,552).
OCR cannot read the LOAD banner, the file rows, or the OK/CANCEL bars (dithered bars,
label inside), so this walks the browser BLIND and deterministic: LOAD GAME row ->
name box -> type the full Z:\\ path -> click OK. Return in the name box only SELECTS
the file; the load needs the OK bar clicked.

`--relaunch` first kills the wedged game (bracket-pkill recipe from m48d_boot.py) and
starts a fresh one. A HUD whose map does not animate for 4 s is a WEDGE, not a turn:
see SESSION_NOTES session 78 (a save taken with turn_flags bit1 set resumes hung).
"""
import os, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P

SAVE = os.environ.get("SMAC_SAVE",
                      r"Z:\home\n100\reverse\smac\programs\saves\auto\Alpha Centauri Autosave 1.SAV")
TITLE_LOAD_ROW = (610, 344)   # "load game" on the title menu (m48d_boot)
NAME_BOX = (406, 527)
LOAD_OK = (330, 552)
LOAD_CANCEL = (482, 552)
CONFIRM_OK = (290, 391)       # LOAD confirm pane (wine-headless-harness.md, verified live)
LAUNCH = ("cd ~/reverse/smac/programs && WINEPREFIX=$HOME/.wine-smac32 DISPLAY=:99 "
          "WINEDLLOVERRIDES='mscoree,msxml=' nohup ~/tools/wine-10.20-staging-tkg-x86/bin/wine "
          "explorer /desktop=smac,800x600 terran.exe > /dev/null 2>&1 &")


def relaunch():
    for name in ("terran.ex[e]", "winedevice.ex[e]", "explorer.ex[e].*desktop=smac"):
        subprocess.run(f"pkill -f '{name}'", shell=True)
        time.sleep(2)
    subprocess.run(LAUNCH, shell=True)
    for _ in range(40):
        time.sleep(3)
        if P.find_window():
            return True
    return False


def type_path():
    P.click(NAME_BOX)
    time.sleep(0.9)
    subprocess.run("DISPLAY=:99 xdotool key End", shell=True)
    subprocess.run("DISPLAY=:99 xdotool key --repeat 200 BackSpace", shell=True)
    subprocess.run(f'DISPLAY=:99 xdotool type --delay 25 "{SAVE}"', shell=True)
    time.sleep(0.9)
    P.click(LOAD_OK)
    time.sleep(4)


def animating(gap=5):
    """Two frames `gap` s apart: a live HUD map always changes; a wedge does not."""
    from PIL import Image, ImageChops
    a = P.freeze("m54a_anim_a")
    time.sleep(gap)
    b = P.freeze("m54a_anim_b")
    return ImageChops.difference(Image.open(a), Image.open(b)).getbbox() is not None


def main():
    if "--relaunch" in sys.argv and not relaunch():
        print("no window after relaunch", flush=True)
        return 3
    t0, last, browser_done = time.time(), None, False
    while time.time() - t0 < 220:
        P.WIN = P.find_window()
        if not P.WIN:
            print("no window", flush=True)
            return 3
        P.focus()
        png = P.freeze("m54aload")
        words = P.ocr(png)
        kind = P.classify(words, P.region_colors(png), png)
        body = " ".join(w[0] for w in words).lower()
        if kind in ("cdrom", "unknown") and "start game" in body:
            kind = "title"          # OCR splits the title rows (m48d_boot's remap)
        if kind != last:
            print(f"[{time.time()-t0:5.1f}s] class={kind} body={body[:64]}", flush=True)
            last = kind
        if kind == "hud":
            live = animating()
            print(f"HUD reached animating={live}", flush=True)
            return 0 if live else 4
        if "really" in body and "quit" in body:
            print("  quit prompt -> Escape (Oops, no, wait!)", flush=True)
            P.key("Escape")
        elif kind == "title" and not browser_done:
            print("  title -> LOAD GAME row, then blind browser step", flush=True)
            P.click(TITLE_LOAD_ROW)
            time.sleep(3)
            type_path()
            browser_done = True
        elif kind in ("loaded-game", "unknown") and ("difficultylevel" in body
                                                     or "difficulty level" in body):
            print("  LOAD confirm -> OK (290,391)", flush=True)
            P.click(CONFIRM_OK)
            time.sleep(3)
        elif "operations director" in body:
            print("  ops director: row + OK", flush=True)
            P.click((400, 307))
            time.sleep(1.4)
            P.click((400, 362))
        elif kind == "base":
            print("  base screen -> Escape", flush=True)
            P.key("Escape")
        elif kind == "cdrom":
            P.key("Return")
        elif browser_done and kind == "unknown":
            print("  browser did not take the path -> retry once", flush=True)
            type_path()
            browser_done = "retry" if browser_done is True else True
        time.sleep(2)
    print("timeout reaching HUD", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
