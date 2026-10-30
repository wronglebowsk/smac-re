#!/usr/bin/env python3
"""M117 — does the band-flag bit 0x40 DECIDE the second-ask branch? Count the test and the take, per faction.

M116 established the gate statically: `test BYTE PTR [esi+0x94d430],0x40` at 0x5aaf7f inside FUN_005aadf0+0x18f,
with the taken branch at 0x5aaf88, and that no `or` anywhere sets 0x40. It also showed bit 0x40 is SET for faction 1
and zero for the other seven — but a value is not a causal link.

This counts both sides of the branch per faction across a real round:
  * a silent bp at 0x5aaf7f logs `esi` and the tested byte   (the test was reached)
  * a silent bp at 0x5aaf88 logs `esi`                        (the branch was TAKEN)
Prediction if the bit decides it: `taken` appears exactly for the factions whose byte had 0x40 set, and no faction
reaches `taken` without it. Any `taken` with the bit clear, or any faction with the bit set that never reaches the
test, falsifies that reading.

    python3 scripts/m117_gate_take.py --tag m117g1 --turns 1
    python3 scripts/m117_gate_take.py --tag m117g1 --turns 1 --relaunch --save m54b_clean.SAV
"""
import argparse
import os
import re
import signal
import struct
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import m55_boundary as MB
import importlib.util

_spec = importlib.util.spec_from_file_location("m105", os.path.join(ROOT, "scripts", "m105_setup_watch.py"))
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)      # exposes SCRATCH, EVID, wine_pids, terran_pid like m109_leg_census uses

FLAG = 0x94D430
STRIDE = 8380          # DECIMAL 8,380 = 0x20BC — NAMED's 'f*8380' is not hex
TEST_PC = 0x5AAF7F
TAKEN_PC = 0x5AAF88
NL = chr(92) + "n"

TMPL = """set pagination off
set confirm off
handle SIGUSR1 nostop noprint pass
handle SIGUSR2 nostop noprint pass
handle SIGPIPE nostop noprint pass
break *0x5aaf7f
commands
silent
printf "M117G test esi=0x%x byte=0x%x@@NL@@", $esi, *(unsigned char *)($esi+0x94d430)
continue
end
break *0x5aaf88
commands
silent
printf "M117T taken esi=0x%x@@NL@@", $esi
continue
end
printf "ARMED gate bps@@NL@@"
continue
@@TAIL@@"""


def flags(pid):
    fd = os.open("/proc/%d/mem" % pid, os.O_RDONLY)
    try:
        return [struct.unpack("<I", os.pread(fd, 4, FLAG + f * STRIDE))[0] for f in range(8)]
    finally:
        os.close(fd)


