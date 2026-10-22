#!/usr/bin/env python3
"""M36: dismiss the TERRAFORM tutor pane that has FUN_004d44d0 parked inside
FUN_0048ef40 (pane call at 0x4d58c6) and catch the store tail for real:
PANERET(0x4d58cb) -> AFTERLATCH(0x4d5b16) -> LOCKCHK(0x4d5b71, DAT_0091f718) ->
0x528930(unit,0,-1,-1,0) -> LOCKRET(0x4d5bae) -> STORE(0x4d5bbf, +17=mode+4) ->
BCAST(0x4d5bc6) -> ENQ 0x2101 idx=unit -> DRAIN -> DISP -> EXEC.

Context (turn_driver.md §M35/§M36): m35v2 paid the 9-credit raise debit, the
footprint pass passed, the tutor latch DAT_00985ad4 bit 0x800 was consumed and the
'TERRAFORM' tutor pane (tutor.txt:1102, OK bar at (400,408)) opened — the harness
killed gdb with the pane still open, so the setter never resumed and STORE never
ran. The pane is STILL open on the live game (pid from pgrep), order byte 0.

Usage: python3 scripts/m36_dismiss.py [--tag m36] [--unit 41] [--no-space]
"""
import argparse, json, os, re, shutil, subprocess, struct, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P

ROOT = P.ROOT
EVID = P.EVID


def wait_for(log, needle, timeout):
    """Poll the gdb log (printf may lag behind reality; final truth is read after
    kill -TERM gdb in finish())."""
    end = time.time() + timeout
    while time.time() < end:
        try:
            for line in open(log, errors="replace"):
                if re.search(needle, line):
                    return line.strip()
        except FileNotFoundError:
            pass
        time.sleep(0.35)
    return ""


