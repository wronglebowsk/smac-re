#!/usr/bin/env python3
"""M89: what value does FUN_005aa880 put in the per-faction slot, and WHICH CALLER asked for it?

M88 proved the store: 0x5aa9d3 `89 1e mov [esi],ebx`, esi built at 0x5aa9c5 by
`lea esi,[eax*4+0x94d7fc]` (eax = faction*2095, so the slot byte address is 0x94d7fc + faction*8380).
This census answers the two open halves:

(a) WHERE THE VALUE COMES FROM. Static, byte-backed (scratch/m71/dis.py windows): the function's first
    branch is 0x5aa883 `a1 34 04 92 00 mov eax,ds:0x920434` / 0x5aa892 `je 0x5aa9a5`, so on a solo box
    (that flag reads 0) it takes 0x5aa9a5: `push 0; push -1; push 0; push edi; call 0x5ab000` at 0x5aa9ac
    -> 0x5aa9b1 `mov edx,edi` / 0x5aa9b3 `mov ebx,eax` -> the stored ebx IS FUN_005ab000's return value.
    The census therefore prints the chooser's return AND its four args, and gates store == return.
(b) WHO ASKED. The return address at entry ([esp]) names the caller's call site. The four sites, each
    verified from its own bytes in scratch/m574/text.txt: 0x52132f (FUN_00521070 stage 3, the MP driver)
    -> ret 0x521334; 0x5aaaab (FUN_005aaa20, the slot<0 allocate leg, 0x5aaab0 `mov ebx,eax`) -> ret
    0x5aaab0; 0x5aab58 (FUN_005aaa20 again, just before its own store 0x5aab60) -> ret 0x5aab5d;
    0x5aafee (FUN_005aadf0) -> ret 0x5aaff3.

SHAPE: poke one slot to the EMPTY marker -1 from python (/proc pwrite works while gdb is attached; a
memory write inside a gdb command list aborts the batch), then run boundaries with m55_boundary.py under
8 PRINT-ONLY breakpoints. gdb convenience variables carry the caller's return site and the chooser's
return from the entry/chooser stop to the store stop, so each allocation is a single ordered event.
Read-back is /proc, per boundary and at the end; a value that a LATER logged event legitimately overwrote
(a20's consumption at 0x5aaac1 stores -1) counts as explained, not as a miss.

PREDICTIONS (printed before any counter is read):
  P1 the poke lands: the slot reads -1 from /proc right after the pwrite;
  P2 every allocation is a store whose entry-printed return site is one of the four verified call sites,
     and NO allocation comes from 0x521334 (M85 proved FUN_00521070, the MP driver, has 0 solo visits);
  P3 the stored value equals FUN_005ab000's return in the SAME call (the convenience var is cleared at
     entry, so a stale carry-over reads as -999, not as a match);
  P4 the slot address the store used reads back the stored value from /proc at some point at or after
     that round, unless a later logged event to the same address explains the difference.

Usage: python3 scripts/m89_alloc_census.py --tag m89alloc1 [--poke-index 5] [--rounds 4] [--timeout 120]
"""
import argparse, csv, os, re, signal, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EVID = os.path.join(ROOT, "evidence")
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
INDEX = os.path.join(ROOT, "ghidra_out", "index.csv")

STRIDE, SLOTB = 8380, 0x94D7FC
ROUND, YEAR, SAVE = 0x985AFC, 0x985B00, 0x920434
CTRL, AAA, CONS, A2ST = 0x51F320, 0x5AAA20, 0x5AAAC1, 0x5AAB60
ENT, CHR, ST, RB = 0x5AA880, 0x5AA9B1, 0x5AA9D3, 0x5AA9D5

# ret -> (call site, verified bytes, container). Bytes are re-read from text.txt at parse time.
SITES = {
    0x521334: (0x52132F, "e8 4c 95 08 00", "FUN_00521070 (MP 7-stage driver, stage 3)"),
    0x5AAAB0: (0x5AAAAB, "e8 d0 fd ff ff", "FUN_005aaa20 (slot<0 allocate leg; 0x5aaab0 mov ebx,eax)"),
    0x5AAB5D: (0x5AAB58, "e8 23 fd ff ff", "FUN_005aaa20 (second call, before its own store 0x5aab60)"),
    0x5AAFF3: (0x5AAFEE, "e8 8d f8 ff ff", "FUN_005aadf0 (before its slot read at 0x5aaf07)"),
}

