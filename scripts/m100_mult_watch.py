#!/usr/bin/env python3
"""M100 — who writes [fac*8380+0x94d6a4] (the per-faction RESEARCH MULTIPLIER) every round?

Static baseline (s154 + this session's grep of scratch/m574/text.txt): EXACTLY FIVE references to
0x94d6a4 in .text and ALL FIVE are loads — 0x445abf (FUN_00445900, clamp*10+100 build-time scale),
0x4aac96 (FUN_004aa7b0, the same scale for the UI), 0x4f352e + 0x4f3566 (FUN_004f34b0, the per-base
upkeep tail) and 0x56dffa (FUN_0056df40, `mult*-5 <= round` gates the acc +1 at 0x56e024). So the
per-round writer does NOT mention 0x94d6a4 as a displacement: only a HARDWARE watchpoint on the
field can name it (skill trap: "a hw watchpoint on the FIELD answers 'who writes it' in one run").

A watchpoint only REPORTS a VALUE CHANGE, so the run POKES every watched faction's multiplier to
`live + 10` (outside the [-5,5] clamp the consumers apply) before each boundary: any recompute is
then a change and MUST log. PREDICTIONS computed from the baseline before the run (see --predict):
  MODEL (a per-round writer runs): >=1 WP event per watched faction, the stored value != the
    sentinel, the events span >= 2 distinct rounds, and the consumer at 0x4f352e sees a value that
    is NOT the sentinel (s154: poked -5, read back -5, live 0 at 0x4f3558 -> the writer runs BEFORE
    the per-base tail).
  NULL (no writer in the window): ZERO WP events and the sentinel is STILL in place at the end.
The two disagree on every candidate -> the shape discriminates.

  python3 scripts/m100_mult_watch.py --predict
  M100_WFACS=1,2,3,6 python3 scripts/m100_mult_watch.py --tag m100mult1 --boundaries 2
"""
import bisect
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
import m99_param2 as P  # noqa: E402  (helpers only: STRIDE/MULT/ACC/..., load_funcs, contain, read_state)

ROOT = os.path.dirname(HERE)
EVID = os.path.join(ROOT, "evidence")
SCRATCH = os.path.join(ROOT, "scratch")
STRIDE, MULT, ACC = P.STRIDE, P.MULT, P.ACC
READ_PC = 0x4f352e          # mov eax,[ecx+0x94d6a4] inside FUN_004f34b0 (the upkeep-tail consumer)
WFACS = [int(x) for x in re.split(",", os.environ.get("M100_WFACS", "1,2,3,6"))]
POKE_ADD = int(os.environ.get("M100_POKE_ADD", "10"))

TMPL = r"""set pagination off
set confirm off
set can-use-hw-watchpoints 1
@@WATCHES@@@@BLOCKS@@printf "ARMED @@N@@ hw watchpoints at @@ADDRS@@; @@NB@@ silent bps at @@BPS@@\n"
continue
"""

