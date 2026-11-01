#!/usr/bin/env python3
"""M241: M181's falsifier — does a SAVE store to ds:0x99aa38 (the save band's staging dword)?

M181 is a LEAD, not a finding: 2 ms samples of ds:0x99aa38 across three round boundaries stayed 0,
but the aggregate counters in the same window were 0 too, so there was NO POSITIVE CONTROL. A value
sampler also cannot tell "no writer" from "a writer storing the SAME value" (a hw watchpoint, like a
sampler, only reports a CHANGE). This run supplies both missing halves: a trigger whose outcome is
verifiable OUTSIDE the game (a new .SAV file on disk, stat'd by the host) and a tracer whose silent
breakpoints COUNT stores whatever the value does.

  sudo -n python3 scripts/m241_m181_control.py [--pid N]

Phase A (no tracer): 2 ms sampler over the 16 staging dwords + controls, ONE UI save.
Phase B (tracer):    41 silent bps — the 33 census stores of 0x99aa38 (M179), the 4 `call
                     0x41a8f0` sites (s189 lead), the packer entry 0x41a8f0, its post-pack read
                     0x41abd4, the GOVERNORCONTROL writer entry 0x512020 and its tagged-writer
                     call 0x512069 — ONE UI save.
Gates G1-G5; prints `PASS M241: 5/5 gates ...` or `FAIL M241: n/5` with the numbers next to them.
"""
import glob
import os
import re
import signal
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import smac_play as P  # noqa: E402  (click/freeze/ocr; DISPLAY=:99)

FLAG = 0x99AA38
STAGE = [0x99AA1C + 4 * i for i in range(16)]          # M182: record base 0x99aa1c, 14+ dwords
CTRL = {"round": 0x985AFC, "year": 0x985B00, "cp": 0x985DCC, "curfac": 0x91B5B4,
        "gate91c62c": 0x91C62C, "selobj": 0x8F0D60}
SAVE_DIR = os.path.join(ROOT, "programs", "saves", "auto")
MENU, GAME_ROW, SAVE_ROW = (61, 369), (30, 186), (200, 331)
NAME_BOX, SAVE_OK = (406, 304), (330, 327)             # SAVE browser (wine-operations.md M54b)
SAVE_NAME = r"Z:\home\n100\reverse\smac\programs\saves\auto\m241_probe.SAV"

# M179 census: the 33 stores to ds:0x99aa38, by owning function (evidence/m178_m180_scratchband.txt:64)
STORES = {}
for _fn, _addrs in {
    "FUN_0041a8f0": [0x41A9B7, 0x41A9D2, 0x41A9E8, 0x41A9FB, 0x41AA0E, 0x41AA21, 0x41AA37, 0x41AA4A,
                     0x41AA5D, 0x41AA72, 0x41AA87, 0x41AA9C, 0x41AAB4, 0x41AACC, 0x41AAE4, 0x41AAFD,
                     0x41AB14, 0x41AB2E, 0x41AB4A, 0x41AB6D],
    "FUN_004d9ae0": [0x4D9B28], "FUN_004dc100": [0x4DC274], "FUN_004dc390": [0x4DC509],
    "FUN_004dc5f0": [0x4DC700], "FUN_004dc8d0": [0x4DC9F7], "FUN_004dcc10": [0x4DCD1C],
    "FUN_004dde00": [0x4DDFC1], "FUN_00510230": [0x510290], "FUN_00512b40": [0x5136DB],
    "FUN_00516b80": [0x5170B5], "FUN_00518c50": [0x518C7F], "FUN_0057c550": [0x57CAB7],
    "FUN_00626b46": [0x626CF6],
}.items():
    for _a in _addrs:
        STORES[_a] = _fn
CALLSITES = {0x41E3BD: "FUN_0041e160", 0x49B306: "FUN_0049af50",
             0x4A9E0E: "FUN_004a99e0", 0x5120D0: "FUN_00512020"}
PACKER, POSTPACK, GOVW, GOVW_CALL = 0x41A8F0, 0x41ABD4, 0x512020, 0x512069
NBP = len(STORES) + len(CALLSITES) + 4                # 33 + 4 + entry/post/writer/writer-call = 41


def u32(fd, a):
    try:
        return int.from_bytes(os.pread(fd, 4, a), "little")
    except OSError:
        return -1


