#!/usr/bin/env python3
"""M106 — the load-window restore a HARDWARE watchpoint cannot see.

M105 (m105s4 PASS 17/17): the per-faction 1436-byte record block 0x927a9c+fac*1436 is BUILT AT PROCESS
START by FUN_005791c0's append loop (15 count increments, every one reporting 0x579b12), and the
save load logged ZERO count events while its own ROUND control fired in the same window — yet the -77
sentinels poked WHILE ARMED came back to the save image. Something writes those pages with no
store that a ring-3 DR watchpoint can see.

THE TEST — no gdb at all (a gdb census cannot see a kernel copy either, and strace and gdb cannot both
ptrace the same task). Relaunch terran.exe, snapshot the region + its VMAs + its page frame numbers,
poke distinct sentinels into all EIGHT count dwords (stride 1436, so the poke spans the whole 11488-byte
region), clear the soft-dirty bits, then run ONE m54b_clean load under two straces:
  A: terran.exe, raw-arg read/pread64/write/mmap/mprotect/mremap/munmap/process_vm_writev (raw mode
     prints the BUFFER POINTER, which is the whole point — `-a 0` still prints content, `-e raw=` does not);
  B: the rest of the wine tree (wineserver/winedevice/explorer/services), the out-of-process writers.
Then read the effect back: the VMAs, the PFNs, the soft-dirty bits, the region bytes and the counts.

CANDIDATES (predictions printed from the baseline BEFORE the run, per the shape rule):
  C1 KERNEL WRITE: the loader passes the region itself as the read buffer -> strace A shows a
     read/pread64 with buf in [RB,RB+8*RS) on the .SAV fd; VMAs + PFNs IDENTICAL; soft-dirty SET.
     (A copy_to_user inside a syscall raises no debug exception — that is exactly what a hw watchpoint
     cannot see, and it is why M105 saw nothing.)
  C2 RING-3 STORE: no read with a buffer in the region; VMAs + PFNs identical; soft-dirty set;
     no out-of-process write -> a store the DR watchpoint missed (post-arm thread). Residual.
  C3 REMAP: an mmap MAP_FIXED/mremap covering the region; VMAs or PFNs CHANGE.
  C4 OUT-OF-PROCESS: process_vm_writev targeting the game pid, or a pwrite64/write on a /proc/<pid>/mem
     fd, in either strace log.
  C5 NOTHING: the sentinels survive.
C1/C3 disagree on the VMA+PFN leg, C1/C2 on the read-buffer leg, C4 on the second log, C5 on the
sentinels — the shape discriminates.

  python3 scripts/m106_load_restore.py --tag m106r1
"""
import argparse
import os
import re
import struct
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import m55_boundary as M          # noqa: E402  (rd)
import m105_setup_watch as S      # noqa: E402  (wine_pids, terran_pid, wait_title, LAUNCH)

ROOT = os.path.dirname(HERE)
EVID = os.path.join(ROOT, "evidence")
SCRATCH = os.path.join(ROOT, "scratch")

