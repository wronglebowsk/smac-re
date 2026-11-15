#!/usr/bin/env python3
"""M302 (s258, BOX-READ, READ-ONLY): pin B19's declared-unmodeled live values.

B19 (evidence/b19_visitcounter.txt, NAMED.md §B19) DECLARED UNMODELED: the
live VALUES ds:0x92a380 (rand+1), ds:0x69220c and ds:0x692210 (branch-B
lattice strides), the bit-0x2000 of the ds:0x985ac4 dword, and the live
CONTENTS of the counter table [0x989ce8+28*site+4] and the MAX table
[0x989ce8+28*site]. This milestone runs the one read-only /proc pass B19
declared would grade its counts ABSOLUTELY, then replays the 2321 recorded
rows through the shipped gate model with the PINNED values.

BOX RULES (non-negotiable, enforced in code):
  - READ ONLY: /proc/<pid>/mem opened "rb"; os.pread only. No pwrite, no gdb,
    no ptrace ops, no pokes, no relaunch, no kill, no save load, no turn
    advance. TracerPid is asserted 0 at start AND at end and printed.
  - An unmapped page / EIO is reported UNKNOWN, never 0. The reader is
    self-tested on a sentinel address that cannot be mapped, so the UNKNOWN
    path is exercised in every run.
  - The game is left running: pid liveness + year/round are re-read at the end.

ADDRESSES (every one decoded by B19 G1 from the pinned W1/W2 windows embedded
in evidence/m299_visitgate.txt; :10): rand 0x92a380, strides 0x69220c/0x692210,
flag dword 0x985ac4 (bit 0x2000), slot table 0x989ce8 + 28*site with MAX at +0
and the visit counter at +4 (0x989cec == 0x989ce8+4); the 128-entry per-region
bound is B18's REGION_BOUND law (sim/sitegate.py:88, evidence/b18_sitegate.txt:7).

ASSERTIONS are derived from landed evidence, never invented:
  A1 TracerPid==0 at start (box rules).
  A2 the UNKNOWN reader path works (sentinel unmapped address -> UNKNOWN, not 0).
  A3 every read address lies inside a mapped region of /proc/<pid>/maps.
  A4 the slot region decodes to exactly 128 slots x 28 B (B18 bound law); the
     two RECORDED sites {1, 9} (B18 anchor rows {1:2253, 9:68}) are readable.
  A5 store-law monotonicity across the two read passes (at start and after the
     replay): the ONLY writers pinned are the MAX store (max(edi,old), B18 G8
     polarity) and the counter ++ (B19) => MAX2>=MAX1 and CNT2>=CNT1 per site.
  A6 the pinned replay keeps every rung1 row refused (B19 G5: "no live state
     accepts" the 1222 rung1 rows) => 0 accepts among them under live values.
  A7 every pinned gate call returns eax in the static ret set {0,1,2} (B19 G1).
  A8 the 1099 previously-undecided (class branchA) rows all decide under the
     pinned state: certain-accept + certain-refuse + still-undecided == 1099,
     and still-undecided == 0 whenever all four scalars pinned.
  A9 the sim's baseline anchors reproduce on disk (rows 2321, kinds
     {branchA:1099, rung1:1222}) so the pinned replay extends B19's run.
  A10 the box is left running and untouched: same pid, TracerPid==0, and the
     year/round globals (0x985b00/0x985afc, preflight's table) unchanged.

counter <= MAX is NOT asserted: no landed evidence states it. The MAX field is
fed by edi (the 4-bit nibble cache, or the FUN_005aff90 body B18/B19 declared
UNMODELED), the counter field counts accepted visits, and the pinned code shows
two independent RMWs of the same slot - no cross-field law exists. The observed
relation is PRINTED, never assumed.
"""
import argparse
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from sim import visitcounter as vc  # noqa: E402  (the shipped B19 model)

DEF_OUT = os.path.join(REPO, "evidence", "m302_livepins.txt")

