#!/usr/bin/env python3
"""M65 — pin the HUD status-bar signal and the multi-look verdict. No game, no OCR of live frames.

WHY THIS EXISTS. classify() names the tactical HUD off exactly one row: the word
`complete` at 380 < y < 450 (the TURN COMPLETE button). On a live animating map that row
fragments. Measured 2026-10-26 with scripts/m65_screen.py: 8 freezes of ONE unchanged HUD
(terran.exe alive, year 2161, nothing clicked) produced classify() == 'unknown' 5 times and
'hud' 3 times; the `complete` token appears in the saved per-sample records
(evidence/m65/before_8looks_samples.json) in samples 1, 5 and 6 only. Meanwhile the HUD's
bottom status bar — `Mission Year <year>` at y~567, the faction score row at y~581,
`Energy:` at y~582 — read in all 8. accept_ready.py treated anything that was not 'hud' as
a modal, so the readiness oracle was a coin-flip that blocked a playable box (14 consecutive
blocked reads in session 104, all of them the plain HUD).

The fix is a SECOND LOOK at the same chrome, so this file asserts three things:

  1. the signal fires on every saved frame whose screen really is the HUD — including the
     two old frames whose button row AND whose `Mission`/`Year` words both fragment
     (`sisson tear zie` on m25_t7.png, `esston 2388` on live_hud.png) — and the four live
     frames that classify() called 'unknown';
  2. it does NOT fire on a screen with no HUD behind it (base screen, cdrom nag, LOAD
     confirm, HELP browser, COMM pane, the full-screen artwork panel);
  3. on a modal drawn OVER a still-drawn HUD it may fire, and that is harmless only because
     classify() names those frames first — so each of those cases asserts the NAME too.

Plus the verdict logic (pure, no OCR): a named modal in any look decides the screen, the
plain HUD needs the bar twice before it is believed, and an `unknown` that never shows the
bar is still 'unknown' — the check is not weakened, only re-read.

    python3 scripts/test_hud_bar.py        # ~45 s of tesseract on an idle box
"""
import os, shutil, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import accept_ready as A                  # noqa: E402
import smac_play as sp                    # noqa: E402

# (frame, must fire?, must classify-as?, why)
FRAMES = [
    # ---- the HUD: the signal must fire on every one of these ----
    ("evidence/m54a/live_hud.png", True, "hud",
     "M54a bug frame. Button row reads, and the bar fires on the FRAGMENTS: `[esston` "
     "(mission) + `2388` (the year number). Energy: is NOT in this frame's bar."),
    ("evidence/m25_t7.png", True, "hud",
     "Plain HUD, session 25. The whole status row fragments to `sisson tear zie` with no "
     "year number at all — it passes on the `Mission` fragment, the `Year`-as-`tear` "
     "fragment and `Energy:` at y 582."),
    ("evidence/m37_recovered.png", True, "hud",
     "The HUD after a quit dialog was answered away: `Mission Year 2275` reads cleanly."),
    ("evidence/m65/sample_00_unknown.png", True, "unknown",
     "LIVE flake frame: classify() == 'unknown' on the plain HUD (year 2161, Korolev "
     "Center queued). The bar reads `Mission Year 2161` — this is the frame the fix is for."),
    ("evidence/m65/sample_02_unknown.png", True, "unknown",
     "Same screen, same freeze loop: 'unknown' with the bar intact (`Mission` garbled to "
     "`||Il)||Mission`, year number clean)."),
    ("evidence/m65/sample_04_unknown.png", True, "unknown",
     "Same screen: 'unknown', the bar's only tokens are the score row and `Mission Year 2161`."),
    ("evidence/m65/sample_07_unknown.png", True, "unknown",
     "Same screen: 'unknown' with almost nothing in the button row (`W)@446 Econ:@449`); "
     "the bar still carries Mission/Year/2161."),
    ("evidence/m65/sample_05_hud.png", True, "hud",
     "The control: the same screen read 'hud' (TURN/COMPLETE at y 416) and the bar fires too."),
    # ---- no HUD behind these: the signal must NOT fire ----
    ("evidence/m45a_post.png", False, "base",
     "A real base screen: 4 tokens land in the bar band and none of them is Mission, Year, "
     "a year number or Energy."),
    ("evidence/m15_boot.png", False, "cdrom", "The boot nag: nothing at all in the bar band."),
    ("evidence/m15_loaded_words.png", False, "loaded-game",
     "LOAD confirm over the title art: 14 tokens in the band, none of them Mission/Year/"
     "year-number/Energy — the title art's own text."),
    ("evidence/m54a/live_now2.png", False, "help",
     "The HELP browser (faction profiles, 234 tokens): profile prose must not fake a HUD."),
    ("evidence/m54c/comm_pane.png", False, "comm",
     "A faction COMMUNICATION pane: its own OK bar at y 347, no HUD status bar."),
    ("evidence/m54d/peek_stuck.png", False, "artwork-close",
     "Full-screen Secret-Project artwork with its own red CLOSE bar: 10 tokens in the whole "
     "frame."),
    # ---- modals drawn OVER a still-drawn HUD: firing is fine ONLY because the name wins ----
    ("evidence/m37_screen0.png", None, "quit-prompt",
     "The quit dialog over the HUD: the bar IS still drawn (Mission Year 2275), so the "
     "signal fires; what saves it is that is_quit_prompt() names the frame first."),
    ("evidence/m54e/chooser_live.png", None, "dest-chooser",
     "The `g` chooser over the HUD (Mission Year row drawn under it, per M54e) — named "
     "first, so the bar never gets a vote."),
    ("evidence/m54g/newbase_pane.png", None, "name-pane",
     "NEWBASE name entry over a still-drawn HUD: M54g's own lesson is that the HUD chrome "
     "under a pane is a trap; is_name_pane() must name it."),
    ("evidence/m54h/chooser_g60b.png", None, "dest-chooser",
     "Two-destination chooser over the HUD — same shape, named first."),
]

