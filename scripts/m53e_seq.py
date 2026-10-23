#!/usr/bin/env python3
"""M53e UI sequence driver: bar-label sweep (phase 1) and mode-5 hunt (phase 2).

Runs while scripts/m53e_drive.py holds gdb attached. Every action is stamped into a
timeline file together with a /proc/mem readback of the base queue fields, so the gdb
log can be correlated by CONTENT (gdb's printf is block-buffered, so line order in the
log is not trustworthy).

Chooser bar labels were label-verified by crop-OCR + vision on the live chooser
(evidence/m53e_grid_pre.txt): HELP ~160 | OK ~285 | REPLACE ~397 | INSERT ~497 |
DELETE ~602 | CANCEL ~692, bar row y = 343.  Icon grid: cols 128/255/383/510/638,
icon rows y = 60/160/260.  QUEUE rows: x 185, y = 437 + 14*(row-1), rows 1..8.
"""
import argparse, os, struct, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P  # noqa: E402

BARS = [("HELP", 160), ("OK", 285), ("REPLACE", 397), ("INSERT", 497),
        ("DELETE", 602), ("CANCEL", 692)]
BAR_Y = 343
ROWS = {r: (185, 437 + 14 * (r - 1)) for r in range(1, 9)}
# item icon cells in the currently-displayed group (unit group, row 2)
ITEMS = {"ScoutPatrol": (128, 160), "ColonyPod": (255, 160), "Formers": (383, 160),
         "ProbeTeam": (510, 160), "Creche": (638, 160)}
QUEUE_BOX = (143, 425, 105, 120)
PANE = 0x6a9480                      # the base-pane UI object (MODE printf, evidence/m53e2_watch.log:72)
SEL_FIELD = PANE + 0xa1c + 0xa774    # chooser result item id; -1 = nothing selected
MODE_FIELD = PANE + 0xa1c + 0xa778   # == pane+0xb194, the value 0x4186ec dispatches on
SLOT_FIELD = PANE + 0x3ff5c


def chooser_fields(pid):
    fd = os.open(f"/proc/{pid}/mem", os.O_RDONLY)
    v = struct.unpack("<3i", os.pread(fd, 12, SEL_FIELD))
    os.close(fd)
    return v  # (sel_item_id, mode, slot)


BAR_BLUE = (103, 91, 181)   # the chooser's flat bar row, sampled live (evidence/m53e_grid_pre.txt)


def bar_px(png=None):
    """Pixel at the HELP bar body (160,343): BAR_BLUE iff the chooser overlay is up."""
    from PIL import Image
    png = png or P.freeze("m53e_seq")
    return Image.open(png).convert("RGB").getpixel((160, 343))


def chooser_open(png=None):
    r, g, b = bar_px(png)
    return abs(r - BAR_BLUE[0]) < 24 and abs(g - BAR_BLUE[1]) < 24 and abs(b - BAR_BLUE[2]) < 24


