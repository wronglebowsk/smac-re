#!/usr/bin/env python3
"""M84b acceptance: does Escape on the item chooser arm the cancel sentinel and make
0x496ad0 return -9999 (0xffffd8f1), routing 0x417ee0 into the snapshot-restore block?

WHAT s129's m84canc1 got wrong (checked against instruction bytes BEFORE this run):
  B1 the ARM site 0x496a43 is `mov DWORD PTR [eax+0xa774],0xffffffff` with
     `mov eax,[ebp-0x4]` at 0x496a40 -- the object is in EAX, not ECX. m84canc1 printed
     $ecx, which was 0, so gdb faulted on 0xa774, aborted the command block and DETACHED
     the inferior: the run ended at the ARM and never reached the next gate.
  B2 the gate 0x497683 is `mov ecx,[ebp-0x10]` / `cmp [ecx+0xa774],-1` and 0x496af1 is
     `mov [ebp-0x10],ecx` -- the field lives on the THISCALL object the caller hands in
     ecx at 0x41860a (`lea ecx,[ebx+0xa1c]` = 0x6a9e9c, the chooser sub-object of the
     static pane 0x6a9480), NOT on the 24 KB `[ebp-0x5e2c]` buffer the caller pushes at
     0x418601. That retracts M84's "ecx = the buffer the caller passes" wording.
  B3 the sentinel is NEGATIVE: 0xffffd8f1 = -9999. m84canc1 gated on edi == 9999, so even
     a correct run would have failed. Every sentinel read below is the unsigned constant.

STATIC PREDICTIONS (bytes, computed before the run):
  P1 0x497680 gate: cancel==-1 (0x497683) AND [obj+0xa778]==0 (0x49768f) -> 0x4976ce stores
     0xffffd8f1 as the return; cancel==-1 with mode!=0 -> 0 (0x497698); cancel!=-1 -> the
     item-list number via 0x497704 `call [eax+8]`-style pump path.
  P2 -1 is written ONLY at 0x496a43 (chooser bar handler 0x496950, jump-table param -2 =
     CANCEL: stores -1 and NOTHING else) and 0x495541 (the modal's own setup).
  P3 the caller 0x417ee0 tests the return at 0x41861b (`cmp edi,0xffffd8f1`) and the
     snapshot-restore block at 0x418d7d is entered only on that equality; 0x418d8a is the
     sole call of 0x577280, returning to 0x418d8f.
Falsifiable claim: Escape -> ARM(obj=0x6a9e9c, pre != -1) -> GATE(cancel==-1) on the same
object -> SENT edi==0xffffd8f1 -> BRANCH -> ENTRY, in that order, in ONE invocation.
"""
import argparse, os, re, signal, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import m74_flag_watch as F

ROOT, EVID = F.ROOT, F.EVID
BASE_INDEX = 18            # Korolev Center
CELL_ITEM = 2
CHOOSER_SUB = 0x6a9e9c     # pane 0x6a9480 + 0xa1c, the ecx the caller passes at 0x41860a
SENTINEL = 0xffffd8f1      # -9999
ARMED = 0xffffffff         # -1 in the guard field