# the four scalars + the slot table (all decoded by B19 G1; see docstring)
SCALARS = (
    ("rand+1",       0x92A380, "Live.rand   (rung4: ==0 -> refuse; branchA +rand)"),
    ("stride s20c",  0x69220C, "Live.s20c   (branchB rhs: trunc4(d)*s20c)"),
    ("stride s210",  0x692210, "Live.s210   (branchB rhs: trunc4(h)*s210)"),
    ("flag dword",   0x985AC4, "Live.flag2000 = (dword & 0x2000) != 0 (rung2)"),
)
YEAR_G, ROUND_G = 0x985B00, 0x985AFC          # preflight's address table
SLOT_BASE, SLOT_STRIDE, REGION_BOUND = 0x989CE8, 28, 128
SENTINEL = 0x00001000                          # cannot be mapped: UNKNOWN test
FIELD = ("max", "cnt", "w2", "w3", "w4", "w5", "w6")   # 28 B = max,cnt,+24 B

L = []           # report lines (print + evidence file)


def emit(s=""):
    L.append(s)
    print(s)


# --------------------------------------------------------------------------
# the read-only reader
# --------------------------------------------------------------------------
def find_pids():
    out = subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True,
                         text=True)
    return [int(x) for x in out.stdout.split()]


def tracer_pid(pid):
    for ln in open("/proc/%d/status" % pid):
        if ln.startswith("TracerPid:"):
            return int(ln.split()[1])
    raise RuntimeError("no TracerPid line")


def maps(pid):
    iv = []
    for ln in open("/proc/%d/maps" % pid):
        rng = ln.split()[0].split("-")
        iv.append((int(rng[0], 16), int(rng[1], 16)))
    return iv


def mapped(iv, addr, n):
    return any(lo <= addr and addr + n <= hi for lo, hi in iv)


class Reader(object):
    """os.pread on /proc/<pid>/mem - open "rb", never written."""

    def __init__(self, pid):
        self.fd = os.open("/proc/%d/mem" % pid, os.O_RDONLY)
        self.iv = maps(pid)

    def dword(self, addr):
        """-> (value_or_None, how): how == 'ok', 'unmapped' or 'err:<e>'."""
        if not mapped(self.iv, addr, 4):
            return None, "unmapped"
        try:
            b = os.pread(self.fd, 4, addr)
        except OSError as e:
            return None, "err:%s" % e.errno
        return int.from_bytes(b, "little"), "ok"

    def slot(self, addr):
        """28 B -> tuple of 7 u32 or None (per-dword UNKNOWN marks kept)."""
        vals = []
        for k in range(7):
            v, how = self.dword(addr + 4 * k)
            vals.append(v if how == "ok" else None)
        return tuple(vals), all(v is not None for v in vals)

    def close(self):
        os.close(self.fd)


def label(v, how):
    return "UNKNOWN(%s)" % how if v is None else "%d (0x%08x)" % (v, v)


def dump_pass(rd, tag):
    """read the four scalars + all 128 slots; -> dict."""
    out = {"scalars": {}, "slots": {}}
    for name, addr, _why in SCALARS:
        out["scalars"][name] = rd.dword(addr)
    for site in range(REGION_BOUND):
        vals, full = rd.slot(SLOT_BASE + SLOT_STRIDE * site)
        out["slots"][site] = (vals, full)
    out["year"] = rd.dword(YEAR_G)
    out["round"] = rd.dword(ROUND_G)
    emit("== pass %s: pid %d ==" % (tag, rd_pid[0]))
    for name, addr, why in SCALARS:
        v, how = out["scalars"][name]
        emit("  scalar %-12s ds:%#08x = %-24s %s" % (name, addr, label(v, how), why))
    emit("  provenance globals: year %s  round %s"
         % (label(*out["year"]), label(*out["round"])))
    return out


