#!/usr/bin/env python3
"""M72 — WHICH TEST SENDS THE VISIT HOME WITHOUT PAYING.

M71 measured the pop twice and named the pay that fires for a UI-queued base-type head
(`0x4efedd`, edi = the head's price).  Its designed-head run (`m71pop2`: head 193, minerals
poked to the head price 18 and READ BACK) produced one VISIT and NO pay/pop/create.  That
run armed only the pop sites and the two pay sites, so it could not say WHERE the visit
turned around.  This instrument arms the visitor's own decision points and names the test.

THE STATIC MODEL (scratch/m574/text.txt instruction bytes, cited by address).  The visitor is
FUN_004ef6d0 (0x4ef6d0..0x4f26da); [0x8f0d60] is the record pointer of the base being
visited:

  0x4ef6d0  ENTRY
  0x4ef88b  ecx = [base+0x50]  THE QUEUE HEAD;  == -38 -> 0x4ef9b3, < 0 -> facility path
            (0x4ef8a1: [ebp-0x30] = -head), >= 0 -> 0x4efa2c  (the unit path, head 193)
  0x4efa3c  call 0x4e40a0 -> eax;  0x4efa4d call 0x5ac950 -> eax;  0x4efa52 edi *= eax
  0x4efa5e  POSAFF  cmp [base+0x40], edi        storage vs the price it computed
  0x4efa63  BAILAFF (storage < edi)  -> message 0x67164c/0x671644 -> epilogue 0x4f0bfa
  0x4efadc  AFFPASS -> the special "type +0x2a == 8" test;  otherwise
  0x4efe41  CMP40   cmp ebx,0x40                 designed ids from base-type ids
  0x4efed8  PAYA    mov [base+0x40], esi         esi = storage - edi
  0x4eff4e  CREATE  call 0x5ab650
  ---- the facility path ----
  0x4ef8fa  NEGAFF  cmp [base+0x40], edi        (edi = count * chassis cost)
  0x4f0a3d  GATE    cmp [base+0x40], edi
  0x4f0a42  BAILMIN (storage < edi)              -> epilogue
  0x4f0b7b  [ebp-0x30] = -head;  > 0 -> 0x4f0ca1 PAYB, else
  0x4f0b86  BAILDESC ([ebp-0x30] <= 0)           -> epilogue
  0x4f0b4f  CMPLOOP ecx = [esi+0xcc]+[esi+0x3c] vs edx = f()*table;  ecx >= edx ->
  0x4f0c28  BAILCNT                              -> epilogue
  0x4f5a93  VISIT   mov [ds:0x8f0d60], ecx       "this base became the current base"

THE ACCEPTANCE (written before the run; PASS on ONE real invocation):
  1 arm        the armed base's head is a POSITIVE id and storage was poked to >= its
               price_of and READ BACK before gdb attached (pokes lie under a tracer);
  2 window     the round counter advanced and >= 1 VISIT fired for the armed base;
  3 visitor    >= 1 ENTRY fired (the visitor actually ran for the armed base);
  4 turn-around ONE KIND of turn-around row fired among {BAILAFF, BAILMIN, BAILDESC, BAILCNT,
               PAYA}: the visitor runs more than once per boundary, so repeats of the same
               test are one answer; two DIFFERENT tests is CONFOUNDED, no row is FAIL;
  5 arithmetic the firing row's OWN logged operands satisfy its condition (BAILAFF and
               BAILMIN: storage < edi; BAILDESC: i30 <= 0; BAILCNT: ecx >= edx at CMPLOOP);
  6 edi        edi is logged at POSAFF/GATE and at the firing row; the run reports whether
               it equals the head's price_of (the M71 edi question);
  7 stability  the armed record is still the same base BY NAME at the same address;
  8 parse      every log line parsed into the known tag set (an unknown line FAILs).
No pay/pop claim is made here: M71 owns that.  This run names the turn-around.

Usage:
    python3 scripts/m72_gate_watch.py [--base-name "University Base"] [--boundaries 2]
                                      [--poke-minerals N] [--timeout 240] [--tag m72gate]
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
TABLE_DE, ROW_BYTES = 0x94DE84, 8380
ENTRY, HEAD, POSAFF, BAILAFF = 0x4EF6D0, 0x4EF88E, 0x4EFA5E, 0x4EFA63
CMP40, PAYA, CREATE, VISIT = 0x4EFE41, 0x4EFED8, 0x4EFF4E, 0x4F5A93
GATE, BAILMIN, BAILDESC, BAILCNT, CMPLOOP = 0x4F0A3D, 0x4F0A42, 0x4F0B86, 0x4F0C28, 0x4F0B4F
# the rows that can account for "the visit turned around without paying"
TURNAROUND = ("BAILAFF", "BAILMIN", "BAILDESC", "BAILCNT", "PAYA")
EVID = os.path.join(ROOT, "evidence")


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
            b["n_units"] = B.rd32(m, 0x985AF0)
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
break *0x4ef6d0 if *(int *)0x8f0d60 == $b
commands
silent
printf "ENTRY base=0x%x storage=%d s0=%d pend=%d\n", $b, *(int *)($b + 0x40), *(int *)($b + 0x50), *(int *)($b + 0x4c)
continue
end
break *0x4ef88e if $eax == $b
commands
silent
printf "HEAD id=%d own=%d storage=%d pend=%d\n", $ecx, *(int *)($b + 4), *(int *)($b + 0x40), *(int *)($b + 0x4c)
continue
end
break *0x4efa5e if *(int *)0x8f0d60 == $b
commands
silent
printf "POSAFF storage=%d edi=%d ebx=%d i1c=0x%x\n", *(int *)($b + 0x40), $edi, $ebx, *(int *)($ebp - 0x1c)
continue
end
break *0x4efa63 if *(int *)0x8f0d60 == $b
commands
silent
printf "BAILAFF storage=%d edi=%d ebx=%d\n", *(int *)($b + 0x40), $edi, $ebx
continue
end
break *0x4efe41 if *(int *)0x8f0d60 == $b
commands
silent
printf "CMP40 ebx=%d edi=%d storage=%d\n", $ebx, $edi, *(int *)($b + 0x40)
continue
end
break *0x4efed8 if $ecx == $b
commands
silent
printf "PAYA storage=%d edi=%d\n", *(int *)($ecx + 0x40), $edi
continue
end
break *0x4eff4e if *(int *)0x8f0d60 == $b
commands
silent
printf "CREATE id=%d arg3=%d storage=%d\n", $ebx, *(int *)($ebp - 0x28), *(int *)($b + 0x40)
continue
end
break *0x4f0a3d if *(int *)0x8f0d60 == $b
commands
silent
printf "GATE storage=%d edi=%d i1c=0x%x i30=%d\n", *(int *)($b + 0x40), $edi, *(int *)($ebp - 0x1c), *(int *)($ebp - 0x30)
continue
end
break *0x4f0a42 if *(int *)0x8f0d60 == $b
commands
silent
printf "BAILMIN storage=%d edi=%d i30=%d\n", *(int *)($b + 0x40), $edi, *(int *)($ebp - 0x30)
continue
end
break *0x4f0b4f if *(int *)0x8f0d60 == $b
commands
silent
printf "CMPLOOP ecx=%d edx=%d obase=0x%x pend=%d head=%d\n", $ecx, $edx, $esi, *(int *)($esi + 0x4c), *(int *)($esi + 0x50)
continue
end
break *0x4f0b86 if *(int *)0x8f0d60 == $b
commands
silent
printf "BAILDESC i30=%d i1c=0x%x edi=%d\n", *(int *)($ebp - 0x30), *(int *)($ebp - 0x1c), $edi
continue
end
break *0x4f0c28 if *(int *)0x8f0d60 == $b
commands
silent
printf "BAILCNT ecx=%d edx=%d i30=%d\n", $ecx, $edx, *(int *)($ebp - 0x30)
continue
end
break *0x4f5a93 if $ecx == $b
commands
silent
printf "VISIT pend=%d s0=%d s1=%d min=%d\n", *(int *)($b + 0x4c), *(int *)($b + 0x50), *(int *)($b + 0x54), *(int *)($b + 0x40)
continue
end
printf "ARMED base=0x%x head=%d pending=%d storage=%d\n", $b, *(int *)($b + 0x50), *(int *)($b + 0x4c), *(int *)($b + 0x40)
continue
"""


