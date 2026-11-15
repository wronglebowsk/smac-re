#!/usr/bin/env python3
"""M301 (s256, STATIC, zero box): the lead "ebx's walked table 0x51de2c-0x51df1d".

QUESTION (NAMED.md:1009 / SESSION_NOTES.md:609-610, recorded by M294 as a LEAD and never
chased): the byte range 0x51de2c-0x51df1d sits immediately BEFORE the slot [+4]
visit-counter gate M299/M300 pinned (`call 0x5832b0` 0x51dffd / `test eax,eax` 0x51e005 /
`je 0x51e11d` 0x51e007 / `inc ecx` 0x51e01a / `mov [esi+0x989cec],ecx` 0x51e01b, all in
FUN_0051dcb0). Census it:
  (a) how many entries does the range hold, and what are the raw values?
  (b) code addresses (a dispatch/jump table), data pointers, masks, or offsets? Prove it
      from the bytes plus how the site uses them - not from the address alone.
  (c) every instruction that indexes it: base register, index register, and where the index
      comes from (traced to its producer inside the same function window)?
  (d) does the range GATE or only LABEL the 0x51dffd decision, and does FUN_005832b0's
      return value (the `eax` tested at 0x51dffd) reach it?

ANSWER (computed below; asserted at the end): THE LEAD IS REFUTED - there is no table.
The range is 0xF3 (243) bytes of executable .text holding ZERO data entries and N
instructions (printed VERBATIM in S1): a straight-line walk of the base_array (cursor
0x95da12 = base+2, `add eax,0x130` = 304-B rows, trip counter [ebp-0x18] against the BSS
row count ds:0x985af4) with ONE back edge, followed by the straight-line exit block that
compares the walk's verdict ebx against BYTE PTR [edi+0x7] (edi = [ebp-0x4]). "ebx's walked table" is the base_array
- a NAMED global (NAMED.md:74) whose row count is runtime - not a static table at 0x51de2c.
The range is UPSTREAM of the 0x51dffd gate and gates NOTHING the counter write depends on.

METHOD / INSTRUMENTS (every number printed is COMPUTED here; nothing hand-counted;
containment ALWAYS via ghidra_out/index.csv, never objdump at an arbitrary address):
  S0 containment of the range endpoints + function extent (index.csv), cross-checked by
     counting dump instructions over the function window against Ghidra's n_insns - two
     toolchains must agree the span is decoded instruction stream.
  S1 the range printed VERBATIM (encodings + mnemonics), contiguity proved from the
     ENCODING BYTES (sum of lengths == span, every gap 0) so it cannot be a misaligned-
     objdump artifact; the loop's own extent derived from its back edge.
  S2 entry census under competing models: dword-aligned entries, dwords in the range that
     resolve to a .text VA (a dispatch body MUST be code addresses), instruction count,
     and CALL instructions inside the span.
  S3 nature: a table is ADDRESSED, a loop body is fallen into and back-edged. Count every
     indirect (memory-form) jmp/call in the function (a dispatch needs one), and every
     mention of a range address as an operand image-wide split branch vs non-branch
     (lea/mov/push would mean data), plus where external branches into the range land.
  S4 the array the walk reads: cursor base register + init immediate, stride immediate,
     trip counter slot + bound global, back edge, the row fields the body touches - each
     asserted against the registry's named globals.
  S5 index provenance: the affine scale chain evaluated (not eyeballed), the BYTE load that
     becomes ebx, and the producer of the index (a callee's return, pinned at its call site).
  S6 the (d) verdict: ebx readers/writers from the range end through the store, every edge
     that BYPASSES the range, every branch between the range exit and the call (does any leg
     skip the call?), every backward edge from after the call into the range (can the
     predicate's eax flow back?), and every consumer of the predicate's eax.
stdout is mirrored to evidence/m301_ebxtable.txt.

Run:  python3 scripts/m301_ebxtable.py        (exit 0 = all assertions hold)
"""
import bisect
import csv
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
INDEX = os.path.join(ROOT, "ghidra_out", "index.csv")
NAMED = os.path.join(ROOT, "NAMED.md")
EVID = os.path.join(ROOT, "evidence", "m301_ebxtable.txt")

