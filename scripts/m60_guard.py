#!/usr/bin/env python3
"""M60 — the create guard at 0x4eff32 is a GLOBAL, not a base field.

Static (scratch/m574/text.txt, whole .text):

  4eff20  89 46 40        mov    DWORD PTR [esi+0x40],eax     ; pay (minerals)
  4eff23  8b 35 60 0d 8f  mov    esi,DWORD PTR ds:0x8f0d60    ; current base record ptr
  4eff29  8b 46 40        mov    eax,DWORD PTR [esi+0x40]
  4eff2c  89 86 98 00 00  mov    DWORD PTR [esi+0x98],eax     ; mirror
  4eff32  a1 70 0d 8f 00  mov    eax,ds:0x8f0d70              ; THE GUARD
  4eff37  85 c0           test   eax,eax
  4eff39  75 21           jne    0x4eff5c                     ; nonzero -> NO create
  4eff3b  a1 60 0d 8f 00  mov    eax,ds:0x8f0d60
  4eff40  0f bf 48 02     movsx  ecx,WORD PTR [eax+0x2]       ; y
  4eff44  0f bf 10        movsx  edx,WORD PTR [eax]           ; x
  4eff4e  e8 fd b6 0b 00  call   0x5ab650                     ; create unit

`grep -c 0x8f0d70` over the whole .text dump is 1: this read.  Nothing in .text
writes it by absolute address, and the live dword reads 0.  So the old footing's
"[base+0x10] == 0" is wrong twice over: base record +0x10 is NOT the guard (it
holds 0x4b000000 / 0x55000000 on our two bases, i.e. not a flag), and the guard
is not a base field at all — it is the process-global scratch dword at 0x8f0d70,
the neighbour of the current-base pointer 0x8f0d60 and the chooser's best-pick
slots 0x8f0d74..0x8f0d90.

  stage=read  : guard value + our bases (minerals, +0x98 mirror, pending, head)
                + per-tile unit multiset + our unit total
  stage=poke  : write --value to 0x8f0d70, read back
  stage=watch : gdb hardware watchpoint on 0x8f0d70 + a marker breakpoint on the
                per-base visit 0x4ef6d0, driven over --boundaries turns

ONE variable per run; the other named base is the control.
"""
import argparse, json, os, re, signal, struct, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m55_boundary as M
import m56_build as B

GUARD = 0x8f0d70
VISIT = 0x4ef6d0          # FUN_004ef6d0, the per-base production visit
NAMES = ["Korolev Center", "University Base"]
EVID = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evidence")


def find_pid():
    pid = os.environ.get("SMAC_PID")
    return int(pid) if pid else M.find_pid()


def named(m, want):
    n = max(0, min(B.rd32(m, M.G["n_bases"][0]), 64))
    for i in range(n):
        b = B.prod_fields(m, i)
        if b["name"] == want:
            return b
    raise SystemExit(f"base {want!r} not among {n} bases")


def our_units(m):
    """Our faction's live units, as (idx, type, x, y)."""
    ours = B.rd32(m, M.G["our_player"][0])
    nu = max(0, min(B.rd32(m, M.G["n_units"][0]), 400))
    out = []
    for i in range(nu):
        u = M.parse_unit(i, M.rd(m, M.UNIT_ARR + i * M.UNIT_SZ, M.UNIT_SZ))
        if u["type"] >= M.MAX_TYPES or u["owner"] != ours:
            continue
        out.append(dict(idx=i, type=u["type"], x=u["x"], y=u["y"], order=u["order"]))
    return out


