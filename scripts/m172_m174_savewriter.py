#!/usr/bin/env python3
"""M172-M174: who calls the bit-decoder and what its byte really is; the aggregator's two counters; the tristate header's tests.

  M172  FUN_004dc100 — 2 callers, both dispatch legs of save-driver functions; the byte is NOT a caller argument,
        it is the shared scratch global ds:0x99aa38, and the function PACKS state into it, writes the record,
        then DECODES the same byte back. Siblings 0x4dc390/0x4dc5f0/0x4dc8d0/0x4dcc10 share the template.
  M173  ds:0x9204ac / ds:0x9204c4 — the aggregator's COUNT and SUM; exactly 3 and 1 consumers.
  M174  0x94d80c — the tristate header's test sites and its arithmetic (signed-modifier) consumers.

    python3 scripts/m172_m174_savewriter.py
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


def ok(mid, cond, text):
    R[mid] = cond
    print("%s  %s — %s" % (mid, "PASS" if cond else "FAIL", text))


def idx_of(pc):
    for i, (p, _) in enumerate(INS):
        if p == pc:
            return i
    raise KeyError(hex(pc))


def m172():
    calls = [pc for pc, s in LOW if re.search(r"call\s+0x4dc100\b", s)]
    print("M172 call sites of 0x4dc100:", [hex(c) for c in calls], "count", len(calls))
    legs = []
    for c in calls:
        i = idx_of(c)
        prev = INS[i - 1][1].lower()
        owner = fnof(c)
        # a dispatch leg pushes NOTHING between its last insn and the call
        pushes = [INS[j][1] for j in range(i - 3, i) if INS[j][1].lower().startswith("push")]
        legs.append((hex(c), owner, prev[:40], len(pushes)))
        print("   leg %s in %s | prev: %s | pushes in prior 3 insns: %d" % legs[-1])
    # pack leg: loads the byte from the shared global, rewrites AL/AH, stores back, then the tagged write
    i_c1 = idx_of(0x4DC1C1)
    load_global = "mov    eax,ds:0x99aa38" in INS[i_c1][1].lower()
    ors = [(hex(p), s) for p, s in LOW if 0x4DC1C8 <= p <= 0x4DC26A and re.match(r"\s*(or|and)\s+(al|ah),", s.lower())]
    store_back = any("mov    ds:0x99aa38,eax" in s.lower() for p, s in LOW if p == 0x4DC274)
    write_call = any("call   0x6267a5" in s.lower() for p, s in LOW if p == 0x4DC279)
    print("   pack: loads global=%s; or/and al|ah rewrites=%d (first %s); store-back@0x4dc274=%s; tagged write@0x4dc279=%s"
          % (load_global, len(ors), ors[0][0], store_back, write_call))
    # decode leg: reload the SAME global after the write gate, then store the decoded fields
    reload_global = any("mov    eax,ds:0x99aa38" in s.lower() for p, s in LOW if p == 0x4DC29C)
    setne_stores = [(hex(p), s) for p, s in LOW if re.match(r"\s*mov\s+dword ptr \[.*0x94d81[048c]\]", s.lower())
                    and 0x4DC2C1 <= p <= 0x4DC301]
    tri_stores = [(hex(p), s) for p, s in LOW if re.search(r"mov\s+dword ptr \[esi\+0x94d80c\],(0x1|0xffffffff|0x0)\b", s.lower())
                  and 0x4DC100 <= p <= 0x4DC386]
    band_ors = [(hex(p), s) for p, s in LOW if re.search(r"or\s+dword ptr \[esi\+0x94d430\],0x[0-9a-f]+", s.lower())
                and 0x4DC33B <= p <= 0x4DC36B]
    print("   decode: reload global@0x4dc29c=%s; setne stores to the quad=%d %s; tristate stores=%s; band ors=%d"
          % (reload_global, len(setne_stores), [p for p, _ in setne_stores],
             [(p, s.split(",")[-1].strip()) for p, s in tri_stores], len(band_ors)))
    # the byte buffer is a shared scratch global: census its writers
    refs38 = [(hex(p), fnof(p), s) for p, s in INS if "0x99aa38" in s]
    stores38 = [(p, fnof(p)) for p, s in INS if re.search(r"mov\s+(dword ptr )?ds:0x99aa38", s.lower())]
    ui_stores = [p for p, f in stores38 if f == "FUN_0041a8d0" or (0x41A9B7 <= p <= 0x41AB4A)]
    print("   ds:0x99aa38: %d refs, %d stores; stores in the 0x41a9xx UI-build block: %d; other storing functions: %s"
          % (len(refs38), len(stores38), len(ui_stores), sorted({f for p, f in stores38 if not (0x41A9B7 <= p <= 0x41AB4A)})))
    # sibling save-section writers: the record-context opener 0x4d9fb0 is called by EXACTLY four functions,
    # two of which (0x4dc100, 0x4dc390) open with `mov eax,ds:0x91b5b4; push 1; push eax; call 0x4d9fb0`
    fam_tmpl = [(hex(p), fnof(p)) for p, s in LOW if "ds:0x91b5b4" in s.lower() and 0x4DC100 <= p < 0x4DD000]
    print("   0x91b5b4 loads inside the 0x4dcXXX band:", fam_tmpl)
    tw = [pc for pc, s in LOW if "call   0x6267a5" in s]
    band = [pc for pc in tw if 0x4D9000 <= pc < 0x4E1700]
    print("   tagged-write 0x6267a5: %d sites total, %d inside the save band 0x4d9000-0x4e1700" % (len(tw), len(band)))
    callers9fb0 = sorted({fnof(pc) for pc, s in LOW if "call   0x4d9fb0" in s.lower()})
    print("   0x4d9fb0 (the record-context opener) is called by:", callers9fb0)
    both_dispatch = (len(calls) == 2 and all(l[3] == 0 for l in legs)
                     and {"FUN_00512b40", "FUN_00516b80"} == {l[1] for l in legs})
    pack_dir = load_global and len(ors) >= 10 and store_back and write_call
    decode_dir = reload_global and len(setne_stores) == 4 and len(tri_stores) == 3 and len(band_ors) == 4
    fam_ok = (len(fam_tmpl) == 2 and len(tw) == 18 and len(band) == 12
              and callers9fb0 == ["FUN_004dc100", "FUN_004dc390", "FUN_004e0260", "FUN_005a2930"])
    ok("M172", both_dispatch and pack_dir and decode_dir and fam_ok,
       "FUN_004dc100 is a SAVE-SECTION WRITER, not a caller-fed decoder: its 2 call sites are argument-free dispatch "
       "legs in FUN_00512b40 (0x51500f) and FUN_00516b80 (0x517eb6); the byte it decodes is the SHARED scratch global "
       "ds:0x99aa38 (19 stores in the 0x41a9xx UI-build block), which its PACK leg first rewrites from the struct + "
       "band-flag bits (or/and al,ah), stores back, and writes via the tagged writer 0x6267a5 — then the DECODE leg "
       "re-materialises 4 boolean dwords + the tristate + band bits. The record-context opener 0x4d9fb0 is called by "
       "EXACTLY four writers (0x4dc100, 0x4dc390, 0x4e0260, 0x5a2930) and the tagged record writer 0x6267a5 has 18 "
       "sites, 12 of them in the 0x4d9xxx-0x4e1xxx save band — this function is one member of the save-section family")


def m173():
    for name, addr, tests in (("0x9204ac", 0x9204AC, (0x53346C, 0x53A9CC, 0x54D30D)), ("0x9204c4", 0x9204C4, (0x533478,))):
        refs = [(hex(p), fnof(p), s) for p, s in INS if hex(addr) in s]
        stores = [p for p, s in INS if re.search(r"mov\s+dword ptr ds:0x%x".lower() % addr, s.lower())]
        print("M173 %s: %d refs, %d stores %s" % (name, len(refs), len(stores), [hex(p) for p in stores]))
        for p, f, s in refs:
            print("   %s %-14s %s" % (p, f, s[:52]))
    gate = " ".join(s.lower() for p, s in INS if 0x53346C <= p <= 0x533493)
    shape = ("cmp    dword ptr ds:0x9204ac,0x2" in gate and "jge" in gate
             and "mov    edx,dword ptr ds:0x9204c4" in gate and "lea    ecx,[edx+eax*2]" in gate and "add    eax,ecx" in gate)
    print("   gate window 0x53346c-0x533493: count<2 + 3*(sum+table[ecx]) vs table[ebx]:", shape)
    abs_leg = " ".join(s.lower() for p, s in INS if 0x532096 <= p <= 0x5320a1)
    print("   aggregator stores header-abs into [ebp-0x20]:", "neg" in abs_leg and "jge" in abs_leg)
    ac_refs = [p for p, s in INS if "0x9204ac" in s]
    c4_refs = [p for p, s in INS if "0x9204c4" in s]
    ac_stores = [p for p in ac_refs if any(p == q for q, s in INS if re.match(r"\s*mov\s+dword ptr ds:0x9204ac", s.lower()))]
    print("M173 ac stores:", [hex(p) for p in ac_stores], "c4 refs", len(c4_refs), "shape", shape)
    ok("M173", len(ac_refs) == 6 and len(c4_refs) == 4 and len(ac_stores) == 2 and shape,
       "the aggregator's pair is a COUNT and a SUM with exactly 3 and 1 CONSUMER sites (reads/tests): each has 2 stores "
       "(the zero at 0x532084/0x532090 + the loop read-modify-write at 0x53214a/0x532158) and the count's 3rd loop step "
       "is a `mov ecx,[g]` load at 0x53213d; consumers are 0x53346c/0x533478 INSIDE FUN_00531df0 "
       "(gate: count < 2, then table[ebx] >= 3*(sum + table[ecx]), then rank < 6), 0x53a9cc in FUN_0053a9c0 (count + "
       "ds:0x920720 builds a local total) and 0x54d30d in FUN_00546800 (count != 0 gates a branch)")


def m174():
    cmp_sites = [(hex(p), fnof(p), s) for p, s in LOW if re.search(r"cmp\s+dword ptr \[.*\+0x94d80c\]", s.lower())]
    arith = [(hex(p), fnof(p), s) for p, s in LOW if re.search(r"(sub|add)\s+\w+,\s*dword ptr \[.*\+0x94d80c\]", s.lower())]
    print("M174 cmp sites (%d):" % len(cmp_sites))
    for p, f, s in cmp_sites:
        print("   %s %-14s %s" % (p, f, s.strip()[:52]))
    print("M174 arithmetic consumers (%d):" % len(arith))
    for p, f, s in arith:
        print("   %s %-14s %s" % (p, f, s.strip()[:52]))
    owners = sorted({f for _, f, _ in cmp_sites})
    consts0 = sum(1 for _, _, s in cmp_sites if s.strip().endswith(",0x0"))
    consts1 = sum(1 for _, _, s in cmp_sites if s.strip().endswith(",0x1"))
    regtest = sum(1 for _, _, s in cmp_sites if re.search(r",(e[a-z]{2}[0-9]?|al|cl|dl|bl)$", s.strip()))
    print("M174 owners:", owners, "consts: vs0=%d vs1=%d reg=%d arith=%d" % (consts0, consts1, regtest, len(arith)))
    ok("M174", len(cmp_sites) == 7 and len(owners) == 4 and consts0 == 2 and consts1 == 4 and regtest == 1 and len(arith) >= 6,
       "the tristate header is tested at exactly 7 sites in 4 functions (2 `cmp vs 0` at 0x4a642f/0x4a6450 [FUN_004a5eb0], "
       "4 `cmp vs 1` at 0x55ee48 [FUN_0055ec10] + 0x576891/0x576bd8/0x576e45 [FUN_00574370], "
       "1 reg-vs-mem `cmp [eax+0x94d80c],ecx` at 0x5520cd [FUN_00551e50]) — and beyond the tests it is CONSUMED "
       "ARITHMETICALLY 6+ times (`sub reg,[hdr]` in FUN_0053cb20 x2, FUN_00546800 x2, FUN_005551e0, FUN_0055f650; "
       "`add ebx,[hdr]` in FUN_005551e0), so its 1/0/-1 value is a SIGNED MODIFIER in scoring, not just a flag; "
       "the aggregator itself reads it as |value| (0x53206f + neg/jge leg)")


print("== M172 =="); m172()
print("== M173 =="); m173()
print("== M174 =="); m174()
print("\nSUMMARY " + " ".join("%s=%s" % (k, "PASS" if v else "FAIL") for k, v in R.items()))
with open(os.path.join(ROOT, "evidence", "m172_m174.log"), "w") as fh:
    fh.write("SUMMARY " + " ".join("%s=%s" % (k, "PASS" if v else "FAIL") for k, v in R.items()) + "\n")
sys.exit(0 if all(R.values()) else 1)
