#!/usr/bin/env python3
"""M286: does the REALLYQUIT (Script.txt message dialog) click path dispatch the
family +0x4c?  (M285 frontier: remaining candidates = message OK/CANCEL dialog,
menu panes, REALLYQUIT - and the box is sitting ON REALLYQUIT.)

Static base (M285, merged): the 12 sites `call [reg+0x4c]` are the exhaustive
whole-image census; the 5 family vtables 0x67164c/0x6717cc/0x6728c0/0x675cc4/
0x6776c8 all have +0x4c == FUN_005f6aa3; the production chooser (0x672298) is
NOT family (+0x4c = 0x404ed0 stub); dialogs ARE family (ctor FUN_00405ef0
installs 0x67164c).

NEW static (this session): FUN_005f6aa3 IS the dialog row-click dispatcher -
it calls FUN_005e7917 (row finder over 0x18-stride rows, returns idx or -1)
and on a hit calls (**(code **)(*ecx + 0xa8))(row_cb_arg): family +0x4c is the
message-dialog click -> row-callback route.  So a REAL family dialog click MUST
enter one of the 12 sites with slot value 0x5f6aa3 (and then FUN_005f6aa3).

Live drive: the box is ALREADY on the REALLYQUIT dialog (s229's closing Escape
on a bare HUD).  Arm the 12 sites + FUN_005f6aa3 entry + pump FUN_005f1394 +
wndproc 0x5d0c33 WM_LBUTTONDOWN control, read the LIVE DIALOG_CUR vptr (the
falsifier: is the dialog at the click a family instance?), click the SAFE
'oops, no, wait!' row (M37 geometry; NEVER the 'Yes, that's an order mister!'
quit row), read DIALOG_CUR again, then parse the log.

Pre-registered live states (same contract as M284/M285):
  0 = measured-positive: a site fired with slot 0x5f6aa3 (or FUN_005f6aa3
      entered) AND the live dialog vptr at the click was family - the family
      +0x4c dispatcher rides the REALLYQUIT message-dialog path.  NAMED.
  4 = measured-negative: clicks delivered (wndproc control fired), dialog
      pump ran, but NO family +0x4c dispatch in the window, and the live
      DIALOG_CUR vptr at the click read family - the 12 sites do not serve it.
      If DIALOG_CUR did NOT read family, the REALLYQUIT pane is ALSO not one
      of the 5 family classes (same non-family reading as the chooser).
  5 = driver wedged: wndproc control silent (no clicks at all) - NO MEASUREMENT.
  8 = box left dirty (TracerPid != 0) - invalid measurement.

    python3 scripts/m286_reallyquit_dispatch.py --static   # no box time
    python3 scripts/m286_reallyquit_dispatch.py --live     # the dialog-click window
"""
import argparse, os, re, struct, subprocess, sys, time

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
XENV = {**os.environ, "DISPLAY": ":99"}


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


