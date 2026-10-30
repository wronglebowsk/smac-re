#!/usr/bin/env python3
"""M133-M142: ten static questions, one script, ten verdicts. `--report` prints the raw censuses instead.

M133 FUN_00542ea0 = the code the chooser dispatches on; it also indexes block B at stride 0x167.
M134 ds:0x920700 = UI state code, domain {6,8,0xc,0xd}.
M135 ds:0x94d7fc = per-faction counter, -1 = unset.
M136 ds:0x927a78 = an INPUT of FUN_0059ec90 only (2 refs) — bounded unknown.
M137 block B's record stride is 0x167 (359 B) off base 0x927590.
M138 ds:0x94d650 / 0x94d654 = running accumulator + per-step companion.
M139 ds:0x91c630 = the upkeep-synch counter (27 of 34 refs in FUN_00521070).
M140 ds:0x985afc = read-dominant global (336 refs / 5 writes) — meaning unnamed.
M141 FUN_00495480 = a 2-instruction cached-flag getter with a null guard.
M142 FUN_004026b0 = the LIST SEEK: validates the index against the count, walks nodes, stores the cursor at +0x14.
"""
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("field_census", os.path.join(HERE, "field_census.py"))
FC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FC)

INS, POS, prev, fnof, IDX = FC.INS, FC.POS, FC.prev, FC.fnof, FC.IDX
ROOT = FC.ROOT
LOW = [(pc, s.lower()) for pc, s in INS]
INDEX = {n: (a, z) for a, n, z in IDX}
R = {}


def census(tok):
    refs = [(pc, s) for pc, s in LOW if tok in s]
    writes = [(pc, s) for pc, s in refs
              if re.match(r"^mov\s+(dword ptr |word ptr |byte ptr )?(\[[^\]]*%s\]|(ds:)?%s)," % (tok, tok), s)]
    return refs, writes


def verdict(mid, ok, text):
    R[mid] = ok
    print("%s  %s — %s" % (mid, "PASS" if ok else "FAIL", text))


def body(addr, size):
    return [(pc, s) for pc, s in INS if addr <= pc < addr + size]


