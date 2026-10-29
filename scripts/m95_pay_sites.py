#!/usr/bin/env python3
"""M95 — the pay-site conflict: 0x4f0ca6 (branch B, NAMED "completion path") vs
0x4efedd (branch A, measured live in M71): which pays/activates ONE designed
completion, and from which field.

Static (instruction bytes, s150): FUN_004ef6d0 dispatches per queue item at
0x4ef897: queue[0] >= 0 -> branch A (gate 0x4efa5e cmp [base+0x40],edi; pay
0x4efedd `mov [ecx+0x40],esi` after `sub esi,edi`; create 0x4eff4e; pop via
0x4ef5d0).  queue[0] < 0 -> typecode = -queue[0]; branch B (gate 0x4f0a3d, race
scan, pay 0x4f0ca6 `mov [edx+0x40],esi` after `sub esi,edi`, pop at 0x4f0f46)
when typecode >= 39 unclaimed (or > 34, or the 0x507410 mask test fails).
BOTH branches subtract edi (price) from storage base+0x40; credit base+0xd0
feeds only the income add 0x4ef7f6 and the clamp.  This run proves which site
FIRES for a UI-queued designed completion, with the effect read back.

    python3 scripts/m95_pay_sites.py --tag m95pay1   # PASS/FAIL
"""
import argparse
import bisect
import csv
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

ROOT = os.path.dirname(HERE)
EVID = os.path.join(ROOT, "evidence")
SCRATCH = os.path.join(ROOT, "scratch")
BASE_ARR, BASE_SZ = 0x95DA10, 304
BASE_NAME = os.environ.get("M95_BASE", "University Base")

# tag, addr, cond-which, printf body — cond reg per site (register-only conditions)
BPS = [
    ("DISP",    0x4EF8FA, "edx", '"M95E DISP base=0x%x tc=%d price=%d storage=%d round=%d\\n", $edx, *(int *)($ebp-0x30), $edi, *(int *)($edx+0x40), *(int *)0x985afc'),
    ("GATEA",   0x4EFA61, "ecx", '"M95E GATEA base=0x%x price=%d storage=%d pending=%d q0=%d credit=%d round=%d\\n", $ecx, $edi, *(int *)($ecx+0x40), *(int *)($ecx+0x4c), *(int *)($ecx+0x50), *(int *)($ecx+0xd0), *(int *)0x985afc'),
    ("GATEAF",  0x4EFA63, "ecx", '"M95E GATEAF base=0x%x price=%d storage=%d round=%d\\n", $ecx, $edi, *(int *)($ecx+0x40), *(int *)0x985afc'),
    ("MARK",    0x4EFE67, "mem", '"M95E MARK tid=%d wasunmarked=%d round=%d\\n", $ebx, $edx, *(int *)0x985afc'),
    ("PAYA",    0x4EFED8, "ecx", '"M95E PAYA base=0x%x price=%d storage=%d pending=%d q0=%d credit=%d round=%d\\n", $ecx, $edi, *(int *)($ecx+0x40), *(int *)($ecx+0x4c), *(int *)($ecx+0x50), *(int *)($ecx+0xd0), *(int *)0x985afc'),
    ("POSTA",   0x4EFF32, "esi", '"M95E POSTA base=0x%x storage=%d mirror=%d credit=%d round=%d\\n", $esi, *(int *)($esi+0x40), *(int *)($esi+0x98), *(int *)($esi+0xd0), *(int *)0x985afc'),
    ("CREATE",  0x4EFF4E, "mem", '"M95E CREATE tid=%d owner=%d round=%d\\n", $ebx, *(int *)($ebp-0x28), *(int *)0x985afc'),
    ("GATEB",   0x4F0A40, "edx", '"M95E GATEB base=0x%x tc=%d price=%d storage=%d round=%d\\n", $edx, *(int *)($ebp-0x30), $edi, *(int *)($edx+0x40), *(int *)0x985afc'),
    ("PAYB",    0x4F0CA1, "edx", '"M95E PAYB base=0x%x tc=%d price=%d storage=%d credit=%d round=%d\\n", $edx, *(int *)($ebp-0x30), $edi, *(int *)($edx+0x40), *(int *)($edx+0xd0), *(int *)0x985afc'),
    ("DEFERB",  0x4F0C28, "edx", '"M95E DEFERB base=0x%x tc=%d price=%d round=%d\\n", $edx, *(int *)($ebp-0x30), $edi, *(int *)0x985afc'),
    ("BRET",    0x4F0B86, "edx", '"M95E BRET base=0x%x tc=%d price=%d round=%d\\n", $edx, *(int *)($ebp-0x30), $edi, *(int *)0x985afc'),
    ("CLAIMED", 0x4F07C2, "edx", '"M95E CLAIMED base=0x%x tc=%d price=%d round=%d\\n", $edx, *(int *)($ebp-0x30), $edi, *(int *)0x985afc'),
]
POP_BP = ("POP", 0x4EF5D0, '"M95E POP idx=%d retn=%x round=%d\\n", *(int *)($esp+4), *(int *)($esp), *(int *)0x985afc')
WATCH = [("STOR", 0x40), ("PEND", 0x4C)]

