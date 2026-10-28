#!/usr/bin/env python3
"""M86: which leg of FUN_005a7970 does a SOLO turn boundary take, and what gates 0x5a7d00 / 0x5a7f67?

M85 closed with: the helper IS entered once per boundary (eax=0, ret 0x569948 inside FUN_0055f650)
and neither tail ran. This script answers the two halves on ONE real invocation, with PRINT-ONLY
breakpoints at the leg ladder and at both gate blocks (the s135 instrument law: a memory write in a
gdb command list aborts the batch with "not an lvalue" and DETACHES).

THE LEG MAP (scratch/m574/text.txt instruction bytes, read this session):
  0x5a79a0 mov ebx,[ebp+0xc]        arg1 -> ebx;  0x5a7aa test ebx,ebx / jge 0x5a7a27
  0x5a7a55 mov eax,1; 0x5a7a5a mov ecx,edi; 0x5a7a5c shl eax,cl; 0x5a7a69 mov [ebp-0x10],eax
           -> [ebp-0x10] = 1 << arg0  (arg0 = faction id; the value is a FACTION MASK)
  0x5a7df2 mov eax,ds:0x985afc (round); 0x5a7e00 je 0x5a8f7d        EXIT leg if round == 0
  0x5a7e06 mov eax,ds:0x926bcc;        0x5a7e0d jne 0x5a8f7d        EXIT leg if != 0
  0x5a7e4f cmp ecx,0x58; 0x5a7e52 jne 0x5a7e5a (arg1==88 also inc [edx+0x94d798])
  0x5a7e63 mov DWORD [ebp-0x1c],0x93325c; 0x5a7e6d movsx ecx,[edx];
  0x5a7e70 cmp [ebp+0xc],ecx; 0x5a7e73 jne 0x5a7f9f
           -> the 64-record band loop is entered ONLY when arg1 == *(short *)0x93325c
  0x5a7e94..0x5a7f96 loop: esi = band*3328 + i*52 over 0x98ad88 (64 records = one FACTION BAND),
           ebx = tid = band*64+i; per-record skips: 0x5a7ea6 je (flag[+0x30] bit0 clear),
           0x5a7eb7 jne ([ebp-0x10] & owner[+0x2c]), 0x5a7eca jge (byte[+0x2f] >= [ebp-0x14])
  0x5a7f3e call 0x573a90 -> eax;  0x5a7f46 cmp eax,ebx / 0x5a7f48 je 0x5a7f83  (skip if self)
  GATE 0x5a7f4a: 0x5a7f4a mov ecx,ds:0x920434; 0x5a7f52 je 0x5a7f71;
                 0x5a7f54 mov cl,[ebp-0x10]; 0x5a7f57 mov dl,ds:0x985b10; 0x5a7f5f je 0x5a7f71
      TAKEN-OR leg 0x5a7f61 lea edx,[eax+eax*2]; 0x5a7f64 lea eax,[eax+edx*4] (eax*=13)
                     0x5a7f67 or BYTE PTR [eax*4+0x98adb9],0x1
                     = type record 0x98ad88 + (eax/13)*52 + 0x31, bit 0 (bit 8 of the +0x30 flag word)
      ELSE leg     0x5a7f71 push 0; push eax; push edi; call 0x572800; push edi; call 0x4ef540
  TWIN block 0x5a7cd7 call 0x573a90 -> 0x5a7ce1 jl 0x5a7d1c -> GATE 0x5a7ce3 (same two operands)
      -> 0x5a7d00 or BYTE PTR [eax*4+0x98adb9],0x1  ELSE 0x5a7d0a call 0x572800 + call 0x4ef540

So both M67 tails need THREE things: the band loop leg (arg1 == *(short*)0x93325c), a non-self
0x573a90 answer, and ds:0x920434 != 0 with (1<<arg0) & ds:0x985b10. A census that only asks about
0x5a7d00/0x5a7f67 cannot tell those apart; this one counts every leg.

PREDICTIONS computed from the baseline BEFORE arming (the "shape must discriminate" rule):
  live ds:0x920434 == 0  ->  OR1 == OR2 == 0 and ELSE1/ELSE2 carry the hits;
  live ds:0x920434 != 0  ->  OR1/OR2 > 0.
  arg1 == *(short*)0x93325c -> LOOP > 0, else LOOP == 0 and ALT > 0.

Usage: python3 scripts/m86_helper_legs.py --tag m86cens1 [--timeout 380]
Exit 0 only when every gate is True; prints VERDICT PASS/FAIL.
"""
import argparse, csv, os, re, signal, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EVID = os.path.join(ROOT, "evidence")
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
INDEX = os.path.join(ROOT, "ghidra_out", "index.csv")

