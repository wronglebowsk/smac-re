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
domain 1087 over 2048 records (:173); call sites 24, 21/2/1 and 17/1/6
(m300_callers.txt S2); the A6 eax-witness and 0 backward edges
(m301_ebxtable.txt). FIRST-MEASUREMENT ANCHORS (this fire, reproducible from
the shipped artifacts; they lock the replay, they are not prior claims): the
ANCHORS dict below - "rec" rows are RECORDED elsewhere, "this" rows are this
fire's anchors.

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
CALLER = 0x51DCB0              # owner of the [+4] write
CALLEE = 0x5832B0              # FUN_005832b0
# recorded pins (evidence/m299_visitgate.txt - see docstring for :line cites)
PIN_W1_LINES = 44
PIN_W2_LINES = 114
PIN_W1_END = 0x51E02C
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
PIN_RET_COUNT = 6
# recorded pins (evidence/m300_callers.txt S2)
PIN_SITES = 24
PIN_CLS_TRUTH = 21
PIN_CLS_STORED = 2
PIN_CLS_EBX = 1
PIN_REACH = 17
PIN_INWRITER = 1
PIN_NOREACH = 6
# first-measurement anchors (this fire): the class census and the per-site
# counter columns over the recorded rows, save record view, under the DECLARED
# baseline Live state. site_hist_save is B18's RECORDED anchor (G7/PIN_SITE_ROWS).
ANCHORS = {
    "rows": 2321, "visits": 1026, "tiles": 101,
    "site_hist_save": {1: 2253, 9: 68},
    "kinds": {"branchA": 1099, "rung1": 1222}, "refuse": 1222,
    "certain": 0, "eax1": 0, "eax2": 20, "undec": 1079, "possible": 1099,
}


# --------------------------------------------------------------------------
# the evidence windows: the pinned disassembly INSIDE the evidence file is the
# instruction source (B18's PINS discipline, read out of the M299 log itself).
# --------------------------------------------------------------------------
INS_RX = re.compile(r"^\s+([0-9a-f]{6}):\t([0-9a-f ]+?)\t(.+?)\s*$")
M300_RX = re.compile(
    r"^(0x[0-9a-f]{6})\s+(FUN_[0-9a-f]+)\s+(.*?)\s+"
    r"(REACHES(?:\([^)]*\))?|IN-WRITER|CANNOT-REACH)\s+(.*)$")


def norm(t):
    return " ".join(t.split())


def parse_windows(path):
    """-> (w1, w2, n1, n2): addr->(bytes,text) maps + the recorded line counts
    from the '44 lines ...' / '114 lines ...' headers."""
    w1, w2, n1, n2 = {}, {}, None, None
    cur = None
    for ln in open(path, errors="replace"):
        hdr = re.match(r"^(\d+) lines (0x[0-9a-f]+)-(0x[0-9a-f]+)", ln.strip())
        if hdr:
            n, lo = int(hdr.group(1)), int(hdr.group(2), 16)
            if lo <= 0x51E000:
                n1, cur = n, w1
            else:
                n2, cur = n, w2
            continue
        m = INS_RX.match(ln)
        if m and cur is not None:
            cur[int(m.group(1), 16)] = (m.group(2).strip(), m.group(3))
    return w1, w2, n1, n2


