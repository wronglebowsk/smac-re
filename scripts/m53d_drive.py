#!/usr/bin/env python3
"""M53d: who WRITES the pending production-queue slots base+0x54..+0x74?

Two modes:
  --arm  : preflight, (optional) poke a known queue, write the gdb script, attach gdb
           in the background and RETURN (gdb keeps running; drive the UI from other
           processes; the log is block-buffered so read it only after --stop).
  --stop : SIGINT the gdb recorded in the pidfile, wait for "detached", kill -CONT
           terran.exe.  Never pkill/pgrep-by-name: this driver's own argv contains the
           tag, so a name match would SIGINT this process (and, inside an agent session,
           the agent itself).

Static sites armed (disasm evidence/m53d_fn417ee0_disasm.txt, FUN_00417ee0 = the UI
enqueue, 0x417ee0 size 7459):
  0x418ac7  insert-shift store  [base+eax+4] = [base+eax]   (writes +0x58..+0x74)
  0x418751  remove-shift store  [base+eax]   = [base+eax+4] (writes +0x50..+0x74)
  0x418b57  head store          [base+0x50] = picked item, reached only when esi==0
  0x418aa2  dialog-answer jump table dispatch (eax = 0..3)
  0x418b24  "BASE: changed production." logger tail (esi = slot index)
  0x418ad3 / 0x418b02 / 0x418762  +0x4c (pending count) stores
  0x4ef6d0  QPIPE, name-conditioned through *(int*)0x8f0d60
"""
import argparse, os, signal, struct, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "evidence")
GDB_SITES = {
    "ENQ":        0x417ee0,
    "ANSWER":     0x418aa2,
    "SHIFTUP":    0x418ac7,
    "SHIFTDN":    0x418751,
    "HEAD":       0x418b57,
    "TAIL":       0x418b24,
    "CNT_INC":    0x418ad3,
    "CNT3":       0x418b02,
    "CNT_DEC":    0x418762,
    "QPIPE":      0x4ef6d0,
}

