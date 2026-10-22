#!/usr/bin/env python3
"""M45: found our FIRST base — press 'b' (BUILD BASE) on the Colony Pod at (45,11).

Why this unit/tile: M43 proved base record +4 == owner player index and we own ZERO
bases; M44 proved with zero bases our income AND upkeep are both 0/turn (energy flat
at 15 for 12 rounds), so the economy milestone was blocked on having a base. The Pod
(idx 30, type 0, class 8) is the only colonist-carrying unit left — 0x4d1280 gates
`b` on the type-record CLASS byte == 8 (else NEEDCOLONISTS), and its tile (45,11) is
ours (tile record +2 nibble 3) with no neighbouring base.

Static path (scripts/fn.py 0x4d1280 / 0x4cca50, turn_driver §M45):
  'b' -> 0x4d1280(unit): class==8 gate -> tile gates (NOTINTRIAD domain/elevation
  table 0x92ae81, FUNGUSDANGUS mask 0x20, NOTONMONOLITH 0x2000, NOTONROCKY rec+5
  &0xc0, SIMULNO 0x5255e0) -> can-act 0x5acc00 (order byte +17 in 1..3 with +4 &
  0x4200 == 0 => UNITMOVED, so poke +17 = 0 first) -> BASETOONEAR = 8-neighbour scan
  for mask bit 0x1 (base present) with owner nibble < 8 -> border dispute via
  0x4e3b50 (TERRPACT / TERRTREATY / TERRTRUCE / THISLANDISMYLAND / BULLY panes) ->
  base-limit 0x4e9b40 (BUREAUCRACY) -> default name 0x4e3cf0 -> NEWBASE name pane
  0x462d30(s_NEWBASE, 0x17, namebuf, 0) -> 0x4cca50(unit, name): 0x4e47d0 allocates
  the slot, name -> base+19, 0x45abb40(unit) consumes the colonist, 0x450bea0 claims
  the border -> BASEFOUNDED Script pane ("$BASENAME0 founded in $NUM0", colfoun_sm.pcx).

Flow: preflight screen -> poke Pod +17=0 / rivals +40=255 / menu-pend 0 -> Tab-select
the Pod -> arm scripts/m45_base.gdb -> press 'b' -> service whatever panes open
(NEWBASE name entry, diplomacy dispute, BASEFOUNDED) -> kill gdb -> verify by memory:
n_bases +1, a base record owned by us at (45,11), tile mask bit 0 set, Pod consumed.

Usage: python3 scripts/m45_base.py [--tag m45a] [--x 45] [--y 11]
"""
import argparse
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P
import m44_idle as IDLE

EVID = P.EVID
UNIT_ARR, SEL_G, ORDERS_G, PEND_G = 0x933278, 0x91B5BC, 0x91B5B8, 0x91B5C4
TYPE_BASE, CLASS_OFF = 0x98AD88, 42          # name +0, ability +32, domain +36, class +42
TILE_PTR_G, NB_G, YEAR_G, CUR_G = 0x92AE14, 0x985AF4, 0x985B00, 0x985DCC
ENERGY_G, ENERGY_STRIDE = 0x94D650, 0x82F
BASE_ARR, BASE_STRIDE = 0x95DA10, 0x130      # +0 x, +2 y, +4 owner, +6 pop, +19 name, +64 minerals
EXPECT_BPS = 15


