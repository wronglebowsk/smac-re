#!/usr/bin/env python3
"""M34 v5: watch a stored Farm order EXECUTE — no tracer anywhere.

Why no tracer: under a live gdb, /proc/pid/mem WRITES never reach the game (M33
pitfall; try3 proof: TERRAF landed on the cycle's unit, not the poked one), and the
selection is game-owned. So we (a) do all pokes with TracerPid 0, (b) press keys only
in the window where the GAME itself has selected our Former (poll 0x91b5bc), and
(c) read every before/after purely through /proc/pid/mem.

Chain under test (all static, ghidra_out):
  'f' -> FUN_00512b40 -> FUN_00512450 -> FUN_004d44d0(unit,0): gates pass on a legal
       tile -> store +17=4 (0x4d5bbf) -> broadcast FUN_00584350 (0x2101).
  Execution trigger candidates:
    (A) Space on the selected unit: FUN_004d1e90 -> can-act FUN_005acc00 ->
        FUN_00529090(unit,-1,0) -> solo FUN_00585720(unit, 0x8-sentinel, 3).
    (B) end-of-turn machinery (explore orders demonstrably run then).
Payment: Farm deferred at issue (M33); debit site 0x4d561a writes
0x94d650[player*0x82f]; refund site 0x4d5908.

Steps:
  1. find our Former (class 9); poke flags &= ~0x5000 (clear explore so the cycle
     treats it as a plain idle unit) and mpused=0.  [TracerPid 0]
  2. poll sel; the instant sel==unit press 'f' (xdotool); poll order byte == 4.
  3. snapshot tile +8 / energy / unit.
  4. press Space (trigger A) and snapshot; then advance N turns via service_turn
     (trigger B) and snapshot after each.
Usage: m34_exec_watch.py [--turns 2] [--unit N] [--tag m34v5]
"""
import argparse, json, os, struct, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "evidence")
UNIT_ARR, CLASS_TBL, MAX_UNITS = 0x933278, 0x98ADB2, 300
PLAYER, SEL = 0x91B5B4, 0x91B5BC
ENERGY_G, ENERGY_STRIDE = 0x94D650, 0x82F
TILE_BASE, TILE_STRIDE_ROW = 0x92AE14, 40


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          env={**os.environ, "DISPLAY": ":99"})


