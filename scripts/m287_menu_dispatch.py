#!/usr/bin/env python3
"""M287: does the in-game MENU PANE click path dispatch the family +0x4c?
(M286 frontier: remaining click-path candidates = the MENU PANES.  TOPMENU/
MAPMENU are title-chain Script.txt panes; the in-game menu dominates them:
MENU button (61,369) raises the console bar GAME/HQ/NETWORK/MAP/ACTION/
TERRAFORM/SCENARIO/EDIT MAP/HELP (chrome, NOT in any Script.txt itemlist -
verified statically), and clicking GAME raises the in-game game menu.)

Reuses M286's arm exactly (12 +0x4c sites, FAM_SLOT 0x5f6aa3 entry, pump
0x5f1394, wndproc 0x5d0c33 LBUTTONDOWN control).  Drive: normalize to the bare
HUD -> click MENU_BTN -> click GAME (the bar's top row) -> FALSIFIER READ
(DIALOG_CUR + vptr: is the raised menu a family instance?) -> click ONE SAFE
row of the game menu (whitelist: LOAD GAME / MULTIPLAYER / VIEW CREDITS /
SCENARIO / options - NEVER start/quick/exit/retire/yes) -> second falsifier
read -> Escape-loop recovery -> detach -> parse.

Pre-registered live states (same contract as M284/M285/M286):
  0 = measured-positive: a +0x4c site fired with slot 0x5f6aa3 (or
      FUN_005f6aa3 entered) AND the live menu vptr at the click was family -
      the menu pane IS a family dialog and its row click dispatches +0x4c.
  4 = measured-negative: clicks delivered + a menu visibly raised, but NO
      family +0x4c dispatch in the window.  If the live vptr did NOT read
      family, the in-game menu is ALSO not one of the 5 family classes (the
      M285 chooser reading).
  5 = driver wedged: no observable menu effect at all - NO MEASUREMENT.
  8 = box left dirty (TracerPid != 0) - invalid measurement.

    python3 scripts/m287_menu_dispatch.py --static   # no box time
    python3 scripts/m287_menu_dispatch.py --live     # the menu-click window
"""
import argparse, json, os, re, struct, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import smac_play as sp  # noqa: E402

IMG = open(os.path.join(ROOT, "programs/terran.exe"), "rb").read()
FAMILY = [0x67164c, 0x6717cc, 0x6728c0, 0x675cc4, 0x6776c8]
FAM_SLOT = 0x5f6aa3
# M284's exhaustive dispatch-form set (whole-image census, merged)
SITES = [(0x4b83f3, "edx"), (0x4ba2e3, "edx"), (0x4c6da9, "ecx"),
         (0x5b7cec, "edx"), (0x5b7dc4, "edx"), (0x5ceec2, "edx"),
         (0x5d9b8e, "eax"), (0x5d9bae, "eax"),
         (0x5fa9df, "edx"), (0x5faddc, "edx"),
         (0x5ffb3b, "eax"), (0x63cfa4, "eax")]
PUMP = 0x5f1394
WNDPROC = 0x5d0c33
DIALOG_CUR = 0x9939c4         # current dialog object pointer (dialogs[] stack, s184)
MENU_BTN = (61, 369)          # in-game console MENU button (m54a, measured)
XENV = {**os.environ, "DISPLAY": ":99"}

# SAFE row whitelist for the raised game menu - prefer Preferences-type rows
# (a modal Escape closes) and 'Switch To Simple Menus'.  NEVER matched:
# resign/quit/start-new-game (y>=548); save/load avoided by construction
# (band + prefix match only, and the fallback row is Preferences).
SAFE_ROWS = ["switch to simple", "switch to detailed", "preferences",
             "warning preferences", "advanced preferences",
             "automation preferences", "audiovisual preferences",
             "audio/visual", "map display", "save game", "load game"]
NEVER = ["resign", "quit", "start new game", "start game", "exit game",
         "retire", "yes that", "new game", "view credits", "scenario"]


def dw(va):
    o = va - 0x400000
    return struct.unpack("<I", IMG[o:o + 4])[0] if 0 <= o + 4 <= len(IMG) else 0


def u32(f, a): return struct.unpack("<I", sp.rd(f, a, 4))[0]


def click(xy):
    subprocess.run(["xdotool", "mousemove", str(xy[0]), str(xy[1])], env=XENV, check=False)
    subprocess.run(["xdotool", "click", "1"], env=XENV, check=False)
    time.sleep(0.4)


