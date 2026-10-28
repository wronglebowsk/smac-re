#!/usr/bin/env python3
"""M82 ACCEPTANCE (tag m82bit7a) — WHAT +0x30 BITS 6/7 DO (and do NOT do) TO THE PRICE.

M81 named the writers: 0x574125 ORs bit 6 (iff [ebp-0xc] != 0) and 0x57412c ORs bit 7
(unconditionally) on the sweep's create path.  Static enumeration of every access to the
flag WORD (0x98ad88 + tid*52 + 0x30, 168 sites in scratch/m574/text.txt) finds NO test of
bit 6 or bit 7: every `test BYTE PTR [...0x98adb8],imm` uses 0x1/0x4/0x8/0x10, the only
bit-7-specific instruction is the CLEARER `and BYTE PTR [eax*4+0x98adb8],0x7f` at 0x577ca8,
and the markup test is `test BYTE PTR [ecx+0x98adb8],0x4` at 0x5ac99c (bit 2 only).
This run tests that prediction on the live price gate.

PART 1 (no gdb): census the flag WORD over ALL 8 bands (0..511) in one read — which records
carry bit 6 / bit 7.
PART 2 (gdb, 3 boundaries, 4 silent base-conditioned breakpoints 0x4efa4b/0x4efa52/0x4efa5e/
0x4efa63 — the proven m72/m73 shape): record 194 sits at the head of University Base and
storage is poked BELOW both prices every boundary, so the gate BAILS: no pay, no create,
the head stays 194 and the gate prints one row per boundary.  Bit 2 (the proven markup
switch, M73/M74) is HELD CLEAR in windows 1 and 2 so the only variable between them is
bit 7; window 3 sets bit 2 as the control that the instrument can detect a markup switch.
Every row prints the flag WORD the gate itself saw, so the flag state is read back, not
assumed.

Gates (one real invocation, no floor weakened):
  G1 gdb armed: the log prints ARMED with the base/head/pending read by gdb itself
  G2 census: 512 records read, >= 1 non-empty, bit6/bit7 carrier lists printed
  G3 W1: >= 1 gate row for tid 194 with bit 2 CLEAR and bit 7 CLEAR (baseline)
  G4 the poke changed ONLY bit 7 of the flag WORD (read back from /proc/pid/mem)
  G5 W2: >= 1 gate row for tid 194 with bit 2 CLEAR and bit 7 SET, after the poke
  G6 W3 control: >= 1 gate row for tid 194 with bit 2 SET whose edi DIFFERS from W1's
     (a shape that cannot see a markup switch is not a test)
  G7 prediction: edi(W1) == edi(W2) — bit 7 does NOT gate the price (the instruction
     bytes at 0x5ac99c test bit 2 only).  A different edi is a surprise, printed.
Exit 0 prints PASS.
"""
import argparse, os, re, signal, struct, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import m74_flag_watch as F

ROOT, EVID = F.ROOT, F.EVID
REC_BASE, STRIDE = 0x98AD88, 52
FLAG_OFF = 0x30
BASE_NAME = "University Base"
BASE_INDEX = 0
TID = 194
STORAGE = 20                      # below BOTH predicted prices (27 markup-off, 45 markup-on)
TMPL = r"""set pagination off
set confirm off
set height 0
set verbose off
set can-use-hw-watchpoints 1
set $b = @@ADDR@@
break *0x4efa4b if *(int *)0x8f0d60 == $b
commands
silent
printf "FACTA id=%d own=%d A=%d\n", $ebx, *(int *)($b + 4), $eax
continue
end
break *0x4efa52 if *(int *)0x8f0d60 == $b
commands
silent
printf "FACTB id=%d A=%d B=%d\n", $ebx, $edi, $eax
continue
end
break *0x4efa5e if *(int *)0x8f0d60 == $b
commands
silent
printf "GATE id=%d storage=%d edi=%d f30=0x%x\n", $ebx, *(int *)($b + 0x40), $edi, *(short *)($ebx*52+0x98adb8)
continue
end
break *0x4efa63 if *(int *)0x8f0d60 == $b
commands
silent
printf "BAIL id=%d storage=%d edi=%d f30=0x%x\n", $ebx, *(int *)($b + 0x40), $edi, *(short *)($ebx*52+0x98adb8)
continue
end
printf "ARMED base=0x%x head=%d pending=%d storage=%d\n", $b, *(int *)($b + 0x50), *(int *)($b + 0x4c), *(int *)($b + 0x40)
continue
"""

LINE = re.compile(r"^(FACTA|FACTB|GATE|BAIL|ARMED)\s*(.*)$")
KV = re.compile(r"(\w+)=(-?0x[0-9a-f]+|-?\d+)")
CHATTER = ("warning:", "Reading symbols", "0x", "Breakpoint", "[", "The program", "This GDB",
           "Enable debuginfod", "<https://debuginfod", "Debuginfod has been disabled",
           "To make this setting", "Thread ", "received signal SIGINT")