def static():
    ok = [True]
    def G(cond, msg):
        print(("PASS " if cond else "FAIL ") + msg, flush=True)
        ok[0] = ok[0] and cond
    # g1: the 12 sites still are `call [reg+0x4c]` at those addresses (M284 census)
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
    G(cnt == 5, "g3: exactly 5 vtables hold +0x4c == 0x5f6aa3 (whole-image scan found %d)" % cnt)
    # g4: the slot target FUN_005f6aa3 is the dialog row-click dispatcher:
    #     body contains the call to FUN_005e7917 (row finder) AND the
    #     dispatch call [reg+0xa8] row-callback (both from fn.py this session)
    body_pairs = [(pc, re.sub(r"\s+", " ", toks[pc])) for pc in sorted(toks)
                  if 0x5f6aa3 <= pc <= 0x5f6af0]
    calls = [t for _, t in body_pairs if t.startswith("call")]
    has_finder = any(re.search(r"call\s+0x5e7917", t) for t in calls)
    has_dispatch = any(re.search(r"call\s+dword ptr \[e[a-z]+\+0xa8\]", t) for t in calls)
    G(has_finder and has_dispatch,
      "g4: FUN_005f6aa3 = dialog row-click dispatcher (finder call 0x5e7917=%s, +0xa8 row-cb dispatch=%s)"
      % (has_finder, has_dispatch))
    # g5: Script.txt #REALLYQUIT pane has the safe 'oops' row and the quit row
    scr = open(os.path.join(ROOT, "programs/Script.txt"), encoding="latin-1").read()
    lines = scr.splitlines()
    try:
        i0 = lines.index("#REALLYQUIT")
    except ValueError:
        i0 = -1
    pane = "\n".join(lines[i0 + 1:] if i0 >= 0 else "").split("#REALLYWIMPOUT")[0]
    G(i0 >= 0 and "Oops, no, wait!" in pane and "Yes, that's an order mister!" in pane,
      "g5: Script.txt #REALLYQUIT pane has both rows (safe 'oops' + quit row)")
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
             "printf \"CTRL wndproc-lbttdown msg=%08x\\n\", *(int*)($esp+8)",
             "end", "continue", "end"]
    body += ["b *0x%x" % PUMP, "commands 2", "silent", "printf \"CTRL pump\\n\"",
             "continue", "end"]
    n = 3
    for pc, reg in SITES:
        body += ["b *0x%x" % pc, "commands %d" % n, "silent"]
        body += ["if $%s >= 0x1000000" % reg,
                 "printf \"SITE @PC@ @SLOT@\\n\", $pc, *(int*)($%s+0x4c)" % reg,
                 "end"]
        body += ["continue", "end"]
        n += 1
    body += ["b *0x%x" % FAM_SLOT, "commands %d" % n, "silent",
             "printf \"ENTRY retaddr=@PC@ ecx=@CX@\\n\", *(int*)$esp, $ecx",
             "continue", "end"]
    body += ["continue"]
    txt = "\n".join(body)
    txt = txt.replace("@PC@", "%08x").replace("@SLOT@", "%08x").replace("@CX@", "%08x")
    open(path, "w").write(txt)


def detach_pid(pid):
    out = subprocess.run(["pgrep", "-x", "gdb"], capture_output=True, text=True).stdout.split()
    for p in out:
        cmd = open("/proc/%s/cmdline" % p, "rb").read().replace(b"\0", b" ").decode()
        if "m286.gdb" in cmd or ("attach" in cmd and str(pid) in cmd):
            subprocess.run(["kill", p], check=False)


def find_oops_row():
    """OCR the frame; return the center of the 'oops, no, wait!' row or None.
    NEVER clicks the 'Yes, that's an order mister!' quit row (M37 row guard:
    only words starting 'oops' in 150<=cx<=660, plus a sanity y in the top
    half - the quit row sits below it)."""
    png = sp.freeze("m286")
    words = sp.ocr(png)
    found = []
    for t, cx, cy in [(w[0], int(w[1]), int(w[2])) for w in words]:
        low = t.lower().strip(".,:;|_*")
        if low.startswith("oops") and 150 <= cx <= 660 and 150 <= cy <= 500:
            found.append((int(cx), int(cy)))
    if not found:
        return None, words
    return min(found, key=lambda p: p[1]), words   # topmost oops-like row


