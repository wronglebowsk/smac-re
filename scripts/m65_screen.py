#!/usr/bin/env python3
"""M65 — measure the screen-read flake: N classify() passes on the SAME live screen.

Session 104 got 14 consecutive classify() == 'unknown' verdicts on frames that
vision_analyze showed to be the plain tactical HUD, while 3 of 6 samples of the same
screen read 'hud'. accept_ready.py treats anything that is not 'hud' as a modal and
BLOCKS the whole session on it, so the readiness oracle is an OCR coin-flip.

This instrument does not fix anything and does not touch the game: it never clicks and
never presses a key. It freezes, OCRs, classifies, and records WHAT THE FRAME ACTUALLY
CONTAINS around the HUD's own landmarks (the TURN COMPLETE row at y~419, the MENU /
COMMLINK buttons, the Mission Year row) so the fix can be designed on measured rows
instead of on a guess about which token drifts.

    python3 scripts/m65_screen.py --samples 8 --save evidence/m65

READ-ONLY: writes only its own frame copies (into --save, default /tmp/m65/).
"""
import argparse, json, os, shutil, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as sp

# The HUD's own chrome, by y-band. classify() identifies the HUD ONLY by the
# TURN COMPLETE row (380 < y < 450), so that band is the interesting one.
ROW_BANDS = [("year", 0, 40), ("caption", 55, 180), ("buttonrow", 380, 450),
             ("console", 500, 600)]


def band_tokens(words, lo, hi):
    return [f"{t}@{int(cy)}" for t, _cx, cy, _w, _h in words if lo <= cy <= hi]


def probe_words(words, ncolors, png):
    """Everything a screen read needs, computed from words we already paid for."""
    return dict(
        kind=sp.classify(words, ncolors, png),
        n_words=len(words),
        ncolors=ncolors,
        ncolors_textcol=sp.region_colors(png, sp.TEXTCOL) if png else None,
        close_bar=bool(png and sp.close_bar(png)),
        load1=float(open("/proc/loadavg").read().split()[0]),
        bands={name: band_tokens(words, lo, hi) for name, lo, hi in ROW_BANDS},
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=8)
    ap.add_argument("--gap", type=float, default=1.0, help="seconds between freezes")
    ap.add_argument("--save", default="/tmp/m65",
                    help="copy every frame here as sample_NN_<class>.png")
    ap.add_argument("--tag", default="m65screen")
    a = ap.parse_args()

    os.makedirs(a.save, exist_ok=True)
    rows = []
    for k in range(a.samples):
        png = sp.freeze(a.tag)
        words = sp.ocr_fast(png)
        nc = sp.region_colors(png)
        rec = probe_words(words, nc, png)
        rec["k"] = k
        dst = os.path.join(a.save, f"sample_{k:02d}_{rec['kind']}.png")
        shutil.copyfile(png, dst)
        for sib in (png.replace(".png", "_3x.png"),):
            if os.path.exists(sib):
                os.remove(sib)          # the gate counts these; the tests rebuild them
        rows.append(rec)
        print(f"[{k}] kind={rec['kind']:12s} n={rec['n_words']:3d} ncol={rec['ncolors']:4d} "
              f"tcol={rec['ncolors_textcol']:4d} bar={int(rec['close_bar'])} load1={rec['load1']:.2f} "
              f"btn={rec['bands']['buttonrow'][:8]}")
        if k + 1 < a.samples:
            time.sleep(a.gap)

    kinds = {}
    for r in rows:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    print("CLASSES SEEN", json.dumps(kinds), f"of {a.samples} samples")
    print("frames:", a.save)
    with open(os.path.join(a.save, "samples.json"), "w") as fh:
        json.dump(rows, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