GDB_TMPL = r"""set pagination off
set confirm off
set height 0
set verbose off
set can-use-hw-watchpoints 1
set $enq = 0
set $qp = 0
set $su = 0
set $sd = 0
set $hd = 0
set $d2 = 0
set $w54 = 0
set $w58 = 0
set $sv = 0
break *0x417ee0
commands
silent
set $b = *(int *)0x8f0d60
set $enq = $enq + 1
printf "ENQ#%d param1=%d param2=%d f40=%d f44=%d f4c=%d f50=%d f54=%d f58=%d f5c=%d\n", $enq, *(int *)($esp + 4), *(int *)($esp + 8), *(int *)($b + 0x40), *(int *)($b + 0x44), *(int *)($b + 0x4c), *(int *)($b + 0x50), *(int *)($b + 0x54), *(int *)($b + 0x58), *(int *)($b + 0x5c)
continue
end
break *0x418aa2
commands
silent
printf "ANSWER eax=%d\n", $eax
continue
end
break *0x418ac7
commands
silent
set $b = *(int *)0x8f0d60
set $su = $su + 1
printf "SHIFTUP#%d dst_off=0x%x old=%d new=%d\n", $su, $eax + 4, *(int *)($b + $eax + 4), $edx
continue
end
break *0x418751
commands
silent
set $b = *(int *)0x8f0d60
set $sd = $sd + 1
printf "SHIFTDN#%d dst_off=0x%x old=%d new=%d\n", $sd, $eax, *(int *)($b + $eax), $edx
continue
end
break *0x418b57
commands
silent
set $b = *(int *)0x8f0d60
set $hd = $hd + 1
printf "HEAD#%d slot0_old=%d new=%d esi=%d f4c=%d\n", $hd, *(int *)($b + 0x50), *(int *)($ebp - 0x10), $esi, *(int *)($b + 0x4c)
continue
end
break *0x418b24
commands
silent
set $b = *(int *)0x8f0d60
printf "TAIL esi=%d slot[esi]=%d f4c=%d f50=%d f54=%d\n", $esi, *(int *)($b + $esi * 4 + 0x50), *(int *)($b + 0x4c), *(int *)($b + 0x50), *(int *)($b + 0x54)
continue
end
break *0x418ad3
commands
silent
printf "CNT_INC_PRE f4c=%d\n", *(int *)(*(int *)0x8f0d60 + 0x4c)
continue
end
break *0x418b02
commands
silent
printf "CNT3_PRE f4c=%d\n", *(int *)(*(int *)0x8f0d60 + 0x4c)
continue
end
break *0x418762
commands
silent
printf "CNT_DEC_PRE f4c=%d\n", *(int *)(*(int *)0x8f0d60 + 0x4c)
continue
end
break *0x41821a
commands
silent
set $b = *(int *)0x8f0d60
set $sv = $sv + 1
printf "SNAP#%d snap_f50=%d snap_f54=%d snap_f58=%d cur_f54=%d f4c=%d\n", $sv, *(int *)($b + 0x50), *(int *)($b + 0x54), *(int *)($b + 0x58), *(int *)($b + 0x54), *(int *)($b + 0x4c)
continue
end
break *0x418633
commands
silent
printf "RESTORE off=0x%x snap=%d\n", $eax, *(int *)($ecx + $eax)
continue
end
break *0x417d20
commands
silent
set $b = *(int *)0x8f0d60
set $d2 = $d2 + 1
printf "D20#%d item=%d slot=%d f4c=%d f50=%d f54=%d f58=%d\n", $d2, *(int *)($esp + 4), *(int *)($ecx + 0x3ff5c), *(int *)($b + 0x4c), *(int *)($b + 0x50), *(int *)($b + 0x54), *(int *)($b + 0x58)
continue
end
break *0x417dd8
commands
silent
set $b = *(int *)0x8f0d60
printf "D20_SHIFT dst_off=0x%x old=%d new=%d\n", $edx, *(int *)($b + $edx), $edi
continue
end
break *0x417e04
commands
silent
set $b = *(int *)0x8f0d60
printf "D20_STORE dst_off=0x%x old=%d new=%d item=%d\n", $edx * 4 + 0x50, *(int *)($b + $edx * 4 + 0x50), $ebx, $ebx
continue
end
break *0x4186d2
commands
silent
printf "POST_PICK edi=%d\n", $edi
continue
end
break *0x4186ec
commands
silent
set $b = *(int *)0x8f0d60
printf "MODE mode=%d slotfield=%d f4c=%d f50=%d f54=%d f58=%d\n", *(int *)($ebx + 0xb194), *(int *)($ebx + 0x3ff5c), *(int *)($b + 0x4c), *(int *)($b + 0x50), *(int *)($b + 0x54), *(int *)($b + 0x58)
continue
end
break *0x418e1d
commands
silent
printf "BRANCH_E1D (param1==0) edi=%d\n", $edi
continue
end
break *0x418cc9
commands
silent
printf "BRANCH_MODE2 edi=%d\n", $edi
continue
end
break *0x418cd8
commands
silent
printf "BRANCH_MODE3 edi=%d\n", $edi
continue
end
break *0x419967
commands
silent
printf "BRANCH_EXIT edi=%d\n", $edi
continue
end
break *0x4ef6d0 if *(int *)0x8f0d60 == BASEADDR
commands
silent
set $b = *(int *)0x8f0d60
set $qp = $qp + 1
printf "QPIPE#%d f40=%d f44=%d f4c=%d f50=%d f54=%d f58=%d f5c=%d\n", $qp, *(int *)($b + 0x40), *(int *)($b + 0x44), *(int *)($b + 0x4c), *(int *)($b + 0x50), *(int *)($b + 0x54), *(int *)($b + 0x58), *(int *)($b + 0x5c)
continue
end
watch *(int *)(WP54)
commands
silent
set $w54 = $w54 + 1
printf "W54#%d pc=0x%x val_after=%d\n", $w54, $pc, *(int *)WP54
continue
end
watch *(int *)(WP58)
commands
silent
set $w58 = $w58 + 1
printf "W58#%d pc=0x%x val_after=%d\n", $w58, $pc, *(int *)WP58
continue
end
continue
"""