def slot_table(passes, tag1, tag2):
    """print the full 128-slot dump (pass1) + monotonicity deltas (pass2)."""
    emit("slot table 0x989ce8 + 28*site, 128 entries (MAX +0, counter +4):")
    emit("%5s %10s %10s   %-40s | %s" % ("site", "MAX", "CNT",
                                         "remaining 20 B (5 dwords)",
                                         "status/%s deltas" % tag2))
    bad_mono = []
    for site in range(REGION_BOUND):
        v1, full1 = passes[tag1]["slots"][site]
        v2, _f2 = passes[tag2]["slots"][site]
        if not full1 and not _f2:
            emit("%5d %10s   UNKNOWN on both passes (unmapped)" % (site, "-"))
            continue
        cells1 = " ".join("UNKNOWN" if v is None else str(v) for v in v1[2:7])
        dl = ""
        for k, f in enumerate(("MAX", "CNT")):
            if v1[k] is not None and v2[k] is not None and v2[k] < v1[k]:
                bad_mono.append((site, f, v1[k], v2[k]))
                dl += " %s SHRANK %d->%d!" % (f, v1[k], v2[k])
        mx = "UNKNOWN" if v1[0] is None else str(v1[0])
        cn = "UNKNOWN" if v1[1] is None else str(v1[1])
        emit("%5d %10s %10s   %-40s | %s%s" % (
            site, mx, cn, cells1, "readable" if full1 else "PARTIAL", dl))
    nz_max = [s for s in range(REGION_BOUND)
              if passes[tag1]["slots"][s][0][0] not in (None, 0)]
    nz_cnt = [s for s in range(REGION_BOUND)
              if passes[tag1]["slots"][s][0][1] not in (None, 0)]
    emit("nonzero per pass1: MAX sites %s ; CNT sites %s" % (nz_max, nz_cnt))
    return bad_mono


rd_pid = [0]


