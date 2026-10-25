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
from hashlib import md5
from PIL import Image

DISPLAY = ":99"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "evidence")
W, H, SCALE = 800, 600, 2
TURN_BTN = (650, 410)          # fallback if OCR can't find the button
MENU_BTN = (61, 369)           # in-game console MENU button (m54b_menu.png, 2026-10-24);
                               # the wedge probe clicks it: dead input = bad save slot
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


def is_help_page(words):
    """The HELP browser (FACTION PROFILES / CONCEPTS / ADVANCED ... pages).

    Opened by accident when a stray click lands in the help menu columns at the bottom of
    the HUD (M54a: a `vote-yea@44,567` click opened it and the round stalled twice —
    Escape does NOT close this screen, only its EXIT bar does).
    """
    t = text_of(words)
    return ("concepts" in t and "categories" in t) or "faction profiles" in t \
        or "chassis types" in t or ("advances" in t and "abilities" in t)


def is_communication(words, png=None):
    """A faction COMMUNICATION pane: "<FACTION> - <MOOD>" banner, a QUOTED demand in the
    upper pane, portrait at left, one wide OK bar across the pane at y~347.

    Measured on `evidence/m54c/comm_pane.png` (session 80, the frame that stuck turn 35 of
    trace_m54c40b for 735 s): banner "BELIEVERS - SEETHING" at y 16, the quoted line
    "You are a contemptuous parasite, Zakharov, ..." at y 45, and pane_bars seeing the OK
    bar's dithered ends at (266,347) and (534,347).

    The quote is the discriminator: the Council's own panes wear the same banner style
    ("GAIANS - OBSTINATE", answer_council_dialog) but print their text UNQUOTED, and the
    HELP browser's banner has no dash. The bar-row test keeps a mis-read quote from
    turning some other pane into a clickable comm.
    """
    banner = quoted = False
    for t, cx, cy, w, h in words:
        low = t.lower().strip(".,:;|_* ")
        if cy <= 40 and low in ("-", "--", "—", "–", "-seething", "-obstinate"):
            banner = True
        if 20 <= cy <= 140 and any(q in t for q in ('"', "“", "”", "„", "“")):
            quoted = True
    if not (banner and quoted):
        return False
    if png is None:
        return True
    return any(330 <= b[1] <= 365 for b in pane_bars(png, y0=330))


def modal_caption(words):
    """Is something drawn OVER the HUD? Long words in the caption band (y 90-118).

    A clean HUD has nothing there: its message pane sits at y 240-330 and the map's base
    labels at y~230 (measured on the frames the classifier tests save; the only tokens 2x OCR
    puts in 90-118 on a clean HUD are 2-3 character noise like 'it'/'rll'). Two words of 4+
    characters, or one of 6+, means a modal is wearing the HUD chrome — which is exactly how
    the OPERATIONS DIRECTOR "Investigate pod beacon?" pane sat in front of the loop for the
    whole of turn 0 while the driver clicked TURN COMPLETE BEHIND it every 6 s
    (`evidence/trace_m54h3_*.jsonl`: the frame flickers between `hud` and `unknown` because
    OCR reads the chrome and misses the dialog test's word count).
    """
    band = [t for t, _cx, cy, *_ in words if 90 <= cy <= 118]
    return any(len(t) >= 6 for t in band) or sum(1 for t in band if len(t) >= 4) >= 2


def is_dest_chooser(words):
    """The `g` ("Move to") chooser (M54d).

    Measured on `evidence/m54d/m54d_move_afterg.png` and `evidence/m54d/chooser_offbase.png`:
    caption `SELECT DESTINATION` at y~102, one base row at y~132 with `Distance: N`, and its
    OWN OK/CANCEL bar row at y~162. OCR reads the caption and the base row but NEVER the bar
    labels, and the panel is flat (12 colours in the dialog box) — yet `upper` counts only 5
    words, so the `dialog` test misses it and it classifies `hud` while it swallows every
    keypress (10 keys, zero order bytes, `evidence/m54d/probe_unit0.json`).
    """
    cap = body = False
    for t, cx, cy, *_ in words:
        low = t.lower().strip(".,:;|_*—")
        if cy < 135:
            if low.startswith("destin"):
                cap = True
            elif low.startswith("selec"):
                body = True
    return cap and body


def is_name_pane(words):
    """NEWBASE — the colonist founding's name-entry pane (M54g, session 84).

    `b` on a class-8 unit standing on a legal tile raises "ENTER A NAME FOR YOUR NEW
    BASE." (caption y 102) with the game's generated name already in the field (y 135),
    and the HUD's TURN COMPLETE row is STILL drawn under it — so classify() fell through
    to `hud` and the loop read two quiet frames while the modal ate every keypress.
    Return accepts the generated name (measured: the base record exists 0.1 s later).
    """
    band = [t for t, cx, cy, _w, _h in words if 90 <= cy <= 128 and 150 <= cx <= 650]
    ts = re.sub(r"[^a-z]", "", "".join(band).lower())
    return "name" in ts and "newbase" in ts


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