E_LINE = re.compile(r"^M95E (\w+) (.*)$")
W_LINE = re.compile(r"^M95W (\w+) pc=([0-9a-f]+) new=(-?\d+) round=(\d+)\s*$")


def gdb_script(row):
    parts = ["set pagination off", "set confirm off", "set can-use-hw-watchpoints 1"]
    for tag, off in WATCH:
        a = row + off
        parts.append(f"watch *(int *){a:#x}")
        parts.append("commands")
        parts.append("silent")
        parts.append(f'printf "M95W {tag} pc=%x new=%d round=%d\\n", $pc, *(int *){a:#x}, *(int *)0x985afc')
        parts.append("continue")
        parts.append("end")
    for tag, addr, cond, body in BPS:
        c = (f" if ${cond}=={row:#x}" if cond != "mem"
               else f" if *(int *)0x8f0d60=={row:#x}")
        parts.append(f"break *{addr:#x}{c}")
        parts.append("commands")
        parts.append("silent")
        parts.append(f"printf {body}")
        parts.append("continue")
        parts.append("end")
    parts.append(f"break *{POP_BP[1]:#x} if *(int *)($esp+4)=={(row-BASE_ARR)//BASE_SZ}")
    parts.append("commands")
    parts.append("silent")
    parts.append(f"printf {POP_BP[2]}")
    parts.append("continue")
    parts.append("end")
    parts.append(f'printf "ARMED {len(WATCH)} hw and {len(BPS)+1} bp\\n"')
    parts.append("continue")
    return "\n".join(parts) + "\n"