def tile_addr(f, x, y):
    return TILE_BASE + (TILE_STRIDE_ROW * y + (x >> 1)) * 0x2c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--turns", type=int, default=2)
    ap.add_argument("--unit", type=int, default=None)
    ap.add_argument("--tag", default="m34v5")
    a = ap.parse_args()
    tag = a.tag

    pid = int(sh("pgrep -x terran.exe | head -1").stdout.split()[0])
    tracer = sh(f"grep TracerPid /proc/{pid}/status").stdout
    assert "TracerPid:\t0" in tracer, "tracer attached — abort (pokes would ghost)"
    _, f = P.mem()
    me = struct.unpack("<I", P.rd(f, PLAYER, 4))[0]

    # --- 1. find our Former ---
    units = P.rd(f, UNIT_ARR, MAX_UNITS * 52)
    classes = P.rd(f, CLASS_TBL, 1024 * 52)
    unit = a.unit
    if unit is None:
        for i in range(MAX_UNITS):
            d = units[i * 52:(i + 1) * 52]
            if d[14] == 0xFF:
                continue
            typ = struct.unpack("<H", d[10:12])[0]
            if (classes[typ * 52] & 0xFF) == 9 and d[14] == me:
                unit = i
                break
    if unit is None:
        sys.exit("no Former owned by us")
    base = UNIT_ARR + unit * 52
    flags0 = struct.unpack("<I", P.rd(f, base + 4, 4))[0]
    P.wr(f, base + 4, struct.pack("<I", flags0 & ~0x5000))     # clear explore bits
    P.wr(f, base + 40, struct.pack("<B", 0))                   # mpused = 0
    u0 = P.unit_rec(f, unit)
    x0, y0 = u0["x"], u0["y"]
    ta = tile_addr(f, x0, y0)
    rec = dict(pid=pid, unit=unit, year=struct.unpack("<I", P.rd(f, 0x985B00, 4))[0],
               flags=(hex(flags0), hex(struct.unpack("<I", P.rd(f, base + 4, 4))[0])),
               unit0={k: v for k, v in u0.items() if k != "raw"},
               tile_addr=hex(ta), tile0=P.rd(f, ta, 0x2c).hex(),
               energy0=struct.unpack("<i", P.rd(f, ENERGY_G + me * ENERGY_STRIDE * 4, 4))[0],
               events=[])
    print(f"target rec{unit} at ({x0},{y0}) flags {rec['flags']} mpused->{P.rd(f, base+40,1)[0]}")
    print(f"tile {ta:#x} +8={P.rd(f, ta+8, 4)[::-1].hex()} energy={rec['energy0']}")

    # --- 2. wait for the GAME to select it, then press 'f' the instant it does ---
    win = sh('xdotool search --name "Sid Meier"').stdout.split()
    def press(k):
        if win:
            sh(f"xdotool windowfocus {win[0]}")
        sh(f'xdotool key --clearmodifiers {k}')
    sel_landed = order_landed = False
    t0 = time.time()
    while time.time() - t0 < 45 and not sel_landed:
        sel = struct.unpack("<i", P.rd(f, SEL, 4))[0]
        if sel == unit:
            sel_landed = True
            rec["events"].append(f"sel=={unit} at +{time.time()-t0:.2f}s")
            press("f")                     # IMMEDIATELY — no sleep
            time.sleep(0.7)
            if P.rd(f, base + 17, 1)[0] == 4:
                order_landed = True
            else:
                # advisor pane may have swallowed it; one retry on the same selection
                press("f"); time.sleep(0.7)
                order_landed = P.rd(f, base + 17, 1)[0] == 4
            break
        time.sleep(0.05)
    rec["sel_landed"], rec["order_landed"] = sel_landed, order_landed
    rec["order_after_f"] = P.rd(f, base + 17, 1)[0]
    print(f"sel_landed={sel_landed} order_landed={order_landed} "
          f"order={rec['order_after_f']}")

    # --- 3. trigger A: Space on the game-selected ordered unit ---
    if order_landed:
        sel = struct.unpack("<i", P.rd(f, SEL, 4))[0]
        if sel == unit:
            press("space")
            time.sleep(2.0)
            rec["space_at_sel"] = True
        else:
            rec["space_at_sel"] = False
    rec["mid"] = dict(order=P.rd(f, base + 17, 1)[0],
                      mpused=P.rd(f, base + 40, 1)[0],
                      tile=P.rd(f, ta, 0x2c).hex(),
                      energy=struct.unpack("<i", P.rd(f, ENERGY_G + me * ENERGY_STRIDE * 4, 4))[0],
                      pos=[struct.unpack("<H", P.rd(f, base, 4))[0],
                           struct.unpack("<H", P.rd(f, base + 2, 4))[0]])
    print("mid-state:", json.dumps(rec["mid"]))

    # --- 4. trigger B: advance turns unattended ---
    rec["turns"] = []
    tr = open(os.path.join(EVID, f"{tag}_turns.jsonl"), "w")
    for i in range(a.turns):
        before = dict(order=P.rd(f, base + 17, 1)[0],
                      energy=struct.unpack("<i", P.rd(f, ENERGY_G + me * ENERGY_STRIDE * 4, 4))[0],
                      tile=P.rd(f, ta, 0x2c).hex())
        ok = P.service_turn(i, tr, 120, verbose=False)
        # unit array may compact during the turn: re-find by class+position
        units = P.rd(f, UNIT_ARR, MAX_UNITS * 52)
        newu = None
        for i2 in range(MAX_UNITS):
            d = units[i2 * 52:(i2 + 1) * 52]
            if d[14] == 0xFF:
                continue
            typ = struct.unpack("<H", d[10:12])[0]
            if (classes[typ * 52] & 0xFF) == 9 and d[14] == me:
                newu = i2
                break
        after = dict(unit=newu, order=P.rd(f, UNIT_ARR + newu * 52 + 17, 1)[0],
                     energy=struct.unpack("<i", P.rd(f, ENERGY_G + me * ENERGY_STRIDE * 4, 4))[0],
                     tile=P.rd(f, ta, 0x2c).hex(),
                     year=struct.unpack("<I", P.rd(f, 0x985B00, 4))[0],
                     advanced=bool(ok))
        rec["turns"].append(dict(before=before, after=after))
        print(f"turn {i+1}: order {before['order']}->{after['order']} "
              f"energy {before['energy']}->{after['energy']} "
              f"tile+8 {before['tile'][16:24]}->{after['tile'][16:24]} advanced={ok}")
        if newu is not None and newu != unit:
            unit = newu
            base = UNIT_ARR + unit * 52

    with open(os.path.join(EVID, f"{tag}_watch.json"), "w") as fh:
        json.dump(rec, fh, indent=1)
    print("saved:", os.path.join(EVID, f"{tag}_watch.json"))


if __name__ == "__main__":
    main()
