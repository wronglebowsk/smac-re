#!/usr/bin/env python3
"""M71 — WHAT THE POP DOES TO THE QUEUE REGION AND TO THE CURSOR AT A REAL COMPLETION.

M70 named the writers of the queue widget's cursor and proved a PAINT does not rewrite the
queue region.  The one window nobody has watched is the engine's own: the round-boundary
COMPLETION that calls the pop.  M67 read back a sorted queue and M68 read back click-order
appends from a different state; the difference is confounded unless the completion's own
writes are measured.  This instrument arms the cursor field + queue slots 1..3 and the pop's
own sites, drives real round boundaries, and reads the region back from memory after detaching.

THE STATIC MODEL (scratch/m574/text.txt, instruction bytes — this is what the acceptance
tests, cited by address):

  FUN_004ef5d0(base_idx)  THE POP.  ebx = idx, esi = idx*0x130, record = 0x95da10 + esi.
    0x4ef5e4  eax = pending = [rec+0x4c]        0x4ef5ea  cl = owner = [rec+0x04] -> edi
    0x4ef5f4  pending == 0 -> return 0, NO writes
    loop 0x4ef5fa:
      head = [rec+0x50];  head >= 0 -> 0x4ef613 lea ecx,[ecx+edx*4+0x94de84] with
                       edx = 2095*owner  ->  0x4ef61a dec BYTE [ecx]   (queued count--)
      shift 0x4ef628-0x4ef639: for k = 0..pending-1  [rec+0x50+4k] = [rec+0x54+4k]
                       (store 0x4ef62c; slot[pending] itself is NOT touched)
      0x4ef642  pending-- (store)
      new head = [rec+0x50]:  >=0 -> call 0x5a73f0(head, owner, idx)   <0 -> 0x5a6e70(-head,..)
      validator result != 0 -> EXIT at 0x4ef68b (the drain STOPS: the new head is "available")
      validator result == 0 -> loop again while pending != 0
    So ONE pop call consumes K >= 1 items: K stops at the first head the validator calls
    available, or at pending == 0.  Two candidates the shape must separate:
      SINGLE  K = 1            (pending_before - 1)
      DRAIN   K = pending      (pending -> 0)
  The composition of K shifts is NOT "shift left by K": each iteration shifts only
  0..pending_j-1 and pending shrinks, so index k is written (pending_before - k) times:
      after[k] = before[k+K]  for k <= pending-K ;  after[k] = before[pending] for
      pending-K < k <= pending-1 ;  unchanged above.   (shift_predict below)
  COMPLET 0x4efe41 `cmp ebx,0x40; jl 0x4efed1` splits designed ids from base-type ids;
  both branches reach the pay 0x4efed8-0x4efedd (`storage -= edi`, edi is the SWEEP-ENTRY
  INDEX per M49a, the price per M53k — the standing CONFLICT, so BOTH pay sites are armed
  and the run reports which one fires).  create 0x5ab650 @ 0x4eff4e.  The pop call in the
  completion path is at 0x4f0f46 (NAMED "THE POP"); the visit marker is the record-pointer
  store 0x4f5a93 (`mov [ds:0x8f0d60], ecx`).

THE ACCEPTANCE (these rules, written before the run; PASS on ONE real invocation):
  1 shape     at arm: pending >= 2, slots 1..pending distinct and > 0, storage >= head price,
              and the two candidate models predict DIFFERENT read-backs (else no claim);
  2 window    >= 1 POPIN for the armed base, >= 1 POPCNT, and the round counter advanced;
  3 walk      K = the POPCNT count, and the walk ended for a logged reason (pending hit 0 or
              a POPRES with r != 0 followed by POPEXIT);
  4 pending   read-back pending == pending_before - K;
  5 region    read-back slots == shift_predict(before, pending_before, K) — this is the
              "write then read back" gate: an unlogged rewrite of the region fails it;
  6 counts    every consumed non-negative head's queued-count byte dropped by exactly 1,
              every unconsumed queued id's byte unchanged (read back from memory);
  7 attribution every logged cursor write maps to the M70 cursor-store table, and every
              logged slot write maps to the enqueue store 0x417e04 or the pop shift store
              0x4ef62c — an unmapped writer pc FAILS rather than being waved through;
  8 stability the armed record address is still the same base BY NAME after the run
              (the base array compacts mid-run; a moved base means the watchpoints watched
              someone else's queue).

Usage:
    python3 scripts/m71_pop_watch.py [--base-name "University Base"] [--boundaries 2]
                                     [--poke-minerals N] [--timeout 240] [--tag m71pop]
Prints PASS or FAIL plus the ordered pop stream and the read-backs.
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
import m70_cursor_watch as W70    # noqa: E402  (the cursor-store table)

BASE_ARR, BASE_SZ = 0x95DA10, 304
CURSOR_ABS = 0x6A9480 + 0x3FF5C            # 0x6e93dc, the queue widget's cursor field
TABLE_DE, ROW_BYTES = 0x94DE84, 8380       # queued-count bytes: TABLE_DE + 8380*owner + id
POP, POPIN, POPDEC, POPAFT, POPCNT = 0x4EF5D0, 0x4EF5E4, 0x4EF61A, 0x4EF61C, 0x4EF642
POPRES, POPEXIT = 0x4EF65D, 0x4EF68B
PAYA, PAYB, CREATE, VISIT = 0x4EFED8, 0x4F0CA1, 0x4EFF4E, 0x4F5A93
QUEUE_STORES = {0x417E04: "enqueue INSERT store queue[cursor] = item (0x417e04)",
                0x4EF62C: "pop shift store queue[k] = queue[k+1] (0x4ef62c)"}
STORE_WINDOW = 16
EVID = os.path.join(ROOT, "evidence")


# ---------------------------------------------------------------- the model
def shift_predict(before, pending, K):
    """Apply the pop's K shifts (iteration j shifts only 0..pending_j-1) to the region."""
    out = list(before)
    for k in range(len(before)):
        if k <= pending - K:
            out[k] = before[k + K]
        elif k <= pending - 1:
            out[k] = before[pending]
    return out