def rd_base(m, row):
    d = M.rd(m, row, 0xA0)
    def i(off):
        return struct.unpack("<i", d[off:off+4])[0] if off + 4 <= len(d) else None
    out = {"storage": i(0x40), "pending": i(0x4C), "q0": i(0x50), "credit": None,
           "flag30": i(0x30)}
    with open(f"/proc/{M.find_pid()}/mem", "rb", 0) as mm:
        mm.seek(row + 0xD0)
        out["credit"] = struct.unpack("<i", mm.read(4))[0]
        mm.seek(row + 0x98)
        out["mirror"] = struct.unpack("<i", mm.read(4))[0]
        mm.seek(0x985AFC)
        out["round"] = struct.unpack("<i", mm.read(4))[0]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m95pay1")
    ap.add_argument("--boundaries", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--poke-minerals", type=int, default=200)
    a = ap.parse_args()

    pid = M.find_pid()
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        n_bases = struct.unpack("<i", M.rd(m, 0x985AF4, 4))[0]
        row = None
        for k in range(min(max(n_bases, 0), 64)):
            rec = M.rd(m, BASE_ARR + k * BASE_SZ, BASE_SZ)
            if rec[19:51].split(b"\0")[0].decode("latin-1", "replace") == BASE_NAME:
                row = BASE_ARR + k * BASE_SZ
                break
        st0 = rd_base(m, row) if row else None
    if row is None:
        raise SystemExit(f"base {BASE_NAME!r} not found")
    print(f"pid {pid} base {BASE_NAME} row {row:#x} pre: {st0}", flush=True)
    if st0["pending"] != 1:
        raise SystemExit(f"pending {st0['pending']} != 1 — enqueue first "
                         f"(m57_ui_enqueue.py --base-index 0 --cell-item 2 --inserts 1)")
    pred = "A(0x4efedd)" if st0["q0"] >= 0 else "B(0x4f0ca6)"
    print(f"PREDICTION from dispatch shape (queue[0]={st0['q0']} sign): pay branch {pred}", flush=True)

    def poke():
        with open(f"/proc/{pid}/mem", "rb+", 0) as mm:
            mm.seek(row + 0x40)
            mm.write(struct.pack("<i", a.poke_minerals))
            mm.seek(row + 0x40)
            return struct.unpack("<i", mm.read(4))[0]

    print(f"storage poked {poke()}", flush=True)
    gpath = os.path.join(SCRATCH, f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.gdblog")
    open(gpath, "w").write(gdb_script(row))
    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath,
                          "-p", str(pid)], stdout=log, stderr=subprocess.STDOUT)
    time.sleep(3.0)
    head = open(lpath, errors="replace").read()
    n_hw = head.count("Hardware watchpoint")
    n_bp = len(re.findall(r"^Breakpoint \d+ at ", head, re.M))
    if "ARMED" not in head or n_hw < len(WATCH) or n_bp < len(BPS) + 1:
        try:
            os.kill(g.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
        subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
        raise SystemExit(f"gdb did not arm (hw={n_hw} bp={n_bp}):\n" + head[-1500:])
    print(f"armed: {n_hw} hw watchpoints, {n_bp} breakpoints", flush=True)

    t0 = time.time()
    rc_ok = True
    for k in range(a.boundaries):
        poke()
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "smac_play.py"),
                            "--turns", "1", "--timeout", str(a.timeout), "--no-escape",
                            "3000", "--orders-per-turn", "1", "--verbose",
                            "--tag", f"{a.tag}_r{k}"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            rc_ok = False
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
    log.close()
    tracer = subprocess.run(["grep", "-m1", "TracerPid", "/proc/%d/status" % pid],
                            capture_output=True, text=True).stdout.split()[-1]

    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        st1 = rd_base(m, row)
    print(f"post: {st1} tracer {tracer}", flush=True)

    ev, unparsed = [], []
    armed = False
    for ln in open(lpath, errors="replace"):
        ln = ln.strip()
        if not ln:
            continue
        mm = E_LINE.match(ln)
        if mm:
            ev.append({"tag": mm.group(1), "fields": mm.group(2)})
            continue
        mm = W_LINE.match(ln)
        if mm:
            ev.append({"tag": "W_" + mm.group(1), "pc": int(mm.group(2), 16),
                       "new": int(mm.group(3)), "round": int(mm.group(4))})
            continue
        if not armed:
            if "ARMED" in ln:
                armed = True
            continue
        if ("Hardware watchpoint" in ln or ln.startswith("[Inferior")
                or re.match(r"^Thread \d+", ln) or "Breakpoint" in ln
                or "debuginfod" in ln.lower() or "This GDB supports" in ln
                or "auto-downloading" in ln
                or "__kernel_vsyscall" in ln or re.match(r"^0x[0-9a-f]+ in ", ln)):
            continue
        unparsed.append(ln)
    with open(os.path.join(SCRATCH, f"{a.tag}_seq.jsonl"), "w") as fh:
        for d in ev:
            fh.write(json.dumps(d) + "\n")

    print(f"--- {len(ev)} events ---")
    for e in ev:
        print("  ", e.get("tag"), e.get("fields", f"pc={e.get('pc') and hex(e['pc'])} new={e.get('new')} round={e.get('round')}"))

    def num(fields, key):
        m = re.search(rf"{key}=(-?\d+)", fields)
        return int(m.group(1)) if m else None

    pays = [e for e in ev if e["tag"] in ("PAYA", "PAYB")]
    pops = [e for e in ev if e["tag"] == "POP"]
    stores = [e for e in ev if e["tag"] == "W_STOR"]
    pend_evs = [e for e in ev if e["tag"] == "W_PEND"]
    # pop-fn containment: stores to pending inside 0x4ef5d0..0x4ef6d0
    g1 = armed and n_hw == len(WATCH) and n_bp == len(BPS) + 1
    g2 = st1["pending"] == 0 and st0["pending"] == 1
    g3 = st1["round"] == st0["round"] + a.boundaries and rc_ok
    g4 = (bool(pays) and all(e["tag"] == "PAYA" for e in pays)
          and not any(e["tag"] == "PAYB" for e in ev)
          and not any(e["tag"] == "W_STOR" and e["pc"] == 0x4F0CA9 for e in ev))
    pay = pays[0] if pays else None
    g5 = False
    if pay:
        price, s_before = num(pay["fields"], "price"), num(pay["fields"], "storage")
        store_pc = 0x4EFEE0 if pay["tag"] == "PAYA" else 0x4F0CA9
        hit = [e for e in stores if e["pc"] == store_pc and e["new"] == s_before - price]
        g5 = bool(hit)
    def hexnum(fields, key):
        m = re.search(rf"{key}=([0-9a-f]+)", fields)
        return int(m.group(1), 16) if m else None
    g6 = (bool(pops) and all(hexnum(e["fields"], "retn") in (0x4EF997, 0x4F0380, 0x4F0F4B)
             for e in pops) and bool(pend_evs)
            and all(0x4EF5D0 <= e["pc"] < 0x4EF6D0 for e in pend_evs))
    g7 = tracer == "0"
    g8 = not unparsed
    g9 = (any(e["tag"] == "PAYA" for e in pays)) != (any(e["tag"] == "PAYB" for e in ev))
    gates = [("G1_armed", g1), ("G2_completion", g2), ("G3_rounds", g3),
             ("G4_pay_is_A_only", g4), ("G5_pay_math", g5), ("G6_pop_activation", g6),
             ("G7_clean", g7), ("G8_clean_log", g8), ("G9_discriminates", g9)]
    for n, v in gates:
        print(f"  {n}: {v}")
    ok = all(v for _n, v in gates)
    print(f"ACCEPTANCE {a.tag}: {'PASS' if ok else 'FAIL'} "
          f"({sum(1 for _n, v in gates if v)}/{len(gates)}) pay={[e['tag'] for e in pays]} "
          f"pop_retn={[hex(hexnum(e['fields'],'retn')) for e in pops]} "
          f"rounds {st0['round']}->{st1['round']} pending {st0['pending']}->{st1['pending']} "
          f"storage {st0['storage']}->{st1['storage']} unparsed={len(unparsed)}", flush=True)


if __name__ == "__main__":
    main()
