#!/usr/bin/env python3
"""M53n: per-round call schedule of the economy block (4e8d60/4e92c0/4e93f0 ...).

  --mode arm   preflight (no gdb, TracerPid 0, ptrace_scope 0), write the gdb script,
               attach gdb in the background via stdbuf -o0 and RETURN (or stay alive
               --hold seconds so the terminal does not reap it).
  --mode stop  SIGINT the gdb in the pidfile, wait for detach, kill -CONT terran.exe.
               Never signal by name: this driver's argv contains its own tag.

Sites (all literals; static evidence evidence/m53n_callsites_raw.txt):
  int3  0x4f5a70 entry  VISIT   (param_1 = base idx at esp+4, caller ret at esp)
  int3  0x4e8d60 entry  SWEEPIN (sweep entry: c6c0/c70 as LEFT by the previous sweep)
  int3  0x4e92c0 entry  RATEIN  (c6c0 as seen by the bc-adder, bc before)
  hw    0x4e9331 exec  BCADD   (reached the unconditional bc += c6c[0] region)
  hw    0x962dec write  BCCHG   (base-70 +0xbc actually changed value)
  hw    0x962df0 write  C0CHG   (base-70 +0xc0 actually changed value)
  hw    0x8f0d60 write  BASEPTR (current-base pointer store: which site, which base)
"""
import argparse, os, signal, struct, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "evidence")

GDB_TMPL = r"""set pagination off
set confirm off
set verbose off
set can-use-hw-watchpoints 1
set $n = 0
set $cap = CAPN

break *0x4f5a70
commands
silent
set $n = $n + 1
printf "VISIT n=%d idx=%d d64=%d c6c0=%d c70=%d ret=%#x\n", $n, *(int *)($esp+4), *(int *)0x8f0d64, *(int *)0x8f0c6c, *(int *)0x8f0c70, *(int *)($esp)
if $n >= $cap
  printf "CAP\n"
  detach
  quit
end
continue
end

break *0x4e8d60
commands
silent
set $n = $n + 1
printf "SWEEPIN n=%d cur=%d d64=%d c6c0pre=%d c70pre=%d ret=%#x\n", $n, *(int *)0x68cbb0, *(int *)0x8f0d64, *(int *)0x8f0c6c, *(int *)0x8f0c70, *(int *)($esp)
if $n >= $cap
  printf "CAP\n"
  detach
  quit
end
continue
end

break *0x4e92c0
commands
silent
set $n = $n + 1
printf "RATEIN n=%d cur=%d d64=%d c6c0=%d bc=%d ret=%#x\n", $n, *(int *)0x68cbb0, *(int *)0x8f0d64, *(int *)0x8f0c6c, *(int *)(*(int *)0x8f0d60 + 0xbc), *(int *)($esp)
if $n >= $cap
  printf "CAP\n"
  detach
  quit
end
continue
end

hbreak *0x4e9331
commands
silent
set $n = $n + 1
printf "BCADD n=%d cur=%d d64=%d c6c0=%d bc_old=%d w0=%#x w1=%#x w2=%#x w3=%#x w4=%#x w5=%#x w6=%#x w7=%#x\n", $n, *(int *)0x68cbb0, *(int *)0x8f0d64, *(int *)0x8f0c6c, *(int *)0x962dec, *(int *)($esp+0), *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(int *)($esp+0x10), *(int *)($esp+0x14), *(int *)($esp+0x18), *(int *)($esp+0x1c)
if $n >= $cap
  printf "CAP\n"
  detach
  quit
end
continue
end

watch *(int *)0x962dec
commands
silent
set $n = $n + 1
printf "BCCHG n=%d new=%d eip=%#x cur=%d d64=%d c6c0=%d c70=%d w0=%#x w1=%#x w2=%#x w3=%#x w4=%#x w5=%#x w6=%#x w7=%#x\n", $n, *(int *)0x962dec, $eip, *(int *)0x68cbb0, *(int *)0x8f0d64, *(int *)0x8f0c6c, *(int *)0x8f0c70, *(int *)($esp+0), *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(int *)($esp+0x10), *(int *)($esp+0x14), *(int *)($esp+0x18), *(int *)($esp+0x1c)
if $n >= $cap
  printf "CAP\n"
  detach
  quit
end
continue
end

watch *(int *)0x962df0
commands
silent
set $n = $n + 1
printf "C0CHG n=%d new=%d eip=%#x cur=%d d64=%d c70=%d c6c0=%d w0=%#x w1=%#x w2=%#x w3=%#x w4=%#x w5=%#x w6=%#x w7=%#x\n", $n, *(int *)0x962df0, $eip, *(int *)0x68cbb0, *(int *)0x8f0d64, *(int *)0x8f0c70, *(int *)0x8f0c6c, *(int *)($esp+0), *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(int *)($esp+0x10), *(int *)($esp+0x14), *(int *)($esp+0x18), *(int *)($esp+0x1c)
if $n >= $cap
  printf "CAP\n"
  detach
  quit
end
continue
end

watch *(int *)0x8f0d60
commands
silent
set $n = $n + 1
printf "BASEPTR n=%d new=%#x idx=%d eip=%#x d64=%d c6c0=%d c70=%d w0=%#x w1=%#x w2=%#x w3=%#x w4=%#x w5=%#x\n", $n, *(int *)0x8f0d60, ((int)*(int *)0x8f0d60 - 0x95da10) / 0x130, $eip, *(int *)0x8f0d64, *(int *)0x8f0c6c, *(int *)0x8f0c70, *(int *)($esp+0), *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(int *)($esp+0x10), *(int *)($esp+0x14)
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
    ap.add_argument("--tag", default="m53n")
    ap.add_argument("--mode", choices=["arm", "stop"], default="arm")
    ap.add_argument("--cap", type=int, default=4000)
    ap.add_argument("--hold", type=int, default=0)
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

    # base-70 identity re-check (owner byte@4 == 3, name)
    fd = os.open(f"/proc/{pid}/mem", os.O_RDONLY)
    nb = struct.unpack("<I", os.pread(fd, 4, 0x985af4))[0]
    rec = os.pread(fd, 0x130, 0x95da10 + 70 * 0x130)
    nm = rec[0x13:0x30].split(b"\0")[0].decode("latin1")
    os.close(fd)
    print(f"nb={nb} idx70 name={nm!r} owner={rec[4]} bc={struct.unpack_from('<i',rec,0xbc)[0]} "
          f"c0={struct.unpack_from('<i',rec,0xc0)[0]}", flush=True)
    if rec[4] != 3 or nm != "Climactic Research":
        print("ABORT: base 70 identity changed"); return 1

    with open(gpath, "w") as f:
        f.write(GDB_TMPL.replace("CAPN", str(a.cap)))
    lf = open(lpath, "wb")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=lf, stderr=subprocess.STDOUT)
    open(pidfile, "w").write(str(g.pid))
    print(f"gdb armed pid {g.pid}; log {lpath}", flush=True)
    if a.hold:
        t0 = time.time()
        while time.time() - t0 < a.hold:
            if g.poll() is not None:
                print("gdb exited", flush=True); break
            time.sleep(2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
