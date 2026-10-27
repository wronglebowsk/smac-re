#!/usr/bin/env python3
"""M65 — measure the two HUD anchors on every saved classifier frame.

classify() identifies the HUD by ONE thing: the TURN COMPLETE row (380 < y < 450). On a
live animating map that row OCRs to garbage in 5 of 8 passes (scripts/m65_screen.py,
2026-10-26), which is why accept_ready.py's screen gate is a coin-flip.

Candidate anchor: the HUD's own bottom status line — `Mission` + `Year` + the 4-digit
mission year at y~567 — which is the same HUD chrome, just a row lower, and landed in
8 of 8 passes. This prints BOTH anchors for every frame test_classify.py pins, plus the
live frames, so the promotion rule can be chosen on the table it prints: an anchor that
fires on the plain HUD but never on a frame whose true class is a modal.

Copies fixtures to a scratch dir before OCR (ocr() writes its 3x sibling next to the
input and the evidence budget counts it).
"""
import os, shutil, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import smac_play as sp                    # noqa: E402
import test_classify as T                 # noqa: E402

BAND = (548, 592)   # the bottom status strip: Mission Year row at y~567 (measured)


def anchors(words):
    band = [w for w in words if BAND[0] <= w[2] <= BAND[1]]
    txt = " ".join(t for t, *_ in band).lower()
    year_num = [t for t, *_ in band if t.isdigit() and 4 == len(t) and 2000 <= int(t) <= 2500]
    turn = sp.find(words, ["complete"])
    return dict(
        turn_complete=bool(turn) and 380 < turn[1] < 450,
        strip_mission="mission" in txt,
        strip_year="year" in txt,
        strip_year_num=year_num[:3],
        strip_n=len(band),
    )


def main():
    frames = list(T.CASES) + [(p, None, "live m65 frame") for p in
                              sorted(sys.argv[1:])]
    tmp = tempfile.mkdtemp(prefix="m65_anchor_")
    try:
        for rel, want, _why in frames:
            src = rel if os.path.isabs(rel) else os.path.join(ROOT, rel)
            if not os.path.exists(src):
                print(f"SKIP {rel} (missing)")
                continue
            work = os.path.join(tmp, os.path.basename(rel))
            shutil.copyfile(src, work)
            words = sp.ocr_fast(work)
            got = sp.classify(words, sp.region_colors(work), work)
            a = anchors(words)
            print(f"{os.path.basename(rel):28s} true={str(want):12s} classify={got:12s} "
                  f"turnrow={int(a['turn_complete'])} strip={int(a['strip_mission'] and a['strip_year'] and bool(a['strip_year_num']))} "
                  f"m={int(a['strip_mission'])} y={int(a['strip_year'])} num={a['strip_year_num']} "
                  f"nwords={len(words)}")
            for sib in (work.replace(".png", "_3x.png"),):
                if os.path.exists(sib):
                    os.remove(sib)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
