#!/usr/bin/env python3
"""B18 (s252): the site-gate VALUE SOURCE + MAX STORES made executable
(R2's "who caches a site value and where does it land" slice; written by this
fire from M298's closed semantics sitting on top of B17's decision core - the
rung was not yet in BUILD_SPINE.md, so the build fire authored it, as B14/
B16/B17 did).

sim/sitegate.py models the three M298 laws and replays them over RECORDED
artifacts only (no box, no /proc, no gdb, no game-binary load):

  1. THE LAZY-NIBBLE CACHE (FUN_0051dcb0 0x51df85-0x51dfa4 + FUN_00582cc0):
     edi = BYTE[rec+2] >> 4 when nonzero, ELSE the 525-insn FUN_005aff90 result
     (a DECLARED recorded input: the machine val column), and FUN_00582cc0
     writes it back with BYTE[rec+2] = (old & 0x0F) | (edi << 4) - a 4-bit
     overwrite of the HIGH nibble that PRESERVES the low nibble, so the next
     walk of the same record takes the cached path. The write-back's record is
     the SAME 44-B tileview record the pod-scan score getter reads
     (rec2 = [0x92ae14] + 0x2c*([0x692184]*Y + sar(X,1)) + 2 == tileview+2).
  2. THE SITE BYTE: the store index [ebp-0xc] is zero-extended BYTE[rec+3] of
     the record the walk is on - its sole store is 0x51dd57 (own frame, the
     11 e8-callers REFUTED). The slot table is 28 B per site.
  3. THE TWO MAX STORES: slot [0x989ce8 + 28*site] = max(edi, old)
     (0x51dfbd-0x51dfcb, UNCONDITIONAL) and cell [0x94eca8 + 8380*block + site]
     = max(edi, old) (0x51dfe2-0x51dff3), SKIPPED when block == 0 (test ebx /
     je 0x51dfc9-0x51dfd1) after the -1 sentinel clamp (0x51df22-24). 8380 =
     4*2095 is the recorded owner-fold stride (NAMED M92/M297: "EXACTLY 8
     player-indexed blocks", site_gate = block 0x94d448 + 0x1860, B15). block
     here is BYTE[rec+7], the record's owner byte (FUN_00556690 indexes the
     same table [owner*8380 + region] at 0x55849b / 0x55f80e).

PARITY (recorded artifacts): evidence/m294_gate_rows_raw.txt (the m294 window:
1026 graded visits / 2321 decision rows, read through B17's loader and B16's
transposition law) and evidence/s249_live_map.bin (the s249 read-only
end-window dump of the live 44-B record array, 2048 records).

RECORDED PINS (prior sessions, cited): visits 1026 / rows 2321 (NAMED ## M294,
evidence/b17_scanleg_chain.txt:1 G1), save-view val law 1931/2321 + lazy 1
(evidence/b17_scanleg_chain.txt:7 G7), machine-multival tiles 9 / rows 230
(M296 S3b), live-snapshot classes 2102 match / 134 bit4 / 85 nibble / 0 lazy
(evidence/s249_live_census.txt S3).
FIRST-MEASUREMENT ANCHORS (this fire, reproducible from the shipped artifacts
above; they lock the model, they are not prior claims): the cache state
machine's per-row classes 2288 cached-path hits / 1 lazy write-back / 32
adopted live mutations (== 2321 rows) and the 86 of 101 tiles whose replayed
end-state nibble still matches the dump, the drift-direction
split 182 down / 31 up, the low-nibble getter rival's 76-row match, the graded
row/site histogram {1: 2253, 9: 68}, the 277 recorded rows whose save-view
owner byte is the -1 sentinel (the cell-store skip class), 0 records carrying a
legitimate 0 owner, 177 records whose high nibble changed save->live with 103
keeping the low nibble, and the store-table digests.

DECLARED UNMODELED (leads, not gaps to paper over): the FUN_005aff90 value body
(525 insns - the machine val column is the input, exactly as in B15/B17), the
[+4] visit counter inside each 28-B slot (its ++ is gated on call 0x5832b0, a
predicate with no recorded input), the identity of ebx's walked table beyond the
owner-byte reading (M298 records it as a LEAD), the live 0x989ce8/0x94eca8 table
CONTENTS (never dumped - a read-only /proc window over both globals grades the
funnel absolutely: LEAD), and every M297 end-window caveat
(evidence/s249_live_census.txt A5: the snapshot is a LAST-TURN witness).
"""
import argparse
import collections
import hashlib
import os
import re
import sys

from . import precheck as pc
from . import save as sosave
from . import scanleg as sl

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEF_SAV = os.path.join(REPO, "programs", "saves", "m54b_clean.SAV")
DEF_RAW = os.path.join(REPO, "evidence", "m294_gate_rows_raw.txt")
DEF_BIN = os.path.join(REPO, "evidence", "s249_live_map.bin")
DEF_WIN = os.path.join(REPO, "evidence", "s251_statics_fn51dcb0.txt")

# ---- the globals the pinned windows name ---------------------------------
SLOT_BASE = 0x989CE8           # site slot table (28 B per site)
SLOT_STRIDE = 28               # esi = (site*8 - site) << 2   (0x51dfb1-ba)
SLOT_FIELD_MAX = 0             # [esi+0x989ce8] the dword MAX store
SLOT_FIELD_CNT = 0x989CEC - 0x989CE8    # +4: the visit counter (0x51e00d)
CELL_BASE = 0x94ECA8           # site_gate bytes (B15: blk 0x94d448 + 0x1860)
CELL_STRIDE = 8380             # 4*(131x<<4 - x) = 4*2095     (0x51dfd3-e0)
CELL_BLOCKS = 8                # recorded: EXACTLY 8 player blocks (M92 G5)
REGION_BOUND = 128             # recorded: 128 entries per region array (M92 G8)
TILEVIEW_BASE_G = 0x92AE14     # dword tileview base pointer
ROWMULT_G = 0x692184           # dword record-row multiplier (= W/2)
REC_LEN = 44

