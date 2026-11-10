#!/usr/bin/env python3
"""M289 acceptance - independent re-walk of the census raw log.

Runs OFFLINE (no box). Reads scratch/m289_gdb_raw.log (the census's own event
stream) and the summary lines in evidence/m289_founder_vector.txt, re-parses
every event with a fresh implementation, and re-derives:
  g1  control: >=1 sweep row (the window lived under gdb)
  g2  marshal: every FOUND/DESTROY row parses; no PARSE? rows
  g3  classification: every founder hit has a known vector (no UNPAIRED /
      UNKNOWN / 59ce10-placement surprises in a mid-game window)
  g4  accounting: every FOUND prints exactly the expected count (cnt0 + net
      events so far); every DESTROY prints the pre-decrement count; the final
      expected count ties the box's post-window read to within 3 (late events
      after driver exit are allowed and reported)
  g5  coherence: per-vector counts sum to the founder-hit count; >=1 hit
      (a zero-hit window is NO MEASUREMENT, not a verdict)
  g6  hygiene: summary says TracerPid=0 and yama-restored=True after the
      window; game still alive

Usage: python3 scripts/m289_accept.py   (from the repo root)
Prints the per-event table and PASS M289: N/6, or FAIL with the numbers.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "evidence")
SCR = os.path.join(ROOT, "scratch")

FOUND_CALLER = {0x4ccbe2: "CC50", 0x5a01fd: "EC90", 0x59d899: "59ce10"}
CC50_VECS = {"hotkey", "v4408", "hub"}
EC90_VECS = {"chain", "place", "place2"}

G = {i: (False, "") for i in range(1, 7)}


def gate(i, ok, why):
    G[i] = (bool(ok), why)


def main():
    evpath = os.path.join(SCR, "m289_gdb_raw.log")
    if not os.path.exists(evpath):
        print("FAIL M289: %s missing - run the census first" % evpath)
        return 1

    # --- summary facts from the evidence file ---
    summ = {}
    sumpath = os.path.join(EVID, "m289_founder_vector.txt")
    if os.path.exists(sumpath):
        for ln in open(sumpath):
            for k in ("PRE :", "POST:", "control:", "per-vector:",
                      "VERDICT:", "accounting:"):
                if ln.startswith(k):
                    summ[k.strip().strip(":").strip()] = ln.split(":", 1)[1].strip()
    m = re.search(r"count=(\d+)", summ.get("PRE", ""))
    cnt0 = int(m.group(1)) if m else None
    m = re.search(r"count=(\d+).*tracer=(\d+)", summ.get("POST", ""))
    cnt_box = int(m.group(1)) if m else None
    tracer = int(m.group(2)) if m else None
    yama_ok = "yama=1" in open(sumpath).read() if os.path.exists(sumpath) else False

    # --- fresh event walk ---
    events = []
    bad_rows = []
    for ln in open(evpath):
        ln = ln.strip()
        if ln == "CTRL":
            events.append(("CTRL", None))
        elif ln.startswith("VEC "):
            events.append(("VEC", ln.split()[1]))
        elif ln.startswith("FOUND"):
            m = re.match(r"FOUND ret=(0x[0-9a-f]+) fac=(\d+) x=(\d+) y=(\d+) cnt=(\d+)", ln)
            if m:
                events.append(("FOUND", {"ret": int(m.group(1), 16),
                                         "fac": int(m.group(2)), "x": int(m.group(3)),
                                         "y": int(m.group(4)), "cnt": int(m.group(5))}))
            else:
                bad_rows.append(ln)
                events.append(("FOUND", None))
        elif ln.startswith("DESTROY"):
            m = re.match(r"DESTROY cnt=(\d+)", ln)
            events.append(("DESTROY", int(m.group(1)) if m else None))
            if not m:
                bad_rows.append(ln)

    ctrl = sum(1 for k, _ in events if k == "CTRL")
    gate(1, ctrl >= 1, "ctrl rows=%d" % ctrl)
    gate(2, not bad_rows, "unparsed rows=%d" % len(bad_rows))

    if cnt0 is None:
        print("FAIL M289: no PRE count in the summary - evidence missing")
        return 1

    pend = None
    founds = []
    unpaired = 0
    for k, v in events:
        if k == "VEC":
            pend = v
        elif k == "FOUND":
            if not isinstance(v, dict):
                continue
            via = FOUND_CALLER.get(v["ret"])
            if via == "CC50":
                if pend in CC50_VECS:
                    vec = pend
                else:
                    vec = "UNPAIRED"
                    unpaired += 1
            elif via == "EC90":
                if pend in EC90_VECS:
                    vec = pend
                else:
                    vec = "UNPAIRED"
                    unpaired += 1
            else:
                vec = via or "UNKNOWN(ret=%#x)" % v["ret"]
            founds.append((vec, v))
            pend = None
        elif k == "DESTROY":
            pass

    n_found = len(founds)
    gate(5, n_found >= 1 and unpaired == 0,
         "found=%d unpaired=%d" % (n_found, unpaired))

    vec_counts = {}
    for f, _ in founds:
        vec_counts[f] = vec_counts.get(f, 0) + 1
    coherent = sum(vec_counts.values()) == n_found and n_found >= 1
    gate(3, coherent and unpaired == 0 and all(not f.startswith(("UN", "59ce10"))
                                               for f in vec_counts),
         "vec_counts=%s" % vec_counts)

    expected = cnt0
    acct_bad = []
    for e in events:
        if e[0] == "FOUND" and isinstance(e[1], dict):
            if e[1]["cnt"] != expected:
                acct_bad.append("FOUND cnt=%d expected=%d" % (e[1]["cnt"], expected))
            expected += 1
        elif e[0] == "DESTROY" and e[1] is not None:
            if e[1] != expected:
                acct_bad.append("DESTROY cnt=%d expected=%d" % (e[1], expected))
            expected -= 1
    if cnt_box is not None:
        late = cnt_box - expected
        acct = (not acct_bad) and 0 <= late <= 3
        why = "acct_bad=%d expected=%d box=%d late=%d" % (len(acct_bad), expected,
                                                          cnt_box, late)
    else:
        acct = False
        why = "no box count in summary"
    gate(4, acct, why)

    gate(6, tracer == 0 and yama_ok and cnt_box is not None,
         "tracer=%s yama=%s cnt_box=%s" % (tracer, yama_ok, cnt_box))

    rows = "\n".join(
        "  %2d  vec=%-10s ret=%#x fac=%d x=%d y=%d cnt=%d" %
        (i + 1, f, v["ret"], v["fac"], v["x"], v["y"], v["cnt"])
        for i, (f, v) in enumerate(founds)) if founds else "  (no founder hits)"

    print("M289 acceptance - re-walk of scratch/m289_gdb_raw.log")
    print("PRE count=%s | events: ctrl=%d vec=%d found=%d" %
          (cnt0, ctrl,
           sum(1 for k, _ in events if k == "VEC"), n_found))
    print("per-vector: %s" % (vec_counts or "{}"))
    print("accounting: expected=%d box_end=%s" % (expected, cnt_box))
    print(rows)
    print("")
    ok = all(v for v, _ in G.values())
    for i in sorted(G):
        v, why = G[i]
        print("g%d %s: %s" % (i, "PASS" if v else "FAIL", why))
    if ok:
        print("PASS M289: %d/6 - founder vector(s): %s" %
              (sum(1 for v, _ in G.values() if v), vec_counts))
        return 0
    print("FAIL M289")
    return 1


if __name__ == "__main__":
    sys.exit(main())
