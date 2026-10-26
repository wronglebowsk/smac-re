#!/usr/bin/env python3
"""M56 — WHY DOES NOTHING GET BUILT? Predict per-base production at the round
boundary from the queue fields, then verify the prediction after the flip.

Fields (NAMED.md M53i-k, cross-checked against ghidra_out/shard_012.c here):
  base+0x4c pending, +0x50..+0x74 queue item ids (0xffffffda = empty slot),
  +0x40 MINERAL STORAGE, +0x3c progress accumulator (display-only per M53k),
  +0xcc build rate, +0xd0 net income, +0x8c.. facility bitmap.
  Completion (0x4ef6d0 pay path): minerals >= price, price = 0x4e40a0(owner,1,-1)
  x type_cost(0x98ad88+type*0x34 byte +41); pay debits minerals (0x4f0ca6),
  the POP (0x4ef5d0) decrements pending, left-shifts the queue, and the unit is
  created on the base tile (FUN_005ab650).

Floors (never weakened): every prediction verified, every observed arrival
predicted, bookkeeping exact, >=1 POSITIVE prediction verified (non-vacuous).
"""
import argparse, json, struct, subprocess, sys, time
from collections import Counter
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m55_boundary as M

BASE_ARR, BASE_SZ = M.BASE_ARR, M.BASE_SZ
TYPE_ARR, TYPE_STRIDE = 0x98AD88, 0x34
ERA_TABLE = 0x68CBB8
EMPTY = 0xffffffda
EMPTY_S = -38          # the same dword read as signed: the empty-queue marker

def rd32(m, a): return struct.unpack("<i", M.rd(m, a, 4))[0]

def prod_fields(m, i):
    b = M.rd(m, BASE_ARR + i * BASE_SZ, BASE_SZ)
    g = lambda off: struct.unpack("<i", b[off:off+4])[0]
    h = lambda off: struct.unpack("<h", b[off:off+2])[0]
    return dict(i=i, x=h(0), y=h(2), fac=b[4], name=b[19:51].split(b"\0")[0].decode("latin-1","replace"),
                pending=g(0x4c), queue=[g(0x50 + 4*k) for k in range(10)],
                minerals=g(0x40), progress=g(0x3c), rate=g(0xcc), income=g(0xd0),
                fac_bits=struct.unpack("<4I", b[0x8c:0x9c]), flags30=g(0x30))

def all_prod(m):
    n = max(0, min(rd32(m, 0x985AF4), 64))
    return [prod_fields(m, i) for i in range(n)]

def type_cost(m, t):
    return M.rd(m, TYPE_ARR + t * TYPE_STRIDE + 41, 1)[0]

def price_of(m, owner, head):
    """price = 0x4e40a0(owner,1,-1) * type_cost. In-mask owner -> 100% factor 10
    (NAMED M53l: DAT_0092a290=10, DAT_0092ada8=2 -> x1). Out-mask: era-table
    price (0..13) reported, prediction NOT floored for out-mask owners."""
    mask = M.u32(m, 0x985B10)
    in_mask = bool((mask >> owner) & 1)
    cost = type_cost(m, head)
    era = rd32(m, 0x985AEC)
    era_mult = struct.unpack("<i", M.rd(m, ERA_TABLE + era * 4, 4))[0] if 0 <= era < 6 else None
    factor = 10 if in_mask else era_mult
    return dict(in_mask=in_mask, cost=cost, factor=factor,
                price=(10 * cost) if in_mask else (0 if factor in (0, None) else factor * cost))

def predict(m, bases, income_first=False):
    """income_first: the queue processor runs INSIDE the base visit after the
    income add (M56 chain: 0x4ef7f6 income, then 0x4f5a70 -> 0x4ef6d0), so the
    storage the gate compares may already include this round's income. The M56
    acceptance armed storage ABOVE price so the two models were indistinguishable;
    the UI-queued run is the first one where they differ, so it is the test."""
    out = []
    for b in bases:
        if b["pending"] <= 0:
            continue
        head = b["queue"][0]
        pr = price_of(m, b["fac"], head & 0xff if 0 <= head < 0x40 else 0)
        unit = 0 <= head < 0x40
        gate = b["minerals"] + (b["income"] if income_first else 0)
        arrive = unit and pr["in_mask"] and gate >= pr["price"]
        out.append(dict(base=b["i"], name=b["name"], x=b["x"], y=b["y"], fac=b["fac"],
                        head=head, unit_type=head if unit else None, pending=b["pending"],
                        minerals=b["minerals"], gate_minerals=gate, income=b["income"],
                        price=pr["price"], factor=pr["factor"],
                        cost=pr["cost"], in_mask=pr["in_mask"], predict_arrive=arrive,
                        queue=b["queue"]))
    return out