def snapshot(m, tag):
    tl = M.timeline_row(m)
    ours_list = our_units(m)
    bases = []
    for want in NAMES:
        b = named(m, want)
        rec = M.rd(m, M.BASE_ARR + b["i"] * M.BASE_SZ, M.BASE_SZ)
        bases.append(dict(name=b["name"], i=b["i"], x=b["x"], y=b["y"],
                          minerals=b["minerals"], income=b["income"],
                          pending=b["pending"], head=b["queue"][0],
                          flags0x30=struct.unpack("<I", rec[0x30:0x34])[0],
                          n_on_tile=sum(1 for u in ours_list if (u["x"], u["y"]) == (b["x"], b["y"])),
                          mirror0x98=struct.unpack("<i", rec[0x98:0x9c])[0],
                          field0x10=struct.unpack("<i", rec[0x10:0x14])[0],
                          plan0x38=struct.unpack("<I", rec[0x38:0x3c])[0]))
    return dict(tag=tag, year=tl["year"], round=tl["round"], cur_player=tl["cur_player"],
                guard=B.rd32(m, GUARD), bases=bases, n_ours=len(ours_list))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["read", "poke", "watch"], required=True)
    ap.add_argument("--value", type=int, default=None, help="value to write to 0x8f0d70")
    ap.add_argument("--boundaries", type=int, default=2)
    ap.add_argument("--timeout", type=float, default=240.0)
    ap.add_argument("--tag", default="m60")
    a = ap.parse_args()
    pid = find_pid()

    if a.stage == "watch":
        if subprocess.run(["pgrep", "-x", "gdb"], capture_output=True,
                          text=True).stdout.strip():
            raise SystemExit("a gdb is already running — run scripts/m57_credit.py --stop first")
        gpath = os.path.join(EVID, f"{a.tag}_watch.gdb")
        lpath = os.path.join(EVID, f"{a.tag}_watch.gdblog")
        open(gpath, "w").write(
            "set pagination off\nset confirm off\nset height 0\nset verbose off\n"
            f"watch *{GUARD:#x}\ncommands\nsilent\n"
            f'printf "GUARDWRITE pc=0x%x new=%d\\n", $pc, *(int*){GUARD:#x}\n'
            "continue\nend\n"
            f"break *{VISIT:#x}\ncommands\nsilent\n"
            f'printf "VISIT guard=%d\\n", *(int*){GUARD:#x}\n'
            "continue\nend\ncontinue\n")
        log = open(lpath, "w")
        g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath,
                              "-p", str(pid)], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        print(f"gdb armed pid {g.pid}; watching {GUARD:#x} for {a.boundaries} boundaries",
              flush=True)
        time.sleep(2.0)
        t0 = time.time()
        runs = []
        for k in range(a.boundaries):
            r = subprocess.run([sys.executable, os.path.join(os.path.dirname(
                os.path.abspath(__file__)), "smac_play.py"), "--turns", "1",
                "--timeout", str(int(min(a.timeout, 200))), "--no-escape", "3000",
                "--orders-per-turn", "1", "--verbose", "--tag", f"{a.tag}_r{k}"],
                capture_output=True, text=True)
            runs.append(r.returncode)
            print(f"  turn {k}: rc={r.returncode}", flush=True)
        try:
            os.kill(g.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
        time.sleep(1.0)
        try:
            g.kill()
        except ProcessLookupError:
            pass
        out = g.stdout.read().decode("latin-1", "replace") if g.stdout else ""
        log.write(out)
        log.close()
        writes = re.findall(r"GUARDWRITE pc=0x([0-9a-f]+) new=(-?\d+)", out)
        visits = re.findall(r"VISIT guard=(-?\d+)", out)
        seen = {}
        for pc, new in writes:
            seen.setdefault(int(pc, 16), []).append(int(new))
        print(json.dumps(dict(gdb_pid=g.pid, rc=g.poll(), boundaries=a.boundaries,
                              turn_rcs=runs, guard_writes=len(writes),
                              writers={f"0x{pc:x}": len(v) for pc, v in seen.items()},
                              visits=len(visits),
                              guard_values_at_visits=sorted(set(visits)),
                              gdb_log=lpath), indent=1))
        if not writes:
            print(f"NO WRITE to {GUARD:#x} across {a.boundaries} boundaries "
                  f"(the only .text reference is the read at 0x4eff32)")
        return

    with open(f"/proc/{pid}/mem", "rb+", 0) as m:
        if a.stage == "poke":
            if a.value is None:
                raise SystemExit("--value required for stage=poke")
            before = B.rd32(m, GUARD)
            m.seek(GUARD)
            m.write(struct.pack("<i", a.value))
            back = struct.unpack("<i", M.rd(m, GUARD, 4))[0]
            print(f"POKE 0x8f0d70 (create guard): {before} -> {a.value} "
                  f"(read back {back}) {'OK' if back == a.value else 'MISMATCH'}")
            if back != a.value:
                raise SystemExit("guard poke readback mismatch")
        print(json.dumps(snapshot(m, a.stage), indent=1))


if __name__ == "__main__":
    main()
