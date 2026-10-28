#!/usr/bin/env python3
"""M81 ACCEPTANCE (tag m81write1) — WHO WRITES A CREATED RECORD'S +0x30 = 0xc1.

M80: slots 324/325 were EMPTY at window start and read "Impact Squad"/"Impact Rover"
with +0x30 = 0xc1 by the time FUN_00573a90 reached 0x5741f0 (CLR4 pre=0xc1, so the
`and ~4` was a NO-OP); the 32 B copy at 0x5741e1 covers bytes 0..0x1f, so NOTHING
named writes +0x30 on the create path. This run puts 4 HARDWARE watchpoints on the
flag WORDS of the next two free slots (326/327) plus silent breakpoints on the sweep's
create sites (0x5741e1 copy / 0x5741f0 and ~4 / 0x5741fe sweep call) and drives real
boundaries; every store to those flag words reports its pc.

Gates (one real invocation, no floor weakened):
  G1 the log prints ARMED 4 and >= 4 "Hardware watchpoint" lines
  G2 baseline: slots 326/327 EMPTY (no name, owner 0, flag word 0) and 324/325 exist 0xc1
  G3 >= 1 FLAGW event with a real pc (a store to a watched flag WORD happened)
  G4 end census: a watched slot's flag word != 0 read back from /proc/pid/mem
  G5 >= 1 SWCOPY visit whose index is in the watched band (the create path ran)
  G6 the FLAGW pc set vs {0x5741e1,0x5741f0,0x5741fe,0x572800} — print the attribution;
     PASS requires >= 1 store pc OUTSIDE that sweep set (else the sweep wrote it and
     M80's "nothing named writes +0x30" is falsified the other way — report, not silent)
Exit 0 prints PASS.
"""
import argparse, os, re, signal, struct, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import m55_boundary as M
import m56_build as MB
import m74_flag_watch as F

ROOT = F.ROOT
EVID = F.EVID
REC_BASE, STRIDE = 0x98AD88, 52
FLAG_ADDR = 0x98ADB8                    # REC_BASE + 0x30
WATCH = [324, 325, 326, 327]            # the four free faction-5 slots (324/325 are what
#            M80 saw created live; on a FRESH reload all four are EMPTY, so all four are watched
SITES = [(0x5741e1, "SWCOPY"), (0x5741f0, "SWCLR4"), (0x5741fe, "SWCALL")]
SWEEP_SET = {0x5741e1, 0x5741f0, 0x5741fe, 0x572800}
BASE_NAME = "University Base"

TMPL = r"""set pagination off
set confirm off
set can-use-hw-watchpoints 1
@@WATCHES@@@@BPS@@printf "ARMED @@N@@ hw watchpoints at @@ADDRS@@\n"
continue
"""

WBLOCK = r"""watch *(short *)@@A@@
commands
silent
printf "FLAGW tid=@@T@@ pc=0x%x val=0x%x\n", $pc, *(short *)@@A@@
continue
end
"""

BBLOCK = r"""break *@@A@@
commands
silent
printf "TAG@@T@@ idx=%d esi=%d ebx=%d f30=0x%x\n", @@I@@, @@E@@, @@B@@, *(short *)(@@R@@+0x30)
continue
end
"""


def gdb_script():
    blocks, addrs = [], []
    for t in WATCH:
        a = FLAG_ADDR + t * STRIDE
        addrs.append("%#x" % a)
        blocks.append(WBLOCK.replace("@@A@@", "%#x" % a).replace("@@T@@", str(t)))
    bps = []
    # the sweep's create sites: ebx holds idx*52 (m80band1), esi the faction
    regs = {"0x5741e1": ("$ebx", "$ebx + 0x98ad88"), "0x5741f0": ("$ebx", "$ebx + 0x98ad88"),
            "0x5741fe": ("$ebx", "$ebx + 0x98ad88")}
    for i, (addr, tag) in enumerate(SITES):
        e, r = regs["%#x" % addr] if "%#x" % addr in regs else ("$esi", "$ebx + 0x98ad88")
        bps.append(BBLOCK.replace("@@A@@", "%#x" % addr).replace("@@T@@", str(i))
                   .replace("@@I@@", "(%s/52)" % e).replace("@@E@@", "$esi")
                   .replace("@@B@@", e).replace("@@R@@", r))
    return (TMPL.replace("@@WATCHES@@", "".join(blocks)).replace("@@BPS@@", "".join(bps))
            .replace("@@N@@", str(len(WATCH))).replace("@@ADDRS@@", " ".join(addrs)))


LINE = re.compile(r"^(FLAGW tid=(\d+) pc=(0x[0-9a-f]+) val=(0x[0-9a-f]+)"
                  r"|TAG(\d) idx=(-?\d+) esi=(-?\d+) ebx=(-?\d+) f30=(0x[0-9a-f]+))\s*$")


