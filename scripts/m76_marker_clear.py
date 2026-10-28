#!/usr/bin/env python3
"""M76: WHO CLEARS the 0x100 sweep marker, and FOR WHICH RECORDS.

Static (instruction bytes, `scratch/m574/text.txt`):
  0x4ef398 `and BYTE PTR [ebx+0x98adb9],0xfe` is the FIRST statement of FUN_004ef380(owner, tid)
  (ebx = tid*52 from [ebp+0xc]*13<<2), so the clear always fires on the record PASSED IN.
  Two callers select records the same way, walking {0..63} U {owner*64..+63}:
    FUN_004ef540(owner)  test at 0x4ef597 (flags&1, &4, &0x100) -> call at 0x4ef5ae (ret 0x4ef5b3)
    inside FUN_004ef6d0 (the production path) test at 0x4f060f -> call at 0x4f0626 (ret 0x4f062b)
  and FUN_004ef540 itself is called only from 0x5a7d14 / 0x5a7f7b (inside FUN_005a7970).
  Two more direct callers: 0x521479 (FUN_00521070), 0x5a8568 (FUN_005a7970).

This script arms 7 silent breakpoints (gate 0x4efa5e, production setter 0x4efe50, sweep store
0x5729d5, the clear 0x4ef398 printing tid/owner/flags/RETURN-ADDR, the two pass entries/tests at
0x4ef540/0x4ef597 and 0x4f060f), reloads `m54b_clean.SAV`, enqueues 194 and drives boundaries;
then it (a) checks every CLEAR landed on a record the printed selection test called a candidate,
(b) replays the observed stores against the before-census and reads the 0x100 bit back from
memory.  Predictions come from the PRINTED flags, never from the observed calls.

    python3 scripts/m76_marker_clear.py --tag m76marker1      # -> PASS / FAIL
"""
import argparse, json, os, re, signal, struct, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import m55_boundary as M
import m74_flag_watch as F
import m75_sweep_replay as S5

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

# (addr, tag, fmt, args, cond) — every tid/record expression below was read off the
# instruction bytes: 0x4efe50 esi = record byte addr & ebx = tid; 0x5729d5 edi = record byte
# addr; 0x4ef398 ebx = tid*52, [ebp+8] = owner, [ebp+4] = return addr; 0x4ef597/0x4f060f
# eax = tid, edi = owner; 0x4efa5e ebx = tid, edi = price, [ebp-0x1c]... base via 0x8f0d60.
BPS = [
    (0x4efa5e, "VISIT", "VISIT tid=%d edi=%d storage=%d",
     "$ebx, $edi, *(int *)($b + 0x40)", "*(int *)0x8f0d60 == $b"),
    (0x4efe50, "PRODSET", "PRODSET tid=%d flags=0x%x",
     "$ebx, *(unsigned short *)($esi + 0x98adb8)", "*(int *)0x8f0d60 == $b"),
    (0x5729d5, "SWEEP", "SWEEP tid=%d flags=0x%x",
     "$edi / 52, *(unsigned short *)($edi + 0x98adb8)", "1"),
    (0x4ef398, "CLEAR", "CLEAR tid=%d owner=%d flags=0x%x ret=%#x",
     "$ebx / 52, *(int *)($ebp + 8), *(unsigned short *)($ebx + 0x98adb8), *(int *)($ebp + 4)", "1"),
    (0x4ef540, "PASS540", "PASS540 owner=%d", "*(int *)($esp + 4)", "1"),
    (0x4ef597, "P540", "P540 owner=%d tid=%d flags=0x%x",
     "$edi, $eax, *(unsigned short *)($eax * 52 + 0x98adb8)",
     "*(unsigned short *)($eax * 52 + 0x98adb8) & 0x100 || $eax == 192 || $eax == 193 || $eax == 194"),
    (0x4f060f, "PPROD", "PPROD owner=%d tid=%d flags=0x%x",
     "$edi, $eax, *(unsigned short *)($eax * 52 + 0x98adb8)",
     "*(unsigned short *)($eax * 52 + 0x98adb8) & 0x100 || $eax == 192 || $eax == 193 || $eax == 194"),
    # the three whole-word flag stores FUN_00595b10 makes (esi = record BYTE address, per the
    # instruction bytes `mov WORD PTR [esi+0x98adb9],1 / 0x105 / 0x115`): they WRITE the 0x100
    # bit, so the replay needs them or a marker flip looks unexplained.
    (0x595f82, "CODEC1", "CODEC1 tid=%d word=0x1", "$esi / 52", "1"),
    (0x595f91, "CODEC105", "CODEC105 tid=%d word=0x105", "$esi / 52", "1"),
    (0x595f9c, "CODEC115", "CODEC115 tid=%d word=0x115", "$esi / 52", "1"),
    # FUN_00521070 (the upkeep pass) clears the marker INLINE: `and bh,0xfe` at 0x521452 then
    # `mov WORD PTR [edi],bx` at 0x52145e, for every record whose word has bit 8 and whose
    # owner byte [edi-4] lacks the group bit; it then calls FUN_004ef380 only when the record's
    # group == DAT_0091b5b4.  tid is the loop var in [ebp-0xc], edi = record+0x30.
    (0x52145e, "INLINECLEAR", "INLINECLEAR tid=%d group=%d word=0x%x",
     "*(int *)($ebp - 0xc), $esi, $bx", "1"),
    (0x521448, "UPKEEPTEST", "UPKEEPTEST tid=%d group=%d word=0x%x ownbyte=0x%x",
     "*(int *)($ebp - 0xc), $esi, *(unsigned short *)($edi), *(unsigned char *)($edi - 4)",
     "*(int *)($ebp - 0xc) == 192 || *(int *)($ebp - 0xc) == 193 || *(int *)($ebp - 0xc) == 194"),
    # the marker SETTERS outside the sweep: production's else branch 0x4f05bd (eax = tid*52)
    # and FUN_005a7970's two `or BYTE [eax*4+0x98adb9],1` (eax = tid*13).
    (0x4f05bd, "MARKSET1", "MARKSET1 tid=%d", "$eax / 52", "1"),
    (0x5a7d00, "MARKSET2", "MARKSET2 tid=%d", "$eax / 13", "1"),
    (0x5a7f67, "MARKSET3", "MARKSET3 tid=%d", "$eax / 13", "1"),
]

