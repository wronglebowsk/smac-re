#!/usr/bin/env python3
"""M338 — the last two #DIFF readers' INDEX PROVENANCE.

PICK: NEXT_PROMPT.md (x6) remaining clauses: `NAMED ## M336` closes `0x48678f`
and leaves "index provenance of 0x44a1c8 / 0x57c606" OPEN (inherited from
`## M335`). The table is alpha.txt's six `#DIFF` names at 0x94d2ac (end
0x94d2c4, M335); this script asks where each of the two remaining readers gets
the value it multiplies by 4.

Measured (all numbers COMPUTED from the static image `scratch/m574/text.txt`
plus the PE strings of `programs/terran.exe`; zero box time):

  0x57c606  `mov eax,DWORD PTR [esi*4+0x94d2ac]` is a UI LIST BUILDER: the
            index is the loop counter `esi`, zeroed by `xor esi,esi` at
            0x57c604, incremented at 0x57c6ca, bounded `cmp esi,6`/`jl` — the
            six rows, one label each. No stored/global index is involved.

  0x44a1c8  `mov eax,DWORD PTR [edx*4+0x94d2ac]` indexes with
            `dl = BYTE PTR [eax+0x20]` (0x44a1c5, zero-extended by
            `xor edx,edx` at 0x44a1b7), where `eax = [ebp-0x1c]` is a record of
            the 35 x 0x8c buffer at 0x983a10 — the "hallfame.jhh" table loaded
            by FUN_0044b690 (fopen "rb" 0x689f3c/0x689f40, read 0x1324 bytes).
            The field has exactly two writers: 0x44b15b fills it from
            `BYTE PTR [0x94d438 + 8380*faction]` = faction-block byte +8, and
            0x44b612 copies it record-to-record. Byte +8 is the faction's
            EFFECTIVE DIFFICULTY (creation 0x59eed6 = ds:0x985aec or 3;
            save-load 0x57ef57). So the reader prints the difficulty NAME of a
            hall-of-fame entry.

GATES (printed first, then asserted; every V row names a mutant in
scripts/m338_mutate.py):
  G1  table census: the .text references to 0x94d2ac are exactly the 2 base
      materialisations + 7 scaled loads, 0 stores; the 7 loads' addresses are
      the declared set (both directions).
  G2  0x57c606 def-use: xor esi,esi immediately precedes; exactly one esi
      definition in the loop body (the inc); cmp esi,6 / jl back; bound ==
      the loader's row count (6).
  G3  0x44a1c8 def-use: the 6-instruction window loads [ebp-0x1c], zeroes edx,
      loads BYTE[eax+0x20], and indexes [edx*4+0x94d2ac]; no call/clamp between.
  G4  [ebp-0x1c]'s provenance: exactly 3 stores in FUN_004495e0, the reader
      bracketed by 0x4497b7 above and 0x44aa33 below, no jump crossing the
      bracket; the stored value is `lea eax,[edx*4+0x983a10]` with
      edx = 140*ecx decoded from the shl/add/lea/sub chain.
  G5  buffer identity: fopen "hallfame.jhh"/"rb" strings read out of the PE,
      read size 0x1324, zero-init 5 x 0x8c per 0x2bc group to 0x984d34; record
      count = end-base / stride = 35, 35*0x8c == 0x1324.
  G6  the +0x20 field's writers: exactly {0x44b15b, 0x44b612} in the module;
      0x44b15b's source fold decodes to 8380 == 0x20bc and the cell is
      0x94d430+8; 0x44b612 is a struct copy.
  G7  0x94d438 is the faction's effective difficulty: creation 0x59eed6
      (`ds:0x985aec` unless `ds:0x985b10` bit selects imm 3) and save-load
      0x57ef57 (same 8380 fold) both measured.
  G8  rivals, measured and killed: (a) the 0x44a1c8 index is ds:0x985aec;
      (b) 0x983a10 is the faction array (stride 0x20bc); (c) 0x57c606's index
      is stored somewhere.
"""
import hashlib
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
EXE = os.path.join(ROOT, "programs/terran.exe")

TABLE = 0x94D2AC
TABLE_END = 0x94D2C4
HOF = 0x983A10
HOF_END = 0x984D34
HOF_STRIDE = 0x8C
FACTION = 0x94D430
DIFF_CELL = 0x94D438
FACTION_STRIDE = 0x20BC

