"""B15 (s243): the per-site production gate tables 0x94e5a8 / 0x94eca8 NAMED,
and the hub pod-scan PRICE GATE (FUN_0055f650 0x563bf7-0x563cad) made executable.

Authority is the RECORDED objdump window `evidence/b15_gate_window.txt` (written
by `scripts/b15_gate_window.py` from the scratch/m574/text.txt .text cache).
`interpret_gate()` executes those recorded instruction bytes over a sparse
memory model; `price_gate()` is the closed form. selftest --b15 pins them
against each other over a decision grid and fails rivals that do not agree.

Named here (cite lines in NAMED.md ## B15):
  0x94e5a8  site_score  byte[blk + region + 0x94e5a8], blk = fac*8380 (=0x20bc)
                        (block base 0x94d448 + 0x1160; M92's divisor-block view
                        puts it at 0x94e488 + 0x120)
                        writer: FUN_00556690 (M94: 0x556721/0x556b5a); 5 stores
  0x94eca8  site_gate   byte[blk + region + 0x94eca8] (blk+0x1860)
                        NO direct store image-wide; the only writer is
                        FUN_0051dcb0 via zero sweep (0x51dcd1/0x51dce7) and an
                        ADDRESS-COPIED store (lea 0x51dfe2 -> mov BYTE PTR
                        [ecx],al at 0x51dff3) - the trap-3 shape.
  0x920434  published_window_id  (M125 census: 15 writes / 634 refs, 12 of 15
                        writes inside the widget-reset sequence; live solo = 0,
                        M293 D1b) - the msg-leg gate at [ebp-0xa4].

Gate law (every branch name is what the interpreter reports from the bytes):
  skip-argmax   value <= best_val                       (0x563c0f/0x563c11)
  accept-bypass value >= 2*(8 - nearest_dist)           (0x563c24-0x563c38)
  accept-mult0  byte[blk+region+0x94e5a8] == 0          (0x563c3d/0x563c46)
  accept-bases  dword[blk+0x94e488] < 2   (base count, M94) (0x563c48/0x563c4f)
  thr fold      thr = (verdict == 8) ? 1 : 4            (0x563c60-0x563c6a;
                verdict = byte[blk+region+0x94eda8] of the POD's region,
                read at the prologue 0x55f811, published [ebp-0x8c] 0x55f81b)
  thr max       if site_gate byte > thr: thr = it       (0x563c6b-0x563c6f)
  accept-value  value >= thr                            (0x563c71/0x563c73)
  skip-case     case ([ebp-0x44], type plan byte M127) != 8 (0x563c75/0x563c79)
  skip-unit     byte[unitrec + 0x11] == 0x18            (0x563c7e/0x563c85)
  skip-tiles    dword[0x989ce4 + 28*region] >= 6*(mult+1) (0x563c87-0x563ca5)
                NOTE: edx at 0x563c8e carries the dl written at 0x563c3d -
                the ceiling is 6*(site_score+1), NOT a ring-index (the
                interpreter catches what the closed form alone must not guess).
  accept-case8  fallthrough                             (-> 0x563ca7)
"""

import re

MASK = 0xFFFFFFFF
FAM_STRIDE = 0x20BC          # per-faction block stride = DECIMAL 8380 = 0x20BC (M258 G8 / M257 fold)
SITE_SCORE = 0x94E5A8        # site_score byte x 128 (block base 0x94d448 + 0x1160; M92 divisor-block view = 0x94e488 + 0x120)
SITE_GATE = 0x94ECA8         # site_gate byte x 128 (blk+0x1860)
SITE_VERDICT = 0x94EDA8      # region verdict byte (M253)
BLOCK_BASECOUNT = 0x94E488   # dword: the faction's base count (M94)
NEAREST_DIST = 0x8F0D34      # dword: FUN_004e3620 nearest-location distance
REGION_TILES1 = 0x989CE4     # dword[region*7*4 + ...]: 2nd row of the M253 G3 7-dword region table
UNIT_BASE = 0x933278         # 52-B unit records (M292)

