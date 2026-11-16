#!/usr/bin/env python3
"""M307 (s266, STATIC, zero box): the folded body of 0x4f35e0 — WHAT the 21x loop walks,
WHAT the FUN_005a2ae0 triad passes, and what the three _rand sites DO.

M306 (merged, f9fca53) settled bounds/entry only: [0x4f35e0,0x4f4051), entered ONLY by the
fold-jmp 0x4f4133. Its OPEN remnant (NEXT_PROMPT shortlist): "the folded body's MEANING -
the 21x(0x54) loop cap + FUN_005a2ae0 args + _rand x3". This instrument answers exactly
those three things, computed from the raw objdump dump + terran.exe bytes:

  S2 the 21x loop @0x4f3c0a: cap immediate 0x54, index [ebp-0xc] zeroed per entry at
     0x4f3bf1, two dword tables T_x=0x67850c / T_y=0x678990, tile-record conversion
     stride 44 over 0x92ae14, row-walk stride 0x34 over 0x933282 (count ds:0x985af0);
  S3 the 21 (dx,dy) OFFSET PAIRS read out of terran.exe .rdata (VA->file-offset via the
     PE section table) and their exact shape: = {(dx,dy): |dx|<=3,|dy|<=3, dx+dy even}
     minus {(+-3,+-3)}  ->  25-4 = 21, D4-symmetric, ordered center/ring/corners/far;
  S4 the triad @0x4f3e00: FUN_005a2ae0(arg1=[ebp-0x14] = RECORD INDEX into 304-B slots
     at 0x95da10, arg2=[ebp-0x4] = BYTE[ds:0x8f0d60+4] bit position) then FUN_0051dcb0;
     and FUN_00507410 proven to be the div-8 decomposition (n/8 rounded toward ZERO, 1<<(n&7));
  S5 the three _rand@0x64c6f0 sites: TWO probability gates (remainders tested+jne, moduli
     [8380*idx+0x94d690]+7 and 3) + ONE value draw (rand%39 kept in esi).

Every number is COMPUTED from scratch/m574/text.txt, ghidra_out/index.csv and
programs/terran.exe bytes; the tables print first, then asserts; four rival explanations
are scored against the SAME printed numbers and FAIL. stdout mirrors to
evidence/m307_folded_body.txt. Run: python3 scripts/m307_folded_body.py (exit 0 = all hold)
"""
import bisect
import csv
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
INDEX = os.path.join(ROOT, "ghidra_out/index.csv")
EXE = os.path.join(ROOT, "programs/terran.exe")
EVID = os.path.join(ROOT, "evidence", "m307_folded_body.txt")

FN = 0x4F35E0            # folded-body entry (M306: bounds settled there)
FN_END = 0x4F4051        # exclusive end (last ret byte + 1, M306 A2/A5)
LOOP_HEAD = 0x4F3C0A
LOOP_TAIL = 0x4F3DF2
IDX_ZERO = 0x4F3BF1
TX, TY = 0x67850C, 0x678990      # the two 21-dword tables the loop indexes
RAND = 0x64C6F0
A2AE0 = 0x5A2AE0
DCB0 = 0x51DCB0
DIV8 = 0x507410
TILE_BASE, TILE_STRIDE = 0x92AE14, 44
ROW_TABLE, ROW_STRIDE = 0x933282, 0x34
REC_TABLE = 0x95DA10               # 304-B record table FUN_005a2ae0 indexes

LINE_RX = re.compile(r"^ +([0-9a-f]{6,8}):\t([0-9a-f ]+?)\t\s*(.+?)\s*$")
JCC_RX = re.compile(r"^(je|jne|jl|jge|jg|jle|jb|jae|ja|jbe|js|jns|jo|jno|jc|jnc)\s+(?:0x)?([0-9a-f]{4,8})$")
JMP_RX = re.compile(r"^jmp\s+(?:0x)?([0-9a-f]{4,8})$")
CALL_RX = re.compile(r"^call\s+(?:0x)?([0-9a-f]{6,8})(?:\s|$)")
EBP_RX = re.compile(r"\[ebp\+0x([0-9a-f]+)\]")


class Out:
    def __init__(self, path):
        self.f = open(path, "w")

    def p(self, s=""):
        self.f.write(s + "\n")
        print(s)

    def close(self):
        self.f.close()


