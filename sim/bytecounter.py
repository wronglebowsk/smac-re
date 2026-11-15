# -*- coding: utf-8 -*-
"""sim/bytecounter.py - RUNG B20: the BYTE-twin visit counter made executable.

M303 closed the identity of the byte side: the post-counter read at 0x51e02c
is the LOAD HALF of an in-place BYTE ++ on the per-block BYTE twin of the
0x94eca8 MAX array - family 0x94ed28 = 0x94eca8 + 0x80, entry width 1 B, 128
entries per field, block stride 8380 B (= 4 * 2095, derived twice: the fold
0x51e013-2a AND the per-call init `add edx,0x20bc`), 8 blocks (init
`cmp edx,0x95f288`, remainder 0). The ++ fires UNCONDITIONALLY on the same
fall-through past `je 0x51e007` that B19's dword ++ rides: between that je and
the byte store 0x51e03e the pinned window carries NO branch (the `je 0x51e040`
AFTER the store tests `test ebx,ebx` flags, not the byte).

This module executes the byte twin over the recorded walk rows (the B17
loader's 2321 m294 decision rows, B16 transposition law, B18 site/block laws)
under the PINNED live state parsed out of evidence/m302_livepins.txt - and
its point is the CONSISTENCY of the two tables: the same accepted-visit set
feeds a DWORD counter per site (0x989ce8+28*site+4) and a BYTE counter per
(block,site) (0x94ed28+8380*block+site), so per site the byte refinement must
sum to the dword count. The MAX side differs in one law-decoded way: the byte
MAX store (0x51dfe2-dff3) is `test ebx,ebx`-gated (block 0 SKIPS it) while the
byte CNT ++ is not - accepted block-0 visits land in the byte CNT table and
never in the byte MAX table.

EVERY constant is decoded from the pinned instruction windows embedded in
evidence/m303_downstream.txt (the module parses the evidence file as its
instruction source, as B19 does for m299), and EVERY replay census is graded
against numbers PARSED from the recorded evidence text (m302_livepins.txt,
b18_sitegate.txt), never hardcoded silently: pins are parsed, the model is
re-derived, and the two are asserted equal.

DECLARED UNMODELED (explicit, per the rung spec):
  * the LIVE CONTENTS of the byte MAX/CNT tables (M303 S9.1 - M302 pinned only
    the dword twin 0x989ce8; no box time in this fire);
  * the LIVE UPPER BOUND of the block byte BYTE[304*i+0x95da14] (M303 S9.2 -
    fold + init imply block < 8, no static bound-check in the window; graded
    rows only ever carry -1 or 1..8, B18 G7);
  * the per-call ZERO-REBUILD cadence: FUN_0051dcb0 zeroes BOTH table families
    at entry (S4), so a recorded table state is always one call's rebuild;
    which outer loop drives the calls, and at what cadence, stays OPEN
    (FUN_0051dcb0's identity, M303/NEXT_PROMPT shortlist). The replay is the
    window-level accumulation model, exactly as B18/B19's;
  * the post-store DISPATCH and the settle nest: the 1<<block gates,
    FUN_0056d480 / FUN_0056d630, ds:0x985b10 / ds:0x985aec and the 8-row walk
    of the byte field @0x950664 (M303 S7 + S9.4, M304's settle-nest MEANING) -
    the byte++ itself never gates them and nothing in this rung reads them;
  * save-carry vs rebuild of the BYTE family (M303 S9.5) and the semantics of
    the sibling fields inside the 8380-B record (S9.3);
  * the save-vs-live record-view drift: BOTH views are replayed and the deltas
    are COUNTED, not smoothed (as B19).
No box time, no /proc, no gdb, no game-binary load.
"""
import argparse
import collections
import hashlib
import os
import re
import sys

from . import precheck as pc
from . import save as sosave
from . import sitegate as sgt
from . import visitcounter as vc

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEF_SAV = os.path.join(REPO, "programs", "saves", "m54b_clean.SAV")
DEF_M302 = os.path.join(REPO, "evidence", "m302_livepins.txt")
DEF_M303 = os.path.join(REPO, "evidence", "m303_downstream.txt")
DEF_B18 = os.path.join(REPO, "evidence", "b18_sitegate.txt")

# ---- the law decoded from the pinned windows (values VERIFIED by G2) ------
BYTE_MAX_BASE = 0x94ECA8        # byte MAX array  (fold-side lea 0x51dfe2)
BYTE_CNT_BASE = 0x94ED28        # byte CNT array  (load 0x51e02c, lea 0x51e033)
BYTE_STRIDE = 8380              # 4 * 2095; derived twice (fold + init step)
BYTE_ENTRIES = 128              # init `cmp ecx,0x80`, entry width 1 B
BYTE_BLOCKS = 8                 # (0x95f288 - 0x94eca8) / 8380, remainder 0
CNT_ENTRY = 1                   # 1 - sentinel clamp to 0 (0x51df22-24)

# ---- instruction addresses inside the M303 embedded windows ---------------
FOLD_ADDRS = (0x51E013, 0x51E015, 0x51E018, 0x51E024, 0x51E027, 0x51E02A,
              0x51E02C)
RIVAL_ADDRS = (0x51DFAC, 0x51DFAF, 0x51DFB1, 0x51DFB8, 0x51DFBA, 0x51DFBD,
               0x51DFCB)
INIT_ADDRS = (0x51DCB8, 0x51DCBD, 0x51DCBF, 0x51DCC1, 0x51DCC7, 0x51DCCE,
              0x51DCD1, 0x51DCD8, 0x51DCDF, 0x51DCE7, 0x51DCEB, 0x51DCEC,
              0x51DCEF, 0x51DCF5, 0x51DCF7, 0x51DCFD, 0x51DD03, 0x51DD05,
              0x51DD0A, 0x51DD0D, 0x51DD0F, 0x51DD12, 0x51DD17)
BLOCK_ADDRS = (0x51E007, 0x51E00D, 0x51E01A, 0x51E01B, 0x51E02C, 0x51E033,
               0x51E03A, 0x51E03C, 0x51E03E, 0x51E040)
