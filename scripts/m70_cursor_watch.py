#!/usr/bin/env python3
"""M70 — WHO WRITES THE QUEUE WIDGET'S CURSOR, and does a repaint rewrite the queue?

M69 proved the INSERT writes `queue[cursor]` (`[0x6a9480+0x3ff5c]`) but never said who sets
that cursor, and the log showed it moving on its own (2 -> 4 after one insert).  The static
read of the enqueue tail (scratch/m574/text.txt, 0x417e04-0x417e43) says:

    queue[cursor] = item ; if (cursor > pending) cursor = pending ;
    if (inserting) { pending++; if (cursor <= pending) cursor = pending + 1; } ; call 0x416080(1)

so the post-INSERT cursor is PREDICTABLE from the post-INSERT pending.  This instrument
watches the field live and attributes every write to a program counter:

  * hw watchpoint on 0x6e93dc = 0x6a9480 + 0x3ff5c (the cursor field itself);
  * breakpoints at the other cursor sites found in .text — 0x40aa22 (read) / 0x40aae5
    (write) in the queue-LIST row-click handler FUN_0040a990, whose disasm says
    `cursor = min(clicked_row, [base_ptr+0x4c] + 1)` — and 0x40b021/0x40b02c/0x40b031
    (a MOVE-UP helper: cursor -= 1, floored at 1) and 0x417e3b (the enqueue tail);
  * hw watchpoints on queue slots 1..3 so a paint that REWROTE the region is visible.

Usage (the clicking belongs to the proven UI scripts):

    python3 scripts/m70_cursor_watch.py --arm --base-name "University Base"
    python3 scripts/m66_insert_slot.py --base-name "University Base" \
        --item-a 193 --item-b 192 --slots 12 --trace /tmp/m70_flow.jsonl
    python3 scripts/m70_cursor_watch.py --stop
    python3 scripts/m70_cursor_watch.py --acceptance     # -> PASS / FAIL
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

GPATH = os.path.join(ROOT, "scratch", "m70", "cursor.gdb")
LPATH = os.path.join(ROOT, "evidence", "m70_cursor.gdblog")
PIDFILE = os.path.join(ROOT, "scratch", "m70", "gdb.pid")
STATE = os.path.join(ROOT, "scratch", "m70", "state.json")

WIDGET = 0x6A9480
CURSOR_OFF = 0x3FF5C
CURSOR_ABS = WIDGET + CURSOR_OFF           # 0x6e93dc
BASE_ARR = 0x95DA10
BASE_SZ = 304
BASE_COUNT = 0x985AF4
QUEUE_OFF = 0x50
PEND_OFF = 0x4C

# cursor writers found in .text (scripts/m70_scan_writers.py) and what each one means
WRITERS = {
    0x40aae5: "row-click handler FUN_0040a990: cursor = min(clicked_row, pending+1)",
    0x40ae56: "row-click handler FUN_0040a990 (the param_4 != 0 branch): cursor = eax",
    0x40b021: "move-up helper 0x40b00a: cursor -= 1 (NOT a row click)",
    0x40b02c: "move-up helper 0x40b00a: cursor floored at 1",
    0x40b031: "move-up helper 0x40b00a: the floored value stored",
    0x40b081: "handler tail reached from the move-up path: cursor = eax",
    0x417d80: "enqueue REMOVE path: cursor -= 1 before the shift-down",
    0x417e3b: "enqueue INSERT tail: cursor = pending + 1 (inserting branch)",
    0x417e6b: "move-up helper 0x417e50: cursor -= 1",
    0x417e7b: "move-up helper 0x417e50: cursor clamped to 1",
    0x418723: "dialog handler (0x4187xx family)",
    0x418734: "dialog handler (0x4187xx family)",
    0x418785: "dialog handler (0x4187xx family)",
    0x4194b3: "handler that zeroes the cursor",
    0x41996b: "handler that zeroes the cursor",
    0x41e231: "handler 0x41e2xx: cursor = eax",
    0x41e239: "handler 0x41e2xx: cursor = 9",
    0x41fa5f: "handler 0x41faxy: cursor = eax",
}
# EVERY `mov [reg+0x3ff5c], ...` in .text (scripts/m70_scan_writers.py found 18).  A gdb
# watchpoint reports the pc of the instruction AFTER the store that dirtied the watch
# (measured 2026-10-27: the run logged 0x40aaeb / 0x417e41 / 0x4194bd where the stores are
# 0x40aae5 / 0x417e3b / 0x4194b3), so a logged pc is mapped back to the store that caused
# it — and only when the gap is small, or an unrelated pc would be dressed up as a writer.
CURSOR_STORES = (0x40AAE5, 0x40AE56, 0x40B021, 0x40B031, 0x40B081, 0x417D80, 0x417E3B,
                 0x417E6B, 0x417E7B, 0x417ECA, 0x418723, 0x418734, 0x418785, 0x4194B3,
                 0x41996B, 0x41E231, 0x41E239, 0x41FA5F)
STORE_MAP_WINDOW = 16


def attribute_store(pc):
    """pc as gdb reported it (the instruction after the store) -> the storing instruction.

    Returns (store_pc, mapped) where mapped is False when no cursor store lies within
    STORE_MAP_WINDOW bytes below the logged pc — then the write is NOT ours to name.
    """
    cands = [s for s in CURSOR_STORES if s <= pc <= s + STORE_MAP_WINDOW]
    if not cands:
        return pc, False
    return max(cands), True


# the enqueue's own reads/stores, used as a control trace
ENQUEUE_BPS = (0x417dbf, 0x417e04)
ROW_BPS = (0x40aa22, 0x40aae5, 0x40ae56, 0x40b02c, 0x40b081, 0x417e3b, 0x417e6b, 0x417e7b)

TMPL = r"""set pagination off
set confirm off
set height 0
set verbose off
set can-use-hw-watchpoints 1
set $b = @@ADDR@@
define slots
  printf " slots"
  set $i = 0
  while $i < 12
    printf " %d", *(int *)($b + 0x50 + 4*$i)
    set $i = $i + 1
  end
  printf "\n"
