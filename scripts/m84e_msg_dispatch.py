#!/usr/bin/env python3
"""M84e acceptance: widget message 0x4d00 is POSTED by the chooser tail 0x417ee0 into the
queue object 0x91db70 and DISPATCHED later by the switch in 0x52bce0 (arm 0x52eb61 ->
handler 0x52ed7d); the cursor zero at 0x4194b3 is in the SENDER, not in that handler.

STATIC (instruction bytes, scratch/m71/dis.py windows, computed BEFORE arming):
  S1 0x584010 is not a dispatcher: it builds a 32-byte record on ITS OWN stack
     ([ebp-0x20]: +0 WORD code, +4 ds:0x91b5b4, +8 the 0x671368 result, +0xc ds:0x91f694,
     +0x10..+0x1c the sender's args 2..5) and posts it: `push [ebp+0xc]; push 0x20;
     push &record; mov ecx,0x91db70; call 0x52a260` under the re-entrancy guard
     inc/dec ds:0x920438. So a send is asynchronous by construction.
  S2 the pumps pop it back: 0x5262ff/0x52633f/... `mov ecx,0x91db70; call 0x6361ff`,
     `test eax,eax; je` else `push edx; push ecx; push eax; mov ecx,esi; call 0x52bce0`.
  S3 0x52bce0 IS the dispatcher: 0x52bd33 `mov ebx,[ebp+0x8]` = the record, 0x52bd3b
     `mov ax,WORD PTR [ebx]` = the code; 53 `cmp eax,0x...` arms; the 0x4d00 arm is
     0x52eb61 `cmp eax,0x4d00` / 0x52eb66 `jg 0x52ef74` / 0x52eb6c `je 0x52ed7d`, so a
     breakpoint at 0x52eb6c can ONLY be reached with eax == 0x4d00 (a greater value left
     at 0x52eb66, a lesser one falls through with ZF clear).
  S4 the handler 0x52ed7d: eax=[ebx+0x10] (the sender's arg2 = 0xffffffd9 - edi, the -39
     sentinel), edi=[ebx+0x4] (player), then 0x52ed89 `lea edx,[eax+eax*2+0x75]` +
     0x52ed90 `shl edx,4` + 0x52ed97 `lea eax,[edx+0x984d38]` = 0x984d38 + a2*48 + 1872,
     and with a2 = -39-tid the +1872 (= 39*48) cancels the sentinel: 0x984d38 - tid*48.
     That is a THIRD stride-48 site for the M67 stride conflict (48 vs 16).
  S5 the handler 0x52ed7d-0x52f756 writes NOTHING at +0x3ff5c / 0x6e93dc (grep of the
     whole arm range), so M70's "a handler zeroes the cursor after sending 0x4d00" is
     wrong about the mechanism: 0x4194b3 `mov [ebx+0x3ff5c],0` is the instruction right
     after `call 0x584010` returns, in the SENDER 0x417ee0 (ebx = 0x2e9480).
Falsifiable claim, ONE invocation: POST(code=0x4d00, a2 = -39 - edi) at 0x4194a9 ->
ZERO(obj=0x2e9480, pre != 0) -> ZEROAFTER(post == 0) -> DISP(record code 0x4d00 with the
same a2) -> ARM(0x52eb6c) -> HND(0x52ed7d, same a2) -> IDX(record == 0x984d38 + a2*48 +
1872), in that order. Negative control: --no-ok leaves the chooser open, so no POST is
made and every gate must be False.
"""
import argparse, os, re, signal, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import m74_flag_watch as F

ROOT, EVID = F.ROOT, F.EVID
BASE_INDEX = 18            # Korolev Center (m57's index into 0x95da10, stride 304)
CELL_ITEM = 2
CURSOR_OBJ = 0x2e9480      # 0x6e93dc - 0x3ff5c, the object 0x417ee0 holds in ebx
CURSOR_G = 0x6e93dc
MSG_CODE = 0x4d00
SENT39 = 0xffffffd9        # -39
TABLE = 0x984d38

