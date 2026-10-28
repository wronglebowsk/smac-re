#!/usr/bin/env python3
"""M77: WHAT REACHES the production marker-clear pass 0x4f05e2, and its GATE.

Static (instruction bytes, scratch/m574/text.txt):
  0x4f05e2 is entered ONLY by fall-through from 0x4f05e0 (`xor esi,esi`); 0x4f05e0's only
  in-edges are `je 0x4f05e0` at 0x4f05d2 and the fall-through from 0x4f05de
  (`je 0x4f0637` on `test DWORD PTR ds:0x985abc,0x100000`).  Both come from the gate block
  0x4f0591-0x4f05de, whose own in-edges are 0x4f056c/0x4f0578/0x4f057f branches plus the
  fall-through 0x4f058e.  The block first bails at 0x4f0599 (`je 0x4f0637`) when
  [ebp-0x20] == 0.  The gate operands are:
    eax = DAT_00920434 (0x4f05a5), al = low byte DAT_00985b10 (0x4f05af),
    bl = low byte [ebp-0x2c] = low byte of (1 << owner) — [ebp-0x2c] is built at
    0x4ef804-0x4ef815 (`mov esi,1; shl esi,cl`; cl = ebx = BYTE [base+4], base = *DAT_008f0d60),
    and DAT_00985abc & 0x100000 (0x4f05d4).
  Admission: (0x920434 == 0 || !(mask & (1<<owner))) -> 0x4f05c6; there, !(mask & (1<<owner))
  -> SWEEP (0x4f05e0), else sweep iff (0x985abc & 0x100000); the ELSE branch
  (0x920434 != 0 && mask & (1<<owner)) SETS the marker at 0x4f05bd and skips the sweep.

This script runs ONE live window and prints the gate operands at 0x4f0591, which branch the
CPU then took (0x4f05bd MARKSET / 0x4f05d4 ROUTEB / 0x4f05e0 SWEEPIN), and every record the
sweep handed to the clear FUN_004ef380 (0x4f0626).  It PREDICTS the branch from the operands
and the 0x100 census from the observed clears, then reads both back.  Prints PASS on one
invocation when every gate holds.
"""
import argparse, json, os, re, signal, struct, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import m74_flag_watch as F

BASE_NAME = "University Base"
PROD = 194
MARKER = 0x100
EVID = F.EVID

TMPL = r"""set pagination off
set confirm off
set height 0
set verbose off
set can-use-hw-watchpoints 1
set $b = @@ADDR@@
@@BREAKS@@printf "ARMED base=0x%x head=%d pending=%d storage=%d\n", $b, *(int *)($b + 0x50), *(int *)($b + 0x4c), *(int *)($b + 0x40)
continue
"""

BP = r"""break *@@ADDR@@ if (@@COND@@)
commands
silent
printf "@@FMT@@\n", @@ARGS@@
continue
end
"""
BPN = r"""break *@@ADDR@@
commands
silent
printf "@@FMT@@\n", @@ARGS@@
continue
end
"""

# (addr, tag, fmt, args, cond).  Register/offset expressions read off the instruction bytes:
# 0x4f0591 locals are ebp-relative; 0x4f05bd eax = tid*52 (0x4f05ba `mov eax,[ebp-0x1c]` then
# `or BYTE PTR [eax+0x98adb9],1`); 0x4f05d4/0x4f05e0 edi = owner = [ebp-0x28]; 0x4f0626 eax = tid.
BPS = [
    (0x4ef6d0, "FUNCIN", "FUNCIN l20=%d owner=%d",
     "*(int *)($ebp - 0x20), *(int *)($ebp - 0x28)", "1"),
    (0x4f0591, "GATE", "GATE l20=%d owner=%d tid=%d bit=0x%x g20434=%d b10=0x%02x abc=0x%x",
     "*(int *)($ebp - 0x20), *(int *)($ebp - 0x28), *(int *)($ebp - 0x1c), "
     "*(int *)($ebp - 0x2c) & 0xff, *(int *)0x920434, *(unsigned char *)0x985b10, "
     "*(int *)0x985abc", "1"),
    (0x4f05bd, "MARKSET", "MARKSET tid=%d", "$eax / 52", "1"),
    (0x4f05d4, "ROUTEB", "ROUTEB owner=%d bit20=%d",
     "$edi, ((*(int *)0x985abc) >> 20) & 1", "1"),
    (0x4f05e0, "SWEEPIN", "SWEEPIN owner=%d g20434=%d b10=0x%02x l20=%d",
     "$edi, *(int *)0x920434, *(unsigned char *)0x985b10, *(int *)($ebp - 0x20)", "1"),
    (0x4f0626, "CLEARCALL", "CLEARCALL tid=%d flags=0x%x",
     "$eax, *(unsigned short *)($eax * 52 + 0x98adb8)", "1"),
]

