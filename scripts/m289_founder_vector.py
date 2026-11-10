#!/usr/bin/env python3
"""M289 - the LIVE founder-vector discriminator (session 235, ANALYSE pick).

Question (NEXT_PROMPT, M282 G5 frontier): WHICH founder vector does the LIVE
AI use to found bases - the action-dispatch leg (0x4408 via FUN_0052bce0),
the AI hub (FUN_0055f650), or the FUN_005a0aa0 faction-create chain?

M282's founder census: FUN_004e47d0(faction,x,y) is the ONLY live base-array
creator (record stride 0x130, count DAT_00985af4, cap 0x200).  Its three
image-wide callers: FUN_004cca50 (the live vector - 'b' hotkey via
FUN_004d1280, the in-game action dispatcher FUN_0052bce0 case 0x4408, and the
AI hub FUN_0055f650), FUN_0059ce10 (new-game placement), FUN_0059ec90
(faction-create - called by FUN_005a0aa0, the AI-mover chain, and by
FUN_005a0fa0, placement).  sim/basefound (B10) left the vector open: the
recorded golden trace carries no cover, so faction/coords are ASSUMED there.

This census arms ONE silent breakpoint PER VECTOR at the call site that is
UNIQUE to it (proof: the instruction image has exactly 3 call sites loading
FUN_004cca50 and exactly 3 loading FUN_0059ec90, one per caller body), plus
the founder entry (ret addr on the stack + fac/x/y args + the live count),
the destroyer -1 store, and a ~per-round sweep-entry control.  It then drives
the clean save with the AI for N turns with --no-orders (our side inert, so
the only founder dispatches possible are the AI's), detaches, and classifies
every founder hit by the vector site that fired just before it.

Sites (VAs; verified against scratch/m574/text.txt + ghidra_out/index.csv):
  into FUN_004cca50:  0x4d1d9c hotkey  (FUN_004d1280 body - player 'b' key)
                      0x52e0cc v4408   (FUN_0052bce0 case 0x4408)
                      0x563d86 hub     (FUN_0055f650 body)
  into FUN_0059ec90:  0x5a0b39 chain   (FUN_005a0aa0 body - AI mover chain)
                      0x5a123e place   (FUN_005a0fa0 body)
                      0x5a1277 place   (FUN_005a0fa0 body)
  founder entry       0x4e47d0  (FOUND; ret=*(int*)$esp, args at esp+4/8/12)
  destroyer count-1   0x4e515d  (DESTROY, inside FUN_004e4e10)
  sweep entry         0x4e8d60  (CTRL, ~once per round)
  count global        DAT_00985af4, year 0x985b00, cur_player 0x985dcc

Exit codes: 0 = measured verdict, 4 = NO MEASUREMENT (window ran, zero
founder hits AND zero count growth), 5 = driver wedged (no rounds advanced),
8 = box precondition dirty (tracer present / game down / yama could not be
toggled).  Every founder hit must classify to a known vector; the verdict is
the per-vector distribution with the pre-registered expectation that M282's
thesis (v4408) is tested against the two rivals.

Box facts (s235): m54b_clean.SAV reloaded via m54a_load --relaunch; game as
uid 1000; harness stays uid 1000; yama ptrace toggled around the window only.
"""
import os, re, signal, struct, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCR = os.path.join(ROOT, "scratch")
EVID = os.path.join(ROOT, "evidence")

