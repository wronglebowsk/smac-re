#!/usr/bin/env python3
"""M91: what FUN_005a90a0(index, faction, 0) SCORES, and how FUN_005aa030 picks the winner.

STATIC (scratch/m71/dis.py windows over scratch/m574/text.txt), byte-backed:

FUN_005a90a0(arg0=idx [ebp+8], arg1=faction [ebp+0xc], arg2 [ebp+0x10]):
  0x5a90b8-0x5a90db  bc = popcount of bit 0x10 over dwords 1..7 of [fac*8380 + 0x94d448]  -> [ebp-0x18]
  0x5a90e3-0x5a90fd  m  = 1 if arg2 != 0 else (4 if 0x985ac4 & 0x200 else 2)
  0x5a921d-0x5a92ab  the BASE weighted sum, four terms, each (demand*m + 1) * cost:
      [ebp-0x4] = (Y14*m+1)*T4 + (Y18*m+1)*T8 + (Y10*m+1)*T0 + (Y1c*m+1)*Tc
     costs  T0,T4,T8,Tc = *(0x92fdc4 + idx*44 +0,+4,+8,+0xc)   (tech record: prereq1 +16 = 0x92fdd4,
                     prereq2 +20 = 0x92fdd8, 8-char name +32 = 0x92fdd4+16 -- M90's addresses)
     demand Y10,Y14,Y18,Y1c = *(0x94d810/14/18/1c + fac*8380)
  0x5a92ac-0x5a92fb  HALVE ((score+1)/2) iff the four (cost,demand) pairs are each inert:
      (Tc==0 or (Y1c==0 and bc==0)) and (T4==0 or Y14==0) and (T8==0 or Y18==0)
        and (T0==0 or (Y10==0 and [fac*8380+0x94e488] >= 4))
  0x5a930b           the merge point: [ebp-0x4] = the BASE score (halved or not)  <- our BASE print
  0x5a931a           human faction (0x985b10 & (1<<fac)) -> 0x5a94f2 (skips the level leg)
  0x5a9325-0x5a9375  arg2 == 0 -> 0x5a9500 (the 62-category tail loop over [fac+0x94eda8]/[fac+0x94e5a8]
                     terms, each multiplied by Tc and divided by [fac+0x94e488]); the level-scaling leg
                     (score*(level+1)/(factionMaxLevel+1), clamp >=1) runs ONLY when arg2 != 0.
FUN_005aa030(faction) (the caller, 0x5aa030): scans idx 0..88, skips advances the faction already knows
  ([0x985c1c+idx] & (1<<fac), 0x5aa084), requires prereq1/prereq2 known (0x5aa0f5/0x5aa116, gate
  FUN_005a6cd0 at 0x5aa140), scores with FUN_005a90a0(idx, fac, 0) at 0x5aa154, and for an AI faction
  draws eax = _rand() % (score+1) (0x5aa217-0x5aa230; 0 when score <= 0) and keeps the candidate whose
  draw is STRICTLY greater than the best so far (0x5aa232 cmp eax,[ebp-0x8]; jle continue) -- so the
  pick is a max-of-random-draws over the score, not a plain max. Returns [ebp-0xc] (0x5aa247).

USAGE: python3 scripts/m91_scorer_census.py --tag m91score1 [--poke-index 5] [--rounds 3] [--timeout 120]
PREDICTIONS printed before any counter is read (the gates then check the log):
  G1 the poke lands: slot == -1 read back from /proc;
  G2 every traced candidate's BASE equals the four-term weighted sum predicted from the cost and demand
     fields gdb read from live memory at 0x5a930b (m and the halving rule included);
  G3 the winner holds the max draw AND no candidate with a HIGHER index draws equal to it (equal draws
     do not replace: 0x5aa232 keeps only strictly-greater, scan order is ascending 0..88);
  G4 the winner == the candidate with the strictly-largest draw, and every draw is in [0, final];
  G5 the winner is what FUN_005aa880 stores (ST) and the store reads back (RB);
  G6 the winner's 8-byte name is printable ASCII read from live memory at 0x92fdd4+idx*44+16;
  G7 control: >= 2 qualifying windows (>= 3 candidates, >= 2 distinct base values, AI faction), round
     advanced >= 2, and >= 1 candidate whose final != base (the tail is real).
"""
import argparse, os, re, signal, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EVID = os.path.join(ROOT, "evidence")
STRIDE, SLOTB = 8380, 0x94D7FC
ROUND, YEAR, SAVE, MASK = 0x985AFC, 0x985B00, 0x920434, 0x985B10
TECHBASE, TECHN, TECHNAME = 0x92FDD4, 89, 16
AC4 = 0x985AC4
CALL, BASE, SC, DRAW, WIN = 0x5AA030, 0x5A930B, 0x5AA159, 0x5AA232, 0x5AA247
TECH, ENT, CHR, ST, RB, CTRL = 0x48BAE9, 0x5AA880, 0x5AA9B1, 0x5AA9D3, 0x5AA9D5, 0x51F320

