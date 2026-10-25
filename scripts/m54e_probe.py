#!/usr/bin/env python3
"""M54e probe: WHICH key makes a unit WALK, verified in memory, one key at a time.

M54d proved the loop can queue 0x18 (`g`) and read its legs, but no walk has ever
EXECUTED, because `g`'s destination is always a BASE tile (NAMED.md `0x4d6fb0`: the
0x18 branch copies `base[piVar21].x/y` into `+20/+28`) and our only base, (6,12),
already carries four of our units.  This probe answers the two open questions with
memory, not screenshots:

  1. what does each candidate key do to `+17` / the leg fields / `+0/+2` / `+40`
     (plain arrow = M27's synchronous step?  Shift+arrow = the 0x19 directional
     order?  `g` = the 0x18 to our base?),
  2. does an order that survives EXEC actually move the record.

Subcommands (each prints the record before/after and the screen class):
  peek [IDX]            dump one record + the live state
  ours [SEC]            wait for OUR phase (cur_player==player, !(turn_flags&2))
  prep [IDX] [X Y]      clear +17/+40/+4&0x10000 and stand the unit at X,Y
  key KEY [IDX]         select IDX (poke 0x91b5bc), press KEY, show the delta
  cursor X Y            poke the map cursor (0x91b5f0/0x91b670 at index 0x91b5e8)
  chooser [IDX]         press `g`, capture + OCR the pane, click its OK, show legs
  exec                  click TURN COMPLETE, poll the year, show every delta
"""
import json
import os
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as sp  # noqa: E402

CURSOR_X_G, CURSOR_Y_G, CURSOR_IDX_G = 0x91B5F0, 0x91B670, 0x91B5E8
FIELDS = ("x", "y", "flags", "frozen", "type", "owner", "order", "mp", "legs_x", "legs_y")


def decode(d):
    """52 raw record bytes -> the fields this milestone cares about (+20/+28 legs)."""
    return dict(
        x=struct.unpack("<h", d[0:2])[0], y=struct.unpack("<h", d[2:4])[0],
        flags=struct.unpack("<I", d[4:8])[0], frozen=d[9],
        type=struct.unpack("<H", d[10:12])[0], owner=d[14], order=d[17], mp=d[40],
        legs_x=[struct.unpack("<h", d[20 + k * 2:22 + k * 2])[0] for k in range(4)],
        legs_y=[struct.unpack("<h", d[28 + k * 2:30 + k * 2])[0] for k in range(4)])


def brief(r):
    return ("xy (%d,%d) order %d mp %d type %d flags %#x legs %s/%s"
            % (r["x"], r["y"], r["order"], r["mp"], r["type"], r["flags"],
               r["legs_x"], r["legs_y"]))


def grab(idx, f):
    return decode(sp.rd(f, sp.UNIT_ARR + idx * 52, 52))


def st():
    s = sp.state()
    return {k: s.get(k) for k in ("year", "cur_player", "player", "turn_flags")}


def cls(png=None):
    png = png or sp.freeze("m54e")
    w = sp.ocr_fast(png)
    return sp.classify(w, sp.region_colors(png), png), w, png


def wait_ours(sec=90):
    t0 = time.time()
    while time.time() - t0 < sec:
        s = st()
        if s["player"] == s["cur_player"] and not (s["turn_flags"] or 0) & 2:
            k, _w, _p = cls()
            if k == "hud":
                return s
        time.sleep(1.0)
    return None


