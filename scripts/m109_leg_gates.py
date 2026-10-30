#!/usr/bin/env python3
"""M109b — the save chunk map as GATED LEGS, measured at the four reader entry points.

M107/M108/M109a built the leg table from the `call 0x64cc00` sites inside FUN_00596850 and could
not close 242,539 B. This harness instruments the four READ WRAPPERS instead, so every leg is
logged wherever it is called, however many times a LOOP calls it, with the real
(ptr, size, count, stream) taken from the stack at the callee entry:

    0x596470 / 0x596540  CONVERTING readers (malloc size*count, read, copy) - used only when the
                         header flag [0x985ae8] & 0x10000000 is set (=> [0x926a14] != 0)
    0x64c9a0 / 0x64cc00  DIRECT readers (read into the caller's pointer)   - the m54b_clean path
    0x596850             FUN_00596850 entry: logs the FILE* the loader was handed

Stack at a callee entry: [esp]=retaddr [esp+4]=ptr [esp+8]=size [esp+0xc]=count [esp+0x10]=stream.

    python3 scripts/m109_leg_gates.py --tag m109g1 --relaunch

Gates (ONE invocation, one m54b_clean load):
  G1  5 bps armed, 0 gdb errors, >=1 ENTER, >=1 READ event
  G2  every READ on the loader's own FILE* is attributed to a return site (inside or outside the
      loader is REPORTED, and the inside/elsewhere split must account for all of them)
  G3  the map CLOSES: sum(size*count) on the loader's stream == the save file size, byte for byte
  G4  the three counted legs == the live model: 0x933278 == 52*[0x985af0], 0x95da10 ==
      304*[0x985af4], 0x930d7c == [0x927538]
  G5  the legs the version/flag GATES turn OFF are ABSENT: the 8x0x680 sparse loop needs
      version<3, the 0xe5e0 malloc leg needs version<3, the 0x991698 leg needs
      [0x985ae8]&0x10 - all false for this save
  G6  TracerPid 0 at the end, 0 unparsed M109 lines
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

READERS = [0x596470, 0x596540, 0x64c9a0, 0x64cc00]
LOADER_LO, LOADER_HI = 0x596850, 0x597a6b
RND, CPP = M.RND, M.CPP

TMPL = """set pagination off
set confirm off
set print elements 0
set $savefile = -1
handle SIGUSR1 nostop noprint pass
handle SIGUSR2 nostop noprint pass
handle SIGPIPE nostop noprint pass
@@BLOCKS@@printf "ARMED 5 bps at 0x596850 0x596470 0x596540 0x64c9a0 0x64cc00\\n"
@@TAIL@@"""

ENTER_BP = """break *0x596850
commands
silent
set $savefile = *(int *)($esp+4)
printf "M109E ENTER stream=0x%x round=0x%x cp=0x%x\\n", *(int *)($esp+4), @RND@, @CPP@
continue
end
"""

READ_BP = """break *@@PC@@ if *(int *)($esp+0x10) == $savefile
commands
silent
printf "M109R ra=0x%x ptr=0x%x size=%d count=%d stream=0x%x round=0x%x cp=0x%x\\n", *(int *)($esp), *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(int *)($esp+0x10), @RND@, @CPP@
continue
end
"""

CHATTER = re.compile(r"^\[New LWP|^\[Switching|^This GDB supports|^Enable debuginfod|"
                     r"^Debuginfod has|^To make this setting|^\[Inferior |^Thread \d+ |"
                     r"^warning:|^Undefined command")


def gdb_script():
    blocks = ENTER_BP.replace("@RND@", RND).replace("@CPP@", CPP)
    for pc in READERS:
        blocks += (READ_BP.replace("@@PC@@", "%#x" % pc)
                   .replace("@RND@", RND).replace("@CPP@", CPP))
    return TMPL.replace("@@BLOCKS@@", blocks).replace("@@TAIL@@", "continue\n" * 400)


def check_script(script):
    """The gdb printf arg-count law: specs must equal args in EVERY emitted printf line."""
    for line in script.splitlines():
        if line.startswith("printf"):
            nspec = len(re.findall(r"%[dux]", line))
            narg = line.count("*(int *)(") + line.count(RND) + line.count(CPP)
            if nspec != narg:
                raise SystemExit("printf arg-count mismatch (%d specs / %d args): %s"
                                 % (nspec, narg, line))


def read_mem(pid, addr, n=4):
    fd = os.open("/proc/%d/mem" % pid, os.O_RDONLY)
    try:
        return struct.unpack("<%dI" % (n // 4), os.pread(fd, n, addr))
    finally:
        os.close(fd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m109g1")
    ap.add_argument("--save", default="m54b_clean.SAV")
    ap.add_argument("--relaunch", action="store_true")
    a = ap.parse_args()

    gpath = os.path.join(M.SCRATCH, a.tag + ".gdb")
    lpath = os.path.join(M.EVID, a.tag + ".gdblog")
    os.makedirs(M.SCRATCH, exist_ok=True)
    script = gdb_script()
    check_script(script)
    open(gpath, "w").write(script)
    print("gdb script: 5 bps (1 ENTER + 4 READERS)", flush=True)

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
        print("terran.exe pid %d" % pid, flush=True)
    else:
        pid = M.terran_pid()
        if not pid:
            raise SystemExit("no terran.exe")

    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=log, stderr=subprocess.STDOUT,
                         env=dict(os.environ, DEBUGINFOD_URLS=""))
    time.sleep(4.0)
    head = open(lpath, errors="replace").read()
    if "ARMED" not in head:
        try:
            os.kill(g.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
        subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
        raise SystemExit("gdb did not arm:\n" + head[-800:])
    print("armed: %s" % [l for l in head.splitlines() if l.startswith("ARMED")][0][:120], flush=True)
    time.sleep(6)

    t0 = time.time()
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "m54a_load.py")],
                       capture_output=True, text=True,
                       env=dict(os.environ,
                                SMAC_SAVE="Z:\\home\\n100\\reverse\\smac\\programs\\saves\\" + a.save))
    print("load rc=%d in %.0f s (rc is NOT gated - s167 law)" % (r.returncode, time.time() - t0),
          flush=True)
    for ln in (r.stdout or "").strip().splitlines()[-3:]:
        print("  load: " + ln[:130], flush=True)
    time.sleep(4)
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
    lines = text.splitlines()
    enters, reads, unparsed = [], [], []
    for l in lines:
        if l.startswith("M109E "):
            m = re.match(r"^M109E ENTER stream=(0x[0-9a-f]+) round=(0x[0-9a-f]+) cp=(0x[0-9a-f]+)$", l)
            if m:
                enters.append(int(m.group(1), 16))
                continue
        elif l.startswith("M109R "):
            m = re.match(r"^M109R ra=(0x[0-9a-f]+) ptr=(0x[0-9a-f]+) size=(-?\d+) count=(-?\d+) "
                         r"stream=(0x[0-9a-f]+) round=(0x[0-9a-f]+) cp=(0x[0-9a-f]+)$", l)
            if m:
                reads.append(dict(ra=int(m.group(1), 16), ptr=int(m.group(2), 16),
                                  size=int(m.group(3)), count=int(m.group(4)),
                                  stream=int(m.group(5), 16),
                                  rnd=int(m.group(6), 16), cp=int(m.group(7), 16)))
                continue
        if l.startswith("M109"):
            unparsed.append(l)
    errs = [l for l in lines if l.startswith("Error") or "Cannot access memory" in l]
    chatter = [l for l in lines if CHATTER.match(l)]

    stream = enters[-1] if enters else None
    on = [e for e in reads if e["stream"] == stream] if stream else []
    off = [e for e in reads if e["stream"] != stream] if stream else reads
    total = sum(e["size"] * e["count"] for e in on)
    file_size = os.path.getsize(os.path.join(ROOT, "programs/saves", a.save))
    nu = read_mem(pid, 0x985af0)[0]
    nb = read_mem(pid, 0x985af4)[0]
    ver = read_mem(pid, 0x985dbc)[0]
    conv = read_mem(pid, 0x926a14)[0]
    cprefix = read_mem(pid, 0x927538)[0]
    counts = [read_mem(pid, 0x927a9c + f * 1436)[0] for f in range(8)]
    tracer = 0
    for l in open("/proc/%d/status" % pid, errors="replace"):
        if l.startswith("TracerPid:"):
            tracer = int(l.split()[1])

    inside = [e for e in on if LOADER_LO <= e["ra"] <= LOADER_HI]
    outside = [e for e in on if not (LOADER_LO <= e["ra"] <= LOADER_HI)]
    byptr = {}
    for e in on:
        byptr[e["ptr"]] = byptr.get(e["ptr"], 0) + e["size"] * e["count"]
    bysite = {}
    for e in on:
        bysite.setdefault(e["ra"], []).append(e)
    model = {0x933278: 52 * nu, 0x95da10: 304 * nb, 0x930d7c: cprefix}
    model_txt = "; ".join("%#x got %d model %d" % (p, byptr.get(p, -1), v) for p, v in model.items())
    model_ok = all(byptr.get(p) == v for p, v in model.items())
    sparse = sum(1 for e in on if e["size"] == 0x680)
    e5e0 = sum(1 for e in on if e["size"] == 0xe5e0)
    n991698 = sum(1 for e in on if e["ptr"] == 0x991698)
    n48p = sum(1 for e in on if e["size"] == 48 * nu and e["ptr"] > 0x40000000)

    gates = []
    gates.append(("G1", "%d bps armed, %d gdb errors, %d ENTER, %d READ events"
                  % (len(READERS) + 1, len(errs), len(enters), len(reads)),
                  "ARMED" in text and not errs and bool(enters) and bool(reads)))
    gates.append(("G2", "%d reads on the loader stream %#x: %d attributed inside FUN_00596850 "
                        "[%x,%x], %d attributed elsewhere; %d reads on other streams"
                  % (len(on), stream or 0, len(inside), LOADER_LO, LOADER_HI, len(outside), len(off)),
                  bool(on) and len(inside) + len(outside) == len(on)))
    gates.append(("G3", "map CLOSES: sum(size*count) on stream %#x = %d vs file %d (remainder %d)"
                  % (stream or 0, total, file_size, file_size - total),
                  stream is not None and total == file_size))
    gates.append(("G4", "counted legs: %s" % model_txt, model_ok))
    gates.append(("G5", "gated-off legs absent: 0x680-sparse %d, 0xe5e0 %d, 0x991698 %d, 48p %d "
                        "(version=%d convert=%d units=%d bases=%d)"
                  % (sparse, e5e0, n991698, n48p, ver, conv, nu, nb),
                  sparse == 0 and e5e0 == 0 and n991698 == 0 and n48p == 0))
    gates.append(("G6", "TracerPid %d, %d unparsed lines, %d gdb chatter lines (whitelisted)"
                  % (tracer, len(unparsed), len(chatter)), tracer == 0 and not unparsed))

    leg_txt = "; ".join("%#x n=%d %s" % (ra, len(v), " ".join("(%x,%d,%d)" % (e["ptr"], e["size"],
                                 e["count"]) for e in v[:3])) for ra, v in sorted(bysite.items()))
    out = "\n".join(["M109b gated leg map - %s, pid %d, loader stream %#x" % (a.save, pid, stream or 0),
                     "  version=%d convert=%d units=%d bases=%d counts=%s" % (ver, conv, nu, nb, counts),
                     "  %d reads on the loader stream, %d on other streams, %d distinct return sites, "
                     "total %d B" % (len(on), len(off), len(bysite), total),
                     "  LEGS ra -> n x (ptr,size,count): " + leg_txt]
                    + ["  [%s] %s  %s" % (g, "PASS" if ok else "FAIL", msg) for g, msg, ok in gates]
                    + ["  VERDICT %s %d/%d" % ("PASS" if all(ok for _, _, ok in gates) else "FAIL",
                                               sum(1 for _, _, ok in gates if ok), len(gates))])
    print(out[:9000], flush=True)
    with open(os.path.join(M.EVID, a.tag + ".log"), "w") as f:
        f.write(out + "\n")
    with open(os.path.join(M.SCRATCH, a.tag + "_legs.txt"), "w") as f:
        for e in reads:
            f.write("%x %x %d %d %x\n" % (e["ra"], e["ptr"], e["size"], e["count"], e["stream"]))
    return 0 if all(ok for _, _, ok in gates) else 1


if __name__ == "__main__":
    sys.exit(main())
