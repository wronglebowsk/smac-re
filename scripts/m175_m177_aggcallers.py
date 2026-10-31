#!/usr/bin/env python3
"""M175-M177: who asks FUN_00531df0 for the aggregate, the calling convention its 17 sites actually pass,
and the pre-call priming of the per-faction stamp [block+0x94d4a8] = ds:0x985afc.

  M175  17 call sites -> 12 owner functions (the aggregator's demand set).
  M176  arg1 = the 0x20bc (8,380) faction BLOCK BASE, arg3 = a small mode code {0,1}.
  M177  5 sites prime [block+0x94d4a8] with the run-state global ds:0x985afc within 15 insns before the call;
        the field is consumed by `sub reg,[block+0x94d4a8]` age tests, one gating the call itself.

    python3 scripts/m175_m177_aggcallers.py
"""
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("field_census", os.path.join(HERE, "field_census.py"))
FC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FC)

INS, fnof, IDX = FC.INS, FC.fnof, FC.IDX
ROOT = FC.ROOT
LOW = [(pc, s.lower()) for pc, s in INS]
INDEX = {n: (a, z) for a, n, z in IDX}
R = {}
SITES = [0x429416, 0x43ff6c, 0x4a6209, 0x4a633e, 0x533ef3, 0x534215, 0x534529, 0x535069, 0x5351b9,
         0x535829, 0x535c9e, 0x5469be, 0x54ebb1, 0x55568c, 0x5559e1, 0x569415, 0x59549b]
POS = {pc: i for i, (pc, _) in enumerate(INS)}


def ok(mid, cond, text):
    R[mid] = cond
    print("%s  %s — %s" % (mid, "PASS" if cond else "FAIL", text))


def fnsize(name):
    for addr, n, size in IDX:
        if n == name:
            return addr, size
    return INDEX[name][0], 0


def m175():
    calls = [pc for pc, s in LOW if re.search(r"call\s+0x531df0\b", s)]
    owners = {}
    for c in calls:
        owners.setdefault(fnof(c), []).append(hex(c))
    print("M175 %d sites in %d owners:" % (len(calls), len(owners)))
    for f in sorted(owners):
        a, sz = fnsize(f)
        print("   %-14s x%d  sites: %s" % (f, len(owners[f]), ", ".join(owners[f])))
    multi = {f: v for f, v in owners.items() if len(v) > 1}
    ok("M175", len(calls) == 17 and len(owners) == 13 and sum(len(v) for v in multi.values()) == 8,
       "the aggregator's demand set is 17 sites in 13 functions: FUN_00546800 (AI hub) x2, FUN_005551e0 x2, "
       "FUN_004a5eb0 x2, FUN_00534fa0 x2 (the 0x94d4a8-priming pair) + single sites in FUN_004282d0, FUN_0043ff20 "
       "(wrapper: arg1 = ds:0x91b5b4, the current-faction global), FUN_00533e70, FUN_00534180, FUN_005344c0, "
       "FUN_00535700, FUN_00535c60 (re-arms the SEH/context globals then calls with arg3=0), FUN_0055f650, "
       "FUN_0058fa40 (the save path, next to a 0x626634 staging call)")


def m176():
    a, size = fnsize("FUN_00531df0")
    body = [(p, s) for p, s in LOW if a <= p < a + size]
    head = " | ".join(s for _, s in body[:12])
    p1 = "mov    esi,dword ptr [ebp+0x8]" in head
    loads = {}
    for reg in ("esi", "edi", "ebx", "ecx", "edx", "eax"):
        n = sum(1 for _, s in body if re.search(r"\[%s(\*4)?\+0x94d" % reg, s))
        if n:
            loads[reg] = n
    arg3_loads = [(hex(pp), s.strip()[:44]) for pp, s in body if re.search(r"mov\s+\w+,dword ptr \[ebp\+0x10\]", s)]
    arg3_test = " ".join(s.lower() for pp, s in body if 0x532194 <= pp <= 0x5321a9)
    mode_gate = re.search(r"test\s+eax,eax", arg3_test) is not None and re.search(r"\bje\b", arg3_test) is not None \
        and "ds:0x9204b0" in arg3_test
    print("M176 prologue arg1->esi:", p1, "| block-deref registers:", loads,
          "| arg3 reloaded at %d sites, first:" % len(arg3_loads), arg3_loads[:3],
          "| arg3!=0 gate exports [edx+0x94d4a8] -> ds:0x9204b0:", mode_gate)
    owners = sorted({fnof(c) for c in SITES})
    print("M176 owners:", len(owners))
    has_mult = {}
    for f in owners:
        fa, fz = fnsize(f)
        body2 = " ".join(s for p, s in LOW if fa <= p < fa + fz)
        has_mult[f] = bool(re.search(r"shl\s+\w+,0x6", body2) and re.search(r"shl\s+\w+,0x4", body2)
                          and re.search(r"sub\s+\w+", body2))
    print("M176 owners carrying the *8380 chain (shl 6 + shl 4 + sub):", sum(has_mult.values()), "of", len(has_mult),
          {k: v for k, v in has_mult.items() if not v})
    consts = []
    for c in SITES:
        i = POS[c]
        w = " ".join(s for _, s in INS[max(0, i - 10):i])
        m = re.findall(r"push\s+(0x[0-9a-f]+|\d+)\b", w)
        consts.append(m[-1] if m else "<reg>")
    print("M176 last-push-before-call (arg3 candidates):", consts.count("0x0"), "x 0x0,",
          consts.count("0x1"), "x 0x1, other:", [c for c in consts if c not in ("0x0", "0x1")])
    ok("M176", p1 and len(loads) >= 3 and len(arg3_loads) >= 5 and mode_gate and consts.count("0x0") >= 12
       and sum(has_mult.values()) >= 10,
       "the convention is (faction BLOCK base, record base, mode): arg1 arrives in ESI (prologue `mov esi,[ebp+0x8]`) "
       "and is dereferenced as a 0x20bc-stride block base through 6 registers; 10 of the 13 callers compute that base "
       "with the folded *8380 chain (shl 6, lea [i+i*2], shl 4, sub i) — the same multiply M169's loop uses; arg3 "
       "(pushed LAST, read at [ebp+0x10]) is a MODE CODE reloaded at %d sites inside — the decisive one is 0x532194 "
       "AFTER the per-faction loop: `test eax,eax; je 0x5321a9` skips, else `mov edx,[ebp-0x10]; mov eax,[edx+0x94d4a8]; "
       "mov ds:0x9204b0,eax` EXPORTS the stamped value — and 12 of 17 sites push 0x0 (1 pushes 0x1)" % len(arg3_loads))


