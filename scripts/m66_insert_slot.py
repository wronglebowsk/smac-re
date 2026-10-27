#!/usr/bin/env python3
"""M66: which queue slot does the BUILD UI's INSERT write?

Every earlier enqueue used the SAME item id (Scout Patrol, id 2) for every insert, so a
slot array of [2,2,...] could not say whether INSERT wrote one slot or two, or whether it
appended or overwrote.  This instrument enqueues TWO DIFFERENT item ids in one open chooser
and reads the queue back after each INSERT, so the layout is identifiable.

The four candidate layouts are written down BEFORE the run (PREDICTIONS below) and the run
prints which one the read-backs select.  PASS requires exactly ONE match plus the integrity
checks (pending +1 per INSERT, the enqueued ids present, the chooser guard moved to the cell
that was clicked).  Nothing here pokes the queue: the only memory writes are the three
enabling pokes the M57 recipe needs (cursor home, SEL_G, orders mode), never a queue field.

    python3 scripts/m66_insert_slot.py [--base-name "Korolev Center"]
                                       [--item-a 193] [--item-b 194]
                                       [--trace evidence/m66_insert_slot.jsonl]
"""
import argparse, json, os, struct, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import smac_play as sp  # noqa: E402

WIN_G, WIN_CUR_X, WIN_CUR_Y = 0x7CDECC, 0x1DD9C, 0x1DDA0
CI, CX, CY = 0x91B5E8, 0x91B5F0, 0x91B670
SEL_G, ORDERS_MODE = 0x91B5BC, 0x91B5B8
CAND, CAND_N = 0x9267E4, 0x9267E0
GUARD = 0x6A9E9C + 0xa774            # chooser selection field = the CELL INDEX
PANE_BASE_IDX = 0x6A9480 + 0x3FF3C   # the base index the QUEUE widget is showing
ARROW_XY, ROW1_XY = (523, 433), (185, 437)
INSERT_XY, OK_XY = (497, 343), (285, 343)
COUNT_A, COUNT_B = 0x94de84, 0x94dc84   # the two queued-count byte arrays in conflict
COUNT_STRIDE = 0x20bc                    # 8380 bytes per faction
SLOTS = 10

# The layouts, stated before observing.  baseline = the slots as they read BEFORE the first
# INSERT (they are usually stale ids left by the pop), A = item_a, B = item_b, `s` = baseline.
PREDICTIONS = [
    ("append_at_pending_index",
     "INSERT writes base+0x50+4*pending_before (slot 0, then slot 1); the tail is untouched",
     lambda base, a, b: a[0:2] == [A(base), base[1]] and b[0:2] == [A(base), B(base)]),
    ("write_head_and_shift_right",
     "INSERT writes head base+0x50 and shifts the existing slots right by one",
     lambda base, a, b: a[0:3] == [A(base), base[0], base[1]] and b[0:3] == [B(base), A(base), base[0]]),
    ("write_head_and_next_slot",
     "INSERT writes BOTH base+0x50 and base+0x54 with the same item id (the M57 doc claim)",
     lambda base, a, b: a[0:2] == [A(base), A(base)] and b[0:2] == [B(base), B(base)]),
    ("eight_byte_entries",
     "a queue ENTRY is 8 bytes: the item id at +0x50 and a companion dword at +0x54, so the "
     "second entry starts at +0x58",
     lambda base, a, b: a[0] == A(base) and b[0] == A(base) and b[2] == B(base)),
]


def A(base):
    return ENQ[0]


def B(base):
    return ENQ[1]


ENQ = [None, None]


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
    b = sp.rd(f, sp.BASE_ARR + i * sp.BASE_SZ, sp.BASE_SZ)
    g = lambda o: struct.unpack("<i", b[o:o + 4])[0]
    return dict(i=i, name=b[19:59].split(b"\0")[0].decode("latin-1", "replace"),
                x=struct.unpack("<H", b[0:2])[0], y=struct.unpack("<H", b[2:4])[0],
                fac=b[4], pending=g(0x4c), queue=[g(0x50 + 4 * k) for k in range(SLOTS)],
                minerals=g(0x40), d0=g(0xd0))


