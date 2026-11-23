#!/usr/bin/env python3
"""M334 (chain2): the upkeep-FAILURE branch of FUN_004f47f0 — what is removed, what ENERGY
becomes, what is announced. Pick (x7) of NEXT_PROMPT's OPEN-LEADS (the row printed, not gated,
by `## M333`). STATIC, zero box, zero /proc, zero gdb. Reuses M326's reviewed .text cache.

SKELETON — constants + the claim set; gates filled in the same fire.

THE OLD CLAIM being tested (docs/named-archive-m32-m84e.md:268, conf H "pseudocode"):
  "insufficient funds => auto-SELL a facility (bitmap bit cleared,
   refund = 0x4e40a0 x refund table 0x984d44[item*0xc], POWERSHORT warning)"

WHAT THE BYTES SAY (to be gated, not asserted here):
  FUN_004f47f0 charges item upkeep per base (M330/M333): ENERGY -= cost @0x4f4952, +300 += cost
  @0x4f4962. Then it re-reads ENERGY and tests it against 0 (@0x4f4968-70, jge -> next item).
  The negative side is a THREE-WAY dispatch:
    A @0x4f4976  cmp [block+0x8],1 / jg  -> ENERGY := 0 @0x4f497f
    B @0x4f498a  cmp [base_rec+0x50], -item / jne -> ENERGY := 0 @0x4f4999
    C @0x4f49a4  the removal path: clear the item's bit in the CURRENT base's facility map
                 (304*ds:0x68cbb0 + byte_index + 0x95da9c), then
                 ENERGY := FUN_004e40a0(owner,1,-1) * row[item]+12 @0x4f4a0b,
                 FUN_006265a2(1, row[item]+0, -1, -1) @0x4f4a11,
                 FUN_0048f100("POWERSHORT",0x10000,0xe,"genwarning_sm.pcx",0) @0x4f4a29.
  The store at 0x4f4a0b is a MOV of a product with NO read of ENERGY on the path — the old
  row's word "refund" (an addition) is refuted; the multiplication is confirmed.

Acceptance: python3 -u scripts/m334_powershort_census.py -> TABLE FIRST, then gates, digest;
a re-run must be byte-identical.  Mutants: scripts/m334_mutate.py (--selftest runs them).
Patch env: M334_PATCH="addr|mnemonic ops" applied to m326.INS after import (the instrument
prints `patches applied: n/m` as contact proof).
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import m326_block224_census as m326  # noqa: E402

INS, ADDRS, AIDX = m326.INS, m326.ADDRS, m326.AIDX
owner, split_ops, memref = m326.owner, m326.split_ops, m326.memref
pe_cstr = m326.pe_cstr

FN = 0x4F47F0                    # FUN_004f47f0(cur_base) facility-upkeep charge loop
LOOP_BOTTOM, LOOP_END = 0x4F4A34, 0x4F4A3C
NEG_TEST = 0x4F4970              # jge LOOP_BOTTOM when ENERGY >= 0
CLAMP_A, CLAMP_B, REMOVAL = 0x4F4976, 0x4F498A, 0x4F49A4
E_STORE = (0x4F497F, 0x4F4999, 0x4F4A0B)   # the three stores to block+0x220
MAPPER, SELLER, SLOTTER, MEMO = 0x507410, 0x4E40A0, 0x6265A2, 0x48F100
ITEM_ROW0, ROW = 0x984D38, 48    # item table row 0; +12 = 0x984d44, +16 = upkeep 0x984d48
BLKBASE, BLKSTRIDE = 0x94D430, 0x20BC
ENERGY_OFF, SPEND_OFF = 0x220, 0x300
BASEMAP, BASE_STRIDE = 0x95DA9C, 304
CURR_BASE, CURR_REC = 0x68CBB0, 0x8F0D60
STR_LABEL, STR_ICON = 0x68D24C, 0x68D238
EV = os.environ.get("M334_EVIDENCE_ROOT", ROOT)

_npatch = 0


def apply_patch():
    """M334_PATCH='addr|mn ops;addr|mn ops' — the mutation harness's contact surface."""
    global _npatch
    spec = os.environ.get("M334_PATCH", "")
    if not spec:
        return 0, 0
    n = 0
    for item in spec.split(";"):
        if not item.strip():
            continue
        a, _, rest = item.partition("|")
        addr = int(a, 16)
        mn, _, ops = rest.strip().partition(" ")
        if addr in INS:
            INS[addr] = (mn, ops)
            n += 1
    _npatch = n
    return n, len([x for x in spec.split(";") if x.strip()])


def main():
    raise SystemExit("skeleton — gates not implemented yet")


if __name__ == "__main__":
    main()
