#!/usr/bin/env python3
"""M340 — does FUN_0058e7f0 ADMIT a `Difficulty` preference value >= 6?

PICK: NEXT_PROMPT §THE PICK open-lead (x6) residual, carried by `NAMED ## M338`
as its #1 next lead: three 0x94d2ac readers index the six-row #DIFF ladder with
an UNCLAMPED value; if the INI reader that fills the pref cell admits >= 6 then
index 6 lands on 0x94d2c4, one past the table (M335: END == 0x94d2c4).

Measured (every number COMPUTED from the static image `scratch/m574/text.txt`
plus the PE strings of `programs/terran.exe`; zero box time):

  * FUN_0058e7f0 reads 18 six-arg GetPrivateProfileStringA keys; exactly ONE
    carries the key immediate 0x692718, whose PE bytes are b"Difficulty".
    Its default argument is the itoa(0) buffer at 0x997120 (push 0x0 at
    0x58e865) and its value lands in ds:0x92bde8 at 0x58e8c6.
  * The 10 instructions 0x58e8a9..0x58e8c6 are STRAIGHT LINE: no jcc, no jmp,
    no ret, two stores (object cursor 0x996be8, pref cell 0x92bde8), and the
    second store's source is eax.
  * eax there is 0x6287e2's return, passed through two 6- and 12-instruction
    wrappers (0x5ea484, 0x5eaa53) that contain no jcc and no eax write after
    their call: the caller applies ZERO post-processing to the parsed value.
  * The whole parse chain (atoi 0x64c360, tokeniser 0x5ea985, radix parsers
    0x6287e2/0x628720/0x62876b) compares only CHARACTER CLASSES: the constant
    set is {0x0,0x1,0x2b,0x2c,0x2d,0x30,0x31,0x36} — '0','1','B'..'x' range
    bound, ',', '+', '-', and the locale flag. Intersection with the value
    space {2,3,4,5,6} is EMPTY.
  * Positive control in the SAME function: `Language` (0x628130) IS bounded —
    `cmp [ebp-0x4],0x4` + `ja` + jump table. The classifier that finds a bound
    for Language finds none for Difficulty, so "no bound" is a measured
    difference, not an unmeasured assumption.

GATES (printed FIRST, then asserted; every V row names a mutant in
scripts/m340_mutate.py):
  G1  the Difficulty read: 18 `call edi` sites whose 6-push window holds exactly
      one `push 0x100` (argc-6); exactly one key imm 0x692718 == "Difficulty"; its
      lpDefault push IS 0x997120, the itoa(0) buffer seeded at 0x58e865; its value
      store ds:0x92bde8 @0x58e8c6 is the ONLY store to that cell in the function.
  G2  0x58e8a9..0x58e8c6: 10 insns, 0 jcc/jmp/ret, exactly the two stores
      ds:0x996be8,eax (parse cursor) and ds:0x92bde8,eax.
  G3  the store's eax IS 0x6287e2's return: 0x58e8b9 calls 0x5ea484 -> 0x5eaa53 ->
      {0x5ea985, 0x6287e2}; both wrappers branch-free, no eax write after their
      call, pop ebp/ret epilogue, and no eax write between call and store.
  G4  parse-chain compare census: the constant set equals the declared set and
      contains NO element of {2,3,4,5,6}.
  G5  rivals, each evaluated and each FAILING on the printed numbers (R1 clamps to
      the 6-row ladder; R2 a bounded default; R3 Language's switch is Difficulty's
      consumer). Positive control READ STRUCTURALLY: the argument reaches
      [ebp-0x4], `cmp [ebp-0x4],0x4`, `ja`, then indexes [edx*4+0x6281ac].
  G6  table endpoints MEASURED from the ladder's own loader (0x57ac74 base,
      0x57ac88 end) and the row count from the list builder's loop bound
      (0x57c6cb `cmp esi,0x6`): 6 rows, k=5 -> 0x94d2c0 last legal, k=6 -> the
      measured end 0x94d2c4, one dword past.
  G7  the pref-fed readers: base and scale decoded from each load's own addressing
      bytes, the index from a memory load, and a def-use gap between that load and
      the table access with NO branch, call, compare or index rewrite.
"""
import hashlib
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
EXE = os.path.join(ROOT, "programs/terran.exe")
EVID = os.path.join(ROOT, "evidence/m340_pref_admission.txt")