LINE = re.compile(r"^\s*([0-9a-f]{6,8}):\s+((?:[0-9a-f]{2} )+)\s*\t(.*)$")
SCALED = re.compile(r"\[(e?[abcds][xi])\*4\+0x([0-9a-f]+)\]")
MEM = re.compile(r"\[([^\]]+)\]")
MUT = os.environ.get("M338_MUT", "")
ALG = os.environ.get("M338_ALG", "")


def load():
    ins = []
    with open(TEXT, errors="replace") as f:
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


def patch(ins, addr, old_bs, new_bs, old_txt, new_txt):
    for i in ins:
        if i["a"] == addr:
            assert i["bs"] == bytes.fromhex(old_bs), (hex(addr), i["bs"].hex())
            assert i["ops"] == old_txt, (hex(addr), i["ops"])
            i["bs"] = bytes.fromhex(new_bs)
            parts = new_txt.split(None, 1)
            i["mn"] = parts[0]
            i["ops"] = parts[1] if len(parts) > 1 else ""
            return
    raise KeyError(hex(addr))


def apply_mut(ins):
    """Byte-faithful mutants (bytes AND text changed together)."""
    P = patch
    if MUT == "MU1":      # loop bound 6 -> 5
        P(ins, 0x57C6CB, "83 fe 06", "83 fe 05", "cmp    esi,0x6", "cmp    esi,0x5")
    elif MUT == "MU2":    # reader table displaced by one row
        P(ins, 0x44A1C8, "8b 04 95 ac d2 94 00", "8b 04 95 b0 d2 94 00",
          "mov    eax,DWORD PTR [edx*4+0x94d2ac]", "mov    eax,DWORD PTR [edx*4+0x94d2b0]")
    elif MUT == "MU3":    # field +0x20 -> +0x24
        P(ins, 0x44A1C5, "8a 50 20", "8a 50 24", "mov    dl,BYTE PTR [eax+0x20]",
          "mov    dl,BYTE PTR [eax+0x24]")
    elif MUT == "MU4":    # the record pointer is stored in a different slot
        P(ins, 0x4497B7, "89 45 e4", "89 45 e0", "mov    DWORD PTR [ebp-0x1c],eax",
          "mov    DWORD PTR [ebp-0x20],eax")
    elif MUT == "MU5":    # buffer base +4
        P(ins, 0x4497AD, "8d 04 95 10 3a 98 00", "8d 04 95 14 3a 98 00",
          "lea    eax,[edx*4+0x983a10]", "lea    eax,[edx*4+0x983a14]")
    elif MUT == "MU6":    # read size 0x1324 -> 0x1320
        P(ins, 0x44B6CD, "68 24 13 00 00", "68 20 13 00 00", "push   0x1324", "push   0x1320")
    elif MUT == "MU7":    # zero-init stride 0x8c -> 0x90
        P(ins, 0x44B6B9, "05 8c 00 00 00", "05 90 00 00 00", "add    eax,0x8c", "add    eax,0x90")
    elif MUT == "MU8":    # field source cell 0x94d438 -> 0x94d43c
        P(ins, 0x44B154, "8a 14 8d 38 d4 94 00", "8a 14 8d 3c d4 94 00",
          "mov    dl,BYTE PTR [ecx*4+0x94d438]", "mov    dl,BYTE PTR [ecx*4+0x94d43c]")
    elif MUT == "MU9":    # fold shl 4 -> shl 3 (8380 -> 4190)
        P(ins, 0x44B14F, "c1 e1 04", "c1 e1 03", "shl    ecx,0x4", "shl    ecx,0x3")
    elif MUT == "MU10":   # AI default 3 -> 4
        P(ins, 0x59EED1, "b8 03 00 00 00", "b8 04 00 00 00", "mov    eax,0x3", "mov    eax,0x4")
    elif MUT == "MU11":   # INSERTION: a second table load appears
        P(ins, 0x40A519, "8b 0c 95 90 d6 94 00", "8b 0c 95 ac d2 94 00",
          "mov    ecx,DWORD PTR [edx*4+0x94d690]", "mov    ecx,DWORD PTR [edx*4+0x94d2ac]")
    elif MUT == "MU12":   # REMOVAL: a declared table load leaves the set
        P(ins, 0x484CC9, "8b 04 95 ac d2 94 00", "8b 04 95 90 d6 94 00",
          "mov    eax,DWORD PTR [edx*4+0x94d2ac]", "mov    eax,DWORD PTR [edx*4+0x94d690]")
    return ins