def decode_pins(w1, w2):
    """Read EVERY model constant out of the pinned instruction texts. Pins use
    ADDRESS ADJACENCY OF THE ORDERED INSTRUCTIONS (instruction lengths differ,
    so addr+1 arithmetic would miss). Any pin that does not resolve decodes to
    None and fails G1 - never a hardcoded fallback."""
    P = {}
    a2 = sorted(w2)
    ix = dict((a, i) for i, a in enumerate(a2))

    def nxt(a, k=1):
        j = ix.get(a, -2) + k
        return a2[j] if 0 <= j < len(a2) else None

    def ins(w, a):
        return w[a][1] if a in w else ""

    # W1 the gate five: call / test / je / counter load / inc / counter store
    a1 = sorted(w1)
    ix1 = dict((a, i) for i, a in enumerate(a1))

    def nxt1(a, k=1):
        j = ix1.get(a, -2) + k
        return a1[j] if 0 <= j < len(a1) else None
    P["call_addr"] = next((a for a in a1 if ins(w1, a).startswith("call")),
                          None)
    cb = w1.get(P["call_addr"], ("", ""))[0].split()
    P["callee_target"] = (P["call_addr"] + 5 + int.from_bytes(
        bytes.fromhex(" ".join(cb[1:5])), "little")
        if len(cb) == 5 and cb[0] == "e8" else None)
    # the GATED je: the TEST-then-JE pair that consumes the call's eax (the
    # window has exactly one `test eax,eax` - structural decode, not a pin)
    tt = next((a for a in a1 if norm(ins(w1, a)) == "test eax,eax"), None)
    P["je_addr"] = nxt1(tt) if tt is not None else None
    jt = ins(w1, P["je_addr"]).split()
    P["je_target"] = int(jt[-1], 16) if (
        jt and jt[0].startswith("je") and jt[-1].startswith("0x")) else None
    # W1 esi fold 0x51dfb1 lea esi,[eax*8+0x0] / sub esi,ecx / shl esi,0x2
    P["slot_stride"] = None
    for a in a1:
        m = re.match(r"lea\s+esi,\[eax\*(\d+)\+0x0\]$", ins(w1, a))
        if m:
            mul = int(m.group(1))
            b = nxt1(a)
            m2 = re.match(r"shl\s+esi,0x([0-9a-f])$", ins(w1, nxt1(b))) \
                if b is not None else None
            if b is not None and norm(ins(w1, b)) == "sub esi,ecx" and m2:
                P["slot_stride"] = (mul - 1) << int(m2.group(1), 16)
    # [esi+disp] operands: MAX store (,eax) 0x51dfcb; counter load 0x51e00d,
    # inc 0x51e01a, store (,ecx) 0x51e01b
    P["max_disp"] = None
    P["cnt_disp"] = None
    P["inc_addr"] = None
    for a in sorted(w1):
        m = re.match(r"mov\s+DWORD PTR \[esi\+(0x[0-9a-f]+)\],eax$", ins(w1, a))
        if m:
            P["max_disp"] = int(m.group(1), 16)
        m = re.match(r"mov\s+ecx,DWORD PTR \[esi\+(0x[0-9a-f]+)\]$", ins(w1, a))
        if m:
            P["cnt_disp"] = int(m.group(1), 16)
        if ins(w1, a) == "inc    ecx":
            P["inc_addr"] = a
    P["counter_off"] = (P["cnt_disp"] - P["max_disp"]) if (
        P["max_disp"] is not None and P["cnt_disp"] is not None) else None
    # W2 the ladder: rung masks + the flag/rand/stride globals + domains
    def imm(a, rx):
        m = re.match(rx, ins(w2, a))
        return int(m.group(1), 16) if m else None
    P["rung1"] = imm(0x5832DC, r"test\s+eax,(0x[0-9a-f]+)$")
    m = re.match(r"test\s+DWORD PTR ds:(0x[0-9a-f]+),(0x[0-9a-f]+)$",
                 ins(w2, 0x5832EA))
    P["flag_addr"], P["flag_bit"] = ((int(m.group(1), 16), int(m.group(2), 16))
                                      if m else (None, None))
    P["rung2mask"] = imm(0x5832F6, r"and\s+eax,(0x[0-9a-f]+)$")
    P["rung3"] = imm(0x583307, r"test\s+eax,(0x[0-9a-f]+)$")
    m = re.match(r"mov\s+edi,DWORD PTR ds:(0x[0-9a-f]+)$", ins(w2, 0x583318))
    P["rand_addr"] = int(m.group(1), 16) if m else None
    P["dom_mask"] = imm(0x583331, r"and\s+al,(0x[0-9a-f]+)$")
    P["dom_cmp"] = imm(0x583335, r"cmp\s+eax,(0x[0-9a-f]+)$")
    P["amask"] = imm(0x58335E, r"and\s+ebx,(0x[0-9a-f]+)$")
    P["bmask"] = imm(0x5833A7, r"and\s+edx,(0x[0-9a-f]+)$")

    def gaddr(a, rx):
        m = re.match(rx, ins(w2, a))
        return int(m.group(1), 16) if m else None
    P["s210"] = gaddr(0x58338B, r"imul\s+ebx,DWORD PTR ds:(0x[0-9a-f]+)$")
    P["s20c"] = gaddr(0x583399, r"imul\s+eax,DWORD PTR ds:(0x[0-9a-f]+)$")
    P["mult_g"] = gaddr(0x5832B3, r"mov\s+eax,(?:DWORD PTR )?ds:(0x[0-9a-f]+)$")
    P["tv_base_g"] = gaddr(0x5832D0, r"mov\s+edx,DWORD PTR ds:(0x[0-9a-f]+)$")
    P["rec_byte0"] = bool(re.match(r"mov\s+al,BYTE PTR \[edx\]$",
                                   ins(w2, 0x58332D)))
    # branch-A lattice coefficients, ORDERED-INSTRUCTION adjacency:
    #   neg ebx / shl ebx,S / sub ebx,eax        -> coef_h = 2^S + 1 (h>>2 leg)
    #   lea edx,[eax+eax*K] ... sub ebx,edx     -> coef_d = K + 1     (d>>2 leg)
    P["coef_h"] = P["coef_d"] = None
    for a in a2:
        if ins(w2, a) == "neg ebx" or norm(ins(w2, a)) == "neg ebx":
            s = re.match(r"shl\s+ebx,0x([0-9a-f])$", norm(ins(w2, nxt(a))))
            if s and norm(ins(w2, nxt(a, 2))) == "sub ebx,eax":
                P["coef_h"] = (1 << int(s.group(1), 16)) + 1
    for a in a2:
        m = re.match(r"lea\s+edx,\[eax\+eax\*(\d)\]$", norm(ins(w2, a)))
        if m:
            for k in range(1, 13):
                if norm(ins(w2, nxt(a, k))) == "sub ebx,edx":
                    P["coef_d"] = int(m.group(1)) + 1
                    break
    # purity: the six rets, zero memory stores, pops precede every ret, and
    # the STATIC eax values the rets can deliver
    P["rets"] = [a for a in a2 if norm(ins(w2, a)) == "ret"]
    P["callee_stores"] = sum(
        1 for a in a2
        if re.match(r"mov\s+(BYTE|WORD|DWORD) PTR \[[^\]]+\],", norm(ins(w2, a))))
    preserved = True
    for r in P["rets"]:
        look = " ".join(norm(ins(w2, b))
                        for b in a2[max(0, ix[r] - 9):ix[r]])
        if not all(p in look for p in ("pop edi", "pop esi", "pop ebx")):
            preserved = False
    P["pops_preserve"] = preserved
    P["ret_vals"] = set()
    for r in P["rets"]:
        look = " ".join(norm(ins(w2, b)) for b in a2[max(0, ix[r] - 9):ix[r]])
        m = re.search(r"mov eax,0x([0-9a-f])", look)
        if m:
            P["ret_vals"].add(int(m.group(1), 16))
        elif "xor eax,eax" in look or "sete" in look:
            P["ret_vals"].add(0)
    # eax==1 legs (mov eax,0x1 / sete of the parity cmp) sit STRICTLY AFTER
    # the flag-set rung-2 block returns - read out of the byte order:
    P["one_after_flagblock"] = all(a > 0x583306 for a in a2
                                   if "mov eax,0x1" in norm(ins(w2, a)))
    return P