# ---- recorded pins + first-measurement anchors (docstring) ----------------
PIN_VISITS = 1026
PIN_DEC_ROWS = 2321
PIN_TILES = 101
PIN_MULTI_TILES = 9
PIN_MULTI_ROWS = 230
PIN_SAVE_MATCH = 1931
PIN_SAVE_LAZY = 1
PIN_LIVE_MATCH = 2102
PIN_LIVE_BIT4 = 134
PIN_LIVE_NIBBLE = 85
PIN_LIVE_LAZY = 0
PIN_LIVE_RECS = 2048
PIN_DOWN_DRIFT = 182
PIN_UP_DRIFT = 31
PIN_LO_GETTER_ROWS = 76
PIN_SITE_ROWS = {1: 2253, 9: 68}
PIN_SAVE_SKIP_ROWS = 277
PIN_COL_DIVERGE = 2321
PIN_ZERO_OWNER_RECS = 0
PIN_HI_CHANGED = 177
PIN_LO_PRESERVED = 103
# cache state-machine anchors (first measurement this fire, reproducible from
# the two shipped artifacts): the per-row class of the walk and the share of
# tiles whose replayed end-state nibble still matches the s249 dump.
PIN_CACHE_HIT = 2288
PIN_CACHE_LAZY = 1
PIN_CACHE_ADOPT = 32
PIN_END_AGREE = 86


# --------------------------------------------------------------------------
# the laws, executable
# --------------------------------------------------------------------------
def cached_edi(r):
    """0x51df85-8a: edi = BYTE[rec+2] >> 4 (0 = the lazy FUN_005aff90 path)."""
    return (r[2] & 0xF0) >> 4


def write_back(b2, edi):
    """the pinned FUN_00582cc0 store (0x582ce3-0x582cf1): the HIGH nibble takes
    edi (4 bits - an edi above 15 is truncated by the pinned shl/or) and the
    LOW nibble survives the `and dl,0xf`."""
    return (b2 & 0x0F) | ((edi << 4) & 0xF0)


def score_getter(r):
    """0x46e770 (M296/B17): val = BYTE[rec+2] high nibble, zeroed when
    dword[rec+8] bit 0x1000 == byte9 bit4. Returns (val, zeroed)."""
    z = (r[9] & 0x10) != 0
    return (0 if z else (r[2] & 0xF0) >> 4), z


def site_of(r):
    """[ebp-0xc] = zero-extended BYTE[rec+3] (sole store 0x51dd57)."""
    return r[3]


def block_of(r):
    """ebx = the record's owner byte BYTE[rec+7] (the walk stores bl at
    0x51df1f; M295 reads the same byte back as tile7). The pinned -1 sentinel
    clamps to 0 (0x51df22-24) and block 0 SKIPS the cell store.
    Returns (block_after_clamp, signed_raw)."""
    raw = r[7] - 256 if r[7] >= 128 else r[7]
    return (0 if raw < 0 else raw), raw


def rec2_off(x, y, mult):
    """FUN_00582cc0's own addressing (0x582cc3-0x582ce6): byte offset of
    BYTE[rec2+2] from the tileview base."""
    return REC_LEN * (mult * y + (x >> 1)) + 2


def slot_addr(site):
    return SLOT_BASE + SLOT_STRIDE * site


def cell_addr(block, site):
    return CELL_BASE + CELL_STRIDE * block + site


class SiteGate(object):
    """the two MAX-store tables, executable, in the order the pins run them."""

    def __init__(self):
        self.slot = {}                  # site -> dword MAX
        self.cell = {}                  # (block, site) -> byte MAX
        self.rows = 0
        self.cell_skips = 0

    def visit(self, site, block, edi):
        """one record-walk step. Returns (slot_took, cell_skipped, cell_took).
        Pinned order: the slot cmp/store runs BEFORE the `test ebx,ebx` branch,
        so an ebx==0 visit still lands the slot store."""
        old = self.slot.get(site, 0)
        slot_took = edi > old                     # cmp edi,eax / jle keep-old
        self.slot[site] = edi if slot_took else old
        skipped = (block == 0)
        cell_took = None
        if not skipped:
            cold = self.cell.get((block, site), 0)
            cell_took = edi > cold
            self.cell[(block, site)] = edi if cell_took else cold
        else:
            self.cell_skips += 1
        self.rows += 1
        return slot_took, skipped, cell_took

    def digest(self):
        h = hashlib.sha256()
        for k in sorted(self.slot):
            h.update(("s%04d=%d;" % (k, self.slot[k])).encode())
        for (b, s) in sorted(self.cell):
            h.update(("c%02d.%04d=%d;" % (b, s, self.cell[(b, s)])).encode())
        return h.hexdigest()[:16]


# --------------------------------------------------------------------------
# G1: the pinned instruction windows and the laws decoded from their BYTES
# --------------------------------------------------------------------------
def load_window(path):
    """parse the shipped objdump windows into {addr: 'mnemonic operands'} (the
    printed spacing is normalised to single spaces; npat() does the same to a
    pin pattern so the two compare directly)."""
    ins = {}
    for ln in open(path):
        m = re.match(r"\s+([0-9a-f]{6}):\t([0-9a-f ]+)\t(.*)$", ln)
        if m:
            ins[int(m.group(1), 16)] = " ".join(m.group(3).split())
    return ins


