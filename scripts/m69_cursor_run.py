#!/usr/bin/env python3
"""M69 — the BUILD-pane INSERT writes at the QUEUE WIDGET'S CURSOR, not at a sorted slot.

M69's gdb run (evidence/m69_enqueue.gdbolg + m69_enqueue.jsonl) shows the enqueue is
`queue[pos] = item` where `pos = *(int *)(widget + 0x3ff5c)`:

    break *0x417dbf        ; edx = [ecx+0x3ff5c]
    break *0x417e04        ; mov [eax+edx*4+0x50], ebx   <- the store, index = that field
    ; live: ENQUEUE obj=0x6a9480 pos=1 pending=2 -> STORE queue[1]=192
    ;       ENQUEUE obj=0x6a9480 pos=4 pending=3 -> STORE queue[4]=193   (same click flow!)

One click flow wrote at the FRONT and at the END because the widget moved its own cursor.
No type-record byte is read between the chooser click and the store.

This script is the controlled poke that proves the index is that field:

  1. open the BUILD chooser, pick an item that is not already queued;
  2. read the widget cursor, POKE it to `--cursor`, read it back;
  3. one INSERT, read the queue back, locate the write with `_shift_index`;
  4. PASS iff the write landed at EXACTLY the poked index, and the item is one whose
     plan-sorted position differs from `--cursor` (otherwise the shape cannot tell the
     cursor from a sort, and the run FAILs as non-discriminating rather than PASSing).

The poke is a UI field, not game state, and it is read back before use; it is the only
write this script makes beyond the M57 recipe's three enabling pokes.
"""
import argparse
import json
import os
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m66_insert_slot as M          # noqa: E402  (click/cand/base_rec/_shift_index live here)
import smac_play as sp               # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURSOR_OBJ = 0x6A9480                # the queue widget object (ecx at 0x417dbf, live)
CURSOR_OFF = 0x3FF5C                 # its cursor row (+ 0x3ff5c)
TYPE_REC, TYPE_SZ = M.TYPE_REC, M.TYPE_SZ


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-name", default="University Base")
    ap.add_argument("--cursor", type=int, required=True, help="row to poke the widget cursor to")
    ap.add_argument("--item", type=int, default=None, help="type id to insert (default: first free)")
    ap.add_argument("--trace", default="evidence/m69_cursor.jsonl")
    a = ap.parse_args()

    rows = []

    def rec(tag, **kw):
        row = dict(tag=tag, t=time.strftime("%H:%M:%S"), **kw)
        rows.append(row)
        print(json.dumps(row), flush=True)

    def write_trace():
        path = a.trace if a.trace.startswith("/") else os.path.join(ROOT, a.trace)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        print("trace: %s (%d rows)" % (path, len(rows)))

    def bail(msg):
        print(msg)
        write_trace()
        return 1

    pid, f = sp.mem()
    M.SLOTS = 12
    mine = sp.own_bases_named(f, 3)
    hits = [b for b in mine if b["name"] == a.base_name]
    if len(hits) != 1:
        return bail("FAIL: base %r matched %d of our bases" % (a.base_name, len(hits)))
    b = hits[0]
    idx, tx, ty = b["idx"], b["x"], b["y"]

    w = M.u32(f, M.WIN_G)
    sp.wr(f, w + M.WIN_CUR_X, struct.pack("<i", tx))
    sp.wr(f, w + M.WIN_CUR_Y, struct.pack("<i", ty))
    ci = M.u32(f, M.CI)
    sp.wr(f, M.CX + ci * 4, struct.pack("<i", tx))
    sp.wr(f, M.CY + ci * 4, struct.pack("<i", ty))
    sp.wr(f, M.SEL_G, struct.pack("<i", -1))
    sp.wr(f, M.ORDERS_MODE, struct.pack("<i", 0))

    sp.find_window()
    sp.focus()
    before = M.base_rec(f, idx)
    rec("before", pending=before["pending"], slots=before["queue"], minerals=before["minerals"])
    p0 = before["pending"]
    cur0 = M.i32(f, CURSOR_OBJ + CURSOR_OFF)
    rec("cursor_before", obj=hex(CURSOR_OBJ), off=hex(CURSOR_OFF), value=cur0)
    if not (0 <= cur0 <= 12):
        return bail("FAIL: %#x + %#x reads %d — that is not the cursor field (is the widget "
                    "object still at %#x?)" % (CURSOR_OBJ, CURSOR_OFF, cur0, CURSOR_OBJ))

    # --- open the BUILD pane and the chooser (always: pane_idx 0 == our base either way)
    sp.key("b")
    time.sleep(1.5)
    M.click(M.ARROW_XY)
    time.sleep(1.0)
    M.click(M.ROW1_XY)
    for _ in range(20):
        time.sleep(1.0)
        if M.i32(f, M.CAND_N) > 0:
            break
    else:
        return bail("FAIL: the chooser never populated (cand_n %d)" % M.i32(f, M.CAND_N))
    c = M.cand(f)
    rec("chooser", cand=c[:12], cand_n=M.i32(f, M.CAND_N))

    used = set(before["queue"][1:p0 + 1]) | {before["queue"][0]}
    if a.item is not None:
        # an explicit --item may be id 0 (the Colony Pod is a legitimate queue entry); 195 stays
        # out because at this base an INSERT of it writes -3 (M68)
        picks = [(cell, tid) for cell, tid in enumerate(c[:10])
                 if tid == a.item and tid != 195 and tid not in used]
    else:
        # auto: avoid 0 (indistinguishable from an empty slot when it appends) and 195 (-3)
        picks = [(cell, tid) for cell, tid in enumerate(c[:10])
                 if tid not in used and tid not in (0, 195) and tid < 250]
    if not picks:
        return bail("FAIL: no free, visible chooser item (used %s, cand %s)" % (sorted(used), c[:12]))
    cell, item = picks[0]

    def u8(off):
        f.seek(off)                      # NB: seek returns the position, so it must not be
        return f.read(1)[0]              #     chained with `or` (it would return the offset)

    plan = u8(TYPE_REC + item * TYPE_SZ + 42)
    # the plan-descending landing index this item would get if the enqueue sorted:
    keys = [(k + 1, u8(TYPE_REC + before["queue"][k + 1] * TYPE_SZ + 42))
            for k in range(p0) if before["queue"][k + 1] not in (0,)]
    plan_pred = next((k for k, pk in keys if pk < plan), p0 + 1)
    rec("plan", item=item, cell=cell, plan=plan, region_keys=keys, plan_sorted_index=plan_pred)
    if plan_pred == a.cursor:
        return bail("FAIL: non-discriminating shape — the plan-sorted index and --cursor %d are "
                    "both %d; pick another --cursor or another queue" % (a.cursor, plan_pred))
    if p0 + 2 > M.QUEUE_CAP - 1:
        return bail("FAIL: pending %d + 1 insert needs slot %d, the array holds %d"
                    % (p0, p0 + 2, M.QUEUE_CAP - 1))

    # --- pick the item in the chooser.  The candidate array RE-SORTS between paints, and the
    # cell -> pixel map is unreliable past row 0 (M68 traps), so re-locate the item, click, and
    # verify the guard on every attempt; abort rather than click INSERT on a stale selection.
    g = None
    for attempt in range(1, 6):
        c = M.cand(f)
        if item not in c:
            return bail("FAIL: item %d left the chooser (cand %s)" % (item, c[:12]))
        cell = c.index(item)
        if cell >= 10:
            return bail("FAIL: item %d sits at cell %d, outside the visible grid" % (item, cell))
        M.click((128 + 127 * (cell % 5), 60 + 100 * (cell // 5)))
        time.sleep(0.4)
        g = M.i32(f, M.GUARD)
        rec("cell_click", attempt=attempt, cell=cell, guard=g, entry_at_cell=c[cell])
        if g == cell:
            break
    if g != cell:
        return bail("FAIL: cell %d never registered in 5 clicks (guard %s) — the cell->pixel map "
                    "past row 0 is unreliable" % (cell, g))

    # --- THE POKE: the widget cursor, read back before the click
    sp.wr(f, CURSOR_OBJ + CURSOR_OFF, struct.pack("<i", a.cursor))
    cur1 = M.i32(f, CURSOR_OBJ + CURSOR_OFF)
    rec("cursor_poked", want=a.cursor, read_back=cur1)
    if cur1 != a.cursor:
        return bail("FAIL: cursor poke did not land (%d)" % cur1)

    # --- one INSERT
    M.click(M.INSERT_XY)
    after = None
    for _ in range(12):
        time.sleep(0.5)
        after = M.base_rec(f, idx)
        if after["pending"] > p0:
            break
    if after["pending"] <= p0:
        return bail("FAIL: INSERT did not raise pending (still %d, cursor now %d)"
                    % (after["pending"], M.i32(f, CURSOR_OBJ + CURSOR_OFF)))
    landing = M._shift_index(after["queue"], before["queue"], M.QUEUE_CAP)
    rec("insert", pending_before=p0, pending_after=after["pending"], slots=after["queue"],
        landing=list(landing) if landing else None, stored=landing[1] if landing else None,
        cursor_after=M.i32(f, CURSOR_OBJ + CURSOR_OFF))
    if landing is None:
        return bail("FAIL: the read-back is not a legal shift of the before state")
    pos, stored = landing
    rec("verdict", poked_cursor=a.cursor, wrote_at=pos, stored=stored, item=item,
        plan_sorted_index=plan_pred)

    ok = (pos == a.cursor and stored == item and after["pending"] == p0 + 1)
    print("%s: INSERT of id %d wrote queue[%d]=%d with the widget cursor poked to %d "
          "(pending %d->%d); the plan byte %d would have put it at %d"
          % ("PASS" if ok else "FAIL", item, pos, stored, a.cursor, p0, after["pending"],
             plan, plan_pred))
    sp.wr(f, M.ORDERS_MODE, struct.pack("<i", 1))
    write_trace()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
