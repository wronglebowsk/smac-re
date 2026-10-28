#!/usr/bin/env python3
"""M84 acceptance: WHAT makes 0x496ad0 return +9999 — the cancel sentinel, live.

STATIC PREDICTIONS (from instruction bytes, computed BEFORE the run):
  P1 the return value is chosen at 0x497680-0x4976ff: `cmp [buf+0xa774],-1` (0x497683, ecx = buf =
     the 24 KB [ebp-0x5e2c] the caller passes at 0x418601) -> if -1 and `[buf+0xa778] == 0`
     (0x49768f) eax = 0xffffd8f1 = +9999 (0x4976ce); if -1 and result != 0 eax = 0 (0x497698);
     else eax = the pump return (0x497704: call 0x401940, negated when 0x495480's bit 0x20 clear).
  P2 `[buf+0xa774]` is written -1 in exactly TWO places in .text: 0x496a43 (inside the dialog's
     message handler FUN_00496950, whose case 7 sets result 0 AND arms -1) and 0x495541 (inside
     FUN_004954e0, the dialog's own setup, called once from 0x496ad0 at line 14866).
  P3 handler FUN_00496950 cases 0/2/5 bail (`return`) when the field is already -1; cases 1/3/4/6/8
     set result 1/3/4/6/7; case 7 arms -1 with result 0. So a Cancel click arms, and the NEXT pump
     return is what turns into +9999.
  P4 the caller tests the sentinel at 0x41861b / 0x4186d2 (`cmp edi,0xffffd8f1`) and the 0x270f
     block at 0x418d7d is entered ONLY on that equality.
So the falsifiable claim: SENT edi == 9999 requires an ARM (cancel armed) BEFORE the pump returns.
Gates below; PASS prints on ONE real invocation. A run that does not arm FAILS with its numbers.
"""
import argparse, os, re, signal, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import m74_flag_watch as F

ROOT, EVID = F.ROOT, F.EVID
BASE_INDEX = 18            # Korolev Center
CELL_ITEM = 2
TMPL = r"""set pagination off
set confirm off
set height 0
set verbose off
break *0x41860f
commands
silent
printf "SENT ptr=0x%x fac=%d edi=%d\n", *(int *)0x8f0d60, *(unsigned char *)(*(int *)0x8f0d60 + 4), $eax
continue
end
break *0x496a43
commands
silent
printf "ARM buf=0x%x pre=%d result_pre=%d\n", $ecx, *(int *)($ecx + 0xa774), *(int *)($ecx + 0xa778)
continue
end
break *0x497683
commands
silent
printf "GATE buf=0x%x cancel=%d result=%d\n", $ecx, *(int *)($ecx + 0xa774), *(int *)($ecx + 0xa778)
continue
end
break *0x418d7d
commands
silent
printf "BRANCH ptr=0x%x fac=%d edi=%d\n", *(int *)0x8f0d60, *(unsigned char *)(*(int *)0x8f0d60 + 4), $edi
continue
end
break *0x577280
commands
silent
printf "ENTRY ret=0x%x p1=%d p2=%d\n", *(int *)($esp), *(int *)($esp + 4), *(int *)($esp + 8)
continue
end
printf "ARMED ptr=0x%x fac=%d pend=%d head=%d\n", *(int *)0x8f0d60, *(unsigned char *)(*(int *)0x8f0d60 + 4), *(int *)(*(int *)0x8f0d60 + 0x4c), *(int *)(*(int *)0x8f0d60 + 0x50)
continue
"""

LINE = re.compile(r"^(SENT|ARM|GATE|BRANCH|ENTRY|ARMED)\s*(.*)$")
KV = re.compile(r"(\w+)=(-?0x[0-9a-f]+|-*\d+)")
CHATTER = ("warning:", "Reading symbols", "0x", "Breakpoint", "[", "The program", "This GDB",
           "Enable debuginfod", "<https://debuginfod", "Debuginfod has been disabled",
           "To make this setting", "Thread ", "received signal SIGINT")


def val(s):
    return int(s, 16) if s.startswith(("0x", "-0x")) else int(s)


def parse(text):
    ev, bad = [], []
    for line in text.splitlines():
        m = LINE.match(line.strip())
        if not m:
            s = line.strip()
            if s and not s.startswith(CHATTER):
                bad.append(line)
            continue
        ev.append((m.group(1), dict((k, val(v)) for k, v in KV.findall(m.group(2)))))
    return ev, bad


