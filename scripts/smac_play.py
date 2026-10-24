#!/usr/bin/env python3
"""SMAC headless turn driver v3 — screen classified by OCR text, turn verified by memory.

Hard-won rules baked in (M9):
  * Keyboard only reaches the game after `xdotool windowfocus <win>` (no WM on Xvfb).
    Without focus every key press is silently dropped.
  * tesseract mangles this pixel font ("units"->"unite"), so dialog detection is a
    fuzzy phrase/difflib match, not exact text.
  * The game interrupts itself: "Some of our units have not moved" confirm dialogs,
    Secret Project movies, base screens (EXPLORE/DISCOVER/BUILD/CONQUER), tech
    breakthroughs. Each needs a different dismissal; blind clicking just re-opens them.
  * A turn may take longer than any fixed click-to-next-frame timeout — poll the year
    in memory instead of timing the animation.

Screen classes -> action:
  hud      (has "Mission Year"/"COMPLETE")  -> click TURN COMPLETE
  confirm  (units-not-moved dialog)         -> select "Yes, end the turn." + OK bar
  base     (GOVERNOR/BUILD/NUTRIENTS/...)   -> Escape
  movie/blank/unknown                       -> Escape, re-check

Usage: python3 smac_play.py --turns 20 [--verbose] [--timeout 120]
Evidence: evidence/trace_<ts>.jsonl, evidence/px_*.png on anomalies only.
Prereq:  sudo sysctl -w kernel.yama.ptrace_scope=0   (Yama resets to 1 every boot)
"""
import argparse, difflib, json, os, random, re, shutil, subprocess, sys, time
from PIL import Image

DISPLAY = ":99"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "evidence")
W, H, SCALE = 800, 600, 2
TURN_BTN = (650, 410)          # fallback if OCR can't find the button
CONFIRM_SENTENCE = ("some of our units have not yet moved this turn do you really want to end "
                    "the turn now")
CONFIRM_PHRASES = ("end the turn", "moved this turn", "really want")
BASE_WORDS = ("governor", "nutrients", "conquer", "discover")
ESC_ALLOW = 0.0                 # wall-clock time before Escape may be pressed at all
WIN = None


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          env={**os.environ, "DISPLAY": DISPLAY})


def find_window():
    out = sh("xdotool search --name \"Sid Meier\"").stdout.split()
    return out[0] if out else None


def focus():
    if WIN:
        sh(f"xdotool windowfocus {WIN}")


def key(k="Escape"):
    focus()
    sh(f"xdotool key --clearmodifiers {k}")


def freeze(tag="t"):
    png = f"/tmp/{tag}.png"
    sh(f"xwd -root -silent -out /tmp/{tag}.xwd && ffmpeg -hide_banner -loglevel error "
       f"-i /tmp/{tag}.xwd -vf crop={W}:{H}:0:0 -y {png}")
    return png


def ocr(png):
    big = png.replace(".png", "_3x.png")
    sh(f"ffmpeg -hide_banner -loglevel error -i {png} -vf "
       f"scale={W*SCALE}:{H*SCALE}:flags=neighbor,format=gray -y {big}")
    out = sh(f"tesseract {big} stdout --psm 6 tsv").stdout
    words = []
    for line in out.splitlines()[1:]:
        f = line.split("\t")
        if len(f) < 12 or not f[11].strip():
            continue
        try:
            x, y, w, h = int(f[6]), int(f[7]), int(f[8]), int(f[9])
        except ValueError:
            continue
        words.append((f[11].strip(), (x + w / 2) / SCALE, (y + h / 2) / SCALE, w / SCALE, h / SCALE))
    return words


BAND = (0, 30, 800, 215)       # captions y~84-104, dialog body to y~180, base tabs
BTN = (520, 375, 280, 90)      # TURN COMPLETE button: (x, y, w, h) — NOT edges
# The text column of a speech/news pane: x 350..630, y 90..320. Deliberately to the
# RIGHT of where those panes put their artwork, because the flat-panel colour test
# fails on a dialog that contains a picture (M14: OPERATIONS DIRECTOR + the Morgan
# "Centauri Monopoly" pyramid, evidence/m15_stuck_screen.png -> 148 colours in the
# old box, 6 here, while the plain HUD gives 90 there).
TEXTCOL = (350, 90, 630, 320)
# The HUD's OWN news/message pane: the strip below the TURN COMPLETE row (that row's
# centre is y~419). News lines there use base-screen vocabulary — on
# evidence/m54a/live_hud.png 'nutrients' is at (355,438), the sentence body runs
# 439-460 and the pane's "Don't Show Again" control sits at y 567 (M54a).
MSGPANE = (0, 425, 800, 600)


def base_word_positions(words):
    """Every BASE_WORDS occurrence, with its coordinates.

    Presence anywhere in the frame cannot mean `base` (M54a): the HUD message pane
    prints news lines, and a line like "...low and is not on = producing enough
    nutrients to meet its..." puts 'nutrients' on screen during a perfectly ordinary
    HUD frame. Session 75: every frame of that position classified `base`, the
    clearing Escape was forbidden (--no-escape > --timeout), and two runs stalled with
    zero year hits.
    """
    out = []
    for t, cx, cy, _w, _h in words:
        low = t.lower().strip(".,:;|_*—")
        if any(b in low for b in BASE_WORDS):
            out.append((int(cx), int(cy)))
    return out


def in_msgpane(pt):
    """True if a word centre falls in the HUD message-pane strip (MSGPANE)."""
    x, y = pt
    return MSGPANE[0] <= x <= MSGPANE[2] and MSGPANE[1] <= y <= MSGPANE[3]


