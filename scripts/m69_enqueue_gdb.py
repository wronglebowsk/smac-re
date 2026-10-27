#!/usr/bin/env python3
"""M69 — arm gdb on the BUILD-pane INSERT and record what the enqueue actually does.

M68 measured an APPEND (five clicks, region slots 1..5) where M67 had measured a SORTED
insert, and the disagreement is confounded by base/round/minerals/queue/chooser.  Click
order cannot settle it any more: this instrument stops guessing and watches the code.

What it logs, for every click made by another script while it is armed:

  * `0x418a99` (`cmp eax,0x3`) — the dialog's return value, i.e. which jump-table case
    will run, with pending and the 12 queue dwords BEFORE anything happens;
  * `0x418aa9` / `0x418ab3` / `0x418ae3` / `0x418af1` — which case fires (minerals store,
    the shift loop, pending := esi, pending := 0);
  * `0x418acd` — the 12 dwords right after the shift loop, so the hole it opens is visible;
  * `0x418b32` — `esi` (the index the code indexes the queue with) and the slot value it
    then pushes onto the queue list at `0x62732a`;
  * every write to the shifted array, via a hardware watchpoint on `base+0x54`, so a store
    that no disassembly search found cannot hide (`rwatch`/`awatch` are word-granular).

Usage (three steps, because the clicking belongs to the proven UI scripts):

    python3 scripts/m69_enqueue_gdb.py --base-name "University Base" --arm
    python3 scripts/m68_cellprobe.py --item 194 --trace evidence/m69_click_194.jsonl
    python3 scripts/m68_cellprobe.py --item 1   --trace evidence/m69_click_1.jsonl
    python3 scripts/m69_enqueue_gdb.py --stop
    python3 scripts/m69_enqueue_gdb.py --parse        # -> evidence/m69_enqueue.jsonl

`--arm` refuses if a gdb is already attached, if `TracerPid` is not 0, if ptrace_scope is
not 0, or if the base's pending is not what the caller expects with `--want-pending N`.
"""
import argparse
import json
import os
import signal
import struct
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPATH = os.path.join(ROOT, "scratch", "m69", "enqueue.gdb")
LPATH = os.path.join(ROOT, "evidence", "m69_enqueue.gdblog")
PIDFILE = os.path.join(ROOT, "scratch", "m69", "gdb.pid")

BASE_ARR = 0x95DA10          # the SAME constants smac_play.py uses (0x9C00/0x986040 is not it)
BASE_SZ = 304
BASE_COUNT = 0x985AF4

# the queue: pending +0x4c, dwords +0x50 .. +0x7c (head + 11)
QUEUE_OFF = 0x50
PEND_OFF = 0x4C

TMPL = r"""set pagination off
set confirm off
set height 0
set verbose off
set can-use-hw-watchpoints 1
set $b = @@ADDR@@
set $n = 0
define slots
  printf " slots"
  set $i = 0
  while $i < 12
    printf " %d", *(int *)($b + 0x50 + 4*$i)
    set $i = $i + 1
  end
  printf "\n"
end
break *0x417dbf
commands
silent
printf "ENQUEUE obj=0x%x pos=%d pending=%d\n", $ecx, *(int *)($ecx + 0x3ff5c), *(int *)($b + 0x4c)
slots
continue
end
break *0x417e04
commands
silent
printf "STORE queue[%d]=%d (item ebx) pending=%d\n", $edx, $ebx, *(int *)($b + 0x4c)
continue
end
break *0x418a99
commands
silent
set $n = $n + 1
printf "CLICK#%d at 418a99: dialog_ret=0x%x pending=%d\n", $n, $eax, *(int *)($b + 0x4c)
slots
continue
end
break *0x418aa9
commands
silent
printf "  case0 minerals_store esi=%d (minerals was %d) pending=%d\n", $esi, *(int *)($b + 0x40), *(int *)($b + 0x4c)
continue
end
break *0x418ab3
commands
silent
printf "  case1 SHIFT entry pending=%d\n", *(int *)($b + 0x4c)
continue
end
break *0x418acd
commands
silent
printf "  after shift:\n"
slots
continue
end
break *0x418ae3
commands
silent
printf "  pending := 1 (esi>=0 path) at 418ae3 pending=%d\n", *(int *)($b + 0x4c)
continue
end
break *0x418af1
commands
silent
printf "  pending := 0 (esi<0 path) at 418af1 pending=%d\n", *(int *)($b + 0x4c)
continue
end
break *0x418b32
commands
silent
printf "  list_append esi=%d slot[esi]=%d pending=%d\n", $esi, *(int *)($b + 0x50 + 4*$esi), *(int *)($b + 0x4c)
continue
end
watch *(int *)($b + 0x54)
commands
silent
printf "  WRITE slot1 pc=0x%x now=%d pend=%d\n", $pc, *(int *)($b + 0x54), *(int *)($b + 0x4c)
continue
end
watch *(int *)($b + 0x58)
commands
silent
printf "  WRITE slot2 pc=0x%x now=%d pend=%d\n", $pc, *(int *)($b + 0x58), *(int *)($b + 0x4c)
continue
end
watch *(int *)($b + 0x5c)
commands
silent
printf "  WRITE slot3 pc=0x%x now=%d pend=%d\n", $pc, *(int *)($b + 0x5c), *(int *)($b + 0x4c)
continue
end
printf "ARMED base=0x%x\n", $b
continue
"""


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def _pread(f, a, n):
    f.seek(a)
    return f.read(n)


def game_pid():
    out = sh(["pgrep", "-x", "terran.exe"]).stdout.split()
    if not out:
        raise SystemExit("terran.exe not running")
    return int(out[0])


