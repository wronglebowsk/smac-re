#!/usr/bin/env python3
"""M292 - the POD MOVEMENT leg: which pod runs the hub vector FUN_0055f650, and
what its per-turn walk looks like vs the recorded founding turns (rises 6,9,18,19,22,23).

STATIC gates (bytes in terran.exe's .text; the cache scratch/m574/text.txt was the
transcription source, the file image below is the arbiter):
  G1 caller law: exactly TWO call sites reach 0x55f650 image-wide (0x50dd84 in
     FUN_0050d140, 0x56cf12 in FUN_0056cdf0); their return addresses are
     0x50dd89 / 0x56cf17.
  G2 hub arg1 = UNIT INDEX: 0x55f65c mov edi,[ebp+8]; the 0x55f6b8-bf fold
     13*edi then *4 (SIB) indexes the 52-B record array at 0x933278+52*u, owner
     byte +14 read vs ds:0x91b5b4 (0x55f6c0-cd). FUN_004cca50 folds the same
     52*u (0x4cca57-64) and reads owner@0x933286 y@0x93327a x@0x933278 (0x4cca67-74).
  G3 the dispatch at 0x563d46 keys on esi = the m291 RING ENTRY INDEX (0-24):
     esi==0 & not-own -> 0x563d82-86 push u; call 0x4cca50          (FOUND leg)
     esi==0 & own     -> 0x563d70 push 0x2408; 0x563d75 call 0x583fa0 (MSG leg)
     1<=esi<9         -> 0x563e06 dec esi -> continue (0x563e04 jge skips it)
     esi>=9           -> 0x563e12/0x563e1c load tables 0x678990[esi]/0x67850c[esi]
                         + own tile, wrap call 0x563e2c, then 0x563e3b
                         call 0x5560f0(u, 0x62, tile)  (ISS leg = the WALK order 'b')

LIVE gates (ONE box census window, m54b_clean t0 state, AI only, our side inert):
  G4 every HUB row's ret is one of the two known returns; >= 1 HUB row.
  G5 DISP esi in [0,24]; ownflag == (ownrec == curfac) on every DISP row (proves the
     52*u+14 owner-address arithmetic live); ISS rows all have esi >= 9; every FOUND
     pairs with the immediately preceding HUBFOUND of the same CTRL segment, x,y equal.
  G6 WALK: >= 1 founding pod was first seen by the hub at a DIFFERENT tile than its
     FOUND tile (the pod moved between hub visits).
  G7 >= 2 FOUNDs, on >= 2 distinct CTRL segments, from >= 2 distinct pod u.

Exit codes: 0 = measured verdict (PASS or documented FAIL with numbers), 4 = window
ran, zero FOUNDs (inconclusive, not a refutation), 5 = no CTRL rows / no year
movement (no measurement), 8 = box precondition dirty. Never weaken a floor.
"""
import os
import re
import signal
import struct
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCR = os.path.join(ROOT, "scratch")
EVID = os.path.join(ROOT, "evidence")

UNIT_X = 0x933278          # (short) x of record u at UNIT_X + 52*u
UNIT_Y = 0x93327A          # (short) y
UNIT_OW = 0x933286         # (byte)  owner
CNT = 0x985AF4
YEAR = 0x985B00
CUR = 0x985DCC
HUB_RET = {0x50dd89, 0x56cf17}
UCAP = 2500

