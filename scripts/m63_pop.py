#!/usr/bin/env python3
"""M63 — the queue pop FUN_004ef5d0, instrumented instruction by instruction.

Static (scratch/m574/text.txt, 0x4ef5d0..0x4ef6c3; record = 0x95da10 + idx*0x130,
so the operands `esi+0x95da5c/60/14` are record+0x4c / +0x50 / +0x04):

  4ef5da  lea esi,[304*idx]                       ; esi = idx*0x130 (no array base yet)
  4ef5e4  mov eax,[esi+0x95da5c]                  ; eax = pending   (record+0x4c)
  4ef5ea  mov cl,[esi+0x95da14]  -> edi           ; edi = OWNER byte (record+0x04)
  4ef5f4  je  0x4ef684                            ; pending == 0 -> return 0, NO shift
  4ef5fa  mov ecx,[esi+0x95da60]                  ; ecx = HEAD slot value (record+0x50)
  4ef600  test ecx,ecx / jl 0x4ef61c              ; negative head skips the count dec
  4ef604  edx = ((65*edi*2 + edi) << 4) - edi = 2095*edi
  4ef613  lea ecx,[ecx+edx*4+0x94de84]            ; 0x94de84 + 8380*owner + head
  4ef61a  dec BYTE PTR [ecx]                      ; per-faction queued-count byte
  4ef622  shift: [0x50+4k] = [0x54+4k] for k = 0..pending-1   (pending MOVES, 0x4ef62c)
  4ef642  mov [esi+0x95da5c],edx                  ; pending--
  4ef648  eax = [esi+0x95da60]                    ; the NEW head (what was slot[1])
  4ef655  call 0x5a73f0(eax, owner, idx)          ; >=0: type-record VALIDATOR
  4ef66a  call 0x5a6e70(-eax, owner, idx, 0)      ; <0 : the negative-code validator
  4ef676  jne 0x4ef5fa while pending != 0         ; it walks the whole queue
  4ef69e  call 0x473760(x, y, 2, 2)               ; refresh the base tile, return 0

0x5a73f0 (0x5a73f0..0x5a7411) reads type record[type*0x34 + 0x38] bit 0 and
record+0x34 bit `owner`, and returns 0 — it is a PREDICATE, not a builder, so the
pop ADVANCES and VALIDATES; the build is the visit's own pay 0x4efedd + create
0x5ab650 @ 0x4eff4e (M59/M60/M61).

Sites armed (all silent + printf + continue, gdb stdout straight to a file):
  0x4ef6d0 VISIT   which base the visit is on (ds:0x8f0d60)
  0x4ef5d0 POPIN   the pop's OWN argument: idx, its record, name, owner, pending, slots
  0x4ef61a POPDEC  the count-table address the game itself computed, byte BEFORE
  0x4ef61c POPAFT  the same byte AFTER the dec (read-back, not inference)
  0x4ef62c POPSHIFT which slot index is written, the value, and the old value
  0x4ef642 POPCNT  the new pending + the slots after the shift
  0x4ef655/0x4ef66a POPVAL the item handed to the validator (>=0 / <0 branch)
  0x4ef65d POPRES the validator's return value
  0x4efedd PAY, 0x4eff4e CREATE (M60/M61 sites, for the order)
hw watchpoints (3 of 4): the named base's head slot +0x50, year 0x985b00,
cur_player 0x985dcc.

ONE variable: the named base's queue.  The other named base is the control.
Poke (minerals) and read back BEFORE attaching — pokes lie under a tracer.

    python3 scripts/m63_pop.py [--base "Korolev Center"] [--boundaries 2]
                               [--timeout 240] [--tag m63pop]
"""
import argparse, json, os, re, signal, struct, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m55_boundary as M
import m56_build as B
import m60_guard as G60

VISIT = 0x4ef6d0
POP, POPDEC, POPAFT, POPSHIFT, POPCNT = 0x4ef5d0, 0x4ef61a, 0x4ef61c, 0x4ef62c, 0x4ef642
POPVAL, POPVALN, POPRES = 0x4ef655, 0x4ef66a, 0x4ef65d
PAY, CREATE = 0x4efedd, 0x4eff4e
GUARD, YEAR_G, ROUND_G, CURP_G = 0x8f0d70, 0x985b00, 0x985afc, 0x985dcc
TABLE_DE, TABLE_DC, ROW_BYTES = 0x94de84, 0x94dc84, 8380   # 0x20bc bytes per faction
BASE_ARR, BASE_SZ = 0x95DA10, 304
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "evidence")