def key(k):
    subprocess.run(["xdotool", "key", "--clearmodifiers", k], env=XENV, check=False)
    time.sleep(0.5)


def live_vptr(f, obj):
    """vptr at [obj] via /proc - the falsifier read. -1 on unmapped."""
    try:
        return struct.unpack("<I", sp.rd(f, obj, 4))[0]
    except OSError:
        return -1


def vptr_scan(pid):
    """count live instances of the 5 family vptrs in writable memory."""
    counts = {v: 0 for v in FAMILY}
    try:
        maps = open("/proc/%d/maps" % pid).read().splitlines()
    except OSError:
        return counts
    for line in maps:
        f = line.split()
        if len(f) < 2 or "rw" not in f[1]:
            continue
        lo, hi = (int(x, 16) for x in f[0].split("-"))
        if hi - lo > 0x4000000:
            continue
        try:
            with open("/proc/%d/mem" % pid, "rb", 0) as m:
                m.seek(lo)
                got = m.read(hi - lo)
        except OSError:
            continue
        for v in counts:
            counts[v] += got.count(struct.pack("<I", v))
    return counts


def normalize_hud(pid):
    """Escape while any pane is up until the bare HUD reads (TURN COMPLETE
    row or its bottom status bar).  Returns (hud_seen, n_esc).  NEVER touches
    a 'yes' row; on the really-quit prompt Escape is the safe 'oops' row.
    A raised console bar must be CLOSED even when the HUD reads through it
    (measured twice: an open bar inverts the next MENU click to a close)."""
    for _ in range(6):
        png = sp.freeze("m287_norm")
        words = sp.ocr(png)
        if find_bar_rows(words):          # a raised console bar eats Escape
            key("Escape")                 # exactly once, then re-check
            time.sleep(0.9)
            continue
        kind = sp.classify(words, png=png)
        if kind in ("hud", "title"):
            return True, _
        if sp.hud_status_bar(words):
            return True, _
        key("Escape")
        time.sleep(1.1)
    return False, 6


def find_bar_rows(words):
    """Words of the raised console bar: 'GAME','HQ','NETWORK','MAP','ACTION',
    'TERRAFORM','SCENARIO','EDIT MAP','HELP' in the left band x<220, y 280-620.
    GAME/HQ OCR poorly (measured: GAME=(26,190) on two independent frames;
    NETWORK anchors y=226, rows are 18 px apart).  'network' is the reliable
    anchor - GAME sits two rows above it: (26, network_y - 36)."""
    found = {}
    best_net = None
    for t, cx, cy, w, h in words:
        low = re.sub(r"[^a-z]", "", t.lower())
        if 0 <= cx <= 240 and 180 <= cy <= 650 and low in (
                "game", "hq", "network", "map", "action", "terra",
                "terraform", "scenario", "editmap", "edit", "help", "men"):
            if low == "network" and (best_net is None or cy < best_net[1]):
                best_net = (int(cx), int(cy))
            found.setdefault(low, (int(cx), int(cy)))
    if "game" not in found and best_net is not None:
        ncx, ncy = best_net
        found["game"] = (26, ncy - 36)   # measured geometry (menu_open.png + m287_bar1)
    return found


def find_safe_row(words):
    """Pick the SAFEST row candidate of the RAISED GAME MENU.  The popup
    (vision-verified 2026-11-10, m287_menu.png) spans x~170-455, y~325-595,
    with rows every ~20 px: Switch To Simple Menus (y328), Preferences...
    (y350), Warning/Advanced/Automation/Audio-Visual/Map Display Preferences
    (y370-450), Save Game... (y488), Load Game... (y508), Resign (y548),
    Start New Game (y568), Quit (y588).  OCR on the small popup text is
    unreliable (tesseract returned only bar words on a live frame), so:
    prefer an OCR word INSIDE the menu band with a >=4-char lowercase stem
    that matches a whitelisted prefix; else fall back to the measured
    'Preferences...' row center (172,350) - a modal that Escape closes,
    nowhere near Resign/Quit/Start (rows 10-12, y>=548).  NEVER matched:
    save/load-digit/file rows are avoided, resign/quit/start never."""
    best = None
    for t, cx, cy, w, h in words:
        low = re.sub(r"[^a-z ]", "", t.lower()).strip()
        low = re.sub(r"\s+", " ", low)
        # the popup band only (never the map/HUD words at y<300)
        if 150 <= cx <= 470 and 310 <= cy <= 600 and len(low) >= 4:
            if any(n in low for n in NEVER):
                continue
            for s in SAFE_ROWS:
                if low.startswith(s.strip()):
                    if best is None or cy < best[1]:
                        best = (int(cx), int(cy), low)
                    break
    if best is None:
        best = (172, 350, "preferences")   # measured row 2 of the popup (safe modal)
    return best


