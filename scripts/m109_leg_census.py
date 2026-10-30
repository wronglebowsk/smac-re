#!/usr/bin/env python3
"""M109c — census EVERY read the save loader performs, using STATIC call-site breakpoints.

Lesson from m109b1 / s168's four runs: a breakpoint CONDITIONED on `*(unsigned int *)$esp` halts the
inferior whenever gdb cannot dereference (syscall, other thread), so the game freezes and the load
driver never gets past the menu — 0 ENTER, 0 loads, every time. Unconditioned bps at the loader's OWN
call instructions have no such failure mode (m109l2 logged its legs) and cannot fire outside a load.

So: parse the loader skeleton (evidence/m109_skel_loader.txt) for every `call` to one of the four
reader entry points whose own address is inside FUN_00596850, and break at those addresses. At a call
instruction the argument block is [esp]=dest, [esp+4]=size, [esp+8]=count, [esp+0xc]=FILE*.

    python3 scripts/m109_leg_census.py --tag m109c1 --relaunch
"""
import argparse
import importlib.util
import os
import re
import signal
import struct
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("m105", os.path.join(ROOT, "scripts", "m105_setup_watch.py"))
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

READERS = (0x596470, 0x596540, 0x64c9a0, 0x64cc00)
LO, HI = 0x596850, 0x597a6b
SKEL = os.path.join(ROOT, "evidence/m109_skel_loader.txt")
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
COUNT_U, COUNT_B = 0x985af0, 0x985af4
# M110: the loader, the second-phase function right after it, and the map loader family
# (the only outside functions whose reader calls a load can plausibly reach).
DEFAULT_RANGES = ("0x596620-0x5966ff,0x596850-0x597a6b,0x597a70-0x5986ff,0x5821e0-0x5823ff,"
                  "0x44b780-0x44b8ff,0x5c7200-0x5c7400,0x62b000-0x62d000")

TMPL = """set pagination off
set confirm off
@@BLOCKS@@printf "ARMED @@N@@ static read-site bps@@NL@@"
continue
"""

NL = chr(92) + "n"          # the two characters gdb's printf needs; built in code so file escaping cannot eat it
FMT = "M109C site=@@PC@@ dest=0x%x size=%d cnt=%d" + NL

BP = """break *@@PC@@
commands
silent
printf "@@FMT@@", *(unsigned int *)$esp, *(unsigned int *)($esp+4), *(unsigned int *)($esp+8)
continue
end
"""


def sites(ranges=None):
    """Every `call <reader>` whose own address is inside one of the ranges."""
    rs = []
    for part in (ranges or DEFAULT_RANGES).split(","):
        lo, _, hi = part.strip().partition("-")
        rs.append((int(lo, 16), int(hi, 16)))
    out = []
    with open(TEXT, errors="replace") as f:
        for line in f:
            m = re.match(r"\s*([0-9a-f]{6,8}):\s", line)
            if not m:
                continue
            a = int(m.group(1), 16)
            if not any(lo <= a <= hi for lo, hi in rs):
                continue
            parts = line.rstrip("\n").split("\t")
            asm = parts[2].strip() if len(parts) > 2 else ""
            c = re.match(r"call\s+0x([0-9a-f]+)", asm)
            if c and int(c.group(1), 16) in READERS:
                out.append(a)
    return sorted(set(out))


def gdb_script(ss):
    blocks = [BP.replace("@@PC@@", "%#x" % pc).replace("@@FMT@@", FMT.replace("@@PC@@", "%#x" % pc))
              for pc in ss]
    return (TMPL.replace("@@BLOCKS@@", "".join(blocks)).replace("@@N@@", str(len(ss)))
            .replace("@@NL@@", NL))