# --- runtime VAs (verified; image base 0x400000 == Ghidra VA) ---
ADDR = {
    "hotkey": 0x4d1d9c,   # FUN_004d1280 -> call FUN_004cca50  (player 'b')
    "v4408":  0x52e0cc,   # FUN_0052bce0 -> call FUN_004cca50  (case 0x4408)
    "hub":    0x563d86,   # FUN_0055f650 -> call FUN_004cca50  (AI hub)
    "chain":  0x5a0b39,   # FUN_005a0aa0 -> call FUN_0059ec90  (AI mover chain)
    "place":  0x5a123e,   # FUN_005a0fa0 -> call FUN_0059ec90  (placement)
    "place2": 0x5a1277,
    "found":  0x4e47d0,   # FUN_004e47d0 entry (the founder)
    "destroy":0x4e515d,   # count -1 store inside FUN_004e4e10
    "ctrl":   0x4e8d60,   # economy sweep entry (~once/round)
}
CNT = 0x985AF4          # base-array count (DAT_00985af4)
YEAR = 0x985B00
CUR = 0x985DCC

# founder-entry return address -> which caller body the call came from
FOUND_CALLER = {0x4ccbe2: "CC50", 0x5a01fd: "EC90", 0x59d899: "59ce10"}
VEC_NAMES = ("hotkey", "v4408", "hub", "chain", "place", "place2")
CC50_VECS = {"hotkey", "v4408", "hub"}
EC90_VECS = {"chain", "place", "place2"}

gdb_script = r"""set pagination off
set confirm off
set verbose off
break *0x4d1d9c
commands
silent
printf "VEC hotkey\n"
continue
end
break *0x52e0cc
commands
silent
printf "VEC v4408\n"
continue
end
break *0x563d86
commands
silent
printf "VEC hub\n"
continue
end
break *0x5a0b39
commands
silent
printf "VEC chain\n"
continue
end
break *0x5a123e
commands
silent
printf "VEC place\n"
continue
end
break *0x5a1277
commands
silent
printf "VEC place2\n"
continue
end
break *0x4e47d0
commands
silent
printf "FOUND ret=%#x fac=%d x=%d y=%d cnt=%d\n", *(int *)($esp), *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+12), *(int *)0x985af4
continue
end
break *0x4e515d
commands
silent
printf "DESTROY cnt=%d\n", *(int *)0x985af4
continue
end
break *0x4e8d60
commands
silent
printf "CTRL\n"
continue
end
continue
"""


def rd32(m, a):
    try:
        return struct.unpack("<I", m[a:a + 4])[0]
    except OSError:
        return None


class Box:
    def __init__(self):
        self.pid = None
        self.mem = None

    def open(self):
        # pgrep -x matches the process NAME only (explorer.exe's argv also
        # contains "terran.exe", so a -f match returns the explorer too)
        out = subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True,
                             text=True).stdout.split()
        assert len(out) == 1, ("terran.exe not running or multiple: %s" % out)
        self.pid = int(out[0])
        self.mem = open("/proc/%d/mem" % self.pid, "rb", buffering=0)

    def tracer(self):
        st = open("/proc/%d/status" % self.pid).read()
        m = re.search(r"TracerPid:\s+(\d+)", st)
        return int(m.group(1))

    def vals(self):
        os.lseek(self.mem.fileno(), CNT, os.SEEK_SET)
        cnt = struct.unpack("<I", self.mem.read(4))[0]
        os.lseek(self.mem.fileno(), YEAR, os.SEEK_SET)
        yr = struct.unpack("<I", self.mem.read(4))[0]
        os.lseek(self.mem.fileno(), CUR, os.SEEK_SET)
        cu = struct.unpack("<I", self.mem.read(4))[0]
        return cnt, yr, cu


def yama_read():
    return int(open("/proc/sys/kernel/yama/ptrace_scope").read().strip())


def yama(val):
    r = subprocess.run(["sudo", "-n", "sh", "-c",
                        "echo %d > /proc/sys/kernel/yama/ptrace_scope" % val])
    return r.returncode == 0


