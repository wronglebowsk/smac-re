#!/bin/bash
# M32: arm the order-setter breakpoints, press the order hotkeys one by one,
# snapshot the selected-unit record between presses, then stop gdb and flush logs.
# Pitfalls honored: gdb PID captured (never pkill -f), read log only after kill -TERM,
# kill -CONT the inferior afterwards.
set -u
cd /home/n100/reverse/smac
PID=$(pgrep -x terran.exe | head -1)
[ -z "$PID" ] && { echo "no terran.exe"; exit 1; }
LOG=${LOG:-evidence/m32_keys.log}
STATE=${STATE:-evidence/m32_keys_state.txt}
read -r -a KEYS <<< "${M32_KEYS:-h slash shift+m shift+s shift+k period o n shift+e shift+b q bracketright bracketleft underscore shift+g r m k d f slash}"
: > "$STATE"
gdb -batch -nx -x scripts/m32_keys.gdb -p "$PID" > "$LOG" 2>&1 &
GPID=$!
sleep 6
NBP=$(grep -c "Breakpoint [0-9]* at" "$LOG")
if [ "$NBP" -lt 29 ]; then
  echo "ARM FAILED ($NBP/24 breakpoints)"; head -30 "$LOG"
  kill -TERM $GPID; sleep 1; kill -CONT "$PID" 2>/dev/null
  exit 2
fi
echo "armed ($NBP bps, gdb $GPID, game $PID)"
WIN=$(xdotool search --name "Sid Meier" | head -1)
[ -z "$WIN" ] && { echo "no game window"; kill -TERM $GPID; kill -CONT "$PID"; exit 3; }
xdotool windowfocus "$WIN"
sleep 0.5
for K in "${KEYS[@]}"; do
  echo ">>> $K $(date +%H:%M:%S)" >> "$STATE"
  xdotool key --clearmodifiers "$K"
  sleep 1.2
  python3 scripts/m26_poke.py show 2>&1 | head -1 >> "$STATE"
done
kill -TERM $GPID
sleep 1.5
kill -CONT "$PID" 2>/dev/null
echo "--- per-key selected-unit state ---"
cat "$STATE"
echo "--- hits ---"
grep -E "^(KEY|DISP|TERRAF|HOLD|BASEORD|CANCEL|JOINBASE|ABILITY|AREA10|CONVOY|SENTRY|ROUTE8|ROADTO|DESIG|UPGRADE|GIVE|UNLOAD|FUNDBASE|OBLIT|RUNORDER|BOMBARD|CLEAR|SOLOWRAP|PANEMODE) " "$LOG"
