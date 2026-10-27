#!/usr/bin/env python3
"""M66: which queue slot does the BUILD UI's INSERT write?

Every earlier enqueue used the SAME item id (Scout Patrol, id 2) for every insert, so a
queue that read [2,2,...] could not say whether INSERT wrote one slot or two, whether it
touched the head, or whether it shifted.  This instrument enqueues TWO DIFFERENT ids in one
open chooser and reads the queue back after each INSERT.

Two confounds are handled explicitly:
  * the chooser's candidate array is REBUILT by the chooser paint (`0x596000`, NAMED), so the
    cell -> id map is read AFTER the chooser opens and again after each click, and the id the
    game actually stored is compared with the array entry at the clicked cell at that moment;
  * the queue tail usually holds STALE ids left by the pop, so the layout test is structural
    (baseline -> after A -> after B) and the baseline must not contain either enqueue id.

The layouts below are written down BEFORE the run; each is a transformation rule with the
written item id as a free variable.  PASS requires exactly ONE rule to explain both read-backs
plus the integrity checks.  Nothing here writes a queue field: the only memory writes are the
three enabling pokes the M57 recipe needs (cursor home, SEL_G, orders mode).

    python3 scripts/m66_insert_slot.py [--base-name "University Base"]
                                       [--item-a 193] [--item-b 195]
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
COUNT_A, COUNT_B = 0x94de84, 0x94dc84   # the two per-faction byte arrays in conflict (NAMED)
COUNT_STRIDE = 0x20bc                    # 8380 bytes per faction
SLOTS = 8

# ---- the layouts, stated before observing.  s = baseline slots, p0 = pending before,
# X = the id the game stored on INSERT A, Y = the id it stored on INSERT B (X != Y).
# Each rule returns the ids it needs, or None if the read-backs cannot be explained by it.


def _inserted_at(dst, src, i):
    """dst is src with a NEW value written at index i and everything from i rightward shifted
    one slot: dst[:i] == src[:i], dst[i] is new, dst[i+1:] == src[i:-1]."""
    return dst[:i] == src[:i] and dst[i] != src[i] and dst[i + 1:] == src[i:-1]


def _overwrote_at(dst, src, i):
    """dst is src with index i overwritten and NOTHING else moved."""
    return dst[:i] == src[:i] and dst[i] != src[i] and dst[i + 1:] == src[i + 1:]


def rule_insert_at_new_pending(s, pa, a, pb, b):
    """INSERT writes base+0x50+4*pending_after and shifts the rest right by one; the head
    slot +0x50 is NOT touched (disasm 0x418b32 reads [base+0x50+4*esi] with esi = the new
    pending, 0x418b57 stores to +0x50 only when esi == 0)."""
    i, j = pa, pb                      # index written = the new pending count
    if i < 1 or j != i + 1:
        return None
    if not _inserted_at(a, s, i) or not _inserted_at(b, a, j):
        return None
    return (a[i], b[j])


def rule_append_at_pending_before(s, pa, a, pb, b):
    """INSERT writes base+0x50+4*pending_before and nothing else moves: the FIRST insert
    overwrites the head slot."""
    i, j = pa - 1, pb - 1
    if i < 0 or j != i + 1:
        return None
    if not _overwrote_at(a, s, i) or not _overwrote_at(b, a, j):
        return None
    return (a[i], b[j])


def rule_write_head_and_next_slot(s, pa, a, pb, b):
    """INSERT writes BOTH base+0x50 and base+0x54 with the same id (the M57 doc claim)."""
    if a[0] != a[1] or a[0] == s[0] or a[2:] != s[2:]:
        return None
    if b[0] != b[1] or b[0] == a[0] or b[2:] != a[2:]:
        return None
    return (a[0], b[0])


def rule_write_head_and_shift_right(s, pa, a, pb, b):
    """INSERT writes head +0x50 and shifts every existing slot right by one."""
    if not _inserted_at(a, s, 0) or not _inserted_at(b, a, 0):
        return None
    return (a[0], b[0])


def rule_eight_byte_entries(s, pa, a, pb, b):
    """a queue ENTRY is 8 bytes (item id at +0x50, a companion dword at +0x54), so the second
    entry starts at +0x58: INSERT A rewrites the head entry only, INSERT B the SECOND entry."""
    if a[0] == s[0] or a[2:] != s[2:]:
        return None
    if b[0] != a[0] or b[1] != a[1] or b[2] == a[2] or b[4:] != a[4:]:
        return None
    return (a[0], b[2])


PREDICTIONS = [
    ("insert_at_new_pending_index", rule_insert_at_new_pending),
    ("append_at_pending_before_index", rule_append_at_pending_before),
    ("write_head_and_next_slot", rule_write_head_and_next_slot),
    ("write_head_and_shift_right", rule_write_head_and_shift_right),
    ("eight_byte_entries", rule_eight_byte_entries),
]


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


def cand(f):
    n = max(0, min(i32(f, CAND_N), 128))
    return [i32(f, CAND + 4 * j) for j in range(n)]


def count_rows(f, owner):
    o = owner * COUNT_STRIDE
    return {"de84": sp.rd(f, COUNT_A + o, COUNT_STRIDE),
            "dc84": sp.rd(f, COUNT_B + o, COUNT_STRIDE)}


def row_diff(before, after):
    out = {}
    for k, a in before.items():
        b = after[k]
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                out[f"{k}[{i}]"] = f"{x}->{y}"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-name", default="University Base")
    ap.add_argument("--item-a", type=int, default=193)
    ap.add_argument("--item-b", type=int, default=195)
    ap.add_argument("--trace", default="evidence/m66_insert_slot.jsonl")
    a = ap.parse_args()

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
        r["rows"] = count_rows(f, r["fac"])
        rec(tag, idx=r["i"], name=r["name"], x=r["x"], y=r["y"], minerals=r["minerals"],
            pending=r["pending"], slots=r["queue"], d0=r["d0"],
            guard=i32(f, GUARD), pane_idx=u32(f, PANE_BASE_IDX))
        return r

    before = snap("before")
    s = before["queue"]
    p0 = before["pending"]
    for nm, tid in (("item_a", a.item_a), ("item_b", a.item_b)):
        if tid in s or tid == 2:
            print(f"FAIL: {nm} {tid} is in the stale baseline slots {s} — the layout would be "
                  f"confounded; pick ids the queue does not already hold")
            return 1

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

    sp.find_window()
    sp.focus()
    key("b")
    for _ in range(8):
        if u32(f, PANE_BASE_IDX) == idx:
            break
        click(ARROW_XY)
    rec("pane", pane_idx=u32(f, PANE_BASE_IDX), want=idx)
    if u32(f, PANE_BASE_IDX) != idx:
        print("FAIL: the QUEUE widget never landed on the target base")
        return 1

    click(ROW1_XY)
    time.sleep(0.6)
    c_open = cand(f)
    rec("chooser_open", guard=i32(f, GUARD),
        pending=i32(f, sp.BASE_ARR + idx * sp.BASE_SZ + 0x4c), cand=c_open[:12])
    for nm, tid in (("item_a", a.item_a), ("item_b", a.item_b)):
        if tid not in c_open:
            print(f"FAIL: {nm} {tid} is not in the chooser's list as it reads with the chooser "
                  f"OPEN: {c_open[:20]}")
            return 1
    ka, kb = c_open.index(a.item_a), c_open.index(a.item_b)
    rec("plan", item_a=a.item_a, cell_a=ka, item_b=a.item_b, cell_b=kb,
        layouts=[n for n, _ in PREDICTIONS], pending_before=p0, baseline=s)

    state = {"pending": p0, "written": []}

    def insert(item, cell, tag):
        r = None
        click((128 + 127 * (cell % 5), 60 + 100 * (cell // 5)))
        g = i32(f, GUARD)
        c_after_click = cand(f)
        if g != cell:
            print(f"FAIL: after clicking cell {cell} (item {item}) the chooser guard reads {g}")
            return None
        for try_n in range(4):
            click(INSERT_XY)
            for _ in range(8):          # poll; never click INSERT again on a stale read
                time.sleep(0.5)
                r = base_rec(f, idx)
                if r["pending"] > state["pending"]:
                    break
            if r["pending"] > state["pending"]:
                c_after_insert = cand(f)
                stored = [v for v in r["queue"] if v not in s]
                rows_row = count_rows(f, r["fac"])
                rec(tag, guard=g, pending=r["pending"], slots=r["queue"],
                    minerals=r["minerals"], d0=r["d0"],
                    cand_at_click=c_after_click[:max(ka, kb) + 1],
                    cand_after_insert=c_after_insert[:max(ka, kb) + 1],
                    cell_entry=c_after_click[cell] if cell < len(c_after_click) else None,
                    new_slot_values=stored, row_delta=row_diff(before["rows"], rows_row),
                    tries=try_n + 1)
                state["pending"] = r["pending"]
                state["written"] = stored
                r["rows"] = rows_row
                return r
            click(ARROW_XY)            # the widget may have moved off our base
            rec(tag + "_retry", pane_idx=u32(f, PANE_BASE_IDX), pending=r["pending"],
                slots=r["queue"], try_n=try_n + 1)
        return None

    ra = insert(a.item_a, ka, "insert_a")
    if ra is None:
        print(f"FAIL: INSERT of item {a.item_a} never incremented pending {p0}")
        return 1
    rb = insert(a.item_b, kb, "insert_b")
    if rb is None:
        print(f"FAIL: INSERT of item {a.item_b} never incremented pending {state['pending']}")
        return 1

    click(OK_XY)
    time.sleep(0.8)
    after = snap("after_ok")
    row_delta = row_diff(before["rows"], after["rows"])

    sp.wr(f, ORDERS_MODE, struct.pack("<i", 1))
    rec("orders_restored", orders_mode=i32(f, ORDERS_MODE))
    kind = None
    for _ in range(4):
        png = sp.freeze("m66pane")
        kind = sp.classify(sp.ocr_fast(png), sp.region_colors(png), png)
        if kind != "base":
            break
        sp.key("Escape")
        time.sleep(1.6)
    rec("pane_closed", screen_class=kind,
        row_delta_after_ok=row_delta)

    scored = []
    for nm, fn in PREDICTIONS:
        ids = fn(s, ra["pending"], ra["queue"], rb["pending"], rb["queue"])
        if ids:
            scored.append((nm, ids))
    distinct = {nm for nm, _ in scored}
    integrity = (ra["pending"] == p0 + 1 and rb["pending"] == p0 + 2
                 and after["pending"] == p0 + 2
                 and all(ids[0] != ids[1] for _, ids in scored)
                 and all(v in rb["queue"] for _, ids in scored for v in ids))
    rec("score", baseline=s, pending_before=p0, after_a=ra["queue"],
        pending_after_a=ra["pending"], after_b=rb["queue"], pending_after_b=rb["pending"],
        after_ok=after["queue"], matched=[nm for nm, _ in scored],
        written=[ids for _, ids in scored], integrity=integrity)

    print("\nlayout read-backs:")
    print(f"  baseline   pending {p0:<2}  slots {s}")
    print(f"  after {a.item_a:<5} pending {ra['pending']:<2}  slots {ra['queue']}")
    print(f"  after {a.item_b:<5} pending {rb['pending']:<2}  slots {rb['queue']}")
    print(f"  after OK   pending {after['pending']:<2}  slots {after['queue']}")
    print("\ncontested per-faction byte arrays, entries that MOVED (before -> after OK):")
    if row_delta:
        for k, v in sorted(row_delta.items()):
            print(f"  {k:<14} {v}")
    else:
        print("  (neither array moved)")

    if len(distinct) == 1 and integrity:
        nm, ids = scored[0]
        print(f"\nPASS: exactly one layout explains both read-backs — {nm} "
              f"(pending {p0}->{ra['pending']}->{rb['pending']}, ids stored {ids})")
        verdict = 0
    else:
        print(f"\nFAIL: layouts that fit = {sorted(distinct)} (need exactly one), "
              f"integrity = {integrity}; no layout claim is made")
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
