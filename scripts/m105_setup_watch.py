#!/usr/bin/env python3
"""M105 — who writes the per-faction 1436-byte record block 0x927a9c + fac*1436 AT SETUP?

M104 proved nobody APPENDS the block mid-game: 0 count-change events across rounds 57->60 while the
CONTROL watchpoint logged 6 writes, and the .SAV carries the live count+TYPE+KEY+VAL image verbatim.
So the entries arrive at SETUP. The open question is WHICH setup writer: the save loader (the .SAV
holds the image at stride 1436) or the 1436-byte template copy on the new-fac paths — FUN_0057c550
(call to FUN_0059ec00 at 0x57ce48) and FUN_0057ecf0 (call at 0x57eee0), the only two setup callers of
the D-rebuild (M103).

THE TEST (process-start window, not a round window): relaunch terran.exe FRESH, wait for the title,
read the counts (are they already populated before any save is loaded?), POKED SENTINELS -77 into the
fac1/fac3/fac6 count dwords, attach gdb with 4 hardware watchpoints (the 3 counts + the ROUND dword
0x985afc as CONTROL — the save load must change 0->60) and silent bps at the two candidate copy
functions, their D-rebuild call sites, FUN_0059ec00/0059ec90 and the two cheat callers; THEN drive the
m54b_clean load under gdb. A hardware watchpoint only reports a VALUE CHANGE, so the sentinel is what
makes the shape discriminate: if a writer copies the block at load, the count changes -77 -> live and
logs its pc; if nobody writes it, the sentinel SURVIVES the load and the block is process-start data.

Every event pc is named twice: by ghidra containment (terran.exe .text) and by /proc/pid/maps (the
module + offset) — a save loader that reads straight into the region stores from ntdll, not .text.

  python3 scripts/m105_setup_watch.py --tag m105s1 --boundaries 1
"""
import argparse
import json
import os
import re
import signal
import struct
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import m55_boundary as M  # noqa: E402
import m99_param2 as P  # noqa: E402  (STRIDE, CP, ROUND, contain, load_funcs)

ROOT = os.path.dirname(HERE)
EVID = os.path.join(ROOT, "evidence")
SCRATCH = os.path.join(ROOT, "scratch")
S = P.STRIDE
RB, RS = 0x927a9c, 1436
TYPE_OFF, KEY_OFF, VAL_OFF, MAXE = 0x04, 0x24, 0x44, 8
DB, ND, ACC = 0x94d700, 11, 0x94d7f8
WFACS = [1, 3, 6]
SENT = -77
ROUND_ADDR = 0x985afc
RND, CPP = "*(int *)0x985afc", "*(int *)0x985dcc"
HUMAN = 3
# entry points + the D-rebuild call sites (M103) + the two cheat callers
ENT_PCS = [0x57c550, 0x57ecf0, 0x59ec00, 0x59ec90]
CALL_SITES = [0x57ce48, 0x57eee0, 0x4dbf6f, 0x4e061b]
LAUNCH = ("cd ~/reverse/smac/programs && WINEPREFIX=$HOME/.wine-smac32 DISPLAY=:99 "
          "WINEDLLOVERRIDES='mscoree,msxml=' nohup ~/tools/wine-10.20-staging-tkg-x86/bin/wine "
          "explorer /desktop=smac,800x600 terran.exe > /dev/null 2>&1 &")

TMPL = r"""set pagination off
set confirm off
set can-use-hw-watchpoints 1
@@BLOCKS@@printf "ARMED @@NW@@ hw watchpoints at @@ADDRS@@ and @@NB@@ silent bps at @@BPS@@\n"
continue
"""

WBLOCK = r"""watch *(int *)@@A@@
commands
silent
printf "@@LINE@@\n"@@ARGS@@
continue
end
"""

BPU = r"""break *@@PC@@
commands
silent
printf "@@LINE@@\n"@@ARGS@@
continue
end
"""


def cnt_addr(f):
    return RB + f * RS


