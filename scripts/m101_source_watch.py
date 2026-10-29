#!/usr/bin/env python3
"""M101 — what FEEDS the research multiplier: who writes the per-faction SOURCE ARRAY
[fac*8380+0x94d700] (slot 10 = 0x94d728 is the ±2 that M100 saw arrive at 0x5a17a0) and who writes
[fac*8380+0x94d658] (the 4 category record indices).

STATIC BASELINE (this session's census of scratch/m574/text.txt — note the instruction lines are
INDENTED, so `grep -E '^[0-9a-f]{6,8}:' finds nothing; grep the offset string itself):
  stores to [reg*4+0x94d700]: 0x59ec68 `add [ecx*4+0x94d700],ebx` (FUN_0059ec00) and 0x5a0471
  `add [ecx*4+0x94d700],esi` (FUN_0059ec90). ZERO references to 0x94d728 (slot 10 is reached as
  0x94d700 + 10*4).  stores to [reg*4+0x94d658]: 0x4b2715 `mov [eax+ecx*4+0x94d658],edx`
  (FUN_004b2570; eax = fac*8380 via `imul eax,[edx+0xcf4],0x20bc`).
  FUN_0059ec00(fac) zeroes the 11-dword array (`rep stos` 0x5a... 0x59ec24, reported 0x59ec26) then
  walks the faction's EFFECTS TABLE (count at [0x927a9c+fac*1436], parallel arrays type@0x927aa0,
  index@0x927ac0, value@0x927ae0, 4 bytes per row) and for every row with type == 3 does
  `src[index] += value`.
OFFLINE MODEL, verified 8/8 against live memory at r54 before ANY run (see --predict):
  src[10] == sum(value for type==3 and index==10)          8/8
  mult    == sum(category row slot 10) + src[10]           8/8
  (fac3 has row (3,10,2); fac6 has row (3,10,-2); fac1's -2 comes from category 0 record 3.)
PREDICTIONS for the run, computed from the baseline BEFORE it:
  MODEL (a rebuild runs in the window): >=1 WP store event; every store pc in the static set
    {0x59ec26 reset, 0x59ec6f add (FUN_0059ec00), 0x5a0478 add (FUN_0059ec90)}; the ENTRY bp logs
    with a return pc contained in a NAMED function; every faction whose rebuild ran ends with
    src[10] == its table sum (the sentinel poke gone); last store == /proc read-back.
  NULL (no rebuild in the window): ZERO store events and all seven sentinel pokes STILL in place.
The two disagree -> the shape discriminates.

  python3 scripts/m101_source_watch.py --predict
  M101_WFACS=1,2,3,6 python3 scripts/m101_source_watch.py --tag m101src1 --boundaries 2
"""
import argparse
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
import m99_param2 as P  # noqa: E402  (load_funcs/contain/STRIDE/ROUND/CP/MASK/AC4 only)

ROOT = os.path.dirname(HERE)
EVID = os.path.join(ROOT, "evidence")
SCRATCH = os.path.join(ROOT, "scratch")
STRIDE = P.STRIDE
SRC, SRC10, RECIDX = 0x94d700, 0x94d728, 0x94d658
MULT, CATROW, TBL = 0x94d6a4, 0x92babc, 0x927a88
RESET_REP, ADD1_REP, ADD2_REP = 0x59ec26, 0x59ec6f, 0x5a0478   # watchpoint-reported pcs
ENTRY_PC, ADD1_PC, ADD2_PC, RECIDX_PC = 0x59ec00, 0x59ec68, 0x5a0471, 0x4b2715
STORE_PCS = {RESET_REP, ADD1_REP, ADD2_REP}
WFACS = [int(x) for x in re.split(",", os.environ.get("M101_WFACS", "1,2,3,6"))]
POKED = list(range(1, 8))
POKE_ADD = int(os.environ.get("M101_POKE_ADD", "10"))

TMPL = r"""set pagination off
set confirm off
set can-use-hw-watchpoints 1
@@WATCHES@@@@BLOCKS@@printf "ARMED @@N@@ hw watchpoints at @@ADDRS@@; @@NB@@ silent bps at @@BPS@@\n"
continue
"""
WBLOCK = r"""watch *(int *)@@A@@
commands
silent
printf "M101W WP pc=0x%x new=%d fac=@@F@@ round=%d cp=%d\n", $pc, *(int *)@@A@@, *(int *)0x985afc, *(int *)0x985dcc
continue
end
"""
BPTPL = r"""break *@@PC@@@@COND@@
commands
silent
printf "@@LINE@@\n"@@ARGS@@
continue
end
"""
RND, CPP = "*(int *)0x985afc", "*(int *)0x985dcc"