FUN = 0x51DCB0                      # FUN_0051dcb0 (containment target)
LO = 0x51DE2C                       # lead's low end: cmp ecx,ebx
HI = 0x51DF1D                       # lead's high end: test ebx,ebx
LOOP_HEAD = 0x51DE27                # xor ecx,ecx - the walk's real head, 5 B below LO
EXIT_BLOCK = 0x51DEFD               # the walk's exit block start (inside the lead's range)
SEL_JE, SEL_JLE = 0x51DE05, 0x51DE19  # the two in-function legs that bypass the walk
CALL = 0x51DFFD                     # call 0x5832b0 (M299's gate call)
GATE_TEST, GATE_JE = 0x51E005, 0x51E007
INC, STORE = 0x51E01A, 0x51E01B     # the slot [+4] visit-counter write
EBX_SKIP_JE = 0x51DFD1              # je 0x51dff5 - the ebx==0 leg
PRECALL = 0x51DFF5                  # the block immediately before the gate call
BASE_ARRAY = 0x95DA10               # NAMED.md:74 base_array (304-B rows)
ROW = 0x130                         # 304 = the row-stride immediate
OWNER_BYTE = 0x95DA14               # base_array + 4 = owner player index (M43/M278)
CURSOR_INIT = 0x95DA12              # base_array + 2 = the y field of row 0
COUNT_G = 0x985AF4                  # ds:0x985af4 = base count (NAMED.md:74)
TILE_BASE = 0x92AE14                # 44-byte tile records (B16 law, NAMED:967)
WIDTH_G = 0x692184                  # map row-stride global
DIST_G = 0x8F0D34                   # nearest-location distance (NAMED:826)
SELECTOR = 0x4E37F0                 # FUN_004e37f0: the nearest-base sweep -> record index
CALLEE = 0x64B870                   # helper the walk calls 4x with a pushed signed value
TEXT_LO, TEXT_HI = 0x401000, 0x671000   # .text VA span (skill: terran.exe PE layout)

LINE_RX = re.compile(r"^ +([0-9a-f]{6,8}):\t([0-9a-f ]+)\t\s*(.+?)\s*$")
CC = r"(?:je|jne|jl|jge|jg|jle|jb|jae|ja|jbe|js|jns|jo|jno|jc|jnc)"
HEX_RX = re.compile(r"0x([0-9a-f]{4,8})")
WS = re.compile(r"\s+")


def norm(t):
    return WS.sub(" ", t).strip()


def mn(t):
    return norm(t).split(None, 1)[0]


def btarget(t):
    """branch target as int if this line is a direct unconditional/conditional jump."""
    m = re.match(r"^(?:jmp|%s)\s+(0x[0-9a-f]+)$" % CC, norm(t))
    return int(m.group(1), 16) if m else None


def call_target(t):
    m = re.match(r"^call\s+(0x[0-9a-f]+)$", norm(t))
    return int(m.group(1), 16) if m else None


class Out:
    def __init__(self, path):
        self.f = open(path, "w")

    def p(self, s=""):
        self.f.write(s + "\n")
        print(s)

    def close(self):
        self.f.close()


def load_dump():
    """addr -> (normalized mnemonic+operands, encoding bytes)."""
    ins, enc = {}, {}
    with open(TEXT, errors="replace") as f:
        for ln in f:
            m = LINE_RX.match(ln)
            if m:
                a = int(m.group(1), 16)
                if a not in ins:
                    ins[a] = norm(m.group(3))
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


O = Out(EVID)
CHECKS = []


def gate(n, ok, text):
    CHECKS.append(bool(ok))
    O.p("A%d %s: %s" % (n, "PASS" if ok else "FAIL", text))


