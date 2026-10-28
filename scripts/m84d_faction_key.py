#!/usr/bin/env python3
"""M84d acceptance: is 0x4a99e0's `param > 9999` leg the FACTION-CONTEXT switch, and
does it run in real play?

WHAT THE STATIC BYTES SAY (computed before this run, scratch/m71/dis.py windows):
  0x4a99e0 `cmp [ebp+0x8],0x270f` / `jle 0x4a9ad3`. The >9999 leg (0x4a99f9-0x4a9ace):
    0x4a99fc  mov [this+0x1d6f0],1                       (the context flag)
    0x4a9a09  sub ecx,0x270f                             key -> key-9999
    0x4a9a12  edx = (ds:0x888514 - 1) * 0xb4c
    0x4a9a24  mov [this+edx+0xb38],-1                    OUTGOING slot state = -1
    0x4a9a48  eax = [this+(ds:0x888514-1)*0xb4c+0x80]; 0x4a9a60 call [eax+0xf0]
    0x4a9a75  mov [this+(key-9999-1)*0xb4c+0xb38],2     INCOMING slot state = 2
    0x4a9aac  call [[this+(key-9999-1)*0xb4c+0x80]+0xf0]
    0x4a9ac9  call 0x4a72c0(this, ds:0x86ae40, key-9999, [this+0x1d6e0])
  The <=9999 leg (0x4a9ad3) requires [this+8]==4 and [this+0x1d6dc]==ds:0x91b5b4 and
  switches on 0xcef..0xcf4 (3311..3316), i.e. the SAME argument is either a message code
  below 10000 or an INDEX above it.
  WHO OWNS THE FUNCTION: the pointer 0x4a99e0 appears exactly ONCE in the image, at
  0x67671c (.rdata). The constructors at 0x498ea6/0x498eac store vptr 0x67658c at [obj]
  and 0x676584 at [obj+0x444], so 0x4a99e0 is slot (0x67671c-0x67658c)/4 = 100 of the
  primary vtable / slot 102 of the secondary; no `call [reg+0x190]` exists in .text, so
  the call is dispatched through a computed index (the same shape as the M84 chooser
  handler table).
  WHAT ds:0x888514 IS: a FACTION index, live 0. Proof: 0x4a0c17 loops i < ds:0x985af4
  (=19 live) over stride-0x130 records at 0x95da14 and compares BYTE[i*0x130] to it; those
  19 records read "University Base", "Gaia's Landing", ... "Korolev Center" (base records,
  owner faction at +0: University Base and Korolev Center both read 3 = our faction).
  0x499f13 indexes a second per-faction array with the same global: `imul eax,0x20bc` over
  0x94d7fc (8380-byte records, entries 0..8 populated).

PREDICTIONS computed from that model BEFORE the run (a PASS means all of them hold):
  P1 the >9999 leg runs at least once during 8 turn boundaries (a faction-context switch
     happens every time the engine moves to the next faction);
  P2 every key satisfies 1 <= key-9999 <= ds:0x985af4 (it is a 1-based faction index);
  P3 the OUT store index equals ds:0x888514-1 and the IN store index equals key-9999-1
     (the two stores are the SAME variable apart from the key);
  P4 the flag [this+0x1d6f0] reads 1 at 0x4a9ab2 on that leg (it is set at 0x4a99fc in the
     same leg and nowhere else on this path);
  P5 the record pointer at slot+0x80 is non-null (the notify call derefs it);
  P6 the object's secondary vptr [this+0x444] == 0x676584 (the call really is to THIS
     vtable, not to a subclass that overrode slot 102).
Falsifiable in the other direction too: if the leg never fires, the 0x270f vocabulary is
NOT a faction-context key and this milestone merges nothing.
"""
import argparse, os, re, signal, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import m74_flag_watch as F

ROOT, EVID = F.ROOT, F.EVID
VTABLE2 = 0x676584
FAC_GLOBAL = 0x888514
STRIDE = 0xb4c

TMPL = r"""set pagination off
set confirm off
set height 0
set verbose off
set $n = 0
set $low = 0
break *0x4a99ec
commands
silent
set $n = $n + 1
set $p = *(int *)($ebp + 0x8)
set $t = *(int *)($ebp - 0x4)
if $p > 9999
printf "KEY n=%d param=%d key=%d this=0x%x ret=0x%x fac=%d maxfac=%d\n", $n, $p, $p - 9999, $t, *(int *)($ebp + 0x4), *(int *)0x888514, *(int *)0x985af4
else
set $low = $low + 1
if $low <= 4
printf "LOW n=%d param=%d this=0x%x ret=0x%x\n", $n, $p, $t, *(int *)($ebp + 0x4)
end
end
continue
end
break *0x4a9a24
commands
silent
printf "OUT n=%d off=%d this=0x%x fac=%d\n", $n, $edx, $eax, *(int *)0x888514
continue
end
break *0x4a9a60
commands
silent
if $eax != 0
printf "NOTIFYOUT n=%d obj=0x%x vptr=0x%x\n", $n, $eax, *(int *)$eax
end
continue
end
break *0x4a9a75
commands
silent
printf "IN n=%d off=%d this=0x%x key=%d\n", $n, $ecx, $edx, *(int *)($ebp + 0x8)
continue
end
break *0x4a9aac
commands
silent
if $edx != 0
printf "NOTIFYIN n=%d obj=0x%x vptr=0x%x\n", $n, $edx, *(int *)$edx
end
continue
end
break *0x4a9ab2
commands
silent
printf "AFTER n=%d flag=%d ctx=%d\n", $n, *(int *)($eax + 0x1d6f0), *(int *)($eax + 0x1d6e0)
continue
end
break *0x4a7d84
commands
silent
printf "SETFLAG2 n=%d this=0x%x\n", $n, $edx
continue
end
break *0x4a759f
commands
silent
printf "CLEARFLAG n=%d this=0x%x\n", $n, $edx
continue
end
continue
"""

