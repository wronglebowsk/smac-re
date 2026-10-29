#!/usr/bin/env python3
"""M102 — the model AT the rebuild's own stores (FUN_005a15a0, slot 10 of the 11-dword block).

M101 proved the OFFLINE model (rows + accumulator D) reproduces the live multiplier on a coherent
snapshot, but the mult LAGS D by one accrual, so comparing pre/post snapshots is state-dependent.
M102 evaluates the model AT the store sites, where every input is printed in the same event:

  0x5a16d9 `mov [edi],eax`  (edi = dest BYTE addr, ecx = row value, eax = old + ecx) — runs 11 slots
    x 4 cats per rebuild; the register condition selects slot 10. A category SKIPS its add iff
    row10 < 0 and (cat,idx) in {(3,1)->byte(304*ds:0x985b90),(3,3)/(2,1)->byte(304*ds:0x985b9c)}
    == fac (bytes 0x5a1601-0x5a1671). Project-table legs type 5/6 (key==cat, val==idx) mutate [edi]
    BEFORE the add, so they are baked into `old` read at the hit.
  0x5a179e `add [eax],edi` (eax = dest, edi = D slot value; 11-iteration loop at 0x5a1799) — slot-10
    iteration iff eax == A10(f). Runs iff param_5 == 0 (0x5a1712; M101: always 0 live).
  0x5a1807 `mov [ecx],eax` — clamp loop over [0x927a9c+f*1436] count, types @[+0x20], keys @[+0x40]:
    type 4 = clamp 0..999 (always stores), type 10 = halve-if-negative (stores only when < 0).
  Entry bps 0x59ec00 / 0x59ec90 (the ONLY two displacement stores to 0x94d700, s156 census) print
    *(int *)$esp = the return address -> names the caller of the +10 D accrual (M101 blocker).
  CALL bp 0x520909 (edi = fac) groups events per rebuild.

PREDICTIONS from the baseline before the run (--predict): MODEL = 2 rebuilds/fac/round (M100 G9),
per rebuild CAT == 4 - skips(rows,eras), DADD == 1, CLAMP == predicted from the live clamp table,
stored == old + src at every hit, chain old_0 == 0. NULL = 0 events (no rebuild runs in the window).
They disagree on every candidate. NO POKES: silent bps fire on EXECUTION, so the watchpoint's
unchanged-store suppression (m100 trap) is moot and the box needs no sentinel.

  python3 scripts/m102_rebuild_at_hit.py --predict
  python3 scripts/m102_rebuild_at_hit.py --tag m102hit1 --boundaries 2
"""
import json
import os
import re
import signal
import struct
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import m55_boundary as M  # noqa: E402
import m99_param2 as P  # noqa: E402  (helpers: STRIDE, CP, load_funcs, contain, read_state)

ROOT = os.path.dirname(HERE)
EVID = os.path.join(ROOT, "evidence")
SCRATCH = os.path.join(ROOT, "scratch")
STRIDE = P.STRIDE                       # 8380
A10 = 0x94d6a4                            # block A slot 10 (the multiplier), + f*STRIDE
IDX0 = 0x94d658                           # 4 category record indices, + f*STRIDE + 4*cat
D10A = 0x94d728                           # accumulator D slot 10, + f*STRIDE
ROW_BASE, CAT_STRIDE, ROW_STRIDE, ROW10 = 0x92babc, 212, 44, 40
CLT = 0x927a9c                            # count; types +0x20, keys +0x40, vals +0x60; + f*1436
CLT_STRIDE = 1436
ERA0, ERA1, ERA_BASE, ERA_REC = 0x985b90, 0x985b9c, 0x95da14, 304
CAT_PC, DADD_PC, CLAMP_PC = 0x5a16d9, 0x5a179e, 0x5a1807
ENT_PCS = (0x59ec00, 0x59ec90)
CALL_PC = 0x520909
WFACS = [int(x) for x in re.split(",", os.environ.get("M102_WFACS", "1,2,3,6"))]
RND, CPP = "*(int *)0x985afc", "*(int *)0x985dcc"

TMPL = r"""set pagination off
set confirm off
@@BLOCKS@@printf "ARMED 15 silent bps (4 CAT + 4 DADD + 4 CLAMP + 2 ENT + 1 CALL)\n"
continue
"""

