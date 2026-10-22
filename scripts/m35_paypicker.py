#!/usr/bin/env python3
"""M35: catch the terraform PAY picker answering INSIDE the terraform setter.

What we are testing (all sites objdump-pinned, see scripts/m35_pay.gdb header):
  the TERRAPAY picker ("Cancel action." / "Expend $NUM0 credits.") is shown by
  FUN_004d44d0 at 0x4d55b3 and BLOCKS there until answered; answering "Expend" must
  (a) debit the faction energy pool at 0x4d561a, (b) store order byte mode+4 at
  0x4d5bbf, (c) broadcast 0x2101 at 0x4d5bc6 -> enqueue (FUN_0052a720) -> drain
  (FUN_005262e0) -> dispatcher (FUN_0052bce0) -> maybe the solo executor.
  Question: does that chain fire SYNCHRONOUSLY with the answer, or is it queued?

Statics this run leans on (new in M35):
  * The payment path (LAB_004d5496) is reached ONLY from the mode 0x10/0x11 case
    (Raise/Lower Land) — xrefs to 0x4d5496 come only from 0x4d5277/0x4d5313/0x4d53d8/
    0x4d53f4/0x4d53f9 inside that case. Farm/Road/Sensor/... never show a pane.
  * The tech gate is FUN_005a7520(mode, domain, player): required tech id =
    *(int*)(0x6938e8 + (mode*8 + domain)*4); researched = bit (player & 0x1f) of byte
    0x985c1c + tech_id. Raise/Lower need tech 59 = Environmental Economics.
  * This save: player 3 has 9 techs, EnvEcon NOT researched, and owns no base (so the
    0xb<mode<0x13 "current base is ours" bypass in FUN_005a7520 cannot fire). To make
    the picker reachable we PUBLISH the tech bit (one byte, /proc/pid/mem, no tracer,
    read back before arming gdb) — a harness intervention, recorded in the evidence.

Run: python3 scripts/m35_paypicker.py [--key bracketright] [--no-poke]
"""
import argparse
import json
import os
import shutil
import struct
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "evidence")
UNIT_ARR, SEL_G, ORDERS_G, PENDING_G = 0x933278, 0x91B5BC, 0x91B5B8, 0x91B5C4
CLASS_TBL, TYPE_STRIDE = 0x98ADB2, 52
TILE_PTR_G, TILE_ROW, TILE_SZ = 0x92AE14, 40, 0x2C
ENERGY_G, ENERGY_STRIDE = 0x94D650, 0x82F
TECH_BITS, ENVECON_ID, TECH_REQ_TBL = 0x985C1C, 59, 0x6938E8
MARKS = ("NATIVESEL", "TERRAF", "TECHCHK", "TECHFAIL", "PAYPATH", "ORDERCHK", "COST",
         "TERRACOSTPANE", "PAYPANE", "PAYDECIDE", "PAYTAKEN", "PAYDECLINED", "DEBIT",
         "SKIPPAY", "STORE", "BCAST", "PANE", "ADVISOR", "ENQ", "DRAIN", "DISP",
         "SOLOWRAP", "EXEC", "MOVEUNIT", "SPACEH")


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          env={**os.environ, "DISPLAY": ":99"})


def rd_u32(f, a):
    return struct.unpack("<I", P.rd(f, a, 4))[0]


def rd_i32(f, a):
    return struct.unpack("<i", P.rd(f, a, 4))[0]


def tile_addr(f, x, y):
    """The tile array base is the POINTER stored at 0x92ae14 (asm: `mov esi,[ds:92ae14]`
    then `[esi + idx*4]` with idx = 11*(40*y + x>>1)); M33/M34 used 0x92ae14 itself."""
    base = rd_u32(f, TILE_PTR_G)
    return base + (TILE_ROW * y + (x >> 1)) * TILE_SZ


def find_former(f):
    units = P.rd(f, UNIT_ARR, 300 * 52)
    for i in range(300):
        d = units[i * 52:(i + 1) * 52]
        if d[14] != rd_u32(f, 0x91B5B4):
            continue
        typ = struct.unpack("<H", d[10:12])[0]
        if P.rd(f, CLASS_TBL + typ * TYPE_STRIDE, 1)[0] == 9:
            return i, struct.unpack("<H", d[0:2])[0], struct.unpack("<H", d[2:4])[0], d[17], d[40]
    return None


