#!/usr/bin/env python3
"""M253-M255: what the region CATEGORY values MEAN, and who starts a NEW GAME.

Pick (NEXT_PROMPT, new from M251 / M250): (a) what NAMES the category bytes 0/2/7/8 at
DAT_0094eda8 — the shape, the 2 writers and the 4 effects are pinned, the names are not;
(b) which of FUN_005b2970's 4 callers is NEW GAME.

Static only: file image + ghidra_out. No box time, no /proc, no gdb.
Acceptance: ONE invocation prints PASS on every gate; an undecided gate prints FAIL with
its numbers.

Gates:
  G1  regression: DAT_0094eda8 reference census (refs / functions / stores / writers / values)
  G2  every READ site classified by test shape; the tested-value set and per-value site counts
  G3  the four effects re-pinned to a pc + owning function (<2 bonus, 7, 8+size, 2 block)
  G4  naming evidence: the string literals each consumer function references, read from the image
  G5  the six STORE sites: where each stored value comes from (immediate vs computed)
  G6  FUN_005b2970's 4 callers: their string literals (name the mode from the tokens)
  G7  the callers' own callers (one level up) + the gate each caller sits behind
  G8  exactly ONE caller attributed to NEW GAME, the others named by their own evidence
"""
import csv
import re
import struct
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXE = ROOT / "programs" / "terran.exe"
INDEX = ROOT / "ghidra_out" / "index.csv"
TEXT_BASE = 0x400000
CATEGORY = 0x94eda8
SCORE = 0x94e5a8        # per-region multiplier/score byte, same index (M94)
OBLIG = 0x94eaa8        # per-region short the auto-manager debits by 10
FLAGS = 0x94e7a8        # per-region flag bytes
CLEAR = 0x94e628        # per-region byte the stage zeroes each pass
TAIL = 0x558b18         # the region-loop tail both terminal stores jmp to
DRIVER = 0x5b2970
CALLERS = ["FUN_004e10c0", "FUN_004e11b0", "FUN_0057c550", "FUN_0057ecf0"]
SHARDS = sorted((ROOT / "ghidra_out").glob("shard_*.c"))
BANNER = re.compile(r"^// ==== (\S+) @ (0x[0-9a-f]+) size=(\d+)")
STORERMW = ("add", "sub", "and", "or", "xor", "adc", "sbb", "inc", "dec")

FUNCS = []
INSN = re.compile(r'^\s+([0-9a-f]{6,8}):\s+(?:[0-9a-f]{2} )*\s*(\S+)\s+(.*)$')
IMM = re.compile(r'0x([0-9a-f]+)')


def load_index():
    with INDEX.open() as f:
        for r in csv.DictReader(f):
            a = int(r['addr'], 16)
            FUNCS.append((a, a + int(r['size_bytes']), r['name']))
    FUNCS.sort()


def fn_of(pc):
    lo, hi = 0, len(FUNCS)
    while lo < hi:
        mid = (lo + hi) // 2
        if FUNCS[mid][0] <= pc:
            lo = mid + 1
        else:
            hi = mid
    i = lo - 1
    if i >= 0 and FUNCS[i][1] > pc:
        return FUNCS[i][2]
    return None


def disasm():
    out = subprocess.run(['objdump', '-d', '-M', 'intel', '--section=.text', str(EXE)],
                         capture_output=True, text=True).stdout
    return [(int(m.group(1), 16), m.group(2), m.group(3).strip())
            for m in (INSN.match(ln.replace('\\t', '\t')) for ln in out.splitlines()) if m]


def immediates(ops):
    return [int(t, 16) for t in IMM.findall(ops)]


def calls_to(ins, target):
    return [(pc, fn_of(pc)) for pc, mn, ops in ins
            if mn == 'call' and immediates(ops)[:1] == [target]]


def body(ins, addr):
    st = next(s for s, e, n in FUNCS if n == addr)
    en = next(e for s, e, n in FUNCS if n == addr)
    return st, en, [(pc, mn, ops) for pc, mn, ops in ins if st <= pc < en]


