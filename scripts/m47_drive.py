#!/usr/bin/env python3
"""M47 driver v2: end our turn and let the round resolve while gdb watchpoints
(scripts/m47_watch2.gdb) are armed on our base's mineral accumulator (known
writer, validation), base+0x7c..0x7f (the transient income field at +0x7e) and
our faction's +4 spending ledger.

Pane rules learned the hard way this session:
  * ADVISOR advisories ("PLANETARY ECOLOGIST / Mindworm boil spotted") block
    input but classify() still says "hud" (HUD visible behind the portrait):
    press Return.
  * Council: "PROTOCOL DIRECTOR ... convenes the Planetary Council / Agenda:"
    needs Return; the ballot ("PROPOSAL ... YEA: n NAY: n / ABSTAIN") needs a
    click on ABSTAIN (or the OK bar); the result page ("MEASURE FAILS/PASSES")
    needs Return.
  * "Some of our units have not yet moved" (OPERATIONS DIRECTOR) is served by
    m44_idle.service_pane (Cancel centre +24 then +49).

Usage: python3 scripts/m47_drive.py --tag m47c --budget 420
"""
import argparse, json, os, re, struct, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P
from m44_idle import service_pane, find_ok_bar


def squash(words):
    return re.sub(r"[^a-z]", "", " ".join(w[0] for w in words).lower())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m47c")
    ap.add_argument("--budget", type=float, default=420.0)
    a = ap.parse_args()

    pid = int(subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True,
                             text=True).stdout.split()[0])
    fh = open(f"/proc/{pid}/mem", "rb", 0)

    def u32(addr):
        fh.seek(addr)
        return int.from_bytes(fh.read(4), "little")

    year = u32(0x985b00)
    rec = {"tag": a.tag, "t0": time.strftime("%F %T"), "year0": year, "events": []}
    print(f"[start] year={year} cur={u32(0x985dcc)}", flush=True)

    t0 = time.time()
    last_click = 0.0
    clicks = returns = 0
    while time.time() - t0 < a.budget:
        if u32(0x985b00) > year:
            break
        P.focus()
        png = P.freeze(f"{a.tag}_d")
        words = P.ocr(png)
        body = squash(words)
        kind = P.classify(words, png=png)
        bar = find_ok_bar(png)

        if "wanttoendtheturn" in body or "havenotyetmoved" in body:
            service_pane(png, words, body, kind, rec, "drive", bar=bar)
            time.sleep(1.5)
            continue

        if "abstain" in body and ("proposal" in body or "council" in body):
            hit = P.find(words, ["abstain"])
            if hit:
                P.click(hit[:2])
                clicks += 1
                rec["events"].append("click ABSTAIN")
                time.sleep(2)
                continue

        if "measure" in body or "convenes" in body or "agenda" in body:
            P.key("Return")
            returns += 1
            rec["events"].append(f"Return on council page '{body[:40]}'")
            time.sleep(2)
            continue

        if kind == "hud":
            if any(k in body for k in ("ecologist", "mindworm", "spotted",
                                       "breakthrough", "discovery", "advisor")):
                P.key("Return")
                returns += 1
                rec["events"].append(f"Return on advisory '{body[:40]}'")
                time.sleep(1.5)
                P.click(P.TURN_BTN)
                clicks += 1
                last_click = time.time()
                continue
            if time.time() - last_click > 8.0:
                P.click(P.TURN_BTN)
                clicks += 1
                last_click = time.time()
                rec["events"].append(f"click TURN_BTN cur={u32(0x985dcc)}")
                for _ in range(10):
                    time.sleep(1)
                    if u32(0x985b00) > year:
                        break
                continue
        else:
            if not service_pane(png, words, body, kind, rec, "drive", bar=bar):
                P.key("Return")
                returns += 1
                rec["events"].append(f"Return on {kind} '{body[:40]}'")
                time.sleep(1.5)
                continue
            time.sleep(1.5)
            continue
        time.sleep(1)

    rec["clicks"], rec["returns"] = clicks, returns
    rec["year_end"] = u32(0x985b00)
    rec["secs"] = round(time.time() - t0, 1)
    json.dump(rec, open(f"evidence/{a.tag}_drive.json", "w"), indent=1)
    print(json.dumps({k: rec[k] for k in ("year0", "year_end", "clicks", "returns", "secs")}))


if __name__ == "__main__":
    main()