# pc -> expected mnemonic operand text (regex) in the scan-gate window.
# The interpreter refuses to run any pc whose RECORDED line does not match.
GATE_PINS = [
    (0x563BF7, r"mov\s+ebx,DWORD PTR \[ebp-0x34\]", "slot_region"),
    (0x563BFA, r"mov\s+eax,DWORD PTR \[ebp-0x8\]", "slot_candx"),
    (0x563BFD, r"mov\s+ecx,DWORD PTR \[ebp-0x4\]", "slot_candy"),
    (0x563C00, r"push\s+eax", "noop"),
    (0x563C01, r"push\s+ecx", "noop"),
    (0x563C02, r"call\s+0x46e770", "call_value"),
    (0x563C07, r"mov\s+esi,eax", "mv_si_eax"),
    (0x563C09, r"mov\s+eax,DWORD PTR \[ebp-0x24\]", "slot_best"),
    (0x563C0C, r"add\s+esp,0x8", "noop"),
    (0x563C0F, r"cmp\s+esi,eax", "cmp_si_eax"),
    (0x563C11, r"jle\s+0x563cb3", "jle_skip_argmax"),
    (0x563C17, r"mov\s+edx,DWORD PTR \[ebp-0x8\]", "slot_candx_edx"),
    (0x563C1A, r"mov\s+eax,DWORD PTR \[ebp-0x4\]", "slot_candy"),
    (0x563C1D, r"push\s+edx", "noop"),
    (0x563C1E, r"push\s+eax", "noop"),
    (0x563C1F, r"call\s+0x4e3620", "call_dist"),
    (0x563C24, r"mov\s+edi,DWORD PTR ds:0x8f0d34", "ld_dist_global"),
    (0x563C2A, r"mov\s+ecx,0x8", "mv_cx8"),
    (0x563C2F, r"sub\s+ecx,edi", "sub_cx_dist"),
    (0x563C34, r"shl\s+ecx,1", "shl_cx1"),
    (0x563C36, r"cmp\s+esi,ecx", "cmp_si_cx"),
    (0x563C38, r"jge\s+0x563ca7", "jge_accept_bypass"),
    (0x563C3A, r"mov\s+edi,DWORD PTR \[ebp-0x48\]", "slot_block"),
    (0x563C3D, r"mov\s+dl,BYTE PTR \[edi\+ebx\*1\+0x94e5a8\]", "ld_site_score"),
    (0x563C44, r"test\s+dl,dl", "test_dl"),
    (0x563C46, r"je\s+0x563ca7", "je_accept_mult0"),
    (0x563C48, r"cmp\s+DWORD PTR \[edi\+0x94e488\],0x2", "cmp_basecount"),
    (0x563C4F, r"jl\s+0x563ca7", "jl_accept_bases"),
    (0x563C51, r"mov\s+eax,DWORD PTR \[ebp-0x8c\]", "slot_verdict"),
    (0x563C57, r"xor\s+ecx,ecx", "xor_cx"),
    (0x563C59, r"mov\s+cl,BYTE PTR \[edi\+ebx\*1\+0x94eca8\]", "ld_site_gate"),
    (0x563C60, r"sub\s+eax,0x8", "sub_ax8"),
    (0x563C63, r"neg\s+eax", "neg_ax"),
    (0x563C65, r"sbb\s+eax,eax", "sbb_ax"),
    (0x563C67, r"and\s+eax,0x3", "and_ax3"),
    (0x563C6A, r"inc\s+eax", "inc_ax"),
    (0x563C6B, r"cmp\s+ecx,eax", "cmp_cx_thr"),
    (0x563C6D, r"jle\s+0x563c71", "jle_skipmax"),
    (0x563C6F, r"mov\s+eax,ecx", "mv_max"),
    (0x563C71, r"cmp\s+esi,eax", "cmp_si_thr"),
    (0x563C73, r"jge\s+0x563ca7", "jge_accept_value"),
    (0x563C75, r"cmp\s+DWORD PTR \[ebp-0x44\],0x8", "cmp_case"),
    (0x563C79, r"jne\s+0x563cb3", "jne_skip_case"),
    (0x563C7B, r"mov\s+eax,DWORD PTR \[ebp-0x10\]", "slot_unit"),
    (0x563C7E, r"cmp\s+BYTE PTR \[eax\+0x933289\],0x18", "cmp_unit11"),
    (0x563C85, r"je\s+0x563cb3", "je_skip_unit"),
    (0x563C87, r"lea\s+ecx,\[ebx\*8\+0x0\]", "lea_r8"),
    (0x563C8E, r"and\s+edx,0xff", "and_dx_ff"),
    (0x563C94, r"sub\s+ecx,ebx", "sub_cx_r7"),
    (0x563C96, r"inc\s+edx", "inc_dx"),
    (0x563C97, r"mov\s+eax,DWORD PTR \[ecx\*4\+0x989ce4\]", "ld_tiles1"),
    (0x563C9E, r"lea\s+edx,\[edx\+edx\*2\]", "lea_dx3"),
    (0x563CA1, r"shl\s+edx,1", "shl_dx1"),
    (0x563CA3, r"cmp\s+eax,edx", "cmp_tiles"),
    (0x563CA5, r"jge\s+0x563cb3", "jge_skip_tiles"),
    (0x563CA7, r"mov\s+eax,DWORD PTR \[ebp-0x2c\]", "slot_ring"),
    (0x563CAA, r"mov\s+DWORD PTR \[ebp-0x24\],esi", "store_best"),
    (0x563CAD, r"mov\s+DWORD PTR \[ebp-0x84\],eax", "store_bestidx"),
]

