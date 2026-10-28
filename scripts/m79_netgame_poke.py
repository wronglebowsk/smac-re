#!/usr/bin/env python3
"""M79: NAME the two production-gate globals and turn the 0x4f05bd MARKSET else-branch ON.

The production function's gate block (0x4f0591-0x4f0637, instruction bytes in
scratch/m574/text.txt) is the ONLY thing that decides between the marker-clear pass and the
marker-setter:

  0x4f0591 mov eax,[ebp-0x20] ; test ; je 0x4f0637          (bail unless the local is nonzero)
  0x4f05a0 push edi ; call 0x47f7b0 ; add esp,4
  0x4f05a5 mov eax,ds:0x920434 ; test eax,eax               <- GLOBAL A (the poke target)
  0x4f05af mov al,ds:0x985b10                               <- GLOBAL B (a byte mask)
  0x4f05b4 je 0x4f05c6                                     (A == 0 -> admit)
  0x4f05b6 test bl,al ; je 0x4f05c6                        (owner bit not in B -> admit)
  0x4f05ba mov eax,[ebp-0x1c] ; 0x4f05bd or BYTE [eax+0x98adb9],0x1   <- MARKSET (bit 8 of the
  flag WORD at rec+0x30, eax = tid*52) ; 0x4f05c4 jmp 0x4f0637         <- skips the pass
  0x4f05c6 admit: test bl,al ; mov DWORD ds:0x8f0d6c,0 ; je 0x4f05e0  (bit clear -> sweep)
  0x4f05d4 test DWORD ds:0x985abc,0x100000 ; je 0x4f0637              (else sweep iff bit20)
  0x4f05e0..0x4f0637 the pass: for each record index, if flags & 0x105 == 0x105 call 0x4f0626
  -> FUN_004ef380, whose first statement 0x4ef398 `and BYTE [ebx+0x98adb9],0xfe` clears bit 8.

M78's baseline run (tag m78order3) read A = 0 at every gate visit, so the ELSE branch was dead
and MARKSET printed ZERO: the sweep marked 192/193 with 0x104 and the same visit cleared them.
This run changes ONE variable: it pokes ds:0x920434 = 1 at 0x4f05a5 (the instruction that reads
it, so nothing else executes under the poke) and restores it to 0 at 0x4f0637, the block's single
convergence point.  Prediction from the baseline census (192=0x001 193=0x041 194=0x041, no
0x100-carriers) with owner 3 and B = 0x08 (bit 3 set):

  NETGAME-ON  — the else branch fires: MARKSET tid=194 sets 0x100 on the produced record, the
                pass never runs (SWEEPIN/CLEAR zero), so the sweep's 0x104 marks on 192/193
                SURVIVE: end census 192=0x105 193=0x145 194=0x145, carriers [192,193,194].
  NETGAME-OFF (m78order3, unchanged) — the pass runs and clears: 192=0x005 193=0x045 194=0x045,
                carriers [].

PASS on one invocation: instrument alive, the poke read back as 1 with the pre-state 0 and the
mask bit for that visit's owner set, one MARKSET per poke on the produced tid, zero SWEEPIN/CLEAR,
the end census exactly the NETGAME-ON prediction (read back from memory, not from events), the
bit-8 replay exact at every boundary, and both globals restored to their baseline values.
"""
import argparse, json, os, re, signal, struct, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import m74_flag_watch as F
import accept_ready as AR
import smac_play as P
from m78_mark_clear import normalize_screen

BASE_NAME = "University Base"
PROD = 194
WATCH = (192, 193, 194)
MARKER = 0x100
NETGAME, HMASK, PMASK_ALL, CUR_PLAYER = 0x920434, 0x985b10, 0x985b11, 0x985dcc
PLAYER_ARR, PLAYER_N = 0x91e494, 0x91e2d0
EVID = F.EVID
SWEEP_RETS = {0x4394c3: "FUN_00438ad0", 0x4efe83: "FUN_004ef6d0 production",
              0x574203: "FUN_00573a90", 0x5a7d13: "FUN_005a7970 @0x5a7d0e",
              0x5a7f7a: "FUN_005a7970 @0x5a7f75"}

TMPL = r"""set pagination off
set confirm off
set height 0
set verbose off
set can-use-hw-watchpoints 1
set $b = @@ADDR@@
@@BREAKS@@printf "ARMED base=0x%x head=%d pending=%d storage=%d netgame=%d mask=0x%02x/0x%02x pl=%d\n", $b, *(int *)($b + 0x50), *(int *)($b + 0x4c), *(int *)($b + 0x40), *(int *)0x920434, *(unsigned char *)0x985b10, *(unsigned char *)0x985b11, *(int *)0x985dcc
continue
"""

