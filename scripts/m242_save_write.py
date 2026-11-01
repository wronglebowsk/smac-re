#!/usr/bin/env python3
"""M242: the save WRITE function is FUN_00597ce0(path) -> FUN_00596850(handle, 1).

M241 proved a save does NOT go through the 0x99aa1c band; this finds the writer and traces it.
Static (ghidra_out/shard_015.c + objdump windows, all VERIFIED before any box time):
  FUN_00597ce0 (363 B): fopen via FUN_0063c610(local_10c, ds:0x692fa0=mode) -> return 1 at 0x597dcf
    on open failure; write magic FUN_00570640(s_TERRAN ds:0x692fa4, handle) at 0x597ddb; write the
    4-byte version dword `local_c = 0x56` via FUN_0064c9a0 at 0x597df0; body FUN_00596850(handle, 1)
    at 0x597e04; write the timeGetTime() dword at 0x597e19; fclose FUN_0064c730 at 0x597e28; and on
    ANY failure code FUN_0064d710(local_10c) DELETES the file it just wrote.  Return 0 = ok.
  FUN_00596850(f, mode) (4,637 B) is ONE codec for BOTH directions: 0x59686b stores param_2 into
    DAT_00926a0c and every leg is `cmp eax,ebx / je` -> call 0x64cc00 (read) else 0x64c9a0 (write)
    (header leg: 0x596883 write / 0x59688a read, args dst=0x985ab8 sz=0x31c cnt=1).  30 write sites,
    28 read sites, plus 28+28 byte-swap siblings 0x596470/0x596540 gated on
    DAT_00926a14 = DAT_00985ae8 & 0x10000000 (set only when DAT_00920434 != 0).
  8 call sites of the writer: 0x521697 (turn-loop autosave, 10 insns after the "Writing save file"
    push at 0x521688), 0x52221e (end-turn loop), 0x598c73 (FUN_005985e0 = the UI Save browser, which
    shows SAVE FAILED through FUN_00626634 when the writer returns != 0), 0x59a121/0x59a166/0x59a1bc
    (FUN_0059a0c0), 0x59a372 (FUN_0059a2b0), 0x59bf46 (FUN_0059bec0).

  sudo -n python3 scripts/m242_save_write.py [--pid N]

Phase A (no tracer): ONE UI save, host-statted.  Phase B (tracer): the same save again with 130
silent bps on the writer's 7 own sites, its 8 callers, the codec entry, and all 114 wrapper/sibling
call sites inside FUN_00596850.  Detection is OUTSIDE the game: the .SAV the game wrote is statted
by MTIME (distinct name per phase - a same-name overwrite adds no filename) and its BYTES are
compared with the global the codec serialized.
Gates G1-G5; prints `PASS M242: 5/5 gates ...` or `FAIL M242: n/5` with the numbers next to them.
"""
import glob
import os
import re
import signal
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import smac_play as P  # noqa: E402  (click/freeze/ocr; DISPLAY=:99)

SAVE_DIR = os.path.join(ROOT, "programs", "saves", "auto")
MENU, GAME_ROW, SAVE_ROW = (61, 369), (30, 186), (200, 331)
NAME_BOX, SAVE_OK = (406, 304), (330, 327)             # SAVE browser (wine-operations.md M54b)
SAVE_NAME = r"Z:\home\n100\reverse\smac\programs\saves\auto\m242_probe.SAV"
HDR, HDRSZ, YEAR = 0x985AB8, 0x31C, 0x985B00          # 796-B block the codec serializes; year at +0x48
DIRFLAG, SWAPFLAG = 0x926A0C, 0x926A14                # DAT_00926a0c = mode, DAT_00926a14 = swap path
MAGIC, VER = b"TERRAN", 0x56                          # file[0:8] magic, file[8:12] version, block at 12

WRITER, CODEC = 0x597CE0, 0x596850
CALLERS = {0x521697: "FUN_00521070 autosave", 0x52221e: "FUN_00521ee0 end-turn",
           0x598c73: "FUN_005985e0 UI save", 0x59a121: "FUN_0059a0c0", 0x59a166: "FUN_0059a0c0",
           0x59a1bc: "FUN_0059a0c0", 0x59a372: "FUN_0059a2b0", 0x59bf46: "FUN_0059bec0"}
