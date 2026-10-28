#!/usr/bin/env python3
"""M73 — SPLIT the `edi` the visit gates on: whose value is it, and where does 27 come from?

M72 measured the product: at 0x4efa5e the affordability test is `cmp [base+0x40],edi` and for
head 193 `edi` is 27 while `m56_build.price_of` says 18 (head 2: 9, where the two agree).  The
instruction bytes at 0x4efa2c-0x4efa52 (scratch/m574/text.txt) show edi is a PRODUCT of two
separately computed calls:

  0x4efa2c  ebx = [base+0x50]  the queue head
  0x4efa3c  call 0x4e40a0(owner, 1, -1) -> eax        FACTOR A, the pace/faction percent
  0x4efa4b  edi = eax
  0x4efa4d  call 0x5ac950(head, [0x68cbb0], 0) -> eax FACTOR B, the head's own price
  0x4efa52  edi *= eax
  0x4efa5e  cmp [base+0x40], edi

`scripts/m56_build.price_of` is documented as `0x4e40a0(owner,1,-1) x type_cost(+41)`, and +41
IS +0x29, the byte 0x5ac950 starts from — so A is already modelled in Python and the whole 27-vs-18
gap lives inside 0x5ac950.  Its instruction bytes (0x5ac950..0x5acaaf) give B exactly:

  ebx = type[+0x29] (clamped to 1 / 999 only when type[+0x2a] == 8 and param_2 > -1)
  id < 0x40 OR type[+0x30] & 4      -> return the byte, NO markup (0x5aca9c)
  cat = id >> 6;  [0x927a98 + 1436*cat] & 0x200        -> markup 0 (0x5ac9c0)
              [0x94d438 + 8380*cat] <= 1               -> markup 0 (0x5ac9e0)
  P = [0x92a2d4] if [0x92ae81 + 144*type[+0x24]] == 1, [0x92a2d8] if == 2, else [0x92a2d0]
  C = 0x595ad0(id) = 0x595820(type+0x24, type+0x25, type+0x26, 0, type+0x27)
  M = (C*P + 50) / 100   (imul 0x5aca2f, add 0x5aca32, imul-magic + sar 5 = signed div 100)
  if param_2 > -1 and (base[+0x8c ..] & (byte)id) != 0  -> M = 0   (0x5aca6b-0x5aca81)
  return  ebx + M   (0x5aca86)

So B is `cost + markup`, and this run reads every term live for TWO designed ids whose
price_of values differ (193: cost 2, price 18; 194: cost 3, price 27) in ONE invocation, with
the queue [2, 194, 193] so the engine itself makes each one the head in turn.

THE ACCEPTANCE (written before the run; PASS on ONE real invocation):
  1 arm        both armed ids sit in the armed base's first six queue slots and storage was
               poked and READ BACK before gdb attached to at least what every queued id ahead of
               them must pay (each one pays before it pops, so the last armed id can be visited);
  2 window     the round counter advanced and >= 1 VISIT fired for the armed base;
  3 factors    >= 1 FACTORA and >= 1 FACTORB row for >= 2 distinct designed ids, and for each id
               A*B equals the edi logged at that id's POSAFF/PAYA/CREATE rows (the imul identity
               on the run's own numbers);
  4 A          every FACTORA row's A equals the Python cost_multiplier(owner) computed from the
               same snapshot before attach (A is the repo's model, not a new constant);
  5 B          for each armed id, PRICE_C / PRICE_M / PRICE_B rows whose logged `ret` is the
               visit's own call site 0x4efa52, with the markup read BEFORE the base-mask zeroing
               satisfying Mpre == trunc_div(C*P+50, 100) on that row's own logged C and P, and
               B == cost + M and B == that id's FACTORB B (a markup that later became 0 is the
               base mask test at 0x5aca81 and is REPORTED, not accepted silently);
  6 shape      the candidate edi vectors (built BEFORE attach from live memory: A x (cost +
               trunc_div(C*P+50,100)) over the readable type bytes 0x595820 is built from, with
               P = 0 when a static guard zeroes markup, plus A x cost = price_of) are NOT all
               equal — if every candidate predicts the same thing the shape cannot discriminate
               and the run FAILs;
  7 economic   the measured edi is NOT price_of for at least one armed id AND equals
               A x (cost + M) for every armed id: the visit's requirement is the markup-included
               price, not the repo's `price_of`;
  8 single     the measured edi has exactly ONE value per armed id (a second value would mean
               something moved under the window); which readable-C candidate, if any, matches the
               measured pair is REPORTED, not gated — 0x595ad0 may return a computed value;
  9 stability  the armed record is still the same base by name at the same address;
  10 parse     every log line parsed into a known tag.

Usage:
    python3 scripts/m73_price_split.py [--base-name "University Base"] [--ids 193,194]
                                       [--boundaries 4] [--poke-minerals 120]
                                       [--timeout 500] [--tag m73split]
"""
import argparse
import json
import os
import re
import signal
import struct
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import m55_boundary as M          # noqa: E402
import m56_build as B             # noqa: E402

