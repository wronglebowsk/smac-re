#!/usr/bin/env python3
"""M54a: unit test for the screen classifier — saved screenshots, no live game.

The bug this pins (VERIFIED session 75): classify() returned `base` for ANY frame whose
OCR text contained a BASE_WORD, and the HUD's OWN message pane prints news lines that do
("...is not on = producing enough nutrients to meet its..." at (355,438) on
evidence/m54a/live_hud.png). Every frame of that position read `base`, the clearing
Escape was forbidden by --no-escape > --timeout, and two runs stalled with zero hits.

The two assertions the milestone asks for, in one file: a HUD whose message pane is
talking still classifies `hud`, and a real base screen still classifies `base`. The rest
of the cases are the guards that already existed (title / cdrom / loaded-game) — the fix
must not knock them over, because clicking those screens ends the game.

    python3 scripts/test_classify.py         # ~40 s; tesseract is the cost, not the logic

Fixtures are COPIED to a scratch dir before OCR: smac_play.ocr() writes its 2x sibling
next to the input, and OCRing straight out of evidence/ litters the repo with _3x pngs.
"""
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import smac_play as sp  # noqa: E402

CASES = [
    ("evidence/m54a/live_hud.png", "hud",
     "M54a bug frame: HUD + message-pane news containing 'nutrients' (355,438), "
     "TURN COMPLETE at (628,419)"),
    ("evidence/m45a_post.png", "base",
     "real base screen (session 42, NAMED.md:329): top menu EXPLORE/DISCOVER/GOVERNOR/"
     "BUILD/CONQUER + tabs, no TURN COMPLETE row at all"),
    ("evidence/m25_t7.png", "hud", "plain HUD, TURN COMPLETE at (697,416), no base words"),
    ("evidence/m15_boot.png", "cdrom", "boot nag wears the game title in its caption"),
    ("evidence/m15_loaded_words.png", "loaded-game",
     "LOAD confirm drawn over the title art (the screen session 20b lost the game on)"),
    ("evidence/m37_screen0.png", "title", "title screen: never click, never Escape"),
]


def main():
    tmp = tempfile.mkdtemp(prefix="m54a_classify_")
    fails = []
    try:
        for rel, want, why in CASES:
            src = os.path.join(ROOT, rel)
            work = os.path.join(tmp, os.path.basename(rel))
            shutil.copyfile(src, work)
            words = sp.ocr_fast(work)
            got = sp.classify(words, sp.region_colors(work), work)
            hits = sp.base_word_positions(words)
            ok = got == want
            print(f"{'ok  ' if ok else 'FAIL'} {rel:34s} got={got:12s} want={want:12s} "
                  f"n={len(words):3d} base_hits={hits}")
            print(f"       {why}")
            if not ok:
                fails.append((rel, want, got))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if fails:
        print("FAIL", fails)
        return 1
    print(f"PASS {len(CASES)}/{len(CASES)} screen classifications")
    return 0


if __name__ == "__main__":
    sys.exit(main())