ROUND, YEAR, NETG, FLAG26B, HUMANMASK = 0x985AFC, 0x985B00, 0x920434, 0x926BCC, 0x985B10
KINDTABLE = 0x93325C
HELPER = 0x5A7970
# leg ladder + both gate blocks, in execution order
LEGS = [
    ("ENTRY",  0x5A7970, "helper entered; prints eax and the three stack args"),
    ("E13",    0x5A7E13, "reached only if BOTH early exits fell through (round!=0 and ds:0x926bcc==0)"),
    ("LOOP",   0x5A7E79, "reached only if arg1 == *(short*)0x93325c  -> the 64-record band loop"),
    ("ALT",    0x5A7F9F, "reached only if arg1 != *(short*)0x93325c  -> the other body"),
    ("EXIT",   0x5A8F7D, "the early-exit leg (round==0 or ds:0x926bcc!=0)"),
    ("HEAD",   0x5A7E94, "band loop head (conditional: $esi==0 -> band 0 record 0 only)"),
    ("GATE1",  0x5A7CE3, "twin gate block, operands printed"),
    ("OR1",    0x5A7D00, "twin OR leg taken"),
    ("ELSE1",  0x5A7D0A, "twin else leg taken (call 0x572800 + 0x4ef540)"),
    ("GATE2",  0x5A7F4A, "loop-tail gate, operands printed"),
    ("OR2",    0x5A7F67, "loop-tail OR leg taken"),
    ("ELSE2",  0x5A7F71, "loop-tail else leg taken (call 0x572800 + 0x4ef540)"),
]
BRANCH = [0x5A7E00, 0x5A7E0D, 0x5A7E73, 0x5A7F52, 0x5A7F5F, 0x5A7CEB, 0x5A7CF8]

TMPL_HEAD = """set pagination off
set confirm off
set height 0
set verbose off
"""
COUNTERS = "".join("set $n_%s = 0\n" % t.lower() for t, _, _ in LEGS)
ARM = ('printf "ARMED round=%d year=%d netg=%d save=%d human=%d kind=%d\\n", '
       '*(int *)0x985afc, *(int *)0x985b00, *(int *)0x926bcc, *(int *)0x920434, '
       '*(unsigned char *)0x985b10, *(short *)0x93325c\n')

PRINTS = {
    "ENTRY": 'printf "ENTRY n=%d eax=%d a0=%d a1=%d a2=%d ret=0x%x\\n", $n_entry, $eax, '
             '*(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(int *)$esp',
    "E13":   'printf "E13 n=%d a1=%d kind=%d round=%d flag26bcc=%d c78c=%d c790=%d c798=%d\\n", '
             '$n_e13, $ecx, *(short *)0x93325c, *(int *)0x985afc, *(int *)0x926bcc, '
             '*(int *)($edx+0x94d78c), *(int *)($edx+0x94d790), *(int *)($edx+0x94d798)',
    "LOOP":  'printf "LOOP n=%d band=%d mask=%d human=%d\\n", $n_loop, $edi, '
             '*(int *)($ebp-0x10), *(unsigned char *)0x985b10',
    "ALT":   'printf "ALT n=%d eax=%d a1=%d kind=%d\\n", $n_alt, $eax, *(int *)($ebp+0xc), '
             '*(short *)0x93325c',
    "EXIT":  'printf "EXIT n=%d eax=%d round=%d flag26bcc=%d\\n", $n_exit, $eax, '
             '*(int *)0x985afc, *(int *)0x926bcc',
    "HEAD":  'printf "HEAD n=%d esi=%d tid=%d mask=%d human=%d\\n", $n_head, $esi, $ebx, '
             '*(int *)($ebp-0x10), *(unsigned char *)0x985b10',
    "GATE1": 'printf "GATE1 n=%d idx=%d save=%d mask=%d human=%d\\n", $n_gate1, $eax, '
             '*(int *)0x920434, *(int *)($ebp-0x10), *(unsigned char *)0x985b10',
    "GATE2": 'printf "GATE2 n=%d idx=%d tid=%d save=%d mask=%d human=%d\\n", $n_gate2, $eax, '
             '$ebx, *(int *)0x920434, *(int *)($ebp-0x10), *(unsigned char *)0x985b10',
    "OR1":   'printf "OR1 n=%d idx=%d\\n", $n_or1, $eax',
    "OR2":   'printf "OR2 n=%d idx=%d\\n", $n_or2, $eax',
    "ELSE1": 'printf "ELSE1 n=%d idx=%d band=%d\\n", $n_else1, $eax, $edi',
    "ELSE2": 'printf "ELSE2 n=%d idx=%d band=%d\\n", $n_else2, $eax, $edi',
}
COND = {"HEAD": " if $esi == 0"}   # register-only condition (s133: memory-read conditions are slow)