def npat(p):
    """collapse the objdump column spacing out of a pin pattern."""
    return " ".join(p.split())


# (label, addr, regex against the printed instruction text)
PINS = (
    # A: FUN_00582cc0 - the whole 19-insn write-back body
    ("wb_push_ebp", 0x582CC0, r"push   ebp"),
    ("wb_load_rowmult", 0x582CC3, r"mov    eax,ds:0x692184"),
    ("wb_arg_y", 0x582CC8, r"mov    ecx,DWORD PTR \[ebp\+0x8\]"),
    ("wb_imul_rowmult", 0x582CCB, r"imul   eax,DWORD PTR \[ebp\+0xc\]"),
    ("wb_sar_x", 0x582CCF, r"sar    ecx,1"),
    ("wb_add_rec_index", 0x582CD1, r"add    eax,ecx"),
    ("wb_load_tileview_base", 0x582CD3, r"mov    ecx,DWORD PTR ds:0x92ae14"),
    ("wb_fold5", 0x582CD9, r"lea    edx,\[eax\+eax\*4\]"),
    ("wb_fold3", 0x582CDC, r"lea    eax,\[eax\+edx\*2\]"),
    ("wb_load_byte2", 0x582CDF, r"mov    dl,BYTE PTR \[ecx\+eax\*4\+0x2\]"),
    ("wb_keep_low_nibble", 0x582CE3, r"and    dl,0xf"),
    ("wb_rec_base_ret", 0x582CE6, r"lea    eax,\[ecx\+eax\*4\]"),
    ("wb_arg_val", 0x582CE9, r"mov    cl,BYTE PTR \[ebp\+0x10\]"),
    ("wb_shl4", 0x582CEC, r"shl    cl,0x4"),
    ("wb_or_nibbles", 0x582CEF, r"or     dl,cl"),
    ("wb_store_byte2", 0x582CF1, r"mov    BYTE PTR \[eax\+0x2\],dl"),
    ("wb_pop_ebp", 0x582CF4, r"pop    ebp"),
    ("wb_ret", 0x582CF5, r"ret"),
    # B: the caller's lazy path
    ("rd_nibble", 0x51DF85, r"mov    al,BYTE PTR \[edi\+0x2\]"),
    ("rd_mov_edi", 0x51DF88, r"mov    edi,eax"),
    ("rd_shr4", 0x51DF8A, r"shr    edi,0x4"),
    ("rd_cached_branch", 0x51DF8D, r"jne    0x51dfac"),
    ("rd_lazy_call", 0x51DF97, r"call   0x5aff90"),
    ("rd_result_edi", 0x51DF9F, r"mov    edi,eax"),
    ("rd_push_edi", 0x51DFA1, r"push   edi"),
    ("rd_wb_call", 0x51DFA4, r"call   0x582cc0"),
    ("rd_eax_reloaded", 0x51DFAC, r"mov    eax,DWORD PTR \[ebp-0xc\]"),
    # C: [ebp-0xc] - own frame, sole store from BYTE[rec+3]
    ("frame_own", 0x51DCB3, r"sub    esp,0x1c"),
    ("site_xor_ecx", 0x51DD48, r"xor    ecx,ecx"),
    ("site_load_byte3", 0x51DD4F, r"mov    cl,BYTE PTR \[edi\+0x3\]"),
    ("site_store", 0x51DD57, r"mov    DWORD PTR \[ebp-0xc\],ecx"),
    # D: the 28 B slot, the two MAX ops and the ebx==0 skip
    ("slot_lea8", 0x51DFB1, r"lea    esi,\[eax\*8\+0x0\]"),
    ("slot_sub", 0x51DFB8, r"sub    esi,ecx"),
    ("slot_shl2", 0x51DFBA, r"shl    esi,0x2"),
    ("slot_load_old", 0x51DFBD, r"mov    eax,DWORD PTR \[esi\+0x989ce8\]"),
    ("slot_cmp", 0x51DFC3, r"cmp    edi,eax"),
    ("slot_jle", 0x51DFC5, r"jle    0x51dfc9"),
    ("slot_take_new", 0x51DFC7, r"mov    eax,edi"),
    ("ebx_test", 0x51DFC9, r"test   ebx,ebx"),
    ("slot_store", 0x51DFCB, r"mov    DWORD PTR \[esi\+0x989ce8\],eax"),
    ("ebx_je_skip", 0x51DFD1, r"je     0x51dff5"),
    ("cell_shl6", 0x51DFD5, r"shl    edx,0x6"),
    ("cell_add_ebx", 0x51DFD8, r"add    edx,ebx"),
    ("cell_lea131", 0x51DFDA, r"lea    eax,\[ebx\+edx\*2\]"),
    ("cell_shl4", 0x51DFDD, r"shl    eax,0x4"),
    ("cell_sub_ebx", 0x51DFE0, r"sub    eax,ebx"),
    ("cell_addr_lea", 0x51DFE2, r"lea    ecx,\[ecx\+eax\*4\+0x94eca8\]"),
    ("cell_load_old", 0x51DFEB, r"mov    al,BYTE PTR \[ecx\]"),
    ("cell_cmp", 0x51DFED, r"cmp    edi,eax"),
    ("cell_jle", 0x51DFEF, r"jle    0x51dff3"),
    ("cell_take_new", 0x51DFF1, r"mov    eax,edi"),
    ("cell_store", 0x51DFF3, r"mov    BYTE PTR \[ecx\],al"),
    ("counter_load", 0x51E00D, r"mov    ecx,DWORD PTR \[esi\+0x989cec\]"),
    ("counter_inc", 0x51E01A, r"inc    ecx"),
    ("counter_store", 0x51E01B, r"mov    DWORD PTR \[esi\+0x989cec\],ecx"),
    # ebx provenance: the byte7 store + the -1 clamp
    ("ebx_store_byte7", 0x51DF1F, r"mov    BYTE PTR \[edi\+0x7\],bl"),
    ("ebx_jge", 0x51DF22, r"jge    0x51df26"),
    ("ebx_clamp", 0x51DF24, r"xor    ebx,ebx"),
    # the walk: one record row per inner pass (x += 2 up to ds:0x92a378)
    ("walk_bounds_global", 0x51E120, r"mov    eax,ds:0x92a378"),
    ("walk_x_step", 0x51E125, r"add    edi,0x2"),
    ("walk_rec_step", 0x51E128, r"add    esi,0x2c"),
    ("walk_loop_test", 0x51E12E, r"cmp    edi,eax"),
)