def sample_row(fd):
    """24 values: 16 staging dwords, 6 controls, then two DERIVED reads (selobj+0x38, published)."""
    vals = [u32(fd, a) for a in STAGE] + [u32(fd, CTRL[k]) for k in sorted(CTRL)]
    sel = u32(fd, CTRL["selobj"])
    fac = u32(fd, CTRL["curfac"])
    vals.append(u32(fd, sel + 0x38) if 0x10000 < sel < 0x0FFFFFFF else -2)
    vals.append(u32(fd, 0x94D600 + fac * 8380) if 0 <= fac < 8 else -2)
    return vals


FIELD_NAMES = [f"+{4*i:02x}" for i in range(16)] + sorted(CTRL) + ["selflag", "pub94d600"]


def run_sampler(fd, stop, rows, period=0.002):
    last, n = None, 0
    t0 = time.time()
    while not stop.is_set():
        v = tuple(sample_row(fd))
        n += 1
        if v != last:
            rows.append((time.time() - t0, v))
            last = v
        time.sleep(period)
    return n


def gdb_script():
    """41 silent bps; every printf takes exactly as many args as it has specs (trap: a mismatch
    aborts the sourced script and DETACHES at the first hit)."""
    L = ["set pagination off", "set confirm off",
         "handle SIGUSR1 nostop noprint pass", "handle SIGUSR2 nostop noprint pass",
         "handle SIGPIPE nostop noprint pass"]
    S = "(*(int*)0x99aa38)"

    def bp(addr, fmt, args):
        L.extend(["break *0x%x" % addr, "commands", "silent",
                  'printf "%s\\n", %s' % (fmt, args), "continue", "end"])

    bp(PACKER, "ENT 41a8f0 ret=%d stage=%d", "(*(int*)$esp), " + S)
    for a in sorted(STORES):
        bp(a, "W %06x pre=%%d" % a, S)
    for a in sorted(CALLSITES):
        bp(a, "CALL %06x stage=%%d" % a, S)
    bp(POSTPACK, "POST 41abd4 stage=%d src=%d", S + ", (*(int*)(*(int*)0x8f0d60+0x38))")
    bp(GOVW, "GOVW arg1=%d f23be8=%d gate=%d fac=%d stage=%d",
       "$ecx, (*(int*)($ecx+0x23be8)), (*(int*)0x91c62c), (*(int*)0x91b5b4), " + S)
    bp(GOVW_CALL, "GOVWRITE stage=%d", S)
    L.append('printf "ARMED n=%d\\n"' % NBP)
    L.append("continue")
    return "\n".join(L) + "\n"


def frame_diff(a, b):
    from PIL import Image, ImageChops
    return ImageChops.difference(Image.open(a), Image.open(b)).getbbox() is not None


def open_browser(tag):
    """Get to the SAVE browser with the path typed, but the write NOT yet done.

    Ctrl+S is the GAME submenu's own hotkey for Save Game... (read off the submenu frame
    m241_a_sub.png), so it skips the dropdown. Verified by FRAME DIFF, not OCR: tesseract renders
    the submenu's small type as garbage ('Load Game...' -> 'lad'), so an OCR 'save' check aborts a
    route that is in fact open — that is what killed invocation 1."""
    P.WIN = P.find_window()
    if not P.WIN:
        return False, "no game window"
    P.focus()
    a = P.freeze(tag + "_f0")
    P.sh("xdotool key ctrl+s")
    time.sleep(2.2)
    if not frame_diff(a, P.freeze(tag + "_f1")):
        P.click(MENU)
        time.sleep(2.0)
        if not frame_diff(a, P.freeze(tag + "_f2")):
            return False, "neither Ctrl+S nor a MENU click changed the frame"
        P.click(GAME_ROW)
        time.sleep(1.5)
        if not frame_diff(a, P.freeze(tag + "_f3")):
            return False, "GAME row click did not change the frame"
        P.click(SAVE_ROW)
        time.sleep(2.2)
        if not frame_diff(a, P.freeze(tag + "_f4")):
            return False, "Save Game row click did not change the frame"
    P.click(NAME_BOX)
    time.sleep(0.8)
    P.sh("xdotool key End")
    P.sh("xdotool key --repeat 200 BackSpace")
    P.sh('xdotool type --delay 25 "%s"' % SAVE_NAME)
    time.sleep(0.8)
    return True, "browser open, name typed"