def gdb_tmpl():
    out = [TMPL_HEAD, COUNTERS, ARM]
    for tag, addr, _ in LEGS:
        out.append("break *0x%x%s\n" % (addr, COND.get(tag, "")))
        out.append("commands\nsilent\nset $n_%s = $n_%s + 1\n" % (tag.lower(), tag.lower()))
        out.append("if $n_%s < 4\n%s\nend\ncontinue\nend\n" % (tag.lower(), PRINTS[tag]))
    out.append("continue\n")
    return "".join(out)


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
    known = {t for t, _, _ in LEGS} | {"ARMED"}
    ev = []
    for ln in text.splitlines():
        p = ln.strip().split()
        if len(p) >= 2 and p[0] in known:
            kv = dict((k, int(v, 0)) for k, v in re.findall(r"(\w+)=(-?0x[0-9a-f]+|-?\d+)", " ".join(p[1:])))
            ev.append((p[0], kv))
    return ev


def branch_bytes():
    """The naming must come from the instruction bytes, not from prose."""
    want = {a: None for a in BRANCH}
    with open(TEXT, errors="replace") as f:
        for ln in f:
            m = re.match(r"\s*([0-9a-f]{6,8}):\t", ln)
            if not m:
                continue
            a = int(m.group(1), 16)
            if a in want:
                want[a] = ln.strip()
            elif a > max(want):
                break
    return want