def static():
    ok = [True]
    def G(cond, msg):
        print(("PASS " if cond else "FAIL ") + msg, flush=True)
        ok[0] = ok[0] and cond
    # g1: the 12 sites still are `call [reg+0x4c]` (M284 census)
    toks = {}
    for l in open(os.path.join(ROOT, "scratch/m574/text.txt"), errors="replace"):
        f = l.rstrip("\n").split("\t")
        if len(f) < 3: continue
        try: pc = int(f[0].rstrip(":"), 16)
        except ValueError: continue
        toks[pc] = re.sub(r"\s+", " ", f[2].strip().lower())
    bad = [hex(pc) for pc, _ in SITES if not re.search(r"call dword ptr \[e[a-z]+\+0x4c\]", toks.get(pc, ""))]
    G(not bad, "g1: 12 sites still read `call [reg+0x4c]` (%s)" % ("none bad" if not bad else " ".join(bad)))
    # g2: every family vtable's +0x4c IS the family slot
    G(all(dw(v + 0x4c) == FAM_SLOT for v in FAMILY),
      "g2: all 5 family vtables +0x4c == 0x%x" % FAM_SLOT)
    # g3: exactly 5 vtables hold +0x4c == 0x5f6aa3 image-wide
    cnt = sum(1 for va in range(0x400000, 0x700000, 4) if dw(va) == FAM_SLOT)
    G(cnt == 5, "g3: exactly 5 vtables hold +0x4c == 0x5f6aa3 (found %d)" % cnt)
    # g4: the console-bar vocabulary (GAME/HQ/NETWORK/.../EDIT MAP/HELP) is in
    #     NO Script.txt pane text (widgets of any kind) -> the raised bar is
    #     chrome (a game class), so its vptr is measured live
    try:
        d = json.load(open(os.path.join(ROOT, "script_parsed.json")))
        bar_tokens = ["EDIT MAP", "NETWORK", "TERRAFORM"]
        vocab_hits = []
        for p in d:
            alltxt = []
            for w in p.get("widgets", []):
                alltxt.append(str(w.get("kind", "")))
                for k in ("items", "text", "label", "caption"):
                    if isinstance(w.get(k), list):
                        alltxt += [str(x) for x in w[k]]
                    elif w.get(k) is not None:
                        alltxt.append(str(w[k]))
            alltxt += [str(v) for v in (p.get("props") or {}).values()]
            joined = " ".join(alltxt).upper()
            # bar-identifying itemlist: EDIT MAP first (never in rules text),
            # else NETWORK AND a menu-ish neighbor
            toks = [t for t in bar_tokens if t in joined]
            if "EDIT MAP" in toks or (len(toks) >= 2 and any(
                    x in joined for x in ("MAP ", "ACTION", "GAME"))):
                vocab_hits.append(p.get("id"))
        G(not vocab_hits,
          "g4: console-bar vocabulary in NO Script.txt pane (bar is chrome; false hits: %s)"
          % (", ".join(str(x) for x in vocab_hits) or "none"))
    except Exception as e:
        G(False, "g4: script_parsed.json unreadable: %s" % e)
    # g5: a real menu pane with rows exists in Script.txt (TOPMENU) and the
    #     in-game game menu is reachable from the MENU button position
    scr = open(os.path.join(ROOT, "programs/Script.txt"), encoding="latin-1").read()
    lines = scr.splitlines()
    try:
        i0 = lines.index("#TOPMENU")
    except ValueError:
        i0 = -1
    pane = "\n".join(lines[i0 + 1:] if i0 >= 0 else "").split("#MAPMENU")[0]
    G(i0 >= 0 and "START GAME" in pane and "EXIT GAME" in pane,
      "g5: Script.txt #TOPMENU pane has the title menu rows")
    sys.exit(0 if ok[0] else 1)


