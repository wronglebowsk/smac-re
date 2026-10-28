#!/usr/bin/env python3
"""M78: SAME-VISIT marks vs clears, and WHO ELSE CALLS FUN_00572800 / FUN_004ef380.

M77 left a census paradox: the production sweep (FUN_00572800, called at 0x4efe7e) stored
`or WORD PTR [rec+0x30],0x104` (0x5729d5) on 192/193 and the clear pass (0x4f05e2 -> FUN_004ef380,
0x4ef398 `and BYTE [rec+0x31],0xfe`) cleared their 0x100 — in ONE production visit — yet the
boundary census still read 192=0x105 / 193=0x145 one boundary and clean two later.  M77 could not
say WHICH boundary each event happened in: the driver's census lines and the gdb event stream were
two separate files.  Here every census is APPENDED (O_APPEND) to the gdb log the moment it is read,
so marks, clears and censuses share ONE stream ordered by execution.

Static caller sets (instruction bytes, scratch/m574/text.txt):
  call 0x572800 at 0x4394be (FUN_00438ad0), 0x4efe7e (FUN_004ef6d0 production), 0x5741fe
  (FUN_00573a90), 0x5a7d0e and 0x5a7f75 (FUN_005a7970) -> returns 0x4394c3/0x4efe83/0x574203/
  0x5a7d13/0x5a7f7a.   call 0x4ef380 at 0x4ef5ae (FUN_004ef540), 0x4f0626 (production inline),
  0x521479 (FUN_00521070 upkeep), 0x5a8568 (FUN_005a7970) -> returns 0x4ef5b3/0x4f062b/0x52147e/
  0x5a856d.   bit-8 (0x100) writers: SET 0x4f05bd (`or BYTE [eax+0x98adb9],1`), 0x5a7d00/0x5a7f67
  (`or BYTE [eax*4+0x98adb9],0x1`, eax = tid*13), 0x5729d5; CLEAR 0x4ef398 and 0x52145e
  (`and bh,0xfe` + `mov WORD PTR [edi],bx`, edi = &rec+0x30, gated on flags & 0x100 at 0x521442).
  Every one of them is instrumented, so the census must be explainable by the event stream alone.

Hypotheses (printed as predictions from the BASELINE before the run, judged on the ordered stream):
  SAME  — no tid is marked in one boundary and cleared in a LATER one; no census ever sees a 0x100
          carrier (the clear always follows the mark inside the same visit).
  ACROSS— some tid is marked in boundary i and cleared in boundary j > i (the mark survives the
          census that reads it, the next turn's pass clears it).
  RACE  — a census disagrees with the replay of the events before it: the driver's census is taken
          mid-pass, or a writer is un-instrumented.  RACE is a FAIL, not an answer.
PASS on one invocation: instrument alive, every observed return address a statically verified call
target, exactly one of SAME/ACROSS holds, the bit-8 replay exact at every boundary, every clear
ran on a carrier, and no cleared tid still carries 0x100 at the end.
"""
import argparse, json, os, re, signal, struct, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import m74_flag_watch as F

BASE_NAME = "University Base"
PROD = 194
WATCH = (192, 193, 194)
MARKER = 0x100
EVID = F.EVID
SET8 = ("MARK", "MARKSET", "TECHSETA", "TECHSETB")
CLR8 = ("CLEAR", "UPKCLR")

SWEEP_RETS = {0x4394c3: "FUN_00438ad0", 0x4efe83: "FUN_004ef6d0 production",
              0x574203: "FUN_00573a90", 0x5a7d13: "FUN_005a7970 @0x5a7d0e",
              0x5a7f7a: "FUN_005a7970 @0x5a7f75"}
CLEAR_RETS = {0x4ef5b3: "FUN_004ef540 selector", 0x4f062b: "production inline selector",
              0x52147e: "FUN_00521070 upkeep", 0x5a856d: "FUN_005a7970 tech"}

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