def base_fields(pid, name="Climactic Research"):
    fd = os.open(f"/proc/{pid}/mem", os.O_RDONLY)
    nb = struct.unpack("<I", os.pread(fd, 4, 0x985af4))[0]
    for i in range(nb):
        a = 0x95da10 + i * 0x130
        if os.pread(fd, 20, a + 0x13).split(b"\0")[0].decode("latin1") == name:
            rec = struct.unpack("<13I", os.pread(fd, 0x34, a + 0x40))
            slot = None
            os.close(fd)
            return i, a, rec
    os.close(fd)
    return None, None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["1", "2", "2b", "3", "4"], default="1")
    ap.add_argument("--tag", default="m53e1")
    ap.add_argument("--skip", type=int, default=0, help="skip the first N steps (resume)")
    a = ap.parse_args()
    P.WIN = P.find_window()
    P.focus()
    pid = int(subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True,
                             text=True).stdout.split()[0])
    tl = open(f"evidence/{a.tag}_timeline.txt", "w")

    def log(msg):
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        tl.write(line + "\n"); tl.flush()

    def snap(note):
        idx, addr, rec = base_fields(pid)
        log(f"{note} idx={idx} f40={rec[0]} f44={rec[1]} f48={rec[2]} f4c={rec[3]} "
            f"q={ [hex(v) for v in rec[4:13]] }")
        return rec

    def click_wait(xy, s=1.35):
        P.click(xy); time.sleep(s)

    def queue_ocr():
        w = P.ocr_crop(P.freeze("m53e_q"), QUEUE_BOX, "m53e_q", scale=6)
        w = sorted(w, key=lambda t: (t[2], t[1]))
        s = " ".join(t[0] for t in w)
        log(f"QUEUE-OCR: {s[:220]}")
        return s

    def ensure_closed():
        for _ in range(3):
            if not chooser_open():
                return True
            click_wait((692, BAR_Y), 1.2)
        return not chooser_open()

    if a.phase == "4":
        def closedown():
            for _ in range(6):
                if chooser_open():
                    click_wait((692, BAR_Y), 1.3); continue
                w = P.ocr_fast(P.freeze("m53e_cd"))
                tx = P.text_of(w).lower()
                if "climactic" in tx:
                    return True
                c = [x for x in w if x[0].lower().startswith("cancel")]
                if c:
                    click_wait((int(c[0][1]), int(c[0][2])), 1.3); continue
                return False
            return False

        def session(row, item, barname, exit_after=True):
            bx = dict(BARS)[barname]
            if chooser_open():
                click_wait((285, BAR_Y), 1.4)          # OK: exit cleanly (mode 0, no restore)
            if not closedown():
                log(f"{barname}: could not reach the base pane"); return
            click_wait(ROWS[row], 1.4)
            if not chooser_open():
                log(f"{barname}: row{row} click did not open the chooser"); return
            click_wait(ITEMS[item], 0.9)
            click_wait((bx, BAR_Y), 1.5)
            log(f"4: row{row} {item} -> {barname}: open={chooser_open()} mode_px={bar_px()}")
            snap("state")
            if exit_after and chooser_open():
                click_wait((285, BAR_Y), 1.4)
                log(f"4:   exited via OK: open={chooser_open()}")
                snap("after-OK")

        if closedown():
            log("4: base pane reached")
        session(1, "ScoutPatrol", "REPLACE")           # count 0: nothing to replace
        session(1, "ScoutPatrol", "INSERT")            # commit an insert
        session(1, "ColonyPod", "REPLACE")             # count 1, slot 1: replace in place?
        session(1, "ScoutPatrol", "INSERT")            # insert ahead of it
        if chooser_open():
            click_wait((285, BAR_Y), 1.4)
        closedown()
        queue_ocr(); snap("final")
        return 0

    steps = []
    if a.phase == "3":
        steps = [("selbar", 1, "ScoutPatrol", "REPLACE"), ("ocr",),
                 ("selbar", 2, "ProbeTeam", "REPLACE"),
                 ("selbar", 1, "ColonyPod", "REPLACE"), ("ocr",),
                 ("selbar", 1, "ScoutPatrol", "INSERT"), ("ocr",),
                 ("selbar", 3, "Formers", "REPLACE"), ("ocr",)]
    elif a.phase == "2b":
        CELLS = [(128, 160), (255, 160), (383, 160), (510, 160), (638, 160),
                 (128, 60), (255, 60), (383, 60), (510, 60), (638, 60),
                 (128, 260), (255, 260), (383, 260)]
        order = ["REPLACE", "INSERT", "DELETE", "OK", "CANCEL", "HELP"]  # HELP last: it opens
        # the unit-design pane, which needs its own CANCEL click to get back
        byname = dict(BARS)
        for _name in order:
            steps.append(("barsweep2b", _name, byname[_name], CELLS))
    elif a.phase == "1":
        for name, x in BARS:
            steps.append(("bar", name, x))
    else:
        steps = [("build", 1, "ScoutPatrol"), ("build", 2, "ColonyPod"),
                 ("ocr",), ("pick_bar", 1, "ProbeTeam", "INSERT"),
                 ("pick_bar", 1, "ScoutPatrol", "OK"),
                 ("pick_bar", 1, "ColonyPod", "REPLACE"),
                 ("pick_bar", 1, "ProbeTeam", "DELETE"),
                 ("pick_bar", 1, "ScoutPatrol", "HELP"),
                 ("pick_bar", 2, "ProbeTeam", "INSERT"),
                 ("ocr",), ("pick_bar", 1, "Creche", "CANCEL")]

    n = 0
    for st in steps:
        n += 1
        if n <= a.skip:
            continue
        if not ensure_closed():
            log("ABORT: chooser will not close"); return 1
        if st[0] == "selbar":
            row, item, bar = st[1], st[2], st[3]
            bx = dict(BARS)[bar]
            if not chooser_open():
                click_wait(ROWS[row], 1.4)
                if not chooser_open():
                    log(f"step {n}: {bar} row{row}: chooser did not open"); continue
            click_wait(ITEMS[item], 0.9)
            click_wait((bx, BAR_Y), 1.5)
            log(f"step {n}: SELBAR row{row} {item} -> BAR {bar} x={bx} open={chooser_open()}")
            snap("state")
            continue
        if st[0] == "barsweep2b":
            name, x, cells = st[1], st[2], st[3]
            if not chooser_open():                      # re-open via a QUEUE-row click
                click_wait(ROWS[1], 1.4)
                if not chooser_open():
                    log(f"step {n}: BAR {name}: could not open the chooser"); continue
            sel = mode = slot = None
            for c in cells:
                click_wait(c, 0.7)
                sel, mode, slot = chooser_fields(pid)
                if sel != -1:
                    break
            log(f"step {n}: BAR {name} x={x} selected item={sel} slot={slot} mode_before={mode}")
            click_wait((x, BAR_Y), 1.5)
            sel2, mode2, slot2 = chooser_fields(pid)
            log(f"step {n}:  -> after BAR {name}: mode_field={mode2} slot={slot2} "
                f"sel={sel2} chooser_open={chooser_open()}")
            snap("state")
            continue
        if st[0] == "ocr":
            if chooser_open():
                click_wait((692, BAR_Y), 1.3)
            queue_ocr(); snap("state"); continue
        if st[0] == "bar":
            name, x = st[1], st[2]
            click_wait(ROWS[1], 1.4)
            if not chooser_open():
                log(f"step {n}: row-1 click did NOT open the chooser barpx={bar_px()}"); continue
            click_wait((x, BAR_Y), 1.5)
            still = chooser_open()
            log(f"step {n}: BAR {name} x={x} chooser_still_open={still} barpx={bar_px()}")
            snap("state")
            if still:
                click_wait((692, BAR_Y), 1.2)
            continue
        if st[0] == "build":
            row, item = st[1], st[2]
            click_wait(ROWS[row], 1.4)
            if not chooser_open():
                log(f"step {n}: row-{row} click did not open chooser"); continue
            click_wait(ITEMS[item], 0.9)
            click_wait((397, BAR_Y), 1.5)
            log(f"step {n}: BUILD row{row} item={item} via REPLACE")
            snap("state")
            ensure_closed()
            continue
        if st[0] == "pick_bar":
            row, item, bar = st[1], st[2], st[3]
            bx = dict(BARS)[bar]
            click_wait(ROWS[row], 1.4)
            if not chooser_open():
                log(f"step {n}: row-{row} click did not open chooser"); continue
            click_wait(ITEMS[item], 0.9)
            click_wait((bx, BAR_Y), 1.5)
            still = chooser_open()
            log(f"step {n}: PICK {item} row{row} then BAR {bar} x={bx} still_open={still} barpx={bar_px()}")
            snap("state")
            if still:
                click_wait((692, BAR_Y), 1.2)
            continue
    snap("final")
    tl.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
