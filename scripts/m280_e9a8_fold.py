"""M280 (s222) - the e9a8 readers DO ride the block fold: M279 G6's "(30,64,0)
different index idiom" was a mid-chain window artifact (evaluator window started
after the fold seeds), NOT a new indexing scheme.

Static only, zero box time. Reuses m277's load/neuter/chain_eval via the
"\\ndef main(" slice (skill law).

ANSWERS:
  G1: e9a8 census re-derived: exactly 2 sites (0x568038, 0x5a9fd5), both READS,
      zero writer stores image-wide (read-only row stands).
  G2: reader 0x568038 (FUN_0055f650, the M278 AI hub) full chain INCLUDING seeds:
      edi = [ebp-0xc] (the acting unit's OWNER byte, M278 identity); edx = 65*edi
      (mov edx,edi; shl edx,6; add edx,edi @0x568021-29) then lea ecx,[edi+edx*2]
      = 131*edi; shl ecx,4 = 2096*edi; sub ecx,edi = 2095*edi; lea edx,[eax+ecx*2]
      = eax + 4190*edi; load [edx*2+0x94e9a8] -> byte index = 8380*block + 2*region
      - THE per-block WORD fold.
  G3: reader 0x5a9fd5 (FUN_005a90a0) same shape: edi = [ebp+0xc] (arg), edx = the
      region loop counter 1..N (mov edx,1 @0x5a9f85, inc edx @0x5a9fe6, loop
      back-edge @0x5a9fed -> 0x5a9f8f); ecx = edx + 4190*edi; load -> 8380*edi + 2*edx.
  G4: artifact proof: the M279 G6 window [0x56802B,0x568035) with FREE atoms
      {edi:(1,0,0), edx:(0,1,0), eax:(0,0,0)} reproduces edx = (30,64,0), and
      substituting the seed edx := 65*edi gives 4190*edi, i.e. the SAME byte index
      (8380) - the "(30,64,0) idiom" was the mid-chain truncation, computed.
  G5: provenance (reader1): the ONLY [ebp-0xc] store in FUN_0055f650 is 0x55f71d
      (`mov DWORD PTR [ebp-0xc],eax`); eax = BYTE[52*edi+0x933286] = unit+14 OWNER
      (13*4 == 52, M278 identity) - the reader is keyed on the OWNER block, like
      the M278 writers.
  G6: containment + the walkers' loop: own(0x568038)=FUN_0055f650,
      own(0x5a9fd5)=FUN_005a90a0; the 0x5a9fd5 region side is a loop counter.
  G7: registry: NAMED.md carries ## M280 (s222); M279's e9a8 row is patched to
      cite M280 (retraction lives in the registry, not just session notes).
"""

import csv
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
INDEX = os.path.join(ROOT, "ghidra_out", "index.csv")
NAMED = os.path.join(ROOT, "NAMED.md")
M277 = os.path.join(ROOT, "scripts", "m277_scaled_row_ownership.py")
STRIDE = 8380

_src = open(M277).read()
_ns = {"__file__": M277}
exec(_src[:_src.index("\ndef main(")], _ns)
load, neuter, chain_eval = _ns["load"], _ns["neuter"], _ns["chain_eval"]

PAT = re.compile(r"\s+([0-9a-f]+):\t([0-9a-f ]+)\t(\S+)\s?(.*)")


def site(a):
    """(op, args) at an address from the aligned cache."""
    with open(TEXT, errors="replace") as fh:
        for line in fh:
            m = PAT.match(line)
            if not m:
                continue
            if int(m.group(1), 16) == a:
                return (m.group(3), m.group(4).split("#")[0].strip())
    raise KeyError(hex(a))


def census_base(base):
    """Image-wide: every site whose operand contains the literal base token."""
    out = []
    tok = "0x%x" % base
    with open(TEXT, errors="replace") as fh:
        for line in fh:
            m = PAT.match(line)
            if not m or not m.group(3):
                continue
            ar = m.group(4).split("#")[0].strip()
            if tok in ar:
                out.append((int(m.group(1), 16), m.group(3), ar))
    return out


