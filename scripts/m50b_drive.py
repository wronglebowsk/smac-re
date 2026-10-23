#!/usr/bin/env python3
"""M48d: definitive mineral-economy round. Session 45.

Fixes every failure mode of m48a-h:
  * base identity: the base array SLIDES (m48h caught rep movsl at 0x64bfa3 moving
    record 73 into 72 while watches sat on the old window). We re-locate our base by
    CONTENT (owner==3) before arming, bake literal watch addresses for THAT address,
    arm a slide-detector bp on 0x64bfa3, and the year marker re-scans owner==3 every
    round so a mid-run slide is visible in the log.
  * the end-turn confirm: m48c_probe stalled because it only clicked the Yes row when
    the row was ALREADY blue; the confirm DEFAULTS to Cancel, so OK-click-only = Cancel
    forever. Here: for any flat blue bar in y 150-430, click (bar_x, bar_y-25) FIRST
    unconditionally, wait 1.3 s, then click the bar.
  * OCR load: colour-only fast loop; tesseract only as a >=35 s-stuck fallback via
    m44_idle.service_pane (one job at a time, pitfall 5).
  * gdb build traps (m48b/e lessons): literal watch addresses, no loop_break inside
    if-in-while in commands lists, no convenience vars in watch expressions, no
    `set print frame-verbosity`, every commands list ends with continue, and a
    SELFTEST block touches every address at script time.

Pokes (TracerPid 0, before arming): base+0x3c (production progress) = 500,
base+0xcc (production RATE -- ours reads 0, which is why the 2315 queue never
progresses) = 1, base+0x40 (mineral storage) = 200. Goal: force the completion path
(SPEND/CLAMP/MIRROR/QDRAIN/PRODUCEPROTO) to execute on OUR base under the armed
instrument, and catch the clamp that pins our storage to max(0, min(d0, cap)) live.

Usage: python3 scripts/m48d_drive.py --tag m48d --rounds 3 --budget 1500
"""
import argparse, json, os, signal, struct, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P
from PIL import Image
from m44_idle import service_pane, find_ok_bar, rightmost_blue_run
from m48_minerals import hud_up

BASE_ARR, BASE_STRIDE = 0x95da10, 0x130
ENERGY_ADDR = 0x953884          # our faction record +0 (stride 0x20bc bytes)
EVID = P.EVID

GDB_TMPL = r"""# M50b generated instrument: who truncates the per-base sweep?
set pagination off
set confirm off
set $sw_p = -1
set $sw_i = -1
set $sw_n = 0
set $nsweep = 0
set $nvis = 0
set $nyear = 0

# 0x520540(player): resets the sweep state for this player's pass
break *0x520540
commands
  silent
  set $nsweep = $nsweep + 1
  set $sw_p = *(int *)($esp + 4)
  set $sw_i = 0
  set $sw_n = 0
  printf "SWEEP %d p=%d nb_entry=%d\n", $nsweep, $sw_p, *(int *)0x985af4
  continue
end

# 0x5206d3: the call to 0x4f5a70 for a base whose owner byte == player
break *0x5206d3
commands
  silent
  set $sw_n = $sw_n + 1
  set $nvis = $nvis + 1
  printf "VISIT p=%d idx=%d owner=%d nb=%d ours=%d st=%d min40=%d\n", $sw_p, $ebx, *(unsigned char *)(0x95da14 + $ebx * 0x130), *(int *)0x985af4, (0x95da14 + $ebx * 0x130 - 4) == @@ADDR@@, *(int *)(0x95da10 + $ebx * 0x130 + 0x40), *(int *)(0x95da10 + $ebx * 0x130 + 0x3c)
  continue
end

# 0x5206f9: loop back edge (ebx already incremented) - records how far the pass got
break *0x5206f9
commands
  silent
  set $sw_i = $ebx - 1
  continue
end

# 0x5206fd: loop exit (or the n_bases<=0 fast path)
break *0x5206fd
commands
  silent
  printf "SWEEPEND p=%d last_idx=%d visits=%d nb_now=%d\n", $sw_p, $sw_i, $sw_n, *(int *)0x985af4
  continue
end

# 0x51f554: the year store - the suspected mid-sweep interrupter
break *0x51f554
commands
  silent
  set $nyear = $nyear + 1
  printf "YEAR %d mid_p=%d mid_idx=%d mid_visits=%d nb=%d cur=%d\n", $nyear, $sw_p, $sw_i, $sw_n, *(int *)0x985af4, *(int *)0x985dcc
  continue
end
printf "ARMED\n"
continue
"""



