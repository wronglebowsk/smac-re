#!/usr/bin/env python3
"""M53s: hardware-watchpoint version — catch EVERY write to base+0xc4 of two
residual bases (46 gain 5, 3 gain 3) with the writing EIP, during one driven round.

The int3 probe on the obvious fold (`base+0xc4 += DAT_008f0c74` at 0x4eaa2e/0x4eaa30,
FUN_004eaa10) logged 211 folds over 74 bases in the 2383->2384 round and EVERY one had
add=0, so that fold is refuted as the source of the 1..5 energy gains.  This script
watches the field itself instead, so no hypothesis about the writer is needed.

  --mode arm / --mode stop   (same pidfile discipline as m53n_drive.py: never signal by
  name; SIGINT the pidfile pid, wait for "detached", then kill -CONT terran.exe)
"""
import argparse, os, signal, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "evidence")
BASES, STRIDE = 0x95DA10, 0x130
WATCH = [46, 3]

GDB_TMPL = r"""set pagination off
set confirm off
set verbose off
set can-use-hw-watchpoints 1
set $n = 0
set $cap = CAPN
set $hit46 = 0
set $hit3 = 0

watch *(int *)ADDR46
commands
silent
set $n = $n + 1
set $hit46 = $hit46 + 1
printf "C4W b46 n=%d pc=%#x new=%d esp=%#x\n", $n, $pc, *(int *)ADDR46, $esp
if $n >= $cap
  printf "CAP\n"
  detach
  quit
end
continue
end

watch *(int *)ADDR3
commands
silent
set $n = $n + 1
set $hit3 = $hit3 + 1
printf "C4W b3 n=%d pc=%#x new=%d esp=%#x\n", $n, $pc, *(int *)ADDR3, $esp
if $n >= $cap
  printf "CAP\n"
  detach
  quit
end
continue
end

continue
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m53s_c4w")
    ap.add_argument("--mode", choices=["arm", "stop"], default="arm")
    ap.add_argument("--cap", type=int, default=4000)
    a = ap.parse_args()
    pidfile = os.path.join(EVID, f"{a.tag}.pid")
    lpath = os.path.join(EVID, f"{a.tag}_watch.log")
    gpath = os.path.join(EVID, f"{a.tag}_watch.gdb")

    if a.mode == "stop":
        dp = int(open(pidfile).read().strip())
        if dp == os.getpid():
            print("pidfile holds us; nothing to stop"); return 0
        os.kill(dp, signal.SIGINT)
        print(f"SIGINT -> gdb {dp}", flush=True)
        pid = int(subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True,
                                 text=True).stdout.split()[0])
        for _ in range(60):
            try:
                if b"detached" in open(lpath, "rb").read().lower():
                    break
            except OSError:
                pass
            time.sleep(0.5)
        subprocess.run(["kill", "-CONT", str(pid)])
        print(f"kill -CONT {pid}; log {lpath}", flush=True)
        return 0

    if subprocess.run(["pgrep", "-x", "gdb"], capture_output=True, text=True).stdout.strip():
        print("ABORT: a gdb is already running"); return 1
    out = subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True, text=True).stdout.split()
    if not out:
        print("ABORT: terran.exe not running"); return 1
    pid = int(out[0])
    st = subprocess.run(["grep", "-m1", "TracerPid", f"/proc/{pid}/status"],
                        capture_output=True, text=True).stdout
    print("status:", st.strip())
    if st.split()[-1].strip() != "0":
        print("ABORT: TracerPid != 0"); return 1
    scope = subprocess.run(["sysctl", "-n", "kernel.yama.ptrace_scope"],
                           capture_output=True, text=True).stdout.strip()
    if scope != "0":
        print(f"ABORT: ptrace_scope={scope}"); return 1
    with open(gpath, "w") as f:
        script = GDB_TMPL.replace("CAPN", str(a.cap))
        script = script.replace("ADDR46", hex(BASES + 46 * STRIDE + 0xc4))
        script = script.replace("ADDR3", hex(BASES + 3 * STRIDE + 0xc4))
        f.write(script)
    lf = open(lpath, "wb")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=lf, stderr=subprocess.STDOUT)
    open(pidfile, "w").write(str(g.pid))
    print(f"gdb armed pid {g.pid}; watch {[hex(BASES + i * STRIDE + 0xc4) for i in WATCH]}; log {lpath}",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