# the writer's own sites: fopen call, open-fail return, magic write, version write, codec call,
# timestamp write, fclose
WINTERNAL = {0x597DB7: "fopen", 0x597DCF: "ret1-openfail", 0x597DDB: "magic", 0x597DF0: "version",
             0x597E04: "codec", 0x597E19: "time", 0x597E28: "fclose"}
WSITES = [0x596883, 0x596927, 0x596976, 0x5969CB, 0x596A03, 0x596A8A, 0x596AF5, 0x596ECF, 0x596F1E,
          0x597026, 0x59707D, 0x5970DD, 0x59713A, 0x5971A5, 0x597203, 0x59728D, 0x597312, 0x597384,
          0x597518, 0x59762F, 0x597697, 0x59770F, 0x59777A, 0x5977D6, 0x59782D, 0x59788B, 0x5978E8,
          0x597948, 0x5979BA, 0x5979DC]                       # 30 call 0x64c9a0 (WRITE) sites
RSITES = [0x59688A, 0x59692E, 0x59697D, 0x5969D2, 0x596A33, 0x596A91, 0x596AFC, 0x596ED6, 0x596F25,
          0x59702D, 0x597084, 0x5970E4, 0x597141, 0x5971AC, 0x59720A, 0x597294, 0x597319, 0x59738B,
          0x59751F, 0x597636, 0x59769E, 0x597716, 0x597781, 0x5977DD, 0x597834, 0x597892, 0x5978EF,
          0x59794F]                                           # 28 call 0x64cc00 (READ) sites
SWSITES = [0x5968D2, 0x596908, 0x59695A, 0x5969AC, 0x596A25, 0x596A6B, 0x596ADA, 0x596EB0, 0x596F02,
           0x597007, 0x597061, 0x5970C2, 0x59711B, 0x597186, 0x5971E8, 0x59726E, 0x5972F7, 0x59736D,
           0x5974FD, 0x597610, 0x597678, 0x5976F0, 0x59775B, 0x5977BA, 0x597811, 0x597873, 0x5978D0,
           0x59792C]                                           # 28 call 0x596470 (swap WRITE)
SRSITES = [0x5968D9, 0x59690F, 0x596961, 0x5969B3, 0x596A2C, 0x596A72, 0x596AE1, 0x596EB7, 0x596F09,
           0x59700E, 0x597068, 0x5970C9, 0x597122, 0x59718D, 0x5971EF, 0x597275, 0x5972FE, 0x597374,
           0x597504, 0x597617, 0x59767F, 0x5976F7, 0x597762, 0x5977C1, 0x597818, 0x59787A, 0x5978D7,
           0x597933]                                           # 28 call 0x596540 (swap READ)
NBP = 1 + len(CALLERS) + len(WINTERNAL) + 1 + len(WSITES) + len(RSITES) + len(SWSITES) + len(SRSITES)


def gdb_script():
    """130 silent bps.  Every printf has exactly as many specs as it has args (a mismatch aborts
    the sourced script and DETACHES at the first hit).  At a wrapper call site the stack is
    [esp]=dst [esp+4]=size [esp+8]=count [esp+0xc]=FILE* (m109 law); at a function entry [esp+4] is
    arg0."""
    L = ["set pagination off", "set confirm off",
         "handle SIGUSR1 nostop noprint pass", "handle SIGUSR2 nostop noprint pass",
         "handle SIGPIPE nostop noprint pass"]

    def bp(addr, fmt, args):
        L.extend(["break *0x%x" % addr, "commands", "silent",
                  'printf "%s\\n", %s' % (fmt, args), "continue", "end"])

    def cs(addr, tag):
        bp(addr, "%s %06x dir=%%d dst=%%d sz=%%d n=%%d h=%%d" % (tag, addr),
           "(*(int*)0x926a0c), (*(int*)$esp), (*(int*)($esp+4)), "
           "(*(int*)($esp+8)), (*(int*)($esp+0xc))")

    # the writer: entry logs the path pointer + the first 16 bytes it points at (no inferior
    # strings in gdb printf), internals log the args they pass.
    L.extend(["break *0x%x" % WRITER, "commands", "silent",
              "set $pathp = *(int*)($esp+4)",
              'printf "ENT %06x p=%%d d0=%%d d1=%%d d2=%%d d3=%%d\\n", ($pathp), (*(int*)$pathp), '
              '(*(int*)($pathp+4)), (*(int*)($pathp+8)), (*(int*)($pathp+12))' % WRITER,
              "continue", "end"])
    for a, nm in sorted(WINTERNAL.items()):
        bp(a, "INT %06x %s a0=%%d a1=%%d" % (a, nm), "(*(int*)$esp), (*(int*)($esp+4))")
    for a, nm in sorted(CALLERS.items()):
        bp(a, "CALLER %06x arg0=%%d" % a, "(*(int*)$esp)")
    bp(CODEC, "ENCODEC mode=%d f=%d swap=%d",
       "(*(int*)($esp+8)), (*(int*)($esp+4)), (*(int*)0x985ae8) & 0x10000000")
    for a in WSITES:
        cs(a, "W")
    for a in RSITES:
        cs(a, "R")
    for a in SWSITES:
        cs(a, "SW")
    for a in SRSITES:
        cs(a, "SR")
    L.append('printf "ARMED n=%d\\n"' % NBP)
    L.append("continue")
    return "\n".join(L) + "\n"