BPTPL = r"""break *@@PC@@ if @@COND@@
commands
silent
printf "@@LINE@@\n",@@ARGS@@
continue
end
"""

BPU = r"""break *@@PC@@
commands
silent
printf "@@LINE@@\n",@@ARGS@@
continue
end
"""


def row_addr(f, cat):
    return ROW_BASE + CAT_STRIDE * cat


def idx_addr(f, cat):
    return IDX0 + f * STRIDE + 4 * cat


def gdb_script():
    blocks = []
    for f in WFACS:
        a = A10 + f * STRIDE
        ahex = "%#x" % a
        dhex = "%#x" % (D10A + f * STRIDE)
        rows = ", ".join("*(int *)(%#x+(*(int *)(%#x))*%d+%d)"
                         % (row_addr(f, c), idx_addr(f, c), ROW_STRIDE, ROW10) for c in range(4))
        blocks.append(BPTPL.replace("@@PC@@", "%#x" % CAT_PC).replace("@@COND@@", "$edi==%s" % ahex)
                      .replace("@@LINE@@", "M102S CAT fac=%d dest=0x%%x old=%%d src=%%d new=%%d "
                                "r0=%%d r1=%%d r2=%%d r3=%%d d10=%%d e0=%%d e1=%%d b0=%%d b1=%%d "
                                "round=%%d cp=%%d" % f)
                      .replace("@@ARGS@@", ", ".join([
                          "$edi", "*(int *)($edi)", "$ecx", "$eax", rows,
                          "*(int *)%s" % dhex,
                          "*(int *)0x985b90", "*(int *)0x985b9c",
                          "*(unsigned char *)(%#x+%d*(*(int *)0x985b90))" % (ERA_BASE, ERA_REC),
                          "*(unsigned char *)(%#x+%d*(*(int *)0x985b9c))" % (ERA_BASE, ERA_REC),
                          RND, CPP])))
        blocks.append(BPTPL.replace("@@PC@@", "%#x" % DADD_PC).replace("@@COND@@", "$eax==%s" % ahex)
                      .replace("@@LINE@@", "M102S DADD fac=%d dest=0x%%x old=%%d src=%%d d10=%%d "
                                "round=%%d cp=%%d" % f)
                      .replace("@@ARGS@@", ", ".join(["$eax", "*(int *)($eax)", "$edi",
                                                      "*(int *)%s" % dhex, RND, CPP])))
        blocks.append(BPTPL.replace("@@PC@@", "%#x" % CLAMP_PC).replace("@@COND@@", "$ecx==%s" % ahex)
                      .replace("@@LINE@@", "M102S CLAMP fac=%d dest=0x%%x old=%%d new=%%d "
                                "round=%%d cp=%%d" % f)
                      .replace("@@ARGS@@", ", ".join(["$ecx", "*(int *)($ecx)", "$eax", RND, CPP])))
    for pc in ENT_PCS:
        blocks.append(BPU.replace("@@PC@@", "%#x" % pc)
                      .replace("@@LINE@@", "M102S ENT pc=0x%x ret=0x%%x round=%%d cp=%%d" % pc)
                      .replace("@@ARGS@@", ", ".join(["*(int *)($esp)", RND, CPP])))
    blocks.append(BPU.replace("@@PC@@", "%#x" % CALL_PC)
                  .replace("@@LINE@@", "M102S CALL fac=%d round=%%d cp=%%d" % -1)
                  .replace("@@ARGS@@", ", ".join(["$edi", RND, CPP])))
    # the CALL line carries fac=%d as a printf ARGUMENT, not a literal:
    blocks[-1] = blocks[-1].replace("M102S CALL fac=-1 round=%d",
                                    "M102S CALL fac=%d round=%d").replace(
        '"M102S CALL fac=%d round=%d cp=%d\\n",$edi', '"M102S CALL fac=%d round=%d cp=%d\\n",$edi')
    return TMPL.replace("@@BLOCKS@@", "".join(blocks))


KV = re.compile(r"^(M102S) (CAT|DADD|CLAMP|ENT|CALL)((?: [a-z][a-z0-9_]*=-?[\dxa-f]+)+)"
                r" round=(\d+) cp=(\d+)\s*$")


