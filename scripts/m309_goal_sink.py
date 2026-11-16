#!/usr/bin/env python3
"""M309 (STATIC, zero box): what IS FUN_0056d350, and what does its -1 6th argument select?

THE PICK (NEXT_PROMPT §THE PICK, s268 close): FUN_0056d350 (299 B, 50 callers) is "the sink every
SITE-list insert (M308's FUN_0056d480) and the FUN_0056d690 rebuild broadcast into"; args
(block, kind, prio, x, y, -1). This instrument reads the ENCODING (scratch/m574/text.txt via the
M308 affine engine, ghidra_out/index.csv, the terran.exe PE) and prints tables first, then asserts
every number it printed. It never quotes the Ghidra C text as evidence.

  S1  scope: the index.csv row + the ret/nop that bound the function
  S2  the record-offset multiply chain, evaluated symbolically -> BYTE stride 8380 (0x20bc), so
      param_1 is a RECORD INDEX, not an offset
  S3  the store map of the insert path: which param lands in which entry field (+0 w, +2 w, +4 d,
      +8 d, +0C d), the field derived from the instruction displacement
  S4  the probe (found) test: entry+4 == p4, entry+8 == p5, entry+0(short) == p2, found -> 0x56d404
  S5  the two back-edge loops: bound 0x4b = 75 entries, stride 0x10 in both, exact targets
  S6  the found path = max() on the +2 short and writes EXACTLY ONE WORD there (no owner refresh)
  S7  the eviction law: 1000 for a negative +0 sentinel, prio+100 for prio <= 0, else 20 - prio;
      candidate gate; strict-greater tie rule; no-candidate -> epilogue with ZERO stores
  S8  the assert guard: (p4 ^ p5) & 1, ds:0x985ae8 bit 0x1000 (DIRECT ds: read), pushed string
      0x6914fc; the je target is the post-call fall-through, so the guard cannot skip the insert
  S9  the PE bytes: 0x6914fc = "Bad GOAL", and the sibling name FUN_0056d480 pushes 0x691505 =
      "Bad SITE" -> the binary names the two lists itself, adjacently in one string pool
  S10 adjacency: 0x94ee28 + 75*0x10 == 0x94f2d8 -> GOAL entries 0..74 and SITE entries 75..99 of
      ONE 8380-byte record
  S11 the 50-caller census: push group per site (bounded by call/ret/jcc, else UNATTRIBUTED), the
      arg6 distribution, and a backward DEF-WALK of every non-constant arg6
  S12 who else touches the record windows: every [reg+0x94ee28..0x94ee34] and [reg+0x94f2d8..]
      operand in .text, bucketed by entry-field and read/write
  S13 the single reader of +0C: signed, guarded by test/jl, scaled 9x -> 19x -> <<4 = *304 and used
      as a byte-bit test on [edx+0x95da40] -> +0C is an OWNER INDEX, -1 = unbound
  S14 ds:0x68cbb0, the global 5 arg6 sites walk back to: ref census (reads/writers/inc-style)

RIVALS that FAIL on the printed numbers:
  R1 the 6th arg is another coordinate            (the probe pair is +4/+8; +0C is never compared,
                                                   its single reader scales it *304 as an index)
  R2 the -1 is a priority value                   (priorities live at +2 as SHORTS, written from
                                                   p3; the eviction scores are 1000/100/20-prio)
  R3 the GOAL list is the 25-entry SITE list      (bound 0x4b = 75 here vs 0x19 = 25 there, bases
                                                   0x94ee28 vs 0x94f2d8)
  R4 the list grows past 75 / overflows into SITE (75*0x10 lands EXACTLY on the SITE base)
  R5 a duplicate call refreshes the owner         (the found path stores ONE WORD, at +2)
  R6 the parity/debug guard can suppress the insert (its je target is the fall-through; no ret in
                                                   between - asserted by target and by scan)
  R7 both lists are one concept (one debug name)  (0x6914fc "Bad GOAL" vs 0x691505 "Bad SITE")
  R8 param_1 is a byte offset into one array       (the chain coefficient is 8380 BYTES)
  R9 +0C is write-only dead state                  (1 write, 1 read, and the read gates on <0)
  R10 every caller passes the constant -1          (42/50 do; 8 walk back to registers, 5 of them
                                                   to ds:0x68cbb0; 1 pushes 0x6)

    python3 -u scripts/m309_goal_sink.py        # stdout -> evidence/m309_goal_sink.txt
"""
import bisect
import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m308_site_list as M

