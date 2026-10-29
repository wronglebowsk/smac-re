#!/usr/bin/env python3
"""M109 — name the 5 COUNTED legs of the save chunk map live, and try to close the map to the byte.

Arms 6 silent breakpoints BEFORE the save load (no watchpoints, no pokes) and drives one
m54b_clean load, then reads the counts back from /proc:

    0x597319  size = $edx   52 * [0x985af0]  -> 0x933278
    0x59738b  size = $eax   48 * [0x985af0]  -> malloc
    0x59751f  size = $eax  304 * [0x985af4]  -> 0x95da10
    0x5970e4  size = $eax   the count prefix  -> 0x930d7c
    0x5979f8  size = $edx   the tail          -> [ebp-0x28]
    0x596ab2  malloc(0xe5e0) — what the 0x40a75b0 buffer really is (0x596ab7 prints $eax)

    python3 scripts/m109_leg_sizes.py --tag m109l1 --relaunch

Gates: G1 6 bps armed with 0 gdb errors; G2 every counted leg logged a live size, 2 rounds worth is
not required; G3 each logged size == the model from the live counts; G4 **the map closes**:
immediates 204,504 + the counted sizes == the file size, 0 remainder; G5 the malloc size is printed
and explains the 86,016-byte direct read or it does not (reported, not gated).
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

TMPL = """set pagination off
set confirm off
set print elements 0
@@BLOCKS@@printf "ARMED @@N@@ bps at @@BPS@@\\n"
continue
"""

BP = """break *@@PC@@
commands
silent
printf "@@LINE@@\\n"@@ARGS@@
continue
end
"""

LEGS = [
    (0x597319, "LEG52", "$edx"),
    (0x59738b, "LEG48", "$eax"),
    (0x59751f, "LEG304", "$eax"),
    (0x5970e4, "LEGCNT", "$eax"),
    (0x5979f8, "LEGTAIL", "*(unsigned int *)($esp+4)"),
    (0x596ab7, "LEGMAL", "$eax"),
]
COUNT_U, COUNT_B = 0x985af0, 0x985af4
IMMEDIATES = 204504
FIXED_IMM = 0xe5e0        # the malloc'd leg's declared size


def gdb_script():
    blocks, pcs = [], []
    for pc, name, reg in LEGS:
        line = "M109L %s size=%%d round=%%d cp=%%d" % name
        args = [reg, M.RND, M.CPP]
        if len(re.findall(r"%[dx]", line)) != len(args):
            raise SystemExit("printf arg count mismatch: " + line)
        blocks.append(BP.replace("@@PC@@", "%#x" % pc).replace("@@LINE@@", line)
                      .replace("@@ARGS@@", "".join(", " + x for x in args)))
        pcs.append("%#x" % pc)
    return TMPL.replace("@@BLOCKS@@", "".join(blocks)).replace("@@N@@", str(len(LEGS))) \
               .replace("@@BPS@@", " ".join(pcs))


def read_counts(pid):
    fd = os.open("/proc/%d/mem" % pid, os.O_RDONLY)
    try:
        return (struct.unpack("<I", os.pread(fd, 4, COUNT_U))[0],
                struct.unpack("<I", os.pread(fd, 4, COUNT_B))[0])
    finally:
        os.close(fd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m109l1")
    ap.add_argument("--save", default="m54b_clean.SAV")
    ap.add_argument("--relaunch", action="store_true")
    a = ap.parse_args()

    gpath = os.path.join(M.SCRATCH, a.tag + ".gdb")
    lpath = os.path.join(M.EVID, a.tag + ".gdblog")
    os.makedirs(M.SCRATCH, exist_ok=True)
    open(gpath, "w").write(gdb_script())
    print("gdb script: %d bps" % len(LEGS), flush=True)

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
    print("armed before any screen: %s" % [l for l in head.splitlines() if l.startswith("ARMED")][0][:160],
          flush=True)
    time.sleep(6)                       # let it reach the quiescent CDROM screen

    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "m54a_load.py")],
                       capture_output=True, text=True,
                       env=dict(os.environ,
                                SMAC_SAVE="Z:\\home\\n100\\reverse\\smac\\programs\\saves\\" + a.save))
    print("load rc=%d" % r.returncode, flush=True)
    for ln in (r.stdout or "").strip().splitlines()[-4:]:
        print("  load: " + ln[:140], flush=True)
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
    ev = [l for l in text.splitlines() if l.startswith("M109L ")]
    errs = [l for l in text.splitlines() if l.startswith("Error") or "Cannot access memory" in l]
    sizes = {}
    for l in ev:
        m = re.match(r"M109L (\w+) size=(-?\d+) round=(-?\d+) cp=(-?\d+)", l)
        if m:
            sizes.setdefault(m.group(1), []).append(int(m.group(2)))
    nu, nb = read_counts(pid)

    gates = []
    gates.append(("G1", f"{len(LEGS)} bps armed, {len(errs)} gdb errors, {len(ev)} events",
                  "ARMED" in text and not errs and bool(ev)))
    gates.append(("G2", "legs logged: " + "; ".join(f"{k}={v}" for k, v in sizes.items()),
                  len(sizes) == len(LEGS)))
    model = {"LEG52": 52 * nu, "LEG48": 48 * nu, "LEG304": 304 * nb}
    ok3 = all(set(sizes.get(k, [])) == {v} for k, v in model.items())
    gates.append(("G3", f"counts nu={nu} nb={nb} -> model {model}; live "
                        f"{ {k: sizes.get(k) for k in model} }", ok3))

    counted = sum(next(iter(set(v))) for k, v in sizes.items() if k != "LEGMAL")
    total = IMMEDIATES + counted
    file_size = os.path.getsize(os.path.join(ROOT, "programs/saves", a.save))
    gates.append(("G4", f"immediates {IMMEDIATES:,} + counted {counted:,} = {total:,} vs file "
                        f"{file_size:,} -> remainder {file_size - total:,}", total == file_size))
    mal = sorted(set(sizes.get("LEGMAL", [])))
    gates.append(("G5", f"malloc leg declared {FIXED_IMM:,} B (0xe5e0); live heap buffer {mal}",
                  True))

    lines = [f"M109 counted legs — {a.save}, pid {pid}", f"  counts nu={nu} nb={nb}",
             "  events: " + " | ".join(ev[:24])]
    lines += [f"  [{g}] {'PASS' if ok else 'FAIL'}  {msg}" for g, msg, ok in gates]
    npass = sum(1 for _, _, ok in gates if ok)
    lines.append(f"  VERDICT {'PASS' if npass == len(gates) else 'FAIL'} {npass}/{len(gates)}")
    out = "\n".join(lines)
    print(out)
    with open(os.path.join(M.EVID, a.tag + ".log"), "w") as f:
        f.write(out + "\n")
    return 0 if npass == len(gates) else 1


if __name__ == "__main__":
    sys.exit(main())