TMPL = r"""set pagination off
set confirm off
set height 0
set verbose off
break *0x4194a9
commands
silent
printf "POST code=%d a1=%d a2=%d mode=%d a4=%d a5=%d edi=%d edi_hex=0x%x\n", *(int *)($esp), *(int *)($esp + 4), *(int *)($esp + 8), *(int *)($esp + 0xc), *(int *)($esp + 0x10), *(int *)($esp + 0x14), $edi, $edi
continue
end
break *0x4194b3
commands
silent
printf "ZERO obj=0x%x pre=%d pre_hex=0x%x\n", $ebx, *(int *)($ebx + 0x3ff5c), *(int *)($ebx + 0x3ff5c)
continue
end
break *0x4194bd
commands
silent
printf "ZEROAFTER obj=0x%x post=%d\n", $ebx, *(int *)($ebx + 0x3ff5c)
continue
end
break *0x52bd3b if *(short *)$ebx == 0x4d00
commands
silent
printf "DISP rec=0x%x code=%d player=%d a10=%d a14=%d a18=%d\n", $ebx, *(short *)$ebx, *(int *)($ebx + 4), *(int *)($ebx + 0x10), *(int *)($ebx + 0x14), *(int *)($ebx + 0x18)
continue
end
break *0x52eb6c
commands
silent
printf "ARM eax=%d eax_hex=0x%x\n", $eax, $eax
continue
end
break *0x52ed7d
commands
silent
printf "HND rec=0x%x code=%d player=%d a10=%d a14=%d a18=%d\n", $ebx, *(short *)$ebx, *(int *)($ebx + 4), *(int *)($ebx + 0x10), *(int *)($ebx + 0x14), *(int *)($ebx + 0x18)
continue
end
break *0x52eda4
commands
silent
printf "IDX rec=0x%x a2=%d a4=%d\n", $eax, *(int *)($ebx + 0x10), *(int *)($ebx + 0x18)
continue
end
printf "ARMED pend=%d head=%d cursor=%d bps=%d\n", *(int *)(*(int *)0x8f0d60 + 0x4c), *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)0x6e93dc, 7
continue
"""

LINE = re.compile(r"^(POST|ZEROAFTER|ZERO|DISP|ARM|HND|IDX|ARMED)\s*(.*)$")
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


def rec_pred(a2):
    """0x52ed89/0x52ed90/0x52ed97: edx = (a2*3 + 0x75) << 4; rec = 0x984d38 + edx."""
    edx = ((a2 * 3 + 0x75) << 4) & 0xffffffff
    return (TABLE + edx) & 0xffffffff


