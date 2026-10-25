#!/usr/bin/env python3
"""M55: read ONE solo round boundary END TO END from memory (S2 inventory).

THE SOLO HEARTBEAT (ghidra-verified; corrected this session — the 7-stage driver
FUN_00521070 is the MULTIPLAYER branch, mode_flags & 0x10; in solo the stage
counter DAT_0091c630 never moves): main loop FUN_00522850 -> FUN_00520c10
(shard_013.c:11746): each round -> FUN_0051f320 (round++ ; year = 2100 + round,
FUN_005b2c00) -> FUN_0051e700(1) -> walk players 0..7: cur_player = p; upkeep
FUN_005208f0(p) (income + research advance: FUN_0051fe90 -> FUN_005aaa20;
debits+zeroes the faction+4 ledger, shard_013.c:11711-13); factions outside the
human mask (player_mask LOW byte, ours 0x08 = us only) get the AI turn
FUN_0056d0c0(p); we get the human loop FUN_0050f420 -> FUN_0051e700(0).
Research fields (faction record stride 0x20bc = 2095 dwords = 0x82f * 4):
points +0x1a8, queued/current tech +0x1ac (-1 = none; re-pick FUN_005aa880
"Set Research"), save-for-later counter +0x1b4 (DAT_00920434 gate), lab-team
countdown in a parallel dword array at 0x94f8c0 + p*8380. The MP stage machine
(FUN_00521070, UPKEEP4..7 strings): 0 transport/base flags, 1 economy, 2 base
netcode msgs, 3 research, 4 mining, 5 AI FUN_0056d0c0 ("Enemy turn"), 6 events +
autosave ("Writing save file...").

Method: poke every one of our records to HOLD(2) and read the records back, press
ONE Enter (TURN COMPLETE) — measured on this box: 90 s idle with everything held
does NOT advance (semaphores zero, tf&2 set for hours); one Enter fires the
boundary within 0.2 s — then sample the globals at ~2 ms through the boundary and
snapshot before/after, and ACCOUNT for every diff. Acceptance: this script prints
PASS on one real invocation; a hand-typed fixture must FAIL.

Usage:
  python3 scripts/m55_boundary.py [--trace F] [--fixture F] [--poll 0.05]
                                  [--timeout 90] [--settle 1.5] [--no-poke]
"""
import argparse, json, struct, subprocess, sys, time
from collections import Counter

G = {  # name -> (addr, size)  all u32 LE unless noted
    "year": (0x985B00, 4), "round": (0x985AFC, 4), "stage": (0x91C630, 4),
    "cur_player": (0x985DCC, 4), "mode": (0x985DC8, 4),
    "turn_flags": (0x985AE8, 4), "flags_lo": (0x985AE4, 4), "flags_ac4": (0x985AC4, 4),
    "n_units": (0x985AF0, 4), "n_bases": (0x985AF4, 4),
    "player_mask": (0x985B10, 4), "active_mask": (0x985B11, 1),
    "our_player": (0x91B5B4, 4), "research_gate": (0x926BD4, 4),
    "save_later": (0x920434, 4),
}
FACTION_ARR, FACTION_STRIDE = 0x94D650, 8380          # 2095 dwords (0x82f * 4)
FFIELDS = {  # dword index in the faction record (SAVE_FORMAT/NAMED.md + code)
    "energy": 0, "ledger": 1, "upkeep_e0": 0xE0 // 4, "trade_e8": 0xE8 // 4,
    "slider_104": 0x104 // 4, "slider_108": 0x108 // 4, "f13c": 0x13C // 4,
    "f140": 0x140 // 4, "rpoints": 0x1A8 // 4, "rtech": 0x1AC // 4,
    "f1b0": 0x1B0 // 4, "saved_b4": 0x1B4 // 4,
}
LAB_ARR = 0x94F8C0   # lab-team countdown dword at +p*8380; queue ctx at -12/-4
UNIT_ARR, UNIT_SZ = 0x933278, 52
BASE_ARR, BASE_SZ = 0x95DA10, 304
MAX_TYPES = 24


def find_pid():
    out = subprocess.check_output(["pgrep", "-x", "terran.exe"], text=True).split()
    if not out:
        raise SystemExit("no terran.exe running")
    return int(out[0])


