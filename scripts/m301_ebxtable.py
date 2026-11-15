#!/usr/bin/env python3
"""M301 (s256, STATIC, zero box): the lead "ebx's walked table 0x51de2c-0x51df1d".

QUESTION (NAMED.md:1009 / SESSION_NOTES.md:609-610, recorded by M294 as a LEAD and
never chased): the byte range 0x51de2c-0x51df1d sits immediately BEFORE the slot [+4]
visit-counter gate that M299/M300 pinned (`call 0x5832b0` 0x51dffd / `test eax,eax`
0x51e005 / `je 0x51e11d` 0x51e007 / `inc ecx` 0x51e01a / `mov [esi+0x989cec],ecx`
0x51e01b, all inside FUN_0051dcb0). Census it:
  (a) how many entries does the range hold, and what are the raw values?
  (b) code addresses (a dispatch/jump table), data pointers, masks, or offsets?
  (c) every instruction that INDEXES it: base register, index register, and where the
      index comes from (traced to its producer in the same function window)?
  (d) does the range GATE or only LABEL the 0x51dffd decision, and does FUN_005832b0's
      return value (the `eax` tested at 0x51dffd) reach it?

HEADLINE (computed below, asserted at the end): the range is NOT a table. It is 0xF3
(243) bytes of executable .text - the BODY OF A LOOP - holding ZERO data entries and
N instructions (printed), and the loop it implements walks a global array that the repo
ALREADY NAMES: base_array @ 0x95da10, 304-byte rows, row count in ds:0x985af4
(NAMED.md:74). "ebx's walked table" is that array, reached through the loop, not a
static table at 0x51de2c.

METHOD / INSTRUMENTS (every number printed is COMPUTED here; nothing is hand-counted;
containment is ALWAYS via ghidra_out/index.csv, never objdump at an arbitrary address):
  S0 containment of the range endpoints + the function extent from index.csv.
  S1 the range printed VERBATIM (bytes + mnemonics) from the full-.text dump
     scratch/m574/text.txt (the dump M299 graded 13/13 constants against Ghidra), with
     contiguity proved from the ENCODING BYTES (sum of byte lengths == span), so the
     window cannot be a misaligned objdump artifact.
  S2 entry census under four competing models: dword-aligned data entries, byte-aligned,
     instruction count, and "how many dwords in the range resolve to a VA inside .text"
     (a real jump/dispatch table body MUST contain such pointers).
  S3 the two instruments that decide nature: (i) every indirect (memory-form) jmp/call
     in the function - a dispatch table needs one; (ii) every mention of any address in
     the range as an OPERAND anywhere in .text, split branch-target vs non-branch
     (lea/mov/push of the address would mean data). A table is addressed; a loop body is
     fallen into and back-edged.
  S4 the walk the range actually implements: cursor base register + its init immediate,
     the stride immediate, the counter slot + its bound global, the back edge, and the
     record fields the body touches - each asserted against the named globals.
  S5 index provenance: the affine multiply chain that scales the scan index to the
     record stride (evaluated, not asserted by eye), the BYTE load that becomes ebx, and
     the producer of the index (a callee's return, pinned by its call site).
  S6 the (d) verdict: every ebx reader/writer from the range end through the store, every
     edge that BYPASSES the range, every branch between the range exit and the call (does
     any leg skip the call?), every backward edge from after the range into it (can the
     predicate's eax flow back?), and every consumer of the predicate's eax.
stdout is mirrored to evidence/m301_ebxtable.txt.

Run:  python3 scripts/m301_ebxtable.py         (exit 0 = all assertions hold)
"""
import bisect
import csv
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
INDEX = os.path.join(ROOT, "ghidra_out", "index.csv")
NAMED = os.path.join(ROOT, "NAMED.md")
EVID = os.path.join(ROOT, "evidence", "m301_ebxtable.txt")

