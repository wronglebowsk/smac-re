#!/usr/bin/env python3
"""M90: the slot value is a TECHNOLOGY INDEX into the 89-entry table at 0x92fdd4 (stride 44, name at +16).

Chain, byte-backed (scratch/m71/dis.py + ghidra_out/shard_009.c:9288, shard_015.c:22025):
  FUN_005aa880(faction) --0x5aa9ac call--> FUN_005ab000(faction,0,-1,0) --0x5ab047 call-->
  FUN_0048b9a0(param_1=faction,0,-1,0), whose leg  `if ((param_2==0 && ((round==0 || !(0x985b10 &
  (1<<param_1))) || bVar14)) && param_3 < 0) { pcVar2 = FUN_005aa030(); ... return pcVar2; }`
  (shard_009.c:9359-9388) is the leg a NON-HUMAN faction takes (the human bit in ds:0x985b10 is set
  only for the player). FUN_0048b9a0's call site is 0x48bae4 `e8 47 e5 11 00 call 0x5aa030`, landing
  0x48bae9. FUN_005aa030(faction) loops `iVar4 < 0x59` (=89) over `(&DAT_0092fdd4)[iVar4*0xb]` =
  0x92fdd4 + index*44, scores candidates with FUN_005a90a0 / FUN_005a6cd0, tie-breaks with _rand,
  and returns the winning INDEX (or -1/-999 style markers). 5ab000 returns it verbatim (0x5ab04c
  `mov esi,eax` -> 0x5ab0bf `mov eax,esi`), 5aa880 stores it (0x5aa9b3 `mov ebx,eax` -> 0x5aa9d3).

SHAPE: poke one slot to -1, run boundaries under 8 PRINT-ONLY breakpoints, then read the chosen
index's NAME out of live memory (/proc at 0x92fdd4 + idx*44 + 16, 8 bytes) — the acceptance is the
name, not the number. A census snapshots a STOPPED engine, so names are read after the run from the
values the log recorded.

PREDICTIONS (printed before any counter is read):
  P1 the poke lands (slot == -1 read back from /proc);
  P2 the value the store prints equals FUN_005aa030's return, observed at its landing 0x48bae9 in the
     same call, with param_1 == the faction whose slot is written;
  P3 every such value is 0..88 and its 8-byte name field at 0x92fdd4+idx*44+16 is printable ASCII;
  P4 the slot reads back that value from /proc at or after that round (or a later logged -1 explains it).

Usage: python3 scripts/m90_tech_choice.py --tag m90tech1 [--poke-index 5] [--rounds 3] [--timeout 100]
"""
import argparse, csv, os, re, signal, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EVID = os.path.join(ROOT, "evidence")
STRIDE, SLOTB = 8380, 0x94D7FC
ROUND, YEAR, SAVE, MASK = 0x985AFC, 0x985B00, 0x920434, 0x985B10
TECHBASE, TECHN, TECHNAME = 0x92FDD4, 89, 16
CTRL, AAA, CONS = 0x51F320, 0x5AAA20, 0x5AAAC1
ENT, CHS, ST, RB = 0x5AA880, 0x5AA9B1, 0x5AA9D3, 0x5AA9D5
A030, TECH = 0x5AA030, 0x48BAE9

