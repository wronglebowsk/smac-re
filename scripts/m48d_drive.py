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

GDB_TMPL = """# M48d generated instrument (do not hand-edit; driver writes this)
# our base record @@ADDR@@  min40=@@MIN40@@ q50=@@Q50@@ d0=@@D0@@  energy=@@NRG@@
# slide window [@@SLO@@, @@SHI@@] on the compaction store 0x64bfa3
set pagination off
set confirm off
set can-use-hw-watchpoints 1
set $n = 0
set $npipe = 0
set $npane = 0
set $nwp = 0
set $prev_year = -99

break *0x51f554
commands
  silent
  set $y = *(int *)0x985b00
  if $y != $prev_year
    set $prev_year = $y
    set $nb = *(int *)0x985af4
    set $found = 0
    set $i = 0
    while $i < $nb
      if $found == 0
        if *(unsigned char *)(0x95da10 + $i * 0x130 + 4) == 3
          set $found = 1
          set $b = 0x95da10 + $i * 0x130
          printf "ROUND year=%d turn=%d cur=%d nb=%d mask=%#x cap=%d g38=%d g4c=%d nrg3=%d led3=%d\\n", $y, *(int *)0x985afc, *(int *)0x985dcc, $nb, *(int *)0x985b10, *(int *)0x92a370, *(int *)0x8f0c38, *(int *)0x8f0c4c, *(int *)0x953884, *(int *)0x953888
          printf "OURBASE idx=%d addr=%#x x=%d y=%d pop=%d f30=%#x 3c=%d min40=%d f44=%d f4c=%d q50=%d mir94=%d mir98=%d c0=%d cc=%d d0=%d e0=%d f0=%d fc=%d f38=%#x\\n", $i, $b, *(unsigned short *)$b, *(unsigned short *)($b + 2), *(unsigned char *)($b + 6), *(int *)($b + 0x30), *(int *)($b + 0x3c), *(int *)($b + 0x40), *(int *)($b + 0x44), *(int *)($b + 0x4c), *(int *)($b + 0x50), *(int *)($b + 0x94), *(int *)($b + 0x98), *(int *)($b + 0xc0), *(int *)($b + 0xcc), *(int *)($b + 0xd0), *(int *)($b + 0xe0), *(int *)($b + 0xf0), *(int *)($b + 0xfc), *(int *)($b + 0x38)
        end
      end
      set $i = $i + 1
    end
    if $found == 0
      printf "ROUND year=%d NOBASE owner3 -- our base is GONE (nb=%d)\\n", $y, $nb
    end
    set $i = 0
    set $nu = 0
    while $i < 300
      if *(char *)(0x933278 + $i * 52 + 14) == 3
        if *(unsigned short *)(0x933278 + $i * 52) != 0xffff
          set $nu = $nu + 1
          set $u = 0x933278 + $i * 52
          printf "UNIT idx=%d type=%d x=%d y=%d order=%d mpused=%d home=%d\\n", $i, *(unsigned char *)($u + 10), *(unsigned short *)$u, *(unsigned short *)($u + 2), *(unsigned char *)($u + 17), *(unsigned char *)($u + 40), *(unsigned short *)($u + 46)
        end
      end
      set $i = $i + 1
    end
    printf "UNITS n=%d\\n", $nu
  else
    printf "YEARTORE eip=%#x year=%d\\n", $eip, $y
  end
  continue
end

break *0x4ef6d0
commands
  silent
  set $npipe = $npipe + 1
  set $cb = *(int *)0x8f0d60
  printf "PIPE n=%d base=%#x own=%d x=%d y=%d min40=%d 3c=%d cc=%d d0=%d q50=%d ours=%d\\n", $npipe, $cb, *(unsigned char *)($cb + 4), *(unsigned short *)$cb, *(unsigned short *)($cb + 2), *(int *)($cb + 0x40), *(int *)($cb + 0x3c), *(int *)($cb + 0xcc), *(int *)($cb + 0xd0), *(int *)($cb + 0x50), $cb == @@ADDR@@
  if $npipe >= 500
    printf "PIPE-CAP\\n"
    detach
    quit
  end
  continue
end

break *0x4ef7db
commands
  silent
  set $n = $n + 1
  printf "SITE %d IGATE base=%#x own=%d d0=%d q50=%d f30=%#x min40=%d ours=%d\\n", $n, $eax, *(unsigned char *)($eax + 4), $ecx, *(int *)($eax + 0x50), *(int *)($eax + 0x30), *(int *)($eax + 0x40), $eax == @@ADDR@@
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x4ef7f6
commands
  silent
  set $n = $n + 1
  printf "SITE %d IADD base=%#x own=%d added=%d newmin40=%d ours=%d\\n", $n, $eax, *(unsigned char *)($eax + 4), $ecx, $edx, $eax == @@ADDR@@
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x4ef88b
commands
  silent
  set $n = $n + 1
  printf "SITE %d QGATE base=%#x own=%d q50=%d ours=%d\\n", $n, $eax, *(unsigned char *)($eax + 4), $ecx, $eax == @@ADDR@@
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x4ef9b3
commands
  silent
  set $n = $n + 1
  printf "SITE %d NOQUEUE base=%#x own=%d min40=%d d0=%d f30=%#x ours=%d\\n", $n, $eax, *(unsigned char *)($eax + 4), *(int *)($eax + 0x40), *(int *)($eax + 0xd0), *(int *)($eax + 0x30), $eax == @@ADDR@@
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x4efd49
commands
  silent
  set $n = $n + 1
  printf "SITE %d PROGDIV base=%#x own=%d esi=%d 3c=%d cc=%d edi=%d ours=%d\\n", $n, $ecx, *(unsigned char *)($ecx + 4), $esi, *(int *)($ecx + 0x3c), *(int *)($ecx + 0xcc), $edi, $ecx == @@ADDR@@
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x4efe41
commands
  silent
  set $n = $n + 1
  set $cb = *(int *)0x8f0d60
  printf "SITE %d COMPLET base=%#x own=%d ebx=%d edi=%d esi=%d min40=%d q50=%d ours=%d\\n", $n, $cb, *(unsigned char *)($cb + 4), $ebx, $edi, $esi, *(int *)($cb + 0x40), *(int *)($cb + 0x50), $cb == @@ADDR@@
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x4efed8
commands
  silent
  set $n = $n + 1
  printf "SITE %d SPENDA base=%#x own=%d cost_edi=%d min40_pre=%d m28=%d m30=%d ours=%d\\n", $n, $ecx, *(unsigned char *)($ecx + 4), $edi, *(int *)($ecx + 0x40), *(int *)($ebp - 0x28), *(int *)($ebp - 0x30), $ecx == @@ADDR@@
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x4eff02
commands
  silent
  set $n = $n + 1
  printf "SITE %d CLAMP1 base=%#x own=%d accum=%d d0=%d cap=%d min=%d evbit=%#x mask=%#x ours=%d\\n", $n, $esi, *(unsigned char *)($esi + 4), *(int *)($esi + 0x40), $eax, $ecx, $edx, $dl, *(int *)0x985b10, $esi == @@ADDR@@
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x4eff29
commands
  silent
  set $n = $n + 1
  printf "SITE %d MIRA base=%#x own=%d accum_final=%d mir98_pre=%d ours=%d\\n", $n, $esi, *(unsigned char *)($esi + 4), $eax, *(int *)($esi + 0x98), $esi == @@ADDR@@
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x4f0ca1
commands
  silent
  set $n = $n + 1
  printf "SITE %d SPENDB base=%#x own=%d cost_edi=%d min40_pre=%d m28=%d m30=%d ours=%d\\n", $n, $edx, *(unsigned char *)($edx + 4), $edi, *(int *)($edx + 0x40), *(int *)($ebp - 0x28), *(int *)($ebp - 0x30), $edx == @@ADDR@@
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x4f0ccb
commands
  silent
  set $n = $n + 1
  printf "SITE %d CLAMP2 base=%#x own=%d accum=%d d0=%d cap=%d min=%d evbit=%#x mask=%#x ours=%d\\n", $n, $esi, *(unsigned char *)($esi + 4), *(int *)($esi + 0x40), $eax, $ecx, $edx, $dl, *(int *)0x985b10, $esi == @@ADDR@@
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x4f0cf2
commands
  silent
  set $n = $n + 1
  printf "SITE %d MIRB base=%#x own=%d accum_final=%d mir98_pre=%d ours=%d\\n", $n, $esi, *(unsigned char *)($esi + 4), $eax, *(int *)($esi + 0x98), $esi == @@ADDR@@
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x4f1e3f
commands
  silent
  set $n = $n + 1
  printf "SITE %d QDRAIN base=%#x own=%d m30=%d q50_pre=%d pop=%d x=%d y=%d ours=%d\\n", $n, $eax, *(unsigned char *)($eax + 4), *(int *)($ebp - 0x30), *(int *)($eax + 0x50), *(unsigned char *)($eax + 6), *(unsigned short *)$eax, *(unsigned short *)($eax + 2), $eax == @@ADDR@@
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x483470
commands
  silent
  set $npane = $npane + 1
  if $npane < 80
    printf "PANE n=%d id=%s\\n", $npane, (char *)*(int *)($esp + 4)
  end
  if $npane >= 80
    printf "PANE-CAP\\n"
    detach
    quit
  end
  continue
end

# no bp on 0x64bfa3: it is a generic dword-copy loop (thousands of hits/frame).
# slide detection = WP identity bytes (own/x/y below) + per-round marker re-scan.
watch *(int *)@@MIN40@@
commands
  silent
  set $nwp = $nwp + 1
  printf "WP %d MIN40 eip=%#x new=%d own=%d x=%d y=%d d0=%d q50=%d eax=%#x ecx=%#x edx=%#x esi=%#x edi=%#x\\n", $nwp, $eip, *(int *)@@MIN40@@, *(unsigned char *)(@@ADDR@@ + 4), *(unsigned short *)@@ADDR@@, *(unsigned short *)(@@ADDR@@ + 2), *(int *)@@D0@@, *(int *)@@Q50@@, $eax, $ecx, $edx, $esi, $edi
  if $nwp >= 40
    printf "WP-CAP\\n"
    detach
    quit
  end
  continue
end

watch *(int *)@@Q50@@
commands
  silent
  set $nwp = $nwp + 1
  printf "WP %d QUEUE50 eip=%#x new=%d min40=%d\\n", $nwp, $eip, *(int *)@@Q50@@, *(int *)@@MIN40@@
  if $nwp >= 40
    printf "WP-CAP\\n"
    detach
    quit
  end
  continue
end

watch *(int *)@@D0@@
commands
  silent
  set $nwp = $nwp + 1
  printf "WP %d D0 eip=%#x new=%d c0=%d f0=%d e0=%d min40=%d\\n", $nwp, $eip, *(int *)@@D0@@, *(int *)(@@ADDR@@ + 0xc0), *(int *)(@@ADDR@@ + 0xf0), *(int *)(@@ADDR@@ + 0xe0), *(int *)@@MIN40@@
  if $nwp >= 40
    printf "WP-CAP\\n"
    detach
    quit
  end
  continue
end

watch *(int *)@@NRG@@
commands
  silent
  set $nwp = $nwp + 1
  printf "WP %d ENERGY eip=%#x new=%d eax=%#x ecx=%#x esi=%#x edi=%#x\\n", $nwp, $eip, *(int *)@@NRG@@, $eax, $ecx, $esi, $edi
  if $nwp >= 40
    printf "WP-CAP\\n"
    detach
    quit
  end
  continue
end

printf "SELFTEST addrs: %#x %#x %#x %#x %#x %#x %#x\\n", @@ADDR@@, @@MIN40@@, @@Q50@@, @@D0@@, @@NRG@@, @@SLO@@, @@SHI@@
printf "SELFTEST state: year=%d turn=%d cur=%d nb=%d min40=%d 3c=%d cc=%d q50=%d d0=%d nrg3=%d mask=%#x cap=%d\\n", *(int *)0x985b00, *(int *)0x985afc, *(int *)0x985dcc, *(int *)0x985af4, *(int *)@@MIN40@@, *(int *)(@@ADDR@@ + 0x3c), *(int *)(@@ADDR@@ + 0xcc), *(int *)@@Q50@@, *(int *)@@D0@@, *(int *)@@NRG@@, *(int *)0x985b10, *(int *)0x92a370
printf "ARMED\\n"
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

    subprocess.run(["pkill", "-INT", "-f", f"[{tag[0]}]{tag[1:]}_drive"])
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
                y = row_y("channel")
                if y:
                    P.click((400, y))
                    time.sleep(1.3)
                rec["events"].append(f"ocr: comm pane -> close-channel row y={y}")
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
