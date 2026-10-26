#!/usr/bin/env python3
"""M57-2: who writes base+0x40 (mineral storage) across a round boundary, and in what order?

A hardware watchpoint on the base's +0x40, armed with gdb in the background (the
m53g_drive pattern: attach, log, SIGINT-detach, kill -CONT). While gdb is attached we
make NO memory writes (pokes lie under a tracer — smac_play.py M33 note) and we press
no keys except the sampler's periodic Return (the M55 finding: Return while the walk is
mid-flight or parked on our turn is consumed as dismiss/turn-end; with every one of our
records HELD the engine auto-ends our turn anyway).

Modes (run them as SEPARATE invocations — one variable at a time):
  --mode queue : leave the queue exactly as the game left it (Korolev Center carries a
                 real UI-queued Scout Patrol: pending 1, head 2, storage 5, d0 2).
                 Measures the accrual AND the completion stores.
  --mode empty : BEFORE attaching, empty the queue (pending 0, head/slots -38) and read
                 it back; then watch. Tests the disasm gate at 0x4ef7e5
                 (`cmp [eax+0x50],0xffffffda; je skip`): an empty queue must produce
                 ZERO +0x40 stores.

Acceptance output: the per-boundary write sequence with the store pc, plus the writer
backtrace for every pc seen.
"""
import argparse, json, os, re, signal, struct, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "evidence")
BASE_ARR, BASE_SZ = 0x95DA10, 304
YEAR, MASK, CURP, TF = 0x985B00, 0x985B10, 0x985DCC, 0x985AE8   # m55_boundary's G table
GDB_TMPL = r"""set pagination off
set confirm off
set height 0
set verbose off
set can-use-hw-watchpoints 1
set $b = @@ADDR@@
set $add = 0
set $gate = 0
set $pay = 0
set $cl = 0
break *0x4ef7db if $eax == @@ADDR@@
commands
silent
set $add = $add + 1
printf "ADD#%d storage=%d d0=%d head=%d pend=%d flag30=0x%x\n", $add, *(int *)($b + 0x40), $ecx, *(int *)($b + 0x50), *(int *)($b + 0x4c), *(int *)($b + 0x30)
continue
end
break *0x4ef985 if $edx == @@ADDR@@
commands
silent
printf "ANDTEST storage=%d edi=%d pend=%d\n", *(int *)($b + 0x40), $edi, *(int *)($b + 0x4c)
continue
end
break *0x4f0a3d if $edx == @@ADDR@@
commands
silent
set $gate = $gate + 1
printf "GATE#%d storage=%d edi(price)=%d pend=%d head=%d\n", $gate, *(int *)($b + 0x40), $edi, *(int *)($b + 0x4c), *(int *)($b + 0x50)
continue
end
break *0x4efed8 if $ecx == @@ADDR@@
commands
silent
set $pay = $pay + 1
printf "PAY#%d before=%d edi=%d\n", $pay, *(int *)($b + 0x40), $edi
continue
end
break *0x4efeec if $esi == @@ADDR@@
commands
silent
set $cl = $cl + 1
printf "CLMP#%d storage=%d cap=%d d0=%d\n", $cl, *(int *)($b + 0x40), $ecx, $eax
continue
end
continue
"""
WATCH_TMPL = r"""set pagination off
set confirm off
set height 0
set verbose off
set can-use-hw-watchpoints 1
set $w = 0
set $b = @@ADDR@@
watch *(int *)@@ADDR@@
commands
silent
set $w = $w + 1
printf "WP#%d pc=0x%x val=%d pend=%d head=%d d0=%d\n", $w, $pc, *(int *)$b, *(int *)($b + 0x4c), *(int *)($b + 0x50), *(int *)($b + 0xd0)
bt 6
continue
end
continue
"""


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def game_pid():
    out = sh(["pgrep", "-x", "terran.exe"]).stdout.split()
    if not out:
        raise SystemExit("terran.exe not running")
    return int(out[0])


def base_addr(pid, name, want_index=None):
    f = open(f"/proc/{pid}/mem", "rb", 0)
    n = int.from_bytes(_pread(f, 0x985AF4, 4), "little")
    hits = []
    for i in range(min(n, 64)):
        b = _pread(f, BASE_ARR + i * BASE_SZ, BASE_SZ)
        nm = b[19:59].split(b"\0")[0].decode("latin-1", "replace")
        if want_index is not None:
            if i == want_index:
                hits.append((i, nm, b))
        elif name and name.lower() in nm.lower():
            hits.append((i, nm, b))
    f.close()
    if len(hits) != 1:
        raise SystemExit(f"base lookup got {len(hits)} hits for {name!r} idx={want_index}")
    i, nm, b = hits[0]
    g = lambda o: struct.unpack("<i", b[o:o + 4])[0]
    return i, nm, BASE_ARR + i * BASE_SZ, dict(pending=g(0x4c), head=g(0x50), minerals=g(0x40),
                                               d0=g(0xd0), progress=g(0x3c), rate=g(0xcc))