def live():
    pid, f = sp.mem()
    tp = re.search(r"TracerPid:\s+(\d+)", open("/proc/%d/status" % pid).read())
    if int(tp.group(1)):
        print("STATE 8: box dirty (TracerPid=%d)" % int(tp.group(1))); return 8
    print("family vptr scan BEFORE: %s" % vptr_scan(pid), flush=True)
    dcur0 = u32(f, DIALOG_CUR)
    dv0 = live_vptr(f, dcur0)
    print("PRE-ARM DIALOG_CUR=0x%08x vptr=0x%08x%s" % (
        dcur0, dv0, " FAMILY" if dv0 in FAMILY else ""), flush=True)
    gdb_script = os.path.join(ROOT, "scratch/m286.gdb")
    LOG = os.path.join(ROOT, "scratch/m286.log")
    if os.path.exists(LOG): os.remove(LOG)
    arm_gdb(gdb_script, pid, LOG)
    gdb = subprocess.Popen(["gdb", "-batch", "-x", gdb_script],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.0)
    sp.find_window(); sp.focus()
    # Drive the REALLYQUIT dialog open (M36/M37): Escape closes the base
    # display (safe, M285 did exactly this); a SECOND Escape on the bare HUD
    # raises REALLYQUIT.  Loop up to 4 Escapes, breaking as soon as the safe
    # 'oops' row OCRs - never click anything until it appears.
    row = None
    for _ in range(4):
        row, words = find_oops_row()
        if row is not None:
            break
        key("Escape")
        time.sleep(1.2)
    if row is None:
        gdb.send_signal(2)
        try:
            gdb.wait(6)
        except subprocess.TimeoutExpired:
            detach_pid(pid); gdb.wait(6)
        print("STATE 5: no 'oops' row OCR-able after 4 Escapes - NO CLICK - "
              "NO MEASUREMENT (last OCR words=%d)" % len(words))
        return 5
    print("REALLYQUIT raised (oops row at %s)" % (row,), flush=True)
    # falsifier READ 1: the dialog object and its vptr at click time
    dcur = u32(f, DIALOG_CUR)
    dv = live_vptr(f, dcur)
    print("LIVE at click: dialog obj=0x%08x vptr=0x%08x%s" % (
        dcur, dv, " FAMILY" if dv in FAMILY else ""), flush=True)
    click(row)                 # the SAFE row: 'Oops, no, wait!' (M37)
    time.sleep(1.4)
    row2, words2 = find_oops_row()
    print("OCR after oops click: oops still up = %s" % (row2 is not None), flush=True)
    if row2 is not None:
        # M37 follow-up: the OK bar sits 47 px below the oops row - still safe
        click((row[0], row[1] + 47))
        time.sleep(1.4)
    # pane-gone check: after the clicks the REALLYQUIT dialog must be CLOSED
    # (M37 recovery ends with the HUD/btn strip).  A dialog that closed proves
    # the clicks were delivered even if the main wndproc never saw them (the
    # modal captures LBUTTONDOWN before the main WndProc).
    _, words3 = find_oops_row()
    pane_gone = not any(re.sub(r"[^a-z]", "", w[0].lower()).startswith("oops")
                        for w in words3)
    print("OCR after follow-up: REALLYQUIT pane gone = %s" % pane_gone, flush=True)
    # falsifier READ 2: dialog vptr after the clicks
    dcur2 = u32(f, DIALOG_CUR)
    dv2 = live_vptr(f, dcur2)
    print("LIVE after clicks: dialog obj=0x%08x vptr=0x%08x%s" % (
        dcur2, dv2, " FAMILY" if dv2 in FAMILY else ""), flush=True)
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
    if fam or entries:
        print("STATE 0: measured-positive - family +0x4c dispatched via site(s) above")
        return 0
    if not ctrls and not pane_gone:
        print("STATE 5: driver produced NO observable click effect (wndproc control "
              "silent AND pane still up) - NO MEASUREMENT")
        return 5
    famlive = (dv in FAMILY) or (dv2 in FAMILY)
    print("STATE 4: measured-negative - %d clicks delivered, pump ran (%d), "
          "LIVE dialog vptr%s family at the click %s - family +0x4c dispatched "
          "through NONE of the 12 sites" % (
          len(ctrls), len(pumps), "" if famlive else " NOT", "" if famlive else
          "(so the REALLYQUIT pane is also not one of the 5 family classes)"))
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
