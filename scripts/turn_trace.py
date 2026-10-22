#!/usr/bin/env python3
"""Sample the turn-loop state every N seconds while smac_play.py advances turns.

Answers "what does a turn actually consist of" with evidence instead of a story:
  year 0x985B00, cur_player 0x985DCC, turn_flags 0x985AE8, n_bases 0x985AF4

Usage:
  python3 scripts/turn_trace.py --turns 20 --interval 0.25
Writes evidence/m30_turn_trace.jsonl and prints a per-turn transition summary.
"""
import argparse, json, os, struct, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "evidence")
G = {"year": 0x985B00, "cur": 0x985DCC, "tf": 0x985AE8, "nb": 0x985AF4, "player": 0x91B5B4}


def get_pid():
    out = subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else None


def reader(pid):
    f = open(f"/proc/{pid}/mem", "rb", 0)

    def read(a):
        f.seek(a)
        return struct.unpack("<I", f.read(4))[0]
    return read


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--turns", type=int, default=20)
    ap.add_argument("--interval", type=float, default=0.25)
    ap.add_argument("--timeout", type=float, default=100)
    a = ap.parse_args()

    pid = get_pid()
    if not pid:
        sys.exit("no terran.exe")
    rd = reader(pid)
    os.makedirs(EVID, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    trace = os.path.join(EVID, f"m30_turn_trace.jsonl")

    drv = subprocess.Popen([sys.executable, os.path.join(ROOT, "scripts", "smac_play.py"),
                            "--turns", str(a.turns), "--timeout", str(a.timeout)],
                           cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    t0 = time.time()
    samples = []
    with open(trace, "w") as out:
        while drv.poll() is None:
            try:
                rec = {"t": round(time.time() - t0, 3), "year": rd(G["year"]), "cur": rd(G["cur"]),
                       "tf": rd(G["tf"]), "nb": rd(G["nb"]), "own": rd(G["player"])}
            except Exception as e:
                break
            if not samples or any(rec[k] != samples[-1][k] for k in ("year", "cur", "tf")):
                samples.append(rec)
                out.write(json.dumps(rec) + "\n"); out.flush()
            time.sleep(a.interval)
    log = drv.stdout.read()
    drv.wait()

    # summarise: group by year, list the cur_player order inside each year
    print("driver log:")
    print(log.rstrip())
    seq = []
    for s in samples:
        if not seq or seq[-1][0] != s["year"]:
            seq.append((s["year"], [s["cur"]], [s["tf"]], s["t"]))
        else:
            if s["cur"] != seq[-1][1][-1]:
                seq[-1][1].append(s["cur"])
            seq[-1][2].append(s["tf"])
    print(f"\n{len(seq)} year-blocks, {len(samples)} state changes over {samples[-1]['t'] if samples else 0:.1f}s")
    for y, curs, tfs, t in seq:
        print(f"  {y}: players {'->'.join(map(str, curs))}  tf={[hex(v) for v in tfs[:3]]}"
              f"{'...' if len(tfs) > 3 else ''}  @{t:.1f}s")
    with open(os.path.join(EVID, "m30_summary.txt"), "w") as f:
        f.write(log + "\n")
        for y, curs, tfs, t in seq:
            f.write(f"{y}: {'->'.join(map(str, curs))} tf={[hex(v) for v in tfs]} @{t:.1f}s\n")


if __name__ == "__main__":
    main()