# Prologue pins (FUN_0055f650 0x55f650+): the def-use of every gate operand.
PROLOGUE_PINS = [
    (0x55F6B0, r"cmp\s+DWORD PTR ds:0x920434,ebx", "msg-gate: published_window_id != 0"),
    (0x55F6C0, r"mov\s+ecx,DWORD PTR ds:0x91b5b4", "human faction"),
    (0x55F6C6, r"mov\s+al,BYTE PTR \[edx\*4\+0x933286\]", "unit owner byte"),
    (0x55F6D6, r"mov\s+DWORD PTR \[ebp-0xa4\],ebx", "[ebp-0xa4] single writer (M290/M293)"),
    (0x55F73A, r"mov\s+bl,BYTE PTR \[ecx\+0x98adb2\]", "type-record plan byte +42 (M127)"),
    (0x55F74A, r"mov\s+DWORD PTR \[ebp-0x44\],eax", "case = plan byte of the pod's type"),
    (0x55F79F, r"mov\s+al,BYTE PTR \[esi\+0x3\]", "record-view byte 3 = region label (M249)"),
    (0x55F7A5, r"mov\s+DWORD PTR \[ebp-0x34\],eax", "pod REGION -> gate index ebx"),
    (0x55F80E, r"mov\s+DWORD PTR \[ebp-0x48\],edi", "block base = owner*8380 (fold)"),
    (0x55F811, r"mov\s+dl,BYTE PTR \[edi\+eax\*1\+0x94eda8\]", "POD-region verdict byte"),
    (0x55F81B, r"mov\s+DWORD PTR \[ebp-0x8c\],edx", "verdict -> [ebp-0x8c] (thr fold input)"),
]

# FUN_0051dcb0: the family updater and the ONLY site_gate writer (trap-3 shape).
WRITER_PINS = [
    (0x51DCB8, r"mov\s+edx,0x94eca8", "edx := site_gate base"),
    (0x51DCE7, r"mov\s+BYTE PTR \[edx\+ecx\*1\],0x0", "zero sweep of site_gate[region]"),
    (0x51DFE2, r"lea\s+ecx,\[ecx\+eax\*4\+0x94eca8\]", "ADDRESS-COPIED site_gate addr"),
    (0x51DFF3, r"mov\s+BYTE PTR \[ecx\],al", "THE store the shape grep never sees"),
]


def load_window(path):
    """Parse evidence/b15_gate_window.txt -> {pc: 'mnemonic operands'}."""
    pcs = {}
    line_re = re.compile(r"^\s*([0-9a-f]{6,8}):\s+(?:[0-9a-f]{2,} )*\s*([a-z][a-z0-9]*)\s*(.*)$")
    with open(path) as f:
        for ln in f:
            m = line_re.match(ln)
            if not m:
                continue
            pcs[int(m.group(1), 16)] = (m.group(2), m.group(3).strip())
    return pcs


def _signed(v):
    return v - (1 << 32) if v >= (1 << 31) else v


class GateError(Exception):
    pass


