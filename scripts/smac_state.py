#!/usr/bin/env python3
"""SMAC live-state reader via /proc/<pid>/mem (no gdb, no screenshots).

Prereq: `sudo sysctl -w kernel.yama.ptrace_scope=0` (Yama resets to 1 on EVERY boot;
without it both this reader and gdb attach fail with EACCES/Inappropriate ioctl).

Usage:
  python3 smac_state.py                 # human-readable snapshot
  python3 smac_state.py --json          # machine-readable
  python3 smac_state.py --watch 5       # poll every 5 s, print only on change
  python3 smac_state.py --read 0x985b00 # raw read of one address (u32)

Addresses are runtime VAs (image base 0x400000 == Ghidra VA). They live in .data's
BSS tail, so they exist ONLY at runtime — the file has no bytes there.
"""
import argparse, json, os, struct, subprocess, sys, time

# name -> (address, kind)   verified against a live game in M9
GLOBALS = {
    "year":        0x985B00,   # mission year (2101 at game start, +1/turn early game)
    "year_start":  0x92BF68,   # scenario start year (2100)
    "year_limit":  0x92BF6C,   # compared against `year` in FUN_0051e700 (end/scenario limit)
    "turn_no":     0x91F694,   # turns elapsed counter (incremented in the end-turn path)
    "player":      0x91B5B4,   # own/current faction index
    "player_mask": 0x985B10,   # bitmask of active factions
    "cur_player":  0x985DCC,   # player whose turn it is (same-loop index)
    "mode_flags":  0x985DC8,   # bit 0x10 = the "multiplayer-ish" branch in FUN_00522240; 0 in solo
    "turn_flags":  0x985AE8,   # turn-state flags (bit1 = end-turn in progress)
    "sema_done":   0x91F6C4,   # DONE bits per faction (MP semaphore; unused in solo)
    "sema_mp":     0x91F698,   # MP-only semaphore flag
    "n_bases":     0x985AF4,   # BASE count (was mislabelled n_factions; 37 in an 8-faction game, and it is the record count of the 304-byte base array at 0x95da10)
}


def find_pid():
    try:
        out = subprocess.check_output(["pgrep", "-x", "terran.exe"], text=True).split()
    except subprocess.CalledProcessError:
        return None
    return int(out[0]) if out else None


def read_u32(pid, addr):
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        m.seek(addr)
        return struct.unpack("<I", m.read(4))[0]


BASE_ARR, BASE_STRIDE = 0x95DA10, 304      # x +0, y +2, faction = LOW byte at +4
UNIT_ARR, UNIT_STRIDE = 0x933278, 52       # x/y +0/+2, TYPE u16 at +10, owner +14
MAX_UNIT_TYPES = 24                        # data/alpha.json rows; a record whose type is out
                                           # of range is an EMPTY STALE SLOT, not a unit


def counts(pid, player):
    """How many bases and units the PLAYER owns (M54f).

    The run checker could not see a defeat: trace_m54e40 ended with bases_ours 0 and every
    existing line still printed PASS, because the trace carried only n_bases (all factions).
    """
    out = {"bases_ours": 0, "units_ours": 0}
    if not isinstance(player, int):
        return out
    n = read_u32(pid, 0x985AF4)
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        for i in range(min(n, 512)):
            m.seek(BASE_ARR + i * BASE_STRIDE)
            rec = m.read(6)
            if len(rec) == 6 and rec[4] == player:
                out["bases_ours"] += 1
        for i in range(119):
            m.seek(UNIT_ARR + i * UNIT_STRIDE)
            rec = m.read(18)
            if len(rec) < 18:
                break
            x, y = struct.unpack("<hh", rec[0:4])
            t = struct.unpack("<H", rec[10:12])[0]
            if rec[14] == player and 0 <= x < 80 and 0 <= y < 80 and t < MAX_UNIT_TYPES:
                out["units_ours"] += 1
    return out


def snapshot(pid):
    out = {}
    for name, addr in GLOBALS.items():
        try:
            out[name] = read_u32(pid, addr)
        except Exception as e:
            out[name] = f"ERR:{type(e).__name__}"
    out["pid"] = pid
    try:
        out.update(counts(pid, out.get("player")))
    except Exception as e:
        out["bases_ours"] = f"ERR:{type(e).__name__}"
        out["units_ours"] = f"ERR:{type(e).__name__}"
    return out


def fmt(s):
    bits = []
    for k in ("year", "turn_no", "player", "cur_player", "n_factions"):
        bits.append(f"{k}={s.get(k)}")
    bits.append(f"mask={s.get('player_mask', 0):#06x}" if isinstance(s.get("player_mask"), int) else "mask=?")
    bits.append(f"mode={s.get('mode_flags', 0):#06x}" if isinstance(s.get("mode_flags"), int) else "mode=?")
    return "  ".join(bits)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--watch", type=float, default=0)
    ap.add_argument("--read", type=lambda x: int(x, 0))
    a = ap.parse_args()
    pid = a.pid or find_pid()
    if not pid or not os.path.exists(f"/proc/{pid}"):
        sys.exit("terran.exe not running")
    if a.read:
        print(f"{a.read:#x} = {read_u32(pid, a.read):#x} ({read_u32(pid, a.read)})")
        return
    if not a.watch:
        s = snapshot(pid)
        print(json.dumps(s, indent=2) if a.json else fmt(s))
        return
    prev = None
    while True:
        s = snapshot(pid)
        key = (s.get("year"), s.get("turn_no"), s.get("player_mask"))
        if key != prev:
            print(time.strftime("%H:%M:%S"), fmt(s), flush=True)
            prev = key
        time.sleep(a.watch)


if __name__ == "__main__":
    main()
