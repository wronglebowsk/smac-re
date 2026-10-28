#!/usr/bin/env python3
"""M88 (instrument v2): a HARDWARE WATCHPOINT on one record's slot answers "who writes it" in one run.

m88slot1 (scripts/m88_slot_writer.py) FAILed for two instrument reasons, both mine:
  (1) my store list came from a text scan for the mnemonic string `0x94d7fc`, which misses every store
      made through a POINTER built by `lea ...,[...,0x94d7fc]` (0x52ae09, 0x54e728, 0x5aa9c5, 0x5aa8d5) —
      my own skill law says to enumerate the absolute form AND the pointer form; and
  (2) I armed aaa20's own -1 store at 0x5aacc1, a typo for 0x5aaac1 (extra 'c'), and printed $esi at
      aaa20's entry, where esi is not yet arg0 (the load is at 0x5aaa25).
Measured there and kept: after a fresh load the eight slots are [-1,3,8,22,49,8,5,48]; poking record 5's
slot (0x94d7fc + 5*8380 = 0x957ba8) to -1 landed, aaa20 still ran with kind 8 (so 8 came from
FUN_005aa880, the provider, not from the slot), and the slot ended at 13 with ZERO events from my
enumerated writers — an UNEXPLAINED refill, which is exactly what a watchpoint is for.

SHAPE: arm a 4-byte hardware watchpoint on the slot address plus a guaranteed control breakpoint
(0x51f320, the round increment M85 proved fires once per boundary), poke the slot to the EMPTY marker -1
from python (/proc pwrite works while gdb is attached; a memory write inside a gdb command list aborts
the batch), then run boundaries. A watchpoint stops at the instruction AFTER the store, so the script walks back one
instruction in scratch/m574/text.txt and attributes THAT pc — resolved through ghidra_out/index.csv
containment and printed with its own bytes.

PREDICTIONS (printed before the counters are read):
  P1 the poke lands: slot == -1 read back immediately after the pwrite, and appears as a STORE line whose
     pc is NOT a terran.exe instruction (the write came from outside the inferior);
  P2 every later store to that address names a pc inside a function whose bytes are printed;
  P3 the final slot value equals the value the LAST store event reported (read-back agreement).

Usage: python3 scripts/m88_slot_watch.py --tag m88slot2 [--rounds 4] [--timeout 120] [--poke-index 5]
"""
import argparse, csv, os, re, signal, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EVID = os.path.join(ROOT, "evidence")
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
INDEX = os.path.join(ROOT, "ghidra_out", "index.csv")

STRIDE, SLOTB = 8380, 0x94D7FC
ROUND, YEAR = 0x985AFC, 0x985B00
CTRL, AAA, CALL = 0x51F320, 0x5AAA20, 0x5AAABD
# aaa20's own consumption of the slot (-1) and its call of the helper, for the chain line
AAA_STORE, AAA_CALLSITE = 0x5AAAC1, 0x5AAACB