def read_counts(pid):
    fd = os.open("/proc/%d/mem" % pid, os.O_RDONLY)
    try:
        return (struct.unpack("<I", os.pread(fd, 4, COUNT_U))[0],
                struct.unpack("<I", os.pread(fd, 4, COUNT_B))[0])
    finally:
        os.close(fd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m109c1")
    ap.add_argument("--save", default="m54b_clean.SAV")
    ap.add_argument("--relaunch", action="store_true")
    ap.add_argument("--ranges", default=DEFAULT_RANGES,
                    help="address ranges to census, comma separated lo-hi (hex)")
    a = ap.parse_args()
    ss = sites(a.ranges)
    if not ss:
        raise SystemExit("no read sites parsed from the skeleton")
    gpath = os.path.join(M.SCRATCH, a.tag + ".gdb")
    lpath = os.path.join(M.EVID, a.tag + ".gdblog")
    open(gpath, "w").write(gdb_script(ss))
    print("%d static read-site bps" % len(ss), flush=True)

    pid = None
    if a.relaunch:
        for p, name in M.wine_pids():
            if name == "terran.exe":
                subprocess.run(["kill", str(p)], capture_output=True)
        time.sleep(3)
        for p, name in M.wine_pids():
            if name != "terran.exe":
                subprocess.run(["kill", str(p)], capture_output=True)
        time.sleep(4)
        subprocess.run(M.LAUNCH, shell=True)
        for _ in range(120):
            pid = M.terran_pid()
            if pid:
                break
            time.sleep(0.25)
        if not pid:
            raise SystemExit("no terran.exe after relaunch")
    else:
        pid = M.terran_pid()
        if not pid:
            raise SystemExit("no live terran.exe — pass --relaunch")
    print("terran.exe pid %d" % pid, flush=True)

    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=log, stderr=subprocess.STDOUT,
                         env=dict(os.environ, DEBUGINFOD_URLS=""))
    time.sleep(6)
    head = open(lpath, errors="replace").read()
    if "ARMED" not in head:
        try:
            os.kill(g.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
        subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
        raise SystemExit("gdb did not arm:\n" + head[-800:])
    print("armed", flush=True)
    time.sleep(10)          # the launch needs ~5-7 min; the driver can start while gdb is attached

    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "m54a_load.py")],
                       capture_output=True, text=True,
                       env=dict(os.environ,
                                M54A_LOAD_TIMEOUT="1800",   # a traced game is ~10x slow (m106 law)
                                SMAC_SAVE="Z:\\home\\n100\\reverse\\smac\\programs\\saves\\" + a.save))
    print("load rc=%d" % r.returncode, flush=True)
    for ln in (r.stdout or "").strip().splitlines()[-3:]:
        print("  load: " + ln[:120], flush=True)
    time.sleep(5)
    try:
        os.kill(g.pid, signal.SIGINT)
    except ProcessLookupError:
        pass
    for _ in range(40):
        if not os.path.exists("/proc/%d" % g.pid):
            break
        time.sleep(0.5)
    subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
    log.close()

    text = open(lpath, errors="replace").read()
    legs = []
    for l in text.splitlines():
        m = re.match(r"M109C site=0x([0-9a-f]+) dest=0x([0-9a-f]+) size=(-?\d+) cnt=(-?\d+)", l)
        if m:
            legs.append((int(m.group(1), 16), int(m.group(2), 16), int(m.group(3)), int(m.group(4))))
    total = sum(s * c for _, _, s, c in legs)
    nu, nb = read_counts(pid)
    file_size = os.path.getsize(os.path.join(ROOT, "programs/saves", a.save))
    errs = [l for l in text.splitlines() if l.startswith("Error") or "Cannot access memory" in l]
    lines = [f"M109c leg census — {a.save}, pid {pid}, {len(legs)} executed read sites, "
             f"{len(errs)} gdb errors, counts {nu}/{nb}",
             f"  ranges {a.ranges}",
             f"  sum(size*count) = {total:,}  vs file {file_size:,}  -> {file_size - total:,}"]
    off = 0
    for site, dest, size, cnt in legs:
        lines.append("  site=0x%x dest=0x%x size=%d cnt=%d file_off=%d" % (site, dest, size, cnt, off))
        off += size * cnt
    gap = file_size - total
    closed = gap == 0
    lines.append("VERDICT %s: sum(size*count) %d vs file %d, gap %d, %d executed of %d armed sites"
                 % ("CLOSED" if closed else "PARTIAL", total, file_size, gap, len(legs), len(ss)))
    out = "\n".join(lines)
    print(out[:4000])
    with open(os.path.join(M.EVID, a.tag + ".log"), "w") as f:
        f.write(out + "\n")
    if not legs:
        print("EXIT 3: 0 read calls — the load never ran (a bp conditioned on *($esp) freezes the game; "
              "see the instrument laws). This is NOT a measurement.", flush=True)
        return 3
    if closed:
        return 0
    print("EXIT 4: PARTIAL — %d of %d bytes unaccounted; a partial census is not a closure."
          % (gap, file_size), flush=True)
    return 4


if __name__ == "__main__":
    sys.exit(main())