_IMG = None


def img():
    global _IMG
    if _IMG is None:
        _IMG = EXE.read_bytes()
    return _IMG


def cstr(va, cap=200):
    """NUL-terminated bytes at a VA -> printable str ('' if not printable)."""
    b = img()
    o = va - TEXT_BASE
    if o < 0 or o >= len(b):
        return ''
    z = b.find(b'\0', o, o + cap)
    if z < 0:
        return ''
    s = b[o:z]
    return s.decode('latin1') if all(32 <= c < 127 for c in s) else ''


_INS = None


def ins():
    global _INS
    if _INS is None:
        load_index()
        _INS = disasm()
    return _INS


def is_store(mn, ops):
    if mn.startswith(("lea", "j", "push", "pop", "cmp", "test")):
        return False
    dest = ops.split(",")[0] if "," in ops else ops
    return mn.split()[0] in ("mov",) + STORERMW and ("%x" % CATEGORY) in dest


def census():
    tok = "%x" % CATEGORY
    refs = [(p, m, o) for p, m, o in ins() if tok in o]
    stores = [r for r in refs if is_store(r[1], r[2])]
    reads = [r for r in refs if r not in stores]
    return refs, stores, reads


_IDX = {}


def window(pc, back=12, fwd=0):
    if not _IDX:
        for k, (p, m, o) in enumerate(ins()):
            _IDX[p] = k
    i = _IDX[pc]
    return ins()[max(0, i - back):i + fwd + 1]


_BMAP = {}


def strings(name):
    if not _BMAP:
        for f in SHARDS:
            lines = f.read_text(errors="replace").splitlines()
            hits = [(i, BANNER.match(l).group(1)) for i, l in enumerate(lines) if BANNER.match(l)]
            for k, (i, nm) in enumerate(hits):
                _BMAP[nm] = (lines, i, hits[k + 1][0] if k + 1 < len(hits) else len(lines))
    e = _BMAP.get(name)
    if e is None:
        return []
    lines, i, j = e
    toks = set(re.findall(r"\bs_([A-Za-z0-9_]+)_(00[0-9a-f]{6})\b", "\n".join(lines[i:j])))
    return sorted({cstr(int(va, 16)) for _, va in toks if cstr(int(va, 16))})


def g1():
    refs, stores, reads = census()
    fns = sorted({fn_of(p) for p, _, _ in refs})
    wr = Counter(fn_of(p) for p, _, _ in stores)
    vals = sorted({immediates(o)[-1] for _, _, o in stores if len(immediates(o)) > 1})
    ok = (len(refs) == 79 and len(fns) == 18 and len(stores) == 6 and len(reads) == 73
          and dict(wr) == {"FUN_00556690": 5, "FUN_0055f650": 1} and vals == [0, 2, 7, 8])
    return ok, ("refs=%d fns=%d stores=%d reads=%d writers=%s imm_values=%s"
                % (len(refs), len(fns), len(stores), len(reads), dict(wr), [hex(v) for v in vals]))


def g2():
    refs, stores, reads = census()
    tested = set()
    kinds = Counter()
    regcmp = set()
    rcs = []
    for p, m, o in reads:
        ii = immediates(o)
        if m == "cmp" and len(ii) > 1:
            kinds["cmp-imm"] += 1
            tested.add(ii[-1])
        elif m == "cmp":
            kinds["cmp-reg"] += 1
        elif m.startswith("mov"):
            kinds["load"] += 1
            dest = o.split(",")[0].strip()
            for q, mm, oo in window(p, 0, 3):
                if mm == "cmp" and oo.startswith(dest + ",") and len(immediates(oo)) == 1:
                    regcmp.add(immediates(oo)[0])
                    rcs.append(hex(q))
                    break
        else:
            kinds["other:" + m] += 1
    unk = sorted(k for k in kinds if k.startswith("other:"))
    ok = (len(reads) == 73 and tested == {2, 7, 8} and not unk
          and regcmp == {2, 7, 8} and len(rcs) >= 3)
    return ok, ("kinds=%s cmp_imm_values=%s cmp_of_loaded_byte=%s@%d_sites unknown=%s"
                % (dict(kinds), sorted(hex(t) for t in tested),
                   sorted(hex(t) for t in regcmp), len(rcs), unk))


