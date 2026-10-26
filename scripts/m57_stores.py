#!/usr/bin/env python3
"""M57-4 — enumerate EVERY store to base+0x40 (mineral storage) inside one base visit.

The M57 gate kept failing because the credit model assumed one add and one pay per round,
while session 94 measured a SECOND, unnamed movement inside a single visit. This harness
stops modelling and starts counting: it breakpoints EVERY instruction that can write
`[reg+0x40]` in the transitive call sets (depth<=4) of the per-base visit driver
FUN_004f5a70 — which is FUN_004ef6d0 (the production/mineral visit), FUN_004f26e0 (the
post-visit distributor it calls), the FUN_00417ee0 queue edit, and the UI/AI sets reachable
from them — conditioning each breakpoint on the STORE'S OWN base register == our base
record, and records (before, after, pending, head, d0, +0x30, +0x3c, +0xcc) before the
store; `after` is the store's OWN source operand (every one of these 23 sites is a plain
`mov [reg+0x40], reg-or-imm`, so that register IS the value the field takes — and the
replay-vs-memory checks below catch it if that is ever false). Single-stepping is NOT
available here: measured 2026-10-26, an `si` inside a breakpoint commands list makes
`gdb -batch` stop after the step and detach ("0x004ef7f9 in ?? ()" then
"[Inferior 1 detached]"), which ends the watch after the first store.

The site list is a whole-image store census (`objdump -d --section=.text`, every
`mov/add/... DWORD PTR [reg+0x40]`, mapped to functions through ghidra_out/index.csv and
filtered by call-graph reachability — generator kept at scratch/m574/census.py), NOT the
four hand-picked sites earlier sessions used. The `lea reg,[reg+0x40]` pointer-arithmetic
shape was censused too: no store runs through such a register in the reachable sets.

Visit marker: 0x4f5a99, the instruction in FUN_004f5a70 where the current-base global
DAT_0x8f0d60 is set to the record being visited (`lea ecx,[eax*304+0x95da10]` has just
run, so $ecx IS the base record address). One marker = one visit of our base.

ACCEPTANCE (one real invocation of this script prints the table and PASS/FAIL):
  A1  replay the stores from the run-start value: every store's `before` must equal the
      replayed current value — a mismatch is a write at a site we did not instrument;
  A2  every value the 2 ms memory sampler observed must be a value the replay produces,
      in order (sampler = ground truth, subsequence test);
  A3  per boundary, sum(store deltas) == the observed net change of the field;
  A4  >= --boundaries boundaries flipped, >= 1 store recorded, and >= 1 boundary whose
      net change is non-zero (so a run that wrote nothing cannot pass vacuously);
  A5  every recorded store is attributed to a named site from the census.
No price, no prediction and no threshold is asserted here: this is the enumeration gate.
"""
import argparse, json, os, re, signal, struct, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "evidence")
BASE_ARR, BASE_SZ = 0x95DA10, 304
YEAR, MASK, CURP, TF = 0x985B00, 0x985B10, 0x985DCC, 0x985AE8
VISIT_MARK = 0x4f5a99          # FUN_004f5a70: mov DAT_0x8f0d60, ecx(= base record)

