#!/usr/bin/env python3
"""M38: issue a SECOND Raise Land at (45,7) — the tile is now elev 5 (M37 completed
the first raise). New ground: bigger footprint (ladder[5+1]=49 tiles = 7x7),
dynamic cost at elev 5, and the FIRST live test of the footprint's foreign-tile /
pact-refuse / treaty-confirm branch (M36 decoded it statically; never fired).

Flow: ENDOFTURN1 Return -> force game selection onto the (45,7) Former (poke
others' mpused=255 if the cycle picks someone else; Escape deselects; the pump
re-selects the only actionable unit) -> arm scripts/m38_issue.gdb (34 bps) ->
press ']' -> service TERRACOST caption + TERRAPAY picker (+ any diplomacy confirm:
answer YES) -> watch STORE+BCAST (issued) or PACTCHK/REFUND/EPILOGUE (refused).

Usage: python3 scripts/m38_issue.py [--tag m38a] [--key bracketright]
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

EVID = P.EVID
TX, TY = 45, 7
UNIT_ARR, SEL_G, ORDERS_G = 0x933278, 0x91B5BC, 0x91B5B8
CLASS_TBL = 0x98ADB2
TILE_PTR_G = 0x92AE14
ENERGY_G, ENERGY_STRIDE = 0x94D650, 0x82F
EXPECT_BPS = 34


def dismiss_reallyquit(words):
    """REALLYQUIT: click the 'oops' row then OK 47 px below (M37 geometry)."""
    row = None
    for t, cx, cy, *_ in words:
        low = t.lower().strip(".,:;|_*")
        if low.startswith("oops") and 150 <= cx <= 660:
            row = (int(cx), int(cy)); break
    if row is None:
        return False
    P.click(row); time.sleep(1.4)
    P.click((row[0], row[1] + 47)); time.sleep(1.4)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m38a")
    ap.add_argument("--key", default="bracketright")
    a = ap.parse_args()
    tag = a.tag
    rec = {"tag": tag, "t": time.strftime("%F %T"), "events": [], "shots": []}

    pid = int(subprocess.run(["pgrep", "-x", "terran.exe"],
                             capture_output=True, text=True).stdout.split()[0])
    tracer = subprocess.run(["grep", "TracerPid", f"/proc/{pid}/status"],
                            capture_output=True, text=True).stdout
    assert tracer.strip().split()[-1] == "0", f"tracer attached: {tracer}"
    rec["pid"] = pid
    _, f = P.mem()

    def u32(addr):
        return struct.unpack("<I", P.rd(f, addr, 4))[0]

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
            cls = P.rd(f, CLASS_TBL + typ * 52, 1)[0]
            out.append(dict(idx=i, x=x, y=y, cls=cls, order=r[17],
                            work37=r[37], mpused=r[40]))
        return out

    def target():
        for u in own_units():
            if u["x"] == TX and u["y"] == TY and u["order"] == 0 and u["cls"] == 9:
                return u
        return None

    def tile():
        tb = u32(TILE_PTR_G)
        ta = tb + (40 * TY + (TX >> 1)) * 0x2c
        t = P.rd(f, ta, 0x2c)
        return dict(addr=hex(ta), elev=t[0] >> 5,
                    mask=struct.unpack("<I", t[8:12])[0])

    tgt = target()
    assert tgt, "no order-0 Former(cls 9) at (45,7)"
    year0 = u32(0x985B00)
    energy0 = struct.unpack("<i", P.rd(f, ENERGY_G + me * ENERGY_STRIDE * 4, 4))[0]
    rec["pre"] = dict(year=year0, cur=u32(0x985DCC), sel=u32(SEL_G) if u32(SEL_G) < 0x80000000
                      else struct.unpack("<i", P.rd(f, SEL_G, 4))[0],
                      orders_mode=u32(ORDERS_G), energy=energy0, target=tgt,
                      tile=tile(), units=own_units())
    print("pre:", json.dumps({k: rec["pre"][k] for k in
                              ("year", "cur", "sel", "orders_mode", "energy", "target", "tile")}),
          flush=True)

    # --- preflight screen: ENDOFTURN1 (expected) / REALLYQUIT / bare HUD ---
    png = P.freeze(f"{tag}_pre"); shutil.copy(png, f"{EVID}/{tag}_pre.png")
    rec["shots"].append(f"{tag}_pre.png")
    words = P.ocr(png)
    body = re.sub(r"[^a-z]", "", " ".join(w for w, *_ in words).lower())
    if "oops" in body or "reallywanttoquit" in body:
        dismiss_reallyquit(words); rec["events"].append("dismissed REALLYQUIT at preflight")
        png = P.freeze(f"{tag}_pre"); shutil.copy(png, f"{EVID}/{tag}_pre.png")
        words = P.ocr(png)
        body = re.sub(r"[^a-z]", "", " ".join(w for w, *_ in words).lower())
    pane_end = "enterfornextturn" in body or "nounitsneedneworders" in body
    kind = P.classify(words, png=png)
    btn = P.ocr_crop(png, (615, 396, 180, 34), f"{tag}_btn", scale=6)
    btxt = re.sub(r"[^a-z]", "", " ".join(w[0] for w in btn).lower())
    hud_ok = kind == "hud" or "mplete" in btxt or "omple" in btxt
    rec["events"].append(f"preflight kind={kind} pane_end={pane_end} btn={btxt!r}")
    assert pane_end or hud_ok, f"unexpected screen {kind}: {body[:120]!r}"

    P.focus()
    if pane_end:
        P.key("Return")
        rec["events"].append("Return on ENDOFTURN1")

    # --- wait for our new turn with a unit auto-selected ---
    sel = -1
    t0 = time.time()
    while time.time() - t0 < 40:
        y, cur = u32(0x985B00), u32(0x985DCC)
        sel = struct.unpack("<i", P.rd(f, SEL_G, 4))[0]
        if y > year0 and cur == me and 0 <= sel < 300:
            break
        png = P.freeze(f"{tag}_cyc"); words = P.ocr(png)
        body = re.sub(r"[^a-z]", "", " ".join(w for w, *_ in words).lower())
        k2 = P.classify(words, png=png)
        if "oops" in body or "reallywanttoquit" in body:
            dismiss_reallyquit(words)
        elif "enterfornextturn" in body or "nounitsneedneworders" in body:
            P.key("Return")
        elif k2 == "confirm":
            P.answer_confirm(words)
        elif k2 == "dialog":
            P.key("Return")
        time.sleep(1)
    rec["events"].append(f"post-Return: year={u32(0x985B00)} cur={u32(0x985DCC)} sel={sel}")

    # --- force selection onto the (45,7) Former if the cycle picked someone else ---
    tgt = target()
    assert tgt, "target Former vanished"
    fidx = tgt["idx"]
    if sel != fidx:
        rec["events"].append(f"sel={sel} != former {fidx}: disabling other units (poke +40=255)")
        for u in own_units():
            if u["idx"] != fidx and u["order"] == 0:
                P.wr(f, UNIT_ARR + u["idx"] * 52 + 40, bytes([255]))
        back = [u for u in own_units() if u["idx"] != fidx and u["mpused"] != 255]
        rec["events"].append(f"poke readback mismatches: {back}")
        P.key("Escape")   # deselect the wrongly-selected unit (unit panel up: safe)
        time.sleep(1.5)
        for _ in range(15):
            sel = struct.unpack("<i", P.rd(f, SEL_G, 4))[0]
            if sel == fidx:
                break
            time.sleep(1)
    tgt = target() or tgt
    fidx = tgt["idx"]
    sel = struct.unpack("<i", P.rd(f, SEL_G, 4))[0]
    om = u32(ORDERS_G)
    rec["sel_final"] = dict(sel=sel, former=fidx, orders_mode=om)
    rec["events"].append(f"sel={sel} former={fidx} orders_mode={om}")
    assert sel == fidx, f"could not steer selection onto former {fidx} (sel={sel})"
    assert om != 0, "orders mode 0 — order keys will not dispatch"
    # ensure the Former itself can act
    mu = P.rd(f, UNIT_ARR + fidx * 52 + 40, 1)[0]
    if mu != 0:
        P.wr(f, UNIT_ARR + fidx * 52 + 40, bytes([0]))
        rec["events"].append(f"poked former mpused {mu}->0")

    # --- arm gdb AFTER all pokes ---
    gsrc = open(os.path.join(P.ROOT, "scripts", "m38_issue.gdb")).read() \
        .replace("__UNIT__", str(fidx))
    gpath = f"{EVID}/{tag}_chain.gdb"
    open(gpath, "w").write(gsrc)
    log = f"{EVID}/{tag}_gdb.log"

    def logtxt():
        try:
            return open(log, errors="replace").read()
        except FileNotFoundError:
            return ""

    def wait_for(prefix, secs):
        t0 = time.time()
        while time.time() - t0 < secs:
            hits = [l for l in logtxt().splitlines() if l.startswith(prefix)]
            if hits:
                return hits
            time.sleep(0.3)
        return []

    gdb = subprocess.Popen(f"gdb -batch -nx -x {gpath} -p {pid} > {log} 2>&1", shell=True)
    time.sleep(4)
    armed = sum(1 for _ in open(log, errors="replace") if "Breakpoint" in _ and " at " in _)
    rec["gdb"] = dict(pid=gdb.pid, armed=armed, expect=EXPECT_BPS)
    print(f"armed {armed}/{EXPECT_BPS} breakpoints (gdb {gdb.pid})", flush=True)
    if armed < EXPECT_BPS:
        subprocess.run(f"kill -TERM {gdb.pid}", shell=True)
        subprocess.run(f"kill -CONT {pid}", shell=True)
        sys.exit(f"arming failed; see {log}")

    def cleanup(reason):
        rec["events"].append(f"cleanup: {reason}")
        subprocess.run(f"kill -TERM {gdb.pid} 2>/dev/null", shell=True)
        time.sleep(0.8)
        subprocess.run(f"kill -CONT {pid} 2>/dev/null", shell=True)
        time.sleep(1.5)
        # post-state: order / energy / work37 (same-turn exec may land within ~10 s)
        post = {}
        for _ in range(20):
            _, f2 = P.mem()
            d = P.rd(f2, UNIT_ARR + fidx * 52, 52)
            en = struct.unpack("<i", P.rd(f2, ENERGY_G + me * ENERGY_STRIDE * 4, 4))[0]
            post = dict(order=d[17], work37=d[37], mpused=d[40], energy=en,
                        year=struct.unpack("<I", P.rd(f2, 0x985B00, 4))[0])
            if post["order"] == 0x14 and post["work37"] >= 2:
                break
            time.sleep(0.8)
        _, f2 = P.mem()
        tb = struct.unpack("<I", P.rd(f2, TILE_PTR_G, 4))[0]
        ta = tb + (40 * TY + (TX >> 1)) * 0x2c
        t = P.rd(f2, ta, 0x2c)
        post["tile_elev"] = t[0] >> 5
        post["tile_mask"] = hex(struct.unpack("<I", t[8:12])[0])
        rec["post"] = post
        png = P.freeze(f"{tag}_post"); shutil.copy(png, f"{EVID}/{tag}_post.png")
        rec["shots"].append(f"{tag}_post.png")
        rec["log"] = logtxt().splitlines()
        json.dump(rec, open(f"{EVID}/{tag}_issue.json", "w"), indent=1)
        print("== post ==", json.dumps(post))
        print("== key log ==")
        for l in rec["log"]:
            if re.match(r"^(TERRAF|TECHCHK|TECHFAIL|PAYPATH|ORDERCHK|COST|TERRACOSTPANE|"
                        r"PAYPANE|PAYDECIDE|PAYTAKEN|PAYDECLINED|DEBIT|SKIPPAY|PACTCHK|"
                        r"REFUND1|REFUND2|DIPLO|PANERET|AFTERLATCH|LOCKCHK|LOCKRET|"
                        r"STORE|BCAST|EPILOGUE|ENQ|PANE|ADVISOR)", l):
                print("  ", l)
        print("saved:", f"{EVID}/{tag}_issue.json")
        sys.exit(0)

    # --- press ']' until TERRAF fires ---
    P.focus()
    for n in range(5):
        P.key(a.key)
        if wait_for("TERRAF ", 6):
            rec["events"].append(f"TERRAF hit after press #{n+1}")
            break
        rec["events"].append(f"no TERRAF after press #{n+1}")
    if not wait_for("TERRAF ", 2):
        cleanup("no TERRAF hit")

    # --- TERRACOST caption -> TERRAPAY picker (m35 sequence) ---
    if wait_for("TERRACOSTPANE ", 15):
        time.sleep(1.0)
        png = P.freeze(f"{tag}_terracost"); shutil.copy(png, f"{EVID}/{tag}_terracost_pane.png")
        rec["shots"].append(f"{tag}_terracost_pane.png")
        rec["terracost_words"] = [t for t, *_ in P.ocr_fast(png)[:30]]
        if not wait_for("PAYPANE ", 4):
            w = P.ocr_fast(png)
            okw = next(((cx, cy) for t, cx, cy, *_ in w
                        if t.lower().strip(".,!|_*— ") == "ok"), None)
            if okw:
                P.click((int(okw[0]), int(okw[1]))); time.sleep(1.4)
                rec["events"].append(f"clicked OK on TERRACOST caption ({okw[0]:.0f},{okw[1]:.0f})")
            wait_for("PAYPANE ", 15)
    if not wait_for("PAYPANE ", 20):
        hits = [l for l in logtxt().splitlines()
                if l.startswith(("TECHFAIL", "SKIPPAY", "PACTCHK", "EPILOGUE", "COST"))]
        cleanup(f"no PAYPANE; early log: {hits}")

    row = None
    for attempt in range(3):
        time.sleep(2.0)
        png = P.freeze(f"{tag}_paypane{attempt}")
        shutil.copy(png, f"{EVID}/{tag}_paypane{attempt}.png")
        rec["shots"].append(f"{tag}_paypane{attempt}.png")
        w = P.ocr_fast(png)
        rec[f"paypane_words{attempt}"] = [(t, int(cx), int(cy)) for t, cx, cy, *_ in w[:45]]
        row = next(((int(cx), int(cy), t) for t, cx, cy, *_ in w
                    if t.lower().strip(".,!|_*— ").startswith("expend")), None)
        if row:
            break
        rec["events"].append(f"paypane shot {attempt}: no Expend row")
    if not row:
        cleanup("picker up but no Expend row (cost>energy?) — "
                f"{[l for l in logtxt().splitlines() if l.startswith('COST')]}")
    P.click((row[0], row[1]))
    rec["events"].append(f"clicked {row[2]!r} row at ({row[0]},{row[1]})")
    time.sleep(1.4)
    png2 = P.freeze(f"{tag}_after_row"); shutil.copy(png2, f"{EVID}/{tag}_after_row.png")
    rec["shots"].append(f"{tag}_after_row.png")
    w2 = P.ocr_fast(png2)
    still = any(t.lower().strip(".,!|_*— ").startswith(("expend", "cancel")) for t, *_ in w2)
    okw = next(((cx, cy) for t, cx, cy, *_ in w2 if t.lower().strip(".,!|_*— ") == "ok"), None)
    if still and okw:
        P.click((int(okw[0]), int(okw[1]))); time.sleep(1.4)
        rec["events"].append(f"clicked OK ({int(okw[0])},{int(okw[1])}) to confirm the row")
    elif still:
        P.click((row[0], row[1] + 26)); time.sleep(1.4)
        rec["events"].append(f"clicked row+26 as OK bar")

    verdict = wait_for("PAYTAKEN ", 8) + wait_for("PAYDECLINED ", 4)
    rec["events"].append(f"pay verdict: {verdict}")
    if any(l.startswith("PAYDECLINED") for l in verdict):
        cleanup("pay declined")

    # --- post-answer service loop: diplomacy confirm / refusal / STORE ---
    t0 = time.time()
    while time.time() - t0 < 75:
        txt = logtxt()
        if "STORE " in txt:
            time.sleep(3)
            cleanup("STORE fired — order issued")
        if re.search(r"^(EPILOGUE|REFUND1|REFUND2|PACTCHK)", txt, re.M):
            time.sleep(2)
            cleanup("refusal path fired (PACTCHK/REFUND/EPILOGUE)")
        png = P.freeze(f"{tag}_svc")
        words = P.ocr(png)
        body = re.sub(r"[^a-z]", "", " ".join(w for w, *_ in words).lower())
        kind = P.classify(words, png=png)
        if "oops" in body or "reallywanttoquit" in body:
            dismiss_reallyquit(words)
        elif kind == "confirm":
            png3 = P.freeze(f"{tag}_diplo"); shutil.copy(png3, f"{EVID}/{tag}_diplo.png")
            rec["shots"].append(f"{tag}_diplo.png")
            rec["events"].append(f"confirm pane: {[t for t,*_ in words][:25]}")
            P.answer_confirm(words)          # answer YES — proceed with the order
            rec["events"].append("answered YES on diplomacy confirm")
        elif kind == "dialog":
            P.key("Return")
        elif "enterfornextturn" in body or "nounitsneedneworders" in body:
            P.key("Return")
            rec["events"].append("ENDOFTURN1 during svc — Return (key may not have landed)")
        elif kind == "unknown" and P.region_colors(png, (180, 60, 620, 200)) < 130:
            P.key("Escape")
        time.sleep(1)
    cleanup("timeout waiting STORE/refusal")


if __name__ == "__main__":
    main()
