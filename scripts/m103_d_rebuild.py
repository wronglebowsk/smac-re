#!/usr/bin/env python3
"""M103 — who WRITES [fac*8380+0x94d700] (the 11-dword D array that feeds the research multiplier)?

STATIC (this session, instruction bytes scratch/m71/dis.py 0x59ec00 and 0x5a0430):
  FUN_0059ec00(fac): 0x59ec18 lea edi,[ecx*4+0x94d700] (ecx = fac*2095); 0x59ec24 rep stos
  DWORD PTR es:[edi],eax (0xb dwords, eax=0) = ZERO the 11; then count = [0x927a9c+fac*1436],
  entry ptr = 0x927ac0+fac*1436 stride 4, TYPE at [e-0x20], KEY at [e], VAL at [e+0x20];
  for each entry with TYPE==3: 0x59ec68 `add DWORD PTR [ecx*4+0x94d700],ebx` (ecx = fac*2095+key,
  ebx = val).  FUN_0059ec90 (the setup/reset function) carries the SAME block inline: rep stos
  0x5a043e, `add [ecx*4+0x94d700],esi` 0x5a0471 (ecx = fac*2095+key, esi = val).  A grep of the
  whole .text for 0x94d700 finds ONLY these stores; every other mention is a load (FUN_004b3050,
  FUN_004b47f0, FUN_004e47d0, FUN_00535c60 read it; FUN_005a15a0 adds it into block A at 0x5a179e).
  Callers of FUN_0059ec00: 0x4dbf6f (FUN_004dbf40, the s_RESETALLFAC cheat, UI message 0x30077),
  0x4e061b (FUN_004e03d0, message 0x30075), 0x57ce48 (FUN_0057c550) and 0x57eee0 (FUN_0057ecf0) —
  the new-faction/setup paths (the loop copies a 1436-byte template per faction, iVar9 < 8).

THE TEST (one variable at a time, discriminating):
  baseline: the model  D[key] = sum(val of type-3 entries)  computed from the LIVE record lists
  must equal live D for all 8 factions (it does: 8/8, scratch/m103/probe.py).
  Then POKES set fac3's and fac6's 11 D dwords to model+77.  MODEL "a per-round writer runs":
  ENT/ADD/RESET events before the controlled call and the sentinel gone.  MODEL "the writer runs
  ONLY on the setup paths": zero ENT/ADD/RESET/TWIN/SITE events in the round window, the sentinel
  STILL in place (and CONSUMED — the DADD at 0x5a179e prints it), and an inferior call
  `call (int (*)(int))0x59ec00(3)` at the STOP bp 0x520909 fires the ENT + the reset + exactly the
  type-3 ADD events and restores fac3 to the model while fac6 (never called) keeps the sentinel.
  The two models disagree on every gate -> the shape discriminates.

  python3 scripts/m103_d_rebuild.py --predict
  python3 scripts/m103_d_rebuild.py --tag m103d1 --boundaries 2
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
import m99_param2 as P  # noqa: E402  (helpers: STRIDE/load_funcs/contain/ROUND/CP/MASK)

ROOT = os.path.dirname(HERE)
EVID = os.path.join(ROOT, "evidence")
SCRATCH = os.path.join(ROOT, "scratch")
S = P.STRIDE                      # 8380
DB, RB, RS = 0x94d700, 0x927a9c, 1436
TYPE_OFF, KEY_OFF, VAL_OFF = 0x04, 0x24, 0x44
ND = 11
POKED = [3, 6]
CALL_FAC = 3
ADD_SENT = 77
ENT_PC, ENT2_PC = 0x59ec00, 0x59ec90
RESET_PC, ADD_PC = 0x59ec26, 0x59ec68          # reset reported AFTER the rep stos
TWIN_RESET_PC, TWIN_ADD_PC = 0x5a0440, 0x5a0471
DADD_PC, STOP_PC = 0x5a179e, 0x520909
SITES = [0x4dbf6f, 0x4e061b, 0x57ce48, 0x57eee0]
RND, CPP = "*(int *)0x985afc", "*(int *)0x985dcc"
KV = re.compile(r"^(M103S) (ENT|ADD|RESET|DADD|SITE|STOP|CALL)"
                r"((?: [a-z][a-z0-9_]*=-?[\dxa-f]+)+) round=(\d+) cp=(\d+)\s*$")
OK_LINE = re.compile(r"^(ARMED |0x[0-9a-f]+ in |\[New LWP\]|\[Thread |\[Switching to |"
                     r"Thread \d+ |This is not |^\$[0-9]+ = |^Continue|^\^|warning:|Cannot "
                     r"breakpoint|Breakpoint \d+ at |Clearing breakpoint|$)")


def daddr(f, i=0):
    return DB + f * S + 4 * i


def rec_block(f):
    """(count, [(type,key,val)...]) for the record list at 0x927a9c + fac*1436."""
    cnt = P_i32_at(RB + f * RS)
    ent = []
    for i in range(max(cnt, 0)):
        ent.append((P_i32_at(RB + f * RS + TYPE_OFF + 4 * i),
                    P_i32_at(RB + f * RS + KEY_OFF + 4 * i),
                    P_i32_at(RB + f * RS + VAL_OFF + 4 * i)))
    return cnt, ent


def model_of(ent):
    m = {}
    for t, k, v in ent:
        if t == 3:
            m[k] = m.get(k, 0) + v
    return [m.get(i, 0) for i in range(ND)]


_MEM = None


def P_i32_at(a):
    _MEM.seek(a)
    return struct.unpack("<i", _MEM.read(4))[0]


def rd_all(pid):
    """live D[8], record lists, mults, round/cp/mask."""
    global _MEM
    _MEM = open("/proc/%d/mem" % pid, "rb", 0)
    out = {"round": P_i32_at(P.ROUND), "cp": P_i32_at(P.CP), "mask": P_i32_at(P.MASK) & 0xff}
    out["mult"] = {f: P_i32_at(P.MULT + f * S) for f in range(8)}
    out["D"] = {f: [P_i32_at(daddr(f, i)) for i in range(ND)] for f in range(8)}
    out["rec"] = {f: rec_block(f) for f in range(8)}
    _MEM.close()
    return out


TMPL = r"""set pagination off
set confirm off
@@BLOCKS@@printf "ARMED @@NB@@ silent bps at @@BPS@@\n"
continue
call (int (*)(int))@@FUNC@@(@@FAC@@)
printf "M103S CALL fac=@@FAC@@ done=1 round=%d cp=%d\n", @@RND@@, @@CPP@@
clear *@@STOP@@
continue
"""

BPTPL = r"""break *@@PC@@ if @@COND@@
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
BPN = r"""break *@@PC@@ if @@COND@@
commands
silent
printf "@@LINE@@\n",@@ARGS@@
end
"""