# The promotion logic, pinned without OCR: (looks, want, why)
LOOKS = [
    ([("hud", False)], "hud", "one clean button-row read is enough, as always"),
    ([("unknown", True), ("unknown", True)], "hud",
     "the flake shape: two looks, no button row either time, the status bar both times"),
    ([("unknown", True), ("unknown", False), ("unknown", True)], "hud",
     "confirmations need not be consecutive: 2 of 3 looks showed the bar"),
    ([("unknown", True)], "unknown",
     "ONE bar-only look is not believed (confirm=2): a single garbled pass cannot open a run"),
    ([("unknown", False)] * 4, "unknown",
     "no button row and no bar in 4 looks: still unknown, still blocked — the check is not "
     "weakened, just re-read"),
    ([("unknown", True), ("dest-chooser", False)], "dest-chooser",
     "a named modal in ANY look wins over a pending bar promotion: the chooser swallows "
     "every keypress"),
    ([("dialog", False)], "dialog", "a named modal decides on the first look"),
    ([("unknown", False), ("unknown", True), ("unknown", True)], "hud",
     "the bar is believed on the third look after two misses"),
]


def main():
    bad = []
    tmp = tempfile.mkdtemp(prefix="m65_bar_")
    try:
        for rel, want_fire, want_class, why in FRAMES:
            src = os.path.join(ROOT, rel)
            if not os.path.exists(src):
                bad.append((rel, "missing frame"))
                print(f"FAIL {rel}: missing")
                continue
            work = os.path.join(tmp, os.path.basename(rel))
            shutil.copyfile(src, work)
            words = sp.ocr_fast(work)
            cls = sp.classify(words, sp.region_colors(work), work)
            bar = sp.hud_status_bar(words)
            ok = True
            if want_fire is not None and bool(bar["fire"]) != want_fire:
                ok = False
            if want_class is not None and cls != want_class:
                ok = False
            if want_class is not None and want_fire is None and not bar["fire"]:
                ok = False            # these cases document that the bar DOES fire there
            print(f"{'ok  ' if ok else 'FAIL'} {rel:38s} cls={cls:12s} fire={int(bar['fire'])} "
                  f"nbar={bar['nbar']:3d} mission={int(bar['mission'])} year={int(bar['year'])} "
                  f"nums={bar['nums']} energy={int(bar['energy'])}")
            print(f"       {why}")
            if not ok:
                bad.append((rel, f"cls={cls} fire={bar['fire']}"))
            sib = work.replace(".png", "_3x.png")
            if os.path.exists(sib):
                os.remove(sib)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    for looks, want, why in LOOKS:
        got, detail = A.verdict(looks)
        ok = got == want
        print(f"{'ok  ' if ok else 'FAIL'} looks={[k for k, _ in looks]} -> {got} (want {want})")
        print(f"       {why}  [{detail}]")
        if not ok:
            bad.append((str(looks), f"got {got} want {want}"))

    n = len(FRAMES) + len(LOOKS)
    if bad:
        print("FAIL", len(bad), "of", n, "cases:", bad)
        return 1
    print(f"PASS {n}/{n} hud-bar cases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