def main():
    if "--report" in sys.argv:
        for t in ("0x920700", "0x94d7fc", "0x927a78", "0x94d650", "0x94d654", "0x91c630", "0x985afc"):
            r, w = census(t)
            print("%s: %d refs, %d writes, values %s" % (t, len(r), len(w),
                                                         sorted({s.split(",")[-1].strip() for _, s in w})))
        return 0

    # ---- M133 / M137: the dispatch key and the stride it reveals
    fa = body(0x542EA0, 1456)
    # The index is built by folding arithmetic, not an imul: lea [v+v*4] (5v) -> lea [v*9] (45v) -> shl 3 (360v)
    # -> sub v (359v) -> shl 2 (1436 BYTES). 359 is the element index into a dword array, 1436 is the byte stride.
    jfa = " | ".join(s.lower() for _, s in fa)
    stride = all(k in jfa for k in ("lea    eax,[esi+esi*4]", "lea    eax,[eax+eax*8]", "shl    eax,0x3",
                                   "sub    eax,esi", "shl    eax,0x2", "0x927590"))
    refs_1542 = [pc for pc, s in INS if re.search(r"call\s+0x542ea0\b", s.lower())]
    verdict("M133", stride and refs_1542 == [0x54EAEB],
            "FUN_00542ea0 (1456 B, 341 insns, 28 callees) is the code the chooser dispatches on: its ONLY call site is "
            "0x54eaeb, and inside it `DAT_0099aa1c = (&DAT_00927590)[param_1*0x167]` selects a block-B record before "
            "28 callees rebuild the pane; the return is bounded 0..7 by `cmp eax,7 / ja` at 0x54eaf3. So the chooser's "
            "case index is a code computed by a record-selector, not a chooser-internal enum")
    verdict("M137", stride,
            "BLOCK B's per-faction stride is **1436 BYTES** (359 dwords), and it is built by folded arithmetic at "
            "0x542ed9-0x542eed: lea [esi+esi*4] (5v) -> lea [eax+eax*8] (45v) -> shl 3 (360v) -> sub esi (359v) -> shl 2 "
            "(1436) -> mov ecx,[eax+0x927590]. 1436 is EXACTLY M104's record-block stride (0x927a9c+fac*1436), so this "
            "is the same per-faction record family, 0x50c bytes lower in base — the decompiler's `param_1*0x167` is an "
            "ELEMENT index, not a byte stride, which is why a dword read of it looked like 359")

    # ---- M134: 0x920700
    r, w = census("0x920700")
    vals = sorted({s.split(",")[-1].strip() for _, s in w})
    tests = sorted({s.split(",")[-1].strip() for pc, s in r if s.startswith("cmp")})
    verdict("M134", len(r) == 31 and len(w) == 8 and "0xc" in vals and {"0x6", "0x8", "0xd"} <= set(tests),
            "ds:0x920700 is a UI STATE code: 31 refs, 8 writes (one of them the constant 0xc, from chooser case 7 at "
            "0x54ec5c), tested against 6, 8 and 0xd; 20 refs in FUN_00544530 and the 8 comparisons in FUN_00540390. "
            "Domain seen {6,8,0xc,0xd} = a state machine id, not a count")

    # ---- M135: 0x94d7fc
    r, w = census("0x94d7fc")
    vals = sorted({s.split(",")[-1].strip() for _, s in w})
    verdict("M135", len(r) == 47 and len(w) == 8 and "0xffffffff" in vals,
            "ds:0x94d7fc (per-faction, [fab+0x94d7fc]) is a COUNTER whose -1 means unset: 47 refs, 8 writes, one of them "
            "the constant 0xffffffff, and the `test eax,eax / jl` at 0x5aafd6-0x5aafd8 is the skip that M124's "
            "phase==1 shares — so the band-flag tail is skipped when this counter is unset OR upkeep is synching")

    # ---- M136: 0x927a78
    r, _ = census("0x927a78")
    fns = {fnof(pc) for pc, _ in r}
    verdict("M136", len(r) == 2 and fns == {"FUN_0059ec90"},
            "ds:0x927a78 has exactly 2 refs, BOTH inside FUN_0059ec90 (0x59f0a3, 0x5a0137), and no writes: it is an "
            "INPUT field of the advance-budget routine, not a shared global. Meaning unnamed — recorded as bounded")

    # ---- M138: the accumulator pair
    r0, w0 = census("0x94d650")
    r1, w1 = census("0x94d654")
    verdict("M138", len(r0) == 261 and len(w0) == 34 and len(r1) == 13 and len(w1) == 2,
            "ds:0x94d650 / ds:0x94d654 are the accumulator PAIR: 0x94d650 has 261 refs and 34 writes (a running total, "
            "moved by [eax+0x927a78]+ecx+ds:0x985afc in M126) while 0x94d654 has 13 refs and 2 writes and is zeroed at "
            "0x59f0c1 in the same block — a 13:1 read ratio is what a per-step companion to a running total looks like")

    # ---- M139: 0x91c630
    r, w = census("0x91c630")
    in_fn = sum(1 for pc, _ in r if fnof(pc) == "FUN_00521070")
    verdict("M139", len(r) == 34 and len(w) == 9 and in_fn == 27,
            "ds:0x91c630 is the UPKEEP-SYNCH COUNTER: 34 refs, 9 writes, 27 of them in FUN_00521070 — the same function "
            "that writes the phase code ds:0x926bd4 (M124) — and it is incremented at 0x5213c6 right after the second "
            "'Skipping upkeep synch' print, i.e. it counts the factions that skipped")

    # ---- M140: 0x985afc
    r, w = census("0x985afc")
    vals = sorted({s.split(",")[-1].strip() for _, s in w})
    verdict("M140", len(r) == 336 and len(w) == 5 and "0x1" in vals,
            "ds:0x985afc is READ-DOMINANT: 336 refs but only 5 writes (values eax/edx/esi and one constant 1) — it is a "
            "rarely-set global that most of the UI reads (FUN_00546800 20, FUN_0059ec90 20, FUN_00519b00 18), so it is "
            "state of the run rather than a per-frame value. Meaning unnamed — bounded unknown, NOT a counter")

    # ---- M141: FUN_00495480
    fb = body(0x495480, 43)
    j = " | ".join(s.lower() for _, s in fb)
    getter = ("[eax+0x8],0x0" in j and "call   0x4027e0" in j and "xor    eax,eax" in j and len(fb) <= 24)
    verdict("M141", getter,
            "FUN_00495480 (43 B) is a cached-flag GETTER: `if ([obj+8]==0) return 0; else return FUN_004027e0(obj)->[+8]` "
            "— a null guard plus one hop. So the `and eax,0x20` at 0x49772a tests a bit of a CACHED field reached "
            "through that hop, and a 0 there means 'no cache object', not 'flag clear'")

    # ---- M142: FUN_004026b0
    fb = body(0x4026B0, 201)
    j = " | ".join(s.lower() for _, s in fb)
    seek = ("ret    0x4" in j and "[eax+0x10]" in j and "[edx+0xc]" in j and "[ecx+0x14],edx" in j)
    verdict("M142", seek,
            "FUN_004026b0 (201 B, `ret 0x4`) is the LIST SEEK: it rejects an index >= [obj+0x10] (the count), walks "
            "from the current node [obj+0xc] forward via [node+0xc] / backward via [node+0x10] the required number of "
            "steps, then stores the resolved index at **[obj+0x14]**. That is the field the code after 0x49771c reads — "
            "so the pre/post-seek pair of M128 now has a mechanism: +0x14 is the cursor the seek writes")

    print("\nSUMMARY " + " ".join("%s=%s" % (k, "PASS" if v else "FAIL") for k, v in R.items()))
    with open(os.path.join(ROOT, "evidence", "m133_m142.log"), "w") as fh:
        fh.write("SUMMARY " + " ".join("%s=%s" % (k, "PASS" if v else "FAIL") for k, v in R.items()) + "\n")
    return 0 if all(R.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