def attribute_queue_store(pc):
    """gdb reports the pc AFTER the store that dirtied a watchpoint; map it back."""
    cands = [s for s in QUEUE_STORES if s <= pc <= s + STORE_WINDOW]
    if not cands:
        return pc, False
    return max(cands), True


# ---------------------------------------------------------------- memory
def game_pid():
    return M.find_pid()


def base_row(m, name):
    for i in range(max(0, min(B.rd32(m, 0x985AF4), 64))):
        b = B.prod_fields(m, i)
        if b["name"] == name:
            rec = M.rd(m, BASE_ARR + i * BASE_SZ, BASE_SZ)
            slots = [struct.unpack("<i", rec[0x50 + 4 * k:0x54 + 4 * k])[0] for k in range(12)]
            b["slots"] = slots
            b["addr"] = BASE_ARR + i * BASE_SZ
            tl = M.timeline_row(m)
            b["year"], b["round"], b["cur_player"] = tl["year"], tl["round"], tl["cur_player"]
            b["cursor"] = B.rd32(m, CURSOR_ABS)
            b["n_units"] = B.rd32(m, 0x985AF0)
            b["counts"] = {}
            for q in slots[:max(b["pending"], 0) + 1]:
                if q >= 0:
                    m.seek(TABLE_DE + ROW_BYTES * b["fac"] + q)
                    b["counts"][q] = m.read(1)[0]
            return b
    raise SystemExit(f"base {name!r} not found in the base array")


def state(m, tag, name):
    b = base_row(m, name)
    b["tag"] = tag
    return b


