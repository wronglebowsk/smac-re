#!/usr/bin/env python3
"""M99 — who feeds param_2 into FUN_005aadf0 (the advance accumulator [fac*8380+0x94d7f8])?

STATIC (ghidra_out + whole-.text grep): FUN_005aadf0 has EXACTLY ONE call site in .text,
0x4f35cb inside FUN_004f34b0 (per-base upkeep tail, called at 0x4f5c2e from FUN_004f5a70),
and it pushes `edx = esi/100` (magic 0x51eb851f imul + sar 5) with esi built at 0x4f3585-0x4f35b2:

  edi = [base_record + 0x104]                      (0x4f34d9; DAT_008f0d60 = current base)
  if the FUN_00507410(0x17) policy leg fires: edi = edi/2          (0x4f3513-0x4f351a)
  if round < mult*-5: edi = 0; if (round<5 && [fac*8380+0x94d438]<2): edi = 0
  [fac*8380+0x94dc30] += edi                                      (store 0x4f3560)
  esi = (clamp([fac*8380+0x94d6a4],-5,5) + 10) * edi * 10         (0x4f3582-0x4f3590)
  carry = [fac*8380+0x94d808] + esi%100; if carry > 99: esi += 100, carry -= 100
  FUN_005aadf0(fac, esi/100)                                      (0x4f35c9-0x4f35cb)

So param_2 = the base's research output scaled by the faction's research multiplier, in
whole points, with the tenths carried in [fac*8380+0x94d808].

The harness puts silent bps at the six FUN_004f34b0 sites + the callee entry + the acc
store/reset/second-add, 4 HARDWARE watchpoints on 4 factions' accumulator (the "any other
writer" check), plays N boundaries, POKES one faction's multiplier before each boundary (the
controlled experiment), then reads the watched accumulators back from /proc.

  python3 scripts/m99_param2.py --predict
  python3 scripts/m99_param2.py --tag m99p1 --boundaries 2
"""
import argparse
import bisect
import csv
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

ROOT = os.path.dirname(HERE)
EVID = os.path.join(ROOT, "evidence")
SCRATCH = os.path.join(ROOT, "scratch")
STRIDE = 8380
ACC, CARRY, C30, MULT = 0x94d7f8, 0x94d808, 0x94dc30, 0x94d6a4
FIELD, SLOT, FLAG, ERA2 = 0x94d800, 0x94d7fc, 0x94d430, 0x94d438
ROUND, CP, MASK, AC4 = 0x985afc, 0x985dcc, 0x985b10, 0x985ac4
RAW = 0x104                                   # base-record research output
P1, P2, P3, P4, P5, P6 = 0x4f34df, 0x4f351c, 0x4f3558, 0x4f3566, 0x4f35b8, 0x4f35c9
CALLSITE_RET = 0x4f35d0                       # return pc of the ONLY call to FUN_005aadf0
C1, A1, A2, S1, R1 = 0x5aadf0, 0x5aaee1, 0x5aaef3, 0x5aaf1b, 0x5aaf66
# every static store to [reg+0x94d7f8] in .text, as the pc gdb REPORTS (store + length)
WP_EXPECT = {0x5090a9, 0x51038c, 0x51bf5e, 0x51bfce, 0x56e024, 0x594158, 0x59f24c,
             0x5aaef1, 0x5aaf1b, 0x5aaf66}
WFACS = [int(x) for x in re.split(",", os.environ.get("M99_WFACS", "2,3,5,6"))]
POKE_FAC = int(os.environ.get("M99_POKE_FAC", "3"))

TMPL = r"""set pagination off
set confirm off
set can-use-hw-watchpoints 1
@@WATCHES@@@@BLOCKS@@printf "ARMED @@N@@ hw watchpoints at @@ADDRS@@; @@NB@@ silent bps at @@BPS@@\n"
continue
"""

WBLOCK = r"""watch *(int *)@@A@@
commands
silent
printf "M99W WP pc=0x%x new=%d fac=@@F@@ round=%d cp=%d\n", $pc, *(int *)@@A@@, *(int *)0x985afc, *(int *)0x985dcc
continue
end
"""

