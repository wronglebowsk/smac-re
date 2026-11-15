#!/usr/bin/env python3
"""B19 (s257): the slot [+4] visit counter made executable (R2's "which sites
get visited and how often" slice; written by this fire from B18's DECLARED
UNMODELED list + M299/M300/M301's landed laws - the rung was not yet in
BUILD_SPINE.md, so the build fire authored it, as B14/B16/B17/B18 did).

sim/visitcounter.py executes the counter law the three merged milestones
settled, over RECORDED artifacts only (no box, no /proc, no gdb, no
game-binary load):

  THE LAW (M299, evidence/m299_visitgate.txt W1/W2): in FUN_0051dcb0's tail,
  after the two MAX stores, the block 0x51e00d-0x51e01b does
  `ecx = [esi+0x989cec]; ecx++; [esi+0x989cec] = ecx` - the [+4] field of the
  SAME 28-B site slot the dword MAX store lands in (0x989cec == 0x989ce8 + 4,
  same pinned esi = 28*site) - and that block is SKIPPED WHOLE when
  FUN_005832b0([ebp-0x10], [ebp-0x8]) returns 0 (0x51dffd call, 0x51e005 test,
  0x51e007 je 0x51e11d). The callee is a pure ladder over the SAME 44-B
  tile-record fold (44*(ds:0x692184*y + sar(x,1)), base ds:0x92ae14) and the
  pair of call legs:
    rung1  dword[rec+8] & 0x102000  -> 0 (byte9 bit5 = the B16 occ bit,
                                        byte10 bit4 = the M296 score-zero bit)
    rung2  ds:0x985ac4 & 0x2000 set -> (dword[rec+8] & 0xc000000) ? 2 : 0
    rung3  dword[rec+8] & 0x10000000 -> 1
    rung4  ds:0x92a380 (rand+1) == 0 -> 0, else the LATTICE PARITY:
      branch A ((BYTE[rec+0] & 0xe0) >= 0x60, the land class): hit iff
        ((h & 3) + 4 * (d & 3)) == (-5*sar(h,2) - 3*sar(d,2) + rand) & 0xf
        for h = sar(x+y,1), d = x - h  -> return 2; on a miss fall to B.
      branch B: (h&3) + 4*(d&3) == (rand + 8 + trunc4(h)*ds:0x692210
        + trunc4(d)*ds:0x69220c) & 0x1f -> 1, else 0 (trunc4 = the pinned
        cdq/and 3/add/sar 2 = division by 4 TRUNCATED toward zero).
  THE CALLER LANDSCAPE (M300, evidence/m300_callers.txt): 24 direct call
  sites, 0 indirect; classes 21 truth-branch / 2 stored-to-memory / 1
  into-ebx; reach-to-writer 17 REACHES / 1 IN-WRITER (0x51dffd inside
  FUN_0051dcb0, the ONLY writer of the counter) / 6 CANNOT-REACH - a visit
  only exists where FUN_0051dcb0 runs.
  THE ebx DEFLECTION (M301, evidence/m301_ebxtable.txt): the walk
  0x51de2c-0x51df1d that produces ebx gates NOTHING of the decision - its
  je 0x51dff5 leg lands BEFORE the call, eax is consumed exactly once
  (0x51e005), and the counter address esi never mentions ebx.

PARITY (recorded artifacts): the pinned W1/W2 windows and the recorded gate
census inside evidence/m299_visitgate.txt itself (the model PARSES the
evidence file as its instruction source, as B18 parses its pinned window);
the S2 call-site table inside evidence/m300_callers.txt; the A6 structural
witness inside evidence/m301_ebxtable.txt; the recorded m294 decision rows
through B18's loader (B17's graded filter + B16's transposition law) and the
s249 end-window live-record dump.

RECORDED PINS (prior sessions, cited): W1 44 lines / W2 114 lines
(m299_visitgate.txt:5,:52); fold 4096/4096 (:169); esi 2048/2048 (:170);
lattice theorem 36 (H,D) x 16 rand (:172); dump digest 093d10a868da55b2,
rung1-close 481 / occ-alone 16 / bits26-27 12 / rung3-open 5 / branch-A
domain 1087 over 2048 records (:173); call sites 24 == n_callers 24, 0
non-call mentions, 21/2/1 and 17/1/6 (:1,:11-36); 8/8 M301 assertions
(m301_ebxtable.txt tail). FIRST-MEASUREMENT ANCHORS (this fire, reproducible
from the shipped artifacts; they lock the replay, they are not prior claims):
the ANCHORS dict below.

DECLARED UNMODELED: the live VALUES ds:0x92a380 (rand+1), ds:0x69220c and
ds:0x692210 (branch-B lattice strides) and ds:0x985ac4 bit 0x2000 - never
dumped, only address witnesses exist (m299_visitgate.txt:175-178); the live
CONTENTS of the counter table 0x989ce8+4 and the MAX tables (a read-only
/proc window over both globals grades the counts absolutely: LEAD, the same
LEAD B18 declared); the 0x51e02c post-counter region byte 0x94ed28 (NAMED:371)
and everything downstream of it; the FUN_005aff90 value body (B18's
frontier - the counter does not depend on it); the save-vs-window per-tile
drift (B16/B18 law - both record views are replayed and the divergence is
COUNTED, never smoothed); which of the 17 REACHES callers actually run
(only IN-WRITER visits are replayed here); and which loop drives FUN_0051dcb0
visits at runtime (the replay is over the RECORDED window rows, as B17/B18).
"""
import argparse
import collections
import hashlib
import os
import random
import re
import sys

from . import podscan as pod
from . import precheck as pc
from . import save as sosave
from . import scanleg as sl
from . import sitegate as sgt

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEF_SAV = os.path.join(REPO, "programs", "saves", "m54b_clean.SAV")
DEF_RAW = os.path.join(REPO, "evidence", "m294_gate_rows_raw.txt")
DEF_BIN = os.path.join(REPO, "evidence", "s249_live_map.bin")
DEF_M299 = os.path.join(REPO, "evidence", "m299_visitgate.txt")
DEF_M300 = os.path.join(REPO, "evidence", "m300_callers.txt")
DEF_M301 = os.path.join(REPO, "evidence", "m301_ebxtable.txt")