CORPUS_N = 11                   # every literal 0x94eca8/0x94ed28 mention (S0)

INS_RX = re.compile(r"^\s+(?:0x)?([0-9a-f]{6}):?\t([0-9a-f ]+?)\t(.+?)\s*$")
INS2_RX = re.compile(r"^\s+(?:0x)?([0-9a-f]{6}):?\t(.+?)\s*$")
_HEXCOL = re.compile(r"^(?:[0-9a-f]{2} )*0x?[0-9a-f]{2}\s*$")
S0_RX = re.compile(r"^\s+(?:0x)?([0-9a-f]{6}) (MAX|CNT) (FUN_[0-9a-f]+)"
                   r"\s+(.+?)\s*$")
S6_RX = re.compile(r"^\s+(?:0x)?([0-9a-f]{6}) (FUN_[0-9a-f]+)\s+(.+?)\s*$")


def npat(p):
    return " ".join(p.split())


def hx(v):
    return "-" if v is None else ("0x%x" % v)


def parse_windows(path):
    """the objdump-format windows inside the M303 evidence file:
    -> ({addr: (hexbytes, 'mnemonic operands')}, corpus_rows, s6_rows)."""
    ins = {}
    corpus = []
    s6 = []
    for ln in open(path, errors="replace"):
        m = INS_RX.match(ln)
        if m:
            ins[int(m.group(1), 16)] = (
                " ".join(m.group(2).split()), " ".join(m.group(3).split()))
            continue
        m = INS2_RX.match(ln)
        if m and "\t" not in m.group(2) and not _HEXCOL.match(m.group(2)):
            ins[int(m.group(1), 16)] = ("", " ".join(m.group(2).split()))
            continue
        m = S0_RX.match(ln)
        if m:
            corpus.append((int(m.group(1), 16), m.group(2), m.group(3),
                           " ".join(m.group(4).split())))
            continue
        m = S6_RX.match(ln)
        if m and m.group(1) not in ("0051dcb0",):
            s6.append((int(m.group(1), 16), m.group(2),
                       " ".join(m.group(3).split())))
    return ins, corpus, s6


def decode_fold(ins, path, corpus):
    """the byte-fold chain decoded OUT OF the pinned texts (never restated):
    edx = (1<<k)+1 times ebx; eax = (1+s2*edx/ebx... ) - every coefficient
    parsed. -> dict with fold65, fold131, fold2095, scale, cnt_disp,
    max_disp, tails."""
    def txt(a):
        return ins.get(a, ("", ""))[1]

    def hexs(a):
        return ins.get(a, ("", ""))[0]

    D = {}
    m = re.match(npat(r"shl +edx,0x([0-9a-f]+)"), txt(0x51E015))
    if not m or not re.match(npat(r"mov +edx,ebx"), txt(0x51E013)) \
            or not re.match(npat(r"add +edx,ebx"), txt(0x51E018)):
        return None
    D["fold65"] = (1 << int(m.group(1), 16)) + 1          # 65
    m = re.match(r"lea +eax,\[ebx\+edx\*(\d+)\]", txt(0x51E024))
    if not m:
        return None
    k2 = int(m.group(1))
    D["fold131"] = 1 + k2 * D["fold65"]                   # 131 (ebx + 2*65ebx)
    m = re.match(npat(r"shl +eax,0x([0-9a-f]+)"), txt(0x51E027))
    if not m or not re.match(npat(r"sub +eax,ebx"), txt(0x51E02A)):
        return None
    D["fold2095"] = (D["fold131"] << int(m.group(1), 16)) - 1   # 2095
    m = re.match(r"mov +dl,BYTE PTR \[ecx\+eax\*(\d+)\+(0x[0-9a-f]+)\]",
                 txt(0x51E02C))
    if not m:
        return None
    D["scale"] = int(m.group(1))                           # 4 (placement)
    D["cnt_disp"] = int(m.group(2), 16)                    # 0x94ed28
    D["stride"] = D["scale"] * D["fold2095"]               # 8380
    maxtxt = ""
    for (_a, _k, _f, t) in corpus:
        if _a == 0x51DFE2 and _k == "MAX":
            maxtxt = t
    m = re.match(r"lea +ecx,\[ecx\+eax\*(\d+)\+(0x[0-9a-f]+)\]", maxtxt)
    if m:
        D["max_disp"] = int(m.group(2), 16)                # 0x94eca8
        D["max_scale"] = int(m.group(1))
    # same-address-expression proof: operand tails (modrm + SIB + disp32)
    D["tail_load"] = hexs(0x51E02C).split()[-4:]
    D["tail_lea"] = hexs(0x51E033).split()[-4:]
    # the ecx (site) pin: the fold base is [ebp-0xc], recorded in prose
    txt49 = ""
    for ln in open(path, errors="replace"):
        if "0x51e021" in ln and "mov    ecx,DWORD PTR [ebp-0xc]" in ln:
            txt49 = ln
            break
    D["ecx_site_pin"] = bool(txt49)
    return D


