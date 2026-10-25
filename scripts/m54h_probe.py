#!/usr/bin/env python3
"""M54h probe: can the `g` chooser name a base the unit is NOT standing on?

M54g founded Korolev Center, but the unit was POKE-positioned onto its tile: on this
build `g` was believed to refuse a unit garrisoned on its own base, and every chooser OK
we ever answered highlighted the single row it drew (M54d: one row, `Distance: 0`).
We now own TWO base tiles — University Base (28,42) and Korolev Center (29,42) — so the
chooser has something else to name.

Memory-first (OCR is slow and a clean HUD sometimes classifies `unknown`): the oracle is
`+17` and the leg arrays, sampled THROUGH the OK click with `order_byte_watcher`; OCR runs
only at pane ends, and only to read the chooser's own row list.

Subcommands (one variable per step; every stage prints the record it touched):
  peek N                    record N + orders mode + cursor + our bases
  chooser N [--row K] [--ok] [--tag T] [--save-frame]
                            select N, press `g`, print the pane class + its destination
                            ROWS (bar geometry) + OCR lines; optionally click row K and
                            re-read, then optionally click OK through the byte watcher.
  legs N                    read +17 / +20..+35 / +40 / x,y on record N (no keys)
"""
import argparse
import json
import os
import struct
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as sp  # noqa: E402

BASE_ARR, BASE_SZ, BASE_COUNT_G = 0x95DA10, 304, 0x985AF4
CURSOR_X_G, CURSOR_Y_G, CURSOR_IDX_G = 0x91B5F0, 0x91B670, 0x91B5E8
OUT_DIR = os.path.join(sp.EVID, "m54h")


def decode(d):
    return dict(
        x=struct.unpack("<h", d[0:2])[0], y=struct.unpack("<h", d[2:4])[0],
        flags=struct.unpack("<I", d[4:8])[0], frozen=d[9],
        type=struct.unpack("<H", d[10:12])[0], owner=d[14], order=d[17], mp=d[40],
        legs_x=[struct.unpack("<h", d[20 + k * 2:22 + k * 2])[0] for k in range(4)],
        legs_y=[struct.unpack("<h", d[28 + k * 2:30 + k * 2])[0] for k in range(4)])


def grab(f, idx):
    return decode(sp.rd(f, sp.UNIT_ARR + idx * 52, 52))


def brief(r):
    return ("xy (%d,%d) order %d mp %d type %d flags %#x legs %s/%s"
            % (r["x"], r["y"], r["order"], r["mp"], r["type"], r["flags"],
               r["legs_x"], r["legs_y"]))


def our_bases(f, faction=3):
    n = struct.unpack("<I", sp.rd(f, BASE_COUNT_G, 4))[0]
    out = []
    for i in range(n):
        b = sp.rd(f, BASE_ARR + i * BASE_SZ, 6)
        if b[4] == faction:
            name = sp.rd(f, BASE_ARR + i * BASE_SZ + 19, 33).split(b"\0")[0]
            out.append(dict(idx=i, x=struct.unpack("<h", b[0:2])[0],
                            y=struct.unpack("<h", b[2:4])[0],
                            name=name.decode("latin-1").strip()))
    return out


def cursor_state(f):
    i = struct.unpack("<I", sp.rd(f, CURSOR_IDX_G, 4))[0]
    return dict(index=i,
                x=struct.unpack("<I", sp.rd(f, CURSOR_X_G + i * 4, 4))[0],
                y=struct.unpack("<I", sp.rd(f, CURSOR_Y_G + i * 4, 4))[0])


def look():
    """Freeze, OCR, classify. Returns (kind, words, png)."""
    png = sp.freeze("m54h")
    w = sp.ocr_fast(png)
    return sp.classify(w, sp.region_colors(png), png), w, png