ROOT = M.ROOT
GOAL_BASE = 0x94EE28
GOAL_COUNT = 0x4B
ENTRY = 0x10
SITE_BASE = 0x94F2D8
SITE_COUNT = 0x19
RECORD = 0x20BC
FUN = (0x56D350, 0x56D47C)
SITE_FUN = (0x56D480, 0x56D630)
REBUILD = (0x56D690, 0x56D710)
OWNER_GOAL = 0x94EE34
OWNER_READ = 0x559B3E
TABLE_304 = 0x95DA40
OWNER_GLOBAL = 0x68CBB0
STR_GOAL, STR_SITE = 0x6914FC, 0x691505
JCC = M.JCC
DISP = re.compile(r"\+0x(94ee28|94ee2a|94ee2c|94ee30|94ee34|"
                  r"94f2d8|94f2da|94f2dc|94f2e0|94f2e4)\b")


class Out:
    def __init__(self):
        self.lines = []

    def p(self, s=""):
        self.lines.append(s)
        print(s)
        sys.stdout.flush()


def track(reg, lo, hi, seed=None):
    """Integer-affine tracker for ONE register over [lo,hi): returns (coef, const) or None.
    'mov r,[ebp+0x8]' is the symbolic parameter (1, 0). Handles mov imm/reg, shl, add, sub,
    inc, or-imm, and lea with the same expression parser as the M308 engine."""
    val = dict(seed or {})
    val.setdefault(reg, None)
    for a, mn, ops in M.window(lo, hi):
        d = M.split_ops(ops)
        if mn == "mov" and len(d) == 2 and d[0] == reg:
            if re.fullmatch(r"0x[0-9a-f]+", d[1]):
                val[reg] = (0, int(d[1], 16))
            elif d[1] == "ebp+0x8" or d[1] == "[ebp+0x8]":
                val[reg] = (1, 0)
            elif d[1] in val:
                val[reg] = val[d[1]]
            else:
                mm = M.MEM.match(d[1])
                if mm and mm.group(2).strip("[]") == "ebp+0x8":
                    val[reg] = (1, 0)
                else:
                    val[reg] = None
        elif mn == "shl" and len(d) == 2 and d[0] == reg and re.fullmatch(r"0x[0-9a-f]+", d[1]):
            v = val[reg]
            val[reg] = (v[0] << int(d[1], 16), v[1] << int(d[1], 16)) if v else None
        elif mn in ("add", "sub") and len(d) == 2 and d[0] == reg:
            v = val[reg]
            if v is None:
                continue
            if re.fullmatch(r"0x[0-9a-f]+", d[1]):
                q = (0, int(d[1], 16))
            elif d[1] in val and val[d[1]]:
                q = val[d[1]]
            else:
                q = None
            if q:
                s = 1 if mn == "add" else -1
                val[reg] = (v[0] + s * q[0], v[1] + s * q[1])
        elif mn == "lea" and len(d) == 2 and d[0] == reg:
            m2 = re.match(r"^(?:\w+ PTR )?\[(.*)\]$", d[1])
            k, c = M.eval_expr(m2.group(1) if m2 else d[1], val)
            val[reg] = None if k is None else (k, c)
        elif mn == "or" and len(d) == 2 and d[0] == reg and re.fullmatch(r"0x[0-9a-f]+", d[1]):
            val[reg] = None
    return val.get(reg)


def push_group(call_addr):
    """The argument push group of a cdecl call: walk back collecting pushes, STOPPING at any
    call / ret / jcc (a crossed branch or call makes the group unverifiable -> declared None)."""
    i = bisect.bisect_left(M._ORDER, call_addr)
    ps, j, blocked = [], i - 1, False
    while j >= 0 and i - j <= 40:
        a = M._ORDER[j]
        mn, ops = M._INS[a]
        if mn == "push":
            ps.append((a, ops))
            if len(ps) == 6:
                break
        elif mn in ("call", "ret") or mn in JCC:
            blocked = True
            break
        j -= 1
    ps.reverse()
    return ps, blocked


def classify(ops):
    if re.fullmatch(r"0x[0-9a-f]+", ops):
        return "const " + ops
    if ops.startswith("ds:") or "PTR" in ops:
        return "mem " + ops
    if re.fullmatch(r"[a-z][a-z0-9]*", ops):
        return "reg " + ops
    return "other " + ops


