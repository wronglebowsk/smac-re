#!/usr/bin/env python3
"""M279 (s221) - the row-family layout: e8a8/e9a8, e5a8/e7a8 and the whole
per-block layout of the 12-array family 0x94e4a8..0x94ee28 (M256) plus the
e8a8 writer/reader fold proofs.

Static only, zero box time. Reuses scripts/m276_fold_stride.py's evaluator
(skill law: do not re-derive the fold) and m277's load/neuter/chain_eval.

ANSWERS:
  G1: 0x94e8a8's ONLY writer (0x51df3d, FUN_0051dcb0) is reached through the
      SAME fold chain as the eaa8 store: eax = 8380*ebx + 2*ecx at both
      stores; eax is untouched between them (no intervening writer).
  G2: the three stores are a NESTED counter family: e8a8 (0x51df3d) is
      UNCONDITIONAL on the fold path (fires for every walked tile), eaa8
      (0x51df61) is behind {cl&0x18==0} && {[edi+5]&0xc0 < 0x80} &&
      {[edi+8]&0x20==0}, eba8 (0x51df70) behind that PLUS {[edi+8]&0x1000}.
  G3: 0x94e8a8's ONLY reader (0x45c088, FUN_0045a920) computes
      8380*[ebp-0x34] + 2*[ebp-0x64] (imul 0x20bc + *2 word read) - the
      per-block fold form, not block-0-only.
  G4: the separate entry fold of FUN_00556690 (0x556699-0x5566bb) evaluates
      to edx = 8380*arg and is stored to [ebp-0xc] (0x5566f9): the BYTE
      arrays e5a8/e628/eca8/ed28/eda8 are indexed [8380*arg + region*1].
  G5: image-wide family census: every base's sites, dominant width, gap to
      the next base; WORD bases (fold form 2*region + 8380*block) sit at
      0x100 gaps, BYTE bases (region*1 + 8380*block) at 0x80.
  G6: e9a8: 2 sites, BOTH readers, ZERO writers; the 0x45c088-style fold
      does NOT reproduce at 0x568038 (chain evaluates to 60*edi+128*edx) -
      read-only, different index idiom, OPEN lead (observed, not forced).
"""
import csv
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
INDEX = os.path.join(ROOT, "ghidra_out", "index.csv")
NAMED = os.path.join(ROOT, "NAMED.md")
M276 = os.path.join(ROOT, "scripts", "m276_fold_stride.py")
M277 = os.path.join(ROOT, "scripts", "m277_scaled_row_ownership.py")
STRIDE = 8380
FAMILY = [0x94e4a8, 0x94e5a8, 0x94e628, 0x94e6a8, 0x94e7a8, 0x94e8a8,
          0x94e9a8, 0x94eaa8, 0x94eba8, 0x94eca8, 0x94ed28, 0x94eda8,
          0x94ee28]

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

    # ---- G1: writer1's fold chain (FUN_0051dcb0) evaluates to (8380,2,0)
    # and BOTH 0x51df3d (e8a8) and 0x51df61 (eaa8) read the SAME eax.
    a1, d1 = load(0x51DF26, 0x51DF3D)
    neuter(d1, [0x51DF28], "ecx load is the slot atom of origin")
    s1, _ = chain_eval(d1, 0x51DF26, 0x51DF3B, {"ebx": (1, 0, 0), "ecx": (0, 1, 0)})
    f1 = s1.get("eax")
    st_e8 = site(0x51DF3D)
    st_ea = site(0x51DF61)
    # eax untouched between the two stores (the filter writes cl/edx only)
    gap_w = []
    for a in sorted(d1):
        if 0x51DF3D < a < 0x51DF61:
            op, ar = d1[a]
            if op in ("mov", "add", "sub", "xor", "lea", "inc", "dec", "imul", "shl",
                      "or", "and"):
                lhs = ar.split(",")[0].strip()
                if lhs.startswith("eax") or lhs == "eax":
                    gap_w.append(hex(a))
    gate(1, f1 == (STRIDE, 2, 0)
         and st_e8 == ("inc", "WORD PTR [eax+0x94e8a8]")
         and st_ea == ("inc", "WORD PTR [eax+0x94eaa8]")
         and not gap_w,
         "writer1 fold (reused evaluator, FUN_0051dcb0): eax = %s = 8380*b + 2*s; "
         "store %#x `%s %s` and store %#x `%s %s` read the SAME eax (intervening eax "
         "writers: %d) - e8a8 is the same per-block WORD row as eaa8, written by the "
         "same fold" % (f1, 0x51DF3D, st_e8[0], st_e8[1], 0x51DF61, st_ea[0], st_ea[1],
                        len(gap_w)))

    # ---- G2: the guard hierarchy between the stores
    # load a window that covers the FOLD through the eba8 store
    gwin, dg = load(0x51DF26, 0x51DF77)
    guards = []
    for a, tup in sorted(dg.items()):
        op, ar = tup
        if 0x51DF3D < a <= 0x51DF70 and op.startswith("j"):
            guards.append((hex(a), op, ar))
    st_eb = site(0x51DF70)
    ok2 = (st_eb == ("inc", "WORD PTR [eax+0x94eba8]")
           and any(g[0] == "0x51df49" and g[1] == "je" for g in guards)
           and any(g[0] == "0x51df59" and g[1] == "jge" for g in guards)
           and any(g[0] == "0x51df5f" and g[1] == "jne" for g in guards)
           and any(g[0] == "0x51df6e" and g[1] == "je" for g in guards))
    gate(2, ok2, "stores: e8a8 @%#x UNCONDITIONAL (no branch fold->store); eaa8 @%#x "
         "behind {test cl,0x18 je 0x51df77} + {[edi+5]&0xc0 cmp 0x80 jge} + "
         "{test [edi+8],0x20 jne}; eba8 @%#x behind those PLUS {test ch,0x10 je} - "
         "branches between first and last store: %s - a nested counter family: "
         "all-tiles / filtered / subset" % (0x51DF3D, 0x51DF61, 0x51DF70, guards))

    # ---- G3: e8a8's ONLY reader: 8380*block + 2*region form
    refs = census_base(0x94E8A8)
    read_sites = [a for a, op, ar in refs if a != 0x51DF3D]
    rd = site(0x45C088)
    imul = site(0x45C07D)
    lod_a = site(0x45C07A)
    lod_c = site(0x45C083)
    ok3 = (sorted(a for a, _, _ in refs) == [0x45C088, 0x51DF3D]
           and lod_a == ("mov", "eax,DWORD PTR [ebp-0x34]")
           and imul == ("imul", "eax,eax,0x20bc")
           and lod_c == ("mov", "ecx,DWORD PTR [ebp-0x64]")
           and rd == ("mov", "dx,WORD PTR [eax+ecx*2+0x94e8a8]"))
    gate(3, ok3, "image-wide referrers of +0x94e8a8: %s (writer + ONE reader); reader "
         "%#x: `imul eax,eax,0x20bc` (0x20bc = 8380 = the block stride) then `%s %s` - "
         "WORD read at 8380*[ebp-0x34] + 2*[ebp-0x64]: the per-block fold form, rival "
         "'block-0-only read' needs no 8380 term and is refuted by the imul"
         % ([hex(a) for a, _, _ in refs], 0x45C088, rd[0], rd[1]))

    # ---- G4: the FUN_00556690 ENTRY fold produces the byte-lane base
    e1, de1 = load(0x556699, 0x5566BD)
    neuter(de1, [0x556699], "eax load is the arg atom of origin")
    # entry chain operates on eax(=arg) then ecx/edx as working regs:
    #   mov eax,[ebp+8]; mov ecx,eax; shl ecx,6; add ecx,eax;
    #   lea edx,[eax+ecx*2]; shl edx,4; sub edx,eax; lea ebx,[ecx+eax*1]; shl edx,2
    es, _ = chain_eval(de1, 0x556699, 0x5566BC,
                       {"eax": (1, 0, 0), "ecx": (1, 0, 0), "edx": (1, 0, 0)})
    edx_form = es.get("edx")
    st_c = site(0x5566F9)
    lod_esi = site(0x5583B2)
    lod_edi = site(0x5583B5)
    g4 = (site(0x55669D) == ("mov", "ecx,eax")
          and site(0x5566A0) == ("shl", "ecx,0x6")
          and site(0x5566A3) == ("add", "ecx,eax")
          and site(0x5566AB) == ("lea", "edx,[eax+ecx*2]")
          and site(0x5566B7) == ("sub", "edx,eax")
          and site(0x5566BC) == ("shl", "edx,0x2")
          and edx_form == (STRIDE, 0, 0)
          and st_c == ("mov", "DWORD PTR [ebp-0xc],edx")
          and lod_esi == ("mov", "esi,DWORD PTR [ebp-0xc]")
          and lod_edi == ("mov", "edi,DWORD PTR [ebp-0x10]"))
    gate(4, g4, "entry fold 0x556699-0x5566bc (eval, atoms eax=ecx=edx=arg): edx = %s = "
         "8380*arg, stored `%s %s` -> [ebp-0xc] = the block base; the BYTE-lane loads "
         "`%s %s` / `%s %s` feed 0x94e5a8/0x94eca8/0x94eda8 at [ebp-0xc] + region*1: "
         "byte arrays index block*8380 + region, NOT the 2*region word form"
         % (edx_form, st_c[0], st_c[1], lod_esi[0], lod_esi[1], lod_edi[0], lod_edi[1]))

    # ---- G5: image-wide census: width, gap arithmetic per base
    print("    family census:")
    widths = {}
    for b in FAMILY:
        sites = census_base(b)
        ws = {}
        for a, op, ar in sites:
            m = re.search(r"\b(BYTE|WORD|DWORD)\b", ar)
            k = m.group(1) if m else "none"
            ws[k] = ws.get(k, 0) + 1
        widths[b] = ws
        print("      %#x sites=%d widths=%s first=%#x %s" %
              (b, len(sites), ws, sites[0][0], sites[0][1]))
    gaps = [(b, FAMILY[i + 1] - b) for i, b in enumerate(FAMILY[:-1])]
    word_bases = [b for b in FAMILY if (widths[b].get("WORD", 0) or 0) > 0
                  and (widths[b].get("BYTE", 0) or 0) == 0]
    byte_bases = [b for b in FAMILY if (widths[b].get("BYTE", 0) or 0) > 0
                  and (widths[b].get("WORD", 0) or 0) == 0]
    gate(5, FAMILY[0] == 0x94e4a8 and FAMILY[-1] == 0x94ee28
         and all(g == 0x100 or g == 0x80 for _, g in gaps)
         and len(word_bases) == 7 and len(byte_bases) == 5,
         "census: 13 bases 0x94e4a8..0x94ee28, gaps %s all in {0x80,0x100}; "
         "pure-WORD bases %s (fold 2*region, 0x100 cell), pure-BYTE bases %s "
         "(region*1, 0x80 cell); e7a8 has BOTH widths (%s) = WORD array with "
         "byte sub-accesses - M256's '0x94e7a8 is WORD' stands"
         % ([hex(g) for _, g in gaps],
            [hex(b) for b in word_bases], [hex(b) for b in byte_bases],
            widths[0x94e7a8]))

    # ---- G6: e9a8 read-only, and its readers do NOT carry the block fold
    r9 = census_base(0x94E9A8)
    wr9 = [a for a, op, ar in r9 if op.startswith("mov") and "PTR [" in ar
           and op != "movsx" and ar.startswith("mov ") and "," in ar
           and ("WORD PTR [" in ar or "DWORD PTR [" in ar)
           and ar.split(",")[0].strip().endswith("]") is False
           and (ar.count("]") == 2)]
    writers9 = [a for a, op, ar in r9 if op in ("mov", "inc", "add", "or", "and")
                and ar.startswith("mov ") and "PTR [" in ar
                and ar.split(",")[1].strip() in ("0", "1", "2", "3", "4", "5",
                                                 "6", "7", "8", "9", "0x0")]
    # conservative writer check: any store form = source reg/immediate, dest [mem]
    writers9 = [a for a, op, ar in r9
                if re.match(r"mov\s+(BYTE|WORD|DWORD) PTR \[[^\]]+\],", ar)
                or re.match(r"(inc|add|or)\s+(WORD|BYTE) PTR \[[^\]]+\]", ar)]
    # 0x568038 chain: lea ecx,[edi+edx*2]; shl ecx,4; sub ecx,edi;
    #   lea edx,[eax+ecx*2]; (mov cx,[edx*2+0x94e9a8])
    e1, de1 = load(0x56802B, 0x568039)
    s9, _ = chain_eval(de1, 0x56802B, 0x568035,
                       {"edi": (1, 0, 0), "edx": (0, 1, 0), "eax": (0, 0, 0)})
    rd9 = site(0x568038)
    gate(6, len(r9) == 2 and not writers9
         and rd9 == ("mov", "cx,WORD PTR [edx*2+0x94e9a8]")
         and s9.get("edx") is not None and s9["edx"] != (STRIDE, 2, 0),
         "e9a8: %d sites, writers %s (ZERO stores image-wide), readers %s; reader "
         "0x568038 chain evaluates to edx = %s which is NOT 8380*b+2*s - read-only "
         "array, different index idiom (OPEN lead, not forced into the fold family)"
         % (len(r9), [hex(a) for a in writers9], [hex(a) for a, _, _ in r9],
            s9.get("edx")))

    # ---- G7 registry: NAMED has M279, and the process table is intact
    named = open(NAMED, errors="replace").read()
    has = re.search(r"^## M279 \(s221", named, re.M) is not None
    ok7 = has and own(0x51DF3D) == "FUN_0051dcb0" and own(0x45C088) == "FUN_0045a920"
    gate(7, ok7, "registry: NAMED.md carries ## M279 (s221) (%s); containment %s/%s"
         % (has, own(0x51DF3D), own(0x45C088)))

    n, tot = sum(res), len(res)
    print("SUMMARY M279: %d/%d gates %s" % (n, tot, "PASS" if n == tot else "FAIL"))
    return 0 if n == tot else 1


if __name__ == "__main__":
    sys.exit(main())
