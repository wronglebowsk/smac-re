#!/usr/bin/env python3
"""M88: who writes the per-record slot [0x94d7fc + idx*8380] (the kind FUN_005aaa20 then hands FUN_005a7970)?

THE STATIC MAP (scratch/m71/dis.py windows over scratch/m574/text.txt, this session):
  The record array has stride 8380 = 0x20BC bytes; aaa20's edi = arg0*8380 (0x5aaa2d-0x5aaa45) and
  FUN_004f34b0's ecx = ebx*8380 (0x4f351c-0x4f352b), so aaa20's arg0 is a RECORD INDEX, and the slot is
  the dword at record offset 0x94d7fc - 0x94d6a4 = 344. FUN_004f34b0 (298 B, one caller 0x4f5c2e inside
  FUN_004f5a70) ends with `push edx; push ebx; call 0x5aadf0` (0x4f35c9-0x4f35cb) after gating on
  `test DWORD ds:0x985ac4, 0x4000000` (0x4f34b6) — so the chain is FUN_004f5a70 -> FUN_004f34b0 ->
  FUN_005aadf0 -> FUN_005aaa20 -> FUN_005a7970.
  Stores to the slot (whole-.text scan of `0x94d7fc`, 47 hits; the non-(-1) ones):
    0x51038c  mov DWORD PTR [esi+0x94d7fc],ecx   inside FUN_005102f0 (177 B, 3 callers): it calls
            0x5ab000(edi) at 0x51035f, and stores the returned value when the slot was < 0 or equal;
    0x59cfce  mov DWORD PTR [esi+0x94d7fc],eax   inside FUN_0059ce10 (5292 B, 1 caller) — the same
            function that calls aaa20 at 0x59cfd4.
  Stores of -1 (the EMPTY marker): 0x59cffe, 0x59f23c, 0x5a7db2 (inside FUN_005a7970), 0x5aaac1 (aaa20
  consuming it) — so a -1 read-back is also a measurable event, not an absence.

THE EXPERIMENT (one variable, a controlled poke): live before arming, record 5's slot held 32 (the census
of M87 consumed its 8 and wrote -1, so SOMETHING refilled it between the runs). This script pokes record
5's slot to -1 while gdb is attached (the s135 law: python /proc pwrite works under a tracer; a memory
write inside a gdb command list aborts the batch), then runs boundaries and reads the slot back.

PREDICTIONS (printed before the counters are read):
  P1 the poke lands: slot(5) == -1 immediately after the pwrite;
  P2 if a writer refills it during the window, the refill value equals the value a W1/W2 event prints for
     esi == 5*8380 (attribution by printed store pc + its own instruction bytes);
  P3 if NO writer event names record 5 across >= 2 boundaries and the slot is still -1, the kind is NOT
     re-queued per boundary — the value seen after a fresh load comes from the load path, not the sim.
Exactly one of P2/P3 may be true; the gate FAILs on a contradiction (a new value with no event, or an
event whose value disagrees with the read-back).

Usage: python3 scripts/m88_slot_writer.py --tag m88slot1 [--rounds 3] [--timeout 120] [--poke-index 5]
"""
import argparse, csv, os, re, signal, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EVID = os.path.join(ROOT, "evidence")
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
INDEX = os.path.join(ROOT, "ghidra_out", "index.csv")