# (pc, function, role, store's base register, value-being-stored expression in gdb)
# Census of every `... DWORD PTR [reg+0x40]` store reachable from the visit driver,
# the queue edit and the AI chooser. src is the store's SOURCE operand: at the moment
# the store executes, that register holds the value the field is about to hold.
SITES = [
    (0x4ef7f6, "FUN_004ef6d0", "visit.income-add",        "eax", "$edx"),
    (0x4efedd, "FUN_004ef6d0", "visit.pay-minus-edi",      "ecx", "$esi"),
    (0x4eff20, "FUN_004ef6d0", "visit.clampB-post-pay",  "esi", "$eax"),
    (0x4f0ca6, "FUN_004ef6d0", "visit2.pay-minus-edi",     "edx", "$esi"),
    (0x4f0ce9, "FUN_004ef6d0", "visit2.clampB-post-pay", "esi", "$eax"),
    (0x4f2d7d, "FUN_004f26e0", "postvisit.distribution",  "edi", "$eax"),
    (0x418aae, "FUN_00417ee0", "queue-edit.store1",       "eax", "$esi"),
    (0x418b21, "FUN_00417ee0", "queue-edit.store2",       "eax", "$edx"),
    (0x41a596, "FUN_00419c30", "reachable",               "edx", "$eax"),
    (0x41dac4, "FUN_0041d480", "reachable",               "eax", "$ecx"),
    (0x4b9df5, "FUN_004b9d20", "reachable",               "edx", "$ecx"),
    (0x4b9e30, "FUN_004b9d20", "reachable",               "edx", "$ecx"),
    (0x4badb0, "FUN_004bad50", "reachable",               "edx", "$ecx"),
    (0x5b5ba9, "FUN_005b59b0", "reachable",               "esi", "$edi"),
    (0x5fc695, "FUN_005fc500", "reachable",               "edx", "$eax"),
    (0x5fcbce, "FUN_005fca14", "reachable",               "eax", "$ecx"),
    (0x5fe34e, "FUN_005fe1e0", "reachable",               "edx", "0"),
    (0x5fe4f7, "FUN_005fe41f", "reachable",               "edx", "0"),
    (0x6150a5, "FUN_00614daf", "reachable",               "edx", "0"),
    (0x615625, "FUN_006154a9", "reachable",               "eax", "$edx"),
    (0x615693, "FUN_006154a9", "reachable",               "edx", "0"),
    (0x62edc8, "FUN_0062ed00", "reachable",               "ecx", "$edx"),
    (0x62ef98, "FUN_0062eed9", "reachable",               "eax", "$ecx"),
]
SITE_BY_PC = {s[0]: s for s in SITES}


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def game_pid():
    out = sh(["pgrep", "-x", "terran.exe"]).stdout.split()
    if not out:
        raise SystemExit("terran.exe not running")
    return int(out[0])


def base_rec(pid, name):
    """Locate our base BY NAME (indices drift); return (idx, name, addr, fields)."""
    f = open(f"/proc/{pid}/mem", "rb", 0)
    f.seek(0x985AF4)
    n = int.from_bytes(f.read(4), "little")
    hits = []
    for i in range(min(n, 64)):
        f.seek(BASE_ARR + i * BASE_SZ)
        b = f.read(BASE_SZ)
        nm = b[19:59].split(b"\0")[0].decode("latin-1", "replace")
        if name.lower() in nm.lower():
            hits.append((i, nm, b))
    f.close()
    if len(hits) != 1:
        raise SystemExit(f"base lookup got {len(hits)} hits for {name!r}")
    i, nm, b = hits[0]
    g = lambda o: struct.unpack("<i", b[o:o + 4])[0]
    return i, nm, BASE_ARR + i * BASE_SZ, dict(pending=g(0x4c), head=g(0x50), minerals=g(0x40),
                                               d0=g(0xd0), progress=g(0x3c), rate=g(0xcc),
                                               flag30=g(0x30))


def gdb_script(addr, sites):
    L = ["set pagination off", "set confirm off", "set height 0", "set verbose off",
         f"set $b = {addr:#x}", "set $n = 0", "set $v = 0",
         # visit marker: one hit per visit of OUR base record
         f"break *{VISIT_MARK:#x} if $ecx == $b",
         "commands", "silent", "set $v = $v + 1",
         ('printf "VISIT#%d storage=%d pend=%d head=%d d0=%d f30=0x%x f3c=%d fcc=%d\\n", '
          "$v, *(int*)($b + 0x40), *(int*)($b + 0x4c), *(int*)($b + 0x50), "
          "*(int*)($b + 0xd0), *(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)"),
         "continue", "end"]
    for pc, func, role, reg, src in sites:
        L += [f"break *{pc:#x} if ${reg} == $b", "commands", "silent", "set $n = $n + 1",
              (f'printf "STORE#%d pc=0x{pc:x} site={role} before=%d src=%d pend=%d head=%d '
               f'd0=%d f30=0x%x f3c=%d fcc=%d\\n", $n, *(int*)($b + 0x40), {src}, '
               f"*(int*)($b + 0x4c), *(int*)($b + 0x50), *(int*)($b + 0xd0), "
               f"*(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)"),
              "continue", "end"]

    L.append("continue")
    return "\n".join(L) + "\n"


