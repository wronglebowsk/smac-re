#!/usr/bin/env python3
"""M37: recover the game from the REALLYQUIT pane (Escape-on-bare-HUD aftermath, M36).

Clicks the "Oops, no, wait!" row (OCR-located), then the OK bar 47 px below
(M36 geometry: rows y~260/281, OK ~307), verifying after each click. Breaks the
pointer grab (M26) with a harmless HUD-chrome click first. Never presses Escape.
"""
import re, shutil, sys, time

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import smac_play as P

TAG = "m37_rec"


def body_of(words):
    return re.sub(r"[^a-z]", "", " ".join(w[0] for w in words).lower())


def pane_up(body):
    return "oops" in body or "reallywanttoquit" in body


def main():
    # grab-breaker click on HUD chrome (bottom-left corner, no widget there)
    P.click((400, 585)); time.sleep(0.8)
    png = P.freeze(f"{TAG}0"); words = P.ocr(png)
    body = body_of(words)
    print("after grab-break: pane =", pane_up(body), flush=True)
    if pane_up(body):
        row = None
        for t, cx, cy, *_ in words:
            low = t.lower().strip(".,:;|_*")
            if low.startswith("oops") and 150 <= cx <= 660:
                row = (int(cx), int(cy)); break
        print("oops row:", row, flush=True)
        if row is None:
            sys.exit("REALLYQUIT open but NO row not OCR-able; stop for human")
        P.click(row); time.sleep(1.4)
        png = P.freeze(f"{TAG}1"); words = P.ocr(png)
        body = body_of(words)
        print("after NO click: pane =", pane_up(body), flush=True)
        if pane_up(body):
            P.click((row[0], row[1] + 47)); time.sleep(1.4)
    png = P.freeze(f"{TAG}2"); words = P.ocr(png)
    body = body_of(words)
    kind = P.classify(words, png=png)
    btn = P.ocr_crop(png, (615, 396, 180, 34), f"{TAG}btn", scale=6)
    btxt = re.sub(r"[^a-z]", "", " ".join(w[0] for w in btn).lower())
    hud = ("mplete" in btxt or "omple" in btxt)
    print(f"final: kind={kind} btn={btxt!r} pane={pane_up(body)} hud_strip={hud}",
          flush=True)
    shutil.copy(f"/tmp/{TAG}2.png", f"{P.EVID}/m37_recovered.png")
    if pane_up(body) or not hud:
        sys.exit("recovery unconfirmed; see evidence/m37_recovered.png")
    print("RECOVERED", flush=True)


if __name__ == "__main__":
    main()