STRIDE, SLOTB = 8380, 0x94D7FC
ROUND, YEAR = 0x985AFC, 0x985B00
SITES = [
    ("W1",   0x51038C, "mov [esi+0x94d7fc],ecx in FUN_005102f0 — ecx is 0x5ab000's return value"),
    ("W2",   0x59CFCE, "mov [esi+0x94d7fc],eax in FUN_0059ce10 (the same function calls aaa20 at 0x59cfd4)"),
    ("CLR2", 0x5AACC1, "aaa20's own store of -1 into the slot, just before it calls the helper"),
    ("CLR3", 0x5A7DB2, "FUN_005a7970 stores -1 into a slot it matched on (0x5a7daa cmp)"),
    ("AAA",  0x5AAA20, "aaa20 entered: a0 = record index, ret names its caller"),
    ("CALL", 0x5AAABD, "aaa20 about to call the helper: esi = index, ebx = the kind it read"),
    ("CTRL", 0x51F320, "the round increment — M85 proved this fires once per boundary, so it proves the window was live"),
]
STORE_BYTES = [0x51038C, 0x59CFCE, 0x5AACC1, 0x5A7DB2, 0x4F35CB]
PRINTS = {
    "W1":   'printf "W1 n=%d off=%d idx=%d val=%d slot_now=%d\\n", $n_w1, $esi, $esi/8380, $ecx, *(int *)($esi+0x94d7fc)',
    "W2":   'printf "W2 n=%d off=%d idx=%d val=%d slot_now=%d\\n", $n_w2, $esi, $esi/8380, $eax, *(int *)($esi+0x94d7fc)',
    "CLR2": 'printf "CLR2 n=%d off=%d idx=%d slot_now=%d\\n", $n_clr2, $edi, $edi/8380, *(int *)($edi+0x94d7fc)',
    "CLR3": 'printf "CLR3 n=%d off=%d idx=%d slot_now=%d ebx=%d\\n", $n_clr3, $edx, $edx/8380, *(int *)($edx+0x94d7fc), $ebx',
    "AAA":  'printf "AAA n=%d idx=%d ret=0x%x\\n", $n_aaa, $esi, *(int *)$esp',
    "CALL": 'printf "CALL n=%d idx=%d kind=%d\\n", $n_call, $esi, $ebx',
    "CTRL": 'printf "CTRL n=%d round=%d\\n", $n_ctrl, *(int *)0x985afc',
}
TMPL = ("set pagination off\nset confirm off\nset height 0\nset verbose off\n"
        + "".join("set $n_%s = 0\n" % t.lower() for t, _, _ in SITES)
        + 'printf "ARMED round=%d year=%d slot0=%d slot1=%d slot2=%d slot3=%d slot4=%d slot5=%d slot6=%d slot7=%d\\n", '
          '*(int *)0x985afc, *(int *)0x985b00, *(int *)0x94d7fc, *(int *)(0x94d7fc+8380), '
          '*(int *)(0x94d7fc+8380*2), *(int *)(0x94d7fc+8380*3), *(int *)(0x94d7fc+8380*4), '
          '*(int *)(0x94d7fc+8380*5), *(int *)(0x94d7fc+8380*6), *(int *)(0x94d7fc+8380*7)\n'
        + "".join("break *0x%x\ncommands\nsilent\nset $n_%s = $n_%s + 1\nif $n_%s < 6\n%s\nend\ncontinue\nend\n"
                  % (a, t.lower(), t.lower(), t.lower(), PRINTS[t]) for t, a, _ in SITES)
        + "continue\n")


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


def parse(text):
    known = {t for t, _, _ in SITES}
    ev = []
    for ln in text.splitlines():
        p = ln.strip().split()
        if len(p) >= 2 and p[0] in known:
            ev.append((p[0], {k: int(v, 0) for k, v in re.findall(r"(\w+)=(-?0x[0-9a-f]+|-?\d+)", " ".join(p[1:]))}))
    return ev


def funcs():
    out = []
    for r in csv.DictReader(open(INDEX)):
        try:
            out.append((int(r["addr"], 0), int(r["size_bytes"]), r["name"], int(r["n_callers"])))
        except Exception:
            pass
    return out


