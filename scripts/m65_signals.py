#!/usr/bin/env python3
"""M65 — candidate HUD signals, measured on every saved frame + the live m65 frames.

classify() calls the tactical HUD 'hud' ONLY when it can read the word `complete` in the
button row (380 < y < 450). On a live animating map that row fragments: 8 freezes of ONE
unchanged HUD (scripts/m65_screen.py) put the token in 3 of 8 passes, and the two oldest
saved HUD frames fragment the row too. The HUD's bottom status bar — Mission Year row,
faction score row, Energy readout, y 555-590 — is the same chrome one row lower and is
what these candidate signals look at.

Prints one row per frame: true class, classify() class, then the candidate signals.
The rule that ships must fire on every frame whose true class is `hud`; on a modal drawn
OVER the HUD it may fire, because classify() names those frames first and the promotion
is only ever consulted on classify() == 'unknown'.
"""
import os, re, shutil, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import smac_play as sp                    # noqa: E402
import test_classify as T                 # noqa: E402

BAR = (548, 592)                          # the HUD bottom status bar
SCORE = re.compile(r"^[0-9-]{2,6}$")      # the faction score row, e.g. `1-1-1`


def signals(words):
    bar = [w for w in words if BAR[0] <= w[2] <= BAR[1]]
    letters = re.sub(r"[^a-z]", "", " ".join(t for t, *_ in bar).lower())
    nums = [t for t, *_ in bar if t.isdigit() and 2000 <= int(t) <= 2500]
    turn = sp.find(words, ["complete"])
    return dict(
        S1_btnrow=bool(turn) and 380 < turn[1] < 450,
        S2_mission="mission" in letters,
        S3_missionfrag=bool(re.search(r"ssion|sslon|sston|ismon|sshon", letters)),
        S4_year="year" in letters or "tear" in letters,
        S5_baryearnum=bool(nums),
        S6_energy="energy" in letters,
        S7_scores=[t for t, *_ in bar if SCORE.match(t) and any(c.isdigit() for c in t)][:4],
        nbar=len(bar),
    )


def main():
    frames = list(T.CASES) + [(p, None, "") for p in sys.argv[1:]]
    tmp = tempfile.mkdtemp(prefix="m65_sig_")
    try:
        for rel, want, _why in frames:
            src = rel if os.path.isabs(rel) else os.path.join(ROOT, rel)
            if not os.path.exists(src):
                print(f"SKIP {rel}")
                continue
            work = os.path.join(tmp, os.path.basename(rel))
            shutil.copyfile(src, work)
            words = sp.ocr_fast(work)
            got = sp.classify(words, sp.region_colors(work), work)
            s = signals(words)
            hud = want == "hud" or (want is None and got == "hud")
            fire = s["S1_btnrow"] or ((s["S2_mission"] or s["S3_missionfrag"] or s["S4_year"]
                                       or s["S5_baryearnum"] or s["S6_energy"]) and s["nbar"] >= 3)
            flag = "" if (fire if hud else True) else "  <-- MISSES A HUD FRAME"
            print(f"{os.path.basename(rel):26s} true={str(want):12s} cls={got:12s} "
                  f"btnrow={int(s['S1_btnrow'])} barfire={int(fire)} nbar={s['nbar']:3d} "
                  f"m={int(s['S2_mission'])}{int(s['S3_missionfrag'])} y={int(s['S4_year'])} "
                  f"num={int(s['S5_baryearnum'])} en={int(s['S6_energy'])} sc={','.join(s['S7_scores'])}"
                  f"{flag}")
            sib = work.replace(".png", "_3x.png")
            if os.path.exists(sib):
                os.remove(sib)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