end
watch *(int *)0x@@CURSOR@@
commands
silent
printf "CURSORWRITE pc=0x%x now=%d pend=%d\n", $pc, *(int *)0x@@CURSOR@@, *(int *)($b + 0x4c)
continue
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
break *0x40aa22
commands
silent
printf "ROWCLICK clicked=%d cursor_before=%d pending=%d\n", $eax, *(int *)($edi + 0x3ff5c), *(int *)($b + 0x4c)
continue
end
break *0x40b02c
commands
silent
printf "ROWCLAMP floor1=%d\n", $eax
continue
end
break *0x40b081
commands
silent
printf "ROWTAIL cursor=%d\n", $eax
continue
end
break *0x417e3b
commands
silent
printf "ENQTAIL_SET cursor_new=%d pending=%d\n", $eax, *(int *)($b + 0x4c)
continue
end
break *0x417e6b
commands
silent
printf "MOVEUP cursor_minus1=%d\n", $esi
continue
end
break *0x417e7b
commands
silent
printf "MOVEUP_CLAMP cursor=%d\n", $eax
continue
end
watch *(int *)($b + 0x54)
commands
silent
printf "SLOT1WRITE pc=0x%x now=%d pend=%d\n", $pc, *(int *)($b + 0x54), *(int *)($b + 0x4c)
continue
end
watch *(int *)($b + 0x58)
commands
silent
printf "SLOT2WRITE pc=0x%x now=%d pend=%d\n", $pc, *(int *)($b + 0x58), *(int *)($b + 0x4c)
continue
end
watch *(int *)($b + 0x5c)
commands
silent
printf "SLOT3WRITE pc=0x%x now=%d pend=%d\n", $pc, *(int *)($b + 0x5c), *(int *)($b + 0x4c)
continue
end
printf "ARMED base=0x%x cursor_abs=0x@@CURSOR@@ cursor=%d pending=%d\n", $b, *(int *)0x@@CURSOR@@, *(int *)($b + 0x4c)
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
    return i, nm, BASE_ARR + i * BASE_SZ, dict(
        pending=g(PEND_OFF), minerals=g(0x40), d0=g(0xD0),
        slots=[g(QUEUE_OFF + 4 * k) for k in range(12)])