def gates(ev):
    def idx(pred):
        return [i for i, e in enumerate(ev) if pred(e)]
    posts = idx(lambda e: e[0] == "POST" and e[1].get("code") == MSG_CODE)
    zeros = idx(lambda e: e[0] == "ZERO" and e[1].get("obj") == CURSOR_OBJ)
    after = idx(lambda e: e[0] == "ZEROAFTER" and e[1].get("post") == 0)
    arms = idx(lambda e: e[0] == "ARM")
    hnds = idx(lambda e: e[0] == "HND" and e[1].get("code") == MSG_CODE)
    idxs = idx(lambda e: e[0] == "IDX")
    disp = []
    for p in posts:
        a2 = ev[p][1].get("a2")
        disp += [d for d in idx(lambda e: e[0] == "DISP" and e[1].get("a10") == a2) if d > p]
    disp = sorted(set(disp))
    res = {
        "G1 the sender 0x417ee0 executed its post site 0x4194a9 with code 0x4d00": len(posts) >= 1,
        "G2 the posted arg2 == 0xffffffd9 - edi (the -39 sentinel arithmetic at 0x41949f)":
            len(posts) >= 1 and any((ev[e][1].get("a2") - (SENT39 - ev[e][1].get("edi"))) % 2**32 == 0
                                    and ev[e][1].get("a1") == 0 and ev[e][1].get("mode") in (0, 1, 2)
                                    for e in posts),
        "G3 the cursor store at 0x4194b3 is a real transition: obj 0x2e9480, pre != 0, read back 0":
            len(zeros) >= 1 and any(ev[e][1].get("pre") != 0 for e in zeros) and len(after) >= 1,
        "G4 the dispatcher 0x52bce0 saw a record with code 0x4d00 carrying the SAME a2": len(disp) >= 1,
        "G5 the 0x4d00 arm was TAKEN (0x52eb6c is reachable only with eax == 0x4d00)": len(arms) >= 1,
        "G6 the handler entry is 0x52ed7d (HND fired with record code 0x4d00 and the same a2)":
            len(hnds) >= 1 and any(ev[h][1].get("a10") == ev[p][1].get("a2")
                                   for h in hnds for p in posts[:1]),
        "G7 the handler's record == 0x984d38 + a2*48 + 1872 (stride 48, sentinel cancels +1872)":
            len(idxs) >= 1 and any(ev[e][1].get("rec") == rec_pred(ev[e][1].get("a2")) for e in idxs),
        "G8 ORDER POST < ZERO < ZEROAFTER < DISP < ARM < HND < IDX (post-then-dispatch, one thread)":
            len(posts) >= 1 and len(zeros) >= 1 and len(after) >= 1 and len(disp) >= 1
            and len(arms) >= 1 and len(hnds) >= 1 and len(idxs) >= 1
            and max(posts) < min(zeros) < min(after) < min(disp) < min(arms) < min(hnds) < min(idxs),
    }
    return res, posts, zeros, after, disp, arms, hnds, idxs