def gdb_script():
    blocks, addrs = [], []
    for f in WFACS:
        a = SRC10 + f * STRIDE
        addrs.append("%#x" % a)
        blocks.append(WBLOCK.replace("@@A@@", "%#x" % a).replace("@@F@@", str(f)))
    bps = [
        ("ENTRY", ENTRY_PC, "", "M101E ENTRY pc=0x59ec00 fac=%d ret=0x%x round=%d cp=%d",
         ["*(int *)($esp+4)", "*(int *)($esp)", RND, CPP]),
        ("ADD1", ADD1_PC, " if ($ecx % 2095) == 10",
         "M101A ADD1 pc=0x59ec68 fac=%d add=%d round=%d cp=%d", ["$ecx/2095", "$ebx", RND, CPP]),
        ("ADD2", ADD2_PC, " if ($ecx % 2095) == 10",
         "M101A ADD2 pc=0x5a0471 fac=%d add=%d round=%d cp=%d", ["$ecx/2095", "$esi", RND, CPP]),
        ("RECIDX", RECIDX_PC, "",
         "M101R RECIDX pc=0x4b2715 fac=%d cat=%d rec=%d round=%d cp=%d",
         ["$eax/8380", "$ecx", "$edx", RND, CPP]),
    ]
    bp_txt, bp_pcs = [], []
    for tag, pc, cond, line, args in bps:
        bp_pcs.append("%#x" % pc)
        bp_txt.append(BPTPL.replace("@@PC@@", "%#x" % pc).replace("@@COND@@", cond)
                      .replace("@@LINE@@", line)
                      .replace("@@ARGS@@", "".join(", " + a2 for a2 in args)))
    blocks += bp_txt
    return (TMPL.replace("@@WATCHES@@", "".join(blocks[:len(WFACS)]))
            .replace("@@BLOCKS@@", "".join(blocks[len(WFACS):]))
            .replace("@@N@@", str(len(WFACS))).replace("@@ADDRS@@", " ".join(addrs))
            .replace("@@NB@@", str(len(bp_pcs))).replace("@@BPS@@", " ".join(bp_pcs)))


KV = re.compile(r"^(M101[WEAR]) (\w+)((?: [a-z][a-z0-9_]*=-?[\dxa-f]+)+) round=(\d+) cp=(\d+)\s*$")


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
        if ("Hardware watchpoint" in ln or ln.startswith("[Inferior")
                or ln.startswith("[New LWP") or ln.startswith("[Thread ")
                or ln.startswith("[Detached") or ln.startswith("[Switching to LWP")
                or re.match(r"Thread \d+ ", ln) or "__kernel_vsyscall" in ln
                or re.match(r"0x[0-9a-f]+ in ", ln)):
            continue
        unparsed.append(ln)
    return ev, unparsed


