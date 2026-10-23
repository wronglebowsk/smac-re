#!/usr/bin/env python3
"""M48d: definitive mineral-economy round. Session 45.

Fixes every failure mode of m48a-h:
  * base identity: the base array SLIDES (m48h caught rep movsl at 0x64bfa3 moving
    record 73 into 72 while watches sat on the old window). We re-locate our base by
    CONTENT (owner==3) before arming, bake literal watch addresses for THAT address,
    arm a slide-detector bp on 0x64bfa3, and the year marker re-scans owner==3 every
    round so a mid-run slide is visible in the log.
  * the end-turn confirm: m48c_probe stalled because it only clicked the Yes row when
    the row was ALREADY blue; the confirm DEFAULTS to Cancel, so OK-click-only = Cancel
    forever. Here: for any flat blue bar in y 150-430, click (bar_x, bar_y-25) FIRST
    unconditionally, wait 1.3 s, then click the bar.
  * OCR load: colour-only fast loop; tesseract only as a >=35 s-stuck fallback via
    m44_idle.service_pane (one job at a time, pitfall 5).
  * gdb build traps (m48b/e lessons): literal watch addresses, no loop_break inside
    if-in-while in commands lists, no convenience vars in watch expressions, no
    `set print frame-verbosity`, every commands list ends with continue, and a
    SELFTEST block touches every address at script time.

Pokes (TracerPid 0, before arming): base+0x3c (production progress) = 500,
base+0xcc (production RATE -- ours reads 0, which is why the 2315 queue never
progresses) = 1, base+0x40 (mineral storage) = 200. Goal: force the completion path
(SPEND/CLAMP/MIRROR/QDRAIN/PRODUCEPROTO) to execute on OUR base under the armed
instrument, and catch the clamp that pins our storage to max(0, min(d0, cap)) live.

Usage: python3 scripts/m48d_drive.py --tag m48d --rounds 3 --budget 1500
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

GDB_TMPL = r"""# M51a instrument: does 0x4f26e0's gate early-return for OUR base, and WHICH instruction writes
# base+0x3c (production progress) and base+0x40 (mineral storage)?
# Identity anchor = the base NAME string at base+0x13 (0x4f5a70 passes DAT_008f0d60+0x13 to the
# rename/announce panes), printed at EVERY hit: the base array SLIDES (compaction moves records)
# and owner bytes change, so a bare index or a bare owner test is not a stable identity.
set pagination off
set confirm off
set can-use-hw-watchpoints 1
set $sw_p = -1
set $sw_i = -1
set $sw_n = 0
set $nsweep = 0
set $nvis = 0
set $nyear = 0
set $ngate = 0
set $nflag = 0
set $npast = 0
set $nconv = 0
set $nwp = 0
set $n40 = 0
set $n3c = 0

# ---- hardware watchpoints on OUR located record FIRST (the exhaustive net; literal addrs, armed
# after the pokes per M33). gdb prints Old/New itself; $eip sits just PAST the store. name_at is
# printed so a SLIDE of the array (another record moving into this slot) is visible in the log.
# ORDER MATTERS: gdb 17.1 on this i386-under-Wine target has a small debug-register budget and the
# 24 breakpoints below eat it, so watchpoints must claim their DR slots before the bps are inserted
# (m51a attempt 1 died with "Could not insert hardware watchpoint 26 / too many hardware
# breakpoints/watchpoints" and detached with zero hits).
watch *(int *)(@@ADDR@@ + 0x3c)
commands
  set $nwp = $nwp + 1
  printf "WP3C %d eip=%#x new=%d name_at=%s curbase=%#x ours_at=%d\n", $nwp, $eip, *(int *)(@@ADDR@@ + 0x3c), (char *)(@@ADDR@@ + 19), *(int *)0x8f0d60, *(int *)0x8f0d60 == @@ADDR@@
  continue
end
watch *(int *)(@@ADDR@@ + 0x40)
commands
  set $nwp = $nwp + 1
  printf "WP40 %d eip=%#x new=%d name_at=%s curbase=%#x ours_at=%d\n", $nwp, $eip, *(int *)(@@ADDR@@ + 0x40), (char *)(@@ADDR@@ + 19), *(int *)0x8f0d60, *(int *)0x8f0d60 == @@ADDR@@
  continue
end
# (m51a attempts 1-2: THREE hw watchpoints registered fine but gdb failed to insert one at the
# first resume -- "Could not insert hardware watchpoint 2 / too many hardware breakpoints/watchpoints"
# -- and the name watch at +19 was unaligned anyway; name= is printed at every bp hit, so the slide
# detector does not need a DR slot. TWO watchpoints = 2 of the 4 i386 DR slots.)