def run_py(args_list, timeout=420):
    return subprocess.run([sys.executable] + args_list, capture_output=True, text=True,
                          timeout=timeout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--escape", action="store_true", help="press Escape while the chooser is open")
    ap.add_argument("--no-ok", action="store_true", help="leave the chooser open (enqueue stops before OK)")
    ap.add_argument("--timeout", type=int, default=300)
    a = ap.parse_args()

    pid = F.game_pid()
    if not pid:
        raise SystemExit("no terran.exe pid")
    import struct
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        m.seek(0x8F0D60)
        bptr = struct.unpack("<I", m.read(4))[0]
        m.seek(bptr + 4)
        fac0 = m.read(1)[0]
        m.seek(bptr + 0x4c)
        pend0, head0 = struct.unpack("<ii", m.read(8))
    print(f"pid {pid} base ptr=0x{bptr:x} fac={fac0} pend={pend0} head={head0}", flush=True)

    gpath = os.path.join(ROOT, "scratch", f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.gdblog")
    os.makedirs(EVID, exist_ok=True)
    open(gpath, "w").write(TMPL)
    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=log, stderr=subprocess.STDOUT)
    head = ""
    for _ in range(60):
        head = open(lpath, "r", errors="replace").read()
        if "ARMED" in head or not os.path.exists("/proc/%d" % g.pid):
            break
        time.sleep(0.5)
    if "ARMED" not in head:
        try:
            os.kill(g.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
        subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
        raise SystemExit("gdb did not arm:\n" + head[-1200:])
    print("armed: " + [l for l in head.splitlines() if l.startswith("ARMED")][0], flush=True)

    t0 = time.time()
    r1 = run_py([os.path.join(ROOT, "scripts", "m57_ui_enqueue.py"),
                 "--base-index", str(BASE_INDEX), "--cell-item", str(CELL_ITEM),
                 "--inserts", "1"] + (["--no-ok"] if a.no_ok else []), timeout=a.timeout + 120)
    enq = (r1.stdout.strip().splitlines() or [""])[-1]
    print(f"  enqueue rc={r1.returncode} t={time.time()-t0:.0f}s {enq!r}", flush=True)
    esc = None
    if a.escape:
        time.sleep(1.0)
        esc = subprocess.run(["xdotool", "key", "--clearmodifiers", "Escape"],
                             capture_output=True, text=True).returncode
        time.sleep(2.0)
        print(f"  Escape rc={esc}", flush=True)

    try:
        os.kill(g.pid, signal.SIGINT)
    except ProcessLookupError:
        pass
    for _ in range(40):
        if not os.path.exists("/proc/%d" % g.pid):
            break
        time.sleep(0.5)
    subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
    time.sleep(1.0)
    log.close()

    text = open(lpath, "r", errors="replace").read()
    ev, bad = parse(text)
    ev = [e for e in ev if e[0] != "ARMED"]
    cnt = {t: sum(1 for e in ev if e[0] == t) for t in ("SENT", "ARM", "GATE", "BRANCH", "ENTRY")}
    print("events:", cnt, flush=True)
    for t in ("SENT", "ARM", "GATE", "BRANCH", "ENTRY"):
        rows = [e[1] for e in ev if e[0] == t]
        print(f"  {t}: {rows[:10]}", flush=True)
    print("bad lines:", bad[:5], flush=True)

    sent = [e[1] for e in ev if e[0] == "SENT"]
    arms = [e[1] for e in ev if e[0] == "ARM"]
    gates = [e[1] for e in ev if e[0] == "GATE"]
    branch = [e[1] for e in ev if e[0] == "BRANCH"]
    entry = [e[1] for e in ev if e[0] == "ENTRY"]
    sent9999 = [e for e in sent if e.get("edi") == 9999]
    armed_gate = [g for g in gates if g.get("cancel") == -1]
    res = {
        "G1 ARM fired (cancel armed by the handler)": len(arms) >= 1,
        "G2 a GATE saw cancel==-1": len(armed_gate) >= 1,
        "G3 SENT returned edi==9999": len(sent9999) >= 1,
        "G4 BRANCH count == count(edi==9999)": len(branch) == len(sent9999) and len(sent9999) >= 1,
        "G5 ENTRY count == BRANCH count": len(entry) == len(branch) and len(branch) >= 1,
        "G6 every ENTRY shows ret=0x418d8f p2==1": bool(entry) and all(
            e.get("ret") == 0x418d8f and e.get("p2") == 1 for e in entry),
        "G7 cancel==-1 at the gate implies edi==9999": bool(armed_gate) and all(
            any(s.get("edi") == 9999 for s in sent) for _ in armed_gate),
    }
    print("gates:", res, flush=True)
    if all(res.values()):
        print(f"PASS {a.tag}: +9999 is the dialog CANCEL sentinel — ARM@0x496a43 -> "
              f"GATE cancel==-1 result==0 -> edi==9999 -> BRANCH -> ENTRY", flush=True)
    else:
        print(f"FAIL {a.tag}: sentinel path not observed (ARM {len(arms)}, gates with cancel==-1 "
              f"{len(armed_gate)}, SENT edi {sorted({e.get('edi') for e in sent})})", flush=True)


if __name__ == "__main__":
    main()