def read_base(pid, name):
    """Locate our base record by NAME (the array slides between passes)."""
    fd = os.open(f"/proc/{pid}/mem", os.O_RDONLY)
    nb = struct.unpack("<I", os.pread(fd, 4, 0x985af4))[0]
    for i in range(nb):
        a = 0x95da10 + i * 0x130
        nm = os.pread(fd, 20, a + 0x13).split(b"\0")[0].decode("latin1")
        if nm == name:
            rec = struct.unpack("<12I", os.pread(fd, 0x30, a + 0x40))
            os.close(fd)
            return i, a, rec
    os.close(fd)
    return None, None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m53d")
    ap.add_argument("--mode", choices=["arm", "stop"], default="arm")
    ap.add_argument("--base-name", default="Climactic Research")
    ap.add_argument("--poke", default="", help="e.g. '2,3,4,5:3:200' = slots f50..f5c, f4c, f40")
    ap.add_argument("--hold", type=int, default=0,
                    help="after arming, stay alive (poll gdb) this many seconds. The Hermes "
                         "terminal kills a foreground command's children when the call returns, "
                         "so arm+drive needs a live parent: run with --hold under background=true.")
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
                if b"detached" in open(lpath, "rb").read():
                    break
            except OSError:
                pass
            time.sleep(0.5)
        subprocess.run(["kill", "-CONT", str(pid)])
        print(f"kill -CONT {pid}; log {lpath}", flush=True)
        return 0

    # ---- arm ----
    if subprocess.run(["pgrep", "-x", "gdb"], capture_output=True, text=True).stdout.strip():
        print("ABORT: a gdb is already running"); return 1
    out = subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True, text=True).stdout.split()
    if not out:
        print("ABORT: terran.exe not running"); return 1
    pid = int(out[0])
    st = subprocess.run(["grep", "-m1", "TracerPid", f"/proc/{pid}/status"],
                        capture_output=True, text=True).stdout
    print("status:", st.strip())
    if "0" not in st.split()[-1:]:
        print("ABORT: TracerPid != 0"); return 1
    scope = subprocess.run(["sysctl", "-n", "kernel.yama.ptrace_scope"],
                           capture_output=True, text=True).stdout.strip()
    if scope != "0":
        print(f"ABORT: ptrace_scope={scope}"); return 1

    idx, addr, rec = read_base(pid, a.base_name)
    if addr is None:
        print(f"ABORT: base {a.base_name!r} not found"); return 1
    print(f"base {a.base_name!r} idx={idx} addr={addr:#x} pre={rec}", flush=True)

    if a.poke:
        slots, f4c, f40 = a.poke.split(":")
        vals = [int(x) for x in slots.split(",")]
        blob = b"".join(struct.pack("<i", v) for v in vals)
        fd = os.open(f"/proc/{pid}/mem", os.O_WRONLY)
        os.pwrite(fd, blob, addr + 0x50)
        os.pwrite(fd, struct.pack("<i", int(f4c)), addr + 0x4c)
        os.pwrite(fd, struct.pack("<i", int(f40)), addr + 0x40)
        os.close(fd)
        fd = os.open(f"/proc/{pid}/mem", os.O_RDONLY)
        print("poked readback:", struct.unpack("<12I", os.pread(fd, 0x30, addr + 0x40)),
              flush=True)
        os.close(fd)

    txt = (GDB_TMPL.replace("BASEADDR", hex(addr))
                  .replace("WP54", hex(addr + 0x54))
                  .replace("WP58", hex(addr + 0x58)))
    open(gpath, "w").write(txt)
    lf = open(lpath, "wb")
    g = subprocess.Popen(["gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=lf, stderr=subprocess.STDOUT)
    open(pidfile, "w").write(str(g.pid))
    print(f"gdb armed pid {g.pid}; log {lpath}; gdb script {gpath}", flush=True)
    print("drive the UI now, then run: python3 scripts/m53d_drive.py --stop", flush=True)
    if a.hold:
        t0 = time.time()
        while time.time() - t0 < a.hold:
            if g.poll() is not None:
                print(f"gdb exited rc={g.returncode}", flush=True)
                break
            time.sleep(1.0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