# ---- sweep identification (M50b instrument, kept) ----
# 0x520540(player): per-player sweep entry
break *0x520540
commands
  silent
  set $nsweep = $nsweep + 1
  set $sw_p = *(int *)($esp + 4)
  set $sw_i = 0
  set $sw_n = 0
  printf "SWEEP %d p=%d nb_entry=%d\n", $nsweep, $sw_p, *(int *)0x985af4
  continue
end

# 0x5206d3: call 0x4f5a70 for a base whose owner byte == player (ebx = base index)
break *0x5206d3
commands
  silent
  set $sw_n = $sw_n + 1
  set $nvis = $nvis + 1
  set $b = 0x95da10 + $ebx * 0x130
  printf "VISIT %d p=%d idx=%d owner=%d nb=%d ours=%d f3c=%d st=%d f38=%#x name=%s\n", $nvis, $sw_p, $ebx, *(unsigned char *)($b + 4), *(int *)0x985af4, $b == @@ADDR@@, *(int *)($b + 0x3c), *(int *)($b + 0x40), *(int *)($b + 0x38), (char *)($b + 19)
  if $b == @@ADDR@@
    bt 2
  end
  continue
end

# 0x5206f9: loop back edge (records how far the pass got)
break *0x5206f9
commands
  silent
  set $sw_i = $ebx - 1
  continue
end

# 0x5206fd: loop exit (or the n_bases<=0 fast path)
break *0x5206fd
commands
  silent
  printf "SWEEPEND p=%d last_idx=%d visits=%d nb_now=%d\n", $sw_p, $sw_i, $sw_n, *(int *)0x985af4
  continue
end

# 0x51f554: the year store - fires BETWEEN passes (M50b)
break *0x51f554
commands
  silent
  set $nyear = $nyear + 1
  printf "YEAR %d mid_p=%d mid_idx=%d mid_visits=%d nb=%d cur=%d\n", $nyear, $sw_p, $sw_i, $sw_n, *(int *)0x985af4, *(int *)0x985dcc
  continue
end

# ---- inside 0x4f26e0 (mineral<->energy conversion step, called from 0x4f5a70 at 0x4f5ae1) ----
# 0x4f2705 is the instruction AFTER the event-owner test 0x4f26ff (test BYTE ds:0x985b10, 1<<owner)
# and BEFORE the je at 0x4f2708, so it executes on EVERY call: owner==3 (mask low byte 0x08) falls
# through to the flag test, every other owner je's straight to the storage check 0x4f2724.
# edx = curbase = *(int*)0x8f0d60, loaded at 0x4f26e6 by the callee itself.
break *0x4f2705
commands
  silent
  set $ngate = $ngate + 1
  printf "GATE %d eip=%#x ebp=%#x curbase=%#x idx=%d owner=%d f38=%#x f3c=%d st=%d ours=%d name=%s\n", $ngate, $eip, $ebp, $edx, ($edx - 0x95da10) / 0x130, *(unsigned char *)($edx + 4), *(int *)($edx + 0x38), *(int *)($edx + 0x3c), *(int *)($edx + 0x40), $edx == @@ADDR@@, (char *)($edx + 19)
  continue
end

# 0x4f271e: jne 0x4f2e97 - REACHED ONLY BY EVENT OWNERS (everyone else je'd at 0x4f2708).
# ecx != 0 means the branch IS taken = 0x4f26e0 returns before any store. ecx = ((~f38>>0x1a)&0x20)
# | (~f38 & 0x20); f38 is the constant 0x00dfbe41 in every record, so ecx = 0x20 here always.
break *0x4f271e
commands
  silent
  set $nflag = $nflag + 1
  printf "FLAGTEST %d eip=%#x ebp=%#x ecx=%#x curbase=%#x owner=%d ours=%d name=%s\n", $nflag, $eip, $ebp, $ecx, $edx, *(unsigned char *)($edx + 4), $edx == @@ADDR@@, (char *)($edx + 19)
  continue
end

# 0x4f2724: the storage check, the ONLY way to reach the conversion body. A FLAGTEST line for frame
# ebp=X with NO PASTFLAG line for ebp=X proves the early return by execution (site absent), not by
# reading memory afterwards.
break *0x4f2724
commands
  silent
  set $npast = $npast + 1
  printf "PASTFLAG %d eip=%#x ebp=%#x curbase=%#x owner=%d st=%d ours=%d name=%s\n", $npast, $eip, $ebp, $edx, *(unsigned char *)($edx + 4), *(int *)($edx + 0x40), $edx == @@ADDR@@, (char *)($edx + 19)
  continue
