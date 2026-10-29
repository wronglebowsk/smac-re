#!/usr/bin/env python3
"""M94 — WHO writes the tail control tables 0x94e488 / 0x94e5a8 / 0x94eda8 /
0x950664 between rounds, and WHEN (which round the store lands in).

M92/M93 proved these are the ladder's inputs: divisor `[fac*8380+0x94e488]`
(0x5a9503), multiplier bytes `[fac*8380+0x94e5a8+esi]`, category bytes
`[fac*8380+0x94eda8+esi]`, and the "band tables" `0x950664 + edi*8380` = the
per-faction multiplier array of faction edi.  They move BETWEEN rounds; nobody
has yet said who writes them.  Four HARDWARE watchpoints (the pick's four
addresses) print `$pc` + new value + the live round for EVERY store; the writer
is then named by containment via ghidra_out/index.csv.  The before/after diff of
the full 64-byte arrays is the instrument's own discrimination check: an array
that moved with no event on it is an instrument gap, not an answer.

    python3 scripts/m94_table_watch.py --tag m94table1 --boundaries 2   # PASS/FAIL
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
STRIDE = 8380
ROUND_ADDR = 0x985AFC
BASE_ARR, BASE_SZ = 0x95DA10, 304
BASE_NAME = os.environ.get("M94_BASE", "Korolev Center")

# tag, addr — divisor instances that MOVED in run m94table1 (fac0's stayed 0,
# its watchpoint proved nobody wrote 0x94e488 in 2 boundaries)
WATCH = [("DIV1", 0x950544), ("DIV2", 0x952600), ("DIV4", 0x956778),
         ("DIV5", 0x958834)]
# region diffs: watched dwords plus the run-1 context arrays (context never gates)
REGS = [("DIV0", 0x94E488, 4), ("MUL0", 0x94E5A8, 64), ("CAT0", 0x94EDA8, 64),
        ("MUL1", 0x950664, 64)] + [(t, a, 4) for t, a in WATCH]

TMPL = r"""set pagination off
set confirm off
set can-use-hw-watchpoints 1
@@WATCHES@@printf "ARMED @@N@@ hw watchpoints at @@ADDRS@@\n"
continue
"""

WBLOCK = r"""watch *(int *)@@A@@
commands
silent
printf "M94W @@T@@ pc=0x%x new=0x%x round=%d cp=%d\n", $pc, *(int *)@@A@@, *(int *)0x985afc, *(int *)0x985dcc
continue
end
"""

LINE = re.compile(r"^M94W (\w+) pc=(0x[0-9a-f]+) new=(0x[0-9a-f]+) round=(\d+) cp=(\d+)\s*$")


def gdb_script():
    blocks, addrs = [], []
    for tag, a in WATCH:
        addrs.append("%#x" % a)
        blocks.append(WBLOCK.replace("@@A@@", "%#x" % a).replace("@@T@@", tag))
    return (TMPL.replace("@@WATCHES@@", "".join(blocks))
                .replace("@@N@@", str(len(WATCH)))
                .replace("@@ADDRS@@", " ".join(addrs)))


def snap(m):
    out = {}
    for name, a, n in REGS:
        out[name] = M.rd(m, a, n)
    out["DIVS"] = [struct.unpack("<i", M.rd(m, 0x94E488 + f * STRIDE, 4))[0]
                   for f in range(8)]
    out["round"] = struct.unpack("<i", M.rd(m, ROUND_ADDR, 4))[0]
    return out


def load_funcs():
    rows = []
    with open(os.path.join(ROOT, "ghidra_out", "index.csv")) as fh:
        for r in csv.DictReader(fh):
            rows.append((int(r["addr"], 16), r["name"], int(r["size_bytes"])))
    rows.sort()
    return rows


def contain(pcs, funcs):
    starts = [a for a, _n, _s in funcs]
    out = {}
    for pc in pcs:
        i = bisect.bisect_right(starts, pc) - 1
        if i >= 0 and starts[i] <= pc < starts[i] + funcs[i][2]:
            out[pc] = funcs[i][1]
        else:
            out[pc] = None
    return out


def dis_window(pc):
    spec = importlib.util.spec_from_file_location("m71dis",
                                                  os.path.join(SCRATCH, "m71", "dis.py"))
    d = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(d)
    return d.dump(pc - 12, pc + 2, cap=8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boundaries", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--tag", default="m94table1")
    ap.add_argument("--poke-minerals", type=int, default=200)
    a = ap.parse_args()

    pid = M.find_pid()
    os.makedirs(SCRATCH, exist_ok=True)
    os.makedirs(EVID, exist_ok=True)
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        before = snap(m)
        row_addr = None
        n_bases = struct.unpack("<i", M.rd(m, 0x985AF4, 4))[0]
        for i in range(min(max(n_bases, 0), 64)):
            rec = M.rd(m, BASE_ARR + i * BASE_SZ, BASE_SZ)
            if rec[19:51].split(b"\0")[0].decode("latin-1", "replace") == BASE_NAME:
                row_addr = BASE_ARR + i * BASE_SZ
                break
    print(f"pid {pid} round {before['round']} base {BASE_NAME} addr "
          f"{'0x%x' % row_addr if row_addr else '??'}", flush=True)
    if row_addr is None:
        raise SystemExit(f"base {BASE_NAME!r} not found in the base array")
    print("divisors before: " + " ".join(str(v) for v in before["DIVS"]), flush=True)

    def poke_storage(value):
        with open(f"/proc/{pid}/mem", "rb+", 0) as mm:
            mm.seek(row_addr + 0x40)
            mm.write(struct.pack("<i", value))
            mm.seek(row_addr + 0x40)
            return struct.unpack("<i", mm.read(4))[0]

    print(f"  storage poked to {a.poke_minerals}, read back {poke_storage(a.poke_minerals)}",
          flush=True)

    gpath = os.path.join(SCRATCH, f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.gdblog")
    open(gpath, "w").write(gdb_script())
    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath,
                          "-p", str(pid)], stdout=log, stderr=subprocess.STDOUT)
    time.sleep(3.0)
    head = open(lpath, "r", errors="replace").read()
    n_hw = head.count("Hardware watchpoint")
    if "ARMED" not in head or n_hw < len(WATCH):
        try:
            os.kill(g.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
        subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
        raise SystemExit(f"gdb did not arm 4 HARDWARE watchpoints (saw {n_hw}):\n"
                         + head[-1200:])
    print(f"armed: {n_hw} hardware watchpoints on {[t for t, _ in WATCH]}", flush=True)

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
              f"{r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ''}",
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
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        after = snap(m)
    print("divisors after:  " + " ".join(str(v) for v in after["DIVS"]), flush=True)
    print(f"  after: round {after['round']} tracer {tracer}", flush=True)

    text = open(lpath, "r", errors="replace").read()
    ev = []
    armed = False
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        mm = LINE.match(ln)
        if mm:
            ev.append({"tag": mm.group(1), "pc": int(mm.group(2), 16),
                       "new": int(mm.group(3), 16), "round": int(mm.group(4)),
                       "cp": int(mm.group(5))})
            continue
        if not armed:
            if "ARMED" in ln:
                armed = True
            continue  # attach preamble: LWP/debuginfod banners are not events
        if ("Hardware watchpoint" in ln or ln.startswith("[Inferior")
                or ln.startswith("Thread 1") or "__kernel_vsyscall" in ln
                or re.match(r"0x[0-9a-f]+ in ", ln)):
            continue  # gdb noise: watchpoint banners, stop-location lines
        ev.append({"tag": "?", "raw": ln})
    with open(os.path.join(SCRATCH, f"{a.tag}_seq.jsonl"), "w") as fh:
        for d in ev:
            fh.write(json.dumps(d) + "\n")

    print(f"--- {len([e for e in ev if e['tag'] != '?'])} M94W events ---")
    for e in ev:
        if e["tag"] != "?":
            print(f"  {e['tag']} pc 0x{e['pc']:x} new 0x{e['new']:x} "
                  f"round {e['round']} cp {e['cp']}")
    unparsed = [e for e in ev if e["tag"] == "?"]

    # region movement vs events (instrument self-check; gates only WATCHed tags)
    moved, gaps = {}, []
    for name, addr, n in REGS:
        changed = before[name] != after[name]
        fired = any(e["tag"] == name for e in ev)
        moved[name] = (changed, fired)
        if any(t == name for t, _ in WATCH) and changed and not fired:
            gaps.append(name)
    print("movement: " + ", ".join(f"{k}: moved={v[0]} events={v[1]}"
                                   for k, v in moved.items()), flush=True)

    pcs = sorted({e["pc"] for e in ev if e["tag"] != "?"})
    funcs = load_funcs()
    names = contain(pcs, funcs)
    for pc in pcs:
        print(f"  writer pc 0x{pc:x} in {names[pc] or 'UNMAPPED'}")
        for ln in dis_window(pc):
            print("   ", ln.strip().split("\t", 1)[-1] if "\t" in ln else ln)

    r_before = before["round"]
    r_after = after["round"]
    n_ev = len([e for e in ev if e["tag"] != "?"])
    g1 = True  # armed (we did not raise)
    g2 = (rc_ok and r_after == r_before + a.boundaries)
    g3 = n_ev >= 1
    g4 = all(names[p] for p in pcs) and bool(pcs)
    moved_any = any(moved[t][0] for t, _ in WATCH)
    g5 = (not gaps) and (moved_any or n_ev > 0)
    g6 = all(after[t][:4] == struct.pack("<I", [e for e in ev if e["tag"] == t][-1]["new"])
             for t, _ in WATCH if any(e["tag"] == t for e in ev))
    g7 = tracer == "0"
    gates = [("G1_armed", g1), ("G2_boundary", g2), ("G3_events", g3),
             ("G4_mapped", g4), ("G5_discriminate", g5), ("G6_readback", g6),
             ("G7_clean", g7)]
    for n, v in gates:
        print(f"  {n}: {v}")
    ok = all(v for _n, v in gates) and not unparsed
    print(f"ACCEPTANCE {a.tag}: {'PASS' if ok else 'FAIL'} "
          f"({sum(1 for _n, v in gates if v)}/{len(gates)}) events={n_ev} "
          f"rounds {r_before}->{r_after} pcs={[hex(p) for p in pcs]} "
          f"writers={sorted({names[p] for p in pcs if names[p]})} gaps={gaps}",
          flush=True)


if __name__ == "__main__":
    main()
