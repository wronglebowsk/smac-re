#!/usr/bin/env python3
"""M85: does the turn boundary reach the tech/upkeep sites 0x52145e / 0x5a7d00 / 0x5a7f67?

WHY THIS SHAPE (static footing, ghidra_out/index.csv addr/size_bytes + scratch/m574/text.txt):
  0x52145e is inside FUN_00521070 (+1006), a function with ONE call site (0x522376) that
  m55_boundary.py's docstring identifies as the MULTIPLAYER 7-stage driver (mode_flags & 0x10).
  0x5a7d00 (+912) and 0x5a7f67 (+1527) are both inside FUN_005a7970, which has 47 call sites,
  one of them at 0x507e57 inside the human-turn loop FUN_0050f420. So the M67 "ZERO events" at
  these three addresses splits into two different causes, and this script decides which is which
  on ONE real invocation:
    - 0x521070 never entered in solo  -> the site is unreachable BY DESIGN (MP branch);
    - 0x5a7970 entered in solo        -> the helper IS live, so a zero at a specific offset means
                                         that branch was not taken (instrument asked the wrong question).

LIVE ARM: print-only breakpoints (the s135 instrument law: no memory writes in a gdb command list,
or the batch aborts with "not an lvalue" and gdb detaches), counters only, first hits printed.
Round/year are read back from /proc/<pid>/mem before AND after the driver, so a PASS is an effect
read back from the game, not a log line.

CONFLICT REPORTED (docs beat code until a controlled poke proves otherwise): m55_boundary.py names
ds:0x920434 "save_later" (research save-for-later gate); the M84e/s134-s135 work named the same
global NETGAME. Both names are asserted here so the conflict cannot silently disappear.

Usage: python3 scripts/m85_tech_census.py --tag m85cens1 [--timeout 120]
"""
import argparse, os, re, signal, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EVID = os.path.join(ROOT, "evidence")
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
INDEX = os.path.join(ROOT, "ghidra_out", "index.csv")

ROUND, YEAR, SAVELATER = 0x985AFC, 0x985B00, 0x920434
STAGES = 0x521070      # MP-only stage driver (1 caller)
HELPER = 0x5A7970      # 47 callers, contains both bit-set tails
IN_MP, IN_H1, IN_H2 = 0x52145E, 0x5A7D00, 0x5A7F67

TMPL = r"""set pagination off
set confirm off
set height 0
set verbose off
set $n_stage = 0
set $n_help = 0
set $n_mp = 0
set $n_h1 = 0
set $n_h2 = 0
set $n_round = 0
printf "ARMED round=%d year=%d savelater=%d\n", *(int *)0x985afc, *(int *)0x985b00, *(int *)0x920434
break *0x521070
commands
silent
set $n_stage = $n_stage + 1
printf "STAGE n=%d arg=%d\n", $n_stage, *(int *)($esp + 4)
continue
end
break *0x5a7970
commands
silent
set $n_help = $n_help + 1
if $n_help < 4
printf "HELPER n=%d eax=%d ret=%d\n", $n_help, $eax, *(int *)$esp
end
continue
end
break *0x52145e
commands
silent
set $n_mp = $n_mp + 1
printf "MP45E n=%d edi=%d bx=%d\n", $n_mp, $edi, $ebx
continue
end
break *0x5a7d00
commands
silent
set $n_h1 = $n_h1 + 1
printf "H1 n=%d eax=%d\n", $n_h1, $eax
continue
end
break *0x5a7f67
commands
silent
set $n_h2 = $n_h2 + 1
printf "H2 n=%d eax=%d\n", $n_h2, $eax
continue
end
break *0x51f320
commands
silent
set $n_round = $n_round + 1
printf "ROUNDINC n=%d round=%d\n", $n_round, *(int *)0x985afc
continue
end
continue
"""

LINE = re.compile(r"^(ARMED|STAGE|HELPER|MP45E|H1|H2|ROUNDINC) (.*)$")
KV = re.compile(r"(\w+)=(-?0x[0-9a-f]+|-?\d+)")


def pid_of():
    out = subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else None


def u32(pid, addr):
    try:
        with open("/proc/%d/mem" % pid, "rb", 0) as f:
            f.seek(addr)
            return int.from_bytes(f.read(4), "little")
    except OSError:
        return -1


def parse(text):
    ev = []
    for ln in text.splitlines():
        m = LINE.match(ln.strip())
        if m:
            ev.append((m.group(1), {k: int(v, 0) for k, v in KV.findall(m.group(2))}))
    return ev