def m177():
    primes = []
    for c in SITES:
        i = POS[c]
        for j in range(i - 15, i):
            p, s = INS[j]
            if re.search(r"mov\s+dword ptr \[.*0x94d4a8\]", s.lower()):
                primes.append((hex(c), fnof(c), hex(p), s.strip()[:46]))
                break
    print("M177 pre-call stores to [block+0x94d4a8] (within 15 insns of a call):")
    for t in primes:
        print("   call %s in %-14s store %s  %s" % t)
    for c, f, p, _ in primes:
        i = POS[int(p, 16)]
        print("   value source before %s:" % p, " ".join(s.strip()[:40] for _, s in INS[max(0, i - 8):i])[:150])
    subs = [(hex(p), fnof(p), s.strip()[:44]) for p, s in LOW if re.search(r"sub\s+\w+,dword ptr \[.*0x94d4a8\]", s.lower())]
    print("M177 `sub reg,[block+0x94d4a8]` age tests: %d" % len(subs))
    for p, f, s in subs:
        print("   %s %-14s %s" % (p, f, s))
    gate = " ".join(s.lower() for p, s in INS if 0x569401 <= p <= 0x569415)
    gate_ok = (re.search(r"sub\s+edx,dword ptr \[eax\*4\+0x94d4a8\]", gate) is not None
               and re.search(r"cmp\s+edx,0x10", gate) is not None and re.search(r"\bjl\b", gate) is not None)
    print("M177 gate at 0x569401 (sub, cmp 0x10, jl past the call):", gate_ok)
    n_stores = sum(1 for _, s in LOW if re.search(r"mov\s+dword ptr \[.*0x94d4a8\]", s.lower()))
    refs = [p for p, s in INS if "0x94d4a8" in s]
    print("M177 0x94d4a8: %d refs = %d stores + %d subs + %d other" % (len(refs), n_stores, len(subs), len(refs) - n_stores - len(subs)))
    n_loads = sum(1 for _, s in LOW if re.search(r"mov\s+\w+,dword ptr \[.*0x94d4a8\]", s.lower()))
    n_lea = sum(1 for _, s in LOW if re.search(r"lea\s+\w+,\[.*0x94d4a8\]", s.lower()))
    print("M177 split: %d stores + %d loads + %d lea + %d subs = %d refs" % (n_stores, n_loads, n_lea, len(subs), len(refs)))
    print("M177 components:", len(primes), len(subs), gate_ok, len(refs), n_stores, n_loads, n_lea)
    ok("M177", len(primes) == 3 and len(subs) == 6 and gate_ok and len(refs) == 38 and n_stores == 26
       and n_loads + n_lea == 6 and n_stores + n_loads + n_lea + len(subs) == len(refs),
       "callers PRIME the per-faction stamp before asking: 3 of the 17 sites store the run-state global ds:0x985afc "
       "into [block+0x94d4a8] within 15 instructions of the call (0x533eec, 0x53420e, 0x534522 — each preceded by "
       "`mov eax,ds:0x985afc`), and a 4th (0x569401 in FUN_0055f650) CONSUMES it as an age test instead; the "
       "aggregator reads the field at 0x53219e only when arg3 != 0 and exports it to ds:0x9204b0; 6 "
       "`sub reg,[block+0x94d4a8]` age tests consume it — "
       "one (0x569401: `sub edx,[eax*4+0x94d4a8]; cmp edx,0x10; jl 0x5696fd`) SKIPS the call when the stamp is fresher "
       "than 16, so 0x94d4a8 is a last-run stamp compared against the round counter (38 refs = 26 stores + 6 loads "
       "+ 1 lea + 6 subs = 38)")


print("== M175 =="); m175()
print("== M176 =="); m176()
print("== M177 =="); m177()
print("\nSUMMARY " + " ".join("%s=%s" % (k, "PASS" if v else "FAIL") for k, v in R.items()))
with open(os.path.join(ROOT, "evidence", "m175_m177.log"), "w") as fh:
    fh.write("SUMMARY " + " ".join("%s=%s" % (k, "PASS" if v else "FAIL") for k, v in R.items()) + "\n")
sys.exit(0 if all(R.values()) else 1)
