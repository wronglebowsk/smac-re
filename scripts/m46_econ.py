#!/usr/bin/env python3
"""M46 option 1: find the income/cost source values in memory and correlate
them against the measured per-round energy deltas.

Static footing this run (see turn_driver.md §M46):
  * FUN_00445900(player,0) is the economy aggregator that recomputes scratch
    globals on every HUD/pane redraw:
      0x745734 = SUM over our bases of base+0xfc            (HUD "gross" row)
      0x7457dc = that - SUM item upkeep FUN_004f4760 +/- trade  (HUD "net" row)
      0x7457d4 = trade net only
      0x744f28 = total item upkeep;  0x744f2c[base] = per-base upkeep
      0x745738[39] = per-item-type counts; 0x74572c = food*mult, 0x745730 = need%
      (scratch describes the LAST player passed to 445900 = us when our HUD is up)
  * HUD "Total Costs" row = 0x7457dc - 0x745734 (FUN_0045a920 case 1).
  * FUN_004eaa10 splits each base's production (base+0xd4 after consumption)
    into four buckets by the FACTION land ratios (faction+0x104/+0x108):
      base+0x100 = (ratio_a * prod + 4)/10
      base+0xfc  = min(prod - 0x100bucket, ((10-a-b)*prod+4)/10)   <- 445900's "income"
      base+0x104 = leftover (445900 treats as FOOD: 74572c += it)
      base+0x108 = ((9-a-b)*prod+4)/10 capped
  * item upkeep = *(int*)(0x984d48 + item*0x30), zeroed if the item is on the
    player's disabled list (0x927ac0 + p*0x167, rec type 2); item 27 special.
  * HUD energy-delta readouts elsewhere = energy - faction+4 (FUN_00416730 et al.),
    i.e. faction+4 looks like a start-of-round energy snapshot (verify live).

This runner snapshots at each start-of-our-turn (same point as m44_idle):
  full 2111-int faction records for every live player (diff => income/cost fields),
  the scratch globals above, our bases' production buckets + accumulators,
  energy for all players, our unit count, and the HUD econ OCR row.
Read-only: no pokes, no gdb (TracerPid must be 0).

Usage: python3 scripts/m46_econ.py --tag m46a --rounds 4 --budget 600
"""
import argparse, json, os, re, shutil, struct, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P
from PIL import Image
from m44_idle import service_pane, find_ok_bar, hud_econ, dismiss_reallyquit

EVID = P.EVID


def hud_up(png):
    """True when the TURN COMPLETE button fill is on screen.

    The button is bright orange (228,104,24) at box (600,395,800,425); the base
    screen's FORCES SUPPORTED panel occupies the same box with zero orange.
    OCR of the busy HUD garbles too badly to positively ID the HUD, and classify()
    misreads the hover-info panel as dialog — this pixel test is the only reliable
    check. A base screen left open silently blocks turn advance forever.
    """
    im = Image.open(png).convert("RGB").crop((600, 395, 800, 425))
    n = sum(1 for r, g, b in im.getdata() if r > 180 and 60 <= g <= 160 and b < 80)
    return n > 300