TMPL = r"""set pagination off
set confirm off
set height 0
set verbose off
set $n_ent = 0
set $n_chr = 0
set $n_st = 0
set $n_rb = 0
set $n_tech = 0
set $n_a0 = 0
set $n_cons = 0
set $n_ctrl = 0
set $ret = 0
set $fac = 0
set $chr = 0
set $idx = -999
printf "ARMED round=%d year=%d save=%d mask=%d\n", *(int *)0x985afc, *(int *)0x985b00, *(int *)0x920434, *(int *)0x985b10
break *0x5aa030
commands
silent
set $n_a0 = $n_a0 + 1
set $idx = -999
if $n_a0 < 10
printf "A030 n=%d arg1=%d ret=0x%x round=%d\n", $n_a0, *(int *)($esp+4), *(int *)$esp, *(int *)0x985afc
end
continue
end
break *0x48bae9
commands
silent
set $n_tech = $n_tech + 1
set $idx = $eax
if $n_tech < 10
printf "TECH n=%d idx=%d param1=%d ret=0x%x round=%d\n", $n_tech, $eax, *(int *)($ebp+8), *(int *)$esp, *(int *)0x985afc
end
continue
end
break *0x5aa880
commands
silent
set $n_ent = $n_ent + 1
set $ret = *(int *)$esp
set $fac = *(int *)($esp+4)
set $chr = -999
if $n_ent < 10
printf "ENT n=%d fac=%d ret=0x%x save=%d round=%d\n", $n_ent, $fac, $ret, *(int *)0x920434, *(int *)0x985afc
end
continue
end
break *0x5aa9b1
commands
silent
set $n_chr = $n_chr + 1
set $chr = $eax
if $n_chr < 10
printf "CHR n=%d eax=%d arg1=%d arg2=%d arg3=%d arg4=%d idx_from_5aa030=%d fac=%d\n", $n_chr, $eax, *(int *)$esp, *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+12), $idx, $edi
end
continue
end
break *0x5aa9d3
commands
silent
set $n_st = $n_st + 1
if $n_st < 10
printf "ST n=%d addr=0x%x val=%d chr=%d idx=%d ret=0x%x fac=%d round=%d\n", $n_st, $esi, $ebx, $chr, $idx, $ret, $fac, *(int *)0x985afc
end
continue
end
break *0x5aa9d5
commands
silent
set $n_rb = $n_rb + 1
if $n_rb < 10
printf "RB n=%d addr=0x%x mem=%d\n", $n_rb, $esi, *(int *)$esi
end
continue
end
break *0x5aaac1
commands
silent
set $n_cons = $n_cons + 1
if $n_cons < 10
printf "CONS n=%d addr=0x%x kind=%d band=%d round=%d\n", $n_cons, ($edi+0x94d7fc), $ebx, $esi, *(int *)0x985afc
end
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
    """The 8-byte name field of the domain entry: 0x92fdd4 + idx*44 + 16, read from live memory."""
    if idx is None or idx < 0 or idx >= TECHN:
        return None
    with open("/proc/%d/mem" % pid, "rb", 0) as f:
        f.seek(TECHBASE + idx * 44 + TECHNAME)
        raw = f.read(8)
    s = raw.split(bytes([0]))[0].decode("latin1")
    return s if s and all(32 <= ord(c) < 127 for c in s) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--poke-index", type=int, default=5)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=100)
    ap.add_argument("--settle", type=float, default=3.0)
    a = ap.parse_args()
    pid = pid_of()
    if not pid:
        raise SystemExit("no terran.exe")
    addr = slot_addr(a.poke_index)
    r0, y0 = mem(pid, ROUND), mem(pid, YEAR)
    slots0 = [mem(pid, slot_addr(i)) for i in range(8)]
    print(f"pid {pid} round={r0} year={y0} save={mem(pid, SAVE)} mask={mem(pid, MASK)} "
          f"watch={addr:#x} slots(0..7)={slots0}", flush=True)
    print("DOMAIN (first 6 of the 89 entries at 0x92fdd4 + i*44, name at +16):",
          [(i, tech_name(pid, i)) for i in range(6)], flush=True)
    print("PREDICTIONS: P1 poke lands; P2 store value == FUN_005aa030's return at its landing 0x48bae9 "
          "with param_1 == the faction written; P3 every value is 0..88 and its 8-byte name is printable "
          "ASCII; P4 the slot reads back that value from /proc at or after that round", flush=True)

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
    after_poke = mem(pid, addr)
    print(f"poke: slot({a.poke_index}) {slots0[a.poke_index]} -> {after_poke}", flush=True)

    snaps = [(r0, list(slots0))]
    seen = []
    for i in range(a.rounds):
        before = mem(pid, ROUND)
        r1 = subprocess.run([sys.executable, os.path.join(HERE, "m55_boundary.py"),
                             "--timeout", str(a.timeout), "--trace",
                             os.path.join(ROOT, "scratch", f"{a.tag}_bnd{i}.jsonl")],
                            capture_output=True, text=True, timeout=a.timeout + 60)
        time.sleep(a.settle)
        after = mem(pid, ROUND)
        cur = [mem(pid, slot_addr(j)) for j in range(8)]
        snaps.append((after, cur))
        txt = open(lpath, errors="replace").read()
        nst = len([1 for ln in txt.splitlines() if ln.startswith("ST ")])
        last = r1.stdout.strip().splitlines()[-1][:90] if r1.stdout.strip() else ""
        print(f"boundary {i+1}: round {before}->{after} slots={cur} stores={nst} rc={r1.returncode} {last}",
              flush=True)
        seen.append((i + 1, before, after, r1.returncode))
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
        if not p or p[0] not in ("A030", "TECH", "ENT", "CHR", "ST", "RB", "CONS", "CTRL"):
            continue
        kv = {k: int(v, 0) for k, v in re.findall(r"(\w+)=(-?0x[0-9a-f]+|-?\d+)", " ".join(p[1:]))}
        kv["_tag"] = p[0]
        events.append(kv)
    st = [e for e in events if e["_tag"] == "ST"]
    tech = [e for e in events if e["_tag"] == "TECH"]
    # the slice must be taken in EVENTS order: enumerating st gave the wrong offsets (m90tech1 G6)
    pos = {id(e): i for i, e in enumerate(events)}
    a0 = [e for e in events if e["_tag"] == "A030"]
    chr_ = [e for e in events if e["_tag"] == "CHR"]
    rb = [e for e in events if e["_tag"] == "RB"]
    cons = [e for e in events if e["_tag"] == "CONS"]
    ctrl = [e for e in events if e["_tag"] == "CTRL"]

    r1v = mem(pid, ROUND)
    slots1 = [mem(pid, slot_addr(j)) for j in range(8)]
    snaps.append((r1v + 1, slots1))

    print("ALLOCATIONS traced to the domain (name read from live memory at 0x92fdd4+idx*44+16):", flush=True)
    traced = []
    for idx_e, e in enumerate(st):
        val, fac, rnd = e.get("val"), e.get("fac"), e.get("round")
        nm = tech_name(pid, val)
        # the FUN_005aa030 return observed in this same call: the last TECH event before this store,
        # counted in EVENTS order (m90tech1 sliced st's own offsets, so t was always None)
        ei = pos[id(e)]
        t = next((x for x in reversed(events[:ei]) if x["_tag"] == "TECH"), None)
        agree = bool(t) and t.get("idx") == val and t.get("param1") == fac
        conf = False
        j = (e.get("addr") - SLOTB) // STRIDE if e.get("addr") else -1
        for sr, sl in snaps:
            if 0 <= j < 8 and sr >= (rnd if rnd is not None else 0) and sl[j] == val:
                conf = True
                break
        sup = [x["_tag"] for x in events[ei + 1:] if x.get("addr") == e.get("addr")][:3]
        traced.append((e, nm, agree, conf, sup))
        print(f"  {e.get('n')} fac={fac} val={val} name={nm!r} round={rnd} ret={hex(e.get('ret') or 0)} "
              f"aa030_return={None if not t else t.get('idx')} param1={None if not t else t.get('param1')} "
              f"agree={agree} proc_confirmed={conf} superseded={sup}", flush=True)
    if a0:
        print("FUN_005aa030 CALLS (arg1 = faction, ret = the landing inside FUN_0048b9a0):",
              [(x.get("n"), x.get("arg1"), hex(x.get("ret") or 0)) for x in a0], flush=True)
    if chr_:
        print("FUN_005ab000 RETURN landing (0x5aa9b1):",
              [(x.get("n"), x.get("eax"), (x.get("arg1"), x.get("arg2"), x.get("arg3"), x.get("arg4")),
                x.get("idx_from_5aa030")) for x in chr_], flush=True)
    if rb:
        print("INFERIOR READ-BACK (0x5aa9d5):", [(x.get("n"), hex(x.get("addr")), x.get("mem")) for x in rb],
              flush=True)
    if cons:
        print("CONS (aaa20 consumes the slot, kind = what it hands FUN_005a7970):",
              [(x.get("n"), hex(x.get("addr")), x.get("kind")) for x in cons], flush=True)

    res = {
        "G1_window_live": len(ctrl) >= 1 and r1v > r0,
        "G2_poke_landed": after_poke == -1,
        "G3_allocation_observed": len(st) >= 1,
        "G4_values_are_domain_indices": bool(st) and all(0 <= (e.get("val") or -1) < TECHN for e in st),
        "G5_every_value_named_from_memory": bool(traced) and all(nm for _, nm, _, _, _ in traced),
        "G6_value_is_the_aa030_return_for_that_faction": bool(traced) and all(ag for _, _, ag, _, _ in traced),
        "G7_readback_from_proc": bool(traced) and all((c or s) for _, _, _, c, s in traced),
        "G8_two_or_more_windows_traced": len({(e.get("round"), e.get("fac")) for e, _, _, _, _ in traced}) >= 2,
    }
    print("GATES:", flush=True)
    for k, v in res.items():
        print(f"  {'T' if v else 'F'} {k}", flush=True)
    ok = all(res.values())
    print("VERDICT %s tag=%s poke %d->%d allocs=%d named=%s tech_calls=%d a030_calls=%d ctrl=%d cons=%d "
          "round %d->%d slots(0..7)=%s detached=%s"
          % ("PASS" if ok else "FAIL", a.tag, slots0[a.poke_index], after_poke, len(st),
             [(e.get("val"), nm) for e, nm, _, _, _ in traced], len(tech), len(a0), len(ctrl), len(cons),
             r0, r1v, slots1, "detached]" in open(lpath, errors="replace").read()), flush=True)
    print("evidence:", lpath, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
