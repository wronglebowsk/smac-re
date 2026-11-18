#!/usr/bin/env python3
"""M313 (s278, STATIC, zero box): NAME THE EVENTS.
M312 closed WHO-fires-the-selection-check to two trunks; this milestone names
the layer ABOVE them: the 15 callers of the cursor thunk FUN_004736a0 and the
28 owner functions holding FUN_00472810's 53 call sites - by exact census,
band membership, the two command pumps, the .text-pointer run carrying
pumpA's door, and the startup-callback registration of pumpB's entry.

Revision after the Greptile review of #294 (2 P1 + 7 P2, all accepted or
honestly narrowed):
 - P1 band-set: pump callee claims now split IN-BAND vs OFF-BAND with exact
   lists; "band members" no longer quietly covers FUN_004736e0/004738f0/...
 - P1 vtable: the .text-pointer run starting 0x672290 spans MULTIPLE class
   tables (the chooser FAMILY dialog table base 0x6728c0 = 0x67290c - 0x4c,
   NAMED ## M288) - claim narrowed to entries-at-addresses + run digest; NO
   single-class table/slot identity is claimed.
 - P2 A6c-e were decorative (hardcoded subtraction): replaced by switch
   ENCODING laws read from PE bytes. pumpA's two switches are TWO-STAGE
   (byte lookup map 0x5165ec keys 0..0x39 -> 8-slot jump 0x5165cc; byte map
   0x516638 keys 0..0x5c -> 4-slot jump 0x516628); pumpB's letter switch is
   one-stage (key = code - 0x51 'Q', bound <= 0xc, 13-slot table 0x5181d0).
   Exact target lists + default targets pinned from bytes, plus the 12
   literal head instructions.
 - P2 A7: the ref count compared "0x5186B0" against LOWERCASE ops (a
   `call 0x5186b0` would have been missed - decorative); now numeric. The
   push-opcode check was swallowed by a trailing '#' on its own physical
   line - now a separate evaluated gate.
 - P2 A2: the 53 hub sites are pinned exactly (new A2b/A2c), not implied.
 - P2 digest: hashes the measured detail strings, not pass/fail booleans.
 - P2 VK names: 0x25=VK_LEFT, 0x27=VK_RIGHT (END/HOME are 0x23/0x24) -
   fixed here and in the docs.

Gates print a table then assert; digest at the end, two runs byte-identical.
Mutation harness: scripts/m313_mutate.py.
"""
import bisect
import hashlib
import os
import re
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
    def fn_span(f):
        k = [i for i, (a, n) in enumerate(idx) if n == "FUN_%08x" % f][0]
        return idx[k][0], (idx[k + 1][0] if k + 1 < len(idx) else 0xFFFFFFFF)
    def direct_callees(f):
        s0, s1 = fn_span(f)
        out = []
        for a, (b, o) in ins.items():
            if b != "call" or not (s0 <= a < s1):
                continue
            t = o.split(",")[0].strip().lower()
            if re.fullmatch(r"0x[0-9a-f]+", t):
                out.append((a, int(t, 16)))
        return sorted(out)

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

    # A2 hub owners AND the exact 53 call sites
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
    WANT_SITES = [
        0x473949, 0x473985, 0x473A48, 0x48E58A, 0x4C4416, 0x4C44E3, 0x4C457F,
        0x4CBECD, 0x4E1138, 0x50BBA2, 0x50BE77, 0x50BF5D, 0x50C084, 0x50C0D8,
        0x50C194, 0x50C1E8, 0x50C2B6, 0x50C5EB, 0x50CA66, 0x50CB37, 0x50CC2B,
        0x50CD06, 0x50F0E1, 0x50F4EB, 0x50F5E7, 0x50F7C7, 0x50F9C3, 0x50FBD0,
        0x50FCD5, 0x510695, 0x510763, 0x5107A1, 0x5107CA, 0x5107F8, 0x51082C,
        0x51086F, 0x511221, 0x511B42, 0x512766, 0x51319E, 0x5137CF, 0x51562D,
        0x51567D, 0x5163D4, 0x5164A5, 0x51653A, 0x516C3E, 0x516D03, 0x5172F3,
        0x51753E, 0x5175A9, 0x5175FA, 0x58C066,
    ]
    ck("A2a_hub_owner_set_exact", owners == WANT_OWNERS, "%d owners" % len(owners))
    ck("A2b_hub_sites_exact", hub_sites == WANT_SITES,
       "%d sites pinned" % len(hub_sites))

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

    # A4 pumps. MESH = 20 band hub-owners + 8 off-band hub owners + cursor
    # thunk. P1 fix: callee sets SPLIT in-band/off-band, exact lists.
    MESH = set(int(o[4:], 16) for o in WANT_BAND_HUB) | set(
        int(o[4:], 16) for o in WANT_OWNERS) | {0x4736E0}
    def split(f):
        d = direct_callees(f)
        inb = sorted({"FUN_%08x" % t for _, t in d if t in MESH and LO <= t < HI})
        off = sorted({"FUN_%08x" % t for _, t in d if t in MESH and not (LO <= t < HI)})
        return inb, off
    a_in, a_off = split(0x512B40)
    ck("A4a_pumpA_callees_split",
       a_in == ["FUN_0050bea0", "FUN_0050c170", "FUN_0050cab0", "FUN_005103b0",
                "FUN_00510730", "FUN_00510bd0", "FUN_00511960", "FUN_00512450"]
       and a_off == ["FUN_004736e0", "FUN_004738f0", "FUN_004739a0", "FUN_004e10c0"],
       "pumpA mesh callees 8 in-band + 4 off-band (off: %s)" % ",".join(a_off))
    b_in, b_off = split(0x516B80)
    ck("A4b_pumpB_callees_split",
       b_in == ["FUN_0050c170", "FUN_0050cab0", "FUN_005103b0", "FUN_00510730",
                "FUN_00510bd0"]
       and b_off == ["FUN_004736e0", "FUN_004738f0", "FUN_004739a0",
                     "FUN_004c40e0", "FUN_004e10c0"],
       "pumpB mesh callees 5 in-band + 5 off-band")
    ck("A4c_pumpA_callers", sorted({owner(a) for a in calls_to(0x512B40)}) ==
        ["FUN_0041bda0", "FUN_004c5d60"], "callers: run-method + dialog-fam")
    ck("A4d_pumpB_callers", sorted({owner(a) for a in calls_to(0x516B80)}) ==
        ["FUN_005186b0"], "single caller")
    mc_in = sorted({"FUN_%08x" % t for _, t in direct_callees(0x476580)
                    if t in MESH and LO <= t < HI})
    mc_off = sorted({"FUN_%08x" % t for _, t in direct_callees(0x476580)
                     if t in MESH and not (LO <= t < HI)})
    ck("A4e_mapclick_mesh_callees",
       mc_in == ["FUN_0050bde0", "FUN_0050ca10", "FUN_0050cab0", "FUN_0050fb80"]
       and mc_off == ["FUN_004739a0"],
       "M28-named map_click_handler(FUN_00476580): 4 in-band + 1 off-band")
    pa_hub = sorted(a for a in hub_sites if 0x512B40 <= a < fn_span(0x512B40)[1])
    pb_hub = sorted(a for a in hub_sites if 0x516B80 <= a < fn_span(0x516B80)[1])
    ck("A4f_pumps_contain_hub_sites",
       pa_hub == [0x51319E, 0x5137CF, 0x51562D, 0x51567D, 0x5163D4, 0x5164A5,
                  0x51653A] and pb_hub == [0x516C3E, 0x516D03, 0x5172F3,
                  0x51753E, 0x5175A9, 0x5175FA],
       "pumpA %d + pumpB %d hub sites (7+6)" % (len(pa_hub), len(pb_hub)))

    # A5 (P1-narrowed) .text-pointer RUN from 0x672290: entries pinned BY
    # ADDRESS; the run spans MULTIPLE class tables (chooser FAMILY dialog
    # table base 0x6728c0 = 0x67290c - 0x4c, NAMED ## M288) - NO single-table
    # or slot-identity claim.
    blob = open(EXE, "rb").read()
    _ib, psecs = E.pe_sections(blob)
    def off(va):
        return E.va2off(psecs, va)
    def word(va):
        o, _nm = off(va)
        return struct.unpack_from("<I", blob, o)[0]
    def in_text(v):
        return off(v)[1] == ".text"
    RUN = 0x672290
    n = 0
    while in_text(word(RUN + 4 * n)):
        n += 1
    o0, _ = off(RUN)
    rsum = hashlib.sha256(blob[o0:o0 + 4 * n]).hexdigest()[:16]
    ck("A5a_run_entries_by_address",
       word(0x6724A8) == 0x41BDA0 and word(0x67290C) == 0x5F6AA3
       and word(RUN) == 0x422310,
       "0x6724a8->FUN_0041bda0 (pumpA door, zero call/jmp refs); "
       "0x67290c->FUN_005f6aa3 (= FAMILY table +0x4c per NAMED ## M288)")
    ck("A5b_run_extent_digest", n == 490 and rsum == "f2e2c9dfae9ba011",
       "run [0x672290,0x672a34) = %d .text pointers, digest %s "
       "(spans multiple tables; no class identity claimed)" % (n, rsum))

    # A6 switch ENCODING laws from raw bytes + PE bytes (P2: not subtraction)
    HEADS = [
        (0x512B9A, ("cmp", "eax,0x39")), (0x512B9D, ("ja", "0x512c19")),
        (0x512BA1, ("mov", "cl,BYTE PTR [eax+0x5165ec]")),
        (0x512BA7, ("jmp", "DWORD PTR [ecx*4+0x5165cc]")),
        (0x51320C, ("cmp", "eax,0x5c")), (0x51320F, ("ja", "0x51322f")),
        (0x513213, ("mov", "cl,BYTE PTR [eax+0x516638]")),
        (0x513219, ("jmp", "DWORD PTR [ecx*4+0x516628]")),
        (0x516DA2, ("lea", "eax,[ebx-0x51]")), (0x516DA5, ("cmp", "eax,0xc")),
        (0x516DA8, ("ja", "0x517110")),
        (0x516DAE, ("jmp", "DWORD PTR [eax*4+0x5181d0]")),
    ]
    ck("A6a_switch_heads", all(ins[a] == t for a, t in HEADS),
       "12 head instrs: pumpA two-stage byte-map+jump (keys 0..0x39 / 0..0x5c); "
       "pumpB letter stage lea code-'Q', bound <=0xc")
    def targets(base, cnt):
        o, _ = off(base)
        return list(struct.unpack_from("<%dI" % cnt, blob, o))
    T1 = targets(0x5165CC, 8)
    T2 = targets(0x516628, 4)
    T3 = targets(0x5181D0, 13)
    ck("A6b_cmd_jump_targets", T1 == [0x512BC9, 0x512BDB, 0x512BB7, 0x512BAE,
        0x512BC0, 0x512BD2, 0x512BE4, 0x512C19],
       "pumpA cmd jump = 8 targets from byte map, default 0x512c19")
    ck("A6c_vk_jump_targets", T2 == [0x513220, 0x51330D, 0x51331C, 0x51322F],
       "pumpA VK jump = 4 targets, default 0x51322f (codes incl. RETURN 0x0d,"
       " ESC 0x1b, PgUp 0x21, PgDn 0x22, LEFT 0x25, RIGHT 0x27)")
    ck("A6d_letter_jump_targets", T3 == [0x516DB5, 0x516DEC, 0x516E23, 0x516E3B,
        0x516E2F, 0x516E47, 0x516E53, 0x516E5F, 0x516E6B, 0x516E79, 0x516EDB,
        0x516EE7, 0x516F6B],
       "pumpB letter = 13 slots ('Q'+i, i<=0xc), default 0x517110")
    # layout law: each 4-byte jump table is IMMEDIATELY followed by its byte
    # lookup map, sized >= the cmp-bounded key range (bounds read from ins,
    # sizes from PE bytes - nothing here is a hand-claimed constant)
    b_cmd = int(ins[0x512B9A][1].split(",")[1], 16)      # cmp eax,0x39
    b_vk = int(ins[0x51320C][1].split(",")[1], 16)       # cmp eax,0x5c
    b_let = int(ins[0x516DA5][1].split(",")[1], 16)      # cmp eax,0xc
    ck("A6e_table_map_layout",
       0x5165CC + 4 * len(T1) == 0x5165EC and 0x5165EC + b_cmd + 1 <= 0x516628
       and 0x516628 + 4 * len(T2) == 0x516638 and 0x516638 + b_vk + 1 <= 0x516698
       and b_let + 1 == len(T3),
       "cmd: 8-jump then 58-key byte map fits [0x5165ec,0x516628); VK: 4-jump"
       " then 93-key map fits [0x516638,0x516698); letter: bound+1 == 13 slots")

    # A7 (P2-fixed) pumpB entry registration: NUMERIC compare; push-opcode in
    # its own evaluated gate (the old one sat after a trailing '#').
    def direct_target(o):
        t = o.split(",")[0].strip().lower()
        return int(t, 16) if re.fullmatch(r"0x[0-9a-f]+", t) else None
    ref = sum(1 for a, (b, o) in ins.items()
              if b in ("call", "jmp") and direct_target(o) == 0x5186B0)
    hits = []
    for _nm, sv, _vsz, rsz, rp in psecs:
        if not rsz:
            continue
        data = blob[rp:rp + rsz]
        pos = data.find(struct.pack("<I", 0x5186B0))
        while pos != -1:
            hits.append(sv + pos)
            pos = data.find(struct.pack("<I", 0x5186B0), pos + 4)
    ck("A7a_pumpB_entry_refcount", ref == 0 and hits == [0x51892E],
       "call/jmp refs=%d (numeric); stored u32 file-wide=%s (imm32 of the"
       " push at 0x51892d)" % (ref, [hex(h) for h in hits]))
    ck("A7b_push_site_verified", ins[0x51892D] == ("push", "0x5186b0")
       and owner(0x51892D) == "FUN_00518820"
       and sorted({owner(x) for x in calls_to(0x518820)}) == ["FUN_00580260"],
       "instr@0x51892d == push imm32 (opcode checked); owner FUN_00518820"
       " <- init FUN_00580260")

    detail_digest = hashlib.sha256(
        "".join("%s|%s" % (n, d) for n, o, d in checks).encode()).hexdigest()[:16]
    print("digest", detail_digest)
    nfail = sum(1 for _, o, _ in checks if not o)
    print("== M313: %d/%d ==" % (len(checks) - nfail, len(checks)))
    return 1 if nfail else 0

if __name__ == "__main__":
    sys.exit(main())
