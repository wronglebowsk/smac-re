#!/usr/bin/env python3
"""M84f: force ds:0x920434 (NETGAME) = 1 from OUTSIDE gdb and test whether the 0x4d00 POST leg fires.

Why the poke lives in python: gdb's `set var *(int *)ADDR = v` inside a breakpoint command list
aborts the batch file ("Left operand of assignment is not an lvalue") and detaches at the first hit
(m84fleg1/2/3 all died that way, 0 events). The breakpoint lists here are PRINTF-ONLY (that shape is
proven: scripts/m84f_path_census.py logged CASE/BUMP/EXIT), and the flag is written through
/proc/pid/mem by a thread that runs for the whole driver window.

Footing (bytes): the POST at 0x4194a9 is behind 0x4193b2 `mov eax,ds:0x920434` / 0x4193b9
`je 0x4194b1`; 0x4193bf arg1 == 0; 0x4193ca head != [ebp-0x1c]. 0x4194b1 is the block's unique
convergence (`push 1; mov [ebx+0x3ff5c],0; call 0x4eb6b0`). s134: ds:0x920434 is written 1 only by
FUN_0057ecf0 (the opening-menu loop) and 0 everywhere else; live 0. m84fpath1 measured the block
running on an insert with flag 0: CASE 1 BUMP 7 EXIT 1 and NO post -> that run is the control.

Run: python3 scripts/m84f_post_leg.py --tag m84fleg4 [--base 17] [--inserts 1]
"""
import argparse, os, re, signal, subprocess, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import m74_flag_watch as F

ROOT, EVID = F.ROOT, F.EVID
NETGAME = 0x920434
BASEP = 0x8F0D60

TMPL = r"""set pagination off
set confirm off
set height 0
set verbose off
set $blk = 0
set $dispall = 0
set $disp4d = 0
set $hnd = 0
set $in4d = 0
set $b = *(unsigned int *)0x8f0d60
printf "ARMED base=0x%x pend=%d head=%d netgame=%d\n", $b, *(int *)($b + 0x4c), *(int *)($b + 0x50), *(int *)0x920434
break *0x4193b2
commands
silent
set $blk = $blk + 1
printf "G1 n=%d flag=%d arg1=%d head=%d snap=%d\n", $blk, *(int *)0x920434, *(int *)($ebp + 8), *(int *)(*(unsigned int *)0x8f0d60 + 0x50), *(int *)($ebp - 0x1c)
continue
end
break *0x4193c4
commands
silent
printf "G2 n=%d arg1=%d flag=%d\n", $blk, $eax, *(int *)0x920434
continue
end
break *0x4193ca
commands
silent
printf "G3 n=%d head=%d snap=%d flag=%d\n", $blk, *(int *)($esi + 0x50), *(int *)($ebp - 0x1c), *(int *)0x920434
continue
end
break *0x4194a9
commands
silent
printf "POST n=%d edi=%d arg1=%d flag=%d head=%d\n", $blk, $edi, *(int *)($ebp + 8), *(int *)0x920434, *(int *)(*(unsigned int *)0x8f0d60 + 0x50)
continue
end
break *0x4194b1
commands
silent
printf "EXIT n=%d cur=%d\n", $blk, *(int *)($ebx + 0x3ff5c)
continue
end
break *0x52bd3b
commands
silent
set $dispall = $dispall + 1
if *(unsigned short *)$ebx == 0x4d00
set $disp4d = $disp4d + 1
printf "DISP n=%d all=%d msg=0x%x\n", $blk, $dispall, $ebx
end
continue
end
break *0x52eb6c
commands
silent
printf "ARM n=%d all=%d msg=0x%x\n", $blk, $dispall, $ebx
continue
end
break *0x52ed7d
commands
silent
set $hnd = $hnd + 1
set $in4d = 1
printf "HND n=%d mode=%d argA=%d fac=%d globfac=%d aa1c=%d aa20=%d msg=0x%x\n", $blk, *(int *)($ebx + 0x14), *(int *)($ebx + 0x10), *(int *)($ebx + 4), *(int *)0x91b5b4, *(int *)0x99aa1c, *(int *)0x99aa20, $ebx
continue
end
break *0x52f756
commands
silent
if $in4d == 1
set $in4d = 0
printf "HOUT n=%d aa1c=%d aa20=%d\n", $blk, *(int *)0x99aa1c, *(int *)0x99aa20
end
continue
end
continue
"""

LINE = re.compile(r"^(G1|G2|G3|POST|EXIT|DISP|ARM|HND|HOUT|ARMED) (.*)$")
KV = re.compile(r"(\w+)=(-?0x[0-9a-f]+|-?\d+)")


def parse(text):
    ev = []
    for ln in text.splitlines():
        m = LINE.match(ln.strip())
        if m:
            ev.append((m.group(1), {k: int(v, 0) for k, v in KV.findall(m.group(2))}))
    return ev


class Poker(threading.Thread):
    """Writes NETGAME = 1 through /proc/<pid>/mem every 50 ms until stopped."""

    def __init__(self, pid, value=1, period=0.05):
        super().__init__(daemon=True)
        self.pid, self.value, self.period = pid, value, period
        self.writes, self.errors, self._stop = 0, 0, threading.Event()

    def run(self):
        fd = os.open("/proc/%d/mem" % self.pid, os.O_RDWR)
        try:
            while not self._stop.is_set():
                try:
                    os.pwrite(fd, int(self.value).to_bytes(4, "little"), NETGAME)
                    self.writes += 1
                except OSError:
                    self.errors += 1
                time.sleep(self.period)
            os.pwrite(fd, (0).to_bytes(4, "little"), NETGAME)
        finally:
            os.close(fd)

    def stop(self):
        self._stop.set()


