#!/usr/bin/env python3
"""M96: the HUMAN leg of the tech chooser FUN_005aa030 — what multiplies the score before the draw,
and which random stream the draw comes from.

BYTE-BACKED SHAPE (scratch/m71/dis.py windows, ghidra_out/shard_009.c:9343-9388):
  FUN_005aa030(faction): edi=fac ([ebp+0x8]), esi=candidate 0..0x58, ebx=esi*44, best_draw [ebp-0x8]
  starts 0xfffffc19 (-999), best_idx [ebp-0xc] starts -1. Gate chain 0x5aa04d-0x5aa14a (prereq fields,
  the researched bytes [idx+0x985c1c] & (1<<fac), FUN_005a6cd0(prereq2,fac)) then 0x5aa154 call
  FUN_005a90a0(idx,fac,0) -> 0x5aa159 mov [ebp-0x4],eax (the SCORE).
  0x5aa15c mov eax,ds:0x985ac4 / 0x5aa164 test ah,0x2 / je 0x5aa1f3: when bit 0x200 is CLEAR the score
  is used unscaled. When SET: 0x5aa16d-0x5aa17e tests (1<<fac) & BYTE ds:0x985b10 (the human mask);
  a MASK-SET faction first reads [fac*8380+0x94d810] and [fac*8380+0x94d818] (0x5aa192/0x5aa19c) and if
  either is nonzero compares the candidate against WORD ds:0x98adee (0x5aa1a6) — equal returns the
  candidate verbatim at 0x5aa251 (a FORCED pick, no draw). Both paths converge at 0x5aa1b5:
  edi = max(FUN_005a6d40(prereq1,1), FUN_005a6d40(prereq2,1)) (the prereq-CHAIN DEPTH; FUN_005a6d40(a,b)
  returns b when a<0||a>=0x59, else the max of its two prereqs at depth+1), then 0x5aa1e4-0x5aa1f0
  [ebp-0x4] = ([ebp-0x4] << 8) / edi. THE MULTIPLY IS THE <<8 (x256), THE DIVISOR IS PREREQ DEPTH.
  0x5aa1f3-0x5aa204 tests the human mask AGAIN: mask-set -> 0x5aa20d call FUN_00625af1(0, score+1) =
  thiscall FUN_00625a0f(this = &ds:0x999fa0, lo=0, hi=score+1): state = state*0x19660d + 0x3c6ef35f
  (mod 2^32), value = (((state & 0xffff) * (hi-lo)) mod 2^32) >> 16 + lo — a SEPARATE LCG stream.
  mask-clear -> 0x5aa217-0x5aa230 draw = rand() % (score+1) (0x64c6f0), 0 when score <= 0.
  0x5aa232 cmp eax,[ebp-0x8]: the DRAW VALUE is the ranking key (strictly greater wins, ties keep the
  earlier candidate); 0x5aa247 mov eax,[ebp-0xc] then 0x5aa24a returns it (break AFTER the load).
  FUN_0048b9a0's chooser leg (shard_009.c:9359) is taken when param_2==0 && (round==0 || !(mask &
  (1<<param_1)) || bVar14) && param_3<0, and bVar14 = ((ds:0x985ac4 & 0x200) != 0 && param_3 <= 0)
  (shard_009.c:9343-9347) — bVar14 is what lets a HUMAN-masked faction take the leg at all.

SHAPE: poke the slots of the HUMAN faction (3, mask 0x08) and a NON-HUMAN faction (2) to -1, run
boundaries under print-only breakpoints, then predict from live memory: the per-candidate divisor, the
scaled score, the LCG draw (from the state read BEFORE the call), and the winning index.
Usage: python3 scripts/m96_human_leg.py --tag m96human1 [--rounds 3] [--timeout 100]
"""
import argparse, os, re, signal, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EVID = os.path.join(ROOT, "evidence")
STRIDE, SLOTB = 8380, 0x94D7FC
ROUND, YEAR, SAVE, MASK, EBC = 0x985AFC, 0x985B00, 0x920434, 0x985B10, 0x985AC4
TECHBASE, TECHN = 0x92FDD4, 89
RNG, FORCED = 0x999FA0, 0x98ADEE
MUL, ADD = 0x19660D, 0x3C6EF35F
CTRL = 0x51F320
A030, TECH = 0x5AA030, 0x48BAE9
SCORE, G164, M17E, SIB10, SIB18, S98, DIV, QUO, M204, HDRAW, RDRAW, DRAW, RETV, EARLY = (
    0x5AA159, 0x5AA164, 0x5AA17E, 0x5AA192, 0x5AA19C, 0x5AA1A6, 0x5AA1E4, 0x5AA1F0, 0x5AA204,
    0x5AA20D, 0x5AA217, 0x5AA232, 0x5AA24A, 0x5AA251)  # RETV at 0x5aa24a = AFTER the return-value load