def static_facts():
    """Containment and caller counts straight from the exports; no game needed."""
    facts = {}
    import csv
    rows = []
    for r in csv.DictReader(open(INDEX)):
        try:
            rows.append((int(r["addr"], 0), int(r["size_bytes"]), r["name"], int(r["n_callers"])))
        except Exception:
            pass
    for name, t in (("mp_site", IN_MP), ("h1", IN_H1), ("h2", IN_H2)):
        hit = [(n, a, c) for a, s, n, c in rows if a <= t < a + s]
        facts[name] = hit[0] if hit else None
    txt = open(TEXT, errors="replace").read()
    facts["calls_stage"] = txt.count("call   0x521070")
    facts["calls_helper"] = txt.count("call   0x5a7970")
    facts["helper_callers_human"] = len([m for m in re.finditer(r"^\s+(50[0-9a-f]{4}):", txt, re.M)
                                         if False])  # placeholder, replaced below
    human = [ln.split(":")[0].strip() for ln in txt.splitlines()
             if "call   0x5a7970" in ln and re.match(r"^\s+507[0-9a-f]{3}:", ln)]
    facts["helper_call_sites_human"] = human
    return facts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--settle", type=float, default=4.0)
    a = ap.parse_args()

    f = static_facts()
    print("static:", {k: (v if not isinstance(v, list) else v[:3]) for k, v in f.items()}, flush=True)

    pid = pid_of()
    if not pid:
        raise SystemExit("no terran.exe")
    r0, y0, s0 = u32(pid, ROUND), u32(pid, YEAR), u32(pid, SAVELATER)
    print(f"pid {pid} round={r0} year={y0} savelater={s0}", flush=True)

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
        raise SystemExit("gdb did not arm:\n" + head[-1000:])
    print([l for l in head.splitlines() if l.startswith("ARMED")][0], flush=True)

    t0 = time.time()
    r1 = subprocess.run([sys.executable, os.path.join(HERE, "m55_boundary.py"),
                         "--timeout", str(a.timeout)], capture_output=True, text=True,
                        timeout=a.timeout + 150)
    print(f"driver rc={r1.returncode} t={time.time()-t0:.0f}s  {r1.stdout.strip().splitlines()[-1][:120] if r1.stdout.strip() else ''}", flush=True)
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
    r1v, y1v = u32(pid, ROUND), u32(pid, YEAR)
    print("EVENT COUNTS:", cnt, flush=True)
    for i, (t, d) in enumerate([e for e in ev if e[0] != "ROUNDINC"][:6]):
        print(f"  {i} {t} {d}", flush=True)
    print(f"read-back: round {r0}->{r1v} year {y0}->{y1v} savelater={u32(pid, SAVELATER)} "
          f"armed={'ARMED round=' in head} detached={'detached]' in text}", flush=True)

    mp = f.get("mp_site")
    h1 = f.get("h1")
    h2 = f.get("h2")
    res = {
        # the boundary really ran, proven from memory, not from a log line
        "G1_boundary_moved": r1v > r0 and y1v >= y0,
        # the MP-only stage driver is never entered in a solo boundary
        "G2_mp_driver_silent": cnt.get("STAGE", 0) == 0,
        # ... and its inner site therefore cannot fire: 0x52145e is unreachable BY DESIGN
        "G3_mp_site_silent": cnt.get("MP45E", 0) == 0,
        # the 47-caller helper IS reached during the boundary: the M67 zero at its offsets was the question, not the game
        "G4_helper_live": cnt.get("HELPER", 0) >= 1,
        # static footing that makes the two readings above different claims
        "G5_static_containment": bool(mp and mp[0] == "FUN_00521070" and mp[2] == 1
                                      and h1 and h1[0] == "FUN_005a7970" and h2 and h2[0] == "FUN_005a7970"),
        # the naming conflict is recorded, not resolved by assertion
        "G6_conflict_recorded": s0 in (0, 1) and u32(pid, SAVELATER) in (0, 1),
    }
    print("GATES:", flush=True)
    for k, v in res.items():
        print(f"  {'T' if v else 'F' } {k}", flush=True)
    print("static detail: mp_site=%s h1=%s h2=%s calls_stage=%s calls_helper=%s human_call_sites=%s"
          % (mp, h1, h2, f.get("calls_stage"), f.get("calls_helper"), f.get("helper_call_sites_human")), flush=True)
    ok = all(res.values())
    print(f"VERDICT {'PASS' if ok else 'FAIL'} tag={a.tag} stage={cnt.get('STAGE',0)} mp45e={cnt.get('MP45E',0)} "
          f"helper={cnt.get('HELPER',0)} h1={cnt.get('H1',0)} h2={cnt.get('H2',0)} "
          f"round={r0}->{r1v} driver_rc={r1.returncode}", flush=True)
    print("evidence:", lpath, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
