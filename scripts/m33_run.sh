#!/bin/bash
# M33: arm the terraform-order breakpoints, let the DRIVER press the hotkey and service
# the payment panes, then stop gdb and read the post-state through /proc/pid/mem.
# Pitfalls honored: gdb PID captured (never pkill -f in the same command), logs read only
# after kill -TERM gdb, kill -CONT the inferior afterwards, tracer held => driver runs
# --no-verify and all state reads happen outside the attach window.
set -u
cd /home/n100/reverse/smac
PID=$(pgrep -x terran.exe | head -1)
[ -z "$PID" ] && { echo "no terran.exe"; exit 1; }
ORDER=${ORDER:-r}
UNIT=${UNIT:-}
TAG=${TAG:-m33}
LOG=evidence/${TAG}_gdb.log
UFLAG=""
[ -n "$UNIT" ] && UFLAG="--unit $UNIT"

echo "--- pre-state ---"
python3 scripts/m33_state.py "evidence/${TAG}_pre.json" "$UNIT" || exit 1
UNIT=$(python3 -c "import json;print(json.load(open('evidence/${TAG}_pre.json'))['target'])")

# poke the selected-unit global BEFORE arming gdb: writes through /proc/pid/mem are
# silently unreliable while a tracer is attached (M33: readbacks lie under ptrace).
python3 - "$UNIT" <<'PY'
import struct, sys
sys.path.insert(0,'scripts')
import smac_play as P
pid,f = P.mem()
P.wr(f, P.SEL_G, struct.pack('<i', int(sys.argv[1])))
print('poked sel ->', struct.unpack('<i', P.rd(f, P.SEL_G,4))[0])
PY

gdb -batch -nx -x scripts/m33_order.gdb -p "$PID" > "$LOG" 2>&1 &
GPID=$!
sleep 5
NBP=$(grep -c "Breakpoint [0-9]* at" "$LOG")
if [ "$NBP" -lt 7 ]; then
  echo "ARM FAILED ($NBP/7 breakpoints)"; head -30 "$LOG"
  kill -TERM $GPID; sleep 1; kill -CONT "$PID" 2>/dev/null
  exit 2
fi
echo "armed ($NBP bps, gdb $GPID, game $PID) — driver presses '$ORDER' on rec$UNIT"

python3 scripts/smac_play.py --order "$ORDER" --unit "$UNIT" --tag "${TAG}_drv" \
       --no-verify --key-only --verbose 2>&1 | tail -25

kill -TERM $GPID
sleep 1.5
kill -CONT "$PID" 2>/dev/null
sleep 1
echo "--- post-state ---"
python3 scripts/m33_state.py "evidence/${TAG}_post.json" "$UNIT"
echo "--- gdb hits ---"
grep -E "^(KEY|DISP|TERRAF|TERRAPAY|DEBIT|STORE|BCAST) " "$LOG"