# --------------------------------------------------------------------------
# the ladder, executable. TWO independent implementations (skill law: pair
# instruments that can fail DIFFERENTLY): gate_exec ports the pinned chain by
# the decoded coefficients; rungA_closed is M299's recorded closed form and
# the recorded 36/36 lattice theorem grades it. G4 grades the pair equal.
# --------------------------------------------------------------------------
M32 = 0xFFFFFFFF


def s32(v):
    v &= M32
    return v - 0x100000000 if v >= 0x80000000 else v


def sar_i(v, n):
    return s32(v) >> n


def trunc4(v):
    """the pinned cdq / and edx,3 / add / sar 2 legs (0x583377-0x583388):
    division by 4 TRUNCATED toward zero."""
    v = s32(v)
    return (v + (3 if v < 0 else 0)) >> 2


def rungA_closed(h, d, rand):
    """M299's RECORDED closed form (scripts/m299_visitgate.py rungA): hit iff
    (h&3) + 4*(d&3) == (-5*(h>>2) - 3*(d>>2) + rand) & 0xf."""
    ebx = (-5 * (h >> 2) - 3 * (d >> 2) + rand) & 0xF
    return ((h & 3) + 4 * (d & 3)) == ebx


def branchA_port(h, d, rand, P):
    """the SAME branch A ported from the pinned chain via the DECODED
    coefficients (0x58333a-0x583366)."""
    ebx = (-P["coef_h"] * sar_i(h, 2) - P["coef_d"] * sar_i(d, 2)
           + rand) & P["amask"]
    return (h & 3) + 4 * (d & 3) == ebx


def a_target(h, d, P):
    """the residue class of (rand & 0xf) that makes branch A hit."""
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
        return "flag2000=%s rand=%s s20c=%s s210=%s" % (
            self.flag2000, self.rand, self.s20c, self.s210)


BASELINE = Live(flag2000=False, rand=1, s20c=None, s210=None)


def dw8(rec):
    return int.from_bytes(rec[8:12], "little")