def main():
    turns = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    tag = "m289"

    box = Box()
    box.open()
    t0 = box.tracer()
    if t0 != 0:
        print("PRECOND DIRTY: TracerPid=%d (a tracer already holds the game)" % t0)
        return 8
    cnt0, yr0, cu0 = box.vals()
    print("PRE-WINDOW: pid=%d count=%d year=%d cur=%d TracerPid=0" %
          (box.pid, cnt0, yr0, cu0))
    print("PREDICTIONS (pre-registered): M282 thesis says v4408 (action dispatch).")
    print("  Rivals: hub (0x5f650 direct) - 0 founder hits; chain (5a0aa0)"
          " - 0 founder hits.")
    print("  Every vector is mutually exclusive by construction (unique call site).")

    evpath = os.path.join(SCR, "m289_gdb_raw.log")
    os.makedirs(SCR, exist_ok=True)
    with open(os.path.join(SCR, "m289_census.gdb"), "w") as f:
        f.write(gdb_script)

    pre_yama = yama_read()
    if pre_yama != 0:
        if not yama(0):
            print("PRECOND DIRTY: could not clear yama ptrace_scope")
            return 8
    try:
        glog = open(evpath, "wb", buffering=0)
        gdb = subprocess.Popen(["stdbuf", "-o0", "gdb", "-q", "-batch",
                                "-x", os.path.join(SCR, "m289_census.gdb"),
                                "-p", str(box.pid)],
                               stdout=glog, stderr=subprocess.STDOUT)
        time.sleep(4)
        if gdb.poll() is not None:
            print("PRECOND DIRTY: gdb exited early (attach failed?)")
            glog.close()
            return 8

        env = dict(os.environ, DISPLAY=":99")
        dlog = open(os.path.join(SCR, "m289_drive.log"), "wb")
        drv = subprocess.Popen(
            ["python3", "scripts/smac_play.py", "--turns", str(turns),
             "--timeout", "300", "--no-escape", "2000", "--tag", tag,
             "--no-orders", "--no-verify", "--verbose"],
            cwd=ROOT, stdout=dlog, stderr=subprocess.STDOUT, env=env)
        try:
            rc = drv.wait(timeout=turns * 30 + 300)
        except subprocess.TimeoutExpired:
            drv.kill()
            rc = -99
        dlog.close()
        time.sleep(20)                      # let the last AI segment finish under the tracer
        if gdb.poll() is None:
            os.kill(gdb.pid, signal.SIGINT)
        else:
            print("WARN gdb already exited")
        for _ in range(60):
            if gdb.poll() is not None:
                break
            time.sleep(0.5)
        if gdb.poll() is None:
            gdb.terminate()
            time.sleep(2)
        glog.close()
        # resume the inferior in case it stopped at detach (m53n recipe)
        try:
            os.kill(box.pid, signal.SIGCONT)
        except OSError:
            pass
    finally:
        ok = yama(pre_yama)
    time.sleep(3)

    try:
        st_post = box.tracer()
        cnt1, yr1, cu1 = box.vals()
    except (OSError, FileNotFoundError):
        print("POST-WINDOW: game process gone (drv rc=%d) - box died under the census" % rc)
        return 5
    print("POST-WINDOW: count=%d year=%d cur=%d TracerPid=%d yama-restored=%s" %
          (cnt1, yr1, cu1, st_post, ok))

    events = []
    try:
        with open(evpath) as f:
            for ln in f:
                ln = ln.strip()
                if ln == "CTRL":
                    events.append(("CTRL", None))
                elif ln.startswith("VEC "):
                    events.append(("VEC", ln.split()[1]))
                elif ln.startswith("FOUND"):
                    m = re.match(r"FOUND ret=(0x[0-9a-f]+) fac=(\d+) x=(\d+) y=(\d+) cnt=(\d+)", ln)
                    if m:
                        events.append(("FOUND", {
                            "ret": int(m.group(1), 16), "fac": int(m.group(2)),
                            "x": int(m.group(3)), "y": int(m.group(4)),
                            "cnt": int(m.group(5))}))
                    else:
                        events.append(("FOUND?", ln))
                elif ln.startswith("DESTROY"):
                    m = re.match(r"DESTROY cnt=(\d+)", ln)
                    events.append(("DESTROY", int(m.group(1)) if m else None))
    except FileNotFoundError:
        pass

    ctrl = sum(1 for k, _ in events if k == "CTRL")
    if ctrl <= 0:
        print("NO CONTROL: zero sweep rows - the window never ran under gdb")
        return 5

    pend = None
    founds = []
    unpaired = 0
    for k, v in events:
        if k == "VEC":
            pend = v
        elif k == "FOUND":
            if not isinstance(v, dict):
                founds.append({"vec": "PARSE?", "ret": None})
                continue
            via = FOUND_CALLER.get(v["ret"])
            if via == "CC50":
                if pend in CC50_VECS:
                    vec = pend
                else:
                    vec = "UNPAIRED"
                    unpaired += 1
            elif via == "EC90":
                if pend in EC90_VECS:
                    vec = pend
                else:
                    vec = "UNPAIRED"
                    unpaired += 1
            else:
                vec = via or "UNKNOWN(ret=%#x)" % v["ret"]
            founds.append({"vec": vec, "ret": v["ret"], "fac": v["fac"],
                           "x": v["x"], "y": v["y"], "cnt": v["cnt"]})
            pend = None
        elif k == "DESTROY":
            pass  # accounting only; never touches the pending-vector pair

    # accounting walk: every FOUND must print the live count, which is
    # expected_u + 1 after the previous FOUND / -1 after the previous DESTROY
    expected = cnt0
    acct_ok = True
    acct_rows = []
    for e in events:
        if e[0] == "FOUND":
            v = e[1]
            if isinstance(v, dict):
                if v["cnt"] != expected:
                    acct_ok = False
                    acct_rows.append("MISMATCH cnt=%d expected=%d" % (v["cnt"], expected))
                expected += 1
        elif e[0] == "DESTROY":
            if e[1] is not None and e[1] != expected:
                acct_ok = False
                acct_rows.append("DESTROY cnt=%d expected=%d" % (e[1], expected))
            expected -= 1

    n_found = len(founds)
    vec_counts = {}
    for f in founds:
        vec_counts[f["vec"]] = vec_counts.get(f["vec"], 0) + 1

    rows = "\n".join(
        "  %2d  vec=%-10s ret=%#x fac=%d x=%d y=%d cnt=%d" %
        (i + 1, f["vec"], f["ret"], f["fac"], f["x"], f["y"], f["cnt"])
        for i, f in enumerate(founds))

    lines = []
    lines.append("M289 founder-vector census (session 235) - %d-turn window on m54b_clean.SAV" % turns)
    lines.append("PRE : count=%d year=%d cur=%d" % (cnt0, yr0, cu0))
    lines.append("POST: count=%d year=%d cur=%d tracer=%d yama=%d" %
                 (cnt1, yr1, cu1, st_post, 1 if ok else 0))
    lines.append("control: %d sweep rows | driver rc=%d | unpaired VEC=%d" % (ctrl, rc, unpaired))
    lines.append("accounting: %s (expected=%d box_end=%d late=%d)" %
                 ("ok" if acct_ok else "FAIL", expected, cnt1, cnt1 - expected))
    lines.append("founder hits: %d" % n_found)
    lines.append("per-vector: %s" % (vec_counts or "{}"))
    lines.append(rows)
    lines.append("")
    lines.append("VERDICT: %s" % ("MEASURED" if n_found else "NO MEASUREMENT"))

    out = "\n".join(lines)
    print(out)
    with open(os.path.join(EVID, "m289_founder_vector.txt"), "w") as f:
        f.write(out + "\n")

    if n_found == 0:
        return 4
    if not acct_ok:
        return 5
    unk = [f["vec"] for f in founds if f["vec"].startswith(("UN", "59ce10", "PARSE"))]
    if unk:
        print("UNCLASSIFIED FOUNDER HITS:", unk)
        return 5
    return 0


if __name__ == "__main__":
    sys.exit(main())