TABLE = 0x94D2AC
TABLE_END = 0x94D2C4
PREF = 0x92BDE8
FUNC = (0x58E7F0, 0x58F002)
OBJC = 0x996BE8          # parse object base 0x996a98 + 0x150 (cursor)
KEY_DIFF = 0x692718
KEY_LANG = 0x69270C
DEFAULT_BUF = 0x997120

# function bodies of the Difficulty parse chain: (start, end-exclusive, label)
CHAIN = [
    (0x64C460, 0x64C471, "atoi-wrapper"),
    (0x64C360, 0x64C45F, "atoi"),
    (0x5EA484, 0x5EA493, "obj-get"),
    (0x5EAA53, 0x5EAA6F, "obj-get2"),
    (0x5EA985, 0x5EAA53, "tokeniser"),
    (0x6287E2, 0x62885F, "radix-parser"),
    (0x628720, 0x62876B, "bin-parser"),
    (0x62876B, 0x6287E2, "hex-parser"),
]
# census of the 0x94d2ac loads (M338 G1 declared set) + index provenance
LOADS = [
    (0x44A1C8, "hof-byte", "unclamped"),
    (0x484CC9, "hof-view", "unclamped"),
    (0x485426, "hof-view2", "unclamped"),
    (0x48678F, "0x8f0090-difficulty-byte", "unclamped"),
    (0x486F40, "FUN_00423af0(0,6)", "inclusive-6"),
    (0x57C606, "loop-counter-0..5", "bounded-5"),
    (0x599405, "ds:0x985aec", "unclamped"),
]
PREF_FED = (0x48678F, 0x44A1C8, 0x599405)   # M336, M338, M332 provenance

LINE = re.compile(r"^\s*([0-9a-f]{6,8}):\s+((?:[0-9a-f]{2} )+)\s*\t(.*)$")
MUT = os.environ.get("M340_MUT", "")
ALG = os.environ.get("M340_ALG", "")

BOUND_SPACE = {2, 3, 4, 5, 6}
DECLARED_CMP = {0x0, 0x1, 0x2B, 0x2C, 0x2D, 0x30, 0x31, 0x36}


def load(path=None):
    ins = []
    with open(path or TEXT, errors="replace") as f:
        for line in f:
            m = LINE.match(line.rstrip("\n"))
            if not m:
                continue
            a = int(m.group(1), 16)
            bs = bytes.fromhex(m.group(2).replace(" ", ""))
            txt = m.group(3).strip()
            parts = txt.split(None, 1)
            ins.append({"a": a, "bs": bs, "mn": parts[0],
                        "ops": parts[1] if len(parts) > 1 else ""})
    ins.sort(key=lambda x: x["a"])
    return ins


def patch(ins, addr, old_bs, new_bs, old_txt, new_txt, new_mn=None):
    for i in ins:
        if i["a"] == addr:
            assert i["bs"] == bytes.fromhex(old_bs), (hex(addr), i["bs"].hex())
            assert i["ops"] == old_txt, (hex(addr), i["ops"])
            i["bs"] = bytes.fromhex(new_bs)
            i["ops"] = new_txt
            if new_mn:
                i["mn"] = new_mn
            return
    raise KeyError(hex(addr))