def find_pid():
    pid = os.environ.get("SMAC_PID")
    return int(pid) if pid else M.find_pid()


def rec_addr(m, want):
    n = max(0, min(B.rd32(m, M.G["n_bases"][0]), 64))
    for i in range(n):
        b = B.prod_fields(m, i)
        if b["name"] == want:
            return b["i"], BASE_ARR + i * BASE_SZ, b
    raise SystemExit(f"base {want!r} not among {n} bases")


def state(m, tag):
    tl = M.timeline_row(m)
    out = dict(tag=tag, year=tl["year"], round=tl["round"], cur_player=tl["cur_player"],
               guard=B.rd32(m, GUARD), bases=[])
    for want in NAMES:
        try:
            i, a, b = rec_addr(m, want)
        except SystemExit:
            out["bases"].append(dict(name=want, gone=True))
            continue
        rec = M.rd(m, a, BASE_SZ)
        q = [struct.unpack("<i", rec[0x50 + 4 * k:0x54 + 4 * k])[0] for k in range(6)]
        out["bases"].append(dict(
            name=want, i=i, addr=a, x=b["x"], y=b["y"], fac=b["fac"],
            minerals=b["minerals"], income=b["income"],
            pending=struct.unpack("<i", rec[0x4c:0x50])[0], queue=q,
            credit_d0=struct.unpack("<i", rec[0xd0:0xd4])[0],
            table_de=byte_at(m, TABLE_DE + ROW_BYTES * b["fac"] + q[0]),
            table_dc=byte_at(m, TABLE_DC + ROW_BYTES * b["fac"] + q[0])))
    out["n_ours"] = len(G60.our_units(m))
    return out


def byte_at(m, a):
    """Read one byte, or None if the address is not mapped (a garbage head can
    point the per-faction count table outside the image)."""
    try:
        m.seek(a)
        return m.read(1)[0]
    except OSError:
        return None


NL = chr(92) * 2 + "n"     # gdb must see TWO backslashes + n to emit a newline
NAMES = ["Korolev Center", "University Base"]