# ---------------------------------------------------------------- gdb
TMPL = r"""set pagination off
set confirm off
set height 0
set verbose off
set can-use-hw-watchpoints 1
set $b = @@ADDR@@
watch *(int *)0x@@CURSOR@@
commands
silent
printf "CURSORWRITE pc=0x%x now=%d\n", $pc, *(int *)0x@@CURSOR@@
continue
end
watch *(int *)($b + 0x54)
commands
silent
printf "SLOT1WRITE pc=0x%x now=%d\n", $pc, *(int *)($b + 0x54)
continue
end
watch *(int *)($b + 0x58)
commands
silent
printf "SLOT2WRITE pc=0x%x now=%d\n", $pc, *(int *)($b + 0x58)
continue
end
watch *(int *)($b + 0x5c)
commands
silent
printf "SLOT3WRITE pc=0x%x now=%d\n", $pc, *(int *)($b + 0x5c)
continue
end
break *0x4f5a93 if $ecx == $b
commands
silent
printf "VISIT idx=%d pend=%d s0=%d s1=%d s2=%d s3=%d min=%d\n", $ebx, *(int *)($b + 0x4c), *(int *)($b + 0x50), *(int *)($b + 0x54), *(int *)($b + 0x58), *(int *)($b + 0x5c), *(int *)($b + 0x40)
continue
end
break *0x4ef5e4 if $ebx*0x130+0x95da10 == $b
commands
silent
printf "POPIN idx=%d pend=%d own=%d s0=%d s1=%d s2=%d s3=%d min=%d\n", $ebx, *(int *)($esi+0x95da5c), *(int *)($esi+0x95da14), *(int *)($esi+0x95da60), *(int *)($esi+0x95da64), *(int *)($esi+0x95da68), *(int *)($esi+0x95da6c), *(int *)($esi+0x95da50)
continue
end
break *0x4ef61a if $esi+0x95da10 == $b
commands
silent
printf "POPDEC count=0x%x byte=%d head=%d pend=%d\n", $ecx, *(unsigned char *)$ecx, *(int *)($esi+0x95da60), *(int *)($esi+0x95da5c)
continue
end
break *0x4ef61c if $esi+0x95da10 == $b && (int)*(int *)($esi+0x95da60) >= 0
commands
silent
printf "POPAFT count=0x%x byte=%d head=%d\n", $ecx, *(unsigned char *)$ecx, *(int *)($esi+0x95da60)
continue
end
break *0x4ef642 if $esi+0x95da10 == $b
commands
silent
printf "POPCNT newpend=%d s0=%d s1=%d s2=%d s3=%d\n", $edx, *(int *)($esi+0x95da60), *(int *)($esi+0x95da64), *(int *)($esi+0x95da68), *(int *)($esi+0x95da6c)
continue
end
break *0x4ef65d if $esi+0x95da10 == $b
commands
silent
printf "POPRES head=%d r=%d pend=%d\n", *(int *)($esi+0x95da60), $eax, *(int *)($esi+0x95da5c)
continue
end
break *0x4ef68b if $esi+0x95da10 == $b
commands
silent
printf "POPEXIT head=%d pend=%d\n", *(int *)($esi+0x95da60), *(int *)($esi+0x95da5c)
continue
end
break *0x4efed8 if $ecx == $b
commands
silent
printf "PAYA base=0x%x storage=%d edi=%d\n", $ecx, *(int *)($ecx + 0x40), $edi
continue
end
break *0x4f0ca1 if $edx == $b
commands
silent
printf "PAYB base=0x%x storage=%d edi=%d\n", $edx, *(int *)($edx + 0x40), $edi
continue
end
break *0x4eff4e if *(int *)0x8f0d60 == $b
commands
silent
printf "CREATE id=%d arg3=%d storage=%d\n", $ebx, *(int *)($ebp-0x28), *(int *)($b + 0x40)
continue
end
printf "ARMED base=0x%x cursor=%d pending=%d s0=%d s1=%d s2=%d s3=%d\n", $b, *(int *)0x@@CURSOR@@, *(int *)($b + 0x4c), *(int *)($b + 0x50), *(int *)($b + 0x54), *(int *)($b + 0x58), *(int *)($b + 0x5c)
continue
"""