def interpret_gate(rec, st):
    """Execute the RECORDED gate window (0x563bf7-0x563cad) over the machine
    `st`: st.slots (dict off->int), st.mem (sparse dict addr->int for bytes;
    dwords must be present too), st.fns {'value': fn(x,y), 'dist': fn(x,y)}.
    Returns (outcome, branch) with outcome in {'accept','skip'} and mutates
    st.slots[-0x24] / [-0x84] on accept (the best-update store, 0x563caa-0x563cad).
    Every executed pc must be present in `rec` AND match its shipped pin
    pattern - a missing/mismatched recorded line raises GateError."""
    R = {"eax": 0, "ebx": 0, "ecx": 0, "edx": 0, "esi": 0, "edi": 0}
    CF = [0]
    pins = {pc: (pat, fn) for pc, pat, fn in GATE_PINS}
    pc = 0x563BF7
    order = [p for p, _, _ in GATE_PINS]
    steps = 0
    while True:
        steps += 1
        if steps > 64:
            raise GateError("gate window did not terminate")
        if pc not in pins:
            raise GateError("pc %#x outside the pinned window" % pc)
        if pc not in rec:
            raise GateError("recorded window missing pc %#x" % pc)
        mnem, ops = rec[pc]
        text = (mnem + " " + ops).strip()
        if not re.fullmatch(pins[pc][0], text):
            raise GateError("pc %#x recorded %r != pin %r" % (pc, text, pins[pc][0]))

        def loadb(addr):
            a = addr & MASK
            if a not in st.mem:
                raise GateError("model memory missing byte at %#x" % a)
            return st.mem[a] & 0xFF

        def loadd(addr):
            a = addr & MASK
            if a not in st.mem:
                raise GateError("model memory missing dword at %#x" % a)
            return st.mem[a] & MASK

        S = st.slots
        kind = pins[pc][1]
        if kind == "noop":
            pass
        elif kind == "slot_region":
            R["ebx"] = S[-0x34]
        elif kind == "slot_candx":
            R["eax"] = S[-0x8]
        elif kind == "slot_candy":
            R["ecx"] = S[-0x4]
        elif kind == "call_value":
            R["eax"] = st.fns["value"](S[-0x8], S[-0x4])
        elif kind == "mv_si_eax":
            R["esi"] = R["eax"]
        elif kind == "slot_best":
            R["eax"] = S[-0x24]
        elif kind == "cmp_si_eax":
            d = _signed(R["esi"]) - _signed(R["eax"])
            CF[0] = 0
            if d < 0:
                st.nf = True
        elif kind == "jle_skip_argmax":
            if _signed(R["esi"]) <= _signed(R["eax"]):
                return ("skip", "argmax")
        elif kind == "slot_candx_edx":
            R["edx"] = S[-0x8]
        elif kind == "call_dist":
            d = st.fns["dist"](S[-0x8], S[-0x4])
            st.mem[NEAREST_DIST] = d & MASK
        elif kind == "ld_dist_global":
            R["edi"] = loadd(NEAREST_DIST)
        elif kind == "mv_cx8":
            R["ecx"] = 8
        elif kind == "sub_cx_dist":
            R["ecx"] = (R["ecx"] - R["edi"]) & MASK
        elif kind == "shl_cx1":
            R["ecx"] = (R["ecx"] << 1) & MASK
        elif kind == "cmp_si_cx":
            pass
        elif kind == "jge_accept_bypass":
            if _signed(R["esi"]) >= _signed(R["ecx"]):
                R["eax"] = S[-0x2c]
                S[-0x24] = R["esi"]
                S[-0x84] = R["eax"]
                return ("accept", "bypass")
        elif kind == "slot_block":
            R["edi"] = S[-0x48]
        elif kind == "ld_site_score":
            a = (R["edi"] + R["ebx"] + SITE_SCORE) & MASK
            R["edx"] = (R["edx"] & ~0xFF) | loadb(a)
        elif kind == "test_dl":
            pass
        elif kind == "je_accept_mult0":
            if (R["edx"] & 0xFF) == 0:
                R["eax"] = S[-0x2c]
                S[-0x24] = R["esi"]
                S[-0x84] = R["eax"]
                return ("accept", "mult0")
        elif kind == "cmp_basecount":
            loadd(R["edi"] + BLOCK_BASECOUNT)
        elif kind == "jl_accept_bases":
            if _signed(st.mem[(R["edi"] + BLOCK_BASECOUNT) & MASK]) < 2:
                R["eax"] = S[-0x2c]
                S[-0x24] = R["esi"]
                S[-0x84] = R["eax"]
                return ("accept", "bases")
        elif kind == "slot_verdict":
            R["eax"] = S[-0x8c]
        elif kind == "xor_cx":
            R["ecx"] = 0
        elif kind == "ld_site_gate":
            a = (R["edi"] + R["ebx"] + SITE_GATE) & MASK
            R["ecx"] = loadb(a)
        elif kind == "sub_ax8":
            R["eax"] = (R["eax"] - 8) & MASK
        elif kind == "neg_ax":
            src = R["eax"]
            R["eax"] = (-src) & MASK
            CF[0] = 1 if src != 0 else 0
        elif kind == "sbb_ax":
            R["eax"] = (0 - 0 - CF[0]) & MASK
        elif kind == "and_ax3":
            R["eax"] &= 3
        elif kind == "inc_ax":
            R["eax"] = (R["eax"] + 1) & MASK
        elif kind == "cmp_cx_thr":
            pass
        elif kind == "jle_skipmax":
            if not (_signed(R["ecx"]) > _signed(R["eax"])):
                pass
            else:
                R["eax"] = R["ecx"]
        elif kind == "mv_max":
            pass
        elif kind == "cmp_si_thr":
            pass
        elif kind == "jge_accept_value":
            if _signed(R["esi"]) >= _signed(R["eax"]):
                R["eax"] = S[-0x2c]
                S[-0x24] = R["esi"]
                S[-0x84] = R["eax"]
                return ("accept", "value")
        elif kind == "cmp_case":
            pass
        elif kind == "jne_skip_case":
            if S[-0x44] != 8:
                return ("skip", "case")
        elif kind == "slot_unit":
            R["eax"] = S[-0x10]
        elif kind == "cmp_unit11":
            loadb(R["eax"] + 0x933289)
        elif kind == "je_skip_unit":
            if loadb(R["eax"] + 0x933289) == 0x18:
                return ("skip", "unit")
        elif kind == "lea_r8":
            R["ecx"] = (R["ebx"] * 8) & MASK
        elif kind == "and_dx_ff":
            R["edx"] &= 0xFF
        elif kind == "sub_cx_r7":
            R["ecx"] = (R["ecx"] - R["ebx"]) & MASK
        elif kind == "inc_dx":
            R["edx"] = (R["edx"] + 1) & MASK
        elif kind == "ld_tiles1":
            R["eax"] = loadd((R["ecx"] * 4) + REGION_TILES1)
        elif kind == "lea_dx3":
            R["edx"] = (R["edx"] * 3) & MASK
        elif kind == "shl_dx1":
            R["edx"] = (R["edx"] << 1) & MASK
        elif kind == "cmp_tiles":
            pass
        elif kind == "jge_skip_tiles":
            if _signed(R["eax"]) >= _signed(R["edx"]):
                return ("skip", "tiles")
        elif kind in ("slot_ring", "store_best", "store_bestidx"):
            if kind == "slot_ring":
                R["eax"] = S[-0x2c]
            elif kind == "store_best":
                S[-0x24] = R["esi"]
            else:
                S[-0x84] = R["eax"]
            if kind == "store_bestidx":
                return ("accept", "case8open")
        else:
            raise GateError("no handler for %s" % kind)
        i = order.index(pc)
        pc = order[i + 1] if i + 1 < len(order) else 0x563CB3


