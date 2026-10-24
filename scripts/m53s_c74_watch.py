#!/usr/bin/env python3
"""M53s: catch the post-rebuild energy fold `base+0xc4 += DAT_008f0c74`.

Site: FUN_004eaa10 0x4eaa2e = `add esi,ecx` (esi = base+0xc4 read at 0x4eaa23,
ecx = DAT_008f0c74 read at 0x4eaa1b); the store is 0x4eaa30. eax = DAT_008f0d60
(current base pointer), so idx = (eax - 0x95da10)/0x130.

  --mode arm   preflight (no gdb, TracerPid 0, ptrace_scope 0), write the gdb script,
               attach gdb in the background and return.
  --mode stop  SIGINT the gdb in the pidfile, wait for detach, kill -CONT terran.exe.
               Never signal by name.
"""
import argparse, os, signal, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "evidence")

GDB_TMPL = r"""set pagination off
set confirm off
set verbose off
set can-use-hw-watchpoints 1
set $n = 0
set $cap = CAPN

break *0x4eaa2e
commands
silent
set $n = $n + 1
printf "C74ADD n=%d idx=%d c4pre=%d add=%d c74=%d curidx=%d ret=%#x\n", $n, ((int)$eax - 0x95da10)/0x130, $esi, $ecx, *(int *)0x8f0c74, *(int *)0x68cbb0, *(int *)($esp)
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
    ap.add_argument("--tag", default="m53s_c74")
    ap.add_argument("--mode", choices=["arm", "stop"], default="arm")
    ap.add_argument("--cap", type=int, default=300)
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
        f.write(GDB_TMPL.replace("CAPN", str(a.cap)))
    lf = open(lpath, "wb")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=lf, stderr=subprocess.STDOUT)
    open(pidfile, "w").write(str(g.pid))
    print(f"gdb armed pid {g.pid}; log {lpath}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
