#!/usr/bin/env python3
"""M48 option 1: the MINERAL economy, driven live with write provenance.

Footing this run (see turn_driver.md §M46/§M47 + NAMED.md):
  * energy provenance is DONE (income 0x4f5c8c `energy += base+0xfc`, facility
    upkeep 0x4f4952, AI per-base 0x4f2dc2).  The MINERAL side is the other half.
  * Ghidra's base-record pointer `DAT_008f0d60` is typed `short *`, so a Ghidra
    offset N is BYTE offset 2N (proof: `+ 0x1c` == the constant field at byte 0x38,
    `+ 0x4c = + 0x20` == the +0x98 == +0x40 mirror, and
    `DAT_008f0d60 = &DAT_0095da10 + idx * 0x98` == 304 B stride).  Under that map
    FUN_004ef6d0 contains  `*(int*)(base+0x20) -= iVar3*iVar4`  (byte +0x40, the
    mineral accumulator, cost = item cost x qty) behind an
    "accumulator < cost" bail, plus the `+0x40 = +0x98` mirror copy.
  * base byte +0x50 is the production-queue head: the drain loop is
    `iVar3 = *(int*)(base+0x28); while (iVar3 != -0x26) {...}` (byte 0x50, sentinel
    -38 = nothing queued) and the popped value is used as a *unit type index*
    (`* 0x34` into the class table 0x98adb2).  Ours read 2 = the Scout Patrol type
    the base has been turning out since M45, i.e. a build was ALREADY queued.

What this runner does: snapshot (TracerPid 0) -> arm gdb watchpoints
(scripts/m48_watch.gdb: base+0x40, base+0x50, faction energy, + a ROUND marker
breakpoint at the M47-verified year store 0x51f554) -> drive rounds to a build
completion -> SIGINT gdb (block-buffered stdout: flush before reading), detach,
CONT the game -> post-snapshot.  Read-only: no pokes, no calls.

Usage: python3 scripts/m48_minerals.py --tag m48a --rounds 4 --budget 600
"""
import argparse, json, os, re, shutil, signal, struct, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P
from PIL import Image
from m44_idle import service_pane, find_ok_bar, hud_econ

EVID = P.EVID
BASE_ARR, BASE_STRIDE = 0x95da10, 0x130
FAC_BASE, FAC_STRIDE, FAC_INTS = 0x94d650, 0x20bc, 2111