def u32(pid, addr):
    try:
        with open("/proc/%d/mem" % pid, "rb", 0) as f:
            f.seek(addr)
            return int.from_bytes(f.read(4), "little")
    except OSError:
        return -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--base", default="17")
    ap.add_argument("--inserts", default="1")
    ap.add_argument("--settle", type=float, default=8.0)
    ap.add_argument("--timeout", type=int, default=300)
    a = ap.parse_args()

    pid = F.pid() if hasattr(F, "pid") else int(subprocess.run(
        ["pgrep", "-x", "terran.exe"], capture_output=True, text=True).stdout.split()[0])
    basep = u32(pid, BASEP)
    if basep < 0x1000:  # pointer not set yet (fresh load): use the record array directly
        basep = 0x95DA14 + int(a.base) * 0x130
    pend0, head0 = u32(pid, basep + 0x4C), u32(pid, basep + 0x50)
    print(f"pid {pid} base=0x{basep:x} pend {pend0} head {head0} netgame {u32(pid, NETGAME)}",
          flush=True)

    gpath = os.path.join(ROOT, "scratch", f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.gdblog")
    os.makedirs(EVID, exist_ok=True)
    open(gpath, "w").write(TMPL)
    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=log, stderr=subprocess.STDOUT)
    time.sleep(7)
    head = open(lpath, errors="replace").read()
    if not os.path.exists("/proc/%d" % g.pid) or "ARMED base=" not in head:
        try:
            os.kill(g.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
        subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
        raise SystemExit("gdb did not arm:\n" + head[-1200:])
    print([l for l in head.splitlines() if l.startswith("ARMED")][0], flush=True)

    pk = Poker(pid, 1)
    pk.start()
    time.sleep(0.3)
    t0 = time.time()
    r1 = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "m57_ui_enqueue.py"),
                         "--base-index", str(a.base), "--cell-item", "2",
                         "--inserts", str(a.inserts)],
                        capture_output=True, text=True, timeout=a.timeout + 120)
    print(f"enqueue rc={r1.returncode} t={time.time()-t0:.0f}s poke_writes={pk.writes} "
          f"poke_errors={pk.errors}", flush=True)
    for ln in (r1.stdout.strip().splitlines() or [""])[-3:]:
        print("  driver:", ln[:140], flush=True)
    time.sleep(a.settle)
    pk.stop()
    pk.join(timeout=3)

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
    ev = parse(text)
    cnt = {}
    for t, d in ev:
        cnt[t] = cnt.get(t, 0) + 1
    print("EVENT COUNTS:", cnt, flush=True)
    for i, (t, d) in enumerate(ev[:16]):
        print(f"  {i:2d} {t} {d}", flush=True)
    armed_ok = "Breakpoint 1 at" in text and "Breakpoint 9 at" in text
    detached = "detached]" in text
    err = [l for l in text.splitlines() if "lvalue" in l or "Error in sourced" in l]
    pend1, head1 = u32(pid, basep + 0x4C), u32(pid, basep + 0x50)
    print(f"read-back: pend {pend0}->{pend1} head {head0}->{head1} netgame {u32(pid, NETGAME)} "
          f"armed={armed_ok} detached={detached} errors={err[:2]}", flush=True)

    g1 = [d for t, d in ev if t == "G1"]
    post = [d for t, d in ev if t == "POST"]
    disp = [d for t, d in ev if t == "DISP"]
    arm = [d for t, d in ev if t == "ARM"]
    hnd = [d for t, d in ev if t == "HND"]
    hout = [d for t, d in ev if t == "HOUT"]
    edi = {d["n"]: d["edi"] for d in post}
    res = {
        # the block ran inside the driver window (path validity, matches m84fpath1)
        "G1_block_runs": bool(g1),
        # the forced flag was visible AT the gate
        "G2_flag_seen_1": any(d.get("flag") == 1 for d in g1),
        # with the flag forced, the POST leg fires
        "G3_post_fires": bool(post),
        # and the posted record is dispatched to the 0x4d00 arm and enters the handler
        "G4_chain_closes": bool(disp) and bool(arm) and bool(hnd),
        # payload links back to the post site and the mode vocabulary holds
        "G5_payload": bool(hnd) and all(d["mode"] in (0, 1, 2) for d in hnd) and
                      all(any(d["argA"] == -39 - e for e in edi.values()) for d in hnd),
        # the handler's exit is reached and the cursor pair is read back there
        "G6_readback": bool(hout),
    }
    print("GATES:", flush=True)
    for k, v in res.items():
        print(f"  {'T' if v else 'F'} {k}", flush=True)
    if post:
        print("post payload:", [{k: d[k] for k in ("n", "edi", "arg1", "flag", "head")}
                                for d in post[:4]], flush=True)
    if hnd:
        print("handler payload:", [{k: d[k] for k in ("n", "mode", "argA", "fac", "globfac")}
                                   for d in hnd[:4]], flush=True)
    ok = all(res.values()) and armed_ok and detached and not err
    print(f"VERDICT {'PASS' if ok else 'FAIL'} tag={a.tag} blk={len(g1)} post={len(post)} "
          f"exit={cnt.get('EXIT',0)} dispall={cnt.get('DISP',0)} arm={len(arm)} hnd={len(hnd)} "
          f"hout={len(hout)} pend={pend0}->{pend1} writes={pk.writes} armed={armed_ok} "
          f"detached={detached}", flush=True)
    print("evidence:", lpath, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