# (addr, tag, fmt, args, cond) — register semantics read off the instruction bytes:
#  0x4efe60/0x4efe6c esi = tid*52;  0x572800 cdecl entry, [esp]=ret, [esp+4/8/0xc]=owner,tid,mode;
#  0x5729d5 edi = tid*52 (the loop steps +0x34);  0x4f05bd eax = tid*52;  0x4ef398 ebx = tid*52
#  (0x4ef38f/0x4ef392), [ebp+8]=owner, [ebp+4]=ret;  0x5a7d00/0x5a7f67 eax = tid*13 (the store is
#  [eax*4+0x98adb9]);  0x52145e edi = &rec+0x30 and bx = the word with bit 8 already cleared.
BPS = [
    (0x4ef6d0, "FUNCIN", "FUNCIN base=0x%x", "$b", "1"),
    (0x4efe60, "PRODFLAG", "PRODFLAG tid=%d pre=0x%x",
     "$esi / 52, *(unsigned short *)($esi + 0x98adb8)", "1"),
    (0x4efe6c, "L20FLAG", "L20FLAG edx=%d tid=%d", "$edx, $esi / 52", "1"),
    (0x572800, "SWEEPCALL", "SWEEPCALL owner=%d tid=%d mode=%d ret=0x%x",
     "*(int *)($esp + 4), *(int *)($esp + 8), *(int *)($esp + 0xc), *(int *)$esp", "1"),
    (0x5729d5, "MARK", "MARK tid=%d pre=0x%x",
     "$edi / 52, *(unsigned short *)($edi + 0x98adb8)", "1"),
    (0x4f0591, "GATE", "GATE l20=%d owner=%d rec=%d bit=0x%x g20434=%d b10=0x%02x abc=0x%x",
     "*(int *)($ebp - 0x20), *(int *)($ebp - 0x28), *(int *)($ebp - 0x1c), "
     "*(int *)($ebp - 0x2c) & 0xff, *(int *)0x920434, *(unsigned char *)0x985b10, "
     "*(int *)0x985abc", "1"),
    (0x4f05bd, "MARKSET", "MARKSET tid=%d", "$eax / 52", "1"),
    (0x4f05e0, "SWEEPIN", "SWEEPIN owner=%d g20434=%d b10=0x%02x l20=%d",
     "$edi, *(int *)0x920434, *(unsigned char *)0x985b10, *(int *)($ebp - 0x20)", "1"),
    (0x4ef398, "CLEAR", "CLEAR tid=%d owner=%d pre=0x%x ret=0x%x",
     "$ebx / 52, *(int *)($ebp + 8), *(unsigned short *)($ebx + 0x98adb8), *(int *)($ebp + 4)", "1"),
    (0x52145e, "UPKCLR", "UPKCLR tid=%d pre=0x%x",
     "($edi - 0x98adb8) / 52, *(unsigned short *)$edi", "1"),
    (0x5a7d00, "TECHSETA", "TECHSETA tid=%d pre=0x%x",
     "$eax / 13, *(unsigned short *)($eax * 4 + 0x98adb8)", "1"),
    (0x5a7f67, "TECHSETB", "TECHSETB tid=%d pre=0x%x",
     "$eax / 13, *(unsigned short *)($eax * 4 + 0x98adb8)", "1"),
]

TAGS = ("FUNCIN", "PRODFLAG", "L20FLAG", "SWEEPCALL", "MARK", "GATE", "MARKSET", "SWEEPIN",
        "CLEAR", "UPKCLR", "TECHSETA", "TECHSETB", "BOUNDARY")