def is_quit_prompt(words):
    """The "Do you really want to quit?" dialog.

    Its banner IS the game title, so the naive `title` test fires on it — which is the
    right REFUSE-to-click answer but the wrong action: Escape on this dialog selects
    "Oops, no, wait!" (safe), while its OK bar exits the game and the process vanishes
    silently. OCR mangles the question ("for" -> "fo"), so match `reallywant` + `quit`
    or the answer row's own words, not the exact sentence.
    """
    ts = re.sub(r"[^a-z]", "", " ".join(w for w, *_ in words).lower())
    return ("reallywant" in ts and "quit" in ts) or ("oops" in ts and "wait" in ts)


def is_cdrom_dialog(words):
    """"CD-ROM was not detected" boot nag. Its caption carries the game TITLE, so the
    `title` test fires on it and the driver quits instead of dismissing it (M14: the
    fresh-boot frame evidence/m15_boot.png classified `title`). Return dismisses it."""
    t = re.sub(r"[^a-z]", "", " ".join(w for w, *_ in words).lower())
    return "cdrom" in t and "detected" in t


def is_loaded_game(words):
    """The LOAD GAME confirm pane: "DIFFICULTY LEVEL: <x>" + "<leader> of the <faction>"
    + OK/CANCEL, drawn OVER the still-visible title art (evidence/m15_loaded_words.png).

    M14 falsification test: this is the screen session 20b lost the game on — it is
    neither `title` (OCR mangles the big title letters behind the pane, so
    `sidmeiersalphacentauri` never appears) nor `hud` (no TURN COMPLETE yet) nor
    `dialog` (its caption sits at y~196, OUTSIDE the 55..180 dialog band), so it fell
    through to `unknown` and the driver's 20 s grace ended in a destructive Escape.

    tesseract reads the caption and the faction line but NOT the "Mission Year" line,
    so trigger on the caption only; "pick"/"choose" excludes the new-game wizard, which
    also says "PICK A DIFFICULTY LEVEL".
    """
    t = re.sub(r"[^a-z]", "", " ".join(w for w, *_ in words).lower())
    return "difficultylevel" in t and "pick" not in t and "choose" not in t


def caption_center(words, want="difficulty"):
    """Centre x of the caption row containing `want` — the pane's own horizontal anchor.

    Measured on evidence/m15_loaded_words.png: caption spans x 293..503 -> centre 398,
    pane centre 400, OK bar centre 290. So OK = caption_centre - 108, caption_y + 194.
    """
    cy = None
    for t, cx, cyy, _w, _h in words:
        if t.lower().strip(".,:;|_*—").startswith(want):
            cy = cyy
            break
    if cy is None:
        return None
    edges = [(cx - ww / 2, cx + ww / 2) for _t, cx, cyy, ww, _h in words if abs(cyy - cy) <= 8]
    if not edges:
        return None
    return ((min(a for a, _ in edges) + max(b for _, b in edges)) / 2, cy)


def ocr_crop(png, box, tag, scale=SCALE):
    """OCR one region and return words in full-frame coordinates."""
    x, y, w, h = box
    out = f"/tmp/{tag}.png"
    sh(f"ffmpeg -hide_banner -loglevel error -i {png} -vf "
       f"crop={w}:{h}:{x}:{y},scale={w*scale}:{h*scale}:flags=neighbor,format=gray -y {out}")
    tsv = sh(f"tesseract {out} stdout --psm 6 tsv").stdout
    words = []
    for line in tsv.splitlines()[1:]:
        f = line.split("\t")
        if len(f) < 12 or not f[11].strip():
            continue
        try:
            bx, by, bw, bh = int(f[6]), int(f[7]), int(f[8]), int(f[9])
        except ValueError:
            continue
        words.append((f[11].strip(), x + (bx + bw / 2) / scale, y + (by + bh / 2) / scale,
                      bw / scale, bh / scale))
    return words


def ocr_fast(png):
    """One full-frame pass at 2x (~0.95 s).

    Region crops were SLOWER (2 ffmpeg + 2 tesseract spawns = 1.9 s) and the small
    button strip is unreadable below 6x, so crop-per-region lost on both counts.
    3x costs 1.85 s for no extra information.
    """
    return ocr(png)


def find(words, targets):
    for t, cx, cy, w, h in words:
        low = t.lower().strip(".,:;|_")
        for want in targets:
            if want.lower() in low:
                return (cx, cy, t)
    return None


