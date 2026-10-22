#!/bin/bash
# M34: watch the stored Farm order EXECUTE.
# Chain hypothesis (static, session 34): Space -> FUN_00512450 -> FUN_004d1e90(unit)
#   -> can-act gate FUN_005acc00 (needs mp: total - mpused > 0) -> FUN_00529090(unit,-1,0)
#   -> solo FUN_00585720(unit, dir=0x8-sentinel, 3) -> runs the unit's stored order byte.
# The Former (order 4, Farm) sits with mpused=3 so the cycle skips it and Space runs the
# cycle's unit. Plan: poke mpused=0 (TracerPid 0 — pokes under a tracer are ghosts),
# arm the chain bps, then race the game's selection: poke 0x91b5bc=Former and press
# Space immediately (selection is game-owned and revalidated within ~1 pump iteration).
# Pitfalls honored: poke before arming; gdb PID captured (never pkill -f in the run
# command); log read only after kill -TERM gdb; kill -CONT the inferior afterwards;
# all state reads outside the attach window.
set -u
cd /home/n100/reverse/smac
PID=$(pgrep -x terran.exe | head -1)
[ -z "$PID" ] && { echo "no terran.exe"; exit 1; }
grep -q 'TracerPid:[[:space:]]*0' /proc/$PID/status || { echo "tracer attached — abort"; exit 1; }
TAG=${TAG:-m34}
export TAG
LOG=evidence/${TAG}_gdb.log

# --- target Former (scan fresh; indices slide under compaction). Prefer one already
#     carrying a terraform order (leftover from a previous try); else any Former owned
#     by us — the race script presses 'f' itself to (re)issue the Farm order. ---
UNIT=$(python3 - <<'PY'
import sys; sys.path.insert(0,'scripts')
from m33_scan import *  # noqa
import struct
p = pid()
with open(f"/proc/{p}/mem","rb",0) as m:
    def rd(a,n): m.seek(a); return m.read(n)
    me = struct.unpack("<I", rd(PLAYER,4))[0]
    units = rd(UNIT_ARR, MAX_UNITS*52); classes = rd(CLASS_TBL, 1024*52)
    pick = None
    for i in range(MAX_UNITS):
        d = units[i*52:(i+1)*52]
        if d[14] == 0xFF: continue
        typ = struct.unpack("<H", d[10:12])[0]
        cls = classes[typ*52] & 0xFF
        if cls == 9 and d[14] == me:
            if d[17] == 4:
                pick = i; break
            if pick is None:
                pick = i
    if pick is not None: print(pick)
PY
)
[ -z "$UNIT" ] && { echo "no Former owned by us found"; exit 1; }
echo "target Former: rec$UNIT"

echo "--- pre-state (no tracer) ---"
python3 scripts/m33_state.py "evidence/${TAG}_pre.json" "$UNIT" >/dev/null || exit 1

# --- poke mpused=0 so the can-act gate passes (mp total 6 - 3 used = 3 > 0 was already
#     true, but the cycle's idle-filter treats mpused>0 as done; make it look fresh) ---
python3 - "$UNIT" <<'PY'
import struct, sys
sys.path.insert(0,'scripts')
import smac_play as P
pid,f = P.mem()
off = P.UNIT_ARR + int(sys.argv[1])*52 + 40
P.wr(f, off, struct.pack('<B', 0))
print('mpused rec%s ->' % sys.argv[1], P.rd(f, off, 1)[0])
PY

# gdb cannot read env vars in expressions: materialize a per-run script with the
# target index substituted into the SETTILE filter condition.
sed "s/__UNIT__/$UNIT/g" scripts/m34_exec.gdb > "evidence/${TAG}_exec.gdb"
gdb -batch -nx -x "evidence/${TAG}_exec.gdb" -p "$PID" > "$LOG" 2>&1 &
GPID=$!
sleep 5
NBP=$(grep -c "Breakpoint [0-9]* at" "$LOG")
if [ "$NBP" -lt 10 ]; then
  echo "ARM FAILED ($NBP/10 breakpoints)"; head -30 "$LOG"
  kill -TERM $GPID 2>/dev/null; sleep 1; kill -CONT "$PID" 2>/dev/null
  exit 2
fi
echo "armed ($NBP bps, gdb $GPID, game $PID)"

# --- race (M34 v4): NO selection pokes — under a live tracer our /proc/pid/mem WRITES
#     never reach the game (M33 pitfall; try3 proved it: TERRAF idx=50 landed on the
#     cycle's unit, not the poked 46). The game itself keeps rec46 selected after an
#     arrow move (M27), so drive it entirely by keys:
#       Up x2  (45,11)->(45,9), 2 steps, mpused 6 -> 3 remaining, still can-act
#       'f'    setter FUN_004d44d0(46,0) on tile (45,9) — farm-legal (M33 try5 landed
#              at (45,7); (45,11) is NOT: mask&0x20 remaps mode 0->0xa -> HASFARM abort)
#       Space  FUN_004d1e90(sel=46) -> can-act(3>0) -> FUN_00529090(46,-1,0) ->
#              FUN_00585720(46, dir 0x8 sentinel, 3) = run the stored order.
#     Stop when EXEC idx=target lands. ---
python3 - "$UNIT" "$LOG" <<'PY'
import os, struct, subprocess, sys, time
sys.path.insert(0,'scripts')
import smac_play as P
unit, log = int(sys.argv[1]), sys.argv[2]
pid, f = P.mem()
win = subprocess.run('xdotool search --name "Sid Meier"', shell=True,
                     capture_output=True, text=True,
                     env={**os.environ, "DISPLAY": ":99"}).stdout.split()
