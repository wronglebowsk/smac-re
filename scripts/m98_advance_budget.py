#!/usr/bin/env python3
"""M98 — what is `[fac*8380+0x94d800]`? (the sibling of the 0x94d7fc work-item slot)

STATIC (whole-.text grep of scratch/m574/text.txt: FIVE sites touch 0x94d800, and only
these): reads 0x593483 (FUN_0058fa40, `aab70(fac)/2 <= [fac*8380+0x94d7f8]`) and 0x5aab8f
(inside FUN_005aab70 itself); writes 0x59f0c7 `= -1` (FUN_0059ec90), and 0x5aaf67 `= -1` +
0x5aaf79 `= eax` (FUN_005aadf0, which calls FUN_005aab70 at 0x5aaf71 between them).

FUN_005aadf0(fac, p) (per-base upkeep tail: 0x4f5c2e FUN_004f34b0 <- FUN_004f5a70):
  [0x94d7f8] += p (AI factions double it under 0x5aae04-0x5aae71);  if (netgame ||
  [0x94d7fc] >= 0) { b = FUN_005aab70(fac); if ([0x94d7fc] > 0x58) acc += p;
  if (b <= acc) { print "Researched Advance"; FUN_005aaa20(fac); FUN_0047f590(fac, item);
  [0x94d7f8] = 0; [0x94d800] = -1; [0x94d800] = FUN_005aab70(fac); } ... }
FUN_005aab70(fac) READS the field and returns it UNCHANGED when it is >= 0 (a memo); only
the < 0 leg recomputes it from era/human-mask/difficulty-percents/per-faction counts.
=> the field is the faction's ADVANCE THRESHOLD: the progress the sibling accumulator
[fac*8380+0x94d7f8] must reach before the next Researched/Secret Advance is granted.

This harness PREDICTS the threshold for all 8 factions from live /proc memory with a
faithful Python model of FUN_005aab70 (C truncating division, 32-bit wrap) BEFORE the run,
arms silent bps at the three stores + the accumulator reset + the FUN_005aab70 entry, one
HARDWARE watchpoint on one faction's field as the "any other writer" check, plays
N boundaries, then reads the fields back from /proc.

  python3 scripts/m98_advance_budget.py --predict                 # model vs live, no game
  python3 scripts/m98_advance_budget.py --tag m98budget1 --boundaries 2   # PASS/FAIL
"""
import argparse
import bisect
import csv
import importlib.util
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
ROUND_ADDR = 0x985AFC
CP_ADDR = 0x985DCC
STRIDE = 8380
BLK = 0x94d78c                      # per-faction block base (fac*8380 + 0x94d78c)
FIELD, ACC, SLOT = 0x94d800, 0x94d7f8, 0x94d7fc
D78C, D790, D804, D728, D438, D430 = 0x94d78c, 0x94d790, 0x94d804, 0x94d728, 0x94d438, 0x94d430
ERA, AFC, AC4, MASK = 0x985aec, 0x985afc, 0x985ac4, 0x985b10
G298, G390 = 0x92a298, 0x92a390
PCT_BASE, PCT_STRIDE = 0x927a88, 1436
# FUN_005aab70's max-loop: int* stride 0x82f (8380 B) from 0x94f848 while < 0x95dd6c
MAX_START, MAX_END, MAX_OFF = 0x94f848, 0x95dd6c, 0x78
RESET, INVAL, STORE, INVAL2, ENTRY = 0x5aaf5c, 0x5aaf67, 0x5aaf79, 0x59f0c7, 0x5aab70
FIELD_STORE_PCS = (INVAL, STORE, INVAL2)
FAC = int(os.environ.get("M98_FAC", "3"))

TMPL = r"""set pagination off
set confirm off
set can-use-hw-watchpoints 1
@@WATCHES@@@@BPS@@printf "ARMED @@N@@ hw watchpoints at @@ADDRS@@; @@NB@@ silent bps at @@BPS@@\n"
continue
"""

