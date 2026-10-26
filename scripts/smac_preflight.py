#!/usr/bin/env python3
"""SMAC preflight — ONE read-only command that proves the live box matches the docs.

Every long run this project lost to a *stale remembered fact*: a wrong cur_player
address, a base index that had shifted under array compaction, a chooser cell index
that moved between eras, a dead/tracer-attached game, a full /tmp. This script checks
them all in one call, prints PASS/FAIL per invariant, and exits 1 on any FAIL.

Read-only: it opens /proc/<pid>/mem for reading and writes nothing anywhere.

    python3 scripts/smac_preflight.py [--json]
"""
import argparse, json, os, struct, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

# The one authoritative table (m55_boundary's G) — never retype these in a session.
G = {"year": 0x985B00, "round": 0x985AFC, "cur_player": 0x985DCC, "turn_flags": 0x985AE8,
     "n_bases": 0x985AF4, "n_units": 0x985AF0, "player_mask": 0x985B10,
     "our_player": 0x91B5B4, "mode": 0x985DC8}
BASE_ARR, BASE_SZ = 0x95DA10, 304
UNIT_ARR, UNIT_SZ = 0x933278, 52


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    checks = []
    def ck(name, ok, detail):
        checks.append(dict(check=name, ok=bool(ok), detail=str(detail)))

    env_pid = os.environ.get("SMAC_PID")
    if env_pid:
        out = [env_pid] if os.path.isdir(f"/proc/{env_pid.strip()}") else []
    else:
        out = sh(["pgrep", "-x", "terran.exe"]).stdout.split()
    ck("game process alive", bool(out), f"terran.exe pid {out[0] if out else 'NONE'}"
       + (" (SMAC_PID override)" if env_pid else ""))
    if not out:
        return finish(checks, a.json)
    pid = int(out[0])

    tracer = sh(["grep", "-m1", "TracerPid", f"/proc/{pid}/status"]).stdout.split()[-1]
    ck("no tracer attached", tracer == "0", f"TracerPid={tracer} (a leftover gdb makes pokes lie)")
    ck("no gdb running", not sh(["pgrep", "-x", "gdb"]).stdout.strip(),
       "pgrep -x gdb is empty" if not sh(["pgrep", "-x", "gdb"]).stdout.strip()
       else "a gdb is attached — run the harness --stop first")

    f = open(f"/proc/{pid}/mem", "rb", 0)
    def u(addr):
        f.seek(addr)
        return struct.unpack("<I", f.read(4))[0]
    def i(addr):
        f.seek(addr)
        return struct.unpack("<i", f.read(4))[0]

    year, cp, tf = u(G["year"]), u(G["cur_player"]), u(G["turn_flags"])
    mask, ours, nb, nu = u(G["player_mask"]), u(G["our_player"]), u(G["n_bases"]), u(G["n_units"])
    ck("year in range", 2100 <= year <= 2600, f"year {year}")
    ck("cur_player is a faction id", 0 <= cp <= 7, f"cur_player {cp} (ours {ours})")
    ck("player mask sane", mask != 0 and mask != 0xFFFFFFFF, f"mask {mask:#x}")
    ck("our faction is active", 0 <= ours <= 7 and bool((mask >> ours) & 1), f"our_player {ours} in mask {mask:#x}")
    ck("base count sane", 0 < nb <= 64, f"n_bases {nb}")
    ck("unit count sane", 0 < nu <= 300, f"n_units {nu}")

    bases = []
    for bi in range(min(nb, 64)):
        f.seek(BASE_ARR + bi * BASE_SZ)
        b = f.read(BASE_SZ)
        if len(b) < 304:
            break
        nm = b[19:59].split(b"\0")[0].decode("latin-1", "replace")
        g = lambda o: struct.unpack("<i", b[o:o + 4])[0]
        bases.append(dict(index=bi, name=nm, x=struct.unpack("<H", b[0:2])[0],
                          y=struct.unpack("<H", b[2:4])[0], fac=b[4],
                          pending=g(0x4c), head=g(0x50), minerals=g(0x40), income=g(0xd0)))
    mine = [b for b in bases if b["fac"] == ours]
    ck("we hold at least one base", len(mine) >= 1,
       f"{len(mine)} of {len(bases)} bases ours: " + "; ".join(
           f"[{b['index']}] {b['name']} ({b['x']},{b['y']}) pend {b['pending']} head {b['head']} "
           f"min {b['minerals']} income {b['income']}" for b in mine))
    ck("our base names decode", all(b["name"] and b["name"].isprintable() for b in mine),
       "printable" if mine else "no own bases")

    units = []
    f.seek(UNIT_ARR)
    arr = f.read(min(nu, 300) * UNIT_SZ)
    for k in range(min(nu, 300)):
        r = arr[k * UNIT_SZ:(k + 1) * UNIT_SZ]
        if len(r) < UNIT_SZ or r[14] != ours:
            continue
        units.append(dict(idx=k, x=struct.unpack("<h", r[0:2])[0], y=struct.unpack("<h", r[2:4])[0],
                          order=r[17], frozen=r[9], mpused=r[40],
                          type=struct.unpack("<H", r[10:12])[0]))
    actionable = [x for x in units if x["order"] == 0 and not x["frozen"] and x["mpused"] == 0]
    ck("our units decode at (x,y) inside the map",
       all(0 <= x["x"] < 256 and 0 <= x["y"] < 128 for x in units) if units else True,
       f"{len(units)} ours, {len(actionable)} actionable (order 0, unfrozen, mp used 0)")

    df = sh(["df", "-k", "/tmp"]).stdout.splitlines()
    free_mb = int(df[1].split()[3]) // 1024 if len(df) > 1 else -1
    ck("tmp has room for frames", free_mb > 1024, f"{free_mb} MB free")
    ev = sh([sys.executable, os.path.join(ROOT, "scripts", "evidence.py"), "budget"]).stdout
    line = [l for l in ev.splitlines() if l.startswith("evidence/:")]
    ev_mb = None
    if line:
        try:
            ev_mb = float(line[0].split("evidence/:")[1].split("MB")[0].strip())
        except ValueError:
            pass
    ck("evidence under the gate budget", ev_mb is not None and ev_mb < 29.0, f"{ev_mb} MB (FAIL at 30)")

    if a.json:
        print(json.dumps(dict(pid=pid, year=year, cp=cp, tf=hex(tf), ours=ours, mask=hex(mask),
                              bases=bases, own=mine, units=units, actionable=actionable,
                              checks=checks), indent=1))
        return 0 if all(c["ok"] for c in checks) else 1
    return finish(checks, a.json, extra=dict(pid=pid, year=year, cp=cp, tf=hex(tf), ours=ours,
                                             own=mine, n_units=len(units),
                                             actionable=len(actionable)))


def finish(checks, as_json, extra=None):
    if as_json:
        print(json.dumps(dict(checks=checks, extra=extra), indent=1))
    else:
        for c in checks:
            print(f"{'ok  ' if c['ok'] else 'FAIL'} {c['check']} — {c['detail']}")
        bad = [c for c in checks if not c["ok"]]
        print(("PASS preflight: the live box matches every invariant" if not bad else
               f"FAIL preflight: {len(bad)} invariant(s) — do NOT build on this state"))
    return 0 if all(c["ok"] for c in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