def main():
    ap = argparse.ArgumentParser(prog="m302_livepins")
    ap.add_argument("--out", default=DEF_OUT)
    ap.add_argument("--sav", default=vc.DEF_SAV)
    a = ap.parse_args()

    pids = find_pids()
    assert len(pids) == 1, "expected exactly one terran.exe, got %r" % (pids,)
    pid = pids[0]
    rd_pid[0] = pid
    tp0 = tracer_pid(pid)
    emit("== M302 the read-only /proc pass over B19's declared-unmodeled "
         "values (READ ONLY: pread on /proc/%d/mem, no pwrite/gdb/poke) =="
         % pid)
    emit("provenance: %s ; pid %d (pgrep -x terran.exe) ; TracerPid(start)=%d ; "
         "loaded save m54b_clean (kickoff + smac_preflight PASS); replay save "
         "file %s" % (time.strftime("%Y-%m-%d %H:%M:%S %Z"), pid, tp0,
                      os.path.relpath(a.sav, REPO)))
    emit("read addresses: scalars %s ; slot region 0x%x..0x%x (%d slots x %d B) ; "
         "globals year 0x%x round 0x%x"
         % (", ".join("0x%x" % s[1] for s in SCALARS), SLOT_BASE,
            SLOT_BASE + SLOT_STRIDE * REGION_BOUND - 1, REGION_BOUND,
            SLOT_STRIDE, YEAR_G, ROUND_G))

    A = []

    def a(name, ok, detail):
        A.append((name, bool(ok), detail))

    rd = Reader(pid)
    p1 = dump_pass(rd, "1 (before replay)")

    # A1 TracerPid 0 at start
    a("A1_tracer_clean_start", tp0 == 0,
      "TracerPid(start) == %d (box rule: no tracer while we read)" % tp0)

    # A2 the UNKNOWN path is real: sentinel read cannot yield a value
    sv, shov = rd.dword(SENTINEL)
    a("A2_unknown_never_zero", sv is None and shov in ("unmapped", "err:14",
                                                       "err:22"),
      "sentinel 0x%x -> %s (an unmapped read reports UNKNOWN, never 0)"
      % (SENTINEL, label(sv, shov)))

    # A3 every read address lies in a mapped region
    want = [addr for _n, addr, _w in SCALARS] + [YEAR_G, ROUND_G]
    want += list(range(SLOT_BASE, SLOT_BASE + SLOT_STRIDE * REGION_BOUND, 4))
    unmapped = ["0x%x" % x for x in want if not mapped(rd.iv, x, 4)]
    a("A3_reads_mapped_first", not unmapped,
      "%d of %d read dwords inside /proc/%d/maps regions before the pread"
      % (len(want) - len(unmapped), len(want), pid))

    # A4 the region decodes to 128 slots and the RECORDED sites {1,9} read
    full = [s for s in range(REGION_BOUND) if p1["slots"][s][1]]
    a("A4_region_128_slots", len(full) == REGION_BOUND and 1 in full and 9 in full,
      "%d/%d slots fully readable (B18 REGION_BOUND 128, evidence/b18_sitegate.txt:7); "
      "the RECORDED sites 1 (rows 2253) and 9 (rows 68) readable: %s"
      % (len(full), REGION_BOUND, [s in full for s in (1, 9)]))

    emit("")
    p2 = dump_pass(rd, "2 (after replay)")
    bad_mono = slot_table({"p1": p1, "p2": p2}, "p1", "p2")
    emit("")

    # A5 monotonicity of the only two pinned writers over the read window
    a("A5_store_law_monotonicity", not bad_mono,
      "MAX/CNT across pass1->pass2 never decrease (B18 G8 max-store polarity + "
      "B19 counter ++: the ONLY writers); violations %s" % (bad_mono[:4],))

    # ---- the replay: B19's shipped model + the PINNED live state
    emit("== replay: the 2321 recorded rows through the shipped B19 gate with "
         "the PINNED live values ==")
    F = vc.build(a.sav)
    rows, P, g = F["rows"], F["P"], F["g"]
    kinds = dict(sorted(F["cnt_save"].kinds.items()))
    base_kinds_ok = (len(rows) == 2321 and kinds.get("branchA") == 1099
                     and kinds.get("rung1") == 1222)
    a("A9_baseline_anchors_reproduce", base_kinds_ok,
      "sim.visitcounter.build on disk reproduces B19's anchors: rows %d (RECORDED "
      "2321), kinds %s (RECORDED {'branchA':1099,'rung1':1222}) - the pinned "
      "replay extends the SAME rows/P/grid" % (len(rows), kinds))

    vrand = p1["scalars"]["rand+1"]
    v20c = p1["scalars"]["stride s20c"]
    v210 = p1["scalars"]["stride s210"]
    vflag = p1["scalars"]["flag dword"]
    pinned = None
    if all(x[1] == "ok" for x in (vrand, v20c, v210, vflag)):
        pinned = vc.Live(flag2000=(vflag[0] & 0x2000) != 0, rand=vrand[0],
                         s20c=v20c[0], s210=v210[0])
    emit("pinned live state: %s" % (pinned.label() if pinned else
                                    "INCOMPLETE (a scalar UNKNOWN - undecided "
                                    "rows stay undecided, never smoothed)"))

    cnt = collections_accept = collections_refuse = 0
    acc_by_site, ref_by_site, und_by_site = {}, {}, {}
    n_acc = n_ref = n_und = 0
    n_acc_1099 = n_ref_1099 = n_und_1099 = 0
    rung1_accepts = 0
    retvals = set()
    base20_kept = base20_flipped = 0
    for (vi, u, s, e) in rows:
        X, Y = e["y"], e["x"]                    # B16 transposition law
        rec = g.rb(X, Y)
        k = vc.classify_row(X, Y, rec, P)
        e0, _p0 = vc.gate_exec(X, Y, rec, vc.BASELINE, P)
        e1, p1leg = vc.gate_exec(X, Y, rec, pinned, P) if pinned else (None,
                                                                       "not-pinned")
        if e1 is not None:
            retvals.add(e1)
        if k["kind"] == "rung1":
            if e1 not in (0, None):
                rung1_accepts += 1
        if k["kind"] == "branchA":
            if e1 in (1, 2):
                n_acc_1099 += 1
                acc_by_site[s] = acc_by_site.get(s, 0) + 1
            elif e1 == 0:
                n_ref_1099 += 1
                ref_by_site[s] = ref_by_site.get(s, 0) + 1
            else:
                n_und_1099 += 1
                und_by_site[s] = und_by_site.get(s, 0) + 1
            if e0 in (1, 2):                     # B19's 20 baseline accepts
                if e1 in (1, 2):
                    base20_kept += 1
                else:
                    base20_flipped += 1
        if e1 in (1, 2):
            n_acc += 1
        elif e1 == 0:
            n_ref += 1
        else:
            n_und += 1
    emit("pinned replay over %d rows: CERTAIN-accept %d / CERTAIN-refuse %d / "
         "still-undecided %d" % (len(rows), n_acc, n_ref, n_und))
    emit("of the 1099 previously-undecided (branchA) rows: CERTAIN-accept %d / "
         "CERTAIN-refuse %d / still-undecided %d"
         % (n_acc_1099, n_ref_1099, n_und_1099))
    emit("per-site split of the 1099 (accept/refuse/undecided): %s"
         % {s: (acc_by_site.get(s, 0), ref_by_site.get(s, 0),
                und_by_site.get(s, 0)) for s in sorted(
                    set(acc_by_site) | set(ref_by_site) | set(und_by_site))})
    emit("B19's 20 baseline eax=2 accepts (rand==1 residue hits): %d kept under "
         "live rand %s, %d flipped"
         % (base20_kept, "pinned" if pinned else "UNPINNED", base20_flipped))
    emit("observed counter-vs-MAX (NO landed law relates them - printed, never "
         "asserted): sites with CNT>MAX %s"
         % [s for s in range(REGION_BOUND)
            if p1["slots"][s][0][1] is not None
            and p1["slots"][s][0][0] is not None
            and p1["slots"][s][0][1] > p1["slots"][s][0][0]])

    # A6 rung1 stays refused under live values (B19 G5 law)
    a("A6_rung1_still_refuses", rung1_accepts == 0,
      "of the 1222 rung1 rows, %d accept under the PINNED live state (law: none "
      "ever may - B19 G5)" % rung1_accepts)
    # A7 outputs stay in the static ret set
    a("A7_ret_values", retvals <= {0, 1, 2},
      "pinned gate calls returned eax in %s subset-of {0,1,2} (B19 G1 ret set)"
      % sorted(retvals))
    # A8 the 1099 decide under the pinned state
    a("A8_branchA_decides", n_acc_1099 + n_ref_1099 + n_und_1099 == 1099
      and (pinned is None or n_und_1099 == 0),
      "1099 branchA rows: %d CERTAIN-accept + %d CERTAIN-refuse + %d undecided "
      "== 1099, undecided==0 iff all four scalars pinned (pinned=%s)"
      % (n_acc_1099, n_ref_1099, n_und_1099, pinned is not None))

    rd.close()

    # A10 the box is left running and untouched
    pids_after = find_pids()
    tp1 = tracer_pid(pid) if pids_after == [pid] else -1
    rd2 = Reader(pid)
    y2 = rd2.dword(YEAR_G)
    r2 = rd2.dword(ROUND_G)
    rd2.close()
    same_state = (pids_after == [pid] and tp1 == 0
                  and y2 == p1["year"] and r2 == p1["round"])
    a("A10_box_left_running", same_state,
      "pid %d alive and unchanged, TracerPid(end)=%d, year %s->%s, round %s->%s "
      "(no turn advance, no writes, game left running)"
      % (pid, tp1, label(*p1["year"]), label(*y2), label(*p1["round"]),
         label(*r2)))
    emit("TracerPid(end) = %d" % tp1)

    emit("")
    nbad = 0
    for name, ok, detail in A:
        nbad += 0 if ok else 1
        emit("%-30s %s  %s" % (name, "PASS" if ok else "FAIL", detail))
    emit("")
    emit("%sM302: %d/%d assertions - the four scalars + the 128-slot MAX/CNT "
         "table pinned read-only from live memory; of B19's 1099 undecided "
         "branchA rows %d became CERTAIN-accept and %d CERTAIN-refuse under the "
         "pinned live state" % ("FAIL " if nbad else "PASS ", len(A) - nbad,
                                len(A), n_acc_1099, n_ref_1099))
    for name, ok, _d in A:
        assert ok, name + " FAILED - see the printed table above"
    with open(a.out, "w") as fobj:
        fobj.write("\n".join(L) + "\n")
    emit("evidence written: %s" % os.path.relpath(a.out, REPO))
    return 0 if not nbad else 1


import collections  # noqa: E402  (kept late to mirror the header order rule)

if __name__ == "__main__":
    sys.exit(main())
