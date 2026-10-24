#!/usr/bin/env python3
"""M53s: click the bottom-most light bar on any Council/bribe pane until the
round returns to the human player.  Bars are found by COLOUR GEOMETRY (the game's
pushed bars are light periwinkle: b>120, r,g>90, b-r>25, run > 55 px), because
tesseract cannot segment their dark label text (verified 2026-10-24: `tesseract tsv`
returned zero hits for yea/nay/abstain/ok on the PROPOSAL pane).
"""
import os, re, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import smac_play as S  # noqa: E402

LIMIT = float(sys.argv[1]) if len(sys.argv) > 1 else 120.0
W, H = 800, 600


def bars(png):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", png, "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    out = []
    for y in range(200, H):
        row = raw[y * W * 3:(y + 1) * W * 3]
        runs, start = [], None
        for x in range(W):
            r, g, b = row[x * 3:x * 3 + 3]
            light = b > 120 and r > 90 and g > 90 and abs(r - g) < 40 and b - r > 25
            if light and start is None:
                start = x
            elif not light and start is not None:
                if x - start > 55:
                    out.append((y, start, x, (start + x) // 2))
                start = None
    return out


def group_bars(found):
    """collapse consecutive scanlines of the same bar into (cx, cy, height)."""
    groups = []
    for y, x0, x1, cx in found:
        for g in groups:
            if 0 <= y - g[3] <= 2 and abs(g[4] - x0) <= 6 and abs(g[5] - x1) <= 6:
                g[3] = y
                break
        else:
            groups.append([cx, (x0 + x1) // 2, y, y, x0, x1])
    return [(g[0], (g[2] + g[3]) // 2, g[3] - g[2] + 1) for g in groups]


S.find_window()
t0 = time.time()
log = []
while time.time() - t0 < LIMIT:
    st = S.state()
    if st.get("cur_player") == st.get("player") and not (st.get("turn_flags") or 0) & 2:
        print("ROUND DONE: back to human, flags", hex(st.get("turn_flags") or 0), flush=True)
        break
    png = S.freeze("m53s_bar")
    bs = group_bars(bars(png))
    tall = [b for b in bs if b[2] >= 12]          # bars are ~18 px tall
    if not tall:
        log.append(("no-bar", st.get("cur_player")))
        time.sleep(2)
        continue
    cx, cy = tall[-1][0], tall[-1][1]             # bottom-most bar
    words = S.ocr_fast(png)
    log.append(("click (%d,%d) h=%d n=%d" % (cx, cy, tall[-1][2], len(tall)),
                " ".join(w for w, *_ in words[:6])[:60]))
    print("  click (%d,%d) bars=%d text=%r" % (cx, cy, len(tall),
          " ".join(w for w, *_ in words[:8])[:70]), flush=True)
    S.click((cx, cy))
    time.sleep(2.5)
print("log:", log[-6:], flush=True)
st = S.state()
print("end: year", S.year(), "cur", st.get("cur_player"), "flags", hex(st.get("turn_flags") or 0),
      flush=True)