TMPL = r"""set pagination off
set confirm off
set height 0
set verbose off
set $n_ent = 0
set $n_chr = 0
set $n_st = 0
set $n_rb = 0
set $n_cons = 0
set $n_a2 = 0
set $n_ctrl = 0
set $n_aaa = 0
set $ret = 0
set $fac = 0
set $chr = 0
printf "ARMED round=%d year=%d save=%d\n", *(int *)0x985afc, *(int *)0x985b00, *(int *)0x920434
break *0x5aaa20
commands
silent
set $n_aaa = $n_aaa + 1
if $n_aaa < 10
printf "AAA n=%d arg0=%d ret=0x%x round=%d\n", $n_aaa, *(int *)($esp+4), *(int *)$esp, *(int *)0x985afc
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
printf "CHR n=%d eax=%d arg1=%d arg2=%d arg3=%d arg4=%d fac=%d\n", $n_chr, $eax, *(int *)$esp, *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+12), $edi
end
continue
end
break *0x5aa9d3
commands
silent
set $n_st = $n_st + 1
if $n_st < 10
printf "ST n=%d addr=0x%x val=%d chr=%d ret=0x%x fac=%d round=%d\n", $n_st, $esi, $ebx, $chr, $ret, $fac, *(int *)0x985afc
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
break *0x5aab60
commands
silent
set $n_a2 = $n_a2 + 1
if $n_a2 < 10
printf "A2ST n=%d addr=0x%x val=%d round=%d\n", $n_a2, ($edi+0x94d7fc), $eax, *(int *)0x985afc
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


def funcs():
    out = []
    for r in csv.DictReader(open(INDEX)):
        try:
            out.append((int(r["addr"], 0), int(r["size_bytes"]), r["name"], int(r["n_callers"])))
        except Exception:
            pass
    return out


def site_line(addr):
    """The objdump line AT this address (exact), for the call-site bytes. Only a line matching
    `<hex6+>:\t` is an instruction line (the `.text` section header is `00401000 <.text>:`)."""
    want = "%x:" % addr
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
    ap.add_argument("--poke-index", type=int, default=5)
    ap.add_argument("--rounds", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--settle", type=float, default=3.0)
    a = ap.parse_args()

    pid = pid_of()
    if not pid:
        raise SystemExit("no terran.exe (fresh load: SMAC_SAVE='m54b_clean.SAV' "
                         "python3 scripts/m54a_load.py --relaunch)")
    addr = slot_addr(a.poke_index)
    r0, y0 = mem(pid, ROUND), mem(pid, YEAR)
    slots0 = [mem(pid, slot_addr(i)) for i in range(8)]
    print(f"pid {pid} round={r0} year={y0} save={mem(pid, SAVE)} watch_addr={addr:#x} "
          f"slots(0..7)={slots0}", flush=True)
    print("SITES (ret -> call site, bytes re-read from text.txt at parse time):", flush=True)
    for ret, (site, want, who) in sorted(SITES.items()):
        ln = site_line(site)
        print(f"  ret={ret:#x} site={site:#x} want[{want}] {'OK' if ln and want in ln else 'MISSING'}  {ln}",
              flush=True)
    print("PREDICTIONS: P1 poke lands (slot == -1); P2 every allocation's entry return site is one of "
          "the four above and NONE comes from 0x521334 (MP driver, 0 solo visits per M85); P3 stored "
          "value == FUN_005ab000's return in the same call (chr cleared to -999 at entry); P4 the slot "
          "reads back the stored value from /proc at or after that round unless a later logged event to "
          "the same address explains the change", flush=True)

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
        last = r1.stdout.strip().splitlines()[-1][:100] if r1.stdout.strip() else ""
        print(f"boundary {i+1}: round {before}->{after} slots={cur} stores_seen={nst} "
              f"rc={r1.returncode}  {last}", flush=True)
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

    text = open(lpath, errors="replace").read()
    events = []
    for ln in text.splitlines():
        p = ln.strip().split()
        if not p or p[0] not in ("AAA", "ENT", "CHR", "ST", "RB", "CONS", "A2ST", "CTRL"):
            continue
        kv = {k: int(v, 0) for k, v in re.findall(r"(\w+)=(-?0x[0-9a-f]+|-?\d+)", " ".join(p[1:]))}
        kv["_tag"] = p[0]
        events.append(kv)
    st = [e for e in events if e["_tag"] == "ST"]
    chr_ = [e for e in events if e["_tag"] == "CHR"]
    rb = [e for e in events if e["_tag"] == "RB"]
    cons = [e for e in events if e["_tag"] == "CONS"]
    a2 = [e for e in events if e["_tag"] == "A2ST"]
    ctrl = [e for e in events if e["_tag"] == "CTRL"]
    aaa = [e for e in events if e["_tag"] == "AAA"]

    fns = funcs()
    print("ALLOCATIONS (store -> caller by its own return-site bytes):", flush=True)
    attrib = []
    for e in st:
        ret = e.get("ret")
        site, want, who = SITES.get(ret, (None, None, "UNKNOWN-CALLER"))
        ln = site_line(site) if site else None
        verified = bool(ln and want in ln)
        fn = next((n for ad, sz, n, c in fns if ad <= (site or 0) < ad + sz), None)
        attrib.append((e, ret, site, verified, fn))
        print(f"  {e.get('n')} addr={e.get('addr'):#x} val={e.get('val')} chr={e.get('chr')} "
              f"fac={e.get('fac')} round={e.get('round')} ret={ret if ret is None else hex(ret)} "
              f"site={site if site is None else hex(site)} verified={verified} container={fn}  {ln}",
              flush=True)
    if chr_:
        print("CHOOSER (FUN_005ab000 return + its args):", flush=True)
        for e in chr_:
            print(f"  {e.get('n')} eax={e.get('eax')} args=({e.get('arg1')},{e.get('arg2')},{e.get('arg3')},"
                  f"{e.get('arg4')}) fac={e.get('fac')}", flush=True)
    if rb:
        print("INFERIOR READ-BACK at 0x5aa9d5 (right after the store):",
              [(e.get('n'), hex(e.get('addr')), e.get('mem')) for e in rb], flush=True)
    if cons:
        print("CONS (aaa20's own -1 at 0x5aaac1; kind = what it hands the helper):",
              [(e.get('n'), hex(e.get('addr')), e.get('kind'), e.get('band')) for e in cons], flush=True)
    if a2:
        print("A2ST (aaa20's own store at 0x5aab60):",
              [(e.get('n'), hex(e.get('addr')), e.get('val')) for e in a2], flush=True)
    per_site = {}
    for e, ret, site, v, fn in attrib:
        per_site[hex(ret) if ret is not None else "?"] = per_site.get(hex(ret) if ret else "?", 0) + 1

    r1v = mem(pid, ROUND)
    slots1 = [mem(pid, slot_addr(j)) for j in range(8)]
    snaps.append((r1v + 1, slots1))  # the end-of-run snapshot is after every event

    # P4: each allocation is confirmed by a /proc read at or after its round, or explained by a later
    # logged write to the same address (aaa20's -1 consumption, or a newer allocation).
    later = []
    for idx, e in enumerate(st):
        ad, val, rnd = e.get("addr"), e.get("val"), e.get("round")
        conf = False
        for sr, sl in snaps:
            if sr is None:
                continue
            try:
                j = (ad - SLOTB) // STRIDE
            except TypeError:
                j = -1
            if 0 <= j < 8 and sr >= (rnd if rnd is not None else 0) and sl[j] == val:
                conf = True
                break
        sup = [x for x in events[idx + 1:] if x.get("addr") == ad]
        later.append((ad, val, rnd, conf, bool(sup), [x["_tag"] for x in sup][:3]))

    res = {
        "G1_window_live": len(ctrl) >= 1 and r1v > r0,
        "G2_poke_landed": after_poke == -1,
        "G3_allocation_observed": len(st) >= 1,
        "G4_every_alloc_attributed_by_return_site_bytes": bool(st) and all(v for _, _, _, v, _ in attrib),
        "G5_value_is_the_chooser_return": bool(st) and all(e.get("chr") == e.get("val") for e in st),
        "G6_readback_from_proc": bool(later) and all(c or s for _, _, _, c, s, _ in later),
        "G7_mp_site_never_allocates": all(e.get("ret") != 0x521334 for e in st),
        "G8_inferior_readback_agrees": bool(rb) and all(
            any(r.get("addr") == e.get("addr") and r.get("mem") == e.get("val") for r in rb) for e in st),
    }
    print("GATES:", flush=True)
    for k, v in res.items():
        print(f"  {'T' if v else 'F'} {k}", flush=True)
    ok = all(res.values())
    print("READBACK TABLE (addr, stored val, round, proc_confirmed, superseded_by_later_event, tags):",
          flush=True)
    for row in later:
        print(f"  {row[0]:#x} val={row[1]} round={row[2]} proc_confirmed={row[3]} superseded={row[4]} "
              f"{row[5]}", flush=True)
    print("VERDICT %s tag=%s poke %d->%d allocs=%d per_site=%s chooser_returns=%s ctrl=%d aaa=%d "
          "cons=%d a2st=%d round %d->%d slots(0..7)=%s detached=%s"
          % ("PASS" if ok else "FAIL", a.tag, slots0[a.poke_index], after_poke, len(st), per_site,
             [e.get("eax") for e in chr_], len(ctrl), len(aaa), len(cons), len(a2), r0, r1v, slots1,
             "detached]" in text), flush=True)
    print("evidence:", lpath, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
