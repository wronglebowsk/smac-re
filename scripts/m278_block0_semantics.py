#!/usr/bin/env python3
"""M278 - block-0 semantics: is block 0 the neutral/player slot or faction 0's REAL row?

Static only, zero box time. Settles the s218 open question by reading the two
0x94eaa8 WRITERS' block-index sources (the pick named FUN_0051dcb0 / FUN_0055f650).

ANSWER: both writers' block index is a PLAYER-INDEX byte, not a loop counter and not
a neutral code:
  writer1 (inc, 0x51df61, FUN_0051dcb0): ebx = BYTE[0x95da14 + 304*i] where i is the
    index returned by FUN_004e37f0 (a walk of the base table: mov ebx,0x95da14,
    add ebx,0x130, count ds:0x985af4) - and 0x95da14 = 0x95da10+4, base+4 = the OWNER
    PLAYER INDEX (M43 identity, 167/167 live). When no base qualifies ebx=-1 and
    0x51df1d-0x51df24 CLAMPS it to 0 immediately before the fold - block 0 is also the
    fallback landing of unowned tiles. No branch ever skips the fold on ebx==0 (the only
    ebx test in the run-up is the sign clamp; its jge jumps into the fold, both legs store).
  writer2 (add -10, 0x564ab1, FUN_0055f650 AI hub): esi = [ebp-0xc], ONE store image-wide
    in the function (0x55f71d), value = BYTE[52*arg + 0x933286] = unit+14 OWNER of the
    acting unit (unit array 0x933278 stride 52, M108/M109; owner @+14 M43), masked
    `and eax,0xff`; the entry cross-checks that byte against ds:0x91b5b4 (current player).
Domain: the row family spans EXACTLY 8 blocks - the zero-init sweep 0x94eca8 -> 0x95f288
steps 0x20bc (8380) 8 times and the per-block min/max loop walks esi 0..7. There is no
ninth neutral block, and the human is not block 0 by definition (M43 recorded the human at
player 3; player 0 was a destroyed-but-still-visited faction owning 199 tiles; "no separate
faction-ID namespace in these records"). So block 0 = player/faction-index-0's REAL row,
DOUBLED as the unowned-verdict fallback via writer1's clamp - not a dedicated neutral slot,
not a player slot. M277's "permanent faction-0 view" of the scaled read stands, refined:
it is that doubled row.
"""
import csv
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
INDEX = os.path.join(ROOT, "ghidra_out", "index.csv")
NAMED = os.path.join(ROOT, "NAMED.md")
TURN = os.path.join(ROOT, "turn_driver.md")
TL = os.path.join(ROOT, "turn_loop_map.md")
NOTES = os.path.join(ROOT, "SESSION_NOTES.md")
M277 = os.path.join(ROOT, "scripts", "m277_scaled_row_ownership.py")
STRIDE, S0 = 8380, 0x20BC
FUN1, FUN1_SZ = 0x51dcb0, 1191
FUN2, FUN2_SZ = 0x55f650, 54483
FOLD1, STORE1 = 0x51df26, 0x51df61
FOLD2, STORE2 = 0x564a9a, 0x564ab1
SWEEP_LO, SWEEP_HI = 0x94ECA8, 0x95F288
BASE_TAB = 0x95DA10
UNIT_LO = 0x933278
OWNER1, OWNER2 = 0x95DA14, 0x933286

# reuse m277's evaluator plumbing WITHOUT running its main() (skill law: do not re-derive)
_src = open(M277).read()
_ns = {"__file__": M277}
# marker is "\ndef main(" NOT "def main(": m277's own source carries the bare string
# inside ITS exec line (line 37), and str.index finds THAT first, slicing mid-literal.
exec(_src[:_src.index("\ndef main(")], _ns)
load, neuter, chain_eval = _ns["load"], _ns["neuter"], _ns["chain_eval"]


def flat(path):
    return re.sub(r"\s+", " ", open(path, errors="replace").read())