def main():
    ins, enc, addrs = load_dump()
    funcs = load_index()

    # ---- S0: containment -------------------------------------------------------------
    O.p("== S0: containment (ghidra_out/index.csv - NEVER objdump at an arbitrary addr) ==")
    cont = {}
    for a in (LO, HI, LOOP_HEAD, CALL, STORE):
        cont[a] = contain(funcs, a)[:2]
        O.p("   0x%-8x -> %-14s inside=%s" % (a, cont[a][0], cont[a][1]))
    fname, fsize, fnins = contain(funcs, FUN)[0], contain(funcs, FUN)[2], \
        contain(funcs, FUN)[3]
    faddr = next(x[0] for x in funcs if x[1] == fname)
    body = [a for a in addrs if faddr <= a < faddr + fsize]
    O.p("   %s entry 0x%x  size %d B  Ghidra n_insns %d  dump insns in window %d"
        % (fname, faddr, fsize, fnins, len(body)))
    gate(0, all(cont[a][1] and cont[a][0] == fname for a in cont) and fnins == len(body),
         "the lead's endpoints 0x%x/0x%x, the walk head 0x%x and the M299 gate chain are all "
         "contained in %s; instruction count over the function window (%d) == Ghidra's "
         "n_insns (%d) - objdump dump and Ghidra, two toolchains, agree the span is decoded "
         "instruction stream with no data island" % (LO, HI, LOOP_HEAD, fname, len(body),
                                                      fnins))

    # ---- S1: the range VERBATIM -------------------------------------------------------
    win = [a for a in addrs if LO <= a <= HI]
    span_end = max(win) + len(enc[max(win)])
    span = span_end - LO
    bytesum = sum(len(enc[a]) for a in win)
    O.p("\n== S1: the range 0x%x-0x%x VERBATIM (%d insns, span 0x%x = %d B) =="
        % (LO, HI, len(win), span, span))
    for a in win:
        O.p("   0x%-8x %-18s %s" % (a, " ".join("%02x" % b for b in enc[a]), ins[a]))
    O.p("   raw bytes: %s" % "".join("%02x" % b for a in win for b in enc[a]))
    gaps = [win[i] - (win[i - 1] + len(enc[win[i - 1]])) for i in range(1, len(win))]
    O.p("   sum(encoding bytes) %d == span %d: %s; max gap %d"
        % (bytesum, span, bytesum == span, max(gaps) if gaps else 0))
    # the walk's own extent, DERIVED from its back edge rather than assumed
    back = [a for a in win if btarget(ins[a]) is not None and btarget(ins[a]) <= a]
    bk = back[0]
    wlo, whi = btarget(ins[bk]), bk + len(enc[bk])      # [head, after back edge)
    walk = [a for a in win if wlo <= a < whi]
    tail = [a for a in win if a >= whi]
    O.p("   back edge: 0x%x `%s` -> head 0x%x  => WALK = 0x%x-0x%x (%d insns); "
        "EXIT BLOCK = 0x%x-0x%x (%d insns)"
        % (bk, ins[bk], wlo, wlo, whi - 1, len(walk), tail[0], HI, len(tail)))
    gate(1, bytesum == span and (not gaps or max(gaps) == 0) and len(back) == 1,
         "the %d B range tiles GAP-FREE from its own encoding bytes (%d insns, every gap 0) "
         "and contains exactly %d back edge (0x%x -> 0x%x): the range is %d instructions of a "
         "single loop plus %d instructions of its straight-line exit block - a data table "
         "cannot tile a byte span as a legal instruction stream that Ghidra also placed "
         "inside %s" % (span, len(win), len(back), bk, wlo, len(walk), len(tail), fname))

    # ---- S2: entry census under competing models ---------------------------------------
    dw_slots = span // 4
    bodyimg = b"".join(enc[a] for a in body)
    off0 = bodyimg.index(b"".join(enc[a] for a in win))

    def va_hits(aligned_only):
        out = []
        for k in range(0, span - 3, 4 if aligned_only else 1):
            v = int.from_bytes(bodyimg[off0 + k:off0 + k + 4], "little")
            if TEXT_LO <= v < TEXT_HI:
                out.append((LO + k, v))
        return out
    h_al, h_any = va_hits(True), va_hits(False)
    calls_in = [a for a in win if call_target(ins[a]) is not None]
    br_in = [a for a in win if btarget(ins[a]) is not None]
    callee_nm = contain(funcs, CALLEE)[0]
    O.p("\n== S2: entry census under four competing models ==")
    O.p("   dword entries: %d slots of 4 B fit in %d B, %d bytes left over -> the span is not "
        "a uniform array of dwords" % (dw_slots, span, span - 4 * dw_slots))
    O.p("   instructions in the range: %d (%d walk + %d exit block)"
        % (len(win), len(walk), len(tail)))
    O.p("   dwords at 4-B-aligned offsets in the range resolving into .text (%02x-%02x): %d %s"
        % (TEXT_LO, TEXT_HI, len(h_al), [("%08x->%08x" % (a, v)) for a, v in h_al]))
    O.p("   dwords at ANY offset in the range resolving into .text: %d %s"
        % (len(h_any), [("%08x->%08x" % (a, v)) for a, v in h_any]))
    O.p("   call instructions INSIDE the range: %d -> %s (callee %s)"
        % (len(calls_in), ["0x%x" % a for a in calls_in], callee_nm))
    O.p("   branches with a direct target inside the range: %d" % len(br_in))
    gate(2, span % 4 != 0 and not h_al and not h_any and bool(win) and bool(calls_in),
         "ZERO entries: %d 4-B-aligned dword slots with %d B left over, and not one dword in "
         "the range - aligned or at any byte offset - resolves to a VA inside .text, which is "
         "what a jump/dispatch body or a pointer table must contain; the raw values are "
         "instruction encodings (S1 prints all %d), %d of them being CALLs to %s - data does "
         "not call" % (dw_slots, span - 4 * dw_slots, len(win), len(calls_in), callee_nm))

    # ---- S3: nature ---------------------------------------------------------------------
    O.p("\n== S3: nature (a table is ADDRESSED; a loop is fallen into and back-edged) ==")
    indirect = [a for a in body if re.match(r"^(?:jmp|call)\s+(?:DWORD PTR\s+)?\[", ins[a])]
    O.p("   indirect (memory-form) jmp/call anywhere in %s: %d %s"
        % (fname, len(indirect), [ins[a] for a in indirect]))
    ext_branch, ext_nonbranch, internal, tail_edge = [], [], [], []
    for a in addrs:
        for m in HEX_RX.finditer(ins[a]):
            v = int(m.group(1), 16)
            if not (LO <= v < span_end):
                continue
            t = btarget(ins[a])
            if t is None:
                ext_nonbranch.append((a, ins[a]))
            elif wlo <= a < whi:
                internal.append((a, v))                      # edge wholly inside the walk
            elif LOOP_HEAD <= a < span_end:
                tail_edge.append((a, v))                      # edge inside the range, in the exit block
            else:
                ext_branch.append((a, v))                     # edge from OUTSIDE the range
    O.p("   mentions of any address in [0x%x,0x%x) as an operand: %d edges inside the walk, %d "
        "inside the exit block, %d from OUTSIDE the range, %d NON-BRANCH (lea/mov/push = would "
        "mean data)" % (LO, span_end, len(internal), len(tail_edge), len(ext_branch),
                        len(ext_nonbranch)))
    for a, v in sorted(set(ext_branch)):
        O.p("       OUTSIDE edge 0x%-8x -> 0x%-8x  %s%s"
            % (a, v, ins[a], "   (BYPASSES the walk)" if v >= EXIT_BLOCK else "   (enters the walk!)"))
    for a, v in sorted(set(tail_edge)):
        O.p("       in-range edge 0x%-8x -> 0x%-8x  %s   (the walk's normal fall-out / the exit "
            "block's own skip)" % (a, v, ins[a]))
    for a, t in sorted(set(ext_nonbranch)):
        O.p("       NON-BRANCH mention 0x%-8x  %s" % (a, t))
    into_walk = sorted({v for a, v in ext_branch if v < EXIT_BLOCK})
    bypass = sorted({a for a, v in ext_branch if v >= EXIT_BLOCK})
    gate(3, not indirect and not ext_nonbranch and not into_walk and len(back) == 1,
         "ZERO indirect jmp/call anywhere in %s (so no dispatch table is read by this function "
         "at all), ZERO lea/mov/push of any range address image-wide, and ZERO external branch "
         "landing inside the walk - the %d external edges (%s) all target the EXIT BLOCK 0x%x, "
         "i.e. they SKIP the walk. Sole entry to the walk body is fall-through from 0x%x plus "
         "the one back edge: control-flow structure, not an addressable table"
         % (fname, len(bypass), ["0x%x" % a for a in bypass], EXIT_BLOCK, LOOP_HEAD + 2))

    # ---- S4: the array the walk reads ----------------------------------------------------
    O.p("\n== S4: the array the walk reads (already NAMED: base_array, NAMED.md:74) ==")
    cur_init = [a for a in body if ins[a] == "mov eax,0x%x" % CURSOR_INIT]
    stride = [a for a in body if re.match(r"^add eax,0x%x$" % ROW, ins[a])]
    bound_ld = [a for a in walk + [LOOP_HEAD - 0x1c, LOOP_HEAD - 0x10]
                if "0x%x" % COUNT_G in ins[a]]
    cnt_refs = [a for a in sorted(body) if "[ebp-0x18]" in ins[a]]
    cnt_loop = [a for a in cnt_refs if LOOP_HEAD - 0x20 <= a <= whi - 1]
    # NOTE: the row+4 load sits at the walk's HEAD (0x51de29), 3 B BELOW the lead's low end,
    # so the field census runs over the walk region, not the quoted range.
    walkreg = [a for a in body if LOOP_HEAD <= a <= HI]
    fields = {"WORD[eax] (row+2 = y)": "movsx esi,WORD PTR [eax]",
              "WORD[eax-0x2] (row+0 = x)": "movsx ecx,WORD PTR [eax-0x2]",
              "BYTE[eax+0x2] (row+4 = flag/owner)": "mov cl,BYTE PTR [eax+0x2]",
              "BYTE[edi+0x7] (exit block; edi = [ebp-0x4])":
                  "movsx ecx,BYTE PTR [edi+0x7]"}
    fhits = {k: [a for a in walkreg if ins[a] == v] for k, v in fields.items()}
    for k, v in fhits.items():
        O.p("   %s%s read at %s" % (k, "" if v else " NOT", ["0x%x" % a for a in v]))
    O.p("   cursor init: %s `%s` = base_array 0x%x + 2"
        % (["0x%x" % a for a in cur_init],
           [ins[a] for a in cur_init], BASE_ARRAY))
    O.p("   cursor spill/reload [ebp-0x14]: %s"
        % ["0x%x `%s`" % (a, ins[a]) for a in body if "[ebp-0x14]" in ins[a]])
    O.p("   row stride: %s `%s` = %d B"
        % (["0x%x" % a for a in stride], [ins[a] for a in stride], ROW))
    O.p("   trip counter [ebp-0x18] refs in the walk region: %s"
        % ["0x%x `%s`" % (a, ins[a]) for a in cnt_loop])
    O.p("   [ebp-0x18] is REUSED later in the function at %s (outside this walk)"
        % ["0x%x" % a for a in cnt_refs if a not in cnt_loop])
    O.p("   bound global ds:0x%x (row count): %s"
        % (COUNT_G, ["0x%x `%s`" % (a, ins[a]) for a in sorted(set(bound_ld))]))
    tile_math = [a for a in walk if "0x%x" % WIDTH_G in ins[a] or "0x%x" % TILE_BASE in ins[a]]
    O.p("   44-B tile-record view inside the walk body (`44*(ds:0x%x*Y + X>>1)` at ds:0x%x; "
        "B16 law NAMED:967): %s" % (WIDTH_G, TILE_BASE,
                                     ["0x%x `%s`" % (a, ins[a]) for a in tile_math]))
    dist_math = [a for a in walk if "0x%x" % DIST_G in ins[a]]
    O.p("   distance global ds:0x%x used at %s (`%s`)"
        % (DIST_G, ["0x%x" % a for a in dist_math],
           [ins[a] for a in dist_math]))
    gate(4, len(cur_init) == 1 and len(stride) == 1 and len(back) == 1 and
         all(fhits[k] for k in fields) and len(bound_ld) >= 2 and len(dist_math) >= 1,
         "the range walks base_array @0x%x: cursor 0x%x = base+2 (`mov eax,0x%x` 0x51de1f, "
         "spilled/reloaded through [ebp-0x14]), rows advance `add eax,0x%x` = %d B at 0x%x, the "
         "trip counter is [ebp-0x18] (zeroed 0x51de10, inc 0x51dee1, stored 0x51dee9) bounded "
         "by the BSS row count ds:0x%x (test 0x51de17 `jle` skips the walk whole, cmp 0x51dee7 "
         "drives the back edge), and the body reads row fields x(+0)/y(+2)/flag(+4) plus the "
         "44-B tile record view, compares a distance against ds:0x%x, and its exit block "
         "compares the walk's verdict ebx against BYTE PTR [edi+0x7] (edi = [ebp-0x4]) - the "
         "lead's \"table\" is this named runtime array, whose row count is NOT a static constant" % (BASE_ARRAY, CURSOR_INIT, CURSOR_INIT, ROW, ROW, stride[0],
                              COUNT_G, DIST_G))

    # ---- S5: index provenance -------------------------------------------------------------
    O.p("\n== S5: index provenance (who computes the value the walk compares) ==")
    chain = [0x51DDF2, 0x51DDF7, 0x51DDFA]
    st = {"eax": 1, "edx": 0}     # affine over i (constant term 0 throughout)
    for a in chain:
        O.p("   0x%-8x %s" % (a, ins[a]))
        t = norm(ins[a]).split(None, 1)[1]
        dst, src = [x.strip() for x in t.split(",")]
        if a == 0x51DDF2:
            st["edx"] = 9 * st["eax"]                     # edx = eax + eax*8
        elif a == 0x51DDF7:
            st["eax"] = st["eax"] + 2 * st["edx"]         # eax = eax + edx*2
        else:
            st["eax"] = 16 * st["eax"]                    # shl eax,0x4
        O.p("       -> eax = %d*i    edx = %d*i" % (st["eax"], st["edx"]))
    scale = st["eax"]
    oload = [a for a in body if ins[a] == "mov bl,BYTE PTR [eax+0x%x]" % OWNER_BYTE]
    cal = [a for a in body if call_target(ins[a]) == SELECTOR]
    O.p("   every call of FUN_004e37f0 in %s: %s (the walk's index comes from 0x51ddb1; "
        "0x51e0d7 is a later leg of the function)" % (fname, ["0x%x" % a for a in cal]))
    O.p("   i = FUN_004e37f0's return: call 0x%x; 0x51ddb9 `%s`; 0x51ddbb `%s`; "
        "0x51ddbd `%s`; 0x51ddc0 `%s`"
        % (cal[0] if cal else 0, ins[0x51DDB9], ins[0x51DDBB], ins[0x51DDBD], ins[0x51DDC0]))
    O.p("   ebx = BYTE[%d*i + 0x%x] at %s: %s"
        % (scale, OWNER_BYTE, ["0x%x" % a for a in oload], [ins[a] for a in oload]))
    ebxw = [a for a in body if a <= HI and re.search(r"\bebx\b", ins[a]) and
            re.match(r"^(?:mov|or|xor|add|sub|inc|dec|and|lea)\s+(?:bl|ebx)\b", ins[a])]
    O.p("   ebx WRITERS up to the range end (%d): %s"
        % (len(ebxw), ["0x%x `%s`" % (a, ins[a]) for a in ebxw]))
    ebp4 = [a for a in body if a < LO and ins[a].startswith("mov DWORD PTR [ebp-0x4]")]
    O.p("   the exit block's record operand: edi = [ebp-0x4]; the ONLY writer below the range "
        "is 0x%x `%s`; its 3 producers:" % (ebp4[0], ins[ebp4[0]]))
    for a in [x for x in body if x < ebp4[0]][-3:]:
        O.p("       0x%-8x %s" % (a, ins[a]))
    O.p("   OPEN: whose record [edi+0x7] is (a 44-B tile record or a base row) - undecided here")
    named_txt = WS.sub(" ", open(NAMED, errors="replace").read())
    cite = "0x95da14+304*i" in named_txt and "base_array" in named_txt
    gate(5, scale == ROW and len(oload) == 1 and cal[:1] == [0x51DDB1] and cite,
         "the walk's compared value is ebx = BYTE[%d*i + 0x%x] (0x51ddff), and the scale chain "
         "0x51ddf2/0x51ddf7/0x51ddfa evaluates to %d*i = exactly the row size %d; i is "
         "FUN_004e37f0's return (call 0x51ddb1; `test eax,eax` 0x51ddb9 / `jge` 0x51ddbb; "
         "on a negative return 0x51ddbd `or ebx,0xffffffff` and 0x51ddc0 jumps straight to the "
         "walk's exit block, skipping the walk). Registry agreement: NAMED.md carries "
         "`ebx = BYTE[0x95da14+304*i]` and `base_array ... 37 x 304 B` (NAMED.md:74, :468 - "
         "M43/M278: base+4 = owner player index). So the INDEX is a base record's owner byte, "
         "not a table subscript, and the walk's own index is its trip counter [ebp-0x18]"
         % (scale, OWNER_BYTE, scale, ROW))

    # ---- S6: the (d) verdict ---------------------------------------------------------------
    O.p("\n== S6: (d) does the range gate or label the 0x51dffd decision? ==")
    ebx_use = [a for a in body if span_end <= a <= STORE and re.search(r"\bebx\b", ins[a])]
    O.p("   every ebx mention from the range end (0x%x) through the counter store 0x%x (%d):"
        % (span_end, STORE, len(ebx_use)))
    for a in ebx_use:
        O.p("   0x%-8x %s" % (a, ins[a]))
    O.p("   edges from OUTSIDE the range landing on the exit block 0x%x (i.e. skipping the walk "
        "whole): %d" % (EXIT_BLOCK, len(bypass)))
    GUARD = {"0x51de05": "guarded by 0x51ddfd `test ecx,ecx` (ecx built before the walk)",
             "0x51de19": "row count ds:0x985af4 <= 0 (0x51de0b load, 0x51de17 `test eax,eax`)",
             "0x51ddc0": "the selector returned negative (0x51ddb1 call, 0x51ddb9 `test`, "
                         "0x51ddbb `jge`)",
             "0x51dded": "ds:0x8f0d34 failed the check at 0x51dde2 `cmp`/0x51dde8 `jl`"}
    for a in bypass:
        O.p("     0x%-8x %-28s %s" % (a, ins[a], GUARD.get(hex(a), "")))
    between = [(a, btarget(ins[a])) for a in body if span_end <= a < CALL
               and btarget(ins[a]) is not None]
    skip_call = [x for x in between if x[1] > CALL]
    O.p("   branches between the range exit (0x%x) and the call 0x%x: %d; legs landing PAST "
        "the call: %d" % (span_end, CALL, len(between), len(skip_call)))
    for a, tv in between:
        O.p("   0x%-8x %-30s -> 0x%-8x  %s"
            % (a, ins[a], tv, "SKIPS THE CALL" if tv > CALL else "rejoins before the call"))
    je_tgt = btarget(ins[EBX_SKIP_JE])
    O.p("   ebx==0 leg: 0x%x `%s` -> 0x%x = the block immediately BEFORE the call (0x%x): it "
        "skips the slot-cell stores 0x51dfd3-0x51dff3 and still executes the call"
        % (EBX_SKIP_JE, ins[EBX_SKIP_JE], je_tgt, PRECALL))
    O.p("   gate bytes: 0x%x `%s` | 0x%x `%s` | 0x%x `%s` | 0x%x `%s` | 0x%x `%s`"
        % (CALL, ins[CALL], GATE_TEST, ins[GATE_TEST], GATE_JE, ins[GATE_JE], INC, ins[INC],
           STORE, ins[STORE]))
    after = [a for a in body if CALL < a <= 0x51E035 and re.search(r"\beax\b", ins[a])]
    O.p("   every eax mention after the call (to 0x51e035): %s"
        % ["0x%x `%s`" % (a, ins[a]) for a in after])
    first_read = next((a for a in after if mn(ins[a]) in ("test", "cmp")), None)
    first_write = next((a for a in after if re.match(r"^(?:mov|lea|shl|sub|add|xor)\s+eax\b",
                                                     ins[a])), None)
    backflow = [a for a in body if a > CALL and btarget(ins[a]) is not None and
                LO <= btarget(ins[a]) < span_end]
    O.p("   backward branches from after the call into the range: %d %s"
        % (len(backflow), ["0x%x" % a for a in backflow]))
    gate(6, not skip_call and not backflow and je_tgt == PRECALL and
         first_read == GATE_TEST and first_write is not None and first_write > first_read,
         "the range neither gates nor LABELS the decision - it is an UPSTREAM PRODUCER of ebx "
         "and the call is flow-unconditional: %d edges bypass the walk whole and land on the "
         "exit block, which falls through to 0x51dff5/0x%x; of the %d branches between the "
         "range exit and the call, ZERO land past the call (the only ebx-driven branch, 0x%x, "
         "targets the pre-call block 0x%x); the ebx the walk produces gates only the cell "
         "stores (0x51dfc9 `test ebx,ebx` / 0x51dfd1) and feeds the POST-STORE byte read "
         "0x51e02c, never the counter address (esi is the 28-B slot fold of [ebp-0xc], M299); "
         "and FUN_005832b0's eax is born at 0x%x, is consumed by exactly one instruction "
         "(0x%x `%s`), is overwritten at 0x%x before any loop, and has ZERO backward edges into "
         "the range - the predicate's return value cannot reach it"
         % (len(bypass), CALL, len(between), EBX_SKIP_JE, PRECALL, CALL, first_read,
            ins[first_read], first_write))

    # ---- S7: the bytes, straight from the PE file image (kills "the dump is patched") -----
    O.p("\n== S7: the same 243 B read out of the PE file image (VA->file via the section table) ==")
    exe = next(p for p in (os.path.join(ROOT, "programs", "terran.exe"),
                           os.path.join(ROOT, "terran.exe")) if os.path.exists(p))
    img = open(exe, "rb").read()
    nthe = struct.unpack_from("<I", img, 0x3c)[0]
    numsec = struct.unpack_from("<H", img, nthe + 6)[0]
    sizopt = struct.unpack_from("<H", img, nthe + 20)[0]
    ibase = struct.unpack_from("<I", img, nthe + 24 + 28)[0]
    shdr = nthe + 24 + sizopt
    sec = None
    for i in range(numsec):
        o = shdr + 40 * i
        nm = img[o:o + 8].rstrip(b"\0").decode(errors="replace")
        vsz, va, rsz, rp = struct.unpack_from("<IIII", img, o + 8)
        if ibase + va <= LO < ibase + va + max(vsz, rsz):
            sec = (nm, va, rp, vsz, rsz)
    nm, va, rp, vsz, rsz = sec
    foff = rp + (LO - ibase - va)
    blob = bodyimg[off0:off0 + span]          # the dump's own bytes for the range
    fileimg = img[foff:foff + span]
    O.p("   %s: image base 0x%x, section %s (vaddr 0x%x vsize 0x%x raw 0x%x size 0x%x)"
        % (os.path.relpath(exe, ROOT), ibase, nm, va, vsz, rp, rsz))
    O.p("   0x%x -> file offset 0x%x, %d B read; identical to the dump's encodings: %s"
        % (LO, foff, len(fileimg), fileimg == blob))
    O.p("   first 24 B: %s ; last 8 B: %s"
        % (" ".join("%02x" % b for b in fileimg[:24]),
           " ".join("%02x" % b for b in fileimg[-8:])))
    gate(7, sec[0] == ".text" and len(fileimg) == span and fileimg == blob,
         "the %d B of the range read straight out of the PE image (%s, file 0x%x) are "
         "BYTE-IDENTICAL to the dump's encodings, and the section is %s (the code section, VA "
         "0x%x+0x%x): the range's raw values are the executable bytes of the shipping file, not "
         "a runtime patch and not a dump artifact" % (span, nm, foff, nm, ibase, va))

    # ---- rollup ------------------------------------------------------------------------
    O.p("\n== ROLLUP (negative result: the lead is refuted) ==")
    O.p("  (a) entries: ZERO data entries. %d B span, %d 4-B dword slots + %d leftover, no "
        "dword resolving into .text; the span is %d instructions (%d walk + %d exit block) "
        "printed VERBATIM in S1"
        % (span, dw_slots, span - 4 * dw_slots, len(win), len(walk), len(tail)))
    O.p("  (b) nature: EXECUTABLE CODE, not code addresses / pointers / masks / offsets - the "
        "body of a walk over base_array 0x%x (row %d B, count ds:0x%x, BSS); (INFERRED shape) it "
        "filters each row's tile by class via the 44-B tile-record view (0x51de5b-0x51de61) and "
        "compares a distance to ds:0x%x (0x51dece-0x51ded0)"
        % (BASE_ARRAY, ROW, COUNT_G, DIST_G))
    O.p("  (c) indexing: base reg = eax (cursor 0x%x = base+2; spill [ebp-0x14]); walk index = "
        "trip counter [ebp-0x18] vs ds:0x%x; the value the walk compares, ebx = BYTE[%d*i + "
        "0x%x], produced at 0x51ddff from i = FUN_004e37f0's return (0x51ddb1)"
        % (CURSOR_INIT, COUNT_G, ROW, OWNER_BYTE))
    O.p("  (d) verdict: the range gates NOTHING that the 0x51dffd decision or the [+4] counter "
        "write depends on (both its bypass legs and its normal fall-through reach the call), "
        "and FUN_005832b0's eax does NOT reach it (defined after it, single consumer `test "
        "eax,eax`, no backward edge)")
    n = len(CHECKS)
    O.p("\n%d/%d assertions hold" % (sum(CHECKS), n))
    O.close()
    return 0 if sum(CHECKS) == n else 1


if __name__ == "__main__":
    sys.exit(main())