def bands_of(png, y0=118):
    """Bar bands (row bands) in the chooser area as (y_center, groups, merged_span).

    `bar_colour_mask` returns rows OFFSET by y0 and `pane_bars` never tells us a bar's
    width, so re-derive the bands here: the chooser draws its destination rows as
    FULL-WIDTH periwinkle bars (measured on `evidence/m54h/chooser_g60b.png`: rows at
    y 125-139 and 144-158, fill 159..638) and its buttons as five 96-px-wide bars on one
    band (Sort: Name / Sort: Size / Sort: Dist / OK / CANCEL at centres 209/305/401/497/
    593, y 172-190). A row band's groups merge into a ~480 px span; the button band's do
    not (91 px at duty 0.3, five groups at duty 0.2).
    """
    rows = sp.bar_colour_mask(png, y0)
    hot = [y for y, r in enumerate(rows) if sum(r) > 100]
    out = []
    bands = []
    for y in hot:
        if bands and y - bands[-1][1] <= 2:
            bands[-1][1] = y
        else:
            bands.append([y, y])
    for b0, b1 in bands:
        h = b1 - b0 + 1
        if h < 8:
            continue
        need = max(4, int(h * 0.3))
        cold = [sum(col) for col in zip(*rows[b0:b1 + 1])]
        groups, x = [], 0
        while x < sp.W:
            if cold[x] < need:
                x += 1
                continue
            x0 = x
            while x < sp.W and cold[x] >= need:
                x += 1
            groups.append((x0, x - 1))
        if not groups:
            continue
        # low-duty pass: separates the five buttons from the label-split row fill
        need2 = max(3, int(h * 0.2))
        groups2, x = [], 0
        while x < sp.W:
            if cold[x] < need2:
                x += 1
                continue
            x0 = x
            while x < sp.W and cold[x] >= need2:
                x += 1
            if x - x0 >= 12:
                groups2.append(((x0 + x) // 2, x - x0))
        out.append(dict(y=y0 + (b0 + b1) // 2, y0=y0 + b0, y1=y0 + b1,
                        span=(groups[0][0], groups[-1][1]),
                        width=groups[-1][1] - groups[0][0],
                        groups=groups, buttons=groups2))
    return out


def rows_of(png, words):
    """The chooser's destination rows: the wide bar bands, with the OCR text on each."""
    rows = []
    for b in bands_of(png):
        if b["width"] < 300:
            continue                     # the button band is never a row
        texts = sorted((round(x), t) for t, x, y, *_ in words
                       if abs(y - b["y"]) <= 8 and x < 700)
        rows.append(dict(y=b["y"], cx=(b["span"][0] + b["span"][1]) // 2,
                         span=list(b["span"]), n_bar_groups=len(b["groups"]),
                         text=" ".join(t for _x, t in texts)))
    return rows


def chooser_buttons(png):
    """The chooser's button band: five evenly-spaced bars. Returns (cy, centres).

    Measured on `evidence/m54h/chooser_g60b.png`: OK is the FOURTH centre (497) and
    CANCEL the LAST (593); the three before them are Sort: Name / Size / Dist. Verified
    by effect, not by label: CANCEL closes the pane and writes no `+17`, OK lands 0x18.
    """
    for b in reversed(bands_of(png)):
        cs = [c for c, _w in b["buttons"]]
        if len(cs) >= 4:
            return b["y"], cs
    return None, []


def ok_bar(png):
    cy, cs = chooser_buttons(png)
    if not cs:
        return None
    return int(cs[-2]), int(cy)           # OK = 4th of the 5 buttons


def cancel_bar(png):
    cy, cs = chooser_buttons(png)
    if not cs:
        return None
    return int(cs[-1]), int(cy)



def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("peek");  p.add_argument("unit", type=int)
    c = sub.add_parser("chooser")
    c.add_argument("unit", type=int)
    c.add_argument("--row", type=int, default=None, help="click the K-th destination row")
    c.add_argument("--ok", action="store_true", help="click the chooser OK (through the watcher)")
    c.add_argument("--cancel", action="store_true", help="click CANCEL (control: no byte, pane closes)")
    c.add_argument("--tag", default="probe")
    c.add_argument("--save-frame", action="store_true")
    l = sub.add_parser("legs");  l.add_argument("unit", type=int)
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    pid, f = sp.mem()
    log = {"pid": pid, "cmd": args.cmd, "unit": args.unit, "stages": []}

    def stage(name, **kw):
        log["stages"].append(dict(stage=name, **kw))
        print(name, json.dumps(kw, sort_keys=True)[:400], flush=True)

    try:
        rec = grab(f, args.unit)
        stage("before", rec=rec, orders_mode=sp.rd(f, sp.ORDERS_MODE_G, 1)[0],
              sel=struct.unpack("<i", sp.rd(f, sp.SEL_G, 4))[0],
              cursor=cursor_state(f), bases=our_bases(f),
              state={k: sp.state().get(k) for k in ("year", "cur_player", "player",
                                                    "turn_flags")})
        if args.cmd == "peek":
            print("rec", args.unit, brief(rec))
            return

        if args.cmd == "legs":
            return

        # --- selection alone (no key): does the pane open from the poke? -------------
        sp.focus()
        sp.wr(f, sp.SEL_G, struct.pack("<i", args.unit))
        time.sleep(0.4)
        k0, w0, png0 = look()
        stage("select_only", sel=struct.unpack("<i", sp.rd(f, sp.SEL_G, 4))[0],
              kind=k0, rec=grab(f, args.unit))

        # --- press `g` --------------------------------------------------------------
        sp.key("g")
        time.sleep(1.3)
        k, w, png = look()
        rows = rows_of(png, w)
        stage("after_g", kind=k, rows=rows,
              ocr=[(int(y), round(x), t) for t, x, y, *_ in w if 90 <= y <= 200][:24],
              rec=grab(f, args.unit))
        print("pane", k, "| rows", json.dumps(rows), flush=True)
        if args.save_frame:
            dst = os.path.join(OUT_DIR, f"chooser_{args.tag}.png")
            os.system(f"cp {png} {dst}")
            log["frame"] = dst.replace(sp.ROOT + "/", "")
            print("frame", log["frame"], flush=True)

        # --- click a destination row (ONE click, then read) -------------------------
        if args.row is not None:
            if not rows:
                stage("row_click", error="no rows to click")
            else:
                r = rows[args.row]
                sp.click((r["cx"], r["y"]))
                time.sleep(0.9)
                k2, w2, png2 = look()
                stage("row_click", clicked=[r["cx"], r["y"]], row=r, kind_after=k2,
                      rows_after=rows_of(png2, w2), rec=grab(f, args.unit))
                if args.save_frame:
                    dst = os.path.join(OUT_DIR, f"chooser_{args.tag}_row.png")
                    os.system(f"cp {png2} {dst}")
                    log["frame_row"] = dst.replace(sp.ROOT + "/", "")

        # --- click OK through the byte watcher --------------------------------------
        if args.ok:
            xy = ok_bar(png) if args.row is None else ok_bar(look()[2])
            if xy is None:
                stage("ok_click", error="no OK bar found")
            else:
                stop, seen = threading.Event(), []
                th = sp.order_byte_watcher(args.unit, stop, seen, dur=2.5)
                sp.click(xy)
                time.sleep(0.6)
                stop.set()
                th.join(timeout=3.0)
                after = grab(f, args.unit)
                stage("ok_click", clicked=list(xy), samples_17=seen[:80], rec=after)
                print("OK clicked at", xy, "| +17 burst", seen[:24], flush=True)
                print("after", brief(after), flush=True)
                k3, w3, png3 = look()
                stage("after_ok", kind=k3, rec=grab(f, args.unit),
                      ocr=[(int(y), round(x), t) for t, x, y, *_ in w3 if 90 <= y <= 200][:16])

        if args.cancel:
            xy = cancel_bar(look()[2])
            if xy is None:
                stage("cancel_click", error="no button band")
            else:
                stop, seen = threading.Event(), []
                th = sp.order_byte_watcher(args.unit, stop, seen, dur=1.5)
                sp.click(xy)
                time.sleep(0.5)
                stop.set()
                th.join(timeout=3.0)
                k4, w4, _p4 = look()
                stage("cancel_click", clicked=list(xy), samples_17=seen[:60], kind_after=k4,
                      rec=grab(f, args.unit))
                print("CANCEL clicked at", xy, "| +17 burst", seen[:16], "| pane", k4, flush=True)
    finally:
        f.close()
        tag = getattr(args, "tag", "probe")
        path = os.path.join(OUT_DIR, f"probe_{args.cmd}_{tag}.json")
        with open(path, "w") as fh:
            json.dump(log, fh, indent=1, sort_keys=True)
        print("wrote", path.replace(sp.ROOT + "/", ""))


if __name__ == "__main__":
    main()