def rd(m, addr, n):
    m.seek(addr)
    return m.read(n)


def u32(m, addr):
    return struct.unpack("<I", rd(m, addr, 4))[0]


def parse_unit(i, r):
    return dict(idx=i, x=struct.unpack("<h", r[0:2])[0], y=struct.unpack("<h", r[2:4])[0],
                type=struct.unpack("<H", r[10:12])[0], owner=r[14], order=r[17],
                mp=r[40], flags=struct.unpack("<I", r[4:8])[0], hex=r.hex())


def parse_base(i, r):
    return dict(idx=i, x=struct.unpack("<H", r[0:2])[0], y=struct.unpack("<H", r[2:4])[0],
                faction=r[4], flags30=struct.unpack("<I", r[0x30:0x34])[0],
                name=r[19:51].split(b"\0")[0].decode("latin-1", "replace"), hex=r.hex())


def snapshot(m):
    g = {k: struct.unpack("<I" if sz == 4 else "<B", rd(m, a, sz))[0] for k, (a, sz) in G.items()}
    nu = max(0, min(g["n_units"], 200))
    nb = max(0, min(g["n_bases"], 64))
    units = [parse_unit(i, rd(m, UNIT_ARR + i * UNIT_SZ, UNIT_SZ)) for i in range(nu)]
    units = [u for u in units if u["type"] < MAX_TYPES]
    bases = [parse_base(i, rd(m, BASE_ARR + i * BASE_SZ, BASE_SZ)) for i in range(nb)]
    factions = {}
    for p in range(8):
        if not (g["active_mask"] >> p) & 1:
            continue
        rec = rd(m, FACTION_ARR + p * FACTION_STRIDE, FACTION_STRIDE)
        f = {k: struct.unpack("<i", rec[dw * 4:dw * 4 + 4])[0] for k, dw in FFIELDS.items()}
        lab = rd(m, LAB_ARR + p * FACTION_STRIDE - 12, 12)
        f["lab_ctx_a"], f["labq_b"], f["labcnt"] = struct.unpack("<iii", lab)
        factions[p] = f
    return dict(globals=g, units=units, bases=bases, factions=factions)


def timeline_row(m):
    # batched reads: 0x985ae4..0x985b11 covers flags/counts/round/year/active mask
    blob = rd(m, 0x985AE4, 0x2E)
    def off(a):
        return struct.unpack_from("<I", blob, a - 0x985AE4)[0]
    mode_cp = rd(m, 0x985DC8, 8)
    return {
        "year": off(0x985B00), "round": off(0x985AFC), "stage": u32(m, G["stage"][0]),
        "cur_player": struct.unpack_from("<I", mode_cp, 4)[0],
        "turn_flags": off(0x985AE8), "mode": struct.unpack_from("<I", mode_cp, 0)[0],
        "flags_lo": off(0x985AE4), "flags_ac4": off(0x985AC4),
        "n_units": off(0x985AF0), "n_bases": off(0x985AF4),
        "active_mask": blob[0x985B11 - 0x985AE4],
        "research_gate": u32(m, G["research_gate"][0]),
        "save_later": u32(m, G["save_later"][0]),
    }


def poke_hold(m, trace):
    """Set every one of OUR records to order 2 (HOLD); read back to verify."""
    me = u32(m, G["our_player"][0])
    nu = max(0, min(u32(m, G["n_units"][0]), 200))
    poked = []
    for i in range(nu):
        a = UNIT_ARR + i * UNIT_SZ
        r = rd(m, a, UNIT_SZ)
        if struct.unpack("<H", r[10:12])[0] >= MAX_TYPES or r[14] != me or r[17] == 2:
            continue
        m.seek(a + 17); m.write(b"\x02")
        poked.append((i, r[17], struct.unpack("<h", r[0:2])[0], struct.unpack("<h", r[2:4])[0]))
    back = []
    for i, old, x, y in poked:
        r = rd(m, UNIT_ARR + i * UNIT_SZ, UNIT_SZ)
        back.append(dict(idx=i, from_order=old, to_order=r[17], x=x, y=y,
                         owner_ok=r[14] == me))
    trace.append(dict(event="poke_hold", poked=[dict(idx=i, from_order=o, x=x, y=y)
                                              for i, o, x, y in poked], readback=back,
                    all_held=all(b["to_order"] == 2 and b["owner_ok"] for b in back)))
    return poked


