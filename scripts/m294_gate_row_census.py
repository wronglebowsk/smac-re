#!/usr/bin/env python3
"""M294 - the pod-walk census RE-ARMED: prints the B15 gate rows live.

Shape = scripts/m292_pod_movement.py (that file's static gates re-run verbatim;
its leg breakpoints are reused ONLY after that re-derivation - M293 guards law).
NEW this census: the price-gate rows of FUN_0055f650's own scan loop, printed at
three byte-pinned points (pins verified against terran.exe at --static time):

  GDEEP @ 0x563c3d  (before mov dl,[edi+ebx+0x94e5a8]) - fires ONLY when the
     slot passed the value>best argmax skip AND the bypass (jge 0x563ca7 at
     0x563c38) was NOT taken: full gate inputs incl. OLD best and mult.
  GACC  @ 0x563ca7  (mov eax,[ebp-0x2c] - the single ACCEPT funnel; the bypass
     accept never reaches 0x563c3d, so this row carries the FULL row set read
     from SLOTS/memory, never from $edi (at this pc $edi may still be the
     nearest_dist dword loaded at 0x563c24 - register/slot divergence trap).
  GROW  @ 0x563cb3  (loop tail; fires EXACTLY once per slot 0..24 - best/win are
     meaningful, but $esi there = slot/x GARBAGE for slots the loop-head
     eligibility pre-checks (0x5638dc/17/28/3e/4e/57/6d -> tail jumps, incl. the
     region==[ebp-0x34] test at 0x56394e and the call 0x4e3c00 no-go at 0x563963)
     skipped: GROW.val counts ONLY where a GDEEP/GACC row for the same slot
     exists. [ebp-0x34] stays the POD region through the whole loop.)

Frame (FUN_0055f650, one giant function, m292 G2/G3 + B15 prologue pins):
  [ebp+8]=u  [ebp-0x34]=region(slot; pod tile in prologue)  [ebp-0x44]=case
  [ebp-0x48]=blk=owner*8380  [ebp-0x8c]=pod-region verdict  [ebp-0x24]=best
  [ebp-0x2c]=slot  [ebp-0x84]=winner slot  [ebp-0x10]=52*u fold  ds:0x8f0d34=dist

LIVE gates (self-contained on THIS window; sim.gatetables.price_gate = the law):
  G4 pump: >=1 CTRL row and year movement (as m292).
  G5 model parity: for EVERY hub visit that printed gate rows, replay the loop
     from the PRINTED GROW/GDEEP rows with price_gate(); the predicted accept-set
     == the actual GACC rows, the predicted winner slot == DISP esi, the
     predicted leg (FOUND/MSG/continue/ISS from esi+own) == the actual leg row.
     A disagreement is THE FINDING (write the numbers; never weaken a floor).
  G6 row-targets: FOUND events at tiles (22,14) / (18,2) (the 3 recorded
     row-dependent winners' tiles, evidence/b15_gate_tables.txt G5) print their
     full gate rows here; if they do not recur, that is recorded, not hidden.
  G7 guardfail rows == 0 (a guard rejected evidence -> instrument gap).
  G8 box hygiene: TracerPid 0 post-window; yama RESTORED TO THE PRE-WINDOW VALUE.

Exit codes: 0 = PASS, 1 = documented FAIL with numbers, 4 = window ran, zero
dispatch-eligible visits (inconclusive), 8 = box precondition dirty.
"""
import os
import re
import signal
import struct
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCR = os.path.join(ROOT, "scratch")
EVID = os.path.join(ROOT, "evidence")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from sim.gatetables import price_gate  # shipped B15 closed form (byte-verified)
import m292_pod_movement as M292       # static_gates() re-run, not trusted blind

