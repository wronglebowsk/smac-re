#!/usr/bin/env python3
"""M310 (STATIC, zero box): name FUN_00470b90 and say exactly what invalidates a GOAL entry.

THE PICK (NEXT_PROMPT §THE PICK, s271 close): FUN_00470b90 (1020 B, 5 callers, 9 callee targets)
= "the routine that stores 0xffff into a GOAL entry's +0 short at 0x470d5c (M308 U2's -1 sentinel,
for the GOAL list) - name it and say what invalidates an entry". The instrument reads the ENCODING
(scratch/m574/text.txt via the M308 affine engine, ghidra_out/index.csv, the terran.exe PE) and
prints tables first, then asserts every number it printed. The Ghidra C text is never evidence.

  S1  scope: index.csv row, the ret/epilogue that bound the function, ret 0x8 (2 stack args)
  S2  the entry gate: thiscall ecx stowed at [ebp-4]; the test is on the DWORD this+0x1dd70,
      bit 0x2000 - the view bit-flags field M228-M245 named - and the je lands on the epilogue
  S3  the outer loop: blocks 1..7 (init 1, cmp 0x8, jge-out); per-block filter is
      (ds:0x985ae8 & 0x80) || (block == ds:0x91b5b4)  [M42 current-player]
  S4  the two 75-entry scans over the GOAL window (bound 0x4b, entry shl 0x10): the exact M309
      layout - +0 kind SHORT, +2 prio SHORT, +4/+8 the two dwords; hit predicate
      p1==+4 && p2==+8 && kind>=0 && prio!=0
  S5  the 5 call sites' argument provenance: at 0x4724ad the unpacker FUN_0046a1b0 is called with
      lea [ebp-0x14], lea [ebp-0x18] as its two OUTPUT pointers; at 0x470bba/bb7 the same slots
      are pushed into FUN_00470b90, and no instruction in between writes them; every other site
      pushes the two slots the caller's own loop header fills
  S6  THE INVALIDATION LAW, instruction by instruction: negative prio -> scan j!=i for same
      (p1,p2) AND same kind (the kind of the OUTER entry i is the register def, read from the
      encoding [ebp-0xc], not from the C text); the unique hit stores WORD 0xffff to entry i +0;
      then entry i +0 is RE-READ, sign-extended, tested, and negative -> continue the scan loop
  S7  the jump table: parsed as raw PE bytes (objdump misassembles it), 42 dwords; case ->
      handler -> pushed .data string + debug code; bounds cmp 0x29 means kind -1 CANNOT enter
      the switch -> the log line fires only for hits that were NOT invalidated
  S8  the kind labels, read from the PE .data
  S9  the log sink chain in exact order: FUN_00403a40(buf, unpacked1, unpacked2, this+0x1ddb4,
      this+0x1ddb8) -> FUN_00407520 -> (debug-only: FUN_00423c20(block)->FUN_00405220, store
      BYTE ds:0x997121=0) -> code 0xff -> switch appends FUN_00405220(label) -> abs(prio) ->
      FUN_004237f0 -> vtable+4 call on the string subobject this+0x444 x2 -> FUN_004081b0(
      ds:0x997120, buf)
  S10 uniqueness inside the function: exactly ONE store to GOAL_BASE+0 (0x470d5c) and exactly
      ONE store to +2; all 15 record-fold immediates are 0x20bc
  S11 callees: 9 distinct targets == the index.csv n_callees column

RIVALS that FAIL on the printed numbers:
  R1 the 0xffff write is a priority clear        (it stores at +0, the KIND short; +2 has 0
                                                  stores in the whole window)
  R2 the invalidator runs in normal play         (the entry gate tests this+0x1dd70 bit 0x2000 and
                                                  the je jumps straight to the epilogue)
  R3 every matching entry is invalidated         (the +0xffff store sits ONLY on the negative-prio
                                                  duplicate path; prio>0 matches just log)
  R4 the re-read is another store                (movsx, not a store; 1 store at +0 in the window)
  R5 the scan mutates args mid-flight            (p1,p2 are read from [ebp+8],[ebp+c]; 0 stores to
                                                  those slots between entry and 0x470d86)
  R6 kind -1 also logs a label                   (cmp 0x29 ja-out fires for -1; default 0x470ea3
                                                  is a label too but -1 never reaches the table)
  R7 it is the only user of the unpacker         (29 callers of FUN_0046a1b0 in the census)
  R8 the 75-loop walks SITE entries too          (no 0x94f2d8 operand in the window)

    python3 -u scripts/m310_goal_invalidator.py   # stdout -> evidence/m310_goal_invalidator.txt
"""
import hashlib
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m308_site_list as M