def counts(f, owner, tids):
    """Read BOTH contested per-faction count arrays at both indexings, for these type ids."""
    out = {}
    for tid in tids:
        for nm, base in (("de84", COUNT_A), ("dc84", COUNT_B)):
            out[f"{nm}[{tid}]"] = struct.unpack("B", sp.rd(f, base + COUNT_STRIDE * owner + tid, 1))[0]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-name", default="Korolev Center")
    ap.add_argument("--item-a", type=int, default=193)
    ap.add_argument("--item-b", type=int, default=194)
    ap.add_argument("--trace", default="evidence/m66_insert_slot.jsonl")
    a = ap.parse_args()
    ENQ[0], ENQ[1] = a.item_a, a.item_b
    if a.item_a == a.item_b:
        print("FAIL: the two item ids must DIFFER or the layout is unidentifiable")
        return 1

    rows = []

    def rec(tag, **kw):
        row = dict(tag=tag, t=time.strftime("%H:%M:%S"), **kw)
        rows.append(row)
        print(json.dumps(row), flush=True)

    pid, f = sp.mem()
    mine = sp.own_bases_named(f, 3)
    hits = [b for b in mine if b["name"] == a.base_name]
    if len(hits) != 1:
        print(f"FAIL: base {a.base_name!r} matched {len(hits)} of our bases: "
              f"{[(b['idx'], b['name']) for b in mine]}")
        return 1
    idx = hits[0]["idx"]

    def snap(tag):
        r = base_rec(f, idx)
        c = counts(f, r["fac"], (a.item_a, a.item_b, 2))
        rec(tag, idx=r["i"], name=r["name"], x=r["x"], y=r["y"], minerals=r["minerals"],
            pending=r["pending"], slots=r["queue"][:SLOTS], d0=r["d0"], counts=c,
            guard=i32(f, GUARD), pane_idx=u32(f, PANE_BASE_IDX))
        r["counts"] = c
        return r

    before = snap("before")
    base_slots = before["slots"]
    if a.item_a in base_slots[:2] or a.item_b in base_slots[:2] or a.item_a == 2 or a.item_b == 2:
        print(f"FAIL: the stale baseline slots {base_slots[:2]} must not contain either "
              f"enqueue id, or the layout is confounded")
        return 1

    cand = [i32(f, CAND + 4 * j) for j in range(min(i32(f, CAND_N), 128))]
    for nm, tid in (("item_a", a.item_a), ("item_b", a.item_b)):
        if tid not in cand:
            print(f"FAIL: {nm} {tid} is not in the chooser candidate array {cand[:20]}...")
            return 1
    ka, kb = cand.index(a.item_a), cand.index(a.item_b)
    rec("plan", item_a=a.item_a, cell_a=ka, item_b=a.item_b, cell_b=kb,
        cand=cand[:12], count=len(cand),
        predictions=[(n, d) for n, d, _ in PREDICTIONS])

    # the three enabling pokes (NOT queue fields) — the M57 recipe
    tx, ty = hits[0]["x"], hits[0]["y"]
    w = u32(f, WIN_G)
    sp.wr(f, w + WIN_CUR_X, struct.pack("<i", tx)); sp.wr(f, w + WIN_CUR_Y, struct.pack("<i", ty))
    ci = u32(f, CI)
    sp.wr(f, CX + ci * 4, struct.pack("<i", tx))
    sp.wr(f, CY + ci * 4, struct.pack("<i", ty))
    sp.wr(f, SEL_G, struct.pack("<i", -1))
    sp.wr(f, ORDERS_MODE, struct.pack("<i", 0))
    rec("pokes", cursor=(i32(f, w + WIN_CUR_X), i32(f, w + WIN_CUR_Y)),
        sel=i32(f, SEL_G), orders_mode=i32(f, ORDERS_MODE))

    win = sp.find_window()
    sp.focus()
    key("b")
    for attempt in range(8):
        if u32(f, PANE_BASE_IDX) == idx:
            break
        click(ARROW_XY)
    rec("pane", pane_idx=u32(f, PANE_BASE_IDX), want=idx)
    if u32(f, PANE_BASE_IDX) != idx:
        print("FAIL: the QUEUE widget never landed on the target base")
        return 1

    click(ROW1_XY)
    time.sleep(0.6)
    rec("chooser_open", guard=i32(f, GUARD), pending=i32(f, sp.BASE_ARR + idx * sp.BASE_SZ + 0x4c))

    def insert(item, cell, tag):
        r = None
        click((128 + 127 * (cell % 5), 60 + 100 * (cell // 5)))
        g = i32(f, GUARD)
        if g != cell:
            print(f"FAIL: after clicking cell {cell} (item {item}) the chooser guard reads {g}")
            return None
        for try_n in range(4):
            click(INSERT_XY)
            for _ in range(8):          # poll; do NOT click INSERT again on a stale read
                time.sleep(0.5)
                r = base_rec(f, idx)
                if r["pending"] > prev_pending[0]:
                    break
            if r["pending"] > prev_pending[0]:
                c = counts(f, r["fac"], (a.item_a, a.item_b, 2))
                rec(tag, guard=g, pending=r["pending"], slots=r["queue"][:SLOTS],
                    minerals=r["minerals"], d0=r["d0"], counts=c, tries=try_n + 1)
                prev_pending[0] = r["pending"]
                return r
            click(ARROW_XY)            # the widget may have moved off our base
            rec(tag + "_retry", pane_idx=u32(f, PANE_BASE_IDX), pending=r["pending"],
                slots=r["queue"][:SLOTS], try_n=try_n + 1)
        return None

    prev_pending = [before["pending"]]
    ra = insert(a.item_a, ka, "insert_a")
    if ra is None:
        print(f"FAIL: INSERT of item {a.item_a} never incremented pending "
              f"{before['pending']} -> {prev_pending[0]}")
        return 1
    rb = insert(a.item_b, kb, "insert_b")
    if rb is None:
        print(f"FAIL: INSERT of item {a.item_b} never incremented pending "
              f"{prev_pending[0]} -> {prev_pending[0]}")
        return 1

    click(OK_XY)
    time.sleep(0.8)
    after = snap("after_ok")

    sp.wr(f, ORDERS_MODE, struct.pack("<i", 1))
    rec("orders_restored", orders_mode=i32(f, ORDERS_MODE))
    kind = None
    for i in range(4):
        png = sp.freeze("m66pane")
        kind = sp.classify(sp.ocr_fast(png), sp.region_colors(png), png)
        if kind != "base":
            break
        sp.key("Escape")
        time.sleep(1.6)
    rec("pane_closed", screen_class=kind)

    # ---- score the predictions against the two read-backs
    sa, sb = ra["queue"], rb["queue"]
    matched = [(n, fn(base_slots, sa, sb)) for n, _, fn in PREDICTIONS]
    ok = [n for n, m in matched if m]
    rec("score", baseline=base_slots, after_a=sa[:SLOTS], after_b=sb[:SLOTS],
        pending_before=before["pending"], pending_after_a=ra["pending"],
        pending_after_b=rb["pending"], matched=ok,
        counts_before=before["counts"], counts_after_b=after["counts"])

    print("\nlayout read-backs:")
    print(f"  baseline  pending {before['pending']}  slots {base_slots[:6]}")
    print(f"  after {a.item_a:<4}  pending {ra['pending']}  slots {sa[:6]}")
    print(f"  after {a.item_b:<4}  pending {rb['pending']}  slots {sb[:6]}")
    print(f"  after OK  pending {after['pending']}  slots {after['queue'][:6]}")
    print("\ncount arrays (the contested pair), before -> after OK:")
    for k in before["counts"]:
        print(f"  {k:<14} {before['counts'][k]:>3} -> {after['counts'][k]:>3}")

    integrity = (ra["pending"] == before["pending"] + 1
                 and rb["pending"] == before["pending"] + 2
                 and after["pending"] == before["pending"] + 2
                 and sa[0] == a.item_a)
    if len(ok) == 1 and integrity:
        print(f"\nPASS: exactly one layout matches — {ok[0]} "
              f"(pending {before['pending']}->{ra['pending']}->{rb['pending']}, "
              f"items {a.item_a} then {a.item_b})")
        verdict = 0
    else:
        print(f"\nFAIL: layouts matched = {ok} (need exactly one), integrity = {integrity}; "
              f"no layout claim is made")
        verdict = 1

    trace = a.trace if a.trace.startswith("/") else os.path.join(ROOT, a.trace)
    os.makedirs(os.path.dirname(trace), exist_ok=True)
    with open(trace, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    print(f"trace: {trace} ({len(rows)} rows)")
    return verdict


if __name__ == "__main__":
    sys.exit(main())
