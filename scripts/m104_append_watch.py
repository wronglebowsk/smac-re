#!/usr/bin/env python3
"""M104 — who APPENDS entries to the per-faction record block 0x927a9c + fac*1436?

M103 proved the block's TYPE==3 entries ARE the source of the research-multiplier array
D [fac*8380+0x94d700] (rebuild-from-zero + `add [ecx*4+0x94d700],ebx` at 0x59ec68) and that the
rebuild runs ONLY on the setup/new-fac paths.  The open question is the PRODUCER of the entries:
M101 saw D drift +10 for facs 1-7 across rounds, which can only mean the record list changed.

LAYOUT (instruction bytes, scratch/m71/dis.py 0x59ec00, and live /proc reads scratch/m104/probe.py):
count at base+0x00, then THREE parallel 8-slot arrays stride 4: TYPE at +0x04, KEY at +0x24,
VAL at +0x44 (FUN_0059ec00 reads TYPE at [p-0x20], KEY at [p], VAL at [p+0x20] off p = base+0x24).
Live counts at m54b_clean r51: fac0 0, fac1 6, fac2 5, fac3 4, fac4 3, fac5 4, fac6 5, fac7 3.

A grep of the WHOLE .text for the displacements 0x927a9c / 0x927aa0 / 0x927ac0 / 0x927ae0 finds
27 + 2 + 17 mentions and NOT ONE of them is a store: every one is `mov reg,[x+disp]` / `cmp` in a
scan loop (0x40d9f4, 0x4e4cd9, 0x4f37b3, 0x4f3e5d, 0x4f47ba, 0x4fcdf3, 0x508c50, 0x522ad4, 0x589089,
0x5a0087, 0x5a0443, 0x5a1689, 0x5a78d0).  So the writer reaches the fields through a POINTER form
the displacement grep cannot see (the M97/M103 lesson) — the instrument is therefore a HARDWARE
WATCHPOINT on the count dword itself, which reports the access that changed the value whatever the
addressing form (and reports pc = store + instruction length).

THE TEST: watch the count of facs 1, 3 and 6 (4 bytes each) plus a CONTROL watchpoint on fac3's
research accumulator [fac*8380+0x94d7f8], proven by M99 to change once per round.  Silent bps: the
D-rebuild entry 0x59ec00 (does the rebuild run mid-window after an append?) and the clamp loop's
count read 0x5a1689 (is the record block walked at all?).  Drive >= 2 round boundaries with a
facility completion queued at Korolev Center (our fac3 base, m57_ui_enqueue item 2), read the whole
block back from /proc/pid/mem afterwards, and compare the model to live D per the frozen-block law.

MODEL A (a mid-game appender exists): >= 1 count-change event, pc contained in a named function,
count read back above the baseline, and — if the rebuild never ran — live D still equal to the
PRE-window model (the append has no effect until a rebuild).
MODEL B (the list is scenario-static): zero count-change events while the control watchpoint and
the walk bps both fire.  The two models disagree on G5, so the shape discriminates.

  python3 scripts/m104_append_watch.py --tag m104w1 --boundaries 3
"""
import argparse
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
import m99_param2 as P  # noqa: E402  (STRIDE, CP, ROUND, contain, load_funcs)

ROOT = os.path.dirname(HERE)
EVID = os.path.join(ROOT, "evidence")
SCRATCH = os.path.join(ROOT, "scratch")
S = P.STRIDE
RB, RS = 0x927a9c, 1436
TYPE_OFF, KEY_OFF, VAL_OFF, MAXE = 0x04, 0x24, 0x44, 8
DB, ND, ACC = 0x94d700, 11, 0x94d7f8
WFACS = [1, 3, 6]
CTRL_FAC = 3
ENT_PC, WALK_PC = 0x59ec00, 0x5a1689
CALLERS = [0x4dbf6f, 0x4e061b, 0x57ce48, 0x57eee0]
RND, CPP = "*(int *)0x985afc", "*(int *)0x985dcc"
HUMAN = 3

TMPL = r"""set pagination off
set confirm off
set can-use-hw-watchpoints 1
@@BLOCKS@@printf "ARMED @@NW@@ hw watchpoints at @@ADDRS@@ and @@NB@@ silent bps at @@BPS@@\n"
continue
"""