LINE = re.compile(r"^(ARMED|VISIT|PRODSET|SWEEP|CLEAR|PASS540|P540|PPROD|INLINECLEAR|UPKEEPTEST|MARKSET3|MARKSET2|MARKSET1|CODEC115|CODEC105|CODEC1)\s*(.*)$")
KV = re.compile(r"(\w+)=(-?0x[0-9a-f]+|-\d+|\d+)")
RET540, RETPROD = 0x4ef5b3, 0x4f062b


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
        if not m:
            continue
        d = {"tag": m.group(1)}
        for k, v in KV.findall(m.group(2)):
            d[k] = int(v, 16) if v.startswith(("0x", "-0x")) else int(v)
        out.append(d)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m76marker1")
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

    pid = F.game_pid()
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        row = F.base_row(m, BASE_NAME)
        before = F.flag_census(m)
        predicted_sweep = S5.model(m)
    print(f"pid {pid} head {row['slots'][0]} pending {row['pending']} round {row['round']} "
          f"storage {row.get('storage')}", flush=True)
    print("baseline 0x100-carriers:", [c for c in range(256) if before[c] & MARKER], flush=True)
    print("predicted sweep(194) marks:", predicted_sweep, flush=True)

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
        raise SystemExit(f"{a.tag}: enqueue did not land (head {row['slots'][0]} pending {row['pending']})")

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
        marks = [c for c in range(256) if c2[c] & MARKER]
        print(f"  boundary {k}: rc={r.returncode} t={time.time()-t0:.0f}s "
              f"192=0x{c2[192]:03x} 193=0x{c2[193]:03x} 194=0x{c2[PROD]:03x} 0x100-carriers={marks}",
              flush=True)
        if c2[PROD] & 4 and not (c2[193] & MARKER) and (c2[193] & 4):
            print("  production + a marker clear landed, stopping the drive", flush=True)
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
        after = F.flag_census(m)
    ev = parse(open(lpath, "r", errors="replace").read())
    with open(os.path.join(EVID, f"{a.tag}_seq.jsonl"), "w") as fh:
        for d in ev: fh.write(json.dumps(d) + "\n")

    sel = [e for e in ev if e["tag"] in ("P540", "PPROD")]
    cand = [(e["tag"], e["owner"], e["tid"]) for e in sel if (e["flags"] & 0x105) == 0x105]
    ret_of = {"P540": RET540, "PPROD": RETPROD}
    pred_calls = [(ret_of[t], o, i) for t, o, i in cand]
    obs_calls = [(e["ret"], e["owner"], e["tid"]) for e in ev if e["tag"] == "CLEAR"
                 and e["ret"] in (RET540, RETPROD)]
    other_calls = [(hex(e["ret"]), e["owner"], e["tid"]) for e in ev
                   if e["tag"] == "CLEAR" and e["ret"] not in (RET540, RETPROD)]
    clears = [e for e in ev if e["tag"] == "CLEAR"]
    iclears = [e for e in ev if e["tag"] == "INLINECLEAR"]

    # g1: every entry clear landed on a record that CARRIED the marker (it is a marker-clear,
    # not a general flag write).  The full candidate rule (&1 &4 &0x100) is only claimed for the
    # two selection loops and is tested by g2; the upkeep/tech routes require just the marker.
    g1 = bool(clears or iclears) and all(e["flags"] & MARKER for e in clears)
    # g2: for the two selection loops the PRINTED test predicts EXACTLY the calls that came
    # from those return sites (a candidate that went uncalled, or an unmarked call, fails it)
    g2 = pred_calls == obs_calls
    # g3: replay the observed stores onto the before-census; the 0x100 bit must read back as
    # the engine left it (SWEEP |=0x104, CLEAR &=~0x100, PRODSET |=4 on the low byte)
    sim = dict(before)
    last_clear, last_sweep = {}, {}
    for n, e in enumerate(ev):
        t = e["tid"]
        if e["tag"] == "SWEEP":
            sim[t] |= 0x104; last_sweep[t] = n
        elif e["tag"] == "CLEAR":
            sim[t] &= ~MARKER; last_clear[t] = n
        elif e["tag"] == "PRODSET":
            sim[t] = (sim[t] & ~0xFF) | ((sim[t] & 0xFF) | 4)
        elif e["tag"] == "CODEC1":
            sim[t] = (sim[t] & ~0xFFFF) | 0x1
        elif e["tag"] == "CODEC105":
            sim[t] = (sim[t] & ~0xFFFF) | 0x105
        elif e["tag"] == "CODEC115":
            sim[t] = (sim[t] & ~0xFFFF) | 0x115
        elif e["tag"] == "INLINECLEAR":
            sim[t] &= ~MARKER; last_clear[t] = n
        elif e["tag"] in ("MARKSET1", "MARKSET2", "MARKSET3"):
            sim[t] |= MARKER; last_sweep[t] = n   # a marker SET counts as the last marker write
    mism = [f"{c}:sim0x{sim[c] & 0xFFFF:x}/obs0x{after[c] & 0xFFFF:x}"
            for c in range(256) if (sim[c] & 0xFFFF) != (after[c] & 0xFFFF)]
    mismark = [c for c in range(256) if bool(sim[c] & MARKER) != bool(after[c] & MARKER)]
    g3 = not mismark
    # g4: the shape discriminated — a marker was cleared AND a marker survived the window,
    # and nothing that ends the window marked was cleared after its last sweep store
    resid = [c for c in range(256) if after[c] & MARKER]
    cleared = sorted({e["tid"] for e in clears + iclears})
    bad_resid = [c for c in cleared if after[c] & MARKER and last_sweep.get(c, -1) < last_clear.get(c, 0)]
    g4 = bool(cleared) and bool(resid) and not bad_resid
    g5 = tracer == "0" and rc_ok and any(e["tag"] in ("PASS540", "PPROD", "UPKEEPTEST",
                                                      "INLINECLEAR", "CLEAR") for e in ev)
    ok = g1 and g2 and g3 and g4 and g5
    print("selection candidates (printed flags):", pred_calls, flush=True)
    print("clears from those sites:", [(hex(r), o, i) for r, o, i in obs_calls], flush=True)
    print("clears from OTHER callers:", other_calls, flush=True)
    print("pass entries:", [e["owner"] for e in ev if e["tag"] == "PASS540"], flush=True)
    print("upkeep tests (192/193/194):", [(e["tid"], hex(e["word"])) for e in ev
          if e["tag"] == "UPKEEPTEST"], flush=True)
    print("inline upkeep clears:", [(e["tid"], e["group"], hex(e["word"])) for e in iclears], flush=True)
    print("marker sets outside the sweep:", [(e["tag"], e["tid"]) for e in ev
          if e["tag"].startswith("MARKSET")], flush=True)
    print("sweep stores:", [(e["tid"], hex(e["flags"])) for e in ev if e["tag"] == "SWEEP"], flush=True)
    print("production setters:", [(e["tid"], hex(e["flags"])) for e in ev if e["tag"] == "PRODSET"], flush=True)
    print("census diff: " + ", ".join(f"{c}:0x{before[c]:03x}->0x{after[c]:03x}"
          for c in range(256) if before[c] != after[c]), flush=True)
    print(f"gates: g1_clear_lands_on_candidate={g1} g2_test==calls={g2} g3_marker_replay={g3} "
          f"g4_discriminated={g4} g5_sanity={g5}\n  cleared={cleared} residue_0x100={resid} "
          f"marker_mismatch={mismark} word_mismatch={mism}", flush=True)
    print(f"ACCEPTANCE {a.tag}: {'PASS' if ok else 'FAIL'} "
          f"(clears={len(cleared)} residue={resid} tracer={tracer})", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