def parse(text):
    ev = []
    for ln in text.splitlines():
        m = LINE.match(ln.strip())
        if m:
            if m.group(2):
                ev.append({"tag": "FLAGW", "tid": int(m.group(2)),
                           "pc": int(m.group(3), 16), "val": int(m.group(4), 16)})
            else:
                ev.append({"tag": SITES[int(m.group(5))][1], "idx": int(m.group(6)),
                           "esi": int(m.group(7)), "ebx": int(m.group(8)),
                           "f30": int(m.group(9), 16)})
    return ev


def slot_state(m, t):
    m.seek(REC_BASE + t * STRIDE)
    b = m.read(STRIDE)
    return dict(name=b[0:20].split(b"\0")[0].decode("latin-1", "replace"),
                owner=b[0x2c], flag=b[0x30] | (b[0x31] << 8),
                raw=b.hex())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boundaries", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--tag", default="m81write1")
    ap.add_argument("--poke-minerals", type=int, default=200)
    a = ap.parse_args()

    pid = F.game_pid()
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        row = F.base_row(m, BASE_NAME)
        base = {t: slot_state(m, t) for t in (324, 325, 326, 327)}
    print(f"pid {pid} base {BASE_NAME!r} addr 0x{row['addr']:x} head {row['slots'][0]} "
          f"pending {row['pending']} storage {row['minerals']}", flush=True)
    for t in (324, 325, 326, 327):
        s = base[t]
        print(f"  slot {t}: name={s['name']!r} owner={s['owner']} flag=0x{s['flag']:04x}",
              flush=True)

    def poke_storage(value):
        with open(f"/proc/{pid}/mem", "rb+", 0) as mm:
            mm.seek(row["addr"] + 0x40)
            mm.write(struct.pack("<i", value))
            mm.seek(row["addr"] + 0x40)
            return struct.unpack("<i", mm.read(4))[0]

    print(f"  storage poked {a.poke_minerals} read back {poke_storage(a.poke_minerals)}",
          flush=True)

    gpath = os.path.join(ROOT, "scratch", f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.gdblog")
    os.makedirs(EVID, exist_ok=True)
    open(gpath, "w").write(gdb_script())
    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath,
                          "-p", str(pid)], stdout=log, stderr=subprocess.STDOUT)
    head = ""
    n_hw = 0
    for _ in range(60):
        head = open(lpath, "r", errors="replace").read()
        n_hw = head.count("Hardware watchpoint")
        if ("ARMED" in head and n_hw >= len(WATCH)) or not os.path.exists("/proc/%d" % g.pid):
            break
        time.sleep(0.5)
    if "ARMED" not in head or n_hw < len(WATCH):
        try:
            os.kill(g.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
        subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
        raise SystemExit(f"gdb did not arm 4 HARDWARE watchpoints (saw {n_hw}):\n"
                         + head[-1200:])
    print(f"armed: {n_hw} hardware watchpoints on flag words of {WATCH}", flush=True)

    t0 = time.time()
    for k in range(a.boundaries):
        poke_storage(a.poke_minerals)
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "smac_play.py"),
                            "--turns", "1", "--timeout", str(a.timeout), "--no-escape",
                            "3000", "--orders-per-turn", "1", "--verbose",
                            "--tag", f"{a.tag}_r{k}"],
                           capture_output=True, text=True)
        print(f"  boundary {k}: rc={r.returncode} t={time.time()-t0:.0f}s "
              f"{r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ''}", flush=True)

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

    text = open(lpath, "r", errors="replace").read()
    ev = parse(text)
    flagw = [e for e in ev if e["tag"] == "FLAGW"]
    copy = [e for e in ev if e["tag"] == "SWCOPY"]
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        after = {t: slot_state(m, t) for t in (324, 325, 326, 327)}
    pcs = sorted({e["pc"] for e in flagw})
    print("FLAGW events:", [(e["tid"], hex(e["pc"]), hex(e["val"])) for e in flagw], flush=True)
    print("SWCOPY visits:", [(e["idx"], e["esi"], hex(e["f30"]), e.get("tag")) for e in copy][:8],
          flush=True)
    for t in (326, 327):
        print(f"  slot {t} after: name={after[t]['name']!r} owner={after[t]['owner']} "
              f"flag=0x{after[t]['flag']:04x} raw={after[t]['raw']}", flush=True)

    g1 = n_hw >= 4
    g2 = all(base[t]["flag"] == 0 and not base[t]["name"] for t in WATCH)
    g3 = len(flagw) >= 1
    g4 = any(after[t]["flag"] != 0 for t in WATCH)
    g5 = any(e["idx"] // 64 == 5 for e in copy)
    outside = [hex(p) for p in pcs if p not in SWEEP_SET]
    g6 = len(outside) >= 1
    res = dict(G1=g1, G2=g2, G3=g3, G4=g4, G5=g5, G6=g6)
    print("store pcs:", [hex(p) for p in pcs], "outside sweep set:", outside, flush=True)
    print("gates:", res, flush=True)
    if all(res.values()):
        print("PASS", flush=True)
        return 0
    print("FAIL", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