def decode_init(ins):
    """the per-call init window decoded out of the pinned texts: -> dict with
    family base, cnt gap, entries, entry step/width, block step, family end,
    dword-twin base/stride/end."""
    def txt(a):
        return ins.get(a, ("", ""))[1]

    I = {}
    m = re.match(r"mov +edx,(0x[0-9a-f]+)", txt(0x51DCB8))
    if not m:
        return None
    I["base"] = int(m.group(1), 16)
    m = re.match(r"mov +BYTE PTR \[edx\+ecx\*1\+(0x[0-9a-f]+)\],0x0",
                 txt(0x51DCDF))
    if not m:
        return None
    I["cnt_gap"] = int(m.group(1), 16)
    if not re.match(r"mov +BYTE PTR \[edx\+ecx\*1\],0x0", txt(0x51DCE7)) \
            or not re.match(r"inc +ecx", txt(0x51DCEB)):
        return None
    I["width"] = 1
    m = re.match(r"cmp +ecx,(0x[0-9a-f]+)", txt(0x51DCEF))
    if not m:
        return None
    I["entries"] = int(m.group(1), 16)
    m = re.match(r"add +edx,(0x[0-9a-f]+)", txt(0x51DCF7))
    if not m:
        return None
    I["step"] = int(m.group(1), 16)
    m = re.match(r"cmp +edx,(0x[0-9a-f]+)", txt(0x51DCFD))
    if not m:
        return None
    I["end"] = int(m.group(1), 16)
    I["blocks"], I["rem"] = divmod(I["end"] - I["base"], I["step"])
    m = re.match(r"mov +eax,(0x[0-9a-f]+)", txt(0x51DD05))
    if not m:
        return None
    I["dw_base"] = int(m.group(1), 16)
    m = re.match(r"add +eax,(0x[0-9a-f]+)", txt(0x51DD0F))
    if not m:
        return None
    I["dw_stride"] = int(m.group(1), 16)
    m = re.match(r"cmp +eax,(0x[0-9a-f]+)", txt(0x51DD12))
    if not m:
        return None
    I["dw_end"] = int(m.group(1), 16)
    I["dw_slots"], I["dw_rem"] = divmod(I["dw_end"] - I["dw_base"],
                                        I["dw_stride"])
    return I


# --------------------------------------------------------------------------
# the pinned live state + the recorded anchors, PARSED from evidence text
# --------------------------------------------------------------------------
SCALAR_RX = re.compile(r"scalar (\S+(?: \S+)?):\s+ds:0x([0-9a-f]+) "
                       r"=\s+(\d+) \(0x[0-9a-f]+\)")


def parse_m302(path):
    """-> dict(live=vc.Live, recorded={...}, state_line=str). All recorded
    numbers are parsed, never hardcoded; duplicates in the file must agree."""
    scalars = {}
    rec = {}
    state_line = None
    for ln in open(path, errors="replace"):
        s = ln.strip()
        m = re.match(r"scalar (.+?)\s+ds:0x([0-9a-f]+) = (\d+) "
                     r"\(0x[0-9a-f]+\)", s)
        if m:
            raw_name, addr, val = (m.group(1), int(m.group(2), 16),
                                   int(m.group(3)))
            if "rand" in raw_name:
                name = "rand+1"
            elif "s20c" in raw_name:
                name = "s20c"
            elif "s210" in raw_name:
                name = "s210"
            elif "dword" in raw_name:
                name = "dword"
            else:
                continue
            if name in scalars and scalars[name] != (addr, val):
                rec["scalar_conflict"] = True
            scalars[name] = (addr, val)
        m = re.match(r"pinned live state: (.*)", s)
        if m:
            state_line = m.group(1)
        m = re.match(r"pinned replay over (\d+) rows: CERTAIN-accept (\d+) / "
                     r"CERTAIN-refuse (\d+) / still-undecided (\d+)", s)
        if m:
            g = [int(x) for x in m.groups()]
            rec.setdefault("rows", []).append(dict(zip(
                ("rows", "acc", "refuse", "undec"), g)))
        m = re.match(r"per-B18-site split of the (\d+) "
                     r"\(accept/refuse/undecided\): (\{.*\})", s)
        if m:
            rec["branchA"] = int(m.group(1))
            rec["split"] = eval(m.group(2), {"__builtins__": {}})
        m = re.search(r"pinned eax counts 0/1/2: (\{[^}]*\})", s)
        if m:
            rec["eax"] = eval(m.group(1), {"__builtins__": {}})
    if "scalar_conflict" in rec or "rows" not in rec or state_line is None:
        return None
    rows = rec["rows"][0]
    if any(r != rows for r in rec["rows"]):
        return None
    flag = scalars["dword"][1]
    live = vc.Live(flag2000=bool(flag & 0x2000),
                   rand=scalars["rand+1"][1],
                   s20c=scalars["s20c"][1], s210=scalars["s210"][1])
    return {"live": live, "scalars": scalars, "rows": rows,
            "branchA": rec["branchA"], "split": rec["split"],
            "eax": rec["eax"], "state_line": state_line}


def parse_b18_anchors(path):
    """B18's own recorded numbers, parsed from its report lines: -> dict
    (sentinel rows, slot entries, cell entries, owner blocks, skips)."""
    out = {}
    for ln in open(path, errors="replace"):
        if "G7_site_byte_and_block" in ln and "sentinel" not in out:
            m = re.search(r"(\d+) graded rows carry the -1 owner sentinel",
                          ln)
            if m:
                out["sentinel"] = int(m.group(1))
        if "G8_max_store_funnel" in ln:
            m = re.search(r"slot entries (\d+).*?cell entries (\d+) over "
                          r"(\d+) owner blocks, (\d+) steps SKIPPED", ln)
            if m:
                out["slot_entries"] = int(m.group(1))
                out["cell_entries"] = int(m.group(2))
                out["blocks"] = int(m.group(3))
                out["skips"] = int(m.group(4))
    if len(out) != 5:
        return None
    return out