def arm_gdb(path, pid, log):
    body = ["set pagination off", "set confirm off",
            "handle SIGUSR1 nostop noprint pass",
            "handle SIGUSR2 nostop noprint pass",
            "handle SIGPIPE nostop noprint pass",
            "attach %d" % pid,
            "set logging file %s" % log, "set logging overwrite on", "set logging on"]
    body += ["b *0x%x" % WNDPROC, "commands 1", "silent",
             "if *(int*)($esp+8) == 0x201",
             "printf \\\"CTRL wndproc-lbttdown msg=%08x\\\\n\\\", *(int*)($esp+8)",
             "end", "continue", "end"]
    body += ["b *0x%x" % PUMP, "commands 2", "silent", "printf \\\"CTRL pump\\\\n\\\"",
             "continue", "end"]
    n = 3
    for pc, reg in SITES:
        body += ["b *0x%x" % pc, "commands %d" % n, "silent"]
        # s240 (M293): the guard must admit IMAGE-range vtables (image base
        # 0x400000, PE section table): the five dialog-family vtables
        # 0x67164c/0x6717cc/0x6728c0/0x675cc4/0x6776c8 ALL sit below
        # 0x1000000, so the old guard printed NOTHING for a real family
        # dispatch - every live "0 of 12 sites fired" in M284-M287 is
        # instrument-invalid, not evidence of absence.
        body += ["if $%s >= 0x400000" % reg,
                 "printf \\\"SITE @PC@ @SLOT@\\\\n\\\", $pc, *(int*)($%s+0x4c)" % reg,
                 "end"]
        body += ["continue", "end"]
        n += 1
    body += ["b *0x%x" % FAM_SLOT, "commands %d" % n, "silent",
             "printf \\\"ENTRY retaddr=@PC@ ecx=@CX@\\\\n\\\", *(int*)$esp, $ecx",
             "continue", "end"]
    body += ["continue"]
    txt = "\n".join(body)
    txt = txt.replace("@PC@", "%08x").replace("@SLOT@", "%08x").replace("@CX@", "%08x")
    open(path, "w").write(txt)


def detach_pid(pid):
    out = subprocess.run(["pgrep", "-x", "gdb"], capture_output=True, text=True).stdout.split()
    for p in out:
        cmd = open("/proc/%s/cmdline" % p, "rb").read().replace(b"\0", b" ").decode()
        if "m287.gdb" in cmd or ("attach" in cmd and str(pid) in cmd):
            subprocess.run(["kill", p], check=False)