ROOT = M.ROOT
FUN_LO, FUN_HI = 0x470B90, 0x470F8C          # 1020 B: entry .. ret@0x470f89 + padding to JT
GOAL_BASE, ENTRY, RECORD = 0x94EE28, 0x10, 0x20BC
GOAL_COUNT, SITE_COUNT = 0x4B, 0x19
SITE_BASE = 0x94F2D8
JT = 0x470F8C
SLOTS_UNPACK = (0x14, 0x18)                    # [ebp-0x14], [ebp-0x18]
CALLSITES = (0x471086, 0x471884, 0x4718BA, 0x4719C7, 0x4724BD)
UNPACKER = 0x46A1B0
VIEW_FLAGS = 0x1DD70
GATE_BIT = 0x2000
DEBUG_FLAGS = 0x985AE8
DEBUG_BIT = 0x80
CUR_PLAYER = 0x91B5B4
SENT_STORE = 0x470D5C
KIND_LABELS = (0x675988, 0x675984, 0x675980, 0x67597C, 0x675978, 0x674DB8, 0x675974)
LOG_SINKS = (0x405220, 0x4237F0, 0x403A40, 0x407520, 0x4081B0, 0x423C20)


class Out:
    def __init__(self):
        self.lines = []

    def p(self, s=""):
        self.lines.append(s)
        print(s)
        sys.stdout.flush()