BASE_ARR, BASE_SZ = 0x95DA10, 304
TYPE_ARR, TYPE_STRIDE = 0x98AD88, 0x34
ENTRY, VISIT = 0x4EF6D0, 0x4F5A93
FACTORA, FACTORB, POSAFF, BAILAFF = 0x4EFA4B, 0x4EFA52, 0x4EFA5E, 0x4EFA63
PAYA, CREATE = 0x4EFED8, 0x4EFF4E
PRICE_C, PRICE_M, PRICE_B = 0x5ACA28, 0x5ACA4B, 0x5ACA88
VISIT_CALLSITE = 0x4EFA52          # the `imul edi,eax` that consumes 0x5ac950's return
GUARD_CAT = 0x927A98               # per-category dword, bit 0x200 = markup 0
GUARD_ERA = 0x94D438               # per-category int, <= 1 = markup 0
OPT_TABLE = 0x92AE81               # per type[+0x24] record, byte +1 selects the option dword
OPT_DWORDS = {0: 0x92A2D0, 1: 0x92A2D4, 2: 0x92A2D8}
GATE_ROWS = ("POSAFF", "BAILAFF", "PAYA")
EVID = os.path.join(ROOT, "evidence")


# ---------------------------------------------------------------- memory
def game_pid():
    return M.find_pid()


def base_row(m, name):
    for i in range(max(0, min(B.rd32(m, 0x985AF4), 64))):
        b = B.prod_fields(m, i)
        if b["name"] == name:
            rec = M.rd(m, BASE_ARR + i * BASE_SZ, BASE_SZ)
            b["slots"] = [struct.unpack("<i", rec[0x50 + 4 * k:0x54 + 4 * k])[0] for k in range(12)]
            b["addr"] = BASE_ARR + i * BASE_SZ
            tl = M.timeline_row(m)
            b["year"], b["round"], b["cur_player"] = tl["year"], tl["round"], tl["cur_player"]
            return b
    raise SystemExit(f"base {name!r} not found in the base array")


def i32(m, a):
    return struct.unpack("<i", M.rd(m, a, 4))[0]


def u32(m, a):
    return struct.unpack("<I", M.rd(m, a, 4))[0]


def byte(m, a):
    return M.rd(m, a, 1)[0]


def type_bytes(m, t):
    """The fields 0x5ac950 / 0x595ad0 read out of the type record, by id."""
    r = M.rd(m, TYPE_ARR + t * TYPE_STRIDE, TYPE_STRIDE)
    return dict(cost=r[0x29], sel=r[0x2a], cat_field=r[0x24], lvl=r[0x25], f26=r[0x26],
                f27=r[0x27], flags30=struct.unpack("<I", r[0x30:0x34])[0])


def static_inputs(m, t):
    """Everything 0x5ac950 reads that is NOT a function result, plus which guards zero markup.

    P is what the function actually multiplies by: 0 when the category flag 0x200 or the
    [0x94d438] test fires (0x5ac9cd / 0x5ac9cd jump with edi zeroed), else the option dword the
    type[+0x24] selector picks.  `early` (id < 0x40 or type[+0x30] bit 2) returns before any of
    that, so no markup and no PRICE row at all.
    """
    tb = type_bytes(m, t)
    cat = t >> 6
    flag200 = bool(u32(m, GUARD_CAT + 1436 * cat) & 0x200)
    era = i32(m, GUARD_ERA + 8380 * cat)
    sel = byte(m, OPT_TABLE + 144 * tb["cat_field"])
    p_opt = i32(m, OPT_DWORDS.get(sel, 0x92A2D0))
    early = (t < 0x40) or bool(tb["flags30"] & 4)
    guard_zero = early or flag200 or era <= 1
    P = 0 if (flag200 or era <= 1) else p_opt
    return dict(id=t, cost=tb["cost"], cat=cat, flag200=flag200, era=era, sel=sel, P=P,
                P_opt=p_opt, early=early, guard_zero=guard_zero, cbytes=dict(
                    cost=tb["cost"], lvl=tb["lvl"], f26=tb["f26"], f27=tb["f27"],
                    cat_field=tb["cat_field"], one=1))