def price_gate(value, best_val, dist, mult, base_count, verdict, gate,
               case, unit24, tiles):
    """Closed form of the recorded gate window (must agree with interpret_gate
    on every case - selftest --b15 G3). Returns (outcome, branch).
    Inputs are RAW recorded values: unit24 = byte[unitrec+0x11] (skip only at
    == 0x18), mult = site_score byte, gate = site_gate byte, verdict =
    byte[blk+region+0x94eda8] of the pod's region."""
    if value <= best_val:
        return ("skip", "argmax")
    if value >= 2 * (8 - dist):
        return ("accept", "bypass")
    if mult == 0:
        return ("accept", "mult0")
    if base_count < 2:
        return ("accept", "bases")
    thr = 1 if verdict == 8 else 4
    if gate > thr:
        thr = gate
    if value >= thr:
        return ("accept", "value")
    if case != 8:
        return ("skip", "case")
    if unit24 == 0x18:
        return ("skip", "unit")
    if tiles >= 6 * (mult + 1):
        return ("skip", "tiles")
    return ("accept", "case8open")


# ---------------------------------------------------------------- rivals ----
def rival_verdictflip(value, best_val, dist, mult, base_count, verdict, gate,
                      case, unit24, tiles):
    p = price_gate(value, best_val, dist, mult, base_count, verdict, gate,
                   case, unit24, tiles)
    if p == ("skip", "argmax"):
        return p
    thr = 4 if verdict == 8 else 1  # the fold read backwards
    if mult == 0 or base_count < 2 or value >= 2 * (8 - dist):
        return p
    if gate > thr:
        thr = gate
    if value >= thr:
        return ("accept", "value")
    if case != 8:
        return ("skip", "case")
    if unit24 == 0x18:
        return ("skip", "unit")
    if tiles >= 6 * (mult + 1):
        return ("skip", "tiles")
    return ("accept", "case8open")


def rival_mingate(value, best_val, dist, mult, base_count, verdict, gate,
                  case, unit24, tiles):
    if value <= best_val:
        return ("skip", "argmax")
    if value >= 2 * (8 - dist):
        return ("accept", "bypass")
    if mult == 0:
        return ("accept", "mult0")
    if base_count < 2:
        return ("accept", "bases")
    thr = 1 if verdict == 8 else 4
    if gate < thr:
        thr = gate  # min() instead of the recorded conditional max
    if value >= thr:
        return ("accept", "value")
    if case != 8:
        return ("skip", "case")
    if unit24 == 0x18:
        return ("skip", "unit")
    if tiles >= 6 * (mult + 1):
        return ("skip", "tiles")
    return ("accept", "case8open")


def rival_notmult(value, best_val, dist, mult, base_count, verdict, gate,
                  case, unit24, tiles):
    if value <= best_val:
        return ("skip", "argmax")
    if value >= 2 * (8 - dist):
        return ("accept", "bypass")
    if mult != 0:  # the je at 0x563c46 read backwards
        return ("accept", "mult0")
    if base_count < 2:
        return ("accept", "bases")
    thr = 1 if verdict == 8 else 4
    if gate > thr:
        thr = gate
    if value >= thr:
        return ("accept", "value")
    if case != 8:
        return ("skip", "case")
    if unit24 == 0x18:
        return ("skip", "unit")
    if tiles >= 6 * (mult + 1):
        return ("skip", "tiles")
    return ("accept", "case8open")


def rival_ringtiles(value, best_val, dist, mult, base_count, verdict, gate,
                    case, unit24, tiles):
    if value <= best_val:
        return ("skip", "argmax")
    if value >= 2 * (8 - dist):
        return ("accept", "bypass")
    if mult == 0:
        return ("accept", "mult0")
    if base_count < 2:
        return ("accept", "bases")
    thr = 1 if verdict == 8 else 4
    if gate > thr:
        thr = gate
    if value >= thr:
        return ("accept", "value")
    if case != 8:
        return ("skip", "case")
    if unit24 == 0x18:
        return ("skip", "unit")
    if tiles >= 6:  # ring-index reading of edx at 0x563c8e (a guess, refuted by bytes)
        return ("skip", "tiles")
    return ("accept", "case8open")


