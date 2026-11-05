#!/usr/bin/env python3
"""M272 - does FUN_0057ecf0 (the NEW GAME caller of the world generator) also run on a LOAD?

M255 settled statically that FUN_005b2970 (the generator) has EXACTLY 4 call sites:
0x4e1151 (FUN_004e10c0), 0x4e122b (FUN_004e11b0), 0x57d2a0 (FUN_0057c550 = scenario/MAP load),
0x57f1ec (FUN_0057ecf0 = new game). NEXT_PROMPT's live question: does 57ecf0 also run on a LOAD?

THE TEST: silent bps at the generator entry (return address at $esp names the caller directly),
at all FOUR caller entries, and at all four call sites. Arm at process start (the boot path runs
the new-game generator = the positive control that the bps exist), partition the log into
STARTUP (arm..title) and LOAD (title..end) windows by offset, POKE -39 into the ROUND dword at the
idle title as the load sentinel (a hw watchpoint cannot see the load's restore path - M105 - but a
value READ BACK can), then drive the m54b_clean load and read everything back.

ANSWER ENCODING (skill verify-outcome): the key gate PASSES iff the LOAD window is valid (the
sentinel was replaced -> the load demonstrably ran); its detail says YES-57ecf0-ran /
NO-57ecf0-did-not. If the load never ran the harness exits 4 (NEVER REACHED = inconclusive).
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
import m99_param2 as P  # noqa: E402  (CP, ROUND, contain, load_funcs)

ROOT = os.path.dirname(HERE)
EVID = os.path.join(ROOT, "evidence")
SCRATCH = os.path.join(ROOT, "scratch")
ROUND_ADDR = 0x985afc
RND, CPP = "*(int *)0x985afc", "*(int *)0x985dcc"
SENT = -39
GEN = 0x5b2970
ENTRIES = [GEN, 0x57ecf0, 0x57c550, 0x4e10c0, 0x4e11b0]
SITES = {0x57f1ec: 0x57ecf0, 0x57d2a0: 0x57c550, 0x4e1151: 0x4e10c0, 0x4e122b: 0x4e11b0}
CTRL = {0x596850: "SAVE_STATE_LOADER", 0x597a70: "BLOCK_LOADER", 0x598340: "FILE_DISPATCH",
        0x5791c0: "PROCESS_START_SETUP"}  # M105 names; NAMED.md rows 12-15
LIVE_IMG = [0, 6, 5, 4, 3, 4, 5, 3]  # m104w3: the loaded m54b_clean count image
RB, RS = 0x927a9c, 1436
LAUNCH = ("cd ~/reverse/smac/programs && WINEPREFIX=$HOME/.wine-smac32 DISPLAY=:99 "
          "WINEDLLOVERRIDES='mscoree,msxml=' nohup ~/tools/wine-10.20-staging-tkg-x86/bin/wine "
          "explorer /desktop=smac,800x600 terran.exe > /dev/null 2>&1 &")

TMPL = r"""set pagination off
set confirm off
@@BLOCKS@@printf "ARMED @@NB@@ silent bps at @@BPS@@\n"
continue
"""

BPU = r"""break *@@PC@@
commands
silent
printf "@@LINE@@\n"@@ARGS@@
continue
end
"""


def gdb_script():
    blocks, pcs, n = [], [], 0

    def chk(line, args):
        if len(re.findall(r"%[dx]", line)) != len(args):
            raise SystemExit("printf arg count %d != specs %d: %s"
                             % (len(args), len(re.findall(r"%[dx]", line)), line))

    for pc in ENTRIES:
        # at a function's FIRST insn $esp is the return address -> it names the caller
        line = "M272E ENT pc=0x%x ret=0x%%x round=%%d cp=%%d" % pc
        args = ["*(int *)$esp", RND, CPP]
        chk(line, args)
        pcs.append("%#x" % pc)
        blocks.append(BPU.replace("@@PC@@", "%#x" % pc).replace("@@LINE@@", line)
                      .replace("@@ARGS@@", "".join(", " + x for x in args)))
        n += 1
    for pc in sorted(SITES):
        line = "M272S SITE pc=0x%x ret=0x%%x round=%%d cp=%%d" % pc
        args = ["*(int *)$esp", RND, CPP]
        chk(line, args)
        pcs.append("%#x" % pc)
        blocks.append(BPU.replace("@@PC@@", "%#x" % pc).replace("@@LINE@@", line)
                      .replace("@@ARGS@@", "".join(", " + x for x in args)))
        n += 1
    for pc in sorted(CTRL):
        line = "M272C CTRL pc=0x%x ret=0x%%x round=%%d cp=%%d" % pc
        args = ["*(int *)$esp", RND, CPP]
        chk(line, args)
        pcs.append("%#x" % pc)
        blocks.append(BPU.replace("@@PC@@", "%#x" % pc).replace("@@LINE@@", line)
                      .replace("@@ARGS@@", "".join(", " + x for x in args)))
        n += 1
    return (TMPL.replace("@@BLOCKS@@", "".join(blocks)).replace("@@NB@@", str(n))
            .replace("@@BPS@@", " ".join(pcs)))


KV = re.compile(r"^(M272[ESC]) (ENT|SITE|CTRL)((?: [a-z][a-z0-9_]*=-?[0-9a-fx ]+?)+) round=(\d+) cp=(\d+)\s*$")
OK_LINE = re.compile(r"^(ARMED |0x[0-9a-f]+ in |\[New LWP |\[Thread |\[Switching to |"
                     r"Thread \d+ |This is not |^\$[0-9]+ = |^Continue|^\^|warning:|"
                     r"Cannot breakpoint|\[Inferior \d+ |This GDB supports |\s+<https://|"
                     r"Enable debuginfod|Debuginfod has|To make this setting |"
                     r"Breakpoint \d+ at |Delete the |$)")


def parse(text):
    ev, bad = [], []
    pos = 0
    for ln in text.split("\n"):
        cur = pos
        pos += len(ln) + 1
        ln = ln.rstrip()
        if not ln:
            continue
        m = KV.match(ln)
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


def wait_ready(timeout):
    """Poll the screen until the game is at the quiescent pre-load point (s161 law: CDROM counts)."""
    import smac_play as SP
    t0 = time.time()
    last = None
    while time.time() - t0 < timeout:
        SP.WIN = SP.find_window()
        if SP.WIN:
            SP.focus()
            png = SP.freeze("m272_boot")
            words = SP.ocr(png)
            kind = SP.classify(words, SP.region_colors(png), png)
            body = " ".join(w[0] for w in words).lower()
            if kind != last:
                print("  [%5.1fs] class=%s body=%s" % (time.time() - t0, kind, body[:56]),
                      flush=True)
                last = kind
            if kind in ("title", "cdrom") or "start game" in body:
                return True
        time.sleep(2)
    return False


def counts(fd):
    return [struct.unpack("<i", M.rd(fd, RB + f * RS, 4))[0] for f in range(8)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m272w1")
    ap.add_argument("--save", default="m54b_clean.SAV")
    ap.add_argument("--relaunch", action="store_true")
    ap.add_argument("--ready-timeout", type=int, default=300)
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
        print("terran.exe pid %d up" % pid, flush=True)
    else:
        pid = terran_pid()
        if not pid:
            raise SystemExit("terran.exe not running")
    with open("/proc/%d/mem" % pid, "rb", 0) as mm:
        rnd_disc, cnt_disc = struct.unpack("<i", M.rd(mm, ROUND_ADDR, 4))[0], counts(mm)
    print("AT DISCOVERY: round=%d counts=%s" % (rnd_disc, cnt_disc), flush=True)

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
    print("armed EARLY: %s" % [ln for ln in head.splitlines() if ln.startswith("ARMED")][0][:200],
          flush=True)

    if not wait_ready(a.ready_timeout):
        raise SystemExit("never reached the quiescent pre-load screen")
    with open("/proc/%d/mem" % pid, "rb", 0) as mm:
        rnd_pre, cnt_pre = struct.unpack("<i", M.rd(mm, ROUND_ADDR, 4))[0], counts(mm)
    print("AT READY POINT (no save loaded): round=%d counts=%s" % (rnd_pre, cnt_pre), flush=True)
    with open("/proc/%d/mem" % pid, "wb", 0) as mm:
        mm.seek(ROUND_ADDR)
        mm.write(struct.pack("<i", SENT))
    with open("/proc/%d/mem" % pid, "rb", 0) as mm:
        sent_rb = struct.unpack("<i", M.rd(mm, ROUND_ADDR, 4))[0]
    print("poke %d into ROUND -> read back %d" % (SENT, sent_rb), flush=True)
    off_ready = os.path.getsize(lpath)

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
    with open(os.path.join(SCRATCH, "%s_seq.jsonl" % a.tag), "w") as fh:
        for e in ev:
            fh.write(json.dumps(e) + "\n")
    funcs = P.load_funcs()

    def name_of(pc):
        c = P.contain(pc, funcs)
        return c or "<unmapped>"

    off_arm = text.index("ARMED")
    boot = [e for e in ev if off_arm <= e["_off"] < off_ready]
    load = [e for e in ev if e["_off"] >= off_ready]
    ent = lambda ws: [e for e in ws if e["kind"] == "ENT"]
    site = lambda ws: [e for e in ws if e["kind"] == "SITE"]
    gen = lambda ws: [e for e in ent(ws) if e["pc"] == GEN]
    brief = lambda ws: sorted({"%s 0x%x ret 0x%x" % (e["kind"], e["pc"], e["ret"]) for e in ws})

    with open("/proc/%d/mem" % pid, "rb", 0) as mm:
        rnd_post, cnt_post = struct.unpack("<i", M.rd(mm, ROUND_ADDR, 4))[0], counts(mm)
        cp_post = struct.unpack("<i", M.rd(mm, P.CP, 4))[0]
    tracer = subprocess.run(["grep", "-m1", "TracerPid", "/proc/%d/status" % pid],
                            capture_output=True, text=True).stdout.split()[-1]

    gates = []

    def gate(name, ok, detail):
        gates.append((name, bool(ok), detail))

    gate("G1-13-bps-armed", "ARMED 13 silent bps" in text,
         [ln for ln in text.splitlines() if ln.startswith("ARMED")][:1])
    bg = gen(boot)
    bctrl = [e for e in boot if e["kind"] == "CTRL"]
    gate("G2-boot-window-events", bool(bg or bctrl),
         "STARTUP: %d GEN %d CTRL %s" % (len(bg), len(bctrl), brief(bctrl)))
    boot_callers = sorted({name_of(e["ret"]) for e in bg})
    static4 = {"FUN_%06x" % s for s in SITES.values()}
    gate("G3-boot-gen-callers-are-the-static-4",
         (not bg) or all(c in static4 for c in boot_callers),
         "ret callers %s" % boot_callers)
    load_sentinel_gone = rnd_post != SENT and rnd_post >= 50
    gate("G4-load-window-valid", load_sentinel_gone,
         "ROUND poked %d -> post-load %d (cp=%d): the load demonstrably ran"
         % (sent_rb, rnd_post, cp_post))
    lctrl = [e for e in load if e["kind"] == "CTRL"]
    gate("G5-load-control-bp-fired", bool(lctrl),
         "%d CTRL events in the LOAD window (the bps are LIVE there): %s"
         % (len(lctrl), brief(lctrl)))
    q_ent = [e for e in ent(load) if e["pc"] == 0x57ecf0]
    q_site = [e for e in site(load) if e["pc"] == 0x57f1ec]
    window_ok = load_sentinel_gone and bool(lctrl)
    if not window_ok:
        gate("G6-ANSWER-57ecf0-on-LOAD", False, "NEVER REACHED - inconclusive, not a NO")
    else:
        ans = "YES-57ecf0-ran" if (q_ent or q_site) else "NO-57ecf0-did-not-run"
        gate("G6-ANSWER-57ecf0-on-LOAD", True,
             "%s; load window: 57ecf0 entry %d, its gen-call-site %d, GEN entry %d, "
             "57c550 entry %d, block-loader CTRL %d"
             % (ans, len(q_ent), len(q_site), len(gen(load)),
                len([e for e in ent(load) if e["pc"] == 0x57c550]),
                len([e for e in lctrl if e["pc"] == 0x597a70])))
    bad_callers = [e for e in gen(boot) + gen(load)
                   if not any(e["ret"] == s + il for s in SITES for il in (5, 6))]
    gate("G7-every-gen-hit-accounted-by-a-site", not bad_callers,
         "%d GEN entries %s; %d SITE events %s -> %s"
         % (len(gen(boot)) + len(gen(load)),
            sorted({"ret %s" % name_of(e["ret"]) for e in gen(boot) + gen(load)}),
            len(site(boot)) + len(site(load)),
            sorted({"0x%x" % e["pc"] for e in site(boot) + site(load)}),
            "all GEN hits have the matching site" if not bad_callers
            else "UNACCOUNTED %s" % brief([{"pc": 0, "ret": e["ret"], "kind": "?"}
                                           for e in bad_callers])))
    wrong = ["fac%d count=%d want %d" % (f, cnt_post[f], LIVE_IMG[f]) for f in range(8)
             if cnt_post[f] != LIVE_IMG[f]]
    gate("G8-post-load-counts-eq-m104-image", not wrong, "; ".join(wrong) or str(cnt_post))
    gate("G9-window-partition", off_ready > off_arm and all(e["_off"] >= off_arm for e in ev),
         "arm@%d ready@%d; STARTUP %s; LOAD %s" % (off_arm, off_ready, brief(boot), brief(load)))
    gate("G10-zero-unparsed", not bad, "%d unparsed %s" % (len(bad), bad[:3]))
    errl = [ln for ln in text.splitlines() if "Undefined" in ln or "Missing" in ln
            or "doesn\'t match" in ln]
    gate("G11-no-gdb-errors", not errl, "%d error lines %s" % (len(errl), errl[:2]))
    gate("G12-tracer-zero", tracer == "0", "TracerPid=%s" % tracer)

    print("--- events: %d STARTUP %d LOAD ---" % (len(boot), len(load)), flush=True)
    good = True
    for name, ok, detail in gates:
        good = good and ok
        print("%-34s %s  %s" % (name, "PASS" if ok else "FAIL", detail))
    print("ACCEPTANCE %s %d/%d  (tag %s, pid %d, save %s, round %d->%d)"
          % ("PASS" if good else "FAIL", sum(1 for _, o, _ in gates if o), len(gates),
             a.tag, pid, a.save, rnd_pre, rnd_post))
    print("context: gdb log %s; gdb script %s" % (lpath, gpath))
    if not window_ok:
        print("STATE: NEVER REACHED (no live control in a valid load window) -> exit 4")
        return 4
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