def owners():
    idx = [r for r in csv.reader(open(INDEX)) if r and r[0].startswith("0x")]
    def own(addr):
        p = None
        for r in idx:
            s = int(r[0], 16)
            if s <= addr:
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
    ins1 = load(FUN1, FUN1 + FUN1_SZ + 1)[1]   # load() returns (ins_list, addr_dict)
    ins2 = load(FUN2, FUN2 + FUN2_SZ + 1)[1]

    # ---- G1 containment + both folds re-evaluate to (8380, 2, 0) with the BLOCK atom
    cont = (own(STORE1) == own(FOLD1) == "FUN_0051dcb0"
            and own(STORE2) == own(FOLD2) == "FUN_0055f650")
    a1, d1 = load(0x51DF26, 0x51DF3D)
    neuter(d1, [0x51DF28], "ecx load is the region atom of origin")
    s1, _ = chain_eval(d1, 0x51DF26, 0x51DF3B, {"ebx": (1, 0, 0), "ecx": (0, 1, 0)})
    a2, d2 = load(0x564A9A, 0x564AB8)
    neuter(d2, [0x564A9C], "ecx load is the slot atom of origin")
    s2, _ = chain_eval(d2, 0x564A9A, 0x564AAF, {"esi": (1, 0, 0), "ecx": (0, 1, 0)})
    f1, f2 = s1.get("eax"), s2.get("eax")
    gate(1, cont and f1 == (STRIDE, 2, 0) and f2 == (STRIDE, 2, 0),
         "containment: stores %s/%s sit in FUN_0051dcb0/FUN_0055f650 with their folds; both "
         "folds re-evaluate (m276/m277 evaluator, not re-derived) to eax = 8380*(block atom) "
         "+ 2*slot: %s and %s" % (hex(STORE1), hex(STORE2), f1, f2))

    # ---- G2 writer1: the COMPLETE ebx-writer census up to the store; the clamp sequence
    # dst_regs lives in the INNER namespace: m277's exec line rebinds _ns to the
    # dict built from m276's slice, and chain_eval/neuter resolve it the same way.
    dst = _ns["_ns"]["dst_regs"]
    ebxw = [a for a in sorted(ins1) if a <= STORE1 and "ebx" in [x for x in dst(*ins1[a]) if x]]
    cens = {hex(a): "%s %s" % ins1[a] for a in ebxw}
    for k in sorted(cens):
        print("      ebx writer %s: %s" % (k, cens[k]))
    clamp = (ins1[0x51DF1D] == ("test", "ebx,ebx")
             and ins1[0x51DF22] == ("jge", hex(0x51DF26))
             and ins1[0x51DF24] == ("xor", "ebx,ebx")
             and ins1[0x51DF26] == ("mov", "edx,ebx"))
    sentinel = sum(1 for a in ebxw if ins1[a] == ("or", "ebx,0xffffffff"))
    load_owner = ins1[0x51ddff] == ("mov", "bl,BYTE PTR [eax+0x95da14]")
    gate(2, set(map(hex, ebxw)) == {"0x51dd5a", "0x51dd92", "0x51ddbd", "0x51ddea",
                                    "0x51ddf5", "0x51ddff", "0x51defa", "0x51df24"}
         and clamp and sentinel == 3 and load_owner,
         "writer1 ebx census (up to %#x): %d writers: 2 are 0x950a64 region-array POINTERS "
         "(0x51dd5a lea + 0x51dd92 add 0x20bc, the 0x51dd61 loop that incs a DIFFERENT "
         "WORD array, off the block-index path); 3 sentinel `or ebx,-1`; 1 `xor ebx,ebx` "
         "zero-extend before the OWNER-BYTE load `%s %s` (0x95da14 = base table 0x95da10 + 4), "
         "1 clamp `xor ebx,ebx` at 0x51df24 guarded by the ONLY ebx test in the run-up "
         "(0x51df1d) whose jge TARGETS THE FOLD 0x51df26 - both legs (byte>=0 and clamped -1) "
         "flow into the store: ebx at the fold is {owner byte} U {0}"
         % (STORE1, len(ebxw), *ins1[0x51ddff]))

    # ---- G3 the selector IS the base-table walk and the docs already named the byte
    sel = load(0x4e37f0, 0x4e3830)[1]
    sel_all = load(0x4e37f0, 0x4e3990)[1]
    walk = (sel.get(0x4e3822) == ("mov", "ebx,0x95da14")
            and sel.get(0x4e3807) == ("mov", "ecx,DWORD PTR ds:0x985af4")
            and any(v == ("add", "ebx,0x130") for v in sel_all.values())
            and any(v == ("mov", "DWORD PTR ds:0x8f0d34,ecx") for v in sel_all.values())
            and any(v == ("mov", "eax,DWORD PTR [ebp-0x4]") for v in sel_all.values()))
    turnf, namedf = flat(TURN), flat(NAMED)
    iden = ("owner player index" in turnf and "167/167" in turnf
            and "no separate faction-ID namespace" in turnf
            and "304m at 0x95da10" in namedf)
    gate(3, walk and iden,
         "FUN_004e37f0 walks the base table (mov ebx,0x95da14; add ebx,0x130; count "
         "ds:0x985af4; writes distance to ds:0x8f0d34; returns the record index [ebp-0x4]) - "
         "so writer1's byte is base+4, which M43 named from 167/167 live: `+4 ... equal the "
         "OWNER PLAYER INDEX`, `There is no separate faction-ID namespace`, and NAMED records "
         "`bases (304m at 0x95da10)`: the block index is a PLAYER INDEX, 0..7")

    # ---- G4 writer2: [ebp-0xc] has ONE store; its value chain is unit+14 owner
    st_c = [a for a in sorted(ins2) if ins2[a][1].startswith("DWORD PTR [ebp-0xc],")]
    chain = (ins2[0x55f6bb] == ("xor", "eax,eax")
             and ins2[0x55f6b8] == ("lea", "ecx,[edi+edi*2]")
             and ins2[0x55f6bd] == ("lea", "edx,[edi+ecx*4]")
             and ins2[0x55f6c6] == ("mov", "al,BYTE PTR [edx*4+0x933286]")
             and ins2[0x55f6e4] == ("lea", "esi,[edi+ecx*4]")
             and ins2[0x55f6e7] == ("shl", "esi,0x2")
             and ins2[0x55f6ed] == ("mov", "al,BYTE PTR [esi+0x933286]")
             and ins2[0x55f712] == ("and", "eax,0xff")
             and ins2[0x55f71d] == ("mov", "DWORD PTR [ebp-0xc],eax"))
    xchk = (ins2[0x55f6c0] == ("mov", "ecx,DWORD PTR ds:0x91b5b4")
            and ins2[0x55f6cd] == ("cmp", "eax,ecx"))
    reloads = (ins2[0x564a18] == ("mov", "esi,DWORD PTR [ebp-0xc]")
               and ins2[0x564a93] == ("mov", "esi,DWORD PTR [ebp-0xc]"))
    off = (OWNER2 - UNIT_LO == 14 and OWNER1 - BASE_TAB == 4)
    docu = ("52n at 0x933278" in namedf and "owner @+14" in turnf
            and "unit+14 (owner)" in turnf)
    tl = flat(TL) + namedf
    cur = bool(re.search(r"0x91b5b4[^\n]{0,60}?current (player|faction)", tl)
               or re.search(r"current player[^\n]{0,40}?0x91b5b4", tl)
               or ("0x91b5b4` current faction" in namedf))
    gate(4, st_c == [0x55f71d] and chain and xchk and reloads and off and docu and cur,
         "writer2: [ebp-0xc] stores image-wide in the hub = %s ONLY; its value: 13*arg then "
         "<<2 = 52*arg (unit stride), `mov al,BYTE PTR [esi+0x933286]` = 0x933278+14 = the "
         "UNIT OWNER byte (docs: `52n at 0x933278`, `unit+14 (owner)`), masked `and eax,0xff`; "
         "the entry cross-checks it against ds:0x91b5b4 (current player, docs); both fold "
         "branches re-load esi from [ebp-0xc] (0x564a18/0x564a93) - the hub's block index is "
         "the acting unit's OWNER" % [hex(x) for x in st_c])

    # ---- G5 domain: exactly 8 blocks (computed), and the fold stride IS the sweep step
    nblocks = (SWEEP_HI - SWEEP_LO) / S0
    sweep = (ins1[0x51dcb8] == ("mov", "edx,0x94eca8")
             and ins1[0x51dcf7] == ("add", "edx,0x20bc")
             and ins1[0x51dcfd] == ("cmp", "edx,0x95f288")
             and ins1[0x51dd03] == ("jl", "0x51dcbd"))
    mm = (ins1[0x51e10b] == ("add", "ecx,0x20bc") and ins1[0x51e111] == ("cmp", "esi,0x8")
          and ins1[0x51e117] == ("jl", "0x51e091"))
    gate(5, S0 == STRIDE and sweep and mm and (SWEEP_HI - SWEEP_LO) % S0 == 0
         and nblocks == 8,
         "the zero-init sweep walks %#x -> %#x by 0x%x = %d whole faction-stride blocks "
         "(%d == the fold's 8380), and the per-block min/max loop at 0x51e107-0x51e117 walks "
         "esi 0..7 by 0x20bc - the row family has EXACTLY 8 blocks: indices 0..7, no ninth "
         "neutral block (rival '7 factions + 1 neutral column separate from faction 0' needs "
         "index 8 or a skip; neither exists)" % (SWEEP_LO, SWEEP_HI, S0, nblocks, S0))

    # ---- G6 discriminator: attribute every conditional branch to ITS guard instruction
    lin = [a for a in sorted(ins1) if FUN1 <= a <= STORE1]
    lastflag, guarded = None, {}
    for a in lin:
        op, ar = ins1[a]
        if op in ("test", "cmp"):
            lastflag = (a, "%s %s" % (op, ar))
        elif op.startswith("j") and lastflag:
            guarded[hex(a)] = (lastflag, ar)
    ebx_guarded = {k: v for k, v in guarded.items() if "ebx" in v[0][1]}
    for k in sorted(ebx_guarded):
        print("      ebx-guarded branch %s <- guard %#x %s | arg %s"
              % (k, ebx_guarded[k][0][0], ebx_guarded[k][0][1], ebx_guarded[k][1]))
    def tgt(a):
        return int(ebx_guarded[a][1].split(",")[-1].strip(), 0)
    keys = {"0x51de2e", "0x51df03", "0x51df22"}
    reenter = all(tgt(k) <= FOLD1 for k in ebx_guarded) and tgt("0x51df22") == FOLD1
    human3 = "cur=3 our turn" in turnf and "owns 199 tiles" in turnf
    gate(6, set(ebx_guarded) == keys and reenter and human3,
         "DISCRIMINATOR (guard-attributed branch census, FUN_0051dcb0 entry..store): exactly 3 "
         "conditional branches are guarded by an ebx test/cmp: 0x51de2e (scan-loop owner match) "
         "and 0x51df03 (owner-change detection) RE-ENTER the clamp path, 0x51df22 `jge` targets "
         "THE FOLD %#x itself - no ebx-conditional branch skips the store (rival 'block 0 is "
         "neutral: a guard or a +1 bias skips/shifts index 0' finds NEITHER in the bytes; the "
         "0x94eaa8 store's own guards at 0x51df49/51df59/0x51df5f key on tile type/mineral/occupancy bytes, not on "
         "the block index); ours predicts byte==0 stores block 0 directly and -1 clamps INTO "
         "it. And the human was NOT block 0: M43's recorded box has us at `cur=3` with player 0 "
         "owning 199 tiles - block 0 is not the player slot either" % FOLD1)

    # ---- G7 registry: NAMED carries M278 and the M277 block carries the refinement
    named = open(NAMED, errors="replace").read()
    # ANCHOR ON THE FULL HEADER LINE: the bare token "## M277" also occurs as a
    # cross-reference earlier in NAMED.md (split()[1] grabbed that segment once here)
    m78 = re.search(r"## M278 \(s219.*?\n## ", named, re.S)
    m77 = re.search(r"## M277 \(s218.*?(?=## M278 \(s219)", named, re.S)
    blk = m78.group(0) if m78 else ""
    m277blk = m77.group(0) if m77 else ""
    c1, c2, c3 = ("owner player index" in blk, "clamp" in blk.lower(),
                  "M278 REFINEMENT" in m277blk)
    print("      registry check: M278-block=%s owner-clause=%s clamp-clause=%s refine-clause=%s "
          "(blk %d B)" % ("## M278" in named, c1, c2, c3, len(blk)))
    gate(7, c1 and c2 and c3,
         "registry: NAMED.md ## M278 names the block index (owner player index + clamp) and "
         "the ## M277 block carries the M278 REFINEMENT line (%d chars)" % len(blk))

    n, tot = sum(res), len(res)
    print("SUMMARY M278: %d/%d gates %s" % (n, tot, "PASS" if n == tot else "FAIL"))
    return 0 if n == tot else 1


if __name__ == "__main__":
    sys.exit(main())