def site(ins, addr):
    for i in ins:
        if i["a"] == addr:
            return i
    raise KeyError(hex(addr))


def window(ins, lo, hi):
    return [i for i in ins if lo <= i["a"] < hi]


def disp_of(i):
    m = SCALED.search(i["ops"])
    return int(m.group(2), 16) if m else None


def mem_disp(i):
    m = MEM.search(i["ops"])
    if not m:
        return None
    mm = re.search(r"([+-])0x([0-9a-f]+)$", m.group(1))
    return int(mm.group(2), 16) if mm else None


def imm(i):
    m = re.search(r",(?:BYTE PTR )?(0x[0-9a-f]+|0x0)$", i["ops"])
    if m:
        return int(m.group(1), 16)
    m = re.search(r"^(?:BYTE PTR )?(0x[0-9a-f]+)$", i["ops"])
    return int(m.group(1), 16) if m else None


def pe_strings(path, vas):
    d = open(path, "rb").read()
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
                out[va] = d[o:o + 64].split(b"\x00")[0].decode("latin-1")
                break
        else:
            out[va] = None
    return out


def fold_2095(ins, lo, hi):
    """Decode the 0x44b145 fold from its own immediates: edx = 65*eax; ecx = 131*eax;
    ecx <<= 4; ecx -= eax => 2095*eax; the load's [ecx*4] makes it 8380*eax."""
    seq = window(ins, lo, hi)
    want = [("mov", "edx,eax"), ("shl", "edx,0x6"), ("add", "edx,eax"),
            ("lea", "ecx,[eax+edx*2]"), ("shl", "ecx,0x4"), ("sub", "ecx,eax")]
    got = [(i["mn"], i["ops"]) for i in seq]
    if got != want:
        return None, ["unexpected: %s" % got]
    log = ["%s %s" % g for g in got]
    v = 1 << imm(seq[1])
    v = v + 1
    v = v * 2 + 1
    v = v << imm(seq[4])
    v = v - 1
    return v * 4, log


