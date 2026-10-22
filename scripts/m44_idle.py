#!/usr/bin/env python3
"""M44: economy-rate idle run — advance N rounds with ZERO player orders and
snapshot, at each round's start-of-our-turn point (cur flips to 3 after the new
year lands = all AI phases + refreshes done):
  * faction energy  (0x94d650 + player*0x82f*4)  for all live players
  * per-owner base totals: count / minerals(+64 u32) / pop(+6)  (owner = +4 byte = player index, M43)
  * our unit count (attrition watch)
Quantifies income vs upkeep (feeds C3; when does the 25-cost elev-6 raise become payable?).
No gdb, no orders — pure turn-advancing + reads.

Pane servicing is COLOUR-based, not vocabulary-based: the bottom-centre message-bar OK
bar (Council PROPOSAL / governor-election / 'X ELECTED' panes) is unreadable to tesseract,
so find_ok_bar() finds the wide blue bar and clicks it. Attempts m44a/b/c died on the old
vocabulary preflight assert with the governor-election pane up (year stuck 2303).

Usage: python3 scripts/m44_idle.py [--tag m44a] [--rounds 12] [--budget 1800]
"""
import argparse, json, os, re, shutil, struct, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P

EVID = P.EVID


def dismiss_reallyquit(words):
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


def find_ok_bar(png, band=(240, 430, 560, 520), min_h=8):
    """Locate the bottom-centre message-bar OK bar by COLOUR, not OCR.

    Tesseract cannot read the label on the blue bar (live: it OCRs 'PROPOSAL /
    ELECT PLANETARY GOVERNOR / Yang: 120 Lal: 94' and returns nothing for the bar),
    so vocabulary servicing can never escape a Council pane — that is what killed
    attempts m44a/b/c. Calibrated live 2026-10-22 on the governor-election pane:
    contiguous blue rows y 488-507, x 268-532, sample rgb (103,91,181).
    Returns the bar centre (x, y) or None. The band stops at y 520 because the HUD
    chrome draws a 1-px blue line at y 526 in EVERY frame (bare HUD included); a
    >=min_h-tall bar is the pane's bottom strip.
    """
    from PIL import Image
    px = Image.open(png).convert("RGB").load()
    x0, y0, x1, y1 = band

    def blue(x, y):
        r, g, b = px[x, y]
        return b > r + 25 and b > 60

    rows, y = [], y1 - 1
    while y >= y0:                       # lowest contiguous blue band = the OK bar
        if sum(1 for x in range(x0, x1, 2) if blue(x, y)) >= 60:
            rows.append(y)
        elif rows:
            break
        y -= 1
    if len(rows) < min_h:
        return None
    xs = [x for yy in rows for x in range(x0, x1, 2) if blue(x, yy)]
    return ((min(xs) + max(xs)) // 2, sum(rows) // len(rows))


def rightmost_blue_run(png, band=(240, 150, 560, 430)):
    """Centre of the RIGHTMOST contiguous blue run inside the lowest blue band of
    `band`.  find_ok_bar returns the centre of the WHOLE blue row set, which lands in
    the GAP when a pane shows two side-by-side buttons -- live-caught on the
    OPERATIONS DIRECTOR "The minerals output of Climactic Research is not sufficient
    to support Scout Patrol unit. The unit has been disbanded." pane, whose bottom
    row is [Don't Show As Popup] | [OK] (centres ~(247,310) and ~(553,310)); clicking
    the bar centre (400,310) hits the gap and the modal never closes.
    """
    from PIL import Image          # local import, same as find_ok_bar
    from collections import Counter
    x0, y0, x1, y1 = band
    im = Image.open(png).convert('RGB')
    px = im.load()

    def blue(x, y):
        r, g, b = px[x, y]
        return b > r + 25 and b > 60

    def flat(y):
        """A pane bar/button row is a FLAT fill: >=100 of the 160 sampled x are blue
        and >=85 % of those share one rgb (tolerance 8).  The map's ocean is patchy
        and gradient-shaded, so it fails both -- without this test the bare HUD's
        water rows read as an OK bar and the runner clicks the map forever (m48c)."""
        cols = [px[x, y] for x in range(x0, x1, 2) if blue(x, y)]
        if len(cols) < 100:
            return False
        top, n = Counter(cols).most_common(1)[0]
        near = sum(1 for c in cols if abs(c[0] - top[0]) <= 8
                   and abs(c[1] - top[1]) <= 8 and abs(c[2] - top[2]) <= 8)
        return near >= 0.85 * len(cols)

    rows = [y for y in range(y0, y1) if flat(y)]
    if not rows:
        return None
    # lowest contiguous group of blue rows = the button/bar row
    grp = [rows[-1]]
    for y in reversed(rows[:-1]):
        if grp[-1] - y <= 2:
            grp.append(y)
        else:
            break
    hot = [x for x in range(x0, x1) if any(blue(x, y) for y in grp)]
    if not hot:
        return None
    # last run of consecutive xs
    start = hot[-1]
    for x in reversed(hot):
        if start - x > 3:
            break
        start = x
    end = hot[-1]
    return ((start + end) // 2, sum(grp) // len(grp))


def service_pane(png, words, body, kind, rec, where, bar=None):
    """One servicing step, in strict priority order. Returns True if acted.

    1. REALLYQUIT (oops row)  2. ENDOFTURN1 -> Return  3. message-bar OK bar
    (colour-detected: covers PROPOSAL / vote bars / 'X ELECTED' / any bottom-centre
    caption pane)  4. ABSTAIN button (live ballot, minimal state change)
    5. confirm pane  6. dialog/unknown -> Return.
    """
    strip = lambda t: t.lower().strip(".,!|_*— ")
    if "oops" in body or "reallywanttoquit" in body:
        if dismiss_reallyquit(words):
            rec["events"].append(f"{where}: dismissed REALLYQUIT"); return True
    if "enterfornextturn" in body or "nounitsneedneworders" in body:
        P.key("Return"); rec["events"].append(f"{where}: ENDOFTURN1 -> Return"); return True
    if "wanttoendtheturn" in body or "havenotyetmoved" in body:
        # OPERATIONS DIRECTOR end-turn confirm (m46a-d blocker): Script pane with
        # option rows Cancel.(default)/Yes,end the turn. + blue OK bar at y~215-350
        # (y drifts with pane stacking) — outside find_ok_bar's 430-520 band, and
        # Return = OK with CANCEL selected, so Return can never end the turn.
        # Live-measured offsets from the Cancel word centre: +24 -> Yes row, +49 -> OK bar.
        #   Route A (m46 calibration): Cancel word centre (cx,cy) -> +24 = Yes row,
        #     +49 = OK bar.  FAILS when Cancel is the SELECTED row: the selection
        #     highlight (fill 120,164,212, dark text) is UNREADABLE to tesseract, so
        #     a freshly popped pane -- whose default selection IS Cancel -- yields no
        #     "cancel" word and the run spins (m48a: 4 min, 0 rounds).
        #   Route B (colour-only, calibrated on evidence/m48a_diag.png 2026-10-22):
        #     find the OK bar with find_ok_bar in band (240,150,560,430).  The Yes row
        #     (fill 103,91,181) is separated from the bar (fill 28,80,99) by a non-blue
        #     gutter at y~207-213, so the lowest contiguous blue band IS the bar; click
        #     (bx, by-26) to select "Yes, end the turn.", wait >=1.2 s, click the bar.
        cw = P.find(words, ["cancel"])
        if cw:
            P.click((cw[0], cw[1] + 24)); time.sleep(1.2)
            P.click((cw[0], cw[1] + 49)); time.sleep(0.9)
            rec["events"].append(f"{where}: ENDTURN confirm -> Yes+OK at ({cw[0]},{cw[1]})")
            return True
        ob = find_ok_bar(png, band=(240, 150, 560, 430))
        if ob:
            P.click((ob[0], ob[1] - 26)); time.sleep(1.3)
            P.click(ob); time.sleep(0.9)
            rec["events"].append(f"{where}: ENDTURN confirm by COLOUR -> "
                                 f"Yes@({ob[0]},{ob[1] - 26}) OK@{ob}")
            return True
    if bar is None:
        bar = find_ok_bar(png)
    if bar:
        P.click(bar); time.sleep(1.5)
        rec["events"].append(f"{where}: clicked message-bar OK bar {bar}"); return True
    ab = next((w for w in words if strip(w[0]) == "abstain"), None)
    if ab:
        P.click((int(ab[1]), int(ab[2]))); time.sleep(1.6)
        rec["events"].append(f"{where}: clicked ABSTAIN ({int(ab[1])},{int(ab[2])})"); return True
    if kind == "confirm":
        P.answer_confirm(words); rec["events"].append(f"{where}: answered confirm pane"); return True
    if kind == "base":
        # The BASE screen (classify keys: governor/nutrients/conquer/discover) is what
        # BUILD BASE leaves open after founding. It has no bar in the 430-520 band (its
        # RENAMEd/OK row is at y ~365), is not a confirm, and is NOT covered by the
        # dialog/unknown default below -> service_pane used to return False and the
        # whole run spun (m45b: 15 min, 1 round). One Escape closes it to the HUD (M26).
        P.key("Escape"); rec["events"].append(f"{where}: Escape on base screen"); return True
    if kind in ("dialog", "unknown"):
        # Mid-band single OK bar = SMAC news / councillor popups.  m48c stalled 6 min
        # at cur=0 on "SECURITY CHIEF: Our Scout Patrol unit has performed admirably,
        # and has now achieved Hardened status." -- a picture pane whose only control
        # is a blue OK bar at y~253-273 (centre (400,262)), i.e. inside band
        # (240,150,560,430) and OUTSIDE the default 430-520 band, so the priority-3
        # branch missed it and Return did nothing: the popup is MODAL (the turn cycle
        # freezes, the round never closes, the per-base economy pipeline never runs).
        # Such panes have no option rows, so clicking the colour-found bar is the whole
        # fix, and strictly better than the Return fallback it replaces.
        ob = rightmost_blue_run(png, band=(240, 150, 560, 430))
        if ob:
            P.click(ob); time.sleep(1.0)
            rec["events"].append(f"{where}: NEWS/mid-band OK by COLOUR (rightmost run) at {ob}")
            return True
        P.key("Return"); rec["events"].append(f"{where}: Return on {kind} pane"); return True
    return False


def hud_econ(png, tag):
    """Best-effort side-read of the HUD economy panel (x 262-394, y 425-497):
    Commerce Income / Gross Income / Total Costs / NET INCOME rows. OCR glues the
    digit to '/turn' ('IncomeOiturn'), so this corroborates the memory deltas, it
    does not replace them."""
    try:
        return [w[0] for w in P.ocr_crop(png, (262, 425, 132, 72), f"{tag}_econ")]
    except Exception as e:
        return [f"ERR {type(e).__name__}: {e}"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m44a")
    ap.add_argument("--rounds", type=int, default=12)
    ap.add_argument("--budget", type=float, default=1800.0)
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

    def snapshot():
        nb = u32(0x985af4)
        blob = rd(0x95da10, nb * 304)
        owners = {}
        for i in range(nb):
            r = blob[i * 304:(i + 1) * 304]
            o = r[4]
            d = owners.setdefault(o, {"bases": 0, "minerals": 0, "pop": 0})
            d["bases"] += 1
            d["minerals"] += struct.unpack("<I", r[64:68])[0]
            d["pop"] += r[6]
        ub = rd(0x933278, 300 * 52)
        nmine = sum(1 for i in range(300)
                    if ub[i * 52 + 14] == 3 and struct.unpack("<H", ub[i * 52:i * 52 + 2])[0] != 0xffff)
        energy = {p: i32(0x94d650 + p * 0x82f * 4) for p in range(8) if p in owners or p == 3}
        return dict(year=u32(0x985b00), cur=u32(0x985dcc), nmine=nmine,
                    energy=energy, owners=owners)

    # --- preflight screen: SERVICE any modal first (diplomacy messages arrive
    # unserviced between runs; a dialog must be answered, not asserted away) ---
    png = P.freeze(f"{tag}_pre"); shutil.copy(png, f"{EVID}/{tag}_pre.png")
    words = P.ocr(png)
    body = re.sub(r"[^a-z]", "", " ".join(w for w, *_ in words).lower())
    pane = "enterfornextturn" in body or "nounitsneedneworders" in body
    kind = P.classify(words, png=png)
    our_turn = u32(0x985dcc) == 3
    t0 = time.time()
    while not (pane or kind == "hud" or our_turn) and time.time() - t0 < 240:
        service_pane(png, words, body, kind, rec, "preflight")
        time.sleep(2.5)
        P.focus()
        png = P.freeze(f"{tag}_pre"); shutil.copy(png, f"{EVID}/{tag}_pre.png")
        words = P.ocr(png)
        body = re.sub(r"[^a-z]", "", " ".join(w for w, *_ in words).lower())
        pane = "enterfornextturn" in body or "nounitsneedneworders" in body
        kind = P.classify(words, png=png)
        our_turn = u32(0x985dcc) == 3
    rec["events"].append(f"preflight kind={kind} pane_end={pane} our_turn={our_turn}")
    if not (pane or kind == "hud" or our_turn):
        # NOT fatal (m44a/b/c died here on an assert while a Council pane sat up):
        # the svc loop below services panes too, so keep going and let it try.
        rec["events"].append(f"preflight unresolved kind={kind} body={body[:120]!r} — continuing")

    P.focus()
    if pane:
        P.key("Return"); rec["events"].append("Return on ENDOFTURN1 (preflight)")
        time.sleep(2)

    snap0 = snapshot()
    rec["snap0"] = snap0
    print("[snap0]", json.dumps(snap0), flush=True)

    def finish(reason):
        rec["reason"] = reason
        rec["final"] = snapshot()
        png = P.freeze(f"{tag}_post"); shutil.copy(png, f"{EVID}/{tag}_post.png")
        json.dump(rec, open(f"{EVID}/{tag}_idle.json", "w"), indent=1)
        # deltas
        if rec.get("rounds"):
            e0 = rec["rounds"][0]["energy"]; e1 = rec["rounds"][-1]["energy"]
            o0 = rec["rounds"][0]["owners"]; o1 = rec["rounds"][-1]["owners"]
            n = len(rec["rounds"]) - 1
            rec["deltas_per_round"] = {
                "rounds": n,
                "energy3": (e1.get(3, 0) - e0.get(3, 0)) / n if n else 0,
                "energy_by_player": {p: (e1.get(p, 0) - e0.get(p, 0)) / n for p in set(e0) | set(e1)} if n else {},
                "minerals_by_owner": {o: (o1.get(o, {}).get("minerals", 0) - o0.get(o, {}).get("minerals", 0)) / n
                                      for o in set(o0) | set(o1)} if n else {},
                "bases_by_owner_end": {o: o1.get(o, {}).get("bases", 0) for o in sorted(set(o0) | set(o1))},
            }
            json.dump(rec, open(f"{EVID}/{tag}_idle.json", "w"), indent=1)
        print(json.dumps({"reason": reason, "deltas": rec.get("deltas_per_round")}, indent=1))
        print("saved:", f"{EVID}/{tag}_idle.json")
        sys.exit(0)

    deadline = time.time() + a.budget
    last_year = snap0["year"]
    last_ocr = 0.0
    last_year_t = time.time()
    rounds = []
    while time.time() < deadline:
        y, cur = u32(0x985b00), u32(0x985dcc)
        if y > last_year:
            last_year = y
            last_year_t = time.time()
            rec["events"].append(f"year {y} landed (cur={cur})")
        # snapshot point: start of OUR turn in a new year (all AI phases done)
        if y > last_year - 1 and cur == 3 and (not rounds or y > rounds[-1]["year"]):
            s = snapshot(); s["point"] = "start-of-our-turn"
            s["hud_econ_ocr"] = hud_econ(P.freeze(f"{tag}_svc"), tag)
            rounds.append(s); rec["rounds"] = rounds
            json.dump(rec, open(f"{EVID}/{tag}_idle.json", "w"), indent=1)   # survives a kill
            print(f"[round {len(rounds)}]", json.dumps(s), flush=True)
            if len(rounds) >= a.rounds:
                finish(f"{a.rounds} rounds")
        if time.time() - last_ocr > 6:
            last_ocr = time.time()
            png = P.freeze(f"{tag}_svc")
            words = P.ocr(png)
            kind = P.classify(words, png=png)
            body = re.sub(r"[^a-z]", "", " ".join(w[0] for w in words).lower())
            cur = u32(0x985dcc)
            bar = find_ok_bar(png)
            if kind == "hud" and cur == 3 and bar is None and time.time() - last_year_t > 15:
                btn = P.find(words, ["complete"])
                P.click(btn[:2] if btn else P.TURN_BTN)
                rec["svc_hud_clicks"] = rec.get("svc_hud_clicks", 0) + 1
            elif service_pane(png, words, body, kind, rec, "svc", bar=bar):
                pass
            elif kind == "unknown":
                png2 = P.freeze(f"{tag}_svc2")
                w2 = P.ocr(png2)
                b2 = re.sub(r"[^a-z]", "", " ".join(w[0] for w in w2).lower())
                if "oops" in b2 or "reallywanttoquit" in b2:
                    dismiss_reallyquit(w2)
                elif P.classify(w2, png=png2) == "unknown" and \
                        P.region_colors(png2, (180, 60, 620, 200)) < 130:
                    P.key("Escape")
        time.sleep(0.7)
    finish("budget")


if __name__ == "__main__":
    main()