TMPL = r"""set pagination off
set confirm off
set height 0
set verbose off
set $n_a = 0
set $n_sc = 0
set $n_g = 0
set $n_m = 0
set $n_s = 0
set $n_f = 0
set $n_d = 0
set $n_q = 0
set $n_m2 = 0
set $n_h = 0
set $n_r = 0
set $n_w = 0
set $n_ret = 0
set $n_e = 0
set $n_t = 0
set $n_c = 0
printf "ARMED round=%d year=%d save=%d mask=%d ebc=%d rng=%d forced=%d\n", *(int *)0x985afc, *(int *)0x985b00, *(int *)0x920434, *(int *)0x985b10, *(int *)0x985ac4, *(int *)0x999fa0, *(short *)0x98adee
break *0x5aa030
commands
silent
set $n_a = $n_a + 1
if $n_a < 40
printf "A030 n=%d fac=%d edi=%d ret=0x%x round=%d ebc=%d mask=%d rng=%d\n", $n_a, *(int *)($esp+4), $edi, *(int *)$esp, *(int *)0x985afc, *(int *)0x985ac4, *(int *)0x985b10, *(int *)0x999fa0
end
continue
end
break *0x5aa159
commands
silent
set $n_sc = $n_sc + 1
if $n_sc < 400
printf "SC n=%d fac=%d idx=%d score=%d round=%d\n", $n_sc, $edi, $esi, $eax, *(int *)0x985afc
end
continue
end
break *0x5aa164
commands
silent
set $n_g = $n_g + 1
if $n_g < 400
printf "G164 n=%d fac=%d idx=%d ebc=%d\n", $n_g, $edi, $esi, *(int *)0x985ac4
end
continue
end
break *0x5aa17e
commands
silent
set $n_m = $n_m + 1
if $n_m < 400
printf "M17E n=%d fac=%d idx=%d bit=%d mbyte=%d\n", $n_m, $edi, $esi, $eax, $ecx
end
continue
end
break *0x5aa192
commands
silent
set $n_s = $n_s + 1
if $n_s < 200
printf "SIB10 n=%d off=%d val=%d fac=%d idx=%d\n", $n_s, ($eax+0x94d810), *(int *)($eax+0x94d810), $edi, $esi
end
continue
end
break *0x5aa19c
commands
silent
set $n_s = $n_s + 1
if $n_s < 200
printf "SIB18 n=%d off=%d val=%d fac=%d idx=%d\n", $n_s, ($eax+0x94d818), *(int *)($eax+0x94d818), $edi, $esi
end
continue
end
break *0x5aa1a6
commands
silent
set $n_f = $n_f + 1
if $n_f < 200
printf "S98 n=%d idx=%d forced=%d fac=%d\n", $n_f, $esi, *(short *)0x98adee, $edi
end
continue
end
break *0x5aa1e4
commands
silent
set $n_d = $n_d + 1
if $n_d < 400
printf "DIV n=%d fac=%d idx=%d score=%d div=%d\n", $n_d, *(int *)($ebp+8), $esi, *(int *)($ebp-4), $edi
end
continue
end
break *0x5aa1f0
commands
silent
set $n_q = $n_q + 1
if $n_q < 400
printf "QUO n=%d fac=%d idx=%d q=%d\n", $n_q, *(int *)($ebp+8), $esi, $eax
end
continue
end
break *0x5aa204
commands
silent
set $n_m2 = $n_m2 + 1
if $n_m2 < 400
printf "M204 n=%d fac=%d idx=%d bit=%d mbyte=%d score=%d\n", $n_m2, $edi, $esi, $eax, $ecx, *(int *)($ebp-4)
end
continue
end
break *0x5aa20d
commands
silent
set $n_h = $n_h + 1
if $n_h < 200
printf "HDRAW n=%d fac=%d idx=%d hi=%d state=%d\n", $n_h, *(int *)($ebp+8), $esi, $edx, *(int *)0x999fa0
end
continue
end
break *0x5aa217
commands
silent
set $n_r = $n_r + 1
if $n_r < 400
printf "RDRAW n=%d fac=%d idx=%d score=%d modulus=%d\n", $n_r, *(int *)($ebp+8), $esi, *(int *)($ebp-4), $edi
end
continue
end
break *0x5aa232
commands
silent
set $n_w = $n_w + 1
if $n_w < 400
printf "DRAW n=%d fac=%d idx=%d draw=%d best=%d score=%d round=%d\n", $n_w, *(int *)($ebp+8), $esi, $eax, *(int *)($ebp-8), *(int *)($ebp-4), *(int *)0x985afc
end
continue
end
break *0x5aa24a
commands
silent
set $n_ret = $n_ret + 1
if $n_ret < 40
printf "RETV n=%d idx=%d best=%d fac=%d rng=%d round=%d\n", $n_ret, $eax, *(int *)($ebp-8), *(int *)($ebp+8), *(int *)0x999fa0, *(int *)0x985afc
end
continue
end
break *0x5aa251
commands
silent
set $n_e = $n_e + 1
if $n_e < 40
printf "EARLY n=%d idx=%d fac=%d\n", $n_e, $esi, *(int *)($ebp+8)
end
continue
end
break *0x48bae9
commands
silent
set $n_t = $n_t + 1
if $n_t < 40
printf "TECH n=%d idx=%d param1=%d ret=0x%x round=%d\n", $n_t, $eax, *(int *)($ebp+8), *(int *)$esp, *(int *)0x985afc
end
continue
end
break *0x51f320
commands
silent
set $n_c = $n_c + 1
if $n_c < 12
printf "CTRL n=%d round=%d\n", $n_c, *(int *)0x985afc
end
continue
end
continue
"""