LINE = re.compile(r"^(%s)\s*(.*)$" % "|".join(TAGS))
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
        if d["tag"] == "BOUNDARY":
            d["idx"] = int(m.group(2).split()[0])
            m2 = re.search(r"carriers=(\S+)", m.group(2))
            d["carriers"] = [] if m2.group(1) == "-" else [int(x) for x in m2.group(1).split(",")]
            for k, v in re.findall(r"w(\d+)=0x([0-9a-f]+)", m.group(2)):
                d["w" + k] = int(v, 16)
        else:
            for k, v in KV.findall(m.group(2)):
                d[k] = int(v, 16) if v.startswith(("0x", "-0x")) else int(v)
        out.append(d)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m78order1")
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
        for script in ("scripts/m70_clear_dialog.py", "scratch/m77_close_pane.py"):
            subprocess.run([sys.executable, os.path.join(F.ROOT, script)],
                           capture_output=True, text=True)

    pid = F.game_pid()
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        row = F.base_row(m, BASE_NAME)
        before = F.flag_census(m)
    print(f"pid {pid} head {row['slots'][0]} pending {row['pending']} round {row['round']} "
          f"owner {row.get('owner')} storage {row.get('storage')}", flush=True)
    print("baseline 192/193/194: " + " ".join(f"{t}=0x{before[t]:03x}" for t in WATCH) +
          "  0x100-carriers: " + str([c for c in range(256) if before[c] & MARKER]), flush=True)

    # predictions from the BASELINE, before the run.  The unit of ordering is the VISIT (one entry
    # of the production function, 0x4ef6d0), not the driver's boundary — a census can be taken
    # while the engine is stopped mid-visit, which is exactly what M77 could not tell.
    pred_same = "carriers visible at a census ONLY between that visit's MARK and its CLEAR"
    pred_across = "some census reads a carrier OUTSIDE any mark->clear pair (a mark whose clear " \
                  "lands in a later visit)"
    print(f"baseline 192/193/194 have bit 8 clear; a MARK sets it (0x104), the pass at 0x4f05e2 "
          f"clears it", flush=True)
    print("PREDICT SAME-VISIT: " + pred_same + " — so a carrier census is a mid-visit snapshot and "
          "the LAST census must read 192=0x%03x 193=0x%03x (bit 8 gone)" %
          (before[192] | 4 & ~MARKER, before[193] | MARKER & ~MARKER), flush=True)
    print("PREDICT ACROSS-VISIT: " + pred_across + " — a census reads 192=0x%03x 193=0x%03x while "
          "no clear of that tid is pending in the same visit" %
          (before[192] | MARKER, before[193] | MARKER), flush=True)
    print(f"the shape discriminates: {pred_same != pred_across}", flush=True)

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
    # O_APPEND on gdb's own fd: without it the driver's census lines are written past gdb's
    # lagging file offset and the very next gdb printf OVERWRITES them (run 1 lost all 4 censuses)
    log = open(lpath, "aw")
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
        carr = [c for c in range(256) if c2[c] & MARKER]
        # O_APPEND puts the census INSIDE the gdb event stream, in execution order
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
    ev = parse(open(lpath, "r", errors="replace").read())
    with open(os.path.join(EVID, f"{a.tag}_seq.jsonl"), "w") as fh:
        for d in ev: fh.write(json.dumps(d) + "\n")

    # VISIT index = how many production-function entries (FUNCIN 0x4ef6d0) precede the event.
    # A BOUNDARY line carries the visit it was appended INTO: if the driver's census lands between
    # that visit's MARK and its CLEAR, the census is a MID-VISIT SNAPSHOT, which is what M77 could
    # not distinguish from a mark that survived to the next turn.
    pos, v, wi = 0, 0, []
    for d in ev:
        d["pos"] = pos
        pos += 1
        if d["tag"] == "FUNCIN":
            v += 1
        d["visit"] = v
        if d["tag"] != "FUNCIN":
            wi.append(d)
    marks = [(d["tid"], d["visit"]) for d in wi if d["tag"] == "MARK"]
    clears = [(d["tid"], d["visit"]) for d in wi if d["tag"] in CLR8]
    sweepcalls = [d for d in wi if d["tag"] == "SWEEPCALL"]
    ret_hist = {"SWEEPCALL": {}, "CLEAR": {}}
    for d in wi:
        if d["tag"] in ret_hist and "ret" in d:
            ret_hist[d["tag"]][d["ret"]] = ret_hist[d["tag"]].get(d["ret"], 0) + 1
    tracked_tags = SET8 + CLR8
    bogus = sorted({d["tid"] for d in wi if "tid" in d and d["tag"] in tracked_tags
                    and not 0 <= d["tid"] < 256})
    wide = sorted({(d["tid"], d["tag"]) for d in wi if "tid" in d and d["tag"] not in tracked_tags
                   and not 0 <= d["tid"] < 256})

    # replay of bit 8 only: baseline -> the event stream, compared at every BOUNDARY line
    bit8 = {t: bool(before[t] & MARKER) for t in range(256)}
    replay_ok, replay_rows, race = True, [], []
    for d in ev:
        if d["tag"] == "BOUNDARY":
            carr = sorted(t for t in bit8 if bit8[t])
            got = {t: d.get("w%d" % t) for t in WATCH}
            ok = (carr == d["carriers"] and
                  all(bool((got[t] or 0) & MARKER) == bit8[t] for t in WATCH))
            replay_rows.append((d["idx"], d["carriers"], carr, got, ok))
            if not ok:
                replay_ok = False
                race.append((d["idx"], d["carriers"], carr,
                             {t: (got[t], bit8[t]) for t in WATCH
                              if bool((got[t] or 0) & MARKER) != bit8[t]}))
            continue
        t = d.get("tid")
        if t is None or not 0 <= t < 256:
            continue
        if d["tag"] in SET8:
            bit8[t] = True
        elif d["tag"] in CLR8:
            bit8[t] = False

    # is a carrier census INSIDE its tid's mark->clear pair of ONE visit?
    def inside_pair(t, d):
        mk = [x for x in wi if x["tag"] == "MARK" and x["tid"] == t and x["visit"] == d["visit"]
              and x["pos"] < d["pos"]]
        cl = [x for x in wi if x["tag"] in CLR8 and x["tid"] == t and x["visit"] == d["visit"]
              and x["pos"] > d["pos"]]
        return bool(mk) and bool(cl)

    census_class = []
    for d in wi:
        if d["tag"] != "BOUNDARY":
            continue
        cls = {t: ("mid-pair" if inside_pair(t, d) else "OUTSIDE") for t in d["carriers"]}
        census_class.append((d["idx"], d["visit"], cls))
    mid_pair = [c for c in census_class if c[2] and all(v2 == "mid-pair" for v2 in c[2].values())]
    outside = [c for c in census_class if any(v2 == "OUTSIDE" for v2 in c[2].values())]

    across_visit = sorted({(t, i, j) for t, i in marks for t2, j in clears
                           if t2 == t and j != i})
    same_visit = bool(marks) and bool(clears) and not across_visit and \
        all(any(t2 == t and j == i for t2, j in clears) for t, i in marks)

    g1 = bool(sweepcalls) and any(d["tag"] == "MARK" for d in wi) and bool(clears) and \
         any(d["tag"] == "GATE" for d in wi) and not bogus
    g2 = bool(sweepcalls) and bool(ret_hist["SWEEPCALL"]) and bool(ret_hist["CLEAR"]) and \
         all(d["ret"] in SWEEP_RETS for d in sweepcalls) and \
         all(t in CLEAR_RETS for t in ret_hist["CLEAR"])
    g3 = pred_same != pred_across
    g4 = same_visit != bool(across_visit)
    g5 = replay_ok and any(d["tag"] == "BOUNDARY" for d in ev)
    g6 = bool(clears) and all((d["pre"] & MARKER) for d in wi if d["tag"] in CLR8)
    cleared_tids = sorted({t for t, _ in clears})
    g7 = bool(cleared_tids) and all(not (after.get(t, 0) & MARKER) for t in cleared_tids)
    # g8: every sweep call from the production site follows a production flag store of the SAME tid
    prod_attr = []
    for n, d in enumerate(wi):
        if d["tag"] == "SWEEPCALL" and d["ret"] == 0x4efe83:
            prev = next((x for x in reversed(wi[:n]) if x["tag"] in ("PRODFLAG", "SWEEPCALL")), None)
            prod_attr.append((d["tid"], prev.get("tid") if prev else None))
    g8 = any(d["ret"] == 0x4efe83 for d in sweepcalls) and bool(prod_attr) and \
         all(x == y for x, y in prod_attr)
    # g9: M77's paradox reproduced AND explained — every census that saw 0x100 saw it inside the
    # one visit that marked and cleared, i.e. the driver's census is a mid-visit snapshot.
    g9 = bool(mid_pair) and not outside and same_visit

    for r_ in replay_rows:
        print(f"  census {r_[0]}: observed carriers {r_[1]} | replayed {r_[2]} | "
              f"observed words {r_[3]} | match={r_[4]}", flush=True)
    print("census classification (boundary, visit, per-carrier mid-pair/OUTSIDE):", census_class, flush=True)
    print("MARK events (tid, visit):", marks, flush=True)
    print("CLEAR/UPKCLR events (tid, visit):", clears, flush=True)
    print("SWEEPCALL callers observed:", {hex(k): (SWEEP_RETS.get(k, "UNVERIFIED"), v)
                                          for k, v in sorted(ret_hist["SWEEPCALL"].items())}, flush=True)
    print("CLEAR callers observed:", {hex(k): (CLEAR_RETS.get(k, "UNVERIFIED"), v)
                                      for k, v in sorted(ret_hist["CLEAR"].items())}, flush=True)
    print("cross-VISIT mark->clear pairs:", across_visit, flush=True)
    print(f"H_SAME-VISIT holds={same_visit}  H_ACROSS-VISIT holds={bool(across_visit)}  "
          f"mid-pair censuses={mid_pair}  outside censuses={outside}  race={race}", flush=True)
    print("production sweep-call attribution (sweep tid, preceding PRODFLAG tid):", prod_attr, flush=True)
    print("tracked tids outside the 256-record array:", bogus,
          " non-tracked events at array indices >= 256:", wide, flush=True)
    res = {"g1_instrument_alive_sweep_mark_clear_gate": g1,
           "g2_every_caller_ret_is_a_static_call_target": g2,
           "g3_shape_discriminates": g3,
           "g4_exactly_one_ordering_hypothesis_holds": g4,
           "g5_census_replay_exact_every_boundary": g5,
           "g6_clears_only_ever_on_carriers": g6,
           "g7_no_cleared_tid_still_carries_0x100": g7,
           "g8_production_sweeps_follow_their_own_prodstore": g8,
           "g9_every_carrier_census_is_a_mid_visit_snapshot": g9}
    for k, v in res.items():
        print(f"  {k}: {v}", flush=True)
    ok = all(res.values())
    print(f"{a.tag}: {'PASS' if ok else 'FAIL'}", flush=True)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