def all_savs():
    return glob.glob(os.path.join(ROOT, "programs", "saves", "**", "*.SAV"), recursive=True)


def body(png):
    return " ".join(w[0] for w in P.ocr(png)).lower()


def frame_diff(a, b):
    from PIL import Image, ImageChops
    return ImageChops.difference(Image.open(a), Image.open(b)).getbbox() is not None


def open_browser(tag):
    """Ctrl+S is the GAME submenu's Save Game hotkey (read off the submenu frame in M241); fall back
    to MENU -> GAME -> Save Game.  Verified by FRAME DIFF, not OCR: tesseract renders the submenu's
    small type as garbage ('Load Game...' -> 'lad'), so an OCR check aborts a route that is open."""
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
    P.sh('xdotool type --delay 25 "%s"' % save_name(tag))     # confirm, no "exist" dialog to dismiss
    time.sleep(0.8)
    return True, "browser open, name typed"


def save_name(tag):
    return SAVE_NAME[:-4] + "_" + tag[-1:].upper() + ".SAV"    # distinct per phase: no overwrite


def press_ok_and_wait(tag, before, t0):
    """The ONE trigger: click OK.  Detection is by MTIME (a same-name overwrite adds no filename)."""
    P.click(SAVE_OK)
    nf = []
    for _ in range(30):
        time.sleep(1.0)
        nf = [f for f in all_savs() if os.path.getmtime(f) > t0]
        if nf:
            break
        b = body(P.freeze(tag + "_wait"))
        if "exist" in b or "overwrite" in b or "really" in b:
            P.key("Return")
    return nf, ("ok" if nf else "no .SAV mtime newer than the window start within 30 s of the OK click")


def close_leftovers(tag):
    P.key("Escape")
    time.sleep(1.2)
    b = body(P.freeze(tag + "_close"))
    if "really" in b and "quit" in b:
        P.key("Escape")
        time.sleep(1.2)
        b = body(P.freeze(tag + "_close2"))
    return b


def hdr_check(fd, path):
    """Outcome read-back OUTSIDE the game: the 796-B global the codec serializes must sit verbatim
    in the file the game wrote, at the offset the writer's own order predicts (8 magic + 4 version)."""
    blk = os.pread(fd, HDRSZ, HDR)
    data = open(path, "rb").read()
    off = data.find(blk)
    ver = int.from_bytes(data[8:12], "little")
    return {"size": len(data), "magic": data[:6] == MAGIC, "ver": ver, "off": off,
            "same12": sum(1 for a, b in zip(blk, data[12:12 + HDRSZ]) if a == b),
            "year": (int.from_bytes(os.pread(fd, 4, YEAR), "little"),
                     int.from_bytes(data[12 + (YEAR - HDR):14 + (YEAR - HDR)], "little"))}


def kv(h):
    return {p.split("=", 1)[0]: int(p.split("=", 1)[1], 16) if p.split("=", 1)[0] == "p"
            else int(p.split("=", 1)[1]) for p in h[2:] if "=" in p}


def tally(hits, tag):
    d = {}
    for h in hits:
        if h[0] == tag:
            a = int(h[1], 16)
            d.setdefault(a, []).append(kv(h))
    return d

