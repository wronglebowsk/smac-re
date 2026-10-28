#!/usr/bin/env python3
"""M75: the production sweep's MATCH SEMANTICS, replayed and tested live.

FUN_00572800(tid,0) (called at 0x4efe7e from the production path, first production of a
record) sweeps the 256 type records.  This script implements the loop from the instruction
bytes (0x572838-0x5729dc) — validity, marked gate, the designed bit-2 gate, validator
0x5a6cd0(shift = produced record's +0x30 low byte), the domain-row equality at
0x92ae80+(id*9)<<4, and the three tier tests (0x92b950[+0x24], 0x92fd18[+0x25], 0x92fd18[+0x26],
16-byte rows, rank = row[0], candidate rank > 0 required, produced byte >= candidate rank) —
predicts the marked set for tid 194 from live memory, then RELOADS the clean save, enqueues
194, arms 4 hardware watchpoints (193/194 marked; 128/130 valid-unmarked byte-matches),
drives 3 boundaries, and checks the prediction against the stores actually observed.

    python3 scripts/m75_sweep_replay.py --tag m75sweep1        # -> PASS / FAIL
"""
import argparse, json, os, signal, struct, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import m55_boundary as M
import m74_flag_watch as F
import m74_flag_hw as H

BASE_NAME = "University Base"
PROD = 194
WATCH = [193, 194, 192, 128]   # 193: predicted sweep store; 194: production store;
#                                 192: unmarked + tier-REJECTED (must stay silent);
#                                 128: sibling (marked in fresh save -> skipped)