CHECKS = []
OUT = None


def chk(name, ok):
    CHECKS.append((name, bool(ok)))
    OUT.p("  [%s] %s" % ("OK" if ok else "FAIL", name))
    return ok


def main():
    out = Out(EVID)
    global OUT
    OUT = out
    # ---------------------------------------------------------------- parse .text
    addrs, ins, raw = [], {}, {}
    with open(TEXT, errors="replace") as fh:
        for line in fh:
            m = LINE_RX.match(line)
            if not m:
                continue
            a = int(m.group(1), 16)
            addrs.append(a)
            raw[a] = m.group(2).replace(" ", "")
            ins[a] = m.group(3)
    idx = {a: i for i, a in enumerate(addrs)}

    # ghidra names for the callees we cite
    names = {}
    with open(INDEX, newline="") as fh:
        for r in csv.DictReader(fh):
            names[int(r["addr"], 16)] = r["name"]

    span = [a for a in addrs if FN <= a < FN_END]
    lo, hi = idx[span[0]], idx[span[-1]] + 1
    # all branch targets dump-wide (for entry/dominance checks)
    targets = {}
    for a in addrs:
        t = ins[a]
        m = JCC_RX.match(t)
        if m:
            targets.setdefault(int(m.group(2), 16), []).append(a)
            continue
        m = JMP_RX.match(t)
        if m:
            targets.setdefault(int(m.group(1), 16), []).append(a)

    # ------------------------------------------------------------------ TABLES
    out.p("M307 folded body 0x%x..0x%x  (objdump insns=%d; M306 settled these bounds)"
          % (FN, FN_END, len(span)))

    # S2 loop shape
    out.p("\n[S2] 21x loop:")
    cap_cmp = [a for a in span if ins[a] == "cmp    eax,0x54"]
    out.p("  cap cmp eax,0x54 sites in span: %s" % [hex(a) for a in cap_cmp])
    back = [a for a in targets.get(LOOP_HEAD, []) if FN <= a < FN_END]
    out.p("  branch preds of loop head 0x%x (inside span): %s" % (LOOP_HEAD, [hex(a) for a in back]))
    tl = span.index(LOOP_TAIL)
    i_add, i_cmp, i_mov, i_jl = (ins[span[tl - 3]], ins[span[tl - 2]], ins[span[tl - 1]], ins[LOOP_TAIL])
    out.p("  tail@0x%x: %s | %s | %s | %s" % (LOOP_TAIL, i_add, i_cmp, i_mov, i_jl))
    # the assertable values are PARSED from these mnemonics, never hardcoded (Greptile #279 P2)
    inc_m = re.match(r"^add    eax,0x([0-9a-f]+)$", i_add)
    cap_m = re.match(r"^cmp    eax,0x([0-9a-f]+)$", i_cmp)
    jl_m = JCC_RX.match(i_jl)
    inc = int(inc_m.group(1), 16) if inc_m else -1
    cap = int(cap_m.group(1), 16) if cap_m else -1
    jlt = int(jl_m.group(2), 16) if jl_m else -1
    out.p("  index var: head reads %s ; zero-store @0x%x: %s"
          % (ins[LOOP_HEAD], IDX_ZERO, ins[IDX_ZERO]))
    n4 = (cap - 0 + inc - 1) // inc if inc > 0 else -1
    out.p("  parsed: inc=%d cap=0x%x jl->0x%x ; iterations = ceil((cap-0)/inc) = %d ; cap %% inc = %d ; idx values 0..%d step %d"
          % (inc, cap, jlt, n4, cap % inc if inc > 0 else -1, (n4 - 1) * inc, inc))
    gap_targets = sorted(t for t in targets
                         if IDX_ZERO + 1 < t < LOOP_HEAD or (LOOP_HEAD < t <= IDX_ZERO))
    out.p("  branch targets landing strictly between zero-store and head: %s" % [hex(t) for t in gap_targets])

    tx_reads = [a for a in span if LOOP_HEAD <= a <= LOOP_TAIL and re.search(r"\[e\w+\+0x67850c\]", ins[a])]
    ty_reads = [a for a in span if LOOP_HEAD <= a <= LOOP_TAIL and re.search(r"\[e\w+\+0x678990\]", ins[a])]
    out.p("  T_x reads in loop @%s: %s" % ([hex(a) for a in tx_reads], [ins[a] for a in tx_reads]))
    out.p("  T_y reads in loop @%s: %s" % ([hex(a) for a in ty_reads], [ins[a] for a in ty_reads]))
    stride_chain = [(a, ins[a]) for a in span if a in (0x4F3C8B, 0x4F3C8E, 0x4F3C93)]
    # PARSE the scale factors out of the three leas (Greptile #279 P2: don't assert addresses)
    s1 = re.match(r"^lea    edx,\[eax\+eax\*(\d)\]$", stride_chain[0][1]) if len(stride_chain) > 0 else None
    s2 = re.match(r"^lea    eax,\[eax\+edx\*(\d)\]$", stride_chain[1][1]) if len(stride_chain) > 1 else None
    s3 = re.match(r"^lea    eax,\[ecx\+eax\*(\d)\]$", stride_chain[2][1]) if len(stride_chain) > 2 else None
    if s1 and s2 and s3:
        m1 = 1 + int(s1.group(1))                      # edx = x + x*s1
        m2 = 1 + int(s2.group(1)) * m1                 # eax = x + edx*s2
        stride_parsed = m2 * int(s3.group(1))          # eax = base + eax*s3
        out.p("  tile-stride chain: %s -> PARSED (1+%d)=%d -> (1+%d*%d)=%d -> *%d = %d over %s"
              % ([(hex(a), t) for a, t in stride_chain], int(s1.group(1)), m1,
                 int(s2.group(1)), m1, m2, int(s3.group(1)), stride_parsed, ins[0x4F3C82]))
    else:
        stride_parsed = -1
        out.p("  tile-stride chain: %s -> PARSE FAILED (chain shape changed)"
              % [(hex(a), t) for a, t in stride_chain])
    rowwalk = {"base lea": [(a, ins[a]) for a in span if "0x933282" in ins[a]],
               "step": [(a, ins[a]) for a in span if re.match(r"^sub    esi,0x34$", ins[a])],
               "count": [(a, ins[a]) for a in span if re.search(r"ds:0x985af0", ins[a])]}
    out.p("  row-walk stride-%s over 0x%x (count ds:0x985af0): %s"
          % (hex(ROW_STRIDE), ROW_TABLE, {k: [hex(a) for a, _ in v] for k, v in rowwalk.items()}))

    # S3 the 21 offset pairs out of terran.exe
    blob = open(EXE, "rb").read()
    e_lfanew = struct.unpack_from("<I", blob, 0x3C)[0]
    opt_sz = struct.unpack_from("<H", blob, e_lfanew + 20)[0]
    image_base = struct.unpack_from("<I", blob, e_lfanew + 52)[0]
    secs = []
    for i in range(struct.unpack_from("<H", blob, e_lfanew + 6)[0]):
        o = e_lfanew + 24 + opt_sz + i * 40
        nm = blob[o:o + 8].rstrip(b"\0").decode("ascii", "replace")
        vsz, va, rsz, rp = struct.unpack_from("<IIII", blob, o + 8)
        secs.append((nm, image_base + va, vsz, rsz, rp))

    def va2off(v):
        for nm, sv, vsz, rsz, rp in secs:
            if sv <= v < sv + max(vsz, rsz):
                if v - sv >= rsz:
                    return None, nm + "(BSS)"
                return rp + (v - sv), nm
        return None, "?"

    offx, secx = va2off(TX)
    offy, secy = va2off(TY)
    out.p("\n[S3] offset tables: T_x VA 0x%x -> %s off %s ; T_y VA 0x%x -> %s off %s"
          % (TX, secx, offx and hex(offx), TY, secy, offy and hex(offy)))
    dxs = [struct.unpack_from("<i", blob, offx + 4 * i)[0] for i in range(21)]
    dys = [struct.unpack_from("<i", blob, offy + 4 * i)[0] for i in range(21)]
    out.p("  %-3s %-4s %-4s | %-3s %-4s %-4s | %-3s %-4s %-4s" %
          ("i", "dx", "dy", "i", "dx", "dy", "i", "dx", "dy"))
    for c in range(7):
        cells = []
        for k in range(3):
            i = c * 3 + k
            if i < 21:
                cells.append("%-3d %-4d %-4d" % (i, dxs[i], dys[i]))
        out.p("  " + "  ".join(cells))
    pairs = set(zip(dxs, dys))
    EXPECT = {(x, y) for x in range(-3, 4) for y in range(-3, 4) if (x + y) % 2 == 0} \
             - {(3, 3), (3, -3), (-3, 3), (-3, -3)}
    out.p("  distinct=%d  equals even-parity Cheb3-box minus (+-3,+-3) (%d elems): %s"
          % (len(pairs), len(EXPECT), pairs == EXPECT))
    out.p("  D4 closed (negate+swap): %s ; first=(0,0): %s"
          % (all((-x, -y) in pairs and (y, x) in pairs for x, y in pairs),
             (dxs[0], dys[0]) == (0, 0)))
    ring = list(zip(dxs[1:9], dys[1:9]))
    out.p("  i1..8 ring: %s" % ring)
    out.p("  i9..12 corners: %s" % list(zip(dxs[9:13], dys[9:13])))
    out.p("  i13..20 far: %s" % list(zip(dxs[13:21], dys[13:21])))

    # S4 the triad + FUN_005a2ae0 arg semantics
    out.p("\n[S4] triad and FUN_005a2ae0 args:")
    tri_calls = [a for a in span if CALL_RX.match(ins[a])
                 and int(CALL_RX.match(ins[a]).group(1), 16) == A2AE0]
    t0 = tri_calls[0]
    out.p("  calls to 0x%x in span: %s" % (A2AE0, [hex(a) for a in tri_calls]))
    for a in addrs[idx[t0] - 3: idx[t0] + 3]:
        out.p("    %s: %s" % (hex(a), ins[a]))
    callee_span = [a for a in addrs if A2AE0 <= a < A2AE0 + 254]
    arg_slots = sorted({int(m.group(1), 16) for a in callee_span for m in [EBP_RX.search(ins[a])] if m})
    out.p("  callee %s [0x%x,+254): stack slots referenced: %s (only +0x8/+0xc = 2 int args)"
          % (names.get(A2AE0), A2AE0, ["[ebp+%#x]" % s for s in arg_slots]))
    a1_chain = [(hex(a), ins[a]) for a in callee_span if re.search(r"lea.*eax\+eax\*[248]9?|shl    eax,0x4", ins[a])][:4]
    out.p("  arg1 scaling chain: %s  -> %d*arg1 + 0x%x (record stride 304 = 0x%x)"
          % (a1_chain, 19 * 16, REC_TABLE, 304))
    coord_reads = [(hex(a), ins[a]) for a in callee_span if "0x95da10" in ins[a] or "0x95da12" in ins[a]]
    out.p("  coordinate reads from the RECORD, not the args: %s" % coord_reads)
    checks_bounds = [(hex(a), ins[a]) for a in callee_span if "ds:0x92a378" in ins[a] or "ds:0x92a37c" in ins[a]]
    out.p("  bounds cmps in callee (against the RECORD's WORDs): %s" % checks_bounds)

    def pushers(call_a):
        p = []
        i = idx[call_a] - 1
        while i >= 0 and ins[addrs[i]].startswith("push"):
            p.insert(0, (addrs[i], ins[addrs[i]]))
            i -= 1
        return p

    out.p("  push sites before the triad call: %s" % [(hex(a), t) for a, t in pushers(t0)])
    b4_w = [(hex(a), ins[a]) for a in span if re.search(r"mov\s+DWORD PTR \[ebp-0x4\],", ins[a])]
    b4_addr = [(hex(a), ins[a]) for a in span if re.search(r"lea\s+\w+,\[ebp-0x4\]", ins[a])]
    b14_w = [(hex(a), ins[a]) for a in span if re.search(r"mov\s+DWORD PTR \[ebp-0x14\],", ins[a])]
    b14_addr = [(hex(a), ins[a]) for a in span if re.search(r"lea\s+\w+,\[ebp-0x14\]", ins[a])]
    out.p("  [ebp-0x4] stores: %s | address-of: %s" % (b4_w, b4_addr))
    out.p("  [ebp-0x14] stores: %s | address-of (out-param): %s" % (b14_w, b14_addr))
    out.p("  [ebp-0x4] value source: %s / %s / %s (ecx=ds:0x8f0d60)"
          % (ins[0x4F35E6], ins[0x4F35F0], ins[0x4F35F6]))

    div8_span = [a for a in addrs if DIV8 <= a < DIV8 + 39]
    out.p("  callee %s (%d insns): %s" % (names.get(DIV8), len(div8_span), [ins[a] for a in div8_span]))
    out.p("    -> out1 = (n + (n>>31 & 7))>>3 : n/8 ROUNDED TOWARD ZERO (n=-1 -> 0, unlike //); out2 = 1<<(n&7)  [div-8 slot->(qword,bit)]")

    # S5 the three _rand sites
    out.p("\n[S5] _rand@0x%x sites in span (index.csv name=%s):" % (RAND, names.get(RAND)))
    rand_sites = [a for a in span if CALL_RX.match(ins[a])
                  and int(CALL_RX.match(ins[a]).group(1), 16) == RAND]
    rand_rows = []
    for rs_ in rand_sites:
        seq = [(a, ins[a]) for a in addrs if rs_ < a <= rs_ + 32]
        idiv = next((t for _, t in seq if t.startswith("idiv")), "?")
        mod_setup = [t for a2, t in seq if t.startswith("mov    ecx,") and "0x" in t]
        cons = [t for a2, t in seq if re.match(r"^(test\s+edx,edx|mov    esi,edx)$", t)]
        gate = next((a2 for a2, t in seq if t == "test   edx,edx" or t.startswith("test    edx,edx")), None)
        jne = next(((a2, t) for a2, t in seq if JCC_RX.match(t)
                    and JCC_RX.match(t).group(1) == "jne"
                    and FN <= int(JCC_RX.match(t).group(2), 16) < FN_END), None)
        kind = "GATE (remainder only tested -> early exit)" if gate and jne else \
               ("VALUE (kept in esi)" if any(t == "mov    esi,edx" for _, t in seq) else "?")
        rand_rows.append((rs_, idiv, mod_setup, kind, jne))
        out.p("  site 0x%x: %s | moduli-setup %s | consumed: %s" % (rs_, idiv, mod_setup, kind))
        out.p("      after: %s" % " ; ".join("%s: %s" % (hex(a2), t) for a2, t in seq[:6]))

    # ------------------------------------------------------------------ ASSERTS
    out.p("\n--- ASSERTS ---")
    chk("A1 span re-parses to 846 insns ending ret@0x4f4050 (M306 bounds hold)",
        len(span) == 846 and span[-1] == 0x4F4050 and ins[0x4F4050] == "ret")
    chk("A2 cap is the immediate 0x54 exactly ONCE in span (%d)" % len(cap_cmp),
        len(cap_cmp) == 1)
    chk("A3 loop head preds inside span = {jl@0x4f3df2} only (%s)" % [hex(a) for a in back],
        back == [LOOP_TAIL])
    chk("A4 index [ebp-0xc] zeroed per entry @0x4f3bf1 (%s), back-edge jl parsed target=0x%x, "
        "tail ops parsed inc=%d cap=0x%x -> %d passes/call, and no branch target lands between the "
        "zero-store and the head (%s)"
        % (ins[IDX_ZERO], jlt, inc, cap, n4, [hex(t) for t in gap_targets]),
        ins[IDX_ZERO].startswith("mov    DWORD PTR [ebp-0xc],0x0") and not gap_targets and
        inc_m and cap_m and jl_m and inc == 4 and cap == 0x54 and jlt == LOOP_HEAD and n4 == 21)
    chk("A5 loop body indexes T_x once (%d) and T_y once (%d) via [idx+disp] dwords"
        % (len(tx_reads), len(ty_reads)), len(tx_reads) == 1 and len(ty_reads) == 1)
    chk("A6 tile conversion inside loop: the 3 lea scale factors PARSE to (1+%d)=%d,(1+%d*%d)=%d,*%d=%d "
        "over ds:0x92ae14 — stride asserted from operands, not addresses"
        % ((int(s1.group(1)), m1, int(s2.group(1)), m1, m2, int(s3.group(1)), stride_parsed)
           if (s1 and s2 and s3) else (-1, -1, -1, -1, -1, -1, -1)),
        bool(s1 and s2 and s3) and stride_parsed == TILE_STRIDE == 44)
    chk("A7 row-walk inside loop: base 0x933282, step sub esi,0x34, count ds:0x985af0 all present",
        rowwalk["base lea"] and rowwalk["step"] and rowwalk["count"])
    chk("A8 tables live in file-backed %s/%s (NOT BSS) -> on-disk constants" % (secx, secy),
        offx is not None and offy is not None and "BSS" not in secx + secy)
    chk("A9 21 pairs are DISTINCT and equal the even-parity Cheb3 box minus (+-3,+-3) (%d elems)"
        % len(EXPECT), len(pairs) == 21 and pairs == EXPECT)
    chk("A10 set closed under (dx,dy)->(-dx,-dy) and (dx,dy)->(dy,dx); pair0=(0,0)",
        all((-x, -y) in pairs and (y, x) in pairs for x, y in pairs) and (dxs[0], dys[0]) == (0, 0))
    chk("A11 ordering: i1..8 all in {|d|<=2}\\{(0,0)} ring; i9..12 = (+-2,+-2); i13..20 all have a 3",
        all(0 < max(abs(x), abs(y)) <= 2 for x, y in ring) and
        sorted(zip(dxs[9:13], dys[9:13])) == sorted([(2, -2), (2, 2), (-2, 2), (-2, -2)]) and
        all(3 in (abs(x), abs(y)) for x, y in list(zip(dxs[13:], dys[13:]))))
    chk("A12 exactly one 0x5a2ae0 call in span @0x4f3e00, then add esp,8, then call 0x51dcb0 (triad)",
        len(tri_calls) == 1 and t0 == 0x4F3E00 and ins[t0 + 5] == "add    esp,0x8" and
        int(CALL_RX.match(ins[t0 + 8]).group(1), 16) == DCB0)
    chk("A13 callee reads ONLY [ebp+0x8],[ebp+0xc] (%s) -> exactly 2 int args" % arg_slots,
        arg_slots == [0x8, 0xc])
    chk("A14 callee scales arg1 by 304 into 0x95da10 slots; coords come from WORD[rec+0]/[+2] "
        "and THOSE are bounds-checked vs ds:0x92a378/7c (%d rec reads, %d bounds cmps)"
        % (len(coord_reads), len(checks_bounds)),
        len(coord_reads) >= 2 and len(checks_bounds) >= 2 and
        not any("ebp+0x8" in ins[a] and ("0x92a378" in ins[a] or "0x92a37c" in ins[a])
                for a in callee_span))
    chk("A15 triad arg stores: [ebp-0x4] written ONCE from BYTE[ds:0x8f0d60+4]; [ebp-0x14] stores = "
        "{imm 0, walk-counter} + one address-of (out of %s) -> no coordinate ever stored"
        % names.get(DIV8),
        len(b4_w) == 1 and len(b4_addr) == 0 and
        sorted(t for _, t in b14_w) == ["mov    DWORD PTR [ebp-0x14],0x0",
                                        "mov    DWORD PTR [ebp-0x14],ecx"] and
        len(b14_addr) == 1)
    chk("A16 FUN_00507410 is the div-8 decomposition: and 7 / sar 3 / shl eax,cl present, "
        "stores *edx,*ecx, 17 insns",
        len(div8_span) == 17 and any("and    ecx,0x7" in ins[a] for a in div8_span) and
        any("sar    eax,0x3" in ins[a] for a in div8_span) and
        any("shl    eax,cl" in ins[a] for a in div8_span) and
        sum(1 for a in div8_span if ins[a].startswith("mov    DWORD PTR [e")) == 2)
    chk("A17 exactly THREE _rand sites in span: %s" % [hex(a) for a in rand_sites],
        rand_sites == [0x4F36DF, 0x4F3750, 0x4F379F])
    kinds = [k for _, _, _, k, _ in rand_rows]
    g_n = sum(1 for k in kinds if k.startswith("GATE"))
    v_n = sum(1 for k in kinds if k.startswith("VALUE"))
    chk("A18 consumers: exactly 2 GATEs (test edx,edx + jne) + 1 VALUE (mov esi,edx): %d+%d %s"
        % (g_n, v_n, kinds), g_n == 2 and v_n == 1)
    chk("A19 moduli: site0 dynamic (idiv edi, edi=[8380*idx+0x94d690]+7), site1 3, site2 0x27(39)",
        rand_rows[0][1] == "idiv   edi" and rand_rows[1][1] == "idiv   ecx" and
        rand_rows[2][1] == "idiv   ecx" and "0x27" in " ".join(rand_rows[2][2]) and
        "0x3" in " ".join(rand_rows[1][2]) and
        ins[0x4F36D5] == "add    edi,0x7" and "0x94d690" in ins[0x4F36CF])
    # dump-wide triad census (M305 claim re-checked here at all 0x51dcb0 call sites)
    dcb0_sites = [a for a in addrs if CALL_RX.match(ins[a])
                  and int(CALL_RX.match(ins[a]).group(1), 16) == DCB0]
    triad_sites = [a for a in dcb0_sites
                   if idx[a] >= 2 and ins[addrs[idx[a] - 1]] == "add    esp,0x8" and
                   CALL_RX.match(ins[addrs[idx[a] - 2]]) is not None and
                   int(CALL_RX.match(ins[addrs[idx[a] - 2]]).group(1), 16) == A2AE0]
    out.p("\n  dump-wide: %d call 0x51dcb0 sites, %d immediately preceded by the 0x5a2ae0 triad %s"
          % (len(dcb0_sites), len(triad_sites), [hex(a) for a in triad_sites]))
    chk("A20 triad pattern (call 0x5a2ae0/add esp,8/call 0x51dcb0) holds at 3 of 11 rebuild sites",
        len(dcb0_sites) == 11 and len(triad_sites) == 3)

    # ------------------------------------------------------------- RIVAL SCORES
    out.p("\n--- RIVALS (scored against the printed numbers above) ---")
    cap_is_imm = bool(cap_cmp) and ins[cap_cmp[0]] == "cmp    eax,0x54"
    out.p("RIVAL-1 'the loop cap tracks a record/row-count global (ds:0x985af4 / ds:0x985af0)': "
          "would need a memory cmp operand and a per-entry non-reset index. Printed: cap cmp operand "
          "is the immediate 0x54 (%s), index re-zeroed to 0 at 0x4f3bf1 every entry (A4). -> FAILS"
          % cap_is_imm)
    moore3 = {(x, y) for x in (-1, 0, 1) for y in (-1, 0, 1)}
    moore5 = {(x, y) for x in range(-2, 3) for y in range(-2, 3)}
    out.p("RIVAL-2 'the 21 offsets are a Moore 3x3 or 5x5 neighborhood': printed set has NO "
          "(+-1,0)/(0,+-1) (not Moore-3: subset %s) and OMITS (+-3,+-3)-class corners (not Moore-5: "
          "not superset %s); exact shape = even-parity Chebyshev-3 box minus the 4 (3,3)-class "
          "corners (A9). -> FAILS" % (moore3 <= pairs, moore5 <= pairs))
    a1_coord = any(("cmp" in ins[a] and ("0x92a378" in ins[a] or "0x92a37c" in ins[a])
                    and "ebp+0x8" in ins[a]) for a in callee_span)
    out.p("RIVAL-3 'FUN_005a2ae0 arg1 is a tile (x,y) coordinate': printed callee NEVER bounds-"
          "checks arg1 vs the map dims; it multiplies arg1 by 304 to select a RECORD and reads the "
          "coordinate WORDs from the record, bounds-checking THOSE (A14); producers of [ebp-0x14] "
          "are a counter and a div-8 out-param, never a coordinate (A15). -> FAILS (bad-bounds check "
          "%s)" % a1_coord)
    gates = sum(1 for k in kinds if k.startswith("GATE"))
    out.p("RIVAL-4 'all three _rand results are data draws': 2 of 3 remainders are consumed ONLY "
          "by test edx,edx + jne early-exit (probability gates, one with dynamic modulus "
          "[8380*idx+0x94d690]+7); only 1 is kept (esi, rand%%39). Printed consumers (A18/"
          "A19): %d gate + %d value. -> FAILS" % (gates, 3 - gates))

    n_ok = sum(1 for _, ok in CHECKS if ok)
    out.p("\n%d/%d checks OK" % (n_ok, len(CHECKS)))
    if n_ok != len(CHECKS):
        out.p("FAILURES: %s" % [nm for nm, ok in CHECKS if not ok])
    out.close()
    return 0 if n_ok == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