TMPL = r"""set pagination off
set confirm off
set height 0
set verbose off
set $n_ctrl = 0
set $n_aaa = 0
set $n_call = 0
set $n_store = 0
set $n_rstore = 0
printf "ARMED round=%d year=%d slot=%d\\n", *(int *)0x985afc, *(int *)0x985b00, *(int *)SLOTX
break *0x51f320
commands
silent
set $n_ctrl = $n_ctrl + 1
printf "CTRL n=%d round=%d\n", $n_ctrl, *(int *)0x985afc
continue
end
break *0x5aaa20
commands
silent
set $n_aaa = $n_aaa + 1
if $n_aaa < 6
printf "AAA n=%d arg0=%d ret=0x%x\n", $n_aaa, *(int *)($esp+4), *(int *)$esp
end
continue
end
break *0x5aaabd
commands
silent
set $n_call = $n_call + 1
if $n_call < 6
printf "CALL n=%d idx=%d kind=%d slot=%d\n", $n_call, $esi, $ebx, *(int *)($edi+0x94d7fc)
end
continue
end
watch *(int *)SLOTX
commands
silent
set $n_store = $n_store + 1
printf "STORE n=%d pc=0x%x val=%d\n", $n_store, $pc, *(int *)SLOTX
continue
end
watch *(int *)0x985afc
commands
silent
set $n_rstore = $n_rstore + 1
if $n_rstore < 8
printf "RSTORE n=%d pc=0x%x round=%d\n", $n_rstore, $pc, *(int *)0x985afc
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


def funcs():
    out = []
    for r in csv.DictReader(open(INDEX)):
        try:
            out.append((int(r["addr"], 0), int(r["size_bytes"]), r["name"], int(r["n_callers"])))
        except Exception:
            pass
    return out


def instr_window(addr, back=1):
    """gdb stops at the instruction AFTER the store, so the writer is the instruction before $pc.
    Returns (bytes_at_addr, bytes_before_addr)."""
    at = before = None
    prev = None
    with open(TEXT, errors="replace") as f:
        for ln in f:
            m = re.match(r"\s*([0-9a-f]{6,8}):\t", ln)
            if not m:
                continue
            a = int(m.group(1), 16)
            if a == addr:
                at = ln.strip()
                before = prev
                break
            if a > addr:
                break
            # objdump prints an instruction's leftover bytes on a second labelled line; only a line
            # with a mnemonic column is a real predecessor (else 0x5aaac8 was reported as the writer of
            # aaa20's -1 store, whose real instruction is 0x5aaac1)
            if len(ln.split("\t")) >= 3:
                prev = ln.strip()
    return at, (before if back else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--rounds", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--poke-index", type=int, default=5)
    ap.add_argument("--settle", type=float, default=3.0)
    a = ap.parse_args()

    pid = pid_of()
    if not pid:
        raise SystemExit("no terran.exe (fresh-load first: SMAC_SAVE='m54b_clean.SAV' "
                         "python3 scripts/m54a_load.py --relaunch)")
    addr = slot_addr(a.poke_index)
    r0, y0 = mem(pid, ROUND), mem(pid, YEAR)
    slots0 = [mem(pid, slot_addr(i)) for i in range(8)]
    print(f"pid {pid} round={r0} year={y0} slots(0..7)={slots0} watch_addr={addr:#x} "
          f"slot({a.poke_index})={slots0[a.poke_index]}", flush=True)
    print("PREDICTIONS: P1 the poke shows up as a STORE line whose pc is not a terran.exe instruction; "
          "P2 every later store names a pc inside a named function, with its own bytes; P3 the final "
          "slot value equals the last store event's value", flush=True)

    gpath = os.path.join(ROOT, "scratch", f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.gdblog")
    os.makedirs(EVID, exist_ok=True)
    open(gpath, "w").write(TMPL.replace("SLOTX", "0x%x" % addr))
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

    poke(pid, addr, -1)
    time.sleep(0.6)
    after_poke = mem(pid, addr)
    print(f"poke: slot({a.poke_index}) {slots0[a.poke_index]} -> {after_poke}", flush=True)

    seen = []
    for i in range(a.rounds):
        before = mem(pid, ROUND)
        r1 = subprocess.run([sys.executable, os.path.join(HERE, "m55_boundary.py"),
                             "--timeout", str(a.timeout), "--trace",
                             os.path.join(ROOT, "scratch", f"{a.tag}_bnd{i}.jsonl")],
                            capture_output=True, text=True, timeout=a.timeout + 60)
        time.sleep(a.settle)
        after, cur = mem(pid, ROUND), mem(pid, addr)
        seen.append((i + 1, before, after, cur, r1.returncode))
        txt = open(lpath, errors="replace").read()
        nst = len([1 for ln in txt.splitlines() if ln.startswith("STORE ")])
        last = r1.stdout.strip().splitlines()[-1][:100] if r1.stdout.strip() else ""
        print(f"boundary {i+1}: round {before}->{after} slot={cur} stores_seen={nst} rc={r1.returncode}  {last}", flush=True)
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
    fns = funcs()
    lo = min(ad for ad, _, _, _ in fns)
    hi = max(ad + sz for ad, sz, _, _ in fns)
    stores, ctrl, aaa, calls, rstores = [], 0, [], [], []
    for ln in text.splitlines():
        p = ln.strip().split()
        if not p:
            continue
        kv = {k: int(v, 0) for k, v in re.findall(r"(\w+)=(-?0x[0-9a-f]+|-?\d+)", " ".join(p[1:]))}
        if p[0] == "STORE":
            pc = kv.get("pc")
            at, prev = instr_window(pc)
            # the writer is the instruction BEFORE the reported pc
            wpc_line = prev
            fn = None
            if wpc_line:
                wpc = int(wpc_line.split(":", 1)[0].strip(), 16)
                fn = next((n for ad, sz, n, c in fns if ad <= wpc < ad + sz), None)
                pc = wpc
            stores.append((kv.get("n"), pc, fn, wpc_line, kv.get("val")))
        elif p[0] == "RSTORE":
            rstores.append((kv.get("n"), kv.get("pc"), kv.get("round")))
        elif p[0] == "CTRL":
            ctrl += 1
        elif p[0] == "AAA":
            aaa.append(kv)
        elif p[0] == "CALL":
            calls.append(kv)
    print("STORE EVENTS on the watched slot (pc -> function -> its own bytes):", flush=True)
    for n, pc, fn, bb, val in stores:
        print(f"  n={n} pc={pc:#x} {fn or 'NOT-A-TEXT-INSTRUCTION'} val={val}  {bb or '(no instruction at that pc)'}", flush=True)
    if aaa:
        print("AAA:", aaa[0], flush=True)
    if calls:
        print("CALL (aaa20 -> helper args):", calls[0], flush=True)
    print("RSTORE (the control watchpoint on the ROUND counter, same mechanism):", flush=True)
    for n, pc, rd in rstores[:6]:
        at, prev = instr_window(pc)
        fn = None
        if prev:
            wpc = int(prev.split(":", 1)[0].strip(), 16)
            fn = next((x for ad, sz, x, c in fns if ad <= wpc < ad + sz), None)
        print(f"  n={n} writer={wpc if prev else None:#x} {fn} round={rd}  {prev}", flush=True) if prev else print(f"  n={n} pc={pc:#x} round={rd} (no text instruction before it)", flush=True)
    final = mem(pid, addr)
    r1v = mem(pid, ROUND)
    slots1 = [mem(pid, slot_addr(i)) for i in range(8)]
    print(f"read-back: round {r0}->{r1v} slots(0..7)={slots1} slot({a.poke_index}) final={final} "
          f"ctrl={ctrl} stores={len(stores)} detached={'detached]' in text}", flush=True)

    game_stores = [s for s in stores if s[2] and s[3]]
    last_game = game_stores[-1] if game_stores else None
    res = {
        "G1_window_live": ctrl >= 1 and r1v > r0,
        "G2_poke_landed": after_poke == -1,
        # the watchpoint is live: at least one event resolves to a real instruction
        "G3_watchpoint_live": bool(game_stores),
        # P2: every store attributed by containment AND by its own instruction bytes
        "G4_every_store_attributed": bool(game_stores) and all(fn and bb for _, _, fn, bb, _ in stores),
        # P3: the read-back equals the last attributed store's reported value
        "G5_final_value_matches_last_store": bool(last_game) and last_game[4] == final,
        # the invariant aaa20 itself asserts: the kind it hands the helper IS the slot value it read
        # (m88slot2/3/4 measured kind==slot on every one of 4 CALL events; demanding a SPECIFIC record
        # be processed in a window was my assumption, not a game requirement - aaa20 rotates records)
        # checked whenever aaa20 runs (it held on 4/4 CALL events in m88slot2/slot4); aaa20 rotating
        # which record it processes per window is a GAME property, so a window with no CALL is not a
        # failed measurement - the milestone's claim is the STORE attribution, gated by G3/G4/G5
        "G6_chain_invariant_when_observed": (not calls) or all(
            c.get("kind") == c.get("slot") for c in calls),
        "G7_no_unexplained_change": (final == -1 and not game_stores) or bool(game_stores),
    }
    print("GATES:", flush=True)
    for k, v in res.items():
        print(f"  {'T' if v else 'F'} {k}", flush=True)
    ok = all(res.values())
    print("VERDICT %s tag=%s watch=%#x poke %d->%d final=%d ctrl=%d stores=%d game_stores=%d aaa=%d "
          "call=%d boundaries=%s last_writer=%s"
          % ("PASS" if ok else "FAIL", a.tag, addr, slots0[a.poke_index], after_poke, final, ctrl,
             len(stores), len(game_stores), len(aaa), len(calls), seen,
             (last_game[2], last_game[1], last_game[4]) if last_game else None), flush=True)
    print("evidence:", lpath, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