def g3():
    st, en, bd = body(ins(), "FUN_00556690")
    bonus = [(p, o) for p, m, o in bd if m == "add" and 0x3e8 in immediates(o)]
    face = [(p, o) for p, m, o in bd if m == "cmp" and immediates(o) == [7]
            and any(("%x" % CATEGORY) in oo for _, _, oo in window(p, 4, 0))]
    small = [(p, o) for p, m, o in bd if m == "cmp" and 0x96 in immediates(o) and "989ce0" in o]
    fold = False
    if small:
        w = window(small[0][0], 8, 0)
        fold = (any(m == "lea" and "*8" in o for _, m, o in w)
                and any(m == "sub" for _, m, o in w))
    s150 = [(hex(p), m, o) for p, m, o in census()[2]
            if fn_of(p) in ("FUN_00556150", "FUN_00556370")]
    ok = (len(bonus) == 1 and len(face) == 1 and len(small) == 1 and fold
          and s150 == [("0x55628e", "cmp", "BYTE PTR [ebx+edx*1+0x94eda8],0x8"),
                       ("0x5563a3", "mov", "dl,BYTE PTR [eax+esi*1+0x94eda8]")])
    return ok, ("+1000_add=%s face7=%s tiles_lt_150=%s stride7_fold=%s score_fns=%s"
                % ([hex(p) for p, o in bonus], [hex(p) for p, o in face],
                   [(hex(p), o) for p, o in small], fold, s150))


def g4():
    out = []
    w = window(0x557fdf, 14, 2)
    out.append(("8=reserved_id_and_zero_score",
                any(m == "and" and 0x3f in immediates(o) for _, m, o in w)
                and any(m == "cmp" and 0x3f in immediates(o) for _, m, o in w)
                and any(("%x" % SCORE) in o for _, m, o in w)
                and any(m == "jmp" and immediates(o) == [TAIL] for _, m, o in w)))
    w = window(0x558516, 10, 0)
    out.append(("7_or_8=sete+add7(worth_test)",
                any(m.startswith("set") for _, m, o in w)
                and any(m == "add" and 7 in immediates(o) for _, m, o in w)))
    w = window(0x558549, 8, 0)
    out.append(("0=accumulator_bit2", any(m == "test" and "ebp-0x40" in o
                                          and 2 in immediates(o) for _, m, o in w)))
    w = window(0x55855e, 8, 0)
    out.append(("2=accumulator_bit1", any(m == "test" and "ebp-0x40" in o
                                          and 1 in immediates(o) for _, m, o in w)))
    w = window(0x55856b, 8, 3)
    out.append(("7=water_band_and_region_done",
                any(m == "cmp" and 0x40 in immediates(o) for _, m, o in w)
                and any(m.startswith("j") and 0x558578 in immediates(o) for _, m, o in w)
                and any(m == "jmp" and immediates(o) == [TAIL] for _, m, o in w)))
    w = window(0x564ad7, 26, 0)
    out.append(("55f650_promotes_8_to_7_with_debit",
                any(m == "cmp" and "ebp-0x8c" in o and 8 in immediates(o) for _, m, o in w)
                and any(m == "mov" and "ebp-0x8c" in o and 7 in immediates(o) for _, m, o in w)
                and any(m == "add" and ("%x" % OBLIG) in o and 0xfff6 in immediates(o)
                        for _, m, o in w)
                and any(m == "or" and ("%x" % FLAGS) in o and 9 in immediates(o)
                        for _, m, o in w)))
    bad = [n for n, v in out if not v]
    return not bad, "; ".join("%s=%s" % (n, "OK" if v else "NO") for n, v in out)