def hud_up(png):
    im = Image.open(png).convert("RGB").crop((600, 395, 800, 425))
    n = sum(1 for r, g, b in im.getdata() if r > 180 and 60 <= g <= 160 and b < 80)
    return n > 300


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m48a")
    ap.add_argument("--rounds", type=int, default=4)
    ap.add_argument("--budget", type=float, default=600.0)
    ap.add_argument("--gdb", default="scripts/m48_watch.gdb")
    ap.add_argument("--no-gdb", action="store_true")
    a = ap.parse_args()
    tag = a.tag
    rec = {"tag": tag, "t": time.strftime("%F %T"), "events": []}

    pid = int(subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True,
                             text=True).stdout.split()[0])
    rec["pid"] = pid

    f = open(f"/proc/{pid}/mem", "rb", 0)

    def rd(addr, n):
        f.seek(addr); return f.read(n)

    def u32(addr):
        return struct.unpack("<I", rd(addr, 4))[0]

    def i32(addr):
        return struct.unpack("<i", rd(addr, 4))[0]

    def ints(addr, n):
        return list(struct.unpack(f"<{n}i", rd(addr, 4 * n)))

    def tracer():
        out = subprocess.run(["grep", "TracerPid", f"/proc/{pid}/status"],
                             capture_output=True, text=True).stdout
        return int(out.split()[-1])

    def snapshot():
        nb = u32(0x985af4)
        blob = rd(BASE_ARR, nb * BASE_STRIDE)
        bases = []
        for i in range(nb):
            r = blob[i * BASE_STRIDE:(i + 1) * BASE_STRIDE]
            g = lambda off: struct.unpack("<i", r[off:off + 4])[0]
            d = dict(idx=i, owner=r[4], x=g(0), y=g(2), pop=r[6], growth=r[7],
                     minerals=g(0x40), f44=g(0x44), queue50=g(0x50),
                     f68=g(0x68), mirror98=g(0x98), c4=g(0xc4), d4=g(0xd4),
                     f90=g(0x120), prod_energy=g(0x100), prod_fc=g(0xfc),
                     prod_104=g(0x104), prod_108=g(0x108))
            if r[4] == 3:
                d["name"] = r[19:39].split(b"\0")[0].decode("latin1", "replace")
                d["full"] = list(struct.unpack("<76i", r))
            bases.append(d)
        live = sorted({b["owner"] for b in bases} | {3})
        live = [p for p in live if p < 8]
        fac = {p: ints(FAC_BASE + p * FAC_STRIDE, FAC_INTS) for p in live}
        ub = rd(0x933278, 300 * 52)
        units = []
        for i in range(300):
            r = ub[i * 52:(i + 1) * 52]
            x = struct.unpack("<H", r[0:2])[0]
            if r[14] == 3 and x != 0xffff:
                units.append(dict(idx=i, type=r[10], x=x,
                                  y=struct.unpack("<H", r[2:4])[0],
                                  order=r[17], mpused=r[40],
                                  home=struct.unpack("<H", r[46:48])[0]))
        scratch = {"net_7457dc": i32(0x7457dc), "gross_745734": i32(0x745734),
                   "trade_7457d4": i32(0x7457d4), "upkeep_744f28": i32(0x744f28),
                   "food_74572c": i32(0x74572c), "needpct_745730": i32(0x745730),
                   "item_counts_745738": ints(0x745738, 39)}
        return dict(year=u32(0x985b00), turn=u32(0x985afc), cur=u32(0x985dcc),
                    n_bases=nb, units=units, nmine=len(units), scratch=scratch,
                    fac=fac, bases=[b for b in bases])

    def brief(s):
        ours = [b for b in s["bases"] if b["owner"] == 3]
        return dict(year=s["year"], turn=s["turn"], cur=s["cur"], n_bases=s["n_bases"],
                    nmine=s["nmine"], energy={p: s["fac"][p][0] for p in s["fac"]},
                    our_bases=[{k: b[k] for k in ("idx", "name", "pop", "minerals",
                                                  "f44", "queue50", "mirror98", "f68",
                                                  "c4", "d4", "prod_energy", "prod_fc",
                                                  "prod_104", "prod_108")} for b in ours],
                    units=s["units"],
                    scratch={k: v for k, v in s["scratch"].items()
                             if not isinstance(v, list)})

    def finish(reason, gproc=None, logpath=None):
        # pitfall 15: gdb's stdout to a file is BLOCK-BUFFERED -- SIGINT flushes it
        # (and detaches cleanly); only then may the log be read.
        try:
            if gproc is not None and gproc.poll() is None:
                gproc.send_signal(signal.SIGINT)
            gpids = subprocess.run(["pgrep", "-x", "gdb"], capture_output=True,
                                   text=True).stdout.split()
            for g in gpids:
                subprocess.run(["kill", "-INT", g])
            for _ in range(60):
                time.sleep(1)
                try:
                    if b"detached" in open(logpath, "rb").read():
                        break
                except Exception:
                    pass
            else:
                for g in subprocess.run(["pgrep", "-x", "gdb"], capture_output=True,
                                        text=True).stdout.split():
                    subprocess.run(["kill", "-KILL", g])
            if gproc is not None and gproc.poll() is None:
                gproc.kill()
        except Exception as e:
            rec["events"].append(f"gdb stop failed: {e}")
        subprocess.run(["kill", "-CONT", str(pid)])
        time.sleep(1)
        rec["tracer_after_gdb"] = tracer()
        rec["reason"] = reason
        try:
            rec["final"] = brief(snapshot())
        except Exception as e:
            rec["events"].append(f"final snapshot failed: {e}")
        try:
            png = P.freeze(f"{tag}_post"); shutil.copy(png, f"{EVID}/{tag}_post.png")
        except Exception:
            pass
        json.dump(rec, open(f"{EVID}/{tag}_drive.json", "w"), indent=1)
        print(json.dumps({"reason": reason, "rounds": len(rec.get("rounds", [])),
                         "final_year": rec.get("final", {}).get("year")}))
        print("saved:", f"{EVID}/{tag}_drive.json")
        sys.exit(0)

    # ---- preflight: get to a clean HUD with no tracer attached ----
    assert tracer() == 0, "tracer already attached"
    png = P.freeze(f"{tag}_pre"); shutil.copy(png, f"{EVID}/{tag}_pre.png")
    words = P.ocr(png)
    body = re.sub(r"[^a-z]", "", " ".join(w[0] for w in words).lower())
    pane = "enterfornextturn" in body or "nounitsneedneworders" in body
    kind = P.classify(words, png=png)
    t0 = time.time()
    while not pane and not hud_up(png) and time.time() - t0 < 240:
        service_pane(png, words, body, kind, rec, "preflight")
        time.sleep(2.5)
        P.focus()
        png = P.freeze(f"{tag}_pre"); shutil.copy(png, f"{EVID}/{tag}_pre.png")
        words = P.ocr(png)
        body = re.sub(r"[^a-z]", "", " ".join(w[0] for w in words).lower())
        pane = "enterfornextturn" in body or "nounitsneedneworders" in body
        kind = P.classify(words, png=png)
    rec["events"].append(f"preflight kind={kind} pane_end={pane} hud={hud_up(png)}")
    P.focus()
    if pane:
        P.key("Return"); rec["events"].append("Return on ENDOFTURN1 (preflight)")
        time.sleep(2)

    snap0 = snapshot()
    rec["snap0"] = brief(snap0)
    print("[snap0]", json.dumps(brief(snap0)), flush=True)

    # ---- arm gdb AFTER all reads (pitfall: pokes/reads under a tracer lie) ----
    gproc = None
    logpath = f"{EVID}/{tag}_watch.log"
    if not a.no_gdb:
        assert snap0["bases"] and any(b["owner"] == 3 and b["idx"] == 72
                                      for b in snap0["bases"]), \
            "our base is not idx 72 -- recompute the watch addresses"
        lf = open(logpath, "wb")
        gproc = subprocess.Popen(["timeout", str(int(a.budget + 240)), "gdb", "-batch",
                                  "-nx", "-x", a.gdb, "-p", str(pid)],
                                 stdout=lf, stderr=subprocess.STDOUT)
        armed = False
        for _ in range(60):
            time.sleep(1)
            try:
                if b"ARMED" in open(logpath, "rb").read():
                    armed = True; break
            except Exception:
                pass
        rec["events"].append(f"gdb armed={armed} log={logpath}")
        print("[gdb]", "armed" if armed else "NOT ARMED", flush=True)
        if not armed:
            finish("gdb did not arm", gproc, logpath)

    rounds, last_year = [], snap0["year"]
    last_svc = last_year_t = 0.0
    deadline = time.time() + a.budget
    while time.time() < deadline:
        y, cur = u32(0x985b00), u32(0x985dcc)
        if y > last_year:
            last_year = y
            rec["events"].append(f"year {y} landed (cur={cur})")
            s = snapshot(); s["point"] = "after-year-advance"
            rounds.append(s); rec["rounds"] = rounds
            json.dump(rec, open(f"{EVID}/{tag}_drive.json", "w"), indent=1)
            print(f"[round {len(rounds)}]", json.dumps(brief(s)), flush=True)
            if len(rounds) >= a.rounds:
                finish(f"{a.rounds} rounds", gproc, logpath)
        if time.time() - last_svc > 5:
            last_svc = time.time()
            png = P.freeze(f"{tag}_svc")
            words = P.ocr(png)
            body = re.sub(r"[^a-z]", "", " ".join(w[0] for w in words).lower())
            if "wanttoendtheturn" in body or "havenotyetmoved" in body:
                # service_pane's priority-2.5 ENDTURN branch handles both routes
                # (Cancel-word anchor, and the colour route for the frame where the
                # selected Cancel row is unreadable -- the m48a stall).
                service_pane(png, words, body, P.classify(words, png=png), rec,
                             "svc-endturn", bar=find_ok_bar(png))
                rec["svc_endturn_panes"] = rec.get("svc_endturn_panes", 0) + 1
                continue
            if hud_up(png):
                bar = find_ok_bar(png)
                if bar is not None:
                    service_pane(png, words, body, P.classify(words, png=png), rec,
                                 "svc", bar=bar)
                elif cur == 3 and time.time() - last_year_t > 12:
                    P.click(P.TURN_BTN)
                    rec["svc_hud_clicks"] = rec.get("svc_hud_clicks", 0) + 1
                    last_year_t = time.time()
            else:
                kw = ("enterfornextturn" in body or "nounitsneedneworders" in body
                      or "reallywanttoquit" in body or "oops" in body
                      or "abstain" in body or "convenes" in body or "agenda" in body
                      or "measure" in body or "ecologist" in body
                      or "mindworm" in body or "breakthrough" in body)
                bar = find_ok_bar(png)
                # A mid-band OK bar (news / councillor popup, m48c) is invisible to
                # find_ok_bar's default 430-520 band AND to the keyword list, so the
                # old gate fell through to Escape -- which does nothing to a modal
                # picture pane -- and the run stalled 6 min at cur=0.  Let it through
                # to service_pane, whose dialog branch now clicks the colour-found bar.
                mid = bar is None and find_ok_bar(png, band=(240, 150, 560, 430)) is not None
                if bar is not None or kw or mid:
                    service_pane(png, words, body, P.classify(words, png=png), rec,
                                 "svc", bar=bar)
                else:
                    P.key("Escape")
                    rec["svc_escapes"] = rec.get("svc_escapes", 0) + 1
        time.sleep(0.7)
    finish("budget", gproc, logpath)


if __name__ == "__main__":
    main()