def gdb_script(addr):
    return TMPL.replace("@@ADDR@@", hex(addr)).replace("@@CURSOR@@", "%x" % CURSOR_ABS)


# ---------------------------------------------------------------- the log
LINE = re.compile(r"^(VISIT|POPIN|POPDEC|POPAFT|POPCNT|POPRES|POPEXIT|PAYA|PAYB|CREATE|"
                  r"CURSORWRITE|SLOT([123])WRITE|ARMED)\s*(.*)$")
KV = re.compile(r"(\w+)=(-?0x[0-9a-f]+|-?\d+)")


def parse(text):
    """Pure: gdb log text -> ordered event rows (slot/cursor writes carry their pc mapped)."""
    ev = []
    for raw in text.splitlines():
        s = raw.strip()
        m = LINE.match(s)
        if not m:
            continue
        tag = m.group(1)
        d = dict(tag=tag)
        for k, v in KV.findall(m.group(3) or ""):
            d[k] = int(v, 16) if v.lower().startswith("0x") else int(v)
        if tag.startswith("SLOT"):
            d["slot"] = int(m.group(2))
            d["store_pc"], d["mapped"] = attribute_queue_store(d["pc"])
            d["store_name"] = QUEUE_STORES.get(d["store_pc"], "UNMAPPED") if d["mapped"] else "UNMAPPED"
        if tag == "CURSORWRITE":
            d["store_pc"], d["mapped"] = W70.attribute_store(d["pc"])
            d["store_name"] = W70.WRITERS.get(d["store_pc"], "UNMAPPED cursor store") if d["mapped"] else "UNMAPPED"
        ev.append(d)
    return ev


