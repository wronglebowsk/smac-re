#!/usr/bin/env python3
"""M87: who calls FUN_005aaa20 (the only live caller of FUN_005a7970 ever measured), and when?

STATIC FOOTING (scratch/m71/dis.py windows over scratch/m574/text.txt, read this session):
  FUN_005aaa20(arg0=faction): edi = faction*191 (0x5aaa34-0x5aaa45) so [edi+0x94d7fc] is a
  PER-FACTION SLOT (stride 191 dwords = 764 B); ebx = [ecx*4+0x9275c4] = the 1436-byte faction
  record (stride 359 dwords, the M84e base). Legs:
    0x5aaa63 mov eax,ds:0x920434; 0x5aaa6b test; 0x5aaa6d je 0x5aaaa0
    0x5aaa6f cmp DWORD ds:0x926bd4,1; 0x5aaa76 jne 0x5aaaa0   -> NET leg (only save!=0 && 0x926bd4==1)
    0x5aaaa0 mov ebx,[edi+0x94d7fc]; 0x5aaaa8 jge 0x5aaabd    -> a stored slot is used as-is
    0x5aaaaa push esi; call 0x5aa880; 0x5aaab0 (eax = the kind it returns); 0x5aaab7 jl 0x5aab66
    0x5aaabd push 0; push ebx; push esi; [edi+0x94d7fc] = -1; call 0x5a7970  (return site 0x5aaad0)
  FUN_005aa880(arg0) itself reads ds:0x920434 and the queue 0x91db70 (call 0x527ca0 at 0x5aa8f0) —
  the M84e queue. So the helper's arg1 (kind) comes from a per-faction slot or from that queue.
  The 9 static call sites of FUN_005aaa20 live in FUN_004ef6d0 (x2: 0x4f1d6c/0x4f1d72 — the same
  function that holds the M73 price gate 0x4efa5e and the PRODFLAG writer 0x4efe60), FUN_00512b40,
  FUN_00516b80, FUN_00520540, FUN_00521070 (the MP driver), FUN_0059ce10, FUN_005aadf0 (x2).

WHY A BOUNDARY CENSUS: m86cens1 caught FUN_005a7970 entered ONCE (ret 0x5aaad0, a0=5 a1=8) during a
2-boundary window on a freshly-loaded box; m86cens2 caught ZERO hits on a clean boundary 3 rounds
later on the same box. The asymmetry's obvious reading is that the trigger is load/first-boundary
driven, not per-boundary — that is the prediction this script tests, and it names the caller by the
RETURN SITE bytes at every hit.

PREDICTIONS (printed before the counters are read):
  P1 the first AAA hit lands on boundary 1 after a fresh load (cens1/cens2 asymmetry);
  P2 save(ds:0x920434)==0 -> LIVE hits == AAA hits and NET hits == 0;
  P3 kind (ebx at 0x5aaabd) not in the live table shorts at 0x93325c/68/74 -> LOOP == 0.

Usage: python3 scripts/m87_aaa20_trigger.py --tag m87trig1 [--rounds 4] [--timeout 300]
Prints VERDICT PASS/FAIL; exit 0 only when every gate is True. Run right after
SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch (do NOT reload again).
"""
import argparse, os, re, signal, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EVID = os.path.join(ROOT, "evidence")
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
INDEX = os.path.join(ROOT, "ghidra_out", "index.csv")

AAA20, A7970, SLOT, NETG, NET26BD4, KINDTABLE = 0x5AAA20, 0x5A7970, 0x94D7FC, 0x920434, 0x926BD4, 0x93325C
ROUND, YEAR = 0x985AFC, 0x985B00
# tag, address, what reaching it proves
SITES = [
    ("AAA",   0x5AAA20, "FUN_005aaa20 entered; ret = *(esp) names its caller"),
    ("NET",   0x5AAA6F, "reached only if ds:0x920434 != 0"),
    ("LIVE",  0x5AAAA0, "reached only if the netgame leg was NOT taken (save==0 or 0x926bd4!=1)"),
    ("KIND",  0x5AAAB0, "reached only if the per-faction slot was < 0: eax = FUN_005aa880's kind"),
    ("CALL",  0x5AAABD, "the helper call site: esi = arg0 (faction), ebx = arg1 (kind)"),
    ("EXIT",  0x5AAB66, "aaa20's exit leg"),
    ("HENTRY",0x5A7970, "FUN_005a7970 entered: a0/a1/a2 + its own return site"),
    ("WALK",  0x5A7E6D, "the 0x5a7e73 operands: table pointer, its short, arg1"),
    ("LOOP",  0x5A7E79, "reached only if arg1 == that table short -> the 64-record band loop"),
    ("ALT",   0x5A7F9F, "the table-miss leg / band-loop completion"),
]
BRANCH = [0x5AAA6D, 0x5AAA76, 0x5AAAA8, 0x5AAAB7, 0x5AAACB, 0x5A7E73]  # 0x5aaacb = aaa20's own call of the helper
STATIC_SITES = {0x4f1d6c, 0x4f1d72, 0x514e56, 0x517df1, 0x52087f, 0x5212ed, 0x59cfd4,
                0x5aaf46, 0x5aafb9}