def live():
    pid, f = sp.mem()
    tp = re.search(r"TracerPid:\s+(\d+)", open("/proc/%d/status" % pid).read())
    if int(tp.group(1)):
        print("STATE 8: box dirty (TracerPid=%d)" % int(tp.group(1))); return 8
    vs0 = vptr_scan(pid)
    print("family vptr scan BEFORE: %s" % vs0, flush=True)
    dcur0 = u32(f, DIALOG_CUR)
    print("PRE-ARM DIALOG_CUR=0x%08x" % dcur0, flush=True)
    # normalize to the bare HUD (base pane needs Escape; Escape on a dialog
    # is its safe close; NEVER a 'yes' row)
    hud, n_esc = normalize_hud(pid)
    print("normalize to HUD: seen=%s esc=%d" % (hud, n_esc), flush=True)
    gdb_script = os.path.join(ROOT, "scratch/m287.gdb")
    LOG = os.path.join(ROOT, "scratch/m287.log")
    if os.path.exists(LOG): os.remove(LOG)
    arm_gdb(gdb_script, pid, LOG)
    gdb = subprocess.Popen(["gdb", "-batch", "-x", gdb_script],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.0)
    sp.find_window(); sp.focus()
    # 1) raise the console bar via the MENU button
    png = sp.freeze("m287_bar0")
    words = sp.ocr(png)
    bar0 = find_bar_rows(words)
    print("bar rows before MENU click: %s" % (sorted(bar0) or "NONE"), flush=True)
    click(MENU_BTN)
    time.sleep(1.6)
    png = sp.freeze("m287_bar1")
    words = sp.ocr(png)
    bar1 = find_bar_rows(words)
    print("bar rows after MENU click: %s" % (sorted(bar1) or "NONE"), flush=True)
    # 2) click GAME (the bar's top row) -> raises the in-game game menu
    game = bar1.get("game")
    if game is None:
        key("Escape"); time.sleep(1.0)     # close the bar we raised
        gdb.send_signal(2)
        try: gdb.wait(6)
        except subprocess.TimeoutExpired: detach_pid(pid); gdb.wait(6)
        print("STATE 5: bar never raised (no GAME row OCR-able) - NO CLICK - NO MEASUREMENT")
        return 5
    click(game)
    time.sleep(1.6)
    # FALSIFIER READ 1: the raised menu object + vptr at the click
    dcur = u32(f, DIALOG_CUR)
    dv = live_vptr(f, dcur)
    print("LIVE at click: menu obj=0x%08x vptr=0x%08x%s" % (
        dcur, dv, " FAMILY" if dv in FAMILY else ""), flush=True)
    png = sp.freeze("m287_menu")
    words = sp.ocr(png)
    print("OCR after GAME click (%d words): %s" % (
        len(words), " ".join(w[0] for w in words[:24])), flush=True)
    # 3) click ONE SAFE row of the raised game menu
    row = find_safe_row(words)
    if row is None:
        # no safe row OCR-able; close the menu (Escape) - no row clicked
        key("Escape"); time.sleep(1.0)
        key("Escape"); time.sleep(1.0)
        gdb.send_signal(2)
        try: gdb.wait(6)
        except subprocess.TimeoutExpired: detach_pid(pid); gdb.wait(6)
        print("STATE 5: game menu raised but NO safe row OCR-able - NO CLICK - NO MEASUREMENT")
        return 5
    print("clicking SAFE row %s (%s)" % (row[:2], row[2]), flush=True)
    click((row[0], row[1]))
    time.sleep(1.8)
    # FALSIFIER READ 2
    dcur2 = u32(f, DIALOG_CUR)
    dv2 = live_vptr(f, dcur2)
    vs1 = vptr_scan(pid)
    print("LIVE after row click: dialog obj=0x%08x vptr=0x%08x%s" % (
        dcur2, dv2, " FAMILY" if dv2 in FAMILY else ""), flush=True)
    print("family vptr scan AFTER: %s (delta %s)" % (vs1, {k: vs1[k] - vs0[k] for k in FAMILY}), flush=True)
    # 4) recovery: Escape-loop until the HUD reads again
    hud2, n2 = normalize_hud(pid)
    print("recovery to HUD: seen=%s esc=%d" % (hud2, n2), flush=True)
    gdb.send_signal(2)
    try:
        gdb.wait(6)
    except subprocess.TimeoutExpired:
        detach_pid(pid); gdb.wait(6)
    st = open("/proc/%d/status" % pid).read()
    if "State:\tT (stopped)" in st:
        subprocess.run(["kill", "-CONT", str(pid)], check=False)
    tp2 = int(re.search(r"TracerPid:\s+(\d+)", open("/proc/%d/status" % pid).read()).group(1))
    rows = [l for l in open(LOG, errors="replace")] if os.path.exists(LOG) else []
    sites_hit = [l for l in rows if l.startswith("SITE")]
    slots = [(int(l.split()[1], 16), int(l.split()[2], 16)) for l in sites_hit if len(l.split()) >= 3]
    fam = [(pc, sl) for pc, sl in slots if sl == FAM_SLOT]
    entries = [l for l in rows if l.startswith("ENTRY")]
    pumps = [l for l in rows if "CTRL pump" in l]
    ctrls = [l for l in rows if "CTRL wndproc" in l]
    print("site bps fired: %d%s; family-slot hits at: %s" % (
        len(sites_hit), "" if not fam else " (SLOT==0x%x)" % FAM_SLOT,
        " ".join("%06x" % pc for pc, _ in fam) or "NONE"), flush=True)
    print("ENTRY hits: %d" % len(entries))
    for e in entries[:8]: print("   %s" % " ".join(e.split()))
    print("pump control hits: %d; wndproc LBUTTONDOWN controls: %d" % (len(pumps), len(ctrls)))
    if tp2:
        print("STATE 8: box left dirty (TracerPid=%d)" % tp2); return 8
    if fam or (entries):
        print("STATE 0: measured-positive - family +0x4c dispatched via site(s) above")
        return 0
    menu_raised = bool(bar1) and (row is not None)
    if not menu_raised:
        print("STATE 5: no observable menu effect - NO MEASUREMENT")
        return 5
    famlive = (dv in FAMILY) or (dv2 in FAMILY)
    print("STATE 4: measured-negative - %d click(s) delivered, bar raised (%d rows), "
          "LIVE menu vptr%s family at the click - family +0x4c dispatched "
          "through NONE of the 12 sites" % (
          len(ctrls), 0 if not bar1 else len(bar1), "" if famlive else " NOT"))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--static", action="store_true")
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()
    if a.static:
        sys.exit(0 if static() else 1)
    if a.live:
        sys.exit(live())


if __name__ == "__main__":
    main()