def screen_ok():
    """HUD-ish: the sample box (180,60,620,200) must be TERRAIN, not a flat panel.
    A modal over the map drops the colour count (measured: customize dialog 77,
    the CHIEF PLANETOLOGIST news pane 104, clean explored map 145-156); OCR word
    counts in the box are useless there because explored terrain OCRs as garbage."""
    png = P.freeze("m35scr")
    w = P.ocr_fast(png)
    nc = P.region_colors(png)
    upper = sum(1 for _t, cx, cy, _w, _h in w if 55 <= cy <= 180 and 180 <= cx <= 620)
    return nc >= 130, png, w, nc, upper


def log_lines(path, prefixes=None):
    out = []
    try:
        with open(path) as fh:
            for ln in fh:
                if ln.startswith(MARKS if prefixes is None else prefixes):
                    out.append(ln.rstrip())
    except OSError:
        pass
    return out


def wait_for(path, prefix, secs):
    t0 = time.time()
    while time.time() - t0 < secs:
        hits = [l for l in log_lines(path) if l.startswith(prefix)]
        if hits:
            return hits
        time.sleep(0.3)
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", default="bracketright", help="xdotool keysym (']' = Raise Land)")
    ap.add_argument("--no-poke", action="store_true", help="skip the EnvEcon tech-bit poke")
    ap.add_argument("--tag", default="m35v1")
    a = ap.parse_args()
    tag = a.tag
    os.makedirs(EVID, exist_ok=True)

    pid = int(sh("pgrep -x terran.exe | head -1").stdout.split()[0])
    assert "TracerPid:\t0" in sh(f"grep TracerPid /proc/{pid}/status").stdout, "tracer attached"
    _, f = P.mem()
    me = rd_u32(f, 0x91B5B4)
    rec = dict(pid=pid, player=me, key=a.key, tag=tag, events=[], panes=[], screenshots=[])

    form = find_former(f)
    if not form:
        sys.exit("no Former owned by us")
    unit, ux, uy = form[0], form[1], form[2]
    rec["unit"] = dict(idx=unit, x=ux, y=uy, order=form[3], mpused=form[4])
    ok, png, words, nc, upper = screen_ok()
    shutil.copy(png, f"{EVID}/{tag}_pre_screen.png")
    rec["pre_screen"] = dict(nc=nc, upper=upper, clean=ok)
    rec["events"].append(f"preflight clean-hud={ok} ncolors={nc} upper={upper}")
    if not ok:
        sys.exit(f"screen not clean (nc={nc} upper={upper}) — dismiss the modal first")

    tech_addr = TECH_BITS + ENVECON_ID
    tech0 = P.rd(f, tech_addr, 1)[0]
    energy0 = rd_i32(f, ENERGY_G + me * ENERGY_STRIDE * 4)
    ta = tile_addr(f, ux, uy)
    tile0 = P.rd(f, ta, TILE_SZ)
    base0 = rd_u32(f, TILE_PTR_G)
    rec["pre"] = dict(tech_byte_59=tech0, energy=energy0, tile_array_ptr=hex(base0),
                      tile_addr=hex(ta), tile=tile0.hex(), tile_elev=tile0[0] >> 5,
                      tile_mask=hex(struct.unpack("<I", tile0[8:12])[0]),
                      sel=rd_i32(f, SEL_G), orders_mode=rd_u32(f, ORDERS_G),
                      pending=rd_u32(f, PENDING_G),
                      req_tech_raise=rd_i32(f, TECH_REQ_TBL + (0x10 * 8 + 0) * 4),
                      req_tech_raise_sea=rd_i32(f, TECH_REQ_TBL + (0x10 * 8 + 1) * 4))
    print("pre:", json.dumps(rec["pre"]))

    sel = rd_i32(f, SEL_G)
    if sel != unit:
        sys.exit(f"game selection is {sel}, not the Former {unit} — steer it first "
                 f"(poke order 0 + let the cycle pick, or click the unit)")
    if rd_u32(f, ORDERS_G) == 0:
        sys.exit("orders mode is 0 — order keys will not dispatch")

    # --- make the picker reachable: publish Environmental Economics (tech 59) ---
    if not a.no_poke and not (tech0 >> (me & 0x1F) & 1):
        P.wr(f, tech_addr, bytes([tech0 | (1 << (me & 0x1F))]))
        back = P.rd(f, tech_addr, 1)[0]
        rec["poke"] = dict(addr=hex(tech_addr), old=tech0, new=back,
                           expected=tech0 | (1 << (me & 0x1F)))
        rec["events"].append(f"poke tech bit 59 (EnvEcon) {tech0:#04x}->{back:#04x}")
        if back != tech0 | (1 << (me & 0x1F)):
            sys.exit(f"tech-bit poke did not stick ({back:#04x})")

    # --- arm gdb (after all pokes: pokes are dead under a tracer, M34) ---
    gsrc = open(os.path.join(ROOT, "scripts", "m35_pay.gdb")).read().replace("__UNIT__", str(unit))
    gpath = f"{EVID}/{tag}_chain.gdb"
    open(gpath, "w").write(gsrc)
    log = f"{EVID}/{tag}_gdb.log"
    gdb = subprocess.Popen(f"gdb -batch -nx -x {gpath} -p {pid} > {log} 2>&1", shell=True)
    time.sleep(6)
    armed = sum(1 for _ in open(log) if "Breakpoint" in _ and " at " in _)
    rec["gdb"] = dict(pid=gdb.pid, breakpoints_armed=armed)
    print(f"armed {armed} breakpoints (gdb {gdb.pid})")
    if armed < 20:
        sh(f"kill -TERM {gdb.pid}")
        time.sleep(1); sh(f"kill -CONT {pid}")
        sys.exit(f"arming failed ({armed}/25 breakpoints); see {log}")

    def cleanup(reason):
        sh(f"kill -TERM {gdb.pid} 2>/dev/null")
        time.sleep(1.5)
        sh(f"kill -CONT {pid} 2>/dev/null")
        time.sleep(1)
        rec["events"].append(f"cleanup: {reason}")
        finish(f, rec, log, tag)

    # --- press the terraform key; gdb holds the game between bps, so the X event is
    #     delivered on the next continue with the selection exactly as polled (M34) ---
    pressed = []
    for n in range(5):
        P.key(a.key)
        pressed.append(n)
        hits = wait_for(log, "TERRAF ", 6)
        if hits:
            rec["events"].append(f"TERRAF hit after press #{n+1}: {hits[0]}")
            break
        rec["events"].append(f"no TERRAF after press #{n+1}")
    rec["presses"] = len(pressed)
    if not wait_for(log, "TERRAF ", 1):
        cleanup("no TERRAF hit")
        return

    # --- service the TERRACOST message pane, then the TERRAPAY picker ---
    # M35 v1 PITFALL: the TERRACOST caption pane closes on its own (~1-2 s, like every
    # SMAC advisor pane). An Escape aimed at it lands on the TERRAPAY picker that has
    # already opened behind it and CANCELS the picker -> PAYDECLINED, no debit, no store.
    # So: give the caption pane 4 s to close by itself; only touch the keyboard if the
    # picker has still not opened by then.
    pane = []
    cost = wait_for(log, "TERRACOSTPANE ", 15)
    if cost:
        time.sleep(1.0)
        png = P.freeze(f"{tag}_terracost")
        shutil.copy(png, f"{EVID}/{tag}_terracost_pane.png")
        rec["screenshots"].append(f"{tag}_terracost_pane.png")
        w = P.ocr_fast(png)
        rec["terracost_words"] = [t for t, *_ in w[:30]]
        pane = wait_for(log, "PAYPANE ", 4)
        if not pane:
            okw = next(((cx, cy) for t, cx, cy, _w, _h in w
                        if t.lower().strip(".,!|_*— ") == "ok"), None)
            if okw:
                P.click((int(okw[0]), int(okw[1]))); time.sleep(1.4)
                rec["events"].append(f"clicked OK on TERRACOST pane at ({okw[0]:.0f},{okw[1]:.0f})")
            else:
                P.key("Escape"); time.sleep(1.2)
                rec["events"].append("Escape on TERRACOST pane (no OK row OCR'd)")
            pane = wait_for(log, "PAYPANE ", 15)
    else:
        rec["events"].append("no TERRACOST pane")
        pane = wait_for(log, "PAYPANE ", 20)
    rec["paypane_seen"] = bool(pane)
    if not pane:
        rec["events"].append("no PAYPANE (picker) — tech gate or a skip path fired")
        cleanup("no picker")
        return
    time.sleep(2.0)
    row = None
    for attempt in range(3):
        png = P.freeze(f"{tag}_paypane{attempt}")
        shutil.copy(png, f"{EVID}/{tag}_paypane{attempt}.png")
        rec["screenshots"].append(f"{tag}_paypane{attempt}.png")
        w = P.ocr_fast(png)
        rec[f"paypane_words{attempt}"] = [(t, int(cx), int(cy)) for t, cx, cy, _w, _h in w[:45]]
        row = next(((int(cx), int(cy), t) for t, cx, cy, _w, _h in w
                    if t.lower().strip(".,!|_*— ").startswith("expend")), None)
        if row:
            break
        rec["events"].append(f"paypane screenshot #{attempt}: no 'Expend' row OCR'd")
        time.sleep(1.2)
    if not row:
        rec["events"].append("picker up but no 'Expend' row OCR'd — leaving it up")
        cleanup("picker unanswerable")
        return
    P.click((row[0], row[1]))
    rec["events"].append(f"clicked {row[2]!r} row at ({row[0]},{row[1]})")
    time.sleep(1.4)
    png2 = P.freeze(f"{tag}_after_row")
    shutil.copy(png2, f"{EVID}/{tag}_after_row.png")
    rec["screenshots"].append(f"{tag}_after_row.png")
    w2 = P.ocr_fast(png2)
    rec["after_row_words"] = [(t, int(cx), int(cy)) for t, cx, cy, _w, _h in w2[:40]]
    still = any(t.lower().strip(".,!|_*— ").startswith(("expend", "cancel")) for t, *_ in w2)
    okw = next(((cx, cy) for t, cx, cy, _w, _h in w2 if t.lower().strip(".,!|_*— ") == "ok"), None)
    if still and okw:
        P.click((int(okw[0]), int(okw[1]))); time.sleep(1.4)
        rec["events"].append(f"clicked OK at ({int(okw[0])},{int(okw[1])}) to confirm the row")
    elif still:
        P.click((row[0], row[1] + 26)); time.sleep(1.4)
        rec["events"].append(f"clicked row+26 ({row[0]},{row[1]+26}) as the OK bar")

    verdict = wait_for(log, "PAYTAKEN ", 8) + wait_for(log, "PAYDECLINED ", 4)
    rec["events"].append(f"pay verdict: {verdict}")
    time.sleep(6)  # let the post-answer chain (debit/store/bcast/enq/drain/disp/exec) run
    cleanup("done")