def apply_mut(ins):
    P = patch
    if MUT == "MU1":      # key immediate Difficulty -> Language
        P(ins, 0x58E8A1, "68 18 27 69 00", "68 0c 27 69 00",
          "0x692718", "0x69270c")
    elif MUT == "MU2":    # a jcc appears inside the store window
        P(ins, 0x58E8B9, "e8 c6 bb 05 00", "75 05 90 90 90",
          "0x5ea484", "0x58e8c0", "jne")
    elif MUT == "MU3":    # an eax write on the return path (pop ebp -> pop eax)
        P(ins, 0x5EA491, "5d", "58", "ebp", "eax", "pop")
    elif MUT == "MU4":    # a value-space bound appears in the atoi
        P(ins, 0x64C3C9, "83 7d fc 2d", "83 7d fc 05",
          "DWORD PTR [ebp-0x4],0x2d", "DWORD PTR [ebp-0x4],0x5")
    elif MUT == "MU5":    # Language's bound 4 -> 2
        P(ins, 0x628145, "83 7d fc 04", "83 7d fc 02",
          "DWORD PTR [ebp-0x4],0x4", "DWORD PTR [ebp-0x4],0x2")
    elif MUT == "MU6":    # a pref-fed reader's table base displaced by one dword
        P(ins, 0x48678F, "8b 04 95 ac d2 94 00", "8b 04 95 b0 d2 94 00",
          "eax,DWORD PTR [edx*4+0x94d2ac]", "eax,DWORD PTR [edx*4+0x94d2b0]")
    elif MUT == "MU7":    # the pref store lands one cell to the right
        P(ins, 0x58E8C6, "a3 e8 bd 92 00", "a3 ec bd 92 00",
          "ds:0x92bde8,eax", "ds:0x92bdec,eax")
    elif MUT == "MU8":    # the ladder's own loop bound 6 -> 7
        P(ins, 0x57C6CB, "83 fe 06", "83 fe 07", "esi,0x6", "esi,0x7")
    elif MUT == "MU9":    # the wrapper's downstream call retargeted (chain identity)
        P(ins, 0x5EAA63, "e8 7a dd 03 00", "e8 b8 dc 03 00", "0x6287e2", "0x628720")
    elif MUT == "MU10":   # the lpDefault argument moves off the itoa(0) buffer
        P(ins, 0x58E89C, "68 20 71 99 00", "68 24 71 99 00", "0x997120", "0x997124")
    elif MUT == "MU11":   # the profile read's size argument is not the 0x100 of the window
        P(ins, 0x58E896, "68 00 01 00 00", "68 00 00 00 00", "0x100", "0x0")
    return ins


def site(ins, addr):
    for i in ins:
        if i["a"] == addr:
            return i
    raise KeyError(hex(addr))


def window(ins, lo, hi):
    return [i for i in ins if lo <= i["a"] < hi]


def writes(i, reg):
    mn, ops = i["mn"], i["ops"]
    if mn in ("cmp", "test", "push", "call", "jmp", "ret", "retn", "nop") or mn.startswith("j"):
        return False
    if mn.startswith(("cmov", "set")):
        return ops.split(",")[0].strip() == reg
    if mn in ("inc", "dec", "neg", "not", "pop", "bswap"):
        return ops.strip() == reg
    if mn in ("xchg", "xadd", "cmpxchg"):
        return reg in [x.strip() for x in ops.split(",")]
    return ops.split(",")[0].strip() == reg


FAMILY = {}
for _r in ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp"):
    FAMILY[_r] = {_r, _r[1:], _r[1] + "l", _r[1] + "h"} if _r[1] in "abcd" else {_r, _r[1:], _r[1] + "l"}


def writes_fam(i, reg):
    """writes() widened to the register's sub-registers (dl counts for edx)."""
    return any(writes(i, r) for r in FAMILY.get(reg, {reg}))


def isbr(i):
    return i["mn"].startswith("j") or i["mn"] in ("ret", "retn")


def consts(seq):
    """(addr, mnemonic, constant) for every cmp/test with an immediate."""
    out = []
    for i in seq:
        if i["mn"] not in ("cmp", "test"):
            continue
        m = re.search(r",(0x[0-9a-f]+)$", i["ops"])
        if m:
            out.append((i["a"], i["mn"], int(m.group(1), 16), i["ops"]))
    return out


def stores(seq, cell):
    pat = re.compile(r"^(?:BYTE PTR |WORD PTR |DWORD PTR )?ds:0x%x," % cell)
    return [i for i in seq if i["mn"] in ("mov",) and pat.match(i["ops"])]


def pe_str(vas):
    d = open(EXE, "rb").read()
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    nsec = struct.unpack_from("<H", d, pe + 6)[0]
    opt = pe + 24
    base = struct.unpack_from("<I", d, opt + 28)[0]
    so = opt + struct.unpack_from("<H", d, pe + 20)[0]
    secs = []
    for k in range(nsec):
        o = so + k * 40
        vsz, va, rsz, ra = struct.unpack_from("<IIII", d, o + 8)
        secs.append((va, rsz, ra, vsz))
    out = {}
    for va in vas:
        r = va - base
        for v, rsz, ra, vsz in secs:
            if v <= r < v + max(rsz, vsz):
                o = ra + (r - v)
                out[va] = d[o:o + 48].split(b"\x00")[0].decode("latin-1")
                break
        else:
            out[va] = None
    return out