def parse(text):
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


def flag_addr(t):
    return REC_BASE + t * STRIDE + FLAG_OFF


def census(m):
    m.seek(REC_BASE)
    blob = m.read(512 * STRIDE)
    rows = []
    for i in range(512):
        r = blob[i * STRIDE:i * STRIDE + STRIDE]
        rows.append((i, r[0:20].split(b"\0")[0].decode("latin-1", "replace"),
                     r[0x2c], r[0x30] | (r[0x31] << 8)))
    return rows


def read_flag(pid, t):
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        m.seek(flag_addr(t))
        b = m.read(2)
    return b[0] | (b[1] << 8)


def poke_flag_bits(pid, t, set_bits=0, clear_bits=0):
    """Byte-OR/AND on the flag LOW byte only (the same shape as 0x57412c / 0x5741f0)."""
    a = flag_addr(t)
    with open(f"/proc/{pid}/mem", "rb+", 0) as m:
        m.seek(a)
        pre = m.read(2)
        m.seek(a)
        m.write(bytes([(pre[0] & ~clear_bits | set_bits) & 0xFF, pre[1]]))
        m.seek(a)
        post = m.read(2)
    return (pre[0] | (pre[1] << 8)), (post[0] | (post[1] << 8))


def run_script(args_list, timeout=200):
    r = subprocess.run([sys.executable] + args_list, capture_output=True, text=True,
                       timeout=timeout)
    out = (r.stdout or "").strip().splitlines()
    return r.returncode, out[-3:] if out else [(r.stderr or "")[-200:]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boundaries", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--tag", default="m82bit7a")
    a = ap.parse_args()

    pid = F.game_pid()
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        row = F.base_row(m, BASE_NAME)
        rows0 = census(m)
    addr = row["addr"]
    print(f"pid {pid} base {BASE_NAME!r} addr 0x{addr:x} head {row['slots'][0]} "
          f"pending {row['pending']} storage {row['minerals']} flag(194)=0x{read_flag(pid, TID):04x}",
          flush=True)

    # ---- PART 1: the census over all 8 bands
    nonempty = [r for r in rows0 if r[1]]
    b6 = [r[0] for r in rows0 if r[3] & 0x40]
    b7 = [r[0] for r in rows0 if r[3] & 0x80]
    b2 = [r[0] for r in rows0 if r[3] & 0x4]
    print(f"CENSUS 512 slots: nonempty {len(nonempty)} ids {[r[0] for r in nonempty]}", flush=True)
    for band in range(8):
        lo = band * 64
        ids = [r[0] for r in nonempty if lo <= r[0] < lo + 64]
        if ids:
            print(f"  band {band} {ids[0]}..{ids[-1]} flags " +
                  " ".join(f"{r[0]}:0x{r[3]:04x}" for r in rows0 if lo <= r[0] < lo + 64 and r[3]),
                  flush=True)
    print(f"  bit6(0x40) carriers {b6}\n  bit7(0x80) carriers {b7}\n  bit2(0x4) carriers {b2}",
          flush=True)

    # ---- setup: 194 at the head, bit 2 and bit 7 CLEAR, storage below both prices
    if row["pending"] == 0 or row["slots"][0] != TID:
        rc, tail = run_script([os.path.join(ROOT, "scripts", "m70_clear_dialog.py")])
        print("dialog clear:", tail, flush=True)
        rc, tail = run_script([os.path.join(ROOT, "scripts", "m57_ui_enqueue.py"),
                               "--base-index", str(BASE_INDEX), "--cell-item", str(TID),
                               "--inserts", "1"])
        print(f"enqueue rc={rc}:", tail, flush=True)
        with open(f"/proc/{pid}/mem", "rb", 0) as m:
            row = F.base_row(m, BASE_NAME)
    print(f"after enqueue: head {row['slots'][0]} pending {row['pending']} "
          f"slots {row['slots'][:3]}", flush=True)
    pre194, post194 = poke_flag_bits(pid, TID, clear_bits=0x84)   # clear bit 2 and bit 7
    print(f"setup flag 194: 0x{pre194:04x} -> 0x{post194:04x} (bit2 and bit7 cleared)", flush=True)

    def poke_storage(value):
        with open(f"/proc/{pid}/mem", "rb+", 0) as mm:
            mm.seek(addr + 0x40)
            mm.write(struct.pack("<i", value))
            mm.seek(addr + 0x40)
            return struct.unpack("<i", mm.read(4))[0]

    stor0 = poke_storage(STORAGE)
    print(f"  storage poked {STORAGE} read back {stor0}", flush=True)

    # ---- PART 2: the gate, three windows
    gpath = os.path.join(ROOT, "scratch", f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.gdblog")
    os.makedirs(EVID, exist_ok=True)
    open(gpath, "w").write(TMPL.replace("@@ADDR@@", hex(addr)))
    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=log, stderr=subprocess.STDOUT)
    head = ""
    for _ in range(60):
        head = open(lpath, "r", errors="replace").read()
        if "ARMED" in head or not os.path.exists("/proc/%d" % g.pid):
            break
        time.sleep(0.5)
    if "ARMED" not in head:
        try:
            os.kill(g.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
        subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
        raise SystemExit("gdb did not arm:\n" + head[-1200:])
    print("armed:", [l for l in head.splitlines() if l.startswith("ARMED")][0], flush=True)

    seen = 0
    windows = []
    t0 = time.time()
    for k in range(a.boundaries):
        stor = poke_storage(STORAGE)
        fl = read_flag(pid, TID)
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "smac_play.py"),
                            "--turns", "1", "--timeout", str(a.timeout), "--no-escape", "3000",
                            "--orders-per-turn", "1", "--verbose", "--tag", f"{a.tag}_r{k}"],
                           capture_output=True, text=True)
        text = open(lpath, "r", errors="replace").read()
        ev, bad = parse(text)
        new = ev[seen:]
        seen = len(ev)
        windows.append(dict(k=k, storage=stor, flag=fl, ev=new,
                            last=(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "")))
        print(f"  boundary {k}: rc={r.returncode} storage={stor} flag(194)=0x{fl:04x} "
              f"t={time.time()-t0:.0f}s rows={len(new)} {windows[-1]['last']}", flush=True)
        if k == 0:                      # W1 -> W2: flip ONLY bit 7
            p1, p2 = poke_flag_bits(pid, TID, set_bits=0x80)
            print(f"  POKE bit7 on 194: 0x{p1:04x} -> 0x{p2:04x} "
                  f"changed={sorted({(p1 ^ p2) & (1 << b) for b in range(16) if (p1 ^ p2) >> b & 1})}",
                  flush=True)
            poke194 = (p1, p2)
        elif k == 1:                    # W2 -> W3: bit7 back off, bit2 ON (control vs W1)
            p1, p2 = poke_flag_bits(pid, TID, set_bits=0x4, clear_bits=0x80)
            print(f"  CONTROL flag 194: 0x{p1:04x} -> 0x{p2:04x} (bit7 off, bit2 on)", flush=True)

    try:
        os.kill(g.pid, signal.SIGINT)
    except ProcessLookupError:
        pass
    for _ in range(40):
        if not os.path.exists("/proc/%d" % g.pid):
            break
        time.sleep(0.5)
    subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
    time.sleep(1.0)
    log.close()

    text = open(lpath, "r", errors="replace").read()
    ev, bad = parse(text)
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        rows1 = census(m)
    poke194 = locals().get("poke194", (0, 0))

    def gate_rows(w):
        return [e for e in w["ev"] if e["tag"] in ("GATE", "BAIL") and e.get("id") == TID]

    wrows = [[e for e in gate_rows(w)] for w in windows]
    for w, rows in zip(windows, wrows):
        print(f"  window {w['k']} flag=0x{w['flag']:04x} gate rows: {rows}", flush=True)
    print("bad lines:", bad[:5], flush=True)

    def pick(rows, bit2, bit7):
        for e in rows:
            f = e.get("f30", 0)
            if bool(f & 4) == bit2 and bool(f & 0x80) == bit7:
                return e
        return None

    w1 = pick(wrows[0], False, False) if wrows else None
    w2 = pick(wrows[1], False, True) if len(wrows) > 1 else None
    w3 = pick(wrows[2], True, False) if len(wrows) > 2 else None
    w1_edi, w2_edi, w3_edi = (w1 or {}).get("edi"), (w2 or {}).get("edi"), (w3 or {}).get("edi")

    g1 = any(e["tag"] == "ARMED" for e in ev)
    g2 = len(rows0) == 512 and len(nonempty) >= 1
    g3 = w1 is not None
    g4 = poke194[1] == (poke194[0] | 0x80) and poke194[0] & 0x80 == 0
    g5 = w2 is not None
    g6 = w3 is not None and w1 is not None and w3_edi != w1_edi
    g7 = w1 is not None and w2 is not None and w1_edi == w2_edi
    verdict = ("bit7 GATES the price" if (w1 and w2 and w1_edi != w2_edi)
               else "bit7 does NOT gate the price")
    print(f"edi W1(bit2 off,bit7 off)={w1_edi} W2(bit2 off,bit7 ON)={w2_edi} "
          f"W3 control(bit2 ON)={w3_edi} -> VERDICT {verdict}", flush=True)
    b6_after = [r[0] for r in rows1 if r[3] & 0x40]
    b7_after = [r[0] for r in rows1 if r[3] & 0x80]
    print(f"after census: bit6 {b6_after} bit7 {b7_after} flag(194)=0x{read_flag(pid, TID):04x}",
          flush=True)
    res = dict(G1=g1, G2=g2, G3=g3, G4=g4, G5=g5, G6=g6, G7=g7)
    print("gates:", res, flush=True)
    if all(res.values()):
        print("PASS", flush=True)
        return 0
    print("FAIL", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
