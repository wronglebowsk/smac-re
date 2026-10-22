#!/usr/bin/env python3
"""M25: calibrate click-pixel -> tile, and watch the cursor state, WITHOUT a tracer.

Two independent oracles, both cheap:
  * the HUD terrain readout token "(x,y)" (OCR, the centre-bottom panel) — the tile the
    game itself says the cursor is on;
  * the globals we located in M24: DAT_0091b5bc (selected unit), 0x91b5b8 (orders mode),
    0x91b5c4 (menu pending), 0x91b5e8 (index) + the u32 cursor/destination lists at
    0x91b5f0 (x) and 0x91b670 (y).

Usage:
  scripts/m25_calibrate.py probe                  # read state + readout, no click
  scripts/m25_calibrate.py click 382 212          # click (xdotool, windowfocused) then read
  scripts/m25_calibrate.py key Left               # key, then read
  scripts/m25_calibrate.py seq "382 212;478 212"  # several clicks, read after each
"""
import os
import re
import struct
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P                      # verified capture/OCR pipeline

WIN = None
SEL, MODE, PEND, CIDX = 0x91b5bc, 0x91b5b8, 0x91b5c4, 0x91b5e8
XL, YL = 0x91b5f0, 0x91b670
UNIT = 0x933278
COORD = re.compile(r"^\((\d{1,3}),\s*(\d{1,3})\)$")


def win():
    global WIN
    if WIN is None:
        out = subprocess.run(["xdotool", "search", "--name", "Sid Meier"],
                             capture_output=True, text=True, check=True).stdout.split()
        WIN = out[0]
    return WIN


def mem():
    pid = int(subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True,
                             text=True, check=True).stdout.split()[0])
    return open(f"/proc/{pid}/mem", "rb", 0)


def u32(f, a):
    f.seek(a)
    return struct.unpack("<I", f.read(4))[0]


def unit(f, idx):
    f.seek(UNIT + idx * 52)
    d = f.read(52)
    x, y = struct.unpack("<hh", d[0:4])
    order = d[17]
    dx, dy = struct.unpack("<hh", d[20:24])
    return x, y, struct.unpack("<I", d[4:8])[0], order, dx, dy


def state(f, n=4):
    ci = u32(f, CIDX)
    xs = [u32(f, XL + i * 4) for i in range(n)]
    ys = [u32(f, YL + i * 4) for i in range(n)]
    sel = u32(f, SEL)
    return (f"sel={sel} mode={u32(f, MODE)} pend={u32(f, PEND)} cidx={ci} "
            f"clist={list(zip(xs, ys))} unit[{sel}]={unit(f, sel) if 0 <= sel < 400 else '?'!r}")


def readout(png):
    """The HUD tile readout: the '(x,y)' token in the bottom third of the screen."""
    for t, cx, cy, w, h in P.ocr_fast(png):
        m = COORD.match(t.strip())
        if m and cy > 480:
            return (int(m.group(1)), int(m.group(2)))
    return None


def snap(tag, label):
    png = P.freeze(tag)
    f = mem()
    print(f"{label:28s} readout={readout(png)}  {state(f)}")
    return png


def main():
    os.environ.setdefault("DISPLAY", ":99")
    w = win()
    subprocess.run(["xdotool", "windowfocus", w], check=False)
    args = sys.argv[1:]
    if not args:
        args = ["probe"]
    if args[0] == "seq":
        for spec in args[1].split(";"):
            x, y = spec.split()
            do_click(int(x), int(y))
            snap("m25_cal", f"click({x},{y})")
            time.sleep(0.4)
        return
    if args[0] == "click":
        do_click(int(args[1]), int(args[2]))
        snap("m25_cal", f"click({args[1]},{args[2]})")
    elif args[0] == "key":
        subprocess.run(["xdotool", "key", "--window", w, args[1]], check=False)
        time.sleep(1.2)
        snap("m25_cal", f"key {args[1]}")
    else:
        snap("m25_cal", "baseline")


def do_click(x, y):
    subprocess.run(["xdotool", "mousemove", str(x), str(y)], check=False)
    time.sleep(0.25)
    subprocess.run(["xdotool", "click", "1"], check=False)
    time.sleep(1.4)


if __name__ == "__main__":
    main()