# --------------------------------------------------------------------------
# the executable walk: one pass, all four stores, in the pinned order
# --------------------------------------------------------------------------
class ByteWalk(object):
    """FUN_0051dcb0's store order per visit, both table families, as ONE
    object. Window-level accumulation (the per-call zero-rebuild cadence is
    DECLARED UNMODELED - the docstring + B18/B19's identical model)."""

    def __init__(self):
        self.rows = 0
        self.smax = {}                       # site -> dword MAX (0x989ce8+0)
        self.bmax = {}                       # (block,site) -> byte MAX (+0)
        self.dcnt = collections.Counter()    # site -> dword CNT (+4)
        self.bcnt = collections.Counter()    # (block,site) -> byte CNT (+128)
        self.skips = 0                       # block-0 cell-store skips
        self.accept = 0
        self.undec = 0
        self.eax_counts = collections.Counter()
        self.kind_counts = collections.Counter()
        self.site_rows = collections.Counter()
        self.site_split = {}                 # site -> [acc, refuse, undec]
        self.site_splitA = {}                # same, branchA-kind rows only
        self.visited = collections.Counter()  # (block,site) -> rows seen
        self.accept_blk = collections.Counter()  # accepted rows by block
        self.fires_equal = True              # per-row dword++ <=> byte++
        self.monotone_ok = True

    def visit(self, x, y, rec, val, P, live):
        """one recorded walk step. val = the RECORDED machine value column
        (edi of the MAX stores - B18's DECLARED-input law)."""
        site = sgt.site_of(rec)
        blk, _raw = sgt.block_of(rec)
        self.rows += 1
        self.site_rows[site] += 1
        self.visited[(blk, site)] += 1
        # 0x51dfbd-cb: the DWORD slot MAX store, UNCONDITIONAL
        old = self.smax.get(site, 0)
        self.smax[site] = val if val > old else old
        # 0x51dfe2-dff3: the BYTE cell MAX store, test ebx,ebx-gated
        if blk == 0:
            self.skips += 1
        else:
            cold = self.bmax.get((blk, site), 0)
            self.bmax[(blk, site)] = val if val > cold else cold
        # 0x51dffd: the gate call; 0x51e007: je skips 0x51e00d..0x51e040 whole
        eax, _path = vc.gate_exec(x, y, rec, live, P)
        kind = vc.classify_row(x, y, rec, P)["kind"]
        self.kind_counts[kind] += 1
        sp = self.site_split.setdefault(site, [0, 0, 0])
        spa = (self.site_splitA.setdefault(site, [0, 0, 0])
               if kind == "branchA" else None)
        if eax is None:
            self.undec += 1
            self.eax_counts["undecided"] += 1
            sp[2] += 1
            if spa is not None:
                spa[2] += 1
            dw_fire = b_fire = False
        else:
            self.eax_counts[eax] += 1
            if eax != 0:
                self.accept += 1
                sp[0] += 1
                if spa is not None:
                    spa[0] += 1
                self.accept_blk[blk] += 1
                dw_fire = b_fire = True
            else:
                sp[1] += 1
                if spa is not None:
                    spa[1] += 1
                dw_fire = b_fire = False
        # 0x51e00d-1b DWORD CNT++ and 0x51e02c-3e BYTE CNT++: ONE straight
        # line behind the je fall-through - they fire on the SAME row.
        self.fires_equal = self.fires_equal and (dw_fire == b_fire)
        if dw_fire:
            self.dcnt[site] += 1
        if b_fire:
            self.bcnt[(blk, site)] += 1
        return eax, kind

    def check_byte_range(self):
        bad = [(k, v) for k, v in self.bcnt.items() if not 0 <= v <= 255]
        bad += [(k, v) for k, v in self.bmax.items() if not 0 <= v <= 255]
        return bad

    def digest(self):
        h = hashlib.sha256()
        for name, tab in (("dc", self.dcnt), ("sm", self.smax)):
            for k in sorted(tab):
                h.update(("%s.%s=%d;" % (name, k, tab[k])).encode())
        for name, tab in (("bc", self.bcnt), ("bm", self.bmax)):
            for (b, s) in sorted(tab):
                h.update(("%s.%02d.%04d=%d;" % (name, b, s, tab[(b, s)])
                          ).encode())
        return h.hexdigest()[:16]


def replay(rows, grid, P, live):
    w = ByteWalk()
    for (vi, u, s, e) in rows:
        X, Y = e["y"], e["x"]                 # B16 transposition law
        w.visit(X, Y, grid.rb(X, Y), e["val"], P, live)
    return w


# --------------------------------------------------------------------------
# the rivals, each graded against a PARSED recorded number
# --------------------------------------------------------------------------
def rival_divergences(w, pins, b18a):
    """-> list of (name, divergence, detail). Every number comes from the
    recorded tables (pins from m302_livepins.txt, b18a from b18_sitegate.txt)
    or from the visited table itself."""
    R = []
    rec_acc = pins["rows"]["acc"]
    # 1. ungated ++: the ++ rides EVERY walk step, not the gate fall-through
    ung = w.rows
    R.append(("R_ungated", abs(ung - rec_acc),
              "ungated totals %d rows vs recorded pinned accept %d"
              % (ung, rec_acc)))
    # 2. eax==2 only: rung3/branch-B accepts never reach the counters
    e2 = w.eax_counts[2]
    R.append(("R_eax2_only", abs(e2 - rec_acc),
              "eax==2 totals %d vs recorded accept %d (recorded eax counts %s"
              " - the eax==1 leg is a REAL row here)" % (e2, rec_acc,
                                                         dict(pins["eax"]))))
    # 3. the 28-B dword law for the BYTE index (M303 R1): rival address
    keys = [k for k in w.bcnt if k[0] >= 1] or [(b, s) for (b, s) in w.bmax]
    alias = sum(1 for (b, s) in keys
                if s + 28 * b + BYTE_CNT_BASE != s + BYTE_STRIDE * b
                + BYTE_CNT_BASE)
    R.append(("R_28law_index", alias,
              "rival address site+28*block differs from the law address on "
              "%d/%d byte-table keys (fold K=%d vs law K=28)"
              % (alias, len(keys), BYTE_STRIDE)))
    # 4. the ++ rides the MAX store's block gate (would DROP accepted
    #    block-0 rows - the accepted-vs-MAX asymmetry is the whole question)
    k0 = w.accept_blk.get(0, 0)
    R.append(("R_blk0skip_CNT", k0,
              "accepted rows on block 0 = %d (dropped under the rival -> "
              "%d vs recorded %d); %s" % (
                  k0, rec_acc - k0, rec_acc,
                  "GRADED on recorded numbers" if k0 else
                  "NO accepted block-0 row in THIS window - refuted by the "
                  "decoded window instead: zero branches between the fold and "
                  "the store, the only je (0x51e040) sits AFTER the store")))
    # 5. the MAX store rides NO block gate (block 0 would enter the byte MAX
    #    table) - refuted by B18's recorded funnel shape
    sites_on0 = sorted(set(s for (b, s) in w.visited if b == 0))
    rival_cells = len(w.bmax) + len(sites_on0)
    R.append(("R_ungated_MAX", rival_cells - b18a["cell_entries"],
              "rival cell entries %d vs RECORDED %d over %d owner blocks; "
              "%d block-0 rows would enter the MAX table under the rival"
              % (rival_cells, b18a["cell_entries"], b18a["blocks"],
                 w.skips)))
    # 6. the pure-read rival (M303 R3): the byte is read but never ++'d back
    R.append(("R_pureread", rec_acc,
              "rival byte increments total 0 vs recorded accept %d; the "
              "pinned window carries the store 0x51e03e `mov BYTE PTR "
              "[eax],dl` (opcode 88 10) between the inc and the je"
              % rec_acc))
    return R


