#!/usr/bin/env python3
"""M56 — WHY DOES NOTHING GET BUILT? Predict per-base production at the round
boundary from the queue fields, then verify the prediction after the flip.

Fields (NAMED.md M53i-k, cross-checked against ghidra_out/shard_012.c here):
  +0x4c pending, +0x50..+0x74 queue item ids (0xffffffda = empty slot),
  +0x40 MINERAL STORAGE, +0x3c progress accumulator (display-only per M53k),
  +0xcc build rate, +0xd0 net income, +0x8c.. facility bitmap.
  Completion (0x4ef6d0 pay path): minerals >= price of whatever unit TYPE sits in
  the HEAD SLOT +0x50, price = 0x4e40a0(owner,1,-1) x type_cost(0x98ad88+type*52
  byte +41); the pay store 0x4efedd DOMINATES the create-unit call 0x5ab650
  @ 0x4eff4e (scratch/m59/dom.py) and nothing between them reads pending.
  M59: PENDING IS NOT A GATE — 0x4c only gates the POP (FUN_004ef5d0 returns at
  0x4ef5f4 when pending == 0), which left-shifts the slots; with pending 0 the
  head is never consumed, so the base re-buys the same type whenever it can pay
  (scripts/m59_head.py measured exactly that: minerals 9 -> 0 + a unit on the
  tile, pending 0 before and after, control base untouched).

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

# M60: the create-unit call 0x5ab650 @ 0x4eff4e is gated at 0x4eff32 by
# `mov eax, ds:0x8f0d70; test eax,eax; jne 0x4eff5c` — a PROCESS GLOBAL (not a
# base field; the old note's "[base+0x10]" is wrong: base+0x10 holds 0x4b000000
# on Korolev Center).  Nothing in .text writes it (1 reference in the whole
# section dump) and an hw watchpoint stayed silent over 2 boundaries, but a
# nonzero value DOES suppress the create (poke 1 -> paid, no unit; poke 0 ->
# paid, unit arrives), so a PASS run records its value in every sampled row.
GUARD_ADDR = 0x8f0d70
CUR_BASE_G = 0x8f0d60   # the current-base POINTER (929 .text references).  0x4f5a70
                        # stores it per base BEFORE the pipeline that ends in the
                        # production visit 0x4ef6d0, so while it names record B, B is
                        # the base the round processor is visiting — measured in
                        # scripts/m60_guard.py --stage watch (evidence/m61a_seq.jsonl
                        # prints VISIT/PAY/CREATE for exactly the base it names).
GUARD_SAMPLES = []

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

def cur_base(m):
    """Resolve ds:0x8f0d60 to the base record it names, if it names one.

    M61: the round processor stores the record pointer there per base, before the
    pipeline that reaches the production visit 0x4ef6d0, so the pointer says which
    base the round processor has visited LAST.  That is what turns an F1 arrival
    "deferral" from a tolerance into an attributed measurement: either the
    after-snapshot beat this base's visit (the pointer names another base), or it
    already named THIS base and the visit had run."""
    p = rd32(m, CUR_BASE_G)
    n = max(0, min(rd32(m, 0x985AF4), 64))
    if BASE_ARR <= p < BASE_ARR + n * BASE_SZ and (p - BASE_ARR) % BASE_SZ == 0:
        i = (p - BASE_ARR) // BASE_SZ
        return dict(ptr=p, i=i, name=prod_fields(m, i)["name"])
    return dict(ptr=p, i=None, name=None)

def type_cost(m, t):
    return M.rd(m, TYPE_ARR + t * TYPE_STRIDE + 41, 1)[0]

def trunc_div(a, b):
    """C signed division truncated toward zero — what the imul-magic + sar at
    0x4e4128-0x4e4139 / 0x4e4148-0x4e4159 / 0x4e4205-0x4e4217 actually does."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def cost_multiplier(m, owner):
    """FUN_004e40a0(owner, 1, -1), the value the pay gate's `edi` is built from,
    re-implemented line-for-line from the disasm (scratch/m574/text.txt call site
    0x4efa2c-0x4efa52; body evidence/m53i_fn4e40a0.txt = ghidra_out/shard_012.c
    :13825-13880).  M58: NOTHING here is a constant chosen to fit an observation —
    every input is read from the same memory snapshot the gate is being run on:

      0x4e40a4/0x4e40b5  mask = [0x985b10] & 0xff, tested bit-by-bit LOW BYTE ONLY
                         (sessions-64-64.md: "4e40a0 tests LOW BYTE ONLY")
      in-mask  -> 10 (0x4e40c0)          out-mask -> era table [0x68cbb8 + era*4]
                         ({13,12,11,10,8,7}, sessions-64-64.md, read live here; the
                          0x4e40fc-0x4e410b subtractions are NOT modelled — reported)
      0x4e4110-0x4e4139 rescale by [0x92a294] (param_2 == 1 picks the +4 variant)
      0x4e413b-0x4e4175 rescale by [0x92ada8]: 1 -> *9/10, 0 -> *8/10, else unchanged
      0x4e421f-0x4e430f switch on the dword at 0x94d6a0 + owner*0x20bc (sessions-56
                         calls it the faction government field; 0 = identity)

    Live in the current box (scripts/m58_price.py): mask&0xff = 0x08 (owner 3 in),
    [0x92a294] = 10, [0x92ada8] = 1, gov field 0 -> factor_tenths 9, and the tracer
    read edi = 9 at 0x4efa52 twice (evidence/trace_m574b/c.jsonl).  The 10 the M56
    model used was the session-56 game's state ([0x92ada8] = 2), not a law."""
    mask = M.u32(m, 0x985B10) & 0xff
    in_mask = bool(mask & (1 << (owner & 0x1F)))
    era = rd32(m, 0x985AEC)
    era_mult = (struct.unpack("<i", M.rd(m, ERA_TABLE + era * 4, 4))[0]
                if 0 <= era < 6 else None)
    if in_mask:
        v, why = 10, "in-mask -> 10 (0x4e40c0)"
    else:
        v = 0 if era_mult is None else era_mult
        why = (f"out-mask -> era table[{era}] = {era_mult} (0x4e40fe; the "
               f"FUN_00531090/government subtractions at 0x4e40fc-0x4e410b are "
               f"not modelled)")
    scale = rd32(m, 0x92A294)
    if scale != 10:
        v = trunc_div(scale * v, 10)
    ada8 = rd32(m, 0x92ADA8)
    if ada8 == 1:
        v = trunc_div(v * 9, 10)
    elif ada8 == 0:
        v = trunc_div(v * 8, 10)
    gov = rd32(m, 0x94D6A0 + owner * 0x20BC)
    if gov == 0:
        pass
    elif gov == 1:
        v = trunc_div(v * 9 + 9, 10)
    elif gov == 2:
        v = trunc_div(v * 4 + 4, 5)
    elif gov == 3:
        v = trunc_div(v * 7 + 9, 10)
    elif gov == 4:
        v = trunc_div(v * 3 + 4, 5)
    elif -7 <= gov <= -3:
        v = trunc_div(v * 13 + 9, 10)
    elif gov == -2:
        v = trunc_div(v * 6 + 4, 5)
    elif gov == -1:
        v = trunc_div(v * 11 + 9, 10)
    else:
        v = trunc_div(v + 1, 2)
    return dict(in_mask=in_mask, factor=v, mask=mask, era=era, era_mult=era_mult,
                scale_a294=scale, ada8=ada8, gov_field=gov, why=why)