def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          env={**os.environ, "DISPLAY": ":99"})
def focus():
    if win: sh(f'xdotool windowfocus {win[0]}')
def press(k):
    focus(); sh(f'xdotool key --clearmodifiers {k}')
def pos():
    return struct.unpack('<HH', P.rd(f, P.UNIT_ARR + unit*52, 4))
def order():
    return P.rd(f, P.UNIT_ARR + unit*52 + 17, 1)[0]
def mpused():
    return P.rd(f, P.UNIT_ARR + unit*52 + 40, 1)[0]
def sel():
    return struct.unpack("<i", P.rd(f, P.SEL_G, 4))[0]
def hits(prefixes, want_idx=None):
    out = []
    try:
        with open(log) as fh:
            for ln in fh:
                for p in prefixes:
                    if ln.startswith(p):
                        if want_idx is not None and f"idx={unit} " not in ln:
                            continue
                        out.append(ln.rstrip())
                        break
    except OSError:
        pass
    return out
def wait_for(prefixes, want_idx=None, secs=8.0):
    t0 = time.time()
    while time.time() - t0 < secs:
        h = hits(prefixes, want_idx)
        if h: return h
        time.sleep(0.3)
    return []
press("Return"); time.sleep(1.0)   # blind-safe pane clear (M32: modal = key sink)

# --- step 1: walk to (45,7) with Up/Down arrows. (45,7) is the EMPIRICALLY proven
#     farm-legal tile: M33 try5's order landed there. (45,11) is NOT farm-legal
#     (mask&0x20 -> mode 0xa remap -> HASFARM abort). Fresh state: Former at (45,11),
#     2 steps away, mpused 0->3, 3 mp remain for the Space-executor's can-act gate. ---
x, y = pos()
print(f"start pos=({x},{y}) order={order()} mpused={mpused()} sel={sel()}")
for t in range(8):
    if (x, y) == (45, 7): break
    key = "Up" if y > 7 else "Down"
    press(key); time.sleep(0.5)
    nx, ny = pos()
    if (nx, ny) == (x, y):
        press("Return"); time.sleep(0.6)   # clear swallow-pane, retry
    else:
        print(f"moved ({x},{y})->({nx},{ny}) [{key}]")
    x, y = nx, ny
print(f"after move: pos=({x},{y}) mpused={mpused()} sel={sel()}")

# --- step 2: wait for the GAME to select our unit (selection is game-owned; under a
#     tracer our pokes never land — try3 proof). Then 'f' (issue) + Space (execute). ---
exec_seen = False
sel_arrived = False
t0 = time.time()
while time.time() - t0 < 30:
    if sel() == unit:
        sel_arrived = True
        break
    if hits(("NATIVESEL ",)):
        sel_arrived = True
        break
    time.sleep(0.5)
print(f"sel={sel()} arrived={sel_arrived} NATIVESEL hits: {hits(('NATIVESEL ',))[-3:]}")
if not sel_arrived:
    press("Return")   # maybe a pane is holding the cycle; clear and one last check
    time.sleep(1.2)
    sel_arrived = (sel() == unit)
    print(f"after clear: sel={sel()} arrived={sel_arrived}")
for attempt in range(1, 4) if sel_arrived else []:
    press("f"); time.sleep(0.9)
    o = order()
    terraf = hits(("TERRAF ",))
    print(f"attempt {attempt}: after 'f' order={o}; TERRAF hits: {terraf[-2:]}")
    if o != 4:
        press("Return"); time.sleep(1.0)
        continue
    press("space")                          # sel is the game's own -> no poke needed
    got = wait_for(("EXEC ",), want_idx=True, secs=12)
    if got:
        print("EXEC chain captured:", got[0])
        exec_seen = True
        break
    print(f"attempt {attempt}: order 4 landed but no EXEC idx={unit}; "
          f"SPACEH hits: {hits(('SPACEH ',))[-4:]}")
    press("Return"); time.sleep(1.0)
if not exec_seen:
    print("no EXEC on target; leaving gdb hits as-is for post-mortem")
time.sleep(1.5)   # let the executor finish its animation/chain
PY

kill -TERM $GPID 2>/dev/null
sleep 1.5
kill -CONT "$PID" 2>/dev/null
sleep 1
echo "--- post-state (no tracer) ---"
python3 scripts/m33_state.py "evidence/${TAG}_post.json" "$UNIT" >/dev/null
python3 - <<'PY'
import json, os
tag = os.environ["TAG"]
pre = json.load(open(f"evidence/{tag}_pre.json"))
post = json.load(open(f"evidence/{tag}_post.json"))
u0, u1 = pre["unit"], post["unit"]
print(json.dumps(dict(
  year=(pre["year"], post["year"]), sel=(pre["sel"], post["sel"]),
  energy=(pre["energy"], post["energy"]),
  order=(u0["order"], u1["order"]), mpused=(u0["mpused"], u1["mpused"]),
  pos=((u0["x"],u0["y"]),(u1["x"],u1["y"])),
  tile_addr=pre["tile_addr"],
  tile_plus8=(pre["tile"][16:24], post["tile"][16:24]),
  tile_full_diff=[f"+{i:02x}:{a}->{b}" for i,(a,b) in enumerate(zip(pre["tile"], post["tile"])) if a!=b],
), indent=1))
PY
echo "--- gdb hits ---"
grep -E "^(KEY|TERRAF|SOLOWRAP|EXEC|SETTILE|DEBIT|BCAST) " "$LOG" | head -60
echo "--- log tail (non-hit lines) ---"
grep -vE "^(KEY|TERRAF|SOLOWRAP|EXEC|SETTILE|DEBIT|BCAST) " "$LOG" | tail -8