FAM = 8380
GDB_SCRIPT = r"""set pagination off
set confirm off
set verbose off
break *0x55f650
commands
silent
printf "HUB u=%d ret=%#x\n", *(int *)($esp+4), *(int *)$esp
continue
end
break *0x563c3d
commands
silent
set $gu = *(int *)($ebp+8)
set $gblk = $edi
if $ebx >= 0 && $ebx < 128 && $gblk >= 0 && $gblk % 8380 == 0 && $gblk == *(int *)($ebp-0x48) && $gu >= 0 && $gu < 2500
printf "GDEEP slot=%d x=%d y=%d val=%d best=%d reg=%d blk=%d dist=%d mult=%d gate=%d verd=%d case=%d basecnt=%d unit24=%d tiles=%d u=%d\n", *(int *)($ebp-0x2c), *(int *)($ebp-0x8), *(int *)($ebp-0x4), $esi, *(int *)($ebp-0x24), $ebx, $gblk, *(int *)0x8f0d34, *(unsigned char *)($gblk+$ebx+0x94e5a8), *(unsigned char *)($gblk+$ebx+0x94eca8), *(int *)($ebp-0x8c), *(int *)($ebp-0x44), *(int *)($gblk+0x94e488), *(unsigned char *)(*(int *)($ebp-0x10)+0x933289), *(int *)(28*$ebx+0x989ce4), $gu
else
printf "GDEEP guardfail slot=%d val=%d best=%d ebx=%d edi=%d u=%d\n", *(int *)($ebp-0x2c), $esi, *(int *)($ebp-0x24), $ebx, $gblk, $gu
end
continue
end
break *0x563ca7
commands
silent
set $gu = *(int *)($ebp+8)
set $gblk = *(int *)($ebp-0x48)
set $greg = *(int *)($ebp-0x34)
if $gblk % 8380 == 0 && $greg >= 0 && $greg < 128 && $gblk >= 0 && $gu >= 0 && $gu < 2500
printf "GACC slot=%d x=%d y=%d val=%d best=%d reg=%d blk=%d dist=%d mult=%d gate=%d verd=%d case=%d basecnt=%d unit24=%d tiles=%d u=%d\n", *(int *)($ebp-0x2c), *(int *)($ebp-0x8), *(int *)($ebp-0x4), $esi, *(int *)($ebp-0x24), $greg, $gblk, *(int *)0x8f0d34, *(unsigned char *)($gblk+$greg+0x94e5a8), *(unsigned char *)($gblk+$greg+0x94eca8), *(int *)($ebp-0x8c), *(int *)($ebp-0x44), *(int *)($gblk+0x94e488), *(unsigned char *)(*(int *)($ebp-0x10)+0x933289), *(int *)(28*$greg+0x989ce4), $gu
else
printf "GACC guardfail slot=%d val=%d ebx=%d blk=%d u=%d\n", *(int *)($ebp-0x2c), $esi, *(int *)($ebp-0x34), $gblk, $gu
end
continue
end
break *0x563cb3
commands
silent
printf "GROW slot=%d val=%d best=%d win=%d\n", *(int *)($ebp-0x2c), $esi, *(int *)($ebp-0x24), *(int *)($ebp-0x84)
continue
end
break *0x563d46
commands
silent
set $u = *(int *)($ebp+8)
if $u >= 0 && $u < 2500
printf "DISP u=%d esi=%d st=%d own=%d ownrec=%d curfac=%d x=%d y=%d\n", $u, $esi, *(int *)($ebp-0x44), *(int *)($ebp-0xa4), *(unsigned char *)(0x933286+52*$u), *(int *)0x91b5b4, *(short *)(0x933278+52*$u), *(short *)(0x93327a+52*$u)
else
printf "DISP u=%d oob\n", $u
end
continue
end
break *0x563d75
commands
silent
printf "MSG u=%d\n", $esi
continue
end
break *0x563d82
commands
silent
set $u = *(int *)($ebp+8)
if $u >= 0 && $u < 2500
printf "HUBFOUND u=%d x=%d y=%d\n", $u, *(short *)(0x933278+52*$u), *(short *)(0x93327a+52*$u)
else
printf "HUBFOUND u=%d oob\n", $u
end
continue
end
break *0x563e37
commands
silent
printf "ISS u=%d esi=%d tile=%d\n", $ecx, $esi, $eax
continue
end
break *0x4e47d0
commands
silent
printf "FOUND ret=%#x fac=%d x=%d y=%d cnt=%d\n", *(int *)($esp), *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+12), *(int *)0x985af4
continue
end
break *0x4e515d
commands
silent
printf "DESTROY cnt=%d\n", *(int *)0x985af4
continue
end
break *0x4e8d60
commands
silent
printf "CTRL yr=%d cur=%d cnt=%d\n", *(int *)0x985b00, *(int *)0x985dcc, *(int *)0x985af4
continue
end
continue
"""