def multiset_diff(before, after, key="hex"):
    cb, ca = Counter(u[key] for u in before), Counter(u[key] for u in after)
    added = list((ca - cb).elements())
    removed = list((cb - ca).elements())
    return added, removed


def base_lookup(bases):
    return {(b["x"], b["y"]): b for b in bases}


def account(before, after, timeline, checks):
    def ck(name, ok, detail):
        checks.append(dict(check=name, ok=bool(ok), detail=detail))

    gb, ga = before["globals"], after["globals"]
    me = gb["our_player"]
    bf = {int(k): v for k, v in before["factions"].items()}
    af = {int(k): v for k, v in after["factions"].items()}

    # C1: exactly one round boundary
    ck("year +1 and round +1 (exactly)",
       ga["year"] == gb["year"] + 1 and ga["round"] == gb["round"] + 1,
       f"year {gb['year']}->{ga['year']} round {gb['round']}->{ga['round']}")
    years_seen = sorted({t["year"] for t in timeline}) if timeline else []
    ck("exactly two distinct years observed (the boundary crossed once, no double flip)",
       years_seen == [gb["year"], ga["year"]] and ga["year"] == gb["year"] + 1,
       f"years observed: {years_seen}")

    # C2: the solo heartbeat — cur_player walks the per-player loop in FUN_00520c10
    # (upkeep FUN_005208f0(p), AI FUN_0056d0c0(p) or human FUN_0050f420). The MP
    # stage counter DAT_0091c630 never moves in solo (measured) — reported, not floored.
    cp_seq = [t["cur_player"] for t in timeline] if timeline else []
    others = sorted(set(cp_seq) - {me})
    ck("cur_player walked the player loop: >=3 distinct non-ours values observed, then "
       "returned to ours (the per-player upkeep/AI/human loop ran end to end)",
       len(others) >= 3 and ga["cur_player"] == me,
       f"cur_player sequence={cp_seq} others={others}")
    stages_seq = [t["stage"] for t in timeline] if timeline else []
    stages_moved = len({s for s in stages_seq}) > 1 or stages_seq and stages_seq[0] != gb["stage"]
    ck("stage counter stayed put (solo path — the 7-stage MP machine must NOT run)",
       not stages_moved,
       f"stage before={gb['stage']} sequence={stages_seq}")

    # C3/C4/C5: unit-record accounting. Identity = (x,y,type,owner,order): the
    # boundary LEGITIMATELY rewrites other bytes (measured: u16s at +28/+48/+50
    # decrement by 1 — index references adjusted by array compaction when units
    # die; flags/mp/x/y/type/owner/order held stable on all our HELD records).
    def keyf(u):
        return (u["x"], u["y"], u["type"], u["owner"], u["order"])
    kb, ka = Counter(keyf(u) for u in before["units"]), Counter(keyf(u) for u in after["units"])
    added_k = list((ka - kb).elements())
    removed_k = list((kb - ka).elements())
    held_bad = []
    for u in before["units"]:
        if u["owner"] == me and u["order"] == 2 and ka[keyf(u)] < kb[keyf(u)]:
            held_bad.append((u["x"], u["y"], u["type"]))
    # byte-rewrite inventory (report, not floor): pair ours by key, diff full bytes
    gb_by_key, ga_by_key = {}, {}
    for u in before["units"]:
        if u["owner"] == me:
            gb_by_key.setdefault(keyf(u), []).append(bytes.fromhex(u["hex"]))
    for u in after["units"]:
        if u["owner"] == me:
            ga_by_key.setdefault(keyf(u), []).append(bytes.fromhex(u["hex"]))
    rewrite_offsets = Counter()
    for k, lst in gb_by_key.items():
        for h1, h2 in zip(sorted(lst), sorted(ga_by_key.get(k, []))):
            for i in range(52):
                if h1[i] != h2[i]:
                    rewrite_offsets[i] += 1
    ck("every HELD record of ours persists at the same (x,y,type,owner,order) — "
       "nothing of ours moved or died", not held_bad,
       f"broken keys: {held_bad}; ours {sum(1 for u in before['units'] if u['owner']==me)}"
       f"->{sum(1 for u in after['units'] if u['owner']==me)}; our records rewritten at "
       f"byte offsets {dict(sorted(rewrite_offsets.items()))} (u16s decrementing by 1 = "
       f"index refs adjusted by compaction)")
    tiles = base_lookup(before["bases"]); tiles.update(base_lookup(after["bases"]))
    # production = net-NEW records per (owner,type) class; moves/deaths net out
    class_net = Counter()
    for t in added_k:
        class_net[(t[3], t[2])] += 1
    for t in removed_k:
        class_net[(t[3], t[2])] -= 1
    bad_add, prod, cargo = [], [], []
    for k, n in sorted(class_net.items()):
        if n <= 0:
            continue
        cls_added = [t for t in added_k if (t[3], t[2]) == k]
        # production arrivals are order 0 (measured: ours arrive order 0; SAVE_FORMAT
        # +17=0). Net-new records arriving with a NONZERO order are cargo
        # materialising from a transport (unload state, e.g. order 24) — reported,
        # not floored; they are not production.
        z = [t for t in cls_added if t[4] == 0]
        nz = [t for t in cls_added if t[4] != 0]
        for t in z:
            b = tiles.get((t[0], t[1]))
            if b is None or b["faction"] != t[3]:
                bad_add.append((t, "order-0 arrival not on a base of its faction"))
            else:
                prod.append(dict(x=t[0], y=t[1], owner=t[3], type=t[2], order=t[4], base=b["name"]))
        for t in nz:
            cargo.append(dict(x=t[0], y=t[1], owner=t[3], type=t[2], order=t[4]))
    ck("every net-NEW record arriving with order 0 sits on a base tile of its own "
       "faction (production is the only thing that adds order-0 records; moves and "
       "deaths net out per class; nonzero-order arrivals are transport cargo, reported "
       "separately)", not bad_add,
       f"net-new classes {dict((k, v) for k, v in class_net.items() if v > 0)}; "
       f"unexplained: {bad_add}")
    losses = [dict(x=t[0], y=t[1], type=t[2], owner=t[3], order=t[4]) for t in removed_k]

    # C7/C8: upkeep ledger zeroed by 0x5208f0; energy never negative (code clamp)
    led = {p: f["ledger"] for p, f in af.items() if f["ledger"] != 0}
    ck("spending ledger (faction+4) zero for every active player after upkeep",
       not led, f"nonzero ledgers: {led}")
    neg = {p: f["energy"] for p, f in af.items() if f["energy"] < 0}
    ck("energy >= 0 for every active player (upkeep clamps at 0)", not neg, f"negative: {neg}")

    # C9: the research engine fired inside upkeep. Floor = the machinery ran
    # (some active faction's points or tech changed); OUR flat points is a
    # reported condition, not a failure (measured: our tech 36 completed at an
    # earlier boundary, points reset 108->8; lab array state under investigation).
    fb, fa = bf.get(me, {}), af.get(me, {})
    rpoints_d = {p: af[p]["rpoints"] - bf[p]["rpoints"] for p in af if p in bf}
    rtech_d = {p: (bf[p]["rtech"], af[p]["rtech"]) for p in af if p in bf
               if bf[p]["rtech"] != af[p]["rtech"]}
    research_moved = any(v != 0 for v in rpoints_d.values()) or any(
        a_ != b_ for b_, a_ in rtech_d.values())
    ck("research advanced across the boundary: >=1 active faction's rpoints changed "
       "or rtech switched (the research engine runs inside each player's upkeep)",
       research_moved, f"rpoints deltas {rpoints_d}; rtech changes {rtech_d}")
    if me in bf and me in af:
        print(f"  report: our research rpoints {fb['rpoints']}->{fa['rpoints']} "
              f"rtech {fb['rtech']}->{fa['rtech']} labcnt {fb['labcnt']}->{fa['labcnt']} "
              f"saved_b4 {fb['saved_b4']}->{fa['saved_b4']} save_later={gb['save_later']}")
    else:
        ck("our faction record readable", False, "our player not in active mask")

    # C6: our bases survived the measured boundary
    own_b = {(b["x"], b["y"]): b for b in before["bases"] if b["faction"] == me}
    own_a = {(b["x"], b["y"]) for b in after["bases"] if b["faction"] == me}
    lost = [own_b[t]["name"] for t in own_b if t not in own_a]
    ck("no base of ours was lost during the measured boundary", not lost,
       f"lost: {lost} (ours after: {sorted(own_a)})")
    return prod, losses, cargo, added_k, removed_k


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", default=None)
    ap.add_argument("--fixture", default=None, help="JSON {before, after, timeline} to account")
    ap.add_argument("--poll", type=float, default=0.002)
    ap.add_argument("--timeout", type=float, default=300.0)
    ap.add_argument("--settle", type=float, default=1.5)
    ap.add_argument("--no-poke", action="store_true")
    ap.add_argument("--no-enter", action="store_true")
    a = ap.parse_args()

    trace_path = a.trace or (f"evidence/trace_m55_boundary_{time.strftime('%Y%m%d_%H%M%S')}.jsonl")
    trace = []

    def log(obj):
        trace.append(obj)

    if a.fixture:
        fx = json.load(open(a.fixture))
        before, after, timeline = fx["before"], fx["after"], fx.get("timeline", [])
        log(dict(event="fixture", path=a.fixture))
    else:
        pid = find_pid()
        m = open(f"/proc/{pid}/mem", "rb+", 0)   # rb+: writable (poke), no truncation
        if not a.no_poke:
            poke_hold(m, trace)
        before = snapshot(m)
        log(dict(event="before", t=time.time(), snap=before))
        gb0 = before["globals"]
        if gb0["year"] < 2101:
            _dump(trace_path, trace)
            print("FAIL not in a game (year < 2101)"); sys.exit(1)
        # Wait (not refuse): with every unit HELD the engine's auto-end path
        # (DAT_0091f69c&1 -> FUN_00520c10(2), "No units need orders Press ENTER")
        # closes our turn on its own, so cur_player==ours is a window that reopens
        # every round; wait for it, then measure the boundary that closes it.
        cp = gb0["cur_player"]
        wait_deadline = time.time() + a.timeout
        last_dismiss = 0.0
        while cp != gb0["our_player"] and time.time() < wait_deadline:
            # modal event dialogs (techs, eradications, contacts) freeze the player
            # walk; Return dismisses them. Safe here: while cp != ours, Return is
            # NOT consumed as turn-end by the engine (measured: it only ends the
            # turn when the human loop is running).
            if not a.no_enter and time.time() - last_dismiss > 2.0:
                try:
                    w = subprocess.check_output(["xdotool", "search", "--name", "Sid Meier"],
                                                text=True).split()[0]
                    subprocess.run(["xdotool", "key", "--clearmodifiers", "Return"], check=True)
                except (IndexError, subprocess.CalledProcessError):
                    pass
                last_dismiss = time.time()
            time.sleep(a.poll)
            cp = u32(m, 0x985DCC)
        if cp != gb0["our_player"]:
            _dump(trace_path, trace)
            print(f"FAIL our turn (cur_player {gb0['our_player']}) never became active "
                  f"within {a.timeout}s (cur_player stayed {cp})"); sys.exit(1)
        if not a.no_enter:
            win = subprocess.check_output(
                ["xdotool", "search", "--name", "Sid Meier"], text=True).split()[0]
            subprocess.run(["xdotool", "windowfocus", win], check=True)
        t0 = time.time()
        timeline = [dict(t=0.0, **gb0)]
        pressed = a.no_enter
        last_press = 0.0
        flip_t = None
        stable_since = None
        deadline = time.time() + a.timeout
        while time.time() < deadline:
            row = timeline_row(m)
            last = timeline[-1]
            if any(row[k] != last[k] for k in row):
                timeline.append(dict(t=round(time.time() - t0, 3), **row))
            if not pressed or (flip_t is None and time.time() - last_press > 2.0):
                # press Enter from INSIDE the sampler loop so the player walk is
                # sampled, not raced; re-press every 2s until the flip because a
                # modal UI (planet display from an event) swallows one press.
                subprocess.run(["xdotool", "key", "--clearmodifiers", "Return"], check=True)
                log(dict(event="press_enter", t=round(time.time() - t0, 3), win=win))
                pressed = True
                last_press = time.time()
            if flip_t is None and row["year"] != gb0["year"]:
                flip_t = time.time()
                log(dict(event="flip", row=row))
            if flip_t is not None and row["cur_player"] == gb0["our_player"]:
                if stable_since is None:
                    stable_since = time.time()
                if time.time() - stable_since >= a.settle:
                    break
            elif flip_t is not None:
                stable_since = None
            time.sleep(a.poll)
        log(dict(event="timeline", rows=timeline))
        if flip_t is None:
            log(dict(event="verdict", ok=False, why="no year flip within timeout"))
            _dump(trace_path, trace)
            print(f"FAIL no round boundary (year never moved) within {a.timeout}s")
            sys.exit(1)
        after = snapshot(m)
        log(dict(event="after", t=time.time(), snap=after))

    checks = []
    prod, losses, cargo, added_k, removed_k = account(before, after, timeline, checks)
    gb, ga = before["globals"], after["globals"]
    me = gb["our_player"]

    # reports (no floors — these are the inventory the milestone asked for)
    energy_d = {p: after["factions"][p]["energy"] - before["factions"][p]["energy"]
                for p in after["factions"] if p in before["factions"]}
    rpoints_d = {p: after["factions"][p]["rpoints"] - before["factions"][p]["rpoints"]
                 for p in after["factions"] if p in before["factions"]}
    rtech_d = {p: (before["factions"][p]["rtech"], after["factions"][p]["rtech"])
               for p in after["factions"]
               if p in before["factions"] and before["factions"][p]["rtech"] != after["factions"][p]["rtech"]}
    tf_flips = []
    for t in timeline[1:]:
        if t["turn_flags"] != timeline[0]["turn_flags"]:
            tf_flips.append((t.get("t"), hex(timeline[0]["turn_flags"]), hex(t["turn_flags"])))
    bf = {int(k): v for k, v in before["factions"].items()}
    af = {int(k): v for k, v in after["factions"].items()}
    sliders = {p: (bf[p]["slider_104"], bf[p]["slider_108"],
                   af[p]["slider_104"], af[p]["slider_108"])
               for p in af if p in bf}
    labcnt_d = {p: (bf[p]["labcnt"], af[p]["labcnt"]) for p in af if p in bf}
    log(dict(event="report", energy_delta=energy_d, rpoints_delta=rpoints_d,
             rtech_changed=rtech_d, turn_flags_before=hex(gb["turn_flags"]),
             turn_flags_after=hex(ga["turn_flags"]), turn_flags_flips=tf_flips,
             production=prod, cargo_arrivals=cargo, losses=losses,
             sliders_104_108_before_after=sliders,
             labcnt=labcnt_d,
             flags_lo=(hex(gb["flags_lo"]), hex(ga["flags_lo"])),
             flags_ac4=(hex(gb["flags_ac4"]), hex(ga["flags_ac4"])),
             research_gate=(gb["research_gate"], ga["research_gate"])))

    ok = all(c["ok"] for c in checks)
    log(dict(event="checks", checks=checks, ok=ok))
    _dump(trace_path, trace)
    for c in checks:
        print(f"  {'ok ' if c['ok'] else 'BAD'} {c['check']} — {c['detail']}")
    print(f"  report: energy deltas {energy_d}")
    print(f"  report: rpoints deltas {rpoints_d} rtech changed {rtech_d}")
    print(f"  report: production {prod if prod else 'no net-new order-0 arrivals this round'}")
    print(f"  report: cargo arrivals (net-new, nonzero order) {cargo}")
    print(f"  report: losses {losses}")
    print(f"  report: turn_flags {hex(gb['turn_flags'])} -> {hex(ga['turn_flags'])} flips {tf_flips}")
    print(f"  trace: {trace_path}")
    if ok:
        print(f"PASS boundary {gb['year']}->{ga['year']}: player walk observed "
              f"(cur_player {sorted({t['cur_player'] for t in timeline})}), upkeep income "
              f"read for {len(energy_d)} factions, research advanced, production: "
              f"{prod if prod else 'no net-new order-0 arrivals this round'}, losses {losses}")
    else:
        print("FAIL boundary accounting")
    sys.exit(0 if ok else 1)


def _dump(path, trace):
    import os
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as fh:
        for obj in trace:
            fh.write(json.dumps(obj) + "\n")


if __name__ == "__main__":
    main()