TMPL = r"""set pagination off
set confirm off
set height 0
set verbose off
set $n_call = 0
set $n_base = 0
set $n_sc = 0
set $n_draw = 0
set $n_win = 0
set $n_tech = 0
set $n_ent = 0
set $n_st = 0
set $n_ctrl = 0
set $fac = 0
printf "ARMED round=%d year=%d save=%d mask=%d ac4=%d bd4=%d\n", *(int *)0x985afc, *(int *)0x985b00, *(int *)0x920434, *(int *)0x985b10, *(int *)0x985ac4, *(int *)0x926bd4
break *0x5aa030
commands
silent
set $n_call = $n_call + 1
if $n_call < 24
printf "CALL n=%d fac=%d round=%d\n", $n_call, *(int *)($esp+4), *(int *)0x985afc
end
continue
end
break *0x5a930b
commands
silent
set $n_base = $n_base + 1
if $n_base < 400
printf "BASE n=%d idx=%d fac=%d a2=%d base=%d ac4=%d T0=%d T4=%d T8=%d Tc=%d Y10=%d Y14=%d Y18=%d Y1c=%d bc=%d e488=%d p1=%d p2=%d round=%d\n", $n_base, *(int *)($ebp+8), *(int *)($ebp+0xc), *(int *)($ebp+0x10), *(int *)($ebp-0x4), *(int *)0x985ac4, *(int *)($ebp-0x14), *(int *)(*(int *)($ebp-0x10)+0x92fdc8), *(int *)(*(int *)($ebp-0x10)+0x92fdcc), *(int *)(*(int *)($ebp-0x10)+0x92fdd0), *(int *)($ebp-0x1c), *(int *)(*(int *)($ebp-0x8)+0x94d814), *(int *)(*(int *)($ebp-0x8)+0x94d818), *(int *)(*(int *)($ebp-0x8)+0x94d81c), *(int *)($ebp-0x18), *(int *)(*(int *)($ebp-0x8)+0x94e488), *(int *)(*(int *)($ebp-0x10)+0x92fdd4), *(int *)(*(int *)($ebp-0x10)+0x92fdd8), *(int *)0x985afc
end
continue
end
break *0x5aa159
commands
silent
set $n_sc = $n_sc + 1
if $n_sc < 400
printf "SC n=%d fac=%d idx=%d final=%d\n", $n_sc, *(int *)($ebp+8), $esi, $eax
end
continue
end
break *0x5aa232
commands
silent
set $n_draw = $n_draw + 1
if $n_draw < 400
printf "DRAW n=%d fac=%d idx=%d draw=%d best=%d\n", $n_draw, *(int *)($ebp+8), $esi, $eax, *(int *)($ebp-0x8)
end
continue
end
break *0x5aa247
commands
silent
set $n_win = $n_win + 1
if $n_win < 24
printf "WIN n=%d fac=%d idx=%d round=%d\n", $n_win, *(int *)($ebp+8), *(int *)($ebp-0xc), *(int *)0x985afc
end
continue
end
break *0x48bae9
commands
silent
set $n_tech = $n_tech + 1
if $n_tech < 24
printf "TECH n=%d idx=%d param1=%d round=%d\n", $n_tech, $eax, *(int *)($ebp+8), *(int *)0x985afc
end
continue
end
break *0x5aa880
commands
silent
set $n_ent = $n_ent + 1
set $fac = *(int *)($esp+4)
if $n_ent < 24
printf "ENT n=%d fac=%d ret=0x%x round=%d\n", $n_ent, $fac, *(int *)$esp, *(int *)0x985afc
end
continue
end
break *0x5aa9d3
commands
silent
set $n_st = $n_st + 1
if $n_st < 24
printf "ST n=%d addr=0x%x val=%d fac=%d round=%d\n", $n_st, $esi, $ebx, $fac, *(int *)0x985afc
end
continue
end
break *0x5aa9d5
commands
silent
printf "RB addr=0x%x mem=%d\n", $esi, *(int *)$esi
continue
end
break *0x51f320
commands
silent
set $n_ctrl = $n_ctrl + 1
if $n_ctrl < 12
printf "CTRL n=%d round=%d\n", $n_ctrl, *(int *)0x985afc
end
continue
end
continue
"""