# --------------------------------------------------------------------------
# TABLE FIRST, gates after (print order == assertion order)
# --------------------------------------------------------------------------
def table_lines(F):
    L = []
    w, wl, pins = F["rp"], F.get("rp_live"), F["pins"]
    if w is None:
        return ["== B20 PARSE FAILURE: the module could not decode the law "
                "windows or the pinned live state - every gate below fails "
                "explicitly, nothing is skipped =="]
    L.append("== B20 the BYTE-twin visit counter, EXECUTED over the recorded "
             "%d rows (%d visits) under the PINNED live state (M302); law "
             "source = the pinned windows inside evidence/m303_downstream.txt "
             "==" % (w.rows, len(set(vi for (vi, _, _, _) in F["rows"]))))
    L.append("pinned live state (parsed from m302_livepins.txt): %s"
             % pins["state_line"])
    L.append("byte family: MAX base 0x%x, CNT base 0x%x (= +0x%x), entry "
             "width 1 B, %d entries/field, block stride %d, %d blocks "
             "(init remainder %d) - index = site + %d*block + base"
             % (BYTE_MAX_BASE, BYTE_CNT_BASE, F["D"]["cnt_disp"] - F["I"]["base"],
                BYTE_ENTRIES, BYTE_STRIDE, BYTE_BLOCKS, F["I"]["rem"],
                BYTE_STRIDE))
    L.append("index law: 65=%d*block (fold leg 1) -> 2095=%d*block (fold leg "
             "2) -> stride %d = 4*2095 (load scale placement); init step "
             "0x%x independently decodes to %d (two legs, one law)"
             % (F["D"]["fold65"], F["D"]["fold2095"], F["D"]["stride"],
                F["I"]["step"], F["I"]["step"]))
    L.append("dword twin (B19): base 0x%x stride %d slots %d (rem %d) - the "
             "SAME accepted fall-through feeds both counters"
             % (F["I"]["dw_base"], F["I"]["dw_stride"], F["I"]["dw_slots"],
                F["I"]["dw_rem"]))
    # per-site dword table
    L.append("")
    L.append("DWORD twin per site (0x989ce8+28*site: +0 MAX, +4 CNT): "
             "rows / accept / refuse / undec / dword CNT / dword MAX")
    for s in sorted(w.site_rows):
        sp = w.site_split[s]
        L.append("%8d %6d %8d %8d %6d %10d %8d"
                 % (s, w.site_rows[s], sp[0], sp[1], sp[2], w.dcnt[s],
                    w.smax[s]))
    # per-(block,site) byte table
    L.append("")
    L.append("BYTE twin per (block,site) (0x94eca8 family: +0 MAX, +128 "
             "CNT): block site / rows seen / byte CNT / byte MAX")
    for (b, s) in sorted(set(w.bcnt) | set(w.bmax) | set(w.visited)):
        L.append("%6d %4d %10d %12d %10s"
                 % (b, s, w.visited[(b, s)], w.bcnt.get((b, s), 0),
                    w.bmax.get((b, s), "SKIP" if b == 0 else 0)))
    L.append("accepted rows by block: %s (block-0 accepts exist: %s)"
             % (dict(sorted(w.accept_blk.items())),
                bool(w.accept_blk.get(0))))
    L.append("byte MAX table entries %d over blocks %s; byte CNT entries %d; "
             "cell-store skips %d" % (len(w.bmax),
                                      sorted(set(b for (b, _) in w.bmax)),
                                      len(w.bcnt), w.skips))
    # the PARITY table: the whole point of the rung
    L.append("")
    L.append("PARITY per site: SUM_blocks byte CNT == dword CNT?")
    for s in sorted(w.dcnt):
        sub = sum(v for (b, ss), v in w.bcnt.items() if ss == s)
        L.append("site %3d: dword CNT %3d == sum over blocks %s -> %3d : %s"
                 % (s, w.dcnt[s],
                    dict(sorted((b, v) for (b, ss), v in w.bcnt.items()
                                if ss == s)), sub,
                    "OK" if sub == w.dcnt[s] else "MISMATCH"))
    L.append("kinds %s | eax %s" % (dict(sorted(w.kind_counts.items())),
                                     dict(sorted(w.eax_counts.items(),
                                                 key=str))))
    L.append("branchA-row per-site split (acc/refuse/undec - the recorded "
             "M302 column covers these rows only): %s"
             % {s: v for s, v in sorted(w.site_splitA.items())})
    L.append("digest %s" % w.digest())
    if wl is not None:
        L.append("live-view (s249 dump) replay over the SAME rows: accept %d "
                 "refuse %d undec %d, byte CNT entries %d, digest %s; "
                 "save-vs-live byte-CNT divergence %d entries differ"
                 % (wl.accept, sum(wl.eax_counts[k] for k in (0,)),
                    wl.undec, len(wl.bcnt), wl.digest(),
                    sum(1 for k in set(w.bcnt) | set(wl.bcnt)
                        if w.bcnt.get(k, 0) != wl.bcnt.get(k, 0))))
    L.append("")
    return L