def model(m):
    def i32(a):
        return struct.unpack("<i", M.rd(m, a, 4))[0]
    out = {}
    for f in range(8):
        b = f * STRIDE
        cnt = max(i32(0x927a9c + f * 1436), 0)
        rows = [(i32(0x927aa0 + f * 1436 + 4 * i), i32(0x927ac0 + f * 1436 + 4 * i),
                 i32(0x927ae0 + f * 1436 + 4 * i)) for i in range(cnt)]
        pred_src10 = sum(v for t, ix, v in rows if t == 3 and ix == 10)
        p1 = [i32(RECIDX + b + 4 * c) for c in range(4)]
        cat = sum(i32(CATROW + c * 0xd4 + p1[c] * 0x2c + 0x28) for c in range(4))
        out[f] = {"cnt": cnt, "rows": rows, "src10": i32(SRC10 + b), "pred": pred_src10,
                  "p1": p1, "cat": cat, "mult": i32(MULT + b), "pred_mult": cat + pred_src10}
    out["round"] = i32(P.ROUND)
    out["cp"] = i32(P.CP)
    out["mask"] = M.rd(m, P.MASK, 1)[0]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boundaries", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--tag", default="m101src1")
    ap.add_argument("--predict", action="store_true")
    ap.add_argument("--arm-acc", action="store_true",
                    help="M98's recipe: poke [fac*8380+0x94d7f8] = [0x94d800]+1 before every boundary "
                         "so the advance GRANT fires (the effects-table change that should call "
                         "FUN_0059ec00)")
    a = ap.parse_args()

    pid = M.find_pid()
    st = model(open(f"/proc/{pid}/mem", "rb", 0))
    rnd = st["round"]
    human = (st["mask"] & -st["mask"]).bit_length() - 1
    sentinel = {f: st[f]["src10"] + POKE_ADD for f in POKED}
    print(f"pid {pid} round {rnd} cp {st['cp']} human fac{human}", flush=True)
    print("--- baseline MODEL (computed from live memory BEFORE the run) ---", flush=True)
    for f in range(8):
        d = st[f]
        print(f"  fac {f} rows {d['rows']} | src10 {d['src10']:>3} pred {d['pred']:>3} "
              f"{'OK' if d['src10'] == d['pred'] else 'DIFF'} | mult {d['mult']:>3} "
              f"cat {d['cat']:>3} pred {d['pred_mult']:>3} "
              f"{'OK' if d['mult'] == d['pred_mult'] else 'DIFF'}"
              + (f"  SENTINEL {sentinel[f]}" if f in POKED else ""), flush=True)
    n_ok_src = sum(1 for f in range(8) if st[f]["src10"] == st[f]["pred"])
    n_ok_mult = sum(1 for f in range(8) if st[f]["mult"] == st[f]["pred_mult"])
    print(f"  MODEL 8/8 CHECK: src10 {n_ok_src}/8, mult {n_ok_mult}/8", flush=True)
    print("  MODEL(run): >=1 store event, every store pc in {0x59ec26,0x59ec6f,0x5a0478}, ENTRY ret "
          "pc named, rebuilt factions end at their table sum", flush=True)
    print("  NULL (run) : 0 store events and all 7 sentinels still in place", flush=True)
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
        raise SystemExit(f"gdb did not arm {len(WFACS)} hw watchpoints (saw {n_hw}):\n" + head[-1200:])
    print(f"armed: {n_hw} hw watchpoints on facs {WFACS} src[10] + 4 silent bps", flush=True)

    t0, rc_ok = time.time(), True

    def poke(addr, value):
        with open(f"/proc/{pid}/mem", "rb+", 0) as mm:
            mm.seek(addr)
            mm.write(struct.pack("<i", value))
            mm.seek(addr)
            return struct.unpack("<i", mm.read(4))[0]

    for k in range(a.boundaries):
        row = [(f, poke(SRC10 + f * STRIDE, sentinel[f])) for f in POKED]
        print(f"  boundary {k}: POKE " + " ".join(f"fac{f}->{sentinel[f]}={g}" for f, g in row),
              flush=True)
        if a.arm_acc:
            with open(f"/proc/{pid}/mem", "rb", 0) as mm:
                fields = {f: struct.unpack("<i", M.rd(mm, 0x94d800 + f * STRIDE, 4))[0]
                          for f in POKED}
            arm = [(f, poke(0x94d7f8 + f * STRIDE, fields[f] + 1)) for f in POKED]
            print(f"  boundary {k}: ARM " + " ".join(f"fac{f} field {fields[f]} acc->{v}"
                  for f, v in arm), flush=True)
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "smac_play.py"),
                            "--turns", "1", "--timeout", str(a.timeout), "--no-escape",
                            "3000", "--orders-per-turn", "1", "--verbose",
                            "--tag", f"{a.tag}_r{k}"], capture_output=True, text=True)
        if r.returncode != 0:
            rc_ok = False
        print(f"  boundary {k}: rc={r.returncode} t={time.time()-t0:.0f}s "
              f"{r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ''}", flush=True)

    waited = 0
    while waited < 90:
        with open(f"/proc/{pid}/mem", "rb", 0) as mm:
            cp = struct.unpack("<i", M.rd(mm, P.CP, 4))[0]
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
    st2 = model(open(f"/proc/{pid}/mem", "rb", 0))
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
    wp, entry = by.get("WP", []), by.get("ENTRY", [])
    add1, add2, recidx = by.get("ADD1", []), by.get("ADD2", []), by.get("RECIDX", [])
    print(f"--- events: WP={len(wp)} ENTRY={len(entry)} ADD1={len(add1)} ADD2={len(add2)} "
          f"RECIDX={len(recidx)} ---", flush=True)
    for d in wp[:14]:
        print("  ", json.dumps(d), flush=True)

    funcs = P.load_funcs()
    wp_pcs = sorted({d["pc"] for d in wp})
    for pc in wp_pcs:
        print(f"  WP pc 0x{pc:x} in {P.contain(pc, funcs) or 'UNMAPPED'}", flush=True)
    callers = {}
    for d in entry:
        nm = P.contain(d["ret"], funcs) or "UNMAPPED"
        callers[nm] = callers.get(nm, 0) + 1
    for f in range(1, 8):
        ef = [d for d in entry if d["fac"] == f]
        print(f"  ENTRY fac{f}: {len(ef)} in rounds {sorted({d['round'] for d in ef})}", flush=True)
    print("  REBUILD CALLERS (ret pc containment): "
          + ", ".join(f"{k} x{v}" for k, v in sorted(callers.items(), key=lambda kv: -kv[1])),
          flush=True)
    for d in (add1[:4] + add2[:4] + recidx[:4]):
        print("  ", json.dumps(d), flush=True)

    lastw = {}
    for d in wp:
        lastw[d["fac"]] = d["new"]
    rows = []
    for f in POKED:
        ev_f = [d for d in wp if d["fac"] == f]
        undone = st2[f]["src10"] != sentinel[f]
        rows.append((f, len(ev_f), undone, lastw.get(f), st2[f]["src10"], st2[f]["pred"],
                     st2[f]["mult"], st2[f]["pred_mult"]))
    for f, n, undone, last, src10, pred, mult, pm in rows:
        print(f"  fac{f}: WP events {n} sentinel {sentinel[f]} undone={undone} | src10 {src10} "
              f"table-sum {pred} {'OK' if src10 == pred else 'DIFF'} | mult {mult} model {pm} "
              f"{'OK' if mult == pm else 'DIFF'} | last store {last}", flush=True)

    rebuilt = [r for r in rows if r[2]]
    g1 = n_hw >= len(WFACS) and "ARMED" in head
    g2 = rc_ok and r_after == rnd + a.boundaries
    g3 = bool(wp)
    g4 = bool(wp_pcs) and all(pc in STORE_PCS for pc in wp_pcs)
    g5 = bool(entry) and all(P.contain(d["ret"], funcs) for d in entry)
    g6 = bool(rebuilt) and all(r[4] == r[5] for r in rebuilt)
    g7 = all(r[6] == r[7] for r in rows)
    g8 = all(r[3] is not None and r[3] == r[4] for r in rebuilt)
    g9 = n_ok_src == 8 and n_ok_mult == 8
    g10 = tracer == "0"
    g11 = not unparsed
    gates = [("G1_armed", g1), ("G2_boundary", g2), ("G3_rebuild_logged", g3),
             ("G4_store_pcs_are_the_static_set", g4), ("G5_entry_caller_named", g5),
             ("G6_src10_equals_table_sum", g6), ("G7_mult_equals_model_all8", g7),
             ("G8_readback", g8), ("G9_baseline_model_8of8", g9), ("G10_clean", g10),
             ("G11_parsed", g11)]
    for n, v in gates:
        print(f"  {n}: {v}", flush=True)
    ok = all(v for _n, v in gates)
    print(f"ACCEPTANCE {a.tag}: {'PASS' if ok else 'FAIL'} ({sum(1 for _n, v in gates if v)}"
          f"/{len(gates)}) wp={len(wp)} entry={len(entry)} add1={len(add1)} add2={len(add2)} "
          f"recidx={len(recidx)} rounds {rnd}->{r_after} wp_pcs={[hex(p) for p in wp_pcs]} "
          f"callers={ {k: v for k, v in callers.items()} } "
          f"src10={ {f: st2[f]['src10'] for f in POKED} } sentinels={sentinel} "
          f"mults={ {f: st2[f]['mult'] for f in range(8)} } unparsed={len(unparsed)}", flush=True)


if __name__ == "__main__":
    main()
