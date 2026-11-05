#!/usr/bin/env python3
"""M273 - what does the row stride 188 mean? (NEXT_PROMPT box pick; settles M256 G5's OPEN row)

M256 settled statically: in FUN_00556690's worth test, esi = [ebp-0x18] = 2*region + 188*fac
(fold 0x558002-0x558026), read UNSCALED at 0x558452 (`mov ax,[edi+0x94eaa8]`, edi=esi) and the
region indexing SCALED at 0x5584aa (`mov cx,[edi*2+0x94eaa8]`, edi=[ebp-0x10]=region). The region
loop runs 1..127 (`inc ecx; cmp ecx,0x80`). The OPEN row: 188-B rows vs 2 B/region mean regions
94..127 at fac>=1 would pass into the NEXT faction's row - "a stride conflict the image cannot
settle; one live read of both indexings answers it".

THE TEST (one live window, both indexings):
  (a) the region COUNT, live and save-derived: DAT_0092ada4 (store 0x582110 = ((W+4)/5+1)/2 * H,
      M244) vs sim.save.region_len(save dims). If count < 94 the stride is not a conflict at all:
      rows hold exactly the map's regions and the 128-bound loop never reaches a spill.
  (b) silent bps at BOTH read sites printing row_addr, region, both loaded WORDs, round, cp;
      plus the CONTROL bp at the year store 0x51f554 (fires every round - a zero-event window is
      an instrument verdict, never a game answer, trap 1).
Gates: count live==save-derived; stride == 2*count; control fired; IF worth-site events: every
region < count, and for a paired (round,region) the two indexings load the SAME value and the
row offset sits at 2*region inside its row; zero site events = NOT-REACHED (exit 4), not a NO.
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

ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from sim import save as sosave  # noqa: E402  (pure decoder: allowed, no harness deps)

EVID = os.path.join(ROOT, "evidence")
SCRATCH = os.path.join(ROOT, "scratch")
G_AD9C, G_ADA0, G_ADA4 = 0x92AD9C, 0x92ADA0, 0x92ADA4
G_YEAR = 0x985B00
RND, CPP = "*(int *)0x985afc", "*(int *)0x985dcc"
ROW_STRIDE, BASE = 188, 0x94EAA8
CTRL_YEARS = 0x51F554
TMPL = r"""set pagination off
set confirm off
@@BLOCKS@@printf "ARMED @@NB@@ silent bps\n"
continue
"""
BPU = r"""break *@@PC@@
commands
silent
printf "@@LINE@@\n"@@ARGS@@
continue
end
"""
KV = re.compile(r"^(M273[SW]) (\w+)((?: [a-z][a-z0-9_]*=-?\S+)+) round=(-?\d+) cp=(\d+)\s*$")
OK_LINE = re.compile(r"^(ARMED |0x[0-9a-f]+ in |\[New LWP |\[LWP |\[Thread |\[Switching to |"
                     r"Thread \d+ |This is not |^\$[0-9]+ = |^Continue|^\^|warning:|"
                     r"Cannot breakpoint|\[Inferior \d+ |This GDB supports |\s+<https://|"
                     r"Enable debuginfod|Debuginfod has|To make this setting |"
                     r"Breakpoint \d+ at |Delete the |$)")


def gdb_script():
    blocks = []
    # after the 6-B load at 0x558452: edi=row_addr(=esi), eax=WORD[base+row]
    line = "M273S UNSCALED row=0x%x reg=%d w=%d round=%d cp=%d"
    args = ["$edi", "*(int *)($ebp-0x10)", "$eax & 0xffff", RND, CPP]
    blocks.append(BPU.replace("@@PC@@", "0x558459").replace("@@LINE@@", line)
                  .replace("@@ARGS@@", "".join(", " + x for x in args)))
    # after the 8-B load at 0x5584aa: edi=region, ecx=WORD[base+2*region]
    line = "M273S SCALED row=0x%x reg=%d w=%d round=%d cp=%d"
    args = ["$edi*2", "*(int *)($ebp-0x10)", "$ecx & 0xffff", RND, CPP]
    blocks.append(BPU.replace("@@PC@@", "0x5584b1").replace("@@LINE@@", line)
                  .replace("@@ARGS@@", "".join(", " + x for x in args)))
    line = "M273W YEAR new=%d round=%d cp=%d"
    args = ["*(unsigned short *)0x985b00", RND, CPP]
    blocks.append(BPU.replace("@@PC@@", "%#x" % CTRL_YEARS).replace("@@LINE@@", line)
                  .replace("@@ARGS@@", "".join(", " + x for x in args)))
    return TMPL.replace("@@BLOCKS@@", "".join(blocks)).replace("@@NB@@", str(len(blocks)))


def parse(text):
    ev, bad = [], []
    for ln in text.split("\n"):
        ln = ln.rstrip()
        if not ln:
            continue
        m = KV.match(ln)
        if m:
            d = {"kind": m.group(2), "tag": m.group(1)}
            for tok in m.group(3).split():
                k, v = tok.split("=", 1)
                d[k] = int(v, 16) if v.startswith("0x") else int(v)
            d["round"], d["cp"] = int(m.group(4)), int(m.group(5))
            ev.append(d)
        elif not OK_LINE.match(ln):
            bad.append(ln)
    return ev, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m273w1")
    ap.add_argument("--sav", default="programs/saves/m54b_clean.SAV")
    ap.add_argument("--timeout", type=int, default=420)
    a = ap.parse_args()

    gpath = os.path.join(SCRATCH, "%s.gdb" % a.tag)
    lpath = os.path.join(EVID, "%s.gdblog" % a.tag)
    open(gpath, "w").write(gdb_script())

    pid = M.find_pid()
    with open("/proc/%d/mem" % pid, "rb", 0) as mm:
        ad9c, ada0, ada4 = [struct.unpack("<i", M.rd(mm, g, 4))[0]
                            for g in (G_AD9C, G_ADA0, G_ADA4)]
        year0 = struct.unpack("<H", M.rd(mm, G_YEAR, 2))[0]
    sv = sosave.parse(os.path.join(ROOT, a.sav))
    count_pred = ((sv.width + 4) // 5 + 1) // 2 * ((sv.height + 4) // 5)
    print("live: ad9c=%d ada0=%d COUNT=%d year=%d | save %s: %dx%d region_len=%d"
          % (ad9c, ada0, ada4, year0, os.path.basename(a.sav), sv.width, sv.height,
             sv.region_bytes), flush=True)

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
        raise SystemExit("gdb did not arm:\n" + head[-800:])
    print("armed: %d Breakpoint lines" % head.count("Breakpoint "), flush=True)

    env = dict(os.environ, DISPLAY=":99")
    drv = subprocess.run([sys.executable, os.path.join(HERE, "m55_boundary.py"),
                          "--timeout", str(a.timeout)],
                         capture_output=True, text=True, env=env, timeout=a.timeout + 90)
    print("driver rc=%d" % drv.returncode, flush=True)
    for ln in (drv.stdout or "").strip().splitlines()[-4:]:
        print("  drv: " + ln[:140], flush=True)
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
    sites = [e for e in ev if e["kind"] in ("UNSCALED", "SCALED")]
    ctrl = [e for e in ev if e["kind"] == "YEAR"]
    with open(os.path.join(SCRATCH, "%s_seq.jsonl" % a.tag), "w") as fh:
        for e in ev:
            fh.write(json.dumps(e) + "\n")
    with open("/proc/%d/mem" % pid, "rb", 0) as mm:
        year1 = struct.unpack("<H", M.rd(mm, G_YEAR, 2))[0]
        ada4_post = struct.unpack("<i", M.rd(mm, G_ADA4, 4))[0]
    tracer = subprocess.run(["grep", "-m1", "TracerPid", "/proc/%d/status" % pid],
                            capture_output=True, text=True).stdout.split()[-1]

    gates = []

    def gate(name, ok, detail):
        gates.append((name, bool(ok), detail))

    gate("G1-count-live-eq-savederived", ada4 == count_pred and ada4_post == ada4,
         "live COUNT=%d (pre AND post) == ((%d+4)/5+1)/2*%d = %d"
         % (ada4, sv.width, (sv.height + 4) // 5, count_pred))
    gate("G2-stride-is-2x-count", ROW_STRIDE == 2 * ada4,
         "188 == 2 * %d: a faction row holds EXACTLY the map's %d region slots" % (ada4, ada4))
    gate("G3-control-fired", bool(ctrl),
         "%d YEAR events at 0x51f554 (window live), year %d -> %d" % (len(ctrl), year0, year1))
    regs = [e["reg"] for e in sites]
    gate("G4-regions-under-count", (not sites) or all(1 <= r < ada4 for r in regs),
         "%d site events, region range %s (count %d)"
         % (len(sites), (min(regs), max(regs)) if regs else "n/a", ada4))
    pairs = {}
    for e in sites:
        pairs.setdefault((e["round"], e["reg"]), {})[e["kind"]] = e
    agree, checked, spills = True, 0, []
    for (rd, rg), pr in sorted(pairs.items()):
        if "UNSCALED" in pr and "SCALED" in pr:
            checked += 1
            u, s = pr["UNSCALED"], pr["SCALED"]
            if u["w"] != s["w"]:
                agree = False
            if u["row"] % ROW_STRIDE != 2 * rg:
                spills.append("r%d reg%d row%%188=%d want %d"
                              % (rd, rg, u["row"] % ROW_STRIDE, 2 * rg))
    gate("G5-two-indexings-agree", (not sites) or (agree and checked > 0 and not spills),
         "%d paired (round,region) observations; values agree=%s; row%%188==2*region violations %s"
         % (checked, agree, spills[:3]))
    gate("G6-zero-unparsed", not bad, "%d unparsed %s" % (len(bad), bad[:3]))
    gate("G7-tracer-zero", tracer == "0", "TracerPid=%s" % tracer)

    print("--- events: %d SITE %d CTRL ---" % (len(sites), len(ctrl)), flush=True)
    for e in sites[:16]:
        print("  %s r%d reg=%d row=0x%x w=%d" % (e["kind"], e["round"], e["reg"],
                                                 e["row"], e["w"]), flush=True)
    good = True
    for name, ok, detail in gates:
        good = good and ok
        print("%-30s %s  %s" % (name, "PASS" if ok else "FAIL", detail))
    print("ACCEPTANCE M273 %s %d/%d  (tag %s, pid %d, count %d)"
          % ("PASS" if good else "FAIL", sum(1 for _, o, _ in gates if o), len(gates),
             a.tag, pid, ada4))
    print("context: gdb log %s; gdb script %s" % (lpath, gpath))
    if not sites:
        print("STATE: worth sites NEVER REACHED (control fired; the counts still settle the "
              "pick offline) -> exit 4")
        return 4
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