RB, RS = 0x927a9c, 1436
REG_LO, REG_HI = RB, RB + 8 * RS
SAV_OFF = 0x10e18                 # fac0 block base inside m54b_clean.SAV (m104w3 G9)
TYPE_OFF, KEY_OFF, VAL_OFF, MAXE = 0x04, 0x24, 0x44, 8
DB, ND = 0x94d700, 11
IMG = [0, 6, 5, 4, 3, 4, 5, 3]    # the m104w3/m105s4 count image
ROUND_ADDR, CP_ADDR = 0x985afc, 0x985dcc
SENT0 = -1000
WFACS = [1, 3, 6]   # the three counts M105 armed hardware watchpoints on
REGION_PAGES = (REG_LO // 4096) * 4096
NPAGES = (REG_HI - REGION_PAGES + 4095) // 4096

RAW_SET = ("read,pread64,pwrite64,pwritev,mmap,mmap2,munmap,mprotect,mremap,"
           "process_vm_writev,process_vm_readv")
TRACE_SET = (RAW_SET + ",open,openat,close,lseek,_llseek")
ONLY_EXIT = "read=" + RAW_SET   # one ptrace stop per traced call instead of two: the game does
                                # ~4k socket reads/s and a double stop made the load take 568s
B_SET = ("process_vm_writev,process_vm_readv,pwrite64,pwritev,mmap,mmap2,mprotect,mremap,"
         "munmap,openat,open")
B_RAW = "process_vm_writev,process_vm_readv,pwrite64,pwritev,mmap,mmap2,mprotect,mremap,munmap"

LINE = re.compile(r"^(?:(\d+)[ \t]+)?([A-Za-z_][A-Za-z0-9_]*)\((.*?)\)\s*(?:=|\.\.\.)\s*"
                  r"(\S+)(?:\s+(\S+))?\s*$")
OPEN_RE = re.compile(r'^(?:\d+[ \t]+)?(?:open|openat|creat)\((.*?)("([^"]*)"|AT_FDCWD)')
VMW_RE = re.compile(r"^process_vm_writev\((\d+),")


# ------------------------------------------------------------------ snapshots
def maps_of(pid):
    out = []
    for ln in open("/proc/%d/maps" % pid):
        m = re.match(r"^([0-9a-f]+)-([0-9a-f]+) (\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*(.*)$", ln)
        if m:
            out.append((int(m.group(1), 16), int(m.group(2), 16), m.group(3), m.group(4),
                        m.group(5), m.group(6), m.group(7) or ""))
    return out


def region_vmas(pid):
    return [v for v in maps_of(pid) if v[0] < REG_HI and v[1] > REG_LO]


def region_bytes(pid):
    with open("/proc/%d/mem" % pid, "rb", 0) as mm:
        return bytes(M.rd(mm, RB, REG_HI - REG_LO))


def counts_and_D(pid):
    with open("/proc/%d/mem" % pid, "rb", 0) as mm:
        cnt = [struct.unpack("<i", M.rd(mm, RB + f * RS, 4))[0] for f in range(8)]
        ent = {}
        for f in range(8):
            a = RB + f * RS
            n = max(cnt[f], 0)
            ent[f] = [(struct.unpack("<i", M.rd(mm, a + TYPE_OFF + 4 * i, 4))[0],
                       struct.unpack("<i", M.rd(mm, a + KEY_OFF + 4 * i, 4))[0],
                       struct.unpack("<i", M.rd(mm, a + VAL_OFF + 4 * i, 4))[0])
                      for i in range(min(n, MAXE))]
        d = {f: list(struct.unpack("<%di" % ND, M.rd(mm, DB + f * S.S, 4 * ND)))
             for f in WFACS}
        rnd = struct.unpack("<i", M.rd(mm, ROUND_ADDR, 4))[0]
        cp = struct.unpack("<i", M.rd(mm, CP_ADDR, 4))[0]
    return cnt, ent, d, rnd, cp


def model_of(e):
    m = {}
    for t, k, v in e:
        if t == 3:
            m[k] = m.get(k, 0) + v
    return [m.get(i, 0) for i in range(ND)]


def pagemap(pid):
    """(present, pfn, soft_dirty) per page covering the region."""
    out = []
    with open("/proc/%d/pagemap" % pid, "rb", 0) as pm:
        pm.seek(REGION_PAGES // 4096 * 8)
        raw = pm.read(NPAGES * 8)
    for i in range(NPAGES):
        w = struct.unpack("<Q", raw[i * 8:i * 8 + 8])[0]
        out.append((1 if w & (1 << 63) else 0, w & ((1 << 55) - 1), (w >> 55) & 1))
    return out


def clear_soft_dirty(pid):
    with open("/proc/%d/clear_refs" % pid, "w") as fh:
        fh.write("4\n")


def tracer(pid):
    for ln in open("/proc/%d/status" % pid):
        if ln.startswith("TracerPid:"):
            return int(ln.split()[1])
    return -1


def entry_image(chunk, f):
    o = f * RS          # chunk is already sliced from SAV_OFF (the fac0 count image)
    n = struct.unpack_from("<i", chunk, o)[0]
    return [(struct.unpack_from("<i", chunk, o + TYPE_OFF + 4 * i)[0],
             struct.unpack_from("<i", chunk, o + KEY_OFF + 4 * i)[0],
             struct.unpack_from("<i", chunk, o + VAL_OFF + 4 * i)[0])
            for i in range(min(max(n, 0), MAXE))]


# ------------------------------------------------------------------ strace
def strace_cmd(log, pids, trace, raw, only_exit=None):
    cmd = ["strace", "-f", "-qq", "-ttt", "-O", "256", "-s", "32", "-o", log,
           "-p", ",".join(str(p) for p in pids), "-e", "trace=" + trace,
           "-e", "raw=" + raw]
    if only_exit:
        cmd.extend(["-e", only_exit])
    return cmd


def spawn(log, pids, trace, raw, err, only_exit=None):
    """strace dies SILENTLY on an invalid syscall name (m106r2: 'lseek64' -> a 0-byte log and a
    blind read leg), so its stderr goes to a file and the process is checked before the load."""
    return subprocess.Popen(strace_cmd(log, pids, trace, raw, only_exit), stdout=subprocess.DEVNULL,
                            stderr=open(err, "wb"))


def preflight():
    """Validate both syscall-name sets on /bin/true BEFORE touching the box (m106r2 law)."""
    out = []
    for name, trace, raw in (("A", TRACE_SET, RAW_SET), ("B", B_SET, B_RAW)):
        r = subprocess.run(["strace", "-f", "-qq", "-O", "256", "-s", "32",
                            "-e", "trace=" + trace, "-e", "raw=" + raw,
                            "-o", os.devnull, "true"], capture_output=True, text=True)
        out.append("%s rc=%d %s" % (name, r.returncode, (r.stderr or "").strip()[:160]))
        if r.returncode != 0:
            raise SystemExit("strace preflight FAILED (%s): %s" % (name, out[-1]))
    return "; ".join(out)


def stop(p, timeout=40):
    for sig in (2, 15, 9):
        try:
            p.send_signal(sig)
        except ProcessLookupError:
            break
        for _ in range(timeout * 4):
            if p.poll() is not None:
                break
            time.sleep(0.25)
        if p.poll() is not None:
            break
    try:
        p.wait(timeout=10)
    except Exception:
        pass


def parse_strace(path):
    """strace -f -ttt lines are 'PID TS name(args) = ret'.
    Returns (events, unparsed, fd->path per pid, merged fd->path, unfinished-entry lines)."""
    ev, bad, fds, merged = [], [], {}, {}
    unfin = 0
    if not os.path.exists(path):
        return ev, bad, fds, merged, unfin
    for ln in open(path, "r", errors="replace"):
        ln = ln.rstrip("\n")
        if not ln.strip():
            continue
        m = re.match(r"^(\d+) (\d+\.\d{6}) (.*)$", ln)
        if m:
            pid, ts, rest = int(m.group(1)), float(m.group(2)), m.group(3)
        else:
            pid, ts, rest = None, None, ln
        if rest.startswith(("???", "+++", "---", "exited", "killed", "attach", "detach")):
            continue
        m3 = LINE.match(rest)
        if not m3:
            if rest.startswith("<...") or re.match(r"^[A-Za-z_][A-Za-z0-9_]*\(", rest):
                unfin += 1          # '<... x resumed>' / an entry line still open at detach
                continue
            bad.append(ln[:220])
            continue
        name, args, ret = m3.group(2), m3.group(3), m3.group(4)
        ev.append((ts, pid, name, args, ret))
        if name in ("open", "openat", "creat") and ret.isdigit():
            mm = re.search(r'"((?:[^"\\]|\\.)*)"', args)
            if mm:
                fds.setdefault(pid or 0, {})[int(ret)] = mm.group(1)
                merged[int(ret)] = mm.group(1)
    return ev, bad, fds, merged, unfin


def hexargs(a):
    out = []
    for tok in a.split(","):
        tok = tok.strip()
        try:
            out.append(int(tok, 16) if tok.startswith("0x") else int(tok))
        except ValueError:
            out.append(None)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m106r1")
    ap.add_argument("--save", default="m54b_clean.SAV")
    ap.add_argument("--load-timeout", type=int, default=300)
    ap.add_argument("--no-relaunch", action="store_true")
    a = ap.parse_args()

    print("preflight: %s" % preflight(), flush=True)

    savp = os.path.join(ROOT, "programs", "saves", a.save)
    sav = open(savp, "rb").read()
    chunk = sav[SAV_OFF:SAV_OFF + 8 * RS]
    log_a = os.path.join(SCRATCH, "%s_terran.strace" % a.tag)
    log_b = os.path.join(SCRATCH, "%s_tree.strace" % a.tag)
    log_ae = os.path.join(SCRATCH, "%s_terran.strace.err" % a.tag)
    log_be = os.path.join(SCRATCH, "%s_tree.strace.err" % a.tag)
    log_e = os.path.join(EVID, "%s.strace" % a.tag)
    os.makedirs(SCRATCH, exist_ok=True)

    if a.no_relaunch:
        pid = S.terran_pid()
        if not pid:
            raise SystemExit("no terran.exe and --no-relaunch")
    else:
        for p, name in S.wine_pids():
            if name == "terran.exe":
                subprocess.run(["kill", str(p)], capture_output=True)
        time.sleep(3)
        for p, name in S.wine_pids():
            if name != "terran.exe":
                subprocess.run(["kill", str(p)], capture_output=True)
        time.sleep(4)
        print("killed old wine tree by PID; leftover %s" % S.wine_pids(), flush=True)
        subprocess.run(S.LAUNCH, shell=True)
        pid = None
        for _ in range(80):
            pid = S.terran_pid()
            if pid:
                break
            time.sleep(0.25)
        if not pid:
            raise SystemExit("no terran.exe after relaunch")
    print("terran.exe pid %d" % pid, flush=True)

    if not S.wait_title(a.load_timeout):
        raise SystemExit("no pre-load screen (title/cdrom) reached")
    t0 = time.time()
    vmas_pre = region_vmas(pid)
    reg_pre = region_bytes(pid)
    cnt_pre, ent_pre, d_pre, rnd_pre, cp_pre = counts_and_D(pid)
    print("PRE-POKE region vmas: %s" % vmas_pre, flush=True)
    print("PRE-POKE round=%d cp=%d counts=%s" % (rnd_pre, cp_pre, cnt_pre), flush=True)

    # baseline: how the live region compares with the save chunk
    diff_off = [i for i in range(len(chunk)) if reg_pre[i] != chunk[i]]
    ent_bad = ["fac%d live %s != sav %s" % (f, ent_pre[f], entry_image(chunk, f))
               for f in range(8) if ent_pre[f] != entry_image(chunk, f)]
    print("BASELINE: live region vs .SAV chunk@0x%x: %d bytes differ at %s%s"
          % (SAV_OFF, len(diff_off), [hex(o) for o in diff_off[:24]],
             "..." if len(diff_off) > 24 else ""), flush=True)
    print("BASELINE entry images (count/TYPE/KEY/VAL) live vs .SAV: %s"
          % ("all 8 match" if not ent_bad else ent_bad), flush=True)

    print("""PREDICTIONS (computed from the baseline BEFORE the run; the shape must discriminate)
  poke  : 8 count dwords at RB+fac*1436 (fac0 0x927a9c .. fac7 0x92a358) -> -1000-fac
  C1 kernel write (read straight into the region) : strace A read/pread64 buf in [0x927a9c,0x92a77c)
      on the .SAV fd; VMA list IDENTICAL; PFNs IDENTICAL; soft-dirty SET; sentinels replaced.
  C2 ring-3 store (DR-missed)                    : NO read with buf in the region; VMA + PFN identical;
      soft-dirty SET; no out-of-process write.
  C3 remap (MAP_FIXED / mremap)                  : an mmap/mremap covering the region; VMA list or
      PFNs CHANGE.
  C4 out-of-process write                        : process_vm_writev(remote pid = %d) or a
      pwrite64/write on a /proc/%d/mem fd in either log.
  C5 nothing writes                              : the 8 sentinels SURVIVE.
  Candidates disagree on the read-buffer leg (C1 vs C2), the VMA/PFN leg (C3) and the sentinel leg
  (C5), so one run answers the question.""" % (pid, pid), flush=True)

    with open("/proc/%d/mem" % pid, "wb", 0) as mm:
        for f in range(8):
            mm.seek(RB + f * RS)
            mm.write(struct.pack("<i", SENT0 - f))
    cnt_poked, _, _, _, _ = counts_and_D(pid)
    print("POKE sentinels -> counts read back %s" % cnt_poked, flush=True)

    clear_soft_dirty(pid)
    pm_pre = pagemap(pid)
    print("PRE-LOAD pagemap (present,pfn,softdirty): %s" % pm_pre, flush=True)

    others = [p for p, _ in S.wine_pids() if p != pid]
    pa = spawn(log_a, [pid], TRACE_SET, RAW_SET, log_ae, ONLY_EXIT)
    time.sleep(2.0)
    if pa.poll() is not None or os.path.getsize(log_a) < 4096:
        raise SystemExit("strace A is BLIND (rc=%s, log %d B after 2s); strace stderr: %s"
                         % (pa.poll(), os.path.getsize(log_a),
                            open(log_ae, "r", errors="replace").read()[-400:]))
    pb = spawn(log_b, others, B_SET, B_RAW, log_be)
    time.sleep(1.0)
    print("strace A on %d (%s, %d B and growing); strace B on %s (%s)"
          % (pid, log_a, os.path.getsize(log_a), others, log_b), flush=True)

    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "m54a_load.py")],
                       capture_output=True, text=True,
                       env=dict(os.environ, SMAC_SAVE="Z:\\home\\n100\\reverse\\smac\\programs\\saves\\"
                                + a.save, M54A_LOAD_TIMEOUT="1200"))
    print("load rc=%d (%.1fs)" % (r.returncode, time.time() - t0), flush=True)
    for ln in (r.stdout or "").strip().splitlines()[-8:]:
        print("  load: " + ln[:150], flush=True)
    time.sleep(3)
    stop(pa)
    stop(pb)
    subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
    time.sleep(1)

    pid_post = S.terran_pid()
    vmas_post = region_vmas(pid_post or pid)
    reg_post = region_bytes(pid_post or pid)
    cnt_post, ent_post, d_post, rnd_post, cp_post = counts_and_D(pid_post or pid)
    pm_post = pagemap(pid_post or pid)
    tr = tracer(pid_post or pid)
    print("POST-LOAD pid=%d (pre %d) round=%d cp=%d counts=%s TracerPid=%d"
          % (pid_post or pid, pid, rnd_post, cp_post, cnt_post, tr), flush=True)
    print("POST-LOAD region vmas: %s" % vmas_post, flush=True)
    print("POST-LOAD pagemap: %s" % pm_post, flush=True)

    ev_a, bad_a, fds_a, merged_a, unfin_a = parse_strace(log_a)
    ev_b, bad_b, fds_b, merged_b, unfin_b = parse_strace(log_b)
    paths_a = sorted({p for d in list(fds_a.values()) + [merged_a]
                      for p in d.values() if p.lower().endswith(".sav")})
    paths_b = sorted({p for d in list(fds_b.values()) + [merged_b]
                      for p in d.values() if p.lower().endswith(".sav")})

    def fd_path(p, fd):
        if fd is None:
            return "?"
        for d in (fds_a, fds_b):
            v = d.get(p, {}).get(fd)
            if v:
                return v
        return merged_a.get(fd) or merged_b.get(fd) or "?"

    def num(tok):
        try:
            return int(tok, 16) if tok.startswith("0x") else int(tok)
        except (TypeError, ValueError):
            return None

    reads_region, scratch, sav_reads = [], [], []
    for ts, p, name, args, ret in ev_a:
        if name not in ("read", "pread64"):
            continue
        ar = hexargs(args)
        if len(ar) < 3 or ar[0] is None or ar[1] is None:
            continue
        fd, buf, ln_ = ar[0], ar[1], ar[2]
        path = fd_path(p, fd)
        rec = (ts, p, name, fd, buf, ln_, ret, path)
        # classify by RANGE OVERLAP with the count region: the writer's destination is the 11488-byte
        # structure array anchor &DAT_00927590 (= the count region shifted by 0x50C), so a read that
        # starts BELOW 0x927a9c still lands on the counts.
        span = ln_ if ln_ is not None else 4
        if buf < REG_HI and buf + span > REG_LO:
            reads_region.append(rec)
        elif path.upper().endswith(".SAV") and span >= 4096:
            scratch.append(rec)
        if path.upper().endswith(".SAV"):
            sav_reads.append(rec)
    maps_covers = []
    for ts, p, name, args, ret in ev_a + ev_b:
        if name not in ("mmap", "mmap2", "mremap", "munmap", "mprotect"):
            continue
        ar = hexargs(args)
        if not ar or ar[0] is None or len(ar) < 2:
            continue
        addr, ln_ = (ar[0], ar[2] if name == "mremap" else ar[1])
        cands = [(addr, ln_)] + ([(num(ret), ln_)] if name in ("mmap", "mmap2") else [])
        for lo, size in cands:
            if lo is None or size is None:
                continue
            if lo < REG_HI and lo + size > REG_LO and name != "mprotect":
                maps_covers.append((ts, p, name, args, ret))
                break
    outwrites = []
    for ts, p, name, args, ret in ev_a + ev_b:
        if name == "process_vm_writev":
            m = VMW_RE.match(args)
            if m and int(m.group(1)) == (pid_post or pid):
                outwrites.append((ts, p, name, args, ret))
        elif name in ("pwrite64", "pwritev", "write"):
            ar = hexargs(args)
            path = fd_path(p, ar[0]) if ar and ar[0] is not None else "?"
            if "/proc/" in path and "/mem" in path:
                outwrites.append((ts, p, name, args, ret))

    with open(os.path.join(SCRATCH, "%s_events.jsonl" % a.tag), "w") as fh:
        for x in reads_region:
            fh.write("READ_REGION %s\n" % (x,))
        for x in scratch:
            fh.write("SCRATCH %s\n" % (x,))
        for x in maps_covers:
            fh.write("MAP_COVER %s\n" % (x,))
        for x in outwrites:
            fh.write("OUTWRITE %s\n" % (x,))
        fh.write("VMAS_PRE %s\nVMAS_POST %s\n" % (vmas_pre, vmas_post))
        fh.write("PM_PRE %s\nPM_POST %s\n" % (pm_pre, pm_post))
        fh.write("COUNTS_PRE %s\nCOUNTS_POKE %s\nCOUNTS_POST %s\n" % (cnt_pre, cnt_poked, cnt_post))
        fh.write("DIFF_OFF %s\n" % ([hex(o) for o in diff_off],))

    with open(log_e, "w") as fh:
        fh.write("# M106 filtered strace extract; the RAW logs are %s and %s\n" % (log_a, log_b))
        fh.write("# pids seen in log A: %s ; in log B: %s\n"
                 % (sorted({e[1] for e in ev_a if e[1]}), sorted({e[1] for e in ev_b if e[1]})))
        for tag_, items in (("READ_REGION", reads_region), ("SAV_READ", sav_reads),
                            ("SCRATCH_SAV_READ", scratch), ("MAP_COVER", maps_covers),
                            ("OUTWRITE", outwrites)):
            fh.write("## %s %d\n" % (tag_, len(items)))
            for x in items[:4000]:
                fh.write("%r\n" % (x,))
        fh.write("## OPENS (fd -> path)\n")
        for p, d in sorted(fds_a.items()):
            for fd, path in sorted(d.items()):
                fh.write("open pid=%s fd=%s path=%s\n" % (p, fd, path))

    gates = []

    def gate(n, ok, detail):
        gates.append((n, bool(ok), detail))

    same_pid = (pid_post == pid)
    gate("G1-same-process-across-the-load", same_pid and rnd_post >= 50 and r.returncode == 0,
         "pid %d -> %s; load rc=%d round %d->%d cp=%d" % (pid, pid_post, r.returncode,
                                                          rnd_pre, rnd_post, cp_post))
    gate("G2-8-sentinels-landed", all(cnt_poked[f] == SENT0 - f for f in range(8)),
         "read back %s (baseline counts %s)" % (cnt_poked, cnt_pre))
    gate("G3-baseline-region-matches-save-entries", not ent_bad,
         "%d region bytes differ from the .SAV chunk at %s; entry images: %s"
         % (len(diff_off), [hex(o) for o in diff_off[:12]], "8/8 match" if not ent_bad else ent_bad))
    gate("G4-strace-instrument-healthy", len(ev_a) > 20 and not bad_a and not bad_b,
         "A: %d events, %d unparsed %s, %d unfinished, .SAV paths %s; B: %d events %d unparsed %s "
         "%d unfinished"
         % (len(ev_a), len(bad_a), bad_a[:2], unfin_a, paths_a, len(ev_b), len(bad_b), bad_b[:2],
            unfin_b))
    gate("G5-read-into-the-region", bool(reads_region),
         "%d read/pread64 whose range overlaps [0x%x,0x%x): %s" % (len(reads_region), REG_LO, REG_HI,
         ["%s fd=%s(%s) buf=0x%x len=0x%x ret=%s" % (x[2], x[3], x[7], x[4], x[5], x[6])
          for x in reads_region[:8]]))
    covered = set()
    for ts, p, name, fd, buf, ln_, ret, path in reads_region:
        got = int(ret, 16) if ret.startswith("0x") else max(ln_ or 0, 0)
        got = max(got, 0)   # the bytes the kernel actually copied, not the number that was asked
        for f in range(8):
            if buf <= RB + f * RS < buf + got:
                covered.add(f)
    gate("G6-m105-watched-counts-inside-the-kernel-written-span", all(f in covered for f in WFACS),
         "M105 armed watchpoints on facs %s; inside a read returning into the region: %s; whole-region"
         " coverage %s of 8 (the rest arrives through the CRT stdio buffer -- FUN_0064cc40 uses a 0x1000"
         " buffer, so it drains what it already holds with ring-3 stores and only the remainder goes in"
         " as a direct read); reads %s"
         % (WFACS, sorted(f for f in WFACS if f in covered), sorted(covered),
            ["0x%x+0x%x ret=%s" % (x[4], x[5], x[6]) for x in reads_region[:8]]))
    wrong = ["fac%d count=%d want %d" % (f, cnt_post[f], IMG[f]) for f in range(8)
             if cnt_post[f] != IMG[f]]
    gate("G7-sentinels-replaced-counts-eq-image", not wrong,
         "%s; counts %s" % ("; ".join(wrong) or "8/8 == the m104w3 image", cnt_post))
    diff_after = [i for i in range(len(reg_post)) if reg_post[i] != chunk[i]]
    restored_ok = all(struct.unpack_from("<i", reg_post, f * RS)[0] == IMG[f] for f in range(8))
    gate("G8-region-restored-from-the-save-chunk", restored_ok,
         "post-load region vs .SAV chunk: %d bytes differ at %s%s (pre-poke baseline %d)"
         % (len(diff_after), [hex(o) for o in diff_after[:16]], "..." if len(diff_after) > 16 else "",
            len(diff_off)))
    gate("G9-no-remap-vmas-identical",
         [(v[0], v[1], v[2]) for v in vmas_pre] == [(v[0], v[1], v[2]) for v in vmas_post]
         and not maps_covers,
         "pre %s post %s; mmap/mremap/mprotect/munmap events covering the region: %d %s"
         % (vmas_pre, vmas_post, len(maps_covers), maps_covers[:4]))
    gate("G10-pages-written-in-place-not-remapped",
         all(p[2] == 0 for p in pm_pre) and all(p[2] == 1 for p in pm_post),
         "pre %s post %s (soft-dirty cleared at the baseline, SET after the load == a write to the "
         "SAME pages; PFNs are hidden from this uid: %s)"
         % (pm_pre, pm_post, ["pfn=%d" % p[1] for p in pm_pre]))
    gate("G11-no-out-of-process-writer", not outwrites,
         "%d process_vm_writev/pwrite-to-/proc-mem events %s" % (len(outwrites), outwrites[:4]))
    gate("G12-scratch-read-candidates-reported", True,
         "%d reads >=4096 B on a .SAV fd with the buffer BELOW the region (a scratch buffer would "
         "mean C2): %s"
         % (len(scratch), ["%s fd=%s(%s) buf=0x%x len=0x%x ret=%s" % (x[2], x[3], x[7], x[4],
                                                                       x[5], x[6])
                           for x in scratch[:6]]))
    tot = sum((x[5] or 0) for x in sav_reads if x[4] is not None)
    gate("G13-save-file-opened-and-region-reads-sized",
         bool(paths_a or paths_b) and bool(reads_region),
         "the .SAV was opened by a traced task: %s ; %d reads whose ranges cover the region; "
         "%d B of them land in buffers above the region; %d reads on a path-matched .SAV fd "
         "(terran's fd arrives over SCM_RIGHTS, so it has no open in log A)"
         % (paths_a or paths_b, len(reads_region), tot, len(sav_reads)))
    c1 = bool(reads_region)
    c3 = bool(maps_covers) or [(v[0], v[1]) for v in vmas_pre] != [(v[0], v[1]) for v in vmas_post]
    c4 = bool(outwrites)
    c5 = any(cnt_post[f] == SENT0 - f for f in range(8))
    alive = [n for n, ok in (("C1-kernel-write-via-read", c1), ("C3-remap", c3),
                             ("C4-out-of-process", c4), ("C5-nothing-wrote", c5)) if ok]
    if not (c1 or c3 or c4 or c5):
        alive = ["C2-ring3-store-residual"]
    gate("G14-mechanism-identified", len(alive) == 1,
         "candidates consistent with the observables: %s (C1 read-in-region=%s C3 remap=%s "
         "C4 out-of-process=%s C5 sentinel-survived=%s)" % (alive, c1, c3, c4, c5))
    gate("G15-hygiene", tr == 0 and not bad_a and not bad_b,
         "TracerPid=%d; unparsed A %d B %d; unfinished A %d B %d; logs %s (%d B) %s (%d B)"
         % (tr, len(bad_a), len(bad_b), unfin_a, unfin_b, log_a, os.path.getsize(log_a), log_b,
            os.path.getsize(log_b)))

    print("--- strace A: %d events; region reads %d; scratch reads %d; map covers %d ---"
          % (len(ev_a), len(reads_region), len(scratch), len(maps_covers)), flush=True)
    good = True
    for name, ok, detail in gates:
        good = good and ok
        print("%-38s %s  %s" % (name, "PASS" if ok else "FAIL", detail))
    print("ACCEPTANCE %s %d/%d  (tag %s, pid %d, save %s, round %d->%d, verdict %s)"
          % ("PASS" if good else "FAIL", sum(1 for _, o, _ in gates if o), len(gates),
             a.tag, pid, a.save, rnd_pre, rnd_post, alive))
    print("context: %s ; raw strace %s (%d B) %s (%d B) ; %s"
          % (log_e, log_a, os.path.getsize(log_a), log_b, os.path.getsize(log_b),
             os.path.join(SCRATCH, "%s_events.jsonl" % a.tag)))
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