def gdb_script(st):
    blocks, pcs = [], []

    def add(tpl, pc, cond, line, args):
        pcs.append("%#x" % pc)
        blocks.append(tpl.replace("@@PC@@", "%#x" % pc).replace("@@COND@@", cond)
                      .replace("@@LINE@@", line)
                      .replace("@@ARGS@@", "".join(", " + a for a in args)))

    # any execution of the two writers (unconditional -> catches every faction)
    add(BPU, ENT_PC, "", "M103S ENT pc=0x59ec00 fac=%d ret=0x%%x round=%%d cp=%%d" % -1,
        ["*(int *)($esp+4)", "*(int *)($esp)", RND, CPP])
    blocks[-1] = blocks[-1].replace("fac=-1 ", "fac=%d ")
    add(BPU, ENT2_PC, "", "M103S ENT pc=0x59ec90 a0=0x%%x arg1=%d round=%%d cp=%%d" % -1,
        ["*(int *)($esp+4)", "*(int *)($esp+8)", RND, CPP])
    blocks[-1] = blocks[-1].replace("arg1=-1 ", "arg1=%d ")
    for f in POKED:
        lo, base = f * 2095, daddr(f)
        add(BPTPL, RESET_PC, "$edi==%#x" % (base + 4 * ND),
            "M103S RESET fac=%d base=0x%%x %s round=%%d cp=%%d"
            % (f, " ".join("v%d=%%d" % i for i in range(ND))),
            ["%#x" % base] + ["*(int *)%#x" % (base + 4 * i) for i in range(ND)] + [RND, CPP])
        add(BPTPL, ADD_PC, "($ecx>=%d && $ecx<=%d)" % (lo, lo + ND - 1),
            "M103S ADD fac=%d key=%%d old=%%d val=%%d round=%%d cp=%%d" % f,
            ["$ecx-%d" % lo, "*(int *)($ecx*4+0x94d700)", "$ebx", RND, CPP])
        add(BPTPL, TWIN_RESET_PC, "$edi==%#x" % (base + 4 * ND),
            "M103S RESET fac=%d base=0x%%x twin=1 %s round=%%d cp=%%d"
            % (f, " ".join("v%d=%%d" % i for i in range(ND))),
            ["%#x" % base] + ["*(int *)%#x" % (base + 4 * i) for i in range(ND)] + [RND, CPP])
        add(BPTPL, TWIN_ADD_PC, "($ecx>=%d && $ecx<=%d)" % (lo, lo + ND - 1),
            "M103S ADD fac=%d key=%%d val=%%d twin=1 round=%%d cp=%%d" % f,
            ["$ecx-%d" % lo, "$esi", RND, CPP])
        add(BPTPL, DADD_PC, "$eax==%#x" % (P.MULT + f * S),
            "M103S DADD fac=%d dest=0x%%x old=%%d src=%%d round=%%d cp=%%d" % f,
            ["$eax", "*(int *)($eax)", "$edi", RND, CPP])
    for pc in SITES:
        add(BPU, pc, "", "M103S SITE pc=0x%x n=1 round=%%d cp=%%d" % pc, [RND, CPP])
    blocks.append(BPN.replace("@@PC@@", "%#x" % STOP_PC).replace("@@COND@@", "$edi==%d" % CALL_FAC)
                   .replace("@@LINE@@", "M103S STOP fac=%d round=%%d cp=%%d" % CALL_FAC)
                   .replace("@@ARGS@@", ", ".join(["$edi", RND, CPP])))
    return (TMPL.replace("@@BLOCKS@@", "".join(blocks))
            .replace("@@NB@@", str(len(pcs))).replace("@@BPS@@", " ".join(pcs))
            .replace("@@FUNC@@", "%#x" % ENT_PC).replace("@@FAC@@", str(CALL_FAC))
            .replace("@@RND@@", RND).replace("@@CPP@@", CPP)
            .replace("@@STOP@@", "%#x" % STOP_PC))