def read_cursor(pid):
    f = open("/proc/%d/mem" % pid, "rb", 0)
    v = struct.unpack("<i", _pread(f, CURSOR_ABS, 4))[0]
    f.close()
    return v


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
    cur = read_cursor(pid)
    print("base %r idx=%d addr=0x%x pending=%d minerals=%d d0=%d"
          % (nm, idx, addr, pre["pending"], pre["minerals"], pre["d0"]))
    print("  slots %s" % pre["slots"])
    print("  cursor field 0x%x = %d" % (CURSOR_ABS, cur))
    if pre["pending"] + 2 > 9:
        raise SystemExit("pending %d + 2 inserts exceeds the 9-slot cap — pick a base with room"
                         % pre["pending"])
    os.makedirs(os.path.dirname(GPATH), exist_ok=True)
    open(GPATH, "w").write(TMPL.replace("@@ADDR@@", hex(addr))
                          .replace("@@CURSOR@@", "%x" % CURSOR_ABS))
    os.makedirs(os.path.dirname(LPATH), exist_ok=True)
    lf = open(LPATH, "wb")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", GPATH, "-p", str(pid)],
                         stdout=lf, stderr=subprocess.STDOUT)
    open(PIDFILE, "w").write(str(g.pid))
    time.sleep(3)
    txt = open(LPATH, "rb").read().decode("latin-1", "replace")
    if "ARMED" not in txt:
        os.kill(g.pid, signal.SIGINT)
        raise SystemExit("gdb did not arm; log:\n" + txt[-1200:])
    json.dump(dict(pid=pid, base_idx=idx, base_name=nm, base_addr=addr,
                   cursor_before=cur, pending_before=pre["pending"], slots_before=pre["slots"]),
              open(STATE, "w"))
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
    cur = read_cursor(pid)
    st = json.load(open(STATE)) if os.path.isfile(STATE) else {}
    f = open("/proc/%d/mem" % pid, "rb", 0)
    addr = st.get("base_addr")
    slots = None
    pend = None
    if addr:
        f.seek(addr + QUEUE_OFF)
        slots = list(struct.unpack("<12i", f.read(48)))
        pend = struct.unpack("<i", _pread(f, addr + PEND_OFF, 4))[0]
    f.close()
    st["cursor_after"] = cur
    st["slots_after"] = slots
    st["pending_after"] = pend
    json.dump(st, open(STATE, "w"))
    print("detached gdb %s; kill -CONT %d" % (dp, pid))
    print("READ BACK: cursor=%d pending=%s" % (cur, pend))
    print("  slots %s" % slots)
    return 0


def parse_lines(text):
    """Pure: gdb log text -> event rows.  Each CURSORWRITE carries the writing pc."""
    ev = []
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"CURSORWRITE pc=(0x[0-9a-f]+) now=(-?\d+) pend=(-?\d+)$", s)
        if m:
            raw = int(m.group(1), 16)
            store_pc, mapped = attribute_store(raw)
            ev.append(dict(tag="cursor_write", pc=store_pc, raw_pc=raw, mapped=mapped,
                           value=int(m.group(2)), pend=int(m.group(3))))
            continue
        m = re.match(r"ENQUEUE obj=(0x[0-9a-f]+) pos=(-?\d+) pending=(-?\d+)$", s)
        if m:
            ev.append(dict(tag="enqueue_read", obj=int(m.group(1), 16),
                           pos=int(m.group(2)), pend=int(m.group(3))))
            continue
        m = re.match(r"STORE queue\[(-?\d+)\]=(-?\d+) \(item ebx\) pending=(-?\d+)$", s)
        if m:
            ev.append(dict(tag="store", slot=int(m.group(1)), item=int(m.group(2)),
                           pend=int(m.group(3))))
            continue
        m = re.match(r"ROWCLICK clicked=(-?\d+) cursor_before=(-?\d+) pending=(-?\d+)$", s)
        if m:
            ev.append(dict(tag="rowclick", clicked=int(m.group(1)),
                           cursor_before=int(m.group(2)), pend=int(m.group(3))))
            continue
        m = re.match(r"ROWCLICKSTORE clamped=(-?\d+)$", s)
        if m:
            ev.append(dict(tag="rowclick_store", value=int(m.group(1))))
            continue
        m = re.match(r"ROWTAIL cursor=(-?\d+)$", s)
        if m:
            ev.append(dict(tag="rowtail", value=int(m.group(1))))
            continue
        m = re.match(r"ENQTAIL_SET cursor_new=(-?\d+) pending=(-?\d+)$", s)
        if m:
            ev.append(dict(tag="enqueue_tail_set", value=int(m.group(1)), pend=int(m.group(2))))
            continue
        m = re.match(r"(MOVEUP(?:_CLAMP)?) cursor(?:_minus1)?=(-?\d+)$", s)
        if m:
            ev.append(dict(tag="moveup", value=int(m.group(2))))
            continue
        m = re.match(r"SLOT([123])WRITE pc=(0x[0-9a-f]+) now=(-?\d+) pend=(-?\d+)$", s)
        if m:
            ev.append(dict(tag="slot_write", slot=int(m.group(1)), pc=int(m.group(2), 16),
                           value=int(m.group(3)), pend=int(m.group(4))))
            continue
        m = re.match(r"ARMED base=(0x[0-9a-f]+) cursor_abs=(0x[0-9a-f]+) cursor=(-?\d+) pending=(-?\d+)$", s)
        if m:
            ev.append(dict(tag="armed", cursor=int(m.group(3)), pend=int(m.group(4))))
    return ev


