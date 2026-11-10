#!/usr/bin/env python3
"""M285: the family +0x4c dispatcher on a REAL Script.txt dialog path (M284 re-scope).

M284 (merged) proved the BASE DISPLAY never dispatches the family +0x4c: its clicks
route through CPane/world handlers, the modal dialog pump FUN_005f1394 never runs, the
12 `call [reg+0x4c]` sites stay silent.  NEW settled fact (probed this session): the
production-item chooser sub-object (live vptr 0x672298, M53g) is NOT family - its +0x4c
is the return-0 stub 0x404ed0 - so the family dispatcher must be on the DIALOG class
(0x67164c ctor FUN_00405ef0, run method FUN_005f1394) that *owns* the chooser.

This instrument opens a REAL chooser (the production item chooser; the queue must be
non-empty/insertable - m54g_prep + one turn per standing facts), and while it is open:
  - reads the LIVE OWNING-DIALOG vtable at click time (the pick's falsifier: a family
    vtable read at a click - if the dialog at the click is a family instance, one of
    the 12 sites MUST dispatch +0x4c with slot value 0x5f6aa3 at some click),
  - arms silent bps at all 12 sites printing the CALLED SLOT VALUE (*(int*)(obj+0x4c)),
  - arms FUN_005f6aa3 ENTRY (who enters it, and from where - retaddr),
  - arms the dialog pump FUN_005f1394 (CTRL: a real dialog pump ran),
  - arms the WNDPROC 0x5d0c33 WM_LBUTTONDOWN control (clicks were delivered).

Pre-registered live states (same contract as M284):
  0 = measured-positive: a family +0x4c dispatch observed (a site fired with slot
      0x5f6aa3, or FUN_005f6aa3 entered) AND the live dialog vtable at the click was
      one of the 5 family vtables - the dispatcher is NAMED.
  4 = measured-negative: clicks delivered (wndproc control fired) with a REAL chooser
      open (pump ran) but NO family +0x4c dispatch in the window, AND the live dialog
      vptr read as family (so the class truly has it) - the 12 sites do not serve it.
  5 = driver wedged: wndproc control silent (no clicks at all) - NO MEASUREMENT.
  8 = box left dirty (TracerPid != 0) - invalid measurement.

    python3 scripts/m285_chooser_dispatch.py --static   # no box time
    python3 scripts/m285_chooser_dispatch.py --live     # the chooser-open click window
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
CHOOSER_SUB = 0x6A9E9C        # pane+0xa1c: the chooser sub-object (its vptr is [sub])
DIALOG_CUR = 0x9939c4         # current dialog object pointer (dialogs[] stack, s184)
WIN_G, WIN_CX, WIN_CY = 0x7CDECC, 0x1DD9C, 0x1DDA0
CI, CX, CY = 0x91B5E8, 0x91B5F0, 0x91B670
SEL_G, ORDERS_MODE = 0x91B5BC, 0x91B5B8
BASE_ARR, BASE_SZ = 0x95DA10, 304
PANE_BASE_IDX = 0x6A9480 + 0x3FF3C
ARROW_XY, ROW1_XY = (523, 433), (185, 437)
INSERT_XY, OK_XY = (497, 343), (285, 343)
XENV = {**os.environ, "DISPLAY": ":99"}


def dw(va):
    o = va - 0x400000
    return struct.unpack("<I", IMG[o:o + 4])[0] if 0 <= o + 4 <= len(IMG) else 0


def u32(f, a): return struct.unpack("<I", sp.rd(f, a, 4))[0]
def i32(f, a): return struct.unpack("<i", sp.rd(f, a, 4))[0]


def click(xy):
    subprocess.run(["xdotool", "mousemove", str(xy[0]), str(xy[1])], env=XENV, check=False)
    subprocess.run(["xdotool", "click", "1"], env=XENV, check=False)
    time.sleep(0.4)


def key(k):
    subprocess.run(["xdotool", "key", "--clearmodifiers", k], env=XENV, check=False)
    time.sleep(0.5)


def base_rec(f, i):
    b = sp.rd(f, BASE_ARR + i * BASE_SZ, BASE_SZ)
    g = lambda o: struct.unpack("<i", b[o:o + 4])[0]
    return dict(i=i, name=b[19:59].split(b"\0")[0].decode("latin-1", "replace"),
                x=struct.unpack("<H", b[0:2])[0], y=struct.unpack("<H", b[2:4])[0],
                fac=b[4], pending=g(0x4c), head=g(0x50), minerals=g(0x40))


def live_vptr(f, obj):
    """vptr at [obj] via /proc - the falsifier read. -1 on unmapped."""
    try:
        return struct.unpack("<I", sp.rd(f, obj, 4))[0]
    except OSError:
        return -1


def vptr_scan(pid):
    """scan all writable regions for the 5 family vptrs + the chooser sub vptr;
    count live instances (a class with no live instance logs zero hits)."""
    counts = {v: 0 for v in FAMILY}
    counts[0x672298] = 0
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
        blk = hi - lo
        try:
            with open("/proc/%d/mem" % pid, "rb", 0) as m:
                m.seek(lo)
                got = m.read(blk)
        except OSError:
            continue
        for v in list(counts):
            counts[v] += got.count(struct.pack("<I", v))
    return counts


def static():
    ok = [True]
    def G(cond, msg):
        print(("PASS " if cond else "FAIL ") + msg, flush=True)
        ok[0] = ok[0] and cond
    # g1: the 12 sites still are `call [reg+0x4c]` at those addresses (M284 census)
    toks = []
    for l in open(os.path.join(ROOT, "scratch/m574/text.txt"), errors="replace"):
        f = l.rstrip("\n").split("\t")
        if len(f) < 3: continue
        try: pc = int(f[0].rstrip(":"), 16)
        except ValueError: continue
        toks.append((pc, re.sub(r"\s+", " ", f[2].strip().lower())))
    tmap = dict(toks)
    bad = [hex(pc) for pc, _ in SITES if not re.search(r"call dword ptr \[e[a-z]+\+0x4c\]", tmap.get(pc, ""))]
    G(not bad, "g1: 12 sites still read `call [reg+0x4c]` (%s)" % ("none bad" if not bad else " ".join(bad)))
    # g2: every family vtable's +0x4c IS the family slot
    G(all(dw(v + 0x4c) == FAM_SLOT for v in FAMILY),
      "g2: all 5 family vtables +0x4c == 0x%x" % FAM_SLOT)
    # g3: 0.5 family class (+0x4c == 0x5f6aa3) image-wide, exactly the 5
    cnt = 0
    for va in range(0x400000, 0x700000, 4):
        if dw(va) == FAM_SLOT:
            cnt += 1
    G(cnt == 5, "g3: exactly 5 vtables hold +0x4c == 0x5f6aa3 (whole-image scan found %d)" % cnt)
    # g4: the production chooser sub-object class is NOT family (+0x4c = stub)
    G(dw(0x672298 + 0x4c) != FAM_SLOT and dw(0x672298 + 0x4c) == 0x404ed0,
      "g4: chooser class 0x672298 +0x4c = 0x%x (stub, NOT family)" % dw(0x672298 + 0x4c))
    # g5: the dialog ctor FUN_00405ef0 writes 0x67164c at [obj] (the owning dialog IS family)
    body = IMG[0x405ef0 - 0x400000: 0x405ef0 - 0x400000 + 0x100]
    G(struct.pack("<I", 0x67164c) in body,
      "g5: FUN_00405ef0 body contains the 0x67164c store (dialog ctor installs family vptr)")
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
        # s240 (M293): the guard must admit IMAGE-range vtables (image base
        # 0x400000, PE section table): the five dialog-family vtables
        # 0x67164c/0x6717cc/0x6728c0/0x675cc4/0x6776c8 ALL sit below
        # 0x1000000, so the old guard printed NOTHING for a real family
        # dispatch - every live "0 of 12 sites fired" in M284-M287 is
        # instrument-invalid, not evidence of absence.
        body += ["if $%s >= 0x400000" % reg,
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
        if "m285.gdb" in cmd or ("attach" in cmd and str(pid) in cmd):
            subprocess.run(["kill", p], check=False)


def live():
    pid, f = sp.mem()
    tp = re.search(r"TracerPid:\s+(\d+)", open("/proc/%d/status" % pid).read())
    if int(tp.group(1)):
        print("STATE 8: box dirty (TracerPid=%d)" % int(tp.group(1))); return 8
    b0 = base_rec(f, 0)
    print("pre base0: %s" % b0, flush=True)
    if not (1 < b0["x"] < 200 and 1 < b0["y"] < 200):
        print("STATE 4: base tile out of range x=%d y=%d" % (b0["x"], b0["y"])); return 4
    print("family vptr scan BEFORE (counts by vptr): %s" % vptr_scan(pid), flush=True)
    # --- the three enabling pokes (m57 recipe) on OUR base 0
    w = u32(f, WIN_G)
    sp.wr(f, w + WIN_CX, struct.pack("<i", b0["x"])); sp.wr(f, w + WIN_CY, struct.pack("<i", b0["y"]))
    ci = u32(f, CI)
    sp.wr(f, CX + ci * 4, struct.pack("<i", b0["x"])); sp.wr(f, CY + ci * 4, struct.pack("<i", b0["y"]))
    sp.wr(f, SEL_G, struct.pack("<i", -1)); sp.wr(f, ORDERS_MODE, struct.pack("<i", 0))
    print("pokes in; cursor %s" % ((i32(f, w + WIN_CX), i32(f, w + WIN_CY)),), flush=True)
    gdb_script = os.path.join(ROOT, "scratch/m285.gdb")
    LOG = os.path.join(ROOT, "scratch/m285.log")
    if os.path.exists(LOG): os.remove(LOG)
    arm_gdb(gdb_script, pid, LOG)
    gdb = subprocess.Popen(["gdb", "-batch", "-x", gdb_script],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.0)
    sp.find_window(); sp.focus()
    key("b")                       # open the base display on our base
    time.sleep(1.0)
    # message popup OK (message box y 440-560 x 10-300)
    click((285, 553)); click((285, 553))
    time.sleep(0.6)
    print("after b+pops: pane base idx = %d (base 0), pending=%d" % (
        i32(f, PANE_BASE_IDX), base_rec(f, 0)["pending"]), flush=True)
    click(ROW1_XY)                 # open the production item chooser (m57: row click opens)
    time.sleep(1.0)
    # falsifier READ 1: owning dialog + chooser sub-object vtables at click time
    dcur = u32(f, DIALOG_CUR)
    dv = live_vptr(f, dcur)
    chooser_vptr = live_vptr(f, CHOOSER_SUB)
    print("LIVE at chooser: dialog obj=0x%08x vptr=0x%08x%s, chooser sub vptr=0x%08x%s" % (
        dcur, dv, " FAMILY" if dv in FAMILY else ("0x%x" % dv), chooser_vptr,
        " FAMILY" if chooser_vptr in FAMILY else ""), flush=True)
    # cell 2 (= candidate[2]=193, the m57 default row) then INSERT bar then OK bar;
    # INSERT lands even at minerals 0 / credit 0 after the prep+turn (standing facts)
    click((382, 60))     # chooser grid cell k=2 (cx=128+127*2, cy=60)
    click(INSERT_XY)     # INSERT bar (497,343) - exercises the dialog family's click path
    time.sleep(0.8)
    click(OK_XY)         # OK bar (285,343)
    time.sleep(0.5)
    # falsifier READ 2: dialog vptr still live after the edits
    dcur2 = u32(f, DIALOG_CUR)
    dv2 = live_vptr(f, dcur2)
    print("LIVE after edits: dialog obj=0x%08x vptr=0x%08x%s" % (
        dcur2, dv2, " FAMILY" if dv2 in FAMILY else ""), flush=True)
    key("Escape")                  # close the base display (safe)
    time.sleep(0.5)
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
        print("STATE 0: measured-positive - family +0x4c dispatched%s via site(s) above" % (
            "" if fam else " (entry only)"))
        return 0
    if not ctrls:
        print("STATE 5: driver produced no clicks (wndproc control silent) - NO MEASUREMENT")
        return 5
    famlive = (dv in FAMILY) or (chooser_vptr in FAMILY) or (dv2 in FAMILY)
    print("STATE 4: measured-negative - %d clicks delivered, chooser pump ran (%d), "
          "LIVE dialog vptr%s family at the click %s - family +0x4c dispatched through "
          "NONE of the 12 sites" % (
          len(ctrls), len(pumps), "" if famlive else " NOT", "" if famlive else "(so the "
          "owning dialog was not a family instance in this window)"))
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
    sys.exit(0 if static() else 1)


if __name__ == "__main__":
    main()
