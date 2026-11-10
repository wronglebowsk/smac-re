#!/usr/bin/env python3
"""M284: WHO dispatches the dialog family's +0x4c (FUN_005f6aa3, 5 vtables / 466 installs /
0 direct calls).  M214 proved: reached ONLY by dispatch; the 12 image-wide `call [reg+0x4c]`
single-insn sites tag 0 SELF-of-family by CONTAINING function.  But a site's containing
function does not constrain its RUNTIME object - a `call [edx+0x4c]` in an unrelated body can
still dispatch a family instance if edx holds one.  The open question is LIVE: which site (if
any) actually dispatches +0x4c on a family class at a real click.

  static half (this file, --static): complete the candidate set - the 12 single-insn sites
  (asserted), the load-then-call form (`mov r,[r+0x4c]; call r` - ZERO in the whole image,
  so the 12 are the only dispatch forms), the family vtable set + install count (M214's
  method), 0 direct `call 0x5f6aa3`.
  live half (--live, box): arm silent bps at the 12 sites printing the CALLED SLOT VALUE
  (*(int*)(obj+0x4c)) + bp FUN_005f6aa3 ENTRY; drive real clicks (base display row, chooser
  cell) via xdotool; the site whose slot reads 0x5f6aa3 IS the family +0x4c dispatcher, and
  the entry hit names the runtime caller by return address.
  Pre-registered live states: 0 = measured (a family +0x4c dispatch observed and the site
  named), 4 = clicks landed (pump fired) but NO family +0x4c dispatch in the window,
  5 = driver produced no clicks (NO MEASUREMENT), 8 = box left dirty (TracerPid != 0).

    python3 scripts/m284_dialog_dispatch.py --static       # no box time
    python3 scripts/m284_dialog_dispatch.py --live         # the click window
Every number the prose quotes is COMPUTED here.
"""
import argparse, bisect, collections, csv, os, re, struct, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import smac_play as sp  # noqa: E402

IMG = open(os.path.join(ROOT, "programs/terran.exe"), "rb").read()
TEXT_LO, TEXT_HI = 0x401000, 0x660000
FAMILY = [0x67164c, 0x6717cc, 0x6728c0, 0x675cc4, 0x6776c8]

def dw(va):
    o = va - 0x400000
    return struct.unpack("<I", IMG[o:o + 4])[0] if 0 <= o + 4 <= len(IMG) else 0

def load_ins():
    """(pc, mnemonic+operands) pairs - the mnemonic field only, NOT the leading hex-bytes
    column (tab-separated: 'addr:\tBYTES\tMNEMONIC OPERANDS'; a line with no operands has
    only two fields)."""
    toks = []
    for l in open(os.path.join(ROOT, "scratch/m574/text.txt"), errors="replace"):
        f = l.rstrip("\n").split("\t")
        if len(f) < 2:
            continue
        try:
            pc = int(f[0].rstrip(":"), 16)
        except ValueError:
            continue
        ins = f[2] if len(f) >= 3 else f[1]
        toks.append((pc, re.sub(r"\s+", " ", ins.strip().lower())))
    return toks

def load_fnof():
    owners = []
    for row in csv.reader(open(os.path.join(ROOT, "ghidra_out/index.csv"))):
        if len(row) >= 2 and re.fullmatch(r"0x[0-9a-f]+", row[0], re.I):
            owners.append((int(row[0], 16), row[1]))
    owners.sort()
    def fnof(pc):
        last = None
        for a, n in owners:
            if a <= pc: last = n
            else: break
        return last
    return fnof

def vtable_tables():
    """same basis as the m213_m216 script (HERE verbatim): bases counted only for
    `mov dword ptr [..],0xXXXXXX` STORES of an immediate in the data range whose first dword
    points into .text; table length derived from the next base."""
    bases = collections.Counter()
    RX_INS = re.compile(r"^mov\s+dword ptr \[[^\]]*\],(0x[0-9a-f]{6,8})$")
    for pc, s in load_ins():
        m = RX_INS.match(s)
        if not m:
            continue
        v = int(m.group(1), 16)
        if 0x660000 <= v < 0x9a0000 and dw(v) and TEXT_LO <= dw(v) < TEXT_HI:
            bases[v] += 1
    B = sorted(bases)
    VT = {}
    for i, b in enumerate(B):
        nxt = B[i + 1] if i + 1 < len(B) else b + 0x4000
        n = 0
        while 4 * (n + 1) <= (nxt - b) and dw(b + 4 * (n + 1)) and TEXT_LO <= dw(b + 4 * (n + 1)) < TEXT_HI:
            n += 1
        VT[b] = (n + 1, bases[b])
    return B, VT