RE_STORE = re.compile(r"STORE#(\d+) pc=0x([0-9a-f]+) site=(\S+) before=(-?\d+) src=(-?\d+) "
                      r"pend=(-?\d+) head=(-?\d+) d0=(-?\d+) f30=0x([0-9a-f]+) f3c=(-?\d+) fcc=(-?\d+)")
RE_AFTER = re.compile(r"AFTER#(\d+) pc=0x([0-9a-f]+) after_si=(-?\d+)")
RE_VISIT = re.compile(r"VISIT#(\d+) storage=(-?\d+) pend=(-?\d+) head=(-?\d+) d0=(-?\d+) "
                      r"f30=0x([0-9a-f]+) f3c=(-?\d+) fcc=(-?\d+)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="Korolev Center")
    ap.add_argument("--boundaries", type=int, default=3)
    ap.add_argument("--timeout", type=float, default=300.0)
    ap.add_argument("--tag", default="m574")
    ap.add_argument("--tail", type=float, default=3.0,
                    help="keep watching this long after the last boundary so the closing "
                         "anchor covers the stores in that window (the game keeps playing "
                         "after the last flip, so a post-detach read-back is NOT an anchor)")
    ap.add_argument("--stall", type=float, default=90.0,
                    help="detach early if the year has not moved this long while attached")
    ap.add_argument("--sites", action="store_true", help="print the census table and exit")
    a = ap.parse_args()

    if a.sites:
        print(f"{len(SITES)} instrumented sites (whole-image store census, "
              f"reachable from FUN_004f5a70 / FUN_00417ee0 / FUN_004f6030):")
        for pc, func, role, reg, src in SITES:
            print("  %08x %-14s %-24s base=%-4s value=%s" % (pc, func, role, reg, src))
        return 0

    pid = game_pid()
    tracer = sh(["grep", "-m1", "TracerPid", f"/proc/{pid}/status"]).stdout.split()[-1]
    if tracer != "0":
        raise SystemExit(f"TracerPid={tracer} != 0 (a leftover tracer makes pokes lie)")
    if sh(["pgrep", "-x", "gdb"]).stdout.strip():
        raise SystemExit("a gdb is already running — run scripts/m57_credit.py --stop first")
    if sh(["sysctl", "-n", "kernel.yama.ptrace_scope"]).stdout.strip() != "0":
        raise SystemExit("ptrace_scope != 0")

    idx, nm, addr, pre = base_rec(pid, a.base)
    V0 = pre["minerals"]
    print(f"base {nm!r} idx={idx} addr={addr:#x} start={pre}", flush=True)

    gpath = os.path.join(EVID, f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.gdblog")
    open(gpath, "w").write(gdb_script(addr, SITES))
    lf = open(lpath, "wb")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    os.set_blocking(g.stdout.fileno(), False)
    open(os.path.join(EVID, f"{a.tag}.gdbpid"), "w").write(str(g.pid))
    print(f"gdb armed pid {g.pid} ({len(SITES)} conditioned breakpoints + visit marker); "
          f"log {lpath}", flush=True)
    time.sleep(2.0)                       # let gdb finish attaching before sampling

    m = open(f"/proc/{pid}/mem", "rb", 0)

    def rd(a_, n_):
        m.seek(a_)
        return m.read(n_)

    def u32(a_):
        return int.from_bytes(rd(a_, 4), "little")

    def fields():
        b = rd(addr, BASE_SZ)
        g_ = lambda o: struct.unpack("<i", b[o:o + 4])[0]
        return dict(store=g_(0x40), pend=g_(0x4c), head=g_(0x50), d0=g_(0xd0),
                    progress=g_(0x3c), rate=g_(0xcc))

    win = None
    try:
        win = sh(["xdotool", "search", "--name", "Sid Meier"]).stdout.split()[0]
        sh(["xdotool", "windowfocus", win])
    except Exception:
        pass

    trace = dict(tag=a.tag, pid=pid, base_index=idx, base_name=nm, base_addr=hex(addr),
                 start=pre, sites=[dict(pc=hex(p), func=f_, role=r_, base_reg=rg, value=sv)
                                   for p, f_, r_, rg, sv in SITES],
                 samples=[], stores=[], visits=[], events=[])

    lines = []               # (wall, text) drained from gdb's pipe
    buf = b""

    def drain():
        nonlocal buf
        try:
            chunk = os.read(g.stdout.fileno(), 65536)
        except (BlockingIOError, OSError):
            chunk = None
        if not chunk:
            return
        buf += chunk
        while b"\n" in buf:
            raw, buf = buf.split(b"\n", 1)
            lines.append((time.time(), raw.decode("latin-1", "replace")))

    t0 = time.time()
    last_press = last_h = last_ok = last_ocr = 0.0
    parked_t = None
    last_year = u32(YEAR)
    flips = []
    samples = []
    tail_at = None
    moved = False
    name_bytes = nm.encode("latin-1", "replace")
    stall_since = time.time()
    try:
        while time.time() - t0 < a.timeout:
            drain()
            now = time.time() - t0
            wall = time.time()
            # The base array COMPACTS/REORDERS mid-run: measured 2026-10-26 Korolev Center
            # walked index 18 -> 17 (0x95ef70 -> 0x95ee40) during a watch, after which the
            # baked address holds ANOTHER faction's record (its storage read 19 where ours
            # read 5) and the conditioned breakpoints would attribute that base's stores to
            # ours. Check the name at the baked address every sample; on a mismatch the
            # watch ends at that instant and the closing anchor is the last good sample.
            nm_here = rd(addr + 19, 40).split(b"\0")[0]
            if nm_here != name_bytes:
                moved = True
                trace["events"].append(dict(event="base_moved", wall=round(wall, 3),
                                            name_at_baked_addr=nm_here.decode("latin-1", "replace")))
                print(f"  the base array MOVED: {addr:#x} now holds {nm_here!r} — ending the "
                      f"watch at the move (the baked address is no longer {nm!r})", flush=True)
                drain()
                break
            b = rd(addr, BASE_SZ)
            g_ = lambda o: struct.unpack("<i", b[o:o + 4])[0]
            y = u32(YEAR)
            cp = u32(CURP)
            s = dict(t=round(now, 3), wall=round(wall, 3), year=y, cp=cp, tf=u32(TF),
                     store=g_(0x40), pend=g_(0x4c), head=g_(0x50), d0=g_(0xd0))
            if not samples or any(s[k] != samples[-1][k] for k in
                                  ("year", "cp", "tf", "store", "pend", "head", "d0")):
                samples.append(s)
            elif now - (samples[-1]["t_heart"] if "t_heart" in samples[-1] else 0) >= 1.0:
                s["heart"] = True
                samples.append(s)
            if samples:
                samples[-1].setdefault("t_heart", now)
            trace["samples"] = samples
            if y != last_year:
                flips.append((last_year, y, round(wall, 3), s["store"]))
                trace["events"].append(dict(event="flip", frm=last_year, to=y, wall=round(wall, 3)))
                print(f"  boundary {last_year}->{y} at t={now:.1f}s", flush=True)
                last_year = y
                stall_since = wall
                if len(flips) >= a.boundaries and tail_at is None:
                    tail_at = wall + a.tail
            if tail_at is not None and time.time() >= tail_at:
                trace["events"].append(dict(event="watch_end", wall=round(time.time(), 3)))
                drain()
                break
            if wall - stall_since > a.stall:
                trace["events"].append(dict(event="stall_abort", wall=round(wall, 3)))
                print(f"  year unmoved {a.stall}s — aborting the watch", flush=True)
                break
            # m56_build's proven escalation: Return every 2 s; OCR for the
            # units-not-moved confirm (it takes NO Return — YES row then OK 26 px below);
            # 'h' on the cursor unit every 4 s past 8 s parked on our turn (a produced
            # order-0 unit blocks the auto-end); OK click at (630,247) past 15 s.
            if now - last_press > 2.0 and win:
                sh(["xdotool", "key", "--clearmodifiers", "Return"])
                trace["events"].append(dict(event="press_return", t=round(now, 3)))
                last_press = now
                if cp == 3:
                    if parked_t is None:
                        parked_t = now
                    if now - parked_t > 5.0 and now - last_ocr > 3.0:
                        last_ocr = now
                        try:
                            import smac_play as sp
                            w = sp.ocr_fast(sp.freeze("m574"))
                            if sp.is_confirm(w):
                                sp.answer_confirm(w)
                                trace["events"].append(dict(event="answer_confirm", t=round(now, 3)))
                                print("  answered the units-not-moved confirm", flush=True)
                        except Exception as e:
                            trace["events"].append(dict(event="ocr_failed", err=str(e)))
                    if now - parked_t > 8.0 and now - last_h > 4.0:
                        sh(["xdotool", "key", "--clearmodifiers", "h"])
                        trace["events"].append(dict(event="press_hold", t=round(now, 3)))
                        last_h = now
                    if now - parked_t > 15.0 and now - last_ok > 6.0 and win:
                        sh(["xdotool", "windowfocus", win])
                        sh(["xdotool", "mousemove", "630", "247"])
                        sh(["xdotool", "click", "1"])
                        trace["events"].append(dict(event="click_ok", t=round(now, 3)))
                        last_ok = now
                else:
                    parked_t = None
                    last_h = last_ok = 0.0
            if g.poll() is not None:
                trace["events"].append(dict(event="gdb_exit", rc=g.returncode, t=round(now, 3)))
                print("  gdb exited early", flush=True)
                break
            time.sleep(0.002)
    finally:
        drain()
        try:
            os.kill(g.pid, signal.SIGINT)
        except ProcessLookupError:
            pass

        detached = False
        for _ in range(60):
            try:
                if not os.path.exists(f"/proc/{g.pid}"):
                    detached = True
                    break
            except OSError:
                detached = True
                break
            time.sleep(0.5)
        try:
            lf.close()
        except Exception:
            pass
        sh(["kill", "-CONT", str(pid)])
        trace["events"].append(dict(event="detach", detached=detached))

    with open(lpath, "ab") as lf2:
        for _, txt in lines:
            lf2.write((txt + "\n").encode("latin-1"))
    trace["gdb_lines"] = len(lines)

    # ---- parse the hit log ----------------------------------------------------
    stores, visits, afters = [], [], {}
    for wall, txt in lines:
        mm = RE_STORE.search(txt)
        if mm:
            stores.append(dict(n=int(mm.group(1)), pc=int(mm.group(2), 16), wall=round(wall, 3),
                               before=int(mm.group(4)), src=int(mm.group(5)),
                               pend=int(mm.group(6)), head=int(mm.group(7)), d0=int(mm.group(8)),
                               f30=int(mm.group(9), 16), progress=int(mm.group(10)),
                               rate=int(mm.group(11))))
            continue
        mm = RE_AFTER.search(txt)
        if mm:
            afters[int(mm.group(1))] = (int(mm.group(2), 16), int(mm.group(3)))
            continue
        mm = RE_VISIT.search(txt)
        if mm:
            visits.append(dict(n=int(mm.group(1)), wall=round(wall, 3), storage=int(mm.group(2)),
                               pend=int(mm.group(3)), head=int(mm.group(4)), d0=int(mm.group(5)),
                               f30=int(mm.group(6), 16), progress=int(mm.group(7)),
                               rate=int(mm.group(8))))
    for srec in stores:
        site = SITE_BY_PC.get(srec["pc"])
        srec["site"] = site[2] if site else "UNNAMED"
        srec["func"] = site[1] if site else "?"
        af = afters.get(srec["n"])
        srec["after_si"] = af[1] if af else None
        srec["after"] = srec["after_si"] if af is not None else srec["src"]
        srec["delta"] = srec["after"] - srec["before"]
    trace["stores"] = stores
    trace["visits"] = visits
    trace["flips"] = flips

    try:
        _, _, _, postp = base_rec(pid, a.base)
        trace["post"] = postp
    except Exception as e:
        trace["post"] = dict(error=str(e))

    jpath = os.path.join(EVID, f"trace_{a.tag}.jsonl")
    with open(jpath, "w") as jf:
        for k in ("tag", "pid", "base_index", "base_name", "base_addr", "start", "sites",
                  "flips", "visits", "stores", "events", "post", "gdb_lines"):
            jf.write(json.dumps(dict(k=k, v=trace[k])) + "\n")
        jf.write(json.dumps(dict(k="samples", v=samples)) + "\n")

    # ---- acceptance -----------------------------------------------------------
    fails = []
    print(f"\nrecorded: {len(visits)} visits of {nm}, {len(stores)} stores to +0x40, "
          f"{len(flips)} boundaries, {len(samples)} sampler rows", flush=True)
    if moved:
        print("note: the base array MOVED during this watch; the accounting below covers "
              "every sample and store up to the move and nothing after it", flush=True)
    print(f"post-detach read-back (located BY NAME, so it may name a different index): "
          f"{trace['post']}", flush=True)

    print("each store's `after` is its own source operand (all 23 sites are plain "
          "`mov [reg+0x40],src`); the replay-vs-memory checks below are what prove it",
          flush=True)

    # A5 + A1: replay
    cur = V0
    unattr = []
    for srec in stores:
        if srec["site"] == "UNNAMED":
            fails.append(f"store at {srec['pc']:#x} is not a named census site")
        if srec["before"] != cur:
            unattr.append(dict(before=cur, after=srec["before"], site=srec["site"],
                               at_store=srec["n"], wall=srec["wall"]))
        cur = srec["after"]
    for u in unattr:
        fails.append(f"A1 unattributed write {u['before']}->{u['after']} before store #"
                     f"{u['at_store']} ({u['site']}) at wall {u['wall']}")
    replayed = [V0] + [s["after"] for s in stores]

    # A2: the sampler's distinct-value sequence must be a subsequence of the replay
    sval = [samples[0]["store"]] if samples else []
    for s in samples[1:]:
        if s["store"] != sval[-1]:
            sval.append(s["store"])
    trace["sampler_values"] = sval
    i = 0
    missed = []
    for v in sval:
        while i < len(replayed) and replayed[i] != v:
            i += 1
        if i == len(replayed):
            missed.append(v)
        else:
            i += 1
    if missed:
        fails.append(f"A2 sampler values no store produced (uninstrumented write): {missed}")
    if "error" in trace["post"]:
        fails.append(f"post-detach read-back failed: {trace['post']['error']}")

    # A3: anchor accounting. At every boundary (and at the run start, and at the
    # post-detach read-back) the field value the game actually holds must equal
    # start + sum(deltas of every store whose wall time is <= that anchor). Anchors
    # being equal two rows in a row makes the per-boundary sums follow.
    anchors = [("start", 0.0, V0)]
    for frm, to, w, val in flips:
        anchors.append((f"{frm}->{to}", w, val))
    if samples:
        anchors.append(("watch-end", samples[-1]["wall"], samples[-1]["store"]))
    per = []
    for ai in range(len(anchors) - 1):
        lo_l, lo_w, lo_v = anchors[ai]
        hi_l, hi_w, hi_v = anchors[ai + 1]
        inw = [s for s in stores if lo_w < s["wall"] <= hi_w]
        tot = sum(s["delta"] for s in inw)
        net = hi_v - lo_v
        # the replayed value at the high anchor, from the start
        rep = V0 + sum(s["delta"] for s in stores if s["wall"] <= hi_w)
        note = ""
        if rep != hi_v:
            # diagnostic only (never a pass): would moving ONE store across this cut
            # reconcile it? that is a timestamp artifact, not an unattributed write.
            outv = [s for s in inw if rep - s["delta"] == hi_v]
            inv = [s for s in stores if s["wall"] > hi_w and rep + s["delta"] == hi_v]
            if outv or inv:
                s0 = (outv or inv)[0]
                note = (f" (store #{s0['n']} {s0['site']} delta {s0['delta']:+d} straddles "
                        f"the cut — boundary attribution uncertain, NOT an unattributed write)")
            else:
                note = " (no single store explains the gap — an uninstrumented write)"
            fails.append(f"A3 anchor {hi_l}: replayed value {rep} != observed {hi_v}{note}")

        per.append(dict(boundary=hi_l, wall=[lo_w, hi_w], stores=len(inw), sum_delta=tot,
                        net=net, first=lo_v, last=hi_v, replayed_at_anchor=rep))
        if tot != net:
            fails.append(f"A3 boundary {hi_l}: sum(store deltas)={tot} != observed net {net}")
    trace["per_boundary"] = per
    trace["anchors"] = [dict(label=l, wall=(w if w != float("inf") else None), observed=v)
                        for l, w, v in anchors]
    if len(flips) < a.boundaries:
        fails.append(f"A4 only {len(flips)} boundaries flipped (need {a.boundaries})")
    if not stores:
        fails.append("A4 no store to +0x40 recorded — the enumeration proves nothing")
    if not any(p["net"] != 0 for p in per):
        fails.append("A4 no boundary shows a net change of the field — vacuous run")

    # ---- the table the milestone asked for -----------------------------------
    print(f"\n{'#':>3} {'pc':>9} {'site':24s} {'before':>6} {'after':>6} {'d':>4} "
          f"{'pend':>4} {'head':>5} {'d0':>3} {'+0x3c':>5} {'+0xcc':>5}")
    for srec in stores:
        print(f"{srec['n']:>3} {srec['pc']:08x} {srec['site']:24s} {srec['before']:>6} "
              f"{srec['after']:>6} {srec['delta']:>+4} {srec['pend']:>4} {srec['head']:>5} "
              f"{srec['d0']:>3} {srec['progress']:>5} {srec['rate']:>5}")
    print("\nper boundary:")
    for p in per:
        print(f"  {p['boundary']}: {p['stores']} stores, sum(delta)={p['sum_delta']}, "
              f"observed {p['first']}->{p['last']} net={p['net']}")
    print("\nOBSERVATIONS (read back, not inferred):")
    adds = [s for s in stores if "income-add" in s["site"]]
    for s in adds[:8]:
        print(f"  add at wall {s['wall']}: delta {s['delta']:+d} while the d0 field read "
              f"{s['d0']} -> {'EQUALS d0' if s['delta'] == s['d0'] else 'NOT d0'}")
    pays = [s for s in stores if ".pay" in s["site"]]
    for s in pays[:8]:
        print(f"  pay at wall {s['wall']}: {s['before']}->{s['after']} with pending {s['pend']}"
              f"{' (pending 0!)' if s['pend'] == 0 else ''}")
    print(f"  sampler value sequence: {sval}")
    print(f"  per-boundary net changes: "
          f"{[f'{p['boundary']}={p['net']}' for p in per]}")
    print(f"trace: {jpath}")

    if fails:
        print("\nFAIL store-sequence enumeration:")
        for f_ in fails:
            print(f"  - {f_}")
        return 1
    print(f"\nPASS store-sequence enumeration: {len(stores)} stores over {len(flips)} "
          f"boundaries, every store attributed to a named census site, every sampler "
          f"value reproduced by the replay, per-boundary sums equal the observed net "
          f"changes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