# --------------------------------------------------------------------------
# build + gates
# --------------------------------------------------------------------------
def build(sav_path, m302=DEF_M302, m303=DEF_M303, b18=DEF_B18):
    F = vc.build(sav_path)                   # rows (B17 loader) + P + grids
    ins, corpus, s6 = parse_windows(m303)
    D = decode_fold(ins, m303, corpus)
    I = decode_init(ins)
    pins = parse_m302(m302)
    b18a = parse_b18_anchors(b18)
    live = pins["live"] if pins else None
    rp = (replay(F["rows"], F["g"], F["P"], live)
          if (D and I and pins and b18a) else None)
    rp_live = (replay(F["rows"], F["lg"], F["P"], live)
               if rp is not None and F["live_len_ok"] else None)
    F.update({"ins": ins, "corpus": corpus, "s6": s6, "D": D or {},
              "I": I or {}, "pins": pins or {}, "b18a": b18a or {},
              "rp": rp, "rp_live": rp_live, "live": live,
              "rec_storeuncond": any(
                  "branch instructions between load and store: []" in ln
                  for ln in open(m303, errors="replace"))})
    return F


def jump_target(hexs, at):
    """decode a near jump's rel32/rel8 target out of the pinned hex bytes."""
    b = [int(x, 16) for x in hexs.split()]
    if not b:
        return None, None
    if b[0] == 0xEB or (len(b) == 2 and b[0] == 0x74):      # rel8 jmp/jcc
        rel = b[1] - 0x100 if b[1] >= 0x80 else b[1]
        return at + len(b), at + len(b) + rel
    if b[:2] == [0x0F, 0x84]:                               # je rel32
        rel = int.from_bytes(bytes(b[2:6]), "little", signed=True)
        return at + 6, at + 6 + rel
    return None, None


