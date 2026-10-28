#!/usr/bin/env python3
"""M57: enqueue a unit through the GAME's own BUILD UI (the session-93 recipe, scripted).

Every step is followed by a memory read-back. The only memory writes are the three
PRE-click pokes (both cursor homes to the base tile, SEL_G = -1, orders mode = 0) that
make `b` open the base display instead of raising the OBLITERATE prompt; the QUEUE
itself is written by the game's 0x417ee0 dispatch, never by us.

    python3 scripts/m57_ui_enqueue.py [--base-index 18] [--cell 3] [--inserts 1]
"""
import argparse, os, struct, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import smac_play as sp  # noqa: E402

WIN_G, WIN_CUR_X, WIN_CUR_Y = 0x7CDECC, 0x1DD9C, 0x1DDA0
CI, CX, CY = 0x91B5E8, 0x91B5F0, 0x91B670
SEL_G, ORDERS_MODE = 0x91B5BC, 0x91B5B8
BASE_ARR, BASE_SZ = 0x95DA10, 304
PANE_BASE_IDX = 0x6A9480 + 0x3FF3C      # the base index the open display is showing
ARROW_XY, ROW1_XY = (523, 433), (185, 437)
INSERT_XY, OK_XY = (497, 343), (285, 343)


def u32(f, a):
    return struct.unpack("<I", sp.rd(f, a, 4))[0]


def i32(f, a):
    return struct.unpack("<i", sp.rd(f, a, 4))[0]


def click(xy):
    subprocess.run(["xdotool", "mousemove", str(xy[0]), str(xy[1])], check=False)
    subprocess.run(["xdotool", "click", "1"], check=False)
    time.sleep(0.4)


def key(k):
    subprocess.run(["xdotool", "key", "--clearmodifiers", k], check=False)
    time.sleep(0.5)