def containment(addr):
    for r in csv.DictReader(open(INDEX)):
        try:
            a, s = int(r["addr"], 0), int(r["size_bytes"])
        except Exception:
            continue
        if a <= addr < a + s:
            return r["name"], a, s, int(r["n_callers"])
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--timeout", type=int, default=380)
    ap.add_argument("--settle", type=float, default=4.0)
    a = ap.parse_args()

    pid = pid_of()
    if not pid:
        raise SystemExit("no terran.exe (fresh-load first: SMAC_SAVE='m54b_clean.SAV' "
                         "python3 scripts/m54a_load.py --relaunch)")
    r0, y0 = mem(pid, ROUND), mem(pid, YEAR)
    s0, k0, f0, hm = mem(pid, NETG), mem(pid, KINDTABLE, 2, True), mem(pid, FLAG26B), mem(pid, HUMANMASK, 1)
    pred = {"loop_gt0": k0 is not None and r0 >= 0, "or_zero_if_save0": s0 == 0}
    print(f"pid {pid} round={r0} year={y0} save(0x920434)={s0} kind(*(short*)0x93325c)={k0} "
          f"flag0x926bcc={f0} humanmask(0x985b10)={hm}", flush=True)
    print(f"baseline: round {r0} year {y0} save {s0} kind {k0} human {hm}", flush=True)

    gpath = os.path.join(ROOT, "scratch", f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.gdblog")
    os.makedirs(EVID, exist_ok=True)
    open(gpath, "w").write(gdb_tmpl())
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

    t0 = time.time()
    r1 = subprocess.run([sys.executable, os.path.join(HERE, "m55_boundary.py"),
                         "--timeout", str(a.timeout), "--trace",
                         os.path.join(ROOT, "scratch", f"{a.tag}_bnd.jsonl")],
                        capture_output=True, text=True, timeout=a.timeout + 120)
    last = r1.stdout.strip().splitlines()[-1][:140] if r1.stdout.strip() else ""
    print(f"driver rc={r1.returncode} t={time.time()-t0:.0f}s  {last}", flush=True)
    time.sleep(a.settle)
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
    r1v, y1v, s1v = mem(pid, ROUND), mem(pid, YEAR), mem(pid, NETG)
    print("EVENT COUNTS:", {t: cnt.get(t, 0) for t, _, _ in LEGS}, flush=True)
    for t, _, why in LEGS:
        rows = [d for tt, d in ev if tt == t]
        if rows:
            print(f"  {t}: {rows[0]}  ({why})", flush=True)
    bb = branch_bytes()
    print("BRANCH BYTES:", flush=True)
    for addr in BRANCH:
        print(f"  {addr:06x}  {bb.get(addr)}", flush=True)
    print(f"read-back: round {r0}->{r1v} year {y0}->{y1v} save {s0}->{s1v} "
          f"armed=True detached={'detached]' in text}", flush=True)

    cont = containment(0x5A7F67), containment(0x5A7D00), containment(0x50DD84)
    save_now = s1v if s1v >= 0 else s0
    res = {
        "G1_boundary_moved": r1v > r0 and y1v >= y0,
        "G2_helper_entered_with_args": cnt.get("ENTRY", 0) >= 1 and any(
            d.get("a1") is not None for t, d in ev if t == "ENTRY"),
        # every entered call resolved to exactly one named leg of the ladder
        "G3_leg_ladder_resolved": cnt.get("ENTRY", 0) >= 1 and (
            cnt.get("LOOP", 0) + cnt.get("ALT", 0) + cnt.get("EXIT", 0) >= cnt.get("ENTRY", 0)),
        # the gate operands were printed AND the same globals read back from /proc match
        "G4_gate_operands_read_back": (cnt.get("GATE1", 0) + cnt.get("GATE2", 0) >= 1
                                       and s1v == s0 and hm == mem(pid, HUMANMASK, 1)),
        # the tail leg agrees with the gate operands: save==0 forbids the OR legs, save!=0 demands them
        "G5_tail_leg_matches_gate": (
            (save_now == 0 and cnt.get("OR1", 0) == 0 and cnt.get("OR2", 0) == 0
             and cnt.get("ELSE1", 0) + cnt.get("ELSE2", 0) >= 1)
            or (save_now != 0 and cnt.get("OR1", 0) + cnt.get("OR2", 0) >= 1)),
        "G6_branch_bytes_named": all(bb.get(x) for x in BRANCH),
        "G7_static_containment": bool(cont[0] and cont[0][0] == "FUN_005a7970"
                                      and cont[1] and cont[1][0] == "FUN_005a7970"
                                      and cont[2] and cont[2][0] == "FUN_0050d140"),
    }
    print("GATES:", flush=True)
    for k, v in res.items():
        print(f"  {'T' if v else 'F'} {k}", flush=True)
    ok = all(res.values())
    print("VERDICT %s tag=%s entry=%d e13=%d loop=%d alt=%d exit=%d head=%d "
          "gate1=%d or1=%d else1=%d gate2=%d or2=%d else2=%d round=%d->%d save=%d kind=%d "
          "driver_rc=%d" % ("PASS" if ok else "FAIL", a.tag, cnt.get("ENTRY", 0), cnt.get("E13", 0),
                            cnt.get("LOOP", 0), cnt.get("ALT", 0), cnt.get("EXIT", 0),
                            cnt.get("HEAD", 0), cnt.get("GATE1", 0), cnt.get("OR1", 0),
                            cnt.get("ELSE1", 0), cnt.get("GATE2", 0), cnt.get("OR2", 0),
                            cnt.get("ELSE2", 0), r0, r1v, save_now, k0, r1.returncode), flush=True)
    print("evidence:", lpath, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