C_MODELS = ("cost", "lvl", "f26", "f27", "cat_field", "one")


def candidates(m, owner, ids):
    """Every edi vector the instruction model can produce, built BEFORE the run.

    A is Python's cost_multiplier(owner) (already the repo's model of 0x4e40a0).  P is read per
    id from the option dword that type[+0x24]'s selector picks — that is state, not a hypothesis.
    The hypothesis is only WHICH value 0x595ad0 returns, so the candidate set is the readable
    type bytes 0x595820 is built from, plus markup 0 (which is `price_of` itself).  A candidate
    whose static guard zeroes markup collapses to A*cost.  Vectors are deduped by value.
    """
    A = B.cost_multiplier(m, owner)["factor"]
    si = {t: static_inputs(m, t) for t in ids}
    cands = {}
    for name, cmodel in [("price_of", None)] + [(f"C={c}", c) for c in C_MODELS]:
        vec = {}
        for t in ids:
            s = si[t]
            mk = 0 if (name == "price_of" or s["guard_zero"]) else \
                B.trunc_div(s["cbytes"][cmodel] * s["P"] + 50, 100)
            vec[t] = A * (s["cost"] + mk)
        key = tuple(vec[t] for t in ids)
        cands.setdefault(key, dict(vector=vec, name=name, C=cmodel, n=0))["n"] += 1
    return A, si, list(cands.values())


# ---------------------------------------------------------------- gdb
TMPL = r"""set pagination off
set confirm off
set height 0
set verbose off
set can-use-hw-watchpoints 1
set $b = @@ADDR@@
set $ids = @@IDS@@
break *0x4ef6d0 if *(int *)0x8f0d60 == $b
commands
silent
printf "ENTRY base=0x%x storage=%d s0=%d pend=%d\n", $b, *(int *)($b + 0x40), *(int *)($b + 0x50), *(int *)($b + 0x4c)
continue
end
break *0x4f5a93 if $ecx == $b
commands
silent
printf "VISIT pend=%d s0=%d s1=%d min=%d\n", *(int *)($b + 0x4c), *(int *)($b + 0x50), *(int *)($b + 0x54), *(int *)($b + 0x40)
continue
end
break *0x4efa4b if *(int *)0x8f0d60 == $b
commands
silent
printf "FACTORA id=%d own=%d A=%d\n", $ebx, *(int *)($b + 4), $eax
continue
end
break *0x4efa52 if *(int *)0x8f0d60 == $b
commands
silent
printf "FACTORB id=%d A=%d B=%d\n", $ebx, $edi, $eax
continue
end
break *0x4efa5e if *(int *)0x8f0d60 == $b
commands
silent
printf "POSAFF storage=%d edi=%d ebx=%d\n", *(int *)($b + 0x40), $edi, $ebx
continue
end
break *0x4efa63 if *(int *)0x8f0d60 == $b
commands
silent
printf "BAILAFF storage=%d edi=%d ebx=%d\n", *(int *)($b + 0x40), $edi, $ebx
continue
end
break *0x4efed8 if $ecx == $b
commands
silent
printf "PAYA storage=%d edi=%d ebx=%d\n", *(int *)($ecx + 0x40), $edi, $ebx
continue
end
break *0x4eff4e if *(int *)0x8f0d60 == $b
commands
silent
printf "CREATE id=%d arg3=%d storage=%d\n", $ebx, *(int *)($ebp - 0x28), *(int *)($b + 0x40)
continue
end
break *0x5aca28 if $esi == @@ID0@@ || $esi == @@ID1@@
commands
silent
printf "PRICE_C id=%d P=%d byte=%d C=%d p2=%d ret=0x%x\n", $esi, $edi, $ebx, $eax, *(int *)($ebp + 0xc), *(int *)($sp + 0x10)
continue
end
break *0x5aca4b if *(int *)($ebp + 8) == @@ID0@@ || *(int *)($ebp + 8) == @@ID1@@
commands
silent
printf "PRICE_M id=%d Mpre=%d\n", *(int *)($ebp + 8), $esi
continue
end
break *0x5aca88 if *(int *)($ebp + 8) == @@ID0@@ || *(int *)($ebp + 8) == @@ID1@@
commands
silent
printf "PRICE_B id=%d B=%d M=%d ret=0x%x\n", *(int *)($ebp + 8), $ebx, $esi, *(int *)($sp + 0x10)
continue
end
printf "ARMED base=0x%x head=%d pending=%d storage=%d\n", $b, *(int *)($b + 0x50), *(int *)($b + 0x4c), *(int *)($b + 0x40)
continue
"""


