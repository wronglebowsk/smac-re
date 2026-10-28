#!/usr/bin/env python3
"""M80 ACCEPTANCE (tag m80band1) — FUN_00573a90's first arg is a FACTION, and the record
array is 8 bands of 64 keyed by faction; index = faction*64 + slot.

BASELINE (read BEFORE the run, scripts/m80_band_census.py --json, save m54b_clean r50):
  band 0 0..13 seeds (Colony Pod..), b1 64, b2 128..131, b3 192..194 (ours), b4 256,
  b5 320..325, b6 384..386 (387 EMPTY), b7 448..449 — each band contiguous from b*64.
STATIC (instruction bytes): 0x573aa3 `mov esi,[ebp+8]` = param_1; loop counter [ebp-0x18]
  to 0x80; index = counter<0x40 ? counter : (counter&0x3f) + param_1<<6; 0x574167-0x574176
  reject unless index/64 == 0 or index/64 == esi; 0x57417e `lea eax,[edx*4+0x98ad88]` (edi*52);
  0x5741f0 `and BYTE [ebx+0x98adb8],0xfd`; 0x5741fe `push 0; push eax; push esi; call 0x572800`
  and the sweep's own band base is `param_1*0xd00` = faction*64*52 (shard_014.c FUN_00572800).

PREDICTIONS the run must discriminate between (computed from the baseline first):
  H_BAND (the claim):  at 0x5741fe esi in 0..7 (a faction) and the index in [ebp-0x4] is
                       band 0 or band == esi; the sweep at 0x572800 gets (faction, index).
  H_TID (the prior reading, M78's parenthetical "indices 324/325/385/387"): esi is a RECORD
                       INDEX, so values >= 64 (ours would be 192..194) appear at 0x5741fe.
The two disagree on every printed esi value; the shape discriminates.

Gates (all must hold, one real invocation, no floor weakened):
  G1 >=1 0x5741fe visit AND >=1 sweep-entry visit
  G2 every visit esi in 0..7                        (falsifies H_TID)
  G3 every visit index < 512 and index//64 in {0, esi}
  G4 every sweep entry from 0x574203: owner == the esi of the visit it came from, and
     owner in 0..7 and tid//64 in {0, owner}
  G5 >=1 visit with esi >= 4 whose index >= 256 names a NON-EMPTY record in the census
     (the >= 256 indices are live records, not padding)
  G6 every census flag-diff index in band >= 4 lies in a band the sweep was called for
Exit 0 prints PASS.
"""
import argparse, json, os, re, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m55_boundary as M
from m80_band_census import census, REC_BASE, STRIDE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "evidence")
SITE_SWEEP_CALL, SITE_SWEEP, SITE_MARK, SITE_CLR = 0x5741fe, 0x572800, 0x5729d5, 0x5741f0
SITE_ENTRY = 0x573a90

BPS = [
    (SITE_ENTRY, "F573IN", "F573IN ret=0x%x fac=%d p2=%d",
     "*(int *)$esp, *(int *)($esp + 4), *(int *)($esp + 8)", None),
    (SITE_SWEEP_CALL, "SW573", "SW573 fac=%d idx=%d ebx=%d",
     "$esi, *(int *)($ebp - 0x4), $ebx", None),
    (SITE_CLR, "CLR4", "CLR4 fac=%d ebxidx=%d slotidx=%d pre=0x%x",
     "$esi, $ebx / 52, *(int *)($ebp - 0x4), *(unsigned short *)($ebx + 0x98adb8)", None),
    (SITE_SWEEP, "SWENTER", "SWENTER owner=%d tid=%d mode=%d ret=0x%x",
     "*(int *)($esp + 4), *(int *)($esp + 8), *(int *)($esp + 0xc), *(int *)$esp", None),
    (SITE_MARK, "MARKHIGH", "MARKHIGH tid=%d pre=0x%x",
     "$edi / 52, *(unsigned short *)($edi + 0x98adb8)", "if ($edi / 52) >= 256"),
]
TAGS = ("F573IN", "SWENTER", "MARKHIGH", "SW573", "CLR4", "BOUNDARY", "ARMED")
LINE = re.compile(r"^(%s)\s*(.*)$" % "|".join(sorted(TAGS, key=len, reverse=True)))
KV = re.compile(r"(\w+)=(-?0x[0-9a-f]+|-\d+|\d+)")


def gdb_script():
    blocks = []
    for addr, tag, fmt, args, cond in BPS:
        head = f"break *{addr:#x}" + (f" {cond}" if cond else "")
        blocks.append(f"{head}\ncommands\nsilent\nprintf \"{fmt}\\n\", {args}\ncontinue\nend\n")
    return ("set confirm off\nset height 0\nset verbose off\nset can-use-hw-watchpoints 1\n"
            + "".join(blocks)
            + 'printf "ARMED fac3_head=%d pend=%d\\n", *(int *)(0x98ad88 + 192*52 + 0x50), '
              '*(int *)0x985dcc\ncontinue\n')


def parse(text):
    out = []
    for ln in text.splitlines():
        m = LINE.match(ln.strip())
        if not m:
            continue
        d = {"tag": m.group(1)}
        rest = m.group(2)
        if d["tag"] == "BOUNDARY":
            d["idx"] = int(rest.split()[0])
        else:
            for k, v in KV.findall(rest):
                d[k] = int(v, 0)
        out.append(d)
    return out