def score(ev, cursor_before, cursor_after, pending_after, slots_before, slots_after):
    """Pure acceptance: name the writers of the cursor field and check the read-backs
    against the static model of the enqueue.

    The cursor is clamped and advanced against the WIDGET's own row count
    (`[[0x8f0d60]+0x4c]` at 0x40aa22 / 0x417e14), not against the base record's pending
    that `--stop` reads back, so the model check uses the widget rows the trace itself
    carries (the `pend=` field of the ENQUEUE / ENQTAIL_SET events).

    PASS needs ALL of:
      1. at least one cursor write observed, and every one of them attributable to a known
         `mov [reg+0x3ff5c]` in .text after mapping gdb's after-store pc back
         (attribute_store); an unmapped pc means a writer we have not read;
      2. the run DISCRIMINATES: a cursor write from a pc that is NOT the enqueue itself
         (0x417xxx).  The enqueue always moves its own cursor, so an enqueue-only run
         proves nothing about who sets the cursor for the user;
      3. every write's VALUE equals what the static model predicts from the event it
         follows (row click -> min(clicked, widget_rows + 1); enqueue tail -> the value it
         printed; explicit zero stores -> 0);
      4. the enqueue tail's prediction holds at the moment it fires: the last tail value
         equals the widget rows it reported + 1 (disasm 0x417e2d-0x417e3b);
      5. the queue region changed (an INSERT really happened) and pending grew.
    """
    reasons = []
    ok = True
    writes = [e for e in ev if e["tag"] == "cursor_write"]
    if not writes:
        ok = False
        reasons.append("no CURSORWRITE event: the cursor field was never written while armed, "
                       "so no writer can be named")
    unmapped = sorted({e["raw_pc"] for e in writes if not e.get("mapped", True)})
    if unmapped:
        ok = False
        reasons.append("cursor writes from pcs with no known cursor store within %d bytes: %s"
                       % (STORE_MAP_WINDOW, ", ".join("0x%x" % p for p in unmapped)))
    non_enqueue = sorted({e["pc"] for e in writes
                          if not (0x417000 <= e["pc"] < 0x418000)})
    if writes and not non_enqueue:
        ok = False
        reasons.append("every cursor write came from the enqueue (0x417xxx) itself: the enqueue "
                       "always moves its own cursor, so this shape cannot name a cursor-setter "
                       "for the user — click a queue LIST row (or move the selection) in the run")

    # 3. value-by-value against the model.  A cursor write is judged against the last
    # NON-cursor-write event before it (the event that caused the store).
    rows = None
    bad_values = []
    prev = None
    for e in ev:
        if e["tag"] in ("enqueue_read", "enqueue_tail_set", "rowclick", "store") \
                and "pend" in e:
            rows = e["pend"]
        if e["tag"] == "enqueue_tail_set":
            if e["value"] != e["pend"] + 1:
                bad_values.append("tail printed %d, model says widget_rows+1 = %d"
                                  % (e["value"], e["pend"] + 1))
        if e["tag"] == "cursor_write":
            pred = None
            if e["pc"] == 0x417E3B and prev is not None and prev["tag"] == "enqueue_tail_set":
                pred = prev["value"]
            elif e["pc"] in (0x40AAE5, 0x40AE56) and prev is not None and prev["tag"] == "rowclick":
                pred = min(prev["clicked"], (rows if rows is not None else 0) + 1)
            elif e["pc"] in (0x4194B3, 0x41996B):
                pred = 0
            if pred is not None and e["value"] != pred:
                bad_values.append("write at 0x%x logged %d, model says %d"
                                  % (e["pc"], e["value"], pred))
        else:
            prev = e
    if bad_values:
        ok = False
        reasons.extend("model/value mismatch: " + b for b in bad_values)

    tail = [e for e in ev if e["tag"] == "enqueue_tail_set"]
    if not tail:
        ok = False
        reasons.append("the enqueue tail (0x417e3b) never fired — no INSERT ran while armed")
    else:
        last = tail[-1]
        pred = last["pend"] + 1
        if last["value"] != pred:
            ok = False
            reasons.append("the last enqueue tail printed %d, model says widget_rows+1 = %d"
                           % (last["value"], pred))
        last_i = max(i for i, e in enumerate(ev) if e is last)
        trailing = [e for i, e in enumerate(ev)
                    if e["tag"] == "cursor_write" and i > last_i]
        zeroers = {0x4194B3, 0x41996B}
        if cursor_after != pred and not any(e["pc"] in zeroers for e in trailing):
            ok = False
            reasons.append("cursor read back %d, model says %d, and no explicit zero store "
                           "(0x4194b3/0x41996b) fired after the last tail to explain it"
                           % (cursor_after, pred))
    if slots_before == slots_after:
        ok = False
        reasons.append("the queue region is unchanged — no INSERT happened, so the run proves "
                       "nothing about who moves the cursor")
    if (pending_after or 0) <= 0:
        ok = False
        reasons.append("pending did not grow")
    named = sorted({e["pc"] for e in writes})
    return ok, dict(cursor_writes=len(writes), writer_pcs=["0x%x" % p for p in named],
                    raw_pcs=["0x%x" % p for p in sorted({e["raw_pc"] for e in writes})],
                    non_enqueue_writers=["0x%x" % p for p in non_enqueue],
                    widget_rows=rows,
                    rowclicks=sum(1 for e in ev if e["tag"] == "rowclick"),
                    slot_writes=sum(1 for e in ev if e["tag"] == "slot_write"),
                    cursor_before=cursor_before, cursor_after=cursor_after,
                    pending_after=pending_after), reasons