def finish(f, rec, log, tag):
    """Post-state (gdb detached, TracerPid back to 0) + parsed log -> evidence JSON."""
    tracer = sh(f"grep TracerPid /proc/{rec['pid']}/status").stdout.strip()
    rec["post_tracer"] = tracer
    try:
        pid2, f2 = P.mem()
        me = rec["player"]
        u = rec["unit"]["idx"]
        d = P.rd(f2, UNIT_ARR + u * 52, 52)
        ta = tile_addr(f2, rec["unit"]["x"], rec["unit"]["y"])
        tile1 = P.rd(f2, ta, TILE_SZ)
        rec["post"] = dict(
            energy=rd_i32(f2, ENERGY_G + me * ENERGY_STRIDE * 4),
            tech_byte_59=P.rd(f2, TECH_BITS + ENVECON_ID, 1)[0],
            tile=tile1.hex(), tile_elev=tile1[0] >> 5,
            tile_mask=hex(struct.unpack("<I", tile1[8:12])[0]),
            order=P.rd(f2, UNIT_ARR + u * 52 + 17, 1)[0],
            mpused=d[40], sel=rd_i32(f2, SEL_G), year=rd_i32(f2, 0x985B00),
            cur_player=rd_i32(f2, 0x985DCC), pending=rd_i32(f2, PENDING_G))
        rec["tile_diff"] = [f"+{i:02x}:{a:02x}->{b:02x}" for i, (a, b)
                            in enumerate(zip(bytes.fromhex(rec["pre"]["tile"]), tile1)) if a != b]
    except Exception as e:  # noqa: BLE001
        rec["post_error"] = repr(e)
    rec["log"] = log_lines(log)
    rec["log_path"] = log
    out = f"{EVID}/{tag}_paypicker.json"
    with open(out, "w") as fh:
        json.dump(rec, fh, indent=1)
    print("\n== chain log ==")
    for ln in rec["log"][:80]:
        print("  ", ln)
    print("\n== post ==", json.dumps(rec.get("post"), indent=1))
    print("== tile diff ==", rec.get("tile_diff"))
    print("saved:", out)


if __name__ == "__main__":
    main()
