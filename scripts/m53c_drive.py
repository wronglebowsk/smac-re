#!/usr/bin/env python3
"""M53c: who dequeues base+0x50 after a POSITIVE production completion? Session 54.

Static (evidence/m53c_*.txt): the only +0x50 writers are FUN_004e5560 (setter: head := new AND
per-player item counts old-1/new+1), FUN_004e46f0/FUN_004e47d0 (base init autocalc), FUN_00417ee0
(UI enqueue) and the clears 0x4f1e3f (pipeline tail, negative-only), FUN_00507ef0, FUN_005437d0.
0x4e5560's only caller is FUN_004e5ae0("re-pick via FUN_004f6030"), which the pipeline calls at
0x4ef87e/0x4f0589/0x4f08d4/0x4f09b6/0x4f1e01/0x4f21b8. Prediction for OUR base (f38=0x00dfbe41,
owner 3 IN mask 0xff08): no re-pick, no drain -> the head persists and re-completes.

Pokes (TracerPid 0, before arming): +0x50=2 (Scout Patrol), +0x54=3 (Transport Foil), +0x4c=1
(TWO-item queue), +0x3c=500, +0xcc=1, +0xd0=200, +0x40=200 (payable). Hardware watchpoints moved
off +0x3c/+0x40 onto +0x50/+0x4c. Soft bps: pipeline sites + 0x4e5ae0/0x4e5560/0x507ef0/0x5437d0/
0x417ee0 entries (any base, ours flag printed).

Usage: python3 scripts/m53c_drive.py --tag m53c --rounds 3 --budget 1100
"""
import argparse, json, os, signal, struct, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P
from PIL import Image
from m44_idle import service_pane, find_ok_bar, rightmost_blue_run
from m48_minerals import hud_up

BASE_ARR, BASE_STRIDE = 0x95da10, 0x130
ENERGY_ADDR = 0x953884          # our faction record +0 (stride 0x20bc bytes)
EVID = P.EVID
OUR_BASE_NAME = "Climactic Research"   # our ONLY base (founded M45; name string lives at base+0x13,
                                      # which 0x4f5a70 passes to the announce/rename panes)