FAC_BASE, FAC_STRIDE, FAC_INTS = 0x94d650, 0x20bc, 2111
BASE_ARR, BASE_STRIDE = 0x95da10, 0x130


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m46a")
    ap.add_argument("--rounds", type=int, default=4)
    ap.add_argument("--budget", type=float, default=600.0)
    a = ap.parse_args()
    tag = a.tag
    rec = {"tag": tag, "t": time.strftime("%F %T"), "events": []}

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

    def i32(addr):
        return struct.unpack("<i", rd(addr, 4))[0]

    def ints(addr, n):
        return list(struct.unpack(f"<{n}i", rd(addr, 4 * n)))

    def snapshot():
        nb = u32(0x985af4)
        live = set()
        blob = rd(BASE_ARR, nb * BASE_STRIDE)
        bases = []
        for i in range(nb):
            r = blob[i * BASE_STRIDE:(i + 1) * BASE_STRIDE]
            g = lambda off: struct.unpack("<i", r[off:off + 4])[0]
            o = r[4]
            live.add(o)
            d = dict(idx=i, owner=o, x=g(0), y=g(2), pop=r[6], growth=r[7],
                     minerals=g(64), c4=g(0xc4), d4=g(0xd4), e4=g(0xe4),
                     f4=g(0xf4), prod_energy=g(0x100), prod_fc=g(0xfc),
                     prod_104=g(0x104), prod_108=g(0x108))
            if o == 3:
                d["name"] = r[19:39].split(b"\0")[0].decode("latin1", "replace")
                d["full"] = list(struct.unpack("<76i", r))
            bases.append(d)
        live.add(3)
        live = sorted(l for l in live if l < 8)
        fac = {p: ints(FAC_BASE + p * FAC_STRIDE, FAC_INTS) for p in live}
        ub = rd(0x933278, 300 * 52)
        nmine = sum(1 for i in range(300)
                    if ub[i * 52 + 14] == 3 and struct.unpack("<H", ub[i * 52:i * 52 + 2])[0] != 0xffff)
        scratch = {
            "net_7457dc": i32(0x7457dc), "gross_745734": i32(0x745734),
            "trade_7457d4": i32(0x7457d4), "upkeep_744f28": i32(0x744f28),
            "food_74572c": i32(0x74572c), "needpct_745730": i32(0x745730),
            "item_counts_745738": ints(0x745738, 39),
            "per_base_upkeep_744f2c": ints(0x744f2c, min(nb, 120)),
        }
        return dict(year=u32(0x985b00), turn=u32(0x985afc), cur=u32(0x985dcc),
                    n_bases=nb, nmine=nmine, scratch=scratch,
                    fac=fac, bases=bases)

    def brief(s):
        """compact per-round line (full fac records live in rec['rounds'] JSON)"""
        e = {p: s["fac"][p][0] for p in s["fac"]}
        ours = [b for b in s["bases"] if b["owner"] == 3]
        return dict(year=s["year"], turn=s["turn"], cur=s["cur"], nmine=s["nmine"],
                    energy=e,
                    our_bases=[{k: b[k] for k in ("idx", "pop", "minerals", "c4", "d4",
                                                  "f4", "prod_energy", "prod_fc",
                                                  "prod_104", "prod_108")} for b in ours],
                    scratch={k: v for k, v in s["scratch"].items()
                             if not isinstance(v, list)})

    # --- preflight: service any modal first (same rules as m44_idle) ---
    png = P.freeze(f"{tag}_pre"); shutil.copy(png, f"{EVID}/{tag}_pre.png")
    words = P.ocr(png)
    body = re.sub(r"[^a-z]", "", " ".join(w for w, *_ in words).lower())
    pane = "enterfornextturn" in body or "nounitsneedneworders" in body
    kind = P.classify(words, png=png)
    t0 = time.time()
    # exit ONLY on a clean HUD (or the end-turn pane, which we Return away below).
    # Never exit on our_turn alone: a base screen left open also has cur==3 and
    # silently blocks the turn forever (m46a/m46b died exactly this way).
    while not pane and not hud_up(png) and time.time() - t0 < 240:
        service_pane(png, words, body, kind, rec, "preflight")
        time.sleep(2.5)
        P.focus()
        png = P.freeze(f"{tag}_pre"); shutil.copy(png, f"{EVID}/{tag}_pre.png")
        words = P.ocr(png)
        body = re.sub(r"[^a-z]", "", " ".join(w for w, *_ in words).lower())
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

    def finish(reason):
        rec["reason"] = reason
        rec["final"] = brief(snapshot())
        png = P.freeze(f"{tag}_post"); shutil.copy(png, f"{EVID}/{tag}_post.png")
        json.dump(rec, open(f"{EVID}/{tag}_econ.json", "w"), indent=1)
        print(json.dumps({"reason": reason, "rounds": len(rec.get("rounds", []))}))
        print("saved:", f"{EVID}/{tag}_econ.json")
        sys.exit(0)

    deadline = time.time() + a.budget
    last_year = snap0["year"]
    last_ocr = 0.0
    last_svc = 0.0
    last_year_t = time.time()
    rounds = []
    while time.time() < deadline:
        y, cur = u32(0x985b00), u32(0x985dcc)
        if y > last_year:
            last_year = y
            last_year_t = time.time()
            rec["events"].append(f"year {y} landed (cur={cur})")
        if cur == 3 and (not rounds or y > rounds[-1]["year"]):
            s = snapshot(); s["point"] = "start-of-our-turn"
            s["hud_econ_ocr"] = hud_econ(P.freeze(f"{tag}_svc"), tag)
            rounds.append(s); rec["rounds"] = rounds
            json.dump(rec, open(f"{EVID}/{tag}_econ.json", "w"), indent=1)
            print(f"[round {len(rounds)}]", json.dumps(brief(s)), flush=True)
            if len(rounds) >= a.rounds:
                finish(f"{a.rounds} rounds")
        if time.time() - last_svc > 4:
            last_svc = time.time()
            png = P.freeze(f"{tag}_svc")
            cur = u32(0x985dcc)
            words = P.ocr(png)
            body = re.sub(r"[^a-z]", "", " ".join(w[0] for w in words).lower())
            # THE blocker (m46a-d all died on it): clicking TURN COMPLETE with idle
            # units pops the Script pane "OPERATIONS DIRECTOR — some of our units
            # have not yet moved this turn… DO YOU REALLY WANT TO END THE TURN NOW?"
            # with option rows Cancel.(default)/Yes,end the turn. + a blue OK bar
            # at y~215-350 (pane y drifts) — OUTSIDE find_ok_bar's 430-520 band, and
            # Return presses OK with CANCEL selected, so it never ends the turn.
            # Servicing (offsets measured live, both frames): Cancel word center
            # (cx,cy) -> click (cx, cy+24) selects "Yes, end the turn.", click
            # (cx, cy+49) hits the OK bar. The orange TURN COMPLETE button stays
            # visible behind this pane, so hud_up must NEVER be consulted first.
            if "wanttoendtheturn" in body or "havenotyetmoved" in body:
                cw = P.find(words, ["cancel"])
                if cw:
                    cx, cy = cw[0], cw[1]
                    P.click((cx, cy + 24)); time.sleep(0.9)
                    P.click((cx, cy + 49)); time.sleep(0.9)
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
            else:
                pane_kw = ("enterfornextturn" in body or "nounitsneedneworders" in body
                           or "reallywanttoquit" in body or "oops" in body)
                bar = find_ok_bar(png)
                if bar is not None or pane_kw:
                    service_pane(png, words, body, P.classify(words, png=png), rec,
                                 "svc", bar=bar)
                else:
                    # base screen or unlabelled pane over the map: Escape closes it
                    # (safe: on confirm dialogs Escape = cancel = No).
                    P.key("Escape")
                    rec["svc_escapes"] = rec.get("svc_escapes", 0) + 1
        time.sleep(0.7)
    finish("budget")


if __name__ == "__main__":
    main()