def instr_bytes(addr):
    with open(TEXT, errors="replace") as f:
        for ln in f:
            m = re.match(r"\s*([0-9a-f]{6,8}):\t", ln)
            if not m:
                continue
            a = int(m.group(1), 16)
            if a == addr:
                return ln.strip()
            if a > addr:
                break
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--poke-index", type=int, default=5)
    ap.add_argument("--settle", type=float, default=3.0)
    a = ap.parse_args()

    pid = pid_of()
    if not pid:
        raise SystemExit("no terran.exe (fresh-load first: SMAC_SAVE='m54b_clean.SAV' "
                         "python3 scripts/m54a_load.py --relaunch)")
    r0, y0 = mem(pid, ROUND), mem(pid, YEAR)
    slots0 = [mem(pid, slot_addr(i)) for i in range(8)]
    print(f"pid {pid} round={r0} year={y0} slots(0..7)={slots0}", flush=True)
    print(f"PREDICTIONS: P1 slot({a.poke_index}) becomes -1 on the poke; P2 a refill value must equal a "
          f"W1/W2 event with idx=={a.poke_index}; P3 else slot==-1 after >=2 boundaries with zero "
          f"idx events -> the kind is load-held, not re-queued", flush=True)

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
        raise SystemExit("gdb did not arm:\n" + head[-800:])
    print([l for l in head.splitlines() if l.startswith("ARMED")][0], flush=True)

    # THE ONE VARIABLE: poke the slot to the EMPTY marker while gdb is attached.
    addr = slot_addr(a.poke_index)
    poke(pid, addr, -1)
    time.sleep(0.4)
    after_poke = mem(pid, addr)
    print(f"poke: slot({a.poke_index}) {slots0[a.poke_index]} -> {after_poke} at {addr:#x}", flush=True)

    seen = []
    for i in range(a.rounds):
        before = mem(pid, ROUND)
        r1 = subprocess.run([sys.executable, os.path.join(HERE, "m55_boundary.py"),
                             "--timeout", str(a.timeout), "--trace",
                             os.path.join(ROOT, "scratch", f"{a.tag}_bnd{i}.jsonl")],
                            capture_output=True, text=True, timeout=a.timeout + 60)
        time.sleep(a.settle)
        after = mem(pid, ROUND)
        cur = mem(pid, addr)
        seen.append((i + 1, before, after, cur, r1.returncode))
        txt = open(lpath, errors="replace").read()
        n5 = sum(1 for t, d in parse(txt) if t in ("W1", "W2") and d.get("idx") == a.poke_index)
        last = r1.stdout.strip().splitlines()[-1][:100] if r1.stdout.strip() else ""
        print(f"boundary {i+1}: round {before}->{after} slot({a.poke_index})={cur} idx_events={n5} rc={r1.returncode}  {last}", flush=True)
        if n5:
            break
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

    text = open(lpath, errors="replace").read()
    ev = parse(text)
    cnt = {}
    for t, _ in ev:
        cnt[t] = cnt.get(t, 0) + 1
    print("EVENT COUNTS:", {t: cnt.get(t, 0) for t, _, _ in SITES}, flush=True)
    writers = [d for t, d in ev if t in ("W1", "W2", "CLR2", "CLR3")]
    fns = funcs()
    print("WRITER EVENTS (store pc -> function, and the store's own bytes):", flush=True)
    named = {}
    for t, _, _ in SITES:
        for tt, d in ev:
            if tt == t:
                print(f"  {t} {d}  ({SITES[[x[0] for x in SITES].index(t)][2]})", flush=True)
                break
    for pc in STORE_BYTES:
        bb = instr_bytes(pc)
        fn = next((n for ad, sz, n, c in fns if ad <= pc < ad + sz), None)
        named[pc] = (fn, bb)
        print(f"  {pc:06x} {fn}  {bb}", flush=True)
    slots1 = [mem(pid, slot_addr(i)) for i in range(8)]
    r1v = mem(pid, ROUND)
    final_slot = mem(pid, addr)
    print(f"read-back: round {r0}->{r1v} slots(0..7)={slots1} slot({a.poke_index}) final={final_slot} "
          f"detached={'detached]' in text}", flush=True)

    idx_events = [d for t, d in ev if t in ("W1", "W2") and d.get("idx") == a.poke_index]
    clr_events = [d for t, d in ev if t in ("CLR2", "CLR3") and d.get("idx") == a.poke_index]
    boundaries_run = sum(1 for _, b, af, _, _ in seen if af > b)
    refilled = final_slot not in (-1,) and final_slot != after_poke
    attributed = bool(idx_events) and any(d.get("val") == final_slot for d in idx_events)
    res = {
        "G1_window_live": cnt.get("CTRL", 0) >= 1 and r1v > r0,
        "G2_poke_landed": after_poke == -1,
        # either the refill is attributed to a printed store of that exact value, ...
        "G3_refill_attributed_or_empty": (attributed if refilled else
                                          (final_slot == -1 and boundaries_run >= 2 and not idx_events)),
        "G4_no_unexplained_change": (not refilled) or attributed,
        # every writer pc in the design is named by containment AND by its own instruction bytes
        "G5_stores_named_by_bytes": all(named.get(pc, (None, None))[0] and named.get(pc, (None, None))[1]
                                        for pc in STORE_BYTES),
        # a -1 written by aaa20/the helper is itself an event, never an absence
        "G6_clear_events_consistent": (final_slot != -1) or (len(clr_events) >= 1 or final_slot == after_poke),
        "G7_other_slots_unchanged_or_explained": all(
            slots1[i] == slots0[i] or any(d.get("idx") == i for d in writers)
            for i in range(8) if i != a.poke_index),
    }
    print("GATES:", flush=True)
    for k, v in res.items():
        print(f"  {'T' if v else 'F'} {k}", flush=True)
    ok = all(res.values())
    outcome = ("RE-QUEUED and attributed" if attributed else
               ("LOAD-HELD (no writer event for the poked record)" if not refilled else "UNEXPLAINED"))
    print("VERDICT %s tag=%s poke_idx=%d poke %d->%d final=%d boundaries=%s ctrl=%d w1=%d w2=%d "
          "clr2=%d clr3=%d aaa=%d call=%d idx_events=%d outcome=%s"
          % ("PASS" if ok else "FAIL", a.tag, a.poke_index, slots0[a.poke_index], after_poke,
             final_slot, seen, cnt.get("CTRL", 0), cnt.get("W1", 0), cnt.get("W2", 0),
             cnt.get("CLR2", 0), cnt.get("CLR3", 0), cnt.get("AAA", 0), cnt.get("CALL", 0),
             len(idx_events), outcome), flush=True)
    print("evidence:", lpath, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