# NEW byte pins this census arms at (address-keyed; EXPECT_BYTES in m292 covers
# the reused leg sites). Source of truth = the file image of terran.exe.
PINS294 = [
    (0x563bf7, "8b5dcc", "loop gate head: mov ebx,[ebp-0x34] (slot_region)"),
    (0x563c0f, "3bf0", "argmax: cmp esi,eax (value vs best)"),
    (0x563c11, "0f8e9c000000", "argmax: jle 0x563cb3 (value<=best skip)"),
    (0x563c24, "8b3d340d8f00", "mov edi,ds:0x8f0d34 (nearest_dist)"),
    (0x563c38, "7d6d", "bypass: jge 0x563ca7 (accept WITHOUT the mult load)"),
    (0x563c3d, "8a941fa8e59400", "GDEEP: mov dl,BYTE[edi+ebx+0x94e5a8] (site_score)"),
    (0x563c48, "83bf88e4940002", "cmp DWORD[edi+0x94e488],2 (base count)"),
    (0x563c51, "8b8574ffffff", "mov eax,[ebp-0x8c] (pod-region verdict slot)"),
    (0x563c59, "8a8c1fa8ec9400", "mov cl,BYTE[edi+ebx+0x94eca8] (site_gate)"),
    (0x563c75, "837dbc08", "cmp DWORD[ebp-0x44],8 (case)"),
    (0x563c7e, "80b88932930018", "cmp BYTE[eax+0x933289],0x18 (unit rec +0x11)"),
    (0x563c87, "8d0cdd00000000", "lea ecx,[ebx*8]; -> sub ecx,ebx = 7*region"),
    (0x563c97, "8b048de49c9800", "mov eax,[ecx*4+0x989ce4] (tiles, 28*region)"),
    (0x563ca3, "3bc2", "cmp eax,edx (tiles >= 6*(mult+1) via dl copy)"),
    (0x563ca7, "8b45d4", "GACC: the single accept funnel mov eax,[ebp-0x2c]"),
    (0x563caa, "8975dc", "accept body: mov [ebp-0x24],esi (best=value)"),
    (0x563cad, "89857cffffff", "accept body: mov [ebp-0x84],eax (win=slot)"),
    (0x563cb3, "8b45d4", "GROW: loop tail mov eax,[ebp-0x2c]"),
    (0x55f7a5, "8945cc", "prologue: region -> [ebp-0x34]"),
    (0x55f74a, "8945bc", "prologue: case (type rec +42) -> [ebp-0x44]"),
    (0x55f7f4, "8b75f4", "blk fold head: mov esi,[ebp-0xc] (owner)"),
    (0x55f800, "8d3c46", "blk fold: lea edi,[esi+eax*2] (131*o)"),
    (0x55f809, "2bfe", "blk fold: sub edi,esi (2095*o)"),
    (0x55f80b, "c1e702", "blk fold: shl edi,2 (= 8380*o)"),
    (0x55f80e, "897db8", "blk -> [ebp-0x48]"),
    (0x55f811, "8a9407a8ed9400", "verdict load BYTE[edi+eax+0x94eda8]"),
    (0x55f81b, "899574ffffff", "verdict -> [ebp-0x8c]"),
]