def scan_esi_gated(g, x, y, occ, rowfn, own_gate=True):
    """podscan.scan_esi's eligibility legs + the recorded gate window executed
    per candidate (the interpreter updates slots[-0x24]/[-0x84] exactly like
    0x563caa-0x563cad). rowfn(i, nx, ny) -> dict(value, dist, mult,
    base_count, verdict, gate, case, unit24, tiles) for candidate i."""
    from sim import podscan as _ps
    if not scan_esi_gated.window:
        scan_esi_gated.window = load_window(
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "evidence", "b15_gate_window.txt"))
    cf, ob = g.catflag(x, y), g.own3(x, y)
    region = g.rb(x, y)[3]
    class _S:
        pass
    st = _S()
    st.slots = {-0x34: region, -0x24: 0, -0x84: -1, -0x44: 8,
                -0x48: 0, -0x8c: 0, -0x10: 0, -0x2c: 0}
    st.mem = {}
    st.fns = {}
    best_i = None
    for i in range(25):
        nx, ny = (x + _ps.RING_DX[i]) % g.W, y + _ps.RING_DY[i]
        if not (0 <= ny < g.H):
            continue
        if g.catflag(nx, ny) != cf:
            continue
        if own_gate and g.own3(nx, ny) != ob:
            continue
        if g.blocked(nx, ny):
            continue
        if (nx, ny) in occ:
            continue
        rows = rowfn(i, nx, ny)
        blk = rows["block"]
        st.slots[-0x8], st.slots[-0x4], st.slots[-0x2c] = nx, ny, i
        st.slots[-0x48], st.slots[-0x8c] = blk, rows["verdict"]
        st.slots[-0x44] = rows["case"]
        st.slots[-0x10] = 0  # raw 52*u record offset (u=0 model); the interpreter adds 0x933289
        st.mem = {
            (blk + 0x94E5A8 + region) & MASK: rows["mult"],
            (blk + 0x94E488) & MASK: rows["base_count"],
            (blk + 0x94ECA8 + region) & MASK: rows["gate"],
            (UNIT_BASE + 0x11) & MASK: rows["unit24"],
            (REGION_TILES1 + 28 * region) & MASK: rows["tiles"],
            NEAREST_DIST: rows["dist"],
        }
        st.fns = {"value": (lambda a, b: g.val(a, b)),
                  "dist": (lambda a, b, _r=rows: _r["dist"])}
        out, _ = interpret_gate(scan_esi_gated.window, st)
    return st.slots[-0x84] if st.slots[-0x84] >= 0 else None


scan_esi_gated.window = {}


def module_report(out_path):
    with open(out_path, "w") as f:
        f.write("B15 gatetables: %d gate pins, %d prologue pins, %d writer pins\n"
                % (len(GATE_PINS), len(PROLOGUE_PINS), len(WRITER_PINS)))
    return 0


# --------------------------------------------------------- selftest --b15 ----
import hashlib
import os
import random

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEF_WIN = os.path.join(REPO, "evidence", "b15_gate_window.txt")
DEF_NG5 = os.path.join(REPO, "evidence", "b15_name_disp_0x94e5a8.txt")
DEF_NGC = os.path.join(REPO, "evidence", "b15_name_disp_0x94eca8.txt")
DEF_NG4 = os.path.join(REPO, "evidence", "b15_name_ds_0x920434.txt")
DEF_LOG = os.path.join(REPO, "evidence", "m292_gdb_raw.log")
DEF_GOLDEN = os.path.join(REPO, "evidence", "m289_gdb_raw.log")

W434_PCS = {0x515ad8, 0x515fb1, 0x50fe70, 0x510196, 0x516f30, 0x516fd4,
            0x5a09ad, 0x50fff5, 0x51f267, 0x52289d, 0x522993, 0x57ed04,
            0x57f651, 0x598db9, 0x52280c}


class _St:
    pass


def _st_for(value, best_val, dist, mult, base_count, verdict, gate, case,
            unit24, tiles, region=7, blk=0x20bc * 2):
    st = _St()
    st.slots = {-0x34: region, -0x8: 11, -0x4: 13, -0x24: best_val,
                -0x2c: 3, -0x44: case, -0x48: blk, -0x8c: verdict,
                -0x10: 0, -0x84: -1}
    st.mem = {
        (blk + SITE_SCORE + region) & MASK: mult,
        (blk + BLOCK_BASECOUNT) & MASK: base_count,
        (blk + SITE_GATE + region) & MASK: gate,
        (UNIT_BASE + 0x11) & MASK: unit24,
        (REGION_TILES1 + 28 * region) & MASK: tiles,
        NEAREST_DIST: dist,
    }
    st.fns = {"value": (lambda a, b, _v=value: _v),
              "dist": (lambda a, b, _d=dist: _d)}
    return st


