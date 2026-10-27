#!/usr/bin/env python3
"""M62 — the READINESS ORACLE: can this box produce a positive prediction at all?

The M61 session lost roughly half its budget to two states that no instrument named:
an Operations Director dialog sitting over the BUILD pane (every UI click swallowed), and
both our bases at minerals 0 / credit 0 (the income add is gated `d0 > 0`, so storage can
never accrue again). Both are decidable from memory in one read. This script decides them.

READ-ONLY. It never pokes, never clicks, never writes `evidence/`.

Exit 0  = at least one of OUR bases can carry the UI-queued acceptance:
           pending > 0            (the run is filled by the GAME's BUILD UI)
           minerals < price       (the completion is NOT armed at start)
           minerals + credit >= price   (an arrival is inside the first window)  OR
           credit > 0             (storage still accrues, so the gate is reached mid-run)
Exit 1  = blocked; prints the single cheapest fix, not a list of everything wrong.

Why each condition is what it is (M56/M59/M61, all measured):
  * price   = FUN_004e40a0(owner,1,-1) x type_cost, gated at 0x4efa5e against [base+0x40]
  * credit  = base+0xd0, recomputed every visit; the add at 0x4ef7f6 is gated d0 >= 0, so a
              base with d0 <= 0 can never reach the gate by waiting
  * pending = gates only the POP, but the acceptance insists the queue came from the UI, so a
              base with pending == 0 cannot be the run's target
"""
import argparse, json, os, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m55_boundary as M
import m56_build as B

PLAYER_G = 0x91B5B4
BUDGET_FAIL_MB = 29.0          # evidence.py FAILs at 30; leave a run's worth of headroom


def gdb_count():
    try:
        out = subprocess.run(["pgrep", "-x", "gdb"], capture_output=True, text=True).stdout
    except OSError:
        return -1
    return len(out.split())


def look(tag="acceptready"):
    """One freeze: classify() plus the HUD status bar, from a single OCR pass.

    Returns (class, bar_dict, text_head). classify() is left completely untouched —
    the driver still sees exactly the classes it saw before; the status bar is only ever
    consulted here, by the readiness oracle, to decide whether an `unknown` frame is really
    the plain HUD.
    """
    import smac_play as sp
    png = sp.freeze(tag)
    words = sp.ocr_fast(png)
    kind = sp.classify(words, sp.region_colors(png), png)
    bar = sp.hud_status_bar(words)
    txt = " ".join(t[0] if isinstance(t, tuple) else t for t in words)
    return kind, bar, txt[:120]


def verdict(looks, confirm=2):
    """Pure: what N looks at the same screen mean. Each look is (class, bar_fired).

    A modal is STABLE — it sits there until something answers it — so a named modal class
    in ANY look decides the screen. The flake this exists for is the other direction: the
    plain HUD read `unknown` 14 times in a row in session 104 and 5 of 8 freezes today,
    because classify()'s only HUD evidence (the TURN COMPLETE row) fragments on an
    animating map. So `unknown` is not treated as a modal: it is re-frozen until the HUD's
    own status bar lands `confirm` times, and only a screen that never shows the bar and
    never names a modal is called `unknown`.
    """
    hits = 0
    for k, (kind, bar) in enumerate(looks):
        if kind == "hud":
            return "hud", f"look {k}: classify() == hud (the TURN COMPLETE row read)"
        if kind != "unknown":
            return kind, (f"look {k}: classify() == {kind!r} — a named modal swallows every "
                          f"click and every turn-end key")
        if bar:
            hits += 1
            if hits >= confirm:
                return "hud", (f"look {k}: classify() == unknown, but the HUD's bottom status "
                               f"bar read in {hits} of {k + 1} look(s) — the same chrome the "
                               f"button row is part of")
    return "unknown", (f"no verdict in {len(looks)} look(s): the button row never read and "
                       f"the status bar fired {hits} time(s)")


def screen_class(samples=4, confirm=2, gap=0.8):
    """What is on screen right now: ('hud'|'dialog'|'base'|'unknown', why).

    A modal swallows EVERY click and every turn-end key, so it is checked first: in M61 an
    Operations Director "unit has been disbanded" dialog sat over the BUILD pane and two
    UI-enqueue attempts silently clicked into it. Return clears a dialog's default row;
    Escape closes a pane (Escape on the bare map raises the quit prompt — never OK it).

    One OCR pass is NOT a reliable screen read on this box (see verdict()), so this re-freezes
    until a verdict lands: the common case (a plain HUD) exits on look 0 or 1.
    """
    looks = []
    last_bar = None
    for k in range(max(1, samples)):
        try:
            kind, bar, txt = look()
        except Exception as e:                                # no display / OCR down
            return f"unknown ({type(e).__name__})", ""
        looks.append((kind, bool(bar["fire"])))
        last_bar = (bar, txt)
        if verdict(looks, confirm)[0] != "unknown":
            break
        if k + 1 < samples:
            time.sleep(gap)
    kind, why = verdict(looks, confirm)
    detail = ""
    if last_bar:
        bar, txt = last_bar
        detail = (f"{why}  [bar: n={bar['nbar']} mission={int(bar['mission'])} "
                  f"year={int(bar['year'])} nums={bar['nums']} energy={int(bar['energy'])}]")
        if txt:
            detail += " text: " + txt
    return kind, detail