def parse(text):
    ev, unparsed, armed = [], [], False
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        m2 = KV.match(ln)
        if m2:
            d = {"tag": m2.group(2)}
            for tok in m2.group(3).split():
                k, v = tok.split("=", 1)
                d[k] = int(v, 16) if v.startswith("0x") else int(v)
            d["round"], d["cp"] = int(m2.group(4)), int(m2.group(5))
            ev.append(d)
            continue
        if not armed:
            if "ARMED" in ln:
                armed = True
            continue
        if (ln.startswith("[New LWP") or ln.startswith("[Thread ") or ln.startswith("[Switching")
                or ln.startswith("[Detached") or ln.startswith("[Inferior")
                or re.match(r"Thread \d+ ", ln) or "__kernel_vsyscall" in ln
                or re.match(r"0x[0-9a-f]+ in ", ln)):
            continue
        unparsed.append(ln)
    return ev, unparsed


def rd32(mm, addr):
    return struct.unpack("<i", M.rd(mm, addr, 4))[0]


def read_inputs(mm):
    """per-fac live inputs: idx[4], row10[4], d10, clamp entries, era values."""
    e0, e1 = rd32(mm, ERA0), rd32(mm, ERA1)
    out = {}
    for f in range(8):
        idx = [rd32(mm, idx_addr(f, c)) for c in range(4)]
        rows = [rd32(mm, row_addr(f, c) + ROW_STRIDE * idx[c] + ROW10) for c in range(4)]
        cl_n = rd32(mm, CLT + f * CLT_STRIDE)
        cl = [(rd32(mm, CLT + f * CLT_STRIDE + 0x20 + 4 * i),
               rd32(mm, CLT + f * CLT_STRIDE + 0x40 + 4 * i)) for i in range(max(cl_n, 0))]
        out[f] = {"idx": idx, "row10": rows, "d10": rd32(mm, D10A + f * STRIDE),
                  "clamp": cl, "a10": rd32(mm, A10 + f * STRIDE),
                  "era": (e0, e1,
                          mm_read8(mm, ERA_BASE + ERA_REC * e0) if e0 >= 0 else -1,
                          mm_read8(mm, ERA_BASE + ERA_REC * e1) if e1 >= 0 else -1)}
    return out


def mm_read8(mm, addr):
    return struct.unpack("B", M.rd(mm, addr, 1))[0]


def skips(inp, f):
    """categories whose slot-10 add is skipped, from (rows, idx, era bytes). inp = the per-fac dict."""
    e0, e1, b0, b1 = inp["era"]
    out = []
    for c in (2, 3):
        i = inp["idx"][c]
        if inp["row10"][c] >= 0:
            continue
        if (c, i) == (3, 1) and e0 >= 0 and b0 == f:
            out.append(c)
        elif (c, i) in ((3, 3), (2, 1)) and e1 >= 0 and b1 == f:
            out.append(c)
    return out


