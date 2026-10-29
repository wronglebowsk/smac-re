#!/usr/bin/env python3
"""M97 — WHO writes base+0xd0 (credit) mid-game, and WHEN (which caller, which round).

The TRAP says +0xd0 is written ONLY at player-record init (0x6310c6 / 0x631154) yet a
-1 -> 0 was seen between r58/r59 (M95 notes).  A full scan of the .text dump finds SIX
stores to `[reg+0xd0]`: 0x5ba9e8 (a ebx-zeroing sweep over +0xa0..+0xe8), 0x6310c6,
0x631154, 0x6315e2 (init/zero) and TWO inside FUN_004e93f0 — 0x4e9557
`mov [eax+0xd0],edx` (credit = [eax+0xc0] - [eax+0xf0]) and 0x4e957f
`mov [eax+0xd0],ebx` (credit -= [eax+0xe0]), followed by the mirror 0x4e9590
`mov [eax+0x94],edx`.  eax is loaded from ds:0x8f0d60 = the CURRENT BASE RECORD pointer.

Four HARDWARE watchpoints on one base row's income chain — CREDIT +0xd0, GROSS +0xc0,
UPKEEP +0xf0, DISPCOPY +0x94 — print pc, the caller return address `*(int*)($ebp+4)`,
the record pointer, the new value and the live c0/f0/e0/d0 at every store.  The gate
PREDICTS the stored value from the live inputs before it is confirmed by the log, and
requires every CREDIT store pc to be one of the two static sites (a third writer would
fail G8).  The before/after movement-vs-events diff is the instrument's own check.

    python3 scripts/m97_credit_watch.py --tag m97credit1 --boundaries 2   # PASS/FAIL
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
CURSOR_PTR = 0x8F0D60
BASE_ARR, BASE_SZ = 0x95DA10, 304
BASE_NAME = os.environ.get("M97_BASE", "University Base")

# the two static stores to [base+0xd0] inside FUN_004e93f0 (reported pc = store + len)
STORE_PCS = (0x4E955D, 0x4E9585)

TMPL = r"""set pagination off
set confirm off
set can-use-hw-watchpoints 1
@@WATCHES@@printf "ARMED @@N@@ hw watchpoints at @@ADDRS@@\n"
continue
"""

WBLOCK = r"""watch *(int *)@@A@@
commands
silent
printf "M97W @@T@@ pc=0x%x ret=0x%x ptr=0x%x new=%d c0=%d f0=%d e0=%d d0=%d round=%d cp=%d\n", $pc, *(int *)($ebp+4), *(int *)0x8f0d60, *(int *)@@A@@, *(int *)@@C0@@, *(int *)@@F0@@, *(int *)@@E0@@, *(int *)@@D0@@, *(int *)0x985afc, *(int *)0x985dcc
continue
end
"""

SBLOCK = r"""break *@@PC@@ if @@COND@@
commands
silent
printf "M97S @@T@@ pc=0x%x val=%d c0=%d f0=%d e0=%d old=%d ret=0x%x round=%d cp=%d\n", $pc, @@VAL@@, *(int *)($eax+0xc0), *(int *)($eax+0xf0), *(int *)($eax+0xe0), *(int *)($eax+0xd0), *(int *)($ebp+4), *(int *)0x985afc, *(int *)0x985dcc
continue
end
"""

SLINE = re.compile(r"^M97S (S\d) pc=(0x[0-9a-f]+) val=(-?\d+) c0=(-?\d+) f0=(-?\d+) "
                   r"e0=(-?\d+) old=(-?\d+) ret=(0x[0-9a-f]+) round=(\d+) cp=(\d+)\s*$")

LINE = re.compile(r"^M97W (\w+) pc=(0x[0-9a-f]+) ret=(0x[0-9a-f]+) ptr=(0x[0-9a-f]+) "
                  r"new=(-?\d+) c0=(-?\d+) f0=(-?\d+) e0=(-?\d+) d0=(-?\d+) "
                  r"round=(\d+) cp=(\d+)\s*$")


def gdb_script(watch, stores):
    blocks, addrs = [], []
    for tag, a, c0, f0, e0, d0 in watch:
        addrs.append("%#x" % a)
        b = (WBLOCK.replace("@@A@@", "%#x" % a).replace("@@T@@", tag)
             .replace("@@C0@@", "%#x" % c0).replace("@@F0@@", "%#x" % f0)
             .replace("@@E0@@", "%#x" % e0).replace("@@D0@@", "%#x" % d0))
        blocks.append(b)
    for tag, addr, cond, val in stores:
        blocks.append(SBLOCK.replace("@@T@@", tag).replace("@@PC@@", "%#x" % addr)
                      .replace("@@COND@@", cond).replace("@@VAL@@", val))
    return (TMPL.replace("@@WATCHES@@", "".join(blocks))
            .replace("@@N@@", str(len(watch)))
            .replace("@@ADDRS@@", " ".join(addrs)))


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


def dis_window(pc):
    spec = importlib.util.spec_from_file_location("m71dis",
                                                  os.path.join(SCRATCH, "m71", "dis.py"))
    d = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(d)
    return d.dump(pc - 12, pc + 2, cap=10)


def read_chain(m, row):
    def i32(off):
        return struct.unpack("<i", M.rd(m, row + off, 4))[0]
    return {o: i32(o) for o in (0x40, 0x4c, 0x94, 0xc0, 0xd0, 0xe0, 0xf0)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boundaries", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--tag", default="m97credit1")
    ap.add_argument("--poke-minerals", type=int, default=200)
    a = ap.parse_args()

    pid = M.find_pid()
    os.makedirs(SCRATCH, exist_ok=True)
    os.makedirs(EVID, exist_ok=True)
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        row = None
        nb = struct.unpack("<i", M.rd(m, 0x985AF4, 4))[0]
        for i in range(min(max(nb, 0), 64)):
            rec = M.rd(m, BASE_ARR + i * BASE_SZ, BASE_SZ)
            if rec[19:51].split(b"\0")[0].decode("latin-1", "replace") == BASE_NAME:
                row = BASE_ARR + i * BASE_SZ
                break
        if row is None:
            raise SystemExit(f"base {BASE_NAME!r} not found in the base array")
        before = read_chain(m, row)
        rnd = struct.unpack("<i", M.rd(m, ROUND_ADDR, 4))[0]
    print(f"pid {pid} round {rnd} base {BASE_NAME} row 0x{row:x}", flush=True)
    print("chain before: " + " ".join(f"+{k:x}={v}" for k, v in before.items()), flush=True)
    # PREDICTION from live memory BEFORE the run
    pred = before[0xc0] - before[0xf0] - before[0xe0]
    print(f"PREDICT credit after the recompute: c0 {before[0xc0]} - f0 {before[0xf0]} "
          f"- e0 {before[0xe0]} = {pred} (live credit {before[0xd0]})", flush=True)

    watch = [("CREDIT", row + 0xD0, row + 0xC0, row + 0xF0, row + 0xE0, row + 0xD0),
             ("GROSS", row + 0xC0, row + 0xC0, row + 0xF0, row + 0xE0, row + 0xD0),
             ("UPKEEP", row + 0xF0, row + 0xC0, row + 0xF0, row + 0xE0, row + 0xD0),
             ("DISPCOPY", row + 0x94, row + 0xC0, row + 0xF0, row + 0xE0, row + 0xD0)]
    # A HARDWARE watchpoint only reports a VALUE CHANGE (gdb re-evaluates the expression
    # and continues silently when it is unchanged), so a recompute that lands on the same
    # credit logs NOTHING (m97credit2 saw 15 GROSS stores and 0 CREDIT events).  Silent
    # breakpoints AT the two static stores fire on EVERY execution and print the value the
    # store is about to write, with a register-only condition so only this row is logged.
    stores = [("S1", 0x4E9557, "$eax==%#x" % row, "$edx"),
              ("S2", 0x4E957F, "$eax==%#x" % row, "$ebx")]

    def poke_storage(value):
        with open(f"/proc/{pid}/mem", "rb+", 0) as mm:
            mm.seek(row + 0x40)
            mm.write(struct.pack("<i", value))
            mm.seek(row + 0x40)
            return struct.unpack("<i", mm.read(4))[0]

    print(f"  storage poked to {a.poke_minerals}, read back {poke_storage(a.poke_minerals)}",
          flush=True)

    gpath = os.path.join(SCRATCH, f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.gdblog")
    open(gpath, "w").write(gdb_script(watch, stores))
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
    print(f"armed: {n_hw} hardware watchpoints on {[t for t, *_ in watch]}", flush=True)

    t0 = time.time()
    rc_ok = True
    for k in range(a.boundaries):
        poke_storage(a.poke_minerals)
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
        after = read_chain(m, row)
        r_after = struct.unpack("<i", M.rd(m, ROUND_ADDR, 4))[0]
    print("chain after:  " + " ".join(f"+{k:x}={v}" for k, v in after.items()), flush=True)
    print(f"  after: round {r_after} tracer {tracer}", flush=True)

    text = open(lpath, "r", errors="replace").read()
    ev, st, unparsed = [], [], []
    armed = False
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        sm = SLINE.match(ln)
        if sm:
            st.append({"tag": sm.group(1), "pc": int(sm.group(2), 16),
                       "val": int(sm.group(3)), "c0": int(sm.group(4)),
                       "f0": int(sm.group(5)), "e0": int(sm.group(6)),
                       "old": int(sm.group(7)), "ret": int(sm.group(8), 16),
                       "round": int(sm.group(9)), "cp": int(sm.group(10))})
            continue
        mm2 = LINE.match(ln)
        if mm2:
            ev.append({"tag": mm2.group(1), "pc": int(mm2.group(2), 16),
                       "ret": int(mm2.group(3), 16), "ptr": int(mm2.group(4), 16),
                       "new": int(mm2.group(5)), "c0": int(mm2.group(6)),
                       "f0": int(mm2.group(7)), "e0": int(mm2.group(8)),
                       "d0": int(mm2.group(9)), "round": int(mm2.group(10)),
                       "cp": int(mm2.group(11))})
            continue
        if not armed:
            if "ARMED" in ln:
                armed = True
            continue
        if ("Hardware watchpoint" in ln or ln.startswith("[Inferior")
                or ln.startswith("[New LWP") or ln.startswith("[Thread ")
                or ln.startswith("[Detached") or ln.startswith("Thread 1")
                or "__kernel_vsyscall" in ln
                or re.match(r"0x[0-9a-f]+ in ", ln)):
            continue  # gdb noise: watchpoint banners, LWP-attach banners, stop locations
        unparsed.append({"tag": "?", "raw": ln})
    with open(os.path.join(SCRATCH, f"{a.tag}_seq.jsonl"), "w") as fh:
        for d in ev + unparsed:
            fh.write(json.dumps(d) + "\n")

    n_ev = len(ev)
    cred = [e for e in ev if e["tag"] == "CREDIT"]
    n_s1 = len([s for s in st if s["tag"] == "S1"])
    n_s2 = len([s for s in st if s["tag"] == "S2"])
    print(f"--- {n_ev} watchpoint events ({len(cred)} on CREDIT +0xd0), {len(st)} store executions "
          f"({n_s1} x S1 [+0xd0]=[+0xc0]-[+0xf0], {n_s2} x S2 [+0xd0]-=[+0xe0]) ---", flush=True)
    for e in ev[:40]:
        print(f"  {e['tag']} pc 0x{e['pc']:x} ret 0x{e['ret']:x} ptr 0x{e['ptr']:x} "
              f"new {e['new']} c0 {e['c0']} f0 {e['f0']} e0 {e['e0']} d0 {e['d0']} "
              f"round {e['round']} cp {e['cp']}")
    for s in st[:30]:
        print(f"  {s['tag']} pc 0x{s['pc']:x} stores {s['val']} (c0 {s['c0']} f0 {s['f0']} e0 {s['e0']} old {s['old']}) ret 0x{s['ret']:x} "
              f"round {s['round']} cp {s['cp']}")

    funcs = load_funcs()
    pcs = sorted({e["pc"] for e in ev})
    rets = sorted({e["ret"] for e in ev} | {s["ret"] for s in st})
    for pc in pcs:
        print(f"  writer pc 0x{pc:x} in {contain(pc, funcs) or 'UNMAPPED'}")
    for rt in rets:
        print(f"  caller ret 0x{rt:x} in {contain(rt, funcs) or 'UNMAPPED'}")
    for pc in sorted({e["pc"] for e in cred}):
        for ln in dis_window(pc):
            print("   ", ln.strip().split("\t", 1)[-1] if "\t" in ln else ln)

    # instrument self-check: a watched dword that moved must have had an event
    offs = {"CREDIT": 0xD0, "GROSS": 0xC0, "UPKEEP": 0xF0, "DISPCOPY": 0x94}
    gaps = [t for t, off in offs.items()
            if before[off] != after[off] and not any(e["tag"] == t for e in ev)]
    moved = {t: (before[off] != after[off], sum(1 for e in ev if e["tag"] == t))
             for t, off in offs.items()}
    print("movement: " + ", ".join(f"{k}: moved={v[0]} events={v[1]}"
                                   for k, v in moved.items()), flush=True)

    # G5: every CREDIT store value == the prediction computed from the live inputs AT the hit
    # PREDICTION from the live record AT each store, before it is confirmed by the log:
    # S1 must store [eax+0xc0] - [eax+0xf0]; S2 must store old_credit - [eax+0xe0].
    pred_ok = []
    for s in st:
        want = s["c0"] - s["f0"] if s["tag"] == "S1" else s["old"] - s["e0"]
        pred_ok.append((s["tag"], s["pc"], want, s["val"], want == s["val"]))
    for tg, pc, want, got, ok in pred_ok:
        print(f"  PREDICT {tg} pc 0x{pc:x}: want {want} stores {got} "
              f"{'OK' if ok else 'MISMATCH'}")
    for e in cred:
        want = e["c0"] - e["f0"] - e["e0"]
        print(f"  WP CREDIT pc 0x{e['pc']:x}: c0-f0-e0 = {want} new {e['new']} "
              f"{'OK' if want == e['new'] else 'MISMATCH'}")
    rounds_seen = sorted({s["round"] for s in st})
    g1 = True
    g2 = rc_ok and r_after == rnd + a.boundaries
    g3 = bool(st) and n_s1 >= 1 and n_s2 >= 1
    g4 = bool(pcs) and all(contain(p, funcs) for p in pcs) and all(contain(r, funcs) for r in rets)
    g5 = bool(pred_ok) and all(o[4] for o in pred_ok)
    g6 = (bool(st) and after[0xD0] == st[-1]["val"] and after[0x94] == after[0xD0]
          and after[0xD0] == after[0xC0] - after[0xF0] - after[0xE0])
    g7 = not gaps
    g8 = all(e["pc"] in STORE_PCS for e in cred)
    g9 = tracer == "0"
    g10 = not unparsed
    g11 = len(rounds_seen) >= a.boundaries
    gates = [("G1_armed", g1), ("G2_boundary", g2), ("G3_both_stores", g3),
             ("G4_mapped", g4), ("G5_predicted_values", g5), ("G6_readback", g6),
             ("G7_no_gap", g7), ("G8_only_static_stores", g8), ("G9_clean", g9),
             ("G10_parsed", g10), ("G11_every_round", g11)]
    for n, v in gates:
        print(f"  {n}: {v}")
    ok = all(v for _n, v in gates)
    print(f"ACCEPTANCE {a.tag}: {'PASS' if ok else 'FAIL'} "
          f"({sum(1 for _n, v in gates if v)}/{len(gates)}) wp_events={n_ev} credit_wp={len(cred)} stores={len(st)} S1={n_s1} S2={n_s2} "
          f"rounds_seen={rounds_seen} "
          f"rounds {rnd}->{r_after} credit {before[0xd0]}->{after[0xd0]} "
          f"pcs={[hex(p) for p in pcs]} callers={[hex(r) for r in rets]} gaps={gaps} "
          f"unparsed={len(unparsed)}", flush=True)


if __name__ == "__main__":
    main()