def keyf(u): return (u["x"], u["y"], u["type"], u["owner"])

def arrivals_on_bases(before_u, after_u, tile2base):
    cb, ca = Counter(keyf(u) for u in before_u), Counter(keyf(u) for u in after_u)
    net = ca - cb
    return [dict(t=k, n=v, base=tile2base.get(k[:2])) for k, v in net.items()
            if v > 0 and tile2base.get(k[:2]) is not None]

def press_return():
    subprocess.run(["xdotool", "key", "--clearmodifiers", "Return"], check=False)


def press_key(k):
    subprocess.run(["xdotool", "key", "--clearmodifiers", k], check=False)

def find_win():
    try:
        return subprocess.check_output(["xdotool", "search", "--name", "Sid Meier"],
                                       text=True).split()[0]
    except subprocess.CalledProcessError:
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", default=None)
    ap.add_argument("--fixture", default=None)
    ap.add_argument("--boundaries", type=int, default=3)
    ap.add_argument("--arm", default=None, help="base index to arm (controlled poke)")
    ap.add_argument("--arm-type", type=int, default=2)
    ap.add_argument("--arm-minerals", type=int, default=100)
    ap.add_argument("--ui-queued", type=int, default=None,
                    help="M57: base index whose queue the GAME filled through the BUILD UI "
                         "(no memory write at all; the run must prove 0 writes)")
    ap.add_argument("--poll", type=float, default=0.002)
    ap.add_argument("--settle", type=float, default=0.3)
    ap.add_argument("--timeout", type=float, default=300.0)
    ap.add_argument("--no-poke-hold", action="store_true")
    ap.add_argument("--stuck", type=float, default=12.0,
                    help="seconds without a flip before a popup is clicked OK")
    a = ap.parse_args()

    trace_path = a.trace or f"evidence/trace_m56_build_{time.strftime('%Y%m%d_%H%M%S')}.jsonl"
    trace = []
    log = trace.append

    if a.fixture:
        fx = json.load(open(a.fixture))
        pid = -1; m = None
        natural_empty = fx.get("natural_queues_empty", False)
        log(dict(event="fixture", path=a.fixture))
        rounds = fx["rounds"]
        armed = fx.get("armed")
        ui = fx.get("ui_queue")
        writes = fx.get("writes", 0)
    else:
        pid = M.find_pid()
        m = open(f"/proc/{pid}/mem", "rb+", 0)
        natural = all_prod(m)
        natural_empty = all(b["pending"] <= 0 for b in natural)
        log(dict(event="natural_state", year=natural and M.u32(m, 0x985B00),
                 pending_bases=[b["i"] for b in natural if b["pending"] > 0],
                 all_queues_empty=natural_empty,
                 heads={b["i"]: b["queue"][0] for b in natural if b["queue"][0] != -38}))
        writes = 0
        ui = None
        armed = None
        if a.ui_queued is not None:
            # M57: the queue was written by the GAME's own BUILD UI dispatch
            # (0x417ee0 -> head store 0x418b57 -> pending store 0x418ad3), so this
            # run makes NO memory write of any kind. The precondition is the
            # milestone's point: at run start the base cannot yet pay (minerals <
            # price), so a later completion cannot have been armed by us.
            bi = int(a.ui_queued)
            b0 = prod_fields(m, bi)
            pr = price_of(m, b0["fac"], b0["queue"][0] if 0 <= b0["queue"][0] < 0x40 else 0)
            ui = dict(base=bi, name=b0["name"], x=b0["x"], y=b0["y"], head=b0["queue"][0],
                      pending=b0["pending"], minerals=b0["minerals"], income=b0["income"],
                      price=pr["price"], cost=pr["cost"], in_mask=pr["in_mask"],
                      provenance="ui", writes=0)
            log(dict(event="ui_queue", **ui))
            bad = []
            if b0["pending"] <= 0:
                bad.append(f"pending {b0['pending']} (queue is EMPTY - nothing for the game to build)")
            if not (0 <= b0["queue"][0] < 0x40):
                bad.append(f"head {b0['queue'][0]} is not a unit type")
            if b0["minerals"] >= pr["price"]:
                bad.append(f"minerals {b0['minerals']} >= price {pr['price']} at run start "
                           f"(the completion would be indistinguishable from an armed one)")
            if bad:
                log(dict(event="ui_precondition_fail", reasons=bad))
                print("FAIL ui-queued preconditions: " + "; ".join(bad))
                M._dump(trace_path, trace)
                sys.exit(1)
        else:
            if not a.no_poke_hold:
                M.poke_hold(m, trace); writes += 1
            armed = None
            if a.arm is not None:
                bi = int(a.arm)
                a0 = BASE_ARR + bi * BASE_SZ
                m.seek(a0 + 0x4c); m.write(struct.pack("<i", 1))
                m.seek(a0 + 0x50); m.write(struct.pack("<i", a.arm_type))
                for k in range(1, 10):
                    m.seek(a0 + 0x50 + 4*k); m.write(struct.pack("<I", EMPTY))
                m.seek(a0 + 0x40); m.write(struct.pack("<i", a.arm_minerals))
                writes += 1
                back = prod_fields(m, bi)
                armed = dict(base=bi, type=a.arm_type, minerals=a.arm_minerals, readback=back)
                log(dict(event="arm", base=bi, unit_type=a.arm_type, minerals=a.arm_minerals, readback=back))
        rounds = []
        our = rd32(m, M.G["our_player"][0])
        OK_XY = (630, 247)   # "OK" on the Operations Director popup (measured 2221:
                             # the popup that appears when a produced unit is disbanded)
        for rnum in range(a.boundaries):
            before = M.snapshot(m)
            bases_before = all_prod(m)
            preds = predict(m, bases_before, income_first=bool(ui))
            y0 = before["globals"]["year"]
            log(dict(event="round_before", r=rnum, year=y0, snap=before,
                     prod=bases_before, predictions=preds))
            # Close the turn and watch for the year flip from memory. Return every
            # 2 s UNCONDITIONALLY: it is consumed as turn-end by the human loop, as
            # dismissal by modal event dialogs, and as OK by popups. If the game
            # sits > a_stuck s without flipping, a popup with a non-Return default
            # (Operations Director: "Zoom to Base Control" is the default row and
            # Return cycles the options instead of closing) is clicked at OK.
            t0 = time.time(); timeline = []; last = None
            last_press = 0.0; last_ok = 0.0; last_h = 0.0; flip_t = None
            deadline = time.time() + a.timeout
            while time.time() < deadline:
                row = M.timeline_row(m)
                if last is None or any(row[k] != last[k] for k in row):
                    timeline.append(dict(t=round(time.time()-t0, 3), **row)); last = row
                if flip_t is None and row["year"] != y0:
                    flip_t = time.time(); log(dict(event="flip", r=rnum, row=row))
                if time.time() - last_press > 2.0:
                    press_return(); log(dict(event="press_enter", r=rnum,
                                             t=round(time.time()-t0, 3))); last_press = time.time()
                if flip_t is None and time.time() - t0 > 8.0 and \
                        row["cur_player"] == our and time.time() - last_h > 4.0:
                    # A produced unit arrives order 0 (actionable) and the auto-end
                    # gate will NOT fire while an actionable unit exists; the cursor
                    # parks on it. 'h' gives the CURSOR unit HOLD (measured 2222:
                    # one 'h' -> turn_flags 0->2, cur_player 3->6) and closes the turn.
                    press_key("h"); log(dict(event="press_hold", r=rnum,
                                             t=round(time.time()-t0, 3))); last_h = time.time()
                if flip_t is None and time.time() - t0 > max(15.0, a.stuck) and \
                        time.time() - last_ok > 6.0:
                    win = find_win()
                    if win:
                        subprocess.run(["xdotool", "windowfocus", win], check=False)
                        subprocess.run(["xdotool", "mousemove", str(OK_XY[0]), str(OK_XY[1])],
                                       check=False)
                        subprocess.run(["xdotool", "click", "1"], check=False)
                    log(dict(event="click_ok", r=rnum, t=round(time.time()-t0, 3), xy=OK_XY))
                    last_ok = time.time()
                if flip_t is not None and time.time() - flip_t >= a.settle:
                    break
                time.sleep(a.poll)
            log(dict(event="timeline", r=rnum, rows=timeline))
            if flip_t is None:
                log(dict(event="round_fail", r=rnum, why="no year flip"))
                rounds.append(dict(r=rnum, before=before, after=M.snapshot(m),
                                   prod_before=bases_before, prod_after=all_prod(m),
                                   predictions=preds, timeline=timeline))
                break
            after = M.snapshot(m)
            bases_after = all_prod(m)
            log(dict(event="round_after", r=rnum, snap=after, prod=bases_after))
            rounds.append(dict(r=rnum, before=before, after=after,
                               prod_before=bases_before, prod_after=bases_after,
                               predictions=preds, timeline=timeline))

    checks = []
    def chk(name, ok, detail): checks.append(dict(check=name, ok=bool(ok), detail=detail))

    n_flip = 0; pos_pred = 0; pos_ok = 0
    for rd_ in rounds:
        gb, ga = rd_["before"]["globals"], rd_["after"]["globals"]
        dy = ga["year"] - gb["year"]
        flipped = dy >= 1
        n_flip += 1 if flipped else 0
        cp_seen = sorted({t["cur_player"] for t in rd_["timeline"]})
        chk(f"r{rd_['r']} boundary: year flipped exactly +1",
            dy == 1, f"year {gb['year']}->{ga['year']} (delta {dy}); cur_player walk {cp_seen}")
        chk(f"r{rd_['r']} boundary: player walk came home to us after the flip",
            ga["cur_player"] == gb["our_player"],
            f"cur_player before {gb['cur_player']} after {ga['cur_player']}; walk seen "
            f"{sorted({t['cur_player'] for t in rd_['timeline']})} (a round may start mid-walk)")
        tile2base = {(b["x"], b["y"]): b for b in rd_["prod_before"]}
        obs = arrivals_on_bases(rd_["before"]["units"], rd_["after"]["units"], tile2base)
        pred_unit = [p for p in rd_["predictions"] if p["predict_arrive"]]
        pos_pred += len(pred_unit)
        pred_keys = {(p["x"], p["y"], p["unit_type"], p["fac"]): p for p in pred_unit}
        # F1: every predicted unit arrival observed (net +n on the base tile)
        for k, p in pred_keys.items():
            got = next((o for o in obs if (o["t"]) == k), None)
            ok = got is not None and got["n"] >= 1
            pos_ok += 1 if ok else 0
            chk(f"r{rd_['r']} prediction base {p['base']} ({p['x']},{p['y']}) type {p['unit_type']}",
                ok, f"predicted (pending {p['pending']}, minerals {p['minerals']} >= price {p['price']}); "
                    f"observed net {got['n'] if got else 0} of that tuple on the base tile")
        # F2: every observed net arrival on a base tile was a prediction (or cargo)
        for o in obs:
            k = o["t"]
            if k in pred_keys: continue
            # cargo/unload materialises with a nonzero order (M55 #5); a produced
            # unit arrives order 0. Label, and floor on order-0 arrivals.
            cand = [u for u in rd_["after"]["units"] if keyf(u) == k]
            orders = sorted({u["order"] for u in cand})
            zero_order = 0 in orders
            ours = (o["base"]["fac"] == gb["our_player"])
            chk(f"r{rd_['r']} unexplained ORDER-0 arrival on OUR base {o['base']['i']}",
                (not ours) or (not zero_order),
                f"net +{o['n']} with orders {orders} on base {o['base']['i']} "
                f"(fac {o['base']['fac']}, ours={ours}); enemy-side arrivals are REPORTED "
                f"(their queues refill inside their own AI turn - confounded, M55 #5)")
        # F3: queue bookkeeping on bases that were pending before the flip
        for pb in rd_["prod_before"]:
            if pb["pending"] <= 0: continue
            pa = next(b for b in rd_["prod_after"] if b["i"] == pb["i"])
            p = next((pp for pp in rd_["predictions"] if pp["base"] == pb["i"]), None)
            if p and p["predict_arrive"]:
                chk(f"r{rd_['r']} bookkeeping base {pb['i']}: pending decremented",
                    pa["pending"] == pb["pending"] - 1,
                    f"pending {pb['pending']}->{pa['pending']}")
                chk(f"r{rd_['r']} bookkeeping base {pb['i']}: minerals debited by >= price",
                    pb["minerals"] - pa["minerals"] >= p["price"],
                    f"minerals {pb['minerals']}->{pa['minerals']} (delta {pa['minerals']-pb['minerals']}), "
                    f"price {p['price']} (clamp B at 0x4f0cc3-0x4f0ce9 re-caps storage after the pay)")
                chk(f"r{rd_['r']} bookkeeping base {pb['i']}: queue left-shifted",
                    pa["queue"] == pb["queue"][1:] + [pb["queue"][-1]] or
                    pa["queue"][:max(pb["pending"]-1,0)] == pb["queue"][1:pb["pending"]] or
                    (pa["pending"] == 0 and pa["queue"][0] in (-38, pb["queue"][1])),
                    f"queue {pb['queue'][:3]}->{pa['queue'][:3]}")
            else:
                chk(f"r{rd_['r']} bookkeeping base {pb['i']}: NOT predicted to arrive -> queue held",
                    pa["pending"] == pb["pending"] and pa["queue"] == pb["queue"],
                    f"pending {pb['pending']}->{pa['pending']}, head {pb['queue'][0]}->{pa['queue'][0]} "
                    f"(minerals {pb['minerals']} vs price {p['price'] if p else '?'})")
    chk("boundaries observed >= 2", n_flip >= 2, f"{n_flip} of {len(rounds)} rounds flipped")
    chk("at least 1 POSITIVE prediction verified (non-vacuous)",
        pos_pred >= 1 and pos_ok == pos_pred, f"{pos_ok}/{pos_pred} positive predictions verified")
    if ui is not None:
        chk("queue provenance: GAME-filled, zero memory writes by this script",
            writes == 0 and ui.get("provenance") == "ui" and ui.get("pending", 0) > 0,
            f"provenance {ui.get('provenance')} pending {ui.get('pending')} head {ui.get('head')} "
            f"on base {ui.get('base')} ({ui.get('name')}); memory writes: {writes}")
        chk("completion NOT armed: storage below price at run start",
            ui.get("minerals", 10**9) < ui.get("price", 0),
            f"minerals {ui.get('minerals')} < price {ui.get('price')} "
            f"(income {ui.get('income')}/round pays the rest)")

    empty_all = natural_empty if not a.fixture else fx.get("natural_queues_empty", False)
    log(dict(event="verdict", checks=checks, ok=all(c["ok"] for c in checks),
             armed=armed, natural_queues_empty_at_start=empty_all,
             positive_predictions=pos_pred, positive_verified=pos_ok))
    M._dump(trace_path, trace)
    for c in checks:
        print(f"  {'ok ' if c['ok'] else 'BAD'} {c['check']} — {c['detail']}")
    if armed:
        rb = armed["readback"]
        print(f"  armed: base {armed['base']} pending {rb['pending']} head {rb['queue'][0]} "
              f"minerals {rb['minerals']} (read back)")
    print(f"  natural state: all queues empty at run start: {empty_all}")
    print(f"  positive predictions {pos_ok}/{pos_pred} verified; boundaries {n_flip}/{len(rounds)}")
    print(f"  trace: {trace_path}")
    if all(c["ok"] for c in checks):
        prov = (f" — queue filled by the GAME's BUILD UI (0 memory writes), "
                f"paid by income at {ui.get('income')}/round") if ui is not None else ""
        print(f"PASS production prediction: {pos_ok} verified unit arrivals over {n_flip} "
              f"boundaries, every prediction and every observed arrival accounted, "
              f"queue bookkeeping exact{prov}")
        sys.exit(0)
    print("FAIL production prediction accounting")
    sys.exit(1)

if __name__ == "__main__":
    main()