PRINTS = {
    "AAA":   'printf "AAA n=%d a0=%d ret=0x%x save=%d net26bd4=%d\\n", $n_aaa, $esi, '
             '*(int *)$esp, *(int *)0x920434, *(int *)0x926bd4',
    "NET":   'printf "NET n=%d save=%d net26bd4=%d\\n", $n_net, *(int *)0x920434, *(int *)0x926bd4',
    "LIVE":  'printf "LIVE n=%d faction=%d slot=%d save=%d\\n", $n_live, $esi, '
             '*(int *)($edi+0x94d7fc), *(int *)0x920434',
    "KIND":  'printf "KIND n=%d kind=%d faction=%d\\n", $n_kind, $eax, $esi',
    "CALL":  'printf "CALL n=%d faction=%d kind=%d slot_pre=%d\\n", $n_call, $esi, $ebx, '
             '*(int *)($edi+0x94d7fc)',
    "EXIT":  'printf "EXIT n=%d eax=%d\\n", $n_exit, $eax',
    "HENTRY":'printf "HENTRY n=%d a0=%d a1=%d a2=%d ret=0x%x\\n", $n_hentry, *(int *)($esp+4), '
             '*(int *)($esp+8), *(int *)($esp+0xc), *(int *)$esp',
    "WALK":  'printf "WALK n=%d ptr=0x%x short=%d arg1=%d\\n", $n_walk, $edx, *(short *)$edx, '
             '*(int *)($ebp+0xc)',
    "LOOP":  'printf "LOOP n=%d band=%d\\n", $n_loop, $edi',
    "ALT":   'printf "ALT n=%d\\n", $n_alt',
}
TMPL = ("set pagination off\nset confirm off\nset height 0\nset verbose off\n"
        + "".join("set $n_%s = 0\n" % t.lower() for t, _, _ in SITES)
        + 'printf "ARMED round=%d year=%d save=%d net26bd4=%d kind0=%d kind1=%d kind2=%d\\n", '
          '*(int *)0x985afc, *(int *)0x985b00, *(int *)0x920434, *(int *)0x926bd4, '
          '*(short *)0x93325c, *(short *)0x933268, *(short *)0x933274\n'
        + "".join("break *0x%x\ncommands\nsilent\nset $n_%s = $n_%s + 1\nif $n_%s < 4\n%s\nend\ncontinue\nend\n"
                  % (a, t.lower(), t.lower(), t.lower(), PRINTS[t]) for t, a, _ in SITES)
        + "continue\n")


def pid_of():
    out = subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else None


def mem(pid, addr, n=4, signed=False):
    try:
        with open("/proc/%d/mem" % pid, "rb", 0) as f:
            f.seek(addr)
            return int.from_bytes(f.read(n), "little", signed=signed)
    except OSError:
        return -1


def parse(text):
    known = {t for t, _, _ in SITES}
    ev = []
    for ln in text.splitlines():
        p = ln.strip().split()
        if len(p) >= 2 and p[0] in known:
            ev.append((p[0], {k: int(v, 0) for k, v in re.findall(r"(\w+)=(-?0x[0-9a-f]+|-?\d+)", " ".join(p[1:]))}))
    return ev


def functions():
    out = []
    import csv
    for r in csv.DictReader(open(INDEX)):
        try:
            out.append((int(r["addr"], 0), int(r["size_bytes"]), r["name"]))
        except Exception:
            pass
    return out