def owners():
    idx = [r for r in csv.reader(open(INDEX)) if r and r[0].startswith("0x")]

    def own(a):
        p = None
        for r in idx:
            s = int(r[0], 16)
            if s <= a:
                p = r[1]
            else:
                break
        return p

    return own


def main():
    res = []

    def gate(n, ok, text):
        res.append(ok)
        print("G%d %s: %s" % (n, "PASS" if ok else "FAIL", text))

    own = owners()

    # ---- G1: e9a8 census (re-derived, not trusted from M279)
    r9 = census_base(0x94E9A8)
    wr9 = [a for a, op, ar in r9
           if re.match(r"mov\s+(BYTE|WORD|DWORD) PTR \[[^\]]+\],", ar)
           or re.match(r"(inc|add|or)\s+(WORD|BYTE) PTR \[[^\]]+\]", ar)]
    sites_sorted = sorted(a for a, _, _ in r9)
    gate(1, len(r9) == 2 and sites_sorted == [0x568038, 0x5A9FD5] and not wr9,
         "e9a8 census: %d sites %s, writers %s (ZERO stores - read-only row stands)"
         % (len(r9), [hex(a) for a in sites_sorted],
            [hex(a) for a in wr9]))

    # ---- G2: reader 0x568038 full chain WITH seeds -> (8380, 2, 0)
    e2, d2 = load(0x56802B, 0x568039)
    s2, _ = chain_eval(d2, 0x56802B, 0x568035,
                       {"edi": (1, 0, 0), "edx": (65, 0, 0), "eax": (0, 1, 0)})
    v2 = s2.get("edx")
    # seed instructions must be exactly the fold opener 65 = 64+1
    sd1 = site(0x568015)
    sd2 = site(0x568021)
    sd3 = site(0x568026)
    sd4 = site(0x568029)
    sd5 = site(0x568023)
    rd2 = site(0x568038)
    ok2 = (v2 == (4190, 1, 0)
           and sd2 == ("mov", "edx,edi")
           and sd3 == ("shl", "edx,0x6")
           and sd4 == ("add", "edx,edi")
           and sd5 == ("mov", "eax,DWORD PTR [ebp-0x34]")
           and sd1 == ("mov", "edi,DWORD PTR [ebp-0xc]")
           and rd2 == ("mov", "cx,WORD PTR [edx*2+0x94e9a8]")
           and 2 * 4190 == STRIDE and 65 == 64 + 1)
    gate(2, ok2,
         "reader 0x568038 chain WITH seeds: edi=[ebp-0xc] "
         "(%s / %s / %s / %s) -> edx = %s; load %s -> byte index = "
         "%d*block + %d*region = (8380,2,0): THE per-block WORD fold"
         % (sd1[1], sd2[1], sd3[1], sd4[1], v2, rd2[1], 2 * v2[0], 2 * v2[1]))

    # ---- G3: reader 0x5a9fd5 same fold; region side is a loop counter
    e3, d3 = load(0x5A9FC1, 0x5A9FD6)
    s3, _ = chain_eval(d3, 0x5A9FC1, 0x5A9FD3,
                       {"edi": (1, 0, 0), "edx": (0, 1, 0)})
    v3 = s3.get("ecx")
    seed = site(0x5A9F80)
    edx_init = site(0x5A9F85)
    edx_inc = site(0x5A9FE6)
    back = site(0x5A9FED)
    rd3 = site(0x5A9FD5)
    ok3 = (v3 == (4190, 1, 0)
           and seed == ("mov", "edi,DWORD PTR [ebp+0xc]")
           and edx_init == ("mov", "edx,0x1")
           and edx_inc == ("inc", "edx")
           and back == ("jl", "0x5a9f8f")
           and rd3 == ("mov", "ax,WORD PTR [ecx*2+0x94e9a8]")
           and 2 * 4190 == STRIDE)
    gate(3, ok3,
         "reader 0x5a9fd5: edi=[ebp+0xc] (arg, %s); edx = loop counter (%s, %s @%#x, "
         "back-edge %s @%#x); ecx = %s; load %s -> byte index = 8380*block + 2*region "
         "- same fold, region side walked by the loop" % (seed[1], edx_init[1],
                                                          edx_inc[1], 0x5A9FE6,
                                                          back[1], 0x5A9FED,
                                                          v3, rd3[1]))

    # ---- G4: M279 G6 artifact reproduction: same chain, mid-chain window, free atoms
    e4, d4 = load(0x56802B, 0x568039)
    s4, _ = chain_eval(d4, 0x56802B, 0x568035,
                       {"edi": (1, 0, 0), "edx": (0, 1, 0), "eax": (0, 0, 0)})
    art = s4.get("edx")
    # substitute the seed: edx_atom := 65*edi  =>  a*edi + b*edx = (a + 65b)*edi
    sub = None
    if art is not None and len(art) >= 2:
        sub = (2 * (art[0] + 65 * art[1]), 0, 2 * art[2])
    ok4 = (art == (30, 64, 0) and sub is not None and sub[0] == STRIDE)
    gate(4, ok4,
         "M279 G6 artifact: mid-chain window [0x56802b,0x568035) with edi/edx as "
         "FREE atoms gives edx = %s (the published '(30,64,0)'); substituting the "
         "excluded seed edx := 65*edi yields byte index coef %s - the SAME 8380 "
         "block stride, so '(30,64,0)' was the truncated-window form, computed"
         % (art, sub))

    # ---- G5: provenance of reader1's block atom (the OWNER byte, M278 identity)
    lo5, hi5 = 0x55F650, 0x56AC40
    slots = []
    with open(TEXT, errors="replace") as fh:
        for line in fh:
            m = PAT.match(line)
            if not m or not m.group(3):
                continue
            a = int(m.group(1), 16)
            if a < lo5:
                continue
            if a >= hi5:
                break
            ar = m.group(4).split("#")[0].strip()
            if ar.startswith("DWORD PTR [ebp-0xc]") and m.group(3) in (
                    "mov", "lea", "add", "sub", "inc", "dec", "or", "and"):
                slots.append((a, m.group(3), ar.strip()))
    sole = slots == [(0x55F71D, "mov", "DWORD PTR [ebp-0xc],eax")]
    src = site(0x55F6ED)
    chain13 = (site(0x55F6B8) == ("lea", "ecx,[edi+edi*2]")
               and site(0x55F6BD) == ("lea", "edx,[edi+ecx*4]"))
    owner = site(0x55F6C6)
    ok5 = (sole and src == ("mov", "al,BYTE PTR [esi+0x933286]")
           and chain13 and owner == ("mov", "al,BYTE PTR [edx*4+0x933286]")
           and 13 * 4 == 52)
    gate(5, ok5,
         "provenance(reader1 block): [ebp-0xc] sole writer in FUN_0055f650 = "
         "%s; its value = BYTE[52*edi+0x933286] = unit+14 OWNER (13*4=52, "
         "%s / %s / %s / %s) - e9a8 read keyed on the OWNER block like the "
         "M278 writers" % (slots, site(0x55F6B8)[1], site(0x55F6BD)[1],
                           owner[1], src[1]))

    # ---- G6: containment + walker identity
    ok6 = (own(0x568038) == "FUN_0055f650" and own(0x5A9FD5) == "FUN_005a90a0"
           and own(0x55F71D) == "FUN_0055f650")
    gate(6, ok6, "containment: 0x568038 -> %s, 0x5a9fd5 -> %s, 0x55f71d -> %s "
         "(AI hub + a per-block walker reading OWNER/arg-keyed rows)"
         % (own(0x568038), own(0x5A9FD5), own(0x55F71D)))

    # ---- G7: registry: M280 block + M279 e9a8 row patched in place
    named = open(NAMED, errors="replace").read()
    has280 = re.search(r"^## M280 \(s222", named, re.M) is not None
    m279_row_patched = re.search(r"^\| e9a8.*M280", named, re.M) is not None
    gate(7, has280 and m279_row_patched,
         "registry: NAMED.md carries ## M280 (s222) (%s); M279's e9a8 row cites "
         "M280 (%s) - the retraction lives in the registry" % (has280,
                                                               m279_row_patched))

    n, tot = sum(res), len(res)
    print("SUMMARY M280: %d/%d gates %s" % (n, tot, "PASS" if n == tot else "FAIL"))
    return 0 if n == tot else 1


if __name__ == "__main__":
    sys.exit(main())