def gate_exec(x, y, rec, live, P):
    """one FUN_005832b0(x, y) evaluation over the record bytes. Returns
    (eax_or_None, path): None means an UNMODELED live global decided the leg.
    The order is the pinned W2 order, leg by leg."""
    dw = dw8(rec)
    if dw & P["rung1"]:
        return 0, "rung1"
    sel = bool(dw & P["rung2mask"])
    if live.flag2000 is None:
        return None, "rung2-flag-unknown"
    if live.flag2000:
        # and 0xc000000 / neg / sbb (CF = sel) / and 2  ->  2 or 0
        return (2 if sel else 0), "rung2-flagset"
    if dw & P["rung3"]:
        return 1, "rung3"
    if live.rand is None:
        return None, "rand-unknown"
    if live.rand == 0:
        return 0, "rand-zero"
    h = sar_i(x + y, 1)
    d = x - h
    if (rec[0] & P["dom_mask"]) >= P["dom_cmp"] and branchA_port(h, d, live.rand, P):
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
    everything else is UNDECIDED and accept-POSSIBLE (the flag value, the
    rand residue class, or the strides can be made to accept - branch A by
    rand mod 16 == target, branch B by any stride pair)."""
    dw = dw8(rec)
    out = {"pass1": not (dw & P["rung1"])}
    if not out["pass1"]:
        out["kind"] = "rung1"
        return out
    sel = bool(dw & P["rung2mask"])
    r3 = bool(dw & P["rung3"])
    h = sar_i(x + y, 1)
    d = x - h
    a_dom = (rec[0] & P["dom_mask"]) >= P["dom_cmp"]
    out.update({"sel": sel, "r3": r3, "a_domain": a_dom})
    if a_dom:
        out["a_target"] = a_target(h, d, P)
    if sel and r3:
        out["kind"] = "certain-accept"
    elif sel:
        out["kind"] = "flag-or-lattice"
    elif r3:
        out["kind"] = "flag-or-1"
    else:
        out["kind"] = "branchA" if a_dom else "branchB"
    return out


class VisitCounter(object):
    """the counter table: per site the rows seen and the count columns, in
    the order the game RUNS them: the gate call at 0x51dffd FIRST, the inc
    block 0x51e00d-0x51e01b on eax != 0 only, at [0x989ce8 + 28*site + 4]."""

    FIELDS = ("rows", "refuse", "certain", "possible", "eax1", "eax2",
              "refuse_base", "undec_base", "a_domain", "flag_dep")

    def __init__(self):
        self.t = collections.defaultdict(
            lambda: dict((f, 0) for f in self.FIELDS))
        self.kinds = collections.Counter()

    def visit(self, x, y, rec, site, live, P):
        """one FUN_0051dcb0 visit at (x, y); site = BYTE[rec+3] (B18 law).
        Returns (eax, kind); the [+4] increment lands iff eax != 0."""
        t = self.t[site]
        t["rows"] += 1
        k = classify_row(x, y, rec, P)
        self.kinds[k["kind"]] += 1
        if not k["pass1"]:
            t["refuse"] += 1
        else:
            t["possible"] += 1
            t["a_domain"] += 1 if k.get("a_domain") else 0
            t["flag_dep"] += 1 if not (k.get("sel") and k.get("r3")) else 0
            if k["kind"] == "certain-accept":
                t["certain"] += 1
        eax, _path = gate_exec(x, y, rec, live, P)
        if eax == 1:
            t["eax1"] += 1
        elif eax == 2:
            t["eax2"] += 1
        elif eax == 0:
            t["refuse_base"] += 1
        else:
            t["undec_base"] += 1
        return eax, k["kind"]

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
# evidence-table parsers (m300 S2, m301 A6) - graded against the byte window
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
    """-> (recorded eax-mention list, recorded backward-edge count)."""
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
# the report: TABLE FIRST, gates after (print order == assertion order)
# --------------------------------------------------------------------------
def build(sav_path, raw_path=DEF_RAW, bin_path=DEF_BIN, m299=DEF_M299,
          m300=DEF_M300, m301=DEF_M301):
    """compute everything; -> dict of facts + gate list [(name, ok, detail)]."""
    sav = sosave.parse(sav_path)
    g = pc.Grid(sav)
    W = sav.width
    lbuf = open(bin_path, "rb").read()
    live_len_ok = len(lbuf) == REC_LEN * PIN_LIVE_RECS
    lg = sgt.LiveGrid(lbuf, W // 2)
    vis = sl.load_visits(raw_path)
    rows = sgt.graded_rows(vis)
    w1, w2, n1, n2 = parse_windows(m299)
    P = decode_pins(w1, w2)
    m300rows = parse_m300(m300)
    m301_mentions, m301_back = parse_m301_a6(m301)

    def replay(grid):
        c = VisitCounter()
        tiles = set()
        for (vi, u, s, e) in rows:
            X, Y = e["y"], e["x"]           # B16 transposition law
            rec = grid.rb(X, Y)
            c.visit(X, Y, rec, sgt.site_of(rec), BASELINE, P)
            tiles.add((X, Y))
        return c, len(tiles)

    cnt_save, n_tiles = replay(g)
    cnt_live = replay(lg)[0] if live_len_ok else None
    return {"sav": sav, "W": W, "g": g, "lg": lg, "lbuf": lbuf,
            "live_len_ok": live_len_ok, "vis": vis, "rows": rows,
            "w1": w1, "w2": w2, "n1": n1, "n2": n2, "P": P,
            "m300rows": m300rows, "m301_mentions": m301_mentions,
            "m301_back": m301_back, "cnt_save": cnt_save,
            "cnt_live": cnt_live, "n_tiles": n_tiles}


def table_lines(F):
    cnt = F["cnt_save"]
    P = F["P"]
    L = []
    L.append("== B19 the slot [+4] visit counter, EXECUTED over the recorded "
             "%d rows (%d visits, %d tiles; B17 loader + B16 transposition + "
             "B18 site law) ==" % (len(F["rows"]), len(
                 set(vi for (vi, _, _, _) in F["rows"])), F["n_tiles"]))
    L.append("state DECLARED baseline (live VALUES unmodeled): %s"
             % BASELINE.label())
    L.append("counter columns per site: rows seen; refuse = CERTAIN refusal "
             "(rung1, no live state accepts); certain = CERTAIN accept (bits "
             "26/27 AND bit 28 - accepted under EVERY flag state); possible = "
             "accepts in SOME live state (bracket upper bound); eax1/eax2/"
             "refuse_base/undec_base = the baseline column (eax of the gate "
             "call; [+4]++ lands iff eax in {1,2})")
    L.append("%6s %6s %8s %8s %8s %6s %6s %11s %10s %8s %9s" % (
        "site", "rows", "refuse", "certain", "possible", "eax1", "eax2",
        "refuse_base", "undec_base", "a_dom", "flag_dep"))
    for s in sorted(cnt.t):
        t = cnt.t[s]
        L.append("%6d %6d %8d %8d %8d %6d %6d %11d %10d %8d %9d" % (
            s, t["rows"], t["refuse"], t["certain"], t["possible"], t["eax1"],
            t["eax2"], t["refuse_base"], t["undec_base"], t["a_domain"],
            t["flag_dep"]))
    L.append("digest %s | class census (kind -> rows): %s" % (
        cnt.digest(),
        dict(sorted(cnt.kinds.items()))))
    if F["cnt_live"] is not None:
        dsum = sum(cnt_save_field_delta(F, f) for f in VisitCounter.FIELDS)
        L.append("save-vs-live record-view divergence over the same rows: "
                 "%d total field deltas across the two views' counter tables"
                 % dsum)
    L.append("")
    return L


def cnt_save_field_delta(F, f):
    a, b = F["cnt_save"], F["cnt_live"]
    ks = set(a.t) | set(b.t)
    return sum(abs(a.t[k][f] - b.t[k][f]) for k in ks
               if k in a.t and k in b.t)


def gates(F):
    R = []
    P = F["P"]
    w1, w2 = F["w1"], F["w2"]
    cnt = F["cnt_save"]
    rows = F["rows"]
    lbuf = F["lbuf"]

    def gate(name, ok, detail):
        R.append((name, bool(ok), detail))

    # ---- G1 the evidence windows and every constant decoded from the bytes
    bad1 = []
    if F["n1"] != PIN_W1_LINES or F["n2"] != PIN_W2_LINES:
        bad1.append("headers %s/%s != %d/%d" % (F["n1"], F["n2"],
                                                PIN_W1_LINES, PIN_W2_LINES))
    if len(w1) != PIN_W1_LINES or len(w2) != PIN_W2_LINES:
        bad1.append("parsed %d/%d" % (len(w1), len(w2)))
    if P["callee_target"] != CALLEE or P["call_addr"] != 0x51DFFD:
        bad1.append("gate call %s -> %s" % (P["call_addr"], P["callee_target"]))
    if P["je_addr"] != 0x51E007 or P["je_target"] != 0x51E11D:
        bad1.append("je %s -> %s" % (P["je_addr"], P["je_target"]))
    if P["inc_addr"] != 0x51E01A:
        bad1.append("inc %s" % P["inc_addr"])
    want = {"rung1": 0x102000, "rung2mask": 0xC000000, "rung3": 0x10000000,
            "flag_addr": 0x985AC4, "flag_bit": 0x2000, "rand_addr": 0x92A380,
            "s210": 0x692210, "s20c": 0x69220C, "dom_mask": 0xE0,
            "dom_cmp": 0x60, "amask": 0xF, "bmask": 0x1F, "slot_stride": 28,
            "counter_off": 4, "coef_h": 5, "coef_d": 3, "mult_g": 0x692184,
            "tv_base_g": 0x92AE14, "cnt_disp": 0x989CEC, "max_disp": 0x989CE8}
    for k, v in want.items():
        if P.get(k) != v:
            bad1.append("%s=%r != %s" % (k, P.get(k),
                                         hex(v) if isinstance(v, int) else v))
    gate("G1_evidence_windows_pins",
         not bad1 and len(P["rets"]) == PIN_RET_COUNT
         and P["callee_stores"] == 0 and P["pops_preserve"]
         and P["ret_vals"] <= {0, 1, 2} and P["one_after_flagblock"],
         "%d + %d pinned instructions parsed from %s (headers '44/114 lines' "
         "RECORDED :5,:52); the call's rel32 BYTES decode to 0x5832b0 @0x51dffd; "
         "the counter operand DECODES to [esi+0x989cec] = the MAX operand "
         "[esi+0x989ce8] +%s - the [+4] FIELD of the slot, not a second slot "
         "(the 28-B stride decodes from the pinned lea/sub/shl chain as %s*site); "
         "EVERY model constant read out of the texts: rung1 %#x, flag %#x @%#x, "
         "sel %#x, rung3 %#x, rand %#x, strides %#x/%#x, domain %#x>=%#x, "
         "masks %#x/%#x, lattice coefs -%s*sar(h,2) -%s*sar(d,2); callee purity: "
         "%d rets (RECORDED 6 :171), %d memory stores, 3 pops precede EVERY ret "
         "%s, static ret values %s, and the eax==1 legs sit AFTER the flag-set "
         "block returns (so eax=1 is flag-clear-only) %s%s"
         % (len(w1), len(w2), os.path.basename(DEF_M299), P["counter_off"],
            P["slot_stride"], P["rung1"], P["flag_bit"], P["flag_addr"],
            P["rung2mask"], P["rung3"], P["rand_addr"], P["s20c"], P["s210"],
            P["dom_mask"], P["dom_cmp"], P["amask"], P["bmask"], P["coef_h"],
            P["coef_d"], len(P["rets"]), P["callee_stores"],
            P["pops_preserve"], sorted(P["ret_vals"]),
            P["one_after_flagblock"],
            "" if not bad1 else " BAD " + "; ".join(bad1[:4])))

    # ---- G2 the folds re-verified on the recorded N
    random.seed(299)
    bad2 = 0
    for _ in range(PIN_FOLD_N):
        x = random.choice([random.randrange(0, 4096), -random.randrange(1, 4096)])
        y = random.randrange(0, 256)
        w2r = random.randrange(20, 200)
        base = random.randrange(0x10000, 0x0FFFFFFF)
        eax = (w2r * y + sar_i(x, 1)) & M32
        dec = (base + (((eax + (eax + eax * 4) * 2) & M32) * 4)) & M32
        if dec != (base + 44 * (w2r * y + sar_i(x, 1))) & M32:
            bad2 += 1
    bad2s = 0
    for _ in range(PIN_SITE_N):
        site = random.randrange(0, 128)
        if ((((site * 8) - site) & M32) << 2) & M32 != (28 * site) & M32:
            bad2s += 1
    gate("G2_fold_laws_reverified", bad2 == 0 and bad2s == 0,
         "the callee's pinned fold chain (imul ds:0x692184, sar(x,1), lea*5, "
         "lea*11, [base+eax*4]) equals 44*(W2*y+sar(x,1)) on %d/%d random "
         "(x,y,W2,base) draws incl. negative x (sar) - RECORDED 4096/4096 "
         ":169; the slot fold lea[esi*8]/sub/shl equals 28*site on %d/%d sites "
         "- RECORDED 2048/2048 :170; both record views replay through exactly "
         "this fold (LiveGrid.rb == podscan Grid.rb)"
         % (PIN_FOLD_N - bad2, PIN_FOLD_N, PIN_SITE_N - bad2s, PIN_SITE_N))

    # ---- G3 the recorded rung census over the s249 dump
    r1 = occ = sel_ = r3 = clsA = 0
    if F["live_len_ok"]:
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
         F["live_len_ok"] and dig == PIN_DUMP_DIGEST and r1 == PIN_R1_CLOSE
         and occ == PIN_OCC_ALONE and sel_ == PIN_SEL_SET
         and r3 == PIN_R3_OPEN and clsA == PIN_CLS_A,
         "the model's OWN rung readers (dw8 + the G1-decoded masks) graded "
         "over the %d records of the s249 dump (digest %s == RECORDED %s; "
         ":173): rung1-close %d (RECORDED %d), occ-alone %d (RECORDED %d), "
         "bits26/27 %d (RECORDED %d), rung3-open %d (RECORDED %d), branch-A "
         "domain %d (RECORDED %d) - the ladder meets the recorded bits"
         % (len(lbuf) // REC_LEN, dig, PIN_DUMP_DIGEST, r1, PIN_R1_CLOSE,
            occ, PIN_OCC_ALONE, sel_, PIN_SEL_SET, r3, PIN_R3_OPEN,
            clsA, PIN_CLS_A))

    # ---- G4 the lattice theorem + the two-instrument agreement
    uniq = all(sum(1 for hh in range(4) for dd in range(4)
                   if rungA_closed(H * 4 + hh, D * 4 + dd, rand)) == 1
               for H in range(-3, 3) for D in range(-3, 3) for rand in range(16))
    dis = 0
    if P["coef_h"] and P["coef_d"] and P["amask"]:
        hs = range(-128, 128, 5)
        ds = range(-128, 128, 7)
        for h in hs:
            for d in ds:
                for rand in range(0, 40):
                    if branchA_port(h, d, rand, P) != rungA_closed(h, d, rand):
                        dis += 1
        ndrawn = len(list(hs)) * len(list(ds)) * 40
    else:
        ndrawn = 0
    gate("G4_lattice_two_instruments", uniq and dis == 0 and ndrawn > 0,
         "branch A: exactly 1 hit per 16 lattice classes for all %d (H,D) x 16 "
         "rand (%d/%d) - RECORDED 36/36 :172; and the pin-decoded instruction "
         "chain (coefs -%s*sar(h,2) -%s*sar(d,2), mask %#x) AGREES with the "
         "closed form on %d (h,d,rand) draws - %d disagreements (two "
         "implementations that fail differently: a wrong coef or a wrong "
         "theorem side both land here)"
         % (PIN_THEOREM_HD, PIN_THEOREM_HD, PIN_THEOREM_HD, P["coef_h"],
            P["coef_d"], P["amask"], ndrawn, dis))

    # ---- G5 ladder purity + analytic-vs-sampled quantifiers
    bad5 = []
    n_certain = n_pass_nsel = wrong = 0
    if F["live_len_ok"]:
        states = [Live(flag2000=f, rand=r, s20c=s, s210=t)
                  for f in (False, True) for r in (0, 1, 50, 272)
                  for (s, t) in ((None, None), (0, 0), (5, 9), (13, 31))]
        for i in range(PIN_LIVE_RECS):
            rec = lbuf[i * REC_LEN:(i + 1) * REC_LEN]
            x = (i % (F["W"] // 2)) * 2
            y = i // (F["W"] // 2)
            k = classify_row(x, y, rec, P)
            dw = dw8(rec)
            for st in states:
                e, _p = gate_exec(x, y, rec, st, P)
                if e is not None and e not in (0, 1, 2):
                    bad5.append("eax %r out of {0,1,2} rec %d" % (e, i))
            if not k["pass1"]:
                if any(gate_exec(x, y, rec, st, P)[0] not in (0, None)
                       for st in states):
                    bad5.append("rung1 accepted %d" % i)
            analytic_certain = bool(k.get("sel") and k.get("r3"))
            if (k["kind"] == "certain-accept") != analytic_certain:
                bad5.append("certain analytic %d" % i)
            if analytic_certain:
                n_certain += 1
                for st in states:
                    if st.flag2000 is None:
                        continue
                    if gate_exec(x, y, rec, st, P)[0] in (0, None):
                        bad5.append("certain refused %d st %s" % (i, st.label()))
        # the flag-set + sel-clear leg REFUSES (pinned neg/sbb/and-2): graded
        # against the wrong-polarity rival over every passing record
        stF = Live(flag2000=True, rand=1, s20c=0, s210=0)
        n_pass_nsel = wrong = 0
        for i in range(PIN_LIVE_RECS):
            rec = lbuf[i * REC_LEN:(i + 1) * REC_LEN]
            dw = dw8(rec)
            if (dw & P["rung1"]) or (dw & P["rung2mask"]):
                continue
            n_pass_nsel += 1
            if gate_exec(0, 0, rec, stF, P)[0] != 0:
                wrong += 1
        if wrong:
            bad5.append("flag-set sel-clear accepted %d" % wrong)
    gate("G5_ladder_purity_quantifiers", live_len_ok(F) and not bad5,
         "model outputs stayed in {0,1,2} over %d records x %d sampled live "
         "states; the CERTAIN-accept class (pass1 & bits26/27 & bit28) holds "
         "%d dump records (n_certain_of) and none of them ever refuses under "
         "ANY sampled flag state (eax=2 with the flag set, eax=1 with it "
         "clear - the eax=1 legs sit after the flag-set block per G1); the "
         "flag-set + bits26/27-CLEAR leg refuses on all %d passing-and-sel-"
         "clear records (pinned neg/sbb/and-2 polarity: the polarity-flipped "
         "rival would accept all %d - the model accepts %d); the analytic "
         "class equals the sampled quantifier everywhere%s"
         % (PIN_LIVE_RECS, 32, n_certain_of(F), n_pass_nsel, n_pass_nsel,
            wrong, "" if not bad5 else " BAD " + "; ".join(bad5[:3])))

    # ---- G6 the M300 call-site census, re-graded
    mr = F["m300rows"]
    c_reach = sum(1 for r in mr if r["reach"].startswith("REACHES"))
    c_inw = sum(1 for r in mr if r["reach"] == "IN-WRITER")
    c_noreach = sum(1 for r in mr if r["reach"] == "CANNOT-REACH")
    c_truth = sum(1 for r in mr if "truth-branch" in r["cls"])
    c_stored = sum(1 for r in mr if r["cls"] == "stored-to-memory")
    c_ebx = sum(1 for r in mr if r["cls"] == "into-ebx")
    inw = [r for r in mr if r["reach"] == "IN-WRITER"]
    tt_t = w1.get(0x51E005, ("", ""))[1]
    je_t = w1.get(0x51E007, ("", ""))[1]
    gate("G6_m300_census_regrade",
         len(mr) == PIN_SITES and c_truth == PIN_CLS_TRUTH
         and c_stored == PIN_CLS_STORED and c_ebx == PIN_CLS_EBX
         and c_reach == PIN_REACH and c_inw == PIN_INWRITER
         and c_noreach == PIN_NOREACH and len(inw) == 1
         and inw[0]["va"] == P["call_addr"] and inw[0]["fn"] == "FUN_0051dcb0"
         and "test @0x51e005" in inw[0]["use"] and norm(tt_t) == "test eax,eax"
         and norm(je_t) == "je 0x51e11d",
         "%d/%d call-site rows re-parsed from %s S2: classes %d truth-branch / "
         "%d stored-to-memory / %d into-ebx (RECORDED %d/%d/%d); reach %d "
         "REACHES / %d IN-WRITER / %d CANNOT-REACH (RECORDED %d/%d/%d); the "
         "SINGLE IN-WRITER row (call@0x%x inside FUN_0051dcb0, the counter's "
         "own writer) agrees with the W1 BYTES line for line: 'test eax,eax' "
         "@0x51e005 + '%s' @0x51e007 skip the inc block 0x51e00d-0x51e01b "
         "WHOLE - so only visits inside FUN_0051dcb0 can increment at all, and "
         "%d of the 24 callers can never reach the writer"
         % (len(mr), PIN_SITES, os.path.basename(DEF_M300), c_truth, c_stored,
            c_ebx, PIN_CLS_TRUTH, PIN_CLS_STORED, PIN_CLS_EBX, c_reach, c_inw,
            c_noreach, PIN_REACH, PIN_INWRITER, PIN_NOREACH,
            inw[0]["va"] if inw else 0, je_t, c_noreach))

    # ---- G7 the M301 structure, re-derived from the same bytes
    mine = ["0x%x `%s`" % (a, norm(w1[a][1])) for a in sorted(w1)
            if P["call_addr"] + 5 <= a <= PIN_W1_END and "eax" in w1[a][1]]
    inside = [m for m in (F["m301_mentions"] or [])
              if int(m.split()[0], 16) <= PIN_W1_END]
    je_leg = norm(w1.get(0x51DFD1, ("", ""))[1])
    cnt_ops = [norm(w1.get(a, ("", ""))[1]) for a in (0x51E00D, 0x51E01B)]
    gate("G7_m301_structure_regrade",
         mine == inside and F["m301_back"] == 0
         and je_leg == "je 0x51dff5" and 0x51DFD1 < 0x51DFFD
         and all("ebx" not in o for o in cnt_ops)
         and all("esi+0x989cec" in o for o in cnt_ops),
         "re-derived from the W1 BYTES vs the m301 A6 witness: the eax mentions "
         "after the call inside the window (%s) EQUAL the recorded list up to "
         "the window edge 0x51e02c (the 6th recorded mention 0x51e033 lies "
         "past it - same list, bounded instrument); backward branches from after "
         "the call into the 0x51de2c-0x51df1d walk range: %d (RECORDED 0); the "
         "ebx-driven branch '%s' @0x51dfd1 lands on 0x51dff5 = the block "
         "IMMEDIATELY BEFORE the call @0x51dffd - the ebx==0 leg (cell-store "
         "skip) STILL calls the gate; the counter load/store mention esi and "
         "0x989cec only (%s) - the ebx walk gates the CELL store, never the "
         "increment, exactly as M301 REFUTED the table lead"
         % (mine, F["m301_back"], je_leg, cnt_ops))

    # ---- G8 the executable replay over the recorded rows
    kinds = dict(sorted(cnt.kinds.items()))
    part = sum(kinds.values()) == len(rows)
    nsites = dict(sorted(collections.Counter(
        sgt.site_of(F["g"].rb(e["y"], e["x"])) for (_, _, _, e) in rows).items()))
    gate("G8_executable_replay_rows",
         len(rows) == cnt.total("rows") == ANCHORS["rows"] and part
         and F["n_tiles"] == ANCHORS["tiles"]
         and nsites == ANCHORS["site_hist_save"]
         and cnt.total("refuse") + cnt.total("possible") == len(rows)
         and cnt.total("possible") >= cnt.total("certain")
         and kinds.get("certain-accept", 0) == cnt.total("certain")
         and (ANCHORS["kinds"] is None or kinds == ANCHORS["kinds"])
         and (ANCHORS["refuse"] is None or cnt.total("refuse") == ANCHORS["refuse"])
         and (ANCHORS["eax1"] is None or cnt.total("eax1") == ANCHORS["eax1"])
         and (ANCHORS["eax2"] is None or cnt.total("eax2") == ANCHORS["eax2"])
         and (ANCHORS["undec"] is None
              or cnt.total("undec_base") == ANCHORS["undec"]),
         "%d rows / %d tiles replayed through the live-state-aware gate: "
         "per-site rows %s match B18's RECORDED site anchor %s (the counter "
         "table and the MAX table are the SAME 28-B slots, +4 vs +0); the "
         "class census %s partitions the rows exactly; %d rows CERTAINLY "
         "refuse (rung1 - no live state increments), %d CERTAINLY accept "
         "(accepted whatever the never-dumped 0x985ac4 bit says), the rest are "
         "UNDECIDED-but-possible; the DECLARED baseline accepts %d with eax=1 "
         "and %d with eax=2 (branch-A parity hits) and leaves %d rows "
         "undecided - branch-A parity MISSES that fall to the branch-B "
         "lattice, whose strides are never recorded"
         % (len(rows), F["n_tiles"], nsites, ANCHORS["site_hist_save"], kinds,
            cnt.total("refuse"), cnt.total("certain"), cnt.total("eax1"),
            cnt.total("eax2"), cnt.total("undec_base")))

    # ---- G9 the rivals fail the same fit
    ungated = sum(cnt.t[s]["rows"] for s in cnt.t)
    aliased = [a for a in w1 if norm(w1[a][1]).startswith("mov")
               and "[esi+0x989ce8]" in norm(w1[a][1])
               and "ecx" in norm(w1[a][1])]
    gate("G9_rivals_fail_same_fit",
         cnt.total("certain") < cnt.total("possible")
         and cnt.total("possible") < ungated
         and not aliased and P["cnt_disp"] != P["max_disp"]
         and F["live_len_ok"] and je_lands_before_call(w1)
         and gate_block_skipped_whole(w1, P),
         "rivals: (a) 'the inc is UNGATED' predicts %d/%d increments - refuted "
         "by the pinned 0x51e007 je and the %d certain-rung1 rows the model "
         "never increments; (b) 'the counter aliases the MAX field [esi"
         "+0x989ce8]' - %d MAX-operand instructions also write ecx (must be "
         "0: the counter store/load texts mention 0x989cec only, %d bytes "
         "further); (c) 'the gated je jumps only the counter LOAD' - the load/"
         "inc/store block 0x51e00d-0x51e01b is entered ONLY by fall-through: "
         "je target 0x51e11d is past the store and no branch in the window "
         "targets the interior (graded %s); (d) 'the ebx walk gates the call' "
         "(M301 REFUTED) - je 0x51dff5 lands BEFORE the call @0x51dffd; NOTE "
         "the eax=1 return is STRUCTURAL ONLY in this window: %d dump records "
         "and %d graded rows reach the rung3 leg in a live state, so no "
         "'only-2-accepts' rival is gradeable here on the eax=1 leg (DECLARED)"
         % (ungated, len(rows), cnt.total("refuse"), len(aliased),
            P["counter_off"], gate_block_skipped_whole(w1, P),
            n_r3_pass1(F), ANCHORS["eax1"]))

    return R, cnt


def live_len_ok(F):
    return F["live_len_ok"]


def r1_of(F):
    n = 0
    if F["live_len_ok"]:
        for i in range(PIN_LIVE_RECS):
            if dw8(F["lbuf"][i * REC_LEN:(i + 1) * REC_LEN]) & F["P"]["rung1"]:
                n += 1
    return n


def n_certain_of(F):
    """dump records of the CERTAIN-accept class: pass1 & bits26/27 & bit28."""
    n = 0
    if not F["live_len_ok"]:
        return -1
    P = F["P"]
    for i in range(PIN_LIVE_RECS):
        dw = dw8(F["lbuf"][i * REC_LEN:(i + 1) * REC_LEN])
        if not (dw & P["rung1"]) and (dw & P["rung2mask"]) and (dw & P["rung3"]):
            n += 1
    return n


def n_r3_pass1(F):
    """dump records that REACH the rung3 leg in a live state: pass1 and the
    bit28 set with bits26/27 clear (flag-clear path) or set (flag-set path
    returns before rung3) - the eax=1-REACHABLE population."""
    n = 0
    if not F["live_len_ok"]:
        return -1
    P = F["P"]
    for i in range(PIN_LIVE_RECS):
        dw = dw8(F["lbuf"][i * REC_LEN:(i + 1) * REC_LEN])
        if not (dw & P["rung1"]) and not (dw & P["rung2mask"]) \
                and (dw & P["rung3"]):
            n += 1
    return n


def je_lands_before_call(w1):
    return norm(w1.get(0x51DFD1, ("", ""))[1]) == "je 0x51dff5" \
        and 0x51DFD1 < 0x51DFFD


def gate_block_skipped_whole(w1, P):
    """the refutation of 'the je jumps only the counter LOAD': load, inc and
    store form one block entered ONLY by fall-through from the test/je pair -
    the je target is past the store and no branch in the window targets the
    block's interior."""
    block = [a for a in sorted(w1)
             if norm(w1[a][1]) in ("mov ecx,DWORD PTR [esi+0x989cec]",
                                    "inc ecx",
                                    "mov DWORD PTR [esi+0x989cec],ecx")]
    if len(block) != 3:
        return False
    tgt = [int(w1[a][1].split()[-1], 16) for a in sorted(w1)
           if re.match(r"j\w+\s+0x", norm(w1[a][1]))
           and w1[a][1].split()[-1].startswith("0x")]
    return (P["je_addr"] is not None and P["je_addr"] < min(block)
            and P["je_target"] is not None and P["je_target"] > max(block)
            and not [t for t in tgt if min(block) < t <= max(block)])