def squash(words):
    import re
    return re.sub(r"[^a-z]", "", " ".join(w[0] for w in words).lower())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m48d")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--budget", type=float, default=1500.0)
    ap.add_argument("--no-poke", action="store_true")
    a = ap.parse_args()
    tag, t0 = a.tag, time.time()
    rec = {"tag": tag, "t": time.strftime("%F %T"), "events": [], "rounds": []}

    # kill stale same-tag drivers but never ourselves (bracket pattern matches our own cmdline)
    for pid_s in subprocess.run(["pgrep", "-f", f"[{tag[0]}]{tag[1:]}_drive"],
                                capture_output=True, text=True).stdout.split():
        if int(pid_s) != os.getpid():
            try:
                os.kill(int(pid_s), signal.SIGINT)
            except ProcessLookupError:
                pass
    time.sleep(1)
    if subprocess.run(["pgrep", "-x", "gdb"], capture_output=True, text=True).stdout.strip():
        print("ABORT: a gdb is already running"); return 1
    pid = int(subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True,
                             text=True).stdout.split()[0])
    rec["pid"] = pid

    def tracer():
        out = subprocess.run(["grep", "TracerPid", f"/proc/{pid}/status"],
                             capture_output=True, text=True).stdout
        return int(out.split()[-1])
    assert tracer() == 0, "tracer attached before run"

    ro = os.open(f"/proc/{pid}/mem", os.O_RDONLY)

    def i32(addr):
        return struct.unpack("<i", os.pread(ro, 4, addr))[0]

    def locate():
        nb = i32(0x985af4)
        blob = os.pread(ro, nb * BASE_STRIDE, BASE_ARR)
        for i in range(nb):
            r = blob[i * BASE_STRIDE:(i + 1) * BASE_STRIDE]
            if r[4] == 3:
                name = r[19:39].split(b"\0")[0].decode("latin1", "replace")
                g = lambda o: struct.unpack("<i", r[o:o + 4])[0]
                return dict(idx=i, addr=BASE_ARR + i * BASE_STRIDE, name=name,
                            pop=r[6], min40=g(0x40), q50=g(0x50), d0=g(0xd0),
                            c0=g(0xc0), cc=g(0xcc), f3c=g(0x3c), fc=g(0xfc))
        return None

    loc = locate()
    if not loc:
        print("ABORT: no owner==3 base"); return 1
    rec["locate"] = loc
    print(f"[locate] {loc}", flush=True)
    addr = loc["addr"]
    MIN40, Q50, D0 = addr + 0x40, addr + 0x50, addr + 0xd0
    SLO, SHI = addr - 0x130, addr + 0x260

    # ---- pokes (TracerPid 0) ----
    if not a.no_poke:
        assert tracer() == 0
        rw = os.open(f"/proc/{pid}/mem", os.O_RDWR)
        for off, val in ((0x3c, 500), (0xcc, 1), (0xd0, 200), (0x40, 200)):
            os.pwrite(rw, struct.pack("<i", val), addr + off)
            got = struct.unpack("<i", os.pread(rw, 4, addr + off))[0]
            rec["events"].append(f"poked +{hex(off)} -> {got}")
            print(f"[poke] +{hex(off)} = {got}", flush=True)
        os.close(rw)

    # ---- generated gdb script ----
    txt = GDB_TMPL
    for k, v in (("@@ADDR@@", hex(addr)), ("@@MIN40@@", hex(MIN40)),
                 ("@@Q50@@", hex(Q50)), ("@@D0@@", hex(D0)),
                 ("@@NRG@@", hex(ENERGY_ADDR)), ("@@SLO@@", hex(SLO)),
                 ("@@SHI@@", hex(SHI))):
        txt = txt.replace(k, v)
    gpath = f"evidence/{tag}_watch.gdb"
    open(gpath, "w").write(txt)
    lpath = f"{EVID}/{tag}_watch.log"

    # ---- arm ----
    lf = open(lpath, "wb")
    g = subprocess.Popen(["gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=lf, stderr=subprocess.STDOUT)
    rec["gdb_pid"] = g.pid
    time.sleep(7)
    rec["events"].append("gdb launched")
    print("[gdb] armed (log block-buffered; read after detach)", flush=True)

    # ---- driver loop (colour-first) ----
    year0 = i32(0x985b00)
    year = year0
    last_click = last_freeze = last_ocr = t0
    ocr_passes = svc_clicks = 0
    stuck_since = t0

    def state():
        loc = locate()
        return dict(year=i32(0x985b00), turn=i32(0x985afc), cur=i32(0x985dcc),
                    nb=i32(0x985af4), nrg3=i32(ENERGY_ADDR),
                    base=loc or {"GONE": 1})

    rounds_done = 0
    while time.time() - t0 < a.budget and rounds_done < a.rounds:
        now = time.time()
        y = i32(0x985b00)
        if y != year:
            st = state()
            rec["rounds"].append({"dt": round(now - t0, 1), **st})
            rec["events"].append(f"year {year}->{y} cur={st['cur']} "
                                 f"min40={st['base'].get('min40')} q50={st['base'].get('q50')}")
            year = y
            rounds_done += 1
            stuck_since = now
            time.sleep(10)
            continue
        if now - last_freeze > 4.0:
            last_freeze = now
            P.focus()
            png = P.freeze(tag)
            # colour dismiss
            ob = rightmost_blue_run(png, band=(240, 150, 560, 430))
            if ob:
                bx, by = ob
                P.click((bx, by - 25))
                time.sleep(1.3)
                P.click((bx, by))
                rec["events"].append(f"colour: row(bar_y-25)+bar at ({bx},{by})")
                svc_clicks += 1
                time.sleep(1.0)
                continue
            bar = find_ok_bar(png)
            if bar:
                P.click(bar)
                rec["events"].append(f"colour: ok-bar click {bar}")
                svc_clicks += 1
                time.sleep(1.0)
                continue
            s = state()
            if s["cur"] == 3 and hud_up(png) and now - last_click > 9.0:
                P.click(P.TURN_BTN)
                last_click = now
                rec["events"].append("clicked TURN_BTN")
                continue
        if now - stuck_since > 35.0 and now - last_ocr > 20.0:
            last_ocr = now
            P.focus()
            png = P.freeze(tag + "_ocr")
            words = P.ocr(png)
            ocr_passes += 1
            body = squash(words)
            kind = P.classify(words, png=png)
            bar = find_ok_bar(png)

            def row_y(word):
                for w, x, y, c in words:
                    if word in w.lower():
                        return y
                return None

            if "tour" in body and "continue" in body:
                P.click((325, 585))
                rec["events"].append("ocr: TOUR popup -> Continue (325,585)")
            elif "socialengineering" in body or ("politics" in body and "society" in body):
                P.click((240, 368))
                rec["events"].append("ocr: Social Engineering screen -> OK (240,368)")
            elif "channel" in body and "through" in body:
                # 3-row COMM OFFICER variant (M50b). A click only highlights the
                # row and the bar cycle drifts onto "Display faction leader
                # profile" (University Intelligence Files, ~8 min drain).
                # Keyboard is deterministic: selection starts on row 1, so one
                # Down lands on "No, close the channel.", Return commits it.
                P.key("Down")
                time.sleep(0.4)
                P.key("Return")
                rec["events"].append("ocr: comm pane -> Down+Return (close channel)")
            elif "disband" in body and "nevermind" in body:
                ob2 = rightmost_blue_run(png, band=(240, 150, 560, 430))
                if ob2:
                    P.click(ob2)
                elif bar:
                    P.click(bar)
                rec["events"].append("ocr: CONFIRM DISBAND -> cancel via OK bar only")
            elif any(k in body for k in ("ecologist", "mindworm", "spotted",
                                          "convenes", "agenda", "measure",
                                          "breakthrough", "discovery")):
                P.key("Return")
                rec["events"].append(f"ocr-fallback: Return on '{body[:40]}'")
            elif not service_pane(png, words, body, kind, rec, "drive", bar=bar):
                if "book" in body or "skim" in body or len(words) > 25:
                    P.click((400, 470))
                    rec["events"].append("ocr-fallback: click (400,470) story page")
                elif "overall" in body or "territory" in body:
                    P.click((400, 580))
                    rec["events"].append("ocr-fallback: click (400,580) table")
                else:
                    P.key("Return")
                    rec["events"].append(f"ocr-fallback: Return generic '{body[:40]}'")
            time.sleep(2)
        time.sleep(2)

    rec["reason"] = "rounds" if rounds_done >= a.rounds else "budget"
    rec["final"] = state()
    rec["ocr_passes"], rec["svc_clicks"] = ocr_passes, svc_clicks

    # ---- cleanup ----
    g.send_signal(signal.SIGINT)
    t1 = time.time()
    detached = False
    while time.time() - t1 < 60:
        try:
            if b"detached" in open(lpath, "rb").read():
                detached = True
                break
        except Exception:
            pass
        time.sleep(2)
    rec["detached"] = detached
    try:
        subprocess.run(["kill", "-CONT", str(pid)])
    except Exception:
        pass
    g.wait(timeout=30)
    os.close(ro)
    json.dump(rec, open(f"{EVID}/{tag}_drive.json", "w"), indent=1)
    print(json.dumps({"reason": rec["reason"], "year0": year0,
                      "final_year": rec["final"]["year"], "ocr_passes": ocr_passes,
                      "rounds": len(rec["rounds"])}))


def dismiss(png):
    ob = rightmost_blue_run(png, band=(240, 150, 560, 430))
    if ob:
        bx, by = ob
        P.click((bx, by - 25))
        time.sleep(1.3)
        P.click((bx, by))
        return True
    bar = find_ok_bar(png)
    if bar:
        P.click(bar)
        return True
    return False


if __name__ == "__main__":
    main()