def gates(F):
    R = []
    D, I, pins, b18a = F["D"], F["I"], F["pins"], F["b18a"]
    ins, w, wl = F["ins"], F["rp"], F["rp_live"]

    def gate(name, ok, detail):
        R.append((name, bool(ok), detail))

    # ---- G1 the M303 windows parse; every pinned address resolves --------
    miss = [a for grp in ("FOLD", "RIVAL", "INIT", "BLOCK")
            for a in (FOLD_ADDRS if grp == "FOLD" else
                      RIVAL_ADDRS if grp == "RIVAL" else
                      INIT_ADDRS if grp == "INIT" else BLOCK_ADDRS)
            if a not in ins]
    cnt_max = sum(1 for (_a, k, _f, _t) in F["corpus"] if k == "MAX")
    cnt_cnt = sum(1 for (_a, k, _f, _t) in F["corpus"] if k == "CNT")
    gate("G1_windows_parse",
         not miss and len(F["corpus"]) == CORPUS_N and cnt_max == 8
         and cnt_cnt == 3,
         "windows: fold %d/%d rival %d/%d init %d/%d block %d/%d insns "
         "(missing %s); S0 corpus %d mentions = MAX %d / CNT %d (RECORDED "
         "11/8/3)" % (len(FOLD_ADDRS), len(FOLD_ADDRS), len(RIVAL_ADDRS),
                      len(RIVAL_ADDRS), len(INIT_ADDRS), len(INIT_ADDRS),
                      len(BLOCK_ADDRS), len(BLOCK_ADDRS), miss or "-",
                      len(F["corpus"]), cnt_max, cnt_cnt))

    # ---- G2 every family constant DECODED from the pinned bytes ----------
    ok2 = (D.get("fold65") == 65 and D.get("fold131") == 131
           and D.get("fold2095") == 2095 and D.get("scale") == 4
           and D.get("stride") == BYTE_STRIDE
           and D.get("cnt_disp") == BYTE_CNT_BASE
           and D.get("max_disp") == BYTE_MAX_BASE
           and D.get("max_scale") == 4
           and D.get("tail_load") == D.get("tail_lea")
           and D.get("ecx_site_pin")
           and I.get("base") == BYTE_MAX_BASE and I.get("cnt_gap") == 0x80
           and I.get("entries") == BYTE_ENTRIES and I.get("width") == 1
           and I.get("step") == BYTE_STRIDE and I.get("blocks") == BYTE_BLOCKS
           and I.get("rem") == 0
           and D.get("cnt_disp") - I.get("base") == I.get("cnt_gap")
           and I.get("dw_base") == sgt.SLOT_BASE
           and I.get("dw_stride") == sgt.SLOT_STRIDE
           and I.get("dw_slots") == 128
           and I.get("dw_rem") == 0)
    gate("G2_fold_init_decode", ok2,
         "fold decodes 65=%s 131=%s 2095=%s *%s -> stride %s; load disp %s "
         "== CNT-MAX gap %s(+%s from init) + base %s; init step %s == "
         "fold stride (two independent legs); entries %s width %s B; blocks "
         "%s rem %s; dword twin %s stride %s slots %s rem %s; load/lea "
         "operand tails %s==%s; ecx(site) pin prose %s"
         % (D.get("fold65"), D.get("fold131"), D.get("fold2095"),
            D.get("scale"), D.get("stride"), hx(D.get("cnt_disp")),
            hx(D.get("cnt_disp", 0) - I.get("base", 0)), hx(I.get("cnt_gap")),
            hx(I.get("base")), hx(I.get("step")), I.get("entries"),
            I.get("width"), I.get("blocks"), I.get("rem"), hx(I.get("dw_base")),
            I.get("dw_stride"), I.get("dw_slots"), I.get("dw_rem"),
            D.get("tail_load"), D.get("tail_lea"), D.get("ecx_site_pin")))

    # ---- G3 the byte++ is ONE straight line behind the B19 je ------------
    tx = {a: ins[a][1] for a in ins}
    je_tgt = {a: (jump_target(ins[a][0], a) if a in ins else (None, None))
              for a in (0x51E007, 0x51E040)}
    br_in = [a for a in range(0x51E008, 0x51E03F)
             if a in tx and tx[a].split()[0].startswith("j")]
    flag_w = [a for a in range(0x51E03C, 0x51E041)
              if a in tx and tx[a].split()[0] in ("test", "cmp")]
    inc_store = tx.get(0x51E03A, "") == "inc dl" and \
        tx.get(0x51E03E, "") == "mov BYTE PTR [eax],dl"
    ok3 = (br_in == [] and je_tgt[0x51E007][1] == 0x51E11D
           and 0x51E11D > 0x51E03E
           and je_tgt[0x51E040][1] == 0x51E083
           and flag_w == [0x51E03C] and inc_store
           and tx.get(0x51E00D, "").startswith("mov ecx,DWORD PTR "
                                               "[esi+0x989cec]")
           and w is not None and w.fires_equal
           and F["rec_storeuncond"])
    gate("G3_unconditional_behind_je", ok3,
         "jumps strictly inside [0x51e007,0x51e03e): %s; je 0x51e007 "
         "(0f 84 10 01 00 00) decodes to target %s (past the byte store "
         "0x51e03e); je 0x51e040 -> %s tests the flags of %s (block id, "
         "NOT the byte); byte RMW = load 0x51e02c + lea 0x51e033 (same "
         "SIB+disp tail) + inc dl + store (opcodes decode); dword++ triple "
         "[esi+0x989cec] = same slot +4 as B19; replay: dword++ and byte++ "
         "fired on the SAME rows in %d/%d steps"
         % (br_in or "[]", hx(je_tgt[0x51E007][1]), hx(je_tgt[0x51E040][1]),
            "0x51e03c test ebx,ebx", w.rows if w else 0,
            w.rows if w else 0))

    # ---- G4 the pinned replay reproduces the RECORDED census -------------
    rec = pins.get("rows", {})
    kinds = dict(w.kind_counts) if w else {}
    split_ok = (w is not None and
                 all(list(w.site_splitA.get(s, [0, 0, 0])) == list(v)
                     for s, v in pins.get("split", {}).items()))
    ok4 = (w is not None and w.rows == rec.get("rows")
           and w.accept == rec.get("acc") and w.rows - w.accept - w.undec
           == rec.get("refuse") and w.undec == rec.get("undec") == 0
           and dict(w.eax_counts) == pins.get("eax")
           and kinds.get("branchA") == pins.get("branchA")
           and kinds.get("rung1") == rec.get("rows") - pins.get("branchA")
           and split_ok
           and len(F["rows"]) == rec.get("rows"))
    gate("G4_pinned_replay", ok4,
         "replay over %d rows (RECORDED %d): accept %d (RECORDED %d) / "
         "refuse %d (RECORDED %d) / undecided %d (RECORDED %d); eax counts "
         "%s (RECORDED %s); kinds %s (RECORDED branchA %d -> rung1 %d); "
         "branchA-row per-site split (the recorded column covers the %s "
         "previously-undecided rows ONLY) %s == RECORDED %s; all live states "
         "decided (0 undecided) - the pinned state collapses B19's brackets "
         "to a point"
         % (w.rows if w else 0, rec.get("rows"), w.accept if w else 0,
            rec.get("acc"), (w.rows - w.accept - w.undec) if w else 0,
            rec.get("refuse"), w.undec if w else 0, rec.get("undec"),
            dict(sorted(w.eax_counts.items(), key=str)) if w else {},
            pins.get("eax"), dict(sorted(kinds.items())),
            pins.get("branchA"),
            (rec.get("rows", 0) - pins.get("branchA", 0)) if w else 0,
            pins.get("branchA"),
            {s: v for s, v in sorted(w.site_splitA.items())} if w else {},
            pins.get("split")))

    # ---- G5 the byte table state is a legal byte table --------------------
    bad = w.check_byte_range() if w else [("no replay", 0)]
    blk0max = [(b, s) for (b, s) in (w.bmax if w else {}) if b == 0]
    maxval = max(list(w.bmax.values()) + [0]) if w else 0
    cntval = max(list(w.bcnt.values()) + [0]) if w else 0
    ok5 = (w is not None and not bad and not blk0max
           and all(k in w.visited for k in w.bcnt)
           and all(k in w.visited for k in w.bmax))
    gate("G5_byte_table_legal", ok5,
         "every byte value in [0,255] (violations %s); no wrap witness "
         "(max byte MAX %d, max byte CNT %d - both under 256, so the byte "
         "table never wrapped in this window); %d byte MAX entries, none on "
         "block 0 (%d would alias); every byte CNT/MAX key is a visited "
         "(block,site) key; digest %s" % (bad or "[]", maxval, cntval,
                                          len(w.bmax) if w else 0,
                                          len(blk0max),
                                          w.digest() if w else "-"))

    # ---- G6 the MAX funnel == B18's own SiteGate replay, live -------------
    sg = sgt.SiteGate()
    for (vi, u, s, e) in F["rows"]:
        X, Y = e["y"], e["x"]
        r = F["g"].rb(X, Y)
        sg.visit(sgt.site_of(r), sgt.block_of(r)[0], e["val"])
    same = (w is not None and sg.slot == {k: v for k, v in w.smax.items()}
            and sg.cell == w.bmax and sg.cell_skips == w.skips
            and sg.rows == w.rows)
    ok6 = (same and w is not None
           and w.skips == b18a.get("skips") == b18a.get("sentinel")
           and len(sg.slot) == b18a.get("slot_entries")
           and len(sg.cell) == b18a.get("cell_entries")
           and len(set(b for (b, _) in sg.cell)) == b18a.get("blocks"))
    gate("G6_max_funnel_matches_B18", ok6,
         "the byte-MAX funnel in THIS module == sim.sitegate.SiteGate replay "
         "byte-for-byte (slot %s, cell %s, skips %d, rows %d); RECORDED B18 "
         "G8/G7: slot entries %s, cell entries %s over %s owner blocks, %s "
         "skips == %s sentinel rows - the byte MAX table is the same five "
         "cells B18 graded, now next to its CNT twin"
         % (dict(sorted(sg.slot.items())),
            dict(sorted(sg.cell.items())), w.skips if w else 0,
            w.rows if w else 0, b18a.get("slot_entries"),
            b18a.get("cell_entries"), b18a.get("blocks"),
            w.skips if w else 0, b18a.get("sentinel")))

    # ---- G7 PARITY: one gate, two tables of different widths --------------
    par = (w is not None and
           all(sum(v for (b, ss), v in w.bcnt.items() if ss == s)
               == w.dcnt[s] for s in w.dcnt))
    par_live = (wl is None) or all(
        sum(v for (b, ss), v in wl.bcnt.items() if ss == s) == wl.dcnt[s]
        for s in wl.dcnt)
    nkeys = (w is not None and len(set(w.dcnt)) > 0
             and all(w.site_split[s][0] == w.dcnt[s] for s in w.dcnt))
    ok7 = (w is not None and par and par_live and nkeys
           and w.accept == sum(w.bcnt.values()) == sum(w.dcnt.values())
           and len(set(w.bcnt) | set(w.bmax) | set(w.visited)) > 0)
    gate("G7_dw_byte_parity", ok7,
         "SAME accepted-visit set feeds both: %d accepted rows -> %d dword "
         "increments over sites %s AND %d byte increments over %s "
         "(block,site) keys; per site sum_blocks(byte CNT) == dword CNT on "
         "all %d sites (live view too: %s); the byte table refines the dword "
         "table without moving a single visit"
         % (w.accept if w else 0, sum(w.dcnt.values()) if w else 0,
            sorted(w.dcnt) if w else [], sum(w.bcnt.values()) if w else 0,
            sorted(set(w.bcnt)) if w else [], len(w.dcnt) if w else 0,
            "OK" if par_live else "FAIL"))

    # ---- G8 the rivals, each graded on recorded numbers -------------------
    rv = rival_divergences(w, pins, b18a) if w else []
    graded = [r for r in rv if r[1] != 0]
    ok8 = len(rv) >= 6 and len(graded) >= 5
    gate("G8_rivals_fail", ok8, "rivals: " + " | ".join(
        "%s diverges by %d (%s)" % (n, d, det) for (n, d, det) in rv))

    # ---- G9 the recorded anchor tables are internally consistent ----------
    p9 = pins and b18a
    acc, ref, undec, rows = (rec.get("acc"), rec.get("refuse"),
                             rec.get("undec"), rec.get("rows"))
    eax = pins.get("eax", {})
    st = pins.get("state_line", "")
    model_state = ("flag2000=%s rand=%d s20c=%d s210=%d"
                   % (F["live"].flag2000, F["live"].rand, F["live"].s20c,
                      F["live"].s210)) if F["live"] else ""
    ok9 = (p9 and acc + ref + undec == rows
           and sum(eax.get(k, 0) for k in (0, 1, 2)) == rows
           and eax.get(0) == ref and eax.get(1, 0) + eax.get(2, 0) == acc
           and sum(sum(v) for v in pins["split"].values())
           == pins["branchA"]
           and b18a["skips"] == b18a["sentinel"]
           and st == model_state
           and len(F["corpus"]) == CORPUS_N)
    gate("G9_anchors_consistent", ok9,
         "m302 recorded table is coherent: %s+%s+%s==%s rows; eax %s sums to "
         "rows, eax0==refuse, eax1+eax2==accept; the site split sums to the "
         "%s branchA rows; b18 skips==sentinel==%s; the parsed live state "
         "'%s' == the model's own '%s'; S0 corpus %d"
         % (acc, ref, undec, rows, eax, pins.get("branchA"),
            b18a.get("skips"), st, model_state, len(F["corpus"])))
    return R, w