REC_LEN = 44
# recorded pins (evidence/m299_visitgate.txt - see docstring for :line cites)
PIN_W1_LINES = 44
PIN_W2_LINES = 114
PIN_FOLD_N = 4096
PIN_SITE_N = 2048
PIN_THEOREM_HD = 36
PIN_DUMP_DIGEST = "093d10a868da55b2"
PIN_R1_CLOSE = 481
PIN_OCC_ALONE = 16
PIN_SEL_SET = 12
PIN_R3_OPEN = 5
PIN_CLS_A = 1087
PIN_LIVE_RECS = 2048
# recorded pins (evidence/m300_callers.txt)
PIN_SITES = 24
PIN_CLS_TRUTH = 21
PIN_CLS_STORED = 2
PIN_CLS_EBX = 1
PIN_REACH = 17
PIN_INWRITER = 1
PIN_NOREACH = 6
# first-measurement anchors (this fire): the replay class census and the
# per-site counter table over the 2321 recorded decision rows (save view).
# Filled from the first run of THIS file; asserted by every later run.
ANCHORS = {
    "rows": 2321, "visits": 1026, "tiles": 101,
    "refuse": None, "cert_accept": None, "undecided": None,
    "branchA": None, "branchB": None, "branchA_reach": None,
    "base_rung3": None, "base_a_hit": None, "base_und_b": None,
    "site_hist_save": {1: 2253, 9: 68},
}

M300_RX = re.compile(
    r"^(0x[0-9a-f]{6})\s+(FUN_[0-9a-f]+)\s+(.*?)\s+"
    r"(REACHES(?:\([^)]*\))?|IN-WRITER|CANNOT-REACH)\s+(.*)$")


# --------------------------------------------------------------------------
# the evidence windows: the pinned disassembly INSIDE the evidence file is the
# instruction source (B18's PINS discipline, but read out of the M299 log).
# --------------------------------------------------------------------------
INS_RX = re.compile(r"^\s+([0-9a-f]{6}):\t([0-9a-f ]+?)\s*\t(.+?)\s*$")


def parse_windows(path):
    """-> (w1, w2, n1, n2): addr->(bytes,text) maps + recorded line counts."""
    w1, w2, n1, n2 = {}, {}, None, None
    cur = None
    for ln in open(path, errors="replace"):
        hdr = re.match(r"^(\d+) lines (0x[0-9a-f]+)-(0x[0-9a-f]+)", ln.strip())
        if hdr:
            n = int(hdr.group(1))
            cur = w1 if n == PIN_W1_LINES else w2
            (n1, n2) = ((n, n2) if cur is w1 else (n1, n))
            continue
        m = INS_RX.match(ln)
        if m and cur is not None:
            cur[int(m.group(1), 16)] = (m.group(2).strip(), m.group(3))
    return w1, w2, n1, n2