BPN = r"""break *@@ADDR@@
commands
silent
printf "@@FMT@@\n", @@ARGS@@
continue
end
"""
POKEBP = r"""break *0x4f05a5
commands
silent
printf "POKE pre=%d b10=0x%02x b11=0x%02x owner=%d rec=%d bit=0x%x l20=%d pl=%d\n", *(int *)0x920434, *(unsigned char *)0x985b10, *(unsigned char *)0x985b11, *(int *)($ebp - 0x28), *(int *)($ebp - 0x1c), *(int *)($ebp - 0x2c) & 0xff, *(int *)($ebp - 0x20), *(int *)0x985dcc
set var *(int *)0x920434 = 1
printf "POKEPOST post=%d\n", *(int *)0x920434
continue
end
"""
RESTOREBP = r"""break *0x4f0637
commands
silent
set var *(int *)0x920434 = 0
printf "RESTORE netgame=%d b10=0x%02x pl=%d\n", *(int *)0x920434, *(unsigned char *)0x985b10, *(int *)0x985dcc
continue
end
"""

# register semantics read off the instruction bytes (see m78_mark_clear.py): esi/edi/ebx = tid*52
# at the sites below; [ebp-0x1c] = tid*52 at 0x4f05ba; [ebp-0x28] = owner, [ebp-0x2c] = 1<<owner.
BPS = [
    (0x4ef6d0, "FUNCIN", "FUNCIN base=0x%x", "$b"),
    (0x4efe60, "PRODFLAG", "PRODFLAG tid=%d pre=0x%x",
     "$esi / 52, *(unsigned short *)($esi + 0x98adb8)"),
    (0x572800, "SWEEPCALL", "SWEEPCALL owner=%d tid=%d mode=%d ret=0x%x",
     "*(int *)($esp + 4), *(int *)($esp + 8), *(int *)($esp + 0xc), *(int *)$esp"),
    (0x5729d5, "MARK", "MARK tid=%d pre=0x%x",
     "$edi / 52, *(unsigned short *)($edi + 0x98adb8)"),
    (0x4f0591, "GATE", "GATE l20=%d owner=%d rec=%d bit=0x%x g20434=%d b10=0x%02x b11=0x%02x pl=%d",
     "*(int *)($ebp - 0x20), *(int *)($ebp - 0x28), *(int *)($ebp - 0x1c), "
     "*(int *)($ebp - 0x2c) & 0xff, *(int *)0x920434, *(unsigned char *)0x985b10, "
     "*(unsigned char *)0x985b11, *(int *)0x985dcc"),
    (0x4f05bd, "MARKSET", "MARKSET tid=%d pre=0x%x",
     "$eax / 52, *(unsigned short *)($eax + 0x98adb8)"),
    (0x4f05e0, "SWEEPIN", "SWEEPIN owner=%d g20434=%d b10=0x%02x l20=%d",
     "$edi, *(int *)0x920434, *(unsigned char *)0x985b10, *(int *)($ebp - 0x20)"),
    (0x4ef398, "CLEAR", "CLEAR tid=%d owner=%d pre=0x%x ret=0x%x",
     "$ebx / 52, *(int *)($ebp + 8), *(unsigned short *)($ebx + 0x98adb8), *(int *)($ebp + 4)"),
    (0x52145e, "UPKCLR", "UPKCLR tid=%d pre=0x%x",
     "($edi - 0x98adb8) / 52, *(unsigned short *)$edi"),
]
TAGS = ("FUNCIN", "PRODFLAG", "SWEEPCALL", "MARK", "GATE", "POKE", "POKEPOST", "MARKSET",
        "SWEEPIN", "CLEAR", "UPKCLR", "RESTORE", "BOUNDARY")
LINE = re.compile(r"^(%s)\s*(.*)$" % "|".join(TAGS))
KV = re.compile(r"(\w+)=(-?0x[0-9a-f]+|-\d+|\d+)")


def gdb_script(base_addr):
    blocks = [BPN.replace("@@ADDR@@", "%#x" % a).replace("@@FMT@@", f).replace("@@ARGS@@", args)
              for a, t, f, args in BPS]
    return (TMPL.replace("@@ADDR@@", hex(base_addr))
            .replace("@@BREAKS@@", "".join(blocks) + POKEBP + RESTOREBP))