def k0_note(w):
    return w is not None and bool(w.accept_blk.get(0))


def report(sav_path, m302=DEF_M302, m303=DEF_M303, b18=DEF_B18, out=None,
           verdict=True):
    F = build(sav_path, m302, m303, b18)
    R, w = gates(F)
    L = list(table_lines(F))
    for name, ok, detail in R:
        L.append("%-28s %s  %s" % (name, "PASS" if ok else "FAIL", detail))
    nbad = sum(1 for _, ok, _ in R if not ok)
    if verdict:
        L.append("")
        L.append("%sB20: %d/%d gates - the BYTE-twin visit counter is "
                 "EXECUTABLE: the pinned-window law 0x94ed28+8380*block+site "
                 "(entry 1 B, 128/field, 8 blocks) ++'d by the same gated "
                 "fall-through that B19's dword counter rides, replayed over "
                 "%d recorded rows under the M302 pinned state -> %d accepts "
                 "-> %d dword CNT / %d byte CNT with per-site parity; the "
                 "byte MAX skips block 0 while the byte CNT does not; live "
                 "byte CONTENTS, the block upper bound and the settle-nest "
                 "meaning stayed DECLARED UNMODELED%s"
                 % ("FAIL " if nbad else "PASS ", len(R) - nbad, len(R),
                    w.rows if w else 0, w.accept if w else 0,
                    sum(w.dcnt.values()) if w else 0,
                    sum(w.bcnt.values()) if w else 0,
                    "" if not nbad else " - FAILING: " + "; ".join(
                        n for n, ok, _ in R if not ok)))
    if out is not None:
        out.write("\n".join(L) + "\n")
    else:
        for ln in L:
            print(ln)
    return R


def acceptance(sav_path, results, m302=DEF_M302, m303=DEF_M303, b18=DEF_B18):
    """Run the B20 gate set; grade ONLY this rung's gates. The PASS line with
    the full gate count belongs to sim.selftest (which adds G10 determinism),
    so the module verdict is suppressed here."""
    R = report(sav_path, m302, m303, b18, verdict=False)
    ok_all = True
    for name, ok, detail in R:
        results.append((name, ok))
        ok_all = ok_all and ok
    return ok_all


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sim.bytecounter")
    ap.add_argument("--sav", default=DEF_SAV)
    ap.add_argument("--m302", default=DEF_M302)
    ap.add_argument("--m303", default=DEF_M303)
    ap.add_argument("--b18", default=DEF_B18)
    ap.add_argument("--out", help="write the report to this file")
    a = ap.parse_args(argv)
    R = report(a.sav, a.m302, a.m303, a.b18,
               out=open(a.out, "w") if a.out else None)
    return 0 if all(ok for _, ok, _ in R) else 1


if __name__ == "__main__":
    sys.exit(main())