def decode_pins(w1, w2):
    """Read EVERY model constant out of the pinned instruction texts. Any pin
    that does not resolve decodes to None and fails G1, never a fallback."""
    P = {}
    j = " ".join
    # W1: the gate five + counter field offset + esi stride
    P["call_addr"] = next((a for a, (_, i) in sorted(w1.items())
                           if i.startswith("call")), None)
    b = w1.get(P.get("call_addr"), ("", ""))[0]
    P["callee_target"] = ((P["call_addr"] + 5 + int(b.split()[1], 16))
                          if len(b.split()) == 2 and b.split()[0] == "e8"
                          else None)
    P["je_addr"] = next((a for a, (_, i) in sorted(w1.items())
                         if i.startswith("je")), None)
    tgt = w1.get(P.get("je_addr"), ("", ""))[1].split()
    P["je_target"] = int(tgt[-1], 16) if tgt and tgt[-1].startswith("0x") else None
    # esi fold 0x51dfb1 lea esi,[eax*8+0x0] / 0x51dfb8 sub esi,ecx / 0x51dfba shl esi,0x2
    mul = lea = sub_ = shl = None
    for a, (_, i) in w1.items():
        m = re.match(r"lea\s+esi,\[eax\*(\d+)\+0x0\]$", i)
        if m:
            mul = int(m.group(1))
            lea = a
        if re.match(r"sub\s+esi,ecx$", i):
            sub_ = a
        m = re.match(r"shl\s+esi,0x([0-9a-f])$", i)
        if m:
            shl = (a, int(m.group(1), 16))
    P["slot_stride"] = ((mul - 1) << shl[1]) if (mul and sub_ is not None
                                                 and shl and lea < sub_ < shl[0]) else None
    # [esi+disp] operands: MAX store 0x51dfcb, counter load/store 0x51e00d/0x51e01b
    disps = []
    for a, (_, i) in sorted(w1.items()):
        m = re.match(r"mov\s+(?:DWORD PTR )?\[esi\+(0x[0-9a-f]+)\],?\w*\s*$", i)
        m2 = re.match(r"mov\s+(?:DWORD PTR )?\[(\w+)\+(0x[0-9a-f]+)\](?:,(\w+))?\s*$", i)
        m3 = re.match(r"mov\s+ecx,DWORD PTR \[esi\+(0x[0-9a-f]+)\]$", i)
        m4 = re.match(r"mov\s+DWORD PTR \[esi\+(0x[0-9a-f]+)\],eax$", i)
        if m4:
            disps.append((a, int(m4.group(1), 16), "store"))
        elif m3:
            disps.append((a, int(m3.group(1), 16), "load"))
    P["max_disp"] = next((d for _, d, k in disps if k == "store"
                          and d == 0x989CE8), None)
    P["cnt_disp"] = next((d for _, d, k in disps if d == 0x989CEC), None)
    P["counter_off"] = (P["cnt_disp"] - P["max_disp"]) if (
        P["max_disp"] and P["cnt_disp"]) else None
    # W2: the ladder masks, globals, domains, lattice coefficients
    def imm(a, rx):
        m = re.match(rx, w2.get(a, ("", ""))[1]) if a in w2 else None
        return int(m.group(1), 16) if m else None
    P["rung1"] = imm(0x5832DC, r"test\s+eax,(0x[0-9a-f]+)$")
    m = re.match(r"test\s+DWORD PTR ds:(0x[0-9a-f]+),(0x[0-9a-f]+)$",
                 w2.get(0x5832EA, ("", ""))[1]) if 0x5832EA in w2 else None
    P["flag_addr"], P["flag_bit"] = (int(m.group(1), 16), int(m.group(2), 16)) if m else (None, None)
    P["rung2mask"] = imm(0x5832F6, r"and\s+eax,(0x[0-9a-f]+)$")
    P["rung3"] = imm(0x583307, r"test\s+eax,(0x[0-9a-f]+)$")
    m = re.match(r"mov\s+edi,DWORD PTR ds:(0x[0-9a-f]+)$",
                 w2.get(0x583318, ("", ""))[1]) if 0x583318 in w2 else None
    P["rand_addr"] = int(m.group(1), 16) if m else None
    P["dom_mask"] = imm(0x583331, r"and\s+al,(0x[0-9a-f]+)$")
    P["dom_cmp"] = imm(0x583335, r"cmp\s+eax,(0x[0-9a-f]+)$")
    P["amask"] = imm(0x58335E, r"and\s+ebx,(0x[0-9a-f]+)$")
    P["bmask"] = imm(0x5833A7, r"and\s+edx,(0x[0-9a-f]+)$")
    def gaddr(a, rx):
        m = re.match(rx, w2.get(a, ("", ""))[1]) if a in w2 else None
        return int(m.group(1), 16) if m else None
    P["s210"] = gaddr(0x58338B, r"imul\s+ebx,DWORD PTR ds:(0x[0-9a-f]+)$")
    P["s20c"] = gaddr(0x583399, r"imul\s+eax,DWORD PTR ds:(0x[0-9a-f]+)$")
    P["mult_g"] = gaddr(0x5832B3, r"mov\s+eax,DWORD PTR ds:(0x[0-9a-f]+)$")
    P["tv_base_g"] = gaddr(0x5832D0, r"mov\s+edx,DWORD PTR ds:(0x[0-9a-f]+)$")
    # branch-A lattice coefficients decoded from the pinned chain:
    #   neg ebx / shl ebx,S1 / sub ebx,eax          -> -(2^S1 + 1) * (h>>2)
    #   lea edx,[eax+eax*K]                          -> (K + 1) * (d>>2)   [sub ebx,edx]
    P["coef_h"] = None
    for a in sorted(w2):
        if w2[a][1] == "neg    ebx" and re.match(r"shl\s+ebx,0x([0-9a-f])$",
                                                 w2.get(a + 1, ("", ""))[1]) \
           and w2.get(a + 2, ("", ""))[1] == "sub    ebx,eax":
            P["coef_h"] = (1 << int(w2[a + 1][1].split(",0x")[1], 16)) + 1
    m = None
    for a in sorted(w2):
        m2 = re.match(r"lea\s+edx,\[eax\+eax\*(\d)\]$", w2[a][1])
        if m2 and w2.get(a + 2, ("", ""))[1] == "sub    ebx,edx":
            m = int(m2.group(1)) + 1
    P["coef_d"] = m
    # purity: ret count, callee stores, pop-before-ret
    P["rets"] = [a for a in sorted(w2) if w2[a][1] == "ret"]
    P["callee_stores"] = sum(1 for _, (_, i) in w2.items()
                             if re.match(r"mov\s+(BYTE|WORD|DWORD) PTR \[[^\]]+\],", i))
    preserved = True
    for r in P["rets"]:
        body = j(i for a in range(max(min(w2), r - 16), r) if a in w2
                 for _, i in [w2[a]])
        if not all(p in body for p in ("pop    edi", "pop    esi", "pop    ebx")):
            preserved = False
    P["pops_preserve"] = preserved
    # eax==1 returns are reachable ONLY through the flag-clear legs: the
    # 0xc000000 branch at 0x5832f4 (je past the neg/sbb block) is bypassed by
    # the flag-clear path, so no flag-SET return can carry 1.
    j = " ".join
    P["r2_bypass_addr"] = None
    for a in sorted(w2):
        m = re.match(r"je\s+(0x[0-9a-f]+)$", w2[a][1])
        if m and P["rung2mask"] and int(m.group(1), 16) <= min(
                x for x in w2 if x > 0x583307 and w2[x][1] == "ret"):
            P["r2_bypass_addr"] = a
    # the six return shapes: the eax value each ret delivers
    P["ret_vals"] = set()
    for r in P["rets"]:
        look = j(w2[a][1] for a in range(r - 12, r) if a in w2)
        for v in ("0x2", "0x1", "0x0"):
            if ("mov    eax," + v) in look or (("xor    eax,eax" in look or
                                                "mov    eax,ecx" in look) and v == "0x0"):
                P["ret_vals"].add(int(v, 16))
                break
    return P


# --------------------------------------------------------------------------
# the ladder, executable. Two independent implementations (skill law: pair
# instruments that can fail DIFFERENTLY): gate_exec ports the pinned chain,
# rungA_closed is M299's recorded closed form; G4 grades them equal.
# --------------------------------------------------------------------------
M32 = 0xFFFFFFFF


def s32(v):
    v &= M32
    return v - 0x100000000 if v >= 0x80000000 else v


def sar_i(v, n):
    return s32(v) >> n


def trunc4(v):
    """the pinned cdq/and edx,3 / add / sar 2: division by 4 TRUNCATED
    toward zero (0x583377-0x583388)."""
    v = s32(v)
    return (v + (3 if v < 0 else 0)) >> 2


def fold_rec(x, y, rec, mult):
    """the callee's own record fold (pinned 0x5832b3-0x5832d6): rec is already
    the record; this grades that the sim's own (mult, x>>1) fold is the one the
    callee computes - the record bytes passed here must come from the same."""
    h = mult * y + sar_i(x, 1)
    return 44 * h


def rungA_closed(h, d, rand):
    """M299's recorded closed form (scripts/m299_visitgate.py rungA, verbatim
    law): hit iff (h&3) + 4*(d&3) == (-5*(h>>2) - 3*(d>>2) + rand) & 0xf."""
    ebx = (-5 * (h >> 2) - 3 * (d >> 2) + rand) & 0xF
    return ((h & 3) + 4 * (d & 3)) == ebx


def branchA_port(h, d, rand, P):
    """the SAME branch A ported from the pinned instruction chain: ebx built by
    coef_h*sar(h,2) neg, minus coef_d*sar(d,2), plus rand, masked amask."""
    ebx = (-P["coef_h"] * sar_i(h, 2) - P["coef_d"] * sar_i(d, 2) + rand) & P["amask"]
    return (sar_i(h, 1) if False else (h & 3)) + 4 * (d & 3) == ebx


def a_target(h, d, P):
    """the residue class of (rand & 0xf) that MAKES branch A hit."""
    return ((h & 3) + 4 * (d & 3) + P["coef_h"] * sar_i(h, 2)
            + P["coef_d"] * sar_i(d, 2)) & P["amask"]


