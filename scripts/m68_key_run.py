#!/usr/bin/env python3
"""M68: WHICH TYPE-RECORD BYTE IS THE SORT KEY — a multi-INSERT run scored against EVERY
single-byte key (52 offsets x descending/ascending x ties after/before = 208 rules) plus the
four whole-name lexicographic rules.

M67 (PR #65) settled that INSERT is a sorted insert and named the PLAN byte `+42` descending,
refuting the cost byte `+41`, but it said plainly that it had NOT separated `+42` from the
other type-record bytes that happen to rank its two-item shapes the same way (NAMED.md M67
block: name bytes +0,+1,+3,+4,+6,+15..+18, +37, +43 read ASCENDING and predict the same
slots).  Two inserts of two ids in one queue cannot separate them: on the box's Korolev Center
queue, three of the 208 byte rules predict the same two landing slots (measured by
`scripts/m68_typebytes.py`, `evidence/m68_typebytes.jsonl`).

This run inserts FIVE different ids, in an order chosen from the live record bytes BEFORE
clicking, and scores the whole sequence of read-backs.  The shape is only accepted if no key
OTHER than the one under test (`--expect`, default `42:desc:after`, the M67 finding) predicts
that landing sequence — two conventions of the same key may agree, which only means the shape
does not test the tie direction (M67 settled it in PR #65).  A PASS means the sequence of
writes is explained by ONE key: one byte of the 52-byte record, or the name string.  A FAIL
means the gate refused the shape before any click, or the writes match zero keys or several.

195 (Impact Battery) is not in the sequence: at this base an INSERT of it writes -3
(0xfffffffd) into the queue instead of its type id (`scripts/m68_cellprobe.py`,
`evidence/m68_cellprobe.jsonl`), and a queue entry with no type record breaks the engine's
own insert (the next INSERT appended a plan-9 item at the END of the region), which would
confound the shape with a fault rather than test it.

Read model inherited from M67 (NOT a hypothesis): the queue REGION is slots[1..pending]
(`base+0x54 ..`), the head slot `+0x50` is not a queued entry, and the INSERT shift is capped
to the 10-slot queue array `+0x50 .. +0x74`.  `--slots 12` so the dword past the array is
visible and cannot be mistaken for a queue entry.

The only memory writes are the M57 recipe's three enabling pokes (cursor home, SEL_G, orders
mode) — no queue field is ever poked.

    python3 scripts/m68_key_run.py --base-name "University Base" \
        --items 2,1,194,192,193 --trace evidence/m68_key_run.jsonl
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

TYPE_REC, TYPE_SZ, NAME_LEN = M.TYPE_REC, 52, 34
SLOTS = 12  # queue slots read; --slots raises it, and the run refuses a shape whose
        # last write would land outside the read window


def cell_xy(cell):
    return (128 + 127 * (cell % 5), 60 + 100 * (cell // 5))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-name", default="University Base")
    ap.add_argument("--items", default="2,1,194,192,193",
                    help="type ids to INSERT, in click order (each at most once)")
    ap.add_argument("--expect", default="42:desc:after",
                    help="the rule the shape must single out (name:offset:direction:tie form)")
    ap.add_argument("--trace", default="evidence/m68_key_run.jsonl")
    ap.add_argument("--slots", type=int, default=12)
    a = ap.parse_args()
    global SLOTS
    SLOTS = max(a.slots, M.QUEUE_CAP)
    items = [int(x) for x in a.items.split(",") if x.strip() != ""]
    specs = M.key_rule_specs()
    names = [nm for nm, _o, _d, _t in specs]
    # a rule's KEY is the type-record byte offset it reads (None = the whole name string).
    # M68's question is WHICH KEY, so the gate and the verdict work at key level: two
    # conventions of the SAME key may agree on a shape (that shape just does not test the tie
    # direction) while two different keys agreeing is the thing that earns nothing.
    RULE_KEY = {nm: off for nm, off, _d, _t in specs}

    rows = []
    trace_path = a.trace if a.trace.startswith("/") else os.path.join(ROOT, a.trace)

    def write_trace():
        os.makedirs(os.path.dirname(trace_path), exist_ok=True)
        with open(trace_path, "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        print(f"trace: {trace_path} ({len(rows)} rows)")

    def bail(msg):
        """every FAIL prints its reason AND leaves the trace behind, so a failed run is
        still readable evidence."""
        print(msg)
        write_trace()
        return 1

    def rec(tag, **kw):
        row = dict(tag=tag, t=time.strftime("%H:%M:%S"), **kw)
        rows.append(row)
        print(json.dumps(row), flush=True)

    pid, f = sp.mem()
    mine = sp.own_bases_named(f, 3)
    hits = [b for b in mine if b["name"] == a.base_name]
    if len(hits) != 1:
        return bail(f"FAIL: base {a.base_name!r} matched {len(hits)} of our bases: "
              f"{[(b['idx'], b['name']) for b in mine]}")
    idx = hits[0]["idx"]

    old_slots = M.SLOTS
    M.SLOTS = SLOTS

    def snap(tag):
        r = M.base_rec(f, idx)
        r["rows"] = M.count_rows(f, r["fac"])
        rec(tag, idx=r["i"], name=r["name"], x=r["x"], y=r["y"], minerals=r["minerals"],
            pending=r["pending"], slots=r["queue"], d0=r["d0"],
            guard=M.i32(f, M.GUARD), pane_idx=M.u32(f, M.PANE_BASE_IDX))
        return r

    before = snap("before")
    s, p0 = before["queue"], before["pending"]

    rec_cache = {}

    def rec_bytes(tid):
        """the whole 52-byte live type record; an id with no record reads all 0xFF so it can
        never be mistaken for a real entry's key."""
        if tid not in rec_cache:
            try:
                rec_cache[tid] = sp.rd(f, TYPE_REC + tid * TYPE_SZ, TYPE_SZ)
            except Exception:
                rec_cache[tid] = b"\xff" * TYPE_SZ
        return rec_cache[tid]

    def rec_name(tid):
        return rec_bytes(tid)[:NAME_LEN].split(b"\0")[0].decode("latin-1", "replace")

    def keyf(off):
        if off is None:
            return rec_name
        return lambda tid: rec_bytes(tid)[off]

    # ---- the shape, checked BEFORE clicking -------------------------------------------
    involved = sorted(set(items + s[1:p0 + 1]))
    table = {tid: {"name": rec_name(tid), "cost": rec_bytes(tid)[M.COST_OFF],
                   "plan": rec_bytes(tid)[M.PLAN_OFF]} for tid in involved}
    rec("type_recs", base=before["name"], pending=p0, region=s[1:p0 + 1], items=items,
        records={tid: {k: v for k, v in d.items() if k != "name"} | {"name": d["name"]}
                 for tid, d in table.items()})

    for it in items:
        if it == 0:
            return bail(f"FAIL: item {it} is id 0 and unused queue slots read 0 — the written slot "
                  f"would be indistinguishable from an empty slot")
        if s.count(it) >= 2:
            return bail(f"FAIL: item {it} already appears {s.count(it)}x in the baseline slots {s} "
                  f"— the written slot could not be identified")
        if it == 2 and 2 in s[1:p0 + 1]:
            return bail(f"FAIL: item 2 (Scout Patrol) is already a queued entry in the region "
                  f"{s[1:p0 + 1]} — the written slot could not be identified")
    if len(set(items)) != len(items):
        return bail(f"FAIL: --items repeats an id ({items}); the second write of the same id is "
              f"unidentifiable")
    if p0 + len(items) > M.QUEUE_CAP - 1:
        return bail(f"FAIL: pending {p0} + {len(items)} inserts needs region slot "
              f"{p0 + len(items)} but the queue array holds {M.QUEUE_CAP - 1} (the enqueue "
              f"refuses pending >= 9 at 0x418b05)")
    if p0 + len(items) > SLOTS - 1:
        return bail(f"FAIL: pending {p0} + {len(items)} inserts needs region slot "
              f"{p0 + len(items)} but only {SLOTS - 1} are read (--slots)")

    preds = M.key_shape_predictions(s, p0, items, keyf)
    if a.expect not in preds:
        return bail(f"FAIL: --expect {a.expect!r} is not one of the {len(specs)} candidate rules "
              f"({names[:6]} ...)")
    exp_lands, exp_group, n_groups, largest, exp_keys = M.key_shape_gate(preds, a.expect)
    exp_key = RULE_KEY[a.expect]
    rec("plan", base=before["name"], items=items, pending_before=p0, baseline=s,
        expect=a.expect, expected_landing=list(exp_lands),
        records=table, n_candidate_rules=len(specs))
    rec("shape_gate", expected_landing=list(exp_lands),
        rules_predicting_the_same=sorted(exp_group),
        n_distinct_prediction_groups=n_groups,
        largest_group_size=largest,
        predictions={nm: preds[nm] for nm in names if nm in
                     (set(exp_group) | {a.expect, "42:asc:after", "41:desc:after",
                                        "name_str:desc:after", "name_str:asc:after",
                                        "name_str:desc:before", "name_str:asc:before"})})
    rec("key_gate", expect=a.expect, expect_key=exp_key, keys_predicting_the_same=sorted(
        str(k) for k in exp_keys), rules_predicting_the_same=sorted(exp_group))
    same_keys = sorted(str(k) for k in exp_keys)
    if len(exp_keys) != 1:
        return bail(f"FAIL: {len(exp_group)} candidate rules predict the same landing sequence "
                    f"{list(exp_lands)} as {a.expect}, and they read bytes {same_keys} — "
                    f"different keys agree, so this shape cannot identify the key byte and no "
                    f"claim would be earned; pick items whose byte order differs (records "
                    f"{table})")
    rival_groups = {}
    for nm, land in preds.items():
        rival_groups.setdefault(tuple(land), []).append(nm)
    rival_groups.pop(exp_lands, None)
    rec("rivals", n_rivals=len(names) - 1,
        rival_groups={str(k): sorted(v) for k, v in rival_groups.items()})

    # ---- the three enabling pokes (NOT queue fields) — the M57 recipe -----------------
    tx, ty = hits[0]["x"], hits[0]["y"]
    w = M.u32(f, M.WIN_G)
    sp.wr(f, w + M.WIN_CUR_X, struct.pack("<i", tx))
    sp.wr(f, w + M.WIN_CUR_Y, struct.pack("<i", ty))
    ci = M.u32(f, M.CI)
    sp.wr(f, M.CX + ci * 4, struct.pack("<i", tx))
    sp.wr(f, M.CY + ci * 4, struct.pack("<i", ty))
    sp.wr(f, M.SEL_G, struct.pack("<i", -1))
    sp.wr(f, M.ORDERS_MODE, struct.pack("<i", 0))
    rec("pokes", cursor=(M.i32(f, w + M.WIN_CUR_X), M.i32(f, w + M.WIN_CUR_Y)),
        sel=M.i32(f, M.SEL_G), orders_mode=M.i32(f, M.ORDERS_MODE))

    sp.find_window()
    sp.focus()
    sp.key("b")
    time.sleep(0.6)
    for _ in range(8):
        if M.u32(f, M.PANE_BASE_IDX) == idx:
            break
        M.click(M.ARROW_XY)
    rec("pane", pane_idx=M.u32(f, M.PANE_BASE_IDX), want=idx)
    if M.u32(f, M.PANE_BASE_IDX) != idx:
        return bail("FAIL: the QUEUE widget never landed on the target base")

    M.click(M.ROW1_XY)
    time.sleep(0.6)
    c_open = M.cand(f)
    rec("chooser_open", guard=M.i32(f, M.GUARD),
        pending=M.i32(f, sp.BASE_ARR + idx * sp.BASE_SZ + 0x4c), cand=c_open[:24])

    state = {"pending": p0, "slots": list(s)}
    steps = []
    for n, it in enumerate(items):
        c_now = M.cand(f)
        if it not in c_now:
            return bail(f"FAIL: item {it} is not in the chooser's list as it reads before click "
                  f"{n + 1}: {c_now[:24]}")
        cell = c_now.index(it)
        if c_now.count(it) != 1:
            return bail(f"FAIL: item {it} appears {c_now.count(it)}x in the candidate array "
                  f"{c_now[:24]} — the cell would be ambiguous")
        M.click(cell_xy(cell))
        g = M.i32(f, M.GUARD)
        c_after_click = M.cand(f)
        if g != cell:
            return bail(f"FAIL: after clicking cell {cell} (item {it}) the chooser guard reads {g}")
        r = None
        for try_n in range(4):
            M.click(M.INSERT_XY)
            for _ in range(10):
                time.sleep(0.5)
                r = M.base_rec(f, idx)
                if r["pending"] > state["pending"]:
                    break
            if r["pending"] > state["pending"]:
                break
            M.click(M.ARROW_XY)
            rec(f"insert_{n + 1}_retry", pane_idx=M.u32(f, M.PANE_BASE_IDX),
                pending=r["pending"], slots=r["queue"], try_n=try_n + 1)
        if r is None or r["pending"] <= state["pending"]:
            return bail(f"FAIL: INSERT of item {it} never incremented pending {state['pending']}")
        after_slots = r["queue"]
        w_idx = M._shift_index(after_slots, state["slots"], M.QUEUE_CAP)
        stored = w_idx[1] if w_idx else None
        steps.append((list(state["slots"]), state["pending"], list(after_slots), r["pending"]))
        rec(f"insert_{'a' if n == 0 else 'b' if n == 1 else n + 1}", item=it, cell=cell,
            guard=g, pending=r["pending"], slots=after_slots, minerals=r["minerals"],
            d0=r["d0"], cand_at_click=c_after_click[:max(cell, 0) + 1],
            cand_before_click=c_now[:max(cell, 0) + 1],
            cell_entry=c_after_click[cell] if cell < len(c_after_click) else None,
            stored_id=stored, tries=try_n + 1)
        if stored != it:
            return bail(f"FAIL: INSERT wrote {stored}, not the intended item {it} (cell {cell} read "
                  f"{c_after_click[cell] if cell < len(c_after_click) else None} after the "
                  f"click); the candidate array re-sorted between the read and the click")
        state["pending"] = r["pending"]
        state["slots"] = list(after_slots)

    M.click(M.OK_XY)
    time.sleep(0.8)
    after = snap("after_ok")
    row_delta = M.row_diff(before["rows"], after["rows"])

    sp.wr(f, M.ORDERS_MODE, struct.pack("<i", 1))
    rec("orders_restored", orders_mode=M.i32(f, M.ORDERS_MODE))
    kind = None
    for _ in range(4):
        png = sp.freeze("m68pane")
        kind = sp.classify(sp.ocr_fast(png), sp.region_colors(png), png)
        if kind != "base":
            break
        sp.key("Escape")
        time.sleep(1.6)
    rec("pane_closed", screen_class=kind, row_delta_after_ok=row_delta)

    # ---- score ------------------------------------------------------------------------
    fits, detail = [], {}
    for nm, off, d, t in specs:
        kf = keyf(off)
        res = M.score_key_sequence(steps, kf, d, t)
        if res:
            fits.append(nm)
            detail[nm] = res[1]
    obs = [M._shift_index(st[2], st[0], M.QUEUE_CAP)[0] for st in steps]
    obs_ids = [M._shift_index(st[2], st[0], M.QUEUE_CAP)[1] for st in steps]
    integrity = (after["pending"] == p0 + len(items)
                 and obs_ids == items
                 and all(M._shift_index(st[2], st[0], M.QUEUE_CAP) for st in steps)
                 and all(v in after["queue"] for v in items))
    fit_keys = sorted({str(RULE_KEY[nm]) for nm in fits})
    rec("score", baseline=s, pending_before=p0, steps=[
        {"before": st[0], "pending_before": st[1], "after": st[2], "pending_after": st[3]}
        for st in steps],
        after_ok=after["queue"], observed_landing=obs, written_ids=obs_ids,
        matched=fits, matched_keys=fit_keys, predicted_for_matches=detail,
        integrity=integrity, n_candidate_rules=len(specs))

    print("\nread-backs (pending, queue slots, head slot first):")
    print(f"  baseline   pending {p0:<2}  slots {s}")
    for n, st in enumerate(steps):
        print(f"  after {items[n]:<5}  pending {st[3]:<2}  slots {st[2]}")
    print(f"  after OK   pending {after['pending']:<2}  slots {after['queue']}")
    print("\nwhat each candidate rule predicted for the WHOLE sequence vs what was WRITTEN:")
    for nm, off, d, t in specs:
        fit = "FITS" if nm in fits else "    "
        star = " <- expected" if nm == a.expect else ""
        print(f"  {fit} {nm:<20} +{('name' if off is None else off):<5} {d:<4} ties {t:<6} "
              f"predicted {preds[nm]} actual {obs}{star}")
    print("\ncontested per-faction byte arrays, entries that MOVED (before -> after OK):")
    if row_delta:
        for k, v in sorted(row_delta.items()):
            print(f"  {k:<14} {v}")
    else:
        print("  (neither array moved)")

    # the verdict is at KEY level: one byte offset (or the name string) must explain every
    # write.  Several CONVENTIONS of that one key may fit — that only means the shape did not
    # test the tie direction, which M67 settled separately (PR #65).
    if len(fit_keys) == 1 and integrity:
        key = fit_keys[0]
        conv = sorted(fits)
        verdict_word = ("MATCHED the expected key" if key == str(exp_key)
                        else "NOT the expected key")
        print(f"\nPASS: exactly one type-record KEY explains all {len(steps)} writes — "
              f"{'the name string' if key == 'None' else 'byte +' + key} "
              f"(conventions that fit: {conv}; pending {p0}->{after['pending']}, ids written "
              f"{obs_ids}; expected {a.expect} -> {verdict_word})")
        verdict = 0
    else:
        print(f"\nFAIL: {len(fits)} of the {len(specs)} candidate rules fit = {sorted(fits)} "
              f"over keys {fit_keys} (need exactly one key), integrity = {integrity}; no key "
              f"claim is made")
        verdict = 1

    write_trace()
    M.SLOTS = old_slots
    return verdict


if __name__ == "__main__":
    sys.exit(main())