def decode_max_polarity(ins, cmp_addr, jle_addr, take_addr, store_addr):
    """True when the pinned chain is `cmp edi,OLD` / `jle L` / `mov eax,edi` at
    take_addr / the store at store_addr with the jump landing AT or AFTER the
    take and AT OR BEFORE the store: the edi <= old path jumps over the take, so
    the value stored is max(edi, old). A MIN store would need `jge` here."""
    if not re.match(npat(r"cmp    edi,eax$"), ins.get(cmp_addr, "")):
        return False
    m = re.match(npat(r"jle    0x([0-9a-f]+)$"), ins.get(jle_addr, ""))
    if not m:
        return False
    land = int(m.group(1), 16)
    if not (cmp_addr < take_addr and take_addr < land <= store_addr):
        return False
    if not re.match(npat(r"mov    eax,edi$"), ins.get(take_addr, "")):
        return False
    st = ins.get(store_addr, "")
    if not re.match(r"mov +(DWORD PTR |BYTE PTR )?\[", st):
        return False
    # nothing between the landing pad and the store may branch away
    for a in sorted(x for x in ins if land <= x < store_addr):
        if re.match(r"(j[a-z]+|loop|call|ret)( |$)", ins[a]):
            return False
    return True


def g1_pins(ins):
    """returns (ok, n_resolved, laws dict, [failures])."""
    bad = []
    for label, addr, pat in PINS:
        txt = ins.get(addr)
        if txt is None:
            bad.append("%s @0x%x ABSENT from the shipped windows" % (label, addr))
        elif not re.search(npat(pat), txt):
            bad.append("%s @0x%x got %r want /%s/" % (label, addr, txt, pat))
    body = " ".join(ins.get(a, "") for a in range(0x582CC0, 0x582CF6))
    callee_saved = sorted(set(re.findall(r"\b(?:e[ds]i|ebx)\b", body)))
    laws = {
        "nibble_split": bool(
            re.search(npat(r"and    dl,0xf"), body) and
            re.search(npat(r"shl    cl,0x4"), body) and
            re.search(npat(r"or     dl,cl"), body) and
            re.search(npat(r"mov    BYTE PTR \[eax\+0x2\],dl"), body)),
        "callee_clobbers": callee_saved,
        "slot_max": decode_max_polarity(ins, 0x51DFC3, 0x51DFC5, 0x51DFC7,
                                        0x51DFCB),
        "cell_max": decode_max_polarity(ins, 0x51DFED, 0x51DFEF, 0x51DFF1,
                                        0x51DFF3),
        "wb_plain_overwrite": not any(
            re.match(r"cmp |test |j", ins.get(a, ""))
            for a in range(0x582CC0, 0x582CF6)),
        "slot_store_before_branch": (ins.get(0x51DFCB) is not None and
                                     0x51DFCB < 0x51DFD1),
        "site_from_byte3_sole_store": bool(
            re.match(npat(r"xor    ecx,ecx"), ins.get(0x51DD48, "")) and
            re.match(npat(r"mov    cl,BYTE PTR \[edi\+0x3\]"),
                     ins.get(0x51DD4F, "")) and
            re.match(npat(r"mov    DWORD PTR \[ebp-0xc\],ecx"),
                     ins.get(0x51DD57, ""))),
        "stride_28": (((8 - 1) * 4) == SLOT_STRIDE),
        "counter_inside_slot": (SLOT_FIELD_CNT + 4 <= SLOT_STRIDE),
        "stride_4_aliases": all(4 * k + SLOT_FIELD_CNT == 4 * (k + 1)
                                for k in range(REGION_BOUND)),
    }
    ok = (not bad and laws["nibble_split"] and not laws["callee_clobbers"]
          and laws["slot_max"] and laws["cell_max"]
          and laws["wb_plain_overwrite"] and laws["slot_store_before_branch"]
          and laws["site_from_byte3_sole_store"] and laws["stride_28"]
          and laws["counter_inside_slot"] and laws["stride_4_aliases"])
    return ok, len(PINS) - len(bad), laws, bad


# --------------------------------------------------------------------------
# the recorded grid: graded decision rows in log order + the live snapshot
# --------------------------------------------------------------------------
class LiveGrid(object):
    """a read-only 44-B record view over the s249 end-window dump (the array
    scripts/s249_livecensus.py wrote; sim/ reads recorded bytes, never a
    process)."""

    def __init__(self, buf, mult):
        self.buf = buf
        self.mult = mult

    def rb(self, x, y):
        o = REC_LEN * (self.mult * y + (x >> 1))
        return self.buf[o:o + REC_LEN]