def gdb_script():
    blocks, addrs, pcs, n = [], [], [], 0

    def chk(line, args):
        if len(re.findall(r"%[dx]", line)) != len(args):
            raise SystemExit("printf arg count %d != specs %d: %s"
                             % (len(args), len(re.findall(r"%[dx]", line)), line))

    for f in WFACS:
        a = cnt_addr(f)
        line = ("M105W CNT fac=%d new=%%d pc=0x%%x round=%%d cp=%%d" % f)
        args = ["*(int *)%#x" % a, "$pc", RND, CPP]
        chk(line, args)
        addrs.append("%#x" % a)
        blocks.append(WBLOCK.replace("@@A@@", "%#x" % a).replace("@@LINE@@", line)
                      .replace("@@ARGS@@", "".join(", " + x for x in args)))
        n += 1
    line = "M105W RND new=%d pc=0x%x round=%d cp=%d"
    args = [RND, "$pc", RND, CPP]
    chk(line, args)
    addrs.append("%#x" % ROUND_ADDR)
    blocks.append(WBLOCK.replace("@@A@@", "%#x" % ROUND_ADDR).replace("@@LINE@@", line)
                  .replace("@@ARGS@@", "".join(", " + x for x in args)))
    n += 1
    for pc in ENT_PCS:
        line = "M105E ENT pc=0x%x a0=%%d round=%%d cp=%%d" % pc
        args = ["*(int *)($esp+4)", RND, CPP]
        chk(line, args)
        pcs.append("%#x" % pc)
        blocks.append(BPU.replace("@@PC@@", "%#x" % pc).replace("@@LINE@@", line)
                      .replace("@@ARGS@@", "".join(", " + x for x in args)))
    for pc in CALL_SITES:
        line = "M105E CALL pc=0x%x s0=%%d round=%%d cp=%%d" % pc
        args = ["*(int *)($esp)", RND, CPP]
        chk(line, args)
        pcs.append("%#x" % pc)
        blocks.append(BPU.replace("@@PC@@", "%#x" % pc).replace("@@LINE@@", line)
                      .replace("@@ARGS@@", "".join(", " + x for x in args)))
    return (TMPL.replace("@@BLOCKS@@", "".join(blocks)).replace("@@NW@@", str(n))
            .replace("@@ADDRS@@", " ".join(addrs)).replace("@@NB@@", str(len(pcs))
                                                          ).replace("@@BPS@@", " ".join(pcs)))


KV = re.compile(r"^(M105W) (CNT|RND)((?: [a-z][a-z0-9_]*=-?[\dxa-f]+)+) round=(\d+) cp=(\d+)\s*$")
KE = re.compile(r"^(M105E) (ENT|CALL)((?: [a-z][a-z0-9_]*=-?[\dxa-f]+)+) round=(\d+) cp=(\d+)\s*$")
OK_LINE = re.compile(r"^(ARMED |0x[0-9a-f]+ in |\[New LWP |\[Thread |\[Switching to |"
                     r"Thread \d+ |This is not |^\$[0-9]+ = |^Continue|^\^|warning:|"
                     r"Cannot breakpoint|\[Inferior \d+ |This GDB supports |\s+<https://|"
                     r"Enable debuginfod|Debuginfod has|To make this setting |"
                     r"Breakpoint \d+ at |Hardware watchpoint \d+: |Watchpoint \d+: |"
                     r"Delete the |$)")


def parse(text):
    ev, bad = [], []
    pos = 0
    for ln in text.split("\n"):
        cur = pos
        pos += len(ln) + 1
        ln = ln.rstrip()
        if not ln:
            continue
        m = KV.match(ln) or KE.match(ln)
        if m:
            d = {"kind": m.group(2), "_off": cur}
            for tok in m.group(3).split():
                k, v = tok.split("=", 1)
                d[k] = int(v, 16) if v.startswith("0x") else int(v)
            d["round"], d["cp"] = int(m.group(4)), int(m.group(5))
            ev.append(d)
        elif not OK_LINE.match(ln):
            bad.append(ln)
    return ev, bad


def read_block(fd, f):
    a = cnt_addr(f)
    cnt = struct.unpack("<i", M.rd(fd, a, 4))[0]
    ent = []
    for i in range(max(cnt, 0)):
        t = struct.unpack("<i", M.rd(fd, a + TYPE_OFF + 4 * i, 4))[0]
        k = struct.unpack("<i", M.rd(fd, a + KEY_OFF + 4 * i, 4))[0]
        v = struct.unpack("<i", M.rd(fd, a + VAL_OFF + 4 * i, 4))[0]
        ent.append((t, k, v))
    d = list(struct.unpack("<%di" % ND, M.rd(fd, DB + f * S, 4 * ND)))
    return cnt, ent, d


def model_of(ent):
    m = {}
    for t, k, v in ent:
        if t == 3:
            m[k] = m.get(k, 0) + v
    return [m.get(i, 0) for i in range(ND)]