WBLOCK = r"""watch *(int *)@@A@@
commands
silent
printf "@@LINE@@\n"@@ARGS@@
continue
end
"""

BPU = r"""break *@@PC@@
commands
silent
printf "@@LINE@@\n"@@ARGS@@
continue
end
"""


def cnt_addr(f):
    return RB + f * RS


def gdb_script():
    blocks, addrs, pcs, n = [], [], [], 0

    def chk(line, args):
        if len(re.findall(r"%[dx]", line)) != len(args):
            raise SystemExit("printf arg count %d != specs %d: %s"
                             % (len(args), len(re.findall(r"%[dx]", line)), line))

    for f in WFACS:
        a = cnt_addr(f)
        # gdb's $old/$new are NOT reliable on Linux hardware watchpoints: print the value AT the
        # stop (the change already landed) plus the pc the watchpoint reports (= store + insn len).
        line = ("M104W CNT fac=%d new=%%d pc=0x%%x round=%%d cp=%%d" % f)
        args = ["*(int *)%#x" % a, "$pc", RND, CPP]
        chk(line, args)
        addrs.append("%#x" % a)
        blocks.append(WBLOCK.replace("@@A@@", "%#x" % a).replace("@@LINE@@", line)
                      .replace("@@ARGS@@", "".join(", " + x for x in args)))
        n += 1
    a = ACC + CTRL_FAC * S
    line = ("M104W ACC fac=%d new=%%d pc=0x%%x round=%%d cp=%%d" % CTRL_FAC)
    args = ["*(int *)%#x" % a, "$pc", RND, CPP]
    chk(line, args)
    addrs.append("%#x" % a)
    blocks.append(WBLOCK.replace("@@A@@", "%#x" % a).replace("@@LINE@@", line)
                  .replace("@@ARGS@@", "".join(", " + x for x in args)))
    n += 1
    for pc in [ENT_PC] + CALLERS:
        line = "M104S ENT pc=0x%x arg=%%d round=%%d cp=%%d" % pc
        args = ["*(int *)($esp+4)", RND, CPP]
        chk(line, args)
        pcs.append("%#x" % pc)
        blocks.append(BPU.replace("@@PC@@", "%#x" % pc).replace("@@LINE@@", line)
                      .replace("@@ARGS@@", "".join(", " + x for x in args)))
    line = "M104S WALK pc=0x%x off=%%d cnt=%%d round=%%d cp=%%d" % WALK_PC
    args = ["$eax", "*(int *)($eax+0x927a9c)", RND, CPP]
    chk(line, args)
    pcs.append("%#x" % WALK_PC)
    blocks.append(BPU.replace("@@PC@@", "%#x" % WALK_PC).replace("@@LINE@@", line)
                  .replace("@@ARGS@@", "".join(", " + x for x in args)))
    return (TMPL.replace("@@BLOCKS@@", "".join(blocks)).replace("@@NW@@", str(n))
            .replace("@@ADDRS@@", " ".join(addrs)).replace("@@NB@@", str(len(pcs))
                                                           ).replace("@@BPS@@", " ".join(pcs)))


KV = re.compile(r"^(M104W) (CNT|ACC)((?: [a-z][a-z0-9_]*=-?[\dxa-f]+)+) round=(\d+) cp=(\d+)\s*$")
KS = re.compile(r"^(M104S) (ENT|WALK)((?: [a-z][a-z0-9_]*=-?[\dxa-f]+)+) round=(\d+) cp=(\d+)\s*$")
OK_LINE = re.compile(r"^(ARMED |0x[0-9a-f]+ in |\[New LWP |\[Thread |\[Switching to |"
                     r"Thread \d+ |This is not |^\$[0-9]+ = |^Continue|^\^|warning:|Cannot "
                     r"breakpoint|Breakpoint \d+ at |Hardware watchpoint \d+: |"
                     r"Watchpoint \d+: |Delete the |$)")


def parse(text):
    ev, bad = [], []
    for ln in text.splitlines():
        ln = ln.rstrip()
        if not ln:
            continue
        m = KV.match(ln) or KS.match(ln)
        if m:
            d = {"kind": m.group(2)}
            for tok in m.group(3).split():
                k, v = tok.split("=", 1)
                d[k] = int(v, 16) if v.startswith("0x") else int(v)
            d["round"], d["cp"] = int(m.group(4)), int(m.group(5))
            ev.append(d)
        elif not OK_LINE.match(ln):
            bad.append(ln)
    return ev, bad