def main():
    import struct
    pid = (int(sys.argv[sys.argv.index("--pid") + 1]) if "--pid" in sys.argv
           else int(subprocess.check_output(["pgrep", "-x", "terran.exe"]).split()[0]))
    fd = os.open("/proc/%d/mem" % pid, os.O_RDONLY)

    def rd(a):
        return int.from_bytes(os.pread(fd, 4, a), "little")

    swap_expected = (rd(0x985AE8) & 0x10000000) != 0
    print("pid=%d  dir ds:0x926a0c=%d  swap ds:0x985ae8&0x10000000=%s  ds:0x920434=%d  "
          "ds:0x985dbc=%d  year=%d" % (pid, rd(DIRFLAG), hex(rd(0x985AE8) & 0x10000000),
                                       rd(0x920434), rd(0x985DBC), rd(YEAR)), flush=True)

    beforeA, tA = set(all_savs()), time.time()
    okA, msgA = open_browser("m242_a")
    if not okA:
        raise SystemExit("BLOCKER phase A: " + msgA)
    nfA, msgA2 = press_ok_and_wait("m242_a", beforeA, tA)
    hA = hdr_check(fd, nfA[0]) if nfA else None
    time.sleep(1.0)
    close_leftovers("m242_a")
    print("PHASE A (no tracer): %s / %s" % (msgA, msgA2), flush=True)
    for f in nfA:
        print("  A file %s  %d B  mtime +%.1f s" % (f, os.path.getsize(f), os.path.getmtime(f) - tA))
    if hA:
        print("  A file bytes: magic=%s ver=%d  block-at=%s  matching-at-12=%d/%d  year mem/file=%s"
              % (hA["magic"], hA["ver"], hA["off"], hA["same12"], HDRSZ, hA["year"]), flush=True)

    okB, msgB = open_browser("m242_b")            # navigate BEFORE arming: only the write is traced
    if not okB:
        raise SystemExit("BLOCKER phase B: " + msgB)
    beforeB, tB = set(all_savs()), time.time()
    gpath = os.path.join(ROOT, "scratch", "m242_b.gdb")
    lpath = os.path.join(ROOT, "scratch", "m242_b.gdblog")
    open(gpath, "w").write(gdb_script())
    if os.path.exists(lpath):
        os.remove(lpath)
    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=log, stderr=subprocess.STDOUT)
    armed = False
    for _ in range(120):
        time.sleep(0.5)
        if "ARMED" in open(lpath, errors="replace").read():
            armed = True
            break
    if not armed:
        os.kill(g.pid, signal.SIGINT)
        subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
        raise SystemExit("BLOCKER: gdb did not arm %d bps:\n" % NBP
                         + open(lpath, errors="replace").read()[-900:])
    nfB, msgB2 = press_ok_and_wait("m242_b", beforeB, tB)
    hB = hdr_check(fd, nfB[0]) if nfB else None   # read while still attached: no post-save drift
    time.sleep(2.0)
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
            if l.split() and l.split()[0] in ("ENT", "INT", "CALLER", "ENCODEC", "W", "R", "SW", "SR")]
    warns = [l for l in txt.splitlines()
             if re.search(r"warning|error:|Cannot access|cannot insert", l, re.I)]
    tracer = next(l.split()[1] for l in open("/proc/%d/status" % pid) if l.startswith("TracerPid"))
    close_leftovers("m242_b")                     # AFTER the detach: one Escape, quit-prompt-guarded
    ent, callers, enc = tally(hits, "ENT"), tally(hits, "CALLER"), tally(hits, "ENCODEC")
    w, r, sw, sr, intr = (tally(hits, "W"), tally(hits, "R"), tally(hits, "SW"),
                          tally(hits, "SR"), tally(hits, "INT"))
    nent = sum(len(v) for v in ent.values())
    ncall = sum(len(v) for v in callers.values())
    nW, nR = sum(len(v) for v in w.values()), sum(len(v) for v in r.values())
    print("PHASE B (tracer): %s / %s  hits=%d  TracerPid after detach=%s"
          % (msgB, msgB2, len(hits), tracer), flush=True)
    for f in nfB:
        print("  B file %s  %d B  mtime +%.1f s" % (f, os.path.getsize(f), os.path.getmtime(f) - tB))
    if hB:
        print("  B file bytes: magic=%s ver=%d  block-at=%s  matching-at-12=%d/%d  year mem/file=%s"
              % (hB["magic"], hB["ver"], hB["off"], hB["same12"], HDRSZ, hB["year"]), flush=True)
    for a, rows in sorted(ent.items()):
        for d in rows:
            raw = b"".join(struct.pack("<I", d[k]) for k in ("d0", "d1", "d2", "d3"))
            print("  WRITER entry p=%08x path16=%r" % (d["p"], raw.split(b"\x00")[0]), flush=True)
    for a, rows in sorted(callers.items()):
        print("  via %s (%s) x%d" % (hex(a), CALLERS[a], len(rows)), flush=True)
    for a, rows in sorted(intr.items()):
        print("  writer site %s %s x%d a0=%s a1=%s"
              % (hex(a), WINTERNAL[a], len(rows), hex(rows[0]["a0"]), rows[0]["a1"]), flush=True)
    modes = [d["mode"] for v in enc.values() for d in v]
    swaps = [d["swap"] for v in enc.values() for d in v]
    print("  codec entry: %d hits mode=%s swap-bits=%s" % (len(modes), modes, swaps))
    print("  write legs (call 0x64c9a0): %d hits at %d of %d sites; read legs (call 0x64cc00): "
          "%d hits at %d of %d; swap-write %d; swap-read %d"
          % (nW, len(w), len(WSITES), nR, len(r), len(RSITES),
             sum(len(v) for v in sw.values()), sum(len(v) for v in sr.values())))
    for a in (0x596883, 0x59688A):
        rows = w.get(a) or r.get(a) or []
        if rows:
            print("  header leg %s x%d dir=%d dst=%s sz=%d n=%d h=%s"
                  % (hex(a), len(rows), rows[0]["dir"], hex(rows[0]["dst"]), rows[0]["sz"],
                     rows[0]["n"], hex(rows[0]["h"])), flush=True)
    hdr_ok = all(d["dst"] == HDR and d["sz"] == HDRSZ and d["n"] == 1 for d in w.get(0x596883, []))
    G1 = bool(nfA and nfB) and all(all(os.path.getsize(f) > 200000 and os.path.getmtime(f) > t - 1
                                       for f in nf) for nf, t in ((nfA, tA), (nfB, tB)))
    G2 = armed and not warns and tracer == "0" and os.path.exists("/proc/%d" % pid)
    G3 = nent >= 1 and nent == ncall
    G4 = (1 in modes and len(w) >= 1 and nR == 0 and nW > 0 and hdr_ok
          and all(d["dir"] == 1 for v in w.values() for d in v)
          and (bool(sw) == swap_expected) and not sr)
    G5 = bool(hB) and hB["magic"] and hB["ver"] == VER and hB["off"] == 12 \
        and hB["same12"] == HDRSZ and hB["year"][0] == hB["year"][1]
    verdict = ("CONFIRMED: a save runs FUN_00597ce0 (open + TERRAN magic + version 0x56 + body + "
               "close, delete-on-fail) which calls FUN_00596850(handle, 1); its 30 write legs ran "
               "(%d hits at %d sites), its 28 read legs ran ZERO, and the 796-B global it serializes "
               "is verbatim at file offset 12 of the file the host statted" % (nW, len(w))
               ) if all((G1, G2, G3, G4, G5)) else \
              ("UNDECIDED: G1..G5 = %s — see the numbers above"
               % [int(x) for x in (G1, G2, G3, G4, G5)])
    print("VERDICT: " + verdict)
    names = ["G1 trigger: a >200 KB .SAV whose mtime is inside BOTH save windows (host stat)",
             "G2 instrument: %d bps armed, no gdb insert warnings, TracerPid back to 0, inferior alive" % NBP,
             "G3 the writer FUN_00597ce0 ran in the traced window and every run is attributed to one "
             "of its armed call sites",
             "G4 one codec, write direction: mode==1 at 0x596850, write legs hot with the predicted "
             "dst/size/count, read legs ZERO, swap siblings match ds:0x985ae8&0x10000000",
             "G5 outcome in the file the game wrote: TERRAN magic, version 0x56 at 8, the live 796-B "
             "block verbatim at 12, year agrees"]
    npass = 0
    for nm, ok in zip(names, (G1, G2, G3, G4, G5)):
        print("%s %s" % ("PASS" if ok else "FAIL", nm))
        npass += ok
    print("%s M242: %d/5 gates" % ("PASS" if npass == 5 else "FAIL", npass))
    return 0 if npass == 5 else 1


sys.exit(main())