def gdb_script(taddr, tname):
    """One command list per site: silent + a tagged printf + continue."""
    R = f"(0x{BASE_ARR:x}+$ebx*0x{BASE_SZ:x})"      # the pop's record, from its arg
    V = "*(int*)0x8f0d60"                            # the visit's base record
    P = ["set pagination off", "set confirm off", "set height 0", "set verbose off"]

    def site(addr, tag, fmt, args, before=True):
        P.append(f"break *{addr:#x}\ncommands\nsilent")
        P.append(f'printf "{tag} {fmt}\\n", {args}')
        P.append("continue\nend")

    P.append(f"watch *(int*){taddr + 0x50:#x}\ncommands\nsilent\n"
             f'printf "HEADW pc=0x%x val=%d pend=%d owner=%d\\n", $pc, '
             f"*(int*){taddr + 0x50:#x}, *(int*){taddr + 0x4c:#x}, "
             f"*(unsigned char*){taddr + 4:#x}\ncontinue\nend")
    P.append(f"watch *(int*){YEAR_G:#x}\ncommands\nsilent\n"
             f'printf "YEARW year=%d round=%d cp=%d\\n", *(int*){YEAR_G:#x}, '
             f"*(int*){ROUND_G:#x}, *(int*){CURP_G:#x}\ncontinue\nend")
    P.append(f"watch *(int*){CURP_G:#x}\ncommands\nsilent\n"
             f'printf "PLAYERW pc=0x%x cp=%d year=%d round=%d\\n", $pc, '
             f"*(int*){CURP_G:#x}, *(int*){YEAR_G:#x}, *(int*){ROUND_G:#x}\ncontinue\nend")
    site(VISIT, "VISIT", "name=%s addr=0x%x owner=%d pend=%d head=%d cp=%d year=%d",
         f"(char*)({V}+19), {V}, *(unsigned char*)({V}+4), *(int*)({V}+0x4c), "
         f"*(int*)({V}+0x50), *(int*){CURP_G:#x}, *(int*){YEAR_G:#x}")
    site(POP, "POPIN", "idx=%d addr=0x%x name=%s owner=%d pend=%d s0=%d s1=%d s2=%d "
         "cp=%d year=%d visit_addr=0x%x",
         f"$ebx, {R}, (char*)({R}+19), *(unsigned char*)({R}+4), *(int*)({R}+0x4c), "
         f"*(int*)({R}+0x50), *(int*)({R}+0x54), *(int*)({R}+0x58), "
         f"*(int*){CURP_G:#x}, *(int*){YEAR_G:#x}, {V}")
    site(POPDEC, "POPDEC", "addr=0x%x byte=%d name=%s owner=%d head=%d",
         f"$ecx, *(unsigned char*)$ecx, (char*)({R}+19), "
         f"*(unsigned char*)({R}+4), *(int*)({R}+0x50)")
    site(POPAFT, "POPAFT", "addr=0x%x byte=%d sibling_dc=0x%x sibling=%d",
         f"$ecx, *(unsigned char*)$ecx, $ecx-0x200, *(unsigned char*)($ecx-0x200)")
    site(POPSHIFT, "POPSHIFT", "slot=%d dest=0x%x val=%d old=%d name=%s pend=%d",
         f"($eax-0x{BASE_ARR:x}-$ebx*0x{BASE_SZ:x})/4, $eax, $edx, *(int*)$eax, "
         f"(char*)({R}+19), *(int*)({R}+0x4c)")
    site(POPCNT, "POPCNT", "name=%s newpend=%d s0=%d s1=%d s2=%d s3=%d",
         f"(char*)({R}+19), $edx, *(int*)({R}+0x50), *(int*)({R}+0x54), "
         f"*(int*)({R}+0x58), *(int*)({R}+0x5c)")
    site(POPVAL, "POPVAL", "item=%d owner=%d idx=%d name=%s",
         f"$eax, $edi, $ebx, (char*)({R}+19)")
    site(POPVALN, "POPVALN", "negitem=%d owner=%d idx=%d name=%s",
         f"$eax, $edi, $ebx, (char*)({R}+19)")
    site(POPRES, "POPRES", "result=%d name=%s head=%d",
         f"$eax, (char*)({R}+19), *(int*)({R}+0x50)")
    site(PAY, "PAY", "name=%s before=%d edi=%d after=%d cp=%d year=%d",
         f"(char*)({V}+19), *(int*)({V}+0x40), $edi, $esi, "
         f"*(int*){CURP_G:#x}, *(int*){YEAR_G:#x}")
    site(CREATE, "CREATE", "name=%s guard=%d owner=%d min=%d cp=%d",
         f"(char*)({V}+19), *(int*){GUARD:#x}, $eax, *(int*)({V}+0x40), "
         f"*(int*){CURP_G:#x}")
    P.append("continue\n")
    return "\n".join(P) + "\n"


TAGS = ("VISIT", "POPIN", "POPDEC", "POPAFT", "POPSHIFT", "POPCNT", "POPVAL",
        "POPVALN", "POPRES", "PAY", "CREATE", "HEADW", "YEARW", "PLAYERW")