BPTPL = r"""break *@@PC@@
commands
silent
@@SETS@@printf "@@LINE@@\n"@@ARGS@@
continue
end
"""

RND = "*(int *)0x985afc"
CPP = "*(int *)0x985dcc"


def wrap(x):
    x &= 0xffffffff
    return x - 0x100000000 if x >= 0x80000000 else x


def tdiv(a, b):
    """C truncating division on 32-bit signed operands."""
    a, b = wrap(a), wrap(b)
    q = abs(a) // abs(b)
    return wrap(q if (a >= 0) == (b >= 0) else -q)


def scale(raw, mult, carry_old):
    """FUN_004f34b0 0x4f3582-0x4f35cb from the values read AT the hit."""
    m = max(-5, min(5, wrap(mult)))
    esi = wrap((m + 10) * wrap(raw) * 10)
    q = tdiv(esi, 100)
    rem = wrap(esi - q * 100)
    cs = wrap(wrap(carry_old) + rem)
    if cs > 99:
        return esi + 100, cs - 100, tdiv(esi + 100, 100)
    return esi, cs, q


def gdb_script():
    blocks, addrs = [], []
    for f in WFACS:
        a = ACC + f * STRIDE
        addrs.append("%#x" % a)
        blocks.append(WBLOCK.replace("@@A@@", "%#x" % a).replace("@@F@@", str(f)))
    bps = [
        ("P1", P1, "M99B P1 pc=0x4f34df base=0x%x fac=%d raw=%d round=%d cp=%d",
         ["$eax", "$ebx", "$edi", RND, CPP]),
        ("P2", P2, "M99B P2 pc=0x4f351c fac=%d half=%d round=%d cp=%d",
         ["$ebx", "$edi", RND, CPP]),
        ("P3", P3, "M99B P3 pc=0x4f3558 fac=%d raw2=%d mult=%d c30o=%d carryo=%d era2=%d "
                   "ac4=%d round=%d cp=%d",
         ["$ebx", "$edi", "*(int *)($ecx+0x94d6a4)", "*(int *)($ecx+0x94dc30)",
          "*(int *)($ecx+0x94d808)", "*(int *)($ecx+0x94d438)", "*(int *)0x985ac4",
          RND, CPP]),
        ("P4", P4, "M99B P4 pc=0x4f3566 fac=%d c30n=%d round=%d cp=%d",
         ["$ebx", "*(int *)($ecx+0x94dc30)", RND, CPP]),
        ("P5", P5, "M99B P5 pc=0x4f35b8 fac=%d scaled=%d carryn=%d round=%d cp=%d",
         ["$ebx", "$esi", "$eax", RND, CPP]),
        ("P6", P6, "M99B P6 pc=0x4f35c9 fac=%d p2=%d round=%d cp=%d",
         ["$ebx", "$edx", RND, CPP]),
        ("C1", C1, "M99C C1 pc=0x5aadf0 fac=%d p2=%d ret=0x%x round=%d cp=%d",
         ["*(int *)($esp+4)", "*(int *)($esp+8)", "*(int *)($esp)", RND, CPP]),
        ("A1", A1, "M99C A1 pc=0x5aaee1 fac=%d ebx=%d acco=%d slot=%d flag=%d field=%d "
                   "round=%d cp=%d",
         ["$edi", "$ebx", "*(int *)($esi+0x94d7f8)", "*(int *)($esi+0x94d7fc)",
          "*(int *)($esi+0x94d430)", "*(int *)($esi+0x94d800)", RND, CPP]),
        ("A2", A2, "M99C A2 pc=0x5aaef3 fac=%d accn=%d round=%d cp=%d",
         ["$edi", "*(int *)($esi+0x94d7f8)", RND, CPP]),
        ("S1", S1, "M99C S1 pc=0x5aaf15 fac=%d acc2=%d round=%d cp=%d",
         ["$edi", "*(int *)($esi+0x94d7f8)", RND, CPP]),
        ("R1", R1, "M99C R1 pc=0x5aaf5c fac=%d acc0=%d round=%d cp=%d",
         ["$edi", "*(int *)($esi+0x94d7f8)", RND, CPP]),
    ]
    bp_txt, bp_pcs = [], []
    for tag, pc, line, args in bps:
        bp_pcs.append("%#x" % pc)
        bp_txt.append(BPTPL.replace("@@PC@@", "%#x" % pc).replace("@@SETS@@", "")
                      .replace("@@LINE@@", line)
                      .replace("@@ARGS@@", "".join(", " + a2 for a2 in args)))
    blocks += bp_txt
    return (TMPL.replace("@@WATCHES@@", "".join(blocks[:len(WFACS)]))
            .replace("@@BLOCKS@@", "".join(blocks[len(WFACS):]))
            .replace("@@N@@", str(len(WFACS))).replace("@@ADDRS@@", " ".join(addrs))
            .replace("@@NB@@", str(len(bp_pcs))).replace("@@BPS@@", " ".join(bp_pcs)))


