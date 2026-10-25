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
    if is_help_page(words):
        return "help"           # full-screen help browser: its profile text contains base
                                # words, so this must run before the base test
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
                                        "turn_flags", "mode_flags", "n_bases")}
                rec["state_after"] = {k: stn.get(k) for k in
                                      ("year", "turn_no", "player", "cur_player",
                                       "turn_flags", "mode_flags", "n_bases")}
                rec["delta"] = {}
                rec["dt"] = round(time.time() - t0, 1)
                tr.write(json.dumps(rec) + "\n"); tr.flush()
                print(f"turn {idx}: WEDGE — HUD byte-static {round(now - last_change)}s, "
                      f"MENU click changed nothing — reporting a bad slot, not a stall",
                      flush=True)
                sys.exit(5)
            key("Escape")                # close the menu the probe opened (in-game)
            time.sleep(1.2)
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
        elif kind == "confirm":
            answer_confirm(words)
        elif kind == "dialog":
            key("Return"); time.sleep(0.5)      # default button = OK
        elif kind == "hud":
            # S3 / M54c: order our own units BEFORE ending the turn. This branch is only
            # reachable in OUR phase (the cur_player/turn_flags gate above `continue`s on
            # an AI round), which is exactly the window where a hotkey is an order rather
            # than a key sink. `ordered` makes it once-per-turn even if it fails.
            if not ordered and ORDER_CAP > 0:
                ordered = True
                nver = order_step_in_loop(rec, verbose)
                rec["handled"].append(f"orders:{nver}")
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

# S3 / M54c — the same orders, INSIDE the unattended loop (see order_step_in_loop).
ORDER_TRY_KEYS = ("f", "M", "S", "F", "r", "o", "n", "E", "K", "B", "q", "m", "s")   # preference order, ORDERS.md §2
ORDER_CAP = 2              # VERIFIED orders to issue per player turn (0 = loop never orders)
ORDER_BUDGET = 35.0        # wall-clock cap on one turn's order step, seconds
ORDER_MAX_ATTEMPTS = 8     # hard cap on keypresses per turn (bounds the cost of dead ends)
ORDER_MODAL_TIMEOUT = 22.0  # cap on servicing the panes one keypress raised, seconds
ORDER_REJECTS = {}         # type -> how many times every tried key was refused (live, per run)
ORDER_KEY_REJECTS = {}     # key -> attempts that produced no +17 delta (live, per run)
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

def issue_order_for_unit(f, me, cand, kname, verbose=False, want=None, label="terraform"):
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
    e0 = energy(f, me)
    ta, tb = tile_recs(f, cand["x"], cand["y"])
    focus()
    wr(f, SEL_G, struct.pack("<i", idx))
    sh(f'xdotool key --clearmodifiers "{kname}"')
    panes, quiet, t0 = [], 0, time.time()
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
    byte_delta = after["order"] != before["order"] and after["order"] in want
    return dict(unit=idx, key=kname, label=label, mode=mode,
                want=sorted(want)[:1] + ([mode + 4] if mode is not None else []),
                ux=cand["x"], uy=cand["y"], utype=cand["type"], ucls=cand.get("cls"),
                order_before=before["order"], order_after=after["order"],
                order_name=ORDER_BYTE_NAMES.get(after["order"],
                                                "terraform" if after["order"] in ORDER_TERRAFORM_WANT else None),
                mpused_after=after["mpused"],
                energy_before=e0, energy_after=e1, energy_delta=e1 - e0,
                tile_addr=hex(ta),
                tile_diff=[f"+{i:02x}:{a:02x}->{b:02x}"
                           for i, (a, b) in enumerate(zip(tb, tafter)) if a != b],
                panes=panes, verified=bool(byte_delta), dt=round(time.time() - t0, 1))


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
        # class-9 (Former) candidates first, then whatever has refused us least this run,
        # then record index — so a position with no Former costs a few keypresses on turn
        # one and nearly nothing afterwards (ORDER_REJECTS accumulates per type).
        cands.sort(key=lambda c: (c["cls"] != 9, ORDER_REJECTS.get(c["type"], 0), c["idx"]))
        cands = cands[:ORDER_CAP * 4]
        verified = attempts = 0
        for cand in cands:
            if (verified >= ORDER_CAP or attempts >= ORDER_MAX_ATTEMPTS
                    or time.time() - t0 > ORDER_BUDGET):
                break
            landed = False
            # A Former gets the terraform family first (that is the one that spends
            # energy and rewrites modes); everyone gets the always-valid keyboard orders.
            plan = ([(k, ORDER_TERRAFORM_WANT, "terraform") for k in ORDER_TRY_KEYS]
                    if cand["cls"] == 9 else []) + list(ORDER_SIMPLE)
            for kname, want, label in plan:
                if (landed or attempts >= ORDER_MAX_ATTEMPTS
                        or time.time() - t0 > ORDER_BUDGET):
                    break
                if ORDER_KEY_REJECTS.get(kname, 0) >= ORDER_KEY_TRIES:
                    continue                    # retired for the rest of this run
                attempts += 1
                o = issue_order_for_unit(f, me, cand, kname, verbose, want=want, label=label)
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