def base_list(f):
    n = struct.unpack("<I", P.rd(f, NB_G, 4))[0]
    blob = P.rd(f, BASE_ARR, n * BASE_STRIDE)
    out = []
    for i in range(n):
        r = blob[i * BASE_STRIDE:(i + 1) * BASE_STRIDE]
        x, y = struct.unpack("<HH", r[0:4])
        out.append(dict(idx=i, x=x, y=y, owner=r[4], pop=r[6],
                        name=r[0x13:0x2b].split(b"\0")[0].decode("latin1"),
                        minerals=struct.unpack("<I", r[64:68])[0]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m45a")
    ap.add_argument("--x", type=int, default=45)
    ap.add_argument("--y", type=int, default=11)
    a = ap.parse_args()
    tag, TX, TY = a.tag, a.x, a.y
    rec = {"tag": tag, "t": time.strftime("%F %T"), "target": [TX, TY],
           "events": [], "shots": [], "log_lines": []}

    def ev(s):
        rec["events"].append(s)
        print(s, flush=True)

    pid = int(subprocess.run(["pgrep", "-x", "terran.exe"],
                             capture_output=True, text=True).stdout.split()[0])
    tracer = subprocess.run(["grep", "TracerPid", f"/proc/{pid}/status"],
                            capture_output=True, text=True).stdout
    assert tracer.strip().split()[-1] == "0", f"tracer attached: {tracer}"
    rec["pid"] = pid
    _, f = P.mem()

    def u32(addr):
        return struct.unpack("<I", P.rd(f, addr, 4))[0]

    def i32(addr):
        return struct.unpack("<i", P.rd(f, addr, 4))[0]

    me = u32(0x91B5B4)

    def own_units():
        out = []
        blob = P.rd(f, UNIT_ARR, 300 * 52)
        for i in range(300):
            r = blob[i * 52:(i + 1) * 52]
            if len(r) < 52 or r[14] != me or struct.unpack("<H", r[0:2])[0] == 0xffff:
                continue
            x, y = struct.unpack("<HH", r[0:4])
            typ = struct.unpack("<H", r[10:12])[0]
            cls = P.rd(f, TYPE_BASE + typ * 52 + CLASS_OFF, 1)[0]
            out.append(dict(idx=i, x=x, y=y, type=typ, cls=cls, order=r[17],
                            work37=r[37], mpused=r[40],
                            name=P.rd(f, TYPE_BASE + typ * 52, 24).split(b"\0")[0].decode("latin1")))
        return out

    def tile():
        tb = u32(TILE_PTR_G)
        ta = tb + (40 * TY + (TX >> 1)) * 0x2c
        t = P.rd(f, ta, 0x2c)
        return dict(addr=hex(ta), elev=t[0] >> 5, owner=t[2] & 0xF,
                    mask=struct.unpack("<I", t[8:12])[0], byte5=t[5])

    def pod():
        for u in own_units():
            if u["x"] == TX and u["y"] == TY and u["cls"] == 8:
                return u
        return None

    def econ():
        bs = base_list(f)
        mine = [b for b in bs if b["owner"] == me]
        return dict(n_bases=len(bs), our_bases=mine,
                    our_minerals=sum(b["minerals"] for b in mine),
                    energy=i32(ENERGY_G + me * ENERGY_STRIDE * 4))

    p0 = pod()
    assert p0, f"no class-8 colonist unit at ({TX},{TY})"
    fidx = p0["idx"]
    rec["pre"] = dict(year=u32(YEAR_G), cur=u32(CUR_G), me=me,
                      sel=struct.unpack("<i", P.rd(f, SEL_G, 4))[0],
                      orders_mode=u32(ORDERS_G), menu_pend=u32(PEND_G),
                      pod=p0, tile=tile(), econ=econ(), units=own_units())
    ev(f"pre: year={rec['pre']['year']} cur={rec['pre']['cur']} me={me} "
       f"sel={rec['pre']['sel']} orders={rec['pre']['orders_mode']} pend={rec['pre']['menu_pend']} "
       f"pod=#{fidx} order={p0['order']} n_bases={rec['pre']['econ']['n_bases']} "
       f"energy={rec['pre']['econ']['energy']} tile={rec['pre']['tile']}")

    # --- preflight screen: service any pane until the HUD/our-turn state is clean ---
    P.focus()
    t0 = time.time()
    while time.time() - t0 < 90:
        png = P.freeze(f"{tag}_pre"); shutil.copy(png, f"{EVID}/{tag}_pre.png")
        rec["shots"].append(f"{tag}_pre.png")
        words = P.ocr(png)
        body = re.sub(r"[^a-z]", "", " ".join(w for w, *_ in words).lower())
        kind = P.classify(words, png=png)
        bar = IDLE.find_ok_bar(png)
        pane_end = "enterfornextturn" in body or "nounitsneedneworders" in body
        # memory is authoritative on whose turn it is (classify() garbles when the
        # side panels are busy — m38run/m39 lesson); a bare HUD needs NO servicing,
        # and service_pane's "unknown -> Return" default would spam Return into it.
        if u32(CUR_G) == me and not pane_end and not bar and kind not in ("confirm", "dialog"):
            rec["events"].append(f"preflight: clean enough (kind={kind}, our turn, no bar)")
            break
        acted = IDLE.service_pane(png, words, body, kind, rec, "preflight", bar=bar)
        if not acted:
            break
        time.sleep(1.2)
    png = P.freeze(f"{tag}_pre"); shutil.copy(png, f"{EVID}/{tag}_pre.png")
    words = P.ocr(png)
    kind = P.classify(words, png=png)
    ev(f"preflight settled: kind={kind} cur={u32(CUR_G)} sel="
       f"{struct.unpack('<i', P.rd(f, SEL_G, 4))[0]} orders={u32(ORDERS_G)} pend={u32(PEND_G)}")
    assert u32(CUR_G) == me, f"not our turn (cur={u32(CUR_G)} me={me})"

    # --- make the Pod the only cycle candidate and actionable ---
    P.wr(f, UNIT_ARR + fidx * 52 + 17, bytes([0]))          # +17 order -> 0 (was 2 Hold)
    ev(f"poked pod #{fidx} +17 order 2->0 (can-act 0x5acc00 refuses order 1..3)")
    for u in own_units():
        if u["idx"] != fidx:
            P.wr(f, UNIT_ARR + u["idx"] * 52 + 40, bytes([255]))   # +40 mpused -> 255
            ev(f"poked rival-candidate unit #{u['idx']} (+40 mpused -> 255)")
    P.wr(f, UNIT_ARR + fidx * 52 + 40, bytes([0]))
    if u32(PEND_G) != 0:
        P.wr(f, PEND_G, struct.pack("<I", 0))
        ev("poked order-menu-pending 0x91b5c4 -> 0")
    for addr, want, nm in ((UNIT_ARR + fidx * 52 + 17, 0, "pod +17"),
                           (UNIT_ARR + fidx * 52 + 40, 0, "pod +40"),
                           (PEND_G, 0, "menu-pend")):
        got = int.from_bytes(P.rd(f, addr, 4 if addr == PEND_G else 1), "little")
        assert got == want, f"poke readback {nm}={got} != {want}"

    # --- select the Pod with Tab (the only actionable unit) ---
    sel = struct.unpack("<i", P.rd(f, SEL_G, 4))[0]
    for n in range(8):
        if sel == fidx:
            break
        pngc = P.freeze(f"{tag}_cyc{n}")
        bc = re.sub(r"[^a-z]", "", " ".join(t for t, *_ in P.ocr_fast(pngc)).lower())
        if "enterfornextturn" in bc or "nounitsneedneworders" in bc:
            P.key("Return"); ev(f"cycle iter {n}: ENDOFTURN1 -> Return"); time.sleep(2.5)
        elif "oops" in bc:
            IDLE.dismiss_reallyquit(P.ocr(pngc)); time.sleep(1.2)
        else:
            P.key("Tab"); time.sleep(1.3)
        sel = struct.unpack("<i", P.rd(f, SEL_G, 4))[0]
    om = u32(ORDERS_G)
    rec["sel_final"] = dict(sel=sel, pod=fidx, orders_mode=om, menu_pend=u32(PEND_G))
    ev(f"selection: sel={sel} pod={fidx} orders_mode={om} pend={u32(PEND_G)}")
    assert sel == fidx, f"could not select the pod (sel={sel})"
    assert om != 0, "orders mode 0 — order keys will not dispatch (M39 lesson)"
    if u32(PEND_G) != 0:
        P.wr(f, PEND_G, struct.pack("<I", 0))
        ev("re-poked menu-pend -> 0 after selection")

    # --- arm gdb AFTER all pokes ---
    gsrc = open(os.path.join(P.ROOT, "scripts", "m45_base.gdb")).read().replace("__UNIT__", str(fidx))
    gpath = f"{EVID}/{tag}_chain.gdb"
    open(gpath, "w").write(gsrc)
    log = f"{EVID}/{tag}_gdb.log"

    def logtxt():
        try:
            return open(log, errors="replace").read()
        except FileNotFoundError:
            return ""

    gdb = subprocess.Popen(f"gdb -batch -nx -x {gpath} -p {pid} > {log} 2>&1", shell=True)
    time.sleep(4)
    armed = sum(1 for _ in open(log, errors="replace") if "Breakpoint" in _ and " at " in _)
    rec["gdb"] = dict(pid=gdb.pid, armed=armed, expect=EXPECT_BPS)
    ev(f"armed {armed}/{EXPECT_BPS} breakpoints (gdb {gdb.pid})")
    if armed < EXPECT_BPS:
        subprocess.run(f"kill -TERM {gdb.pid}", shell=True)
        subprocess.run(f"kill -CONT {pid}", shell=True)
        sys.exit(f"arming failed; see {log}")

    def cleanup(reason):
        ev(f"cleanup: {reason}")
        subprocess.run(f"kill -TERM {gdb.pid} 2>/dev/null", shell=True)
        time.sleep(0.8)
        subprocess.run(f"kill -CONT {pid} 2>/dev/null", shell=True)
        time.sleep(1.5)

    # --- press 'b' and service the panes it opens ---
    P.key("b")
    ev("pressed 'b' (BUILD BASE) on the selected pod")
    created = None
    quiet = 0
    t0 = time.time()
    while time.time() - t0 < 180:
        txt = logtxt()
        hits = [l for l in txt.splitlines() if l.startswith("M45 CREATERET")]
        if hits:
            created = hits[0]
            break
        adv = [l for l in txt.splitlines() if l.startswith("M45 ADV")]
        if adv and "PANE" not in txt:
            # an advisory fired and nothing else is pending: the setter refused
            time.sleep(1.0)
            if [l for l in logtxt().splitlines() if l.startswith("M45 ADV")] == adv:
                cleanup(f"setter refused; advisories: {[l.split('id=')[-1] for l in adv]}")
                rec["outcome"] = "refused"
                break
            continue
        png = P.freeze(f"{tag}_svc"); shutil.copy(png, f"{EVID}/{tag}_svc.png")
        rec["shots"].append(f"{tag}_svc.png")
        words = P.ocr(png)
        body = re.sub(r"[^a-z]", "", " ".join(w for w, *_ in words).lower())
        kind = P.classify(words, png=png)
        bar = IDLE.find_ok_bar(png)
        pane_end = "enterfornextturn" in body or "nounitsneedneworders" in body
        name_pane = ("enteranameforyour" in body or "foryourn" in body
                     or ("newbase" in body and "name" in body))
        is_pane = bool(bar) or pane_end or name_pane or "oops" in body \
            or kind in ("confirm", "dialog", "base")
        if not is_pane:
            quiet += 1
            txt2 = logtxt()
            busy = any(l.startswith(("M45 SETTER", "M45 ADV", "M45 PANE", "M45 CREATE"))
                       for l in txt2.splitlines())
            if quiet >= 4 and not busy:
                cleanup("no pane, no trace line — key never reached the setter")
                rec["outcome"] = "no-op"
                break
            time.sleep(1.0)
            continue
        # NEWBASE name-entry pane: accept the generated default name. FIRSTBASE has
        # the same Script geometry (#x 10 #y 40 #xs 320 + 'Name:') and its OK was
        # measured live at (400,171) (skill wine-runnability.md line 30).
        if name_pane:
            P.key("Return"); time.sleep(1.6)
            png2 = P.freeze(f"{tag}_name"); shutil.copy(png2, f"{EVID}/{tag}_name.png")
            rec["shots"].append(f"{tag}_name.png")
            b2 = re.sub(r"[^a-z]", "", " ".join(t for t, *_ in P.ocr_fast(png2)).lower())
            still = "enteranameforyour" in b2 or "foryourn" in b2
            rec["events"].append(f"name pane: Return (still_open={still} body={b2[:90]!r})")
            if still:
                okrow = next((w for w in P.ocr(png2)
                              if w[0].lower().strip(".,!|_* ") in ("ok", "0k")), None)
                spot = (int(okrow[1]), int(okrow[2])) if okrow else (400, 171)
                P.click(spot); time.sleep(1.6)
                rec["events"].append(f"name pane: clicked OK at {spot}")
            continue
        if IDLE.service_pane(png, words, body, kind, rec, "post-b", bar=bar):
            time.sleep(1.2)
            continue
        time.sleep(1.0)
    else:
        cleanup("timeout waiting for CREATERET")
        rec["outcome"] = "timeout"

    if created is not None:
        # creation happened: dismiss the BASEFOUNDED / follow-up panes, but do NOT
        # advance the turn here (the M45b idle re-measure owns ENDOFTURN1).
        t1 = time.time()
        while time.time() - t1 < 45:
            png = P.freeze(f"{tag}_post"); shutil.copy(png, f"{EVID}/{tag}_post.png")
            words = P.ocr(png)
            body = re.sub(r"[^a-z]", "", " ".join(w for w, *_ in words).lower())
            if "enterfornextturn" in body or "nounitsneedneworders" in body:
                rec["events"].append("post-create: ENDOFTURN1 up — left for the idle run")
                break
            kind = P.classify(words, png=png)
            if kind == "hud" and not IDLE.find_ok_bar(png):
                rec["events"].append("post-create: back to bare HUD")
                break
            if kind == "base":
                # BUILD BASE leaves the new base's BASE screen open (RENAMEd/OK row at
                # y ~365, outside find_ok_bar's band). One Escape closes it (M26).
                P.key("Escape"); time.sleep(1.5)
                rec["events"].append("post-create: Escape on base screen")
                continue
            if IDLE.service_pane(png, words, body, kind, rec, "post-create",
                                 bar=IDLE.find_ok_bar(png)):
                time.sleep(1.2)
                continue
            time.sleep(1.0)
        cleanup("base created")
        rec["outcome"] = "created"

    # --- read the trace + the post-state ---
    txt = logtxt()
    rec["log_lines"] = [l for l in txt.splitlines() if l.startswith("M45 ")]
    rec["gdb_log"] = f"{tag}_gdb.log"
    time.sleep(2)
    _, f2 = P.mem()

    def u32b(addr):
        return struct.unpack("<I", P.rd(f2, addr, 4))[0]

    tb = u32b(TILE_PTR_G)
    ta = tb + (40 * TY + (TX >> 1)) * 0x2c
    t = P.rd(f2, ta, 0x2c)
    n = u32b(NB_G)
    blob = P.rd(f2, BASE_ARR, n * BASE_STRIDE)
    ours = []
    for i in range(n):
        r = blob[i * BASE_STRIDE:(i + 1) * BASE_STRIDE]
        if r[4] == me:
            x, y = struct.unpack("<HH", r[0:4])
            ours.append(dict(idx=i, x=x, y=y, pop=r[6],
                             name=r[0x13:0x2b].split(b"\0")[0].decode("latin1"),
                             minerals=struct.unpack("<I", r[64:68])[0]))
    units = []
    ublob = P.rd(f2, UNIT_ARR, 300 * 52)
    for i in range(300):
        r = ublob[i * 52:(i + 1) * 52]
        if len(r) == 52 and r[14] == me and struct.unpack("<H", r[0:2])[0] != 0xffff:
            typ = struct.unpack("<H", r[10:12])[0]
            units.append(dict(idx=i, x=struct.unpack("<H", r[0:2])[0],
                              y=struct.unpack("<H", r[2:4])[0], type=typ,
                              cls=P.rd(f2, TYPE_BASE + typ * 52 + CLASS_OFF, 1)[0],
                              order=r[17], mpused=r[40]))
    rec["post"] = dict(year=u32b(YEAR_G), cur=u32b(CUR_G), n_bases=n,
                       our_bases=ours,
                       tile=dict(elev=t[0] >> 5, owner=t[2] & 0xF,
                                 mask=struct.unpack("<I", t[8:12])[0],
                                 mask_bit0_base=bool(struct.unpack("<I", t[8:12])[0] & 1)),
                       units=units,
                       energy=struct.unpack("<i", P.rd(f2, ENERGY_G + me * ENERGY_STRIDE * 4, 4))[0])
    ev(f"post: year={rec['post']['year']} n_bases={n} our_bases={ours}")
    ev(f"post tile ({TX},{TY}): {rec['post']['tile']}")
    ev(f"post units: {units}")
    ev(f"trace: {len(rec['log_lines'])} M45 lines")
    for l in rec["log_lines"]:
        print("   ", l, flush=True)

    rec["delta"] = dict(n_bases=n - rec["pre"]["econ"]["n_bases"],
                        energy=rec["post"]["energy"] - rec["pre"]["econ"]["energy"],
                        units_before=len(rec["pre"]["units"]), units_after=len(units))
    json.dump(rec, open(f"{EVID}/{tag}_base.json", "w"), indent=1)
    print(f"saved: {EVID}/{tag}_base.json  outcome={rec.get('outcome')}", flush=True)


if __name__ == "__main__":
    main()