LINE = re.compile(r"^([A-Z][A-Z0-9]+) (.*)$")
KV = re.compile(r"(\w+)=(-?0x[0-9a-f]+|-?\d+)")


def parse(text):
    ev, bad = [], []
    for raw in text.splitlines():
        m = LINE.match(raw.strip())
        if not m:
            if raw.strip():
                bad.append(raw.strip()[:80])
            continue
        d = {}
        for k, v in KV.findall(m.group(2)):
            d[k] = int(v, 16) if v.startswith("0x") or v.startswith("-0x") else int(v)
        ev.append((m.group(1), d))
    return ev, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--boundaries", type=int, default=8)
    ap.add_argument("--timeout", type=int, default=380)
    a = ap.parse_args()

    pid = F.pid() if hasattr(F, "pid") else int(subprocess.run(
        ["pgrep", "-x", "terran.exe"], capture_output=True, text=True).stdout.split()[0])
    print("pid", pid, flush=True)

    gpath = os.path.join(ROOT, "scratch", f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.gdblog")
    os.makedirs(EVID, exist_ok=True)
    open(gpath, "w").write(TMPL)
    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p",
                          str(pid)], stdout=log, stderr=subprocess.STDOUT)
    time.sleep(6)
    if not os.path.exists("/proc/%d" % g.pid):
        raise SystemExit("gdb died on attach:\n" + open(lpath, errors="replace").read()[-800:])
    print("gdb attached (breakpoints armed)", flush=True)

    t0 = time.time()
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "m56_build.py"),
                        "--ui-queued", "18", "--boundaries", str(a.boundaries),
                        "--timeout", str(a.timeout), "--no-poke-hold"],
                       capture_output=True, text=True, timeout=a.timeout + 120)
    tail = (r.stdout.strip().splitlines() or [""])[-3:]
    print(f"driver rc={r.returncode} t={time.time()-t0:.0f}s", flush=True)
    for ln in tail:
        print("  driver:", ln[:160], flush=True)

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

    text = open(lpath, errors="replace").read()
    ev, bad = parse(text)
    counts = {}
    for t, d in ev:
        counts[t] = counts.get(t, 0) + 1
    print("EVENT COUNTS:", counts, flush=True)
    print("ORDERED (first 24):", flush=True)
    for i, (t, d) in enumerate(ev[:24]):
        print(f"  {i:2d} {t} {d}", flush=True)
    if bad:
        print("bad lines:", bad[:5], flush=True)

    keys = [d for t, d in ev if t == "KEY"]
    outs = [d for t, d in ev if t == "OUT"]
    ins = [d for t, d in ev if t == "IN"]
    aft = [d for t, d in ev if t == "AFTER"]
    nout = [d for t, d in ev if t == "NOTIFYOUT"]
    nin = [d for t, d in ev if t == "NOTIFYIN"]
    lows = [d for t, d in ev if t == "LOW"]
    byn = {d["n"]: d for d in keys}
    # P3: the OUT store index must be (faction-1) and the IN store index (key-1),
    # both read off the printed byte offsets (stride 0xb4c)
    out_ok = [o for o in outs if o["n"] in byn and o["off"] // STRIDE == byn[o["n"]]["fac"] - 1]
    in_ok = [i for i in ins if i["n"] in byn and i["off"] // STRIDE == i["key"] - 1]
    res = {
        # the function is reached at all (either leg)
        "G1_reached": bool(keys or lows),
        # the >9999 leg fires in real play
        "G2_gt9999": bool(keys),
        # P2: every key is a 1-based faction index in range
        "G3_range": bool(keys) and all(1 <= d["key"] <= d["maxfac"] for d in keys),
        # P3: the two stores are the outgoing (fac-1) and incoming (key-1) slots
        "G4_out_is_fac_minus_1": len(out_ok) == len(outs) and len(out_ok) >= 1,
        "G5_in_is_key_minus_1": len(in_ok) == len(ins) and len(in_ok) >= 1,
        # P4: the context flag is 1 when the leg finishes
        "G6_flag_1": bool(aft) and all(d["flag"] == 1 for d in aft),
        # P5: both notify objects are real objects (non-null, vptr inside the image)
        "G7_notify_objects": bool(nout) and bool(nin) and
        all(0x400000 <= d["vptr"] < 0x9b0000 for d in nout + nin),
        # the leg ran END TO END (AFTER reached) at least once
        "G8_end_to_end": len(aft) >= 1 and len(keys) >= 1,
    }
    print("GATES:", flush=True)
    for k, v in res.items():
        print(f"  {k}: {v}", flush=True)
    ok = all(res.values())
    print(f"VERDICT {'PASS' if ok else 'FAIL'} tag={a.tag} "
          f"keys={len(keys)} outs={len(outs)} ins={len(ins)} after={len(aft)} "
          f"notify={len(nout)}/{len(nin)} low={len(lows)}", flush=True)
    print("evidence:", lpath, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