class Live(object):
    """the four live globals the ladder reads but NO evidence file ever
    dumped. None = the UNMODELED live value (m299_visitgate.txt:175-178)."""

    def __init__(self, flag2000=None, rand=None, s20c=None, s210=None):
        self.flag2000 = flag2000   # (ds:0x985ac4 & 0x2000) != 0
        self.rand = rand           # ds:0x92a380 (the rand+1 dword)
        self.s20c = s20c           # ds:0x69220c
        self.s210 = s210           # ds:0x692210

    def label(self):
        return "flag=%s rand=%s s20c=%s s210=%s" % (
            self.flag2000, self.rand, self.s20c, self.s210)


BASELINE = Live(flag2000=False, rand=1, s20c=None, s210=None)


def dw8(rec):
    return int.from_bytes(rec[8:12], "little")


def gate_exec(x, y, rec, live, P):
    """one FUN_005832b0(x, y) evaluation over the record bytes. Returns
    (eax_or_None, path): None means an UNMODELED live global decided the leg.
    The instruction order is the pinned W2 order, leg by leg."""
    dw = dw8(rec)
    if dw & P["rung1"]:
        return 0, "rung1"
    sel = bool(dw & P["rung2mask"])
    if live.flag2000 is True:
        # and 0xc000000 / neg / sbb (CF = sel) / and 2  ->  2 or 0
        return (2 if sel else 0), "rung2-flagset"
    if live.flag2000 is None:
        return None, "rung2-flag-unknown"
    if dw & P["rung3"]:
        return 1, "rung3"
    if live.rand is None:
        return None, "rand-unknown"
    if live.rand == 0:
        return 0, "rand-zero"
    h = sar_i(x + y, 1)
    d = x - h
    a_domain = (rec[0] & P["dom_mask"]) >= P["dom_cmp"]
    if a_domain and branchA_port(h, d, live.rand, P):
        return 2, "branchA-hit"
    if live.s20c is None or live.s210 is None:
        return None, "branchB-strides-unknown"
    rhs = (live.rand + 8 + trunc4(h) * live.s210 + trunc4(d) * live.s20c) & P["bmask"]
    return (1 if (h & 3) + 4 * (d & 3) == rhs else 0), "branchB"


def classify_row(x, y, rec, P):
    """the live-state-FREE classification (min/max semantics):
    CERTAIN refuse  <=> rung1 hit (eax == 0 in every live state);
    CERTAIN accept  <=> pass1 AND bits26/27 AND bit28 (flag set -> 2,
                        flag clear -> 1; accepted in every live state);
    everything else is UNDECIDED but accept-POSSIBLE (the flag, the rand
    residue, or the strides can be made to accept)."""
    dw = dw8(rec)
    out = {"pass1": not (dw & P["rung1"])}
    if not out["pass1"]:
        out.update(certain=False, kind="rung1")
        return out
    sel = bool(dw & P["rung2mask"])
    r3 = bool(dw & P["rung3"])
    h = sar_i(x + y, 1)
    d = x - h
    a_dom = (rec[0] & P["dom_mask"]) >= P["dom_cmp"]
    out.update(sel=sel, r3=r3, a_domain=a_dom)
    if a_dom:
        out["a_target"] = a_target(h, d, P)
    if sel and r3:
        out.update(certain=True, kind="certain-accept")
    elif sel:
        out.update(certain=False, kind="flag-or-lattice")
    elif r3:
        out.update(certain=False, kind="flag-or-1")
    else:
        out.update(certain=False, kind="branchA" if a_dom else "branchB")
    return out


class VisitCounter(object):
    """the counter table: per site, the rows seen and the three count columns
    (certain / baseline-assumed / possible), in the order the game runs them:
    the gate call at 0x51dffd FIRST, the inc block 0x51e00d-0x51e01b on eax!=0
    only, at slot [0x989ce8 + 28*site + 4]."""

    FIELDS = ("rows", "refuse", "certain", "base_accept", "base_refuse",
              "base_undec", "possible", "eax2", "eax1", "a_domain",
              "a_miss", "b_rows")

    def __init__(self):
        self.t = collections.defaultdict(lambda: dict((f, 0) for f in
                                                      self.FIELDS))
        self.kinds = collections.Counter()

    def visit(self, x, y, rec, site, live, P):
        """one FUN_0051dcb0 visit at (x, y); site = BYTE[rec+3] (B18 law).
        Returns the gate outcome (0/1/2/None); increments [+4] iff nonzero."""
        t = self.t[site]
        t["rows"] += 1
        eax, _ = gate_exec(x, y, rec, live, P)
        k = classify_row(x, y, rec, P)
        self.kinds[k["kind"]] += 1
        if not k["pass1"]:
            t["refuse"] += 1
        else:
            t["possible"] += 1
            t["a_domain"] += 1 if k.get("a_domain") else 0
            if k["kind"] == "certain-accept":
                t["certain"] += 1
            if eax is not None:
                t["base_refuse" if eax == 0 else "base_accept"] += 1
                if eax == 2:
                    t["eax2"] += 1
                elif eax == 1:
                    t["eax1"] += 1
            else:
                t["base_undec"] += 1
                if k["kind"] == "branchA":
                    t["a_miss"] += 1
                elif k["kind"] == "branchB":
                    t["b_rows"] += 1
        return eax

    def total(self, f):
        return sum(t[f] for t in self.t.values())

    def digest(self):
        h = hashlib.sha256()
        for s in sorted(self.t):
            h.update(("v%04d=%s;" % (s, ",".join(str(self.t[s][f])
                                                 for f in self.FIELDS)))
                     .encode())
        return h.hexdigest()[:16]


# --------------------------------------------------------------------------
# evidence-table parsers (m300 S2, m301 A6) - graded against the bytes window
# --------------------------------------------------------------------------
def parse_m300(path):
    rows = []
    for ln in open(path, errors="replace"):
        m = M300_RX.match(ln.strip())
        if m:
            rows.append({"va": int(m.group(1), 16), "fn": m.group(2),
                         "cls": m.group(3).strip(), "reach": m.group(4),
                         "use": m.group(5)})
    return rows


def parse_m301_a6(path):
    """-> (recorded eax-mention list, recorded backward-edge count, je-target
    note) straight out of the A6 witness lines."""
    mentions, back = None, None
    for ln in open(path, errors="replace"):
        m = re.search(r"every eax mention after the call \(to 0x[0-9a-f]+\): (\[.*\])", ln)
        if m:
            mentions = eval(m.group(1), {"__builtins__": {}})
        m = re.search(r"backward branches from after the call into the range: (\d+) \[", ln)
        if m:
            back = int(m.group(1))
    return mentions, back


