#!/usr/bin/env python3
"""M53s: end the human turn and ride the AI phase through to the next year.

Reuses scripts/smac_play.py's own helpers (freeze/ocr_fast/classify/answer_confirm/
click/key/state/year) because its classifier is the one this repo trusts.  The stock
driver never clicks TURN COMPLETE here: the HUD's message pane says "nutrients", which
is a BASE_WORD, so every frame classifies as `base` and the --no-escape gate forbids the
Escape that would clear it (verified 2026-10-24: two STUCK runs, 0 hits at 0x4eaa2e).
Here the turn is ended by hand and the AI phase is serviced with the same rules the
driver uses while cur_player != player.
"""
import os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import smac_play as S  # noqa: E402

LIMIT = float(sys.argv[1]) if len(sys.argv) > 1 else 150.0
S.find_window()
y0 = S.year()
st = S.state()
print("start year=%s player=%s cur=%s flags=%s" % (y0, st.get("player"), st.get("cur_player"),
                                                   hex(st.get("turn_flags") or 0)), flush=True)
png = S.freeze("m53s_e0")
w = S.ocr_fast(png)
btn = S.find(w, ["complete"])
print("clicking TURN COMPLETE at", btn, flush=True)
S.click((btn[0], btn[1]) if btn else (660, 420))
t0 = time.time()
seen = {}
while time.time() - t0 < LIMIT:
    time.sleep(1.2)
    st = S.state()
    own, cur = st.get("player"), st.get("cur_player")
    tf = st.get("turn_flags") or 0
    if S.year() != y0:
        print("YEAR ADVANCED %s -> %s after %.1fs" % (y0, S.year(), time.time() - t0), flush=True)
        break
    ai = (own is not None and cur is not None and cur != own) or bool(tf & 2)
    png = S.freeze("m53s_e1")
    w = S.ocr_fast(png)
    kind = S.classify(w, png=png)
    seen[kind] = seen.get(kind, 0) + 1
    if S.is_confirm(w):
        print("  confirm -> answer_confirm", flush=True)
        S.answer_confirm(w)
    elif ai and kind in ("dialog", "base", "unknown", "hud"):
        if S.is_datalinks(w):
            S.key("Return")
        elif kind in ("base", "dialog", "unknown"):
            S.key("Escape")
        time.sleep(0.6)
    elif kind == "hud" and not ai:
        S.click((660, 420))
    elif kind == "title":
        print("  TITLE SCREEN (refusing to click)", flush=True)
        break
print("screens seen:", seen, "year", S.year(), "cur", S.state().get("cur_player"),
      "flags", hex(S.state().get("turn_flags") or 0), flush=True)