def gdb_script(addr, ids):
    s = TMPL.replace("@@ADDR@@", hex(addr)).replace("@@IDS@@", ",".join(str(i) for i in ids))
    for k in range(2):
        s = s.replace(f"@@ID{k}@@", str(ids[k] if k < len(ids) else -1))
    return s


LINE = re.compile(r"^(ENTRY|VISIT|FACTORA|FACTORB|POSAFF|BAILAFF|PAYA|CREATE|PRICE_C|PRICE_M|"
                  r"PRICE_B|ARMED)\s*(.*)$")
KV = re.compile(r"(\w+)=(-?0x[0-9a-f]+|-?\d+)")
CHATTER = ("warning:", "Reading symbols", "0x", "Breakpoint", "[", "The program", "This GDB",
           "Enable debuginfod", "<https://debuginfod", "Debuginfod has been disabled",
           "To make this setting", "Thread ", "received signal SIGINT")


def parse(text):
    """Pure: gdb log text -> ordered event rows.  Returns (events, unparsed_lines)."""
    ev, bad = [], []
    for raw in text.splitlines():
        s = raw.strip()
        if not s:
            continue
        m = LINE.match(s)
        if not m:
            if s.startswith(CHATTER):
                continue
            bad.append(s)
            continue
        d = {"tag": m.group(1)}
        for k, v in KV.findall(m.group(2) or ""):
            neg = v.startswith("-")
            body = v[1:] if neg else v
            n = int(body, 16) if body.lower().startswith("0x") else int(body)
            d[k] = -n if neg else n
        ev.append(d)
    return ev, bad