GDB_TMPL = r"""# M53c instrument: WHO advances base+0x50 after a POSITIVE completion?
# Static (see evidence/m53c_*): the ONLY +0x50 writers in the corpus are FUN_004e5560 (the setter:
# head := new AND per-player item count old-1 / new+1 at 0x94de84+owner*0x20bc+id), FUN_004e46f0 /
# FUN_004e47d0 (base init autocalc), FUN_00417ee0 (UI enqueue) and the clears 0x4f1e3f (pipeline
# tail, negative-only), FUN_00507ef0, FUN_005437d0. FUN_004e5560 has exactly ONE caller chain:
# FUN_004e5ae0(base,0) = "re-pick via FUN_004f6030", called from the pipeline at 0x4ef87e / 0x4f0589
# / 0x4f08d4 / 0x4f09b6 / 0x4f1e01 / 0x4f21b8 (M53a's disasm dump stopped at 0x4f1d5d, which is why
# the tail sites 0x4f1e01/0x4f1e3f/0x4f21b8 looked absent). Gates: 0x4f1e01 needs (base+0x38 bit0 AND
# bit31 AND [ebp-0x10]==0) OR (1<<owner)&mask==0; 0x4f1e3f needs owner IN mask AND NOT(f38&0x80000001
# ==0x80000001) AND head == -[ebp-0x30] AND +0x4c==0. Our base has f38=0x00dfbe41 (bit31 clear) and
# owner 3 IN mask 0xff08, so the prediction is: NEITHER fires -> the head persists.
# Live test: 2-item queue (+0x50=2 Scout Patrol, +0x54=3 Transport Foil, +0x4c=1), storage 200.
set pagination off
set confirm off
set can-use-hw-watchpoints 1
set $nwp50 = 0
set $nwp4c = 0
set $nq = 0
set $nc = 0
set $nyear = 0
set $nsp = 0
set $ncl = 0
set $nrp = 0
set $ndrain = 0
set $n5ae0 = 0
set $n5560 = 0
set $n7ef0 = 0
set $n37d0 = 0
set $nenq = 0

# ---- hardware watchpoints FIRST (2 of 4 i386 DR slots; the +0x3c story is closed, so +0x50 and
# +0x4c take the slots). $eip sits just PAST the store; name_at detects an array slide.
watch *(int *)(@@ADDR@@ + 0x50)
commands
  set $nwp50 = $nwp50 + 1
  printf "WP50 %d eip=%#x new=%d f54=%d f4c=%d f44=%d name_at=%s cb=%#x ours_at=%d\n", $nwp50, $eip, *(int *)(@@ADDR@@ + 0x50), *(int *)(@@ADDR@@ + 0x54), *(int *)(@@ADDR@@ + 0x4c), *(int *)(@@ADDR@@ + 0x44), (char *)(@@ADDR@@ + 19), *(int *)0x8f0d60, *(int *)0x8f0d60 == @@ADDR@@
  continue
end
watch *(int *)(@@ADDR@@ + 0x4c)
commands
  set $nwp4c = $nwp4c + 1
  printf "WP4C %d eip=%#x new=%d f50=%d f54=%d name_at=%s cb=%#x ours_at=%d\n", $nwp4c, $eip, *(int *)(@@ADDR@@ + 0x4c), *(int *)(@@ADDR@@ + 0x50), *(int *)(@@ADDR@@ + 0x54), (char *)(@@ADDR@@ + 19), *(int *)0x8f0d60, *(int *)0x8f0d60 == @@ADDR@@
  continue
end

# ---- round marker ----
break *0x51f554
commands
  silent
  set $nyear = $nyear + 1
  printf "YEAR %d year=%d turn=%d cur=%d nb=%d\n", $nyear, *(int *)0x985b00, *(int *)0x985afc, *(int *)0x985dcc, *(int *)0x985af4
  continue
end

# ---- OUR base: pipeline entry + completion (NAME-conditioned, slide-proof) ----
break *0x4ef6d0 if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $nq = $nq + 1
  printf "QPIPE %d name=%s f50=%d f54=%d f58=%d f5c=%d f4c=%d f44=%d f68=%d st=%d f3c=%d fcc=%d d0=%d f38=%#x\n", $nq, (char *)(*(int *)0x8f0d60 + 19), *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x54), *(int *)(*(int *)0x8f0d60 + 0x58), *(int *)(*(int *)0x8f0d60 + 0x5c), *(int *)(*(int *)0x8f0d60 + 0x4c), *(int *)(*(int *)0x8f0d60 + 0x44), *(int *)(*(int *)0x8f0d60 + 0x68), *(int *)(*(int *)0x8f0d60 + 0x40), *(int *)(*(int *)0x8f0d60 + 0x3c), *(int *)(*(int *)0x8f0d60 + 0xcc), *(int *)(*(int *)0x8f0d60 + 0xd0), *(int *)(*(int *)0x8f0d60 + 0x38)
  continue
end
break *0x4efe41 if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $nc = $nc + 1
  printf "QCOMPLET %d name=%s f50=%d f54=%d f4c=%d f44=%d st=%d ebx=%d m1c=%d m30=%d m10=%d\n", $nc, (char *)(*(int *)0x8f0d60 + 19), *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x54), *(int *)(*(int *)0x8f0d60 + 0x4c), *(int *)(*(int *)0x8f0d60 + 0x44), *(int *)(*(int *)0x8f0d60 + 0x40), $ebx, *(int *)($ebp - 0x1c), *(int *)($ebp - 0x30), *(int *)($ebp - 0x10)
  continue
end
break *0x4efed8 if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $nsp = $nsp + 1
  printf "SPENDA %d st=%d cost_edi=%d f50=%d f4c=%d\n", $nsp, *(int *)(*(int *)0x8f0d60 + 0x40), $edi, *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x4c)
  continue
end
break *0x4eff20 if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $ncl = $ncl + 1
  printf "CLAMP1 %d esi=%#x st=%d f50=%d f4c=%d\n", $ncl, $esi, *(int *)($esi + 0x40), *(int *)($esi + 0x50), *(int *)($esi + 0x4c)
  continue
end

# ---- the six pipeline re-pick call sites (0x4e5ae0) + the tail clear (0x4f1e3f) ----
break *0x4ef87e if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $nrp = $nrp + 1
  printf "REPICK_EARLY %d f50=%d f4c=%d f38=%#x m10=%d\n", $nrp, *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x4c), *(int *)(*(int *)0x8f0d60 + 0x38), *(int *)($ebp - 0x10)
  continue
end
break *0x4f0589 if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $nrp = $nrp + 1
  printf "REPICK_A %d f50=%d f4c=%d f38=%#x edi=%d\n", $nrp, *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x4c), *(int *)(*(int *)0x8f0d60 + 0x38), $edi
  continue
end
break *0x4f08d4 if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $nrp = $nrp + 1
  printf "REPICK_B %d f50=%d f4c=%d m30=%d\n", $nrp, *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x4c), *(int *)($ebp - 0x30)
  continue
end
break *0x4f09b6 if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $nrp = $nrp + 1
  printf "REPICK_C %d f50=%d f4c=%d m30=%d\n", $nrp, *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x4c), *(int *)($ebp - 0x30)
  continue
end
break *0x4f1e01 if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $nrp = $nrp + 1
  printf "REPICK_TAIL %d f50=%d f4c=%d f38=%#x m10=%d m2c=%d\n", $nrp, *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x4c), *(int *)(*(int *)0x8f0d60 + 0x38), *(int *)($ebp - 0x10), *(int *)($ebp - 0x2c)
  continue
end
break *0x4f21b8 if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $nrp = $nrp + 1
  printf "REPICK_PROJ %d f50=%d f4c=%d m30=%d\n", $nrp, *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x4c), *(int *)($ebp - 0x30)
  continue
end
break *0x4f1e3f if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $ndrain = $ndrain + 1
  printf "QDRAIN %d f50=%d f54=%d f4c=%d m30=%d\n", $ndrain, *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x54), *(int *)(*(int *)0x8f0d60 + 0x4c), *(int *)($ebp - 0x30)
  continue
end

# ---- the writers themselves (any base; ours=1 marks OUR record) ----
break *0x4e5ae0
commands
  silent
  set $n5ae0 = $n5ae0 + 1
  printf "SET_REPICK %d base_idx=%d param2=%d ours=%d head=%d f4c=%d cb_idx=%d\n", $n5ae0, *(int *)($esp + 4), *(int *)($esp + 8), *(int *)($esp + 4) == *(int *)0x68cbb0, *(int *)(0x95da10 + *(int *)($esp + 4) * 0x130 + 0x50), *(int *)(0x95da10 + *(int *)($esp + 4) * 0x130 + 0x4c), *(int *)0x68cbb0
  continue
end
break *0x4e5560
commands
  silent
  set $n5560 = $n5560 + 1
  printf "SET_HEAD %d base_idx=%d new=%d ours=%d OLD_head=%d OLD_f4c=%d cb_idx=%d\n", $n5560, *(int *)($esp + 4), *(int *)($esp + 8), *(int *)($esp + 4) == *(int *)0x68cbb0, *(int *)(0x95da10 + *(int *)($esp + 4) * 0x130 + 0x50), *(int *)(0x95da10 + *(int *)($esp + 4) * 0x130 + 0x4c), *(int *)0x68cbb0
  continue
end
break *0x507ef0
commands
  silent
  set $n7ef0 = $n7ef0 + 1
  printf "CLR_507EF0 %d p1=%d p2=%#x ours=%d head=%d f4c=%d\n", $n7ef0, *(int *)($esp + 4), *(int *)($esp + 8), *(int *)($esp + 4) == *(int *)0x68cbb0, *(int *)(0x95da10 + *(int *)($esp + 4) * 0x130 + 0x50), *(int *)(0x95da10 + *(int *)($esp + 4) * 0x130 + 0x4c)
  continue
end
break *0x5437d0
commands
  silent
  set $n37d0 = $n37d0 + 1
  printf "CLR_5437D0 %d p1=%d p2=%#x ours=%d head=%d f4c=%d\n", $n37d0, *(int *)($esp + 4), *(int *)($esp + 8), *(int *)($esp + 4) == *(int *)0x68cbb0, *(int *)(0x95da10 + *(int *)($esp + 4) * 0x130 + 0x50), *(int *)(0x95da10 + *(int *)($esp + 4) * 0x130 + 0x4c)
  continue
end
break *0x417ee0
commands
  silent
  set $nenq = $nenq + 1
  printf "ENQ_417EE0 %d p1=%#x p2=%#x p3=%#x\n", $nenq, *(int *)($esp + 4), *(int *)($esp + 8), *(int *)($esp + 0xc)
  continue
end

# SELFTEST: touch every literal address + the name pointer at script time, pre-continue.
printf "SELFTEST addr=%#x owner=%d f38=%#x f3c=%d st=%d f50=%d f54=%d f4c=%d name=%s\n", @@ADDR@@, *(unsigned char *)(@@ADDR@@ + 4), *(int *)(@@ADDR@@ + 0x38), *(int *)(@@ADDR@@ + 0x3c), *(int *)(@@ADDR@@ + 0x40), *(int *)(@@ADDR@@ + 0x50), *(int *)(@@ADDR@@ + 0x54), *(int *)(@@ADDR@@ + 0x4c), (char *)(@@ADDR@@ + 19)
printf "ARMED\n"
continue
"""