def g5():
    st, en, bd = body(ins(), "FUN_00531bf0")
    callees = sorted({"FUN_%08x" % t for t in {immediates(o)[0] for p, m, o in bd
                                                if m == "call" and immediates(o)}})
    terr = any("92ae14" in o for _, _, o in bd)
    sites = [(p, fn_of(p)) for p, m, o in ins()
             if m == "call" and immediates(o)[:1] == [0x531bf0]]
    in_stage = sum(1 for p, f in sites if f == "FUN_00556690")
    bd2 = body(ins(), "FUN_00556690")[2]
    ors = [(p, o.split(",")[-1].strip()) for p, m, o in bd2
           if m == "or" and "[ebp-0x40]" in (o.split(",")[0] if "," in o else o)]
    verdict = []
    for p, reg in ors:
        w = window(p, 14, 1)
        vals = sorted({immediates(oo)[0] for _, mm, oo in w
                       if mm == "mov" and oo.startswith(reg + ",0x") and immediates(oo)})
        verdict.append((hex(p), reg, [hex(v) for v in vals],
                        any(mm.startswith("j") and p in immediates(oo) for _, mm, oo in w)))
    masks = sorted({immediates(o)[-1] for p, m, o in bd2
                    if m == "test" and "ebp-0x40" in o and len(immediates(o)) > 1})
    ok = (callees == ["FUN_0058b1b0", "FUN_0058cfc0"] and terr and in_stage == 2
          and masks == [1, 2] and len(ors) == 1 and len(verdict) == 1
          and verdict[0][2] == ["0x1", "0x2"] and verdict[0][3])
    return ok, ("531bf0 callees=%s terrain_base=%s call_sites=%d in_stage=%d verdict=%s "
                "acc_masks=%s" % (callees, terr, len(sites), in_stage, verdict,
                                  [hex(x) for x in masks]))


def g6():
    rows = []
    for nm in CALLERS:
        st, en, bd = body(ins(), nm)
        sites = [p for p, m, o in bd if m == "call" and immediates(o)[:1] == [DRIVER]]
        g = {"set80": False, "clr80": False, "skip_to_return": 0, "world_dims": 0}
        for p in sites:
            w = window(p, 16, 1)
            g["set80"] |= any(m == "or" and 0x80 in immediates(o) for _, m, o in w)
            g["clr80"] |= any(m == "and" and 0x7f in immediates(o) for _, m, o in w)
            g["skip_to_return"] += sum(1 for _, m, o in w
                                       if m.startswith("j") and (p + 5) in immediates(o))
            g["world_dims"] = max(g["world_dims"],
                                  len({x for _, m, o in w if m == "mov"
                                       for x in IMM.findall(o) if x.startswith("92ad")}))
        rows.append((nm, [hex(p) for p in sites], g))
    d = {nm: (s, g) for nm, s, g in rows}
    ok = (all(len(s) == 1 for s, _ in d.values())
          and d["FUN_004e10c0"][1]["set80"] and not d["FUN_004e10c0"][1]["clr80"]
          and d["FUN_004e11b0"][1]["clr80"] and not d["FUN_004e11b0"][1]["set80"]
          and d["FUN_0057c550"][1]["skip_to_return"] >= 2
          and d["FUN_0057ecf0"][1]["skip_to_return"] == 0
          and d["FUN_0057ecf0"][1]["world_dims"] >= 4)
    return ok, " ".join("%s site=%s %s" % (nm, s, g) for nm, s, g in rows)


CHAIN = ["FUN_004e10c0", "FUN_004e11b0", "FUN_0057c550", "FUN_0057ecf0",
         "FUN_00512b40", "FUN_00516b80", "FUN_0057e890", "FUN_0057f740", "FUN_00522850"]
EXPECT_CALLERS = {"FUN_004e10c0": ["FUN_00512b40", "FUN_00516b80"],
                  "FUN_004e11b0": ["FUN_00512b40", "FUN_00516b80"],
                  "FUN_0057c550": ["FUN_0057e890", "FUN_0057f740"],
                  "FUN_0057ecf0": ["FUN_00522850", "FUN_0057f740"]}