# ---------------- static byte gates ----------------
TEXT_VA_LO, TEXT_VA_HI = 0x401000, 0x671000
EXPECT_BYTES = [
    (0x55f650, "558bec", "hub prologue"),
    (0x55f65c, "8b7d08", "mov edi,[ebp+8]  (arg1 -> edi)"),
    (0x55f6b8, "8d0c7f33c08d148f", "lea ecx,[edi+edi*2]; xor eax,eax; lea edx,[edi+ecx*4] (13u)"),
    (0x55f6c0, "8b0db4b59100", "mov ecx,ds:0x91b5b4"),
    (0x55f6c6, "8a049586329300", "mov al,[edx*4+0x933286]  (owner byte 52u+14)"),
    (0x55f6cd, "3bc1", "cmp eax,ecx"),
    (0x4cca57, "8b5d08", "mov ebx,[ebp+8]  (cc50 arg1)"),
    (0x4cca5d, "8d045b578d1c83c1e3", "fold ebx = 52*u (lea;push esi;lea;shl 2)"),
    (0x4cca67, "8a8b86329300", "mov cl,[ebx+0x933286] owner"),
    (0x4cca6d, "0fbf837a329300", "movsx eax,[ebx+0x93327a] y"),
    (0x4cca74, "0fbfbb78329300", "movsx edi,[ebx+0x933278] x"),
    (0x563d46, "85f6", "test esi,esi  (ring index dispatch)"),
    (0x563d48, "0f85ac000000", "jne 0x563dfa  (far leg)"),
    (0x563d54, "5685c07429", "push esi; test eax,eax; je 0x563d82 (own flag gate)"),
    (0x563d70, "6808240000", "push 0x2408"),
    (0x563d75, "e826020200", "call 0x583fa0  (MSG leg)"),
    (0x563d82, "8b450850", "mov eax,[ebp+8]; push u"),
    (0x563d86, "e8c58cf6ff", "call 0x4cca50  (FOUND leg)"),
    (0x563dfa, "83fe09", "cmp esi,0x9  (far-leg split)"),
    (0x563e04, "7d0c", "jge 0x563e12"),
    (0x563e06, "4e", "dec esi  (1-8: continue)"),
    (0x563e12, "8b14b590896700", "mov edx,[esi*4+0x678990]"),
    (0x563e1c, "8b04b50c856700", "mov eax,[esi*4+0x67850c]"),
    (0x563e2c, "e8df51f0ff", "call 0x469010 (wrap)"),
    (0x563e3b, "e8b022ffff", "call 0x5560f0  (ISS leg: order u,0x62,tile)"),
]


def load_text():
    d = open(os.path.join(ROOT, "terran.exe"), "rb").read()
    e = struct.unpack_from("<I", d, 0x3c)[0]
    nsec = struct.unpack_from("<H", d, e + 6)[0]
    optsz = struct.unpack_from("<H", d, e + 20)[0]
    sec = e + 24 + optsz
    for i in range(nsec):
        o = sec + 40 * i
        if d[o:o + 8].rstrip(b"\0") == b".text":
            vsize = struct.unpack_from("<I", d, o + 8)[0]
            vaddr = struct.unpack_from("<I", d, o + 12)[0]
            raddr = struct.unpack_from("<I", d, o + 20)[0]
            va0 = 0x400000 + vaddr
            return d, va0, vsize, raddr
    raise SystemExit(".text not found")