KV = re.compile(r"^(M99[WBC]) (\w+)((?: [a-z][a-z0-9_]*=-?[\dxa-f]+)+) round=(\d+) cp=(\d+)\s*$")


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
            d["round"] = int(m2.group(4))
            d["cp"] = int(m2.group(5))
            ev.append(d)
            continue
        if not armed:
            if "ARMED" in ln:
                armed = True
            continue
        if ("Hardware watchpoint" in ln or ln.startswith("[Inferior")
                or ln.startswith("[New LWP") or ln.startswith("[Thread ")
                or ln.startswith("[Detached") or ln.startswith("[Switching to LWP")
                or re.match(r"Thread \d+ ", ln)
                or "__kernel_vsyscall" in ln or re.match(r"0x[0-9a-f]+ in ", ln)):
            continue
        unparsed.append(ln)
    return ev, unparsed


def load_funcs():
    rows = []
    with open(os.path.join(ROOT, "ghidra_out", "index.csv")) as fh:
        for r in csv.DictReader(fh):
            rows.append((int(r["addr"], 16), r["name"], int(r["size_bytes"])))
    rows.sort()
    return rows


def contain(addr, funcs):
    starts = [a for a, _n, _s in funcs]
    i = bisect.bisect_right(starts, addr) - 1
    if i >= 0 and starts[i] <= addr < starts[i] + funcs[i][2]:
        return funcs[i][1]
    return None