def main():
    a = sys.argv[1:]
    cmd = a[0] if a else "peek"
    args = a[1:]
    sp.WIN = sp.find_window()
    pid, f = sp.mem()
    print("state", st(), "pid", pid)
    try:
        if cmd == "peek":
            idx = int(args[0]) if args else 3
            print("rec", idx, brief(grab(idx, f)))
        elif cmd == "ours":
            s = wait_ours(int(args[0]) if args else 90)
            print("ours", s if s else "TIMEOUT still not our phase")
        elif cmd == "prep":
            idx = int(args[0]) if args else 3
            x, y = (int(args[1]), int(args[2])) if len(args) > 2 else (7, 12)
            print("before", brief(grab(idx, f)))
            base = sp.UNIT_ARR + idx * 52
            d = bytearray(sp.rd(f, base, 52))
            d[17] = 0
            d[40] = 0
            struct.pack_into("<I", d, 4, struct.unpack("<I", d[4:8])[0] & ~0x10000)
            struct.pack_into("<h", d, 0, x)
            struct.pack_into("<h", d, 2, y)
            for k in range(4):
                struct.pack_into("<h", d, 20 + k * 2, -1)
                struct.pack_into("<h", d, 28 + k * 2, -1)
            sp.wr(f, base, bytes(d))
            print("after ", brief(grab(idx, f)))
        elif cmd == "cursor":
            x, y = int(args[0]), int(args[1])
            i = struct.unpack("<I", sp.rd(f, CURSOR_IDX_G, 4))[0]
            sp.wr(f, CURSOR_X_G + i * 4, struct.pack("<I", x))
            sp.wr(f, CURSOR_Y_G + i * 4, struct.pack("<I", y))
            print("cursor index", i, "->",
                  struct.unpack("<I", sp.rd(f, CURSOR_X_G + i * 4, 4))[0],
                  struct.unpack("<I", sp.rd(f, CURSOR_Y_G + i * 4, 4))[0])
        elif cmd == "key":
            kname, idx = args[0], (int(args[1]) if len(args) > 1 else 3)
            sp.wr(f, sp.SEL_G, struct.pack("<i", idx))
            print("sel", struct.unpack("<i", sp.rd(f, sp.SEL_G, 4))[0],
                  "orders_mode", sp.rd(f, sp.ORDERS_MODE_G, 1)[0],
                  "|", brief(grab(idx, f)))
            sp.key(kname)
            time.sleep(1.2)
            for _ in range(4):
                k, w, png = cls()
                print("  pane:", k, " ".join(t for t, *_ in w[:10])[:90])
                if k == "dest-chooser":
                    sp.answer_dest_chooser(png, True)
                elif k == "hud":
                    break
                else:
                    sp.key("Return")
                time.sleep(1.0)
            print("after", brief(grab(idx, f)))
        elif cmd == "chooser":
            idx = int(args[0]) if args else 3
            sp.wr(f, sp.SEL_G, struct.pack("<i", idx))
            print("sel", idx, "|", brief(grab(idx, f)))
            sp.key("g")
            time.sleep(1.5)
            k, w, png = cls()
            print("pane", k)
            rows = {}
            for t, x, y, *_ in w:
                rows.setdefault(int(y) // 12 * 12, []).append((round(x), t))
            for y in sorted(rows):
                print("  OCR", y, " ".join(t for _x, t in sorted(rows[y]))[:120])
            out = os.path.join(sp.EVID, "m54e")
            os.makedirs(out, exist_ok=True)
            sp.sh(f"cp {png} {out}/chooser_live.png")
            if k == "dest-chooser":
                sp.answer_dest_chooser(png, True)
                time.sleep(1.2)
                print("afterOK", brief(grab(idx, f)))
                sp.sh(f"cp {sp.freeze('m54e_ok')} {out}/after_ok.png")
        elif cmd == "exec":
            idxs = [int(v) for v in args] or [3]
            before = {i: grab(i, f) for i in idxs}
            y0 = sp.year()
            for i in idxs:
                print("before", i, brief(before[i]))
            btn = None
            k, w, png = cls()
            for t, x, y, *_ in w:
                if t.lower().startswith("complete"):
                    btn = (int(x), int(y))
            sp.click(btn or sp.TURN_BTN)
            print("clicked TURN COMPLETE at", btn or sp.TURN_BTN)
            t0 = time.time()
            while sp.year() == y0 and time.time() - t0 < 180:
                k, w, png = cls()
                print("  ", round(time.time() - t0), k, " ".join(t for t, *_ in w[:8])[:70])
                if k == "confirm":
                    sp.answer_confirm(w)
                elif k == "dest-chooser":
                    sp.answer_dest_chooser(png)
                elif k == "comm":
                    sp.answer_communication(png)
                elif k in ("dialog", "unknown", "movie"):
                    if not sp.handle_pane(w, png, {"handled": []}, k):
                        sp.key("Return")
                time.sleep(1.5)
            print("year", y0, "->", sp.year(), "state", st())
            for i in idxs:
                print("after ", i, brief(grab(i, f)))
    finally:
        f.close()


if __name__ == "__main__":
    main()