def snap(tag):
    png = P.freeze(tag)
    dst = os.path.join(EVID, f"{tag}.png")
    shutil.copy(png, dst)
    return dst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m36")
    ap.add_argument("--unit", type=int, default=41)
    ap.add_argument("--no-space", action="store_true")
    a = ap.parse_args()
    U = a.unit
    tag = a.tag
    rec = {"tag": tag, "unit": U, "t": time.strftime("%F %T")}

    # ---- preflight (no tracer) ----
    pid = int(subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True,
                             text=True).stdout.split()[0])
    tracer = subprocess.run(["grep", "TracerPid", f"/proc/{pid}/status"],
                            capture_output=True, text=True).stdout
    rec["tracerpid_line"] = tracer.strip()
    assert "0" in tracer.split()[-1], f"tracer attached: {tracer}"
    rec["pid"] = pid

    f = open(f"/proc/{pid}/mem", "rb", 0)
    def rd(addr, n):
        f.seek(addr); return f.read(n)
    def u32(addr):
        return struct.unpack("<I", rd(addr, 4))[0]

    def snapshot(label):
        u = P.unit_rec(f, U)
        # M35 correction: 0x92ae14 holds a POINTER; P.tile_recs still indexes the
        # slot region, so dereference here (record = *(0x92ae14) + (40*y + x>>1)*0x2c).
        tb = u32(0x92AE14)
        ta = tb + (40 * u["y"] + (u["x"] >> 1)) * 0x2c
        t = rd(ta, 0x2c)
        me = u32(P.PLAYER_G if hasattr(P, "PLAYER_G") else 0x91B5B4)
        out = dict(
            year=u32(0x985B00), cur=u32(0x985DCC), sel=struct.unpack("<i", rd(P.SEL_G, 4))[0],
            orders_mode=u32(0x91B5B8), pending=u32(0x91B5C4),
            energy=struct.unpack("<i", rd(P.ENERGY_G + me * P.ENERGY_STRIDE * 4, 4))[0],
            lock=u32(0x91F718), latch800=bool(u32(0x985AD4) & 0x800),
            tech59=u32(0x985C1C + 59) & 0xff,
            unit=dict(x=u["x"], y=u["y"], order=u["order"], mpused=u["mpused"],
                      flags=hex(u["flags"])),
            tile_addr=hex(ta), tile0=t[0], tile_elev=t[0] >> 5,
            tile_mask=struct.unpack("<I", t[8:12])[0], tile_hex=t.hex())
        rec[label] = out
        return out

    pre = snapshot("pre")
    assert pre["unit"]["order"] == 0, f"unit {U} order already {pre['unit']['order']}"
    assert pre["unit"]["x"] == 45 and pre["unit"]["y"] == 7, f"unit moved: {pre['unit']}"
    assert pre["lock"] == 0, "issue lock already held"

    # pane up? OK bar at (400,408): OCR the bar strip and look for ok/0K
    png = snap(f"{tag}_prepane")
    words = P.ocr_crop(png, (205, 394, 390, 28), f"{tag}_okbar")
    txt = " ".join(w[0] for w in words).lower().replace("0", "o")
    rec["okbar_ocr"] = txt
    assert re.search(r"\bo[kk]\b", txt), f"OK bar not readable: {txt!r}"

    # ---- arm gdb ----
    gsrc = open(os.path.join(ROOT, "scripts", "m36_store.gdb")).read().replace("__UNIT__", str(U))
    gpath = f"{EVID}/{tag}_chain.gdb"
    open(gpath, "w").write(gsrc)
    log = f"{EVID}/{tag}_gdb.log"
    gdb = subprocess.Popen(f"gdb -batch -nx -x {gpath} -p {pid} > {log} 2>&1", shell=True)
    time.sleep(2.5)
    armed = sum(1 for _ in open(log, errors="replace") if "Breakpoint" in _ and " at " in _)
    rec["gdb"] = dict(pid=gdb.pid, breakpoints_armed=armed, expect=18)
    print(f"armed {armed}/18 breakpoints (gdb {gdb.pid})")
    if armed < 18:
        subprocess.run(f"kill -TERM {gdb.pid}", shell=True)
        subprocess.run(f"kill -CONT {pid}", shell=True)
        sys.exit(f"arming failed; see {log}")

    def finish(reason):
        rec["reason"] = reason
        subprocess.run(f"kill -TERM {gdb.pid} 2>/dev/null", shell=True)
        time.sleep(0.8)
        subprocess.run(f"kill -CONT {pid} 2>/dev/null", shell=True)
        time.sleep(1.5)
        rec["post"] = snapshot("post")
        rec["post_png"] = snap(f"{tag}_post")
        rec["gdb_log_tail"] = [l.rstrip() for l in open(log, errors="replace")][-40:]
        json.dump(rec, open(f"{EVID}/{tag}_dismiss.json", "w"), indent=1)
        print(json.dumps({"reason": reason, "post": rec["post"]}, indent=1))
        print("events:", [l for l in open(log, errors="replace")
                          if re.match(r"^[A-Z]", l.strip()) and "Breakpoint" not in l])
        sys.exit(0)

    # ---- dismiss the pane: focus, click OK (400,408); retry once if still up ----
    P.focus()
    P.click((400, 408))
    hit = wait_for(log, "PANERET ", 8)
    if not hit:
        png = snap(f"{tag}_midclick")
        words = P.ocr_crop(png, (205, 394, 390, 28), f"{tag}_okbar2")
        txt = " ".join(w[0] for w in words).lower().replace("0", "o")
        rec["retry_okbar_ocr"] = txt
        if re.search(r"\bo[kk]\b", txt):
            P.focus()
            P.click((400, 408))
            hit = wait_for(log, "PANERET ", 8)
    if not hit:
        finish("no PANERET after two OK clicks (pane not dismissed?)")
    rec["paneret"] = hit

    # ---- store tail ----
    for needle, key, tmo in [("AFTERLATCH ", "afterlatch", 4), ("LOCKCHK ", "lockchk", 4),
                             ("LOCKRET ", "lockret", 4), ("STORE ", "store", 5),
                             ("BCAST ", "bcast", 5), (r"ENQ q=\d+ idx=%d " % U, "enq_unit", 5)]:
        rec[key] = wait_for(log, needle, tmo)
        print(key, "->", rec[key] or "(none)")
    rec["drain"] = wait_for(log, "DRAIN #", 8)
    rec["disp"] = wait_for(log, "DISP ", 4)
    print("drain ->", rec["drain"] or "(none)", "| disp ->", rec["disp"] or "(none)")

    # ---- EXEC: Space on the still-selected unit (skip if turn already ran it) ----
    if not a.no_space:
        sel = struct.unpack("<i", rd(P.SEL_G, 4))[0]
        year_now = u32(0x985B00)
        rec["exec_gate"] = dict(sel=sel, year=year_now,
                                order=struct.unpack("<B", rd(P.UNIT_ARR + U * 52 + 17, 1))[0])
        if not wait_for(log, "EXEC ", 1) and sel == U and year_now == pre["year"]:
            P.focus()
            P.key("space")
            rec["spaceh"] = wait_for(log, "SPACEH ", 5) or wait_for(log, "SOLOWRAP ", 3)
            if not rec["spaceh"]:
                P.focus()
                P.key("space")
                rec["spaceh2"] = wait_for(log, "SPACEH ", 4)
            rec["exec"] = wait_for(log, "EXEC ", 8)
        time.sleep(2)
    finish("done")


if __name__ == "__main__":
    main()