def graded_rows(vis):
    """B17's graded filter (a full 25-slot GROW trajectory + at least one
    decision row), decision rows in LOG order (the order the cache sees them).
    Tile legs are TRANSPOSED per the B16 reader law: field x= is the Y leg."""
    out = []
    for vi, v in enumerate(vis):
        if len(v["grow"]) != 25 or not (v["deep"] or v["acc"]):
            continue
        for s in sorted(set(v["deep"]) | set(v["acc"])):
            e = v["deep"].get(s) or v["acc"][s]
            out.append((vi, v["u"], s, e))
    return out


# --------------------------------------------------------------------------
# the report
# --------------------------------------------------------------------------
def report(sav_path, raw_path=DEF_RAW, bin_path=DEF_BIN, win_path=DEF_WIN):
    sav = sosave.parse(sav_path)
    g = pc.Grid(sav)
    W, H = sav.width, sav.height
    ins = load_window(win_path)
    rows = graded_rows(sl.load_visits(raw_path))
    lbuf = open(bin_path, "rb").read()
    lg = LiveGrid(lbuf, W // 2)

    R = []

    def gate(name, ok, detail):
        R.append((name, bool(ok), detail))

    # ---- G1 the pinned windows + the laws decoded from their bytes -------
    ok1, npin, laws, bad1 = g1_pins(ins)
    gate("G1_pins_and_decoded_laws",
         ok1 and npin == len(PINS),
         "%d/%d pinned instructions resolve in %s; decoded from the bytes: the "
         "write-back is a NIBBLE-SPLIT overwrite %s; the callee touches no "
         "edi/esi/ebx (edi SURVIVES) %s; slot store MAX %s; cell store MAX %s; "
         "no cmp/test/branch inside 0x582cc0 (a plain overwrite, not an "
         "accumulator) %s; the slot store precedes the ebx test %s; [ebp-0xc] "
         "has ONE store, from BYTE[rec+3] %s; stride 28 from (site*8-site)<<2 "
         "%s; the +4 counter fits inside the 28-B slot %s; the RETRACTED 4x "
         "indexing aliases slot k's counter onto slot k+1's value dword (so it "
         "cannot be the stride) %s%s"
         % (npin, len(PINS), os.path.basename(win_path),
            laws["nibble_split"], laws["callee_clobbers"], laws["slot_max"],
            laws["cell_max"], laws["wb_plain_overwrite"],
            laws["slot_store_before_branch"], laws["site_from_byte3_sole_store"],
            laws["stride_28"], laws["counter_inside_slot"],
            laws["stride_4_aliases"],
            "" if not bad1 else " BAD " + "; ".join(bad1[:3])))

    # ---- G2 the cached byte IS the score byte ----------------------------
    bad2 = 0
    for t in range(W * H):
        x, y = t % W, t // W
        if rec2_off(x, y, W // 2) != REC_LEN * ((W // 2) * y + (x >> 1)) + 2:
            bad2 += 1
    n_id = n_trunc = 0
    for old in range(256):
        for edi in range(32):
            nb = write_back(old, edi)
            if ((nb & 0x0F) == (old & 0x0F) and
                    ((nb & 0xF0) >> 4) == (edi & 0x0F)):
                n_id += 1
            if edi > 15:
                n_trunc += 1
    gate("G2_cache_byte_is_score_byte",
         not bad2 and n_id == 256 * 32 and n_trunc == 256 * 16,
         "the write-back target rec2+2 == the tileview record's byte2 on %d/%d "
         "tiles (row mult %d = W/2; the two globals 0x692184 / 0x92ae14 the "
         "callee loads ARE the tileview formula's own); the nibble law holds "
         "exhaustively over 256 old bytes x 32 edi values (low nibble preserved "
         "AND high nibble == edi mod 16): %d/%d combos - and the cache field is "
         "4 bits, so an edi above 15 is TRUNCATED by the pinned shl/or (%d "
         "combos; no recorded val reaches it)"
         % (W * H - bad2, W * H, W // 2, n_id, 256 * 32, n_trunc))

    # ---- G3 the sticky cache over the recorded walk ----------------------
    tile_seen = collections.OrderedDict()
    for (vi, u, s, e) in rows:
        tile_seen.setdefault((e["y"], e["x"]), []).append((vi, e["val"]))
    tiles = len(tile_seen)
    multi = {}
    for k, vs in tile_seen.items():
        if len(set(v for (_, v) in vs)) > 1:
            multi[k] = sorted(set(v for (_, v) in vs))
    multi_rows = sum(len(vs) for k, vs in tile_seen.items() if k in multi)
    # the FULL state replay, honoring the pinned branch at 0x51df8d: the lazy
    # call AND the 0x582cc0 write-back run only when the cached nibble is zero;
    # a nonzero cached nibble that disagrees with the machine val is an external
    # map mutation (the model adopts the observed byte, the only gradeable read)
    cl3 = collections.Counter()
    end_agree = 0
    for (X, Y), vs in tile_seen.items():
        b2 = g.rb(X, Y)[2]
        for (vi, val) in vs:
            edi = (b2 & 0xF0) >> 4
            if edi == val:
                cl3["hit"] += 1                        # the cached path 0x51df8d
            elif edi == 0:
                cl3["lazy_wb"] += 1                    # 0x5aff90 then 0x582cc0
                b2 = write_back(b2, val)
            else:
                cl3["adopt_mutate"] += 1               # live map recompute
                b2 = write_back(b2, val)
        end_agree += 1 if ((lg.rb(X, Y)[2] & 0xF0) >> 4) == ((b2 & 0xF0) >> 4) \
            else 0
    n_agree = end_agree
    gate("G3_sticky_cache_replay",
         (len(rows) == PIN_DEC_ROWS and tiles == PIN_TILES and
          len(multi) == PIN_MULTI_TILES and multi_rows == PIN_MULTI_ROWS and
          cl3["hit"] == PIN_CACHE_HIT and cl3["lazy_wb"] == PIN_CACHE_LAZY and
          cl3["adopt_mutate"] == PIN_CACHE_ADOPT and
          cl3["hit"] + cl3["lazy_wb"] + cl3["adopt_mutate"] == len(rows) and
          n_agree == PIN_END_AGREE),
         "%d rows over %d tiles replayed through the cache STATE machine (the "
         "pinned 0x51df8d branch: the lazy call and the 0x582cc0 write-back run "
         "ONLY on a zero nibble): %d cached-path hits, %d lazy+write-back "
         "resolutions, %d adopted live mutations == %d rows. Tiles whose value "
         "changed more than once inside the window %d (RECORDED M296 S3b %d) "
         "carrying %d rows (RECORDED %d) - the sticky law: a record keeps its "
         "cached value until a live map mutation forces a recompute. The "
         "replayed end-state nibble equals the s249 end-window snapshot's on "
         "%d/%d tiles (anchor %d): the cache law survives to the dump%s"
         % (len(rows), tiles, cl3["hit"], cl3["lazy_wb"], cl3["adopt_mutate"],
            len(rows), len(multi), PIN_MULTI_TILES, multi_rows, PIN_MULTI_ROWS,
            n_agree, tiles, PIN_END_AGREE,
            " (the %d divergences are the declared post-grading drift, A5)"
            % (tiles - n_agree) if n_agree < tiles else ""))

    # ---- G4 the save-seeded read path -----------------------------------
    cl4 = collections.Counter()
    for (vi, u, s, e) in rows:
        sv = cached_edi(g.rb(e["y"], e["x"]))
        cl4["match" if sv == e["val"] else
            ("lazy" if (sv == 0 and e["val"] > 0) else "mutate")] += 1
    gate("G4_lazy_class_save_side",
         (cl4["match"] == PIN_SAVE_MATCH and cl4["lazy"] == PIN_SAVE_LAZY and
          sum(cl4.values()) == PIN_DEC_ROWS),
         "the read path seeded at the y2150 save: cached-path match %d "
         "(RECORDED 1931, evidence/b17_scanleg_chain.txt:7), lazy FUN_005aff90 "
         "class %d (RECORDED 1), nibble-mutation class %d - the last class is "
         "the write-back/lazy population the save view cannot see; sum %d == "
         "%d rows" % (cl4["match"], cl4["lazy"], cl4["mutate"],
                      sum(cl4.values()), PIN_DEC_ROWS))

    # ---- G5 the snapshot: the cache is never undone ----------------------
    cl5 = collections.Counter()
    for (vi, u, s, e) in rows:
        lv, z = score_getter(lg.rb(e["y"], e["x"]))
        if lv == e["val"] and not z:
            cl5["match"] += 1
        elif z:
            cl5["bit4"] += 1
        elif lv == 0:
            cl5["lazy"] += 1
        else:
            cl5["nibble"] += 1
    hi_ch = lo_pres = 0
    for y in range(H):
        for x in range(0, W, 2):
            a, b = g.rb(x, y), lg.rb(x, y)
            if (a[2] & 0xF0) != (b[2] & 0xF0):
                hi_ch += 1
                if (a[2] & 0x0F) == (b[2] & 0x0F):
                    lo_pres += 1
    gate("G5_live_snapshot_no_clears",
         (cl5["match"] == PIN_LIVE_MATCH and cl5["bit4"] == PIN_LIVE_BIT4 and
          cl5["nibble"] == PIN_LIVE_NIBBLE and cl5["lazy"] == PIN_LIVE_LAZY and
          len(lbuf) == REC_LEN * PIN_LIVE_RECS and hi_ch == PIN_HI_CHANGED and
          lo_pres == PIN_LO_PRESERVED),
         "%d records x %d B graded (RECORDED M297 S3 verbatim): match %d, "
         "bit4-zeroed %d, nibble-drift %d, and the cache law's own observable "
         "lazy %d (RECORDED %d) - no recorded nonzero val ever meets a zeroed "
         "nibble in the snapshot: the write-back is never undone on a graded "
         "tile; the write-back signature over the whole map: high nibble "
         "changed on %d records (anchor %d), of which %d kept the LOW nibble "
         "intact (anchor %d) - the pinned nibble-split, not a whole-byte store"
         % (len(lbuf) // REC_LEN, REC_LEN, cl5["match"], cl5["bit4"],
            cl5["nibble"], cl5["lazy"], PIN_LIVE_LAZY, hi_ch, PIN_HI_CHANGED,
            lo_pres, PIN_LO_PRESERVED))

    # ---- G6 the cache is an overwrite, not an accumulator ---------------
    dn = up = lo_eq = 0
    for (vi, u, s, e) in rows:
        r = lg.rb(e["y"], e["x"])
        hi = (r[2] & 0xF0) >> 4
        dn += 1 if hi < e["val"] else 0
        up += 1 if hi > e["val"] else 0
        lo_eq += 1 if (r[2] & 0x0F) == e["val"] else 0
    gate("G6_overwrite_not_accumulator",
         (dn == PIN_DOWN_DRIFT and up == PIN_UP_DRIFT and
          lo_eq == PIN_LO_GETTER_ROWS),
         "the nibble moves BOTH ways against the recorded val: %d rows have the "
         "live high nibble BELOW the val (anchor %d) and %d ABOVE it (anchor "
         "%d) - a MAX-accumulator cache contradicts the %d down-drifts, a "
         "MIN-accumulator contradicts the %d up-drifts, and the pinned "
         "0x582cc0 is an overwrite; the MAX laws live in the store tables "
         "(0x989ce8 / 0x94eca8), NOT in the nibble; rival getter 'val = LOW "
         "nibble' matches only %d/%d rows (vs %d for the high nibble)"
         % (dn, PIN_DOWN_DRIFT, up, PIN_UP_DRIFT, dn, up, lo_eq, PIN_DEC_ROWS,
            PIN_LIVE_MATCH))

    # ---- G7 site byte + owner block, both from the record ---------------
    sites_hist = collections.Counter()
    per_visit = collections.defaultdict(set)
    neg_one_save = 0
    for (vi, u, s, e) in rows:
        X, Y = e["y"], e["x"]
        r = g.rb(X, Y)
        sites_hist[site_of(r)] += 1
        per_visit[vi].add(site_of(r))
        if block_of(r)[1] == -1:
            neg_one_save += 1
    mixed = sum(1 for k in per_visit if len(per_visit[k]) != 1)
    nvis = len(per_visit)
    max_site = max(sites_hist)
    zero_owner = 0
    for y in range(H):
        for x in range(0, W, 2):
            for gr in (g, lg):
                zero_owner += 1 if gr.rb(x, y)[7] == 0 else 0
    col_div = 0
    for (vi, u, s, e) in rows:
        X, Y = e["y"], e["x"]
        col_div += 1 if sav.data[sav.grid_off + 22 * (e["x"] * W + e["y"])] \
            != site_of(g.rb(X, Y)) else 0
    walk_row = 32                        # ds:0x92a378 = 64 bounds / step 2
    gate("G7_site_byte_and_block",
         (dict(sites_hist) == PIN_SITE_ROWS and max_site < REGION_BOUND and
          mixed == 0 and nvis == PIN_VISITS and
          neg_one_save == PIN_SAVE_SKIP_ROWS and
          zero_owner == PIN_ZERO_OWNER_RECS and col_div == PIN_COL_DIVERGE and
          walk_row * REC_LEN * H == len(lbuf)),
         "site = BYTE[rec+3]: the graded rows carry %s (anchor %s), max site "
         "%d is under the %d-entry per-region bound, %d/%d visits are "
         "single-site; block = BYTE[rec+7]: %d graded rows carry the -1 owner "
         "sentinel (anchor %d) so the clamp sends them to block 0 and the CELL "
         "store is SKIPPED while the slot store stands, and a legitimate 0 "
         "owner appears in %d records of %d in either view (anchor %d) - the "
         "skip class IS exactly the unowned tiles; the ring-index rival for ebx "
         "would reach block %d+, past the recorded %d-block family; rival 'site "
         "= the save 22-B column byte0' diverges on %d/%d rows (anchor %d); the "
         "pinned inner walk (x += 2 up to ds:0x92a378) steps %d records of 0x2c "
         "== one row of the %d-record dump"
         % (dict(sorted(sites_hist.items())), PIN_SITE_ROWS, max_site,
            REGION_BOUND, nvis - mixed, nvis, neg_one_save, PIN_SAVE_SKIP_ROWS,
            zero_owner, 2 * PIN_LIVE_RECS, PIN_ZERO_OWNER_RECS, CELL_BLOCKS,
            CELL_BLOCKS, col_div, PIN_DEC_ROWS, PIN_COL_DIVERGE, walk_row,
            PIN_LIVE_RECS))

    # ---- G8 the MAX-store funnel ----------------------------------------
    sg = SiteGate()
    last_write = {}
    min_t = {}
    site_max = collections.defaultdict(lambda: -1)
    cell_exp = {}          # the expected (block, site) MAX, from the record set
    cell_min_exp = {}
    cell_blkless_exp = {}   # rival key: the owner block ignored
    zero_owner_rows = 0
    for (vi, u, s, e) in rows:
        X, Y = e["y"], e["x"]
        r = g.rb(X, Y)
        blk, raw = block_of(r)
        site = site_of(r)
        sg.visit(site, blk, e["val"])
        last_write[site] = e["val"]
        min_t[site] = min(min_t.get(site, e["val"]), e["val"])
        site_max[site] = max(site_max[site], e["val"])
        if blk == 0:
            zero_owner_rows += 1
            continue                    # the pinned skip: no cell write at all
        cell_exp[(blk, site)] = max(cell_exp.get((blk, site), -1), e["val"])
        cell_min_exp[(blk, site)] = min(
            cell_min_exp.get((blk, site), e["val"]), e["val"])
        cell_blkless_exp[site] = max(cell_blkless_exp.get(site, -1), e["val"])
    slot_final_ok = all(sg.slot[k] == site_max[k] for k in sg.slot)
    diverge_last = sum(1 for k in sg.slot if sg.slot[k] != last_write[k])
    diverge_min = sum(1 for k in sg.slot if sg.slot[k] != min_t[k])
    # the CELL table is GRADED, not just counted (Greptile #264 P2): exact key
    # set, exact per-(block,site) MAX, no entry for the skipped block 0 - and
    # the MIN / block-blind rivals must actually disagree (a vacuous check is
    # no check, and two identical wrong runs would pass determinism)
    cell_n_diverge = (len(set(sg.cell) ^ set(cell_exp)) +
                      sum(1 for k in set(sg.cell) & set(cell_exp)
                          if sg.cell[k] != cell_exp[k]))
    cell_div_min = sum(1 for k in sg.cell
                       if sg.cell[k] != cell_min_exp.get(k, -2))
    cell_div_blk = sum(1 for k in sg.cell
                       if sg.cell[k] != cell_blkless_exp.get(k[1], -2))
    gate("G8_max_store_funnel",
         (sg.rows == PIN_DEC_ROWS and sg.cell_skips == PIN_SAVE_SKIP_ROWS and
          zero_owner_rows == PIN_SAVE_SKIP_ROWS and slot_final_ok and
          cell_n_diverge == 0 and not any(b == 0 for (b, _) in sg.cell) and
          len(sg.cell) == len(cell_exp) and diverge_last > 0 and
          diverge_min > 0 and cell_div_min > 0 and cell_div_blk > 0),
         "%d walk steps through the tables: slot entries %d (sites %s), cell "
         "entries %d over %d owner blocks, %d steps SKIPPED the cell store "
         "(anchor %d; %d rows carried the -1 owner byte -> clamp 0, the two "
         "agree, and NO cell entry exists for block 0); every stored value is "
         "monotone non-decreasing, each SLOT ends at the recorded MAX (%s) and "
         "every CELL (block, site) equals the recorded per-pair MAX EXACTLY - "
         "key set and values, %d disagreements. The model's law CHOICE is "
         "DISCRIMINATING on this record set: last-write ends %d slot(s) "
         "elsewhere, a MIN store %d slot(s) and %d cell(s), and a cell key "
         "without the owner block %d cell(s); slot+cell digest %s. DECLARED: "
         "neither table's LIVE contents are in any recorded artifact - the "
         "absolute grade is a read-only /proc window over 0x989ce8/0x94eca8 "
         "(LEAD) - and the [+4] visit counter is UNMODELED (its ++ is gated on "
         "call 0x5832b0, no recorded input)"
         % (sg.rows, len(sg.slot), sorted(sg.slot), len(sg.cell),
            len(set(b for (b, _) in sg.cell)), sg.cell_skips,
            PIN_SAVE_SKIP_ROWS, zero_owner_rows, slot_final_ok,
            cell_n_diverge, diverge_last, diverge_min, cell_div_min,
            cell_div_blk, sg.digest()))

    # ---- G9 the rivals, consolidated ------------------------------------
    riv = [
        ("whole-byte write-back",
         "the pinned body keeps the low nibble (and dl,0xf / or dl,cl) and %d "
         "changed records kept it too" % lo_pres),
        ("edi clobbered by 0x582cc0",
         "the 19-insn body names no edi/esi/ebx: %s" % (laws["callee_clobbers"],)),
        ("nibble max-accumulator", "%d rows where the live high nibble is BELOW "
         "the recorded val" % dn),
        ("nibble min-accumulator", "%d rows where it is ABOVE" % up),
        ("getter reads the LOW nibble", "matches %d/%d rows, not %d"
         % (lo_eq, PIN_DEC_ROWS, PIN_LIVE_MATCH)),
        ("site = the 22-B column byte0", "diverges on %d/%d rows"
         % (col_div, PIN_DEC_ROWS)),
        ("ebx = the 25-slot ring index", "block %d+ runs past the recorded %d-"
         "block owner family" % (CELL_BLOCKS, CELL_BLOCKS)),
        ("slot store indexed 4*value (RETRACTED M294 phrasing)",
         "aliases slot k's +4 counter onto slot k+1's value dword"),
        ("the 11 e8-callers write [ebp-0xc]",
         "own frame (sub esp,0x1c), ONE store 0x51dd57 from BYTE[rec+3]"),
        ("the save is the whole story (no live cache change)",
         "%d mutation rows + %d records whose high nibble moved save->live"
         % (cl4["mutate"], hi_ch)),
    ]
    gate("G9_rivals_fail_the_same_fit",
         (len(riv) == 10 and dn > 0 and up > 0 and lo_eq < PIN_LIVE_MATCH and
          col_div == PIN_DEC_ROWS and cl4["mutate"] > 0 and
          not laws["callee_clobbers"]),
         " | ".join("%s: refuted by %s" % (n, v) for (n, v) in riv))

    return R


def acceptance(sav_path, results, raw=DEF_RAW, bin_path=DEF_BIN, win=DEF_WIN):
    for name, ok, detail in report(sav_path, raw, bin_path, win):
        results.append((name, ok))
        print("%-27s %s  %s" % (name, "PASS" if ok else "FAIL", detail))
    return all(ok for (_, ok) in results)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sim.sitegate")
    ap.add_argument("--sav", default=DEF_SAV)
    ap.add_argument("--raw", default=DEF_RAW)
    ap.add_argument("--live", default=DEF_BIN)
    ap.add_argument("--windows", default=DEF_WIN)
    ap.add_argument("--out", help="write the report here (else stdout)")
    a = ap.parse_args(argv)
    R = report(a.sav, a.raw, a.live, a.windows)
    lines = ["%-27s %s  %s" % (n, "PASS" if ok else "FAIL", d)
             for (n, ok, d) in R]
    nbad = sum(1 for (_, ok, _) in R if not ok)
    lines.append(("FAIL B18: %d/%d gates failed" % (nbad, len(R))) if nbad else
                 "PASS B18: %d/%d gates - the site-gate value source (the lazy "
                 "nibble cache + the 0x582cc0 write-back), the BYTE[rec+3] site "
                 "index and the slot/cell MAX stores replay the recorded m294 "
                 "window and the s249 end-window snapshot (no box time, no "
                 "/proc, no gdb)" % (len(R), len(R)))
    txt = "\n".join(lines) + "\n"
    if a.out:
        with open(a.out, "w") as f:
            f.write(txt)
    else:
        sys.stdout.write(txt)
    return 1 if nbad else 0


if __name__ == "__main__":
    sys.exit(main())