def collect(m):
    """Every base of ours, with the four numbers the decision needs."""
    player = B.rd32(m, PLAYER_G)
    n = max(0, min(B.rd32(m, 0x985AF4), 64))
    rows = []
    for i in range(n):
        b = B.prod_fields(m, i)
        if b["fac"] != player:
            continue
        pr = B.price_of(m, b["fac"], b["queue"][0] & 0xFF)
        rows.append(dict(i=b["i"], name=b["name"], x=b["x"], y=b["y"],
                         minerals=b["minerals"], credit=b["income"],
                         pending=b["pending"], head=b["queue"][0],
                         price=pr["price"], horizon=b["queue"]))
    return player, rows


def decide(bases, budget_mb=0.0, gdb_n=0, orphan_traces=0, screen=None, boundaries=10):
    """Pure decision function — the whole point of the script, unit-tested without a game."""
    reasons, capable = [], []
    if screen and screen != "hud":
        if screen.startswith("unknown"):
            return dict(ready=False, verdict="BLOCKED",
                        fix="the screen read got NO verdict — freeze and look at the frame: "
                            "python3 scripts/m65_screen.py --samples 4 --save /tmp/m65, then "
                            "read /tmp/m65/sample_00_unknown.png. Return clears a dialog's "
                            "default row and Escape closes a pane; the bare map needs neither",
                        reasons=[f"no verdict from the screen read ({screen!r}): the HUD "
                                 f"button row never read, the HUD status bar never fired and "
                                 f"no modal detector named the frame"],
                        bases=bases)
        key = "Escape" if screen in ("base", "pane", "city") else "Return"
        return dict(ready=False, verdict="BLOCKED",
                    fix=f"screen is {screen!r}: press {key} until it reads 'hud', then re-run",
                    reasons=[f"a modal swallows every click AND every turn-end key "
                             f"(classify() == {screen!r})"], bases=bases)
    if gdb_n > 0:
        return dict(ready=False, verdict="BLOCKED", fix="a gdb is attached — scripts/m57_credit.py --stop",
                    reasons=[f"{gdb_n} gdb process(es) running; the store tracer and the watch "
                             f"tracer both refuse to start and pokes lie under a tracer"], bases=bases)
    if budget_mb >= BUDGET_FAIL_MB:
        return dict(ready=False, verdict="BLOCKED",
                    fix=f"evidence at {budget_mb:.1f} MB — scripts/evidence.py audit --delete",
                    reasons=["a 10-boundary run costs ~0.65 MB and the gate FAILs at 30"],
                    bases=bases)
    if not bases:
        return dict(ready=False, verdict="BLOCKED", fix="no base of ours is in the array — reload",
                    reasons=["bases_ours == 0"], bases=bases)
    for b in bases:
        credit = b["credit"] if isinstance(b["credit"], int) else 0
        mn = b["minerals"] if isinstance(b["minerals"], int) else 0
        price = b["price"]
        immediate = mn + max(credit, 0) >= price
        accrues = credit > 0
        armed = mn >= price
        tagged = b.get("name", f"#{b['i']}")
        if b["pending"] <= 0:
            reasons.append(f"{tagged}: pending 0 — not UI-queued")
            continue
        if armed:
            reasons.append(f"{tagged}: minerals {mn} >= price {price} — the completion is ARMED "
                           f"at start, so no positive-prediction window exists")
            continue
        if immediate or accrues:
            rounds = 0 if immediate else (price - mn + credit - 1) // max(credit, 1)
            tight = rounds > max(0, boundaries - 2)
            b = dict(b, rounds=rounds, tight=tight)
            capable.append(b)
            reasons.append(f"{tagged}: pending {b['pending']}, minerals {mn} < price {price}, "
                           f"credit {credit} — "
                           + ("arrival inside the first window" if immediate
                              else f"reaches the gate in ~{rounds} round(s)")
                           + (f"  TIGHT for {boundaries} boundaries — prefer a reload" if tight else ""))
        else:
            reasons.append(f"{tagged}: minerals {mn} < price {price} but credit {credit} <= 0 — "
                           f"the income add is gated d0 > 0, so storage can NEVER accrue")
    if capable:
        best = sorted(capable, key=lambda b: (b["tight"], b["rounds"]))[0]
        return dict(ready=True, verdict="READY", fix=None, reasons=reasons,
                    target=best["name"], target_index=best["i"],
                    target_tight=best["tight"], target_rounds=best["rounds"], bases=bases)
    # pick the single cheapest fix
    ours = next((b for b in bases if b["pending"] > 0), None)
    if ours is None:
        cand = sorted(bases, key=lambda b: (b["credit"] <= 0, b["minerals"] >= b["price"]))
        best = cand[0]
        fix = (f"enqueue on {best['name']} (idx {best['i']}): "
               f"scripts/m57_ui_enqueue.py --base-index {best['i']} --cell-item 2 --inserts 1")
    elif any((b["credit"] if isinstance(b["credit"], int) else 0) <= 0
             and (b["minerals"] if isinstance(b["minerals"], int) else 0) < b["price"] for b in bases):
        fix = ("credit <= 0 with minerals < price: reload the clean save "
               "(m54a_load --relaunch -> m54g_prep -> smac_play --turns 1 -> enqueue)")
    else:
        fix = ("every queued base is already at or above the price: poke storage down "
               "(m59_head.py --stage poke --base NAME --minerals <price-1>) or wait for a pay")
    return dict(ready=False, verdict="BLOCKED", fix=fix, reasons=reasons, bases=bases)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--base-index", type=int, default=None,
                    help="only consider this base index (must still be one of ours)")
    ap.add_argument("--budget", type=float, default=None, help="evidence MB (default: measure)")
    ap.add_argument("--no-screen", action="store_true",
                    help="skip the screen classification (memory-only, ~2 s faster)")
    ap.add_argument("--samples", type=int, default=4,
                    help="freezes the screen read may take to reach a verdict")
    ap.add_argument("--confirm", type=int, default=2,
                    help="how many of those looks must show the HUD status bar to call the "
                         "screen 'hud' when classify() says 'unknown'")
    ap.add_argument("--boundaries", type=int, default=10,
                    help="boundaries the run will observe (sets the horizon warning)")
    a = ap.parse_args()

    pid = os.environ.get("SMAC_PID") or M.find_pid()
    if not pid or not os.path.exists(f"/proc/{pid}"):
        print("BLOCKED: terran.exe not running — load a save (m54a_load.py --relaunch)")
        return 1
    budget = a.budget
    if budget is None:
        ev = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evidence")
        budget = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(ev)
                     for f in fs) / 1e6
    orphans = len([f for f in os.listdir(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "evidence")) if "_3x" in f])

    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        player, rows = collect(m)
        tl = M.timeline_row(m)
    if a.base_index is not None:
        rows = [r for r in rows if r["i"] == a.base_index] or rows
    kind, ktxt = ("", "") if a.no_screen else screen_class(samples=a.samples, confirm=a.confirm)
    res = decide(rows, budget_mb=budget, gdb_n=gdb_count(), orphan_traces=orphans,
                 screen=kind, boundaries=a.boundaries)
    res["box"] = dict(pid=pid, year=tl["year"], round=tl["round"], screen=kind,
                      cur_player=tl["cur_player"], player=player, budget_mb=round(budget, 1))
    if ktxt:
        res["screen_evidence"] = ktxt

    if a.json:
        print(json.dumps(res, indent=1))
        return 0 if res["ready"] else 1
    b = res["box"]
    print(f"{res['verdict']}  year {b['year']} round {b['round']} cur_player {b['cur_player']} "
          f"player {b['player']}  evidence {b['budget_mb']} MB")
    if b["screen"]:
        print(f"  SCREEN {b['screen']}: {res.get('screen_evidence', '')}")
    for r in rows:
        print(f"  i{r['i']:>3} {r['name'][:22]:22} min {r['minerals']:>4} credit {r['credit']:>3} "
              f"pend {r['pending']:>2} head {r['head']:>3} price {r['price']:>3}")
    for x in res["reasons"]:
        print("  - " + x)
    if res["fix"]:
        print("FIX: " + res["fix"])
    elif res.get("target"):
        print(f"RUN: scripts/m56_build.py --ui-queued {res['target_index']} "
              f"--boundaries {a.boundaries} --timeout 400 --no-poke-hold")
        if res.get("target_tight"):
            print(f"NOTE: the gate is ~{res['target_rounds']} rounds away in a {a.boundaries}-boundary "
                  f"run — a reload gives a window-0 arrival instead")
    return 0 if res["ready"] else 1


if __name__ == "__main__":
    sys.exit(main())