LINE = re.compile(r"^(ARMED|FUNCIN|GATE|MARKSET|ROUTEB|SWEEPIN|CLEARCALL)\s*(.*)$")
KV = re.compile(r"(\w+)=(-?0x[0-9a-f]+|-\d+|\d+)")


def gdb_script(base_addr):
    blocks = []
    for addr, tag, fmt, args, cond in BPS:
        tpl = BP if cond != "1" else BPN
        blocks.append(tpl.replace("@@ADDR@@", "%#x" % addr).replace("@@COND@@", cond)
                      .replace("@@FMT@@", fmt).replace("@@ARGS@@", args))
    return TMPL.replace("@@ADDR@@", hex(base_addr)).replace("@@BREAKS@@", "".join(blocks))


def parse(text):
    out = []
    for ln in text.splitlines():
        m = LINE.match(ln.strip())
        if not m or m.group(1) == "ARMED":
            continue
        d = {"tag": m.group(1)}
        for k, v in KV.findall(m.group(2)):
            d[k] = int(v, 16) if v.startswith(("0x", "-0x")) else int(v)
        out.append(d)
    return out


def predict(g):
    """The branch the gate block takes, from the operands printed at 0x4f0591."""
    if g["l20"] == 0:
        return "NOENTRY"           # 0x4f0599 je 0x4f0637 — the pass is not reached at all
    inter = (g["bit"] & 0xFF) & g["b10"]
    if g["g20434"] != 0 and inter:
        return "MARKSET"           # 0x4f05ba/0x4f05bd, sweep skipped
    if inter == 0:
        return "SWEEPIN"           # 0x4f05b4 (g20434==0) or 0x4f05b8 -> 0x4f05d2 -> 0x4f05e0
    return "SWEEP-B" if (g["abc"] >> 20) & 1 else "SKIP-B"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m77gate1")
    ap.add_argument("--boundaries", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=240)
    ap.add_argument("--poke-minerals", type=int, default=200)
    ap.add_argument("--no-reload", action="store_true")
    a = ap.parse_args()

    if not a.no_reload:
        r = subprocess.run([sys.executable, os.path.join(F.ROOT, "scripts", "m54a_load.py"), "--relaunch"],
                           capture_output=True, text=True,
                           env=dict(os.environ, SMAC_SAVE="m54b_clean.SAV"))
        print(f"reload rc={r.returncode}", flush=True)
        if r.returncode != 0:
            print(r.stdout[-700:], r.stderr[-300:]); raise SystemExit(f"{a.tag}: reload failed")
        time.sleep(4.0)
        subprocess.run([sys.executable, os.path.join(F.ROOT, "scripts", "m70_clear_dialog.py")],
                       capture_output=True, text=True)
        subprocess.run([sys.executable, os.path.join(F.ROOT, "scratch", "m77_close_pane.py")],
                       capture_output=True, text=True)

    pid = F.game_pid()
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        row = F.base_row(m, BASE_NAME)
        before = F.flag_census(m)
        m.seek(0x920434); g20434 = struct.unpack("<i", m.read(4))[0]
        m.seek(0x985b10); b10 = m.read(1)[0]
        m.seek(0x985abc); abc = struct.unpack("<i", m.read(4))[0]
    print(f"pid {pid} head {row['slots'][0]} pending {row['pending']} round {row['round']} "
          f"owner {row.get('owner')} storage {row.get('storage')}", flush=True)
    print(f"PRE-ATTACH gate globals: DAT_00920434={g20434} DAT_00985b10=0x{b10:02x} "
          f"DAT_00985abc=0x{abc & 0xffffffff:08x} bit20={(abc >> 20) & 1}", flush=True)
    print("baseline 0x100-carriers:", [c for c in range(256) if before[c] & MARKER], flush=True)

    # the shape must discriminate: predict each candidate operand state's outcome
    cands = {}
    for g2 in (0, 7):
        for bitset in (False, True):
            for b20 in (0, 1):
                key = (g2, bitset, b20)
                cands[key] = predict({"l20": 1, "bit": 8 if bitset else 0, "b10": 8 if bitset else 0,
                                      "g20434": g2, "abc": b20 << 20})
    print("candidate predictions:", {str(k): v for k, v in sorted(cands.items())}, flush=True)

    landed = False
    for attempt in range(3):
        r = subprocess.run([sys.executable, os.path.join(F.ROOT, "scripts", "m57_ui_enqueue.py"),
                            "--base-index", "0", "--cell-item", str(PROD), "--inserts", "1"],
                           capture_output=True, text=True)
        with open(f"/proc/{pid}/mem", "rb", 0) as m:
            row = F.base_row(m, BASE_NAME)
        if row["pending"] >= 1 and PROD in row["slots"][:9]:
            landed = True
            break
        print(f"enqueue attempt {attempt}: rc={r.returncode} head {row['slots'][0]} "
              f"pending {row['pending']}", flush=True)
        subprocess.run([sys.executable, os.path.join(F.ROOT, "scripts", "m70_clear_dialog.py")],
                       capture_output=True, text=True)
    print(f"after enqueue: head {row['slots'][0]} pending {row['pending']} landed={landed}", flush=True)
    if not landed:
        raise SystemExit(f"{a.tag}: enqueue did not land (pending {row['pending']})")

    def poke_storage(value):
        with open(f"/proc/{pid}/mem", "rb+") as mm:
            mm.seek(row["addr"] + 0x40); mm.write(struct.pack("<i", value))
            mm.seek(row["addr"] + 0x40); return struct.unpack("<i", mm.read(4))[0]
    print(f"storage poked {a.poke_minerals} read back {poke_storage(a.poke_minerals)}", flush=True)

    gpath = os.path.join(F.ROOT, "scratch", f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.gdblog")
    open(gpath, "w").write(gdb_script(row["addr"]))
    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=log, stderr=subprocess.STDOUT)
    time.sleep(3.0)
    head = open(lpath, "r", errors="replace").read()
    n_bp = head.count("Breakpoint ")
    if "ARMED" not in head:
        try: os.kill(g.pid, signal.SIGINT)
        except ProcessLookupError: pass
        subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
        raise SystemExit(f"gdb never printed ARMED (breakpoints seen {n_bp})")
    print(f"armed (gdb breakpoints seen {n_bp})", flush=True)

    t0 = time.time()
    for k in range(a.boundaries):
        poke_storage(a.poke_minerals)
        r = subprocess.run([sys.executable, os.path.join(F.ROOT, "scripts", "smac_play.py"),
                            "--turns", "1", "--timeout", str(a.timeout), "--no-escape", "3000",
                            "--orders-per-turn", "1", "--verbose", "--tag", f"{a.tag}_r{k}"],
                           capture_output=True, text=True)
        with open(f"/proc/{pid}/mem", "rb", 0) as m:
            c2 = F.flag_census(m)
        print(f"  boundary {k}: rc={r.returncode} t={time.time()-t0:.0f}s "
              f"192=0x{c2[192]:03x} 193=0x{c2[193]:03x} 194=0x{c2[PROD]:03x} "
              f"0x100-carriers={[c for c in range(256) if c2[c] & MARKER]}", flush=True)
    try: os.kill(g.pid, signal.SIGINT)
    except ProcessLookupError: pass
    for _ in range(40):
        if not os.path.exists("/proc/%d" % g.pid): break
        time.sleep(0.5)
    subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
    log.close()

    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        after = F.flag_census(m)
    ev = parse(open(lpath, "r", errors="replace").read())
    with open(os.path.join(EVID, f"{a.tag}_seq.jsonl"), "w") as fh:
        for d in ev: fh.write(json.dumps(d) + "\n")

    gates = [e for e in ev if e["tag"] == "GATE"]
    funcin = [e for e in ev if e["tag"] == "FUNCIN"]
    marks = [e for e in ev if e["tag"] == "MARKSET"]
    sweepin = [e for e in ev if e["tag"] == "SWEEPIN"]
    routeb = [e for e in ev if e["tag"] == "ROUTEB"]
    clears = [e for e in ev if e["tag"] == "CLEARCALL"]

    # per-GATE: the branch that actually followed, from the event stream
    seq_ok, rows = True, []
    for i, e in enumerate(ev):
        if e["tag"] != "GATE":
            continue
        nxt = []
        for e2 in ev[i + 1:]:
            if e2["tag"] == "GATE":
                break
            if e2["tag"] in ("MARKSET", "SWEEPIN", "ROUTEB"):
                nxt.append(e2["tag"])
        pred = predict(e)
        # what the observable set must be if the prediction holds
        want = {"NOENTRY": (), "MARKSET": ("MARKSET",), "SWEEPIN": ("SWEEPIN",),
                "SWEEP-B": ("ROUTEB", "SWEEPIN"), "SKIP-B": ("ROUTEB",)}[pred]
        took = tuple(t for t in ("MARKSET", "ROUTEB", "SWEEPIN") if t in nxt)
        rows.append((e["owner"], e["g20434"], hex(e["bit"]), hex(e["b10"]),
                     (e["abc"] >> 20) & 1, e["l20"], pred, took, tuple(nxt)))
        if took != want:
            seq_ok = False
    for r_ in rows[:12]:
        print("  GATE owner=%d g20434=%d bit=%s b10=%s abc_bit20=%d l20=%d -> predicted %-8s took %-8s events=%s"
              % r_, flush=True)

    carriers_after = [c for c in range(256) if after[c] & MARKER]
    cleared = sorted({e["tid"] for e in clears})
    # g5a: every hand-off to the clear ran on a record the selector admits (bits 0,2,0x100)
    sel_ok = all((e["flags"] & 0x105) == 0x105 for e in clears) and bool(clears)
    # g5b: the sweep's effect read back — a tid the sweep cleared ends the run WITHOUT 0x100
    effect_ok = bool(cleared) and all(not (after[t] & MARKER) for t in cleared)
    g1 = bool(funcin) and bool(gates)
    g2 = bool(gates) and seq_ok
    g3 = len(set(cands.values())) > 1
    g4 = bool(gates) and all(e["g20434"] == 0 for e in gates) and not marks
    g5 = sel_ok
    g6 = bool(sweepin) and bool(cleared) and effect_ok
    g7 = all((e["g20434"], (e["bit"] & 0xFF & e["b10"]) != 0, (e["abc"] >> 20) & 1)
             == (g20434, (8 & b10) != 0, (abc >> 20) & 1) for e in gates)
    print(f"events: FUNCIN={len(funcin)} GATE={len(gates)} MARKSET={len(marks)} "
          f"ROUTEB={len(routeb)} SWEEPIN={len(sweepin)} CLEARCALL={len(clears)}", flush=True)
    print("cleared tids:", cleared, " 0x100-carriers after:", carriers_after, flush=True)
    res = {"g1_instrument_alive_and_gate_fired": g1, "g2_branch_matches_operands": g2,
           "g3_shape_discriminates": g3, "g4_else_branch_dead_when_920434_zero": g4,
           "g5_selector_admits_only_carriers": g5, "g6_sweep_ran_and_effect_read_back": g6,
           "g7_operands_match_pre_attach_read": g7}
    for k, v in res.items():
        print(f"  {k}: {v}", flush=True)
    ok = all(res.values())
    print(f"{a.tag}: {'PASS' if ok else 'FAIL'}", flush=True)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
