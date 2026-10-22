#!/usr/bin/env python3
"""M36b: execute the stored terraform order (unit 41, order 0x14) and catch the
queue/executor chain: ENDOFTURN1 pane ("Press ENTER for next turn") -> Return ->
execution phase -> SOLOWRAP(0x529090)/EXEC(0x585720) -> SETMASK(0x582ed0) ->
tile height 4 -> 5. Watches for DRAIN(0x5262e0)/DISP(0x52bce0) firing in solo,
setter re-entry (TERRAF/PAYPATH/DEBIT would mean EXEC re-runs the issue path),
and services any modal that pops during AI turns.

Usage: python3 scripts/m36_exec.py [--tag m36b] [--unit 41] [--tilex 45] [--tiley 7]
"""
import argparse, json, os, re, shutil, struct, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P

EVID = P.EVID


def wait_for(log, needle, timeout):
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m36b")
    ap.add_argument("--unit", type=int, default=41)
    ap.add_argument("--tilex", type=int, default=45)
    ap.add_argument("--tiley", type=int, default=7)
    ap.add_argument("--budget", type=float, default=180.0)
    a = ap.parse_args()
    U, TX, TY, tag = a.unit, a.tilex, a.tiley, a.tag
    rec = {"tag": tag, "unit": U, "t": time.strftime("%F %T")}

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

    def snapshot(label):
        u = P.unit_rec(f, U)
        tb = u32(0x92AE14)
        ta = tb + (40 * TY + (TX >> 1)) * 0x2c
        t = rd(ta, 0x2c)
        me = u32(0x91B5B4)
        out = dict(year=u32(0x985B00), cur=u32(0x985DCC),
                   sel=struct.unpack("<i", rd(P.SEL_G, 4))[0],
                   energy=struct.unpack("<i", rd(P.ENERGY_G + me * P.ENERGY_STRIDE * 4, 4))[0],
                   unit=dict(x=u["x"], y=u["y"], order=u["order"], mpused=u["mpused"]),
                   tile_addr=hex(ta), tile0=t[0], tile_elev=t[0] >> 5,
                   tile_mask=struct.unpack("<I", t[8:12])[0])
        rec[label] = out
        return out

    pre = snapshot("pre")
    assert pre["unit"]["order"] == 0x14, f"order not stored: {pre['unit']}"

    # ENDOFTURN1 pane must be up: OCR and look for the phrase body
    png = P.freeze(f"{tag}_pre")
    shutil.copy(png, f"{EVID}/{tag}_pre.png")
    words = P.ocr(png)
    body = re.sub(r"[^a-z]", "", " ".join(w for w, *_ in words).lower())
    rec["pre_body"] = body[:200]
    pane = "enterfornextturn" in body or "nounitsneedneworders" in body
    kind = P.classify(words, png=png)
    # the centre info panel cycles pages (Mission Year / Econ / Commerce...), so the
    # only reliable HUD marker is the TURN COMPLETE button itself: OCR its strip at 6x
    btn_words = P.ocr_crop(png, (615, 396, 180, 34), f"{tag}_btn", scale=6)
    btxt = re.sub(r"[^a-z]", "", " ".join(w[0] for w in btn_words).lower())
    rec["btn_ocr"] = btxt
    hud_ok = kind == "hud" or "mplete" in btxt or "omple" in btxt
    rec["pre_kind"] = kind
    assert pane or hud_ok, f"unexpected screen {kind}: {body[:120]!r} btn={btxt!r}"

    gsrc = (open(os.path.join(P.ROOT, "scripts", "m36_exec.gdb")).read()
            .replace("__UNIT__", str(U)).replace("__TILEX__", str(TX))
            .replace("__TILEY__", str(TY)))
    gpath = f"{EVID}/{tag}_chain.gdb"
    open(gpath, "w").write(gsrc)
    log = f"{EVID}/{tag}_gdb.log"
    gdb = subprocess.Popen(f"gdb -batch -nx -x {gpath} -p {pid} > {log} 2>&1", shell=True)
    time.sleep(2.5)
    armed = sum(1 for _ in open(log, errors="replace") if "Breakpoint" in _ and " at " in _)
    rec["gdb"] = dict(pid=gdb.pid, breakpoints_armed=armed, expect=14)
    print(f"armed {armed}/14 breakpoints (gdb {gdb.pid})", flush=True)
    if armed < 14:
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
        rec["post_kind"] = P.classify(P.ocr(png))
        rec["events"] = [l.strip() for l in open(log, errors="replace")
                         if re.match(r"^(ENQ|DRAIN|DISP|SOLOWRAP|EXEC|MOVEUNIT|SETMASK|"
                                     r"TERRAF|PAYPATH|DEBIT|STORE|SPACEH|PANE|ADVISOR)", l.strip())]
        json.dump(rec, open(f"{EVID}/{tag}_exec.json", "w"), indent=1)
        print(json.dumps({"reason": reason, "post": rec["post"]}, indent=1))
        for e in rec["events"]:
            print("EV:", e)
        sys.exit(0)

    # --- end our turn: ENTER on the ENDOFTURN1 pane, else click TURN COMPLETE ---
    P.focus()
    if pane:
        P.key("Return")
        rec["pressed"] = "Return (ENDOFTURN1)"
    else:
        btn = P.find(words, ["complete"])
        P.click(btn[:2] if btn else P.TURN_BTN)
        rec["pressed"] = f"TURN COMPLETE at {tuple(btn[:2]) if btn else P.TURN_BTN}"

    # --- watch execution; service modals that pop during the round ---
    deadline = time.time() + a.budget
    exec_seen = drain_seen = disp_seen = setmask_seen = reentry = False
    last_ocr = 0.0
    events_log = []
    while time.time() < deadline:
        line = wait_for(log, r"^(SOLOWRAP|EXEC) idx=%d " % U, 2)
        if line and not exec_seen:
            exec_seen = True
            events_log.append(line)
            print("EXEC chain:", line, flush=True)
        if not drain_seen and wait_for(log, "^DRAIN #", 0.5):
            drain_seen = True
            print("DRAIN fired", flush=True)
        if not disp_seen and wait_for(log, "^DISP ", 0.5):
            disp_seen = True
            print("DISP fired", flush=True)
        if not setmask_seen and wait_for(log, "^SETMASK ", 0.5):
            setmask_seen = True
        if wait_for(log, "^TERRAF-REENTRY", 0.2):
            reentry = True
        year_now = u32(0x985B00)
        cur = u32(0x985DCC)
        if exec_seen and (setmask_seen or year_now > pre["year"]) and time.time() - \
                (rec.get("exec_t") or 0) > 6:
            break
        if exec_seen and "exec_t" not in rec:
            rec["exec_t"] = time.time()
        # service modals every ~6 s
        if time.time() - last_ocr > 6:
            last_ocr = time.time()
            png = P.freeze(f"{tag}_svc")
            words = P.ocr(png)
            kind = P.classify(words, png=png)
            if kind == "confirm":
                P.answer_confirm(words)
            elif kind == "dialog":
                P.key("Return")
            elif kind == "unknown":
                # transient news/breakthrough panes: one Escape only if it persists
                if rec.get("last_kind") == "unknown":
                    P.key("Escape")
            rec["last_kind"] = kind
            if kind not in ("hud",):
                events_log.append(f"svc {kind}")
        if year_now > pre["year"] and cur == pre["cur"] and exec_seen:
            break
    rec["exec_seen"], rec["drain_seen"], rec["disp_seen"] = exec_seen, drain_seen, disp_seen
    rec["setmask_seen"], rec["setter_reentry"] = setmask_seen, reentry
    time.sleep(2)
    finish("done")


if __name__ == "__main__":
    main()