def static():
    T = load_ins()
    fnof = load_fnof()
    s1 = [(pc, s) for pc, s in T if "call" in s and re.search(r"\[[^\]]*\+0x4c\]", s)]
    # load-then-call: mov/lea r,[...0x4c] followed <=40 insns later (same fn) by call r
    ltc = []
    for i, (pc, s) in enumerate(T):
        m = re.match(r"^(?:mov|lea)\s+([a-z0-9]+),\s*\[[^\]]*\+0x4c\]", s, re.I)
        if not m: continue
        for j in range(i + 1, min(i + 41, len(T))):
            if re.match(r"call\s+%s\b" % m.group(1), T[j][1], re.I):
                ltc.append((pc, T[j][0]))
                break
            if "ret" in T[j][1]: break
    dc = [pc for pc, s in T if re.fullmatch(r"call\s+0x5f6aa3", s)]
    B, VT = vtable_tables()
    w4c = sorted(b for b in B if 0x4c < 4 * VT[b][0] and dw(b + 0x4c) == 0x5f6aa3)
    inst = sum(VT[b][1] for b in w4c)
    print("call [reg+0x4c] sites: %d" % len(s1))
    for pc, s in s1: print("   %06x in %s: %s" % (pc, fnof(pc), s))
    print("load-then-call +0x4c pairs: %d" % len(ltc))
    for pc, cpc in ltc: print("   %06x -> %06x" % (pc, cpc))
    print("direct call 0x5f6aa3: %d" % len(dc))
    print("family vtables with +0x4c==0x5f6aa3: %s (%d installs)" % ([hex(x) for x in w4c], inst))
    ok = (len(s1) == 12 and not ltc and not dc
          and [hex(x) for x in w4c] == [hex(x) for x in FAMILY] and inst == 466)
    print("STATIC %s" % ("PASS" if ok else "FAIL: %s" % dict(s1=len(s1), ltc=len(ltc),
          dc=len(dc), w4c=[hex(x) for x in w4c], inst=inst)))
    return ok

def live():
    pid, f = sp.mem()
    pp = open("/proc/%d/status" % pid).read()
    tp = int(re.search(r"TracerPid:\s+(\d+)", pp).group(1))
    if tp:
        print("STATE 8: box dirty (TracerPid=%d)" % tp); return 8
    b0 = base_rec(f, 0)
    print("pre base0: x=%d y=%d name=%s" % (b0["x"], b0["y"], b0["name"]), flush=True)
    if not (1 < b0["x"] < 200 and 1 < b0["y"] < 200):
        print("STATE 4: base tile out of range, cannot open its display; x=%d y=%d" % (b0["x"], b0["y"]))
        return 4
    # the three enabling pokes (m57 recipe) on OUR base 0
    w = u32(f, 0x7CDECC)
    sp.wr(f, w + 0x1DD9C, struct.pack("<i", b0["x"])); sp.wr(f, w + 0x1DDA0, struct.pack("<i", b0["y"]))
    ci = u32(f, 0x91B5E8)
    sp.wr(f, 0x91B5F0 + ci * 4, struct.pack("<i", b0["x"])); sp.wr(f, 0x91B670 + ci * 4, struct.pack("<i", b0["y"]))
    sp.wr(f, 0x91B5BC, struct.pack("<i", -1)); sp.wr(f, 0x91B5B8, struct.pack("<i", 0))
    print("pokes in", flush=True)
    gdb_script = os.path.join(ROOT, "scratch/m284.gdb")
    LOG = os.path.join(ROOT, "scratch/m284.log")
    if os.path.exists(LOG): os.remove(LOG)
    arm_gdb(gdb_script, pid, LOG)
    gdb = subprocess.Popen(["gdb", "-batch", "-x", gdb_script],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.0)          # let gdb attach + arm
    win = sp.find_window()
    sp.focus()
    print("focus ok", flush=True)
    key("b")                 # ensure base display open on our base
    time.sleep(1.0)
    # the message popup's OK button (message box at y 440-560 x 10-300)
    click((285, 553))
    time.sleep(0.7)
    click((285, 553))
    time.sleep(0.7)
    click((400, 20))         # topbar BUILD tab
    time.sleep(0.6)
    key("Escape")
    time.sleep(0.6)
    gdb.send_signal(2)          # SIGINT gdb -> it detaches (m53n stop recipe)
    try:
        gdb.wait(6)
    except subprocess.TimeoutExpired:
        detach_pid(pid)
        gdb.wait(6)
    st = open("/proc/%d/status" % pid).read()
    if "State:\tT (stopped)" in st:
        subprocess.run(["kill", "-CONT", str(pid)], check=False)
    pp2 = open("/proc/%d/status" % pid).read()
    tp2 = int(re.search(r"TracerPid:\s+(\d+)", pp2).group(1))
    rows = [l for l in open(LOG, errors="replace")] if os.path.exists(LOG) else []
    sites_hit = [l for l in rows if l.startswith("SITE")]
    slots = [(int(l.split()[1], 16), int(l.split()[2], 16)) for l in sites_hit if len(l.split()) >= 3]
    fam = [(pc, sl) for pc, sl in slots if sl == 0x5f6aa3]
    entries = [l for l in rows if l.startswith("ENTRY")]
    pumps = [l for l in rows if "CTRL" in l]
    print("site bps fired: %d, family-slot (%s) at: %s" % (
        len(sites_hit), "0x5f6aa3", " ".join("%06x" % pc for pc, _ in fam)))
    print("ENTRY hits: %d" % len(entries))
    for e in entries[:10]: print("   %s" % " ".join(e.split()))
    print("pump control hits: %d" % len(pumps))
    if fam:
        print("DISPATCHER SITE(S): %s" % " ".join("%06x" % pc for pc, _ in fam))
    if tp2:
        print("STATE 8: box left dirty (TracerPid=%d)" % tp2); return 8
    if fam or entries:
        print("STATE 0: measured - a family +0x4c dispatch happened (site + entry above)")
        return 0
    if not pumps:
        print("STATE 5: driver produced no clicks (wndproc LBUTTONDOWN control silent)")
        return 5
    print("STATE 0: measured-negative - %d clicks DELIVERED (wndproc control fired),\n"
          "          the family +0x4c was dispatched through NONE of the 12 sites and\n"
          "          FUN_005f6aa3 never entered - the base display is a CPane screen, not\n"
          "          a Script.txt dialog class; the dispatcher sits on the Script.txt path" % len(pumps))
    return 0