def chain_info():
    out = {}
    for nm in CHAIN:
        st, en, bd = body(ins(), nm)
        callers = sorted({fn_of(p) for p, m, o in ins()
                          if m == "call" and immediates(o)[:1] == [st]})
        n_alpha = sum(1 for p, m, o in bd if m == "call" and immediates(o)[:1] == [0x5ea431])
        out[nm] = {"size": en - st, "callers": callers, "strings": strings(nm),
                   "alpha": n_alpha}
    return out


def g7():
    ci = chain_info()
    bad = []
    for nm, want in EXPECT_CALLERS.items():
        if ci[nm]["callers"] != want:
            bad.append("%s callers=%s want=%s" % (nm, ci[nm]["callers"], want))
    if not {"FACTIONS", "WORLDSIZE", "SCENARIO", "INTRO"} <= set(ci["FUN_0057ecf0"]["strings"]):
        bad.append("57ecf0 strings=%s" % ci["FUN_0057ecf0"]["strings"])
    if not {"RULES", "USERULES", "RELOADFAC", "DIFFICULTY", "CUSTOMNAMES", "FACTION"} <= \
            set(ci["FUN_0057c550"]["strings"]):
        bad.append("57c550 strings=%s" % ci["FUN_0057c550"]["strings"])
    for nm in ("FUN_004e10c0", "FUN_004e11b0"):
        if ci[nm]["strings"]:
            bad.append("%s strings=%s" % (nm, ci[nm]["strings"]))
    return not bad, ("bad=%s | 522850=%s 57e890=%s 57f740=%s 512b40=%s 516b80=%s"
                     % (bad, ci["FUN_00522850"]["strings"], ci["FUN_0057e890"]["strings"],
                        ci["FUN_0057f740"]["strings"], ci["FUN_00512b40"]["strings"][:4],
                        ci["FUN_00516b80"]["strings"][:4]))


def g8():
    ci = chain_info()
    cand = {}
    for nm in CALLERS:
        s2, e2, bd2 = body(ins(), nm)
        site = [p for p, m, o in bd2 if m == "call" and immediates(o)[:1] == [DRIVER]][0]
        w = window(site, 16, 1)
        ungated = not any(m.startswith("j") and (site + 5) in immediates(o) for _, m, o in w)
        dims = len({x for _, m, o in w if m == "mov" for x in IMM.findall(o)
                    if x.startswith("92ad")})
        names = {"FACTIONS", "WORLDSIZE", "SCENARIO"} <= set(ci[nm]["strings"])
        cand[nm] = {"ungated": ungated, "dims": dims, "names": names,
                    "alpha": ci[nm]["alpha"], "callers": ci[nm]["callers"]}
    hits = sorted(nm for nm, c in cand.items()
                  if c["ungated"] and c["dims"] >= 4 and c["names"] and c["alpha"] == 2)
    return hits == ["FUN_0057ecf0"], ("attributed=%s discriminators=%s" % (hits, cand))



def main():
    gates = []
    for name, fn in [("G1", g1), ("G2", g2), ("G3", g3), ("G4", g4),
                     ("G5", g5), ("G6", g6), ("G7", g7), ("G8", g8)]:
        try:
            ok, detail = fn()
        except Exception as exc:
            ok, detail = False, "EXC %s: %s" % (type(exc).__name__, exc)
        gates.append((name, ok, detail))
        print("%s %s: %s" % (name, "PASS" if ok else "FAIL", detail))
    n_ok = sum(1 for _, ok, _ in gates if ok)
    print("SUMMARY %s: %d/%d gates on terran.exe (%s)"
          % ("PASS" if n_ok == len(gates) else "FAIL", n_ok, len(gates),
             "static image, no box"))
    return 0 if n_ok == len(gates) else 1


if __name__ == "__main__":
    sys.exit(main())