def close_bar(png):
    """The bottom-right red CLOSE bar of a full-screen scene/artwork panel (M54d), or None.

    Measured on `evidence/m54d/peek_stuck.png` (the scene the driver burned two runs on):
    the bar fills y 579-599 from x 596 to the right edge, and its colours are (94,10,9) and
    (73,9,8) — the (73,9,8) patches are the "CLOSE" glyphs. The terrain it sits on is
    (85,52,30)-ish, so the GREEN channel, not brightness, is what separates bar from ground:
    r>70 & g<30 & b<30. OCR is useless here — it read 7 tokens off this whole frame — so
    this is a colour test on the bottom-right strip, and the click target is the fill's own
    centre, not a corner.
    """
    im = Image.open(png).convert("RGB")
    w, h = im.size
    strip = im.crop((w // 2, h - 25, w, h))
    px = strip.load()
    pts = [(x, y) for y in range(strip.height) for x in range(strip.width)
           if px[x, y][0] > 70 and px[x, y][1] < 30 and px[x, y][2] < 30]
    if len(pts) < 300:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (w // 2 + (min(xs) + max(xs)) // 2, (h - 25) + (min(ys) + max(ys)) // 2)


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
    if is_help_page(words):
        return "help"           # full-screen help browser: its profile text contains base
                                # words, so this must run before the base test
    if is_communication(words, png):
        return "comm"           # faction communication: click ITS OK bar (y~347), never a
                                # console bar — session 80's turn 35 clicked (333,560) 38
                                # times and the year never moved
    if is_dest_chooser(words):
        return "dest-chooser"   # M54d: the `g` chooser — its own OK bar at y~162, NOT the
        # console row and NOT a hud: it swallows every keypress
    if is_name_pane(words):
        return "name-pane"      # M54g: NEWBASE name entry ("ENTER A NAME FOR YOUR NEW
        # BASE." at y 102 over a still-drawn HUD): Return accepts the generated name and
        # the base record exists 0.1 s later. Untested it read `hud` and ate the order.
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
    # M54d: a full-screen scene/artwork panel (the Secret-Project / Prophet movies) carries
    # its OWN red CLOSE bar bottom-right. It OCRs to ~7 tokens, so it used to fall through
    # to `movie`, where the driver only ever presses Escape — and Escape is gated by
    # --no-escape, so two runs sat on it with the year frozen (trace_m54d40b turn 0).
    if png is not None and close_bar(png):
        return "artwork-close"
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


def bar_colour_mask(png, y0=200):
    """Per-scanline mask of the game's light periwinkle push-bar fill.

    PIL, not `ffmpeg -f rawvideo -` piped through sh(): raw RGB blows up a text=True
    subprocess on the first non-UTF-8 byte. The colour predicate is the one proven live in
    session 75 (evidence/m53s_barclick.py): b>120, r,g>90, |r-g|<40, b-r>25. It excludes
    the red NAY / green YEA / amber ELIMINATED tally bars the Council draws under the
    delegate portraits, so only the clickable bars pass.
    """
    im = Image.open(png).convert("RGB")
    return [[b > 120 and r > 90 and g > 90 and abs(r - g) < 40 and b - r > 25
             for r, g, b in im.crop((0, y, W, y + 1)).getdata()]
            for y in range(y0, H)]


def pane_bars(png, y0=200, min_band_h=12, min_w=40, duty=0.3):
    """Push-bars in the frame as (cx, cy, height), found by COLOUR GEOMETRY.

    Band-then-column, never a run. The game draws these bars DITHERED (measured on the
    PROPOSAL vote, evidence/m54a/stuck2.png: fill (103,91,181) on every OTHER scanline over
    y 489-507 with (28,80,99) between), so no vertical run longer than 1 px exists, and the
    label drawn INSIDE each bar breaks the horizontal runs too. So: take the rows that are
    bar-filled over >100 px, group them into bands across 1-row dither gaps (that frame's
    band is y 489-507, 19 px), then count fill per column INSIDE the band — 10 in a clean
    column, 5-7 through a label glyph, 0-2 in the ~3 px dark gap between two bars. 30% duty
    separates YEA/NAY/ABSTAIN into exactly three bars (centres 311/400/489 = the
    YEA(310,495) NAY(398,495) ABSTAIN(485,495) row wine-operations measured by hand in
    session 75); 40% cuts a labelled bar in half, 15% merges the row into one bar and the
    driver clicks NAY. Scanning only y>=200 keeps the delegate portraits (y 40-170) out.
    """
    rows = bar_colour_mask(png, y0)
    if not rows:
        return []
    # 1) rows that are bar-filled somewhere wide enough to be a bar row
    hot = [y for y, r in enumerate(rows) if sum(r) > 100]
    bands = []
    for y in hot:
        if bands and y - bands[-1][1] <= 2:          # dither => every other row is empty
            bands[-1][1] = y
        else:
            bands.append([y, y])
    bars = []
    for b0, b1 in bands:
        h = b1 - b0 + 1
        if h < min_band_h:
            continue
        need = max(4, int(h * duty))
        cold = [sum(col) for col in zip(*rows[b0:b1 + 1])]
        x = 0
        while x < W:
            if cold[x] < need:
                x += 1
                continue
            x0 = x
            while x < W and cold[x] >= need:         # strict contiguity: the ~3 px dark gap
                x += 1                               # between two bars is a separator
            if x - x0 >= min_w:
                bars.append(((x0 + x) // 2, y0 + (b0 + b1) // 2, h))
    return bars


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


def answer_help_page(png):
    """Close the HELP browser: click EXIT, the right-hand bar of the BACK/EXIT pair.

    Measured on evidence/m54a/live_now2.png: BACK (275,344), EXIT (525,344). Escape is
    ignored by this screen (three Escapes, still there, round stalled twice).
    """
    bs = [b for b in pane_bars(png) if 320 <= b[1] <= 380]
    if len(bs) >= 2:
        xy = max(bs, key=lambda b: b[0])
        click((xy[0], xy[1]))
        return (xy[0], xy[1])
    key("Escape")
    return None


def answer_communication(png):
    """Answer a faction COMMUNICATION: click the MIDPOINT of its own OK bar row (y~347).

    Measured on `evidence/m54c/comm_pane.png`: the bar's dithered purple ends are
    (266,347) and (534,347) and the "OK" label between them is not fill, so the row's
    centre — not any one segment — is the click target. The HUD console row (DATALINKS
    333,560 / PROFILE 467,560 / HQINFO 619,560) is still drawn under this pane and is NOT
    a close bar: M54b's bottom-bar rule clicked (333,560) on 38 consecutive frames of
    turn 35, each click opening DATALINKS/PROFILES and each EXIT click landing back on the
    same communication (735 s, year 2185 never moved).
    """
    bs = [b for b in pane_bars(png, y0=330) if 330 <= b[1] <= 365]
    if bs:
        left = min(b[0] - b[2] / 2.0 for b in bs)
        right = max(b[0] + b[2] / 2.0 for b in bs)
        xy = (int((left + right) / 2), int(sum(b[1] for b in bs) / len(bs)))
        click(xy)
        return xy
    key("Return")
    return None


def bar_bands(png, y0=118):
    """Bar bands in the upper panel area as dicts (y centre, merged span, groups, buttons).

    `bar_colour_mask` returns rows OFFSET by y0 and `pane_bars` never reports a bar's
    WIDTH, so the chooser's own geometry has to be re-derived here. Measured on
    `evidence/m54h/chooser_g60b.png` (the two-base chooser): the destination rows are
    FULL-WIDTH periwinkle bars (fill 159..638) on the bands y 125-139 and 144-158 (a 19 px
    pitch), and the buttons are five 96-px bars on the band y 172-190 at centres
    209/305/401/497/593 (Sort: Name / Sort: Size / Sort: Dist / OK / CANCEL). A row band's
    label-split groups merge into a ~480 px span; the button band's do not (91 px at duty
    0.3, five groups at duty 0.2), which is how the two are told apart.
    """
    rows = bar_colour_mask(png, y0)
    hot = [y for y, r in enumerate(rows) if sum(r) > 100]
    bands = []
    for y in hot:
        if bands and y - bands[-1][1] <= 2:
            bands[-1][1] = y
        else:
            bands.append([y, y])
    out = []
    for b0, b1 in bands:
        h = b1 - b0 + 1
        if h < 8:
            continue
        cold = [sum(col) for col in zip(*rows[b0:b1 + 1])]
        need = max(4, int(h * 0.3))
        groups, x = [], 0
        while x < W:
            if cold[x] < need:
                x += 1
                continue
            x0 = x
            while x < W and cold[x] >= need:
                x += 1
            groups.append((x0, x - 1))
        if not groups:
            continue
        need2 = max(3, int(h * 0.2))          # low duty: separates five buttons from a row
        buttons, x = [], 0
        while x < W:
            if cold[x] < need2:
                x += 1
                continue
            x0 = x
            while x < W and cold[x] >= need2:
                x += 1
            if x - x0 >= 12:
                buttons.append(((x0 + x) // 2, x - x0))
        # A BUTTON band is five bars of one width on one pitch (measured: 92 px wide,
        # 96 px apart); a destination row's fill breaks into label-shaped groups of
        # wildly different widths (25/43/331/17/49 on the frame above). The merged span
        # cannot tell them apart — five buttons span 163..638, exactly like a row.
        ws = [w for _c, w in buttons]
        cs = [c for c, _w in buttons]
        button_band = False
        if len(ws) >= 4:
            wmed = sorted(ws)[len(ws) // 2]
            pitches = [cs[i + 1] - cs[i] for i in range(len(cs) - 1)]
            pmed = sorted(pitches)[len(pitches) // 2]
            button_band = (all(abs(w - wmed) <= max(8, 0.15 * wmed) for w in ws)
                           and all(abs(p - pmed) <= max(8, 0.15 * pmed) for p in pitches)
                           and wmed < 120)
        out.append(dict(y=y0 + (b0 + b1) // 2, span=(groups[0][0], groups[-1][1]),
                        width=groups[-1][1] - groups[0][0], groups=groups,
                        buttons=buttons, button_band=button_band))
    return out


def chooser_rows(png, words=None):
    """The `g` chooser's destination rows (the wide bar bands, buttons excluded)."""
    words = ocr_fast(png) if words is None else words
    rows = []
    for b in bar_bands(png):
        if b["button_band"] or b["width"] < 300:
            continue
        texts = sorted((round(x), t) for t, x, y, *_ in words
                       if abs(y - b["y"]) <= 8 and x < 700)
        rows.append(dict(y=b["y"], cx=(b["span"][0] + b["span"][1]) // 2,
                         span=list(b["span"]), n_groups=len(b["groups"]),
                         text=" ".join(t for _x, t in texts)))
    return rows


def chooser_buttons(png):
    """The `g` chooser's button band as (y, [centres]): five 96-px bars.

    Measured on `evidence/m54h/chooser_g60b.png`: Sort: Name / Sort: Size / Sort: Dist /
    OK / CANCEL at centres 209/305/401/497/593 (y 181 with two rows, y 162 with one). OK is
    the FOURTH centre and CANCEL the LAST — verified by effect, not by label: OK landed
    0x18 (`evidence/m54h/probe_chooser_walk1.json`), CANCEL wrote nothing and closed the
    pane (`evidence/m54h/probe_chooser_cancel67.json`).
    """
    for b in reversed(bar_bands(png)):
        cs = [c for c, _w in b["buttons"]]
        if len(cs) >= 4:
            return b["y"], cs
    return None, []


def own_bases_named(f, me):
    """Our bases as (idx, x, y, name) — the chooser's row list is one per own base (M54h)."""
    import struct
    n = max(0, min(struct.unpack("<I", rd(f, BASE_COUNT_G, 4))[0], 64))
    blob = rd(f, BASE_ARR, n * BASE_SZ)
    out = []
    for i in range(n):
        rec = blob[i * BASE_SZ:(i + 1) * BASE_SZ]
        if rec[4] != me:
            continue
        name = rec[19:52].split(b"\0")[0].decode("latin-1").strip()
        out.append(dict(idx=i, x=struct.unpack("<h", rec[0:2])[0],
                        y=struct.unpack("<h", rec[2:4])[0], name=name))
    return out


def answer_dest_chooser(png, verbose=False, words=None, f=None, avoid=None,
                        me=None, out=None):
    """Answer the `g` chooser: pick a destination ROW, then click ITS OK bar (M54d + M54h).

    M54d measured the OK bar and answered whatever row the pane had already HIGHLIGHTED.
    That row is the nearest base — for a unit garrisoned on its own base, its OWN tile —
    so the queued MOVE was a no-op and the walk proved nothing.

    M54h measured the pane itself (`evidence/m54h/chooser_g60b.png` +
    `evidence/m54h/probe_chooser_walk1.json`, unit rec60 on Korolev Center (29,42)):
      * it lists EVERY base we own: two rows, y 132 and y 151, alphabetical by name under
        the default Sort: Name ("Korolev Center", then "University Base");
      * clicking a row only HIGHLIGHTS it: `+17` and the legs were unchanged 0.9 s after
        the click (stage `row_click`), so the row click is a selection, not an order;
      * the OK click is what lands the order: `+17` went 0 -> 0x18 87 ms after the click
        and the record carried legs [28,42] (stage `ok_click`), and the pump stepped the
        unit (29,42) -> (28,43) with `+40` = 3 spent;
      * CANCEL (the LAST of the five buttons) closes the pane and writes nothing
        (`evidence/m54h/probe_chooser_cancel67.json`: 60 samples of `+17`, all 0).
    So when `avoid` (the tile the unit is standing on) is given and a DIFFERENT own base
    exists, click that base's row first. The row<->base mapping is by name order; nothing
    downstream trusts it — the destination is read back out of the record's own leg array.
    """
    pick = None
    if f is not None and avoid is not None:
        rows = chooser_rows(png, words)
        bases = own_bases_named(f, me)
        others = [b for b in bases if (b["x"], b["y"]) != tuple(avoid)]
        # M54i2: (x+y) parity is invariant under the step table (see `delta_table`),
        # so only a base of the WALKER TILE's parity is ever reachable. Prefer it;
        # an opposite-parity row queues a move that oscillates forever (run2's walker
        # at (29,42)/(28,43) vs University Base (28,42)).
        target = next((b for b in others if walk_parity_ok(avoid, (b["x"], b["y"]))),
                      None) or next(iter(others), None)
        row_ix = None
        if target is not None:
            # Prefer the row whose OWN text names the base we mean: the pane's sort is
            # Sort: Name by default, but the alphabetical mapping is an ASSUMPTION (both
            # frames seen so far put the alphabetically-first base first AND nearest-first
            # would have done the same), and the row text is what the pane actually shows.
            word = re.sub(r"[^a-z]", "", target["name"].lower())[:9]
            for i, r in enumerate(rows):
                if len(word) >= 5 and word in re.sub(r"[^a-z]", "", r["text"].lower()):
                    row_ix = i
                    break
            if row_ix is None and len(rows) == len(bases):
                order = sorted(bases, key=lambda b: b["name"].lower())
                row_ix = next((i for i, b in enumerate(order)
                               if (b["x"], b["y"]) != tuple(avoid)
                               and walk_parity_ok(avoid, (b["x"], b["y"]))), None)
                if row_ix is None:
                    row_ix = next((i for i, b in enumerate(order)
                                   if (b["x"], b["y"]) != tuple(avoid)), None)
        if row_ix is not None and 0 <= row_ix < len(rows):
            click((rows[row_ix]["cx"], rows[row_ix]["y"]))
            time.sleep(0.8)
            pick = dict(row_index=row_ix, row_y=rows[row_ix]["y"],
                        row_text=rows[row_ix]["text"], base=[target["x"], target["y"]],
                        base_name=target["name"])
            if verbose:
                print(f"    chooser: clicked row {row_ix} y{rows[row_ix]['y']} "
                      f"({target['name']} at {target['x']},{target['y']}; unit stands on "
                      f"{avoid[0]},{avoid[1]})", flush=True)
        elif len(rows) >= 2 and verbose:
            print(f"    chooser: {len(rows)} rows vs {len(bases)} own bases and no text "
                  f"match — answering the highlighted row", flush=True)
    bs = [b for b in pane_bars(png, y0=150) if 150 <= b[1] <= 190]
    if bs:
        left = min(b[0] - b[2] / 2.0 for b in bs)
        right = max(b[0] + b[2] / 2.0 for b in bs)
        xy = (int((left + right) / 2), int(sum(b[1] for b in bs) / len(bs)))
        # M54i: the merged midpoint is NOT the OK button. With two destination rows the
        # bar band at y 150-190 contains a ROW bar as well as the five buttons, and the
        # midpoint of that span (~x 398) is the `Sort: Dist` button — clicking it
        # re-sorts the pane instead of answering it. `chooser_buttons()` measures the
        # button band and OK is its FOURTH centre (verified by effect: OK landed 0x18,
        # CANCEL — the fifth — wrote nothing; evidence/m54h/probe_chooser_walk1.json /
        # probe_chooser_cancel67.json).
        by, cs = chooser_buttons(png)
        if len(cs) >= 4:
            xy = (int(cs[3]), int(by))
        click(xy)
        if verbose:
            print(f"    dest-chooser OK at {xy} (bars {bs})", flush=True)
        if out is not None:
            out["chooser_pick"] = pick
        return xy
    key("Return"); time.sleep(0.8)
    if out is not None:
        out["chooser_pick"] = pick
    return None



def answer_council_dialog(png):
    """The Council's own panes: option rows + an OK bar (M54a).

    Measured on evidence/m54a/live_now3.png ("GAIANS - OBSTINATE / Have you any further
    business?"): six dithered option rows at y 70-175 (the first, "I believe we are finished
    here. Zakharov out.", is the one that ENDS the Council round) and one OK bar across the
    pane bottom at y~347 — the "OK" label splits it into two column groups (266,347) and
    (534,347), so the click has to land on the merged row's centre (400,347). `Return` does
    nothing on this pane: 240 s of it and the turn stayed STUCK (trace_m54a40g turn 5).
    The PROTOCOL DIRECTOR pane has no option rows, only its OK bar in the 430-520 band.
    """
    rows = pane_bars(png, y0=55)
    opts = [b for b in rows if 55 <= b[1] <= 200]
    okb = [b for b in rows if 300 <= b[1] <= 420] or [b for b in rows if 430 <= b[1] <= 520]
    if opts and okb:
        click((opts[0][0], opts[0][1]))          # select the top option ("finished here")
        time.sleep(1.0)
    if okb:
        x0 = min(b[0] for b in okb)
        x1 = max(b[0] for b in okb)
        cy = sum(b[1] for b in okb) // len(okb)
        click(((x0 + x1) // 2, cy))
        return ((x0 + x1) // 2, cy)
    if opts:
        click((opts[0][0], opts[0][1]))
        return (opts[0][0], opts[0][1])
    return None


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
        if kind == "movie":
            # Secret Project / discovery movies (the "Oracle" clip:
            # evidence/m54a/movie_oracle.png) draw a RED Close bar at (690,577) that
            # `pane_bars` — which looks for the purple push-bar fill (103,91,181) —
            # never sees, and the clip does not end on its own. Session 78's run sat
            # 150 s on `movie` frames at 2109 until one Return dismissed it. The battle
            # REPLAY keeps its own path above (it has a detectable bottom bar).
            key("Return")
            rec["handled"].append("movie:Return")
            time.sleep(1.0)
            return True
        return False
    # A full-screen `movie` frame that carries a bottom bar is not a cinematic that ends on
    # its own: it is the battle REPLAY ("Replay: 2415" + a Close bar at (400,587),
    # evidence/m54a/movie_stuck.png), and it loops until something clicks Close. With
    # --no-escape the driver was forbidding itself from doing anything, so turn 0 burned
    # 243 s of `movie` frames (trace_m54a40i).
    # M54b pane-scoping: a bottom bar at y >= 560 is the battle REPLAY's Close bar
    # (evidence/m54a/movie_stuck.png) — and Replay/Close bars are what a bar-less-frame
    # class shows. A `dialog` kind frame is NOT clicked here: its own bars are advisory
    # rows (y 219-310) answered by Return, and session 77 ended by clicking a bar that
    # belonged to no pane we owned (HELP, then the LOAD browser at y 552).
    if kind in ("movie", "unknown") and not is_council_pane(words):
        close = [b for b in bs if b[1] >= 560]
        if close:
            b = max(close, key=lambda c: c[2])
            click((b[0], b[1]))
            rec["handled"].append(f"close-bar@{int(b[0])},{int(b[1])}")
            time.sleep(1.2)
            return True
    row = is_vote_row(bs)
    council = is_council_pane(words)
    # A 3-bar row only counts as a VOTE when it sits in the y>=460 band: the Council puts
    # YEA/NAY/ABSTAIN at y~498, while the advisory panes' bar rows ("Don't Show As Popup" +
    # OK, the highlighted option row) measure y 219-310 on the same fixtures.
    vote = bool(row) and 460 <= row[0][1] <= 520      # the Council vote row is at y~498;
    if vote:
        target = row[0]
        click((target[0], target[1]))
        rec["handled"].append(f"vote-yea@{int(target[0])},{int(target[1])}" +
                              ("/council" if council else ""))
        time.sleep(1.6)
        return True
    if council:
        xy = answer_council_dialog(png)         # option row + merged OK bar, or just the OK
        if xy:
            rec["handled"].append(f"council-ok@{int(xy[0])},{int(xy[1])}")
            time.sleep(1.6)
            return True
    return False


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


def frame_hash(png):
    """Deterministic fingerprint of a capture: a wedged game re-renders the identical
    frame, so its PNG bytes repeat; a live game (animating map, pane churn) never does."""
    return md5(open(png, "rb").read()).hexdigest()


def legs_of(raw):
    """The queued-MOVE route in a 52-byte record as [(x, y), ...].

    ORDERS.md §4: legs at `+20..+27` (x) / `+28..+35` (y), -1-terminated. The arrays
    SURVIVE the pump (`order 0`, legs still (29,42) on parked records — measured by
    `m54d_census.py` on the live position), so stale legs sit on records that were
    ordered on an earlier turn; a destination is only attributable to THIS order when
    the legs of THIS record changed (M54i).
    """
    import struct
    lx = [struct.unpack("<h", raw[20 + k * 2:22 + k * 2])[0] for k in range(4)]
    ly = [struct.unpack("<h", raw[28 + k * 2:30 + k * 2])[0] for k in range(4)]
    return [(a, b) for a, b in zip(lx, ly) if a >= 0 and b >= 0]


def our_rows(f, me, n=119, with_raw=False):
    """Every live record we own, decoded for the walk check: idx/x/y/type/order/mp/legs."""
    import struct
    arr = rd(f, UNIT_ARR, n * 52)
    out = []
    for i in range(n):
        d = arr[i * 52:(i + 1) * 52]
        if d[14] != me or d[14] == 0xFF:
            continue
        r = dict(idx=i, x=struct.unpack("<h", d[0:2])[0],
                 y=struct.unpack("<h", d[2:4])[0],
                 type=struct.unpack("<H", d[10:12])[0], order=d[17], mp=d[40],
                 legs=legs_of(d))
        if with_raw:
            r["raw"] = d
        out.append(r)
    return out


BASE_ARR, BASE_SZ, BASE_COUNT_G = 0x95DA10, 304, 0x985AF4


def own_base_tiles(f, me):
    """Tiles holding one of OUR bases (304-byte records: x@0, y@2, faction = the LOW byte
    of the duplicated nibble at +4 — SAVE_FORMAT.md 150-160; count at 0x985AF4, which that
    document corrects from "n_factions" to a base count).

    M54c read this set as "tiles `g` refuses" and skipped the MOVE key on all of them.
    M54h measured otherwise (`evidence/m54h/chooser_g60b.png`,
    `evidence/m54h/probe_chooser_walk1.json`): a unit garrisoned on our base DOES get a
    chooser, and it lists every base we own — the refusal is only that the pane cannot
    meaningfully name the tile the unit is standing on. The set is therefore used to ask
    "is there another own base to walk to?", not "is this unit un-orderable?".
    """
    import struct
    n = max(0, min(struct.unpack("<I", rd(f, BASE_COUNT_G, 4))[0], 64))
    b = rd(f, BASE_ARR, n * BASE_SZ)
    out = set()
    for i in range(n):
        r = b[i * BASE_SZ:(i + 1) * BASE_SZ]
        if r[4] == me:
            out.add((struct.unpack("<H", r[0:2])[0], struct.unpack("<H", r[2:4])[0]))
    return out


# M54i2 (2026-10-25, live read at 2159 from pid 1110005): the game's step table is 21
# int32 pairs — `dx` at 0x67850c, `dy` at 0x678990; the adjacency loop runs
# `do { ... } while ((int)local_2c < 0x54)` in 4-byte steps (ghidra_out/shard_013.c:
# 21829-21868), i.e. 21 entries. EVERY entry preserves (x+y) parity — the short steps
# (±2,0),(±1,±1),(0,±2) and the long steps (±2,±2),(±3,±1),(±1,±3) all do. A queued
# MOVE walks along these steps, so a unit can NEVER reach a base tile of the other
# parity: measured, the run2 walker ordered to University Base (28,42) (sum 70, even)
# oscillated (28,43)<->(29,42) (sum 71, odd) across TURN COMPLETEs (scratch/m54i2_pump
# .py: (28,43) -> (29,42) in one cycle, order still 24) and never entered the base.
# ORDERS.md §7 listed only (±2,0),(±1,±1) for this table; the live read is 21 pairs.
DELTA_TABLE_G = 0x67850c
DELTA_DY_G = 0x678990
DELTA_N = 21


def delta_table(f):
    """The live step table as 21 (dx, dy) pairs (see the block comment above)."""
    import struct
    dx = struct.unpack(f"<{DELTA_N}i", rd(f, DELTA_TABLE_G, DELTA_N * 4))
    dy = struct.unpack(f"<{DELTA_N}i", rd(f, DELTA_DY_G, DELTA_N * 4))
    return list(zip(dx, dy))


def table_neighbors(x, y, table):
    """Tiles a step from (x,y) can land on, per a given delta table."""
    return {(x + dx, y + dy) for dx, dy in table if (dx, dy) != (0, 0)}


def walk_parity_ok(unit_xy, base_xy):
    """(x+y) parity is invariant under the step table: the only bases a walk from
    `unit_xy` can ever ARRIVE at share its parity. Necessary, not sufficient (terrain
    and route still apply)."""
    return (unit_xy[0] + unit_xy[1]) % 2 == (base_xy[0] + base_xy[1]) % 2


def pick_reactivation(held, own_tiles, table):
    """Which HELD records may be re-activated (poked +17 2 -> 0) into the order step.

    M54j (measured, run1): the game AUTO-SENTRIES an order-0 unit across the round
    boundary — a setup that leaves a unit waiting at +17 = 0 finds it wearing byte 1
    (SENTRY) and PATROLLING ON ITS OWN (ORDERS.md §10) by the time our phase opens.
    Byte 2 (HOLD) is the only state that survives the round; the unit therefore has
    to be re-activated IN-PHASE, in the same window as the keypress.

    Eligible: not standing on one of OUR bases (there `g` raises the BASE SCREEN
    instead of the chooser — session 86 run5 t0), and at least one own base of the
    unit's own (x+y) parity exists that is NOT the tile under its feet (the only
    reachable walk target). Returns the eligible records, nearest own same-parity base
    first (`man` is the Chebyshev distance to that base) — a multi-leg route is the
    point, but a unit 30 tiles out is a worse bet than one 6 out.
    """
    table = table_neighbors(0, 0, table)  # the pure step shapes
    out = []
    for r in held:
        tile = (r["x"], r["y"])
        if tile in own_tiles:
            continue
        cands = [t for t in own_tiles
                 if t != tile and walk_parity_ok(tile, t)]
        if not cands:
            continue
        man = min(max(abs(tile[0] - t[0]), abs(tile[1] - t[1])) for t in cands)
        # a unit that already stands on a legal step of a same-parity own base is a
        # ONE-step arrival, not a multi-leg route — keep it eligible, sort it last
        out.append(dict(r, reactivated=True, man=man,
                        on_step=any((tile[0] + dx, tile[1] + dy) in own_tiles
                                    for dx, dy in table)))
    out.sort(key=lambda r: (r["on_step"], r["man"], r["idx"]))
    return out


def walker_on_dest(rows, utype, dest, ordered_legs):
    """Is THE WALKER (not merely a same-type unit) on the destination tile?

    M54j run4 (measured): University Base holds six identical Scout Patrols, so
    `bool(hits)` — "a record of our type sits on the destination" — was TRUE while the
    ordered unit had moved only (49,33) -> (47,33). The walker's identity is the ROUTE:
    the only record wearing the ordered leg array is the one the chooser answered
    (ORDERS.md §4: the pump consumes `+17` but the legs survive; run4 watched the same
    record carry legs [(28,42)] through (47,33) and (43,35)). An order whose legs are
    EMPTY (the session-86 legs-less chooser OK shape) keeps the old type+tile reading —
    there is no route to match.
    """
    if not ordered_legs:
        return any(r["type"] == utype and (r["x"], r["y"]) == tuple(dest) for r in rows)
    route = [tuple(l) for l in ordered_legs]
    return any(r["type"] == utype and (r["x"], r["y"]) == tuple(dest)
               and [tuple(l) for l in r["legs"]] == route for r in rows)


def held_walk_records(f, me, n=119):
    """Our +17 = 2 (HOLD) records, decoded like `find_actionable` (not frozen,
    movement unspent). The re-activation pool for `order_step_in_loop`."""
    import struct
    out = []
    arr = rd(f, UNIT_ARR, n * 52)
    for i in range(n):
        d = arr[i * 52:(i + 1) * 52]
        if d[14] != me or d[14] == 0xFF:
            continue
        if bool(d[9]) or d[17] != 2 or d[40] != 0:
            continue
        typ = struct.unpack("<H", d[10:12])[0]
        out.append(dict(idx=i, x=struct.unpack("<h", d[0:2])[0],
                        y=struct.unpack("<h", d[2:4])[0], type=typ,
                        cls=unit_class(f, typ), order=d[17], mp=d[40],
                        legs=legs_of(d)))
    return out


def snap_our_units():
    """The pre-EXEC snapshot `verify_moves` later diffs against live memory."""
    try:
        _pid, f = mem()
    except Exception:
        return None
    try:
        return our_rows(f, state().get("player"))
    except Exception:
        return None
    finally:
        try:
            f.close()
        except Exception:
            pass


def verify_moves(orders, snap, verbose=False):
    """M54d/e: did an ordered walk actually HAPPEN? Memory, never the screen.

    A queued MOVE is only an intention, and (measured in M54e, three TURN COMPLETEs with a
    parked 0x18 that never moved) the year flip is NOT what runs it: the game's own order
    pump runs it when its cycle visits the unit, i.e. as the `g` chooser is answered. So
    the walk is watched twice — `issue_order_for_unit` catches it at the pump (that is
    where `+40` gets spent, before the phase-start refresh zeroes it again, see M37), and
    this function re-reads the records after the year flips and requires the record to
    STILL sit on the destination its own leg array named. Identity is (type, tile): the
    record INDEX is not a persistent id — the array compacts when a unit dies — which is
    the same caveat ORDERS.md §6 records for the order step.
    """
    want = [o for o in orders if o.get("verified") and o.get("order_after") == 0x18
            and o.get("dest") and tuple(o["dest"]) != (o.get("ux"), o.get("uy"))]
    if not want:
        return []
    try:
        _pid, f = mem()
    except Exception:
        return []
    try:
        rows = our_rows(f, state().get("player"))
        # M54i: the milestone's question is "did the loop's unit reach a base WE OWN",
        # so the destination tile is checked against the base array in the same read.
        own_tiles = own_base_tiles(f, state().get("player"))
        out = []
        for o in want:
            dx, dy = o["dest"]
            hits = [r for r in rows if r["type"] == o["utype"] and r["x"] == dx
                    and r["y"] == dy]
            still = [r for r in rows if r["type"] == o["utype"]
                     and (r["x"], r["y"]) == (o["ux"], o["uy"])]
            # M54h: "a record of this type is on the destination tile" is worth nothing
            # when identical units were parked there before the order (five of ours sit on
            # University Base in this position). The arrival is the DELTA against the
            # baseline the order itself recorded: same-type count at the destination goes
            # UP, same-type count at the origin goes DOWN. Traces from before M54h have no
            # baseline, so they keep the old (weaker) reading.
            c0 = o.get("order_counts") or {}
            d_after = len(hits)
            s_after = len(still)
            d_before, s_before = c0.get("dest"), c0.get("src")
            # M54j: the fallback is RETIRED. "no baseline -> believe the tiles" is what
            # let run4 print ARRIVED for a unit that had moved 2 of 21 tiles: the dest
            # count never rose (six garrisons were already there) yet count_proof passed
            # on a missing baseline. A new-format order without counts is a bug, not a
            # pass; only pre-M54h traces (no counts field at all) keep the tile reading.
            has_base = "order_counts" in o and c0.get("dest") is not None \
                and c0.get("src") is not None
            count_proof = (not has_base
                           or (d_after > d_before and s_after < s_before))
            # M54j: AND the walker itself must be ON the destination — identified by the
            # route it carries, not by a same-type headcount (see `walker_on_dest`).
            # M54j: the route the ORDER wrote (the walker's identity among identical
            # garrisons — see `walker_on_dest`); it lives in the attribution claim.
            route = ((o.get("walk_diff") or {}).get("claim") or {}).get("legs_after") or []
            on_dest = walker_on_dest(rows, o["utype"], (dx, dy), route)
            # `+40` is spent at the pump and re-zeroed at the next phase start, so the
            # movement evidence comes from the in-phase sample; the tile evidence is re-
            # taken here, after EXEC.
            # M54i2: read the ARRIVAL's mp, not an arbitrary hit's. A unit that walked
            # this round shows +40 spent at our next phase start (scratch/m54i2_pump.py:
            # the moved record read mp 3 while every held unit read 0); garrison/HOLD
            # units and base-produced units on the destination tile sit at 0 (run3
            # census at 2165: three HELD garrisons and a fresh produced unit all mp 0).
            # `hits[0]` is index-order — in run3 turn 0 it was a held garrison, so the
            # arrival's own spent mp was invisible and a memory-verified landing scored
            # `landed false`. max() asks exactly what the floor asks — "some same-type
            # record ON THE DESTINATION TILE spent movement this round" — and the floor
            # itself (mp_after > 0, plus the count delta) is unchanged.
            mp_after = (o.get("walk_mp") or o.get("mpused_after")
                        or max([h["mp"] for h in hits], default=0))
            m = dict(order=o["key"], unit=o["unit"], utype=o["utype"],
                     frm=[o["ux"], o["uy"]], dest=[dx, dy],
                     landed=on_dest and count_proof and mp_after > 0,
                     on_dest_after_exec=bool(hits), walked_inphase=bool(o.get("walk_landed")),
                     mp_after=mp_after, walk_ms=o.get("walk_ms"),
                     dest_count=[d_before, d_after], src_count=[s_before, s_after],
                     dest_is_own_base=bool((dx, dy) in own_tiles),
                     still_at_start=bool(still))
            out.append(m)
            if verbose:
                print(f"    MOVE rec{o['unit']} type {o['utype']} ({o['ux']},{o['uy']}) -> "
                      f"ordered ({dx},{dy}): {'ARRIVED' if hits else 'did not arrive'} "
                      f"(dest count {d_before}->{d_after}, origin {s_before}->{s_after}, "
                      f"mp_after {m['mp_after']})", flush=True)
        return out
    finally:
        try:
            f.close()
        except Exception:
            pass


PENDING_WALKS = []         # 0x18 orders whose walk outlived the turn that ordered them
PRE_ARM_DONE = [False]     # M54j: one mid-AI-round arming poke per run (see the hook
                           # in service_turn's ai-phase branch; probe2 measured that an
                           # actionable unit at phase open makes the game WAIT for input,
                           # while an all-HELD phase auto-advances unseen)
PENDING_MAX_TURNS = 8      # stop re-checking a walk after this many later turns


def diff_order_records(before, cand_idx, want, byte_samples, pre_legs,
                       after=None, pre_order=0):
    """M54i: WHICH record did the keypress order? Snapshot-and-diff, never one index.

    The proof of a FRESH order is the through-the-click watcher's own samples on the
    CANDIDATE's record slot: a 0 -> wanted-byte transition seen there is the order
    landing on the unit we raised the key against. `after` is only read for RIVALS —
    by the time it is taken the pump may already have run the order (`order_after 0`)
    or a unit built mid-run may have shifted every index after it, and session 85
    proved what a re-used index costs: legs naming bases nobody ordered.

    A rival is another record on the candidate's own tile (same type, same order
    before the press — indistinguishable from it; three identical Scout Patrols stack
    on University Base) that carries the wanted byte with legs its record did not hold
    before the press: a fresh order we did NOT watch land. A record that already
    carried the byte (a live 0x18 walker) or whose legs did not CHANGE (the leg arrays
    survive the pump — a parked decoy, a walk ordered on an earlier turn) is not fresh.

    Returns (claim, rivals, attributed, confounded). `attributed` is True for ONE
    unambiguous claim with no rival; `confounded` names the two-orders-at-once case the
    milestone asks to be reported, not smoothed over. When `attributed` is False the
    destination stays UNATTRIBUTED — an honest negative beats a guessed destination.
    """
    import struct
    cand = next((b for b in before if b["idx"] == cand_idx), None)
    if cand is None:
        return None, [], False, False
    want_bytes = set(want)
    # samples are (raw52, ms, byte) triples from `order_byte_watcher`
    zero_i = next((i for i, s in enumerate(byte_samples) if s[2] == 0), None)
    land_i = next((i for i, s in enumerate(byte_samples) if s[2] in want_bytes), None)
    # fresh = the watcher saw our slot sitting at NO ORDER and then at the byte.
    fresh_order = (zero_i is not None and land_i is not None and zero_i < land_i)
    final = byte_samples[-1][0] if (byte_samples and land_i is not None) else None
    post_legs = legs_of(final) if final is not None else []
    # where our record sits AFTER the click (the pump may have stepped it one tile);
    # rivals are scanned against THIS tile, since it is our record that must not be
    # confusable with a look-alike that took an order we did not watch land
    post_tile = (struct.unpack("<h", final[0:2])[0], struct.unpack("<h", final[2:4])[0]) \
        if final is not None else (cand["x"], cand["y"])
    claim = None
    if fresh_order and post_legs != [tuple(p) for p in pre_legs]:
        claim = dict(idx_before=cand["idx"], idx_after=cand["idx"],
                     type=cand["type"], frm=[cand["x"], cand["y"]],
                     to=[struct.unpack("<h", final[0:2])[0],
                         struct.unpack("<h", final[2:4])[0]],
                     order=[pre_order, byte_samples[land_i][2]],
                     legs_before=[list(p) for p in pre_legs],
                     legs_after=[list(p) for p in post_legs],
                     raw_after=final, mp=final[40],
                     landed_at_ms=byte_samples[land_i][1],
                     cand=True)
    rivals = []
    if after is not None and fresh_order:
        pre_by_idx = {b["idx"]: b for b in before}
        # The watched slot is only excluded from the rival scan while the after-snapshot
        # still shows OUR candidate on it: same tile, and either the order we watched
        # land (with the legs our setter wrote — the byte + route pair is our signature,
        # the pump consumes the byte but the legs survive) or the order it started with.
        # A unit built mid-run shifts every index after it — then the row wearing our
        # index is a look-alike and its fresh order IS the ambiguity (that is how session
        # 85 got legs naming bases nobody ordered).
        # Did the array shift under us? The watcher's own last sample says where our
        # record is now: if it is still on its start tile, the watched slot IS our
        # record whatever the (re-usable) indices say. If it left its tile AND no
        # after-row still wears our (index, start-tile, pre-press order) triple, a unit
        # was built or died below us, every index after that point moved, and a
        # look-alike wearing our index carries the same signature — the ambiguity that
        # gave session 85 legs naming bases nobody ordered.
        watched_stayed = final is not None and (post_tile == (cand["x"], cand["y"]))
        stayed = any(a["idx"] == cand_idx
                     and (a["type"], a["x"], a["y"], a["order"])
                     == (cand["type"], cand["x"], cand["y"], cand["order"])
                     for a in after)
        # Is OUR pre-press record still sitting on its start tile (any index — indices
        # lie)? If yes and the watched slot wears the signature elsewhere, the slot is a
        # LOOK-ALIKE that took an order we did not watch land — session 85 read legs
        # naming bases nobody ordered off exactly this shape. If no (the start tile is
        # vacated of our record), the signature row on the slot IS our record, read
        # after it stepped.
        start_vacated = not any(
            (a["type"], a["x"], a["y"], a["order"])
            == (cand["type"], cand["x"], cand["y"], cand["order"])
            for a in after)
        for a in after:
            b = pre_by_idx.get(a["idx"])
            if a["idx"] == cand_idx and (watched_stayed or stayed):
                continue
            # (a) a look-alike on our tile whose order is FRESH against its own
            #     pre-press value, or (b) an INDISTINGUISHABLE TWIN of our record
            #     anywhere in the array — same type, same tile, the byte we watched
            #     land and the route our setter wrote. A mid-run index shift makes (b)
            #     real: the twin and our record carry the same signature and only the
            #     (unreliable) index tells them apart.
            own_sig = ((a["type"], a["x"], a["y"], a["order"], tuple(a["legs"]))
                       == (cand["type"], post_tile[0], post_tile[1],
                           byte_samples[land_i][2], tuple(post_legs)))
            if own_sig and a["idx"] != cand_idx:
                twin = True                       # a row at ANOTHER index wearing our
            elif own_sig:                         # watched byte + route = ambiguity
                if start_vacated:
                    continue                      # our record, read after it stepped
                twin = False                      # our unit is STILL parked on its start
            else:                                 # tile; the slot's signature is a look-
                twin = False                      # alike's order we never watched land
                fresh_rival = (b is not None
                               and (a["type"], a["x"], a["y"]) == (cand["type"],
                                                                   post_tile[0], post_tile[1])
                               and a["order"] in want_bytes
                               and a["order"] != b["order"] and a["legs"] != b["legs"])
                if not fresh_rival:
                    continue
            rivals.append(dict(idx_before=(b["idx"] if b else a["idx"]),
                               idx_after=a["idx"],
                               type=a["type"],
                               frm=[b["x"], b["y"]] if b else [a["x"], a["y"]],
                               to=[a["x"], a["y"]],
                               order=([b["order"], a["order"]] if b
                                      else [cand["order"], a["order"]]),
                               legs_before=[list(p) for p in (b["legs"] if b else [])],
                               legs_after=[list(p) for p in a["legs"]],
                               mp=a["mp"], twin=twin, cand=False))
    confounded = bool(rivals)
    attributed = claim is not None and not confounded
    return claim, rivals, attributed, confounded



def verify_pending_walks(cur_turn, verbose=False):
    """M54h: finish the accounting for walks ordered on an EARLIER turn.

    A queued MOVE can cost more movement than one turn gives it. Measured M54h
    (`evidence/m54h/probe_chooser_walk1.json`): `g` on rec60 at (29,42) named University
    Base (28,42), the pump stepped it to (28,43) with `+40` = 3 spent, and the last leg
    stayed in the record for a later turn to spend. `verify_moves` only looks at the
    orders issued inside its own turn, so a walk that takes two turns would be reported
    as never landing — and "the loop reached a destination" is exactly what M54h is about.

    Same evidence, same rules as `verify_moves` (the count delta against the order's own
    baseline, plus in-phase `+40`), re-read on every later turn. A walk is reported ONCE,
    on the turn it lands, and then leaves the pending list.
    """
    if not PENDING_WALKS:
        return []
    try:
        _pid, f = mem()
    except Exception:
        return []
    out, keep = [], []
    try:
        me = state().get("player")
        rows = our_rows(f, me)
        own_tiles = own_base_tiles(f, me)      # M54i: same base-array check as verify_moves
        for o in PENDING_WALKS:
            dx, dy = o["dest"]
            hits = [r for r in rows if r["type"] == o["utype"]
                    and (r["x"], r["y"]) == (dx, dy)]
            still = [r for r in rows if r["type"] == o["utype"]
                     and (r["x"], r["y"]) == (o["ux"], o["uy"])]
            c0 = o.get("order_counts") or {}
            d_before, s_before = c0.get("dest"), c0.get("src")
            # M54i2: read the ARRIVAL's mp, not an arbitrary hit's. A unit that walked
            # this round shows +40 spent at our next phase start (scratch/m54i2_pump.py:
            # the moved record read mp 3 while every held unit read 0); garrison/HOLD
            # units and base-produced units on the destination tile sit at 0 (run3
            # census at 2165: three HELD garrisons and a fresh produced unit all mp 0).
            # `hits[0]` is index-order — in run3 turn 0 it was a held garrison, so the
            # arrival's own spent mp was invisible and a memory-verified landing scored
            # `landed false`. max() asks exactly what the floor asks — "some same-type
            # record ON THE DESTINATION TILE spent movement this round" — and the floor
            # itself (mp_after > 0, plus the count delta) is unchanged.
            mp_after = (o.get("walk_mp") or o.get("mpused_after")
                        or max([h["mp"] for h in hits], default=0))
            # M54j: same rules as verify_moves — the WALKER (the record wearing the
            # ordered route) must be on the dest tile; six identical garrisons are not
            # an arrival. For a CARRIED (multi-turn) walk the pre-press count baseline is
            # stale by design — the origin was vacated rounds ago — so the arrival rule
            # is: identity on the destination + movement spent + the origin tile empty
            # of that type. (A same-turn landing in `verify_moves` still needs the
            # count delta against the press — session 87's run4 had both.)
            route = ((o.get("walk_diff") or {}).get("claim") or {}).get("legs_after") or []
            on_dest = walker_on_dest(rows, o["utype"], (dx, dy), route)
            m = dict(order=o["key"], unit=o["unit"], utype=o["utype"],
                     frm=[o["ux"], o["uy"]], dest=[dx, dy],
                     landed=on_dest and mp_after > 0 and not still,
                     on_dest_after_exec=bool(hits), carried=True,
                     ordered_turn=o.get("ordered_turn"),
                     mp_after=mp_after, walk_ms=o.get("walk_ms"),
                     dest_count=[d_before, len(hits)], src_count=[s_before, len(still)],
                     dest_is_own_base=bool((dx, dy) in own_tiles),
                     still_at_start=bool(still))
            out.append(m)
            turns_since = cur_turn - (o.get("ordered_turn") or cur_turn)
            if not m["landed"] and turns_since < PENDING_MAX_TURNS:
                keep.append(o)
            if verbose:
                print(f"    CARRY t{o.get('ordered_turn')} rec{o['unit']} "
                      f"({o['ux']},{o['uy']}) -> ({dx},{dy}): "
                      f"{'ARRIVED' if m['landed'] else 'not yet'} "
                      f"(dest count {d_before}->{len(hits)}, origin "
                      f"{s_before}->{len(still)}, mp {mp_after})", flush=True)
        PENDING_WALKS[:] = keep
    finally:
        try:
            f.close()
        except Exception:
            pass
    return out


def service_turn(idx, tr, timeout, verbose=False):
    """Press TURN COMPLETE, then keep servicing whatever the game throws up until the
    mission year in memory actually changes.

    Turns are not a single click: during one turn the game raises the units-not-moved
    confirm, NETFLASH news, tech breakthroughs, Secret Project movies and base screens.
    Every one of those blocks the turn, so a one-shot click-then-wait always times out.

    M54b round-aware budget: a Council round (vote panes + movies + replays) can outlast
    one turn's timeout while the game is ALIVE and answering. The deadline slides forward
    (capped at 3x timeout) as long as consecutive captures differ; a byte-static screen
    does NOT extend it, and after 45 s without a year flip a static screen gets an input
    probe (MENU click): no change = dead input = WEDGED save slot -> report and stop
    (exit 5), never burn the run's budget on it.
    """
    y0 = year()
    st0 = state()
    rec = {"turn": idx, "year_before": y0, "t": time.strftime("%H:%M:%S"), "handled": []}
    t0 = time.time()
    deadline = t0 + timeout
    round_cap = t0 + 3 * timeout
    last_press = 0.0
    last_esc = 0.0
    ordered = False             # S3/M54c: the order step runs at most once per turn
    snap_units = None           # M54d: our records as of just before TURN COMPLETE
    prev_hash = None
    last_change = t0
    last_probe = 0.0
    while time.time() < deadline:
        if not sh("xdotool search --name \"Sid Meier\"").stdout.strip():
            sys.exit("game window gone — driver stopped (avoid pretending the run continued)")
        if year() != y0:
            break
        png = freeze("px")
        now = time.time()
        h = frame_hash(png)
        if prev_hash is not None and h != prev_hash:
            last_change = now
            if deadline < round_cap:
                deadline = min(round_cap, now + timeout)
        prev_hash = h
        words = ocr_fast(png)
        kind = classify(words, region_colors(png), png)
        rec["handled"].append(kind)
        if verbose:
            print(f"    [{kind}] {' '.join(w for w, *_ in words[:16])}", flush=True)
        rec.setdefault("screens", {}).setdefault(kind, 0)
        rec["screens"][kind] += 1
        # Wedge guard (M54b) — `hud` frames ONLY: the hung-resume signature is a static
        # HUD with dead input (session 78); modals like the base screen are legitimately
        # byte-static and must not trigger it (session 79 lost turn 28 to exactly that
        # false positive — evidence/px_wedge_t28.png).
        if (kind == "hud" and now - t0 > 45 and now - last_change > 15
                and now - last_probe > 20):
            last_probe = now
            a = freeze("px_wa")
            click(MENU_BTN)              # diagnostic click: opens the menu iff input lives
            time.sleep(2.2)
            b = freeze("px_wb")
            if frame_hash(b) == frame_hash(a):
                sh(f"cp {b} {EVID}/px_wedge_t{idx}.png")
                stn = state()
                rec["wedge"] = True
                rec["state_before"] = {k: st0.get(k) for k in
                                       ("year", "turn_no", "player", "cur_player",
                                        "turn_flags", "mode_flags", "n_bases",
                                        "bases_ours", "units_ours")}
                rec["state_after"] = {k: stn.get(k) for k in
                                      ("year", "turn_no", "player", "cur_player",
                                       "turn_flags", "mode_flags", "n_bases",
                                        "bases_ours", "units_ours")}
                rec["delta"] = {}
                rec["dt"] = round(time.time() - t0, 1)
                tr.write(json.dumps(rec) + "\n"); tr.flush()
                print(f"turn {idx}: WEDGE — HUD byte-static {round(now - last_change)}s, "
                      f"MENU click changed nothing — reporting a bad slot, not a stall",
                      flush=True)
                sys.exit(5)
            key("Escape")                # close the menu the probe opened (in-game)
            time.sleep(1.2)
        # M54c: a faction COMMUNICATION has its own OK bar (y~347) and the console row at
        # y 560 is still drawn under it, so it must be answered before handle_pane's
        # bottom-bar rule mistakes DATALINKS for a close bar (session 80, turn 35).
        if kind == "comm":
            xy = answer_communication(png)
            rec["handled"].append(f"comm-ok@{int(xy[0])},{int(xy[1])}" if xy else "comm:Return")
            time.sleep(1.2)
            continue
        # M54a: the Council vote row and the HIVE bribe pane come up in BOTH phases (the
        # Council convenes while cur_player is an AI), and neither has a control OCR can
        # see, so they get a handler ahead of the generic dialog/Escape paths.
        if kind in ("dialog", "unknown", "movie") and handle_pane(words, png, rec, kind):
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
            # M54j: arm our walker DURING the AI round. probe2 (scratch/m54j_probe2.py,
            # read back on a live handle): a record poked +17 2 -> 0 mid-round is still
            # byte 0 and unmoved when our phase opens, and the phase then WAITS (flags 0
            # for ~8 s of sampling); a phase where every record is HELD draws "No units
            # need new orders. Press ENTER" and auto-advances before the driver's first
            # OCR (run2/run3: 0 orders on 6/6 turns). One arming per run; the order step
            # finds the armed record via find_actionable on the first hud frame.
            if not PRE_ARM_DONE[0] and ORDER_CAP > 0:
                PRE_ARM_DONE[0] = True
                try:
                    _pid2, f2 = mem()
                    try:
                        me2 = state().get("player")
                        react = pick_reactivation(held_walk_records(f2, me2),
                                                  own_base_tiles(f2, me2),
                                                  delta_table(f2))
                        if react:
                            wr(f2, UNIT_ARR + react[0]["idx"] * 52 + 17, b"\x00")
                            f2.flush()
                            rec["handled"].append(f"pre-arm:rec{react[0]['idx']}")
                            if verbose:
                                print(f"    PRE-ARM rec{react[0]['idx']} "
                                      f"({react[0]['x']},{react[0]['y']}) +17 2->0 in the "
                                      f"AI round (man {react[0]['man']})", flush=True)
                    finally:
                        f2.close()
                except Exception:
                    pass
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
        elif kind == "help":
            xy = answer_help_page(png)
            rec["handled"].append(f"help-exit@{int(xy[0])},{int(xy[1])}" if xy else "help:Escape")
            time.sleep(1.2)
        elif kind == "dest-chooser":
            # M54d: the `g` chooser is a key sink with an OK bar of its own (y~162).
            # Escape does not answer it, and at a clean HUD behind it Escape raises the
            # quit prompt — click its merged OK row.
            xy = answer_dest_chooser(png, verbose)
            rec["handled"].append(f"dest-chooser-ok@{int(xy[0])},{int(xy[1])}" if xy
                                  else "dest-chooser:Return")
            time.sleep(1.0)
        elif kind == "artwork-close":
            # M54d: the scene panel is closed by its own red bar, not by a key: the movie
            # branch only presses Escape and Escape is gated, which froze two runs.
            xy = close_bar(png)
            if xy:
                click(xy)
            rec["handled"].append(f"artwork-close@{int(xy[0])},{int(xy[1])}" if xy
                                  else "artwork-close:no-bar")
            time.sleep(1.2)
        elif kind == "confirm":
            answer_confirm(words)
        elif kind == "dialog":
            key("Return"); time.sleep(0.5)      # default button = OK
        elif kind == "hud":
            # M54h: a modal wearing the HUD chrome (see `modal_caption`) has to be ANSWERED,
            # not walked past: the OPERATIONS DIRECTOR "Investigate pod beacon?" pane ate a
            # whole turn of TURN COMPLETE clicks landing BEHIND it. Return is a dialog's
            # default button (it cleared this very pane today in scratch/m54h_clear.py), and at
            # a genuinely clean HUD Return IS TURN COMPLETE, so a false positive still ends the
            # turn rather than idling it.
            if modal_caption(words):
                rec["handled"].append("hud-with-caption")
                key("Return"); time.sleep(0.9)
                continue
            # S3 / M54c: order our own units BEFORE ending the turn. This branch is only
            # reachable in OUR phase (the cur_player/turn_flags gate above `continue`s on
            # an AI round), which is exactly the window where a hotkey is an order rather
            # than a key sink. `ordered` makes it once-per-turn even if it fails.
            if not ordered and ORDER_CAP > 0:
                ordered = True
                nver = order_step_in_loop(rec, verbose)
                rec["handled"].append(f"orders:{nver}")
                # M54d: freeze our records NOW — TURN COMPLETE is the execution, and a
                # walk is only proven by what the records say after the year flips.
                snap_units = snap_our_units()
                continue
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
        elif kind == "base":
            # M54b: Escape is the base screen's documented close, and the class is
            # unambiguous (classify tests quit-prompt and title FIRST, and since M54a
            # the base test is positional), so it may fire even inside the --no-escape
            # gate. Session 79 lost turn 28 because the gate starved this path: the
            # base screen sat byte-static for 42 s with the turn unflippable.
            if time.time() - last_esc > 6:
                key("Escape"); last_esc = time.time()
            time.sleep(0.4)
        else:                                    # movie / unknown
            # M54h: a CLEAN HUD whose TURN COMPLETE row failed to OCR classifies `unknown`.
            # Measured live at (28,42) with the base label drawn on the map: 2x OCR finds
            # MENU (61,369) and COMMLINK but neither "TURN" nor "COMPLETE" (region_colors
            # 167), so the `hud` branch — the only thing that clicks the button — never
            # runs, and with --no-escape the loop idles out the whole turn budget while the
            # year sits unmoved in OUR phase (trace_m54h_20261025_093424 turn 2).
            # Fallback, not a reclassification: in OUR phase, with the HUD chrome present,
            # NO bar band in the modal band (a chooser/dialog/pane always draws bars at
            # y 145-200) and the year unmoved for HUD_BLIND_S, click TURN COMPLETE at its
            # measured coordinates. If a modal really is up the click lands behind it and
            # the year simply stays where it is.
            # M54j: the OUR-PHASE gate below is memory-verified; the order step runs on
            # the FIRST frame that passes it, NOT gated by HUD_BLIND_S — with everything
            # HELD the game draws "No units need new orders. Press ENTER", TURN COMPLETE
            # stops OCR-ing, the frame classifies `unknown`, and the game's own ENTER
            # advances the turn in seconds (run2: 4 of 6 turns, order step never ran).
            no_modal_bars = not [b for b in pane_bars(png, y0=145) if 145 <= b[1] <= 200]
            hud_chrome = (find(words, ["menu"]) and find(words, ["commlink"])
                          and no_modal_bars)
            # M54k (measured, run2 turn 1, evidence/px_m54k_banner_probe.png at 2173): the
            # map HUD with the production line drawn in the message box ("Korolev Center
            # builds ScoutPatrol.") OCRs as GARBAGE — no MENU, no COMMLINK — so hud_chrome
            # was false while memory said OUR phase (cur_player 3, turn_flags 0) and the
            # whole 240 s turn budget burned with NO input ever sent (the turn would have
            # been recorded STUCK). OCR lies about legibility (§ traps); memory + "nothing
            # drawn in the modal band" is the clean-HUD oracle, so the our-phase blind
            # gates use THAT, not the OCR chrome read. A click behind a real modal is
            # harmless (the year stays where it is).
            if kind == "unknown" and no_modal_bars:
                st_now = state()
                if (st_now.get("cur_player") == st_now.get("player")
                        and not (st_now.get("turn_flags") or 0) & 2
                        and not ordered and ORDER_CAP > 0):
                    ordered = True
                    nver = order_step_in_loop(rec, verbose)
                    rec["handled"].append(f"blind-orders:{nver}")
                    snap_units = snap_our_units()
                    continue
            if (kind == "unknown" and now - last_press > HUD_BLIND_S
                    and now - t0 > HUD_BLIND_S):
                st_now = state()
                if (st_now.get("cur_player") == st_now.get("player")
                        and not (st_now.get("turn_flags") or 0) & 2
                        and no_modal_bars):
                    click(TURN_BTN)
                    rec["handled"].append("turn-complete-blind")
                    last_press = now
                    if verbose:
                        print("    HUD blind: OCR found no TURN COMPLETE row — clicked the "
                              "button at its measured place", flush=True)
                    for _ in range(4):
                        time.sleep(0.15)
                        if year() != y0:
                            break
                    continue
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
    if ok:
        # M54d: the year flipping IS the execution. The walk is proven here, by comparing
        # the records against the ordered leg — not by a screenshot.
        rec["moves"] = verify_moves(rec.get("orders", []), snap_units, verbose) \
            if snap_units else []
        # M54h: a queued MOVE can cost more movement than one turn gives it, so a walk
        # ordered on an earlier turn is re-read every later turn and reported on the turn
        # it actually lands.
        carried = verify_pending_walks(idx, verbose)
        rec["moves"] = carried + rec["moves"]
        rec["moves_verified"] = sum(1 for m in rec["moves"] if m["landed"])
        for o in rec.get("orders", []):
            if (o.get("verified") and o.get("order_after") == 0x18 and o.get("dest")
                    and tuple(o["dest"]) != (o.get("ux"), o.get("uy"))
                    and not any(m.get("landed") and m.get("unit") == o["unit"]
                                for m in rec["moves"])):
                o["ordered_turn"] = idx
                PENDING_WALKS.append(o)
    st1 = state()
    rec["state_before"] = {k: st0.get(k) for k in ("year", "turn_no", "player", "cur_player",
                                                   "turn_flags", "mode_flags", "n_bases",
                                        "bases_ours", "units_ours")}
    rec["state_after"] = {k: st1.get(k) for k in ("year", "turn_no", "player", "cur_player",
                                                  "turn_flags", "mode_flags", "n_bases",
                                        "bases_ours", "units_ours")}
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
TILE_PITCH_G = 0x692184           # DAT_00692184 row pitch, READ LIVE (32 on this 64x64 map)
TILE_ROW = 40                     # DAT_00692184, read live = 40
TILE_SZ = 0x2C

# hotkey -> #TERRAIN mode (ORDERS.md §2 table; xdotool key names)
ORDER_KEYS = {
    "f": 0, "M": 2, "m": 2, "S": 3, "s": 3, "F": 4, "r": 5, "K": 7, "k": 7,
    "period": 8, "o": 9, "n": 0xc, "E": 0xd, "B": 0xe, "q": 0xf,
    "bracketright": 0x10, "bracketleft": 0x11, "underscore": 0x12,
}

# S3 / M54c — the same orders, INSIDE the unattended loop (see order_step_in_loop).
ORDER_TRY_KEYS = ("f", "M", "S", "F", "r", "o", "n", "E", "K", "B", "q", "m", "s")   # preference order, ORDERS.md §2
ORDER_CAP = 2              # VERIFIED orders to issue per player turn (0 = loop never orders)
ORDER_BUDGET = 35.0        # wall-clock cap on one turn's order step, seconds
ORDER_MAX_ATTEMPTS = 8     # hard cap on keypresses per turn (bounds the cost of dead ends)
ORDER_MODAL_TIMEOUT = 22.0  # cap on servicing the panes one keypress raised, seconds
ORDER_REJECTS = {}         # type -> how many times every tried key was refused (live, per run)
ORDER_KEY_REJECTS = {}     # key -> attempts that produced no +17 delta (live, per run)

# M54g — the colonist FOUNDING, issued in the loop and verified in the BASE ARRAY.
# `b` (case 0x62, shard_013.c:4384) dispatches to FUN_004d1280 unless the unit's type is
# class 9 (-> the borehole mode); FUN_004d1280 gates on class 8 (NEEDCOLONISTS) and then
# on the tile. It writes NO order byte: its proof is a new base record (0x95DA10, count
# 0x985AF4), and it consumes the founding unit (record 11 compacted away 0.1 s after the
# name pane was answered, evidence/m54g/probe_found1.json).
FOUND_KEY = "b"
FOUND_CLASS = 8            # the class gate at shard_012.c:2852
FOUND_TRIES = [3]          # keypress cap for foundings per run (mutable: decremented live)
FOUND_MODAL_TIMEOUT = 45.0  # wall-clock cap on answering NEWBASE + the aftermath
FOUND_DONE = [False]       # one founding per run is enough to prove the destination
ORDER_KEY_TRIES = 3        # retire a key for the rest of the run after this many duds

# Non-terraform keyboard orders, verified by the SAME `+17` delta. Measured live on this
# build against a selected Scout Patrol (`evidence/m54c_probe.txt`): `l` took `+17` 0->1
# on records 0 AND 3 with no pane and no energy change; plain `Up`/`Right` did NOT order
# the unit (arrows drive the map cursor — `Right` even opened the base pane) and
# `shift+Up` raised a pane. So the keys that are safe to fire blind at a selected unit
# are `g` (queued MOVE to own base, ORDERS.md §4 byte 0x18), `l` (SENTRY, 1) and
# `h` (HOLD, 2). Escape is never one of them: on a plain HUD Escape raises the quit
# prompt, and Return on that prompt is "Yes, that's an order, mister!" = the game exits.
ORDER_SIMPLE = (("g", {0x18}, "move-to-base"), ("l", {1}, "sentry"), ("h", {2}, "hold"))
# M54d: `g` is the one key that makes a unit WALK (byte 0x18, route in the leg arrays), so
# the in-loop plan tries it before anything else — see order_step_in_loop. Split out so the
# plan can put it first without firing it twice.
ORDER_MOVE = ("g", {0x18}, "move-to-base")
ORDER_SIMPLE_NO_MOVE = (("l", {1}, "sentry"), ("h", {2}, "hold"))
WALK_POLL = 3.0            # M54e: seconds to watch the record after a queued MOVE is
                           # answered — the pump runs the order THEN, not at EXEC
HUD_BLIND_S = 25.0         # M54h: how long a clean-but-unreadable HUD (class `unknown`,
                           # our phase, chrome present, no modal bars) waits before the
                           # driver clicks TURN COMPLETE at its measured coordinates
ORDER_TERRAFORM_WANT = set(range(4, 0x18))     # #TERRAIN index + 4 (mode rewrites allowed)
ORDER_BYTE_NAMES = {1: "sentry", 2: "hold", 3: "convoy", 0x18: "move-to-base",
                    0x19: "move-dir", 0x1b: "road-to-base", 0x1c: "tube-to-base"}


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


def find_actionable(f, me, n=119):
    """Unmoved, actionable units owned by us — the game's OWN select gate (NAMED.md
    `0x40c8d0` / `0x5acc00`: owner == current player, not frozen at `+9`, movement not
    spent at `+40`) — but WITHOUT the class-9 pre-filter find_former applies.

    Why no class filter (M54c, live): in the `m54b_clean.SAV` position at 2153 every one
    of our six records decodes to type 2 (`Scout Patrol`, class 3) and NO class-9 record
    exists for us at all, and `f` on records 0 and 20 changed neither `+17` nor faction
    energy (`evidence/m54c_probe.txt`). A hard class filter therefore ordered nothing.
    The memory delta is the oracle; this is only a candidate PICKER, and a
    faction-variant type (`type >= 64`, NAMED.md `0x98adb2`) whose class byte does not
    read 9 must stay reachable. `cls` is carried so class-9 units get tried first.
    """
    import struct
    out = []
    arr = rd(f, UNIT_ARR, n * 52)
    for i in range(n):
        d = arr[i * 52:(i + 1) * 52]
        if d[14] != me or d[14] == 0xFF:
            continue
        if bool(d[9]) or d[17] != 0 or d[40] != 0:      # frozen / already ordered / moved
            continue
        typ = struct.unpack("<H", d[10:12])[0]
        out.append(dict(idx=i, x=struct.unpack("<h", d[0:2])[0],
                        y=struct.unpack("<h", d[2:4])[0], type=typ, cls=unit_class(f, typ),
                        order=d[17], mpused=d[40],
                        flags=struct.unpack("<I", d[4:8])[0]))
    return out


def energy(f, player):
    import struct
    return struct.unpack("<i", rd(f, ENERGY_G + player * ENERGY_STRIDE * 4, 4))[0]


def tile_recs(f, x, y):
    """The 0x2c tile record for (x,y).

    M54g correction (live, this box): 0x92ae14 holds a POINTER to the tile array
    (`mov esi,[ds:92ae14]`, M35) and the row pitch is DAT_00692184, which is 32 here
    (a 64x64 map) — the hard-coded 40 was an 80-wide world. Indexing the slot itself
    reads pointer data, not tiles (all-zero "tiles" at (28,42) while the base is there).
    Record = *(0x92ae14) + (pitch*y + x>>1)*0x2c.
    """
    import struct
    base = struct.unpack("<I", rd(f, TILE_G, 4))[0]
    pitch = struct.unpack("<I", rd(f, TILE_PITCH_G, 4))[0]
    a = base + (pitch * y + (x >> 1)) * TILE_SZ
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


# ---------------------------------------------------------------------------
# S3 / M54c — orders INSIDE the unattended loop.
#
# give_order() is the lab harness: it works, but only when someone runs `--order`, so
# the spine-S2 driver never MOVED a unit. This is the fold-in: in our own phase, while
# the screen is the HUD, pick a waiting Former out of memory, poke the selection slot,
# press a REAL terraform hotkey, service the payment panes the setter raises
# synchronously, and PROVE the order by the memory diff it caused — order byte 0 ->
# 4..0x17 plus the energy debit. The byte is the only honest oracle: ORDERS.md §2 says
# a dropped keypress and a rejected order look identical from the outside.
#
# The check is a RANGE, not `== mode + 4`, because of the documented mode rewrites
# (ORDERS.md §2: mode 5 Road -> 6 Mag Tube on a road tile, mode 0 Farm -> 1 Soil
# Enricher or 0xa by tile bits) that happen BEFORE validation, so the landed byte can
# legitimately differ from the pressed key's mode. `expected_byte` is recorded anyway.

def order_byte_watcher(idx, stop, out, dur=1.5, recs=None):
    """M54e: sample unit `+17` at ~5 ms resolution from a second /proc/pid/mem handle.

    The `g` chooser's OK click lands the byte and the game's own order pump eats it a tick
    later; the gap is tens of milliseconds, and a single read after the click lands on
    either side of it (session 81 read 0 and called the order unverified; the 2026-10-25
    smoke run read 0 on a walk that had already landed). A burst that spans the click
    catches the byte itself, which is the delta the milestone asks for.

    M54i: pass `recs` to collect the WHOLE 52-byte record with each sample (the legs
    belong to the same read as the byte — an attribution must not mix a byte from one
    sample with legs from another).
    """
    import threading

    def loop():
        try:
            _pid, g = mem()
        except Exception:
            return
        t0 = time.time()
        try:
            while not stop.is_set() and time.time() - t0 < dur:
                try:
                    if recs is not None:
                        raw = rd(g, UNIT_ARR + idx * 52, 52)
                        recs.append((raw, round((time.time() - t0) * 1000), raw[17]))
                        out.append((round((time.time() - t0) * 1000), raw[17]))
                    else:
                        out.append((round((time.time() - t0) * 1000),
                                    rd(g, UNIT_ARR + idx * 52 + 17, 1)[0]))
                except Exception:
                    break
                time.sleep(0.005)
        finally:
            try:
                g.close()
            except Exception:
                pass

    th = threading.Thread(target=loop, daemon=True)
    th.start()
    return th


ORDER_MOVE_KEY = ORDER_MOVE[0]          # "g"
MOVE_ORDER_RETRIES = 2                  # attempts AFTER the first


def resolve_move_dest(pick, pts):
    """M54i2: where a queued MOVE is BOUND for — the chooser's named base, not a leg.

    Measured live 2026-10-25 (run m54i2_run1 turn 3, read back after the walk started):
    the OK we answered named `University Base (28,42)` and the record's leg array holds
    `(11,17)` — the FIRST STEP of the route, not the end. `+20..+27`/`+28..+35` carry one
    step the pump is about to take (session 82's oscillating walker re-read the pair every
    round; `FUN_005a071e` rewrites them on each arrival), so the last leg is a waypoint,
    not a destination. The chooser's own pick is the ordered destination; the legs stay
    the fallback for a move that was queued without a chooser row.
    """
    base = (pick or {}).get("base")
    if base is not None:
        return [base[0], base[1]]
    return list(pts[-1]) if pts else None


def move_order_needs_retry(order, attempts):
    """M54i2: when is a `g` worth RE-RAISING? (session 86's two live failure modes)

    (a) the chooser's OK landed `+17 = 0x18` with LEGS STILL EMPTY (run5 t3: `claim None,
        rivals 0` — a MOVE queued with no route; a second OK after a row click may write
        the route); or the diff refused to attribute (confounded / unclaimed) — the
        destination is not knowable from this attempt;
    (b) the keypress FELL THROUGH to the cursor-tile handler (ORDERS.md §1 rule 3: with
        orders mode off, or with the game's own selection unset, `g` opens the BASE
        SCREEN of the base near the map cursor and the dispatcher never sees it —
        session 86 run5 turn 0) — the pane list says so (`base`).

    Only a MOVE order retries: `l`/`h`/terraform keys land without a chooser, and a
    failed founding must not be pressed twice. `attempts` counts PRIOR attempts.
    """
    if order.get("key") != ORDER_MOVE_KEY or attempts >= MOVE_ORDER_RETRIES:
        return False
    dud_pane = "base" in (order.get("panes") or [])
    landed_no_route = bool(order.get("verified")) and not order.get("dest")
    return dud_pane or landed_no_route


def issue_order_for_unit(f, me, cand, kname, verbose=False, want=None, label="terraform",
                         avoid=None):
    """M54i2: one hotkey on one selected unit, RE-RAISED when a MOVE says it fell through.

    `_issue_order_once` is the measurement; this wrapper applies `move_order_needs_retry`
    (at most `MOVE_ORDER_RETRIES` re-raises, MOVE keys only) and records every attempt in
    `attempts` so the trace shows the retries rather than smoothing them over.
    """
    out = _issue_order_once(f, me, cand, kname, verbose=verbose, want=want,
                            label=label, avoid=avoid)
    attempts = [dict({k: v for k, v in out.items() if k != "attempts"},
                     attempt=0)]
    n = 0
    while move_order_needs_retry(out, n):
        n += 1
        if verbose:
            print(f"    re-raising `{kname}` (attempt {n}): "
                  f"panes={out.get('panes')} dest={out.get('dest')}", flush=True)
        nxt = _issue_order_once(f, me, cand, kname, verbose=verbose, want=want,
                                label=label, avoid=avoid)
        attempts.append(dict({k: v for k, v in nxt.items() if k != "attempts"},
                             attempt=n))
        out = nxt
    out = dict(out)
    out["attempts"] = attempts
    return out


def _issue_order_once(f, me, cand, kname, verbose=False, want=None, label="terraform",
                      avoid=None):
    """One hotkey on one selected unit. Returns the record with its memory delta.

    `want` is the set of `+17` bytes this key may legitimately produce (ORDERS.md §4).
    Verification is `+17` MOVING INTO `want` — never a screenshot, never "we pressed the
    key": ORDERS.md §2 says a dropped keypress and a rejected order look identical from
    outside, and a pane that swallows the event looks like both.
    """
    struct = __import__("struct")
    want = ORDER_TERRAFORM_WANT if want is None else want
    mode = ORDER_KEYS.get(kname)
    idx = cand["idx"]
    before = unit_rec(f, idx)
    # M54i: the record's legs BEFORE the keypress — stale legs from an earlier turn are
    # not evidence of THIS order; only a leg array that CHANGED is.
    before_legs = legs_of(before["raw"])
    # M54i: snapshot EVERY record we own before the keypress; after the OK the ordered
    # record is found by DIFF (`diff_order_records`), never by trusting `idx` — session
    # 85's loop read legs naming bases nobody ordered, off the one index it carried.
    snap_before = our_rows(f, me)
    e0 = energy(f, me)
    ta, tb = tile_recs(f, cand["x"], cand["y"])
    focus()
    wr(f, SEL_G, struct.pack("<i", idx))
    sh(f'xdotool key --clearmodifiers "{kname}"')
    panes, quiet, t0 = [], 0, time.time()
    queued = {"order": None, "legs": None}   # M54e: +17/legs sampled AS the pane is answered
    picks = []                                # M54h: which chooser row we clicked, and why
    while time.time() - t0 < ORDER_MODAL_TIMEOUT:
        ob = rd(f, UNIT_ARR + idx * 52 + 17, 1)[0]        # cheap oracle: the byte FIRST
        if ob != before["order"] and ob in want:
            break
        png = freeze("om")
        w = ocr_fast(png)
        k = classify(w, region_colors(png), png)
        if k == "hud":
            quiet += 1
            if quiet >= 2:
                break
            time.sleep(0.5)
            continue
        if k == "quit-prompt":
            # Escape = "Oops, no, wait!". Return here is "Yes, that's an order, mister!"
            # and the process is gone (the trap that killed the 120-turn run), and a
            # stray Escape at a plain HUD is what RAISES this pane.
            panes.append("quit-prompt")
            key("Escape"); time.sleep(1.0)
            continue
        if k == "dest-chooser":
            # M54d: `g` raises its own SELECT DESTINATION chooser. It used to classify
            # `hud`, so this loop read two "quiet" HUD frames and gave up with the order
            # unlanded while the pane was still eating keys — 10 keys, 0 order bytes,
            # evidence/m54d/probe_unit0.json. Answer ITS OK bar, never Escape (Escape at a
            # clean HUD behind it raises the quit prompt).
            panes.append("dest-chooser")
            # M54e: the OK click both WRITES the order (the setter only lands after its
            # pane is answered — session 81's `order_after 0`) and hands the unit to the
            # game's own order pump, which eats the byte a tick later. The gap is tens of
            # milliseconds, so sample THROUGH the click instead of after it.
            import threading
            stop, seen_bytes, seen_recs = threading.Event(), [], []
            th = order_byte_watcher(idx, stop, seen_bytes, recs=seen_recs)
            pick = {}
            answer_dest_chooser(png, verbose, words=w, f=f, me=me,
                                avoid=(before["x"], before["y"]), out=pick)
            if pick.get("chooser_pick"):
                picks.append(pick["chooser_pick"])
            time.sleep(0.35)
            stop.set()
            th.join(timeout=2.0)
            hit = [b for _raw, _ms, b in seen_recs if b in want and b != before["order"]]
            snap_after = our_rows(f, me)
            # M54i: the watcher samples THE CANDIDATE's record slot, so the 0 -> byte
            # transition seen there is the proof the keypress landed on the unit we
            # raised the key against — and the legs read from the SAME samples are that
            # record's route. `snap_after` is only consulted for RIVALS (records on the
            # same tile that got a fresh order we did not watch land): by the time it is
            # taken the pump may have consumed the byte, and a unit built mid-run may
            # have shifted every index after it.
            claim, rivals, attributed, confounded = diff_order_records(
                snap_before, idx, want, seen_recs, before_legs,
                after=snap_after, pre_order=before["order"])
            if hit:
                queued["order"] = hit[0]
                # M54i: the legs come from the DIFF-qualified record, not from `idx`.
                # `claim` is the candidate's record when the watcher caught the byte on
                # it and nothing else could have been the unit we ordered; that is what
                # makes the destination attributable to THIS keypress.
                queued["legs"] = ((claim["raw_after"] if claim else seen_recs[-1][0])
                                  if seen_recs else rd(f, UNIT_ARR + idx * 52, 52))
                queued["samples"] = [(ms, b) for _r, ms, b in seen_recs[:60]]
                queued["diff"] = dict(claim=claim, rivals=rivals,
                                      attributed=attributed, confounded=confounded,
                                      n_changed=1 if attributed else 0,
                                      n_samples=len(seen_bytes))
                if verbose:
                    print(f"    +17 burst through the chooser OK: {seen_bytes[:12]}",
                          flush=True)
                    print(f"    record diff: attributed={attributed} confounded={confounded} "
                          f"claim={ {k: v for k, v in (claim or {}).items() if k != 'raw_after'} } "
                          f"rivals={rivals}", flush=True)
                break
            time.sleep(0.4)
            quiet = 0
            continue
        if k in ("dialog", "confirm", "unknown") and is_terraform_pane(w):
            panes.append("terraform:" + k)
            if answer_terraform_pane(w, verbose) is None:
                break
            quiet = 0
            continue
        panes.append(k)                                    # advisor pane / stray modal
        if len(panes) > 4:
            break
        if k == "base":
            # The base screen is what a dud `g` (or `Right`) opens, and it is a KEY SINK:
            # the smoke run's `l` on rec7 was swallowed by exactly this pane
            # (evidence/trace_m54c_smoke2_*.jsonl turn 0, panes [base, unknown, base]).
            # Escape is its documented close (M54b); Return does nothing to it.
            key("Escape"); time.sleep(0.9)
            continue
        key("Return")                                      # default button = OK
        time.sleep(0.7)
    after = unit_rec(f, idx)
    e1 = energy(f, me)
    ta2, tafter = tile_recs(f, cand["x"], cand["y"])
    # M54e: the chooser's OK lands the byte and hands the unit to the pump in the same
    # game tick, so `after` may already show the CONSUMED byte (session 81 read
    # `order_after 0` on a walk that had already happened). Either sample proves the
    # delta: the one taken as the pane was answered, or the one taken now.
    seen = queued["order"] if queued["order"] is not None else after["order"]
    byte_delta = seen != before["order"] and seen in want
    if queued.get("diff") is None and byte_delta:
        # M54i: the chooser was answered by its DEFAULT button (Return on a pane that
        # classified `unknown` — run m54i_run2 turn 0) or the byte landed between two
        # reads, so the through-the-click watcher never ran. The same attribution rule
        # applies to the two reads that BRACKET the press: the pre-press snapshot and
        # the post-press read of the slot we keyed. A 0 -> byte transition across those
        # two reads with legs that CHANGED attributes the destination to THIS keypress;
        # a rival or a signature twin still says confounded, and stale legs (unchanged)
        # still claim nothing.
        try:
            snap_after = our_rows(f, me)
        except Exception:
            snap_after = None
        bracket = [(before["raw"], -1.0, before["order"]),
                   (after["raw"], 1.0, after["order"])]
        claim, rivals, attributed, confounded = diff_order_records(
            snap_before, idx, want, bracket, before_legs,
            after=snap_after, pre_order=before["order"])
        queued["diff"] = dict(claim=claim, rivals=rivals,
                              attributed=attributed, confounded=confounded,
                              n_changed=1 if attributed else 0,
                              n_samples=2)
        if attributed and claim:
            queued["legs"] = claim["raw_after"]
    # M54d: a queued MOVE carries its route in the record itself — the leg arrays at
    # `+20..+27` (x) and `+28..+35` (y), -1-terminated (ORDERS.md §4 0x18). The LAST leg
    # is the ordered destination, so the walk has a memory-checkable target instead of a
    # guess; `service_turn` compares it against x,y after the year flips.
    dest = None
    src = queued["legs"] if queued["legs"] is not None else after["raw"]
    diff_info = queued.get("diff")
    # M54i: the legs are only THIS order's destination when they sit on the ONE record
    # the keypress changed (`diff_order_records`). A leg array that was already there
    # (a parked decoy, a walker ordered on an earlier turn) names somebody else's
    # trip; session 85 read (14,56)/(17,55) that way. Rival records = two of our
    # indistinguishable units changed at once = confounded = no attribution either.
    attrib = diff_info is None or bool(diff_info["attributed"])
    if diff_info is not None and attrib:
        # the legs travel with the record the diff qualified, wherever it sits
        src = diff_info["claim"]["raw_after"] or src
    walk_diff = (None if diff_info is None else dict(
        attributed=bool(diff_info["attributed"]),
        confounded=bool(diff_info["confounded"]),
        claim=({k: v for k, v in diff_info["claim"].items() if k != "raw_after"}
               if diff_info["claim"] else None),
        rivals=[{k: v for k, v in c.items() if k != "raw_after"}
                for c in diff_info["rivals"]],
        n_samples=diff_info["n_samples"],
        before_legs=[list(p) for p in before_legs]))
    if (kname == ORDER_MOVE[0] or 0x18 in (seen, after["order"])) and attrib:
        lx = [struct.unpack("<h", src[20 + k * 2:22 + k * 2])[0] for k in range(4)]
        ly = [struct.unpack("<h", src[28 + k * 2:30 + k * 2])[0] for k in range(4)]
        pts = [(a, b) for a, b in zip(lx, ly) if a >= 0 and b >= 0]
        # M54i2: the leg array is the NEXT STEP, not the destination (see
        # `resolve_move_dest`); the chooser's named base is the ordered destination.
        dest = resolve_move_dest(picks[-1] if picks else None, pts)
    # M54e: DOES THE WALK LAND, and when? Measured on this build: a parked 0x18 sat
    # through three TURN COMPLETEs without moving (years 2153, 2154, 2155), while the same
    # order executed 100 ms after a chooser OK — the pump (`FUN_0050ef60` -> `FUN_00529e70`
    # -> `FUN_004d1200` -> `FUN_004ce4a0`) runs the order when the game's own cycle visits
    # the unit, and the year flip is not such a visit. The pump also will not path INTO a
    # tile our own units stand on: with four of ours on (6,12) the walker oscillated
    # (6,13)<->(7,12) forever, and the walk landed the moment the base tile was emptied.
    # So watch the record here, right now: landed = it sits on the leg with `+40` spent.
    walk = dict(landed=False, mp=0, ms=None)
    counts0 = {}
    if dest is not None:
        # M54h: the tile evidence has to be a DIFF, not a coincidence. Seven identical
        # Scout Patrols stand on University Base, so "a record of this type sits on the
        # destination" is true before the walk even starts. Count the same-type records at
        # the destination and at the origin and let `verify_moves` require the
        # destination count to rise and the origin count to fall.
        # M54i correction (measured run m54i_run4 turn 0): the baseline MUST be the
        # PRE-PRESS snapshot `snap_before`, not a fresh read after the OK — the pump
        # runs as the chooser's OK is answered (M54e), so a post-OK read sees the origin
        # ALREADY vacated (src 0) and "origin count falls" (still < 0) can then never
        # fire, no matter how cleanly the walk lands. The pre-press count includes the
        # unit itself (src >= 1) and the destination before the walker joins it.
        counts0 = dict(
            dest=sum(1 for r in snap_before if r["type"] == cand["type"]
                     and (r["x"], r["y"]) == (dest[0], dest[1])),
            src=sum(1 for r in snap_before if r["type"] == cand["type"]
                    and (r["x"], r["y"]) == (cand["x"], cand["y"])))
    if dest is not None:
        t1 = time.time()
        while time.time() - t1 < WALK_POLL:
            now = unit_rec(f, idx)
            if [now["x"], now["y"]] == dest and now["mpused"] > 0:
                walk = dict(landed=True, mp=now["mpused"],
                            ms=round((time.time() - t1) * 1000))
                break
            time.sleep(0.1)
        after = unit_rec(f, idx)
    return dict(unit=idx, key=kname, label=label, mode=mode,
                want=sorted(want)[:1] + ([mode + 4] if mode is not None else []),
                ux=cand["x"], uy=cand["y"], utype=cand["type"], ucls=cand.get("cls"),
                order_before=before["order"], order_after=seen, order_final=after["order"],
                order_name=ORDER_BYTE_NAMES.get(seen,
                                                "terraform" if seen in ORDER_TERRAFORM_WANT else None),
                dest=dest, walk_landed=walk["landed"], walk_mp=walk["mp"], walk_ms=walk["ms"],
                chooser_pick=(picks[-1] if picks else None),
                walk_diff=walk_diff,
                order_counts=counts0,
                mpused_after=after["mpused"],
                energy_before=e0, energy_after=e1, energy_delta=e1 - e0,
                tile_addr=hex(ta),
                tile_diff=[f"+{i:02x}:{a:02x}->{b:02x}"
                           for i, (a, b) in enumerate(zip(tb, tafter)) if a != b],
                panes=panes, verified=bool(byte_delta), dt=round(time.time() - t0, 1))


def founding_gate(f, x, y, typ):
    """Why can't a unit of this TYPE found a base at (x,y)? Mirrors FUN_004d1280's tile
    gates (shard_012.c:2838+) read live: NOTINTRIAD ((b0 & 0xe0) < 0x60 XOR the domain's
    DAT_0092ae81[dom*0x90] byte == 1), FUNGUSDANGUS (mask1 & 0x20 and elevation > 3),
    NOTONMONOLITH (mask1 & 0x2000), NOTONROCKY ((b5 & 0xc0) > 0x40 and elevation > 4),
    BASETOONEAR (any of the 8 delta-table neighbours has mask1 bit 0x1 with an owner
    nibble < 8 — the base tile's OWN bit 1 does not block a founding on that tile).
    Empty list = the tile passes. (Live signature: `b` on a class-8 unit at (26,43), a
    tile this reports legal, raised NEWBASE; at (26,42), which it reports NOTONROCKY,
    nothing happened — evidence/m54g/probe_offbase.json / probe_found1.json.)
    """
    import struct
    reasons = []
    d0 = rd(f, 0x98ADAC + typ * 52, 1)[0]                       # type domain byte
    dom1 = rd(f, 0x92AE81 + d0 * 0x90, 1)[0] == 1
    _a, d = tile_recs(f, x, y)
    hi, b5 = d[0] & 0xE0, d[5]
    m1 = struct.unpack("<I", d[8:12])[0]
    if (hi < 0x60) != dom1:
        reasons.append("NOTINTRIAD")
    if (m1 & 0x20) and hi > 0x3F:
        reasons.append("FUNGUSDANGUS")
    if m1 & 0x2000:
        reasons.append("NOTONMONOLITH")
    if (b5 & 0xC0) > 0x40 and hi > 0x5F:
        reasons.append("NOTONROCKY")
    w = struct.unpack("<I", rd(f, 0x92A378, 4))[0]
    h = struct.unpack("<I", rd(f, 0x92A37C, 4))[0]
    even_wrap = (struct.unpack("<I", rd(f, 0x92A394, 4))[0] & 1) == 0
    for k in range(0, 32, 4):
        nx = struct.unpack("<i", rd(f, 0x6784A0 + k, 4))[0] + x
        ny = struct.unpack("<i", rd(f, 0x6784C4 + k, 4))[0] + y
        if even_wrap:
            if nx < 0:
                nx = w + nx
            elif nx >= w:
                nx -= w
        if -1 < ny < h and -1 < nx < w:
            _na, nd = tile_recs(f, nx, ny)
            if (struct.unpack("<I", nd[8:12])[0] & 1) and (nd[2] & 0xF) < 8:
                reasons.append(f"BASETOONEAR via ({nx},{ny})")
                break
    return reasons


def issue_found_for_unit(f, me, cand, verbose=False):
    """Press `b` (BUILD BASE) at one selected unit and PROVE the founding in memory.

    The proof is NOT the order byte — the founding writes none. It is the base array:
    our tile count goes up and one of our bases sits on the tile the unit stood on
    (`own_base_tiles`). Memory-first: poll the array at 100 ms and only OCR when the
    array has not answered, because the NEWBASE pane is modal and every second it is up
    is a second the turn cannot end.
    """
    import struct
    idx = cand["idx"]
    e0 = energy(f, me)
    tiles0 = own_base_tiles(f, me)
    reasons = founding_gate(f, cand["x"], cand["y"], cand["type"])
    om0 = struct.unpack("<i", rd(f, ORDERS_MODE_G, 4))[0]
    om_poked = False
    if om0 == 0:
        # With orders mode off `b` is a MAP-level key: it opens the base screen of the
        # base near the cursor and the order dispatcher never sees it (measured twice,
        # evidence/m54g/probe_c_control.json vs probe_omode.json).
        wr(f, ORDERS_MODE_G, struct.pack("<i", 1))
        om_poked = struct.unpack("<i", rd(f, ORDERS_MODE_G, 4))[0] == 1
    focus()
    wr(f, SEL_G, struct.pack("<i", idx))
    t0 = time.time()
    sh(f'xdotool key --clearmodifiers "{FOUND_KEY}"')
    panes, answered, founded_at = [], [], None
    while time.time() - t0 < FOUND_MODAL_TIMEOUT:
        tiles = own_base_tiles(f, me)
        new = tiles - tiles0
        if new:
            founded_at = sorted(new)[0]
            break
        png = freeze("fd")
        w = ocr_fast(png)
        k = classify(w, region_colors(png), png)
        if k == "name-pane":
            panes.append("name-pane")
            key("Return"); time.sleep(0.4)          # accepts the GENERATED name (M45)
            answered.append("name-pane:Return")
            continue
        if k == "base":                             # a dud `b` opened the base screen
            panes.append("base")
            key("Escape"); time.sleep(0.9)
            break
        if k == "quit-prompt":
            panes.append("quit-prompt")
            key("Escape"); time.sleep(0.9)          # "Oops, no, wait!"
            break
        if k in ("dialog", "confirm"):
            panes.append(k)
            key("Return"); time.sleep(0.7)
            continue
        if k == "hud":
            if len(panes) >= 2:
                break
            time.sleep(1.0)
            continue
        panes.append(k)
        if len(panes) > 4:
            break
        time.sleep(1.0)
    tiles1 = own_base_tiles(f, me)
    after = unit_rec(f, idx)
    e1 = energy(f, me)
    verified = bool(founded_at) and founded_at in tiles1
    out = dict(unit=idx, key=FOUND_KEY, label="found-base", mode=None, ux=cand["x"],
               uy=cand["y"], utype=cand["type"], ucls=cand.get("cls"), gate_reasons=reasons,
               orders_mode_poked=om_poked, panes=panes, answered=answered,
               bases_before=len(tiles0), bases_after=len(tiles1), base_at=list(founded_at or []),
               energy_before=e0, energy_after=e1, energy_delta=e1 - e0,
               unit_after=dict(x=after["x"], y=after["y"], type=after["type"]),
               verified=bool(verified), dt=round(time.time() - t0, 1))
    if verbose:
        print(f"    FOUND rec{idx} ({cand['x']},{cand['y']}) type {cand['type']} "
              f"gates {reasons or 'legal'} -> bases {len(tiles0)}->{len(tiles1)} at "
              f"{founded_at} panes {panes} ({out['dt']}s)", flush=True)
    return out


def order_step_in_loop(rec, verbose=False):
    """Issue up to ORDER_CAP VERIFIED orders (terraform for Formers, MOVE/SENTRY/HOLD for
    every other unit), then return how many landed.

    Called only from service_turn's `hud` branch, which the cur_player/turn_flags gate
    has already established is OUR phase (pressing order keys into a modal or an AI
    round is a key sink — M32). Each waiting Former gets a few keys in preference
    order; the whole step is capped by ORDER_BUDGET so ordering can never eat a turn.
    Every attempt is recorded in rec["orders"]; only the ones with the byte delta are
    `verified`. Caveat recorded in ORDERS.md: unit identity here is the RECORD INDEX,
    which is stable inside our own phase but is NOT a persistent id (the list compacts
    when a unit dies).
    """
    if ORDER_CAP <= 0:
        return 0
    t0 = time.time()
    try:
        _pid, f = mem()
    except Exception:
        return 0
    out = []
    try:
        me = state().get("player")
        if me is None:
            return 0
        cands = find_actionable(f, me)
        own_tiles = own_base_tiles(f, me)      # M54d: `g` is wasted on a unit on its base
        # M54g: a colonist (class 8) standing on a founding-legal tile goes FIRST. `b`
        # spends the unit and the record list compacts, so the index it occupied can be a
        # different unit a second later — nothing else may share the turn. The proof is
        # the base array, not `+17` (the founding writes no order byte).
        if not FOUND_DONE[0] and FOUND_TRIES[0] > 0:
            for fc in [c for c in cands if c["cls"] == FOUND_CLASS
                       and (c["x"], c["y"]) not in own_tiles]:
                FOUND_TRIES[0] -= 1
                o = issue_found_for_unit(f, me, fc, verbose)
                out.append(o)
                if o["verified"]:
                    FOUND_DONE[0] = True
                    rec["founds"] = [o]
                    rec["orders"] = out
                    rec["orders_verified"] = 1
                    rec["order_seconds"] = round(time.time() - t0, 1)
                    return 1
                break
        # M54i2: a candidate standing on a step-table NEIGHBOR of one of our bases
        # (same parity, one legal step away) lands the moment the pump visits it;
        # try those first. Units of the wrong parity for every own base cannot
        # arrive at all — the `can_walk` gate below retires `g` for them.
        try:
            table = delta_table(f)
        except Exception:
            table = []
        nb = set()
        for (bx, by) in own_tiles:
            nb |= table_neighbors(bx, by, table)
        # class-9 (Former) candidates first, then whatever has refused us least this run,
        # then record index — so a position with no Former costs a few keypresses on turn
        # one and nearly nothing afterwards (ORDER_REJECTS accumulates per type).
        cands.sort(key=lambda c: (c["cls"] != 9,
                                  (c["x"], c["y"]) not in nb,
                                  ORDER_REJECTS.get(c["type"], 0), c["idx"]))
        # M54j: byte 2 (HOLD) is the only order that survives the round boundary — the
        # game auto-sentries an order-0 unit across it (run1: the lone actionable at
        # (20,42) wore byte 1 and had PATROLLED AWAY by our phase; scratch/m54j_probe).
        # When nothing is actionable, re-activate the best HELD walker IN-PHASE (poke
        # +17 2 -> 0 in this same window, next to the keypress) and order it.
        if not cands:
            try:
                react = pick_reactivation(held_walk_records(f, me), own_tiles, table)
            except Exception:
                react = []
            for r in react[:ORDER_CAP]:
                wr(f, UNIT_ARR + r["idx"] * 52 + 17, b"\x00")
                cands.append(r)
            if cands and verbose:
                print(f"    REACTIVATED {len(cands)} held walker(s): "
                      f"{[(r['idx'], r['x'], r['y'], r['man']) for r in cands]}",
                      flush=True)
        cands = cands[:ORDER_CAP * 4]
        verified = attempts = 0
        for cand in cands:
            if (verified >= ORDER_CAP or attempts >= ORDER_MAX_ATTEMPTS
                    or time.time() - t0 > ORDER_BUDGET):
                break
            landed = False
            # A Former gets the terraform family first (that is the one that spends
            # energy and rewrites modes); everyone gets the always-valid keyboard orders.
            # M54d: the MOVE key first, for every candidate that can use it. A Former that
            # gets `f` first lands a terraform byte, `landed` stops the plan, and no walk is
            # ever tried — which is how M54c ordered 31 units and moved none.
            # M54h RETRACTS the M54c rule "skip `g` for a unit standing on our base": the
            # chooser lists EVERY base we own (`evidence/m54h/chooser_g60b.png` — two rows
            # for two bases) and OK on a row that is not the unit's own tile lands 0x18 with
            # that base in the legs (`evidence/m54h/probe_chooser_walk1.json`). What `g`
            # cannot do is name the tile under the unit's feet, so `g` is skipped only when
            # our ONLY base is the one it stands on.
            tile = (cand["x"], cand["y"])
            # M54i2: only a base of the candidate tile's OWN (x+y) parity is ever
            # reachable (step-table invariant, see `delta_table`); `g` toward the
            # other one queues a move that oscillates and never lands.
            can_walk = any(t != tile and walk_parity_ok(tile, t) for t in own_tiles)
            plan = (([ORDER_MOVE] if can_walk else [])
                    + ([(k, ORDER_TERRAFORM_WANT, "terraform") for k in ORDER_TRY_KEYS]
                       if cand["cls"] == 9 else [])
                    + list(ORDER_SIMPLE_NO_MOVE))
            for kname, want, label in plan:
                if (landed or attempts >= ORDER_MAX_ATTEMPTS
                        or time.time() - t0 > ORDER_BUDGET):
                    break
                if ORDER_KEY_REJECTS.get(kname, 0) >= ORDER_KEY_TRIES:
                    continue                    # retired for the rest of this run
                attempts += 1
                o = issue_order_for_unit(f, me, cand, kname, verbose, want=want, label=label,
                                         avoid=(cand["x"], cand["y"]))
                out.append(o)
                if o["verified"]:
                    verified += 1
                    landed = True
                    if verbose:
                        print(f"    ORDER rec{cand['idx']} ({cand['x']},{cand['y']}) "
                              f"type {cand['type']} cls {cand['cls']} '{kname}' -> "
                              f"{label} byte {o['order_before']}->{o['order_after']} "
                              f"({o['order_name']}) energy {o['energy_delta']} "
                              f"({o['dt']}s)", flush=True)
                else:
                    ORDER_KEY_REJECTS[kname] = ORDER_KEY_REJECTS.get(kname, 0) + 1
            if not landed:
                ORDER_REJECTS[cand["type"]] = ORDER_REJECTS.get(cand["type"], 0) + 1
        rec["orders"] = out
        rec["orders_verified"] = verified
        rec["order_seconds"] = round(time.time() - t0, 1)
        return verified
    finally:
        try:
            f.close()
        except Exception:
            pass


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
    global WIN, ESC_ALLOW, ORDER_CAP, ORDER_BUDGET
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
    ap.add_argument("--load", default=None, metavar="PATH",
                    help="M54b: start by LOADING this save (Z:\\ path as the game sees "
                         "it). Relaunches the game if no window; walks title -> LOAD "
                         "browser -> confirm -> ops-director itself; a resume with dead "
                         "input is reported as a WEDGE (exit 5), not stalled.")
    ap.add_argument("--orders-per-turn", type=int, default=2, dest="orders_per_turn",
                    help="S3/M54c: VERIFIED terraform orders to issue each player turn "
                         "in the unattended loop (default 2)")
    ap.add_argument("--no-orders", action="store_true",
                    help="S3/M54c: the loop only ends turns; it never issues an order")
    ap.add_argument("--order-budget", type=float, default=35.0, dest="order_budget",
                    help="max seconds one turn's order step may take (default 35)")
    ap.add_argument("--no-verify", action="store_true",
                    help="skip in-loop/post memory reads (use when a tracer holds the process)")
    ap.add_argument("--key-only", action="store_true",
                    help="skip the selection poke (poke BEFORE arming the tracer; pokes are ignored under ptrace)")
    a = ap.parse_args()
    ESC_ALLOW = time.time() + a.no_escape
    ORDER_CAP = 0 if a.no_orders else a.orders_per_turn
    ORDER_BUDGET = a.order_budget
    run_seed = random.randrange(1 << 31)   # recorded in the trace header (M54a)
    os.makedirs(EVID, exist_ok=True)
    for tool in ("xdotool", "xwd", "ffmpeg", "tesseract"):
        if not shutil.which(tool):
            sys.exit(f"missing {tool}")
    if a.load:
        # M54b: the DRIVER answers the load — relaunch if no window, then walk
        # title -> LOAD GAME row -> blind browser (name box + OK bar) -> LOAD
        # confirm -> ops-director -> HUD (scripts/m54a_load.py). A HUD that is
        # static AND ignores the MENU click is a WEDGED slot: report and stop.
        import m54a_load
        m54a_load.SAVE = a.load
        if not find_window():
            print("no window -> relaunching the game (m54a_load.relaunch)", flush=True)
            if not m54a_load.relaunch():
                sys.exit("no window after relaunch")
        WIN = find_window()
        if not state().get("year"):
            argv_save = sys.argv
            sys.argv = [sys.argv[0]]          # keep m54a_load from killing our session
            try:
                rc = m54a_load.main()
            finally:
                sys.argv = argv_save
            if rc == 4:
                sys.exit("WEDGE: this save resumes hung (static HUD, dead MENU input) "
                         "— bad slot, reported not stalled")
            if rc != 0:
                sys.exit(f"load step failed (rc={rc}) — refusing to drive blind")
            WIN = find_window()
    else:
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
           "load": a.load, "orders_per_turn": ORDER_CAP, "order_budget": ORDER_BUDGET,
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
