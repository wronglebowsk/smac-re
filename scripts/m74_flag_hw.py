#!/usr/bin/env python3
"""M74 (second instrument): HARDWARE watchpoints on the live +0x30 flag WORDS.

m74_flag_watch armed 11 conditional breakpoints on the eleven known absolute-address
writers and ZERO fired while 193/194 flipped 0x41 -> 0x05 (tag m74flag2).  That
instrument guessed the writers; this one does not.  It watches the flag words
themselves — four 2-byte hardware watchpoints on the records whose bit 2 was observed
to flip (65, 193, 194, 195) — and prints `$pc` for EVERY store that touches them.
A watchpoint cannot miss a write to its own word, so a no-event run means the words
did NOT change in the window (or the instrument is mis-armed — it prints its own
addresses and demands "Hardware watchpoint" four times before driving).

The watchpoint reports the pc AFTER the store (map back with a 16-byte objdump
window).  Shape: fresh m54b_clean.SAV (193/194 load at 0x41), one designed unit
enqueued, storage poked and read back, then N turn boundaries.

    python3 scripts/m74_flag_hw.py --boundaries 3 --tag m74flag3   # -> PASS / FAIL
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

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import m55_boundary as M          # noqa: E402
import m74_flag_watch as F        # noqa: E402  (reuses game_pid/base_row/flag_census)

ROOT = F.ROOT
EVID = F.EVID
WATCH = [193, 194, 65, 195]       # bit 2 was observed to flip on these (notes s114/s115)
BASE_NAME = "University Base"

TMPL = r"""set pagination off
set confirm off
set can-use-hw-watchpoints 1
@@WATCHES@@printf "ARMED @@N@@ hw watchpoints at @@ADDRS@@\n"
continue
"""

WBLOCK = r"""watch *(short *)@@A@@
commands
silent
printf "FLAGW tid=@@T@@ pc=0x%x val=0x%x\n", $pc, *(short *)@@A@@
continue
end
"""


def gdb_script(tids):
    blocks, addrs = [], []
    for t in tids:
        a = F.FLAG_ADDR + t * 0x34
        addrs.append("%#x" % a)
        blocks.append(WBLOCK.replace("@@A@@", "%#x" % a).replace("@@T@@", str(t)))
    return (TMPL.replace("@@WATCHES@@", "".join(blocks))
                .replace("@@N@@", str(len(tids)))
                .replace("@@ADDRS@@", " ".join(addrs)))


LINE = re.compile(r"^FLAGW tid=(\d+) pc=(0x[0-9a-f]+) val=(0x[0-9a-f]+)\s*$")


def parse(text):
    ev = []
    for ln in text.splitlines():
        m = LINE.match(ln.strip())
        if m:
            ev.append({"tag": "FLAGW", "tid": int(m.group(1)),
                       "pc": int(m.group(2), 16), "val": int(m.group(3), 16)})
    return ev


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boundaries", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=150)
    ap.add_argument("--tag", default="m74flag3")
    ap.add_argument("--poke-minerals", type=int, default=200)
    a = ap.parse_args()

    pid = F.game_pid()
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        row = F.base_row(m, BASE_NAME)
        census_before = F.flag_census(m)
    before = {t: census_before[t] for t in WATCH}
    print(f"pid {pid} base {BASE_NAME!r} addr 0x{row['addr']:x} head {row['slots'][0]} "
          f"pending {row['pending']} storage {row['minerals']} round {row['round']}",
          flush=True)
    print("watched flags before: " + ", ".join(f"{t}=0x{v:08x}" for t, v in
                                               sorted(before.items())), flush=True)

    def poke_storage(value):
        with open(f"/proc/{pid}/mem", "rb+", 0) as mm:
            mm.seek(row["addr"] + 0x40)
            mm.write(struct.pack("<i", value))
            mm.seek(row["addr"] + 0x40)
            return struct.unpack("<i", mm.read(4))[0]

    got = poke_storage(a.poke_minerals)
    print(f"  storage poked to {a.poke_minerals}, read back {got}", flush=True)

    gpath = os.path.join(ROOT, "scratch", f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.gdblog")
    os.makedirs(os.path.dirname(gpath), exist_ok=True)
    os.makedirs(EVID, exist_ok=True)
    open(gpath, "w").write(gdb_script(WATCH))
    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath,
                          "-p", str(pid)], stdout=log, stderr=subprocess.STDOUT)
    time.sleep(3.0)
    head = open(lpath, "r", errors="replace").read()
    n_hw = head.count("Hardware watchpoint")
    if "ARMED" not in head or n_hw < len(WATCH):
        try:
            os.kill(g.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
        subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
        raise SystemExit(f"gdb did not arm 4 HARDWARE watchpoints (saw {n_hw}):\n"
                         + head[-1200:])
    print(f"armed: {n_hw} hardware watchpoints on {WATCH}", flush=True)

    t0 = time.time()
    rc_ok = True
    for k in range(a.boundaries):
        poke_storage(a.poke_minerals)
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "smac_play.py"),
                            "--turns", "1", "--timeout", str(a.timeout), "--no-escape",
                            "3000", "--orders-per-turn", "1", "--verbose",
                            "--tag", f"{a.tag}_r{k}"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            rc_ok = False
        print(f"  boundary {k}: rc={r.returncode} t={time.time()-t0:.0f}s "
              f"{r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ''}",
              flush=True)

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

    tracer = subprocess.run(["grep", "-m1", "TracerPid", "/proc/%d/status" % pid],
                            capture_output=True, text=True).stdout.split()[-1]
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        after_row = F.base_row(m, BASE_NAME)
        census_after = F.flag_census(m)
    after = {t: census_after[t] for t in WATCH}
    print("watched flags after:  " + ", ".join(f"{t}=0x{v:08x}" for t, v in
                                               sorted(after.items())), flush=True)
    print(f"  after: head {after_row['slots'][0]} pending {after_row['pending']} "
          f"round {after_row['round']} tracer {tracer}", flush=True)

    text = open(lpath, "r", errors="replace").read()
    ev = parse(text)
    with open(os.path.join(EVID, f"{a.tag}_seq.jsonl"), "w") as fh:
        for d in ev:
            fh.write(json.dumps(d) + "\n")
    print(f"--- {len(ev)} FLAGW events ---")
    for e in ev:
        print(f"  tid {e['tid']} pc 0x{e['pc']:x} val 0x{e['val']:x}")

    flipped = sorted(t for t in WATCH
                     if not (before[t] & 4) and (after[t] & 4))
    attrib = sorted({(e["tid"], e["pc"]) for e in ev
                     if e["tid"] in flipped and (e["val"] & 4)})
    ok = bool(flipped) and bool(attrib) and tracer == "0" and rc_ok
    print(f"flipped in window: {flipped}; writer pcs: "
          f"{sorted(set(pc for _t, pc in attrib))}")
    print(f"ACCEPTANCE m74flag3: {'PASS' if ok else 'FAIL'} "
          f"(flipped={flipped} attributed_pcs="
          f"{sorted(set(pc for _t, pc in attrib))} events={len(ev)} tracer={tracer})",
          flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