def static_gates():
    d, va0, vsize, raddr = load_text()

    def b(va, n):
        return d[raddr + (va - va0): raddr + (va - va0) + n]

    rows = []
    ok = True
    for va, hexs, note in EXPECT_BYTES:
        got = b(va, len(hexs) // 2).hex()
        good = got == hexs
        ok = ok and good
        rows.append("  %s %#x want %s got %s  ; %s" %
                    ("OK " if good else "BAD", va, hexs, got, note))
    # G1: exhaustive e8-scan for calls to 0x55f650
    calls = []
    base = raddr
    for va in range(va0, va0 + vsize - 5):
        i = base + (va - va0)
        if d[i] == 0xE8:
            rel = struct.unpack_from("<i", d, i + 1)[0]
            if (va + 5 + rel) == 0x55f650:
                calls.append(va)
    g1 = sorted(calls) == [0x50dd84, 0x56cf12]
    ok = ok and g1
    rows.append("  %s call sites to FUN_0055f650: %s (expect [0x50dd84, 0x56cf12])" %
                ("OK " if g1 else "BAD", [hex(c) for c in calls]))

    # G2/G3 grouping
    g2 = all(h == s for va, h, s in
             [(x[0], x[1], b(x[0], len(x[1]) // 2).hex()) for x in EXPECT_BYTES
              if 0x55f650 <= x[0] < 0x560000])
    g3 = all(h == s for va, h, s in
             [(x[0], x[1], b(x[0], len(x[1]) // 2).hex()) for x in EXPECT_BYTES
              if 0x563d46 <= x[0] <= 0x563e3b])
    g2 = g2 and all(h == s for va, h, s in
                    [(x[0], x[1], b(x[0], len(x[1]) // 2).hex()) for x in EXPECT_BYTES
                     if 0x4cca57 <= x[0] <= 0x4cca74])
    print("G1 (caller law: exactly 2 call sites): %s" % ("PASS" if g1 else "FAIL"))
    print("G2 (arg1 = unit index 52*u folds):     %s" % ("PASS" if g2 else "FAIL"))
    print("G3 (ring-index 3-leg dispatch):        %s" % ("PASS" if g3 else "FAIL"))
    print("\n".join(rows))
    return ok


# ---------------- live census ----------------
GDB_SCRIPT = """set pagination off
set confirm off
set verbose off
break *0x55f650
commands
silent
printf "HUB u=%d ret=%#x\\n", *(int *)($esp+4), *(int *)$esp
continue
end
break *0x563d46
commands
silent
set $u = *(int *)($ebp+8)
if $u >= 0 && $u < 2500
printf "DISP u=%d esi=%d st=%d own=%d ownrec=%d curfac=%d x=%d y=%d\\n", $u, $esi, *(int *)($ebp-0x44), *(int *)($ebp-0xa4), *(unsigned char *)(0x933286+52*$u), *(int *)0x91b5b4, *(short *)(0x933278+52*$u), *(short *)(0x93327a+52*$u)
else
printf "DISP u=%d oob\\n", $u
end
continue
end
break *0x563d75
commands
silent
printf "MSG u=%d\\n", $esi
continue
end
break *0x563d82
commands
silent
set $u = *(int *)($ebp+8)
if $u >= 0 && $u < 2500
printf "HUBFOUND u=%d x=%d y=%d\\n", $u, *(short *)(0x933278+52*$u), *(short *)(0x93327a+52*$u)
else
printf "HUBFOUND u=%d oob\\n", $u
end
continue
end
break *0x563e37
commands
silent
printf "ISS u=%d esi=%d tile=%d\\n", $ecx, $esi, $eax
continue
end
break *0x4e47d0
commands
silent
printf "FOUND ret=%#x fac=%d x=%d y=%d cnt=%d\\n", *(int *)($esp), *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+12), *(int *)0x985af4
continue
end
break *0x4e515d
commands
silent
printf "DESTROY cnt=%d\\n", *(int *)0x985af4
continue
end
break *0x4e8d60
commands
silent
printf "CTRL yr=%d cur=%d cnt=%d\\n", *(int *)0x985b00, *(int *)0x985dcc, *(int *)0x985af4
continue
end
continue
"""

ROW = re.compile(r"^(HUB|DISP|MSG|HUBFOUND|ISS|FOUND|DESTROY|CTRL)\b")


class Box:
    def __init__(self):
        self.pid = None
        self.mem = None

    def open(self):
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


def parse_log(path):
    rows = []
    with open(path) as f:
        for ln in f:
            ln = ln.strip()
            if not ROW.match(ln):
                continue
            rows.append(ln)
    return rows


def main():
    args = sys.argv[1:]
    if args and args[0] == "--static":
        ok = static_gates()
        print("STATIC %s" % ("PASS" if ok else "FAIL"))
        return 0 if ok else 1

    turns = 12
    if args and args[0] == "--turns":
        turns = int(args[1])
    tag = "m292"

    print("static gates first (no box):")
    if not static_gates():
        print("STATIC FAIL - not arming the box")
        return 1

    box = Box()
    box.open()
    if box.tracer() != 0:
        print("PRECOND DIRTY: TracerPid=%d" % box.tracer())
        return 8
    cnt0, yr0, cu0 = box.vals()
    print("PRE-WINDOW: pid=%d count=%d year=%d cur=%d TracerPid=0" %
          (box.pid, cnt0, yr0, cu0))
    print("PREDICTIONS (pre-registered): FOUNDs >= 2 on >= 2 segments from >= 2 pods;")
    print("  >=1 walking founding pod (first-seen tile != FOUND tile);")
    print("  hub entries ONLY from ret {0x50dd89, 0x56cf17}; DISP esi in [0,24];")
    print("  ISS only with esi >= 9; ownflag == (ownrec == curfac) on every DISP row.")

    os.makedirs(SCR, exist_ok=True)
    gpath = os.path.join(SCR, "m292_census.gdb")
    with open(gpath, "w") as f:
        f.write(GDB_SCRIPT)
    evpath = os.path.join(SCR, "m292_gdb_raw.log")

    pre_yama = yama_read()
    if pre_yama != 0:
        if not yama(0):
            print("PRECOND DIRTY: could not clear yama ptrace_scope")
            return 8
    try:
        glog = open(evpath, "wb", buffering=0)
        gdb = subprocess.Popen(["stdbuf", "-o0", "gdb", "-q", "-batch",
                                "-x", gpath, "-p", str(box.pid)],
                               stdout=glog, stderr=subprocess.STDOUT)
        time.sleep(4)
        if gdb.poll() is not None:
            print("PRECOND DIRTY: gdb exited early (attach failed?)")
            glog.close()
            return 8
        env = dict(os.environ, DISPLAY=":99")
        dlog = open(os.path.join(SCR, "m292_drive.log"), "wb")
        drv = subprocess.Popen(
            ["python3", "scripts/smac_play.py", "--turns", str(turns),
             "--timeout", "300", "--no-escape", "2000", "--tag", tag,
             "--no-orders", "--no-verify", "--verbose"],
            cwd=ROOT, stdout=dlog, stderr=subprocess.STDOUT, env=env)
        try:
            rc = drv.wait(timeout=turns * 90 + 300)
        except subprocess.TimeoutExpired:
            drv.kill()
            rc = -99
        dlog.close()
        time.sleep(20)
        if gdb.poll() is None:
            os.kill(gdb.pid, signal.SIGINT)
        for _ in range(60):
            if gdb.poll() is not None:
                break
            time.sleep(0.5)
        if gdb.poll() is None:
            gdb.terminate()
            time.sleep(2)
        glog.close()
        try:
            os.kill(box.pid, signal.SIGCONT)
        except OSError:
            pass
    finally:
        ok_y = yama(pre_yama)
    time.sleep(3)

    try:
        st_post = box.tracer()
        cnt1, yr1, cu1 = box.vals()
    except (OSError, FileNotFoundError):
        print("POST-WINDOW: game process gone (drv rc=%d)" % rc)
        return 5
    print("POST-WINDOW: count=%d year=%d cur=%d TracerPid=%d yama-restored=%s drv rc=%d" %
          (cnt1, yr1, cu1, st_post, ok_y, rc))

    if st_post != 0:
        print("BOX DIRTY: TracerPid=%d after census" % st_post)
        return 8

    rows = parse_log(evpath)
    hubs, disps, msgs, hubfounds, iss, founds, ctrl = [], [], [], [], [], [], []
    seg = 0
    last_disp_esi_own = None
    for ln in rows:
        if ln.startswith("CTRL"):
            m = re.match(r"CTRL yr=(\d+) cur=(\d+) cnt=(\d+)", ln)
            ctrl.append((m.group(1), m.group(2), m.group(3)) if m else None)
            seg += 1
        elif ln.startswith("HUB "):
            m = re.match(r"HUB u=(-?\d+) ret=(0x[0-9a-f]+)", ln)
            if m:
                hubs.append((int(m.group(1)), int(m.group(2), 16)))
        elif ln.startswith("DISP"):
            m = re.match(r"DISP u=(\d+) esi=(\d+) st=(\d+) own=(\d+) ownrec=(\d+) "
                         r"curfac=(\d+) x=(-?\d+) y=(-?\d+)", ln)
            disps.append(m.groups() if m else ("OOB",) + (None,) * 8)
        elif ln.startswith("MSG "):
            m = re.match(r"MSG u=(\d+)", ln)
            msgs.append((int(m.group(1)), seg) if m else None)
        elif ln.startswith("HUBFOUND"):
            m = re.match(r"HUBFOUND u=(\d+) x=(-?\d+) y=(-?\d+)", ln)
            hubfounds.append((int(m.group(1)), int(m.group(2)), int(m.group(3)), seg)
                             if m else None)
        elif ln.startswith("ISS "):
            m = re.match(r"ISS u=(\d+) esi=(\d+) tile=(-?\d+)", ln)
            iss.append((int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None)
        elif ln.startswith("FOUND "):
            m = re.match(r"FOUND ret=(0x[0-9a-f]+) fac=(\d+) x=(-?\d+) y=(-?\d+) cnt=(\d+)", ln)
            if m:
                founds.append({"ret": int(m.group(1), 16), "fac": int(m.group(2)),
                               "x": int(m.group(3)), "y": int(m.group(4)),
                               "cnt": int(m.group(5)), "seg": seg})

    print("rows: HUB=%d DISP=%d MSG=%d HUBFOUND=%d ISS=%d FOUND=%d CTRL=%d" %
          (len(hubs), len(disps), len(msgs), len(hubfounds), len(iss), len(founds), len(ctrl)))

    no_ctrl = len(ctrl) == 0
    yr_delta = yr1 - yr0
    if no_ctrl or yr_delta < turns // 2:
        print("NO MEASUREMENT: CTRL=%d year_delta=%d (driver rc=%d)" % (len(ctrl), yr_delta, rc))
        return 5

    # G4
    rets = set(r for _, r in hubs)
    g4 = len(hubs) >= 1 and rets <= HUB_RET
    # G5
    esi_vals = [int(d[1]) for d in disps if d[0] != "OOB"]
    own_ok = all(int(d[3]) == (1 if int(d[4]) == int(d[5]) else 0)
                 for d in disps if d[0] != "OOB")
    iss_ok = all(i[1] >= 9 for i in iss) if iss else False
    pairs_ok = True
    for f in founds:
        hf = None
        for h in reversed(hubfounds):
            if h and h[3] == f["seg"]:
                hf = h
                break
        if hf is None or hf[1] != f["x"] or hf[2] != f["y"]:
            pairs_ok = False
    g5 = (len(disps) >= 1 and esi_vals and all(0 <= v <= 24 for v in esi_vals)
          and own_ok and iss_ok and pairs_ok)
    # G6 walk
    first_seen = {}
    for d in disps:
        if d[0] == "OOB":
            continue
        u = int(d[0])
        if u not in first_seen:
            first_seen[u] = (int(d[6]), int(d[7]))
    walked = []
    for f in founds:
        hf = None
        for h in reversed(hubfounds):
            if h and h[3] == f["seg"]:
                hf = h
                break
        if hf is None:
            continue
        fs = first_seen.get(hf[0])
        if fs is not None and fs != (f["x"], f["y"]):
            walked.append((hf[0], fs, (f["x"], f["y"])))
    g6 = len(walked) >= 1
    # G7
    segs = set(f["seg"] for f in founds)
    podu = set()
    for f in founds:
        for h in reversed(hubfounds):
            if h and h[3] == f["seg"]:
                podu.add(h[0])
                break
    g7 = len(founds) >= 2 and len(segs) >= 2 and len(podu) >= 2

    if not founds:
        print("ZERO FOUNDs in the window: inconclusive (exit 4), gates G5-G7 not scored")
        for name, good in (("G1-G3 static", True), ("G4 caller law live", g4)):
            print("  %s: %s" % (name, "PASS" if good else "FAIL"))
        return 4

    print("ret distribution: %s" % sorted(hex(r) for _, r in hubs).
          __str__()[:120])
    esid = {}
    for v in esi_vals:
        esid[v] = esid.get(v, 0) + 1
    print("DISP esi histogram: %s" % sorted(esid.items()))
    print("walked pods (u, first-seen tile, FOUND tile):")
    for w in walked:
        print("  u=%d %s -> %s" % w)
    for i, f in enumerate(founds):
        print("  FOUND %d seg=%d fac=%d (%d,%d) cnt=%d" %
              (i + 1, f["seg"], f["fac"], f["x"], f["y"], f["cnt"]))

    gates = [("G1-G3 static", True), ("G4 caller law", g4),
             ("G5 ring-index + flag laws", g5), ("G6 walk", g6),
             ("G7 spread", g7)]
    npass = sum(1 for _, v in gates if v)
    for name, v in gates:
        print("  %-26s %s" % (name, "PASS" if v else "FAIL"))
    verdict = "PASS M292: %d/5" % npass if npass == 5 else "FAIL M292: %d/5" % npass
    print(verdict)

    # evidence
    with open(os.path.join(EVID, "m292_gdb_raw.log"), "w") as f:
        f.write("\n".join(rows) + "\n")
    with open(os.path.join(EVID, "m292_pod_movement.txt"), "w") as f:
        f.write("M292 POD MOVEMENT census (session 239) - %d-turn window, m54b_clean t0\n" % turns)
        f.write("PRE count=%d year=%d | POST count=%d year=%d TracerPid=%d drv rc=%d\n" %
                (cnt0, yr0, cnt1, yr1, st_post, rc))
        f.write("rows HUB=%d DISP=%d MSG=%d HUBFOUND=%d ISS=%d FOUND=%d CTRL=%d\n" %
                (len(hubs), len(disps), len(msgs), len(hubfounds), len(iss), len(founds), len(ctrl)))
        f.write("esi histogram %s\n" % sorted(esid.items()))
        f.write("walked %s\n" % walked)
        for name, v in gates:
            f.write("%-26s %s\n" % (name, "PASS" if v else "FAIL"))
        f.write(verdict + "\n")
    return 0 if npass == 5 else 1


if __name__ == "__main__":
    sys.exit(main())