def base_rec(f, i):
    b = sp.rd(f, BASE_ARR + i * BASE_SZ, BASE_SZ)
    g = lambda o: struct.unpack("<i", b[o:o + 4])[0]
    return dict(i=i, name=b[19:59].split(b"\0")[0].decode("latin-1", "replace"),
                x=struct.unpack("<H", b[0:2])[0], y=struct.unpack("<H", b[2:4])[0],
                fac=b[4], pending=g(0x4c), queue=[g(0x50 + 4 * k) for k in range(6)],
                minerals=g(0x40), d0=g(0xd0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-index", type=int, default=18)
    ap.add_argument("--cell", type=int, default=3, help="chooser grid cell (3 = Scout Patrol)")
    ap.add_argument("--cell-item", type=int, default=None,
                    help="pick the cell whose candidate-array entry equals this item id "
                         "(the array order is era-dependent; 2 = Scout Patrol)")
    ap.add_argument("--inserts", type=int, default=1)
    ap.add_argument("--no-ok", action="store_true",
                    help="stop with the CHOOSER still open (the M84 cancel-sentinel test needs "
                         "the pump to be running when the Cancel arrives)")
    a = ap.parse_args()

    pid, f = sp.mem()
    b0 = base_rec(f, a.base_index)
    print(f"pre: {b0}", flush=True)
    tx, ty = b0["x"], b0["y"]

    # the three enabling pokes (NOT queue fields)
    w = u32(f, WIN_G)
    sp.wr(f, w + WIN_CUR_X, struct.pack("<i", tx)); sp.wr(f, w + WIN_CUR_Y, struct.pack("<i", ty))
    ci = u32(f, CI)
    sp.wr(f, CX + ci * 4, struct.pack("<i", tx)); sp.wr(f, CY + ci * 4, struct.pack("<i", ty))
    sp.wr(f, SEL_G, struct.pack("<i", -1))
    sp.wr(f, ORDERS_MODE, struct.pack("<i", 0))
    print("cursor read-back:", dict(win=(i32(f, w + WIN_CUR_X), i32(f, w + WIN_CUR_Y)),
          arr=(i32(f, CX + u32(f, CI) * 4), i32(f, CY + u32(f, CI) * 4)),
          sel=i32(f, SEL_G), orders_mode=i32(f, ORDERS_MODE)), flush=True)

    win = sp.find_window()
    sp.focus()
    key("b")
    print(f"after b: pane base index = {u32(f, PANE_BASE_IDX)} (want {a.base_index})", flush=True)

    # The QUEUE widget's base is INDEPENDENT of the display's base (measured 2163/2168:
    # `b` opened on Korolev while the widget held University, and vice versa). Cycle the
    # right arrow until the QUEUE widget shows the base we want: the pane base-index field
    # follows the widget after an arrow click. Then open the chooser and INSERT.
    for attempt in range(8):
        if u32(f, PANE_BASE_IDX) == a.base_index:
            break
        click(ARROW_XY)
        print(f"arrow {attempt+1}: pane base index = {u32(f, PANE_BASE_IDX)} "
              f"(want {a.base_index})", flush=True)
    print(f"queue widget on pane base index {u32(f, PANE_BASE_IDX)}", flush=True)

    click(ROW1_XY)
    time.sleep(0.6)
    print("after row-1 click: pending =", i32(f, BASE_ARR + a.base_index * BASE_SZ + 0x4c), flush=True)

    cand = [i32(f, 0x9267E4 + 4 * j) for j in range(8)]
    cnt = i32(f, 0x9267E0)
    k = a.cell
    if a.cell_item is not None:
        if a.cell_item not in cand:
            print(f"FAIL: item {a.cell_item} not in candidate array {cand[:cnt]}", flush=True)
            return 1
        k = cand.index(a.cell_item)
    cx, cy = 128 + 127 * (k % 5), 60 + 100 * (k // 5)
    print(f"clicking cell {k} -> ({cx},{cy}); candidate array {cand[:cnt]} count {cnt}", flush=True)
    click((cx, cy))
    print(f"after cell-{k} click: chooser guard (cell index) = {i32(f, 0x6A9E9C + 0xa774)}", flush=True)

    for n in range(a.inserts):
        landed = False
        for attempt in range(6):
            click(INSERT_XY)
            time.sleep(1.0)      # an immediate read can show the OLD pending (session 93)
            b1 = base_rec(f, a.base_index)
            print(f"after INSERT {n+1} (try {attempt+1}): pending={b1['pending']} "
                  f"head={b1['queue'][0]} slots={b1['queue']} minerals={b1['minerals']} "
                  f"d0={b1['d0']}", flush=True)
            if b1["pending"] > 0:
                landed = True
                break
            click(ARROW_XY)      # cycle the QUEUE widget to another base
            print(f"  queue widget cycled; pane base index = {u32(f, PANE_BASE_IDX)}", flush=True)
        if not landed:
            print(f"FAIL: INSERT {n+1} never landed on base {a.base_index}", flush=True)
            return 1

    if a.no_ok:
        print("STOPPED with the chooser open (--no-ok): guard (cell index) =",
              i32(f, 0x6A9E9C + 0xa774), "pending =",
              i32(f, BASE_ARR + a.base_index * BASE_SZ + 0x4c), flush=True)
        return 0

    click(OK_XY)
    time.sleep(0.8)
    b2 = base_rec(f, a.base_index)
    print(f"after OK: pending={b2['pending']} head={b2['queue'][0]} slots={b2['queue']} "
          f"minerals={b2['minerals']} d0={b2['d0']}", flush=True)
    # The recipe turns orders mode OFF to open the base display; leave it OFF and every order
    # key (h/g/l) falls through to the cursor handler, and a turn with an actionable unit then
    # never ends (measured: 240 s parked on cur_player 3 with Return/h/OK doing nothing).
    # Restore it — this is setup state for a later run, NOT a queue/economy write.
    sp.wr(f, ORDERS_MODE, struct.pack("<i", 1))
    print("orders mode restored:", i32(f, ORDERS_MODE), " sel:", i32(f, SEL_G), flush=True)
    # The base display this recipe opened is STILL OPEN, and a modal pane swallows every
    # turn-end key: a 90 s watch sat parked on cur_player 3 with Return/h/OK doing nothing
    # until the pane was closed (measured 2026-10-26, class `base` with the Operations
    # Director advice line on screen). Close it and verify by class — Escape is safe HERE
    # (the pane eats it); it is Escape on the bare map that raises the quit prompt.
    for i in range(3):
        png = sp.freeze("m574eq")
        w = sp.ocr_fast(png)
        kind = sp.classify(w, sp.region_colors(png), png)
        if kind != "base":
            print(f"pane closed after {i} Escape(s): class {kind}", flush=True)
            break
        sp.key("Escape")
        time.sleep(1.6)
    else:
        print("WARN: the base pane is still open after 3 Escapes — the turn will not end",
              flush=True)
    return 0



if __name__ == "__main__":
    sys.exit(main())
