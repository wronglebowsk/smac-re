#!/usr/bin/env python3
"""M54d probe: WHICH input queues a real MOVE on a unit that stands on its own base?

    python3 scripts/m54d_probe.py --unit 0 [--keys g,shift+Right,...] [--json out.json]

M54c established the SENTRY/HOLD keys and proved `g` refuses a unit standing on its own
base (`evidence/m54c_probe.txt`). M54d needs a unit that actually WALKS, so this fires one
input at a time at one selected record and reads the record back after each: `+17` (the
order byte), the `+20..+27`/`+28..+35` leg arrays (ORDERS.md §4 0x18), `+0/+2` (x,y) and
`+40` (movement spent) — the memory oracle, never the screen — plus the screen class the
input raised (a pane is a key sink, so its frame is saved for the classifier).

Between attempts the probe RESTORES `+17 = 0` with a poke, so each row tests one input on
the same starting state. Reads and pokes /proc/pid/mem; the ORDER itself is always a real
xdotool keypress through the game's own handler (ORDERS.md §1).
"""
import argparse, json, os, struct, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "evidence", "m54d")

# (xdotool key, the +17 bytes this input may legitimately produce, label)
SEQ = [
    ("g",             {0x18},           "move-to-own-base (M54c: refused on own base)"),
    ("Right",         {0x18, 0x19},     "plain arrow = map cursor (M54c: not an order)"),
    ("shift+Right",   {0x19},           "Shift+arrow = directional order (ORDERS.md 4 0x19, M27)"),
    ("shift+Up",      {0x19},           "Shift+arrow up (M54c saw a pane here)"),
    ("KP_Right",      {0x18, 0x19},     "numpad dir cluster (ORDERS.md 1 rule 2)"),
    ("i",             {0xfd},           "route to home base (FUN_004d6fb0 -3)"),
    ("l",             {1},              "SENTRY control (M54c: lands on any selected unit)"),
    ("h",             {2},              "HOLD control"),
    ("slash",         {0},              "explore (FUN_004d9470; a WALK, clears the order)"),
    ("period",        set(range(4, 0x18)), "terraform control: class-3 unit -> NEEDTERRAFORMERS"),
]


def legs(f, idx):
    d = P.rd(f, P.UNIT_ARR + idx * 52, 52)
    return dict(x=[struct.unpack("<h", d[20 + k * 2:22 + k * 2])[0] for k in range(4)],
                y=[struct.unpack("<h", d[28 + k * 2:30 + k * 2])[0] for k in range(4)],
                dir=struct.unpack("<h", d[20:22])[0],
                ox=struct.unpack("<h", d[22:24])[0], oy=struct.unpack("<h", d[30:32])[0])


def close_pane(kind, png, tag):
    if kind in ("hud", None):
        return
    if kind not in ("quit-prompt",):
        os.system(f"cp {png} {EVID}/probe_{tag}_{kind}.png")
    if kind in ("base", "quit-prompt"):
        P.key("Escape"); time.sleep(1.0)          # Escape = close / "Oops, no, wait!"
    elif kind == "help":
        xy = P.answer_help_page(png)
        if xy:
            P.click(xy)
        time.sleep(1.0)
    else:
        P.key("Return"); time.sleep(1.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit", type=int, default=0)
    ap.add_argument("--keys", default=None, help="comma list from SEQ, e.g. g,shift+Right,l")
    ap.add_argument("--json", default=None)
    ap.add_argument("--settle", type=float, default=1.4)
    a = ap.parse_args()
    os.makedirs(EVID, exist_ok=True)
    P.WIN = P.find_window()
    if not P.WIN:
        sys.exit("no game window")
    pid, f = P.mem()
    st = P.state()
    me = st.get("player")
    idx = a.unit
    seq = SEQ
    if a.keys:
        want = set(a.keys.split(","))
        seq = [s for s in SEQ if s[0] in want]
    rows = []
    print(f"PROBE pid={pid} year={st.get('year')} player={me} cur_player={st.get('cur_player')} "
          f"unit={idx}", flush=True)
    b0 = P.unit_rec(f, idx)
    print(f"  start rec{idx} ({b0['x']},{b0['y']}) type {b0['type']} cls {P.unit_class(f, b0['type'])} "
          f"order {b0['order']} mp {b0['mpused']} flags {b0['flags']:#x}", flush=True)
    for kname, want, label in seq:
        P.wr(f, P.ORDERS_MODE_G, struct.pack("<i", 1))
        P.wr(f, P.SEL_G, struct.pack("<i", idx))
        P.wr(f, P.UNIT_ARR + idx * 52 + 17, b"\x00")      # restore the starting state
        before = P.unit_rec(f, idx)
        e0 = P.energy(f, me)
        P.focus()
        P.sh(f'xdotool key --clearmodifiers "{kname}"')
        time.sleep(a.settle)
        png = P.freeze("m54dp")
        words = P.ocr_fast(png)
        kind = P.classify(words, P.region_colors(png), png)
        after = P.unit_rec(f, idx)
        L = legs(f, idx)
        e1 = P.energy(f, me)
        landed = after["order"] != before["order"] and (not want or after["order"] in want)
        row = dict(key=kname, label=label, want=sorted(want),
                   order_before=before["order"], order_after=after["order"],
                   landed=bool(landed), x=after["x"], y=after["y"], mp_after=after["mpused"],
                   legs=L, energy_delta=e1 - e0, screen=kind,
                   text=" ".join(w for w, *_ in words[:14]))
        rows.append(row)
        print(f"  {kname:12s} order {before['order']:3d}->{after['order']:3d} "
              f"{'LANDED' if landed else 'no   '} x,y=({after['x']},{after['y']}) "
              f"mp {after['mpused']} legs={L['x']}/{L['y']} dE={e1-e0} screen={kind}", flush=True)
        print(f"                 {row['text'][:70]}", flush=True)
        close_pane(kind, png, kname.replace("+", "_"))
        P.WIN = P.find_window()
    for _ in range(3):
        if P.classify(P.ocr_fast(P.freeze("m54dz")), P.region_colors(P.freeze("m54dz")),
                      None) == "hud":
            break
        P.key("Escape"); time.sleep(1.0)
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(dict(pid=pid, state=st, unit=idx, rows=rows), fh)
        print(f"wrote probe -> {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