WBLOCK = r"""watch *(int *)@@A@@
commands
silent
printf "M98W WP pc=0x%x new=%d fac=@@F@@ acc=%d round=%d cp=%d\n", $pc, *(int *)@@A@@, *(int *)@@A@@-0x8, *(int *)0x985afc, *(int *)0x985dcc
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


def wrap(x):
    x &= 0xffffffff
    return x - 0x100000000 if x >= 0x80000000 else x


def tdiv(a, b):
    """C signed integer division: truncates toward zero."""
    if b == 0:
        raise ZeroDivisionError("idiv by 0 (L == 8 in FUN_005aab70)")
    q = abs(a) // abs(b)
    return -q if (a < 0) != (b < 0) else q


def aab70_model(f, G, per, max7):
    """FUN_005aab70's <0 recompute leg, faithful to the C (wrap + trunc division)."""
    if G["g298"] == 0:
        return 999999999
    L = wrap(wrap(per[D804] * 2 - per[D790]) + per[D78C])
    L = 2 if L < 2 else (9999 if L > 9999 else L)
    Mx = max(max7)
    v5 = tdiv(L, 2)
    human = (((1 << (f & 0x1f)) & G["mask"]) != 0)
    x = per[D438] if human else G["era"]
    if x < 3:
        x += 1
    mul = 3
    if not human:
        mul = G["era"]
        x = wrap(x * -3 + 0x1d)
    else:
        x = wrap(x * 4 + 8)
    v4 = wrap(v5 + 0xc)
    v2 = wrap(0xc - v5)
    if v2 <= x and v2 <= v4:
        v2 = x
        if v4 < x:
            v2 = v4
    u = (G["ac4"] & 0x20) | 0x40
    x2 = wrap((u >> 5) * v2) >> 1
    v4b = wrap(v5 - tdiv(G["afc"], (u >> 3)))
    if v4b < 0 or x2 < 0:
        x2 = 0
    elif v4b <= x2:
        x2 = v4b
    v4c = wrap(tdiv(wrap((v2 + x2) * mul), 10) + 1)
    # NOTE: Ghidra REASSIGNS local_8 to 3 (human) / era (AI) before these two lines, so
    # both the `*local_8/10+1` cap and the `(8 - local_8)` divisor use mul, NOT the clamped
    # L from the top of the function (s153: using L gave 68/101/151 for fac7/6/4 vs live 64/77/166).
    m2 = tdiv(wrap(wrap(wrap(Mx // 2) - mul) - v5) + 7, wrap(8 - mul))
    if m2 < 0 or v4c < 0:
        m2 = 0
    elif v4c < m2:
        m2 = v4c
    d728 = per[D728]
    sgn = 1 if d728 >= 1 else (0 if d728 == 0 else -1)
    v5b = wrap(v5 - sgn)
    v5b = 1 if v5b < 1 else (99999 if v5b > 99999 else v5b)
    v5c = wrap(v5b * wrap((v2 + x2) - m2))
    if G["g298"] != 100:
        v5c = tdiv(wrap(v5c * 100), G["g298"])
    pct = per["pct"]
    if pct != 100:
        v5c = tdiv(wrap(pct * v5c), 100)
    res = tdiv(wrap(G["g390"] * v5c), 0x38)
    if G["ac4"] & 0x20:
        res = wrap(res + tdiv(res, 2))
    if res > 0:
        return res if res < 99999999 else 99999999
    return 1


def read_state(m):
    def i32(a):
        return struct.unpack("<i", M.rd(m, a, 4))[0]

    def u8(a):
        return M.rd(m, a, 1)[0]

    G = {"era": i32(ERA), "afc": i32(AFC), "ac4": i32(AC4), "mask": u8(MASK),
         "g298": i32(G298), "g390": i32(G390)}
    per, max7 = {}, []
    for f in range(8):
        i = f * STRIDE
        per[f] = {o: i32(o + i) for o in (D78C, D790, D804, D728, D438, D430)}  # keys are ABSOLUTE
        per[f].update({"pct": i32(PCT_BASE + f * PCT_STRIDE), "field": i32(FIELD + i),
                       "acc": i32(ACC + i), "slot": i32(SLOT + i)})
    a = MAX_START
    while a < MAX_END:
        max7.append(i32(a) + i32(a + MAX_OFF) * 2)
        a += STRIDE
    return G, per, max7


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


def gdb_script(watched):
    blocks, addrs = [], []
    for a in watched:
        addrs.append("%#x" % a)
        blocks.append(WBLOCK.replace("@@A@@", "%#x" % a).replace("@@F@@", str(FAC)))
    sets = "".join("set $m%d = *(int *)%#x + *(int *)%#x * 2\n"
                   % (k, MAX_START + k * STRIDE, MAX_START + k * STRIDE + MAX_OFF)
                   for k in range(7))
    bps = [
        ("A0", RESET,
         "M98S A0 pc=0x5aaf5c fac=%d acc=%d field=%d slot=%d flag=%d round=%d cp=%d",
         ["$esi/%d" % STRIDE, "*(int *)($esi+0x94d7f8)", "*(int *)($esi+0x94d800)",
          "*(int *)($esi+0x94d7fc)", "*(int *)($esi+0x94d430)",
          "*(int *)0x985afc", "*(int *)0x985dcc"], ""),
        ("A1", INVAL,
         "M98S A1 pc=0x5aaf67 fac=%d old=%d acc=%d round=%d cp=%d",
         ["$esi/%d" % STRIDE, "*(int *)($esi+0x94d800)", "*(int *)($esi+0x94d7f8)",
          "*(int *)0x985afc", "*(int *)0x985dcc"], ""),
        ("A2", STORE,
         "M98S A2 pc=0x5aaf79 fac=%d val=%d old=%d d78c=%d d790=%d d804=%d d728=%d d438=%d "
         "pct=%d era=%d afc=%d ac4=%d mask=%d g298=%d g390=%d m0=%d m1=%d m2=%d m3=%d m4=%d "
         "m5=%d m6=%d round=%d cp=%d",
         ["$esi/%d" % STRIDE, "$eax", "*(int *)($esi+0x94d800)", "*(int *)($esi+0x94d78c)",
          "*(int *)($esi+0x94d790)", "*(int *)($esi+0x94d804)", "*(int *)($esi+0x94d728)",
          "*(int *)($esi+0x94d438)", "*(int *)(0x927a88+$esi/%d*1436)" % STRIDE,
          "*(int *)0x985aec", "*(int *)0x985afc", "*(int *)0x985ac4",
          "*(unsigned char *)0x985b10", "*(int *)0x92a298", "*(int *)0x92a390",
          "$m0", "$m1", "$m2", "$m3", "$m4", "$m5", "$m6",
          "*(int *)0x985afc", "*(int *)0x985dcc"], sets),
        ("A3", INVAL2,
         "M98S A3 pc=0x59f0c7 fac=%d old=%d round=%d cp=%d",
         ["$ebx/%d" % STRIDE, "*(int *)($ebx+0x94d800)",
          "*(int *)0x985afc", "*(int *)0x985dcc"], ""),
        ("A4", ENTRY,
         "M98S A4 pc=0x5aab70 fac=%d cached=%d ret=0x%x round=%d cp=%d",
         ["*(int *)($esp+4)", "*(int *)(0x94d800+*(int *)($esp+4)*%d)" % STRIDE,
          "*(int *)($esp)", "*(int *)0x985afc", "*(int *)0x985dcc"], ""),
    ]
    bp_txt, bp_pcs = [], []
    for tag, pc, line, args, sets in bps:
        bp_pcs.append("%#x" % pc)
        bp_txt.append(BPTPL.replace("@@PC@@", "%#x" % pc).replace("@@SETS@@", sets)
                      .replace("@@LINE@@", line.replace("%d", "%d")).replace("@@ARGS@@",
                      "".join(", " + a for a in args)))
    blocks += bp_txt
    return (TMPL.replace("@@WATCHES@@", "".join(blocks[:len(watched)]))
            .replace("@@BPS@@", "".join(blocks[len(watched):]))
            .replace("@@N@@", str(len(watched))).replace("@@ADDRS@@", " ".join(addrs))
            .replace("@@NB@@", str(len(bp_pcs))).replace("@@BPS@@", " ".join(bp_pcs)))


KV = re.compile(r"^(M98[SW]) (\w+)((?: [a-z]+=-?[\dxa-f]+)+) round=(\d+) cp=(\d+)\s*$")


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
                or ln.startswith("[Detached") or ln.startswith("Thread 1")
                or "__kernel_vsyscall" in ln or re.match(r"0x[0-9a-f]+ in ", ln)):
            continue
        unparsed.append(ln)
    return ev, unparsed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boundaries", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--tag", default="m98budget1")
    ap.add_argument("--predict", action="store_true", help="print predictions, no game touch")
    a = ap.parse_args()

    pid = M.find_pid()
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        G, per, max7 = read_state(m)
        rnd = struct.unpack("<i", M.rd(m, ROUND_ADDR, 4))[0]
    print(f"pid {pid} round {rnd} era {G['era']} afc {G['afc']} ac4 {G['ac4']:#x} "
          f"mask {G['mask']:#x} g298 {G['g298']} g390 {G['g390']} max7 {max7}", flush=True)
    print("PREDICTIONS (model of FUN_005aab70's recompute, from live memory BEFORE the run):",
          flush=True)
    preds = []
    for f in range(8):
        try:
            want = aab70_model(f, G, per[f], max7)
        except ZeroDivisionError as e:
            want = None
            print(f"  fac {f}: MODEL-EXCEPTION {e}")
            continue
        row = (f, per[f]["field"], per[f]["acc"], per[f]["slot"], want,
               per[f]["acc"] >= per[f]["field"])
        preds.append(row)
        print(f"  fac {f}: field {row[1]} acc {row[2]} slot {row[3]} -> MODEL {want} "
              f"{'== field (cache fresh)' if want == row[1] else '!= field'}; "
              f"grant-now={row[5]}", flush=True)
    n_eq = sum(1 for r in preds if r[4] == r[1] and r[1] >= 0)
    n_ne = sum(1 for r in preds if r[4] != r[1])
    print(f"model agrees with the live field on {n_eq}/7 cached factions; differs on {n_ne}",
          flush=True)
    if a.predict:
        return

    watch = [FIELD + FAC * STRIDE]
    gpath = os.path.join(SCRATCH, f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.gdblog")
    os.makedirs(SCRATCH, exist_ok=True)
    os.makedirs(EVID, exist_ok=True)
    open(gpath, "w").write(gdb_script(watch))
    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath,
                          "-p", str(pid)], stdout=log, stderr=subprocess.STDOUT)
    time.sleep(3.0)
    head = open(lpath, "r", errors="replace").read()
    n_hw = head.count("Hardware watchpoint")
    if "ARMED" not in head or n_hw < len(watch):
        try:
            os.kill(g.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
        subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
        raise SystemExit(f"gdb did not arm {len(watch)} HARDWARE watchpoints (saw {n_hw}):\n"
                         + head[-1200:])
    print(f"armed: {n_hw} hardware watchpoint on fac{FAC} field {FIELD + FAC*STRIDE:#x} "
          f"+ 5 silent bps", flush=True)

    t0 = time.time()
    rc_ok = True
    for k in range(a.boundaries):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "smac_play.py"),
                            "--turns", "1", "--timeout", str(a.timeout), "--no-escape",
                            "3000", "--orders-per-turn", "1", "--verbose",
                            "--tag", f"{a.tag}_r{k}"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            rc_ok = False
        print(f"  boundary {k}: rc={r.returncode} t={time.time()-t0:.0f}s "
              f"{r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ''}", flush=True)

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
        G2, per2, max72 = read_state(m)
        r_after = struct.unpack("<i", M.rd(m, ROUND_ADDR, 4))[0]
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
    a0, a1, a2, a3, a4, wp = (by.get(t, []) for t in ("A0", "A1", "A2", "A3", "A4", "WP"))
    print(f"--- events: {len(a0)} A0(acc reset) {len(a1)} A1(-1) {len(a2)} A2(store) "
          f"{len(a3)} A3(other -1) {len(a4)} A4(aab70 entry) {len(wp)} WP ---", flush=True)
    for d in ev[:60]:
        print("  ", json.dumps(d))

    funcs = load_funcs()
    pcs = sorted({d["pc"] for d in ev if "pc" in d})
    for pc in pcs:
        print(f"  pc 0x{pc:x} in {contain(pc, funcs) or 'UNMAPPED'}")

    # G5: every store value == the model recomputed from the inputs printed AT that hit
    g5rows = []
    for d in a2:
        Gh = {"era": d["era"], "afc": d["afc"], "ac4": d["ac4"], "mask": d["mask"],
              "g298": d["g298"], "g390": d["g390"]}
        ph = {D78C: d["d78c"], D790: d["d790"], D804: d["d804"], D728: d["d728"],
              D438: d["d438"], "pct": d["pct"]}
        mh = [d[f"m{k}"] for k in range(7)]
        try:
            want = aab70_model(d["fac"], Gh, ph, mh)
        except ZeroDivisionError:
            want = None
        g5rows.append((d["fac"], want, d["val"], want == d["val"], d["old"]))
    for fac, want, got, ok, old in g5rows:
        print(f"  PREDICT A2 fac {fac}: model {want} stores {got} (old {old}) "
              f"{'OK' if ok else 'MISMATCH'}")
    # G3: the invalidate -> recompute -> store order on one faction block
    seq = [(d["tag"], d["fac"]) for d in ev if d["tag"] in ("A0", "A1", "A2")]
    triples = sum(1 for i in range(len(seq) - 2)
                  if seq[i] == ("A0", seq[i + 1][1]) and seq[i + 1] == ("A1", seq[i + 1][1])
                  and seq[i + 2] == ("A2", seq[i + 1][1]))
    # G7: read-back — replay the store sequence per faction and compare with /proc
    lastw = {}
    for d in ev:
        if d["tag"] == "A2":
            lastw[d["fac"]] = d["val"]
        elif d["tag"] in ("A1", "A3"):
            lastw[d["fac"]] = -1
    rb_ok = [(f, lastw[f], per2[f]["field"], lastw[f] == per2[f]["field"])
             for f in sorted(lastw)]
    for f, want, got, ok in rb_ok:
        print(f"  READ-BACK fac {f}: last store {want} /proc {got} {'OK' if ok else 'MISMATCH'}")
    fired = sorted({d["fac"] for d in a2})
    moved = [f for f in range(8) if per[f]["field"] != per2[f]["field"]]
    g1 = n_hw >= 1 and len(pcs) >= 4
    g2 = rc_ok and r_after == rnd + a.boundaries
    g3 = triples >= 1
    g4 = bool(pcs) and all(contain(p, funcs) for p in pcs)
    g5 = bool(g5rows) and all(r[3] for r in g5rows)
    g6 = bool(a0) and all(d["acc"] >= d["field"] for d in a0)
    g7 = bool(rb_ok) and all(r[3] for r in rb_ok)
    g8 = all(d["pc"] in FIELD_STORE_PCS for d in wp)
    g9 = tracer == "0"
    g10 = not unparsed
    g11 = (bool(g5rows) and any(r[1] != r[4] for r in g5rows)) or n_ne >= 1
    gates = [("G1_armed", g1), ("G2_boundary", g2), ("G3_triple", g3), ("G4_mapped", g4),
             ("G5_model_at_hit", g5), ("G6_threshold_law", g6), ("G7_readback", g7),
             ("G8_only_static_stores", g8), ("G9_clean", g9), ("G10_parsed", g10),
             ("G11_discriminates", g11)]
    for n, v in gates:
        print(f"  {n}: {v}")
    ok = all(v for _n, v in gates)
    print(f"ACCEPTANCE {a.tag}: {'PASS' if ok else 'FAIL'} "
          f"({sum(1 for _n, v in gates if v)}/{len(gates)}) triples={triples} "
          f"model_ok={sum(1 for r in g5rows if r[3])}/{len(g5rows)} fired={fired} "
          f"moved={moved} a0={len(a0)} a1={len(a1)} a2={len(a2)} a3={len(a3)} a4={len(a4)} "
          f"wp={len(wp)} rounds {rnd}->{r_after} pcs={[hex(p) for p in pcs]} "
          f"unparsed={len(unparsed)}", flush=True)


if __name__ == "__main__":
    main()