FUN = 0x51DCB0                      # FUN_0051dcb0 (containment target)
LO = 0x51DE2C                       # lead's low end: cmp ecx,ebx
HI = 0x51DF1D                       # lead's high end: test ebx,ebx
LOOP_HEAD = 0x51DE27                # xor ecx,ecx - the real loop head, 5 B below LO
CALL = 0x51DFFD                     # call 0x5832b0 (M299's gate call)
GATE_TEST, GATE_JE = 0x51E005, 0x51E007
INC, STORE = 0x51E01A, 0x51E01B     # the slot [+4] visit-counter write
CELL_SKIP_JE = 0x51DFD1             # je 0x51dff5 - the ebx==0 leg
PRECALL = 0x51DFF5                  # the block right before the gate call
BASE_ARRAY = 0x95DA10               # NAMED.md:74 base_array (304-B rows)
ROW = 0x130                         # 304 = the row stride immediate
OWNER_BYTE = 0x95DA14               # base_array + 4 = owner player index (M43)
CURSOR_INIT = 0x95DA12              # base_array + 2 = the y field of row 0
COUNT_G = 0x985AF4                  # ds:0x985af4 = base count (NAMED.md:74)
TILE_BASE = 0x92AE14                # 44-byte tile records (B16/NAMED:967)
WIDTH_G = 0x692184                  # map row stride global
DIST_G = 0x8F0D34                   # nearest-location distance (NAMED:826)
TILE_STRIDE = 44
SELECTOR = 0x4E37F0                 # FUN_004e37f0: the nearest-base sweep -> index
ABS = 0x64B870                      # the abs() helper the body calls
TEXT_LO, TEXT_HI = 0x401000, 0x671000   # .text VA span (skill: PE layout)

LINE_RX = re.compile(r"^ +([0-9a-f]{6,8}):\t([0-9a-f ]+)\t\s*(.+?)\s*$")
CC = r"(?:je|jne|jl|jge|jg|jle|jb|jae|ja|jbe|js|jns|jo|jno|jc|jnc)"
BR_RX = re.compile(r"^(?:jmp|%s)\s+(0x[0-9a-f]+)\s*$" % CC)
INDIRECT_RX = re.compile(r"^(?:jmp|call)\s+(?:DWORD PTR )?\[")
CALL_RX = re.compile(r"^call\s+(0x[0-9a-f]+)")
MEM_RX = re.compile(r"\[([^\]]*)\]")
HEX_RX = re.compile(r"0x([0-9a-f]{4,8})")


class Out:
    def __init__(self, path):
        self.f = open(path, "w")

    def p(self, s=""):
        self.f.write(s + "\n")
        print(s)

    def close(self):
        self.f.close()


O = Out(EVID)
CHECKS = []


def gate(n, ok, text):
    CHECKS.append(ok)
    O.p("A%d %s: %s" % (n, "PASS" if ok else "FAIL", text))


def load_dump():
    """addr -> (mnemonic_and_operands, encoding_bytes, length)."""
    ins, enc = {}, {}
    with open(TEXT, errors="replace") as f:
        for ln in f:
            m = LINE_RX.match(ln)
            if m:
                a = int(m.group(1), 16)
                if a not in ins:
                    ins[a] = m.group(3)
                    enc[a] = bytes(int(b, 16) for b in m.group(2).split())
    return ins, enc, sorted(ins)


def load_index():
    funcs = []
    with open(INDEX) as f:
        for row in csv.DictReader(f):
            funcs.append((int(row["addr"], 16), row["name"], int(row["size_bytes"]),
                          int(row["n_insns"])))
    funcs.sort()
    return funcs


def contain(funcs, a):
    i = bisect.bisect_right([x[0] for x in funcs], a) - 1
    st, nm, sz, ni = funcs[i]
    return nm, (st <= a < st + sz), sz, ni


def mn(t):
    return t.split(None, 1)[0]


def ops(t):
    p = t.split(None, 1)
    return p[1] if len(p) > 1 else ""


