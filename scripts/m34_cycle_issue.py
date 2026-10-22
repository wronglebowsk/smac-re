#!/usr/bin/env python3
"""M34 v6: cycle the game's own selection onto our Former, issue Farm, end turn,
watch the EXECUTE half of the effect. No tracer anywhere.

Facts this leans on (all proven earlier sessions):
  * Selection 0x91b5bc is game-owned: pokes under a tracer never land (try3), pokes
    no-tracer work but the pump revalidates within a frame (M33). The ONLY reliable
    selection is the game's own cycle.
  * After 'h' (HOLD) or 'r' the selection ROLLS to the next unit (M33 note) — so
    HOLDing the cycle's current unit should walk the cycle forward.
  * 'f' lands only on the SELECTED unit (setter runs in-handler on 0x91b5bc).
  * (45,7) is farm-legal (M33 try5 store landed there); (45,11) is not (mask&0x20
    remap -> HASFARM abort).
  * Explore orders execute during end-of-turn (units moved across M32->now). Whether a
    terraform order executes at end-of-turn (or only via Space on the selected unit,
    FUN_004d1e90 -> FUN_00529090(unit,-1,0) -> FUN_00585720 dir 0x8) is THE question.
  * Debit site 0x4d561a writes energy 0x94d650[player*0x82f]; refund 0x4d5908.

Steps:
  1. identify our Former (class 9) + its tile; snapshot tile/energy/order.
  2. loop: read sel; if sel==Former -> press 'f', poll order==4. else if sel is one of
     our actionable units -> press 'h' (HOLD, safe no-op) to roll the cycle; poll.
  3. snapshot after the order; press Space (trigger A) if sel still == Former.
  4. advance turns via service_turn (trigger B = end-of-turn machinery); snapshot
     order/energy/tile before and after each turn; re-find the Former after compaction.
Usage: m34_cycle_issue.py [--turns 2] [--max-holds 12] [--tag m34v6]
"""
import argparse, json, os, struct, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "evidence")
UNIT_ARR, CLASS_TBL, MAX_UNITS = 0x933278, 0x98ADB2, 300
PLAYER, SEL, YEAR = 0x91B5B4, 0x91B5BC, 0x985B00
ENERGY_G, ENERGY_STRIDE = 0x94D650, 0x82F
TILE_BASE, ROW_PITCH = 0x92AE14, 40


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          env={**os.environ, "DISPLAY": ":99"})


def tile_addr(x, y):
    return TILE_BASE + (ROW_PITCH * y + (x >> 1)) * 0x2c