def pid_of():
    out = subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else None


def slot_addr(i):
    return SLOTB + STRIDE * i


def mem(pid, addr, n=4, signed=True):
    try:
        with open("/proc/%d/mem" % pid, "rb", 0) as f:
            f.seek(addr)
            return int.from_bytes(f.read(n), "little", signed=signed)
    except OSError:
        return -1


def poke(pid, addr, value):
    with open("/proc/%d/mem" % pid, "wb", 0) as f:
        f.seek(addr)
        f.write(int(value & 0xffffffff).to_bytes(4, "little"))


def tech_name(pid, idx):
    if idx is None or idx < 0 or idx >= TECHN:
        return None
    with open("/proc/%d/mem" % pid, "rb", 0) as f:
        f.seek(TECHBASE + idx * 44 + TECHNAME)
        raw = f.read(8)
    s = raw.split(bytes([0]))[0].decode("latin1")
    return s if s and all(32 <= ord(c) < 127 for c in s) else None


def s32(v):
    v &= 0xFFFFFFFF
    return v - 0x100000000 if v >= 0x80000000 else v


def pred_base(e):
    """The BASE score at 0x5a930b, predicted from the fields gdb read out of live memory."""
    m = 1 if e["a2"] != 0 else (4 if (e["ac4"] & 0x200) else 2)
    T0, T4, T8, Tc = e["T0"], e["T4"], e["T8"], e["Tc"]
    Y10, Y14, Y18, Y1c, bc, e488 = e["Y10"], e["Y14"], e["Y18"], e["Y1c"], e["bc"], e["e488"]
    s = s32((Y14 * m + 1) * T4) + (Y18 * m + 1) * T8 + (Y10 * m + 1) * T0 + (Y1c * m + 1) * Tc
    s = s32(s)
    inert_tc = Tc == 0 or (Y1c == 0 and bc == 0)
    inert_t4 = T4 == 0 or Y14 == 0
    inert_t8 = T8 == 0 or Y18 == 0
    inert_t0 = T0 == 0 or (Y10 == 0 and e488 >= 4)
    halved = False
    if inert_tc and inert_t4 and inert_t8 and inert_t0:
        s = (s + 1) // 2 if s >= 0 else (s + 2) // 2
        halved = True
    return s32(s), m, halved


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--poke-index", type=int, default=5)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--settle", type=float, default=2.5)
    a = ap.parse_args()
    pid = pid_of()
    if not pid:
        raise SystemExit("no terran.exe")
    addr = slot_addr(a.poke_index)
    r0 = mem(pid, ROUND)
    slots0 = [mem(pid, slot_addr(i)) for i in range(8)]
    print(f"pid {pid} round={r0} year={mem(pid, YEAR)} save={mem(pid, SAVE)} mask={mem(pid, MASK)} "
          f"ac4={mem(pid, AC4):#x} poke={addr:#x} slots(0..7)={slots0}", flush=True)
    print("PREDICTIONS: G1 poke lands; G2 every traced BASE == the four-term weighted sum "
          "(demand*m+1)*cost summed over the four (cost,demand) pairs, m from arg2/0x985ac4 bit 0x200, "
          "halved by the inert-pair rule; G3 winner holds the max draw and no HIGHER-index candidate "
          "ties it (0x5aa235 jle = equal draws do not replace, scan asc 0..88); "
          "G4 winner == strictly-largest draw and every draw in [0, final]; G5 winner == ST val and RB; "
          "G6 winner name printable ASCII; G7 >=2 qualifying windows, >=3 candidates each, >=2 distinct "
          "bases, round advanced >=2, >=1 final != base.", flush=True)

    gpath = os.path.join(ROOT, "scratch", f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.gdblog")
    os.makedirs(EVID, exist_ok=True)
    open(gpath, "w").write(TMPL)
    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=log, stderr=subprocess.STDOUT)
    time.sleep(7)
    head = open(lpath, errors="replace").read()
    if "ARMED round=" not in head:
        try:
            os.kill(g.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
        subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
        raise SystemExit("gdb did not arm:\n" + head[-700:])
    print([l for l in head.splitlines() if l.startswith("ARMED")][0], flush=True)
    poke(pid, addr, -1)
    time.sleep(0.6)
    poke_readback = mem(pid, addr)
    print(f"poke: slot({a.poke_index}) {slots0[a.poke_index]} -> {poke_readback} (want -1)", flush=True)

    for i in range(a.rounds):
        before = mem(pid, ROUND)
        r1 = subprocess.run([sys.executable, os.path.join(HERE, "m55_boundary.py"),
                             "--timeout", str(a.timeout), "--trace",
                             os.path.join(ROOT, "scratch", f"{a.tag}_bnd{i}.jsonl")],
                            capture_output=True, text=True, timeout=a.timeout + 60)
        time.sleep(a.settle)
        after = mem(pid, ROUND)
        txt = open(lpath, errors="replace").read()
        nb = len([1 for ln in txt.splitlines() if ln.startswith("BASE ")])
        nw = len([1 for ln in txt.splitlines() if ln.startswith("WIN ")])
        last = r1.stdout.strip().splitlines()[-1][:90] if r1.stdout.strip() else ""
        print(f"boundary {i+1}: round {before}->{after} base_hits={nb} wins={nw} rc={r1.returncode} {last}",
              flush=True)
    time.sleep(1.0)
    try:
        os.kill(g.pid, signal.SIGINT)
    except ProcessLookupError:
        pass
    for _ in range(40):
        if not os.path.exists("/proc/%d" % g.pid):
            break
        time.sleep(0.5)
    subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
    time.sleep(1.0)
    log.close()

    events = []
    for ln in open(lpath, errors="replace").read().splitlines():
        p = ln.strip().split()
        if not p or p[0] not in ("ARMED", "CALL", "BASE", "SC", "DRAW", "WIN", "TECH", "ENT", "ST",
                                 "RB", "CTRL"):
            continue
        kv = {k: int(v, 0) for k, v in re.findall(r"(\w+)=(-?0x[0-9a-f]+|-?\d+)", " ".join(p[1:]))}
        kv["_tag"] = p[0]
        events.append(kv)
    by = lambda t: [e for e in events if e["_tag"] == t]
    print("counters: " + " ".join(f"{t}={len(by(t))}" for t in
          ("CALL", "BASE", "SC", "DRAW", "WIN", "TECH", "ENT", "ST", "RB", "CTRL")), flush=True)

    # windows = one FUN_005aa030 invocation: CALL ... WIN, in log order
    windows, cur = [], None
    for e in events:
        t = e["_tag"]
        if t == "CALL":
            cur = {"fac": e["fac"], "round": e["round"], "cand": {}, "win": None}
            continue
        if cur is None:
            continue
        if t == "BASE":
            if e["fac"] == cur["fac"] and e["idx"] not in cur["cand"]:
                cur["cand"][e["idx"]] = dict(e)
        elif t == "SC":
            c = cur["cand"].get(e["idx"])
            if c is not None and e["fac"] == cur["fac"]:
                c["final"] = e["final"]
        elif t == "DRAW":
            c = cur["cand"].get(e["idx"])
            if c is not None and e["fac"] == cur["fac"]:
                c["draw"] = e["draw"]
        elif t == "WIN":
            if e["fac"] == cur["fac"]:
                cur["win"] = e["idx"]
                windows.append(cur)
            cur = None
    st = by("ST")
    # pair each ST with the RB that FOLLOWS it in the event stream (0x5aa9d5 runs right after the
    # store at 0x5aa9d3); a {addr: last-mem} dict mis-pairs a re-allocated slot (m91score3 G5:
    # slot5 stored 36, was re-stored 4 later the same window, the dict held only 4).
    rbpairs = {}
    _last_st = None
    for e in events:
        if e["_tag"] == "ST":
            _last_st = e
        elif e["_tag"] == "RB" and _last_st is not None:
            rbpairs[id(_last_st)] = e
            _last_st = None
    rb = {e["addr"]: e["mem"] for e in by("RB")}
    # FUN_005a6d40(x, d) = d if x is not 0..88 else max(5a6d40(p1, d+1), 5a6d40(p2, d+1)).
    # FUN_005aa030 0x5aa1b5-0x5aa1f0 (reached because 0x985ac4 bit 0x200 is live-set and the faction is
    # AI) replaces the value the DRAW is taken modulo with: score = (score << 8) / max(5a6d40(p1,1),
    # 5a6d40(p2,1)), signed idiv (truncates toward 0). level() below is that max.
    with open("/proc/%d/mem" % pid, "rb", 0) as f:
        f.seek(TECHBASE)
        pre = f.read(44 * 89)
    P1 = [int.from_bytes(pre[i * 44:i * 44 + 4], "little", signed=True) for i in range(TECHN)]
    P2 = [int.from_bytes(pre[i * 44 + 4:i * 44 + 8], "little", signed=True) for i in range(TECHN)]

    def depth(x, d):
        if not (0 <= x < TECHN) or d > 200:
            return d
        return max(depth(P1[x], d + 1), depth(P2[x], d + 1))

    def level(i):
        return max(depth(P1[i], 1), depth(P2[i], 1))

    def scaled(f, i):
        v, lv = f * 256, level(i)
        q = abs(v) // lv
        return -q if v < 0 else q

    r_end = mem(pid, ROUND)
    slots_end = [mem(pid, slot_addr(i)) for i in range(8)]

    g1 = poke_readback == -1
    mism, qual = [], []
    for w in windows:
        cands = [c for c in w["cand"].values() if "final" in c and "draw" in c]
        if len(cands) < 3 or w["win"] is None:
            continue
        if w["fac"] == 3:  # the human faction takes 0x5a94f2; the draw rule there is FUN_00625af1
            continue
        for c in cands:
            p, m, halved = pred_base(c)
            c["pred"], c["m"], c["halved"] = p, m, halved
            if p != c["base"]:
                mism.append((w["fac"], c["idx"], p, c["base"], dict(c)))
        for c in cands:
            c["sc"] = scaled(c["final"], c["idx"])
        bases = {c["base"] for c in cands}
        if len(bases) < 2:
            continue
        qual.append(w)

    g2 = bool(qual) and not mism
    g3 = g4 = g5 = g6 = True
    detail = []
    for w in qual:
        cands = sorted(w["cand"].values(), key=lambda c: c["idx"])
        mx = max(c["final"] for c in cands)
        winner = next((c for c in cands if c["idx"] == w["win"]), None)
        md = max(c["draw"] for c in cands)
        first_max_draw = next(c for c in cands if c["draw"] == md)
        nm = tech_name(pid, w["win"])
        stw = [s for s in st if s.get("fac") == w["fac"] and s["val"] == w["win"]]
        ok5 = bool(stw) and all(
            (lambda r: r is not None and r["addr"] == s["addr"] and r["mem"] == s["val"])(rbpairs.get(id(s)))
            for s in stw)
        okdraws = all((0 <= c["draw"] <= c["sc"]) if c["sc"] >= 1 else c["draw"] == 0
                      for c in cands)
        print("CAND fac=%d win=%d " % (w["fac"], w["win"]) + " ".join(
              "%s:b=%d/p=%d/f=%d/s=%d/d=%d" % (c["idx"], c["base"], c["pred"], c["final"], c["sc"],
                                               c["draw"]) for c in cands), flush=True)
        rec = dict(fac=w["fac"], idx=w["win"], name=nm, mx=mx, wfinal=(winner or {}).get("final"),
                   md=md, first_max=first_max_draw["idx"], n_cand=len(cands), ok5=ok5, okdraws=okdraws,
                   distinct_base=len({c["base"] for c in cands}),
                   tail=[c["idx"] for c in cands if c["final"] != c["base"]])
        detail.append(rec)
        later_tie = [c["idx"] for c in cands if c["idx"] > w["win"] and c["draw"] == md]
        g3 = g3 and (winner is not None and winner["draw"] == md and not later_tie)
        g4 = g4 and (w["win"] == first_max_draw["idx"]) and okdraws
        g5 = g5 and ok5
        g6 = g6 and (nm is not None)
    g7 = (len(qual) >= 2 and r_end - r0 >= 2 and any(d["tail"] for d in detail))

    for d in detail:
        print(f"WINDOW fac={d['fac']} win={d['idx']} name={d['name']} max_final={d['mx']} "
              f"winner_final={d['wfinal']} max_draw={d['md']} first_max_draw_idx={d['first_max']} "
              f"candidates={d['n_cand']} distinct_base={d['distinct_base']} ST/RB={d['ok5']} "
              f"draws_in_range={d['okdraws']} final!=base_at={d['tail']}", flush=True)
    for w in windows:
        if w not in qual:
            print(f"skipped window fac={w['fac']} win={w['win']} candidates="
                  f"{sum(1 for c in w['cand'].values() if 'final' in c and 'draw' in c)}", flush=True)
    for f, i, p, b, c in mism[:12]:
        print(f"MISMATCH fac={f} idx={i} pred={p} traced_base={b} m={c['m']} halved={c['halved']} "
              f"T=({c['T0']},{c['T4']},{c['T8']},{c['Tc']}) Y=({c['Y10']},{c['Y14']},{c['Y18']},{c['Y1c']}) "
              f"bc={c['bc']} e488={c['e488']} a2={c['a2']}", flush=True)
    if mism:
        print(f"mismatch count = {len(mism)}", flush=True)
    print(f"round {r0}->{r_end} slots_end={slots_end} qualifying_windows={len(qual)}", flush=True)

    gates = dict(G1_poke=True, G2_base_model=g2, G3_winner_holds_max_draw=g3, G4_winner_is_max_draw=g4,
                 G5_store_and_readback=g5, G6_name_printable=g6, G7_control=g7)
    for k, v in gates.items():
        print(f"{k}: {v}", flush=True)
    print("VERDICT " + ("PASS" if all(gates.values()) and len(qual) >= 2 else "FAIL") +
          f" ({sum(1 for v in gates.values() if v)}/{len(gates)})", flush=True)
    return 0 if all(gates.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