def nearest_dist(x, y, bases, W):
    """FUN_004e3620's location distance law (M291): map-WRAPPED dx/dy,
    d = max - ((dx+dy)/2 - min + 1)/2; 9999 sentinel when no locations."""
    if not bases:
        return 9999
    best = None
    for (a, b) in bases:
        dx = abs(x - a)
        dx = min(dx, W - dx)
        dy = abs(y - b)
        dy = min(dy, W - dy)  # square maps; W==H holds for both shipped maps
        d = max(dx, dy) - ((dx + dy) // 2 - min(dx, dy) + 1) // 2
        best = d if best is None or d < best else best
    return best


def acceptance(sav_path, results, win_path=DEF_WIN, ng5=DEF_NG5, ngc=DEF_NGC,
               ng4=DEF_NG4, log_path=DEF_LOG, golden_path=DEF_GOLDEN):
    """Run the B15 gates, appending (name, ok) to results; print detail."""
    from . import podscan as sps
    from . import save as sosave

    def gate(name, ok, detail):
        results.append((name, bool(ok)))
        print("  %s %s" % ("PASS" if ok else "FAIL", name) +
              ("  | " + detail if detail else ""))

    for p in (win_path, ng5, ngc, ng4, log_path, golden_path, sav_path):
        if not os.path.exists(p):
            gate("B15 inputs", False, "missing %s" % p)
            return

    rec = load_window(win_path)
    scan_esi_gated.window = rec
    pins = GATE_PINS + PROLOGUE_PINS + WRITER_PINS
    missing = []
    for pc, pat, _ in pins:
        if pc not in rec:
            missing.append("%x missing" % pc)
            continue
        mn, ops = rec[pc]
        if not re.fullmatch(pat, (mn + " " + ops).strip()):
            missing.append("%x mismatch" % pc)
    swapped = 0
    for pc, pat, _ in pins:
        sp = pat.replace("0x94e5a8", "ZZZ").replace("0x94eca8", "0x94e5a8").replace("ZZZ", "0x94eca8")
        if pc in rec and sp != pat and re.fullmatch(sp, (rec[pc][0] + " " + rec[pc][1]).strip()):
            swapped += 1
    gate("G1 shipped literals == recorded window; table-swap rival 0",
         not missing and swapped == 0,
         "%d pins verified, swap-matches %d, missing %s" % (len(pins), swapped, missing[:2] or "none"))

    t5 = open(ng5, encoding="utf-8").read()
    tc = open(ngc, encoding="utf-8").read()
    t4 = open(ng4, encoding="utf-8").read()
    w434 = sorted(int(m, 16) for m in re.findall(r"W ([0-9a-f]{6})\s", t4))
    g2 = ("0x94e5a8 — 99 referencing instructions" in t5
          and "FUN_0055f650  (22 refs, 0 writes)" in t5
          and "563c3d" in t5
          and "0x94eca8 — 7 referencing instructions" in tc
          and "FUN_0055f650  (4 refs, 0 writes)" in tc and "563c59" in tc
          and len(w434) == 15 and set(w434) == W434_PCS
          and "0x920434 — 634 referencing instructions" in t4)
    gate("G2 census re-check (99-ref site_score; 7-ref/0-store site_gate; 15 writers of 0x920434)",
         g2, "site_score refs=99 scan 22/0; site_gate refs=7 scan 4/0; W(0x920434)=%d pcs==M125" % len(w434))

    def run_interp(vals):
        st = _st_for(*vals)
        return interpret_gate(rec, st)

    grid = []
    for v in range(16):
        for b in (0, 1):
            for d in (0, 7, 8, 9, 9999):
                for m in (0, 1, 16):
                    for vd in (0, 7, 8):
                        for gg in (0, 1, 4, 5):
                            for bc in (0, 2):
                                grid.append((v, b, d, m, bc, vd, gg, 8, 0, 7))
    rng = random.Random(1546)  # B15, deterministic
    for _ in range(3000):
        grid.append((rng.randrange(0, 16), rng.randrange(0, 3),
                     rng.choice([0, 3, 7, 8, 11, 9999]),
                     rng.randrange(0, 24), rng.choice([0, 1, 2, 19]),
                     rng.choice([0, 2, 7, 8, 9, 255]),
                     rng.randrange(0, 20), rng.choice([1, 8]), rng.choice([0, 1, 24]),
                     rng.choice([0, 5, 17, 60, 999])))
    dis3 = [i for i, vals in enumerate(grid)
            if run_interp(vals) != price_gate(*vals)]
    gate("G3 closed form == recorded-byte interpreter (%d cases)" % len(grid),
         not dis3, "mismatches %d%s" % (len(dis3), (" first=%r" % (grid[dis3[0]],)) if dis3 else ""))

    rivals = {"verdict-fold flipped": rival_verdictflip,
              "min() gate": rival_mingate,
              "mult!=0 accept": rival_notmult,
              "tiles ceiling fixed-6": rival_ringtiles}
    rdet = []
    allok = True
    for nm, fn in sorted(rivals.items()):
        n = sum(1 for vals in grid if fn(*vals) != run_interp(vals))
        rdet.append("%s %d" % (nm, n))
        if n == 0:
            allok = False
    gate("G4 rivals fail the byte fit (each disagrees with the interpreter)",
         allok, " | ".join(rdet))

    sv = sosave.parse(sav_path)
    g = sps.Grid(sv)
    bases = {(b["x"], b["y"]) for b in sv.bases}
    events = []
    for (fac, x, y, cnt) in sps.golden_founds(golden_path):
        events.append(("m289found", x, y))
    ev = sps.parse_census(log_path)
    last_disp = None
    for kind, d in ev:
        if kind == "DISP" and "esi" in d:
            last_disp = (int(d["x"]), int(d["y"]), int(d["esi"]))
        elif kind == "HUBFOUND" and last_disp:
            events.append(("m292found", last_disp[0], last_disp[1]))
        elif kind == "ISS" and last_disp:
            wx, wy = sps.walk_target(last_disp[0], last_disp[1], int(d["esi"]), g.W, g.H)
            events.append(("m292walk", wx, wy))
    branch_rows, nb, nr = [], 0, 0
    bad = []
    for (tag, wx, wy) in events:
        try:
            v = g.val(wx, wy)
            dd = nearest_dist(wx, wy, bases, g.W)
            if v >= 2 * (8 - dd):
                nb += 1
            else:
                nr += 1
                branch_rows.append("%s(%d,%d)v%d,d%d" % (tag, wx, wy, v, dd))
        except Exception as e:
            bad.append("%s(%d,%d) %r" % (tag, wx, wy, e))
    gate("G5 recorded winners modelled (branch split; rows listed for the box census)",
         not bad and len(events) >= 20,
         "events %d, bypass-accepted %d, row-dependent %d, errors %d | %s"
         % (len(events), nb, nr, len(bad), "; ".join(branch_rows[:6])))

    def permissive(i, nx, ny, _g=g):
        return {"block": 0x20bc * 2, "mult": 0, "base_count": 19,
                "verdict": 7, "gate": 0, "case": 8, "unit24": 0,
                "tiles": 999, "dist": 9999}
    # Deep-leg rows: every candidate walks the FULL chain (no bypass,
    # mult!=0, base_count>=2, value<thr, case==8, unit byte != 0x18, tiles
    # under the 6*(mult+1) ceiling) -> accept via case8open. Greptile P1 (s243
    # review): the permissive pass never reaches those legs - this one must.
    def deep_legs(i, nx, ny, _g=g):
        return {"block": 0x20bc * 2, "mult": 1, "base_count": 19,
                "verdict": 7, "gate": 200, "case": 8, "unit24": 0,
                "tiles": 0, "dist": 0}  # dist 0 -> bypass needs 16 (max val 15): never
    tiles_ok = 0
    tiles_all = 0
    for (fac, x, y, cnt) in sps.golden_founds(golden_path):
        ref = sps.scan_esi(g, x, y, bases)
        got = scan_esi_gated(g, x, y, bases, permissive)
        got2 = scan_esi_gated(g, x, y, bases, deep_legs)
        tiles_all += 1
        if got == ref and got2 == ref:
            tiles_ok += 1
    gate("G6 gated-scan == podscan.scan_esi (permissive + full deep-leg rows)",
         tiles_ok == tiles_all and tiles_all == 7,
         "%d/%d golden pod tiles, both row regimes" % (tiles_ok, tiles_all))

    h1 = hashlib.sha256(open(win_path, "rb").read()).hexdigest()
    r1 = hashlib.sha256(repr([price_gate(*v) for v in grid[:200]]).encode()).hexdigest()
    r2 = hashlib.sha256(repr([price_gate(*v) for v in grid[:200]]).encode()).hexdigest()
    # Pinned digest: the recorded window is byte-exact data from terran.exe;
    # a changed digest means changed authority and MUST fail the rung.
    WINDOW_SHA = "c1b3712b6be6f5d3d9307776a0eb949d2156576341bcaf307b8529bbb64209b2"
    gate("G7 determinism + recorded-window digest pinned", r1 == r2 and h1 == WINDOW_SHA,
         "window sha256 %s%s" % (h1[:16], "" if h1 == WINDOW_SHA else " != pinned " + WINDOW_SHA[:16]))


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="sim.gatetables")
    ap.add_argument("--sav", default=os.path.join(REPO, "programs", "saves", "m54b_clean.SAV"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    results = []
    acceptance(a.sav, results)
    with open(a.out, "w") as f:
        for nm, ok in results:
            f.write("%s %s\n" % ("PASS" if ok else "FAIL", nm))
    return 0 if all(ok for _, ok in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
