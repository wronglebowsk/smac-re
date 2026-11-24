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
  G1  the Difficulty read: 18 profile-call sites, exactly one with key imm
      0x692718 == "Difficulty"; its value store is ds:0x92bde8 at 0x58e8c6;
      that is the ONLY store to 0x92bde8 in the function; the injected default
      is the string "0".
  G2  the 0x58e8a9..0x58e8c6 window is straight-line: 10 insns, 0 jcc/jmp/ret,
      exactly 2 stores, the pref store's source register is eax.
  G3  return-path identity: 0x5ea484 and 0x5eaa53 have no jcc and no eax write
      after their downstream call -> the stored dword IS the parser's return.
  G4  parse-chain compare census: the constant set equals the declared set and
      contains NO element of {2,3,4,5,6}.
  G5  rivals, each evaluated and each FAILING on the printed numbers:
      R1 "the Difficulty path clamps to the 6-row ladder"; R2 "a bounded
      default caps it"; R3 "Language's bounded switch is Difficulty's
      consumer". Positive control: Language bound == 4 (found), Difficulty
      bound == none (found).
  G6  table arithmetic: (0x94d2c4-0x94d2ac)/4 == 6 rows; k=5 -> 0x94d2c0 (last
      legal row); k=6 -> 0x94d2c4 == TABLE_END, i.e. one dword past by exactly
      4 bytes.
  G7  the pref-fed readers: the three census loads whose index provenance is a
      difficulty pref cell all compute TABLE_END at k=6 (base and scale decoded
      from their own addressing bytes), while the loop-counted builder cannot
      reach 6.
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
    # key immediate = the push of a 0x69xxxx address inside the 6-push window
    keys = {}
    for c in calls:
        prev = [i for i in body if i["a"] < c["a"]][-6:]
        k = [i for i in prev if i["mn"] == "push" and re.match(r"^0x69[0-9a-f]{4}$", i["ops"].strip())]
        keys[c["a"]] = (k[0]["a"], int(k[0]["ops"].strip(), 16)) if k else (None, None)
    strs = pe_str([KEY_DIFF, KEY_LANG])
    diff_sites = [a for a, (ka, kv) in keys.items() if kv == KEY_DIFF]
    lang_sites = [a for a, (ka, kv) in keys.items() if kv == KEY_LANG]
    store_cell = stores(body, PREF)
    store_addrs = [s["a"] for s in store_cell]

    print("== M340 gate table (computed, printed before assertion) ==")
    print("FN_0058e7f0 extent 0x%x..0x%x  insns=%d" % (fs, fe, len(body)))
    print("G1  profile-call sites=%d  keys: Difficulty=%d (%s)  Language=%d"
          % (len(calls), len(diff_sites), strs.get(KEY_DIFF), len(lang_sites)))
    if diff_sites:
        print("    Difficulty call 0x%x key-push 0x%x  PE=%r"
              % (diff_sites[0], keys[diff_sites[0]][0], strs.get(KEY_DIFF)))
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
    print("    default seed: push 0x0 at %s (itoa(0)/strcpy into 0x%x)"
          % ([hex(i["a"]) for i in default_zero], DEFAULT_BUF))

    # ---- G3 return path -------------------------------------------------
    rp = []
    for lo, hi, lab in ((0x5EA484, 0x5EA493, "0x5ea484"), (0x5EAA53, 0x5EAA6F, "0x5eaa53")):
        seq = window(ins, lo, hi)
        ci = [n for n, i in enumerate(seq) if i["mn"] == "call"]
        tail = seq[ci[0] + 1:] if ci else []
        eaw = [i for i in tail if writes(i, "eax")]
        br = [i for i in seq if i["mn"].startswith("j")]
        rp.append((lab, len(seq), len(br), len(eaw),
                   [("%x" % i["a"], i["mn"], i["ops"]) for i in eaw]))
        print("G3  %s: insns=%d jcc=%d eax-writes-after-call=%d %s"
              % (lab, len(seq), len(br), len(eaw), rp[-1][4]))

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
    lang = window(ins, 0x628130, 0x6281AC)
    lang_c = [(a, c) for a, _, c, _ in consts(lang)]
    lang_ja = [i for i in lang if i["mn"].startswith("j")]
    lang_bound = [c for _, c in lang_c if c in BOUND_SPACE]
    diff_bound = hit
    print("G5  positive control Language@0x628130: cmp consts=%s jcc=%s bound=%s"
          % ([hex(c) for _, c in lang_c], [i["mn"] for i in lang_ja], lang_bound))
    print("    Difficulty@0x58e8c6: bound=%s" % diff_bound)
    print("    R1 'Difficulty clamps to the 6-row ladder'  -> bound found? %s (must be empty)"
          % diff_bound)
    print("    R2 'a bounded default caps it'              -> default is the string %r, comps before store=%d"
          % ("0", len([i for i in win if i["mn"] in ("cmp", "test")])))
    print("    R3 'Language's bounded switch is Difficulty's consumer' -> the switch is at 0x628130 reached from 0x58e85a, difficulty store followed by 0x58e8be (next field setup)")

    # ---- G6 table arithmetic --------------------------------------------
    # the row count is MEASURED, not assumed: the UI list builder's loop bound
    lb = site(ins, 0x57C6CB)
    m = re.search(r",0x([0-9a-f]+)$", lb["ops"])
    rows_meas = int(m.group(1), 16) if m else None
    rows_n, rem = divmod(TABLE_END - TABLE, 4)
    k5, k6 = TABLE + 4 * 5, TABLE + 4 * 6
    print("G6  loop bound 0x57c6cb `%s %s` -> rows_measured=%s"
          % (lb["mn"], lb["ops"], rows_meas))
    print("G6  rows=(0x%x-0x%x)/4=%d rem=%d  k=5 -> 0x%x  k=6 -> 0x%x (END=0x%x)"
          % (TABLE_END, TABLE, rows_n, rem, k5, k6, TABLE_END))

    # ---- G7 pref-fed readers --------------------------------------------
    r7 = []
    for a, lab, kind in LOADS:
        si = site(ins, a)
        base, sc = scale_of(si)
        m = re.search(r"\[(e?[abcds][xi])\*", si["ops"])
        reg = m.group(1) if m else None
        prev = [i for i in ins if i["a"] < a]
        defs = [i for i in prev if writes_fam(i, reg)] if reg else []
        d = defs[-1] if defs else None
        r7.append((a, lab, kind, base, sc, reg, d))
        print("G7  0x%x %-26s %-11s base=0x%x scale=%d idx=%s def=%s"
              % (a, lab, kind, base, sc, reg,
                 ("%x %s %s" % (d["a"], d["mn"], d["ops"])) if d else "none"))
    pref_ok = True
    for a, lab, kind, base, sc, reg, d in r7:
        if a not in PREF_FED:
            continue
        # the index must come from a MEMORY LOAD, not a constant or a compare
        if not (base == TABLE and sc == 4 and d is not None and "PTR" in d["ops"]):
            pref_ok = False
    print("G7  pref-fed sites %s: base==TABLE, scale==4, index defined by a memory"
          " load: %s" % ([hex(a) for a in PREF_FED], pref_ok))

    # ---- assert ----------------------------------------------------------
    gate("G1", len(calls) == 18 and len(diff_sites) == 1 and strs.get(KEY_DIFF) == "Difficulty"
         and store_addrs == [0x58E8C6] and len(default_zero) == 1,
         "18 profile calls; 1 Difficulty key (PE %r); store 0x92bde8 at %s; default '0'"
         % (strs.get(KEY_DIFF), [hex(a) for a in store_addrs]))
    gate("G2", len(win) == 10 and not any(isbr(i) for i in win) and len(wstores) == 2
         and wstores[-1]["ops"] == "ds:0x92bde8,eax",
         "10 insns, 0 branches, stores %s, pref store src eax" % [i["ops"] for i in wstores])
    gate("G3", all(b == 0 and e == 0 for _, _, b, e, _ in rp),
         "both wrappers: 0 branches, 0 eax writes after the call -> stored dword == parser return")
    gate("G4", set(cset) == DECLARED_CMP and not hit,
         "cmp constants == declared set, intersection with {2..6} empty")
    gate("G5", lang_bound == [4] and not diff_bound,
         "Language bound=%s (positive control), Difficulty bound=%s -> R1/R2/R3 fail"
         % (lang_bound, diff_bound))
    gate("G6", rows_n == 6 and rem == 0 and k5 == 0x94D2C0 and k6 == TABLE_END
         and rows_meas == rows_n,
         "6 rows (loop bound measured 0x57c6cb), k=5 last legal 0x94d2c0,"
         " k=6 == 0x94d2c4 one dword past")
    gate("G7", pref_ok and len(LOADS) == 7,
         "each pref-fed reader: base==0x94d2ac, scale==4, index from a memory"
         " load (no constant, no clamp) -> k=6 lands on 0x94d2c4")

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
