#!/bin/bash
# M34 v7: single traced run catching the whole Farm-order chain (setter -> store ->
# broadcast -> enqueue -> dispatch -> executor -> tile write / energy debit).
# Selection is game-owned and pokes under a tracer are ghosts, so we WAIT for the
# cycle to select our Former (poll 0x91b5bc + NATIVESEL bp), then press 'f' while the
# tracer holds the game between breakpoints (the X event is delivered when we continue,
# at which point the selection is exactly what we polled — the race closes itself).
# Pitfalls honored: no pokes while attached; gdb PID captured; log read after
# kill -TERM gdb; kill -CONT afterwards; state reads outside the attach window.
set -u
cd /home/n100/reverse/smac
PID=$(pgrep -x terran.exe | head -1)
[ -z "$PID" ] && { echo "no terran.exe"; exit 1; }
grep -q 'TracerPid:[[:space:]]*0' /proc/$PID/status || { echo "tracer attached — abort"; exit 1; }
TAG=${TAG:-m34v7}
export TAG
LOG=evidence/${TAG}_gdb.log

# --- target Former + pre-state (no tracer) ---
UNIT=$(python3 - <<'PY'
import sys, struct; sys.path.insert(0,'scripts')
import smac_play as P
pid,f = P.mem()
me = struct.unpack("<I", P.rd(f, 0x91B5B4, 4))[0]
units = P.rd(f, 0x933278, 300*52); classes = P.rd(f, 0x98ADB2, 1024*52)
for i in range(300):
    d = units[i*52:(i+1)*52]
    if d[14] == 0xFF: continue
    typ = struct.unpack("<H", d[10:12])[0]
    if (classes[typ*52] & 0xFF) == 9 and d[14] == me:
        print(i); break
PY
)
[ -z "$UNIT" ] && { echo "no Former owned by us"; exit 1; }
echo "target Former: rec$UNIT"
python3 scripts/m33_state.py "evidence/${TAG}_pre.json" "$UNIT" >/dev/null || exit 1

sed "s/__UNIT__/$UNIT/g" scripts/m34_chain.gdb > "evidence/${TAG}_chain.gdb"
gdb -batch -nx -x "evidence/${TAG}_chain.gdb" -p "$PID" > "$LOG" 2>&1 &
GPID=$!
sleep 5
NBP=$(grep -c "Breakpoint [0-9]* at" "$LOG")
if [ "$NBP" -lt 12 ]; then
  echo "ARM FAILED ($NBP/12 breakpoints)"; head -30 "$LOG"
  kill -TERM $GPID 2>/dev/null; sleep 1; kill -CONT "$PID" 2>/dev/null
  exit 2
fi
echo "armed ($NBP bps, gdb $GPID, game $PID)"

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
def press(k):
    if win: sh(f'xdotool windowfocus {win[0]}')
    sh(f'xdotool key --clearmodifiers {k}')
def sel():
    return struct.unpack("<i", P.rd(f, P.SEL_G, 4))[0]
def order():
    return P.rd(f, P.UNIT_ARR + unit*52 + 17, 1)[0]
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

press("Return"); time.sleep(1.0)
# --- wait for the game's cycle to select our Former (no pokes under tracer). If the
#     cycle sits still (sel=-1 or another unit), press '+' — the SMAC cycle-through-
#     units key (router case 0x2b -> FUN_00416dd0) — to walk it. ---
arrived = False
t0 = time.time()
last_sel = None
while time.time() - t0 < 45 and not arrived:
    if sel() == unit or hits(("NATIVESEL ",)):
        arrived = True; break
    s = sel()
    if s == last_sel:                     # cycle stuck: nudge it
        press("plus"); time.sleep(0.5)
    else:
        last_sel = s
    time.sleep(0.4)
print(f"sel={sel()} arrived={arrived} after {time.time()-t0:.1f}s")
if arrived:
    press("f")        # delivered on the next continue; selection is ours at that moment
    got = wait_for(("STORE ",), secs=10)
    print("STORE:", got[:2], "order now", order())
    # give the chain time to run sync or get pumped; then nudge the pump once
    time.sleep(3.0)
    if not hits(("DISP ", "EXEC ")):
        press("h")    # HOLD the selected unit: safe no-op that forces pump work
        time.sleep(3.0)
    print("chain so far:")
    for ln in hits(("NATIVESEL","TERRAF","STORE","BCAST","ENQ","DRAIN","DISP","SOLOWRAP","EXEC","SETTILE","DEBIT","REFUND"))[:40]:
        print("  ", ln)
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
echo "--- full gdb hits ---"
grep -E "^(NATIVESEL|TERRAF|STORE|BCAST|ENQ|DRAIN|DISP|SOLOWRAP|EXEC|SETTILE|DEBIT|REFUND) " "$LOG" | head -60
echo "--- log tail ---"
grep -vE "^(NATIVESEL|TERRAF|STORE|BCAST|ENQ|DRAIN|DISP|SOLOWRAP|EXEC|SETTILE|DEBIT|REFUND) |Breakpoint|New LWP|^\[|debuginfod|Enable|Answering|This GDB" "$LOG" | tail -6