def clamp_pred(inp, f):
    """clamp events on slot 10 per rebuild: type 4 always stores; type 10 stores iff value < 0.
    inp = the per-fac dict."""
    return [(t, k) for (t, k) in inp["clamp"] if k == 10 and t in (4, 10)]


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--boundaries", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=150)
    ap.add_argument("--tag", default="m102hit1")
    ap.add_argument("--predict", action="store_true", help="print live inputs + predictions, no touch")
    a = ap.parse_args()

    pid = M.find_pid()
    with open("/proc/%d/mem" % pid, "rb", 0) as m:
        st = P.read_state(m)
        inp = read_inputs(m)
    rnd = st["round"]
    human = (st["mask"] & -st["mask"]).bit_length() - 1
    print("pid %d round %d cp %d mask %#x human fac%d" % (pid, rnd, st["cp"], st["mask"], human),
          flush=True)
    print("--- baseline (the PREDICTION table, computed before the run) ---", flush=True)
    pred = {}
    for f in range(8):
        d = inp[f]
        sk = skips(d, f)
        ncat = 4 - len(sk)
        cl = clamp_pred(d, f)
        final = sum(d["row10"][c] for c in range(4) if c not in sk) + d["d10"]
        pred[f] = {"ncat": ncat, "clamp": len(cl), "final": final}
        mark = "WATCHED" if f in WFACS else "        "
        print("  fac %d %s: a10 %3d  idx %s  row10 %s  d10 %4d  skips %s  clamp10 %s  "
              "PREDICTED next mult %d  era %s" % (f, mark, d["a10"], d["idx"], d["row10"], d["d10"],
                                                  sk, cl, final, d["era"]), flush=True)
    mixed = any(pred[f]["final"] < 0 for f in WFACS) and any(pred[f]["final"] > 0 for f in WFACS)
    nz = [f for f in WFACS if any(v != 0 for v in inp[f]["row10"]) or inp[f]["d10"] != 0]
    print("  MODEL: 2 rebuilds/fac/round (M100 G9): CAT == %s per fac per round, DADD == 2, "
          "stored == old + src AT every hit, chain old_0 == 0; CLAMP == predicted"
          % {f: pred[f]["ncat"] * 2 for f in WFACS}, flush=True)
    print("  NULL : 0 CAT/DADD events (no rebuild in the window) and A10 unchanged at the end",
          flush=True)
    print("  DISCRIMINATES: nonzero inputs on facs %s -> model and null disagree on every candidate"
          % nz, flush=True)
    print("  STATE PRECONDITION (M101 law, checked BEFORE the run): mixed signs %s "
          "(predicted %s)" % (mixed, {f: pred[f]["final"] for f in WFACS}), flush=True)
    if a.predict:
        return

    gpath = os.path.join(SCRATCH, "%s.gdb" % a.tag)
    lpath = os.path.join(EVID, "%s.gdblog" % a.tag)
    os.makedirs(SCRATCH, exist_ok=True)
    open(gpath, "w").write(gdb_script())
    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath,
                          "-p", str(pid)], stdout=log, stderr=subprocess.STDOUT)
    time.sleep(3.0)
    head = open(lpath, "r", errors="replace").read()
    n_bp = head.count("Breakpoint ")
    if "ARMED" not in head or n_bp < 15:
        try:
            os.kill(g.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
        subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
        raise SystemExit("gdb did not arm 15 bps (saw %d):\n%s" % (n_bp, head[-1200:]))
    print("armed: %d bps" % n_bp, flush=True)

    t0 = time.time()
    rc_ok = True
    for k in range(a.boundaries):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "smac_play.py"),
                            "--turns", "1", "--timeout", str(a.timeout), "--no-escape",
                            "3000", "--orders-per-turn", "1", "--verbose",
                            "--tag", "%s_r%d" % (a.tag, k)], capture_output=True, text=True)
        if r.returncode != 0:
            rc_ok = False
        print("  boundary %d: rc=%d t=%.0fs %s" % (k, r.returncode, time.time() - t0,
              r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""), flush=True)

    waited = 0
    while waited < 120:
        with open("/proc/%d/mem" % pid, "rb", 0) as mm:
            cp = rd32(mm, P.CP)
        if cp == human:
            break
        time.sleep(2)
        waited += 2
    print("  settle: cp back to the human fac%d after %ds" % (human, waited), flush=True)
    # the human segment's rebuild fires at segment START, seconds after cp flips; detach must
    # wait for it (M98 trap: early detach leaves the LAST recomputes UNLOGGED):
    target = "M102S CALL fac=%d round=%d" % (human, rnd + a.boundaries)
    extra = 0
    while extra < 90:
        try:
            if target in open(lpath, "r", errors="replace").read():
                break
        except OSError:
            pass
        time.sleep(2)
        extra += 2
    print("  settle+: %s %s after %ds" % (target, "seen" if extra < 90 else "MISSING", extra),
          flush=True)
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

    tracer = subprocess.run(["grep", "-m1", "TracerPid", "/proc/%d/status" % pid],
                            capture_output=True, text=True).stdout.split()[-1]
    with open("/proc/%d/mem" % pid, "rb", 0) as mm:
        st2 = P.read_state(mm)
        inp2 = read_inputs(mm)
    r_after = st2["round"]
    print("  after: round %d tracer %s" % (r_after, tracer), flush=True)

    text = open(lpath, "r", errors="replace").read()
    ev, unparsed = parse(text)
    with open(os.path.join(SCRATCH, "%s_seq.jsonl" % a.tag), "w") as fh:
        for d in ev:
            fh.write(json.dumps(d) + "\n")
        for ln in unparsed:
            fh.write(json.dumps({"tag": "?", "raw": ln}) + "\n")
    by = {}
    for i, d in enumerate(ev):
        by.setdefault(d["tag"], []).append((i, d))
    cat = [d for _i, d in by.get("CAT", [])]
    dadd = [d for _i, d in by.get("DADD", [])]
    clm = [d for _i, d in by.get("CLAMP", [])]
    ent = [d for _i, d in by.get("ENT", [])]
    call = [d for _i, d in by.get("CALL", [])]
    print("--- events: CAT=%d DADD=%d CLAMP=%d ENT=%d CALL=%d ---"
          % (len(cat), len(dadd), len(clm), len(ent), len(call)), flush=True)

    # group events BACKWARD from the CALL bp: 0x520909 fires AFTER the rebuild returns, so a
    # rebuild's CAT/DADD/CLAMP events precede its CALL line; segments do not interleave, so the
    # buffer since the previous CALL belongs to this CALL's faction.
    rebuilds = []
    buf = []
    for d in ev:
        if d["tag"] != "CALL":
            buf.append(d)
            continue
        rebuilds.append({"fac": d["fac"], "round": d["round"],
                         "cat": [x for x in buf if x["tag"] == "CAT" and x["fac"] == d["fac"]],
                         "dadd": [x for x in buf if x["tag"] == "DADD" and x["fac"] == d["fac"]],
                         "clamp": [x for x in buf if x["tag"] == "CLAMP" and x["fac"] == d["fac"]]})
        buf = []

    funcs = P.load_funcs()
    ent_pcs = {d["pc"]: d for d in ent}
    for pc in sorted(ent_pcs):
        nm = P.contain(pc, funcs) or "UNMAPPED"
        print("  ENT 0x%x in %s" % (pc, nm), flush=True)
    rets = {}
    for d in ent:
        nm = P.contain(d["ret"], funcs) or "UNMAPPED"
        rets.setdefault((d["pc"], d["ret"]), [0, nm])[0] += 1
    for (pc, ret), (n, nm) in sorted(rets.items()):
        print("  ENT 0x%x ret 0x%x -> %s x%d" % (pc, ret, nm, n), flush=True)

    g1 = "ARMED" in head and n_bp >= 15
    g2 = rc_ok and r_after == rnd + a.boundaries
    # G3: per rebuild CAT == 4 - skips(at-hit), DADD == 1
    g3, g3det = True, []
    for grp in rebuilds:
        f = grp["fac"]
        if f not in WFACS:
            continue
        hit = {"idx": None}
        rows = {c: grp["cat"][0]["r%d" % c] for c in range(4)} if grp["cat"] else {}
        d10 = (grp["dadd"][0]["d10"] if grp["dadd"] else
               (grp["cat"][0]["d10"] if grp["cat"] else None))
        if not grp["cat"]:
            nsk = 4  # cannot happen unless all skipped; DADD old==0 checks it
        else:
            c0 = grp["cat"][0]
            sk = []
            for c in (2, 3):
                if rows[c] >= 0:
                    continue
                i_ = None  # idx at hit not printed; rows printed ARE at idx(cat) so skip test
                # uses (cat, idx) — idx is STATIC within the window (written only at 0x4b2715,
                # the chooser; no completion fires this window) -> use the baseline idx
                i_ = inp[f]["idx"][c]
                if (c, i_) == (3, 1) and c0["e0"] >= 0 and c0["b0"] == f:
                    sk.append(c)
                elif (c, i_) in ((3, 3), (2, 1)) and c0["e1"] >= 0 and c0["b1"] == f:
                    sk.append(c)
            nsk = len(sk)
        ok = len(grp["cat"]) == 4 - nsk and len(grp["dadd"]) == 1
        g3 &= ok and grp["round"] > 0
        g3det.append((f, grp["round"], len(grp["cat"]), 4 - nsk, len(grp["dadd"]), ok))
    for t in g3det:
        print("  REBUILD fac%d r%d: CAT %d (pred %d) DADD %d %s"
              % (t[0], t[1], t[2], t[3], t[4], "OK" if t[5] else "BAD"), flush=True)
    per = {}
    for t in g3det:
        per[(t[0], t[1])] = per.get((t[0], t[1]), 0) + 1
    # coverage: every watched faction must rebuild in >= 2 distinct rounds of the window (the
    # M100 shape gate); exact per-round completeness is impossible mid-segment at detach.
    rounds_by_fac = {}
    for t in g3det:
        rounds_by_fac.setdefault(t[0], set()).add(t[1])
    print("  rebuild rounds per fac: %s" % {f: sorted(v) for f, v in sorted(rounds_by_fac.items())},
          flush=True)
    g3 &= all(len(rounds_by_fac.get(f, set())) >= 2 for f in WFACS)
    g4 = all(d["new"] == d["old"] + d["src"] for d in cat)
    g5 = all(d["src"] in (d["r0"], d["r1"], d["r2"], d["r3"]) for d in cat)
    g6 = True
    for grp in rebuilds:
        if grp["fac"] not in WFACS:
            continue
        seq, prev = [], 0
        for d in grp["cat"]:
            g6 &= (d["old"] == prev and d["dest"] == A10 + grp["fac"] * STRIDE)
            prev = d["new"]
        for d in grp["dadd"]:
            g6 &= (d["old"] == prev and d["dest"] == A10 + grp["fac"] * STRIDE)
            prev = d["old"] + d["src"]
        g6 &= bool(grp["dadd"])
    g7 = all(d["src"] == d["d10"] for d in dadd)
    g8 = len(clm) == sum(pred[grp["fac"]]["clamp"] for grp in rebuilds if grp["fac"] in WFACS)
    for d in clm:
        t4 = max(0, min(999, d["old"]))
        t10 = ((d["old"] + 1) >> 1) if d["old"] < 0 else d["old"]
        g8 &= d["new"] in ((t4, "type4"), (t10, "type10")) or d["new"] == t4 or d["new"] == t10
    g9 = all(P.contain(d["pc"], funcs) and P.contain(d["ret"], funcs) for d in ent) \
        and (bool(ent) or all(inp[f]["d10"] == inp2[f]["d10"] for f in range(8)))
    g10 = all(d["cp"] == d["fac"] for d in cat + dadd + call if "fac" in d)
    g11 = tracer == "0"
    g12 = not unparsed
    g13 = any(d["new"] < 0 or d["src"] < 0 for d in cat + dadd)
    lastg = {}
    for grp in rebuilds:
        if grp["fac"] in WFACS and grp["dadd"]:
            lastg[grp["fac"]] = grp["dadd"][0]
    g14 = len(lastg) == len(WFACS) and all(d["old"] + d["src"] == inp2[f]["a10"]
                                           for f, d in lastg.items())
    gates = [("G1_armed15", g1), ("G2_boundary", g2), ("G3_counts_at_hit", g3),
             ("G4_new_eq_old_plus_src", g4), ("G5_src_is_a_row10", g5), ("G6_chain_from_zero", g6),
             ("G7_dadd_src_is_D10", g7), ("G8_clamp_predicted", g8), ("G9_accrual_callers_named", g9),
             ("G10_cp_eq_fac", g10), ("G11_tracer0", g11), ("G12_parsed", g12),
             ("G13_negative_leg", g13), ("G14_final_readback", g14)]
    for n, v in gates:
        print("  %s: %s" % (n, v), flush=True)
    ok = all(v for _n, v in gates)
    print("ACCEPTANCE %s: %s (%d/%d) CAT=%d DADD=%d CLAMP=%d ENT=%d CALL=%d rounds %d->%d "
          "finalA10=%s predicted=%s unparsed=%d" % (
              a.tag, "PASS" if ok else "FAIL", sum(1 for _n, v in gates if v), len(gates),
              len(cat), len(dadd), len(clm), len(ent), len(call), rnd, r_after,
              {f: inp2[f]["a10"] for f in WFACS}, {f: pred[f]["final"] for f in WFACS},
              len(unparsed)), flush=True)


if __name__ == "__main__":
    main()