def acceptance(a):
    st = json.load(open(STATE)) if os.path.isfile(STATE) else {}
    if "cursor_after" not in st:
        raise SystemExit("run --arm, then a click flow, then --stop first")
    text = open(LPATH, "r", errors="ignore").read()
    ev = parse_lines(text)
    json.dump(ev, open(os.path.join(ROOT, "evidence", "m70_cursor_events.jsonl"), "w"),
              indent=0)
    ok, summary, reasons = score(ev, st.get("cursor_before"), st.get("cursor_after"),
                                 st.get("pending_after"), st.get("slots_before"),
                                 st.get("slots_after"))
    print("events: %d  cursor_writes=%d  rowclicks=%d  slot_writes=%d"
          % (len(ev), summary["cursor_writes"], summary["rowclicks"], summary["slot_writes"]))
    print("  non-enqueue cursor writers: %s"
          % (", ".join(summary["non_enqueue_writers"]) or "NONE"))
    for p in summary["writer_pcs"]:
        pc = int(p, 16)
        print("  WRITER %s — %s" % (p, WRITERS.get(pc, "UNREAD pc")))
    for e in ev:
        if e["tag"] in ("enqueue_read", "store", "rowclick", "enqueue_tail_set"):
            print("  " + json.dumps(e))
    print("cursor before=%s after=%s pending after=%s"
          % (summary["cursor_before"], summary["cursor_after"], summary["pending_after"]))
    print("  slots before %s" % st.get("slots_before"))
    print("  slots after  %s" % st.get("slots_after"))
    for r in reasons:
        print("  reason: " + r)
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", action="store_true")
    ap.add_argument("--stop", action="store_true")
    ap.add_argument("--acceptance", action="store_true")
    ap.add_argument("--base-name", default="University Base")
    ap.add_argument("--base-index", type=int, default=None)
    a = ap.parse_args()
    if a.arm:
        return arm(a)
    if a.stop:
        return stop(a)
    if a.acceptance:
        return acceptance(a)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