def press_ok_and_wait(tag, before, t0):
    """The ONE trigger action: click OK (330,327). The save landing on disk IS the trigger proof."""
    P.click(SAVE_OK)
    nf = []
    for _ in range(25):
        time.sleep(1.0)
        nf = new_saves(before)
        if nf:
            break
        b = body(P.freeze(tag + "_wait"))
        if "exist" in b or "overwrite" in b or "really" in b:
            P.key("Return")
    return nf, ("ok" if nf else "no .SAV appeared within 25 s of the OK click")


def close_leftovers(tag):
    """Escape ONCE closes a still-open browser; a bare-map Escape raises the quit prompt, so look
    for it and Escape again (m54a_load: 'really ... quit' -> Escape = 'Oops, no, wait!', never OK)."""
    P.key("Escape")
    time.sleep(1.2)
    b = body(P.freeze(tag + "_close"))
    if "really" in b and "quit" in b:
        P.key("Escape")
        time.sleep(1.2)
        b = body(P.freeze(tag + "_close2"))
    return b


def all_savs():
    return glob.glob(os.path.join(ROOT, "programs", "saves", "**", "*.SAV"), recursive=True)


def new_saves(before):
    now = set(glob.glob(os.path.join(ROOT, "programs", "saves", "**", "*.SAV"), recursive=True))
    return sorted(now - before)


def body(png):
    return " ".join(w[0] for w in P.ocr(png)).lower()


def timelines(rows):
    """Per-field change sequence [(t, value)] in the sampler's window."""
    out = []
    for i in range(len(FIELD_NAMES)):
        seq = []
        for t, v in rows:
            if not seq or seq[-1][1] != v[i]:
                seq.append((t, v[i]))
        out.append(seq)
    return out


def show(seq, n=10):
    return " -> ".join("%08x@%.2f" % (v, t) for t, v in seq[:n]) + (" ..." if len(seq) > n else "")


