#!/usr/bin/env python3
"""M37: watch the terraform EXECUTION lifecycle for the stored 0x14 order.

Arms scratch/m37_exec41.gdb (REFRESH/ORDEREXEC/TERRAFEXEC/CHECK/NOTYET/COMPLETE/
RAISE/SETELEV/MASKSET), ends our turn, and follows rounds until the completion
path fires (accumulated work >= threshold) or N rounds pass. Snapshots the unit's
+37 work accumulator and the target tile elevation at every round boundary.

Usage: python3 scripts/m37_exec41.py [--tag m37a] [--rounds 3] [--budget 300]
"""
import argparse, json, os, re, shutil, struct, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P

EVID = P.EVID
TX, TY = 45, 7


def dismiss_reallyquit(words):
    """REALLYQUIT pane (Escape-on-bare-HUD aftermath, M36): click the 'Oops, no,
    wait!' row then the OK bar 47 px below (verified geometry: row y~261, OK ~308).
    answer_confirm MUST NOT touch this pane — its find_yes_row scans y 160..220
    and defaults to 196, which is pane artwork (m37b left the pane open that way).
    """
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
    ap.add_argument("--tag", default="m37a")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--budget", type=float, default=300.0)
    ap.add_argument("--order", type=lambda s: int(s, 0), default=0x14,
                    help="stored order byte to assert in pre-state (e.g. 0x9 road)")
    a = ap.parse_args()
    tag = a.tag
    rec = {"tag": tag, "t": time.strftime("%F %T")}

    pid = int(subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True,
                             text=True).stdout.split()[0])
    tracer = subprocess.run(["grep", "TracerPid", f"/proc/{pid}/status"],
                            capture_output=True, text=True).stdout
    assert tracer.strip().split()[-1] == "0", f"tracer attached: {tracer}"
    rec["pid"] = pid

    f = open(f"/proc/{pid}/mem", "rb", 0)

    def rd(addr, n):
        f.seek(addr); return f.read(n)

    def u32(addr):
        return struct.unpack("<I", rd(addr, 4))[0]

    def find_terraforming():
        """our units with a terraform-range order (4..0x17) — index-slide-proof"""
        out = []
        for i in range(300):
            r = rd(0x933278 + i * 52, 52)
            if len(r) < 52 or r[14] != u32(0x91B5B4):
                continue
            x, y = struct.unpack("<HH", r[0:4])
            if x == 0xffff or not (4 <= r[17] <= 0x17):
                continue
            out.append(dict(idx=i, x=x, y=y, order=r[17], work37=r[37],
                            mpused=r[40]))
        return out

    def tile():
        tb = u32(0x92AE14)
        ta = tb + (40 * TY + (TX >> 1)) * 0x2c
        t = rd(ta, 0x2c)
        return dict(addr=hex(ta), elev=t[0] >> 5,
                    mask=struct.unpack("<I", t[8:12])[0])

    def snapshot(label):
        out = dict(year=u32(0x985B00), cur=u32(0x985DCC),
                   units=find_terraforming(), tile=tile())
        rec[label] = out
        print(f"[{label}] year={out['year']} cur={out['cur']} "
              f"units={out['units']} tile={out['tile']}", flush=True)
        return out

    pre = snapshot("pre")
    assert any(u["order"] == a.order for u in pre["units"]), f"no {hex(a.order)} order present"

    # --- preflight screen: ENDOFTURN1 pane or bare HUD (TURN COMPLETE strip OCR) ---
    png = P.freeze(f"{tag}_pre")
    shutil.copy(png, f"{EVID}/{tag}_pre.png")
    words = P.ocr(png)
    body = re.sub(r"[^a-z]", "", " ".join(w for w, *_ in words).lower())
    if "oops" in body or "reallywanttoquit" in body:
        dismiss_reallyquit(words)
        png = P.freeze(f"{tag}_pre")
        shutil.copy(png, f"{EVID}/{tag}_pre.png")
        words = P.ocr(png)
        body = re.sub(r"[^a-z]", "", " ".join(w for w, *_ in words).lower())
    pane = "enterfornextturn" in body or "nounitsneedneworders" in body
    kind = P.classify(words, png=png)
    btn_words = P.ocr_crop(png, (615, 396, 180, 34), f"{tag}_btn", scale=6)
    btxt = re.sub(r"[^a-z]", "", " ".join(w[0] for w in btn_words).lower())
    hud_ok = kind == "hud" or "mplete" in btxt or "omple" in btxt
    # a selected unit panel makes classify() return `unknown` with a garbled strip OCR
    # (m38run: body had the terrain-description page + ALREADY MOVED) — on OUR turn
    # that state is fine: the svc loop below ends the turn via TURN COMPLETE/TURN_BTN
    our_turn = u32(0x985DCC) == 3
    rec.update(pre_body=body[:160], pre_kind=kind, btn_ocr=btxt)
    assert pane or hud_ok or our_turn, f"unexpected screen {kind}: {body[:120]!r} btn={btxt!r}"

    # --- arm the probe ---
    gp = os.path.join(P.ROOT, "scripts", "m37_exec41.gdb")
    if not os.path.exists(gp):
        gp = os.path.join(P.ROOT, "scratch", "m37_exec41.gdb")
    gsrc = open(gp).read()
    gpath = f"{EVID}/{tag}_chain.gdb"
    open(gpath, "w").write(gsrc)
    log = f"{EVID}/{tag}_gdb.log"
    gdb = subprocess.Popen(f"gdb -batch -nx -x {gpath} -p {pid} > {log} 2>&1",
                           shell=True)
    time.sleep(2.5)
    armed = sum(1 for _ in open(log, errors="replace")
                if "Breakpoint" in _ and " at " in _)
    rec["gdb"] = dict(pid=gdb.pid, armed=armed, expect=11)
    print(f"armed {armed}/11 breakpoints (gdb {gdb.pid})", flush=True)
    if armed < 11:
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
        png = P.freeze(f"{tag}_post")
        shutil.copy(png, f"{EVID}/{tag}_post.png")
        rec["events"] = [l.strip() for l in open(log, errors="replace")
                         if re.match(r"^(REFRESH|ORDEREXEC|TERRAFEXEC|CHECK|NOTYET|"
                                     r"CANCEL|COMPLETE|RAISE|LOWER|SETELEV|MASKSET)",
                                     l.strip())]
        json.dump(rec, open(f"{EVID}/{tag}_exec41.json", "w"), indent=1)
        print(json.dumps({"reason": reason, "events_n": len(rec["events"])}))
        for e in rec["events"]:
            print("EV:", e)
        sys.exit(0)

    # --- end our turn ---
    P.focus()
    if pane:
        P.key("Return")
        rec["pressed"] = "Return (ENDOFTURN1)"
    else:
        btn = P.find(words, ["complete"])
        P.click(btn[:2] if btn else P.TURN_BTN)
        rec["pressed"] = f"TURN COMPLETE at {tuple(btn[:2]) if btn else P.TURN_BTN}"

    # --- follow rounds ---
    deadline = time.time() + a.budget
    year0 = pre["year"]
    rounds_done = 0
    last_snap = year0
    last_ocr = 0.0
    last_year_t = time.time()
    complete_seen = False
    while time.time() < deadline:
        try:
            logtxt = open(log, errors="replace").read()
        except FileNotFoundError:
            logtxt = ""
        if re.search(r"^(COMPLETE unit=\d+ x=45 y=7|SETELEV x=45 y=7 new=5|RAISE x=45 y=7)", logtxt, re.M):
            if not complete_seen:
                complete_seen = True
                print("completion path fired; grace 4s", flush=True)
                time.sleep(4)
                finish("completion")
        y = u32(0x985B00)
        cur = u32(0x985DCC)
        if y > last_snap:
            rounds_done += 1
            last_snap = y
            last_year_t = time.time()
            snapshot(f"round{rounds_done}")
            if cur != 3:
                # our turn hasn't started yet in this year; keep waiting
                pass
            if rounds_done >= a.rounds:
                finish(f"{rounds_done} rounds, no completion")
        if time.time() - last_ocr > 6:
            last_ocr = time.time()
            png = P.freeze(f"{tag}_svc")
            words = P.ocr(png)
            kind = P.classify(words, png=png)
            body = re.sub(r"[^a-z]", "", " ".join(w[0] for w in words).lower())
            cur = u32(0x985DCC)
            if "oops" in body or "reallywanttoquit" in body:
                dismiss_reallyquit(words)
            elif "enterfornextturn" in body or "nounitsneedneworders" in body:
                P.key("Return")   # ENDOFTURN1: Return advances (M36), never Escape
            elif kind == "confirm":
                P.answer_confirm(words)
            elif kind == "dialog":
                P.key("Return")
            elif kind == "hud" and cur == 3 and time.time() - last_year_t > 18:
                # bare HUD stuck on our turn: the pump has no actionable unit and
                # no pane; the loop must end the turn itself every round (m37c
                # stalled at 2276 because only the FIRST turn-end was clicked)
                btn = P.find(words, ["complete"])
                P.click(btn[:2] if btn else P.TURN_BTN)
                rec["svc_hud_clicks"] = rec.get("svc_hud_clicks", 0) + 1
            elif kind == "unknown":
                png2 = P.freeze(f"{tag}_svc2")
                w2 = P.ocr(png2)
                b2 = re.sub(r"[^a-z]", "", " ".join(w[0] for w in w2).lower())
                if "oops" in b2 or "reallywanttoquit" in b2:
                    dismiss_reallyquit(w2)
                elif P.classify(w2, png=png2) == "unknown" and \
                        P.region_colors(png2, (180, 60, 620, 200)) < 130:
                    # a pane is over the map; a bare HUD has >=130 terrain colours
                    # there (M36) — Escape on the bare HUD opens REALLYQUIT
                    P.key("Escape")
        time.sleep(1)
    finish("budget")


if __name__ == "__main__":
    main()