TAGS = ("A030", "SC", "G164", "M17E", "SIB10", "SIB18", "S98", "DIV", "QUO", "M204",
        "HDRAW", "RDRAW", "DRAW", "RETV", "EARLY", "TECH", "CTRL")


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


def prereqs(pid):
    """(prereq1, prereq2) for all 89 tech entries, read from live memory."""
    out = []
    for i in range(TECHN):
        out.append((mem(pid, TECHBASE + i * 44), mem(pid, TECHBASE + i * 44 + 4)))
    return out


def depth(idx, d, pre):
    """FUN_005a6d40(a,b) exactly: b when a<0 || a>=89, else max over the two prereqs at d+1."""
    if idx < 0 or idx >= TECHN:
        return d
    a, b = pre[idx]
    return max(depth(a, d + 1, pre), depth(b, d + 1, pre))


def lcg_draw(state, lo, hi):
    """FUN_00625a0f(this, lo, hi): swap if lo>hi, ONE LCG step, ((state&0xffff)*(hi-lo))>>16 + lo."""
    if lo > hi:
        lo, hi = hi, lo
    state = (state * MUL + ADD) & 0xFFFFFFFF
    val = (((state & 0xFFFF) * (hi - lo)) & 0xFFFFFFFF) >> 16
    return val + lo, state, lo, hi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--human-index", type=int, default=3)
    ap.add_argument("--other-index", type=int, default=2)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=100)
    ap.add_argument("--settle", type=float, default=3.0)
    a = ap.parse_args()
    pid = pid_of()
    if not pid:
        raise SystemExit("no terran.exe")
    r0 = mem(pid, ROUND)
    mask0 = mem(pid, MASK) & 0xFF
    ebc0 = mem(pid, EBC)
    rng0 = mem(pid, RNG)
    pre = prereqs(pid)
    slots0 = [mem(pid, slot_addr(i)) for i in range(8)]
    sib = [(mem(pid, 0x94D810 + STRIDE * i), mem(pid, 0x94D818 + STRIDE * i)) for i in range(8)]
    forced = mem(pid, FORCED, 2, signed=True)
    hum, oth = a.human_index, a.other_index
    print(f"pid {pid} round={r0} mask={mask0:#x} ebc={ebc0:#x} (bit200={ (ebc0>>9)&1 }) rng0={rng0} "
          f"forced_short={forced} slots={slots0} siblings={sib}", flush=True)
    print(f"human fac {hum} maskbit={ (mask0>>hum)&1 } control fac {oth} maskbit={ (mask0>>oth)&1 }",
          flush=True)
    print("PREDICTIONS: P1 both pokes land (-1 read back); P2 DIV.div == max(depth(prereq1,1),"
          "depth(prereq2,1)) computed from the live prereq table; P3 QUO.q == (score<<8)/div; "
          "P4 every mask-set candidate hits 0x5aa20d and never 0x5aa217 (and the reverse for "
          "mask-clear); P5 HDRAW.draw == the LCG output predicted from the state read BEFORE the call "
          "and hi=score+1, with the state chain advancing one step per draw; P6 RETV.idx == the "
          "max-draw candidate of that call; P7 EARLY only when a sibling != 0 and idx == forced short; "
          "P8 the TECH landing equals the RETV index for that faction.", flush=True)

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
    for i in (hum, oth):
        poke(pid, slot_addr(i), -1)
    time.sleep(0.6)
    after_poke = [mem(pid, slot_addr(i)) for i in (hum, oth)]
    print(f"poke: slots({hum},{oth}) {[slots0[i] for i in (hum,oth)]} -> {after_poke}", flush=True)

    for i in range(a.rounds):
        before = mem(pid, ROUND)
        r1 = subprocess.run([sys.executable, os.path.join(HERE, "m55_boundary.py"),
                             "--timeout", str(a.timeout), "--trace",
                             os.path.join(ROOT, "scratch", f"{a.tag}_bnd{i}.jsonl")],
                            capture_output=True, text=True, timeout=a.timeout + 60)
        time.sleep(a.settle)
        cur = [mem(pid, slot_addr(j)) for j in range(8)]
        txt = open(lpath, errors="replace").read()
        nd = len([1 for ln in txt.splitlines() if ln.startswith("DRAW ")])
        last = r1.stdout.strip().splitlines()[-1][:90] if r1.stdout.strip() else ""
        print(f"boundary {i+1}: round {before}->{mem(pid, ROUND)} slots={cur} draws={nd} "
              f"rc={r1.returncode} {last}", flush=True)
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

    raw = open(lpath, errors="replace").read()
    events = []
    for ln in raw.splitlines():
        p = ln.strip().split()
        if not p or p[0] not in TAGS:
            continue
        kv = {k: int(v, 0) for k, v in re.findall(r"(\w+)=(-?0x[0-9a-f]+|-?\d+)", " ".join(p[1:]))}
        kv["_tag"] = p[0]
        events.append(kv)
    by = {}
    for e in events:
        by.setdefault(e["_tag"], []).append(e)
    pos = {id(e): i for i, e in enumerate(events)}   # dicts can be EQUAL, so index() lies: key by id
    r1v = mem(pid, ROUND)
    rng1 = mem(pid, RNG)
    slots1 = [mem(pid, slot_addr(i)) for i in range(8)]

    # ---- predictions, printed BEFORE any counter is read ----
    div_ok = div_tot = 0
    for d in by.get("DIV", []):
        idx, got = d.get("idx"), d.get("div")
        p1, p2 = pre[idx] if 0 <= idx < TECHN else (-1, -1)
        want = max(depth(p1, 1, pre), depth(p2, 1, pre))
        div_tot += 1
        div_ok += (want == got)
        if want != got:
            print(f"  DIV-MISMATCH fac={d.get('fac')} idx={idx} observed_div={got} predicted={want}",
                  flush=True)
    quo_ok = quo_tot = 0
    for q in by.get("QUO", []):
        quo_tot += 1
    # pair DIV->QUO by ORDER: 0x5aa1e4 and 0x5aa1f0 are hit 1:1 (no branch between them)
    divq = by.get("DIV", [])
    quov = by.get("QUO", [])
    quo_ok = 0
    quo_tot = min(len(divq), len(quov))
    for i in range(quo_tot):
        d, q = divq[i], quov[i]
        want = (d.get("score") << 8) // d.get("div") if d.get("div") else None
        # signed trunc toward zero
        if d.get("score") is not None and d.get("div"):
            num = d["score"] << 8
            want = -((-num) // d["div"]) if num < 0 else num // d["div"]
        if want == q.get("q") and d.get("idx") == q.get("idx") and d.get("fac") == q.get("fac"):
            quo_ok += 1
        else:
            print(f"  QUO-MISMATCH fac={d.get('fac')} idx={d.get('idx')} want={want} got={q.get('q')}",
                  flush=True)
    leg_ok = leg_tot = 0
    for m in by.get("M204", []):
        fac, bit = m.get("fac"), m.get("bit")
        human = (bit & ((m.get("mbyte") or 0) & 0xFF)) != 0   # ecx's UPPER byte is the fac, mask to 0xff
        ei = pos[id(m)]
        nxt = next((x for x in events[ei + 1:] if x["_tag"] in ("HDRAW", "RDRAW")), None)
        ok = bool(nxt) and ((nxt["_tag"] == "HDRAW") == human) and nxt.get("idx") == m.get("idx")
        leg_tot += 1
        leg_ok += ok
        if not ok:
            print(f"  LEG-MISMATCH fac={fac} idx={m.get('idx')} human={human} "
                  f"next={None if not nxt else (nxt['_tag'], nxt.get('idx'))}", flush=True)
    draw_ok = draw_tot = 0
    for h in by.get("HDRAW", []):
        want, newst, lo, hi = lcg_draw(h.get("state"), 0, h.get("hi"))
        ei = pos[id(h)]
        w = next((x for x in events[ei + 1:] if x["_tag"] == "DRAW" and x.get("idx") == h.get("idx")),
                 None)
        got = None if not w else w.get("draw")
        draw_tot += 1
        draw_ok += (want == got)
        if want != got:
            print(f"  DRAW-MISMATCH fac={h.get('fac')} idx={h.get('idx')} hi={hi} state={h.get('state')} "
                  f"want={want} got={got}", flush=True)
    # the winner: max draw per chooser call (ties keep the earlier), vs RETV
    win_ok = win_tot = 0
    calls = by.get("A030", [])
    for ci, call in enumerate(calls):
        lo_i = pos[id(call)]
        hi_i = len(events) if ci + 1 >= len(calls) else pos[id(calls[ci + 1])]
        ds = [e for e in events[lo_i:hi_i] if e["_tag"] == "DRAW" and e.get("fac") == call.get("fac")]
        rt = next((e for e in events[lo_i:hi_i] if e["_tag"] in ("RETV", "EARLY")
                   and e.get("fac") == call.get("fac")), None)
        if not ds or not rt:
            continue
        win_tot += 1
        bestv, bestidx = None, None
        for e in ds:
            if bestv is None or e.get("draw") > bestv:
                bestv, bestidx = e.get("draw"), e.get("idx")
        if rt.get("idx") == bestidx:
            win_ok += 1
        else:
            print(f"  WIN-MISMATCH fac={call.get('fac')} predicted={bestidx} (draw {bestv}) "
                  f"returned={rt.get('idx')} tag={rt['_tag']}", flush=True)
    early_bad = 0
    for e in by.get("EARLY", []):
        f = e.get("fac")
        if f is None or 0 > f or f >= 8:
            early_bad += 1
            continue
        s10, s18 = sib[f]
        if not (s10 or s18) or e.get("idx") != forced:
            early_bad += 1
            print(f"  EARLY-VIOLATION idx={e.get('idx')} fac={f} siblings={(s10, s18)} "
                  f"forced={forced}", flush=True)
    legfac = {}
    for tag, t in (("HDRAW", "human"), ("RDRAW", "rand")):
        for e in by.get(tag, []):
            legfac.setdefault(e.get("fac"), set()).add(t)
    tech = by.get("TECH", [])
    retv = by.get("RETV", [])
    pair_ok = 0
    for t in tech:
        r = next((x for x in reversed(retv) if x.get("fac") == t.get("param1")
                  and pos[id(x)] < pos[id(t)]), None)
        pair_ok += bool(r) and r.get("idx") == t.get("idx")

    human_legs = len(by.get("HDRAW", []))
    rand_legs = len(by.get("RDRAW", []))
    hum_calls = len([c for c in calls if c.get("fac") == hum])
    oth_calls = len([c for c in calls if c.get("fac") == oth])
    res = {
        "G1_round_moved": r1v > r0 and len(by.get("CTRL", [])) >= 1,
        "G2_pokes_landed": after_poke == [-1, -1],
        "G3_both_legs_seen": human_legs >= 1 and rand_legs >= 1,
        "G4_chooser_ran_for_human_and_control": hum_calls >= 1 and oth_calls >= 1,
        "G5_leg_matches_mask_every_candidate": leg_tot >= 1 and leg_ok == leg_tot,
        "G6_divisor_is_prereq_depth": div_tot >= 1 and div_ok == div_tot,
        "G7_scaled_score_is_score_times_256_over_div": quo_tot >= 1 and quo_ok == quo_tot,
        "G8_human_lcg_draw_predicted_exactly": human_legs >= 5 and draw_ok == draw_tot and draw_tot == human_legs,
        "G9_return_is_the_max_draw_candidate": win_tot >= 1 and win_ok == win_tot,
        "G10_early_return_consistent_with_siblings": early_bad == 0,
        "G11_landing_matches_return": tech and pair_ok == len(tech),
        "G12_detached": "detached]" in raw,
    }
    print("GATES:", flush=True)
    for k, v in res.items():
        print(f"  {'T' if v else 'F'} {k}", flush=True)
    ok = all(res.values())
    print("VERDICT %s tag=%s round %d->%d ebc %#x mask %#x forced=%d chooser_calls=%d(human %d ctrl %d) "
          "candidates_scored=%d scaled=%d/%d div=%d/%d human_draws=%d predicted_ok=%d rand_draws=%d "
          "leg=%d/%d wins=%d/%d early=%d rng %d->%d slots=%s"
          % ("PASS" if ok else "FAIL", a.tag, r0, r1v, ebc0, mask0, forced, len(calls), hum_calls,
             oth_calls, len(by.get("SC", [])), quo_ok, quo_tot, div_ok, div_tot, human_legs, draw_ok,
             rand_legs, leg_ok, leg_tot, win_ok, win_tot, len(by.get("EARLY", [])), rng0, rng1, slots1),
          flush=True)
    print("evidence:", lpath, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