def tracer(pid):
    try:
        for line in open("/proc/%d/status" % pid):
            if line.startswith("TracerPid:"):
                return line.split()[1]
    except OSError:
        pass
    return "?"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m117g1")
    ap.add_argument("--turns", type=int, default=1)
    ap.add_argument("--relaunch", action="store_true")
    ap.add_argument("--save", default="m54b_clean.SAV")
    a = ap.parse_args()

    if a.relaunch:
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "m54a_load.py"), "--relaunch"],
                           capture_output=True, text=True,
                           env=dict(os.environ,
                                    SMAC_SAVE="Z:\\home\\n100\\reverse\\smac\\programs\\saves\\" + a.save))
        print("load rc=%d" % r.returncode, flush=True)
    pid = MB.find_pid()

    gpath = os.path.join(M.SCRATCH, a.tag + ".gdb")
    lpath = os.path.join(M.EVID, a.tag + ".gdblog")
    open(gpath, "w").write(TMPL.replace("@@NL@@", NL).replace("@@TAIL@@", "continue\n" * 400))
    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=log, stderr=subprocess.STDOUT,
                         env=dict(os.environ, DEBUGINFOD_URLS=""))
    time.sleep(6)
    if "ARMED" not in open(lpath, errors="replace").read():
        try:
            os.kill(g.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
        raise SystemExit("gdb did not arm:\n" + open(lpath, errors="replace").read()[-600:])
    before = flags(pid)
    print("armed; bit0x40 before: %s" % "".join("Y" if v & 0x40 else "." for v in before), flush=True)

    p = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "smac_play.py"),
                        "--turns", str(a.turns)],
                       capture_output=True, text=True,
                       env=dict(os.environ, M54A_LOAD_TIMEOUT="1800"))
    print("driver rc=%d %s" % (p.returncode, (p.stdout or "").strip().splitlines()[-1:]), flush=True)
    time.sleep(5)
    try:
        os.kill(g.pid, signal.SIGINT)
    except ProcessLookupError:
        pass
    for _ in range(40):
        if not os.path.exists("/proc/%d" % g.pid):
            break
        time.sleep(0.5)
    for sig in (signal.SIGTERM, signal.SIGKILL):
        if not os.path.exists("/proc/%d" % g.pid):
            break
        try:
            os.kill(g.pid, sig)
        except ProcessLookupError:
            break
        time.sleep(2)
    subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
    log.close()

    after = flags(pid)
    text = open(lpath, errors="replace").read()
    tests, takes, raw = {}, {}, set()
    for line in text.splitlines():
        m = re.match(r"M117G test esi=0x([0-9a-f]+) byte=0x([0-9a-f]+)", line)
        if m:
            esi = int(m.group(1), 16)
            raw.add(esi)
            f = esi // STRIDE
            tests[f] = tests.get(f, 0) + 1
        m = re.match(r"M117T taken esi=0x([0-9a-f]+)", line)
        if m:
            f = int(m.group(1), 16) // STRIDE
            takes[f] = takes.get(f, 0) + 1

    lines = ["M117 gate take — %s, %d turn(s), %d test hits, %d take hits, gdb errors %d" %
             (a.tag, a.turns, sum(tests.values()), sum(takes.values()),
              sum(1 for l in text.splitlines() if l.startswith("Error"))),
             "  faction   bit0x40   reached test   took branch",
             "  -------   -------   ------------   -----------"]
    for f in range(8):
        bit = "SET " if before[f] & 0x40 else "clr "
        lines.append("  %7d   %s     %5d          %5d" % (f, bit, tests.get(f, 0), takes.get(f, 0)))
    viol = [f for f in takes if not (before[f] & 0x40)]
    idle = [f for f in tests if (before[f] & 0x40) and not takes.get(f)]
    off = sorted(e for e in raw if e % STRIDE)
    lines.append("  esi values seen: %s%s" % (" ".join("0x%x" % e for e in sorted(raw)[:6]),
                                              "" if not off else "   **NOT multiples of 0x8380: the f column is wrong**"))
    lines.append("  takes with the bit CLEAR: %s" % (viol or "none"))
    lines.append("  bit set but never taken: %s" % (idle or "none"))
    if p.returncode != 0:
        verdict = ("NO MEASUREMENT: the turn driver returned rc=%d (wedge/no orders) — 0 test hits is the DRIVER, not "
                   "the gate. Relaunch and load a clean save, then re-run." % p.returncode)
    elif not tests:
        verdict = ("NO TEST HITS: FUN_005aadf0 never reached 0x5aaf7f in this window — the run cannot decide "
                   "anything (not evidence that the gate is inert)")
    elif viol:
        verdict = ("FALSIFIED: faction(s) %s took the branch with bit 0x40 CLEAR — the bit does not decide it" %
                   ",".join(map(str, viol)))
    elif takes:
        verdict = ("CONSISTENT: %d take(s), all for factions with bit 0x40 SET; no take without the bit" %
                   sum(takes.values()))
    else:
        verdict = ("CONSISTENT-BUT-EMPTY: the test was reached %d time(s) and never taken while bit 0x40 is set "
                   "only for %s — re-run on a state where a faction has the bit set and the branch is live" %
                   (sum(tests.values()), ",".join(str(f) for f in range(8) if before[f] & 0x40) or "none"))
    lines.append("  VERDICT " + verdict)
    out = "\n".join(lines)
    print(out, flush=True)
    with open(os.path.join(M.EVID, a.tag + ".log"), "w") as fh:
        fh.write(out + "\n")
    # Exit semantics: a NEGATIVE result is still a result. "tests > 0, takes == 0" means the gate is CLOSED on
    # this state, which is what M117 set out to find, and must not look like a broken run (it did: m117g2 exited 4).
    rc = 0
    if p.returncode != 0:
        rc = 5          # wedge / no orders -> NO MEASUREMENT
    elif not tests:
        rc = 4          # the site was never reached -> inconclusive, not a gate result
    if tracer(pid) != "0":
        print("EXIT 8: box not clean (TracerPid=%s) — kill gdb %d by pid" % (tracer(pid), g.pid), flush=True)
        rc = 8
    return rc


if __name__ == "__main__":
    sys.exit(main())
