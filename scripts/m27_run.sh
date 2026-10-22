#!/bin/bash
# M27: arm the solo-wrapper breakpoints, press arrow keys, then stop gdb and flush its log.
set -u
cd /home/n100/reverse/smac
PID=$(pgrep -x terran.exe | head -1)
[ -z "$PID" ] && { echo "no terran.exe"; exit 1; }
LOG=${1:-evidence/m27_solowrap2.log}
gdb -batch -nx -x scripts/m27_solowrap.gdb -p "$PID" > "$LOG" 2>&1 &
GPID=$!
sleep 6
if ! grep -q "Breakpoint 1 at" "$LOG"; then echo "ARM FAILED"; cat "$LOG" | head -20; kill -TERM $GPID; exit 2; fi
echo "armed (gdb $GPID)"
for i in 1 2 3; do
  python3 scripts/smac_probe.py --key "${2:-Right}" --quiet >/dev/null 2>&1
  sleep 2
  python3 scripts/m26_poke.py show 2>&1 | head -1
done
kill -TERM $GPID
sleep 1.5
kill -CONT "$PID" 2>/dev/null
echo "--- hits ---"
grep -E "SOLOWRAP|EXEC|SETTILE" "$LOG" | head -40