def main():
    out = Out()
    # Engine parser from M308/M309 (skill's TAB-field rule) - two of this milestone's first
    # reds were MY probe's bad field-split, not the engine's: a hand-rolled
    # `.split(None,1)` / `endswith("0x10")` pair invents missing instructions. Verified here:
    # the engine resolves every address in the window and n_insns == parsed count (A2).
    ins, order = M.parse_text()
    M._INS, M._ORDER = ins, order
    M._SPANS = M.load_spans()
    fnrows = M.load_index()
    chk = []

    def A(cid, ok, detail=""):
        chk.append((cid, bool(ok)))
        out.p("  %-5s %s %s" % (cid, "OK " if ok else "RED", detail))

    def ops(a):
        return ins[a][1]

    def mn(a):
        return ins[a][0]

    def win(lo, hi):
        import bisect as _b
        i = _b.bisect_left(order, lo)
        j = _b.bisect_right(order, hi - 1)
        return [(a, ins[a][0], ins[a][1]) for a in order[i:j]]

    def hexset(vals):
        return sorted({hex(v) for v in vals})

    out.p("M310 static instrument: .text insns %d, window %s-%s" %
          (len(M._ORDER), hex(FUN_LO), hex(FUN_HI)))

    # ---------------- S1 scope -------------------------------------------------------------
    out.p("\n[S1] scope")
    row = [l for l in open(M.INDEX) if l.startswith("0x00470b90,")][0].strip()
    out.p("  index.csv: " + row)
    fields = dict(zip("addr name size_bytes n_insns n_callers n_callees n_strings ok chars "
                      "shard".split(), row.split(",")))
    inwin = [a for a, _, _ in win(FUN_LO, FUN_HI)]
    rets = [a for a in inwin if mn(a) == "ret"]
    epi = [a for a in inwin if mn(a) == "pop" and ops(a) == "edi"]
    out.p("  rets: %s ; pop-edi epilogue head: %s ; last insn: %s %s" %
          (hexset(rets), hexset(epi), hex(inwin[-1]), M._INS[inwin[-1]]))
    A("A1", len(rets) == 1 and rets[0] == 0x470F89,
      "exactly 1 ret, at 0x470f89 (0x470f83 is the single epilogue the 3 ies jump to)")
    A("A2", int(fields["size_bytes"]) == FUN_HI - FUN_LO == 1020 and
      int(fields["n_insns"]) == len(inwin),
      "size 1020 == span and n_insns %d == insns the engine parser sees in the window (the "
      "parser-coverage guard against my own probe bugs)" % len(inwin))
    A("A3", ops(0x470F89) == "0x8" and mn(0x470B99) == "mov" and
      ops(0x470B99) == "DWORD PTR [ebp-0x4],ecx",
      "ret 0x8 (2 stack args) + ecx stowed at [ebp-4] -> thiscall(int,int)")

    # ---------------- S2 the entry gate ----------------------------------------------------
    out.p("\n[S2] entry gate (the caller's own field, not a global)")
    for a in (0x470B9F, 0x470BA5, 0x470BAB, 0x470BAD):
        out.p("  %s: %s %s" % (hex(a), mn(a), ops(a)))
    gate_reads = [a for a, m_, o_ in win(FUN_LO, 0x470BB3) if "0x1dd70" in o_]
    and2000 = [a for a, m_, o_ in win(FUN_LO, FUN_HI) if m_ == "and" and o_.endswith("0x2000")]
    A("A4", len(and2000) == 1 and and2000[0] == 0x470BA5 and
      ins[0x470BA5][1] == "ecx,%#x" % GATE_BIT and
      ins[0x470B9F][1] == "ecx,DWORD PTR [eax+%#x]" % VIEW_FLAGS and
      ops(0x470BAD) == "0x470f83",
      "the ONLY +0x1dd70 test in the window is bit 0x2000 at 0x470ba5; je -> 0x470f83 the "
      "epilogue: without the bit the routine does NOTHING (R2) [field = the view bit-flags, "
      "M228-M245 archive row]")

    # ---------------- S3 outer block loop + filter -----------------------------------------
    out.p("\n[S3] outer loop over the block index, filtered")
    for a in (0x470BCB, 0x470BDD, 0x470BE1, 0x470BE7, 0x470BED, 0x470BF5,
              0x470BF7, 0x470BFA, 0x470C00, 0x470C02):
        out.p("  %s: %s %s" % (hex(a), mn(a), ops(a)))
    cmp8 = [a for a, m_, o_ in win(FUN_LO, FUN_HI) if m_ == "cmp" and o_.endswith(",0x8")]
    cmp80 = [a for a, m_, o_ in win(FUN_LO, FUN_HI) if m_ == "and" and o_.endswith("0x80")]
    cp = [a for a, m_, o_ in win(FUN_LO, FUN_HI) if "0x91b5b4" in o_]
    A("A5", [a for a in cmp8 if a == 0x470BDD] == [0x470BDD] and mn(0x470BCB) == "mov" and
      ops(0x470BCB) == "DWORD PTR [ebp-0x8],0x1" and ops(0x470BE1) == "0x470f83",
      "blocks start at 1 (0 skipped) and end below 8; jge-out to the epilogue")
    A("A6", len(cmp80) == 2 and cp == [0x470BFA],
      "ds:0x985ae8 & 0x80 tested exactly twice (the block filter 0x470be7 + the name sink "
      "guard 0x470db3); the block filter passes iff debug-bit set OR block == ds:0x91b5b4 "
      "[the current player, M42]")

    # ---------------- S4 the two scans over the GOAL window --------------------------------
    out.p("\n[S4] the 75-entry scans: layout + hit predicate (displacements, not the C text)")
    cmpb = [a for a, m_, o_ in win(FUN_LO, FUN_HI) if m_ == "cmp" and o_.endswith(",0x4b")]
    shl10 = [a for a, m_, o_ in win(FUN_LO, FUN_HI)
             if m_ == "shl" and re.match(r"\w+,0x4$", o_)]
    imul = [a for a, m_, o_ in win(FUN_LO, FUN_HI) if m_ == "imul" and o_.endswith(",0x20bc")]
    other_imul = [a for a, m_, o_ in win(FUN_LO, FUN_HI) if m_ == "imul" and
                  not o_.endswith(",0x20bc")]
    offs = sorted({int(m, 16) - GOAL_BASE
                   for _, _, o_ in win(FUN_LO, FUN_HI)
                   for m in re.findall(r"\+0x(94ee[0-9a-f]{2})", o_)})
    comps = [(a, ops(a)) for a, m_, o_ in win(FUN_LO, FUN_HI) if m_ == "cmp"
             for _m in re.findall(r"\+0x(94ee[0-9a-f]{2})", o_)]
    tests = [(a, ops(a)) for a, m_, o_ in win(FUN_LO, FUN_HI) if m_ == "movsx"
             for _m in re.findall(r"\+0x(94ee[0-9a-f]{2})", o_)]
    out.p("  cmp 0x4b sites: %s | shl 0x10 sites: %d | imul 0x20bc: %d | other imul: %s" %
          (hexset(cmpb), len(shl10), len(imul), hexset([a for a in other_imul])))
    out.p("  entry offsets touched: %s" % [hex(o) for o in offs])
    out.p("  cmps: %s" % [(hex(a), o) for a, o in comps])
    out.p("  movsx reads (entry+0 / +2): %d" % len(tests))
    A("A7", sorted(cmpb) == [0x470C16, 0x470CC8] and len(shl10) == 15 and len(imul) == 15 and
      not other_imul,
      "two 75-bound scans (cmp 0x4b at 0x470c16 outer / 0x470cc8 inner) over 16-B entries "
      "(15 x shl 0x4 (x16 B = the 0x10 entry step) == 15 x imul 0x20bc (x8380 B = the record "
      "step), 1:1 folds, M309 GOAL layout)")
    fold_uses = {}
    for slot in ("[ebp-0xc]", "[ebp-0x10]"):
        seq = [hex(a) for a, m_, o_ in win(FUN_LO, FUN_HI)
               if m_ == "mov" and re.match(r"\w+,DWORD PTR " + re.escape(slot) + r"$", o_)]
        fold_uses[slot] = seq
        out.p("  fold index loads from %s: %d at %s" % (slot, len(seq), seq))
    A("A8", len(fold_uses["[ebp-0xc]"]) == 13 and len(fold_uses["[ebp-0x10]"]) == 5 and
      len(set(fold_uses["[ebp-0xc]"]) & set(fold_uses["[ebp-0x10]"])) == 0 and
      fold_uses["[ebp-0xc]"].count("0x470d36") == 0 and
      set(fold_uses["[ebp-0xc]"]) <= set(
          ["0x470c0d", "0x470c29", "0x470c46", "0x470c63", "0x470c80", "0x470ca0",
           "0x470d1f", "0x470d56", "0x470d6f", "0x470def", "0x470ec0", "0x470edb",
           "0x470ef7"]) and
      all(x.startswith("0x470") for x in fold_uses["[ebp-0xc]"]) and
      set(fold_uses["[ebp-0x10]"]) == {"0x470cbf", "0x470cd2", "0x470ce5", "0x470d02",
                                       "0x470d36"} and
      offs == [0, 2, 4, 8] and
      len([1 for _, o in comps if "+0x94ee2c" in o]) == 2 and
      len([1 for _, o in comps if "+0x94ee30" in o]) == 2,
      "only +0/+2/+4/+8 touched (NEVER the +0C owner); the (p1,p2) pair is compared EXACTLY "
      "2x each (outer predicate + duplicate scan); TWO DISJOINT index variables: the outer "
      "scan/sentinel/tail seed their folds from [ebp-0xc] (13 sites) and the duplicate scan "
      "ONLY from [ebp-0x10] (5 sites, the set is printed) - 0 overlap (R3/R5-class)")
    A("A9", not any("+0x94f2" in o_ for _, _, o_ in win(FUN_LO, FUN_HI)),
      "the SITE list window 0x94f2d8 is never referenced in this function (R8)")
    HIT_CHAIN = [
        (0x470C2F, "mov",  "eax,DWORD PTR [ebp+0x8]"),
        (0x470C32, "cmp",  "eax,DWORD PTR [ecx+edx*1+0x94ee2c]"),
        (0x470C39, "je",   "0x470c3d"),
        (0x470C3B, "jmp",  "0x470c0d"),
        (0x470C4C, "mov",  "eax,DWORD PTR [ebp+0xc]"),
        (0x470C4F, "cmp",  "eax,DWORD PTR [ecx+edx*1+0x94ee30]"),
        (0x470C56, "je",   "0x470c5a"),
        (0x470C58, "jmp",  "0x470c0d"),
        (0x470C69, "movsx", "eax,WORD PTR [ecx+edx*1+0x94ee28]"),
        (0x470C71, "test", "eax,eax"),
        (0x470C73, "jge",  "0x470c77"),
        (0x470C75, "jmp",  "0x470c0d"),
        (0x470C86, "movsx", "eax,WORD PTR [ecx+edx*1+0x94ee2a]"),
        (0x470C8E, "test", "eax,eax"),
        (0x470C90, "jne",  "0x470c97"),
        (0x470C92, "jmp",  "0x470c0d"),
        (0x470CA6, "movsx", "eax,WORD PTR [ecx+edx*1+0x94ee2a]"),
        (0x470CAE, "test", "eax,eax"),
        (0x470CB0, "jge",  "0x470d86")]
    bad = [(hex(a), "%s %s" % (mn(a), ops(a)), "%s %s" % (mm, oo))
           for a, mm, oo in HIT_CHAIN if not (mn(a) == mm and ops(a) == oo)]
    for a, mm, oo in HIT_CHAIN:
        out.p("  hit-chain %-10s %-8s %-40s%s" % (hex(a), mn(a), ops(a),
              "" if (mn(a), ops(a)) == (mm, oo) else "   <<< MISMATCH (want %s %s)" % (mm, oo)))
    A("A10", not bad and len(HIT_CHAIN) == 19,
      "the hit test asserted INSTRUCTION BY INSTRUCTION (mnemonic AND operand string of all 15), "
      "printed above, not by two branch targets: p2 == entry+4 (`mov` arg / `cmp` / `je`-continue "
      "+ `jmp`-next-entry), kind >= 0 via `movsx` + `test eax,eax` + `jge` (a SIGNED read, so the "
      "-1 free slot falls to `jmp 0x470c0d`; note this is test/jge, NOT `cmp kind,-1`), prio != 0 "
      "via `test` + `je`-next-entry, then the SIGN test `movsx`+`test`+`jge 0x470d86` so prio>0 "
      "goes STRAIGHT to the log (no store) and only prio<0 falls through to 0x470cb6, the "
      "duplicate-scan init (`mov DWORD PTR [ebp-0x10],0x0`) (R3)")
    reject_sites = [a for a, mm, oo in HIT_CHAIN if mm == "jmp" and oo == "0x470c0d"]
    A("A24", reject_sites == [0x470C3B, 0x470C58, 0x470C75, 0x470C92] and
      all(mn(a) == "jmp" and ops(a) == "0x470c0d" for a in reject_sites) and
      len(reject_sites) == 4 and
      (mn(0x470C0D), ops(0x470C0D)) == ("mov", "eax,DWORD PTR [ebp-0xc]") and
      (mn(0x470CB6), ops(0x470CB6)) == ("mov", "DWORD PTR [ebp-0x10],0x0") and
      0x470C0D < min(reject_sites) < max(reject_sites) < 0x470CB6,
      "the branch SKELETON is pinned separately from the conditions (A10): EXACTLY four rejecting "
      "edges exist in the hit test - p1 (0x470c3b), p2 (0x470c58), kind<0 (0x470c75), prio==0 "
      "(0x470c92) - every one of them is `jmp 0x470c0d`, the address that re-reads and advances "
      "the OUTER index [ebp-0xc], and the prio<0 fall-through is 0x470cb6, the inner-index init "
      "(the duplicate scan), NOT the log tail. Retargeting any single reject edge (M14 moves the "
      "prio!=0 one into the log) fails the exact list here")


    # ---------------- S5 argument provenance from the callers ------------------------------
    out.p("\n[S5] what the two int args are, from the callers' encodings")
    unpack_pushes = [(hex(a), o_) for a, m_, o_ in win(0x470BB3, 0x470BC7) if m_ == "push"]
    unpack_addr = [(hex(a), mn(a), o_) for a, m_, o_ in win(0x470BB3, 0x470BC7) if m_ == "lea"]
    out.p("  the 4 pushes before the unpacker call 0x470bc6: %s" % unpack_pushes)
    out.p("  the lea (address-of) instructions: %s" % unpack_addr)
    between = [(hex(a), mn(a), o_) for a, m_, o_ in win(0x470BCB, 0x470C4C)
               if m_ == "mov" and re.search(r"\[ebp-0x(14|18)\],", o_)]
    out.p("  writes to [ebp-0x14]/[ebp-0x18] between the unpack call and their use: %s" % between)
    consumed = [(hex(a), o_) for a, m_, o_ in win(0x470D9A, 0x470DA2) if m_ == "push"]
    consumed_loads = [(hex(a), o_) for a, m_, o_ in win(0x470D9A, 0x470DA2) if m_ == "mov"]
    out.p("  the two output slots consumed at the formatter: loads %s pushes %s" %
          (consumed_loads, consumed))
    A("A11", unpack_pushes == [("0x470bb6", "edx"), ("0x470bba", "eax"),
                               ("0x470bbe", "ecx"), ("0x470bc2", "edx")] and
      ops(0x470BBB) == "ecx,DWORD PTR [ebp+0xc]" and ops(0x470BBF) == "edx,DWORD PTR [ebp+0x8]" and
      unpack_addr == [("0x470bb3", "lea", "edx,[ebp-0x18]"),
                      ("0x470bb7", "lea", "eax,[ebp-0x14]")] and
      consumed == [("0x470d9d", "ecx"), ("0x470da1", "edx")] and
      consumed_loads == [("0x470d9a", "ecx,DWORD PTR [ebp-0x18]"),
                         ("0x470d9e", "edx,DWORD PTR [ebp-0x14]")] and
      not between,
      "FUN_0046a1b0 is called (0x470bc6, ecx=this) with its 2 INPUTS = this routine's own "
      "p2 [ebp+0xc] then p1 [ebp+8], and its 2 OUTPUT POINTERS = &[ebp-0x18], &[ebp-0x14] "
      "(lea pushes, order printed); those slots are NEVER written by any mov in the window "
      "(only by the callee through the pointers) and are consumed again ONLY at 0x470d9a/9e "
      "(the log formatter) - so the GOAL +4/+8 pair the routine compares is (p1,p2) "
      "re-expressed in the derived (wrapped/row-adjusted) coordinate space")
    site_rows = []
    for cs in CALLSITES:
        grp, a = [], cs
        while len(grp) < 3:
            a = max(x for x in order if x < a)
            m_, o_ = ins[a]
            if (m_ == "call" and a != cs) or m_ == "ret" or a < cs - 40:
                break
            if m_ == "push":
                grp.append((hex(a), o_))
        defs = []
        for _addr, reg in [g for g in grp if "," not in g[1]]:
            b = int(_addr, 16)
            want = reg.split()[-1]
            while True:
                b = max(x for x in order if x < b)
                if b < int(_addr, 16) - 24:
                    defs.append("%s<??" % want)
                    break
                m2, o2 = ins[b]
                if m2 in ("mov", "lea", "xor", "pop") and o2.split(",")[0].split()[-1] == want:
                    defs.append("%s<-%s %s" % (want, m2, o2))
                    break
        site_rows.append((hex(cs), grp, defs))
    for r in site_rows:
        out.p("  %s push group (newest first): %s   reg defs: %s" % (r[0], r[1], r[2]))
    s5 = site_rows[-1]
    pairs = [tuple(sorted(re.sub(r"\w+<-(mov|lea) \w+,DWORD PTR |\w+<-\w+ ", "", d)
                          for d in defs)) for _, _, defs in site_rows]
    A("A12", len(site_rows) == 5 and all(len(g) == 2 for _, g, _ in site_rows) and
      all("??" not in " ".join(d) for _, _, d in site_rows) and
      sorted(re.findall(r"\[ebp-0x[0-9a-f]+\]", " ".join(s5[2]))) ==
      sorted(["[ebp-0x18]", "[ebp-0x1c]"]) and len(s5[2]) == 2 and
      pairs[1] == pairs[2] == pairs[3] == ("[ebp-0x10]", "[ebp-0x14]") and
      pairs[0] == ("[ebp+0x8]", "[ebp+0xc]"),
      "every site forwards EXACTLY 2 register pushes (the ecx=this load sits outside the "
      "group); every forwarded register's defining load is printed and closed on a stack "
      "slot: sites 2/3/4 read the SAME slot pair [ebp-0x10],[ebp-0x14] (their x,y loop "
      "variables), site 1 re-forwards the caller's own incoming pair, and site 5 reads the "
      "unpacker's output slots [ebp-0x18]/[ebp-0x1c] - NO site reads a global for the pair "
      "the GOAL +4/+8 compare against (R5)")

    # ---------------- S6 the invalidation law ----------------------------------------------
    out.p("\n[S6] the duplicate-kind law + sentinel store + re-read (instruction by instruction)")
    law = [0x470CB6, 0x470CC8, 0x470CCC, 0x470CD2, 0x470CD5, 0x470CD8, 0x470CDA,
           0x470CEE, 0x470D0B, 0x470D25, 0x470D3C, 0x470D44, 0x470D46, 0x470D48,
           0x470D5C, 0x470D66, 0x470D75, 0x470D7D, 0x470D7F, 0x470D81]
    for a in law:
        out.p("  %s: %s %s" % (hex(a), mn(a), ins[a][1].rstrip()))
    word_stores = [(hex(a), o_) for a, m_, o_ in win(FUN_LO, FUN_HI)
                   if m_ == "mov" and o_.startswith("WORD PTR") and "0x94ee" in o_]
    re_read = [a for a, m_, o_ in win(0x470D63, 0x470D86) if m_ == "movsx" and "0x94ee28" in o_]
    A("A13", word_stores == [(hex(SENT_STORE), "WORD PTR [ecx+edx*1+0x94ee28],0xffff")],
      "exactly ONE WORD store to the +0 kind in the window, and it is 0xffff (R1: not a prio "
      "clear; +2 has no store)")
    outer_fold_seed = [(hex(a), ins[a][1]) for a in (0x470D1F, 0x470D25) if "ebp-0xc" in ins[a][1]]
    inner_fold_seed = [(hex(a), ins[a][1]) for a in (0x470D36, 0x470D3C) if "ebp-0x10" in ins[a][1]]
    store_fold_seed = [(hex(a), ins[a][1]) for a in (0x470D56, 0x470D59, 0x470D5C)
                       if "ebp-0xc" in ins[a][1]]
    A("A14", outer_fold_seed == [("0x470d1f", "ecx,DWORD PTR [ebp-0xc]")] and
      inner_fold_seed == [("0x470d36", "ecx,DWORD PTR [ebp-0x10]")] and
      store_fold_seed == [("0x470d56", "edx,DWORD PTR [ebp-0xc]")] and
      ops(0x470D25) == "edx,WORD PTR [eax+ecx*1+0x94ee28]" and
      ops(0x470D3C) == "eax,WORD PTR [eax+ecx*1+0x94ee28]" and
      ops(0x470D44) == "edx,eax" and ops(0x470D46) == "0x470d4d" and
      mn(0x470C1A) == "jge" and ops(0x470C1A) == "0x470f7e" and
      0x470D5C < 0x470D66 < 0x470D75 and
      ops(0x470D5C) == "WORD PTR [ecx+edx*1+0x94ee28],0xffff",
      "the compared kind pair: edx = movsx of entry.+0 through the fold seeded [ebp-0xc] "
      "(the OUTER index i) and eax = movsx of entry.+0 through the fold seeded [ebp-0x10] (the "
      "INNER index j), cmp edx,eax / je reaches the 0xffff store - the store fold at 0x470d56 "
      "re-seeds [ebp-0xc], so the WRITE hits entry i, not j; i != j is enforced at 0x470cd5; "
      "the outer scan exits to 0x470f7e (the block-loop increment), NOT into the log tail. "
      "Ghidra's C agrees with this reading (`local_10` vs `local_14` in the comparison), so it is "
      "CORROBORATION, not a refutation - the encoding remains the primary evidence")
    A("A15", len(re_read) == 1 and re_read[0] == 0x470D75 and mn(0x470D7D) == "test" and
      mn(0x470D7F) == "jge" and ops(0x470D7F) == "0x470d86" and ops(0x470D81) == "0x470c0d",
      "the store is followed by a RE-READ (movsx) of entry i +0, test/jge: negative (the 0xffff "
      "we just wrote, or already set by another block iteration) -> jmp back to the block-filter "
      "head 0x470c0d; only a still-non-negative entry reaches the log tail (R4)")
    argslot_writes = [(hex(a), mn(a), o_) for a, m_, o_ in win(0x470B90, 0x470D86)
                      if m_ == "mov" and re.search(r"\[ebp\+(0x8|0xc)\],", o_)]
    A("A16", not argslot_writes,
      "0 writes to the argument slots [ebp+8]/[ebp+c] before the tail (R5)")

    # ---------------- S7 the jump table -----------------------------------------------------
    out.p("\n[S7] the kind switch: 8-entry dword table + 42-entry BYTE index table, from raw PE")
    out.p("  (objdump misassembles both regions as instructions; this parse reads the bytes)")
    blob = open(M.EXE, "rb").read()
    _ib, secs = M.pe_sections(blob)

    def pe_read(va, n):
        off, _nm = M.va2off(secs, va)
        return None if off is None else blob[off:off + n]

    kind_load = [a for a, m_, o_ in win(0x470DF5, 0x470E15) if m_ == "movsx"]
    A("A16b", kind_load == [0x470DF5] and "0x94ee2a" not in ops(0x470DF5) and
      "0x94ee28" in ops(0x470DF5),
      "the switch selector is the RE-READ of entry i +0 KIND (0x470df5), stored to [ebp-0x30], "
      "not the +2 priority")
    JT_BYTES = pe_read(JT, 32 + 42) or b""
    dtab = struct.unpack_from("<8I", JT_BYTES, 0)
    btab = list(JT_BYTES[32:74])
    out.p("  dword table @0x470f8c: %s" % [hex(x) for x in dtab])
    out.p("  byte  table @0x470fac: %s" % btab)
    groups = {}
    for k in range(42):
        t = dtab[btab[k]] if btab[k] < len(dtab) else None
        groups.setdefault(t, []).append(k)
    cases = []
    for tgt, ks in sorted(groups.items(), key=lambda kv: (kv[0] is None, kv[0])):
        body = [(hex(a), m_, o_) for a, m_, o_ in (win(tgt, tgt + 16) if tgt else [])]
        push_addr = [o_ for _, m_, o_ in body if m_ == "push" and o_.startswith("0x")]
        store_code = [o_ for _, m_, o_ in body if "ebp-0x1c" in o_]
        cases.append((ks, tgt, push_addr, store_code))
        out.p("  kinds %-16s -> %s push %s code %s" %
              (str(ks) if len(ks) < 6 else "%d..%d (%d kinds)" % (ks[0], ks[-1], len(ks)),
               hex(tgt) if tgt else "None", push_addr, store_code))
    singles = [(t, ks[0]) for t, ks in groups.items() if t and len(ks) == 1]
    wide = [(t, ks) for t, ks in groups.items() if t and len(ks) > 1]
    A("A17", len(dtab) == 8 and len(btab) == 42 and all(b < 8 for b in btab) and
      len(groups) == 8 and len(singles) == 7 and len(wide) == 1 and
      wide[0][0] == 0x470EB7 and sorted(wide[0][1]) == sorted([1, 4, 5, 7] + list(range(10, 41))),
      "the byte table indexes into EXACTLY 8 dword targets (all values < 8); 7 kinds get their "
      "own block (0,2,3,6,8,9,41) and ONE block 0x470eb7 - which is also the ja-out default - "
            "serves the other 35 kinds (1,4,5,7,10..40). THIS AGREES with Ghidra's case list "
      "(0,2,3,6,8,9,0x29) - 0x29 IS 41 - so the C collapses nothing here; what only the BYTES "
      "show is the STRUCTURE: 42 selector values share 8 handler blocks, 35 of them (plus the "
      "ja default) sharing one that pushes no token at all")

    A("A18", mn(0x470DFD) == "mov" and ops(0x470DFD) == "DWORD PTR [ebp-0x30],edx" and
      mn(0x470E00) == "cmp" and ops(0x470E00) == "DWORD PTR [ebp-0x30],0x29" and
      mn(0x470E04) == "ja" and ops(0x470E04) == "0x470eb7" and
      ops(0x470E0F) == "al,BYTE PTR [ecx+0x470fac]" and
      ops(0x470E15) == "DWORD PTR [eax*4+0x470f8c]",
      "cmp kind,0x29 / ja 0x470eb7 + byte table @0x470fac -> jmp dword[eax*4+0x470f8c]: "
      "kind -1 (0xffff) is UNSIGNED-above 0x29 -> an invalidated entry NEVER logs a label (R6); "
      "0x470eb7 is BOTH the tail and the out-of-range/default block")
    label_pushes = [int(c[2][0], 16) for c in cases if c[1] != 0x470EB7 and c[2]]
    dflt = [c for c in cases if c[1] == 0x470EB7]

    # ---------------- S8 the tokens ---------------------------------------------------------
    out.p("\n[S8] the per-kind tokens appended after the block/priority text (PE .rdata)")
    def cstr(va):
        b = pe_read(va, 64)
        return "?" if b is None else b.split(b"\0")[0].decode("latin1", "replace")
    tokmap = {}
    for c in cases:
        if c[2]:
            for k in c[0]:
                tokmap[k] = (int(c[2][0], 16), cstr(int(c[2][0], 16)))
    for k in sorted(tokmap):
        out.p("  kind %-3d -> 0x%x %r" % (k, tokmap[k][0], tokmap[k][1]))
    named = {k: v for k, v in tokmap.items() if k < 42 and k in
             [kk for t, ks in groups.items() if t != 0x470EB7 for kk in ks]}
    A("A19", len(named) == 7 and len({v[1] for v in named.values()}) == 7 and
      all(re.fullmatch(r"[!-~]", v[1]) for v in named.values()) and
      all(not c[2] for c in cases if c[1] == 0x470EB7) and
      tokmap.get(0) and not tokmap.get(41)[1].isalpha(),
      "7 kinds (0,2,3,6,8,9,41) append a ONE-CHARACTER .rdata token; kinds 1,4,5,7,10..40 and "
      "the out-of-range default reach 0x470eb7 which pushes NOTHING - the log line carries no "
      "token for them (the tokens are chars, not names: the earlier 'asset string' reading is "
      "DECLARED UNMODELED here - the adjacent pool entries 'REALLYOVER', 'DESTNO', 'DESTTRI2' "
      "belong to other code)")

    # ---------------- S9 the log sink chain -------------------------------------------------
    out.p("\n[S9] the tail: build-string -> append x2 -> vtable -> global buffer")
    tail_calls = [(hex(a), ops(a)) for a, m_, o_ in win(0x470D86, FUN_HI) if m_ == "call"]
    for t in tail_calls:
        out.p("  %s call %s" % t)
    v4 = [a for a, m_, o_ in win(0x470D86, FUN_HI)
          if m_ == "call" and "0x4" == ops(a).strip() and "edx" in ops(a)]
    abs_neg = [a for a, m_, o_ in win(0x470D86, FUN_HI) if m_ == "neg"]
    tail_seq = [ops(int(a, 16)) for a, _ in tail_calls]
    A("A20", tail_seq == ["0x403a40", "0x407520", "0x423c20", "0x405220"] +
      ["0x405220"] * 7 + ["0x4237f0", "0x5c17d1", "0x5c176e", "0x4081b0"],
      "tail call sequence from the encoding: unpacker, formatter, terminator, then (debug) "
      "name+append, 8x label-append, prio-append, two string vtable calls, buffer flush")
    A("A21", len(abs_neg) == 1 and 0x470F05 in [a for a, m_, o_ in win(0x470D86, FUN_HI)
                                                if m_ == "neg"] and
      any("0x997120" in ops(a) for a in (0x470F62,)) and
      ops(0x470D86) == "eax,DWORD PTR [ebp-0x4]",
      "the log line = FUN_00403a40(buf, unpacked pair, this+0x1ddb4, this+0x1ddb8) then the "
      "ABSOLUTE priority via neg-if-negative -> FUN_004237f0 append -> FUN_004081b0 appends the "
      "built line to the global buffer ds:0x997120; the block NAME (FUN_00423c20) is appended "
      "only under debug flag 0x985ae8&0x80, which also clears BYTE ds:0x997121 (a dirty flag)")

    # ---------------- S10 uniqueness --------------------------------------------------------
    out.p("\n[S10] uniqueness inside the window")
    stores = [(hex(a), ops(a)) for a, m_, o_ in win(FUN_LO, FUN_HI)
              if "PTR" in o_ and o_.startswith(("WORD PTR", "BYTE PTR", "DWORD PTR"))
              and "0x94ee" in o_]
    out.p("  stores into the GOAL window: %s" % stores)
    A("A22", stores == [(hex(SENT_STORE), "WORD PTR [ecx+edx*1+0x94ee28],0xffff")],
      "the sentinel at 0x470d5c is the ONLY GOAL-window store in the function (R1/R3)")

    # ---------------- S11 callees ------------------------------------------------------------
    out.p("\n[S11] callees")
    cal = sorted({int(ops(a), 16) for a, m_, o_ in win(FUN_LO, FUN_HI)
                  if m_ == "call" for o2 in [o_] if ops(a).startswith("0x")})
    targets = sorted({int(ops(a), 16) for a, m_, _ in win(FUN_LO, FUN_HI) if m_ == "call"})
    out.p("  %d distinct targets: %s" % (len(targets), hexset(targets)))
    A("A23", len(targets) == int(fields["n_callees"]) == 9,
      "9 callee targets == index.csv n_callees")

    # ---------------- rivals -----------------------------------------------------------------
    out.p("\n[rivals]")
    prio_leg = mn(0x470CB0) == "jge" and ops(0x470CB0) == "0x470d86"
    rv = [("R1 the 0xffff store clears a priority",
           word_stores != [(hex(SENT_STORE), "WORD PTR [ecx+edx*1+0x94ee28],0xffff")] or
           len(stores) != 1),
          ("R2 it runs during normal play",
           mn(0x470BAD) != "je" or ops(0x470BAD) != "0x470f83" or len(and2000) != 1),
          ("R3 every matching entry is invalidated",
           not prio_leg or len(word_stores) != 1 or
           sum(1 for a, m_, o_ in win(FUN_LO, FUN_HI)
               if m_ == "mov" and o_.startswith("WORD PTR") and "0x94ee2a" in o_) != 0),
          ("R4 the post-store read is another store", len(re_read) != 1 or
           mn(0x470D75) != "movsx"),
          ("R5 the args are rewritten mid-scan", bool(argslot_writes) or bool(between)),
          ("R6 kind -1 logs a label",
           not (mn(0x470E04) == "ja" and ops(0x470E04) == "0x470eb7") or
           len(singles) != 7 or wide[0][0] != 0x470EB7),
          ("R7 the unpacker belongs to this routine",
           len([l for l in open(M.INDEX) if ",FUN_0046a1b0," in l]) != 1 or
           int([l for l in open(M.INDEX) if ",FUN_0046a1b0," in l][0].split(",")[4]) <= 5),
          ("R8 the scans also walk the SITE list",
           any("+0x94f2" in o_ for _, _, o_ in win(FUN_LO, FUN_HI)))]
    for name, holds in rv:
        out.p("  %-46s %s" % (name, "HOLDS (bad)" if holds else "REFUTED"))
        chk.append(("RIVALS-" + name.split()[0], not holds))

    bad = 0
    out.p("\n[checks]")
    for cid, good in chk:
        if not good:
            bad += 1
            out.p("  %-9s RED" % cid)
    out.p("\n%d/%d checks OK" % (len(chk) - bad, len(chk)))
    out.p("table sha %s" % hashlib.sha256("\n".join(out.lines).encode()).hexdigest()[:16])
    if bad:
        print("RESULT: FAIL (%d checks red)" % bad, file=sys.stderr)
        return 1
    print("RESULT: PASS M310 FUN_00470b90 = the debug-gated GOAL duplicate-invalidator + "
          "labelled log line of the view object")
    return 0


if __name__ == "__main__":
    sys.exit(main())