def text_of(words):
    t = " ".join(w for w, *_ in words).lower()
    t = re.sub(r"[^a-z0-9 ?!]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def is_confirm(words):
    """Require the actual question, squashed to letters.

    A difflib ratio against the sentence gave false positives on title/map text, and
    tesseract's punctuation varies wildly ("Yes, end the turn." -> "*fes—end-theturn,"),
    so strip everything but a-z and look for the phrase body.
    """
    t = re.sub(r"[^a-z]", "", " ".join(w for w, *_ in words).lower())
    if "endtheturn" not in t:
        return False
    return "moved" in t or "reallywant" in t or "notyet" in t


def region_colors(png, box=(180, 60, 620, 200)):
    """Distinct colours in the upper-centre: a dialog panel is flat (13-33), map text
    sits on terrain (100+). This is what separates a real overlay from map labels."""
    im = Image.open(png).convert("RGB").crop(box)
    return len(im.getcolors(maxcolors=300000) or [])


def classify(words, ncolors=None, png=None):
    """Dialog test: SMAC captions sit at y~102 with a body block at y~130-160.

    Colour counting can't separate a dialog from an unexplored (black) map, and OCR
    misreads the caption itself, so use geometry + mass instead of vocabulary.
    """
    if is_confirm(words):
        return "confirm"
    t = text_of(words)
    ts = re.sub(r"[^a-z]", "", t)
    # The HUD's identity is its TURN COMPLETE row at y~419. Compute it up front: the
    # base test below has to know whether the HUD is even on screen (M54a).
    btn = find(words, ["complete"])
    hud_btn = bool(btn) and 380 < btn[1] < 450
    # Boot nag and LOAD confirm both wear the game title in their caption/ backdrop;
    # test them BEFORE `title` or the driver quits instead of answering them (M14).
    if is_cdrom_dialog(words):
        return "cdrom"
    if is_loaded_game(words):
        return "loaded-game"
    # The quit dialog wears the game title as its banner, so `title` fires on it and the
    # run stops (M54a: trace_m54a40c turn 13 — an `unknown` frame's last-resort Escape
    # opened it). Test it first: this one has a SAFE answer, the title screen does not.
    if is_quit_prompt(words):
        return "quit-prompt"
    # Title/menu screens: NEVER click these. Escape on the title selects "Exit" and the
    # quit dialog's OK ends the session (both happened; 120 turns of play lost).
    if "sidmeiersalphacentauri" in ts or "reallywanttoquit" in ts:
        return "title"
    # breakthrough/news panels are full screens: Escape closes them (verified)
    if "breakthrough" in t or "researchers" in t:
        return "unknown"
    # M54a: this test used to be `any(w in t for w in BASE_WORDS)`, which the HUD's own
    # message pane defeats — its news lines say "nutrients"/"low"/"producing", so every
    # frame of a plain HUD position read `base`, the driver Escaped (or, with
    # --no-escape > --timeout, did nothing) and TURN COMPLETE was never clicked.
    # Base words count only OUTSIDE that bottom strip, and only while the HUD button row
    # is absent: a real base screen (evidence/m54a/base_screen.png, from m45a_post.png)
    # has no TURN COMPLETE row at all, so its MENU/tab words still classify `base`.
    hits = base_word_positions(words)
    if hits and not (hud_btn and all(in_msgpane(p) for p in hits)):
        return "base"
    # A dialog's text block is centred in the upper half and dominates the OCR output.
    # This test must run BEFORE the HUD test: speech/news dialogs are drawn over a
    # still-visible HUD, so the TURN COMPLETE button is on screen but unreachable.
    upper = sum(1 for _t, cx_, cy, _w, _h in words if 55 <= cy <= 180 and 180 <= cx_ <= 620)
    if upper >= 10 and (ncolors is None or ncolors < 45):
        return "dialog"
    # Second chance: a pane with ARTWORK inside the old sample box is not flat there,
    # but its text column still is (see TEXTCOL). Without this the driver reads such a
    # modal as `hud` (TURN COMPLETE is still drawn beneath it) and hammers the map
    # while the pane blocks the turn — the M14 156 s "STUCK" turn.
    if upper >= 10 and png is not None and region_colors(png, TEXTCOL) < 45:
        return "dialog"
    if hud_btn:
        return "hud"
    # The HUD is identified by its TURN COMPLETE button at y~416, nothing else: the
    # tech-breakthrough screen also contains the words "Mission Year" in its panels.
    if len(words) < 15:
        return "movie"
    return "unknown"


def click(xy):
    focus()
    sh(f"xdotool mousemove {int(xy[0])} {int(xy[1])} click 1")


def text_has(words, *needles):
    t = text_of(words)
    return any(n in t for n in needles)


def is_datalinks(words):
    """PSI-COMBAT / DATALINKS pages take Return (M27); they are plain full-screen text."""
    return text_has(words, "datalinks", "psicombat", "psicombatdatalinks")


def is_ops_director(words):
    """OPERATIONS DIRECTOR pane (opened with a base screen) takes exactly one Escape."""
    return text_has(words, "operationsdirector", "operations")


def find_yes_row(words):
    """y of the "Yes, end the turn." row, or the verified default 196.

    Never use a bare substring search for "yes": the unit panel OCRs as "Moyes:" at
    y=521 and a naive match clicks the map instead of the dialog.
    """
    for t, cx, cy, _w, _h in words:
        low = t.lower().strip(".,:;|_*—")
        if 160 <= cy <= 220 and 150 <= cx <= 660 and (low.startswith("yes") or "turn" in low):
            return int(cy)
    return 196


def answer_confirm(words):
    y = find_yes_row(words)
    click((400, y)); time.sleep(1.2)       # select "Yes, end the turn."
    click((400, y + 26)); time.sleep(1.2)  # OK bar ~26 px below. Verified: <1 s and the
                                           # OK click confirms the OLD selection ("No, let
                                           # me move them") and the same dialog reopens.


def answer_loaded_game(words):
    """Click the LOAD confirm pane's OK bar (verified live 2026-10-20 23:16: OK at
    (290,391) on evidence/m15_loaded_words.png -> next frame classified `hud`).

    Position is derived from the caption row rather than hard-coded, per the harness
    rule that fixed coordinates drift between UI states.
    """
    c = caption_center(words)
    x, y = (c[0] - 108, c[1] + 194) if c else (290, 391)
    click((x, y))
    return (x, y)


# ---------------------------------------------------------------------------
# M54a — the panes that blocked session 75's round (recipe: evidence/m53s_findings.md
# "Driving"; bar finder: evidence/m53s_barclick.py, which is what actually closed it).
#
#   * "Do you really want to end the turn now?"  -> answer_confirm (already in the driver)
#   * the Council PROPOSAL vote: three bars at y~498, x = 311 / 400 / 489. Their dark
#     labels are invisible to tesseract on this build (verified 2026-10-24: `tesseract
#     tsv` returns zero hits for yea/nay/abstain/ok), so the row is found by COLOUR
#     GEOMETRY, never by OCR.
#   * the HIVE bribe pane: Escape closes it, Return advances the round.
#
# A vote row is >=3 bars of the same height on one line >100 px apart; anything else is
# an OK bar and gets the proven bottom-most click.


def light_bar_rows(png, y0=200, min_run=55):
    """Raw-pixel scan for the game's light periwinkle push-bars (run > min_run px).

    PIL, not `ffmpeg -f rawvideo -`: piping raw RGB through smac_play.sh() (text=True)
    blows up with a UnicodeDecodeError on the first non-UTF-8 byte, and a per-pixel
    PIL row read costs ~0.3 s for the whole 400x800 band, which is cheap next to OCR.
    """
    im = Image.open(png).convert("RGB")
    out = []
    for y in range(y0, H):
        light = [b > 120 and r > 90 and g > 90 and abs(r - g) < 40 and b - r > 25
                 for r, g, b in im.crop((0, y, W, y + 1)).getdata()]
        start = None
        for x, on in enumerate(light):
            if on and start is None:
                start = x
            elif not on and start is not None:
                if x - start > min_run:
                    out.append((y, start, x, (start + x) // 2))
                start = None
    return out


def group_bars(found):
    """Collapse consecutive scanlines of the same bar into (cx, cy, height)."""
    groups = []
    for y, x0, x1, cx in found:
        for g in groups:
            if 0 <= y - g[3] <= 2 and abs(g[4] - x0) <= 6 and abs(g[5] - x1) <= 6:
                g[3] = y
                break
        else:
            groups.append([cx, (x0 + x1) // 2, y, y, x0, x1])
    return [(g[0], (g[2] + g[3]) // 2, g[3] - g[2] + 1) for g in groups]


def pane_bars(png):
    """Tall (>=12 px) push-bars in the frame — bars are ~18 px tall."""
    return [b for b in group_bars(light_bar_rows(png)) if b[2] >= 12]


def is_vote_row(bars):
    """>=3 bars on one row >100 px apart: that is a vote, not an OK bar."""
    for b in bars:
        row = [c for c in bars if abs(c[1] - b[1]) <= 6]
        if len(row) >= 3 and max(c[0] for c in row) - min(c[0] for c in row) > 100:
            return sorted(row, key=lambda c: c[0])
    return None


def is_council_pane(words):
    """The Council convenes as PROTOCOL DIRECTOR -> PROPOSAL vote; the HIVE bribe pane is
    its own thing. Captions DO OCR (only the bar labels don't), so the pane is named by
    its caption."""
    return text_has(words, "council", "proposal", "protocol", "hive", "senate", "delegate")


def is_hive_pane(words):
    return text_has(words, "hive")


def handle_pane(words, png, rec, kind):
    """Click/keys for the modals that have no OCR-readable control. True = acted.

    Two triggers, and only two (M54a, learned the hard way on evidence/m54a/stuck_pane.png):
      * a 3-bar VOTE ROW (>=3 bars, same line, >100 px apart) is unambiguous geometry — the
        Council PROPOSAL vote, click YEA = leftmost (310,495 measured, wine-operations).
      * a single bar is clicked only when the pane's CAPTION names a Council/HIVE pane
        (PROTOCOL DIRECTOR's OK bar at (393,495), the bribe pane's bars).
    Everything else — including the "OUR CITIZENS ARE STARVING" alert, whose bar at
    (310,221) is its "Zoom to base control" button and which clicking did NOT clear
    (trace_m54a40: two identical `bar@310,221` hits, turn STUCK 277.8 s) — falls through to
    the generic dialog path, which is `Return` = the pane's default button.
    """
    if is_hive_pane(words):
        key("Escape"); time.sleep(0.6)          # verified 2026-10-24: Escape closes the
        key("Return"); time.sleep(0.8)          # HIVE bribe pane, Return advances
        rec["handled"].append("hive-bribe:Escape+Return")
        return True
    if kind == "base":                          # a base screen has progress bars that
        return False                            # pass the colour test — never click them
    bs = pane_bars(png)
    if not bs:
        return False
    row = is_vote_row(bs)
    if row is None and not is_council_pane(words):
        return False                            # not ours: let the caller press Return
    target = row[0] if row else sorted(bs, key=lambda b: b[1])[-1]
    click((target[0], target[1]))
    rec["handled"].append(("vote-yea" if row else "bar") +
                          f"@{int(target[0])},{int(target[1])}" +
                          ("/council" if is_council_pane(words) else ""))
    time.sleep(1.6)
    return True


def state():
    out = sh(f"python3 {ROOT}/scripts/smac_state.py --json").stdout.strip()
    try:
        return json.loads(out)
    except Exception:
        return {}


def year():
    return state().get("year")


def wait_year_change(old, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if year() != old:
            return True, time.time() - t0
        time.sleep(1.0)
    return False, timeout


def do_turn(idx, tr, timeout, verbose=False):
    y0 = year()
    rec = {"turn": idx, "year_before": y0, "t": time.strftime("%H:%M:%S"), "handled": []}
    pressed = False
    for attempt in range(8):
        words = ocr(freeze("px"))
        kind = classify(words)
        rec["handled"].append(kind)
        if verbose:
            print(f"    [{kind}] {' '.join(w for w, *_ in words[:18])}", flush=True)
        if kind == "hud":
            if pressed:
                break                     # already pressed; let the wait decide
            btn = find(words, ["complete"])
            click((btn[0], btn[1]) if btn else TURN_BTN)
            pressed = True
            time.sleep(0.6)
            # a confirm dialog usually appears right after the press
            w2 = ocr(freeze("px2"))
            if is_confirm(w2):
                rec["handled"].append("confirm-after-press")
                answer_confirm(w2)
            break
        if kind == "confirm":
            answer_confirm(words)
            pressed = True
            continue
        if kind == "dialog":
            # Enter activates the dialog's default button (works only with window focus).
            # If Enter navigates into another screen, the next round ESCs back out.
            rec.setdefault("dialogs", []).append(len(words))
            key("Return"); time.sleep(1.8)
            continue
        # base screen / movie / unknown: back out and re-classify
        key("Escape"); time.sleep(2.0)
    ok, dt = wait_year_change(y0, timeout)
    rec["year_after"] = year(); rec["advanced"] = ok; rec["dt"] = round(dt, 1)
    if not ok:
        sh(f"cp {freeze('stuck')} {EVID}/px_stuck_t{idx}.png")
        rec["stuck"] = True
    print(f"turn {idx}: {y0}->{rec['year_after']} {'OK' if ok else 'STUCK'} "
          f"({rec['dt']}s, {','.join(rec['handled'])})", flush=True)
    tr.write(json.dumps(rec) + "\n"); tr.flush()
    return ok


def service_turn(idx, tr, timeout, verbose=False):
    """Press TURN COMPLETE, then keep servicing whatever the game throws up until the
    mission year in memory actually changes.

    Turns are not a single click: during one turn the game raises the units-not-moved
    confirm, NETFLASH news, tech breakthroughs, Secret Project movies and base screens.
    Every one of those blocks the turn, so a one-shot click-then-wait always times out.
    """
    y0 = year()
    st0 = state()
    rec = {"turn": idx, "year_before": y0, "t": time.strftime("%H:%M:%S"), "handled": []}
    t0 = time.time()
    last_press = 0.0
    last_esc = 0.0
    while time.time() - t0 < timeout:
        if not sh("xdotool search --name \"Sid Meier\"").stdout.strip():
            sys.exit("game window gone — driver stopped (avoid pretending the run continued)")
        if year() != y0:
            break
        png = freeze("px")
        words = ocr_fast(png)
        kind = classify(words, region_colors(png), png)
        rec["handled"].append(kind)
        if verbose:
            print(f"    [{kind}] {' '.join(w for w, *_ in words[:16])}", flush=True)
        rec.setdefault("screens", {}).setdefault(kind, 0)
        rec["screens"][kind] += 1
        # M54a: the Council vote row and the HIVE bribe pane come up in BOTH phases (the
        # Council convenes while cur_player is an AI), and neither has a control OCR can
        # see, so they get a handler ahead of the generic dialog/Escape paths.
        if kind in ("dialog", "unknown") and handle_pane(words, png, rec, kind):
            time.sleep(0.4)
            continue
        # Whose turn is it *right now*?  During the AI phase the HUD is still drawn and
        # TURN COMPLETE is still on screen, so an OCR-only driver clicks it into a
        # half-finished AI turn and then sits in a modal for the whole timeout (M27:
        # 2198->2199 stalled at cur_player=AI with turn_flags&2).  Ask memory instead.
        st = state()
        own, cur = st.get("player"), st.get("cur_player")
        tf = st.get("turn_flags") or 0
        ai_phase = (own is not None and cur is not None and cur != own) or bool(tf & 2)
        if ai_phase and kind in ("dialog", "base", "unknown", "hud"):
            rec["handled"].append(f"ai-phase:{kind}")
            if is_datalinks(words):
                key("Return"); time.sleep(0.5)          # full-screen text page
            elif is_ops_director(words) or kind == "base":
                key("Escape"); time.sleep(0.8)          # pane closes, game stays
            elif kind == "hud":
                time.sleep(0.5)                         # plain map during the AI phase
            elif time.time() - last_esc > 2.5:
                key("Return"); last_esc = time.time()   # default button = OK
            time.sleep(0.3)
            continue
        if kind == "quit-prompt":
            # Escape = "Oops, no, wait!". NEVER click OK here: that exits the game and
            # the process vanishes silently (the trap that killed the 120-turn run).
            key("Escape"); time.sleep(1.2)
            rec["handled"].append("quit-prompt:Escape=oops")
            continue
        if kind == "title":
            sh(f"cp {png} {EVID}/px_title_t{idx}.png")
            sys.exit("driver stopped: game is at the title/quit screen — refusing to click menus")
        if kind == "loaded-game":
            xy = answer_loaded_game(words)
            rec["handled"].append(f"loaded-ok@{int(xy[0])},{int(xy[1])}")
            time.sleep(1.5)
        elif kind == "cdrom":
            key("Return"); time.sleep(1.0)
        elif kind == "confirm":
            answer_confirm(words)
        elif kind == "dialog":
            key("Return"); time.sleep(0.5)      # default button = OK
        elif kind == "hud":
            if time.time() - last_press > 6:
                btn = find(words, ["complete"])
                click((btn[0], btn[1]) if btn else TURN_BTN)
                last_press = time.time()
                # poll the year before paying for another OCR: the confirm dialog is
                # only worth looking for while the turn is still unflipped
                flipped = False
                for _ in range(4):
                    time.sleep(0.15)
                    if year() != y0:
                        flipped = True; break
                if not flipped:
                    w2 = ocr_fast(freeze("px2"))
                    if is_confirm(w2):
                        rec["handled"].append("confirm-after-press")
                        answer_confirm(w2)
        else:                                    # base screen / movie / unknown
            # Never spam Escape on unrecognized/dark screens: on the title menu Escape
            # can land on "Exit" and end the session (process vanished at year 2181).
            # movies end on their own; only escape a genuinely stuck screen.
            # ESC_ALLOW (--no-escape) gates it entirely for the first N seconds so a
            # mis-classified startup screen cannot quit the game out from under a test.
            if time.time() - last_esc > 20 and time.time() > ESC_ALLOW:
                key("Escape"); last_esc = time.time()
            time.sleep(0.4)
        # cheap year poll instead of a fat fixed sleep
        for _ in range(8):
            if year() != y0:
                break
            time.sleep(0.15)
    ok = year() != y0
    st1 = state()
    rec["state_before"] = {k: st0.get(k) for k in ("year", "turn_no", "player", "cur_player",
                                                   "turn_flags", "mode_flags", "n_bases")}
    rec["state_after"] = {k: st1.get(k) for k in ("year", "turn_no", "player", "cur_player",
                                                  "turn_flags", "mode_flags", "n_bases")}
    rec["delta"] = {k: [st0.get(k), st1.get(k)] for k, v in rec["state_after"].items()
                    if st0.get(k) != v}
    rec["year_after"] = year(); rec["advanced"] = ok; rec["dt"] = round(time.time() - t0, 1)
    if not ok:
        sh(f"cp {freeze('stuck')} {EVID}/px_stuck_t{idx}.png")
        rec["stuck"] = True
    print(f"turn {idx}: {y0}->{rec['year_after']} {'OK' if ok else 'STUCK'} "
          f"({rec['dt']}s, {','.join(rec['handled'][:6])})", flush=True)
    tr.write(json.dumps(rec) + "\n"); tr.flush()
    return ok


# ---------------------------------------------------------------------------
# M33 — the driver ISSUES A REAL ORDER (C2 close).
#
# Model (ORDERS.md, live-proven M32): with orders mode on (0x91b5b8 != 0) and a unit
# selected (0x91b5bc >= 0), a terraform hotkey reaches FUN_00512b40 -> FUN_00512450 ->
# FUN_004d44d0(unit, mode) (mode = alpha.txt #TERRAIN index). The setter runs
# SYNCHRONOUSLY inside the key handler: it gates (Former class 9, terrain, tech), shows
# the payment dialogs (Want_to_terraform picker -> TERRACOST message -> TERRAPAY itemlist
# "Cancel action. / Expend $NUM0 credits."), debits faction energy
# (0x94d650[player*0x82f], store at 0x4d561a), then writes the order byte
# (+17 = mode+4, store at 0x4d5bbf) and broadcasts (call 0x584350 @ 0x4d5bc6).
# So the modal must be serviced WHILE the setter call is still on the stack — the
# order byte only appears after the player answers the payment pane.
#
# Selection: the driver pokes the selected-unit global (0x91b5bc). That is a UI-slot
# poke (M25 proved /proc/pid/mem pokes persist); the ORDER itself is issued entirely
# by the game's own handlers from a real keypress. FUN_0040c8d0(idx,...) is the game's
# own select routine (owner + can-act gates) — the scan below re-implements its FILTER,
# not its side effects.
UNIT_ARR = 0x933278
SEL_G = 0x91B5BC
ORDERS_MODE_G = 0x91B5B8
ENERGY_G = 0x94D650
ENERGY_STRIDE = 0x82F
TILE_G = 0x92AE14
TILE_ROW = 40                     # DAT_00692184, read live = 40
TILE_SZ = 0x2C

# hotkey -> #TERRAIN mode (ORDERS.md §2 table; xdotool key names)
ORDER_KEYS = {
    "f": 0, "M": 2, "m": 2, "S": 3, "s": 3, "F": 4, "r": 5, "K": 7, "k": 7,
    "period": 8, "o": 9, "n": 0xc, "E": 0xd, "B": 0xe, "q": 0xf,
    "bracketright": 0x10, "bracketleft": 0x11, "underscore": 0x12,
}


def mem():
    pid = int(sh("pgrep -x terran.exe").stdout.split()[0])
    return pid, open(f"/proc/{pid}/mem", "rb+", 0)


def rd(f, addr, n):
    f.seek(addr)
    return f.read(n)


def wr(f, addr, data):
    f.seek(addr)
    f.write(data)
    f.flush()


def unit_rec(f, idx):
    d = rd(f, UNIT_ARR + idx * 52, 52)
    import struct
    return dict(x=struct.unpack("<h", d[0:2])[0], y=struct.unpack("<h", d[2:4])[0],
                flags=struct.unpack("<I", d[4:8])[0], type=struct.unpack("<H", d[10:12])[0],
                owner=d[14], order=d[17], mpused=d[40],
                raw=d)


def unit_class(f, typ):
    import struct
    return struct.unpack("<I", rd(f, 0x98ADB2 + typ * 52, 4))[0] & 0xFF


def find_former(f, me):
    """Indices of live, actionable Formers owned by us — the filter of the game's own
    select routine FUN_0040c8d0 (owner == player, mp remaining via +40, not frozen)."""
    import struct
    out = []
    arr = rd(f, UNIT_ARR, 300 * 52)
    for i in range(300):
        d = arr[i * 52:(i + 1) * 52]
        if d[14] != me or d[14] == 0xFF:
            continue
        typ = struct.unpack("<H", d[10:12])[0]
        cls = unit_class(f, typ)
        frozen = bool(d[9])                       # +9 != 0 in FUN_0040c8d0
        if cls == 9 and not frozen:
            out.append(dict(idx=i, x=struct.unpack("<h", d[0:2])[0],
                            y=struct.unpack("<h", d[2:4])[0],
                            flags=struct.unpack("<I", d[4:8])[0], order=d[17], mpused=d[40]))
    return out


def energy(f, player):
    import struct
    return struct.unpack("<i", rd(f, ENERGY_G + player * ENERGY_STRIDE * 4, 4))[0]


def tile_recs(f, x, y):
    """The 0x2c tile record for (x,y): base + (40*y + x>>1)*0x2c (asm-verified at
    0x4d5b25: imul stride, *11 dwords). Neighbours N/S are +/-(40*0x2c); E/W +/-0x2c."""
    a = TILE_G + (TILE_ROW * y + (x >> 1)) * TILE_SZ
    return a, rd(f, a, TILE_SZ)


def is_terraform_pane(words):
    """TERRAPAY ('Expend N credits.' / 'Cancel action.') or the Want_to_terraform
    picker ('Continue.'/'Cancel action.') or TERRACOST ('cost N credits')."""
    t = text_of(words)
    return ("expend" in t and "credit" in t) or "wanttoterraform" in t or \
           ("cost" in t and "credit" in t and "reserves" in t)


def answer_terraform_pane(words, verbose=False):
    """Click the accept row, then the OK bar >=1.2 s later (M29 rule: faster confirms the
    PREVIOUS selection). Returns the word it acted on, or None when nothing clickable."""
    target = None
    for t, cx, cy, w, h in words:
        low = t.lower().strip(".,:;|_*—")
        if low.startswith("expend") or low.startswith("continue"):
            target = (int(cx), int(cy), low)
            break
    if target:
        x, y, low = target
        click((x, y)); time.sleep(1.4)
        click((x, y + 26)); time.sleep(1.4)       # OK bar below the row (answer_confirm pattern)
        if verbose:
            print(f"    clicked {low!r} row at ({x},{y}) + OK", flush=True)
        return low
    # message panes (TERRACOST etc.) and anything else: default button
    key("Return"); time.sleep(1.0)
    if verbose:
        print("    Return (default button)", flush=True)
    return "return"


def give_order(kname, unit_idx=None, modal_timeout=60.0, verbose=False, tag="m33",
               verify=True, key_only=False):
    """Issue one terraform order through the game's own handlers and prove the effect.

    Returns a record dict; None on preflight failure.
    """
    mode = ORDER_KEYS.get(kname)
    if mode is None:
        print(f"unknown order key {kname!r}; known: {sorted(ORDER_KEYS)}")
        return None
    pid, f = mem()
    st = state()
    me = st.get("player")
    # preflight: HUD only (modal = key sink, M32), our turn
    png = freeze("pre")
    words = ocr_fast(png)
    kind = classify(words, region_colors(png), png)
    if kind != "hud":
        print(f"preflight: screen={kind}, not hud — refusing to press order keys")
        sh(f"cp {png} {EVID}/{tag}_preflight_{kind}.png")
        return None
    cands = find_former(f, me)
    if unit_idx is None:
        cands = [c for c in cands if c["order"] == 0] or cands
        if not cands:
            print("no Former owned by us — nothing to order")
            return None
        unit_idx = cands[0]["idx"]
    u = unit_rec(f, unit_idx)
    if unit_class(f, u["type"]) != 9:
        print(f"rec{unit_idx} class {unit_class(f, u['type'])} != 9 (Former) — abort")
        return None
    e0 = energy(f, me)
    ta, t0 = tile_recs(f, u["x"], u["y"])
    # M33 pitfalls baked in:
    #  * pokes through /proc/pid/mem are UNRELIABLE while a tracer (gdb) is attached —
    #    the write readbacks lie. Poke only with no tracer; verify after kill -CONT.
    #  * the game's own selection cycle re-validates the selection on pump iterations:
    #    a poked selection that fails the gate is replaced within a frame or two. So:
    #    poke, then press the key IMMEDIATELY (no sleep) — the X event dispatches
    #    before the next pump iteration. Verified: 'f' landed on the poked rec that way.
    #  * advisor panes (road/fungus/etc.) are TRANSIENT (auto-dismiss ~1-2 s, faster
    #    than one OCR poll) and while up they SWALLOW the next input event (menu-code
    #    echoes like 0x20011). A rejected order looks exactly like a dropped keypress.
    sel = __import__("struct").unpack("<i", rd(f, SEL_G, 4))[0]
    focus()
    if sel != unit_idx and not key_only:
        wr(f, SEL_G, __import__("struct").pack("<i", unit_idx))
    sh(f'xdotool key --clearmodifiers "{kname}"')
    print(f"selected rec{unit_idx} at ({u['x']},{u['y']}) type {u['type']} "
          f"order {u['order']} | energy={e0} | tile@{ta:#x} +8={t0[8:12].hex()}", flush=True)
    t0p = time.time()
    panes = []
    order_landed = None
    quiet = 0
    while time.time() - t0p < modal_timeout:
        if verify:
            u2 = unit_rec(f, unit_idx)
            if u2["order"] == mode + 4:
                order_landed = u2["order"]
                break
        png = freeze("mid")
        w2 = ocr_fast(png)
        k2 = classify(w2, region_colors(png), png)
        if k2 == "hud":
            time.sleep(0.6)
            continue
        if k2 in ("dialog", "confirm", "unknown") and is_terraform_pane(w2):
            panes.append(("terraform:" + k2, [t for t, *_ in w2[:12]]))
            acted = answer_terraform_pane(w2, verbose)
            quiet = 0
            if acted is None:
                break
            time.sleep(0.8)
            continue
        if k2 == "hud":
            quiet += 1
            if not verify and quiet >= 3:      # panes settled; gdb run ends via run script
                break
        if k2 == "title":
            sh(f"cp {png} {EVID}/{tag}_title.png")
            print("game hit title/quit screen — stop")
            return None
        # advisor message panes (NEEDTERRAFORMERS etc.) and strays: dismiss
        panes.append((k2, [t for t, *_ in w2[:12]]))
        if time.time() > ESC_ALLOW:
            key("Return"); time.sleep(0.8)
        else:
            time.sleep(0.8)
    if not verify:
        rec = dict(t=time.strftime("%H:%M:%S"), pid=pid, key=kname, mode=mode,
                   unit=unit_idx, ux=u["x"], uy=u["y"], verify="external",
                   panes=[p0[0] for p0 in panes], pane_words=panes)
        print(json.dumps(rec, indent=1))
        return rec
    u1 = unit_rec(f, unit_idx)
    e1 = energy(f, me)
    t1 = rd(f, ta, TILE_SZ)
    diff = [f"+{i:02x}:{a:02x}->{b:02x}" for i, (a, b) in enumerate(zip(t0, t1)) if a != b]
    rec = dict(t=time.strftime("%H:%M:%S"), pid=pid, key=kname, mode=mode,
               unit=unit_idx, ux=u["x"], uy=u["y"],
               order_before=u["order"], order_after=u1["order"],
               energy_before=e0, energy_after=e1, energy_delta=e1 - e0,
               tile_addr=hex(ta), tile_before=t0.hex(), tile_after=t1.hex(), tile_diff=diff,
               panes=[p[0] for p in panes], pane_words=panes,
               flags_after=hex(u1["flags"]), mpused_after=u1["mpused"])
    print(json.dumps(rec, indent=1))
    path = os.path.join(EVID, f"{tag}_order.json")
    with open(path, "w") as fh:
        json.dump(rec, fh, indent=1)
    print("record:", path)
    return rec


def main():
    global WIN, ESC_ALLOW
    ap = argparse.ArgumentParser()
    ap.add_argument("--turns", type=int, default=5)
    ap.add_argument("--timeout", type=float, default=120)
    ap.add_argument("--no-escape", type=float, default=60.0,
                    help="seconds at the start of the run during which Escape is never pressed")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--order", default=None,
                    help="M33: issue this terraform hotkey (f r M S o n E B q . K m s F) then verify")
    ap.add_argument("--unit", type=int, default=None, help="unit index to order (default: first Former)")
    ap.add_argument("--turns-after", type=int, default=0, help="turns to advance after the order")
    ap.add_argument("--tag", default="m33")
    ap.add_argument("--no-verify", action="store_true",
                    help="skip in-loop/post memory reads (use when a tracer holds the process)")
    ap.add_argument("--key-only", action="store_true",
                    help="skip the selection poke (poke BEFORE arming the tracer; pokes are ignored under ptrace)")
    a = ap.parse_args()
    ESC_ALLOW = time.time() + a.no_escape
    run_seed = random.randrange(1 << 31)   # recorded in the trace header (M54a)
    os.makedirs(EVID, exist_ok=True)
    for tool in ("xdotool", "xwd", "ffmpeg", "tesseract"):
        if not shutil.which(tool):
            sys.exit(f"missing {tool}")
    WIN = find_window()
    if not WIN:
        sys.exit("game window not found")
    s = state()
    if not s.get("year"):
        sys.exit(f"cannot read game state: {s}")
    print(f"win={WIN} start year={s['year']}", flush=True)
    if a.order:
        rec = give_order(a.order, a.unit, verbose=a.verbose, tag=a.tag,
                         verify=not a.no_verify, key_only=a.key_only)
        if rec is None:
            sys.exit("order not issued")
        if a.turns_after:
            path = os.path.join(EVID, f"trace_{a.tag}_after_{time.strftime('%Y%m%d_%H%M%S')}.jsonl")
            with open(path, "w") as tr:
                for i in range(a.turns_after):
                    service_turn(i, tr, a.timeout, a.verbose)
            print("post-order turn trace:", path)
        sys.exit(0)
    path = os.path.join(EVID, f"trace_{a.tag}_{time.strftime('%Y%m%d_%H%M%S')}.jsonl")
    stuck = 0
    # M54a acceptance wants a trace per run carrying seed + action log + per-turn state
    # deltas. `seed` is the RUN seed: scripts/smac_state.py exposes no game RNG seed, so
    # the position is pinned instead by the start state on the same line.
    hdr = {"type": "start", "seed": run_seed, "tag": a.tag, "turns": a.turns,
           "timeout": a.timeout, "no_escape": a.no_escape, "argv": sys.argv[1:],
           "state": s}
    with open(path, "w") as tr:
        tr.write(json.dumps(hdr) + "\n")
        for i in range(a.turns):
            if service_turn(i, tr, a.timeout, a.verbose):
                stuck = 0
            else:
                stuck += 1
                if stuck >= 2:
                    print("two consecutive stalls — stopping"); break
    print("trace:", path)


if __name__ == "__main__":
    main()
