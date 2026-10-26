#!/usr/bin/env python3
"""M57-2b: which base does the BUILD UI's INSERT actually write?

gdb (m53g_drive pattern) armed on the enqueue dispatch inside FUN_00417ee0:
  0x418b57  head store   [base+0x50] = picked item (reached only when esi==0)
  0x418ad3  pending store (+0x4c) on the insert path
  0x418762  pending store (+0x4c) on the remove path
  0x418ac7  insert-shift store
  0x418b24  "BASE: changed production." tail (esi = slot index)
and, alongside them, the Korolev income-add decision site 0x4ef7db (eax == Korolev) so
the run also samples the credit cadence while the UI is being driven.

The gdb commands print the CURRENT-BASE pointer (`*0x8f0d60`) at every hit — that is the
base the store lands on. Run this, drive `scripts/m57_ui_enqueue.py` from another
process, then `--stop` and read the log.
"""
import argparse, os, signal, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "evidence")
GDB_TMPL = r"""set pagination off
set confirm off
set height 0
set verbose off
set can-use-hw-watchpoints 1
set $b = @@ADDR@@
set $enq = 0
set $hd = 0
set $pi = 0
set $pr = 0
set $sh = 0
set $tl = 0
set $add = 0
break *0x417ee0
commands
silent
set $enq = $enq + 1
printf "ENQ#%d param1=%d param2=%d curbase=0x%x\n", $enq, *(int *)($esp + 4), *(int *)($esp + 8), *(int *)0x8f0d60
continue
end
break *0x418b57
commands
silent
set $hd = $hd + 1
printf "HEADSTORE#%d curbase=0x%x writes=[base+0x50]=%d base40=%d base4c=%d\n", $hd, *(int *)0x8f0d60, $eax, *(int *)(*(int *)0x8f0d60 + 0x40), *(int *)(*(int *)0x8f0d60 + 0x4c)
continue
end
break *0x418ad3
commands
silent
set $pi = $pi + 1
printf "PEND_INC#%d curbase=0x%x base4c=%d\n", $pi, *(int *)0x8f0d60, *(int *)(*(int *)0x8f0d60 + 0x4c)
continue
end
break *0x418762
commands
silent
set $pr = $pr + 1
printf "PEND_DEC#%d curbase=0x%x base4c=%d\n", $pr, *(int *)0x8f0d60, *(int *)(*(int *)0x8f0d60 + 0x4c)
continue
end
break *0x418ac7
commands
silent
set $sh = $sh + 1
printf "SHIFT#%d curbase=0x%x\n", $sh, *(int *)0x8f0d60
continue
end
break *0x418b24
commands
silent
set $tl = $tl + 1
printf "TAIL#%d curbase=0x%x slot=%d\n", $tl, *(int *)0x8f0d60, $esi
continue
end
break *0x4ef7db if $eax == @@ADDR@@
commands
silent
set $add = $add + 1
printf "ADD#%d storage=%d d0=%d head=%d pend=%d flag30=0x%x\n", $add, *(int *)($b + 0x40), $ecx, *(int *)($b + 0x50), *(int *)($b + 0x4c), *(int *)($b + 0x30)
continue
end
continue
"""


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-index", type=int, default=18)
    ap.add_argument("--hold", type=float, default=90.0)
    ap.add_argument("--stop", action="store_true")
    ap.add_argument("--tag", default="m57d")
    a = ap.parse_args()
    os.makedirs(EVID, exist_ok=True)
    pidfile = os.path.join(EVID, f"{a.tag}.gdbpid")
    gpath = os.path.join(EVID, f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.log")

    pid = int(sh(["pgrep", "-x", "terran.exe"]).stdout.split()[0])
    if a.stop:
        dp = int(open(pidfile).read().strip())
        os.kill(dp, signal.SIGINT)
        for _ in range(60):
            try:
                if b"detached" in open(lpath, "rb").read() or not os.path.exists(f"/proc/{dp}"):
                    break
            except OSError:
                pass
            time.sleep(0.5)
        sh(["kill", "-CONT", str(pid)])
        txt = open(lpath, errors="replace").read()
        for line in txt.splitlines():
            if line.startswith(("ENQ#", "HEADSTORE#", "PEND_", "SHIFT#", "TAIL#", "ADD#")):
                print(line, flush=True)
        print(f"detached; log {lpath}", flush=True)
        return 0

    if sh(["pgrep", "-x", "gdb"]).stdout.strip():
        raise SystemExit("a gdb is already running — run --stop first")
    tracer = sh(["grep", "-m1", "TracerPid", f"/proc/{pid}/status"]).stdout.split()[-1]
    if tracer != "0":
        raise SystemExit(f"TracerPid={tracer} != 0")
    addr = 0x95DA10 + a.base_index * 304
    open(gpath, "w").write(GDB_TMPL.replace("@@ADDR@@", hex(addr)))
    lf = open(lpath, "wb")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=lf, stderr=subprocess.STDOUT)
    open(pidfile, "w").write(str(g.pid))
    print(f"gdb armed pid {g.pid}; base {hex(addr)}; log {lpath}", flush=True)
    t0 = time.time()
    while time.time() - t0 < a.hold:
        if g.poll() is not None:
            print(f"gdb exited rc={g.returncode}", flush=True)
            break
        time.sleep(1.0)
    print(f"hold {a.hold}s elapsed; run --stop when the UI driving is done", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
