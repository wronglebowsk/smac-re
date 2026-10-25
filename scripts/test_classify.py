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
    ("evidence/m37_screen0.png", "quit-prompt",
     "NOT the title screen: this session-37 frame is the quit dialog over the HUD (OCR "
     "says 'do you really want to quit?' + 'oops no wait!'). The old classifier called it "
     "`title` because its banner IS the game title, and a run stopped on it"),
    ("evidence/m15_title_now.png", "quit-prompt", "the same trap, frame from session 15"),
    ("evidence/m54a/quit_prompt.png", "quit-prompt",
     "the quit dialog at 2398; Escape selects 'Oops, no, wait!' and the round goes on "
     "(trace_m54a40c turn 13 died before this class existed)"),
    ("evidence/m37_recovered.png", "hud", "the HUD after a quit dialog was answered away"),
    ("evidence/m54a/live_now2.png", "help",
     "the HELP browser (FACTION PROFILES): profile text contains base words, and Escape is "
     "ignored by it — only its EXIT bar closes it (a stray vote-row click opened it and the "
     "round stalled twice)"),
    ("evidence/m54c/comm_pane.png", "comm",
     "M54c: a faction COMMUNICATION — 'BELIEVERS - SEETHING' banner + a QUOTED demand + "
     "its own OK bar at y 347. It used to classify `unknown`, so the bottom-bar rule "
     "clicked the console DATALINKS bar (333,560) 38 times in a row and turn 35 of "
     "trace_m54c40b burned 735 s with the year stuck at 2185"),
    ("evidence/m54d/m54d_move_afterg.png", "dest-chooser",
     "M54d: the `g` (\"Move to\") chooser — SELECT DESTINATION caption at y 102, a base row "
     "with 'Distance: 0' at y 132, its OWN OK/CANCEL bar row at y 162. It used to classify "
     "`hud` (only 5 words land in the dialog band, so the dialog test misses it) while it "
     "swallowed every keypress: 10 keys fired at a selected unit, zero order bytes, "
     "evidence/m54d/probe_unit0.json"),
    ("evidence/m54d/synth_chooser.png", "dest-chooser",
     "M54d: the same chooser over a unit standing OFF its base — same caption, same bar row, "
     "and the row it lists is still 'University Base Distance: 0' because the pane reports "
     "the CURSOR's distance, not the unit's"),
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
