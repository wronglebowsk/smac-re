#!/bin/bash
# M28: arm m28_order.gdb, fire one click at the given pixel, screenshot, stop gdb, print hits.
# usage: m28_click.sh X Y [logname]
set -u
cd /home/n100/reverse/smac
PID=$(pgrep -x terran.exe | head -1)
[ -z "$PID" ] && { echo "no terran.exe"; exit 1; }
LOG=${3:-evidence/m28_click.log}
GDB=${4:-scripts/m28_order.gdb}
gdb -batch -nx -x "$GDB" -p "$PID" > "$LOG" 2>&1 &
GPID=$!
sleep 6
if ! grep -q "Breakpoint 1 at" "$LOG"; then echo "ARM FAILED"; head -20 "$LOG"; kill -TERM $GPID; exit 2; fi
if ! grep -q "Hardware watchpoint 3" "$LOG"; then echo "WATCH ARMED FAILED"; grep -i "watchpoint\|cannot" "$LOG" | head; fi
echo "armed with $GDB"
python3 - "$1" "$2" <<'PY'
import sys, subprocess, os, time
x, y = int(sys.argv[1]), int(sys.argv[2])
subprocess.run(f'xdotool mousemove {x} {y} click 1', shell=True,
               env={**os.environ, "DISPLAY": ":99"})
time.sleep(2.0)
print(f"clicked {x},{y}")
PY
python3 scripts/smac_probe.py --tag m28 --save evidence/m28_last.png --quiet 2>&1 | tail -1
kill -TERM $GPID
sleep 1.5
kill -CONT "$PID" 2>/dev/null
echo "--- hits ---"
grep -E "^(MAPH|ACT|ORDER|SOLOWRAP|EXEC|W12)" "$LOG" | head -60