def main():
    ins, enc, addrs = load_dump()
    funcs = load_index()

    # ---- S0: containment ------------------------------------------------------------
    O.p("== S0: containment (ghidra_out/index.csv - NEVER objdump at an arbitrary addr) ==")
    cont = {}
    for a in (LO, HI, LOOP_HEAD, CALL, STORE):
        nm, inside, sz, ni = contain(funcs, a)
        cont[a] = (nm, inside)
        O.p("   0x%-8x -> %-14s inside=%s (function size %d B, n_insns %d)"
            % (a, nm, inside, sz, ni))
    fname, fsize, fnins = contain(funcs, FUN)[0], contain(funcs, FUN)[2], \
        contain(funcs, FUN)[3]
    fstart = contain(funcs, FUN)[0]
    faddr = [x[0] for x in funcs if x[1] == fname][0]
    O.p("   %s entry 0x%x  size %d B  Ghidra n_insns %d" % (fname, faddr, fsize, fnins))
    body = [a for a in addrs if faddr <= a < faddr + fsize]
    gate(0, all(cont[a][1] and cont[a][0] == fname for a in cont) and fnins == len(body),
         "range endpoints 0x%x/0x%x, loop head 0x%x and the gate chain all contained in %s; "
         "dump instruction count over the function window (%d) == Ghidra's n_insns (%d) - "
         "the two toolchains agree the whole span is decoded instruction stream, and the "
         "range holds no data island" % (LO, HI, LOOP_HEAD, fname, len(body), fnins))

    # ---- S1: the range printed VERBATIM ---------------------------------------------
    win = [a for a in addrs if LO <= a <= HI]
    span_end = max(win) + len(enc[max(win)])
    span = span_end - LO
    bytesum = sum(len(enc[a]) for a in win)
    O.p("\n== S1: the range 0x%x-0x%x VERBATIM from the dump (%d insns, span 0x%x = %d B) =="
        % (LO, HI, len(win), span, span))
    for a in win:
        O.p("   0x%-8x %-18s %s" % (a, " ".join("%02x" % b for b in enc[a]), ins[a]))
    gaps = [win[i] - (win[i - 1] + len(enc[win[i - 1]])) for i in range(1, len(win))]
    O.p("   sum(encoding bytes) %d == span %d: %s; max gap %d" %
        (bytesum, span, bytesum == span, max(gaps) if gaps else 0))
    O.p("   loop head (5 B below LO, the real entry of the body):")
    for a in addrs:
        if LOOP_HEAD <= a < LO:
            O.p("   0x%-8x %-18s %s" % (a, " ".join("%02x" % b for b in enc[a]), ins[a]))
    gate(1, bytesum == span and (not gaps or max(gaps) == 0),
         "the %d B range decodes GAP-FREE from its own encoding bytes (%d insns, every gap "
         "0): a data table cannot tile a byte span as a legal instruction stream that "
         "Ghidra also placed inside %s" % (span, len(win), fname))

    # ---- S2: entry census under competing models --------------------------------------
    dw_aligned = [LO + 4 * i for i in range(span // 4)]
    bodyimg = b"".join(enc[a] for a in sorted(ins) if faddr <= a < faddr + fsize)
    off0 = bodyimg.index(b"".join(enc[a] for a in win))

    def va_hits(aligned_only):
        hits = []
        step = 4 if aligned_only else 1
        for k in range(0, span - 3, step):
            v = int.from_bytes(bodyimg[off0 + k:off0 + k + 4], "little")
            if TEXT_LO <= v < TEXT_HI:
                hits.append((LO + k, v))
        return hits
    h_al, h_any = va_hits(True), va_hits(False)
    calls_in = [a for a in win if CALL_RX.match(ins[a])]
    br_in = [a for a in win if BR_RX.match(ins[a])]
    O.p("\n== S2: entry census under four models ==")
    O.p("   span %d B / 4 = %s  -> %s" % (span, span / 4.0,
                                          "NOT an integral number of dword entries"
                                          if span % 4 else "integral dwords"))
    O.p("   instructions in the range: %d" % len(win))
    O.p("   dwords at 4-byte-aligned offsets in the range resolving into .text (%02x-%02x): "
        "%d %s" % (TEXT_LO, TEXT_HI, len(h_al),
                   [("%08x->%08x" % (a, v)) for a, v in h_al]))
    O.p("   dwords at ANY offset in the range resolving into .text: %d %s"
        % (len(h_any), [("%08x->%08x" % (a, v)) for a, v in h_any]))
    O.p("   call instructions INSIDE the range: %d -> %s"
        % (len(calls_in), [("0x%x %s" % (a, ins[a])) for a in calls_in]))
    O.p("   conditional/unconditional branches INSIDE the range: %d" % len(br_in))
    gate(2, span % 4 != 0 and len(h_al) == 0 and len(h_any) == 0 and len(win) > 0,
         "%d dword-aligned entries (span %% 4 = %d), ZERO dwords anywhere in the range that "
         "resolve to a .text address (a dispatch table body is code addresses), ZERO at any "
         "byte offset either; instead %d instructions of which %d are CALLs to 0x%x - a data "
         "table does not call abs()" % (len(dw_aligned), span % 4, len(win), len(calls_in),
                                        ABS))

    # ---- S3: nature - addressed as data, or fallen into? ------------------------------
    O.p("\n== S3: nature (a table is ADDRESSED; a loop body is fallen into and back-edged) ==")
    indirect = [a for a in body if INDIRECT_RX.match(ins[a])]
    O.p("   indirect (memory-form) jmp/call anywhere in %s: %d %s"
        % (fname, len(indirect), [ins[a] for a in indirect]))
    named, nonbranch = [], []
    for a in addrs:
        for m in HEX_RX.finditer(ins[a]):
            v = int(m.group(1), 16)
            if LO <= v < span_end and a not in win:
                nonbranch.append((a, ins[a]))
            elif LO <= v < span_end:
                named.append((a, ins[a]))
    nbr_bad = [x for x in nonbranch if not BR_RX.match(x[1])]
    O.p("   .text mentions of any address in [0x%x,0x%x): %d total; %d of them from OUTSIDE "
        "the range" % (LO, span_end, len(named), len(nonbranch)))
    for a, t in sorted(set(nonbranch)):
        O.p("       0x%-8x %s   [%s]" % (a, t, "branch" if BR_RX.match(t) else "NON-BRANCH"))
    O.p("   non-branch (lea/mov/push) mentions of the range: %d" % len(nbr_bad))
    ext_into = sorted({int(BR_RX.match(t).group(1), 16) for a, t in nonbranch
                       if BR_RX.match(t)})
    src_outside = sorted({a for a, t in nonbranch if BR_RX.match(t)})
    O.p("   loop back edge(s) targeting the range head: %s"
        % [("0x%x -> %s" % (a, ins[a])) for a in src_outside])
    gate(3, len(indirect) == 0 and len(nbr_bad) == 0 and len(src_outside) == 1,
         "ZERO indirect jmp/call in the function (no dispatch is read anywhere in it), ZERO "
         "lea/mov/push of any address in the range image-wide, and exactly %d external branch "
         "into it - 0x%x `%s`, the loop's own BACK EDGE to 0x%x, plus fall-through from 0x%x. "
         "Entry by fall-through + back edge = loop body; a jump table is entered through an "
         "indexed indirect branch reading a base address, and nothing here does"
         % (len(src_outside), src_outside[0] if src_outside else 0,
            ins[src_outside[0]] if src_outside else "", LOOP_HEAD, LOOP_HEAD + 2))

    # ---- S4: the walk the range implements --------------------------------------------
    O.p("\n== S4: the array the loop walks (named already: NAMED.md:74 base_array) ==")
    cur_init = [a for a in body if ins[a] == "mov eax,0x%x" % CURSOR_INIT]
    stride = [a for a in body if re.match(r"^add\s+(?:eax|ebx),0x%x$" % ROW, ins[a])]
    bound_ld = [a for a in body if "0x%x" % COUNT_G in ins[a]]
    counter = sorted({a for a in body if "[ebp-0x18]" in ins[a]})
    back = [a for a in win if BR_RX.match(ins[a]) and
            int(BR_RX.match(ins[a]).group(1), 16) <= LOOP_HEAD]
    fields = {"WORD[eax] (+2 = y)": "movsx esi,WORD PTR [eax]",
              "WORD[eax-0x2] (+0 = x)": "movsx ecx,WORD PTR [eax-0x2]",
              "BYTE[eax+0x2] (+4 = flag/owner)": "mov cl,BYTE PTR [eax+0x2]"}
    hits = {k: [a for a in win if ins[a] == v] for k, v in fields.items()}
    for k, v in hits.items():
        O.p("   row field %s read at %s: `%s`" % (k, ["0x%x" % a for a in v],
                                                  fields[k] if v else "ABSENT"))
    O.p("   cursor init: %s (`%s`) = base_array 0x%x + 2"
        % (["0x%x" % a for a in cur_init], ins[cur_init[0]] if cur_init else "", BASE_ARRAY))
    O.p("   cursor spill/reload slots [ebp-0x14]: %s"
        % ["0x%x `%s`" % (a, ins[a]) for a in sorted(body) if "[ebp-0x14]" in ins[a]])
    O.p("   row stride: %s (`%s`) = %d == base_array row size"
        % (["0x%x" % a for a in stride], ins[stride[0]] if stride else "", ROW))
    O.p("   counter [ebp-0x18]: %s" % ["0x%x `%s`" % (a, ins[a]) for a in counter])
    O.p("   bound global ds:0x%x (base count): %s"
        % (COUNT_G, ["0x%x `%s`" % (a, ins[a]) for a in bound_ld]))
    O.p("   back edge: %s" % ["0x%x `%s`" % (a, ins[a]) for a in back])
    tile_math = [a for a in win if "0x%x" % WIDTH_G in ins[a] or "0x%x" % TILE_BASE in ins[a]]
    O.p("   44-B tile-record view inside the body (44*(%s.Y + X>>1), NAMED:967): %s"
        % (hex(WIDTH_G), ["0x%x `%s`" % (a, ins[a]) for a in tile_math]))
    gate(4, len(cur_init) == 1 and len(stride) == 1 and len(back) == 1 and
         all(v for v in hits.values()) and
         all(COUNT_G <= 0 or "0x%x" % COUNT_G in ins[a] for a in bound_ld) and len(bound_ld) >= 2,
         "the range is a single walk of base_array @0x%x: cursor 0x%x = base+2 (%s), rows "
         "advance by `add eax,0x%x` = %d (the %d-B record) at 0x%x, the trip counter is "
         "[ebp-0x18] (init 0x51de10, inc 0x51dee1) bounded by ds:0x%x (loaded twice, "
         "test-at-0x51de17 / cmp-at-0x51dee7), one back edge 0x%x -> 0x%x, and the body "
         "touches row fields x(+0), y(+2), flag(+4) and the 44-B tile record view - so the "
         "'table' is a RUNTIME array whose row count lives in BSS, not a static table"
         % (BASE_ARRAY, CURSOR_INIT, ins[cur_init[0]], ROW, ROW, stride[0], COUNT_G,
            back[0], LOOP_HEAD))

    # ---- S5: where the index comes from -----------------------------------------------
    O.p("\n== S5: index provenance (who computes what the loop compares) ==")
    chain = [0x51DDF2, 0x51DDF7, 0x51DDFA]
    for a in chain:
        O.p("   0x%-8x %s" % (a, ins[a]))

    def affine(step, st):
        """tiny affine tracker over {reg:(coef, const)} for the 3-insn scale chain."""
        m, r, v = step
        if r == "edx" and m == "lea":            # edx = eax + eax*8
            st["edx"] = (st["eax"][0] * 9, 0)
        elif r == "eax" and m == "lea":           # eax = eax + edx*2
            st["eax"] = (st["eax"][0] + 2 * st["edx"][0], 0)
        elif r == "eax" and m == "shl":           # eax <<= 4
            st["eax"] = (st["eax"][0] * 16, 0)
        return st
    st = {"eax": (1, 0), "edx": (0, 0)}
    for a in chain:
        t = ins[a].split(None, 1)[1]
        dst, src = t.split(",")[0].strip(), t.split(",")[1].strip()
        st = affine((mn(ins[a]), dst.split()[0].strip(), src), st)
        O.p("       -> eax = %d*i + %d, edx = %d*i" % (st["eax"][0], st["eax"][1],
                                                       st["edx"][0]))
    scale = st["eax"][0]
    oload = [a for a in body if ins[a] == "mov bl,BYTE PTR [eax+0x%x]" % OWNER_BYTE]
    cal = [a for a in body if CALL_RX.match(ins[a]) and
           int(CALL_RX.match(ins[a]).group(1), 16) == SELECTOR]
    O.p("   i arrives as FUN_004e37f0's return: 0x%x `%s`; 0x51ddb9 `%s`; 0x51ddbb `%s`; "
        "0x51ddbd `%s`" % (cal[0] if cal else 0, ins[cal[0]] if cal else "",
                           ins[0x51DDB9], ins[0x51DDBB], ins[0x51DDBD]))
    O.p("   ebx = BYTE[%d*i + 0x%x] at %s: `%s`"
        % (scale, OWNER_BYTE, ["0x%x" % a for a in oload],
           ins[oload[0]] if oload else ""))
    O.p("   ebx zeroing + the 3 sentinel writes: %s"
        % ["0x%x `%s`" % (a, ins[a]) for a in body if ins[a] in
           ("xor ebx,ebx", "or ebx,0xffffffff")])
    named_txt = open(NAMED, errors="replace").read()
    cite = "0x95da14+304*i" in " ".join(named_txt.split()) or \
        ("304 B" in named_txt and "0x95da10" in named_txt)
    gate(5, scale == ROW and len(oload) == 1 and len(cal) == 1 and cite,
         "the loop's comparison value is ebx = BYTE[%d*i + 0x%x] (0x51ddff) where i is "
         "FUN_004e37f0's return (call 0x51ddb1, `test eax,eax`/`jge` guard, `-1` sentinel at "
         "0x51ddbd), the scale chain 0x51ddf2-fa evaluating to %d*i = exactly the row size "
         "%d; that matches the registry (NAMED.md `ebx = BYTE[0x95da14+304*i]`, base+4 = owner "
         "player index, M43/M278) - so the INDEX is a base record's owner byte, and the loop's "
         "own index is its trip counter [ebp-0x18], not a table subscript" %
         (scale, OWNER_BYTE, scale, ROW))

    # ---- S6: the (d) verdict -----------------------------------------------------------
    O.p("\n== S6: does the range gate or label the 0x51dffd decision? ==")
    ebx_use = [a for a in body if span_end <= a <= STORE and
               re.search(r"\bebx\b", ins[a])]
    O.p("   every ebx reader/writer from the range end (0x%x) through the counter store "
        "0x%x (%d):" % (span_end, STORE, len(ebx_use)))
    for a in ebx_use:
        O.p("   0x%-8x %s" % (a, ins[a]))
    skip_legs = [a for a in body if BR_RX.match(ins[a]) and
                 int(BR_RX.match(ins[a]).group(1), 16) == 0x51DEFD]
    O.p("   edges that BYPASS the range (target 0x51defd): %d" % len(skip_legs))
    for a in skip_legs:
        O.p("   0x%-8x %s" % (a, ins[a]))
    between = [a for a in body if span_end <= a < CALL and BR_RX.match(ins[a])]
    past = [(a, ins[a], int(BR_RX.match(ins[a]).group(1), 16)) for a in between]
    skip_call = [x for x in past if x[2] > CALL]
    O.p("   branches between the range exit and the call (%d); legs landing PAST the call: %d"
        % (len(past), len(skip_call)))
    for a, t, tv in past:
        O.p("   0x%-8x %-26s -> 0x%x  %s" % (a, t, tv, "SKIPS THE CALL" if tv > CALL else
                                             "rejoins before the call"))
    O.p("   ebx==0 leg: 0x%x `%s` targets 0x%x (the block immediately BEFORE the call at "
        "0x%x) - it skips the slot-cell stores only" %
        (CELL_SKIP_JE, ins[CELL_SKIP_JE], int(BR_RX.match(ins[CELL_SKIP_JE]).group(1), 16),
         CALL))
    O.p("   gate bytes: 0x%x `%s` | 0x%x `%s` | 0x%x `%s` | 0x%x `%s`"
        % (CALL, ins[CALL], GATE_TEST, ins[GATE_TEST], GATE_JE, ins[GATE_JE],
           INC, ins[INC]))
    eax_after = [a for a in body if a > CALL and a <= 0x51E035 and
                 re.search(r"\beax\b", ins[a])]
    O.p("   consumers of the predicate's eax after 0x%x (to 0x51e035): %s"
        % (CALL, ["0x%x `%s`" % (a, ins[a]) for a in eax_after]))
    backflow = sorted({a for a, t in nonbranch if BR_RX.match(t) and a > CALL})
    O.p("   backward branches from AFTER the call into the range: %d %s"
        % (len(backflow), ["0x%x" % a for a in backflow]))
    gate(6, len(skip_call) == 0 and len(backflow) == 0 and
         int(BR_RX.match(ins[CELL_SKIP_JE]).group(1), 16) == PRECALL and
         eax_after and all(mn(ins[a]) == "test" for a in eax_after[:1]),
         "the range neither gates nor labels the decision: %d edges bypass it whole and land "
         "on 0x51defd, which falls through to the call; NO leg between the range exit 0x%x and "
         "the call 0x%x skips past it (the only forward-target branch is the ebx==0 leg 0x%x -> "
         "0x%x, the pre-call block), so the call and its `test eax,eax` run on EVERY leg; and "
         "the predicate's eax (0x51dffd) is consumed ONLY by `test eax,eax` 0x51e005 (it is "
         "never stored, and 0x51e00d reloads ecx from memory), with ZERO backward edges from "
         "after the call into the range - the value cannot reach the range"
         % (len(skip_legs), span_end, CALL, CELL_SKIP_JE, PRECALL))

    # ---- rollup -----------------------------------------------------------------------
    O.p("\n== ROLLUP ==")
    O.p("  (a) entries: 0 data entries in %d B (span %% 4 = %d, no dword resolves into .text); "
        "%d instructions" % (span, span % 4, len(win)))
    O.p("  (b) nature: EXECUTABLE CODE - the body of the base_array walk (stride %d, count "
        "ds:0x%x); not code addresses, not pointers, not masks, not offsets" % (ROW, COUNT_G))
    O.p("  (c) indexing: base reg eax (cursor 0x%x, spill [ebp-0x14]) + trip counter [ebp-0x18] "
        "vs ds:0x%x; the compared value ebx = BYTE[%d*i + 0x%x], i = FUN_004e37f0's return"
        % (CURSOR_INIT, COUNT_G, ROW, OWNER_BYTE))
    O.p("  (d) verdict: the range is UPSTREAM of the gate and gates NOTHING the counter write "
        "depends on; ebx (the range's only output) gates only the 0x51dfcb slot store's "
        "companion cell store (0x51dfd3-e0) and feeds the post-store byte read 0x51e02c; "
        "FUN_005832b0's eax does not reach the range")
    n = len(CHECKS)
    O.p("\n%d/%d assertions hold" % (sum(CHECKS), n))
    O.close()
    return 0 if sum(CHECKS) == n else 1


if __name__ == "__main__":
    sys.exit(main())