_pread = lambda f, a, n: (f.seek(a), f.read(n))[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["queue", "empty"], default="queue")
    ap.add_argument("--wp", action="store_true", help="use a hardware watchpoint on +0x40 "
                        "instead of breakpoints at the known store sites (slow: the store "
                        "is also read constantly by the display)")
    ap.add_argument("--base", default="Korolev Center")
    ap.add_argument("--boundaries", type=int, default=4)
    ap.add_argument("--timeout", type=float, default=180.0)
    ap.add_argument("--stop", action="store_true", help="detach a leftover gdb (crash recovery)")
    ap.add_argument("--tag", default="m57c")
    a = ap.parse_args()

    os.makedirs(EVID, exist_ok=True)
    pidfile = os.path.join(EVID, f"{a.tag}.gdbpid")
    gpath = os.path.join(EVID, f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.log")
    tpath = os.path.join(EVID, f"trace_{a.tag}.jsonl")

    if a.stop:
        dp = int(open(pidfile).read().strip())
        os.kill(dp, signal.SIGINT)
        pid = game_pid()
        for _ in range(60):
            try:
                if b"detached" in open(lpath, "rb").read() or not os.path.exists(f"/proc/{dp}"):
                    break
            except OSError:
                pass
            time.sleep(0.5)
        sh(["kill", "-CONT", str(pid)])
        print(f"detached gdb {dp}; kill -CONT {pid}; log {lpath}")
        return 0

    pid = game_pid()
    if sh(["pgrep", "-x", "gdb"]).stdout.strip():
        raise SystemExit("a gdb is already running — run --stop first")
    tracer = sh(["grep", "-m1", "TracerPid", f"/proc/{pid}/status"]).stdout.split()[-1]
    if tracer != "0":
        raise SystemExit(f"TracerPid={tracer} != 0")
    scope = sh(["sysctl", "-n", "kernel.yama.ptrace_scope"]).stdout.strip()
    if scope != "0":
        raise SystemExit(f"ptrace_scope={scope}")

    idx, nm, addr, pre = base_addr(pid, a.base)
    print(f"base {nm!r} idx={idx} addr={addr:#x} pre={pre}", flush=True)

    # --mode empty: the ONLY poke, done before the tracer attaches, read back after.
    poke = None
    if a.mode == "empty":
        fd = os.open(f"/proc/{pid}/mem", os.O_WRONLY)
        os.pwrite(fd, struct.pack("<i", 0), addr + 0x4c)
        os.pwrite(fd, b"".join(struct.pack("<i", -38) for _ in range(10)), addr + 0x50)
        os.close(fd)
        _, _, _, post = base_addr(pid, a.base)
        poke = dict(before=pre, after=post)
        print(f"poke empty-queue readback: {post}", flush=True)
        if post["pending"] != 0 or post["head"] != -38:
            raise SystemExit("poke did not land (queue not empty) — abort before attaching")

    tmpl = WATCH_TMPL if a.wp else GDB_TMPL
    open(gpath, "w").write(tmpl.replace("@@ADDR@@", hex(addr)))
    lf = open(lpath, "wb")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=lf, stderr=subprocess.STDOUT)
    open(pidfile, "w").write(str(g.pid))
    print(f"gdb armed pid {g.pid}; log {lpath}", flush=True)

    trace = dict(tag=a.tag, pid=pid, base_index=idx, base_name=nm, base_addr=hex(addr),
                 mode=a.mode, poke=poke, pre=pre, samples=[], events=[])

    def log(obj):
        trace["events"].append(obj)

    m = open(f"/proc/{pid}/mem", "rb", 0)

    def u32(off):
        return int.from_bytes(_pread(m, off, 4), "little")

    year0 = u32(YEAR)
    win = None
    try:
        win = sh(["xdotool", "search", "--name", "Sid Meier"]).stdout.split()[0]
        sh(["xdotool", "windowfocus", win])
    except Exception:
        pass

    t0 = time.time()
    last_press = 0.0
    last_h = 0.0
    last_ok = 0.0
    parked_t = None
    flips = []
    last_year = year0
    parked_since = None
    while time.time() - t0 < a.timeout:
        y = u32(YEAR)
        cp = u32(CURP)
        tf = u32(TF)
        now = time.time() - t0
        trace["samples"].append(dict(t=round(now, 3), wall=round(time.time(), 3), year=y, cp=cp, tf=tf,
                                    store=u32(addr + 0x40), pend=u32(addr + 0x4c),
                                    head=u32(addr + 0x50), d0=u32(addr + 0xd0)))
        if y != last_year:
            flips.append((last_year, y, round(now, 3)))
            log(dict(event="flip", frm=last_year, to=y, t=round(now, 3),
                     wall=round(time.time(), 3)))
            last_year = y
        if len(flips) >= a.boundaries:
            break
        # m56_build's proven escalation: Return every 2 s (consumed as turn-end by the
        # human loop, as dismissal by modal dialogs, as OK by popups); if parked on our
        # turn > 8 s a produced order-0 unit has frozen the auto-end -> 'h' on the
        # cursor unit every 4 s; > 15 s -> click OK (a popup whose default is NOT Return).
        if now - last_press > 2.0:
            if win:
                subprocess.run(["xdotool", "key", "--clearmodifiers", "Return"], check=False)
                log(dict(event="press_return", t=round(now, 3)))
            last_press = now
            if cp == 3 and now - parked_t > 8.0 and now - last_h > 4.0:
                subprocess.run(["xdotool", "key", "--clearmodifiers", "h"], check=False)
                log(dict(event="press_hold", t=round(now, 3)))
                last_h = now
            if cp == 3 and now - parked_t > 15.0 and now - last_ok > 6.0 and win:
                sh(["xdotool", "windowfocus", win])
                sh(["xdotool", "mousemove", "630", "247"])
                sh(["xdotool", "click", "1"])
                log(dict(event="click_ok", t=round(now, 3), xy=[630, 247]))
                last_ok = now
        if cp == 3:
            if parked_t is None:
                parked_t = now
        else:
            parked_t = None
            last_h = last_ok = 0.0
        if g.poll() is not None:
            log(dict(event="gdb_exit", rc=g.returncode, t=round(now, 3)))
            print(f"gdb exited rc={g.returncode}", flush=True)
            break

    # detach
    os.kill(g.pid, signal.SIGINT)
    detached = False
    for _ in range(60):
        try:
            if b"detached" in open(lpath, "rb").read() or not os.path.exists(f"/proc/{g.pid}"):
                detached = True
                break
        except OSError:
            detached = True
            break
        time.sleep(0.5)
    sh(["kill", "-CONT", str(pid)])
    log(dict(event="detach", detached=detached))
    try:
        _, _, _, postp = base_addr(pid, a.base)
        trace["post"] = postp
    except Exception as e:
        trace["post"] = {"error": str(e)}

    # parse the watch log
    txt = open(lpath, errors="replace").read()
    hits = []
    for line in txt.splitlines():
        mm = re.match(r"ADD#(\d+) storage=(-?\d+) d0=(-?\d+) head=(-?\d+) pend=(-?\d+) flag30=0x([0-9a-f]+)", line)
        if mm:
            hits.append(dict(kind="ADD", n=int(mm.group(1)), pc=0x4EF7DB,
                             storage=int(mm.group(2)), d0=int(mm.group(3)),
                             head=int(mm.group(4)), pend=int(mm.group(5)),
                             flag30=int(mm.group(6), 16))); continue
        mm = re.match(r"ANDTEST storage=(-?\d+) edi=(-?\d+) pend=(-?\d+)", line)
        if mm:
            hits.append(dict(kind="ANDTEST", n=0, pc=0x4EF985,
                             storage=int(mm.group(1)), edi=int(mm.group(2)),
                             pend=int(mm.group(3)))); continue
        mm = re.match(r"GATE#(\d+) storage=(-?\d+) edi\(price\)=(-?\d+) pend=(-?\d+) head=(-?\d+)", line)
        if mm:
            hits.append(dict(kind="GATE", n=int(mm.group(1)), pc=0x4F0A3D,
                             storage=int(mm.group(2)), price=int(mm.group(3)),
                             pend=int(mm.group(4)), head=int(mm.group(5)))); continue
        mm = re.match(r"PAY#(\d+) before=(-?\d+) edi=(-?\d+)", line)
        if mm:
            hits.append(dict(kind="PAY", n=int(mm.group(1)), pc=0x4EFED8,
                             before=int(mm.group(2)), edi=int(mm.group(3)))); continue
        mm = re.match(r"CLMP#(\d+) storage=(-?\d+) cap=(-?\d+) d0=(-?\d+)", line)
        if mm:
            hits.append(dict(kind="CLMP", n=int(mm.group(1)), pc=0x4EFEEC,
                             storage=int(mm.group(2)), cap=int(mm.group(3)),
                             d0=int(mm.group(4)))); continue
        mm = re.match(r"WP#(\d+) pc=0x([0-9a-f]+) val=(-?\d+) pend=(-?\d+) head=(-?\d+) d0=(-?\d+)", line)
        if mm:
            hits.append(dict(kind="WP", n=int(mm.group(1)), pc=int(mm.group(2), 16),
                             val=int(mm.group(3)), pend=int(mm.group(4)),
                             head=int(mm.group(5)), d0=int(mm.group(6)), bt=[]))
    # backtraces (watch mode only): the frames following each WP# line
    cur = None
    for line in txt.splitlines():
        mm = re.match(r"WP#(\d+) ", line)
        if mm:
            cur = int(mm.group(1))
            continue
        fm = re.match(r"#(\d+)\s+0x([0-9a-f]+) in ([A-Za-z0-9_<>~]+)", line)
        if fm and cur is not None:
            wps = [h for h in hits if h["kind"] == "WP"]
            if cur <= len(wps) and len(wps[cur - 1]["bt"]) < 6:
                wps[cur - 1]["bt"].append(f"#{fm.group(1)} {fm.group(2)} {fm.group(3)}")
        elif line.startswith("Watchpoint"):
            cur = None
    trace["watch_hits"] = hits
    trace["flips"] = flips

    with open(tpath, "w") as fh:
        for k in ("tag", "pid", "base_index", "base_name", "base_addr", "mode", "poke",
                  "pre", "post", "flips", "watch_hits", "events"):
            fh.write(json.dumps({k: trace[k]}, sort_keys=True) + "\n")
        fh.write(json.dumps({"samples": trace["samples"]}, sort_keys=True) + "\n")

    print(f"boundaries flipped: {len(flips)} {flips}", flush=True)
    print(f"log hits: {len(hits)}", flush=True)
    for h in hits:
        if h["kind"] == "ADD":
            gated = "SKIPPED" if (h["d0"] <= 0 or h["head"] == -38 or (h["flag30"] & 2)) else "ADDS"
            print(f"  ADD#{h['n']} storage={h['storage']} d0={h['d0']} head={h['head']} "
                  f"pend={h['pend']} flag30=0x{h['flag30']:x}  {gated}"
                  + (f" -> {h['storage'] + h['d0']}" if gated == "ADDS" else ""), flush=True)
        elif h["kind"] == "ANDTEST":
            print(f"  ANDTEST storage={h['storage']} edi={h['edi']} pend={h['pend']} "
                  f"(ZF={h['edi'] == 0} -> {'gate path 0x4f0a37' if h['edi'] == 0 else 'pop path 0x4ef98b'})",
                  flush=True)
        elif h["kind"] == "GATE":
            verdict = "PASS->completes" if h["storage"] >= h["price"] else "fail"
            print(f"  GATE#{h['n']} storage={h['storage']} price={h['price']} "
                  f"pend={h['pend']} head={h['head']}  {verdict}", flush=True)
        elif h["kind"] == "PAY":
            print(f"  PAY#{h['n']} storage {h['before']} -> {h['before'] - h['edi']} "
                  f"(edi={h['edi']})", flush=True)
        elif h["kind"] == "CLMP":
            fired = "STORES" if h["storage"] > min(h["cap"], h["d0"]) else "no-store"
            print(f"  CLMP#{h['n']} sees storage={h['storage']} min(cap={h['cap']},d0={h['d0']})"
                  f"={min(h['cap'], h['d0'])}  {fired}", flush=True)
        else:
            print(f"  WP#{h['n']} pc=0x{h['pc']:x} val={h['val']} pend={h['pend']} "
                  f"head={h['head']} d0={h['d0']}", flush=True)
    kinds = {}
    for h in hits:
        kinds[h["kind"]] = kinds.get(h["kind"], 0) + 1
    print("hit counts by site:", kinds, flush=True)
    for h in hits:
        if h.get("bt"):
            print(f"  bt WP#{h['n']} (pc=0x{h['pc']:x}):", flush=True)
            for fr in h["bt"]:
                print(f"    {fr}", flush=True)
    print(f"trace: {tpath}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