def read_block(fd, pid, f):
    a = cnt_addr(f)
    cnt = struct.unpack("<i", M.rd(fd, a, 4))[0]
    ent = []
    for i in range(max(cnt, 0)):
        t = struct.unpack("<i", M.rd(fd, a + TYPE_OFF + 4 * i, 4))[0]
        k = struct.unpack("<i", M.rd(fd, a + KEY_OFF + 4 * i, 4))[0]
        v = struct.unpack("<i", M.rd(fd, a + VAL_OFF + 4 * i, 4))[0]
        ent.append((t, k, v))
    d = list(struct.unpack("<%di" % ND, M.rd(fd, DB + f * S, 4 * ND)))
    return cnt, ent, d


def model_of(ent):
    m = {}
    for t, k, v in ent:
        if t == 3:
            m[k] = m.get(k, 0) + v
    return [m.get(i, 0) for i in range(ND)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m104w1")
    ap.add_argument("--boundaries", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=140)
    a = ap.parse_args()

    pid = M.find_pid()
    funcs = P.load_funcs()
    with open("/proc/%d/mem" % pid, "rb", 0) as mm:
        base = {f: read_block(mm, pid, f) for f in range(8)}
        raw = {f: bytes(M.rd(mm, cnt_addr(f), 100)) for f in range(8)}
        rnd0 = struct.unpack("<i", M.rd(mm, P.ROUND, 4))[0]
    for f in WFACS:
        cnt, ent, d = base[f]
        print("fac%d count=%d model=%s live D=%s %s" %
              (f, cnt, model_of(ent), d, "MATCH" if model_of(ent) == d else "STALE"))
    gpath = os.path.join(SCRATCH, "%s.gdb" % a.tag)
    lpath = os.path.join(EVID, "%s.gdblog" % a.tag)
    os.makedirs(SCRATCH, exist_ok=True)
    open(gpath, "w").write(gdb_script())
    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=log, stderr=subprocess.STDOUT)
    time.sleep(3.0)
    head = open(lpath, "r", errors="replace").read()
    if "ARMED" not in head:
        try:
            os.kill(g.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
        subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
        raise SystemExit("gdb did not arm:\n" + head[-1200:])
    armed = [ln for ln in head.splitlines() if ln.startswith("ARMED")]
    print("armed: %s" % (armed[0][:160] if armed else "<none>"), flush=True)

    for k in range(a.boundaries):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "smac_play.py"),
                            "--turns", "1", "--timeout", str(a.timeout), "--no-escape", "3000",
                            "--orders-per-turn", "1", "--verbose", "--tag", "%s_r%d" % (a.tag, k)],
                           capture_output=True, text=True)
        print("  boundary %d: rc=%d %s" % (k, r.returncode,
              (r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "")), flush=True)
        time.sleep(2)
    waited = 0
    while waited < 120:
        with open("/proc/%d/mem" % pid, "rb", 0) as mm:
            cp = struct.unpack("<i", M.rd(mm, P.CP, 4))[0]
        if cp == HUMAN:
            break
        time.sleep(2)
        waited += 2
    print("  settle: cp back to fac%d after %ds" % (HUMAN, waited), flush=True)
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

    text = open(lpath, "r", errors="replace").read()
    ev, bad = parse(text)
    cnt_e = [e for e in ev if e["kind"] == "CNT"]
    acc_e = [e for e in ev if e["kind"] == "ACC"]
    ent_e = [e for e in ev if e["kind"] == "ENT"]
    walk_e = [e for e in ev if e["kind"] == "WALK"]
    tracer = subprocess.run(["grep", "-m1", "TracerPid", "/proc/%d/status" % pid],
                            capture_output=True, text=True).stdout.split()[-1]
    with open("/proc/%d/mem" % pid, "rb", 0) as mm:
        fin = {f: read_block(mm, pid, f) for f in range(8)}
        rnd1 = struct.unpack("<i", M.rd(mm, P.ROUND, 4))[0]
    with open(os.path.join(SCRATCH, "%s_seq.jsonl" % a.tag), "w") as fh:
        for e in ev:
            fh.write(json.dumps(e) + "\n")

    gates = []

    def gate(name, ok, detail):
        gates.append((name, bool(ok), detail))

    def contain_of(addr):
        return P.contain(addr, funcs)

    gate("G1-4-watchpoints-armed", " %d hw watchpoints at " % (len(WFACS) + 1) in head,
         "armed: %s" % (armed[0][:120] if armed else "<none>"))
    gate("G2-rounds-moved", rnd1 - rnd0 >= a.boundaries, "round %d -> %d" % (rnd0, rnd1))
    gate("G3-acc-control-fires", len(acc_e) >= a.boundaries,
         "%d ACC events pcs=%s (same machinery logs a count change)"
         % (len(acc_e), sorted({"%#x" % e["pc"] for e in acc_e})))
    walked = {}
    for e in walk_e:
        f = e["off"] // RS
        if 0 <= f < 8 and e["off"] % RS == 0:
            walked.setdefault(f, set()).add(e["cnt"])
    gate("G4-block-walked", len(walk_e) >= a.boundaries and bool(walked),
         "%d WALK events; factions seen %s" % (len(walk_e), sorted(walked)))
    gate("G5-no-midgame-append", not cnt_e,
         "%d count-change events %s" % (len(cnt_e),
         ["fac%d ->%d pc=0x%x r%d" % (e["fac"], e["new"], e["pc"], e["round"]) for e in cnt_e[:8]]))
    moved = ["fac%d %d->%d" % (f, base[f][0], fin[f][0]) for f in range(8) if fin[f][0] != base[f][0]]
    gate("G6-counts-read-back-static", not moved,
         "counts after=%s %s" % ([fin[f][0] for f in range(8)], moved or "all unchanged"))
    badD = []
    for f in WFACS:
        if model_of(base[f][1]) != base[f][2]:
            badD.append("fac%d baseline model %s != D %s" % (f, model_of(base[f][1]), base[f][2]))
        if model_of(fin[f][1]) != fin[f][2]:
            badD.append("fac%d after model %s != D %s" % (f, model_of(fin[f][1]), fin[f][2]))
    gate("G7-model-eq-live-D", not badD,
         "; ".join(badD) or "3/3 at both ends (the frozen-block law holds)")
    gate("G8-rebuild-never-runs", not ent_e,
         "%d rebuild/caller events %s" % (len(ent_e),
         ["pc=%#x arg=%d" % (e["pc"], e["arg"]) for e in ent_e[:6]]))
    spath = os.environ.get("SMAC_SAVE_PATH",
                           os.path.join(ROOT, "programs", "saves", "m54b_clean.SAV"))
    save = open(spath, "rb").read() if os.path.exists(spath) else b""
    hits = {f: save.find(bytes(raw[f])) for f in (1, 3, 6)}
    stride_ok = all(v >= 0 for v in hits.values()) and \
        hits[6] - hits[3] == 3 * RS and hits[3] - hits[1] == 2 * RS
    gate("G9-save-carries-blocks", bool(save) and stride_ok,
         "%s hits=%s consecutive-at-stride-1436=%s"
         % (os.path.basename(spath), {f: hex(v) for f, v in hits.items()}, stride_ok))
    gate("G10-zero-unparsed", not bad, "%d unparsed %s" % (len(bad), bad[:3]))
    gate("G11-detached-clean", tracer == "0", "TracerPid=%s" % tracer)
    errl = [ln for ln in text.splitlines() if "Error" in ln or "Aborting" in ln]
    gate("G12-no-gdb-errors", not errl, "%d error lines %s" % (len(errl), errl[:2]))

    print("count trace (factions the walk bps reached, count values seen):")
    for f in sorted(walked):
        print("  fac%d distinct=%d %s" % (f, len(walked[f]), sorted(walked[f])))
    print("\n=== ACCEPTANCE %s ===" % a.tag)
    ok = 0
    for name, good, detail in gates:
        print("%-28s %s  %s" % (name, "PASS" if good else "FAIL", detail))
        ok += good
    print("%d/%d gates green" % (ok, len(gates)))
    print("context: gdb log %s; ACC writer mapped to %s"
          % (lpath, sorted({str(contain_of(e["pc"])) for e in acc_e})))
    return 0 if ok == len(gates) else 1


def contain_of(addr, funcs):
    return P.contain(addr, funcs)


if __name__ == "__main__":
    sys.exit(main())