def parse(out):
    ev = []
    for ln in out.splitlines():
        ln = ln.strip()
        head = ln.split(" ", 1)
        if not head or head[0] not in TAGS:
            continue
        tag = head[0]
        rest = head[1] if len(head) > 1 else ""
        d = dict(t=tag)
        for k, v in re.findall(r"(\w+)=(-?0x[0-9a-f]+|-?\d+)", rest):
            d[k] = int(v, 16) if v.startswith(("0x", "-0x")) else int(v)
        nm = re.search(r'name=(.*?) (owner|head|pend|newpend|min|result|idx|cp)=', rest)
        if nm:
            d["name"] = nm.group(1)
        ev.append(d)
    return ev


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="Korolev Center")
    ap.add_argument("--boundaries", type=int, default=2)
    ap.add_argument("--timeout", type=float, default=240.0)
    ap.add_argument("--tag", default="m63pop")
    a = ap.parse_args()
    if subprocess.run(["pgrep", "-x", "gdb"], capture_output=True,
                      text=True).stdout.strip():
        raise SystemExit("a gdb is already running — run scripts/m57_credit.py --stop first")
    pid = find_pid()
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        before = state(m, "before")
    idx = taddr = b = None
    for row in before["bases"]:
        if row["name"] == a.base:
            idx, taddr, b = row["i"], row["addr"], row
    if taddr is None:
        raise SystemExit(f"target base {a.base!r} not found before arming")
    gpath = os.path.join(EVID, f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.gdblog")
    open(gpath, "w").write(gdb_script(taddr, a.base))
    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath,
                          "-p", str(pid)], stdout=log, stderr=subprocess.STDOUT)
    print(f"gdb armed pid {g.pid} on {a.base} idx {idx} record 0x{taddr:x} "
          f"(pend {b['pending']} slots {b['queue'][:4]} minerals {b['minerals']}); "
          f"sites pop=0x{POP:x} dec=0x{POPDEC:x} shift=0x{POPSHIFT:x} "
          f"cnt=0x{POPCNT:x} val=0x{POPVAL:x}/{POPVALN:x} pay=0x{PAY:x} "
          f"create=0x{CREATE:x}; hw watch head 0x{taddr + 0x50:x}", flush=True)
    time.sleep(2.0)
    t0, runs = time.time(), []
    for k in range(a.boundaries):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "smac_play.py"),
                            "--turns", "1", "--timeout", str(int(min(a.timeout, 200))),
                            "--no-escape", "3000", "--orders-per-turn", "1",
                            "--verbose", "--tag", f"{a.tag}_r{k}"],
                           capture_output=True, text=True)
        runs.append(r.returncode)
        print(f"  turn {k}: rc={r.returncode} t={time.time() - t0:.0f}s", flush=True)
    try:
        os.kill(g.pid, signal.SIGINT)
    except ProcessLookupError:
        pass
    time.sleep(1.0)
    try:
        g.kill()
    except ProcessLookupError:
        pass
    log.close()
    out = open(lpath, "r", errors="replace").read()
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        after = state(m, "after")
    ev = parse(out)
    jpath = os.path.join(EVID, f"{a.tag}_seq.jsonl")
    with open(jpath, "w") as fh:
        for d in ev:
            fh.write(json.dumps(d) + "\n")
    print("--- ordered pop stream (our bases + round markers) ---")
    for d in ev:
        nm = d.get("name", "*")
        if d["t"] in ("VISIT", "PAY", "CREATE") and nm not in NAMES:
            continue
        if d["t"] == "YEARW":
            print(f"== YEAR FLIP to {d.get('year')} (round {d.get('round')}) cp={d.get('cp')}")
        elif d["t"] == "PLAYERW":
            print(f"   cur_player -> {d.get('cp')} pc=0x{d.get('pc'):x} (year {d.get('year')})")
        else:
            keys = [k for k in ("idx", "addr", "name", "owner", "pend", "newpend", "s0",
                                "s1", "s2", "s3", "slot", "dest", "val", "old", "item",
                                "negitem", "result", "head", "byte", "sibling",
                                "before", "edi", "after", "min", "cp", "year", "guard",
                                "visit_addr") if k in d]
            print(d["t"] + " " + " ".join(f"{k}=" +
                    (f"0x{d[k]:x}" if k in ("addr", "sibling", "dest", "pc", "visit_addr")
                     else str(d[k])) for k in keys))
    counts = dict((t, sum(1 for d in ev if d["t"] == t)) for t in TAGS)
    popins = [d for d in ev if d["t"] == "POPIN"]
    print(json.dumps(dict(gdb_pid=g.pid, rc=g.poll(), boundaries=a.boundaries,
                          turn_rcs=runs, counts=counts,
                          popin_by_name=dict((n, sum(1 for d in popins if d.get("name") == n))
                                             for n in NAMES),
                          popin_with_pending=sum(1 for d in popins if d.get("pend", 0) != 0),
                          shifts_by_name=dict(
                              (n, sum(1 for d in ev if d["t"] == "POPSHIFT"
                                     and d.get("name") == n)) for n in NAMES),
                          seq=jpath, gdb_log=lpath), indent=1))
    print("--- state before / after (read back from memory, not from gdb) ---")
    for side in (before, after):
        for row in side["bases"]:
            if row.get("gone"):
                print(side["tag"], row["name"], "GONE")
                continue
            print(side["tag"], f"{row['name']:18s} y{side['year']} cp{side['cur_player']} "
                  f"pend={row['pending']} slots={row['queue'][:4]} min={row['minerals']} "
                  f"d0={row['credit_d0']} tbl_de@{TABLE_DE:#x}={row['table_de']} "
                  f"tbl_dc@{TABLE_DC:#x}={row['table_dc']}")


if __name__ == "__main__":
    main()