def report(sav_path, raw_path=DEF_RAW, bin_path=DEF_BIN, m299=DEF_M299,
           m300=DEF_M300, m301=DEF_M301, out=None, verdict=True):
    F = build(sav_path, raw_path, bin_path, m299, m300, m301)
    R, cnt = gates(F)
    L = list(table_lines(F))
    for name, ok, detail in R:
        L.append("%-28s %s  %s" % (name, "PASS" if ok else "FAIL", detail))
    nbad = sum(1 for _, ok, _ in R if not ok)
    if verdict:
        L.append("")
        L.append("%sB19: %d/%d gates - the slot [+4] visit counter is "
                 "EXECUTABLE: for each of the %d recorded FUN_0051dcb0 visits "
                 "the gate FUN_005832b0 decides inc/no-inc (or is DECLARED "
                 "undecided by an unrecorded live value), and the counters "
                 "land %d CERTAIN + <= %d POSSIBLE increments over sites %s; "
                 "live VALUES and table CONTENTS stayed DECLARED UNMODELED%s"
                 % ("FAIL " if nbad else "PASS ", len(R) - nbad, len(R),
                    len(F["rows"]), cnt.total("certain"),
                    cnt.total("possible"), sorted(cnt.t),
                    "" if not nbad else " - FAILING: " + "; ".join(
                        n for n, ok, _ in R if not ok)))
    if out is not None:
        out.write("\n".join(L) + "\n")
    else:
        for ln in L:
            print(ln)
    return R


def acceptance(sav_path, results, raw=DEF_RAW, bin_path=DEF_BIN):
    """Run the B19 gate set; grade ONLY this rung's gates (review #264 P1).
    The PASS line with the full gate count belongs to sim.selftest (which
    adds G10 determinism), so the module verdict is suppressed here."""
    R = report(sav_path, raw, bin_path, verdict=False)
    ok_all = True
    for name, ok, detail in R:
        results.append((name, ok))
        ok_all = ok_all and ok
    return ok_all


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sim.visitcounter")
    ap.add_argument("--sav", default=DEF_SAV)
    ap.add_argument("--raw", default=DEF_RAW)
    ap.add_argument("--bin", default=DEF_BIN)
    ap.add_argument("--out", help="write the report to this file")
    a = ap.parse_args(argv)
    R = report(a.sav, raw_path=a.raw, bin_path=a.bin,
               out=open(a.out, "w") if a.out else None)
    return 0 if all(ok for _, ok, _ in R) else 1


if __name__ == "__main__":
    sys.exit(main())