def scan_units(f):
    units = P.rd(f, UNIT_ARR, MAX_UNITS * 52)
    classes = P.rd(f, CLASS_TBL, 1024 * 52)
    out = {}
    for i in range(MAX_UNITS):
        d = units[i * 52:(i + 1) * 52]
        if d[14] == 0xFF:
            continue
        typ = struct.unpack("<H", d[10:12])[0]
        out[i] = dict(cls=classes[typ * 52] & 0xFF, owner=d[14], order=d[17],
                      x=struct.unpack("<H", d[0:2])[0], y=struct.unpack("<H", d[2:4])[0],
                      mpused=d[40], flags=struct.unpack("<I", d[4:8])[0])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--turns", type=int, default=2)
    ap.add_argument("--max-holds", type=int, default=12)
    ap.add_argument("--tag", default="m34v6")
    a = ap.parse_args()
    tag = a.tag

    pid = int(sh("pgrep -x terran.exe | head -1").stdout.split()[0])
    assert "TracerPid:\t0" in sh(f"grep TracerPid /proc/{pid}/status").stdout, "tracer!"
    _, f = P.mem()
    me = struct.unpack("<I", P.rd(f, PLAYER, 4))[0]
    U = scan_units(f)
    formers = [i for i, u in U.items() if u["cls"] == 9 and u["owner"] == me]
    if not formers:
        sys.exit("no Former owned by us")
    unit = formers[0]
    x0, y0 = U[unit]["x"], U[unit]["y"]
    ta = tile_addr(x0, y0)
    energy = lambda: struct.unpack("<i", P.rd(f, ENERGY_G + me * ENERGY_STRIDE * 4, 4))[0]
    order = lambda u: P.rd(f, UNIT_ARR + u * 52 + 17, 1)[0]
    rec = dict(pid=pid, unit=unit, year=struct.unpack("<I", P.rd(f, YEAR, 4))[0],
               pos=(x0, y0), tile_addr=hex(ta),
               tile0=P.rd(f, ta, 0x2c).hex(), energy0=energy(),
               order0=U[unit]["order"], flags0=hex(U[unit]["flags"]),
               sel0=struct.unpack("<i", P.rd(f, SEL, 4))[0], holds=[], events=[])
    print(f"target rec{unit} at ({x0},{y0}) order={rec['order0']} sel={rec['sel0']} "
          f"energy={rec['energy0']} tile+8={P.rd(f, ta+8, 4)[::-1].hex()}")

    win = sh('xdotool search --name "Sid Meier"').stdout.split()
    def press(k):
        if win:
            sh(f"xdotool windowfocus {win[0]}")
        sh(f'xdotool key --clearmodifiers {k}')

    # --- 2. roll the cycle with 'h' until the game selects our Former; then 'f' ---
    order_landed = False
    holds = 0
    t0 = time.time()
    while time.time() - t0 < 90:
        sel = struct.unpack("<i", P.rd(f, SEL, 4))[0]
        if sel == unit:
            press("f")                                   # setter in-handler
            time.sleep(0.8)
            if order(unit) == 4:
                order_landed = True
                rec["events"].append(f"'f' landed after {holds} holds")
                break
            press("f"); time.sleep(0.8)                  # pane may have swallowed it
            if order(unit) == 4:
                order_landed = True
                rec["events"].append(f"'f' landed (retry) after {holds} holds")
                break
            rec["events"].append(f"sel=={unit} but 'f' did not land (order={order(unit)})")
            break
        # not ours: HOLD the cycle's current unit (safe no-op) to advance the cycle
        if sel in U and U[sel]["owner"] == me and holds < a.max_holds:
            press("h")
            holds += 1
            rec["holds"].append(dict(n=holds, held=sel, at=round(time.time() - t0, 1)))
            print(f"hold {holds}: sel={sel} ({U[sel]['x']},{U[sel]['y']}) cls={U[sel]['cls']}")
            time.sleep(0.7)
        else:
            time.sleep(0.4)
    rec["order_after_f"] = order(unit)
    rec["order_landed"] = order_landed
    print(f"order_landed={order_landed} order={rec['order_after_f']} sel="
          f"{struct.unpack('<i', P.rd(f, SEL, 4))[0]}")

    # --- 3. trigger A: Space while the game still has our unit selected ---
    sel = struct.unpack("<i", P.rd(f, SEL, 4))[0]
    if order_landed and sel == unit:
        press("space"); time.sleep(2.0)
        rec["space_pressed"] = True
    else:
        rec["space_pressed"] = False
    rec["mid"] = dict(order=order(unit), energy=energy(),
                      tile=P.rd(f, ta, 0x2c).hex(), sel=sel)
    print("mid:", json.dumps(rec["mid"]))

    # --- 4. trigger B: end-of-turn machinery ---
    tr = open(os.path.join(EVID, f"{tag}_turns.jsonl"), "w")
    rec["turns"] = []
    for i in range(a.turns):
        U = scan_units(f)
        # re-find Former after possible compaction (prefer same tile)
        cand = [k for k, u in U.items() if u["cls"] == 9 and u["owner"] == me
                and (u["x"], u["y"]) == (x0, y0)] or \
               [k for k, u in U.items() if u["cls"] == 9 and u["owner"] == me]
        if not cand:
            rec["turns"].append({"error": "Former gone"}); break
        unit = cand[0]; base = UNIT_ARR + unit * 52
        before = dict(order=order(unit), energy=energy(), tile=P.rd(f, ta, 0x2c).hex(),
                      unit=unit)
        ok = P.service_turn(i, tr, 120, verbose=False)
        after = dict(order=order(unit), energy=energy(), tile=P.rd(f, ta, 0x2c).hex(),
                     year=struct.unpack("<I", P.rd(f, YEAR, 4))[0], advanced=bool(ok))
        rec["turns"].append(dict(unit=unit, before=before, after=after))
        print(f"turn {i+1}: order {before['order']}->{after['order']} "
              f"energy {before['energy']}->{after['energy']} "
              f"tile+8 {before['tile'][16:24]}->{after['tile'][16:24]} advanced={ok}")

    with open(os.path.join(EVID, f"{tag}_watch.json"), "w") as fh:
        json.dump(rec, fh, indent=1)
    print("saved:", os.path.join(EVID, f"{tag}_watch.json"))


if __name__ == "__main__":
    main()