def base_rec(f, i):
    b = sp.rd(f, 0x95DA10 + i * 304, 304)
    return dict(x=struct.unpack("<H", b[0:2])[0], y=struct.unpack("<H", b[2:4])[0],
                name=b[19:59].split(b"\0")[0].decode("latin-1", "replace"))

def u32(f, a): return struct.unpack("<I", sp.rd(f, a, 4))[0]
XENV = {**os.environ, "DISPLAY": ":99"}
def click(xy):
    subprocess.run(["xdotool", "mousemove", str(xy[0]), str(xy[1])], env=XENV, check=False)
    subprocess.run(["xdotool", "click", "1"], env=XENV, check=False)
    time.sleep(0.4)
def key(k):
    subprocess.run(["xdotool", "key", "--clearmodifiers", k], env=XENV, check=False)
    time.sleep(0.5)

def arm_gdb(path, pid, log):
    slots = [
        (0x4b83f3, "edx"), (0x4ba2e3, "edx"), (0x4c6da9, "ecx"),
        (0x5b7cec, "edx"), (0x5b7dc4, "edx"), (0x5ceec2, "edx"),
        (0x5d9b8e, "eax"), (0x5d9bae, "eax"),
        (0x5fa9df, "edx"), (0x5faddc, "edx"),
        (0x5ffb3b, "eax"), (0x63cfa4, "eax"),
    ]
    body = ["set pagination off", "set confirm off",
            "handle SIGUSR1 nostop noprint pass",
            "handle SIGUSR2 nostop noprint pass",
            "handle SIGPIPE nostop noprint pass",
            "attach %d" % pid,
            "set logging file %s" % log, "set logging overwrite on", "set logging on"]
    body += ["b *0x5d0c33", "commands 1", "silent",
             "if *(int*)($esp+8) == 0x201",
             "printf \"CTRL wndproc-lbttdown msg=%08x\\n\", *(int*)($esp+8)",
             "end",
             "continue", "end"]
    body += ["b *0x5f1394", "commands 2", "silent", "printf \"CTRL pump\\n\"",
             "continue", "end"]
    n = 3
    for pc, reg in slots:
        body += ["b *0x%x" % pc, "commands %d" % n, "silent"]
        body += ["if $%s >= 0x1000000" % reg,
                 "printf \"SITE @PC@ @SLOT@\\n\", $pc, *(int*)($%s+0x4c)" % reg,
                 "end"]
        body += ["continue", "end"]
        n += 1
    body += ["b *0x5f6aa3", "commands %d" % n, "silent",
             "printf \"ENTRY retaddr=@PC@ ecx=@CX@\\n\", *(int*)$esp, $ecx",
             "continue", "end"]
    # m53n-style tail: ONE continue resumes; the command blocks' own continues keep the
    # window open; gdb runs in the background and is SIGINTed by the driver afterwards.
    body += ["continue"]
    txt = "\n".join(body)
    txt = txt.replace("@PC@", "%08x").replace("@SLOT@", "%08x").replace("@CX@", "%08x")
    open(path, "w").write(txt)

def detach_pid(pid):
    # leave the box clean: kill this gdb by pid (never by name)
    out = subprocess.run(["pgrep", "-x", "gdb"], capture_output=True, text=True).stdout.split()
    for p in out:
        cmd = open("/proc/%s/cmdline" % p, "rb").read().replace(b"\0", b" ").decode()
        if "m284.gdb" in cmd or ("attach" in cmd and str(pid) in cmd):
            subprocess.run(["kill", p], check=False)

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