# --------------------------------------------------------------------------
# the report
# --------------------------------------------------------------------------
def report(sav_path, raw_path=DEF_RAW, bin_path=DEF_BIN, m299=DEF_M299,
           m300=DEF_M300, m301=DEF_M301, out=None):
    P = []
    L = print if out is None else (lambda s="": (print(s), out.write(s + "\n")))
    R = []

    def gate(name, ok, detail):
        R.append((name, bool(ok)))
        L("%-30s %s  %s" % (name, "PASS" if ok else "FAIL", detail))

    sav = sosave.parse(sav_path)
    g = pc.Grid(sav)
    W, H = sav.width, sav.height
    lbuf = open(bin_path, "rb").read()
    live_len_ok = len(lbuf) == REC_LEN * PIN_LIVE_RECS
    lg = sgt.LiveGrid(lbuf, W // 2)
    vis = sl.load_visits(raw_path)
    rows = sgt.graded_rows(vis)
    w1, w2, n1, n2 = parse_windows(m299)
    P = decode_pins(w1, w2)
    m300rows = parse_m300(m300)
    m301_mentions, m301_back = parse_m301_a6(m301)

    # ---------------- THE TABLE FIRST (print, then assert) ----------------
    def replay(grid, live, use_live_site=False):
        c = VisitCounter()
        tiles = set()
        for (vi, u, s, e) in rows:
            X, Y = e["y"], e["x"]           # B16 transposition law
            rec = grid.rb(X, Y)
            c.visit(X, Y, rec, sgt.site_of(rec), live, P)
            tiles.add((X, Y))
        return c, len(c and tiles)

    cnt_save = replay(g, BASELINE)
    cnt_save = cnt_save[0]
    cnt_live = replay(lg, BASELINE)[0] if live_len_ok else None

    L("== B19 the slot [+4] visit counter, executed over the recorded rows ==")
    L("state DECLARED baseline (live globals UNMODELED; see DECLARED): %s"
      % BASELINE.label())
    L("per-site counter table (site -> rows/certain/base-accept-1/base-accept-2/"
      "base-undecided/possible):  [view=save]")
    hdr = ("site", "rows", "refuse", "certain", "acc1", "acc2", "undec",
           "poss", "a_dom")
    L("%-6s %6s %7s %8s %5s %5s %6s %6s %6s" % hdr)
    for s in sorted(cnt_save.t):
        t = cnt_save.t[s]
        L("%-6d %6d %7d %8d %5d %5d %6d %6d %6d"
          % (s, t["rows"], t["refuse"], t["certain"], t["eax1"], t["eax2"],
             t["base_undec"], t["possible"], t["a_domain"]))
    L("class census over the %d graded rows: %s"
      % (len(rows), dict(sorted(cnt_save.kinds.items()))))
    if cnt_live is not None:
        dsum = sum(abs(cnt_save.t[s][f] - cnt_live.t[s][f])
                   for s in set(cnt_save.t) | set(cnt_live.t)
                   for f in VisitCounter.FIELDS
                   if s in cnt_save.t and s in cnt_live.t)
        L("save-vs-live view divergence over the same rows: %d field deltas" % dsum)

    # ---------------- gates ----------------
    bad1 = []
    if n1 != PIN_W1_LINES or n2 != PIN_W2_LINES:
        bad1.append("window sizes %s/%s != %d/%d" % (n1, n2, PIN_W1_LINES, PIN_W2_LINES))
    if P["callee_target"] != 0x5832B0:
        bad1.append("call rel32 decodes to %s" % P["callee_target"])
    want = {"rung1": 0x102000, "rung2mask": 0xC000000, "rung3": 0x10000000,
            "flag_addr": 0x985AC4, "flag_bit": 0x2000, "rand_addr": 0x92A380,
            "s210": 0x692210, "s20c": 0x69220C, "dom_mask": 0xE0,
            "dom_cmp": 0x60, "amask": 0xF, "bmask": 0x1F,
            "slot_stride": 28, "counter_off": 4, "coef_h": 5, "coef_d": 3,
            "mult_g": 0x692184, "tv_base_g": 0x92AE14, "cnt_disp": 0x989CEC}
    for k, v in want.items():
        if P.get(k) != v:
            bad1.append("%s=%s != %s" % (k, P.get(k),
                                         hex(v) if isinstance(v, int) else v))
    if P["je_target"] != 0x51E11D or P["call_addr"] != 0x51DFFD:
        bad1.append("gate five je_target=%s call=%s" % (P["je_target"], P["call_addr"]))
    gate("G1_evidence_windows_pins",
         not bad1 and len(w1) == PIN_W1_LINES and len(w2) == PIN_W2_LINES
         and len(P["rets"]) == 6 and P["callee_stores"] == 0
         and P["pops_preserve"] and P["ret_vals"] <= {0, 1, 2},
         "%d + %d pinned instructions parsed from %s; the call rel32 DECODES to "
         "0x5832b0; the counter operand DECODES to [esi+0x989cec] = the MAX "
         "operand [esi+0x989ce8] + %s (the field, not a second slot - the "
         "28-B stride DECODES from the pinned lea/sub/shl chain as %s); every "
         "model constant READ OUT OF THE BYTES: rung1 %#x flag %#x@%#x sel "
         "%#x rung3 %#x rand %#x strides %#x/%#x domain %#x>=%#x masks %#x/%#x "
         "lattice coefs -%s(h>>2) -%s(d>>2); callee: %d rets, %d memory "
         "stores, pops precede ALL rets %s, ret eax values %s%s"
         % (len(w1), len(w2), os.path.basename(m299), P["counter_off"],
            P["slot_stride"], P["rung1"], P["flag_bit"], P["flag_addr"],
            P["rung2mask"], P["rung3"], P["rand_addr"], P["s20c"], P["s210"],
            P["dom_mask"], P["dom_cmp"], P["amask"], P["bmask"],
            P["coef_h"], P["coef_d"], len(P["rets"]), P["callee_stores"],
            P["pops_preserve"], sorted(P["ret_vals"]),
            "" if not bad1 else " BAD " + "; ".join(bad1[:4])))

    random.seed(299)
    bad2 = 0
    for _ in range(PIN_FOLD_N):
        x = random.choice([random.randrange(0, 4096), -random.randrange(1, 4096)])
        y = random.randrange(0, 256)
        w2r = random.randrange(20, 200)
        base = random.randrange(0x10000, 0x0FFFFFFF)
        eax = (w2r * y + sar_i(x, 1)) & M32
        dec = (base + ((eax + (eax + eax * 4) * 2) & M32) * 4) & M32
        if dec != (base + 44 * (w2r * y + sar_i(x, 1))) & M32:
            bad2 += 1
    random.seed(299 + 7)
    for _ in range(4096):
        x = random.choice([random.randrange(0, 4096), -random.randrange(1, 4096)])
        y = random.randrange(0, 256)
        w2r = random.randrange(20, 200)
        base = random.randrange(0x10000, 0x0FFFFFFF)
        eax = (w2r * y + sar_i(x, 1)) & M32
        dec = (base + ((eax + (eax + eax * 4) * 2) & M32) * 4) & M32
        if dec != (base + 44 * (w2r * y + sar_i(x, 1))) & M32:
            bad2 += 1
    bad2s = 0
    for _ in range(PIN_SITE_N):
        site = random.randrange(0, 128)
        esi = (((site * 8) - site) & M32) << 2
        if (esi & M32) != (28 * site) & M32:
            bad2s += 1
    gate("G2_fold_laws_reverified",
         bad2 == 0 and bad2s == 0,
         "fold==44*(W2*y+sar(x,1)) graded %d/%d random (x,y,W2,base) incl. "
         "negative x (sar) (RECORDED %d/4096: m299:169); esi fold 28*site "
         "graded %d/%d (RECORDED 2048/2048: m299:170); the sim's LiveGrid/"
         "podscan Grid folds ARE that law (both views replay through rb(x,y))"
         % (PIN_FOLD_N - bad2, PIN_FOLD_N, PIN_FOLD_N, PIN_SITE_N - bad2s,
            PIN_SITE_N))

    r1 = occ = sel_ = r3 = clsA = 0
    if live_len_ok:
        for i in range(PIN_LIVE_RECS):
            rec = lbuf[i * REC_LEN:(i + 1) * REC_LEN]
            dw = dw8(rec)
            r1 += 1 if dw & P["rung1"] else 0
            occ += 1 if dw & 0x2000 else 0
            sel_ += 1 if dw & P["rung2mask"] else 0
            r3 += 1 if dw & P["rung3"] else 0
            clsA += 1 if (rec[0] & P["dom_mask"]) >= P["dom_cmp"] else 0
    dig = hashlib.sha256(lbuf).hexdigest()[:16]
    gate("G3_recorded_census_replayed",
         live_len_ok and dig == PIN_DUMP_DIGEST and r1 == PIN_R1_CLOSE
         and occ == PIN_OCC_ALONE and sel_ == PIN_SEL_SET and r3 == PIN_R3_OPEN
         and clsA == PIN_CLS_A,
         "the model's OWN rung readers graded over the %d records of the s249 "
         "dump (digest %s, RECORDED %s: m299:173): rung1-close %d (RECORDED "
         "%d), occ-alone %d (RECORDED %d), bits26/27 %d (RECORDED %d), "
         "rung3-open %d (RECORDED %d), branch-A domain %d (RECORDED %d)"
         % (len(lbuf) // REC_LEN, dig, PIN_DUMP_DIGEST, r1, PIN_R1_CLOSE,
            occ, PIN_OCC_ALONE, sel_, PIN_SEL_SET, r3, PIN_R3_OPEN,
            clsA, PIN_CLS_A))

    uniq = all(sum(1 for hh in range(4) for dd in range(4)
                   if rungA_closed(H * 4 + hh, D * 4 + dd, rand)) == 1
               for H in range(-3, 3) for D in range(-3, 3) for rand in range(16))
    dis = 0
    if P["coef_h"] and P["coef_d"] and P["amask"]:
        for h in range(-128, 128, 5):
            for d in range(-128, 128, 7):
                for rand in range(0, 40):
                    if branchA_port(h, d, rand, P) != rungA_closed(h, d, rand):
                        dis += 1
    gate("G4_lattice_two_instruments",
         uniq and dis == 0,
         "branch A: exactly 1 hit per 16 lattice classes for all %d (H,D) x 16 "
         "rand (%d/%d) (RECORDED 36/36: m299:172); the closed form and the "
         "pin-decoded chain (coefs -%s sar(h,2) -%s sar(d,2), mask %#x) AGREE "
         "on %d (h,d,rand) draws - port: %d disagreements"
         % (PIN_THEOREM_HD, PIN_THEOREM_HD, PIN_THEOREM_HD, P["coef_h"],
            P["coef_d"], P["amask"], 256 * 256 * 40 // (5 * 7 * 40) if False
            else 255 * 37 * 40, dis))

    # G5: ladder purity + the analytic-vs-sampled quantifier agreement
    bad5 = []
    if live_len_ok:
        states = [Live(flag2000=f, rand=r, s20c=s, s210=t)
                  for f in (False, True) for r in (0, 1, 50, 272)
                  for (s, t) in ((None, None), (0, 0), (5, 9), (13, 31))]
        for i in range(PIN_LIVE_RECS):
            rec = lbuf[i * REC_LEN:(i + 1) * REC_LEN]
            x = (i % (W // 2)) * 2
            y = i // (W // 2)
            k = classify_row(x, y, rec, P)
            outs = set()
            for st in states:
                e, _ = gate_exec(x, y, rec, st, P)
                if e is not None:
                    if e not in (0, 1, 2):
                        bad5.append("eax %r out of {0,1,2}" % e)
                    outs.add(e != 0)
            if not k["pass1"] and outs - {False}:
                bad5.append("rung1 record accepted in %d" % i)
            allacc = all(st.flag2000 is not None and
                         gate_exec(x, y, rec, st, P)[0] is not None
                         for st in states) and (False not in outs)
            sampled_acc_certain = (False not in outs and
                                   all(gate_exec(x, y, rec, st, P)[0] is not None
                                       or st.flag2000 is not None
                                       for st in states))
            if k["certain"] != (k["pass1"] and k.get("sel") and k.get("r3")):
                bad5.append("certain analytic %d" % i)
        # a record is CERTAIN-accept iff pass1&sel&r3: check the sampled flag
        # states never refuse such a record, and flag-set+sel-clear never accepts.
        for i in range(PIN_LIVE_RECS):
            rec = lbuf[i * REC_LEN:(i + 1) * REC_LEN]
            dw = dw8(rec)
            if dw & P["rung1"] or not (dw & P["rung2mask"]) or not (dw & P["rung3"]):
                continue
            if gate_exec(0, 0, rec, Live(flag2000=True, rand=1, s20c=0, s210=0), P)[0] == 0:
                bad5.append("certain refused %d" % i)
            if gate_exec(0, 0, rec, Live(flag2000=False, rand=None), P)[0] == 0:
                bad5.append("certain refused flag0 %d" % i)
            if gate_exec(0, 0, rec, Live(flag2000=True, rand=1, s20c=0, s210=0), P)[0] != 2:
                bad5.append("certain flagset eax!=2 %d" % i)
    n_certain_dump = sum(
        1 for i in range(PIN_LIVE_RECS)
        if not (dw8(lbuf[i * REC_LEN:(i + 1) * REC_LEN]) & P["rung1"])
        and (dw8(lbuf[i * REC_LEN:(i + 1) * REC_LEN]) & P["rung2mask"])
        and (dw8(lbuf[i * REC_LEN:(i + 1) * REC_LEN]) & P["rung3"])) if live_len_ok else -1
    gate("G5_ladder_purity_quantifiers",
         live_len_ok and not bad5 and len(P["rets"]) == 6
         and P["callee_stores"] == 0 and P["pops_preserve"],
         "model outputs stayed in {0,1,2} over %d records x %d sampled live "
         "states; rung1 CLOSES the gate in every state (the pinned je leg); "
         "the CERTAIN-accept class (pass1 & bits26/27 & bit28: %d records in "
         "the dump) accepts under flag-set (eax=2) AND flag-clear (eax=1) - "
         "eax=1 is only REACHABLE through the flag-clear legs (pinned: the "
         "rung2 block returns before the 0x10000000 test - the mov-eax-1 "
         "returns sit at/after rung3); rival 'eax==2 is the accept value' "
         "sees %d rung3-open records (RECORDED %d) as refusals%s"
         % (PIN_LIVE_RECS, 2 * 4 * 4, n_certain_dump, n_certain_dump,
            PIN_R3_OPEN, "" if not bad5 else " BAD " + "; ".join(bad5[:3])))

    c_reach = sum(1 for r in m300rows if r["reach"].startswith("REACHES"))
    c_inw = sum(1 for r in m300rows if r["reach"] == "IN-WRITER")
    c_noreach = sum(1 for r in m300rows if r["reach"] == "CANNOT-REACH")
    c_truth = sum(1 for r in m300rows if "truth-branch" in r["cls"])
    c_stored = sum(1 for r in m300rows if r["cls"] == "stored-to-memory")
    c_ebx = sum(1 for r in m300rows if r["cls"] == "into-ebx")
    inw = [r for r in m300rows if r["reach"] == "IN-WRITER"]
    je_t = w1.get(P["je_addr"], ("", ""))[1]
    tt_t = w1.get(P["je_addr"] - 2, ("", ""))[1]
    gate("G6_m300_census_regrade",
         len(m300rows) == PIN_SITES and c_truth == PIN_CLS_TRUTH
         and c_stored == PIN_CLS_STORED and c_ebx == PIN_CLS_EBX
         and c_reach == PIN_REACH and c_inw == PIN_INWRITER
         and c_noreach == PIN_NOREACH and len(inw) == 1
         and inw[0]["va"] == P["call_addr"] and inw[0]["fn"] == "FUN_0051dcb0"
         and "test @0x51e005" in inw[0]["use"] and tt_t == "test   eax,eax"
         and je_t == "je     0x51e11d",
         "%d/%d call-site rows re-parsed from %s: classes %d truth-branch / %d "
         "stored-to-memory / %d into-ebx (RECORDED %d/%d/%d), reach %d REACHES "
         "/ %d IN-WRITER / %d CANNOT-REACH (RECORDED %d/%d/%d: m300:1-36); the "
         "single IN-WRITER row (call@0x%x in FUN_0051dcb0) agrees with the "
         "pinned bytes: consumption 'test eax,eax' @0x51e005 and '%s' @0x51e007 "
         "skip the inc block 0x51e00d-0x51e01b WHOLE - the counter has exactly "
         "ONE writer and %d callers cannot reach it at all"
         % (len(m300rows), PIN_SITES, os.path.basename(m300), c_truth,
            c_stored, c_ebx, PIN_CLS_TRUTH, PIN_CLS_STORED, PIN_CLS_EBX,
            c_reach, c_inw, c_noreach, PIN_REACH, PIN_INWRITER, PIN_NOREACH,
            inw[0]["va"] if inw else 0, je_t, c_noreach))

    recmentions = [a for a in sorted(w1) if P["call_addr"] + 5 <= a <= 0x51E035
                   and "eax" in w1[a][1]]
    mine = ["0x%x `%s`" % (a, w1[a][1]) for a in recmentions]
    je_leg = w1.get(0x51DFD1, ("", ""))[1]
    gate("G7_m301_structure_regrade",
         mine == m301_mentions and m301_back == 0
         and je_leg == "je     0x51dff5" and P["je_addr"] == 0x51E007
         and 0x51DFD1 and all(a < P["call_addr"] for a in recmentions[:1])
         and "ebx" not in w1[0x51E00D][1] and "esi" in w1[0x51E00D][1],
         "re-derived from the W1 BYTES vs the m301 witness: eax mentions after "
         "the call (to 0x51e035) EQUAL the recorded %d-item list %s; backward "
         "branches into the 0x51de2c-0x51df1d walk range: %d (RECORDED %d: "
         "m301 A6); the ebx-driven branch '%s' @0x51dfd1 lands on 0x51dff5 = "
         "the block BEFORE the call, so the ebx==0 leg STILL calls 0x5832b0 and "
         "the counter block operands (0x51e00d/0x51e01b) mention esi only - the "
         "ebx walk gates the CELL store, never the increment%s"
         % (len(mine), mine, m301_back, 0, je_leg,
            "" if mine == m301_mentions else " MISMATCH vs %s" % m301_mentions))

    nsites_ok = dict(collections.Counter(
        sgt.site_of(g.rb(e["y"], e["x"])) for (_, _, _, e) in rows))
    tsum = cnt_save.total("rows")
    kinds = cnt_save.kinds
    part_ok = (kinds["rung1"] + kinds["certain-accept"] + kinds["flag-or-lattice"]
               + kinds["flag-or-1"] + kinds.get("branchA", 0)
               + kinds.get("branchB", 0) == tsum)
    L("")
    gate("G8_executable_replay_rows",
         tsum == ANCHORS["rows"] == len(rows) and len(vis) and
         nsites_ok == ANCHORS["site_hist_save"] and part_ok
         and cnt_save.total("refuse") + cnt_save.total("possible") == tsum
         and cnt_save.total("possible") >= cnt_save.total("certain")
         and cnt_save.total("certain") == kinds["certain-accept"],
         "%d rows / %d visits / %d distinct tiles replayed through the "
         "UNMODELED-live-aware gate (B17 loader + B16 transposition + B18 "
         "site_of law): per-site rows %s (RECORDED B18 anchor %s - the counter "
         "table and the MAX table are the SAME slots, +0 vs +4); class census "
         "%s partitions the rows exactly; %d rows CERTAINLY refuse (rung1) and "
         "%d certainly accept (bits26/27 AND bit28: accepted whatever the "
         "never-dumped 0x985ac4 bit says); %d rows are live-state-UNDECIDED, "
         "every one accept-POSSIBLE; the baseline column (%s) adds %d eax=1 + "
         "%d eax=2 accepts and leaves %d branch-B rows undecided"
         % (tsum, ANCHORS["visits"], ANCHORS["tiles"], dict(sorted(nsites_ok.items())),
            ANCHORS["site_hist_save"], dict(sorted(kinds.items())),
            cnt_save.total("refuse"), cnt_save.total("certain"),
            cnt_save.total("rows") - cnt_save.total("refuse")
            - cnt_save.total("certain"),
            BASELINE.label(), cnt_save.total("eax1"), cnt_save.total("eax2"),
            cnt_save.total("base_undec")))

    ungated = dict((s, cnt_save.t[s]["rows"]) for s in cnt_save.t)
    aliased_at0 = P["cnt_disp"] != 0x989CE8
    flag_polarity_rival = Live(flag2000=True, rand=1, s20c=0, s210=0)
    sel_clear_flag_accepts = sum(
        1 for i in range(PIN_LIVE_RECS)
        if (dw8(lbuf[i * REC_LEN:(i + 1) * REC_LEN]) & P["rung1"]) == 0
        and (dw8(lbuf[i * REC_LEN:(i + 1) * REC_LEN]) & P["rung2mask"]) == 0
        and gate_exec(0, 0, lbuf[i * REC_LEN:(i + 1) * REC_LEN],
                      flag_polarity_rival, P)[0] != 0) if live_len_ok else -1
    ebx_rival_targets_call_after = not (w1.get(0x51DFD1, ("", ""))[1]
                                        == "je     0x51dff5"
                                        and 0x51DFD1 < 0x51DFFD)
    gate("G9_rivals_fail_same_fit",
         cnt_save.total("certain") < cnt_save.total("possible")
         and cnt_save.total("possible") < ungated[1] + ungated[9]
         and not aliased_at0 and sel_clear_flag_accepts == 0
         and not ebx_rival_targets_call_after,
         "rivals: (a) 'the counter++ is UNGATED' predicts %s - the pinned je "
         "0x51e11d and the %d certain-rung1-refuse rows contradict it; (b) "
         "'the counter aliases the MAX field at [esi+0x989ce8]' contradicts the "
         "DECODED operand %#x (+%d - a distinct field of the same 28-B slot); "
         "(c) 'flag-set with bits26/27 CLEAR accepts' (reading neg/sbb wrong) "
         "fires on %d/%d dump records under the decoded leg (must be 0); (d) "
         "'the ebx walk gates the call' (M301 REFUTED) is contradicted by the "
         "je 0x51dff5 landing BEFORE 0x51dffd"
         % (ungated, cnt_save.total("refuse"), P["cnt_disp"], P["counter_off"],
            sel_clear_flag_accepts, PIN_LIVE_RECS))

    nbad = sum(1 for _, ok in R if not ok)
    L("")
    L("%sB19: %d/%d gates - the slot [+4] visit counter is EXECUTABLE: per "
      "recorded visit the gate FUN_005832b0 (44-B ladder, flag/rung3/branch-A "
      "lattice/branch-B classes) decides inc/no-inc, and %d visits land %d "
      "certain + %d baseline + <= %d possible increments over sites %s; live "
      "VALUES (rand+1, both strides, 0x985ac4 bit) and the counter CONTENTS "
      "stayed DECLARED UNMODELED%s"
      % ("FAIL " if nbad else "PASS ", len(R) - nbad, len(R), tsum,
         cnt_save.total("certain"), cnt_save.total("eax1") + cnt_save.total("eax2"),
         cnt_save.total("possible"), sorted(cnt_save.t),
         "" if not nbad else " - FAILING: " + "; ".join(n for n, ok in R if not ok)))
    return 0 if not nbad else 1


def acceptance(sav_path, results, raw=DEF_RAW, bin_path=DEF_BIN):
    """run report(), re-deriving each gate's pass flag from the printed lines
    (the table-then-assertion order is the report's own)."""
    lines = []
    rc = report(sav_path, raw_path=raw, bin_path=bin_path,
                out=collections.namedtuple("Cap", "write")(
                    write=lines.append))
    for ln in lines:
        m = re.match(r"^(G\d+)_\S+\s+\s*(PASS|FAIL)", ln)
        if m:
            results.append((ln.split()[0], m.group(2) == "PASS"))
        elif ln.startswith("==") or ln.startswith("site ") or ln.startswith(
                "per-site") or ln.startswith("state ") or ln.startswith("class"):
            print(ln)
        elif len(ln.split()) >= 6 and re.match(r"^\d+\s+\d+$", " ".join(ln.split()[1:3])):
            pass
    print("\n".join(ln for ln in lines if re.match(r"^(site |G\d|state|per-site|class|%s)"
                                                   .replace("%s", "$"), ln)))
    return rc


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sim.visitcounter")
    ap.add_argument("--sav", default=DEF_SAV)
    ap.add_argument("--raw", default=DEF_RAW)
    ap.add_argument("--bin", default=DEF_BIN)
    ap.add_argument("--out", help="write the report to this file")
    a = ap.parse_args(argv)
    if a.out:
        with open(a.out, "w") as f:
            report(a.sav, raw_path=a.raw, bin_path=a.bin, out=f)
        return 0
    return report(a.sav, raw_path=a.raw, bin_path=a.bin)


if __name__ == "__main__":
    sys.exit(main())
