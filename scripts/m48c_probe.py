#!/usr/bin/env python3
"""M48c probe: catch the store that zeroes our base's mineral accumulator, with NO OCR.

m48a/e/f all showed base+0x40 (0x962fd0) go 200 -> 0 at the round boundary while the
game announced "The minerals output of Climactic Research is not sufficient to support
Scout Patrol unit. The unit has been disbanded."  The driver-based runs were useless
for this: tesseract hogged 4 cores (pitfall 5) so a round took 12+ min, and gdb's log
came back with zero hits.  This probe arms scripts/m48c_minwatch.gdb (4 hw watchpoints
+ 5 conditioned int3 sites) and services panes BY COLOUR ONLY -- freeze + pixel scan,
no tesseract -- so the game runs at full speed.

Pane rule measured today: the OPERATIONS DIRECTOR end-turn confirm has its OK bar at
y~222-231 with the "Yes, end the turn." row at y~190-205 (fill 103,91,181) 26 px above
it, and the DEFAULT row is Cancel (highlight fill 120,164,212, unreadable to OCR), so
the click order is (bar_x, bar_y-26) then (bar_x, bar_y).  Panes whose row above the
lowest blue band is NOT that blue (news popups, the two-button "unit disbanded" pane)
just get the band's RIGHTMOST blue run -- the OK button, never the gap between buttons.
"""
import json
import os
import signal
import struct
import subprocess
import sys
import time

sys.path.insert(0, 'scripts')
import smac_play as P                      # noqa: E402
from m44_idle import rightmost_blue_run       # noqa: E402
from m48_minerals import hud_up               # noqa: E402  (defined there, not in m44_idle)
from PIL import Image                      # noqa: E402

PID = 914079
BASE = 0x962f90
EVID = 'evidence'
FD = os.open(f'/proc/{PID}/mem', os.O_RDONLY)
ROW_BLUE = (103, 91, 181)


def i32(addr):
    return struct.unpack('<i', os.pread(FD, 4, addr))[0]


def state():
    return dict(year=i32(0x985b00), turn=i32(0x985afc), cur=i32(0x985dcc),
                nb=i32(0x985af4), min40=i32(BASE + 0x40), q50=i32(BASE + 0x50),
                d0=i32(BASE + 0xd0), c0=i32(BASE + 0xc0), f0=i32(BASE + 0xf0),
                e0=i32(BASE + 0xe0), mir98=i32(BASE + 0x98), nrg3=i32(0x953884),
                mask=i32(0x985b10))


def px(png, x, y):
    return Image.open(png).convert('RGB').load()[x, y]


def dismiss(png):
    """Colour-only pane dismissal. Returns True if a click was made."""
    ob = rightmost_blue_run(png, band=(240, 150, 560, 430))
    if not ob:
        return False
    bx, by = ob
    try:
        r, g, b = px(png, bx, by - 26)
    except Exception:
        r, g, b = (0, 0, 0)
    row_is_option = abs(r - ROW_BLUE[0]) < 45 and abs(g - ROW_BLUE[1]) < 45 \
        and abs(b - ROW_BLUE[2]) < 55
    if row_is_option:
        P.click((bx, by - 26))
        time.sleep(1.2)
    P.click((bx, by))
    time.sleep(0.8)
    return True


def main():
    budget = float(sys.argv[1]) if len(sys.argv) > 1 else 280.0
    # leftover runners first (pitfall 5: one OCR job at a time, and none here at all)
    subprocess.run(['pkill', '-INT', '-f', '[m]48_minerals.py'])
    time.sleep(2)
    tracer = subprocess.run(['grep', 'TracerPid', f'/proc/{PID}/status'],
                            capture_output=True, text=True).stdout
    assert 'TracerPid:\t0' in tracer, tracer
    log = f'{EVID}/m48c_minwatch.log'
    rec = {'t': time.strftime('%F %T'), 'events': [], 'polls': []}

    w = os.open(f'/proc/{PID}/mem', os.O_RDWR)
    os.pwrite(w, struct.pack('<i', 200), BASE + 0x40)
    rec['poke_min40'] = struct.unpack('<i', os.pread(w, 4, BASE + 0x40))[0]
    os.close(w)
    rec['events'].append(f'poked base+0x40 -> {rec["poke_min40"]}')

    with open(log, 'wb') as lf:
        g = subprocess.Popen(['gdb', '-batch', '-nx', '-x', 'scripts/m48c_minwatch.gdb',
                              '-p', str(PID)], stdout=lf, stderr=subprocess.STDOUT)
    rec['gdb_pid'] = g.pid
    time.sleep(4)
    t0 = time.time()
    y0 = state()['year']
    rec['start'] = state()
    while time.time() - t0 < budget:
        s = state()
        rec['polls'].append([round(time.time() - t0, 1), s['year'], s['cur'], s['min40'],
                             s['q50'], s['d0']])
        if s['year'] != y0:
            rec['events'].append(f'year {y0}->{s["year"]} (cur={s["cur"]} min40={s["min40"]})')
            y0 = s['year']
            time.sleep(12)
            break
        png = P.freeze('m48c_probe')
        if dismiss(png):
            rec['events'].append('dismissed pane by colour')
            time.sleep(1.5)
            continue
        if s['cur'] == 3 and hud_up(png) and time.time() - t0 > 15:
            P.click(P.TURN_BTN)
            rec['events'].append('clicked TURN COMPLETE')
        time.sleep(6)
    rec['end'] = state()
    g.send_signal(signal.SIGINT)
    t1 = time.time()
    while time.time() - t1 < 45:
        try:
            if b'detached' in open(log, 'rb').read():
                break
        except Exception:
            pass
        time.sleep(2)
    rec['gdb_returncode'] = g.poll()
    json.dump(rec, open(f'{EVID}/m48c_probe.json', 'w'), indent=1)
    print(json.dumps(rec['events']))
    print('start', rec['start'])
    print('end  ', rec['end'])


if __name__ == '__main__':
    main()