# ---------------------------------------------------------------- acceptance
def score(before, after, ev, A_py, si, cands, required, bad_lines=()):
    """Pure acceptance.  Returns (ok, gates, findings).

    `required` is the storage the engine must have by the time the LAST armed id is visited: the
    largest candidate edi of every queued id up to and including it (each one pays before it pops).
    """
    gates, find = [], []
    rows = [e for e in ev if e["tag"] != "ARMED"]
    ids = [t for t in si]

    pos = {t: k for k, t in enumerate(before["slots"]) if t in si}
    gates.append(("1 the armed ids are in the armed base's queue and storage was read back >= "
                  "every pay that must happen before the last of them is visited",
                  all(0 <= pos.get(t, 99) < 6 for t in ids) and before["minerals"] >= required,
                  f"queue {before['slots'][:6]} armed {ids} at {pos}, storage "
                  f"{before['minerals']} vs required {required}"))

    visits = [e for e in rows if e["tag"] == "VISIT"]
    gates.append(("2 window round advanced and >= 1 VISIT for the armed base",
                  after["round"] > before["round"] and len(visits) >= 1,
                  f"round {before['round']} -> {after['round']}, {len(visits)} VISIT"))

    fa = [e for e in rows if e["tag"] == "FACTORA"]
    fb = [e for e in rows if e["tag"] == "FACTORB"]
    gate_rows = [e for e in rows if e["tag"] in GATE_ROWS]
    seen = sorted({e["id"] for e in fb} & {e["id"] for e in fa})
    bad_prod = []
    for t in seen:
        ab = {e["A"] * e["B"] for e in fb if e["id"] == t}
        ed = {e["edi"] for e in gate_rows if e.get("ebx") == t}
        if not ab or not ed or ab != ed:
            bad_prod.append(f"id {t}: A*B {sorted(ab)} vs gate-row edi {sorted(ed)}")
    gates.append(("3 both factors logged for >= 2 designed ids and A*B == edi at that id's gate "
                  "rows", len(seen) >= 2 and not bad_prod,
                  f"ids with both factors: {seen}" + (f"  bad: {'; '.join(bad_prod)}" if bad_prod else "")))

    offA = sorted({(e["id"], e["A"]) for e in fa if e["A"] != A_py})
    gates.append((f"4 every FACTORA A equals Python cost_multiplier(owner) = {A_py}",
                  bool(fa) and not offA,
                  f"{len(fa)} FACTORA rows" + (f"  off: {offA}" if offA else "")))

    # B's own terms, from the visit's own call (the logged `ret` says which caller it was).
    # Mpre is read at 0x5aca4b, BEFORE the base-mask zeroing at 0x5aca81, so the formula is
    # checked against the row's own logged C and P; a markup that later became 0 is the mask,
    # and that is reported, not silently accepted.
    pc = [e for e in rows if e["tag"] == "PRICE_C" and e.get("ret") == VISIT_CALLSITE]
    pb = [e for e in rows if e["tag"] == "PRICE_B" and e.get("ret") == VISIT_CALLSITE]
    pm = [e for e in rows if e["tag"] == "PRICE_M"]
    bad_b, covered, mask_zero, guard_conflict = [], [], [], []
    for t in ids:
        c = [e for e in pc if e["id"] == t]
        b_ = [e for e in pb if e["id"] == t]
        m_ = [e for e in pm if e["id"] == t]
        if not c or not b_:
            bad_b.append(f"id {t}: no visit-path PRICE row")
            continue
        covered.append(t)
        C0, P0 = c[0]["C"], c[0]["P"]
        exp = B.trunc_div(C0 * P0 + 50, 100)
        if m_ and m_[0]["Mpre"] != exp:
            bad_b.append(f"id {t}: Mpre {m_[0]['Mpre']} != (C {C0} * P {P0} + 50)/100 = {exp}")
        for e in b_:
            if e["B"] != si[t]["cost"] + e["M"]:
                bad_b.append(f"id {t}: B {e['B']} != cost {si[t]['cost']} + M {e['M']}")
            if m_ and e["M"] != m_[0]["Mpre"]:
                mask_zero.append(f"id {t}: markup {m_[0]['Mpre']} zeroed by the base mask test")
        fbv = {e["B"] for e in fb if e["id"] == t}
        if fbv and fbv != {e["B"] for e in b_}:
            bad_b.append(f"id {t}: 0x5ac950 B {sorted({e['B'] for e in b_})} != FACTORB B {sorted(fbv)}")
        if si[t]["guard_zero"] and P0 != 0:
            guard_conflict.append(f"id {t}: guard says markup 0 but the run logged P {P0}")
    gates.append(("5 B's internals logged from the visit's own call (ret 0x4efa52): Mpre == "
                  "(C*P+50)/100, B == cost + M, B == FACTORB B",
                  bool(covered) and len(covered) == len(ids) and not bad_b,
                  f"covered {covered}" + (f"  bad: {'; '.join(bad_b)}" if bad_b else "")))

    vecs = sorted({tuple(c["vector"][t] for t in ids) for c in cands})
    gates.append(("6 the candidate edi vectors are not all equal (the shape discriminates)",
                  len(vecs) >= 2, f"{len(cands)} candidates, {len(vecs)} distinct vectors: "
                  + "; ".join(str(list(v)) for v in vecs[:6])))

    measured, mlogged = {}, {}
    for e in gate_rows:
        if e.get("ebx") in si:
            measured.setdefault(e["ebx"], set()).add(e["edi"])
    for e in fb:
        if e["id"] in si:
            measured.setdefault(e["id"], set()).add(e["A"] * e["B"])
    for t in ids:
        v = {e["B"] for e in pb if e["id"] == t}      # B already contains the markup (0x5aca86)
        if len(v) == 1:
            mlogged[t] = A_py * next(iter(v))
    not_price_of = [t for t in ids if t in measured and all(
        x != A_py * si[t]["cost"] for x in measured[t])]
    bad_comp = [f"id {t}: measured {sorted(measured.get(t, []))} vs A * the logged B "
                f"{mlogged.get(t)}" for t in ids if t in mlogged and measured.get(t) != {mlogged[t]}]
    gates.append(("7 the visit's requirement is NOT price_of for at least one armed id, and "
                  "equals A*(cost + M) for every armed id",
                  bool(not_price_of) and len(mlogged) == len(ids) and not bad_comp,
                  f"ids where edi != price_of: {not_price_of}"
                  + (f"  bad: {'; '.join(bad_comp)}" if bad_comp else "")))

    multi = [f"id {t}: edi {sorted(v)}" for t, v in sorted(measured.items()) if len(v) != 1]
    gates.append(("8 the measured edi has exactly ONE value per armed id (a second value means "
                  "the state moved under the window)", bool(measured) and not multi,
                  f"measured { {t: sorted(v) for t, v in measured.items()} }"
                  + (f"  multi-valued: {multi}" if multi else "")))

    hits = [c for c in cands if all(measured.get(t) == {c["vector"][t]} for t in ids)]

    gates.append(("9 armed record is still the same base by name at the same address",
                  after["addr"] == before["addr"] and after["name"] == before["name"],
                  f"armed 0x{before['addr']:x} now 0x{after['addr']:x} ({after['name']!r})"))
    gates.append(("10 parse every log line into a known tag", not bad_lines,
                  f"{len(bad_lines)} unknown lines"
                  + (": " + " | ".join(bad_lines[:3]) if bad_lines else "")))

    find.append(f"A (0x4e40a0) = {A_py}; per id: " + ", ".join(
        f"id {t}: cost +0x29 {si[t]['cost']} cat {si[t]['cat']} flag200 {si[t]['flag200']} "
        f"era {si[t]['era']} P {si[t]['P']} (sel {si[t]['sel']}) early {si[t]['early']} "
        f"guard_zero {si[t]['guard_zero']}" for t in ids))
    find.append("measured A*B per id: " + ", ".join(
        f"id {t}: {sorted(v)}" for t, v in sorted(measured.items())))
    find.append("PRICE_C rows: " + (", ".join(
        f"id {e['id']} P {e['P']} byte {e['byte']} C {e['C']} p2 {e['p2']}" for e in pc) or "none"))
    find.append("PRICE_B rows: " + (", ".join(f"id {e['id']} B {e['B']} M {e['M']}" for e in pb) or "none"))
    find.append("markup zeroed by the base mask test: " + ("; ".join(sorted(set(mask_zero)))
                                                          or "none observed"))
    find.append("static guard vs logged P conflicts: " + ("; ".join(sorted(set(guard_conflict)))
                                                         or "none"))
    find.append("readable-C candidate that matches the measured pair: "
                + (", ".join(f"{c['name']} -> {[c['vector'][t] for t in ids]}" for c in hits)
                   if hits else "none (0x595ad0 returns a computed value, not a readable byte)"))
    find.append("ordered stream: " + (" -> ".join(e["tag"] for e in rows) or "empty"))
    ok = all(g[1] for g in gates)
    return ok, gates, find


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-name", default="University Base")
    ap.add_argument("--ids", default="193,194")
    ap.add_argument("--boundaries", type=int, default=4)
    ap.add_argument("--poke-minerals", type=int, default=None)
    ap.add_argument("--timeout", type=float, default=500.0)
    ap.add_argument("--tag", default="m73split")
    a = ap.parse_args()
    ids = [int(x) for x in a.ids.split(",")]
    if len(ids) < 2:
        raise SystemExit("--ids needs two designed ids to discriminate")
    if any(i < 0x40 for i in ids):
        raise SystemExit("--ids must both be designed ids (>= 0x40); below that 0x5ac950 returns "
                         "the bare type byte and cannot carry a markup")

    if subprocess.run(["pgrep", "-x", "gdb"], capture_output=True, text=True).stdout.strip():
        raise SystemExit("a gdb is already running — stop it first")
    pid = game_pid()
    tracer = subprocess.run(["grep", "-m1", "TracerPid", "/proc/%d/status" % pid],
                            capture_output=True, text=True).stdout.split()[-1]
    if tracer != "0":
        raise SystemExit("TracerPid=%s != 0" % tracer)
    if subprocess.run(["sysctl", "-n", "kernel.yama.ptrace_scope"],
                      capture_output=True, text=True).stdout.strip() != "0":
        raise SystemExit("ptrace_scope != 0")

    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        before = base_row(m, a.base_name)
        A_py, si, cands = candidates(m, before["fac"], ids)
        pos = {t: k for k, t in enumerate(before["slots"]) if t in ids}
        if not ids or max(pos.values(), default=99) >= 6:
            raise SystemExit(f"arm gate: armed ids {ids} are not in the first six queue slots "
                             f"({before['slots'][:6]}) — enqueue them first")
        head_ids = [t for t in before["slots"][:max(pos.values()) + 1] if t > 0]
        _, _, cands_all = candidates(m, before["fac"], head_ids)
        required = sum(max(c["vector"][t] for c in cands_all) for t in head_ids)
    maxcand = max(max(c["vector"].values()) for c in cands)
    print(f"static (read before attach): owner {before['fac']} A = {A_py}")
    for t in ids:
        s = si[t]
        print(f"  id {t}: cost +0x29 = {s['cost']}  cat {s['cat']}  flag200 {s['flag200']}  "
              f"[0x94d438] {s['era']}  P {s['P']} (option {s['P_opt']}, sel {s['sel']})  "
              f"early {s['early']}  guard_zero {s['guard_zero']}")
    print("  candidates (edi per id " + str(ids) + "):")
    for c in sorted(cands, key=lambda c: (tuple(c["vector"][t] for t in ids), c["name"])):
        print(f"    {c['name']:12} -> {[c['vector'][t] for t in ids]}  (x{c['n']})")
    print(f"  queue {before['slots'][:6]}: the engine must pay through {head_ids} before "
          f"{ids[-1]} is visited -> storage >= {required}")

    poke = a.poke_minerals if a.poke_minerals is not None else required + 30
    poked = None
    if poke != before["minerals"]:
        with open(f"/proc/{pid}/mem", "rb+", 0) as m:
            m.seek(before["addr"] + 0x40)
            m.write(struct.pack("<i", poke))
            m.seek(before["addr"] + 0x40)
            poked = struct.unpack("<i", m.read(4))[0]
        with open(f"/proc/{pid}/mem", "rb", 0) as m:
            before = base_row(m, a.base_name)
    if before["minerals"] < required:
        raise SystemExit(f"arm gate: storage {before['minerals']} < required {required} "
                         f"after the poke")

    gpath = os.path.join(ROOT, "scratch", f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.gdblog")
    os.makedirs(os.path.dirname(gpath), exist_ok=True)
    open(gpath, "w").write(gdb_script(before["addr"], ids))
    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=log, stderr=subprocess.STDOUT)
    time.sleep(3.0)
    head = open(lpath, "r", errors="replace").read()
    if "ARMED" not in head:
        os.kill(g.pid, signal.SIGINT)
        time.sleep(1.0)
        raise SystemExit("gdb did not arm:\n" + head[-1500:])
    print(f"armed: base {a.base_name!r} addr 0x{before['addr']:x} head {before['slots'][0]} "
          f"pending {before['pending']} queue {before['slots'][:4]} storage {before['minerals']} "
          f"({'read back' if poked else 'already'} vs largest candidate {maxcand}); "
          f"round {before['round']}", flush=True)

    t0 = time.time()
    for k in range(a.boundaries):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "smac_play.py"),
                            "--turns", "1", "--timeout", str(int(min(a.timeout, 220))),
                            "--no-escape", "3000", "--orders-per-turn", "1",
                            "--verbose", "--tag", f"{a.tag}_r{k}"],
                           capture_output=True, text=True)
        print(f"  boundary {k}: rc={r.returncode} t={time.time()-t0:.0f}s "
              f"{r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ''}", flush=True)

    try:
        os.kill(g.pid, signal.SIGINT)
    except ProcessLookupError:
        pass
    for _ in range(40):
        if not os.path.exists("/proc/%d" % g.pid):
            break
        time.sleep(0.5)
    subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
    log.close()

    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        after = base_row(m, a.base_name)
    text = open(lpath, "r", errors="replace").read()
    ev, bad = parse(text)
    with open(os.path.join(EVID, f"{a.tag}_seq.jsonl"), "w") as fh:
        for d in ev:
            fh.write(json.dumps(d) + "\n")

    print("--- ordered stream (armed base only) ---")
    for e in ev:
        print("  " + " ".join(f"{k}={v}" for k, v in e.items()))
    print(f"read back: head {before['slots'][0]} -> {after['slots'][0]}  pending "
          f"{before['pending']} -> {after['pending']}  queue {before['slots'][:4]} -> "
          f"{after['slots'][:4]}  storage {before['minerals']} -> {after['minerals']}  round "
          f"{before['round']} -> {after['round']}")
    ok, gates, find = score(before, after, ev, A_py, si, cands, required, bad)
    print("--- gates ---")
    for name, good, detail in gates:
        print(f"  [{'PASS' if good else 'FAIL'}] {name}: {detail}")
    print("--- findings ---")
    for f in find:
        print("  " + f)
    print(f"log {os.path.relpath(lpath, ROOT)} ({len(ev)} events)")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