def static_gates294():
    d, va0, vsize, raddr = M292.load_text()

    def b(va, n):
        return d[raddr + (va - va0): raddr + (va - va0) + n]

    ok = True
    bad = []
    for va, hexs, note in PINS294:
        got = b(va, len(hexs) // 2).hex()
        if got != hexs:
            ok = False
            bad.append("  BAD %#x want %s got %s ; %s" % (va, hexs, got, note))
    # fold arithmetic re-check (identity only; the pins above are the authority):
    # eax=o<<6; eax+=o (65o); edi=o+eax*2 (131o); edi<<=4 (2096o); edi-=o (2095o);
    # edi<<=2 (8380o).
    o = 3
    eax = (o << 6) + o
    edi = o + eax * 2
    edi = (edi << 4) - o
    edi = edi << 2
    fold_ok = edi == FAM * o
    if not fold_ok:
        ok = False
        bad.append("  BAD fold identity 8380*o")
    print("S1 new bp pins (%d sites): %s" % (len(PINS294), "PASS" if ok else "FAIL"))
    for ln in bad:
        print(ln)
    print("S2 blk fold == 8380*owner: %s" % ("PASS" if fold_ok else "FAIL"))
    return ok


ROW = re.compile(r"^(HUB|DISP|MSG|HUBFOUND|ISS|FOUND|DESTROY|CTRL|GDEEP|GACC|GROW)\b")

KV = re.compile(r"(\w+)=(-?\d+|0x[0-9a-f]+)")


def parse_rows(path):
    rows = []
    for ln in open(path):
        ln = ln.strip()
        if not ROW.match(ln):
            continue
        parts = ln.split(None, 1)
        tag = parts[0]
        kv = {k: int(v, 0) for k, v in KV.findall(ln)}
        rows.append((tag, kv, ln))
    return rows


def model_visits(rows):
    """Split into hub visits (between HUB rows); replay each loop from GROW rows."""
    visits = []
    cur = None
    for tag, kv, ln in rows:
        if tag == "HUB" and "ret" in kv:
            if cur:
                visits.append(cur)
            cur = {"hub": kv, "GROW": [], "GDEEP": [], "GACC": [], "DISP": None,
                   "MSG": None, "HUBFOUND": None, "ISS": None, "FOUNDs": []}
        elif cur is not None:
            if tag in ("GROW", "GDEEP", "GACC"):
                cur[tag].append(kv)
            elif tag == "DISP":
                cur["DISP"] = kv
            elif tag in ("MSG", "HUBFOUND", "ISS"):
                cur[tag] = kv
            elif tag == "FOUND":
                cur["FOUNDs"].append(kv)
    if cur:
        visits.append(cur)
    return visits


def replay(v):
    """Predict from printed rows: returns dict(ok, notes, pred_win, pred_legs)."""
    notes = []
    grow = {g["slot"]: g for g in v["GROW"]}
    deep = {g["slot"]: g for g in v["GDEEP"] if "mult" in g}
    accs = {g["slot"]: g for g in v["GACC"] if "mult" in g}
    if len(v["GROW"]) != len(grow):
        notes.append("DUPLICATE-slot GROW rows (ring re-entry within one visit?)")
    partial = len(grow) < 25          # truncated window tail
    pred_acc = []
    for slot in sorted(set(deep) | set(accs)):
        d = deep.get(slot) or accs[slot]
        outcome, branch = price_gate(d["val"], d["best"], d["dist"], d["mult"],
                                     d["basecnt"], d["verd"], d["gate"], d["case"],
                                     d["unit24"], d["tiles"])
        if outcome == "accept":
            pred_acc.append(slot)
            if slot not in accs:
                notes.append("slot %d: law ACCEPT(%s) but no GACC row" % (slot, branch))
            elif slot not in deep and branch != "bypass":
                notes.append("slot %d: GACC without GDEEP but law says %s (not bypass)" %
                             (slot, branch))
        elif slot in accs:
            notes.append("slot %d: law SKIP(%s) but GACC row printed" % (slot, branch))
    pred_win = pred_acc[-1] if pred_acc else None
    if grow:  # the tail's win field is an ACTUAL: last-slot GROW win == real winner
        last = grow[max(grow)]
        if len(grow) == 25 and pred_win is not None and last.get("win") not in (None, pred_win):
            notes.append("GROW win field %s != model winner %s" % (last.get("win"), pred_win))
    return {"ok": (not notes) or partial, "partial": partial, "notes": notes,
            "pred_win": pred_win, "n_grow": len(grow),
            "n_dec": len(set(deep) | set(accs))}


def main():
    args = sys.argv[1:]
    if args and args[0] == "--static":
        print("m292 static gates (re-derived, never reused blind):")
        ok = M292.static_gates()
        print("m294 new pins:")
        ok = static_gates294() and ok
        print("STATIC %s" % ("PASS" if ok else "FAIL"))
        return 0 if ok else 1

    turns = 24
    if args and args[0] == "--turns":
        turns = int(args[1])

    print("STATIC FIRST (no box): re-derive every reused guard")
    if not M292.static_gates():
        print("STATIC FAIL - not arming the box")
        return 1
    if not static_gates294():
        print("STATIC FAIL - not arming the box")
        return 1

    box = M292.Box()
    box.open()
    if box.tracer() != 0:
        print("PRECOND DIRTY: TracerPid=%d" % box.tracer())
        return 8
    cnt0, yr0, cu0 = box.vals()
    print("PRE-WINDOW: pid=%d count=%d year=%d cur=%d TracerPid=0" % (box.pid, cnt0, yr0, cu0))

    os.makedirs(SCR, exist_ok=True)
    gpath = os.path.join(SCR, "m294_census.gdb")
    with open(gpath, "w") as f:
        f.write(GDB_SCRIPT)
    rawlog = os.path.join(SCR, "m294_gdb_raw.log")

    pre_yama = M292.yama_read()
    if pre_yama != 0:
        if not M292.yama(0):
            print("PRECOND DIRTY: could not clear yama ptrace_scope")
            return 8
    try:
        glog = open(rawlog, "wb", buffering=0)
        gdb = subprocess.Popen(["stdbuf", "-o0", "gdb", "-q", "-batch",
                                "-x", gpath, "-p", str(box.pid)],
                               stdout=glog, stderr=subprocess.STDOUT)
        time.sleep(4)
        if gdb.poll() is not None:
            print("PRECOND DIRTY: gdb exited early (attach failed?)")
            glog.close()
            return 8
        env = dict(os.environ, DISPLAY=":99")
        dlog = open(os.path.join(SCR, "m294_drive.log"), "wb")
        drv = subprocess.Popen(
            ["python3", "scripts/smac_play.py", "--turns", str(turns),
             "--timeout", "300", "--no-escape", "2000", "--tag", "m294",
             "--no-orders", "--no-verify", "--verbose"],
            cwd=ROOT, stdout=dlog, stderr=subprocess.STDOUT, env=env)
        try:
            rc = drv.wait(timeout=turns * 90 + 300)
        except subprocess.TimeoutExpired:
            drv.kill()
            rc = -99
        dlog.close()
        time.sleep(20)
        if gdb.poll() is None:
            os.kill(gdb.pid, signal.SIGINT)
        for _ in range(60):
            if gdb.poll() is not None:
                break
            time.sleep(0.5)
        if gdb.poll() is None:
            gdb.terminate()
            time.sleep(2)
        glog.close()
        try:
            os.kill(box.pid, signal.SIGCONT)
        except OSError:
            pass
    finally:
        ok_y = M292.yama(pre_yama)          # restore the PRE value, never hardcode
    time.sleep(3)

    try:
        st_post = box.tracer()
        cnt1, yr1, cu1 = box.vals()
    except (OSError, FileNotFoundError):
        print("POST-WINDOW: game process gone (drv rc=%d)" % rc)
        return 5
    print("POST-WINDOW: count=%d year=%d cur=%d TracerPid=%d yama-restored=%s drv rc=%d" %
          (cnt1, yr1, cu1, st_post, ok_y, rc))
    if st_post != 0:
        print("BOX DIRTY: TracerPid=%d after census" % st_post)
        return 8

    rows = parse_rows(rawlog)
    ctrl = [r for r in rows if r[0] == "CTRL"]
    yrs = [r[1]["yr"] for r in ctrl if "yr" in r[1]]
    visits = model_visits(rows)
    with_rows = [v for v in visits if v["GROW"]]
    guardfail = sum(1 for tag, kv, ln in rows
                    if tag in ("GDEEP", "GACC") and "guardfail" in ln)
    disp = [v for v in with_rows if v["DISP"]]

    print("rows: visits=%d with-GROW=%d with-DISP=%d CTRL=%d FOUND=%d guardfail=%d" %
          (len(visits), len(with_rows), len(disp), len(ctrl),
           sum(len(v["FOUNDs"]) for v in visits), guardfail))

    lines = []          # evidence report lines
    fails = []

    # G4 pump
    g4 = len(ctrl) >= 1 and len(set(yrs)) >= max(1, turns // 4)
    if not g4:
        fails.append("G4 pump: CTRL=%d distinct-years=%d turns=%d" % (len(ctrl), len(set(yrs)), turns))
    lines.append("G4 pump: CTRL=%d years=%d -> %s" % (len(ctrl), len(set(yrs)), "PASS" if g4 else "FAIL"))

    # G5 model parity over every gate-row visit
    bad_visits = 0
    part_visits = 0
    total_acc = 0
    for v in with_rows:
        r = replay(v)
        total_acc += len(v["GACC"])
        if v["DISP"] and not r["partial"]:
            esi = v["DISP"].get("esi")
            if r["pred_win"] is None:
                r["notes"].append("DISP esi=%s but model found NO accept" % esi)
            elif esi != r["pred_win"]:
                r["notes"].append("esi mismatch: model %s vs DISP %s" % (r["pred_win"], esi))
            own = v["DISP"].get("own")
            got_leg = ("MSG" if v["MSG"] else "HUBFOUND/ISS" if (v["HUBFOUND"] or v["ISS"])
                       else "none")
            if r["pred_win"] == 0:
                want = "MSG" if own else "HUBFOUND/ISS"
                if got_leg != want:
                    r["notes"].append("leg mismatch own=%d: %s vs %s" % (own, got_leg, want))
            elif r["pred_win"] is not None and r["pred_win"] >= 1 and r["pred_win"] <= 8:
                if got_leg != "none":
                    r["notes"].append("continue-leg but %s row printed" % got_leg)
        if r["partial"]:
            part_visits += 1
        if not r["ok"]:
            bad_visits += 1
            lines.append("VISIT u=%s ret=%#x esi=%s GROW=%d GDEEP=%d GACC=%s -> NOTES %s" %
                         (v["hub"].get("u"), v["hub"].get("ret", 0),
                          (v["DISP"] or {}).get("esi"), len(v["GROW"]), len(v["GDEEP"]),
                          sorted(a["slot"] for a in v["GACC"]), "; ".join(r["notes"])))
    disp_no_rows = sum(1 for v in visits if v["DISP"] and not v["GROW"])
    if disp_no_rows:
        fails.append("G5: %d visits had DISP but NO GROW rows (instrument silence, M293)" % disp_no_rows)
    g5 = bad_visits == 0 and len(with_rows) >= 1 and not disp_no_rows
    lines.append("G5 parity: %d gate-visits (%d partial tail), %d accepts, %d disagreements, "
                 "%d DISP-without-rows -> %s" %
                 (len(with_rows), part_visits, total_acc, bad_visits, disp_no_rows,
                  "PASS" if g5 else "FAIL"))
    if not g5 and len(with_rows) >= 1:
        fails.append("G5 parity: %d/%d visits disagree" % (bad_visits, len(with_rows)))

    # every printed gate row verbatim for the record (bounded): FOUND tiles + all GACC
    for v in with_rows:
        for a in v["GACC"]:
            lines.append("GACC-ROW u=%s %s" % (a.get("u"), a))

    # G6 row-targets (recorded row-dependent winners' tiles)
    targets = [(22, 14), (18, 2)]
    for tx, ty in targets:
        hit = None
        for v in visits:
            for fd in v["FOUNDs"]:
                if fd.get("x") == tx and fd.get("y") == ty:
                    hit = (v, fd)
        if hit:
            v, fd = hit
            lines.append("G6 TARGET (%d,%d) FOUND u=%s: GACC rows %s" %
                         (tx, ty, fd.get("cnt"), [str(a) for a in v["GACC"]]))
        else:
            lines.append("G6 TARGET (%d,%d) did NOT recur this window (recorded, not hidden)" % (tx, ty))
    g6_note = all(any(fd.get("x") == tx and fd.get("y") == ty
                      for v in visits for fd in v["FOUNDs"]) for tx, ty in targets)

    # G7 guardfail
    g7 = guardfail == 0
    lines.append("G7 guardfail rows: %d -> %s" % (guardfail, "PASS" if g7 else "FAIL"))
    if not g7:
        fails.append("G7 guardfail=%d (instrument gap)" % guardfail)

    # G8 hygiene (printed above); counted PASS if yama restored and TracerPid 0
    g8 = ok_y and st_post == 0
    lines.append("G8 hygiene: yama-restored=%s TracerPid=%d -> %s" % (ok_y, st_post, "PASS" if g8 else "FAIL"))
    if not g8:
        fails.append("G8 hygiene yama=%s tracer=%d" % (ok_y, st_post))

    verdict = len(with_rows) == 0
    passed = not fails and not verdict
    out = []
    out.append("M294 pod-walk gate-row census  turns=%d  state y%d/%d cnt=%d -> y%d cnt=%d" %
               (turns, yr0, cu0, cnt0, yr1, cnt1))
    out.extend(lines)
    out.append("VERDICT: %s" % ("PASS" if passed else ("INCONCLUSIVE (no gate rows)" if verdict else "FAIL")))
    for fmsg in fails:
        out.append("FAIL " + fmsg)
    out.append("G6 targets recurred: %s" % g6_note)
    report = "\n".join(out) + "\n"

    ev_main = os.path.join(EVID, "m294_gate_rows.txt")
    ev_raw = os.path.join(EVID, "m294_gate_rows_raw.txt")
    with open(ev_main, "w") as f:
        f.write(report)
    with open(ev_raw, "w") as f:
        f.write("=== raw gdb rows (M294, %d turns from y%d) ===\n" % (turns, yr0))
        n = 0
        kept = 0
        with open(rawlog) as g:
            for ln in g:
                if ROW.match(ln.strip()):
                    n += 1
                    if kept < 60000:
                        f.write(ln)
                        kept += 1
        f.write("=== rows total %d, kept %d (%s) ===\n" %
                (n, kept, "FULL" if kept == n else "TRUNCATED - full log in scratch/m294_gdb_raw.log"))
    print(report)
    print("evidence: %s (%d B), %s (%d B)" %
          (ev_main, os.path.getsize(ev_main), ev_raw, os.path.getsize(ev_raw)))
    if verdict:
        return 4
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