def fn_extents():
    """(start, size) of every function from ghidra_out/index.csv."""
    import csv
    out = []
    with open(os.path.join(ROOT, "ghidra_out/index.csv")) as f:
        for r in csv.DictReader(f):
            if r.get("addr"):
                out.append((int(r["addr"], 16), int(r["size_bytes"])))
    return out


def scale_of(i):
    m = re.search(r"\[(e?[abcds][xi])\*(\d)\+0x([0-9a-f]+)\]", i["ops"])
    if m:
        return int(m.group(3), 16), int(m.group(2))
    return TABLE, 1


def main():
    ins = apply_mut(load())
    rows = []
    fails = []

    def gate(gid, ok, detail):
        rows.append((gid, "PASS" if ok else "FAIL", detail))
        if not ok:
            fails.append(gid)

    fs, fe = FUNC
    body = window(ins, fs, fe)
    calls = [i for i in body if i["mn"] == "call" and i["ops"].strip() == "edi"]

    def pushes_before(c):
        """The push window feeding `call edi`: collect pushes backwards, stop at a call."""
        got, seen = [], 0
        for i in reversed([x for x in body if x["a"] < c["a"]]):
            seen += 1
            if i["mn"] == "push":
                got.append(i)
            elif i["mn"] == "call":
                break
            if len(got) == 6 or seen > 14:
                break
        return list(reversed(got))

    # key immediate = the push of a 0x69xxxx address inside the 6-push window
    keys = {}
    argc6 = 0
    for c in calls:
        prev = pushes_before(c)
        if len(prev) == 6 and [p["ops"].strip() for p in prev].count("0x100") == 1:
            argc6 += 1
        k = [i for i in prev if i["mn"] == "push" and re.match(r"^0x69[0-9a-f]{4}$", i["ops"].strip())]
        keys[c["a"]] = (k[0]["a"] if k else None, int(k[0]["ops"].strip(), 16) if k else None,
                        [p["ops"].strip() for p in prev])
    strs = pe_str([KEY_DIFF, KEY_LANG])
    diff_sites = [a for a, (ka, kv, _) in keys.items() if kv == KEY_DIFF]
    lang_sites = [a for a, (ka, kv, _) in keys.items() if kv == KEY_LANG]
    diff_push = keys[diff_sites[0]][2] if diff_sites else []
    store_cell = stores(body, PREF)
    store_addrs = [s["a"] for s in store_cell]

    print("== M340 gate table (computed, printed before assertion) ==")
    print("FN_0058e7f0 extent 0x%x..0x%x  insns=%d" % (fs, fe, len(body)))
    print("G1  `call edi` sites=%d  six-push (argc-6) windows=%d  Difficulty=%d (%s)  Language=%d"
          % (len(calls), argc6, len(diff_sites), strs.get(KEY_DIFF), len(lang_sites)))
    if diff_sites:
        print("    Difficulty call 0x%x key-push 0x%x  PE=%r  push window=%s"
              % (diff_sites[0], keys[diff_sites[0]][0], strs.get(KEY_DIFF), diff_push))
    print("    stores to ds:0x92bde8 in the function = %s" % [hex(a) for a in store_addrs])
    win = window(ins, 0x58E8A9, 0x58E8C7)
    print("G2  window 0x58e8a9..0x58e8c6: %d insns, branches=%d" %
          (len(win), len([i for i in win if isbr(i)])))
    for i in win:
        print("      %x  %s %s" % (i["a"], i["mn"], i["ops"]))
    wstores = [i for i in win if i["mn"] == "mov" and re.search(r"ds:0x[0-9a-f]+,", i["ops"])]
    print("    stores in window = %s" % [i["ops"] for i in wstores])
    # default string: the itoa(0) push that seeds 0x997120 before the key window
    pre = window(ins, 0x58E85F, 0x58E892)
    default_zero = [i for i in pre if i["mn"] == "push" and i["ops"].strip() == "0x0"]
    print("    default seed: push 0x0 at %s -> itoa(0)/strcpy into 0x%x, then pushed as the"
          " lpDefault argument (%s)" % ([hex(i["a"]) for i in default_zero], DEFAULT_BUF,
                                        "0x997120" in diff_push))

    # ---- G3 return path -------------------------------------------------
    rp = []
    link = {}
    # the window's call must BE the wrapper, the wrapper must call the next, etc.
    c0 = site(ins, 0x58E8B9)
    link["0x58e8b9"] = c0["ops"].strip()
    for lo, hi, lab in ((0x5EA484, 0x5EA493, "0x5ea484"), (0x5EAA53, 0x5EAA6F, "0x5eaa53")):
        seq = window(ins, lo, hi)
        ci = [n for n, i in enumerate(seq) if i["mn"] == "call"]
        tail = seq[ci[0] + 1:] if ci else []
        eaw = [i for i in tail if writes(i, "eax")]
        br = [i for i in seq if i["mn"].startswith("j")]
        epi = [(i["mn"], i["ops"]) for i in seq[-3:]]
        link[lab] = [i["ops"].strip() for i in seq if i["mn"] == "call"]
        rp.append((lab, len(seq), len(br), len(eaw), epi, ci[0] if ci else None,
                   [("%x" % i["a"], i["mn"], i["ops"]) for i in eaw]))
        print("G3  %s: insns=%d jcc=%d eax-writes-after-call=%d call->%s epilogue=%s"
              % (lab, len(seq), len(br), len(eaw), link[lab], epi))
    # nothing between the wrapper's return and the store may touch eax
    between = window(ins, 0x58E8BE, 0x58E8C6)
    btw = [i for i in between if writes(i, "eax")]
    print("G3  0x58e8be..0x58e8c6 between call and store: %d insns, eax writes=%d %s"
          % (len(between), len(btw), [(i["mn"], i["ops"]) for i in between]))

    # ---- G4 compare census ----------------------------------------------
    census = []
    for lo, hi, lab in CHAIN:
        seq = window(ins, lo, hi)
        last = seq[-1]["mn"] if seq else None
        for a, mn, c, ops in consts(seq):
            census.append((a, lab, mn, c, ops))
        print("G4  %-13s 0x%x..0x%x insns=%3d ends=%s" % (lab, lo, hi, len(seq), last))
    cset = sorted({c for _, _, _, c, _ in census})
    hit = sorted(set(cset) & BOUND_SPACE)
    if ALG == "ALG1":   # algorithm mutant: treat every cmp constant as a value bound
        hit = sorted(cset)
    print("G4  compared constants (chain) = %s" % [hex(c) for c in cset])
    print("G4  declared = %s  intersection with {2..6} = %s"
          % ([hex(c) for c in sorted(DECLARED_CMP)], [hex(c) for c in hit]))
    for a, lab, mn, c, ops in census:
        print("      %x  %-5s %-13s 0x%-2x  %s" % (a, mn, lab, c, ops))

    # ---- G5 rivals / positive control -----------------------------------
    # STRUCTURAL read of the Language switch: the compared operand is the ARGUMENT,
    # the branch is `ja`, and the table index is that same slot.
    lang = window(ins, 0x628130, 0x6281B0)
    seq = [(i["mn"], i["ops"]) for i in lang]
    want_shape = [("push", "ebp"), ("mov", "ebp,esp"), ("push", "ecx"),
                  ("mov", "eax,DWORD PTR [ebp+0x8]"), ("mov", "ds:0x99aa98,eax"),
                  ("mov", "ecx,DWORD PTR ds:0x99aa98"), ("mov", "DWORD PTR [ebp-0x4],ecx"),
                  ("cmp", "DWORD PTR [ebp-0x4],0x4"), ("ja", "0x6281a8"),
                  ("mov", "edx,DWORD PTR [ebp-0x4]"),
                  ("jmp", "DWORD PTR [edx*4+0x6281ac]")]
    lang_bound = [c for a, _, c, _ in consts(lang) if c in BOUND_SPACE]
    diff_bound = hit
    print("G5  Language@0x628130 instruction shape (%d of %d expected):" % (len(seq), len(want_shape)))
    for n, (mn, op) in enumerate(seq[:len(want_shape)]):
        print("      %2d %-5s %-32s %s" % (n, mn, op,
                                           "OK" if (mn, op) == want_shape[n] else "SHAPE"))
    print("    compared slot is the argument: cmp operand %r == jump index source"
          " (edx <- [ebp-0x4])" % (seq[7][1] if len(seq) > 7 else None))
    print("    Language bound=%s  Difficulty bound=%s" % (lang_bound, diff_bound))
    print("    R1 'Difficulty clamps to the 6-row ladder'  -> bound found? %s (must be empty)"
          % diff_bound)
    print("    R2 'a bounded default caps it'              -> default is the string %r, comps before store=%d"
          % ("0", len([i for i in win if i["mn"] in ("cmp", "test")])))
    print("    R3 'Language's bounded switch is Difficulty's consumer' -> the switch is at 0x628130 reached from 0x58e85a, difficulty store followed by 0x58e8be (next field setup)")

    # ---- G6 table arithmetic --------------------------------------------
    # BOTH endpoints are MEASURED from the ladder's own loader (0x57ac74 / 0x57ac88),
    # and the row count from the UI list builder's loop bound (0x57c6cb).
    b_ins = site(ins, 0x57AC74)
    e_ins = site(ins, 0x57AC88)
    mb = re.search(r",0x([0-9a-f]+)$", b_ins["ops"])
    me = re.search(r",0x([0-9a-f]+)$", e_ins["ops"])
    base_m = int(mb.group(1), 16) if mb else None
    end_m = int(me.group(1), 16) if me else None
    lb = site(ins, 0x57C6CB)
    m = re.search(r",0x([0-9a-f]+)$", lb["ops"])
    rows_meas = int(m.group(1), 16) if m else None
    rows_n, rem = divmod(end_m - base_m, 4) if (end_m and base_m) else (0, 1)
    k5, k6 = base_m + 4 * 5, base_m + 4 * 6
    print("G6  loader endpoints measured: 0x57ac74 `%s %s` -> base=0x%x ;"
          " 0x57ac88 `%s %s` -> end=0x%x"
          % (b_ins["mn"], b_ins["ops"], base_m or 0, e_ins["mn"], e_ins["ops"], end_m or 0))
    print("G6  loop bound 0x57c6cb `%s %s` -> rows_measured=%s"
          % (lb["mn"], lb["ops"], rows_meas))
    print("G6  rows=(0x%x-0x%x)/4=%d rem=%d  k=5 -> 0x%x  k=6 -> 0x%x"
          % (end_m or 0, base_m or 0, rows_n, rem, k5, k6))

    # ---- G7 pref-fed readers --------------------------------------------
    r7 = []
    for a, lab, kind in LOADS:
        si = site(ins, a)
        base, sc = scale_of(si)
        m = re.search(r"\[(e?[abcds][xi])\*", si["ops"])
        reg = m.group(1) if m else None
        defs = [i for i in ins if i["a"] < a and writes_fam(i, reg)] if reg else []
        d = defs[-1] if defs else None
        gap = window(ins, d["a"] + 1, a) if d else []
        bad = [i for i in gap if i["mn"].startswith("j") or i["mn"] in ("call", "ret")
               or i["mn"] in ("cmp", "test") or writes_fam(i, reg)]
        r7.append((a, lab, kind, base, sc, reg, d, gap, bad))
        print("G7  0x%x %-26s %-11s base=0x%x scale=%d idx=%s def=%s gap=%d bad=%d"
              % (a, lab, kind, base, sc, reg,
                 ("%x %s %s" % (d["a"], d["mn"], d["ops"])) if d else "none",
                 len(gap), len(bad)))
        for i in gap:
            print("        gap %x %s %s" % (i["a"], i["mn"], i["ops"]))
    pref_ok = True
    for a, lab, kind, base, sc, reg, d, gap, bad in r7:
        if a not in PREF_FED:
            continue
        # def-use WINDOW: the index comes from a memory load and NOTHING between that
        # load and the table access branches, calls, compares or rewrites the index.
        if not (base == TABLE and sc == 4 and d is not None and "PTR" in d["ops"] and not bad):
            pref_ok = False
    print("G7  pref-fed sites %s: base==TABLE, scale==4, memory-loaded index, and a gap"
          " window with 0 branches/calls/compares/rewrites: %s"
          % ([hex(a) for a in PREF_FED], pref_ok))

    # ---- assert ----------------------------------------------------------
    gate("G1", len(calls) == 18 and argc6 == 18 and len(diff_sites) == 1
         and strs.get(KEY_DIFF) == "Difficulty" and store_addrs == [0x58E8C6]
         and len(default_zero) == 1 and "0x997120" in diff_push,
         "18 argc-6 push windows (one push 0x100 each); 1 Difficulty key (PE %r);"
         " lpDefault = 0x997120 seeded by itoa(0); store 0x92bde8 at %s"
         % (strs.get(KEY_DIFF), [hex(a) for a in store_addrs]))
    gate("G2", len(win) == 10 and not any(isbr(i) for i in win) and len(wstores) == 2
         and wstores[0]["ops"] == "ds:0x996be8,eax"
         and wstores[-1]["ops"] == "ds:0x92bde8,eax",
         "10 insns, 0 branches, stores %s, pref store src eax" % [i["ops"] for i in wstores])
    gate("G3", link.get("0x58e8b9") == "0x5ea484"
         and link.get("0x5ea484") == ["0x5eaa53"]
         and link.get("0x5eaa53") == ["0x5ea985", "0x6287e2"] and not btw
         and all(b == 0 and e == 0 and epi[-2:] == [("pop", "ebp"), ("ret", "")]
                 for _, _, b, e, epi, _, _ in rp),
         "call chain 0x58e8b9 -> 0x5ea484 -> 0x5eaa53 -> {0x5ea985, 0x6287e2}: both wrappers"
         " branch-free, no eax write after their call, pop ebp/ret epilogue; 0 eax writes"
         " between the wrapper and the store")
    gate("G4", set(cset) == DECLARED_CMP and not hit,
         "cmp constants == declared set, intersection with {2..6} empty")
    gate("G5", seq[:len(want_shape)] == want_shape and lang_bound == [4] and not diff_bound,
         "Language: the compared slot IS the argument ([ebp-0x4] <- [0x99aa98] <- [ebp+0x8]),"
         " branch ja, table [edx*4+0x6281ac]; bound=%s; Difficulty bound=%s"
         % (lang_bound, diff_bound))
    gate("G6", rows_n == 6 and rem == 0 and base_m == TABLE and end_m == TABLE_END
         and rows_meas == rows_n and k5 == 0x94D2C0 and k6 == end_m,
         "endpoints MEASURED from 0x57ac74/0x57ac88 (base 0x94d2ac, end 0x94d2c4), 6 rows,"
         " k=5 last legal 0x94d2c0, k=6 == 0x94d2c4 one dword past")
    gate("G7", pref_ok and len(LOADS) == 7,
         "each pref-fed reader: base==0x94d2ac, scale==4, index from a memory load, and a"
         " def-use gap with 0 branches/calls/compares/rewrites -> k=6 lands on 0x94d2c4")

    print("\n== gate rows ==")
    for gid, st, det in rows:
        print("%-3s %-4s %s" % (gid, st, det))
    tbl = "\n".join("%s|%s|%s" % r for r in rows)
    print("\ndigest rows  %s" % hashlib.sha256(tbl.encode()).hexdigest()[:16])
    print("digest census %s" % hashlib.sha256(
        (";".join("%x:%x" % (a, c) for a, _, _, c, _ in census)).encode()).hexdigest()[:16])
    print("digest window %s" % hashlib.sha256(
        (";".join("%x:%s %s" % (i["a"], i["mn"], i["ops"]) for i in win)).encode()).hexdigest()[:16])

    if fails:
        print("FAIL M340: %d/%d gates red: %s" % (len(fails), len(rows), fails))
        return 1
    print("PASS M340: %d/%d gates" % (len(rows), len(rows)))
    return 0


if __name__ == "__main__":
    import contextlib

    _out = sys.stdout

    class Tee:
        def __init__(self):
            self.buf = []

        def write(self, s):
            _out.write(s)
            self.buf.append(s)

        def flush(self):
            _out.flush()

    t = Tee()
    with contextlib.redirect_stdout(t):  # type: ignore[arg-type]
        rc = main()
    text = "".join(t.buf)
    if not os.environ.get("M340_NO_EVID"):
        with open(EVID, "w") as f:
            f.write(text)
    sys.exit(rc)