def squash(words):
    import re
    return re.sub(r"[^a-z]", "", " ".join(w[0] for w in words).lower())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m48d")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--budget", type=float, default=1500.0)
    ap.add_argument("--no-poke", action="store_true")
    ap.add_argument("--stop", metavar="TAG",
                    help="SIGINT the driver recorded for TAG (pidfile) and exit")
    a = ap.parse_args()
    if a.stop:
        # Safe stop: signal ONLY the pid this tag recorded, after proving that pid is a python
        # process running this script. Never `pkill -f <script>`: inside an agent session the
        # parent's argv contains the prompt, which quotes the filename, so a name match SIGINTs
        # the agent itself (happened twice in M51a, exit 130, gdb left attached).
        pf = f"evidence/{a.stop}_driver.pid"
        try:
            dp = int(open(pf).read().strip())
        except (OSError, ValueError):
            print(f"no driver pid recorded in {pf}"); return 1
        try:
            with open(f"/proc/{dp}/cmdline", "rb") as fh:
                parts = fh.read().split(b"\0")
            exe = os.path.basename(parts[0].decode(errors="ignore"))
            args = [q.decode(errors="ignore") for q in parts[1:] if q]
            # The recorded pid runs SOME *_drive.py with this tag; the script name need not
            # encode the tag (one driver serves many tags).
            ok = (exe.startswith("python")
                  and any(q.endswith("_drive.py") for q in args)
                  and a.stop in args)
        except OSError:
            ok = False
        if not ok:
            print(f"pid {dp} is not the {a.stop} driver; refusing"); return 1
        os.kill(dp, signal.SIGINT)
        print(f"SIGINT -> {dp}"); return 0
    tag, t0 = a.tag, time.time()
    rec = {"tag": tag, "t": time.strftime("%F %T"), "events": [], "rounds": []}
    os.makedirs("evidence", exist_ok=True)
    with open(f"evidence/{tag}_driver.pid", "w") as fh:
        fh.write(str(os.getpid()))

    # Kill stale same-tag drivers, but only real python drivers. A bare pgrep on the script name
    # also matches any parent whose argv merely mentions it -- an agent prompt quoting the filename
    # got its own Hermes SIGINTed this way (M51a, exit 130, gdb left attached) -- so each candidate's
    # /proc/PID/cmdline is checked for a python interpreter running THIS script before signalling.
    def _is_driver(pid_s, tag):
        try:
            with open(f"/proc/{pid_s}/cmdline", "rb") as fh:
                parts = fh.read().split(b"\0")
        except OSError:
            return False
        exe = os.path.basename(parts[0].decode(errors="ignore"))
        if not exe.startswith("python"):
            return False
        want = f"{tag}_drive.py"
        return any(p.decode(errors="ignore").endswith(want) for p in parts[1:] if p)

    for pid_s in subprocess.run(["pgrep", "-f", f"{tag}_drive\\.py"],
                                capture_output=True, text=True).stdout.split():
        if int(pid_s) != os.getpid() and _is_driver(pid_s, tag):
            try:
                os.kill(int(pid_s), signal.SIGINT)
            except ProcessLookupError:
                pass
    time.sleep(1)
    if subprocess.run(["pgrep", "-x", "gdb"], capture_output=True, text=True).stdout.strip():
        print("ABORT: a gdb is already running"); return 1
    pid = int(subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True,
                             text=True).stdout.split()[0])
    rec["pid"] = pid

    def tracer():
        out = subprocess.run(["grep", "TracerPid", f"/proc/{pid}/status"],
                             capture_output=True, text=True).stdout
        return int(out.split()[-1])
    assert tracer() == 0, "tracer attached before run"

    ro = os.open(f"/proc/{pid}/mem", os.O_RDONLY)

    def i32(addr):
        return struct.unpack("<i", os.pread(ro, 4, addr))[0]

    def locate():
        """M51a identity anchor: the NAME string at base+0x13, not the index and not the owner byte.

        The array SLIDES (records compact when a base is destroyed) and the owner byte changes
        (capture), so M50a's 'owner 3 at idx N' and M50b's 'owner 2 at idx N' were both readings of
        whichever record happened to sit in that slot. Match by name; owner==3 is only a fallback,
        and every match is logged so a slide is visible instead of inferred.
        """
        nb = i32(0x985af4)
        blob = os.pread(ro, nb * BASE_STRIDE, BASE_ARR)
        recs = []
        for i in range(nb):
            r = blob[i * BASE_STRIDE:(i + 1) * BASE_STRIDE]
            g = lambda o: struct.unpack("<i", r[o:o + 4])[0]
            recs.append(dict(idx=i, addr=BASE_ARR + i * BASE_STRIDE, owner=r[4],
                             name=r[19:39].split(b"\0")[0].decode("latin1", "replace"),
                             pop=r[6], min40=g(0x40), q50=g(0x50), d0=g(0xd0),
                             c0=g(0xc0), cc=g(0xcc), f3c=g(0x3c), fc=g(0xfc), f38=g(0x38)))
        byname = [r for r in recs if r["name"] == OUR_BASE_NAME]
        byown = [r for r in recs if r["owner"] == 3]
        hits = byname or byown
        if not hits:
            return None
        loc = dict(hits[0])
        loc["anchor"] = "name" if byname else "owner3"
        loc["n_name_matches"] = len(byname)
        loc["n_owner3_matches"] = len(byown)
        loc["owner3_matches"] = [(r["idx"], r["name"]) for r in byown]
        return loc

    loc = locate()
    if not loc:
        print("ABORT: no owner==3 base"); return 1
    rec["locate"] = loc
    print(f"[locate] {loc}", flush=True)
    addr = loc["addr"]
    MIN40, Q50, D0 = addr + 0x40, addr + 0x50, addr + 0xd0
    SLO, SHI = addr - 0x130, addr + 0x260

    # ---- pokes (TracerPid 0) ----
    if not a.no_poke:
        assert tracer() == 0
        rw = os.open(f"/proc/{pid}/mem", os.O_RDWR)
        for off, val in ((0x50, 2), (0x54, 3), (0x4c, 1), (0x3c, 500), (0xcc, 1), (0xd0, 200), (0x40, 200)):
            os.pwrite(rw, struct.pack("<i", val), addr + off)
            got = struct.unpack("<i", os.pread(rw, 4, addr + off))[0]
            rec["events"].append(f"poked +{hex(off)} -> {got}")
            print(f"[poke] +{hex(off)} = {got}", flush=True)
        os.close(rw)

    # ---- generated gdb script ----
    txt = GDB_TMPL
    for k, v in (("@@ADDR@@", hex(addr)), ("@@MIN40@@", hex(MIN40)),
                 ("@@Q50@@", hex(Q50)), ("@@D0@@", hex(D0)),
                 ("@@NRG@@", hex(ENERGY_ADDR)), ("@@SLO@@", hex(SLO)),
                 ("@@SHI@@", hex(SHI))):
        txt = txt.replace(k, v)
    gpath = f"evidence/{tag}_watch.gdb"
    open(gpath, "w").write(txt)
    lpath = f"{EVID}/{tag}_watch.log"

    # ---- arm ----
    lf = open(lpath, "wb")
    g = subprocess.Popen(["gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=lf, stderr=subprocess.STDOUT)
    rec["gdb_pid"] = g.pid
    time.sleep(7)
    rec["events"].append("gdb launched")
    print("[gdb] armed (log block-buffered; read after detach)", flush=True)

    # ---- driver loop (colour-first) ----
    year0 = i32(0x985b00)
    year = year0
    last_click = last_freeze = last_ocr = t0
    ocr_passes = svc_clicks = 0
    stuck_since = t0

    def state():
        loc = locate()
        return dict(year=i32(0x985b00), turn=i32(0x985afc), cur=i32(0x985dcc),
                    nb=i32(0x985af4), nrg3=i32(ENERGY_ADDR),
                    base=loc or {"GONE": 1})

    rounds_done = 0
    while time.time() - t0 < a.budget and rounds_done < a.rounds:
        now = time.time()
        y = i32(0x985b00)
        if y != year:
            st = state()
            rec["rounds"].append({"dt": round(now - t0, 1), **st})
            rec["events"].append(f"year {year}->{y} cur={st['cur']} "
                                 f"min40={st['base'].get('min40')} q50={st['base'].get('q50')}")
            year = y
            rounds_done += 1
            stuck_since = now
            time.sleep(10)
            continue
        if now - last_freeze > 4.0:
            last_freeze = now
            P.focus()
            png = P.freeze(tag)
            # colour dismiss
            ob = rightmost_blue_run(png, band=(240, 150, 560, 430))
            if ob:
                bx, by = ob
                P.click((bx, by - 25))
                time.sleep(1.3)
                P.click((bx, by))
                rec["events"].append(f"colour: row(bar_y-25)+bar at ({bx},{by})")
                svc_clicks += 1
                time.sleep(1.0)
                continue
            bar = find_ok_bar(png)
            if bar:
                P.click(bar)
                rec["events"].append(f"colour: ok-bar click {bar}")
                svc_clicks += 1
                time.sleep(1.0)
                continue
            s = state()
            if s["cur"] == 3 and hud_up(png) and now - last_click > 9.0:
                P.click(P.TURN_BTN)
                last_click = now
                rec["events"].append("clicked TURN_BTN")
                continue
        if now - stuck_since > 35.0 and now - last_ocr > 20.0:
            last_ocr = now
            P.focus()
            png = P.freeze(tag + "_ocr")
            words = P.ocr(png)
            ocr_passes += 1
            body = squash(words)
            kind = P.classify(words, png=png)
            bar = find_ok_bar(png)

            def row_y(word):
                for w, x, y, c in words:
                    if word in w.lower():
                        return y
                return None

            if "tour" in body and "continue" in body:
                P.click((325, 585))
                rec["events"].append("ocr: TOUR popup -> Continue (325,585)")
            elif "socialengineering" in body or ("politics" in body and "society" in body):
                P.click((240, 368))
                rec["events"].append("ocr: Social Engineering screen -> OK (240,368)")
            elif "channel" in body and "through" in body:
                # 3-row COMM OFFICER variant (M50b). A click only highlights the
                # row and the bar cycle drifts onto "Display faction leader
                # profile" (University Intelligence Files, ~8 min drain).
                # Keyboard is deterministic: selection starts on row 1, so one
                # Down lands on "No, close the channel.", Return commits it.
                P.key("Down")
                time.sleep(0.4)
                P.key("Return")
                rec["events"].append("ocr: comm pane -> Down+Return (close channel)")
            elif ("intelligence" in body and "files" in body) or "leader profile" in body:
                # The leader-profile pane is the 8-minute drain the comm pane falls into. It has
                # no dismissible row the colour driver understands; Escape leaves it (verified).
                P.key("Escape")
                rec["events"].append("ocr: leader-profile pane -> Escape")
            elif "disband" in body and "nevermind" in body:
                ob2 = rightmost_blue_run(png, band=(240, 150, 560, 430))
                if ob2:
                    P.click(ob2)
                elif bar:
                    P.click(bar)
                rec["events"].append("ocr: CONFIRM DISBAND -> cancel via OK bar only")
            elif any(k in body for k in ("ecologist", "mindworm", "spotted",
                                          "convenes", "agenda", "measure",
                                          "breakthrough", "discovery")):
                P.key("Return")
                rec["events"].append(f"ocr-fallback: Return on '{body[:40]}'")
            elif not service_pane(png, words, body, kind, rec, "drive", bar=bar):
                if "book" in body or "skim" in body or len(words) > 25:
                    P.click((400, 470))
                    rec["events"].append("ocr-fallback: click (400,470) story page")
                elif "overall" in body or "territory" in body:
                    P.click((400, 580))
                    rec["events"].append("ocr-fallback: click (400,580) table")
                else:
                    P.key("Return")
                    rec["events"].append(f"ocr-fallback: Return generic '{body[:40]}'")
            time.sleep(2)
        time.sleep(2)

    rec["reason"] = "rounds" if rounds_done >= a.rounds else "budget"
    rec["final"] = state()
    rec["ocr_passes"], rec["svc_clicks"] = ocr_passes, svc_clicks

    # ---- cleanup ----
    g.send_signal(signal.SIGINT)
    t1 = time.time()
    detached = False
    while time.time() - t1 < 60:
        try:
            if b"detached" in open(lpath, "rb").read():
                detached = True
                break
        except Exception:
            pass
        time.sleep(2)
    rec["detached"] = detached
    try:
        subprocess.run(["kill", "-CONT", str(pid)])
    except Exception:
        pass
    g.wait(timeout=30)
    os.close(ro)
    json.dump(rec, open(f"{EVID}/{tag}_drive.json", "w"), indent=1)
    print(json.dumps({"reason": rec["reason"], "year0": year0,
                      "final_year": rec["final"]["year"], "ocr_passes": ocr_passes,
                      "rounds": len(rec["rounds"])}))


def dismiss(png):
    ob = rightmost_blue_run(png, band=(240, 150, 560, 430))
    if ob:
        bx, by = ob
        P.click((bx, by - 25))
        time.sleep(1.3)
        P.click((bx, by))
        return True
    bar = find_ok_bar(png)
    if bar:
        P.click(bar)
        return True
    return False


if __name__ == "__main__":
    raise SystemExit(main())