def flags_of(recs):
    return {r["i"]: r["flags"] for r in recs}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m80band1")
    ap.add_argument("--boundaries", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=200)
    a = ap.parse_args()
    pid = os.environ.get("SMAC_PID") or M.find_pid()
    if not pid:
        raise SystemExit("no terran.exe")
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        before = census(m)
    fb = flags_of(before)
    named_hi = [r["i"] for r in before if r["i"] >= 256 and (r["name"] or r["flags"])]
    print(f"baseline pid {pid}: non-empty records with index >= 256: {named_hi}", flush=True)

    gpath = os.path.join(ROOT, "scratch", f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.gdblog")
    open(gpath, "w").write(gdb_script())
    log = open(lpath, "a")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=log, stderr=subprocess.STDOUT)
    time.sleep(3.0)
    head = open(lpath, errors="replace").read()
    if "ARMED" not in head:
        try:
            os.kill(g.pid, 2)
        except ProcessLookupError:
            pass
        subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
        raise SystemExit(f"gdb never printed ARMED (breakpoints seen {head.count('Breakpoint ')})")
    print(f"armed ({head.count('Breakpoint ')} breakpoints) :: "
          f"{[l for l in head.splitlines() if l.startswith('ARMED')][0]}", flush=True)

    t0 = time.time()
    for k in range(a.boundaries):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "smac_play.py"),
                            "--turns", "1", "--timeout", str(a.timeout), "--no-escape", "3000",
                            "--orders-per-turn", "1", "--verbose", "--tag", f"{a.tag}_r{k}"],
                           capture_output=True, text=True)
        with open(f"/proc/{pid}/mem", "rb", 0) as m:
            c = census(m)
        with open(lpath, "a") as fh:
            fh.write("BOUNDARY %d rc=%d hi=%s\n" % (
                k, r.returncode, ",".join(str(x["i"]) for x in c
                                          if x["i"] >= 256 and (x["name"] or x["flags"])) or "-"))
        print(f"  boundary {k}: rc={r.returncode} t={time.time()-t0:.0f}s", flush=True)
    try:
        os.kill(g.pid, 2)
    except ProcessLookupError:
        pass
    for _ in range(40):
        if not os.path.exists("/proc/%d" % g.pid):
            break
        time.sleep(0.5)
    subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
    log.close()

    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        after = census(m)
    fa = flags_of(after)
    diff = {i: (fb[i], fa[i]) for i in fb if fb[i] != fa[i]}
    text = open(lpath, errors="replace").read()
    ev = parse(text)
    with open(os.path.join(EVID, f"{a.tag}_seq.jsonl"), "w") as fh:
        for d in ev:
            fh.write(json.dumps(d) + "\n")
    with open(os.path.join(EVID, f"{a.tag}_census.json"), "w") as fh:
        json.dump({"before": fb, "after": fa, "diff": diff}, fh)

    sw = [d for d in ev if d["tag"] == "SW573"]
    ent = [d for d in ev if d["tag"] == "SWENTER"]
    marks = [d for d in ev if d["tag"] == "MARKHIGH"]
    clrs = [d for d in ev if d["tag"] == "CLR4"]
    facs = sorted({d["fac"] for d in sw})
    owners = sorted({d["owner"] for d in ent})
    print(f"SW573 visits {len(sw)} facs {facs} idx "
          f"{[(d['fac'], d['idx']) for d in sw][:12]}", flush=True)
    print(f"SWENTER {len(ent)} owners {owners} "
          f"{[(d['owner'], d['tid'], d['mode'], hex(d['ret'])) for d in ent][:12]}", flush=True)
    print(f"CLR4 {len(clrs)} MARKHIGH {len(marks)} census flag-diffs {diff}", flush=True)

    g1 = len(sw) >= 1 and len(ent) >= 1
    g2 = bool(sw) and all(0 <= d["fac"] <= 7 for d in sw)
    g3 = bool(sw) and all(0 <= d["idx"] < 512 and (d["idx"] // 64 in (0, d["fac"])) for d in sw)
    pair_ok, g4 = True, bool(ent)
    for d in ent:
        if d["ret"] != SITE_SWEEP_CALL + 5:
            continue
        g4 = True
        if d["owner"] != d["owner"]:
            pass
        if not (0 <= d["owner"] <= 7 and (d["tid"] // 64 in (0, d["owner"]))):
            pair_ok = False
    from collections import deque
    q = deque(sw)
    match_ok = True
    ents = [d for d in ent if d["ret"] == SITE_SWEEP_CALL + 5]
    for d in ents:
        while q and q[0]["fac"] != d["owner"]:
            q.popleft()
        if not q:
            match_ok = False
            break
        q.popleft()
    g4 = bool(ents) and pair_ok and match_ok
    hi_live = [d for d in sw if d["fac"] >= 4 and d["idx"] >= 256
               and (after[d["idx"]]["name"] or after[d["idx"]]["flags"])]
    g5 = bool(hi_live)
    swept = set(facs) | set(owners)
    bad = {i: v for i, v in diff.items() if i >= 256 and i // 64 not in swept}
    g6 = not bad
    gates = [("G1 visits seen", g1), ("G2 esi is a faction (0..7)", g2),
             ("G3 index band in {0, esi}", g3),
             ("G4 sweep entry (owner,tid) matches, owner in 0..7", g4),
             ("G5 a band>=256 record is live", g5), ("G6 diffs only in swept bands", g6)]
    for name, ok in gates:
        print(f"  {'PASS' if ok else 'FAIL'} {name}")
    ok = all(g[1] for g in gates)
    print(f"{'PASS' if ok else 'FAIL'} {a.tag}: {len(sw)} sweep-call visits facs {facs}, "
          f"{len(ents)} sweep entries owners {owners}, {len(marks)} MARKHIGH, "
          f"{len(diff)} census flag-diffs {sorted(diff.items())[:8]}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
