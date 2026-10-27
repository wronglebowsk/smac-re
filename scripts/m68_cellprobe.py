#!/usr/bin/env python3
"""M68 probe: click ONE chooser cell, click INSERT, read back what the queue got.

The acceptance run wrote -3 (0xfffffffd) into the queue for chooser cell 6 (the array entry
reads 195) while cells 1, 2 and 3 stored their array entries exactly.  This probe answers
which of "that id" or "that cell" produced the -3, with nothing but clicks and reads: it
clicks the cell for one id and prints the value the queue actually received.

It assumes the BUILD chooser is already open on the target base (the acceptance run leaves it
open when it bails) and re-arms the cursor pokes (the M57 recipe's three, no queue fields).
"""
import argparse
import json
import os
import struct
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import smac_play as sp  # noqa: E402
import m66_insert_slot as M  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-name", default="University Base")
    ap.add_argument("--item", type=int, required=True)
    ap.add_argument("--trace", default="evidence/m68_cellprobe.jsonl")
    a = ap.parse_args()
    M.SLOTS = 12
    ROOT_DIR = ROOT
    rows = []

    def rec(tag, **kw):
        row = dict(tag=tag, t=time.strftime("%H:%M:%S"), **kw)
        rows.append(row)
        print(json.dumps(row), flush=True)

    def write_trace():
        path = a.trace if a.trace.startswith("/") else os.path.join(ROOT_DIR, a.trace)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        print(f"trace: {path} ({len(rows)} rows)")

    def bail(msg):
        print(msg)
        write_trace()
        return 1

    pid, f = sp.mem()
    mine = sp.own_bases_named(f, 3)
    hits = [b for b in mine if b["name"] == a.base_name]
    if len(hits) != 1:
        print(f"FAIL: base {a.base_name!r} matched {len(hits)} of our bases")
        return 1
    idx = hits[0]["idx"]

    tx, ty = hits[0]["x"], hits[0]["y"]
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
    rec("before", item=a.item, pending=before["pending"], slots=before["queue"],
        minerals=before["minerals"], guard=M.i32(f, M.GUARD),
        pane_idx=M.u32(f, M.PANE_BASE_IDX))
    if M.u32(f, M.PANE_BASE_IDX) != idx:
        sp.key("b")
        time.sleep(0.6)
        for _ in range(8):
            if M.u32(f, M.PANE_BASE_IDX) == idx:
                break
            M.click(M.ARROW_XY)
        M.click(M.ROW1_XY)
        time.sleep(0.6)
    c = M.cand(f)
    if a.item not in c:
        write_trace()
        return bail(f"item {a.item} not in the chooser list {c[:12]} "
                    f"(cand_n {M.i32(f, M.CAND_N)})")
    cell = c.index(a.item)
    xy = (128 + 127 * (cell % 5), 60 + 100 * (cell // 5))
    rec("chooser", cand=c[:12], cand_n=M.i32(f, M.CAND_N), cell=cell, click_xy=list(xy),
        entry_at_cell=c[cell])
    M.click(xy)
    g = M.i32(f, M.GUARD)
    c2 = M.cand(f)
    rec("after_click", cell=cell, guard=g,
        entry_at_cell=c2[cell] if cell < len(c2) else None, cand=c2[:12])
    p0 = M.base_rec(f, idx)["pending"]
    M.click(M.INSERT_XY)
    r = before
    for _ in range(10):
        time.sleep(0.5)
        r = M.base_rec(f, idx)
        if r["pending"] > p0:
            break
    w_idx = M._shift_index(r["queue"], before["queue"], M.QUEUE_CAP)
    rec("after_insert", item=a.item, pending=r["pending"], pending_before=p0,
        slots=r["queue"], shift_write=list(w_idx) if w_idx else None,
        stored_id=w_idx[1] if w_idx else None, minerals=r["minerals"])
    sp.wr(f, M.ORDERS_MODE, struct.pack("<i", 1))
    write_trace()
    return 0


if __name__ == "__main__":
    sys.exit(main())