end

# 0x4f2d7d: CONVST store [edi+0x40]=eax (edi = curbase set at 0x4f2d30, eax = NEW value).
break *0x4f2d7d
commands
  silent
  set $nconv = $nconv + 1
  printf "CONVST %d eip=%#x ebp=%#x store_to=%#x idx=%d owner=%d f38=%#x f3c=%d old40=%d new=%d ours=%d name=%s\n", $nconv, $eip, $ebp, $edi, ($edi - 0x95da10) / 0x130, *(unsigned char *)($edi + 4), *(int *)($edi + 0x38), *(int *)($edi + 0x3c), *(int *)($edi + 0x40), $eax, $edi == @@ADDR@@, (char *)($edi + 19)
  continue
end

# ---- EVERY static writer of base+0x40 in the per-base chain (0x4f5a70 and its callees) ----
# Conditional on the store's target register being OUR located record, so the print is identity-
# anchored by the name at the target and immune to a mid-round slide of the array.
break *0x4ef7f6 if $eax == @@ADDR@@
commands
  silent
  set $n40 = $n40 + 1
  printf "W40_IADD %d eip=%#x ebp=%#x target=%#x name=%s old=%d new=%d d0=%d cb=%#x\n", $n40, $eip, $ebp, $eax, (char *)($eax + 19), *(int *)($eax + 0x40), $edx, *(int *)($eax + 0xd0), *(int *)0x8f0d60
  continue
end
break *0x4efedd if $ecx == @@ADDR@@
commands
  silent
  set $n40 = $n40 + 1
  printf "W40_SPENDA %d eip=%#x ebp=%#x target=%#x name=%s old=%d new=%d edi=%d cb=%#x\n", $n40, $eip, $ebp, $ecx, (char *)($ecx + 19), *(int *)($ecx + 0x40), $esi, $edi, *(int *)0x8f0d60
  continue
end
break *0x4eff20 if $esi == @@ADDR@@
commands
  silent
  set $n40 = $n40 + 1
  printf "W40_CLAMP1 %d eip=%#x ebp=%#x target=%#x name=%s old=%d new=%d cap=%d ownmask=%d cb=%#x\n", $n40, $eip, $ebp, $esi, (char *)($esi + 19), *(int *)($esi + 0x40), $eax, *(int *)0x92a370, *(unsigned char *)($esi + 4), *(int *)0x8f0d60
  continue
end
break *0x4f0ca6 if $edx == @@ADDR@@
commands
  silent
  set $n40 = $n40 + 1
  printf "W40_SPENDB %d eip=%#x ebp=%#x target=%#x name=%s old=%d new=%d edi=%d cb=%#x\n", $n40, $eip, $ebp, $edx, (char *)($edx + 19), *(int *)($edx + 0x40), $esi, $edi, *(int *)0x8f0d60
  continue
end
break *0x4f0ce9 if $esi == @@ADDR@@
commands
  silent
  set $n40 = $n40 + 1
  printf "W40_CLAMP2 %d eip=%#x ebp=%#x target=%#x name=%s old=%d new=%d cap=%d cb=%#x\n", $n40, $eip, $ebp, $esi, (char *)($esi + 19), *(int *)($esi + 0x40), $eax, *(int *)0x92a370, *(int *)0x8f0d60
  continue
end

# ---- EVERY static writer of base+0x3c in the per-base chain ----
# 0x4e92c0 tail: +0x3c clamped to 0 (rate>=0) or -1 (rate<0); +0xcc (rate) is computed at 0x4e937b
break *0x4e9397 if $eax == @@ADDR@@
commands
  silent
  set $n3c = $n3c + 1
  printf "W3C_SET0 %d eip=%#x ebp=%#x target=%#x name=%s old=%d cc=%d cb=%#x\n", $n3c, $eip, $ebp, $eax, (char *)($eax + 19), *(int *)($eax + 0x3c), *(int *)($eax + 0xcc), *(int *)0x8f0d60
  continue
end
break *0x4e93a4 if $eax == @@ADDR@@
commands
  silent
  set $n3c = $n3c + 1
  printf "W3C_SETM1 %d eip=%#x ebp=%#x target=%#x name=%s old=%d cc=%d cb=%#x\n", $n3c, $eip, $ebp, $eax, (char *)($eax + 19), *(int *)($eax + 0x3c), *(int *)($eax + 0xcc), *(int *)0x8f0d60
  continue