def main():
    pid = (int(sys.argv[sys.argv.index("--pid") + 1]) if "--pid" in sys.argv
           else int(subprocess.check_output(["pgrep", "-x", "terran.exe"]).split()[0]))
    fd = os.open("/proc/%d/mem" % pid, os.O_RDONLY)
    base = sample_row(fd)
    print("pid=%d  baseline: %s" % (pid, " ".join("%s=%08x" % kv for kv in zip(FIELD_NAMES, base))))
    print("gate ds:0x91c62c=%d (FUN_00512020 skips the GOVERNORCONTROL record unless it is 0)"
          % base[FIELD_NAMES.index("gate91c62c")], flush=True)

    beforeA, tA = set(all_savs()), time.time()
    okA, msgA = open_browser("m241_a")
    if not okA:
        raise SystemExit("BLOCKER phase A: " + msgA)
    stop, rows, cnt = threading.Event(), [], [0]
    threading.Thread(target=lambda: cnt.__setitem__(0, run_sampler(fd, stop, rows)), daemon=True).start()
    time.sleep(0.5)
    nfA, msgA2 = press_ok_and_wait("m241_a", beforeA, tA)
    time.sleep(1.0)
    stop.set()
    time.sleep(0.3)
    close_leftovers("m241_a")
    tl = timelines(rows)
    churn = [FIELD_NAMES[i] for i in range(16) if i != 7 and len(tl[i]) >= 2]
    print("PHASE A (no tracer): %s / %s  samples=%d change-rows=%d"
          % (msgA, msgA2, cnt[0], len(rows)), flush=True)
    for f in nfA:
        print("  save file %s  %d B  mtime +%.1f s" % (f, os.path.getsize(f), os.path.getmtime(f) - tA))
    print("  staging fields that CHANGED value (all but +1c): %s" % (churn or "NONE"))
    print("  +1c (ds:0x99aa38) timeline: %s" % show(tl[7], 8), flush=True)

    okB, msgB = open_browser("m241_b")          # navigate BEFORE arming: only the write is traced
    if not okB:
        raise SystemExit("BLOCKER phase B: " + msgB)
    beforeB, tB = set(all_savs()), time.time()
    gpath = os.path.join(ROOT, "scratch", "m241_b.gdb")
    lpath = os.path.join(ROOT, "scratch", "m241_b.gdblog")
    open(gpath, "w").write(gdb_script())
    if os.path.exists(lpath):
        os.remove(lpath)
    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=log, stderr=subprocess.STDOUT)
    armed = False
    for _ in range(80):
        time.sleep(0.5)
        if "ARMED" in open(lpath, errors="replace").read():
            armed = True
            break
    if not armed:
        os.kill(g.pid, signal.SIGINT)
        subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
        raise SystemExit("BLOCKER: gdb did not arm 41 bps:\n" + open(lpath, errors="replace").read()[-900:])
    stop2, rows2, cnt2 = threading.Event(), [], [0]
    threading.Thread(target=lambda: cnt2.__setitem__(0, run_sampler(fd, stop2, rows2)), daemon=True).start()
    time.sleep(0.5)
    nfB, msgB2 = press_ok_and_wait("m241_b", beforeB, tB)
    time.sleep(2.0)
    stop2.set()
    os.kill(g.pid, signal.SIGINT)
    for _ in range(60):
        if not os.path.exists("/proc/%d" % g.pid):
            break
        time.sleep(0.5)
    subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
    time.sleep(1.5)
    log.close()
    txt = open(lpath, errors="replace").read()
    hits = [l.split() for l in txt.splitlines()
            if l.split() and l.split()[0] in ("ENT", "W", "CALL", "POST", "GOVW", "GOVWRITE")]
    warns = [l for l in txt.splitlines() if re.search(r"warning|error:|Cannot access|cannot insert", l, re.I)]
    tracer = next(l.split()[1] for l in open("/proc/%d/status" % pid) if l.startswith("TracerPid"))
    tl2 = timelines(rows2)
    close_leftovers("m241_b")                   # AFTER the detach: one Escape, quit-prompt-guarded
    print("PHASE B (tracer): %s / %s  gdb hits=%d  sampler samples=%d  TracerPid after detach=%s"
          % (msgB, msgB2, len(hits), cnt2[0], tracer), flush=True)
    for f in nfB:
        print("  save file %s  %d B  mtime +%.1f s" % (f, os.path.getsize(f), os.path.getmtime(f) - tB))
    sh = {}
    for h in hits:
        if h[0] == "W":
            sh[int(h[1], 16)] = sh.get(int(h[1], 16), 0) + 1
    nstore = sum(sh.values())
    byfn = {}
    for a, c in sorted(sh.items()):
        byfn[STORES[a]] = byfn.get(STORES[a], 0) + c
    print("  store hits at ds:0x99aa38: %d at %d of %d census sites -> by function %s"
          % (nstore, len(sh), len(STORES), byfn or "{}"))
    for h in hits:
        if h[0] in ("ENT", "CALL", "POST", "GOVW", "GOVWRITE"):
            print("  %s %s" % (h[0], " ".join(h[1:])))
    print("  +1c timeline under the tracer: %s" % show(tl2[7], 8))
    G1 = all(nf and all(os.path.getsize(f) > 20000 and os.path.getmtime(f) > t - 1 for f in nf)
             for nf, t in ((nfA, tA), (nfB, tB)))
    G2 = len(churn) >= 2
    G3 = armed and not warns and tracer == "0" and os.path.exists("/proc/%d" % pid)
    G4 = len(hits) >= 1
    G5 = (nstore >= 1 and G1) or (nstore == 0 and G1 and G2 and G4)
    verdict = (("CONFIRMED: the traced save ran %d stores to ds:0x99aa38 at %d of %d census sites %s"
                % (nstore, len(sh), len(STORES), byfn)) if (nstore and G1) else
               ("REFUTED for this trigger: 0 stores at the 33 sites during a traced save that DID "
                "write records (G1/G2/G4 passed) — no writer in this site set fires on a save"
                if G5 else
                "UNDECIDED: the traced window held no COMPLETED save (G1) — the trigger never "
                "fired, so neither side of M181 is settled"))
    print("VERDICT: " + verdict)
    names = ["G1 trigger: a new .SAV > 20 KB appeared in BOTH save windows",
             "G2 sampler control: >=2 non-+1c staging fields changed value in the save window",
             "G3 instrument: 41 bps armed, no gdb warnings, TracerPid back to 0, inferior alive",
             "G4 band control: the traced save executed >=1 armed site (band code ran under tracer)",
             "G5 falsifier decides: stores fired, OR zero stores with G1+G2+G4 controls passing"]
    npass = 0
    for nm, ok in zip(names, (G1, G2, G3, G4, G5)):
        print("%s %s" % ("PASS" if ok else "FAIL", nm))
        npass += ok
    print("%s M241: %d/5 gates" % ("PASS" if npass == 5 else "FAIL", npass))
    return 0 if npass == 5 else 1


sys.exit(main())