def base_addr(pid, name=None, want_index=None):
    f = open("/proc/%d/mem" % pid, "rb", 0)
    n = int.from_bytes(_pread(f, BASE_COUNT, 4), "little")
    hits = []
    for i in range(min(n, 64)):
        b = _pread(f, BASE_ARR + i * BASE_SZ, BASE_SZ)
        nm = b[19:59].split(b"\0")[0].decode("latin-1", "replace")
        if want_index is not None:
            if i == want_index:
                hits.append((i, nm, b))
        elif name and name.lower() in nm.lower():
            hits.append((i, nm, b))
    f.close()
    if len(hits) != 1:
        raise SystemExit("base lookup got %d hits for %r idx=%r" % (len(hits), name, want_index))
    i, nm, b = hits[0]
    g = lambda o: struct.unpack("<i", b[o:o + 4])[0]
    slots = [g(QUEUE_OFF + 4 * k) for k in range(12)]
    return i, nm, BASE_ARR + i * BASE_SZ, dict(pending=g(PEND_OFF), minerals=g(0x40),
                                               d0=g(0xD0), slots=slots)


def arm(a):
    pid = game_pid()
    if sh(["pgrep", "-x", "gdb"]).stdout.strip():
        raise SystemExit("a gdb is already running — run --stop first")
    tracer = sh(["grep", "-m1", "TracerPid", "/proc/%d/status" % pid]).stdout.split()[-1]
    if tracer != "0":
        raise SystemExit("TracerPid=%s != 0" % tracer)
    scope = sh(["sysctl", "-n", "kernel.yama.ptrace_scope"]).stdout.strip()
    if scope != "0":
        raise SystemExit("ptrace_scope=%s (need 0)" % scope)
    idx, nm, addr, pre = base_addr(pid, a.base_name, a.base_index)
    print("base %r idx=%d addr=0x%x pending=%d minerals=%d" % (nm, idx, addr, pre["pending"],
                                                              pre["minerals"]))
    print("  slots %s" % pre["slots"])
    if a.want_pending is not None and pre["pending"] != a.want_pending:
        raise SystemExit("pending %d != --want-pending %d" % (pre["pending"], a.want_pending))
    os.makedirs(os.path.dirname(GPATH), exist_ok=True)
    open(GPATH, "w").write(TMPL.replace("@@ADDR@@", hex(addr)))
    os.makedirs(os.path.dirname(LPATH), exist_ok=True)
    lf = open(LPATH, "wb")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", GPATH, "-p", str(pid)],
                         stdout=lf, stderr=subprocess.STDOUT)
    open(PIDFILE, "w").write(str(g.pid))
    time.sleep(3)
    txt = open(LPATH, "rb").read().decode("latin-1", "replace")
    if "ARMED" not in txt:
        os.kill(g.pid, signal.SIGINT)
        raise SystemExit("gdb did not arm; log:\n" + txt[-800:])
    print("gdb armed pid %d; log %s" % (g.pid, os.path.relpath(LPATH, ROOT)))
    return 0


def stop(a):
    dp = int(open(PIDFILE).read()) if os.path.isfile(PIDFILE) else None
    pid = game_pid()
    if dp:
        try:
            os.kill(dp, signal.SIGINT)
        except ProcessLookupError:
            pass
        for _ in range(60):
            if not os.path.exists("/proc/%d" % dp):
                break
            time.sleep(0.5)
    sh(["kill", "-CONT", str(pid)])
    print("detached gdb %s; kill -CONT %d; log %s" % (dp, pid, os.path.relpath(LPATH, ROOT)))
    return 0


def parse(a):
    rows, keep = [], []
    for line in open(LPATH, "r", errors="ignore"):
        s = line.strip()
        if s.startswith("CLICK#"):
            # CLICK#1 at 418a99: dialog_ret=0x1 pending=0
            head, rest = s.split(" at ", 1)
            kv = dict(p.split("=", 1) for p in rest.split(": ", 1)[1].split() if "=" in p)
            rows.append(dict(tag="click", n=int(head.split("#")[1]), dialog_ret=kv["dialog_ret"],
                             pending=int(kv["pending"]), slots=None, raw=s))
        elif s.startswith("slots ") and rows and rows[-1].get("slots") is None:
            rows[-1]["slots"] = [int(x) for x in s.split()[1:]]
        elif s.startswith("ENQUEUE") or s.startswith("STORE") \
                or s.startswith("case0") or s.startswith("case1") or s.startswith("pending :=") \
                or s.startswith("list_append") or s.startswith("WRITE") \
                or s.startswith("after shift") or s.startswith("slots "):
            rows.append(dict(tag=s.split()[0].rstrip(":"), raw=s))
        elif s.startswith("ARMED") or "Thread" in s or s.startswith("[New Thread"):
            keep.append(s)
    out = os.path.join(ROOT, "evidence", "m69_enqueue.jsonl")
    with open(out, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    print("wrote %s (%d rows)" % (os.path.relpath(out, ROOT), len(rows)))
    for r in rows:
        print(" ", r["tag"], r["raw"][:110])
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-name", default="University Base")
    ap.add_argument("--base-index", type=int, default=None)
    ap.add_argument("--want-pending", type=int, default=None)
    ap.add_argument("--arm", action="store_true")
    ap.add_argument("--stop", action="store_true")
    ap.add_argument("--parse", action="store_true")
    a = ap.parse_args()
    if a.arm:
        return arm(a)
    if a.stop:
        return stop(a)
    if a.parse:
        return parse(a)
    ap.error("pick one of --arm | --stop | --parse")


if __name__ == "__main__":
    sys.exit(main())