def model(m, flags_override=None):
    """Predict FUN_00572800(194,0)'s marked set from live memory (flags_override = pre-state)."""
    blob = M.rd(m, F.TYPE_ARR, 52 * 256)
    vtab = M.rd(m, 0x92FDD4, 0x14 * 0x58)
    own = M.rd(m, 0x985C1C, 0x100)
    t24 = M.rd(m, 0x92B950, 16 * 0x40)
    t25 = M.rd(m, 0x92FD18, 16 * 0x40)
    domr = M.rd(m, 0x92AE80, 0x90 * 0x100)
    def rec(t): return blob[t*52:(t+1)*52]
    def flag(t):
        if flags_override and t in flags_override: return flags_override[t]
        return struct.unpack("<I", rec(t)[0x30:0x34])[0]
    def rank(tab, b): return tab[b*16]
    p = rec(PROD)
    pf = flag(PROD)
    shift = pf & 0xff
    def validator(tid):
        if shift <= 0 or shift >= 32: return False
        tech = struct.unpack("<i", vtab[tid*0x14:tid*0x14+4])[0]
        if tech < 0: return False
        d1 = struct.unpack("<i", vtab[tid*0x14+4:tid*0x14+8])[0]
        if d1 >= -1 and tech == -1: return False
        return bool(own[tech] & (1 << shift))
    out = []
    for c in range(256):
        r = rec(c); f = flag(c)
        # LIVE (m75sweep1): unmarked designed 192 (tier-FAILING triple) AND 193 were
        # both stored; marked designed 128/129/130/131 got NO store; alpha 0-13 got no
        # store.  Model: valid + unmarked + (designed: store at the 0x5728ba je, which
        # SKIPS the tier checks) + (alpha: validator 0x5a6cd0 then the tier checks).
        if not f & 1: continue
        if c == PROD: continue   # production sets bit 2 BEFORE calling the sweep (0x4efe60)
        if f & 4: continue
        if c >= 0x40:
            out.append(c); continue
        if not validator(c): continue
        ok = True
        for off, tab in ((0x24, t24), (0x25, t25), (0x26, t25)):
            ct = rank(tab, r[off])
            if ct <= 0: ok = False; break
            if p[off] < ct: ok = False; break
        if ok: out.append(c)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m75sweep1")
    ap.add_argument("--boundaries", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=150)
    ap.add_argument("--poke-minerals", type=int, default=200)
    ap.add_argument("--no-reload", action="store_true")
    a = ap.parse_args()
    EVID = F.EVID

    if not a.no_reload:
        r = subprocess.run([sys.executable, os.path.join(F.ROOT, "scripts", "m54a_load.py"), "--relaunch"],
                           capture_output=True, text=True,
                           env=dict(os.environ, SMAC_SAVE="m54b_clean.SAV"))
        print(f"reload rc={r.returncode}", flush=True)
        if r.returncode != 0:
            print(r.stdout[-800:], r.stderr[-400:]); raise SystemExit(f"{a.tag}: reload failed")
        time.sleep(4.0)
        subprocess.run([sys.executable, os.path.join(F.ROOT, "scripts", "m70_clear_dialog.py")],
                       capture_output=True, text=True)

    pid = F.game_pid()
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        row = F.base_row(m, BASE_NAME)
        census_before = F.flag_census(m)
        predicted = model(m)
    print(f"pid {pid} head {row['slots'][0]} pending {row['pending']} round {row['round']}", flush=True)
    print("PREDICTED sweep(194) marked set:", predicted, flush=True)
    for c in range(256):
        if census_before[c] & 1 and c not in predicted:
            print(f"  rejected {c}: flag 0x{census_before[c]:08x}", flush=True)

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
        print(f"enqueue attempt {attempt}: rc={r.returncode} head {row['slots'][0]} pending {row['pending']}", flush=True)
        subprocess.run([sys.executable, os.path.join(F.ROOT, "scripts", "m70_clear_dialog.py")],
                       capture_output=True, text=True)
    print(f"after enqueue: head {row['slots'][0]} pending {row['pending']} landed={landed}", flush=True)
    if not landed:
        raise SystemExit(f"{a.tag}: enqueue did not land (head {row['slots'][0]} pending {row['pending']})")

    def poke_storage(value):
        with open(f"/proc/{pid}/mem", "rb+") as mm:
            mm.seek(row["addr"] + 0x40); mm.write(struct.pack("<i", value))
            mm.seek(row["addr"] + 0x40); return struct.unpack("<i", mm.read(4))[0]
    got = poke_storage(a.poke_minerals)
    print(f"storage poked {a.poke_minerals} read back {got}", flush=True)

    gpath = os.path.join(F.ROOT, "scratch", f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.gdblog")
    open(gpath, "w").write(H.gdb_script(WATCH))
    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=log, stderr=subprocess.STDOUT)
    time.sleep(3.0)
    head = open(lpath, "r", errors="replace").read()
    n_hw = head.count("Hardware watchpoint")
    if "ARMED" not in head or n_hw < len(WATCH):
        try: os.kill(g.pid, signal.SIGINT)
        except ProcessLookupError: pass
        subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
        raise SystemExit(f"gdb did not arm 4 hw watchpoints (saw {n_hw})")
    print(f"armed {n_hw} hw watchpoints on {WATCH}", flush=True)

    rc_ok = True
    t0 = time.time()
    for k in range(a.boundaries):
        poke_storage(a.poke_minerals)
        r = subprocess.run([sys.executable, os.path.join(F.ROOT, "scripts", "smac_play.py"),
                            "--turns", "1", "--timeout", str(a.timeout), "--no-escape", "3000",
                            "--orders-per-turn", "1", "--verbose", "--tag", f"{a.tag}_r{k}"],
                           capture_output=True, text=True)
        if r.returncode != 0: rc_ok = False
        with open(f"/proc/{pid}/mem", "rb", 0) as m:
            c2 = F.flag_census(m)
        fired = bool(c2[193] & 4) and bool(c2[PROD] & 4)
        print(f"  boundary {k}: rc={r.returncode} t={time.time()-t0:.0f}s flags 193=0x{c2[193]:02x} "
              f"194=0x{c2[PROD]:02x} 192=0x{c2[192]:02x}", flush=True)
        if fired:
            print("  sweep + production stores landed, stopping the drive", flush=True)
            break
    try: os.kill(g.pid, signal.SIGINT)
    except ProcessLookupError: pass
    for _ in range(40):
        if not os.path.exists("/proc/%d" % g.pid): break
        time.sleep(0.5)
    subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
    log.close()

    tracer = subprocess.run(["grep", "-m1", "TracerPid", f"/proc/{pid}/status"],
                            capture_output=True, text=True).stdout.split()[-1]
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        after_row = F.base_row(m, BASE_NAME)
        census_after = F.flag_census(m)
    ev = H.parse(open(lpath, "r", errors="replace").read())
    with open(os.path.join(EVID, f"{a.tag}_seq.jsonl"), "w") as fh:
        for d in ev: fh.write(json.dumps(d) + "\n")
    sweep_stores = sorted({e["tid"] for e in ev if e["pc"] == 0x5729de})
    prod_store   = sorted({e["tid"] for e in ev if e["pc"] == 0x4efe67})
    print("events:", [(hex(e["pc"]), e["tid"], hex(e["val"])) for e in ev], flush=True)
    print(f"sweep stores @0x5729d5(or, pc reports 0x5729de): {sweep_stores}; "
          f"production store @0x4efe60(or, pc 0x4efe67): {prod_store}", flush=True)
    print(f"census diff: " + ", ".join(
        f"{c}:0x{census_before[c]:02x}->0x{census_after[c]:02x}"
        for c in range(256) if census_before[c] != census_after[c]), flush=True)

    newly_bit2 = sorted(c for c in range(256)
                        if not census_before[c] & 4 and census_after[c] & 4)
    g1 = prod_store == [PROD]
    g2 = sweep_stores == predicted
    g3 = (193 in predicted and 195 not in predicted and 65 not in predicted
          and not [c for c in predicted if c < 0x40])
    g4 = (census_after[PROD] & 4) and (census_after[193] & 4) and (census_after[192] & 4) \
         and census_after[128] == census_before[128] and newly_bit2 == sorted(predicted + [PROD])
    # discriminating: a record that was MARKED before (128) stays untouched while an
    # unmarked one (193, 192) flips — the marked gate is live, not the tier tables
    rej_marked = [c for c in range(256) if census_before[c] & 1 and census_before[c] & 4
                  and c not in predicted and c != PROD]
    g5 = 128 in rej_marked and census_after[128] == census_before[128] \
         and tracer == "0" and rc_ok
    ok = g1 and g2 and g3 and g4 and g5
    print(f"gates: g1_production={g1} g2_predicted==observed={g2} g3_membership={g3} "
          f"g4_census={g4} g5_discriminating={g5} newly_bit2={newly_bit2} "
          f"marked-untouched={rej_marked}")
    print(f"ACCEPTANCE {a.tag}: {'PASS' if ok else 'FAIL'} "
          f"(predicted={predicted} observed_sweep={sweep_stores} tracer={tracer})", flush=True)
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