def gdb_script(addr):
    return TMPL.replace("@@ADDR@@", hex(addr))


LINE = re.compile(r"^(ENTRY|HEAD|POSAFF|BAILAFF|CMP40|PAYA|CREATE|GATE|BAILMIN|CMPLOOP|"
                  r"BAILDESC|BAILCNT|VISIT|ARMED)\s*(.*)$")
KV = re.compile(r"(\w+)=(-?0x[0-9a-f]+|-?\d+)")


def parse(text):
    """Pure: gdb log text -> ordered event rows.  Returns (events, unparsed_lines)."""
    ev, bad = [], []
    for raw in text.splitlines():
        s = raw.strip()
        if not s:
            continue
        m = LINE.match(s)
        if not m:
            if s.startswith(("warning:", "Reading symbols", "0x", "Breakpoint", "[", "The program",
                             "This GDB", "Enable debuginfod", "<https://debuginfod",
                             "Debuginfod has been disabled", "To make this setting",
                             "Thread ", "received signal SIGINT")):
                continue          # gdb's own chatter, not a row
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
def score(before, after, ev, price, bad_lines=()):
    """Pure acceptance.  Returns (ok, gates, findings)."""
    gates, find = [], []
    tag_rows = [e for e in ev if e["tag"] != "ARMED"]

    gates.append(("8 parse every log line into a known tag", not bad_lines,
                  f"{len(bad_lines)} unknown lines" + (": " + " | ".join(bad_lines[:3]) if bad_lines else "")))
    gates.append(("1 arm head is a positive id with storage >= its price read back",
                  before["slots"][0] > 0 and before["minerals"] >= price,
                  f"head {before['slots'][0]} storage {before['minerals']} price {price}"))
    visits = [e for e in tag_rows if e["tag"] == "VISIT"]
    gates.append(("2 window round advanced and >= 1 VISIT for the armed base",
                  after["round"] > before["round"] and len(visits) >= 1,
                  f"round {before['round']} -> {after['round']}, {len(visits)} VISIT"))
    entries = [e for e in tag_rows if e["tag"] == "ENTRY"]
    gates.append(("3 visitor ran for the armed base (>= 1 ENTRY)", len(entries) >= 1,
                  f"{len(entries)} ENTRY"))

    turn = [e for e in tag_rows if e["tag"] in TURNAROUND]
    kinds = sorted({e["tag"] for e in turn})
    # A REPEATED visit is normal (the visitor is called more than once per boundary); the
    # claim is about WHICH test, so repeats of one test are one answer, two tests is none.
    gates.append(("4 one turn-around KIND fired (CONFOUNDED if two differ)", len(kinds) == 1,
                  f"{len(turn)} turn-around rows of {kinds or 'none'}: " + (
                      ", ".join(e["tag"] for e in turn) or "none")))

    ok_arith, why = False, "no turn-around row"
    if len(kinds) == 1:
        bad = []
        for e in turn:
            if e["tag"] in ("BAILAFF", "BAILMIN"):
                good = e["storage"] < e["edi"]
                why = f"{e['tag']} storage {e['storage']} < edi {e['edi']}"
            elif e["tag"] == "BAILDESC":
                good = e.get("i30", 1) <= 0
                why = f"BAILDESC i30 {e.get('i30')} <= 0"
            elif e["tag"] == "BAILCNT":
                good = any(c["tag"] == "CMPLOOP" and c["ecx"] >= c["edx"] for c in tag_rows)
                why = f"BAILCNT needs a CMPLOOP row with ecx >= edx"
            else:                        # PAYA: the visit PAID — for m71pop2's shape, a paradox
                good = True
                why = f"PAYA fired (storage {e['storage']} edi {e['edi']}) — the visit paid"
            if not good:
                bad.append(f"{e['tag']} {e.get('storage')}/{e.get('edi')}")
        ok_arith = not bad
        why = f"{why} -> {ok_arith}" + (f"  bad: {', '.join(bad)}" if bad else "")
    gates.append(("5 every turn-around row's operands satisfy its condition", ok_arith, why))

    edis = [(e["tag"], e["edi"]) for e in tag_rows if "edi" in e]
    gates.append(("6 edi logged at the affordability sites", len(edis) >= 1,
                  "; ".join(f"{t}={v} (price {price})" for t, v in edis) or "no edi row"))

    gates.append(("7 armed record is still the same base by name",
                  after["addr"] == before["addr"] and after["name"] == before["name"],
                  f"armed 0x{before['addr']:x} now 0x{after['addr']:x} ({after['name']!r})"))

    named = kinds[0] if len(kinds) == 1 else ("CONFOUNDED " + str(kinds) if turn else "NOTHING")
    find.append(f"turn-around named: {named}")
    find.append("VISIT rows: " + (", ".join(
        f"pend {e.get('pend')} head {e.get('s0')} min {e.get('min')}" for e in visits) or "none"))
    find.append("ENTRY rows: " + (", ".join(
        f"head {e.get('s0')} pend {e.get('pend')} storage {e.get('storage')}" for e in entries) or "none"))
    find.append("edi rows: " + (", ".join(f"{t}={v}" for t, v in edis) or "none") + f"; head price {price}")
    find.append("ordered stream: " + " -> ".join(
        e["tag"] for e in tag_rows if e["tag"] != "VISIT") if tag_rows else "empty")
    ok = all(g[1] for g in gates)
    return ok, gates, find


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-name", default="University Base")
    ap.add_argument("--boundaries", type=int, default=2)
    ap.add_argument("--poke-minerals", type=int, default=None)
    ap.add_argument("--timeout", type=float, default=300.0)
    ap.add_argument("--tag", default="m72gate")
    a = ap.parse_args()

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
        before = state(m, "before", a.base_name)
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        price = B.price_of(m, before["fac"], before["slots"][0])["price"]
    if before["slots"][0] <= 0:
        raise SystemExit(f"arm gate: head {before['slots'][0]} is not a positive id — "
                         f"enqueue a designed/base-type id first")

    poke = a.poke_minerals if a.poke_minerals is not None else max(price, before["minerals"])
    poked = None
    if poke != before["minerals"]:
        with open(f"/proc/{pid}/mem", "rb+", 0) as m:
            m.seek(before["addr"] + 0x40)
            m.write(struct.pack("<i", poke))
            m.seek(before["addr"] + 0x40)
            poked = struct.unpack("<i", m.read(4))[0]
        with open(f"/proc/{pid}/mem", "rb", 0) as m:
            before = state(m, "before", a.base_name)
    if before["minerals"] < price:
        raise SystemExit(f"arm gate: storage {before['minerals']} < head price {price} after the poke")

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
    print(f"armed: base {a.base_name!r} addr 0x{before['addr']:x} head {before['slots'][0]} "
          f"pending {before['pending']} storage {before['minerals']} "
          f"({'read back' if poked else 'already'} vs head price {price}); "
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
        after = state(m, "after", a.base_name)
    text = open(lpath, "r", errors="replace").read()
    ev, bad = parse(text)
    with open(os.path.join(EVID, f"{a.tag}_seq.jsonl"), "w") as fh:
        for d in ev:
            fh.write(json.dumps(d) + "\n")

    print("--- ordered stream (armed base only) ---")
    for e in ev:
        print("  " + " ".join(f"{k}={v}" for k, v in e.items()))
    print(f"read back: head {before['slots'][0]} -> {after['slots'][0]}  pending "
          f"{before['pending']} -> {after['pending']}  storage {before['minerals']} -> "
          f"{after['minerals']}  round {before['round']} -> {after['round']}")
    ok, gates, find = score(before, after, ev, price, bad)
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