def callsite_bytes(addr):
    """The instruction bytes of the call that put us here — the attribution must be byte-backed."""
    with open(TEXT, errors="replace") as f:
        for ln in f:
            m = re.match(r"\s*([0-9a-f]{6,8}):\t", ln)
            if m and int(m.group(1), 16) == addr:
                return ln.strip()
            if m and int(m.group(1), 16) > addr:
                break
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--rounds", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--settle", type=float, default=3.0)
    a = ap.parse_args()

    pid = pid_of()
    if not pid:
        raise SystemExit("no terran.exe (fresh-load first: SMAC_SAVE='m54b_clean.SAV' "
                         "python3 scripts/m54a_load.py --relaunch)")
    r0, y0 = mem(pid, ROUND), mem(pid, YEAR)
    save0, net0 = mem(pid, NETG), mem(pid, NET26BD4)
    kinds = [mem(pid, KINDTABLE + 12 * i, 2, True) for i in range(3)]
    print(f"pid {pid} round={r0} year={y0} save(0x920434)={save0} 0x926bd4={net0} "
          f"table shorts {kinds}", flush=True)
    print("PREDICTIONS (before the counters are read): P1 first AAA on boundary 1 of a freshly "
          f"loaded box; P2 save={save0} -> {'LIVE==AAA and NET==0' if save0 == 0 else 'NET>0'}; "
          f"P3 kinds {kinds} -> LOOP==0 for any kind not in them", flush=True)

    funcs = functions()
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

    seen_round = []
    for i in range(a.rounds):
        before = mem(pid, ROUND)
        r1 = subprocess.run([sys.executable, os.path.join(HERE, "m55_boundary.py"),
                             "--timeout", str(a.timeout), "--trace",
                             os.path.join(ROOT, "scratch", f"{a.tag}_bnd{i}.jsonl")],
                            capture_output=True, text=True, timeout=a.timeout + 60)
        time.sleep(a.settle)
        after = mem(pid, ROUND)
        seen_round.append((i + 1, before, after, r1.returncode))
        txt = open(lpath, errors="replace").read()
        n_aaa = sum(1 for t, _ in parse(txt) if t == "AAA")
        last = r1.stdout.strip().splitlines()[-1][:110] if r1.stdout.strip() else ""
        print(f"boundary {i+1}: round {before}->{after} driver_rc={r1.returncode} AAA={n_aaa}  {last}", flush=True)
        if n_aaa:
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
    first_aaa_boundary = None
    print("ATTRIBUTION (return site -> function, and the call-site bytes):", flush=True)
    attribs = []
    for t, d in ev:
        if t != "AAA":
            continue
        ret, site = d["ret"], d["ret"] - 5
        fn = next((n for a_, s_, n in funcs if a_ <= site < a_ + s_), None)
        bb = callsite_bytes(site)
        attribs.append((hex(ret), hex(site), fn, bb))
        print(f"  ret={ret:#07x} site={site:#07x} caller={fn} bytes={bb}", flush=True)
        if first_aaa_boundary is None:
            first_aaa_boundary = len(seen_round)  # filled below by boundary scan
    # recompute the boundary index honestly: the per-boundary AAA counts were printed live
    for t, _, why in SITES:
        rows = [d for tt, d in ev if tt == t]
        if rows and t != "AAA":
            print(f"  {t}: {rows[0]}  ({why})", flush=True)
    print("BOUNDARIES:", seen_round, flush=True)
    bb2 = {x: callsite_bytes(x) for x in BRANCH}
    print("BRANCH BYTES:", flush=True)
    for x in BRANCH:
        print(f"  {x:06x}  {bb2.get(x)}", flush=True)
    r1v = mem(pid, ROUND)
    print(f"read-back: round {r0}->{r1v} save={mem(pid, NETG)} detached={'detached]' in text}", flush=True)

    aaa = [d for t, d in ev if t == "AAA"]
    calls = [d for t, d in ev if t == "CALL"]
    hen = [d for t, d in ev if t == "HENTRY"]
    kinds_seen = [d["kind"] for d in calls]
    # which boundary produced the first AAA (from the live per-boundary counts printed above)
    fb_idx = None
    if aaa:
        # the driver loop broke out on the boundary that produced the first AAA hit
        fb_idx = len(seen_round)
    res = {
        "G1_aaa20_entered": len(aaa) >= 1,
        # every hit attributed to a NAMED function, byte-backed by its own call site
        "G2_every_hit_attributed": bool(attribs) and all(fn and bb for _, _, fn, bb in attribs),
        # the chain closes: aaa20's (faction, kind) at 0x5aaabd == the helper's a0/a1 at its entry
        "G3_chain_closed_on_args": bool(calls and hen) and all(
            any(c["faction"] == h["a0"] and c["kind"] == h["a1"] and h["a2"] == 0
                and h["ret"] == 0x5AAAD0 for h in hen) for c in calls),
        # P2: the netgame leg is decided by ds:0x920434, read live
        "G4_net_leg_prediction_confirmed": (
            (save0 == 0 and cnt.get("NET", 0) == 0 and cnt.get("LIVE", 0) == len(aaa))
            or (save0 != 0 and cnt.get("NET", 0) >= 1)),
        # P3: the band loop runs only for a kind that is in the live table shorts
        "G5_loop_prediction_confirmed": all(
            ((k in kinds) == (cnt.get("LOOP", 0) > 0)) for k in kinds_seen) and bool(kinds_seen),
        "G6_branch_bytes_named": all(bb2.get(x) for x in BRANCH),
        "G7_static_call_sites_agree": bool(attribs) and all(
            int(site, 16) in STATIC_SITES for _, site, _, _ in attribs),
        "G8_boundary_actually_ran": any(b != af for _, b, af, _ in seen_round) and r1v > r0,
    }
    print("GATES:", flush=True)
    for k, v in res.items():
        print(f"  {'T' if v else 'F'} {k}", flush=True)
    ok = all(res.values())
    print("VERDICT %s tag=%s aaa=%d net=%d live=%d kind=%d call=%d exit=%d hentry=%d walk=%d "
          "loop=%d alt=%d kinds=%s first_aaa_after_boundary=%d boundaries=%s save=%d table=%s"
          % ("PASS" if ok else "FAIL", a.tag, len(aaa), cnt.get("NET", 0), cnt.get("LIVE", 0),
             cnt.get("KIND", 0), cnt.get("CALL", 0), cnt.get("EXIT", 0), cnt.get("HENTRY", 0),
             cnt.get("WALK", 0), cnt.get("LOOP", 0), cnt.get("ALT", 0), kinds_seen, fb_idx,
             seen_round, save0, kinds), flush=True)
    print("evidence:", lpath, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