def price_of(m, owner, head):
    """price = 0x4e40a0(owner,1,-1) x type_cost(+41) — the multiplier is DERIVED
    from the live mask / era / difficulty / government inputs (cost_multiplier),
    which is exactly the shape docs/sessions/sessions-56-56.md already described
    as "multiplier x +41".  Out-mask owners: the era-table price is reported and
    the prediction is still NOT floored for them (unchanged since M57)."""
    cm = cost_multiplier(m, owner)
    cost = type_cost(m, head)
    out = dict(cm)
    out["cost"] = cost
    out["price"] = cm["factor"] * cost
    return out

def predict(m, bases, income_first=False):
    """M59 RESTATEMENT — the HEAD SLOT is the queue truth, PENDING is not.

    Static (scratch/m59/queue_census.py + scratch/m59/dom.py, both over
    scratch/m574/text.txt): inside the per-base visit FUN_004ef6d0 the completion
    gate 0x4efa5e `cmp DWORD PTR [ecx+0x40], edi; jge 0x4efadc` compares mineral
    storage against `edi = 0x4e40a0(owner,1,-1) * 0x5ac950([eax+0x50], base, 0)` —
    the price of whatever unit TYPE sits in the head slot.  Nothing between that
    gate and the create-unit call 0x5ab650 @ 0x4eff4e reads [base+0x4c]: the pay
    store 0x4efedd and the create are DOMINATED by the gate-taken block (removing
    the pay block makes 0x4eff4e unreachable from the entry and from the gate), and
    the pop FUN_004ef5d0 — the only thing pending gates (0x4ef5f4 `je 0x4ef684` when
    pending == 0) — is called LATER (0x4f037b / 0x4f0f46) and only ADVANCES the
    queue (left-shift + pending-- + the per-faction queued-count byte).

    Measured (scripts/m59_head.py, 2026-10-26, one variable, internal control):
    Korolev Center idx 17 pending 0 head 2 minerals poked 0 -> 9 (read back), all
    our units held, University Base idx 0 untouched at minerals 0; one turn later
    Korolev minerals 0 (debited exactly the derived price 9), income 0 -> -1 (the
    new unit's upkeep), pending STILL 0, head still 2, and the base tile went
    5 -> 6 units of (type 2, owner 3).  Control University Base: minerals 0,
    6 -> 6 units.  A base with an EMPTY queue still buys the head slot's type.

    Scope: only OUR bases are predicted.  The visit refreshes any base whose owner
    is not in the human mask (or whose +0x38 sign bit is clear) through
    FUN_004e5ae0 -> FUN_004f6030 -> FUN_004e5560 at 0x4ef87e, which is BEFORE the
    gate, so another faction's head at our before-snapshot is not the head its own
    visit will price; their production also happens mid-round inside their own turn
    (M55 #5, confounded).  Enemy arrivals are still REPORTED by check F2.

    income_first: the queue processor runs INSIDE the base visit after the income
    add (0x4ef7f6), so the storage the gate compares may already include this
    round's income (+0xd0)."""
    our = M.u32(m, M.G["our_player"][0])
    out = []
    for b in bases:
        if b["fac"] != our:
            continue
        head = b["queue"][0]
        unit = 0 <= head < 0x40
        if not unit:
            continue      # a facility/project head builds no UNIT; nothing to predict
        pr = price_of(m, b["fac"], head & 0xff)
        gate = b["minerals"] + (b["income"] if income_first else 0)
        arrive = pr["in_mask"] and gate >= pr["price"]
        out.append(dict(base=b["i"], name=b["name"], x=b["x"], y=b["y"], fac=b["fac"],
                        head=head, unit_type=head, pending=b["pending"],
                        minerals=b["minerals"], gate_minerals=gate, income=b["income"],
                        price=pr["price"], factor=pr["factor"],
                        cost=pr["cost"], in_mask=pr["in_mask"], predict_arrive=arrive,
                        pop_expected=bool(arrive and b["pending"] > 0), queue=b["queue"]))
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

    # Fixture replays are reproductions, not evidence: they used to land in evidence/ and be
    # counted by the budget gate and the citation audit (M62 emptied two of them out by hand).
    if a.fixture and not a.trace:
        _fxdir = os.environ.get("TMPDIR", "/tmp")
        trace_path = os.path.join(_fxdir, f"fixture_trace_{time.strftime('%Y%m%d_%H%M%S')}.jsonl")
    else:
        trace_path = a.trace or f"evidence/trace_m56_build_{time.strftime('%Y%m%d_%H%M%S')}.jsonl"
    trace = []
    log = trace.append

    if a.fixture:
        fx = json.load(open(a.fixture))
        pid = -1; m = None
        natural_empty = fx.get("natural_queues_empty", False)
        log(dict(event="fixture", path=a.fixture))
        rounds = fx["rounds"]
        # A fixture timeline carries the guard samples too (the live sampler stamps
        # row["guard"] on every row it records), so the same floor applies to a
        # replayed run — a fixture with no zero-guard samples cannot pass it.
        for _rd in rounds:
            for _row in _rd.get("timeline") or []:
                if "guard" in _row:
                    GUARD_SAMPLES.append(_row["guard"])
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
            # M57-2 lesson: the credit is the base visit's RECOMPUTED +0xd0 (the income
            # add is gated d0>0), so an exact-round prediction only holds while that
            # number is stable and non-zero. Say the arithmetic BEFORE running N rounds
            # (a diagnostic, not a floor): rounds_needed is what the model would need.
            deficit = pr["price"] - b0["minerals"]
            if b0["income"] > 0:
                need = -(-deficit // b0["income"])
                diag = (f"needs {deficit} more minerals at {b0['income']}/round -> "
                        f"~{need} round(s) to the gate")
            else:
                diag = (f"income {b0['income']}: the add is gated d0>0, so storage cannot "
                        f"accrue while it stays 0 — no prediction can land")
            print(f"credit arithmetic: {diag}")
            log(dict(event="credit_arithmetic", deficit=deficit, income=b0["income"],
                     rounds_estimate=(None if b0["income"] <= 0 else need), detail=diag))
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
            last_press = 0.0; last_ok = 0.0; last_h = 0.0; flip_t = None; last_ocr = 0.0
            deadline = time.time() + a.timeout
            while time.time() < deadline:
                row = M.timeline_row(m)
                row["guard"] = rd32(m, GUARD_ADDR)
                GUARD_SAMPLES.append(row["guard"])
                if last is None or any(row[k] != last[k] for k in row):
                    timeline.append(dict(t=round(time.time()-t0, 3), **row)); last = row
                if flip_t is None and row["year"] != y0:
                    flip_t = time.time(); log(dict(event="flip", r=rnum, row=row))
                if time.time() - last_press > 2.0:
                    press_return(); log(dict(event="press_enter", r=rnum,
                                             t=round(time.time()-t0, 3))); last_press = time.time()
                if flip_t is None and time.time() - t0 > 5.0 and \
                        row["cur_player"] == our and time.time() - last_ocr > 3.0:
                    # "SOME OF OUR UNITS HAVE NOT YET MOVED ... do you really want to end
                    # the turn now?" blocks the turn FOREVER and does not take Return: it
                    # needs its YES row clicked, then the OK bar 26 px below
                    # (smac_play.answer_confirm, verified live). Without this the 240 s
                    # escalation sat on that dialog and the year never moved (measured).
                    import smac_play as sp
                    png = sp.freeze("m56c")
                    w = sp.ocr_fast(png)
                    if sp.is_confirm(w):
                        sp.answer_confirm(w)
                        log(dict(event="answer_confirm", r=rnum, t=round(time.time()-t0, 3)))
                        print(f"  [r{rnum}] answered the units-not-moved confirm", flush=True)
                    last_ocr = time.time()
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
                # M57-3: break as soon as the WALK IS HOME after the flip, not after a fixed
                # settle. With everything held the engine auto-ends and the next round can
                # flip 1-2 s after this one (measured r4/r5: year delta 2), so a fixed sleep
                # either misses the walk (settle too short) or swallows the next flip (too
                # long). The floor is unchanged — the after-snapshot must show cur_player ==
                # ours; this just takes it at the right instant.
                if flip_t is not None and (row["cur_player"] == our
                                           or time.time() - flip_t >= max(a.settle, 4.0)):
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
            cur_after = cur_base(m)     # M61: which base the round processor had
                                        # visited when this snapshot was taken
            log(dict(event="round_after", r=rnum, snap=after, prod=bases_after,
                     cur_base=cur_after))
            rounds.append(dict(r=rnum, before=before, after=after,
                               prod_before=bases_before, prod_after=bases_after,
                               predictions=preds, timeline=timeline,
                               cur_base_after=cur_after))

    checks = []
    def chk(name, ok, detail): checks.append(dict(check=name, ok=bool(ok), detail=detail))

    n_flip = 0; pos_pred = 0; pos_ok = 0
    for rk, rd_ in enumerate(rounds):
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
        # F1: every predicted unit arrival observed (net +n on the base tile).
        # M59 saw an arrival that was NOT in its pay window's after-snapshot and only
        # present at the next window's before-snapshot (this file's own r2,
        # evidence/trace_m56_build_20261026_144801.jsonl: Korolev paid in r2 — minerals
        # 8 -> 1, identity check passes — pending still 1 at the r2 after- AND the r3
        # before-snapshot, our unit total 6 at r2-after -> 7 at r3-before).  M61
        # MEASURED why: the create is not late, the SNAPSHOT is early — see the block
        # below.  An arrival is therefore still accepted if it shows in THIS window's
        # diff or is present at the NEXT window's before-snapshot, but only when the
        # round processor had not reached this base at the after-snapshot; the tuple,
        # the tile and the mineral identity are required exactly, within one round.
        for k, p in pred_keys.items():
            got = next((o for o in obs if (o["t"]) == k), None)
            ok = got is not None and got["n"] >= 1
            deferred = beat_visit = False
            cb = rd_.get("cur_base_after") or {}
            if not ok and rk + 1 < len(rounds):
                nxt = arrivals_on_bases(rd_["before"]["units"],
                                        rounds[rk + 1]["before"]["units"], tile2base)
                got2 = next((o for o in nxt if o["t"] == k), None)
                if got2 is not None and got2["n"] >= 1:
                    # M61 MEASUREMENT (scripts/m60_guard.py --stage watch --boundaries 2,
                    # evidence/m61a_seq.jsonl + evidence/m61a_watch.gdblog).  The ordered
                    # stream inside one round, stamped by conditioned breakpoints on the
                    # visit 0x4ef6d0, the pay store 0x4efedd and the create call 0x4eff4e
                    # plus hardware watchpoints on the year 0x985b00 and cur_player
                    # 0x985dcc:  year store 0x51f54f fires while cur_player is STILL 7
                    # -> cur_player 0 -> 1 -> 2 -> 3 -> VISIT University Base -> VISIT
                    # Korolev Center (minerals 9, guard 0) -> PAY 0x4efedd 9->0 with
                    # edi = the price 9 -> CREATE 0x4eff4e -> cur_player 4 -> 5 -> 6 -> 7
                    # -> next year store.  The pay and the create are one and the same
                    # visit invocation (nothing in .text jumps to 0x4efedd, 0x4eff32 or
                    # 0x4eff4e, and the log prints them adjacent with nothing between),
                    # in the round whose year has just flipped, four player switches
                    # after that flip, while cur_player == 3.  So an arrival is never a
                    # round late: the only way it can be missing from this window's
                    # after-snapshot is that the snapshot was taken at cur_player 3
                    # BEFORE player 3's upkeep reached this base.  ds:0x8f0d60 names the
                    # base the round processor reached last, so if the after-snapshot
                    # already named THIS base the visit had run and the arrival really
                    # was absent — a model gap, not a race, and not accepted.
                    if cb.get("name") == p["name"]:
                        beat_visit = True
                    else:
                        ok, deferred = True, True
            pos_ok += 1 if ok else 0
            chk(f"r{rd_['r']} prediction base {p['base']} ({p['x']},{p['y']}) type {p['unit_type']}",
                ok, f"predicted (pending {p['pending']}, minerals {p['minerals']} >= price {p['price']}); "
                    f"observed net {got['n'] if got else 0} of that tuple on the base tile"
                    + ("; ATTRIBUTED, not tolerated: the create lands in the SAME visit "
                       "as the pay (measured PAY->CREATE adjacent at cur_player 3, "
                       "evidence/m61a_seq.jsonl), so this window's after-snapshot beat "
                       "the visit — at that snapshot ds:0x8f0d60 named "
                       f"{cb.get('name') or 'no base record'}"
                       if deferred else "")
                    + ("; NOT deferred: at the after-snapshot ds:0x8f0d60 already named "
                       "this base, so its visit had run and the predicted arrival really "
                       "was absent" if beat_visit else ""))
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
        # F3: queue bookkeeping on bases that were pending before the flip.
        # M58 MEASUREMENTS. (a) evidence/m58pop.gdblog, two visits of Korolev Center
        # 0x95ee40: VISIT#1 storage=9 pend=1 | 0x4ef7f6 add +0 (d0 0) | 0x4efedd pay
        # 9->0 with pend STILL 1 | VISIT#2 storage=0 pend=0 — the pop store 0x4ef641
        # (in FUN_004ef5d0, called from the unit path at 0x4f037b/0x4f0f46) runs
        # strictly AFTER the pay store, so a boundary after-snapshot can land on either
        # side of it: the 2177-box run read pending 1->1 in the pay window and 0 in the
        # next one, the 2151-box run read 1->0 in the pay window (its r2).  Session 96
        # recorded "pending 1 -> 0 in the same visit" as a rule; both orders are real.
        # The mineral identity must also carry the visit's income credit: the store
        # census (scripts/m57_stores.py, evidence/trace_m574c.jsonl) shows the only
        # +0x40 stores a visit reaches are the add at 0x4ef7f6 (== +0xd0 as read at
        # the visit, gated d0 >= 0 at 0x4ef7db) and the pay at 0x4efedd (== price),
        # so storage_after == storage_before + credit - price is EXACT, not a >=.
        # The pre-M58 check ignored the credit the model itself predicts
        # (income_first) and only ever passed because the armed run had income 0.
        for pb in rd_["prod_before"]:
            if pb["fac"] != gb["our_player"]:
                continue      # M59 scope: their head is re-picked by their own visit
            # PAIR BY NAME, not index: the base array compacts mid-run (session 97
            # watched Korolev Center walk index 18 -> 17), so a baked index can name
            # another faction's record in the after-snapshot.
            pa = next(b for b in rd_["prod_after"] if b["name"] == pb["name"])
            p = next((pp for pp in rd_["predictions"] if pp["name"] == pb["name"]), None)
            credit = pb["income"] if pb["income"] > 0 else 0
            if p and p["predict_arrive"]:
                chk(f"r{rd_['r']} bookkeeping base {pb['i']}: minerals identity "
                    f"storage + income - price == storage after",
                    pa["minerals"] == pb["minerals"] + credit - p["price"],
                    f"computed {pb['minerals']} + credit {credit} - price {p['price']} = "
                    f"{pb['minerals'] + credit - p['price']}, observed storage after "
                    f"{pa['minerals']}; the add 0x4ef7f6 and the pay 0x4efedd are the "
                    f"only +0x40 stores a visit reaches (evidence/trace_m574c.jsonl)")
                if pb["pending"] <= 0:
                    # M59: pending 0 does NOT stop the buy (scripts/m59_head.py measured
                    # minerals 9 -> 0 + a unit on the tile with pending 0 before and after).
                    # pending only gates the POP (0x4ef5f4 `je 0x4ef684`), so with pending 0
                    # the pop cannot fire: pending must stay 0 and the slots unchanged.
                    chk(f"r{rk} bookkeeping base {pb['i']}: pending 0 paid -> the pop "
                        f"cannot fire, pending and slots unchanged",
                        pa["pending"] == 0 and pa["queue"] == pb["queue"],
                        f"pending {pb['pending']}->{pa['pending']}, head "
                        f"{pb['queue'][0]}->{pa['queue'][0]} with minerals "
                        f"{pb['minerals']}>=price {p['price']}; the pop 0x4ef5d0 returns "
                        "at 0x4ef5f4 when pending == 0 (scratch/m574/text.txt)")
                else:
                    nb = (next(b for b in rounds[rk + 1]["prod_after"]
                               if b["name"] == pb["name"])
                          if rk + 1 < len(rounds) else None)
                    chk(f"r{rk} bookkeeping base {pb['i']}: pending decremented by exactly "
                        f"1 in the pay window or the window after it",
                        pa["pending"] == pb["pending"] - 1 or
                        (nb is not None and nb["pending"] == pb["pending"] - 1),
                        f"pending {pb['pending']} -> {pa['pending']}"
                        + (f" -> {nb['pending']}" if nb is not None else " (last window)")
                        + "; the pop store 0x4ef641 (FUN_004ef5d0) runs strictly AFTER the "
                        "pay store — evidence/m58pop.gdblog reads pending 1 AT 0x4efedd and 0 "
                        "at the next visit — so a boundary snapshot can land on either side "
                        "(same window: this run's Korolev r2; next window: the 2177-box run "
                        "r6, evidence/trace_m574c-era trace)")
            else:
                # The pop is applied strictly after the pay store, so the window AFTER a
                # verified pay legitimately shows pending - 1 with no new arrival
                # (measured: evidence/m58pop.gdblog, and the 2151-box run r8 pay / r9 pop
                # in evidence/trace_m56_build_20261026_142139.jsonl).  A pending-0 base has
                # no pop to defer (M59), so the exception only applies when pending > 0.
                deferred_pop = (pb["pending"] > 0 and rk > 0 and any(
                    pp["name"] == pb["name"] and pp["predict_arrive"]
                    for pp in rounds[rk - 1]["predictions"]))
                exp_pending = pb["pending"] - (1 if deferred_pop else 0)
                chk(f"r{rd_['r']} bookkeeping base {pb['i']}: NOT predicted to arrive -> "
                    f"queue held" + (" (deferred pop excepted)" if deferred_pop else ""),
                    pa["pending"] == exp_pending and pa["queue"] == pb["queue"],
                    f"pending {pb['pending']}->{pa['pending']} (expected {exp_pending}), "
                    f"head {pb['queue'][0]}->{pa['queue'][0]} "
                    f"(minerals {pb['minerals']} vs price {p['price'] if p else '?'})")
    chk("boundaries observed >= 2", n_flip >= 2, f"{n_flip} of {len(rounds)} rounds flipped")
    chk("at least 1 POSITIVE prediction verified (non-vacuous)",
        pos_pred >= 1 and pos_ok == pos_pred, f"{pos_ok}/{pos_pred} positive predictions verified")
    chk("create guard ds:0x8f0d70 read 0 in every sampled row (no create was suppressed)",
        set(GUARD_SAMPLES) == {0},
        f"{len(GUARD_SAMPLES)} sampled rows, values {sorted(set(GUARD_SAMPLES))}")
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