def parse(text):
    out = []
    for ln in text.splitlines():
        m = LINE.match(ln.strip())
        if not m:
            continue
        d = {"tag": m.group(1)}
        if d["tag"] == "BOUNDARY":
            d["idx"] = int(m.group(2).split()[0])
            m2 = re.search(r"carriers=(\S+)", m.group(2))
            d["carriers"] = [] if m2.group(1) == "-" else [int(x) for x in m.group(1).split(",")]
            for k, v in re.findall(r"w(\d+)=0x([0-9a-f]+)", m.group(2)):
                d["w" + k] = int(v, 16)
        else:
            for k, v in KV.findall(m.group(2)):
                d[k] = int(v, 16) if v.startswith(("0x", "-0x")) else int(v)
        out.append(d)
    return out


def read_globals(pid):
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        m.seek(NETGAME); ng = struct.unpack("<i", m.read(4))[0]
        m.seek(HMASK); b10 = m.read(1)[0]; b11 = m.read(1)[0]
        m.seek(CUR_PLAYER); pl = struct.unpack("<i", m.read(4))[0]
        m.seek(PLAYER_N); n = struct.unpack("<i", m.read(4))[0]
        recs = []
        for i in range(8):
            m.seek(PLAYER_ARR + i * 0x19c); recs.append(m.read(1)[0])
    return ng, b10, b11, pl, n, recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m79net1")
    ap.add_argument("--boundaries", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=240)
    ap.add_argument("--poke-minerals", type=int, default=200)
    ap.add_argument("--no-reload", action="store_true")
    a = ap.parse_args()

    if not a.no_reload:
        for attempt in range(3):
            r = subprocess.run([sys.executable, os.path.join(F.ROOT, "scripts", "m54a_load.py"),
                                "--relaunch"], capture_output=True, text=True,
                               env=dict(os.environ, SMAC_SAVE="m54b_clean.SAV"))
            print(f"reload attempt {attempt}: rc={r.returncode}", flush=True)
            if r.returncode != 0:
                print(r.stdout[-500:], r.stderr[-200:]); time.sleep(4.0); continue
            time.sleep(4.0)
            ok, seen = normalize_screen()
            print(f"  screen after reload: hud={ok} saw={seen}", flush=True)
            if ok:
                break
        else:
            raise SystemExit(f"{a.tag}: reload/screen never normalized")

    pid = F.game_pid()
    ng0, b10_0, b11_0, pl0, pn0, prec = read_globals(pid)
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        row = F.base_row(m, BASE_NAME)
        before = F.flag_census(m)
    print(f"pid {pid} head {row['slots'][0]} pending {row['pending']} round {row['round']} "
          f"owner {row.get('owner')} storage {row.get('storage')}", flush=True)
    print(f"GLOBALS: 0x920434={ng0} 0x985b10=0x{b10_0:02x} 0x985b11=0x{b11_0:02x} "
          f"cur_player(0x985dcc)={pl0} player-count(0x91e2d0)={pn0} "
          f"player-array[0..7] first bytes={prec}", flush=True)
    print("baseline 192/193/194: " + " ".join(f"{t}=0x{before[t]:03x}" for t in WATCH) +
          "  0x100-carriers: " + str([c for c in range(256) if before[c] & MARKER]), flush=True)

    # PREDICTIONS from the baseline.  The sweep store at 0x5729d5 is `or WORD [rec+0x30],0x104`
    # (bits 2 and 8); PRODFLAG 0x4efe60 sets bit 2 of the produced record; MARKSET 0x4f05bd sets
    # bit 8 of the produced record.  The two gate branches predict DIFFERENT end censuses.
    pred_on = {192: before[192] | 0x104, 193: before[193] | 0x104,
               194: before[194] | 0x4 | MARKER}
    pred_off = {t: v & ~MARKER for t, v in pred_on.items()}
    print(f"PREDICT NETGAME-ON  (else branch): end census " +
          " ".join(f"{t}=0x{pred_on[t]:03x}" for t in WATCH) + " carriers=[192,193,194], "
          "MARKSET 1, SWEEPIN/CLEAR 0", flush=True)
    print(f"PREDICT NETGAME-OFF (m78order3):  end census " +
          " ".join(f"{t}=0x{pred_off[t]:03x}" for t in WATCH) + " carriers=[], "
          "SWEEPIN/CLEAR >= 1", flush=True)
    print(f"the shape discriminates: {pred_on != pred_off} "
          f"(they differ only in bit 8; baseline carriers "
          f"{[c for c in range(256) if before[c] & MARKER]})", flush=True)

    ok_scr, seen = normalize_screen()
    print(f"screen normalized before enqueue: hud={ok_scr} saw={seen}", flush=True)
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
              f"pending {row['pending']} out={r.stdout[-300:]!r}", flush=True)
        ok_scr, seen = normalize_screen()
        print(f"  recovery normalize: hud={ok_scr} saw={seen}", flush=True)
    print(f"after enqueue: head {row['slots'][0]} pending {row['pending']} landed={landed}",
          flush=True)
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
    log = open(lpath, "a")                       # O_APPEND: the census shares gdb's stream
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
    print(f"armed (gdb breakpoints seen {n_bp}) :: {head.strip().splitlines()[-1]}", flush=True)

    t0 = time.time()
    for k in range(a.boundaries):
        poke_storage(a.poke_minerals)
        r = subprocess.run([sys.executable, os.path.join(F.ROOT, "scripts", "smac_play.py"),
                            "--turns", "1", "--timeout", str(a.timeout), "--no-escape", "3000",
                            "--orders-per-turn", "1", "--verbose", "--tag", f"{a.tag}_r{k}"],
                           capture_output=True, text=True)
        with open(f"/proc/{pid}/mem", "rb", 0) as m:
            c2 = F.flag_census(m)
        carr = [c for c in range(256) if c2[c] & MARKER]
        with open(lpath, "a") as fh:
            fh.write("BOUNDARY %d %s carriers=%s\n" %
                     (k, " ".join("w%d=0x%03x" % (t, c2[t]) for t in WATCH),
                      ",".join(str(c) for c in carr) or "-"))
        print(f"  boundary {k}: rc={r.returncode} t={time.time()-t0:.0f}s " +
              " ".join(f"{t}=0x{c2[t]:03x}" for t in WATCH) + f" carriers={carr}", flush=True)
    try: os.kill(g.pid, signal.SIGINT)
    except ProcessLookupError: pass
    for _ in range(40):
        if not os.path.exists("/proc/%d" % g.pid): break
        time.sleep(0.5)
    subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
    log.close()

    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        after = F.flag_census(m)
    ngA, b10A, b11A, plA, pnA, precA = read_globals(pid)
    text = open(lpath, "r", errors="replace").read()
    ev = parse(text)
    with open(os.path.join(EVID, f"{a.tag}_seq.jsonl"), "w") as fh:
        for d in ev: fh.write(json.dumps(d) + "\n")

    v = 0
    for d in ev:
        if d["tag"] == "FUNCIN":
            v += 1
        d["visit"] = v
    by = lambda t: [d for d in ev if d["tag"] == t]
    gate, poke, post = by("GATE"), by("POKE"), by("POKEPOST")
    markset, sweepin, marks = by("MARKSET"), by("SWEEPIN"), by("MARK")
    sweeps, restore = by("SWEEPCALL"), by("RESTORE")
    clears = [d for d in ev if d["tag"] in ("CLEAR", "UPKCLR")]
    prodflags = by("PRODFLAG")
    cands = [d for d in ev if d["tag"] == "BOUNDARY"]
    after_carr = sorted(t for t in range(256) if after[t] & MARKER)

    # g1 instrument alive: gate visits, a poke, the production store, the sweep call and its marks
    g1 = ("ARMED" in text) and bool(gate) and bool(poke) and bool(prodflags) and bool(sweeps) \
         and bool(marks)
    # g2 the poke is real: pre 0 (baseline), read back 1 in the same visit, and the admission
    # precondition (owner bit set in the mask) actually held for that visit
    g2 = bool(poke) and all(d["pre"] == 0 and (d["b10"] & (1 << d["owner"])) and
                            d["rec"] % 52 == 0 and d["rec"] // 52 == PROD for d in poke) and \
         len(post) == len(poke) and all(d["post"] == 1 for d in post) and \
         all(any(p["visit"] == q["visit"] for q in post) for p in poke)
    # g3 the shape discriminates: the two branches predict different end censuses and the
    #    baseline had no 0x100-carrier to begin with
    g3 = pred_on != pred_off and not [c for c in range(256) if before[c] & MARKER]
    # g4 the else branch fired exactly where the poke was made, on the produced record
    g4 = bool(markset) and len(markset) == len(poke) and \
         all(d["tid"] == PROD and (d["pre"] & MARKER) == 0 for d in markset) and \
         all(any(m["visit"] == p["visit"] for m in markset) for p in poke)
    # g5 the clear pass never ran
    g5 = not sweepin and not clears
    # g6 read the EFFECT back from memory: the census is exactly the NETGAME-ON prediction
    g6 = all(after.get(t) == pred_on[t] for t in WATCH) and after_carr == [192, 193, 194]
    # g7 bit-8 replay from the events matches every census (no un-instrumented writer touched it)
    bit8 = {t: bool(before[t] & MARKER) for t in range(256)}
    replay_ok, rows = True, []
    for d in ev:
        if d["tag"] == "BOUNDARY":
            carr = sorted(t for t in bit8 if bit8[t])
            ok = carr == d["carriers"] and all(
                bool((d.get("w%d" % t) or 0) & MARKER) == bit8[t] for t in WATCH)
            rows.append((d["idx"], d["carriers"], carr, ok)); replay_ok &= ok
            continue
        t = d.get("tid")
        if t is None or not 0 <= t < 256:
            continue
        if d["tag"] in ("MARK", "MARKSET"):
            bit8[t] = True
        elif d["tag"] in ("CLEAR", "UPKCLR"):
            bit8[t] = False
    g7 = replay_ok and bool(cands)
    # g8 only the gate global moved: mask/all-mask unchanged everywhere, the sweep call still
    #    follows its own production store, and the sweep still marks exactly 192/193
    g8 = all(d["b10"] == b10_0 and d["b11"] == b11_0 for d in gate + poke + restore) and \
         all(d["g20434"] == 0 for d in gate) and \
         any(d["ret"] == 0x4efe83 and d["tid"] == PROD for d in sweeps) and \
         all(d["ret"] in SWEEP_RETS for d in sweeps) and \
         sorted({d["tid"] for d in marks}) == [192, 193] and \
         all(d["tid"] == PROD for d in prodflags)
    # g9 the state is restored: every visit ends with netgame 0 and the game reads baseline values
    g9 = len(restore) >= len(poke) and all(d["netgame"] == 0 for d in restore) and \
         ngA == 0 and b10A == b10_0 and b11A == b11_0

    for r_ in rows:
        print(f"  census {r_[0]}: observed carriers {r_[1]} | replayed {r_[2]} | match={r_[3]}",
              flush=True)
    print("GATE visits (l20, owner, pl, b10, b11):",
          [(d["l20"], d["owner"], d["pl"], hex(d["b10"]), hex(d["b11"])) for d in gate], flush=True)
    print("POKE (pre, post, owner, rec, tid):",
          [(d["pre"], next((q["post"] for q in post if q["visit"] == d["visit"]), None),
            d["owner"], d["rec"], d["rec"] // 52) for d in poke], flush=True)
    print("MARKSET:", [(d["tid"], hex(d["pre"])) for d in markset], flush=True)
    print("MARK:", [(d["tid"], hex(d["pre"])) for d in marks], flush=True)
    print("SWEEPCALL:", [(d["tid"], hex(d["ret"]), SWEEP_RETS.get(d["ret"], "UNVERIFIED"))
                         for d in sweeps], flush=True)
    print("SWEEPIN/CLEAR/UPKCLR events:", len(sweepin), len(clears), flush=True)
    print("mask-vs-cur_player discriminator (owner, pl, b10) per gate visit:",
          [(d["owner"], d["pl"], hex(d["b10"])) for d in gate], flush=True)
    print(f"end globals: 0x920434={ngA} 0x985b10=0x{b10A:02x} 0x985b11=0x{b11A:02x} pl={plA}",
          flush=True)
    print("end census: " + " ".join(f"{t}=0x{after[t]:03x}" for t in WATCH) +
          f" carriers={after_carr}", flush=True)
    res = {"g1_instrument_alive": g1, "g2_poke_read_back_and_admission_precondition": g2,
           "g3_shape_discriminates": g3, "g4_else_branch_fires_once_per_poke_on_produced_tid": g4,
           "g5_clear_pass_never_ran": g5, "g6_end_census_is_the_netgame_on_prediction": g6,
           "g7_bit8_replay_exact_every_census": g7, "g8_only_the_gate_global_changed": g8,
           "g9_globals_restored_to_baseline": g9}
    for k, val in res.items():
        print(f"  {k}: {val}", flush=True)
    ok = all(res.values())
    print(f"{a.tag}: {'PASS' if ok else 'FAIL'}", flush=True)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