end
# 0x4ee410 (called by 0x4f5a70 right AFTER 0x4f26e0): the production-progress accumulator
break *0x4ee56b if $eax == @@ADDR@@
commands
  silent
  set $n3c = $n3c + 1
  printf "W3C_E410A %d eip=%#x ebp=%#x target=%#x name=%s old=%d new=%d cc=%d cb=%#x\n", $n3c, $eip, $ebp, $eax, (char *)($eax + 19), *(int *)($eax + 0x3c), $ecx, *(int *)($eax + 0xcc), *(int *)0x8f0d60
  continue
end
break *0x4ee709 if $eax == @@ADDR@@
commands
  silent
  set $n3c = $n3c + 1
  printf "W3C_E410B %d eip=%#x ebp=%#x target=%#x name=%s old=%d new=%d cb=%#x\n", $n3c, $eip, $ebp, $eax, (char *)($eax + 19), *(int *)($eax + 0x3c), $ebx, *(int *)0x8f0d60
  continue
end
break *0x4ee72c if $edi == @@ADDR@@
commands
  silent
  set $n3c = $n3c + 1
  printf "W3C_E410C %d eip=%#x ebp=%#x target=%#x name=%s old=%d new=%d cb=%#x\n", $n3c, $eip, $ebp, $edi, (char *)($edi + 19), *(int *)($edi + 0x3c), $ebx, *(int *)0x8f0d60
  continue
end
break *0x4ee82f if $ecx == @@ADDR@@
commands
  silent
  set $n3c = $n3c + 1
  printf "W3C_E410D %d eip=%#x ebp=%#x target=%#x name=%s old=%d new=%d pop=%d cb=%#x\n", $n3c, $eip, $ebp, $ecx, (char *)($ecx + 19), *(int *)($ecx + 0x3c), $eax, *(unsigned char *)($ecx + 6), *(int *)0x8f0d60
  continue
end
break *0x4ee869 if $edi == @@ADDR@@
commands
  silent
  set $n3c = $n3c + 1
  printf "W3C_E410ZERO %d eip=%#x ebp=%#x target=%#x name=%s old=%d cb=%#x\n", $n3c, $eip, $ebp, $edi, (char *)($edi + 19), *(int *)($edi + 0x3c), *(int *)0x8f0d60
  continue
end
break *0x4ee8c7 if $edi == @@ADDR@@
commands
  silent
  set $n3c = $n3c + 1
  printf "W3C_E410ACCR %d eip=%#x ebp=%#x target=%#x name=%s old=%d new=%d cc=%d cb=%#x\n", $n3c, $eip, $ebp, $edi, (char *)($edi + 19), *(int *)($edi + 0x3c), $esi, *(int *)($edi + 0xcc), *(int *)0x8f0d60
  continue
end
# 0x4ef6d0 pipeline: stockpile-gated progress bump (non-event owners, 0x985aec>3) and pod clamp
break *0x4efb31 if $ecx == @@ADDR@@
commands
  silent
  set $n3c = $n3c + 1
  printf "W3C_PIPE %d eip=%#x ebp=%#x target=%#x name=%s old=%d new=%d stock=%d cb=%#x\n", $n3c, $eip, $ebp, $ecx, (char *)($ecx + 19), *(int *)($ecx + 0x3c), $edx, *(int *)0x985aec, *(int *)0x8f0d60
  continue
end
break *0x4f022b if $eax == @@ADDR@@
commands
  silent
  set $n3c = $n3c + 1
  printf "W3C_PODCLAMP %d eip=%#x ebp=%#x target=%#x name=%s old=%d cb=%#x\n", $n3c, $eip, $ebp, $eax, (char *)($eax + 19), *(int *)($eax + 0x3c), *(int *)0x8f0d60
  continue
end

# SELFTEST: touch every literal address + the name pointer at script time, pre-continue.
printf "SELFTEST addr=%#x owner=%d f38=%#x f3c=%d st=%d name=%s\n", @@ADDR@@, *(unsigned char *)(@@ADDR@@ + 4), *(int *)(@@ADDR@@ + 0x38), *(int *)(@@ADDR@@ + 0x3c), *(int *)(@@ADDR@@ + 0x40), (char *)(@@ADDR@@ + 19)
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
        for off, val in ((0x3c, 500), (0xcc, 1), (0xd0, 200), (0x40, 200)):
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