def main():
    ins = apply_mut(load())
    rows = []
    fails = []

    def gate(gid, ok, detail):
        rows.append((gid, "PASS" if ok else "FAIL", detail))
        if not ok:
            fails.append(gid)

    # ---- G1 table census -------------------------------------------------
    refs = [i for i in ins if "0x94d2ac" in i["ops"]]
    loads = sorted(i["a"] for i in refs
                   if SCALED.search(i["ops"]) and disp_of(i) == TABLE)
    bases = sorted(i["a"] for i in refs if not SCALED.search(i["ops"]))
    stores = [i["a"] for i in refs if re.search(r"PTR \[[^\]]*0x94d2ac\],", i["ops"])]
    declared = [0x44A1C8, 0x484CC9, 0x485426, 0x48678F, 0x486F40, 0x57C606, 0x599405]
    if ALG == "ALG1":   # algorithm mutant: count base materialisations as readers
        loads = sorted(loads + [a for a in bases if a != 0x57AC74])
    print("== G1 table census: %d scaled loads of 0x94d2ac ==" % len(loads))
    for a in loads:
        print("   0x%x %s" % (a, site(ins, a)["ops"]))
    print("   base materialisations: %s   stores: %s" % ([hex(a) for a in bases],
                                                         [hex(a) for a in stores]))
    print("   loader: mov esi,0x94d2ac @0x57ac74 ; bound cmp esi,0x94d2c4 -> 6 rows")
    gate("G1", loads == declared and bases == [0x4DDAFA, 0x57AC74] and not stores,
         "loads==declared=%s bases=%s stores=%s" %
         (loads == declared, [hex(a) for a in bases], stores))

    # ---- G2 0x57c606 index ------------------------------------------------
    pre = site(ins, 0x57C604)
    ld = site(ins, 0x57C606)
    body = window(ins, 0x57C606, 0x57C6D4)

    def dest(i):
        return i["ops"].split(",")[0].strip()

    incs = [i for i in body if i["mn"] == "inc" and i["ops"].strip() == "esi"]
    bound = site(ins, 0x57C6CB)
    jl = site(ins, 0x57C6CE)
    # every instruction in the body that writes esi
    defs_esi = [i["a"] for i in body
                if (i["mn"] in ("mov", "xor", "add", "sub", "shl", "or", "and",
                                "movsx", "movzx") and dest(i) == "esi")
                or (i["mn"] in ("inc", "dec") and i["ops"].strip() == "esi")]
    ok2 = (pre["mn"] == "xor" and pre["ops"].replace(" ", "") == "esi,esi"
           and ld["mn"] == "mov" and SCALED.search(ld["ops"]) and disp_of(ld) == TABLE
           and len(incs) == 1 and defs_esi == [0x57C6CA]
           and bound["mn"] == "cmp" and imm(bound) == 6
           and jl["mn"] == "jl" and "0x57c606" in jl["ops"]
           and 6 == ((TABLE_END - TABLE) // 4))
    print("== G2 0x57c606: literal loop index ==")
    print("   0x%x %s %s" % (pre["a"], pre["mn"], pre["ops"]))
    print("   0x%x %s %s" % (ld["a"], ld["mn"], ld["ops"]))
    print("   esi definitions in body: %s   bound=%s   back-edge=%s %s" %
          ([hex(a) for a in defs_esi], imm(bound), jl["mn"], jl["ops"]))
    print("   rows: loader (end-base)/4 = %d == loop bound %d" %
          ((TABLE_END - TABLE) // 4, imm(bound)))
    gate("G2", bool(ok2), "pre=xor esi,esi body-defs=%s bound=%d rows=%d" %
         ([hex(a) for a in defs_esi], imm(bound), (TABLE_END - TABLE) // 4))

    # ---- G3 0x44a1c8 index -----------------------------------------------
    w = window(ins, 0x44A1B4, 0x44A1CF)
    seq = [(i["a"], i["mn"], i["ops"]) for i in w]
    eax_load = site(ins, 0x44A1B4)
    xz = site(ins, 0x44A1B7)
    dl = site(ins, 0x44A1C5)
    idx = site(ins, 0x44A1C8)
    between = window(ins, 0x44A1C5, 0x44A1C8)
    ok3 = (eax_load["ops"] == "eax,DWORD PTR [ebp-0x1c]"
           and xz["mn"] == "xor" and xz["ops"].replace(" ", "") == "edx,edx"
           and dl["mn"] == "mov" and dl["ops"] == "dl,BYTE PTR [eax+0x20]"
           and idx["mn"] == "mov" and SCALED.search(idx["ops"]) and disp_of(idx) == TABLE
           and len(between) == 1 and idx["bs"].hex() == "8b0495acd29400"
           and not [i for i in w if i["mn"] == "call"])
    print("== G3 0x44a1c8: the index is BYTE[rec+0x20] ==")
    for a, mn, o in seq:
        print("   0x%x %s %s" % (a, mn, o))
    print("   instructions between the byte load and the table load: %d" % (len(between) - 1))
    gate("G3", bool(ok3), "window exact=%s disp=%s gap=%d" %
         (bool(ok3), hex(disp_of(idx)) if disp_of(idx) else None, len(between) - 1))

    # ---- G4 [ebp-0x1c] provenance ----------------------------------------
    LO, SZ = 0x4495E0, 5917
    fn = window(ins, LO, LO + SZ)
    slots = [i["a"] for i in fn if re.match(r"mov\s+DWORD PTR \[ebp-0x1c\],", i["mn"] + " " + i["ops"])]
    jumps = []
    for i in fn:
        m = re.match(r"(j\w+)\s+(0x[0-9a-f]+)", i["mn"] + " " + i["ops"])
        if m:
            jumps.append((i["a"], int(m.group(2), 16)))
    cross = [a for a, t in jumps
             if (0x4497B7 <= a < 0x44A1B4 and t < 0x4497B7)
             or (a >= 0x44AA33 and 0x4497BB <= t < 0x44A1B4)]
    chain = window(ins, 0x44979A, 0x4497AE)
    coeff = None
    try:
        lea8 = site(ins, 0x44979A)["ops"]        # eax,[ecx*8+0x0]
        sub = site(ins, 0x4497A1)["ops"]         # eax,ecx
        lea5 = site(ins, 0x4497A3)["ops"]        # edx,[eax+eax*4]
        m8 = int(re.search(r"\*(\d+)", lea8).group(1))
        m5 = 1 + int(re.search(r"\*(\d+)", lea5).group(1))
        sc = int(re.search(r"\[edx\*(\d+)\+", site(ins, 0x4497AD)["ops"]).group(1))
        if sub.replace(" ", "") == "eax,ecx":
            coeff = (m8 - 1) * m5 * sc
    except Exception:
        coeff = None
    base_lea = site(ins, 0x4497AD)
    flag = site(ins, 0x4497A6)
    ok4 = (slots == [0x4497B7, 0x44AA33, 0x44ACD1] and not cross
           and coeff == HOF_STRIDE and base_lea["ops"] == "eax,[edx*4+0x983a10]"
           and mem_disp(flag) == HOF)
    print("== G4 [ebp-0x1c] holds a 0x983a10 record ==")
    for i in chain:
        print("   0x%x %s %s" % (i["a"], i["mn"], i["ops"]))
    print("   stores to [ebp-0x1c]: %s   bracket crossings: %s" %
          ([hex(a) for a in slots], cross))
    print("   index math: edx = 35*ecx -> lea [edx*4+0x983a10] => stride 0x%x == 0x%x" %
          (coeff, HOF_STRIDE))
    gate("G4", bool(ok4), "slots=%s cross=%s stride=%s base=%s" %
         ([hex(a) for a in slots], cross, coeff, base_lea["ops"]))

    # ---- G5 buffer identity ----------------------------------------------
    strs = pe_strings(EXE, [0x689F3C, 0x689F40])
    size_push = site(ins, 0x44B6CD)
    buf_push = site(ins, 0x44B6D2)
    call = site(ins, 0x44B6E1)
    z = window(ins, 0x44B6AC, 0x44B6C8)
    zs = [(i["mn"], i["ops"]) for i in z]
    n = (HOF_END - HOF) // HOF_STRIDE
    ok5 = (strs[0x689F3C] == "rb" and strs[0x689F40] == "hallfame.jhh"
           and imm(size_push) == 0x1324 and imm(buf_push) == HOF
           and call["mn"] == "call" and "0x64cc00" in call["ops"]
           and ("mov", "eax,0x983a10") in zs and ("mov", "ecx,0x5") in zs
           and ("add", "eax,0x8c") in zs and ("cmp", "eax,0x984d34") in zs
           and n == 35 and n * HOF_STRIDE == imm(size_push))
    print("== G5 0x983a10 = the hallfame.jhh buffer ==")
    print("   fopen args: %r %r   read size 0x%x at 0x%x" %
          (strs[0x689F3C], strs[0x689F40], imm(size_push), imm(buf_push)))
    print("   zero-init: %s" % zs)
    print("   (0x984d34-0x983a10)/0x8c = %d records; %d*0x8c = 0x%x" %
          (n, n, n * HOF_STRIDE))
    gate("G5", bool(ok5), "file=%r size=0x%x count=%d" %
         (strs[0x689F40], imm(size_push), n))

    # ---- G6 the +0x20 writers --------------------------------------------
    module = window(ins, 0x448C60, 0x44C000)
    w20 = [i["a"] for i in module
           if re.match(r"mov\s+(BYTE|WORD|DWORD) PTR \[[^\]]*\+0x20\],", i["mn"] + " " + i["ops"])]
    src = site(ins, 0x44B154)
    coeff6, log6 = fold_2095(ins, 0x44B145, 0x44B154)
    cp1 = site(ins, 0x44B60F)
    cp2 = site(ins, 0x44B612)
    esi_base = site(ins, 0x44AFA8)
    ok6 = (w20 == [0x44B15B, 0x44B612] and coeff6 == FACTION_STRIDE
           and src["ops"] == "dl,BYTE PTR [ecx*4+0x94d438]"
           and DIFF_CELL == FACTION + 8
           and cp1["ops"] == "cl,BYTE PTR [edi+0x20]" and cp2["ops"] == "BYTE PTR [esi+0x20],cl"
           and esi_base["ops"] == "esi,0x983a10")
    print("== G6 the +0x20 field's writers ==")
    print("   stores to [reg+0x20] in 0x448c60..0x44c000: %s" % [hex(a) for a in w20])
    print("   fold: %s -> coeff %d == 0x%x" % (" ; ".join(log6), coeff6, FACTION_STRIDE))
    print("   source cell 0x%x == faction base 0x%x + 8" % (DIFF_CELL, FACTION))
    print("   copy: 0x%x %s / 0x%x %s" % (cp1["a"], cp1["ops"], cp2["a"], cp2["ops"]))
    gate("G6", bool(ok6), "writers=%s fold=%s cell=%s" %
         ([hex(a) for a in w20], coeff6, hex(DIFF_CELL)))

    # ---- G7 0x94d438 = effective difficulty ------------------------------
    cw = window(ins, 0x59EEC3, 0x59EED7)
    cs = [(i["mn"], i["ops"]) for i in cw]
    call_site = site(ins, 0x59EED6)
    sv = window(ins, 0x57EF33, 0x57EF58)
    # decode the ecx chain only (the lea/shl/sub on esi is the faction-name fold)
    ecx_chain = [i for i in sv if re.search(r"^(mov ecx|shl ecx|add ecx|sub ecx)", i["mn"] + " " + i["ops"])
                 or i["ops"].startswith("ecx,[eax+ecx*2]")]
    v = None
    for i in ecx_chain:
        o, mn = i["ops"], i["mn"]
        if mn == "shl" and v is None:
            v = 1 << imm(i)
        elif mn == "add":
            v += 1
        elif mn == "lea":
            v = v * 2 + 1
        elif mn == "shl":
            v = v << imm(i)
        elif mn == "sub":
            v -= 1
    coeff7 = v * 4 if v is not None else None
    store7 = site(ins, 0x57EF57)
    ok7 = (call_site["mn"] == "mov" and call_site["ops"] == "DWORD PTR [esi+0x94d438],eax"
           and ("mov", "al,ds:0x985b10") in cs and ("mov", "eax,ds:0x985aec") in cs
           and ("mov", "eax,0x3") in cs and ("test", "dl,al") in cs
           and coeff7 == FACTION_STRIDE
           and store7["ops"] == "DWORD PTR [ecx*4+0x94d438],edx")
    print("== G7 0x94d438 = the faction's effective difficulty ==")
    print("   creation 0x59eec3..0x59eed6: %s" % cs)
    print("   save-load 0x57ef33..0x57ef57 ecx chain=%s -> %s ; store %s" %
          ([(i["mn"], i["ops"]) for i in ecx_chain], coeff7, store7["ops"]))
    gate("G7", bool(ok7), "creation=%s fold=%s store=%s" % (cs, coeff7, store7["ops"]))

    # ---- G8 rivals --------------------------------------------------------
    g3chain = window(ins, 0x44A1B4, 0x44A1C8)
    r1 = [i for i in g3chain if "0x985aec" in i["ops"]]
    r2 = (HOF_STRIDE, FACTION_STRIDE, n)
    r3 = [i["a"] for i in window(ins, 0x57C605, 0x57C606) if re.match(r"^(mov|xor)", i["mn"])]
    ok8 = (len(r1) == 0 and r2[0] != r2[1] and r2[0] * r2[2] == 0x1324
           and r3 == [] and site(ins, 0x57C604)["ops"].replace(" ", "") == "esi,esi")
    print("== G8 rivals, measured ==")
    print("   R1 'index is ds:0x985aec': loads of 0x985aec in the 0x44a1b4..0x44a1c8")
    print("      chain: %d (the chain has exactly one load: BYTE[eax+0x20])" % len(r1))
    print("   R2 'buffer = faction array': buffer stride 0x%x (%d recs, 0x%x bytes) vs"
          % (r2[0], r2[2], r2[0] * r2[2]))
    print("      faction stride 0x%x -> different arrays" % r2[1])
    print("   R3 '0x57c606 index stored': instructions between xor esi,esi and the load: %s"
          % r3)
    gate("G8", bool(ok8), "r1_refs=%d strides=%s r3=%s" %
         (len(r1), (hex(r2[0]), hex(r2[1])), r3))

    # ---- verdict ----------------------------------------------------------
    blob = "\n".join("%s %s %s" % r for r in rows)
    digest = hashlib.sha256(blob.encode()).hexdigest()[:16]
    print()
    for gid, st, detail in rows:
        print("%-4s %-4s %s" % (gid, st, detail))
    print("digest=%s gates=%d pass=%d" % (digest, len(rows), len(rows) - len(fails)))
    if fails:
        print("FAIL M338: %d/%d gates (red: %s)" % (len(rows) - len(fails), len(rows), fails))
        return 1
    print("PASS M338: %d/%d gates" % (len(rows), len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
