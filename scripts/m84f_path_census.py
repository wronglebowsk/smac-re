#!/usr/bin/env python3
"""M84f path census: does the UI chooser-insert path execute ANY instruction of the
netgame-gated 0x4d00 case (FUN_00417ee0's queue-count block at 0x419355)?

Why this is the question: s134 showed the 0x4d00 POST (0x4194a9) is gated at 0x4193b9 on
ds:0x920434 (NETGAME, written 1 only by the opening-menu loop FUN_0057ecf0, live 0), and the
m84fleg1 poke run could not exercise the gate because the block itself never ran (blk=0).
This run separates the two reasons: a REAL insert (m57_ui_enqueue, read back as pending +N)
with silent bps on the case's entry, its queued-count bump, its pane-index read and its exit,
plus an ALIVE control (0x4eb6b0, called from this case AND 65 other places) and the chooser
modal call (0x41860a) that proves the UI path was exercised.

Gates: chooser ran, the insert landed, the instrument is alive, the case never ran, NETGAME 0.
Run: python3 scripts/m84f_path_census.py --tag m84fpath1 [--base 17] [--inserts 1]
"""
import argparse, os, signal, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import m74_flag_watch as F

ROOT, EVID = F.ROOT, F.EVID

TMPL = r"""set pagination off
set confirm off
set height 0
set verbose off
set $chooser = 0
set $case = 0
set $bump = 0
set $idx = 0
set $exit = 0
set $eb6 = 0
set $net = 0
set $b = *(unsigned int *)0x8f0d60
printf "ARMED base=0x%x pend=%d head=%d netgame=%d\n", $b, *(int *)($b + 0x4c), *(int *)($b + 0x50), *(int *)0x920434
break *0x41860a
commands
silent
set $chooser = $chooser + 1
printf "CHOOSER n=%d\n", $chooser
continue
end
break *0x419355
commands
silent
set $case = $case + 1
printf "CASE n=%d arg1=%d arg2=%d pend=%d head=%d\n", $case, *(int *)($ebp + 8), *(int *)($ebp + 0xc), *(int *)(*(unsigned int *)0x8f0d60 + 0x4c), *(int *)(*(unsigned int *)0x8f0d60 + 0x50)
continue
end
break *0x4193a0
commands
silent
set $bump = $bump + 1
printf "BUMP n=%d\n", $bump
continue
end
break *0x4193ec
commands
silent
set $idx = $idx + 1
printf "IDX n=%d base_idx=%d\n", $idx, *(int *)($ebx + 0x3ff3c)
continue
end
break *0x4194b1
commands
silent
set $exit = $exit + 1
printf "EXIT n=%d cur=%d\n", $exit, *(int *)($ebx + 0x3ff5c)
continue
end
break *0x4eb6b0
commands
silent
set $eb6 = $eb6 + 1
if $eb6 == 1
printf "EB6 first\n"
end
continue
end
break *0x528760
commands
silent
set $net = $net + 1
printf "NETCALL n=%d\n", $net
continue
end
continue
"""


def u32(pid, addr):
    with open("/proc/%d/mem" % pid, "rb", 0) as f:
        f.seek(addr)
        return int.from_bytes(f.read(4), "little")


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
    basep = u32(pid, 0x8F0D60)
    pend0 = u32(pid, basep + 0x4C)
    head0 = u32(pid, basep + 0x50)
    print(f"pid {pid} base=0x{basep:x} pend {pend0} head {head0}", flush=True)

    gpath = os.path.join(ROOT, "scratch", f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.gdblog")
    os.makedirs(EVID, exist_ok=True)
    open(gpath, "w").write(TMPL)
    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=log, stderr=subprocess.STDOUT)
    import time
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

    r1 = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "m57_ui_enqueue.py"),
                         "--base-index", str(a.base), "--cell-item", "2",
                         "--inserts", str(a.inserts)],
                        capture_output=True, text=True, timeout=a.timeout + 120)
    print(f"enqueue rc={r1.returncode}", flush=True)
    for ln in (r1.stdout.strip().splitlines() or [""])[-4:]:
        print("  driver:", ln[:150], flush=True)
    time.sleep(a.settle)

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
    cnt = {}
    for ln in text.splitlines():
        t = ln.split(" ", 1)[0].strip()
        if t in ("CHOOSER", "CASE", "BUMP", "IDX", "EXIT", "NETCALL", "EB6"):
            cnt[t] = cnt.get(t, 0) + 1
    armed_ok = "Breakpoint 1 at" in text and "Breakpoint 7 at" in text
    detached = "detached]" in text
    netgame = 0
    for ln in text.splitlines():
        if ln.startswith("ARMED") and "netgame=" in ln:
            netgame = int(ln.split("netgame=")[1].split()[0])
    pend1 = u32(pid, basep + 0x4C)
    head1 = u32(pid, basep + 0x50)
    print(f"read-back after detach: pend {pend0} -> {pend1}  head {head0} -> {head1}", flush=True)
    print("counts:", cnt, f"armed={armed_ok} detached={detached} netgame={netgame}", flush=True)

    res = {
        "G1_chooser_ran": cnt.get("CHOOSER", 0) >= 1,
        "G2_insert_landed": pend1 > pend0,
        "G3_instrument_alive": cnt.get("EB6", 0) >= 1,
        "G4_case_never_runs": cnt.get("CASE", 0) == 0 and cnt.get("BUMP", 0) == 0 and
                              cnt.get("IDX", 0) == 0 and cnt.get("EXIT", 0) == 0,
        "G5_netgame_zero": netgame == 0,
    }
    print("GATES:", flush=True)
    for k, v in res.items():
        print(f"  {'T' if v else 'F'} {k}", flush=True)
    ok = all(res.values()) and armed_ok and detached
    print(f"VERDICT {'PASS' if ok else 'FAIL'} tag={a.tag} chooser={cnt.get('CHOOSER', 0)} "
          f"case={cnt.get('CASE', 0)} bump={cnt.get('BUMP', 0)} idx={cnt.get('IDX', 0)} "
          f"exit={cnt.get('EXIT', 0)} netcall={cnt.get('NETCALL', 0)} "
          f"pend={pend0}->{pend1} armed={armed_ok} detached={detached}", flush=True)
    print("evidence:", lpath, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
