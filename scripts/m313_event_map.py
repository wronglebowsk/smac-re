#!/usr/bin/env python3
"""M313 (s278, STATIC, zero box): NAME THE EVENTS.
M312 closed WHO-fires-the-selection-check to two trunks; this milestone names
the layer ABOVE them: the 15 callers of the cursor thunk FUN_004736a0 and the
28 owner functions holding FUN_00472810's 53 call sites - by exact census,
shared-band membership, and vtable/message-map dispatch structure (PE bytes).

Gates print a table then assert; digest at the end, two runs byte-identical.
Mutation harness: scripts/m313_mutate.py.
"""
import bisect
import collections
import hashlib
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import m308_site_list as E

IDX = os.path.join(REPO, "ghidra_out", "index.csv")
TEXT = os.path.join(REPO, "scratch", "m574", "text.txt")
EXE = os.path.join(REPO, "terran.exe")

checks = []
def ck(name, ok, detail=""):
    checks.append((name, bool(ok), detail))
    print(("OK   " if ok else "FAIL ") + name + ": " + detail)

def main():
    idx = E.load_index()
    addrs = [a for a, _ in idx]
    names = dict(idx)
    def owner(va):
        return names[addrs[max(0, bisect.bisect_right(addrs, va) - 1)]]
    ins, _order = E.parse_text()
    def calls_to(t):
        return sorted(a for a, (b, ops) in ins.items() if b == "call"
                      and ops.split(",")[0].strip() == "0x%x" % t)

    # A1 exact 15-site census of callers of the cursor thunk FUN_004736a0
    WANT_6A0 = {
        0x47373E: "FUN_004736e0", 0x50C08F: "FUN_0050c060",
        0x50C19F: "FUN_0050c170", 0x50C2C1: "FUN_0050c290",
        0x50C5F6: "FUN_0050c550", 0x50CC36: "FUN_0050cab0",
        0x50F7D2: "FUN_0050f420", 0x50FBDB: "FUN_0050fb80",
        0x50FC10: "FUN_0050fb80", 0x50FCE0: "FUN_0050fc50",
        0x50FD0F: "FUN_0050fc50", 0x515638: "FUN_00512b40",
        0x5164B0: "FUN_00512b40", 0x5164E2: "FUN_00512b40",
        0x5175B4: "FUN_00516b80",
    }
    got = {a: owner(a) for a in calls_to(0x4736A0)}
    ck("A1_thunk_callers_exact", got == WANT_6A0, "%d sites" % len(got))

    # A2 the hub's 28 owners, exact set (from M312's run, re-derived here)
    hub_sites = calls_to(0x472810)
    owners = sorted({owner(a) for a in hub_sites})
    WANT_OWNERS = [
        "FUN_004738f0", "FUN_00473960", "FUN_004739a0", "FUN_0048e530",
        "FUN_004c40e0", "FUN_004cbc70", "FUN_004e10c0", "FUN_0050bb20",
        "FUN_0050bde0", "FUN_0050bea0", "FUN_0050c060", "FUN_0050c170",
        "FUN_0050c290", "FUN_0050c550", "FUN_0050ca10", "FUN_0050cab0",
        "FUN_0050ef60", "FUN_0050f420", "FUN_0050fb80", "FUN_0050fc50",
        "FUN_005103b0", "FUN_00510730", "FUN_00510bd0", "FUN_00511960",
        "FUN_00512450", "FUN_00512b40", "FUN_00516b80", "FUN_0058b1b0",
    ]
    ck("A2_hub_owner_set_exact", owners == WANT_OWNERS,
       "%d owners, %d sites" % (len(owners), len(hub_sites)))

    # A3 interaction-band law: hub owners and thunk owners both live in
    # [0x50bb20, 0x5175b4]; exact member lists.
    LO, HI = 0x50BB20, 0x5175B4
    band_hub = [o for o in owners if LO <= int(o[4:], 16) < HI]
    WANT_BAND_HUB = ["FUN_0050bb20", "FUN_0050bde0", "FUN_0050bea0",
        "FUN_0050c060", "FUN_0050c170", "FUN_0050c290", "FUN_0050c550",
        "FUN_0050ca10", "FUN_0050cab0", "FUN_0050ef60", "FUN_0050f420",
        "FUN_0050fb80", "FUN_0050fc50", "FUN_005103b0", "FUN_00510730",
        "FUN_00510bd0", "FUN_00511960", "FUN_00512450", "FUN_00512b40",
        "FUN_00516b80"]
    ck("A3a_band_hub_owners", band_hub == WANT_BAND_HUB,
       "%d of 28 hub owners in band" % len(band_hub))
    thunk_band = sorted({v for k, v in got.items() if LO <= k < HI})
    WANT_THUNK_BAND = ["FUN_0050c060", "FUN_0050c170", "FUN_0050c290",
        "FUN_0050c550", "FUN_0050cab0", "FUN_0050f420", "FUN_0050fb80",
        "FUN_0050fc50", "FUN_00512b40"]
    ck("A3b_band_thunk_owners", thunk_band == WANT_THUNK_BAND,
       "%d distinct thunk owners in band" % len(thunk_band))
    nonband = [o for o in owners if o not in WANT_BAND_HUB]
    ck("A3c_offband_hub_owners", nonband == ["FUN_004738f0", "FUN_00473960",
        "FUN_004739a0", "FUN_0048e530", "FUN_004c40e0", "FUN_004cbc70",
        "FUN_004e10c0", "FUN_0058b1b0"], "%d off-band" % len(nonband))

    # A4 the two pumps: exact band-member callee sets + exact caller sets
    def fn_span(f):
        k = [i for i, (a, n) in enumerate(idx) if n == "FUN_%08x" % f][0]
        return idx[k][0], idx[k + 1][0] if k + 1 < len(idx) else 0xFFFFFFFF
    def direct_callees(f):
        s0, s1 = fn_span(f)
        return sorted(a for a, (b, o) in ins.items() if b == "call"
                      and s0 <= a < s1 and o.split(",")[0].strip().startswith("0x")
                      and "[" not in o.split(",")[0])
    BANDSET = set(int(o[4:], 16) for o in WANT_BAND_HUB) | set(
        int(o[4:], 16) for o in WANT_OWNERS) | {0x4736E0}  # + cursor thunk
    pa_sites = direct_callees(0x512B40)
    pa_band = sorted({"FUN_%08x" % int(ins[a][1].split(",")[0], 16)
                      for a in pa_sites if int(ins[a][1].split(",")[0], 16) in BANDSET})
    ck("A4a_pumpA_band_callees", pa_band == [
        "FUN_004736e0", "FUN_004738f0", "FUN_004739a0", "FUN_004e10c0",
        "FUN_0050bea0", "FUN_0050c170", "FUN_0050cab0", "FUN_005103b0",
        "FUN_00510730", "FUN_00510bd0", "FUN_00511960", "FUN_00512450"],
        "pumpA(FUN_00512b40)->%d band members" % len(pa_band))
    pb_sites = direct_callees(0x516B80)
    pb_band = sorted({"FUN_%08x" % int(ins[a][1].split(",")[0], 16)
                      for a in pb_sites if int(ins[a][1].split(",")[0], 16) in BANDSET})
    ck("A4b_pumpB_band_callees", pb_band == [
        "FUN_004736e0", "FUN_004738f0", "FUN_004739a0", "FUN_004c40e0",
        "FUN_004e10c0", "FUN_0050c170", "FUN_0050cab0", "FUN_005103b0",
        "FUN_00510730", "FUN_00510bd0"],
        "pumpB(FUN_00516b80)->%d band members" % len(pb_band))
    ck("A4c_pumpA_callers", sorted({owner(a) for a in calls_to(0x512B40)}) ==
        ["FUN_0041bda0", "FUN_004c5d60"], "callers: vtable-method + dialog-fam")
    ck("A4d_pumpB_callers", sorted({owner(a) for a in calls_to(0x516B80)}) ==
        ["FUN_005186b0"], "single caller")
    mc = sorted({"FUN_%08x" % int(ins[a][1].split(",")[0], 16)
                 for a in direct_callees(0x476580)
                 if int(ins[a][1].split(",")[0], 16) in BANDSET})
    ck("A4e_mapclick_band_callees", mc == [
        "FUN_004739a0", "FUN_0050bde0", "FUN_0050ca10", "FUN_0050cab0",
        "FUN_0050fb80"], "M28-named map_click_handler(FUN_00476580)->%d" % len(mc))
    pa_hub = sorted(a for a in hub_sites if 0x512B40 <= a < fn_span(0x512B40)[1])
    pb_hub = sorted(a for a in hub_sites if 0x516B80 <= a < fn_span(0x516B80)[1])
    ck("A4f_pumps_contain_hub_sites",
        pa_hub == [0x51319E, 0x5137CF, 0x51562D, 0x51567D, 0x5163D4, 0x5164A5,
                   0x51653A] and pb_hub == [0x516C3E, 0x516D03, 0x5172F3,
                   0x51753E, 0x5175A9, 0x5175FA],
        "pumpA %d + pumpB %d hub sites (7+6)" % (len(pa_hub), len(pb_hub)))

    # A5 vtable 0x672290: 490 slots; slot134 = pumpA's only code-path entry
    # (FUN_0041bda0), slot415 = M284-named chooser row dispatcher (FUN_005f6aa3)
    blob = open(EXE, "rb").read()
    ib, psecs = E.pe_sections(blob)
    def off(va):
        return E.va2off(psecs, va)
    vt = 0x672290
    def slot(i):
        o, nm = off(vt + 4 * i)
        return struct.unpack_from("<I", blob, o)[0]
    def in_text(v):
        o, nm = off(v)
        return nm == ".text"
    n = 0
    while in_text(slot(n)): n += 1
    lo = 0
    while in_text(slot(lo - 1)) if lo else False: lo -= 1
    ck("A5a_vtable_slots", n == 490 and slot(134) == 0x41BDA0
        and slot(415) == 0x5F6AA3 and slot(0) == 0x422310,
        "vtable@0x672290 slots=%d slot134=FUN_0041bda0 slot415=FUN_005f6aa3" % n)
    vsum = hashlib.sha256(b"".join(struct.pack("<I", slot(i)) for i in range(n))).hexdigest()[:16]
    ck("A5b_vtable_digest", vsum == "f2e2c9dfae9ba011", "digest %s" % vsum)

    # A6 pump jump tables: exact (jmp site -> table) census + slot counts
    def tbl_jmps(f):
        s0, s1 = fn_span(f)
        out = []
        for a in sorted(x for x in range(s0, s1) if x in ins):
            b, o = ins[a]
            if b == "jmp" and "*" in o and "+" in o and "0x5" in o:
                out.append((a, int(o.split("+")[-1].strip().rstrip("]"), 16)))
        return out
    ta = tbl_jmps(0x512B40)
    ck("A6a_pumpA_tables", ta == [
        (0x512BA7, 0x5165CC), (0x513219, 0x516628), (0x51328C, 0x516698),
        (0x51341D, 0x516708), (0x51361D, 0x51678C), (0x513928, 0x5167E8),
        (0x514E39, 0x516858), (0x514E8E, 0x516888), (0x514F84, 0x5168D8),
        (0x515059, 0x5168F0), (0x515506, 0x51691C), (0x51577B, 0x5169B8),
        (0x515815, 0x5169CC), (0x515B58, 0x5169EC), (0x515DC7, 0x516A28),
        (0x516022, 0x516A4C), (0x516096, 0x516A6C)],
        "pumpA: %d table-jmps" % len(ta))
    tb_ = tbl_jmps(0x516B80)
    ck("A6b_pumpB_tables", tb_ == [
        (0x516DAE, 0x5181D0), (0x517031, 0x518204), (0x517140, 0x518248),
        (0x5172AC, 0x5182B4), (0x5174D7, 0x5182F8), (0x517778, 0x518418),
        (0x517A51, 0x518484), (0x517ABF, 0x518494), (0x517BD3, 0x5184DC),
        (0x517CBB, 0x5185C4), (0x518007, 0x5185E8)],
        "pumpB: %d table-jmps" % len(tb_))
    def slots_between(a, b): return (b - a) // 4
    ck("A6c_command_table_size", slots_between(0x5165CC, 0x516628) == 23,
        "menu/toolbar-ID switch table = 23 slots (0x30041 base + Ghidra C)")
    ck("A6d_vk_table_size", slots_between(0x516628, 0x516698) == 28,
        "navigation-VK switch table = 28 slots")
    ck("A6e_letter_table_size", slots_between(0x5181D0, 0x518204) == 13,
        "letter-key 'Q'..'Z'+ switch table = 13 slots")

    # A7 FUN_005186b0 (pumpB's sole caller) has NO call/jmp refs anywhere and
    # EXACTLY ONE stored u32 in the whole file: `push 0x5186b0` (imm32 field at 0x51892e),
    # inside FUN_00518820 (itself reached only from init FUN_00580260) - the
    # pointer is installed as a callback at startup (INFERRED mechanism; the
    # census - zero call/jmp, exactly one stored u32 at that site - is VERIFIED).
    ref = sum(1 for a, (b, o) in ins.items()
              if b in ("call", "jmp") and o.strip() == "0x5186B0")
    hits = []
    for _nm, sv, _vsz, rsz, rp in psecs:
        if not rsz: continue
        data = blob[rp:rp + rsz]; pos = data.find(struct.pack("<I", 0x5186B0))
        while pos != -1:
            hits.append(sv + pos); pos = data.find(struct.pack("<I", 0x5186B0), pos + 4)
    ck("A7_pumpB_entry_callback_registration",
        ref == 0 and hits == [0x51892E]  # imm32 field of the push at 0x51892d and ins[0x51892D] == ("push", "0x5186b0")
        and owner(0x51892D) == "FUN_00518820"
        and sorted({owner(x) for x in calls_to(0x518820)}) == ["FUN_00580260"],
        "call/jmp=%d stored=%s@0x51892d(owner FUN_00518820<-FUN_00580260)" % (ref, hits))

    print("digest", hashlib.sha256(
        "".join("%s=%d" % (n, o) for n, o, _ in checks).encode()).hexdigest()[:16])
    nfail = sum(1 for _, o, _ in checks if not o)
    print("== M313: %d/%d ==" % (len(checks) - nfail, len(checks)))
    return 1 if nfail else 0

if __name__ == "__main__":
    sys.exit(main())