def main():
    out = Out()
    M._INS, M._ORDER = M.parse_text()
    M._SPANS = M.load_spans()
    fnrows = M.load_index()
    ins = M._INS
    chk = []

    def A(cid, ok, detail=""):
        chk.append((cid, bool(ok)))
        out.p("  %-5s %s %s" % (cid, "OK " if ok else "RED", detail))

    out.p("M309 static instrument: .text insns %d, functions %d, window %s-%s"
          % (len(M._ORDER), len(fnrows), hex(FUN[0]), hex(FUN[1])))

    # ---------------- S1 scope -------------------------------------------------------------
    out.p("\n[S1] scope")
    row = [l for l in open(M.INDEX) if l.startswith("0x0056d350,")]
    out.p("  index.csv: " + row[0].strip())
    last = [a for a in M._ORDER if a < FUN[1]][-1]
    rets = [a for a in M._ORDER if FUN[0] <= a < FUN[1] and M._INS[a][0] == "ret"]
    out.p("  index row fields: %s" % dict(zip("addr name size_bytes n_insns n_callers n_callees "
                                              "n_strings ok chars shard".split(),
                                              row[0].strip().split(","))))
    A("A1", len(rets) == 2 and rets[-1] == 0x56D47A,
      "2 rets, last at 0x%x (the function ends there; 0x56d47b is padding)" % rets[-1])
    A("A2", int(row[0].split(",")[2]) == FUN[1] - FUN[0] == 299, "size_bytes 299 == span")

    # ---------------- S2 record stride -----------------------------------------------------
    out.p("\n[S2] param_1 -> record byte offset (affine chain, never the C text)")
    for a, mn, ops in M.window(0x56D386, 0x56D3A3):
        out.p("  %s: %s %s" % (hex(a), mn, ops))
    coef = track("edx", 0x56D386, 0x56D39D, seed={})
    out.p("  chain value of edx as (coef_of_p1, const) = %s" % (coef,))
    A("A3", coef == (RECORD, 0), "coefficient == 0x%x == %d bytes/record -> p1 is a RECORD INDEX "
                                 "(R8 fails)" % (RECORD, RECORD))
    base = track("ecx", 0x56D386, 0x56D3A3)
    out.p("  lea ecx,[edx+0x94ee30] -> ecx = %s * p1 + 0x%x" % (base[0], base[1]))
    A("A4", base == (RECORD, GOAL_BASE + 8), "the walk starts at record_base+8 (entry0's +8 slot)")

    # ---------------- S3 store map ---------------------------------------------------------
    out.p("\n[S3] insert-path stores: field from the DISPLACEMENT, param from a backward walk")
    stores = []
    for a, mn, ops in M.window(0x56D43F, 0x56D476):
        if mn != "mov":
            continue
        d = M.split_ops(ops)
        m = M.MEM.match(d[0])
        if not m:
            continue
        disp = DISP.search(m.group(2))
        f = int(disp.group(1), 16) - GOAL_BASE
        w = {"DWORD": "d", "WORD": "w", "BYTE": "b"}[m.group(1)]
        src = d[1]
        slot = None
        for x, mn2, ops2 in reversed(M.window(FUN[0], a)):
            d2 = M.split_ops(ops2)
            if mn2 == "mov" and len(d2) == 2 and d2[0].split()[0].lower() in (
                    src[:3], src[:2].lower(), src):
                mm = M.MEM.match(d2[1])
                if mm and mm.group(2).startswith("ebp+"):
                    slot = int(mm.group(2).split("+")[1], 16)
                    break
        stores.append((a, hex(a), f, w, src, slot))
        out.p("  %s: %-38s field +0x%-2X %s  src=%-3s param slot [ebp+0x%x]"
              % (hex(a), ops, f, w, src, slot or 0))
    want = {(0, "w", 0xC), (2, "w", 0x10), (4, "d", 0x14), (8, "d", 0x18), (0xC, "d", 0x1C)}
    got = {(f, w, s) for _, _, f, w, _, s in stores}
    out.p("  (field,width,param-slot) set = %s" % sorted(got))
    A("A5", got == want, "5 stores cover +0/+2/+4/+8/+0C with the 6 params in order "
                         "(p2,p3,p4,p5,p6)")
    A("A6", len([s for s in stores if s[2] == 0xC]) == 1 and
      [hex(s[0]) for s in stores if s[2] == 0xC] == ["0x56d470"],
      "the +0C (owner) store is exactly ONE instruction, 0x56d470, taking [ebp+0x1c] = p6")

    # ---------------- S4 probe test --------------------------------------------------------
    out.p("\n[S4] probe (is the entry already present?)")
    probe = []
    for a, mn, ops in M.window(0x56D3A3, 0x56D3B5):
        out.p("  %s: %s %s" % (hex(a), mn, ops))
        if mn in ("cmp", "movsx"):
            probe.append((a, mn, ops))
    f4 = "DWORD PTR [ecx-0x4],esi" in ins[0x56D3A3][1]
    A("A7", f4 and ins[0x56D3A8][1] == "DWORD PTR [ecx],edi",
      "entry+4 vs p4 (%s) and entry+8 vs p5 (%s) - the pair the probe matches on"
      % (classify(ins[0x56D3A3][1].split(", ")[1]), classify(ins[0x56D3A8][1].split(", ")[1])))
    A("A8", ins[0x56D3AC][0] == "movsx" and ins[0x56D3B0][1] == "ebx,DWORD PTR [ebp+0xc]",
      "entry+0 is compared as a SIGNED WORD against p2 ([ebp+0xc])")
    A("A9", ins[0x56D3B3][1] == "0x56d404" and M._INS[0x56D3B3][0] == "je",
      "the found-path branch is `je 0x56d404` (target asserted, not mnemonic)")

    # ---------------- S5 loops -------------------------------------------------------------
    out.p("\n[S5] back-edges and bounds")
    back = []
    for a, mn, ops in M.window(*FUN):
        if mn in JCC:
            tgt = ops.strip()
            if re.fullmatch(r"0x[0-9a-f]+", tgt) and int(tgt, 16) <= a:
                back.append((a, mn, tgt))
                out.p("  back-edge %s: %-4s %s  (cmp before it: %s)"
                      % (hex(a), mn, tgt,
                         " ".join("%s %s" % M._INS[x][0:2] for x in
                                  [y for y in M._ORDER if y < a][-1:])))
    A("A10", len(back) == 2 and back[0][2] == "0x56d3a3" and back[1][2] == "0x56d3cc",
      "exactly 2 loops, targets 0x56d3a3 / 0x56d3cc")
    bounds = [(a, ins[a][1]) for a in (0x56D3B9, 0x56D436)]
    out.p("  bound insns: %s" % ["%s: cmp %s" % (hex(a), o) for a, o in bounds])
    A("A11", all(o == "eax,0x4b" or o == "edi,0x4b" for _, o in bounds) and
      ins[0x56D3B9][0] == "cmp" and ins[0x56D436][0] == "cmp",
      "both loops bound at 0x4b = %d entries (R3/R4 fail on this number)" % GOAL_COUNT)
    strides = [a for a, mn, ops in M.window(*FUN) if mn == "add" and ops in ("ecx,0x10",)]
    out.p("  `add ecx,0x10` at %s" % [hex(x) for x in strides])
    A("A12", len(strides) == 2, "both walks step 0x10 = %d bytes/entry" % ENTRY)
    out.p("  immediate inventory of the whole function (unfiltered): %s"
          % sorted({int(m, 16) for _, mn, o in M.window(*FUN) for m in
                    re.findall(r"\b0x([0-9a-f]+)\b", o)}))

    # ---------------- S6 found path = max --------------------------------------------------
    out.p("\n[S6] found path (0x56d404): what does a duplicate do?")
    for a, mn, ops in M.window(0x56D404, 0x56D422):
        out.p("  %s: %s %s" % (hex(a), mn, ops))
    fstores = [(a, mn, ops) for a, mn, ops in M.window(0x56D404, 0x56D422)
               if M.MEM.match(M.split_ops(ops)[0]) if mn.startswith("mov")]
    out.p("  stores on the found path: %s" % ["%s: %s %s" % (hex(a), mn, o)
                                              for a, mn, o in fstores])
    A("A13", len(fstores) == 1 and M.MEM.match(M.split_ops(fstores[0][2])[0]).group(1) == "WORD",
      "exactly ONE store, a WORD -> the owner dword at +0C is NOT refreshed (R5 fails)")
    A("A14", ins[0x56D40C][1] == "edx,DWORD PTR [ebp+0x10]" and
      ins[0x56D416][1] == "0x56d41a" and ins[0x56D418][1] == "eax,edx" and
      ins[0x56D41C][1] == "WORD PTR [ecx],ax",
      "max(): cmp old,p3 / `jg 0x56d41a` keeps the old / else mov eax,p3 / store the WORD at +2")
    A("A15", M.window(0x56D404, 0x56D422) and [a for a, mn, _ in M.window(0x56D404, 0x56D422)
                                               if mn == "ret"] == [0x56D421],
      "the found path rets at 0x56d421 without reaching the insert block")

    # ---------------- S7 eviction law ------------------------------------------------------
    out.p("\n[S7] eviction law (the do-loop at 0x56d3cc)")
    for a, mn, ops in M.window(0x56D3CC, 0x56D3E2):
        out.p("  %s: %s %s" % (hex(a), mn, ops))
    A("A16", ins[0x56D3D3][1] == "0x56d3dd" and M._INS[0x56D3D3][0] == "jl",
      "a NEGATIVE +0 short (the empty sentinel) is a candidate -> `jl 0x56d3dd`")
    A("A17", ins[0x56D3D8][1] == "ebx,DWORD PTR [ebp+0x10]" and ins[0x56D3DB][1] == "0x56d432"
      and M._INS[0x56D3DB][0] == "jge",
      "a non-empty entry is skipped when prio >= p3 -> `jge 0x56d432` (the next entry)")
    A("A18", ins[0x56D3E6][1] == "ebx,0x3e8" and
      [x[0] for x in M.window(0x56D3DD, 0x56D3EC)] == [0x56D3DD, 0x56D3DF, 0x56D3E5, 0x56D3E6],
      "score 1000 for an empty slot via setge/dec/and 0x3e8, four insns, no branch")
    A("A19", ins[0x56D425][1] == "eax,0x64" and ins[0x56D3FB][1] == "eax,0x14" and
      ins[0x56D400][1] == "eax,ebx", "prio+100 when prio <= 0, else 0x14-prio (20-prio)")
    A("A20", ins[0x56D42B][1] == "0x56d432" and M._INS[0x56D42B][0] == "jle" and
      ins[0x56D428][1] == "eax,DWORD PTR [ebp+0x8]",
      "strictly-greater wins (ties keep the FIRST index): `jle 0x56d432` on the best-score cmp")
    A("A21", ins[0x56D43D][1] == "0x56d476" and M._INS[0x56D43D][0] == "jl" and
      ins[0x56D43B][1] == "esi,esi",
      "no candidate -> `test esi,esi` / `jl 0x56d476` skips the insert block entirely")
    nostore = [(a, mn) for a, mn, ops in M.window(0x56D476, 0x56D47B)
               if M.MEM.match(M.split_ops(ops)[0]) if mn == "mov"]
    insblock = [(a, mn, ops) for a, mn, ops in M.window(0x56D43F, 0x56D476)
                if mn == "mov" and M.MEM.match(M.split_ops(ops)[0])]
    out.p("  stores in the epilogue 0x56d476-0x56d47a: %d ; in the insert block: %d"
          % (len(nostore), len(insblock)))
    A("A22", len(nostore) == 0 and len(insblock) == 5,
      "the no-candidate epilogue is store-free over exactly the 5 insert stores")
    A("A23", ins[0x56D3C0][1] == "esi,0xffffffff" and ins[0x56D3BE][1] == "edi,edi",
      "the eviction scan starts best-index = 0 and best-score sentinel esi = -1 "
      "(so `test esi,esi;jl` really means 'no candidate')")

    # ---------------- S8 the debug guard ---------------------------------------------------
    out.p("\n[S8] the (p4^p5) parity guard + the debug flag")
    for a, mn, ops in M.window(0x56D35C, 0x56D386):
        out.p("  %s: %s %s" % (hex(a), mn, ops))
    A("A24", ins[0x56D35C][1] == "eax,esi" and ins[0x56D35E][1] == "eax,edi" and
      ins[0x56D360][1] == "al,0x1",
      "guard operand identity: esi=p4 and edi=p5 are XORed, then `test al,0x1`")
    direct = [(a, mn, ops) for a, mn, ops in M.window(*FUN)
              if re.search(r"\bds:", ops)]
    out.p("  direct ds: accesses in the function: %s" % ["%s: %s %s" % (hex(a), mn, o)
                                                         for a, mn, o in direct])
    A("A25", len(direct) == 1 and direct[0][0] == 0x56D364 and
      direct[0][1] == "mov" and direct[0][2] == "eax,ds:0x985ae8" and
      ins[0x56D369][1] == "ah,0x10",
      "the ONLY out-of-frame memory is a DIRECT read of ds:0x985ae8, masked `test ah,0x10` "
      "= bit 12")
    A("A26", ins[0x56D362][1] == "0x56d386" and ins[0x56D36C][1] == "0x56d386" and
      not [a for a, mn, _ in M.window(0x56D362, 0x56D386) if mn == "ret"],
      "both je targets are 0x56d386 = the instruction after the call cleanup, and no ret lies "
      "between -> the guard cannot suppress the insert (R6 fails)")
    A("A27", ins[0x56D379][1] == "0x6914fc" and ins[0x56D37E][1] == "0x530490",
      "the assert pushes 0x6914fc and calls 0x530490 (the report/format sink)")

    # ---------------- S9 the binary names it ----------------------------------------------
    out.p("\n[S9] the two debug strings, read from the PE bytes")
    blob = open(M.EXE, "rb").read()
    _ib, secs = M.pe_sections(blob)

    def cstr(va):
        off, nm = M.va2off(secs, va)
        return blob[off:off + 32].split(b"\0")[0].decode("latin1", "replace") if off else "?"
    pushes_site = [a for a, mn, ops in M.window(*SITE_FUN)
                   if mn == "push" and ops.startswith("0x69")]
    out.p("  0x6914fc -> %r   (pushed at 0x56d379 by FUN_0056d350)" % cstr(STR_GOAL))
    out.p("  0x691505 -> %r   (pushed by FUN_0056d480 at %s)"
          % (cstr(STR_SITE), [hex(x) for x in pushes_site]))
    A("A28", cstr(STR_GOAL) == "Bad GOAL" and cstr(STR_SITE) == "Bad SITE" and
      len(pushes_site) == 1 and M._INS[pushes_site[0]][1] == "0x691505",
      "the binary names the two lists adjacently in one string pool: Bad GOAL here, "
      "Bad SITE in the 25-entry insert (R7 fails)")

    # ---------------- S10 adjacency --------------------------------------------------------
    out.p("\n[S10] one record, two sub-lists")
    out.p("  0x94ee28 + 75*0x10 = 0x%x ; FUN_0056d480's list base = 0x%x" %
          (GOAL_BASE + GOAL_COUNT * ENTRY, SITE_BASE))
    A("A29", GOAL_BASE + GOAL_COUNT * ENTRY == SITE_BASE and SITE_COUNT == 25,
      "GOAL entries 0..74 then SITE entries 75..99 of the SAME 8380-byte record -> "
      "100 x 16-B entries, no overflow (R4 fails)")
    out.p("  SITE record end = 0x%x (0x94f2d8 + 25*0x10); record window = [0x94ee28, 0x%x)"
          % (SITE_BASE + SITE_COUNT * ENTRY, GOAL_BASE + 100 * ENTRY))
    A("A30", SITE_BASE + SITE_COUNT * ENTRY == GOAL_BASE + 100 * ENTRY,
      "the two sub-lists tile 100 entries exactly")

    # ---------------- S11 caller census ----------------------------------------------------
    out.p("\n[S11] caller census (every `call 0x56d350` in .text)")
    calls = [a for a in M._ORDER if ins[a][0] == "call" and ins[a][1].startswith("0x56d350")]
    out.p("  %-9s %-16s %-9s %-9s %-9s %-9s" % ("site", "caller", "arg1", "arg2", "arg5", "arg6"))
    dist, unattr, arg6reg = {}, [], {}
    for c in calls:
        ps, blocked = push_group(c)
        f = M.contain(fnrows, c)
        if len(ps) != 6 or blocked:
            unattr.append((c, f, len(ps), blocked))
            out.p("  %-9s %-16s UNATTRIBUTED (pushes=%d, blocked_by_branch_or_call=%s)"
                  % (hex(c), f, len(ps), blocked))
            continue
        a1, a2, a3, a4, a5, a6 = [x[1] for x in ps]
        dist[classify(a6)] = dist.get(classify(a6), 0) + 1
        if not a6.startswith("0x"):
            lo, hi, _n = M.span_of(c)
            srcs, _ch = M.def_globals(ps[-1][0], a6, lo, hi)
            arg6reg[c] = (a6, sorted(hex(s) if isinstance(s, int) else str(s) for s in srcs))
        out.p("  %-9s %-16s %-9s %-9s %-9s %-9s"
              % (hex(c), f, classify(a1), classify(a2), classify(a5), classify(a6)))
    out.p("  sites %d | attributed %d | unattributed %d"
          % (len(calls), len(calls) - len(unattr), len(unattr)))
    out.p("  arg6 distribution: %s" % sorted(dist.items(), key=lambda x: (-x[1], x[0])))
    out.p("  non-constant arg6 -> def-walk source(s):")
    for c, v in sorted(arg6reg.items()):
        out.p("    %s  reg=%-4s srcs=%s" % (hex(c), v[0], v[1]))
    nidx = [c for c, v in arg6reg.items() if "0x68cbb0" in v[1]]
    out.p("  sites whose arg6 walks back to ds:0x68cbb0: %d -> %s" % (len(nidx),
                                                                      [hex(x) for x in sorted(nidx)]))
    A("A31", len(calls) == 50 and int(row[0].split(",")[4]) == 50,
      "50 call sites in the dump == index.csv n_callers=50")
    A("A32", dist.get("const 0xffffffff", 0) == 42 and
      dist.get("const 0x6", 0) == 1 and sum(v for k, v in dist.items()
                                            if k.startswith("reg ")) == 7,
      "arg6 = -1 at 42/50 sites, 0x6 at 1, a register at 7 -> NOT a uniform constant (R10 fails)")
    A("A33", len(nidx) == 5 and all(v[1] == ["0x68cbb0"] for c, v in arg6reg.items()
                                    if c in nidx),
      "5 of the register sites provably LOAD ds:0x68cbb0 into arg6 (def-walk closed, not proximity)")
    A("A34", 0x56D590 in calls and 0x56D6F8 in calls,
      "both in-family sites are in the census (0x56d590 in FUN_0056d480, 0x56d6f8 in "
      "FUN_0056d690)")
    mir = [c for c in calls if M.contain(fnrows, c) in ("FUN_0056d480", "FUN_0056d690")]
    out.p("  in-family sites (mirror + rebuild): %s" % [(hex(c), M.contain(fnrows, c)) for c in mir])
    A("A35", len(mir) == 2 and all(
        push_group(c)[0][-1][1] == "0xffffffff" for c in mir if len(push_group(c)[0]) == 6),
      "both the SITE->GOAL mirror and the rebuild broadcast pass arg6 = -1 (unbound owner)")

    # ---------------- S12 window ref census ------------------------------------------------
    out.p("\n[S12] every [reg+DISP] / ds: access of the two sub-lists in .text")
    owner_w, owner_r, fields = [], [], {}
    for a in M._ORDER:
        mn, ops = ins[a]
        for tok in M.split_ops(ops):
            m = M.MEM.match(tok) or re.match(r"^(?:DWORD|WORD|BYTE) PTR ds:(0x[0-9a-f]+)$", tok)
            raw = m.group(2) if m and m.lastindex and m.lastindex >= 2 and m.group(2) else \
                (m.group(1) if m else None)
            if not raw:
                continue
            hits = DISP.findall(raw)
            for h in hits:
                d = int(h, 16)
                is_w = mn in ("mov", "movzx", "movbe", "xchg") and tok is M.split_ops(ops)[0] or \
                    mn in ("mov",) and tok is M.split_ops(ops)[0]
                win, field = ("GOAL", d - GOAL_BASE) if d < 0x94f000 else \
                             ("SITE", d - SITE_BASE)
                key = (win, field % ENTRY, {"DWORD": "d", "WORD": "w", "BYTE": "b"}[
                    tok.split()[0] if tok.split()[0] in ("DWORD", "WORD", "BYTE") else "DWORD"])
                fields[key] = fields.get(key, [0, 0])
                fields[key][0 if is_w else 1] += 1
                if win == "GOAL" and field % ENTRY == 0xC:
                    (owner_w if is_w else owner_r).append((a, mn, ops))
    for k in sorted(fields):
        out.p("  %-6s field +0x%-2X %s : writes %d, reads %d" % (k[0], k[1], k[2], k[3] if False else
                                                                  fields[k][0], fields[k][1]))
    out.p("  GOAL +0C writes: %s" % [(hex(a), o) for a, _, o in owner_w])
    out.p("  GOAL +0C reads: %s" % [(hex(a), o) for a, _, o in owner_r])
    A("A36", [a for a, _, _ in owner_w] == [0x56D470] and [a for a, _, _ in owner_r] == [OWNER_READ],
      "the owner dword has EXACTLY 1 writer (0x56d470, inside FUN_0056d350) and 1 reader "
      "(0x559b3e) in all of .text (R9 fails)")

    # ---------------- S13 what the owner index indexes ------------------------------------
    out.p("\n[S13] the single reader of +0C (0x559b3e, in %s)" % M.contain(fnrows, OWNER_READ))
    for a, mn, ops in M.window(0x559B30, 0x559B78):
        out.p("  %s: %s %s" % (hex(a), mn, ops))
    seed = {"eax": (1, 0)}
    chain = {}
    for reg in ("ecx", "edx"):
        chain[reg] = None
    v = dict(seed)
    for a, mn, ops in M.window(OWNER_READ + 6, 0x559B54):
        d = M.split_ops(ops)
        if mn in ("lea", "shl") and d[0] in ("ecx", "edx"):
            if mn == "shl":
                p = v[d[0]]
                v[d[0]] = (p[0] << int(d[1], 16), p[1] << int(d[1], 16)) if p else None
            else:
                m2 = re.match(r"^(?:\w+ PTR )?\[(.*)\]$", d[1])
                k, c = M.eval_expr(m2.group(1), v)
                v[d[0]] = None if k is None else (k, c)
            out.p("    -> after %s: %s = %s * (owner)" % (mn, d[0], v[d[0]]))
    scale = v.get("edx")
    A("A37", scale == (304, 0), "the owner is scaled by %d (9x -> 19x -> <<4) -> a 304-byte-stride "
                                "table (R1/R2 fail: not a coordinate, not a priority)"
      % (scale[0] if scale else None))
    A("A38", ins[0x559B44][1] == "eax,eax" and M._INS[0x559B44][0] == "test" and
      ins[0x559B49][1] == "0x559b74" and M._INS[0x559B49][0] == "jl",
      "the reader is SIGNED and guarded: `test eax,eax` / `jl 0x559b74` -> a NEGATIVE owner "
      "(the -1) is NEVER used as an index")
    use = [(a, mn, ops) for a, mn, ops in M.window(0x559B54, 0x559B74) if "0x95da40" in ops]
    out.p("  uses of the scaled index: %s" % [(hex(a), "%s %s" % (mn, o)) for a, mn, o in use])
    A("A39", len(use) == 1 and use[0][1] == "test" and "0x20" in use[0][2],
      "exactly one use: `test BYTE PTR [edx+0x95da40],0x20` -> the owner selects a RECORD in the "
      "304-B table at 0x95da40 and reads its bit 0x20")
    A("A40", ins[0x559B30][1].startswith("WORD PTR [edi+0x94ee28],0x9"),
      "the read is gated on the SAME entry's +0 short == 9 (a kind value), so the owner field is "
      "consulted only for entries of that kind")

    # ---------------- S14 ds:0x68cbb0 ------------------------------------------------------
    out.p("\n[S14] ds:0x68cbb0, the global 5 arg6 sites load")
    refs = []
    for a in M._ORDER:
        mn, ops = ins[a]
        if "0x68cbb0" in ops:
            d = M.split_ops(ops)
            w = bool(d and mn in ("mov", "add", "sub", "inc", "dec", "and", "or", "movzx") and
                     M.MEM.match(d[0]) and "0x68cbb0" in d[0])
            refs.append((a, mn, ops, w))
    wr = [r for r in refs if r[3]]
    out.p("  refs %d | writers %d | readers %d" % (len(refs), len(wr), len(refs) - len(wr)))
    for a, mn, ops, w in refs[:12]:
        out.p("    %s: %-6s %-34s %s" % (hex(a), mn, ops, "WRITE" if w else "read"))
    incof = [r for r in wr if r[1] in ("inc", "dec")]
    out.p("  inc/dec-style writers: %d ; writers in FUN_004eb6f0/FUN_004ebef0: %s"
          % (len(incof), sorted({M.contain(fnrows, r[0]) for r in wr})))
    A("A41", len(refs) > 0 and len(wr) > 0,
      "ds:0x68cbb0 is a real global with %d refs and %d writers -> arg6 is not always a literal"
      % (len(refs), len(wr)))

    # ---------------- rivals ---------------------------------------------------------------
    out.p("\n[R] rivals, decided by the numbers above")
    rv = [("R1 arg6 is a coordinate", scale == (304, 0) and len(owner_r) == 1),
          ("R2 -1 is a priority", all(s[2] == 0x10 for s in stores if s[2] == 0x10) and
           "0x3e8" in ins[0x56D3E6][1]),
          ("R3 the GOAL list IS the 25-entry SITE list", GOAL_COUNT == SITE_COUNT or
           GOAL_BASE == SITE_BASE),
          ("R4 the GOAL list overflows into SITE", (GOAL_BASE + GOAL_COUNT * ENTRY) != SITE_BASE),
          ("R5 a duplicate refreshes the owner", len(fstores) > 1),
          ("R6 the parity guard can suppress the insert",
           bool([a for a, mn, _ in M.window(0x56D362, 0x56D386) if mn == "ret"]) or
           ins[0x56D362][1] != "0x56d386"),
          ("R7 one debug name for both lists", cstr(STR_GOAL) == cstr(STR_SITE)),
          ("R8 param_1 is a byte offset", coef != (RECORD, 0)),
          ("R9 +0C is write-only", len(owner_r) == 0),
          ("R10 every caller passes -1", dist.get("const 0xffffffff", 0) == 50)]
    for name, holds in rv:
        out.p("  %-46s %s" % (name, "HOLDS (bad)" if holds else "REFUTED"))
        chk.append(("RIVALS-" + name.split()[0], not holds))

    bad = 0
    out.p("\n[checks]")
    for cid, good in chk:
        if not good:
            bad += 1
            out.p("  %-5s RED" % cid)
    out.p("\n%d/%d checks OK" % (len(chk) - bad, len(chk)))
    out.p("table sha %s" % hashlib.sha256("\n".join(out.lines).encode()).hexdigest()[:16])
    if bad:
        print("RESULT: FAIL (%d checks red)" % bad, file=sys.stderr)
        return 1
    print("RESULT: PASS M309 FUN_0056d350 = the GOAL-list insert of the block record")
    return 0


if __name__ == "__main__":
    sys.exit(main())