TMPL = r"""set pagination off
set confirm off
set height 0
set verbose off
break *0x41860a
commands
silent
printf "CALL obj=0x%x cancel=0x%x mode=%d slot=%d buf=0x%x\n", $ecx, *(int *)($ecx + 0xa774), *(int *)($ecx + 0xa778), *(int *)($esp + 0xc), *(int *)($esp + 8)
continue
end
break *0x41860f
commands
silent
printf "SENT edi=%d edi_hex=0x%x\n", $eax, $eax
continue
end
break *0x496a43
commands
silent
printf "ARM obj=0x%x pre=0x%x mode=%d ecx=0x%x\n", $eax, *(int *)($eax + 0xa774), *(int *)($eax + 0xa778), $ecx
continue
end
break *0x497683
commands
silent
printf "GATE obj=0x%x cancel=0x%x mode=%d\n", $ecx, *(int *)($ecx + 0xa774), *(int *)($ecx + 0xa778)
continue
end
break *0x418d7d
commands
silent
printf "BRANCH ptr=0x%x fac=%d edi=%d edi_hex=0x%x\n", *(int *)0x8f0d60, *(unsigned char *)(*(int *)0x8f0d60 + 4), $edi, $edi
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

LINE = re.compile(r"^(CALL|SENT|ARM|GATE|BRANCH|ENTRY|ARMED)\s*(.*)$")
KV = re.compile(r"(\w+)=(-?0x[0-9a-f]+|-*\d+)")
CHATTER = ("warning:", "Reading symbols", "0x", "Breakpoint", "[", "The program", "This GDB",
           "Enable debuginfod", "<https://debuginfod", "Debuginfod has been disabled",
           "To make this setting", "Thread ", "received signal SIGINT")


def val(s):
    return int(s, 16) if s.startswith(("-0x", "0x")) else int(s)


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
    ap.add_argument("--settle", type=float, default=6.0,
                    help="seconds to keep gdb attached after Escape (m84canc1 used 2)")
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
        m.seek(CHOOSER_SUB + 0xa774)
        cancel0, mode0 = struct.unpack("<ii", m.read(8))
    print(f"pid {pid} base ptr=0x{bptr:x} fac={fac0} pend={pend0} head={head0} "
          f"chooser_sub cancel=0x{cancel0:x} mode={mode0}", flush=True)

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
        time.sleep(a.settle)
        print(f"  Escape rc={esc} settled {a.settle}s", flush=True)

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
    print("ORDERED EVENTS (log order = time order):", flush=True)
    for i, (t, d) in enumerate(ev):
        print(f"  {i:2d} {t} {d}", flush=True)
    print("bad lines:", bad[:5], flush=True)

    def idx(pred):
        return [i for i, e in enumerate(ev) if pred(e)]

    arms = idx(lambda e: e[0] == "ARM" and e[1].get("obj") == CHOOSER_SUB)
    fresh = [i for i in arms if ev[i][1].get("pre") != ARMED]
    gates = idx(lambda e: e[0] == "GATE" and e[1].get("obj") == CHOOSER_SUB
                and e[1].get("cancel") == ARMED)
    sents = idx(lambda e: e[0] == "SENT" and e[1].get("edi_hex") == SENTINEL)
    branch = idx(lambda e: e[0] == "BRANCH")
    entry = idx(lambda e: e[0] == "ENTRY")
    res = {
        "G1 ARM fired on the chooser_sub 0x6a9e9c": len(arms) >= 1,
        "G2 a GATE on that object saw cancel==0xffffffff": len(gates) >= 1,
        "G3 a SENT returned edi==0xffffd8f1": len(sents) >= 1,
        "G4 BRANCH count == count(edi==0xffffd8f1)": len(branch) == len(sents)
                                                   and len(sents) >= 1,
        "G5 ENTRY count == BRANCH count": len(entry) == len(branch) and len(branch) >= 1,
        "G6 every ENTRY shows ret=0x418d8f p2==1": bool(entry) and all(
            ev[i][1].get("ret") == 0x418d8f and ev[i][1].get("p2") == 1 for i in entry),
        "G7 order ARM < GATE(-1) < SENT(-9999) < BRANCH < ENTRY": bool(arms) and any(
            a_ < g_ < s_ < b_ < e_ for a_ in arms for g_ in gates for s_ in sents
            for b_ in branch for e_ in entry),
        "G8 the ARM transitioned the field (pre != 0xffffffff)": len(fresh) >= 1,
    }
    print("gates:", res, flush=True)
    if all(res.values()):
        print(f"PASS {a.tag}: Escape arms [0x6a9e9c+0xa774]=-1 at 0x496a43 and the chooser "
              f"modal 0x496ad0 then returns 0xffffd8f1 (-9999), which is what enters the "
              f"snapshot-restore block 0x418d7d and thunks 0x577280 at 0x418d8a", flush=True)
    else:
        print(f"FAIL {a.tag}: ARM on chooser_sub {len(arms)} (fresh {len(fresh)}), "
              f"GATE cancel==-1 {len(gates)}, SENT edi==0xffffd8f1 {len(sents)}, "
              f"BRANCH {len(branch)}, ENTRY {len(entry)}, "
              f"SENT edi values seen {sorted({e[1].get('edi') for e in ev if e[0]=='SENT'})}, "
              f"GATE cancels {sorted({e[1].get('cancel') for e in ev if e[0]=='GATE'})}",
              flush=True)


if __name__ == "__main__":
    main()