def run_py(args_list, timeout=420):
    return subprocess.run([sys.executable] + args_list, capture_output=True, text=True,
                          timeout=timeout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--no-ok", action="store_true", help="NEGATIVE CONTROL: leave the chooser open")
    ap.add_argument("--settle", type=float, default=10.0)
    ap.add_argument("--timeout", type=int, default=240)
    a = ap.parse_args()

    if a.tag == "selftest":
        pos = ("ARMED pend=1 head=2 cursor=3 bps=7\n"
               "POST code=19712 a1=0 a2=-42 mode=0 a4=0 a5=0 edi=3 edi_hex=0x3\n"
               "ZERO obj=0x2e9480 pre=4 pre_hex=0x4\nZEROAFTER obj=0x2e9480 post=0\n"
               "DISP rec=0xbe3900 code=19712 player=3 a10=-42 a14=0 a18=0\n"
               "ARM eax=19712 eax_hex=0x4d00\n"
               "HND rec=0xbe3900 code=19712 player=3 a10=-42 a14=0 a18=0\n"
               "IDX rec=0x%x a2=-42 a4=0\n" % rec_pred(-42))
        neg = ("ARMED pend=1 head=2 cursor=3 bps=7\n"
               "ZERO obj=0x2e9480 pre=4 pre_hex=0x4\nZEROAFTER obj=0x2e9480 post=0\n"
               "DISP rec=0xbe3900 code=8449 player=3 a10=-42 a14=0 a18=0\n"
               "HND rec=0xbe3900 code=8449 player=3 a10=-42 a14=0 a18=0\n"
               "IDX rec=0x984d38 a2=-42 a4=0\n")
        for name, text, want in (("positive", pos, True), ("negative", neg, False)):
            res, *_ = gates(parse(text)[0])
            got = all(res.values())
            print(f"selftest {name}: all_gates={got} want={want} "
                  f"{ {k.split()[0]: v for k, v in res.items()} }", flush=True)
            if got != want:
                raise SystemExit(f"SHAPE DOES NOT DISCRIMINATE ({name})")
        print("PASS selftest: the shape separates a 0x4d00 dispatch from a 0x2101 one", flush=True)
        return

    pid = F.game_pid()
    if not pid:
        raise SystemExit("no terran.exe pid")
    import struct
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        m.seek(0x8F0D60)
        bptr = struct.unpack("<I", m.read(4))[0]
        m.seek(bptr + 0x4c)
        pend0, head0 = struct.unpack("<ii", m.read(8))
        m.seek(CURSOR_G)
        cur0 = struct.unpack("<i", m.read(4))[0]
    print(f"pid {pid} base ptr=0x{bptr:x} pend={pend0} head={head0} cursor0={cur0}", flush=True)

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
    armed = [l for l in head.splitlines() if l.startswith("ARMED")][0]
    narm = len([l for l in head.splitlines() if l.startswith("Breakpoint ")])
    print(f"armed: {armed} (Breakpoint lines: {narm})", flush=True)

    t0 = time.time()
    r1 = run_py([os.path.join(ROOT, "scripts", "m57_ui_enqueue.py"),
                 "--base-index", str(BASE_INDEX), "--cell-item", str(CELL_ITEM),
                 "--inserts", "1"] + (["--no-ok"] if a.no_ok else []), timeout=a.timeout + 120)
    enq = (r1.stdout.strip().splitlines() or [""])[-1]
    print(f"  enqueue rc={r1.returncode} t={time.time()-t0:.0f}s {enq!r}", flush=True)
    time.sleep(a.settle)
    print(f"  settled {a.settle}s", flush=True)

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
    res, posts, zeros, after, disp, arms, hnds, idxs = gates(ev)
    print("gates:", flush=True)
    for k, v in res.items():
        print(f"  {'T' if v else 'F'} {k}", flush=True)
    print(f"counts: POST {len(posts)} ZERO {len(zeros)} ZEROAFTER {len(after)} DISP {len(disp)} "
          f"ARM {len(arms)} HND {len(hnds)} IDX {len(idxs)}; "
          f"POST a2 {sorted({ev[i][1].get('a2') for i in posts})} "
          f"edi {sorted({ev[i][1].get('edi') for i in posts})} "
          f"mode {sorted({ev[i][1].get('mode') for i in posts})}; "
          f"IDX rec {sorted(hex(ev[i][1].get('rec')) for i in idxs)} "
          f"pred {[hex(rec_pred(ev[i][1].get('a2'))) for i in idxs]}", flush=True)
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        m.seek(CURSOR_G)
        cur1 = struct.unpack("<i", m.read(4))[0]
        m.seek(0x8F0D60)
        bptr = struct.unpack("<I", m.read(4))[0]
        m.seek(bptr + 0x4c)
        pend1, head1 = struct.unpack("<ii", m.read(8))
    print(f"read-back after detach: cursor {cur0} -> {cur1}; pend {pend0} -> {pend1} "
          f"head {head0} -> {head1}", flush=True)
    if all(res.values()):
        print(f"PASS {a.tag}: message 0x4d00 is POSTED by 0x417ee0 (0x584010 -> queue 0x91db70) "
              f"with arg2 = -39 - <chooser key>, the pump hands the record to the switch 0x52bce0, "
              f"the 0x4d00 arm 0x52eb61/0x52eb6c takes it to the handler 0x52ed7d, whose record is "
              f"0x984d38 - key*48 (stride 48); the cursor zero at 0x4194b3 is in the SENDER and "
              f"lands before the dispatch", flush=True)
    else:
        print(f"FAIL {a.tag}: POST {len(posts)} ZERO {len(zeros)} ZEROAFTER {len(after)} "
              f"DISP {len(disp)} ARM {len(arms)} HND {len(hnds)} IDX {len(idxs)} — "
              f"the 0x4d00 send->dispatch chain did not close", flush=True)


if __name__ == "__main__":
    main()