# ---------------------------------------------------------------- acceptance
def score(before, after, ev, armed_addr):
    """Pure acceptance.  Returns (ok, gate_lines, findings)."""
    gates, find = [], []
    pb, sb = before["pending"], before["slots"]
    pa, sa = after["pending"], after["slots"]
    K = sum(1 for e in ev if e["tag"] == "POPCNT")
    pops = [e for e in ev if e["tag"] == "POPIN"]

    # 1 shape (re-check what the arm promised)
    ok_shape = pb >= 2 and all(sb[k] > 0 for k in range(1, pb + 1)) \
        and len(set(sb[1:pb + 1])) == pb
    gates.append(("1 shape pending>=2 + distinct live ids", ok_shape,
                  f"pending {pb} slots {sb[:pb+2]}"))
    cand = {1: shift_predict(sb, pb, 1), pb: shift_predict(sb, pb, pb)}
    discrim = cand[1] != cand[pb]
    gates.append(("1 shape SINGLE vs DRAIN differ", discrim,
                  f"K=1 -> {cand[1]}  K={pb} -> {cand[pb]}"))

    # 2 window
    tl_moved = after["round"] > before["round"] or after["year"] > before["year"]
    gates.append(("2 window >=1 POPIN for the armed base", len(pops) >= 1, f"{len(pops)} POPIN"))
    gates.append(("2 window >=1 POPCNT", K >= 1, f"{K} POPCNT"))
    gates.append(("2 window round boundary crossed", tl_moved,
                  f"round {before['round']} -> {after['round']}"))

    # 3 the walk ended for a logged reason
    last_popcnt = max((i for i, e in enumerate(ev) if e["tag"] == "POPCNT"), default=-1)
    tail = ev[last_popcnt + 1:]
    refused = any(e["tag"] == "POPRES" and e["r"] != 0 for e in tail) and \
        any(e["tag"] == "POPEXIT" for e in tail)
    drained = pb - K == 0
    gates.append(("3 walk ended for a logged reason", K == 0 or refused or drained,
                  f"K={K} pending_after={pb - K} refused={refused}"))

    # 4 pending read-back
    gates.append(("4 pending == pending_before - K", pa == pb - K,
                  f"read back {pa}, predicted {pb - K}"))

    # 5 region read-back
    pred = shift_predict(sb, pb, K)
    gates.append(("5 region == shift_predict(before, pending, K)", sa == pred,
                  f"read back {sa}\n            predicted {pred}"))

    # 6 queued-count bytes
    consumed = [sb[j] for j in range(K)]
    bad = []
    for q in sorted(set(consumed + [sb[j] for j in range(K, max(pb, 0) + 1)])):
        b0, b1 = before["counts"].get(q), after["counts"].get(q)
        want = b0 - (consumed.count(q) if q >= 0 else 0)
        if b0 is None or b1 is None:
            continue
        if b1 != want:
            bad.append(f"id {q}: {b0}->{b1} want {want}")
    gates.append(("6 queued-count bytes move by exactly the consumed heads", not bad,
                  "; ".join(bad) or f"consumed {consumed} counts {before['counts']} -> {after['counts']}"))

    # 7 attribution
    cw = [e for e in ev if e["tag"] == "CURSORWRITE"]
    sw = [e for e in ev if e["tag"].startswith("SLOT")]
    bad_cw = [e for e in cw if not e["mapped"]]
    bad_sw = [e for e in sw if not e["mapped"]]
    gates.append(("7 every cursor write maps to a known cursor store", not bad_cw,
                  f"{len(cw)} cursor writes: " + ", ".join(
                      f"0x{e['store_pc']:x}={e['store_name']}" for e in cw) or "none"))
    gates.append(("7 every queue-slot write maps to the enqueue or the pop shift", not bad_sw,
                  f"{len(sw)} slot writes: " + ", ".join(
                      f"slot{e['slot']}@0x{e['store_pc']:x}={e['store_name']}" for e in sw) or "none"))

    # 8 the armed record is still the same base
    gates.append(("8 armed record is still the same base by name",
                  after["addr"] == armed_addr,
                  f"armed 0x{armed_addr:x} now 0x{after['addr']:x} ({after['name']!r})"))

    find.append(f"K (pop iterations) = {K}; SINGLE predicted {cand[1]}, "
                f"DRAIN predicted {cand[pb]}; the read-back matches "
                f"{'SINGLE' if sa == cand[1] and pb - K == pb - 1 else ('DRAIN' if sa == cand[pb] and pa == 0 else 'NEITHER')}")
    find.append("pays seen: " + (", ".join(
        f"{e['tag']} storage {e['storage']} edi {e['edi']}" for e in ev if e["tag"] in ("PAYA", "PAYB")) or "none"))
    find.append("creates seen: " + (", ".join(
        f"id {e['id']} arg3 {e['arg3']}" for e in ev if e["tag"] == "CREATE") or "none"))
    find.append("validator verdicts: " + (", ".join(
        f"head {e['head']} r {e['r']}" for e in ev if e["tag"] == "POPRES") or "none"))
    find.append(f"units before/after: {before['n_units']} -> {after['n_units']}")
    find.append("VISIT rows: " + ", ".join(
        f"pend {e['pend']} s {e['s0']},{e['s1']},{e['s2']},{e['s3']} min {e['min']}"
        for e in ev if e["tag"] == "VISIT"))
    ok = all(g[1] for g in gates)
    return ok, gates, find


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-name", default="University Base")
    ap.add_argument("--boundaries", type=int, default=2)
    ap.add_argument("--poke-minerals", type=int, default=None)
    ap.add_argument("--timeout", type=float, default=300.0)
    ap.add_argument("--tag", default="m71pop")
    a = ap.parse_args()

    if subprocess.run(["pgrep", "-x", "gdb"], capture_output=True, text=True).stdout.strip():
        raise SystemExit("a gdb is already running — scripts/m70_cursor_watch.py --stop first")
    pid = game_pid()
    tracer = subprocess.run(["grep", "-m1", "TracerPid", "/proc/%d/status" % pid],
                            capture_output=True, text=True).stdout.split()[-1]
    if tracer != "0":
        raise SystemExit("TracerPid=%s != 0" % tracer)
    if subprocess.run(["sysctl", "-n", "kernel.yama.ptrace_scope"],
                      capture_output=True, text=True).stdout.strip() != "0":
        raise SystemExit("ptrace_scope != 0")

    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        before = state(m, "before", a.base_name)
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        price = B.price_of(m, before["fac"], before["slots"][0])["price"]

    # PREP: the completion gate needs storage >= the head's price; poke, then READ BACK,
    # always BEFORE attaching (pokes lie under a tracer).
    poke = a.poke_minerals if a.poke_minerals is not None else (
        max(price, before["minerals"]) if before["minerals"] < price else None)
    poked = None
    if poke is not None and poke != before["minerals"]:
        with open(f"/proc/{pid}/mem", "rb+", 0) as m:
            m.seek(before["addr"] + 0x40)
            m.write(struct.pack("<i", poke))
            m.seek(before["addr"] + 0x40)
            poked = struct.unpack("<i", m.read(4))[0]
        with open(f"/proc/{pid}/mem", "rb", 0) as m:
            before = state(m, "before", a.base_name)

    pb, sb = before["pending"], before["slots"]
    if pb < 2 or not all(sb[k] > 0 for k in range(1, pb + 1)) or len(set(sb[1:pb + 1])) != pb:
        raise SystemExit(f"shape gate: pending {pb} slots {sb[:pb+2]} — need pending>=2 with "
                         f"distinct live ids in slots 1..pending")
    if shift_predict(sb, pb, 1) == shift_predict(sb, pb, pb):
        raise SystemExit("shape gate: SINGLE and DRAIN predict the same read-back — no claim")
    if before["minerals"] < price:
        raise SystemExit(f"shape gate: minerals {before['minerals']} < head price {price}")

    gpath = os.path.join(ROOT, "scratch", f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.gdblog")
    os.makedirs(os.path.dirname(gpath), exist_ok=True)
    open(gpath, "w").write(gdb_script(before["addr"]))
    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=log, stderr=subprocess.STDOUT)
    time.sleep(3.0)
    head = open(lpath, "r", errors="replace").read()
    if "ARMED" not in head:
        os.kill(g.pid, signal.SIGINT)
        time.sleep(1.0)
        raise SystemExit("gdb did not arm:\n" + head[-1500:])
    print(f"armed: base {a.base_name!r} idx {before['i']} addr 0x{before['addr']:x} "
          f"pending {pb} slots {sb[:4]} minerals {before['minerals']} "
          f"(poke {before['minerals'] if poked is None else f'{poked} (read back)'} "
          f"vs head price {price}); cursor field 0x{CURSOR_ABS:x} = {before['cursor']}; "
          f"round {before['round']} year {before['year']}", flush=True)

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
        after = state(m, "after", a.base_name)
    text = open(lpath, "r", errors="replace").read()
    ev = parse(text)
    with open(os.path.join(EVID, f"{a.tag}_seq.jsonl"), "w") as fh:
        for d in ev:
            fh.write(json.dumps(d) + "\n")

    print("--- ordered stream (armed base only) ---")
    for e in ev:
        if e["tag"] in ("CURSORWRITE", "SLOT1WRITE", "SLOT2WRITE", "SLOT3WRITE"):
            print(f"  {e['tag']:11s} pc=0x{e['pc']:x} -> store 0x{e['store_pc']:x} "
                  f"{e['store_name']} now={e.get('now')}")
        else:
            print("  " + " ".join(f"{k}={v}" for k, v in e.items()))
    print(f"read back: pending {pb} -> {after['pending']}  slots {sb[:6]} -> "
          f"{after['slots'][:6]}  cursor {before['cursor']} -> {after['cursor']}  "
          f"minerals {before['minerals']} -> {after['minerals']}  "
          f"round {before['round']} -> {after['round']}")
    ok, gates, find = score(before, after, ev, before["addr"])
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
