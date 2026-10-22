#!/usr/bin/env python3
"""M48d recovery: relaunch terran.exe and load Autosave 1 (year 2344).

M27-recipe load (name box + typed Windows path), per wine-headless-harness.md:244.
Stuck-pane escape: the CONFIRM DISBAND pane queued behind base-panel widgets is
unreachable (modal key-sink M32 + OK bar occluded). Relaunch is the clean path.
"""
import os, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P

SAVE = r"Z:\home\n100\reverse\smac\programs\saves\auto\Alpha Centauri Autosave 1.SAV"
LAUNCH = ("cd ~/reverse/smac/programs && WINEPREFIX=$HOME/.wine-smac32 DISPLAY=:99 "
          "WINEDLLOVERRIDES='mscoree,msxml=' nohup ~/tools/wine-10.20-staging-tkg-x86/bin/wine "
          "explorer /desktop=smac,800x600 terran.exe > /dev/null 2>&1 &")


def main():
    # 1. kill old game + orphan winedevices
    subprocess.run("pkill -f 'terran.ex[e]'", shell=True)
    time.sleep(3)
    subprocess.run("pkill -f 'winedevice.ex[e]'", shell=True)
    subprocess.run("pkill -f 'explorer.ex[e].*desktop=smac'", shell=True)
    time.sleep(2)
    # 2. launch
    subprocess.run(LAUNCH, shell=True)
    print("launched, waiting for window...", flush=True)
    for i in range(60):
        time.sleep(3)
        w = subprocess.run("DISPLAY=:99 xdotool search --name 'Sid Meier'", shell=True,
                           capture_output=True, text=True).stdout.split()
        if w:
            break
    print("window:", w, flush=True)
    # 3. drive to HUD
    t0 = time.time()
    last = None
    typed = False
    while time.time() - t0 < 240:
        P.WIN = P.find_window()
        P.focus()
        png = P.freeze("m48boot")
        words = P.ocr(png)
        kind = P.classify(words, P.region_colors(png), png)
        body = ' '.join(w[0] for w in words).lower()
        if kind != last:
            print(f"[{time.time()-t0:5.1f}s] class={kind} body={body[:80]}", flush=True)
            last = kind
        if kind == "hud":
            print("HUD reached", flush=True)
            return 0
        if kind in ("cdrom", "unknown") and "start game" in body:
            kind = "title"
        if kind == "cdrom":
            P.key("Return")
        elif kind == "title":
            print("  -> LOAD GAME", flush=True)
            P.click((610, 344))
        elif kind == "load" or ("load game" in body and "name" in body):
            # file browser: click name box, clear, type path, Return
            if not typed:
                P.click((400, 252)); time.sleep(0.8)
                subprocess.run("DISPLAY=:99 xdotool key End", shell=True)
                subprocess.run("DISPLAY=:99 xdotool key BackSpace --repeat 200", shell=True)
                subprocess.run(f'DISPLAY=:99 xdotool type --delay 25 "{SAVE}"', shell=True)
                typed = True
                time.sleep(0.8)
                P.key("Return")
                print("  -> typed path + Return", flush=True)
            else:
                P.key("Return")
        elif "difficultylevel" in body or "difficulty level" in body:
            # LOAD confirm pane: OK at (290,391)
            print("  -> LOAD confirm OK", flush=True)
            P.click((290, 391))
        elif "operations director" in body:
            # post-load modal on base screen: row (~400,307) then OK (400,362)
            print("  -> ops director: row + OK", flush=True)
            P.click((400, 307)); time.sleep(1.4)
            P.click((400, 362)); time.sleep(1.2)
        elif kind == "base":
            print("  -> base screen: Escape", flush=True)
            P.key("Escape")
        elif "really" in body and "quit" in body:
            print("  FATAL quit prompt", flush=True)
            return 2
        time.sleep(2)
    print("timeout reaching HUD", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