def parse(text):
    """Events are OUR protocol lines only; an M103S line that fails the grammar is UNPARSED.
    gdb chatter is not protocol, but any line carrying an error is surfaced for inspection."""
    ev, unparsed, noise = [], [], []
    for ln in text.splitlines():
        ln = ln.rstrip()
        if ln.startswith("M103S "):
            m = KV.match(ln)
            if m:
                fields = dict(kv.split("=", 1) for kv in m.group(3).split())
                for k, v in fields.items():
                    fields[k] = int(v, 0)
                ev.append((m.group(2), fields, int(m.group(4)), int(m.group(5))))
                continue
            unparsed.append(ln)
        elif re.search(r"Error|Cannot|Invalid|not defined|no source|Traceback", ln):
            noise.append(ln)
    return ev, unparsed, noise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boundaries", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--tag", default="m103d1")
    ap.add_argument("--predict", action="store_true")
    a = ap.parse_args()

    pid = M.find_pid()
    st = rd_all(pid)
    human = (st["mask"] & -st["mask"]).bit_length() - 1
    print("pid %d round %d cp %d mask %#x human fac%d" % (pid, st["round"], st["cp"], st["mask"],
                                                          human), flush=True)
    print("--- baseline: the PREDICTION table (model vs live D, computed before the run) ---",
          flush=True)
    base_ok = []
    for f in range(8):
        cnt, ent = st["rec"][f]
        mdl = model_of(ent)
        t3 = [(t, k, v) for t, k, v in ent if t == 3]
        base_ok.append(mdl == st["D"][f])
        print("  fac %d cnt %2d D %-42s model %-42s match=%s type3=%s"
              % (f, cnt, st["D"][f], mdl, mdl == st["D"][f], t3), flush=True)
    sentinel = {f: [st["D"][f][i] + ADD_SENT for i in range(ND)] for f in POKED}
    print("  MODEL per-round-writer: ENT/ADD/RESET before the call, sentinel gone.  "
          "MODEL setup-only: 0 ENT/ADD/RESET/SITE before the call, sentinel CONSUMED at 0x5a179e "
          "and STILL there, and the call restores fac%d to the model." % CALL_FAC, flush=True)
    if a.predict:
        return

    gpath = os.path.join(SCRATCH, "%s.gdb" % a.tag)
    lpath = os.path.join(EVID, "%s.gdblog" % a.tag)
    os.makedirs(SCRATCH, exist_ok=True)
    open(gpath, "w").write(gdb_script(st))
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
    print("armed: %s" % (armed[0][:120] if armed else "<none>"), flush=True)

    def poke(addr, value):
        with open("/proc/%d/mem" % pid, "rb+", 0) as mm:
            mm.seek(addr)
            mm.write(struct.pack("<i", value))
            mm.seek(addr)
            return struct.unpack("<i", mm.read(4))[0]

    landed = []
    for f in POKED:
        for i in range(ND):
            got = poke(daddr(f, i), sentinel[f][i])
            landed.append(got == sentinel[f][i])
    print("  POKE facs %s -> model+%d, %d/%d landed" % (POKED, ADD_SENT, sum(landed),
                                                        len(landed)), flush=True)
    rc_ok = True
    for k in range(a.boundaries):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "smac_play.py"),
                            "--turns", "1", "--timeout", str(a.timeout), "--no-escape", "3000",
                            "--orders-per-turn", "1", "--verbose", "--tag", "%s_r%d" % (a.tag, k)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            rc_ok = False
        print("  boundary %d: rc=%d %s" % (k, r.returncode,
              (r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "")), flush=True)
    waited = 0
    while waited < 90:
        with open("/proc/%d/mem" % pid, "rb", 0) as mm:
            cp = struct.unpack("<i", M.rd(mm, P.CP, 4))[0]
        if cp == human:
            break
        time.sleep(2)
        waited += 2
    print("  settle: cp back to fac%d after %ds" % (human, waited), flush=True)
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
    fin = rd_all(pid)
    # restore the control faction (fac6) to the model; fac3 was restored by the writer itself
    restored = []
    for f in POKED:
        cnt, ent = fin["rec"][f]
        for i in range(ND):
            got = poke(daddr(f, i), model_of(ent)[i])
            restored.append(got == model_of(ent)[i])
    fin2 = rd_all(pid)
    print("  after: round %d tracer %s; restore %d/%d" % (fin2["round"], tracer, sum(restored),
                                                          len(restored)), flush=True)
    text = open(lpath, "r", errors="replace").read()
    ev, unparsed, noise = parse(text)
    open(os.path.join(SCRATCH, "%s_seq.jsonl" % a.tag), "w").write(
        "\n".join(json.dumps([t, f, r, c]) for t, f, r, c in ev))

    stop_i = next((i for i, (t, f, r, c) in enumerate(ev) if t == "STOP"), None)
    call_i = next((i for i, (t, f, r, c) in enumerate(ev) if t == "CALL"), None)
    pre = [e for i, e in enumerate(ev) if stop_i is not None and i < stop_i]
    post = [e for i, e in enumerate(ev) if stop_i is not None and i > stop_i]
    w3 = model_of(fin["rec"][CALL_FAC])
    t3 = [(t, k, v) for t, k, v in fin["rec"][CALL_FAC][1] if t == 3]
    adds_post = [(f["key"], f["val"]) for t, f, r, c in post if t == "ADD" and f.get("fac") == CALL_FAC
                 and "twin" not in f]
    dadd3_pre = [f["src"] for t, f, r, c in pre if t == "DADD" and f["fac"] == CALL_FAC]
    dadd3_post = [f["src"] for t, f, r, c in post if t == "DADD" and f["fac"] == CALL_FAC]
    dadd6 = [f["src"] for t, f, r, c in ev if t == "DADD" and f["fac"] == 6]
    resets_post = [f for t, f, r, c in post if t == "RESET" and f.get("fac") == CALL_FAC
                   and "twin" not in f]
    gates = [
        ("G1 baseline model == live D for 8/8 factions", sum(base_ok) == 8, "%d/8" % sum(base_ok)),
        ("G2 pokes landed", sum(landed) == len(landed), "%d/%d" % (sum(landed), len(landed))),
        ("G3 sentinel CONSUMED pre-call (DADD src == sentinel)",
         len(dadd3_pre) >= 1 and all(s == sentinel[CALL_FAC][10] for s in dadd3_pre),
         "n=%d src=%s want %d" % (len(dadd3_pre), dadd3_pre, sentinel[CALL_FAC][10])),
        ("G4 NO writer event before the call (setup-only, not per-round)",
         not [e for e in pre if e[0] in ("ENT", "ADD", "RESET")],
         "pre ENT/ADD/RESET=%d" % len([e for e in pre if e[0] in ("ENT", "ADD", "RESET")])),
        ("G5 the STOP bp fired and the inferior call completed",
         stop_i is not None and call_i is not None, "stop=%s call=%s" % (stop_i, call_i)),
        ("G6 the call ran the writer: ENT fac3 + the 11-dword reset",
         any(f.get("fac") == CALL_FAC for t, f, r, c in post if t == "ENT")
         and len(resets_post) >= 1 and all(all(f["v%d" % i] == 0 for i in range(ND))
                                           for f in resets_post),
         "ENT=%d RESET=%d" % (len([e for e in post if e[0] == "ENT"]), len(resets_post))),
        ("G7 ADD events == the live type-3 entries (key,val) exactly",
         sorted(adds_post) == sorted((k, v) for t, k, v in t3),
         "adds=%s entries=%s" % (adds_post, [(k, v) for t, k, v in t3])),
        ("G8 read-back: fac%d D == the model after the call (sentinel undone)" % CALL_FAC,
         fin["D"][CALL_FAC] == w3, "%s vs %s" % (fin["D"][CALL_FAC], w3)),
        ("G9 CONTROL fac6 kept the sentinel (writer ran for the called fac only)",
         fin["D"][6] == sentinel[6] and len(dadd6) >= 1 and all(s == sentinel[6][10] for s in dadd6),
         "D6=%s sentinel=%s src=%s" % (fin["D"][6], sentinel[6], dadd6)),
        ("G10 post-call DADD src == the rebuilt model (the effect is live)",
         len(dadd3_post) >= 1 and all(s == w3[10] for s in dadd3_post),
         "n=%d src=%s want %d" % (len(dadd3_post), dadd3_post, w3[10])),
        ("G11 the 4 real call sites + FUN_0059ec90 + the twin: 0 events",
         not [e for e in ev if e[0] == "SITE" or (e[0] == "ENT" and e[1].get("pc") == 0x59ec90)
              or (e[0] in ("ADD", "RESET") and "twin" in e[1])],
         "SITE=%d twin=%d" % (len([e for e in ev if e[0] == "SITE"]),
                              len([e for e in ev if "twin" in e[1]]))),
        ("G12 rounds moved >= 2 and cp == fac on every rebuild read",
         fin2["round"] - st["round"] >= 2 and all(f.get("cp") == f.get("fac")
                                                  for t, f, r, c in ev if t in ("DADD", "ADD", "RESET")),
         "rounds %d->%d" % (st["round"], fin2["round"])),
        ("G13 tracer 0, 0 unparsed, driver rc 0, restore 22/22",
         tracer == "0" and not unparsed and rc_ok and sum(restored) == len(restored),
         "tracer %s unparsed %d rc %s restore %d/%d" % (tracer, len(unparsed), rc_ok,
                                                        sum(restored), len(restored))),
    ]
    npass = sum(1 for _n, ok, _d in gates if ok)
    for n, ok, d in gates:
        print("%s %s  %s" % ("PASS" if ok else "FAIL", n, d), flush=True)
    print("ACCEPTANCE %s: %s (%d/%d) ENT=%d ADD=%d RESET=%d DADD=%d SITE=%d STOP=%d rounds %d->%d"
          % (a.tag, "PASS" if npass == len(gates) else "FAIL", npass, len(gates),
             len([e for e in ev if e[0] == "ENT"]), len([e for e in ev if e[0] == "ADD"]),
             len([e for e in ev if e[0] == "RESET"]), len([e for e in ev if e[0] == "DADD"]),
             len([e for e in ev if e[0] == "SITE"]), len([e for e in ev if e[0] == "STOP"]),
             st["round"], fin2["round"]), flush=True)
    if unparsed:
        print("UNPARSED: " + " || ".join(unparsed[:6]), flush=True)
    if noise:
        print("GDB-NOISE: " + " || ".join(noise[:8]), flush=True)


if __name__ == "__main__":
    main()