def wine_pids():
    pids = []
    try:
        for d in os.listdir("/proc"):
            if not d.isdigit():
                continue
            try:
                cl = open("/proc/%s/cmdline" % d, "rb").read().split(b"\0")
            except OSError:
                continue
            if not cl:
                continue
            argv0 = os.path.basename(cl[0]).decode("ascii", "replace").lower()
            if (argv0 in ("terran.exe", "winedbg.exe", "explorer.exe", "winedevice.exe",
                          "services.exe", "wine", "wine-preloader", "wineserver",
                          "wineserver.exe")
                    or b"desktop=smac" in b" ".join(cl)):
                pids.append((int(d), argv0))
    except OSError:
        pass
    return pids


def terran_pid():
    for p, name in wine_pids():
        if name == "terran.exe":
            return p
    return None


def wait_title(timeout):
    """Poll the screen until the game is initialized and IDLE at a pre-load pane."""
    import smac_play as SP
    t0 = time.time()
    last = None
    while time.time() - t0 < timeout:
        SP.WIN = SP.find_window()
        if SP.WIN:
            SP.focus()
            png = SP.freeze("m105_boot")
            words = SP.ocr(png)
            kind = SP.classify(words, SP.region_colors(png), png)
            body = " ".join(w[0] for w in words).lower()
            if kind != last:
                print("  [%5.1fs] class=%s body=%s" % (time.time() - t0, kind, body[:56]),
                      flush=True)
                last = kind
            if kind == "title" or "start game" in body:  # s161: 'cdrom' is still STARTUP
                return True
        time.sleep(2)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m105s1")
    ap.add_argument("--save", default="m54b_clean.SAV")
    ap.add_argument("--relaunch", action="store_true")
    ap.add_argument("--load-timeout", type=int, default=240)
    ap.add_argument("--boundaries", type=int, default=1)
    a = ap.parse_args()

    gpath = os.path.join(SCRATCH, "%s.gdb" % a.tag)
    lpath = os.path.join(EVID, "%s.gdblog" % a.tag)
    os.makedirs(SCRATCH, exist_ok=True)
    open(gpath, "w").write(gdb_script())

    if a.relaunch:
        for p, name in wine_pids():
            if name == "terran.exe":
                subprocess.run(["kill", str(p)], capture_output=True)
        time.sleep(3)
        for p, name in wine_pids():
            if name != "terran.exe":
                subprocess.run(["kill", str(p)], capture_output=True)
        time.sleep(4)
        print("killed old wine tree by PID; leftover %s" % wine_pids(), flush=True)
        subprocess.run(LAUNCH, shell=True)
        pid = None
        for _ in range(80):
            pid = terran_pid()
            if pid:
                break
            time.sleep(0.25)
        if not pid:
            raise SystemExit("no terran.exe after relaunch")
        print("terran.exe pid %d up after %.1fs" % (pid, time.time()), flush=True)
    with open("/proc/%d/mem" % pid, "rb", 0) as mm:
        disc = [struct.unpack("<i", M.rd(mm, cnt_addr(f), 4))[0] for f in range(8)]
        rnd_disc = struct.unpack("<i", M.rd(mm, ROUND_ADDR, 4))[0]
    print("AT DISCOVERY (earliest read): round=%d counts=%s" % (rnd_disc, disc), flush=True)

    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=log, stderr=subprocess.STDOUT,
                         env=dict(os.environ, DEBUGINFOD_URLS=""))
    time.sleep(3.0)
    head = open(lpath, "r", errors="replace").read()
    if "ARMED" not in head:
        try:
            os.kill(g.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
        subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
        raise SystemExit("gdb did not arm:\n" + head[-1200:])
    armed = [ln for ln in head.splitlines() if ln.startswith("ARMED")]
    print("armed EARLY (before the title): %s" % (armed[0][:200] if armed else "<none>"),
          flush=True)
    off_arm = os.path.getsize(lpath)

    if not wait_title(a.load_timeout):
        raise SystemExit("no true title screen after relaunch")
    with open("/proc/%d/mem" % pid, "rb", 0) as mm:
        pre = {f: read_block(mm, f) for f in range(8)}
        rnd_pre = struct.unpack("<i", M.rd(mm, ROUND_ADDR, 4))[0]
    print("AT TRUE TITLE (no save loaded): round=%d counts=%s"
          % (rnd_pre, [pre[f][0] for f in range(8)]), flush=True)
    print("  entries at title: " + "; ".join(
        "fac%d %s" % (f, pre[f][1]) for f in WFACS), flush=True)

    with open("/proc/%d/mem" % pid, "wb", 0) as mm:
        for f in WFACS:
            mm.seek(cnt_addr(f))
            mm.write(struct.pack("<i", SENT))
    with open("/proc/%d/mem" % pid, "rb", 0) as mm:
        poked = {f: struct.unpack("<i", M.rd(mm, cnt_addr(f), 4))[0] for f in WFACS}
    print("poke %d at the idle title -> counts facs %s read back %s"
          % (SENT, WFACS, list(poked.values())), flush=True)
    off_title = os.path.getsize(lpath)

    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "m54a_load.py")],
                       capture_output=True, text=True,
                       env=dict(os.environ, SMAC_SAVE="Z:\\home\\n100\\reverse\\smac\\programs\\saves\\"
                                + a.save))
    print("load rc=%d" % r.returncode, flush=True)
    for ln in (r.stdout or "").strip().splitlines()[-6:]:
        print("  load: " + ln[:150], flush=True)
    time.sleep(3)
    try:
        os.kill(g.pid, signal.SIGINT)
    except ProcessLookupError:
        pass
    for _ in range(40):
        if not os.path.exists("/proc/%d" % g.pid):
            break
        time.sleep(0.5)
    subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
    log.close()

    text = open(lpath, "r", errors="replace").read()
    ev, bad = parse(text)
    cnt_e = [e for e in ev if e["kind"] == "CNT"]
    rnd_e = [e for e in ev if e["kind"] == "RND"]
    ent_e = [e for e in ev if e["kind"] in ("ENT", "CALL")]
    tracer = subprocess.run(["grep", "-m1", "TracerPid", "/proc/%d/status" % pid],
                            capture_output=True, text=True).stdout.split()[-1]
    with open("/proc/%d/mem" % pid, "rb", 0) as mm:
        fin = {f: read_block(mm, f) for f in range(8)}
        rnd_post = struct.unpack("<i", M.rd(mm, ROUND_ADDR, 4))[0]
        cp_post = struct.unpack("<i", M.rd(mm, P.CP, 4))[0]
        blk = {f: bytes(M.rd(mm, cnt_addr(f), RS)) for f in WFACS}
    with open(os.path.join(SCRATCH, "%s_seq.jsonl" % a.tag), "w") as fh:
        for e in ev:
            fh.write(json.dumps(e) + "\n")
    maps = {}
    for ln in open("/proc/%d/maps" % pid):
        mm2 = re.match(r"^([0-9a-f]+)-([0-9a-f]+) (\S+) \S+ \S+ \S+\s+(.*)$", ln)
        if mm2 and mm2.group(4).startswith("/"):
            maps.setdefault(mm2.group(4), (int(mm2.group(1), 16), int(mm2.group(2), 16)))
    funcs = P.load_funcs()

    def name_of(pc):
        c = P.contain(pc, funcs)
        for mod, (lo, hi) in maps.items():
            if lo <= pc < hi:
                return "%s%s" % (c or "?", " [%s+0x%x]" % (os.path.basename(mod), pc - lo))
        return c or "<unmapped>"

    gates = []

    def gate(name, ok, detail):
        gates.append((name, bool(ok), detail))

    gate("G1-4-watchpoints-armed", " %d hw watchpoints at " % (len(WFACS) + 1) in head,
         "armed: %s" % (armed[0][:120] if armed else "<none>"))
    gate("G2-poke-landed", all(poked[f] == SENT for f in WFACS),
         "counts read back %s at arm" % list(poked.values()))
    gate("G3-save-loaded", r.returncode == 0 and rnd_post >= 50,
         "load rc=%d round %d -> %d cp=%d" % (r.returncode, rnd_pre, rnd_post, cp_post))
    gate("G4-count-write-observed", bool(cnt_e),
         "%d CNT events %s" % (len(cnt_e), ["fac%d ->%d pc=%s" % (e["fac"], e["new"],
          name_of(e["pc"])) for e in cnt_e[:6]]))
    unmapped = [e for e in cnt_e + rnd_e if name_of(e["pc"]) == "<unmapped>"]
    gate("G5-every-writer-pc-named", not unmapped,
         "%d/%d pcs named; CNT writers %s; RND writer %s"
         % (len(cnt_e) + len(rnd_e) - len(unmapped), len(cnt_e) + len(rnd_e),
            sorted({name_of(e["pc"]) for e in cnt_e}),
            sorted({name_of(e["pc"]) for e in rnd_e})))
    gate("G6-round-control-fires", bool(rnd_e),
         "%d RND events %s (the control proves the machinery logs a store in this window)"
         % (len(rnd_e), ["new=%d pc=%s" % (e["new"], name_of(e["pc"])) for e in rnd_e[:4]]))
    surviving = [f for f in WFACS if fin[f][0] == SENT]
    gate("G7-sentinel-replaced-or-survives", len(surviving) != len(WFACS),
         "counts after=%s sentinel-survivors=%s" % ([fin[f][0] for f in range(8)], surviving))
    LIVE_IMG = [0, 6, 5, 4, 3, 4, 5, 3]  # m104w3 G6: the loaded m54b_clean count image
    wrong = ["fac%d count=%d want %d" % (f, fin[f][0], LIVE_IMG[f]) for f in range(8)
             if fin[f][0] != LIVE_IMG[f]]
    gate("G8-post-load-counts-eq-m104-image", not wrong, "; ".join(wrong) or
         "all 8 counts == the m104w3 baseline (the setup writer produced the save image)")
    badD = ["fac%d model %s != D %s" % (f, model_of(fin[f][1]), fin[f][2]) for f in WFACS
            if model_of(fin[f][1]) != fin[f][2]]
    gate("G9-model-eq-live-D", not badD, "; ".join(badD) or "3/3 after the load")
    seen = {rnd_pre} | {e["new"] for e in rnd_e}
    stray = [e for e in cnt_e if e["round"] not in seen]
    gate("G10-cnt-inside-the-load-window", not stray,
         "%d CNT events at rounds %s; in-window rounds %s; stray %d"
         % (len(cnt_e), [e["round"] for e in cnt_e][:8], sorted(seen), len(stray)))
    gate("G11-zero-unparsed", not bad, "%d unparsed %s" % (len(bad), bad[:3]))
    gate("G12-tracer-zero", tracer == "0", "TracerPid=%s" % tracer)
    errl = [ln for ln in text.splitlines() if "Undefined" in ln or "Missing" in ln
            or "doesn't match" in ln]
    gate("G13-no-gdb-errors", not errl, "%d error lines %s" % (len(errl), errl[:2]))
    off_arm = head.index("ARMED")  # the arm printf; every event line follows it
    startup_e = [e for e in ev if e["_off"] < off_title]
    load_e = [e for e in ev if e["_off"] >= off_title]
    def brief(es):
        return sorted({"%s %s@%s" % (e["kind"], ("fac%d" % e["fac"]) if "fac" in e else "RND",
                                     name_of(e["pc"])) for e in es})
    gate("G14-rebuild-or-caller-events", True,
         "%d ENT/CALL events %s" % (len(ent_e), sorted({"%s %s" % (e["kind"], name_of(e["pc"]))
                                                        for e in ent_e})))
    gate("G16-window-partition", off_title > off_arm and all(e["_off"] >= off_arm for e in ev),
         "arm@%d title@%d; %d STARTUP-window events %s; %d LOAD-window events %s"
         % (off_arm, off_title, len(startup_e), brief(startup_e), len(load_e), brief(load_e)))
    unlogged = [f for f in WFACS if fin[f][0] != SENT
                and not any(e["kind"] == "CNT" and e["fac"] == f for e in ev)]
    gate("G17-every-sentinel-replacement-logged", not unlogged,
         "survivors %s; replaced-without-an-event %s" % (surviving, unlogged))
    savp = os.path.join(ROOT, "programs", "saves", a.save)
    sav = open(savp, "rb").read() if os.path.exists(savp) else b""
    hits = {}
    for f in WFACS:
        j = 0
        while True:
            j = sav.find(blk[f], j)
            if j < 0:
                break
            hits[f] = j
            j += 1
    gate("G15-live-block-bytes-in-save", len(hits) == len(WFACS),
         "live 1436-B block found in %s at %s" % (a.save, ["fac%d@0x%x" % (f, hits[f])
                                                          for f in sorted(hits)]))
    print("--- events: %d CNT %d RND %d ENT/CALL ---" % (len(cnt_e), len(rnd_e), len(ent_e)),
          flush=True)
    for e in cnt_e[:12] + rnd_e[:6] + ent_e[:12]:
        print("  %s %s r%d cp%d %s" % (e["kind"], ("fac%d" % e["fac"]) if "fac" in e else "",
              e["round"], e["cp"], name_of(e["pc"])), flush=True)
    good = True
    for name, ok, detail in gates:
        good = good and ok
        print("%-28s %s  %s" % (name, "PASS" if ok else "FAIL", detail))
    print("ACCEPTANCE %s %d/%d  (tag %s, pid %d, save %s, round %d->%d)"
          % ("PASS" if good else "FAIL", sum(1 for _, o, _ in gates if o), len(gates),
             a.tag, pid, a.save, rnd_pre, rnd_post))
    print("context: gdb log %s; gdb script %s" % (lpath, gpath))
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