WBLOCK = r"""watch *(int *)@@A@@
commands
silent
printf "M100W WP pc=0x%x new=%d fac=@@F@@ round=%d cp=%d\n", $pc, *(int *)@@A@@, *(int *)0x985afc, *(int *)0x985dcc
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


def gdb_script():
    blocks, addrs = [], []
    for f in WFACS:
        a = MULT + f * STRIDE
        addrs.append("%#x" % a)
        blocks.append(WBLOCK.replace("@@A@@", "%#x" % a).replace("@@F@@", str(f)))
    bps = [("READ", READ_PC, "M100B READ pc=0x4f352e fac=%d mult=%d round=%d cp=%d",
            ["$ebx", "*(int *)($ecx+0x94d6a4)", RND, CPP])]
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


KV = re.compile(r"^(M100[WBC]) (\w+)((?: [a-z][a-z0-9_]*=-?[\dxa-f]+)+) round=(\d+) cp=(\d+)\s*$")


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


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--boundaries", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--tag", default="m100mult1")
    ap.add_argument("--predict", action="store_true", help="print live inputs + predictions, no touch")
    ap.add_argument("--no-poke", action="store_true")
    a = ap.parse_args()

    pid = M.find_pid()
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        st = P.read_state(m)
    rnd = st["round"]
    human = (st["mask"] & -st["mask"]).bit_length() - 1
    print(f"pid {pid} round {rnd} cp {st['cp']} mask {st['mask']:#x} human fac{human} "
          f"ac4 {st['ac4']:#x}", flush=True)
    sentinel = {}
    for f in WFACS:
        sentinel[f] = st[f][MULT] + (0 if a.no_poke else POKE_ADD)
    print("--- baseline (the PREDICTION table, computed before the run) ---", flush=True)
    for f in range(8):
        mark = "WATCHED" if f in WFACS else "        "
        print(f"  fac {f} {mark}: mult {st[f][MULT]:>3}  sentinel {sentinel.get(f, '-'):>4}  "
              f"acc {st[f][ACC]:>5}  field {st[f][P.FIELD]:>5}", flush=True)
    print("  MODEL: >=1 WP event per watched faction, new != sentinel, >=2 distinct rounds, "
          "consumer mult != sentinel", flush=True)
    print("  NULL : 0 WP events and the sentinel STILL in [fac*8380+0x94d6a4] at the end", flush=True)
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
    print(f"armed: {n_hw} hw watchpoints on facs {WFACS} mult + 1 silent bp at 0x4f352e", flush=True)

    t0 = time.time()
    rc_ok = True
    pokes = []

    def poke(addr, value):
        with open(f"/proc/{pid}/mem", "rb+", 0) as mm:
            mm.seek(addr)
            mm.write(struct.pack("<i", value))
            mm.seek(addr)
            return struct.unpack("<i", mm.read(4))[0]

    for k in range(a.boundaries):
        if not a.no_poke:
            row = []
            for f in WFACS:
                got = poke(MULT + f * STRIDE, sentinel[f])
                row.append((f, sentinel[f], got, got == sentinel[f]))
            pokes.append(row)
            print(f"  boundary {k}: POKE " + " ".join(f"fac{f}->{s} read {g} {'OK' if ok else 'BAD'}"
                  for f, s, g, ok in row), flush=True)
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
    with open(f"/proc/{pid}/mem", "rb", 0) as mm:
        st2 = P.read_state(mm)
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
    wp, rd = by.get("WP", []), by.get("READ", [])
    print(f"--- events: WP={len(wp)} READ={len(rd)} ---", flush=True)
    for d in wp[:12]:
        print("  ", json.dumps(d), flush=True)

    funcs = P.load_funcs()
    pcs = sorted({d["pc"] for d in wp})
    writers = {}
    for pc in pcs:
        nm = P.contain(pc, funcs) or "UNMAPPED"
        writers[nm] = writers.get(nm, 0) + 1
        print(f"  WP pc 0x{pc:x} in {nm}  (store = pc - length; watchpoint reports store+length)",
              flush=True)
    print("  WRITERS: " + ", ".join(f"{k} x{v}" for k, v in sorted(writers.items(),
          key=lambda kv: -kv[1])), flush=True)
    cps = sorted({d["cp"] for d in wp})
    print(f"  cp at the stores: {cps}  (the segment the writer ran in)", flush=True)

    lastw = {}
    for d in wp:
        lastw[d["fac"]] = d["new"]
    rows = []
    for f in WFACS:
        ev_f = [d for d in wp if d["fac"] == f]
        rounds_f = sorted({d["round"] for d in ev_f})
        rows.append((f, len(ev_f), rounds_f, lastw.get(f), st2[f][MULT],
                     st2[f][MULT] != sentinel[f]))
    for f, n, rr, last, proc_val, undone in rows:
        print(f"  fac{f}: events {n} rounds {rr} last store {last} /proc {proc_val} "
              f"sentinel {sentinel[f]} undone={undone}", flush=True)

    g1 = n_hw >= len(WFACS) and "ARMED" in head
    g2 = rc_ok and r_after == rnd + a.boundaries
    g3 = bool(wp) and all(r[1] >= 1 for r in rows)
    g4 = bool(pcs) and all(P.contain(p, funcs) for p in pcs)
    g5 = bool(wp) and all(d["new"] != sentinel[d["fac"]] for d in wp)
    g6 = all(r[5] for r in rows)
    g7 = all(r[3] is not None and r[3] == r[4] for r in rows)
    g8 = len({d["round"] for d in wp}) >= 2
    rd_w = [d for d in rd if d["fac"] in WFACS]
    seen = {f: [d for d in rd_w if d["fac"] == f] for f in WFACS}
    for f in WFACS:
        vals = sorted({d["mult"] for d in seen[f]})
        print(f"  CONSUMER fac{f}: {len(seen[f])} reads, mult values seen {vals} "
              f"(sentinel was {sentinel[f]})", flush=True)
    g9 = bool(rd_w) and all(any(d["mult"] != sentinel[f] for d in seen[f]) for f in WFACS)
    g10 = tracer == "0"
    g11 = not unparsed
    gates = [("G1_armed", g1), ("G2_boundary", g2), ("G3_event_per_faction", g3),
             ("G4_writer_named", g4), ("G5_stored_not_the_poke", g5), ("G6_poke_undone", g6),
             ("G7_readback", g7), ("G8_two_rounds", g8), ("G9_consumer_sees_restore", g9),
             ("G10_clean", g10), ("G11_parsed", g11)]
    for n, v in gates:
        print(f"  {n}: {v}", flush=True)
    ok = all(v for _n, v in gates)
    print(f"ACCEPTANCE {a.tag}: {'PASS' if ok else 'FAIL'} ({sum(1 for _n, v in gates if v)}"
          f"/{len(gates)}) wp={len(wp)} read={len(rd)} rounds {rnd}->{r_after} "
          f"writers={ {k: v for k, v in writers.items()} } "
          f"final_mults={ {f: st2[f][MULT] for f in WFACS} } "
          f"sentinels={sentinel} cp={cps} unparsed={len(unparsed)}", flush=True)


if __name__ == "__main__":
    main()