def read_state(m):
    def i32(a):
        return struct.unpack("<i", M.rd(m, a, 4))[0]
    st = {"round": i32(ROUND), "cp": i32(CP), "mask": M.rd(m, MASK, 1)[0], "ac4": i32(AC4)}
    for f in range(8):
        i = f * STRIDE
        st[f] = {o: i32(o + i) for o in (ACC, CARRY, C30, MULT, FIELD, SLOT, ERA2)}
    return st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boundaries", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--tag", default="m99p1")
    ap.add_argument("--predict", action="store_true", help="print live inputs, no game touch")
    ap.add_argument("--poke-carry", type=int, default=0,
                    help="poke [fac*8380+0x94d808] to THIS before every boundary: the percent-100 "
                         "carry that decides whether param_2 gets its +1")
    ap.add_argument("--no-poke", action="store_true")
    a = ap.parse_args()

    pid = M.find_pid()
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        st = read_state(m)
    rnd = st["round"]
    human = (st["mask"] & -st["mask"]).bit_length() - 1
    print(f"pid {pid} round {rnd} cp {st['cp']} mask {st['mask']:#x} human fac{human} "
          f"ac4 {st['ac4']:#x}", flush=True)
    for f in range(8):
        s = st[f]
        print(f"  fac {f}: mult {s[MULT]} acc {s[ACC]} carry {s[CARRY]} c30 {s[C30]} "
              f"field {s[FIELD]} slot {s[SLOT]} era2 {s[ERA2]}", flush=True)
    print("  poke fac%d [0x94d808] carry -> %d (natural pre-run carry %d)"
          % (POKE_FAC, a.poke_carry, st[POKE_FAC][CARRY]) if not a.no_poke else "  no poke",
          flush=True)
    if a.predict:
        return

    gpath = os.path.join(SCRATCH, f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.gdblog")
    os.makedirs(SCRATCH, exist_ok=True)
    os.makedirs(EVID, exist_ok=True)
    open(gpath, "w").write(gdb_script())
    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath,
                          "-p", str(pid)], stdout=log, stderr=subprocess.STDOUT)
    time.sleep(3.0)
    head = open(lpath, "r", errors="replace").read()
    n_hw = head.count("Hardware watchpoint")
    if "ARMED" not in head or n_hw < len(WFACS):
        try:
            os.kill(g.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
        subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
        raise SystemExit(f"gdb did not arm {len(WFACS)} HARDWARE watchpoints (saw {n_hw}):\n"
                         + head[-1200:])
    print(f"armed: {n_hw} hw watchpoints on facs {WFACS} acc + 11 silent bps", flush=True)

    t0 = time.time()
    rc_ok = True

    def poke(addr, value):
        with open(f"/proc/{pid}/mem", "rb+", 0) as mm:
            mm.seek(addr)
            mm.write(struct.pack("<i", value))
            mm.seek(addr)
            return struct.unpack("<i", mm.read(4))[0]

    for k in range(a.boundaries):
        if not a.no_poke:
            got = poke(CARRY + POKE_FAC * STRIDE, a.poke_carry)
            print(f"  boundary {k}: POKE fac{POKE_FAC} carry {a.poke_carry} read back {got}",
                  flush=True)
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "smac_play.py"),
                            "--turns", "1", "--timeout", str(a.timeout), "--no-escape",
                            "3000", "--orders-per-turn", "1", "--verbose",
                            "--tag", f"{a.tag}_r{k}"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            rc_ok = False
        print(f"  boundary {k}: rc={r.returncode} t={time.time()-t0:.0f}s "
              f"{r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ''}", flush=True)

    # SETTLE: the turn driver returns while the AI upkeep is still playing (m98budget3).
    waited = 0
    while waited < 60:
        with open(f"/proc/{pid}/mem", "rb", 0) as mm:
            cp = struct.unpack("<i", M.rd(mm, CP, 4))[0]
        if cp == human:
            break
        time.sleep(2)
        waited += 2
    print(f"  settle: cp back to the human fac{human} after {waited}s", flush=True)
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
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        st2 = read_state(m)
    r_after = st2["round"]
    print(f"  after: round {r_after} tracer {tracer}", flush=True)

    text = open(lpath, "r", errors="replace").read()
    ev, unparsed = parse(text)
    with open(os.path.join(SCRATCH, f"{a.tag}_seq.jsonl"), "w") as fh:
        for d in ev:
            fh.write(json.dumps(d) + "\n")
        for ln in unparsed:
            fh.write(json.dumps({"tag": "?", "raw": ln}) + "\n")
    by = {}
    for d in ev:
        by.setdefault(d["tag"], []).append(d)
    c1, a1, a2, s1, r1 = (by.get(t, []) for t in ("C1", "A1", "A2", "S1", "R1"))
    p1, p2, p3, p4, p5, p6 = (by.get(t, []) for t in ("P1", "P2", "P3", "P4", "P5", "P6"))
    wp = by.get("WP", [])
    evc = " ".join("%s=%d" % (t, len(by.get(t, [])))
                  for t in ("P1", "P2", "P3", "P4", "P5", "P6", "C1", "A1", "A2", "S1", "R1", "WP"))
    print("--- events: %s ---" % evc, flush=True)
    for d in (p3[:3] + p6[:3] + c1[:3] + a1[:2]):
        print("  ", json.dumps(d), flush=True)

    funcs = load_funcs()
    pcs = sorted({d["pc"] for d in ev if "pc" in d})
    for pc in pcs:
        print(f"  pc 0x{pc:x} in {contain(pc, funcs) or 'UNMAPPED'}", flush=True)

    # G6: for EVERY call, predict param_2 from the values printed at the hits.
    g6rows, g7rows = [], []
    chain = {f: st[f][CARRY] for f in range(8)}
    # the harness pokes the carry BETWEEN the pre-run read and the hit, so the first hit of
    # each round for the poked faction must read the POKED value (m99p2: seed 60 vs carryo 0)
    poked_seen = set()
    for i, h in enumerate(p3):
        nxt = p4[i] if i < len(p4) else None
        q5 = p5[i] if i < len(p5) else None
        q6 = p6[i] if i < len(p6) else None
        if nxt is None or q5 is None or q6 is None:
            continue
        if not (nxt["fac"] == q5["fac"] == q6["fac"] == h["fac"]):
            continue
        seed = chain.get(h["fac"])
        if ((not a.no_poke) and h["fac"] == POKE_FAC
                and (h["fac"], h["round"]) not in poked_seen):
            seed = a.poke_carry
            poked_seen.add((h["fac"], h["round"]))
        scaled, carry_new, p2w = scale(h["raw2"], h["mult"], h["carryo"])
        _s, _c, p2_nat = scale(h["raw2"], h["mult"], st[h["fac"]][CARRY])
        g6rows.append((h["fac"], h["round"], p2w, q6["p2"], p2w == q6["p2"], h["raw2"],
                       h["mult"], h["carryo"], p2_nat))
        g7rows.append((h["fac"], scaled, q5["scaled"], carry_new, q5["carryn"],
                       wrap(h["c30o"] + h["raw2"]) == wrap(nxt["c30n"]),
                       seed == h["carryo"], h["carryo"]))
        chain[h["fac"]] = q5["carryn"]
    for fac, rnd2, want, got, ok, raw2, mult, carryo, pnat in g6rows:
        print(f"  PREDICT fac {fac} r{rnd2} raw {raw2} mult {mult} carry {carryo}: model p2 "
              f"{want} pushed {got} {'OK' if ok else 'MISMATCH'} (pre-run-carry model "
              f"{pnat})", flush=True)
    # C1 must agree with P6 for the same call
    c1_ok = sum(1 for h, k in zip(p6, c1) if h["fac"] == k["fac"] and h["p2"] == k["p2"])
    # G8: the accumulator law on every A1/A2 pair
    g8rows = []
    for h, k in zip(a1, a2):
        if h["fac"] != k["fac"]:
            continue
        g8rows.append((h["fac"], h["acco"], h["ebx"], k["accn"],
                       wrap(h["acco"] + h["ebx"]) == wrap(k["accn"])))
    # pair each call's param_2 (C1) with its ebx (A1) PER FACTION, in order
    dbl, modes = {}, []
    per_f = {}
    for k in c1:
        # FUN_005aadf0 returns at 0x5aaffc when param_2 <= 0: no acc store, so that call has
        # a C1 but no A1 - pairing must skip it or every later pair shifts by one (m99p2 G8)
        if k["p2"] > 0:
            per_f.setdefault(k["fac"], []).append(k)
    for f, lst in per_f.items():
        alist = [h for h in a1 if h["fac"] == f]
        for h, k in zip(alist, lst):
            mode = 2 if h["ebx"] == 2 * k["p2"] else (1 if h["ebx"] == k["p2"] else 0)
            dbl[f] = dbl.get(f, 0) + (1 if mode == 2 else 0)
            modes.append((f, k["p2"], h["ebx"], mode))
    for fac, acco, ebx, accn, ok in g8rows[:6]:
        print(f"  ACC fac {fac}: old {acco} + ebx {ebx} -> {accn} {'OK' if ok else 'MISMATCH'}",
              flush=True)
    # G9: read-back — replay the acc writes per watched faction
    lastw = {}
    for d in ev:
        if d["tag"] == "A2":
            lastw[d["fac"]] = d["accn"]
        elif d["tag"] == "S1":
            lastw[d["fac"]] = d["acc2"]
        elif d["tag"] == "R1":
            lastw[d["fac"]] = 0
        elif d["tag"] == "WP":
            lastw[d["fac"]] = d["new"]
    rb = [(f, lastw.get(f), st2[f][ACC], lastw.get(f) == st2[f][ACC]) for f in WFACS]
    for f, want, got, ok in rb:
        print(f"  READ-BACK fac {f}: replay {want} /proc {got} {'OK' if ok else 'MISMATCH'}",
              flush=True)
    # G13: the controlled poke — a hit where the multiplier IS the poked value and the
    # scaled answer differs from the naive "param_2 == raw" answer.
    g13 = []
    if not a.no_poke:
        for fac, rnd2, want, got, ok, raw2, mult, carryo, pnat in g6rows:
            if fac == POKE_FAC and ok and carryo == a.poke_carry and want != pnat:
                g13.append((fac, rnd2, raw2, mult, carryo, want, got, pnat))
    for fac, rnd2, raw2, mult, carryo, want, got, pnat in g13[:4]:
        print(f"  POKE fac{fac} r{rnd2}: carry poked to {carryo}, raw {raw2} mult {mult} -> "
              f"model p2 {want} pushed {got}; the pre-run carry {st[POKE_FAC][CARRY]} would "
              f"have given {pnat}", flush=True)

    g1 = n_hw >= len(WFACS) and len(pcs) >= 8
    g2 = rc_ok and r_after == rnd + a.boundaries
    g3 = (len(c1) >= 4 and len({d["round"] for d in c1}) >= 2
          and sum(1 for d in c1 if d["p2"] != 0) >= 2)
    g4 = bool(pcs) and all(contain(p, funcs) for p in pcs)
    g5 = bool(c1) and all(d["ret"] == CALLSITE_RET for d in c1)
    g6 = bool(g6rows) and all(r[4] for r in g6rows) and c1_ok == len(g6rows)
    g7 = bool(g7rows) and all(r[1] == r[2] and r[3] == r[4] and r[5] and r[6] for r in g7rows)
    g8 = (bool(g8rows) and all(r[4] for r in g8rows) and len(g8rows) >= 4
          and bool(modes) and all(m[3] in (1, 2) for m in modes))
    g9 = all(r[3] for r in rb) and all(f in lastw for f in WFACS)
    g10 = bool(wp) and all(d["pc"] in WP_EXPECT for d in wp)
    g11 = tracer == "0"
    g12 = not unparsed
    g13g = (bool(g13) if not a.no_poke else True)
    gates = [("G1_armed", g1), ("G2_boundary", g2), ("G3_calls", g3), ("G4_mapped", g4),
             ("G5_sole_caller", g5), ("G6_model_p2", g6), ("G7_carry_and_c30", g7),
             ("G8_acc_law", g8), ("G9_readback", g9), ("G10_only_static_writers", g10),
             ("G11_clean", g11), ("G12_parsed", g12), ("G13_poke_discriminates", g13g)]
    for n, v in gates:
        print(f"  {n}: {v}", flush=True)
    ok = all(v for _n, v in gates)
    print(f"ACCEPTANCE {a.tag}: {'PASS' if ok else 'FAIL'} ({sum(1 for _n, v in gates if v)}"
          f"/{len(gates)}) calls={len(c1)} model_ok={sum(1 for r in g6rows if r[4])}"
          f"/{len(g6rows)} carry_ok={sum(1 for r in g7rows if r[1] == r[2] and r[3] == r[4] and r[5] and r[6])}"
          f"/{len(g7rows)} acc_ok={sum(1 for r in g8rows if r[4])}/{len(g8rows)} "
          f"dbl_by_fac={dbl} poke_hits={len(g13)} wp={len(wp)} rounds {rnd}->{r_after} "
          f"pcs={[hex(p) for p in pcs]} unparsed={len(unparsed)}", flush=True)


if __name__ == "__main__":
    main()
