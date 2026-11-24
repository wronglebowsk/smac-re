"""sim.feeder - FUN_004f47f0's per-item upkeep charge, EXECUTABLE (BUILD_SPINE rung B28).

The law is M333's, pinned by address in `evidence/m333_feeder_slot_census.txt`; this module
evaluates it and invents nothing.  B27 (`sim.energy`) ran the round but took the feeder's
per-item `v` as an INPUT; here `v` comes out of the loop.

The loop, as read (all addresses are .text, from the M333 census lines cited per pin):

    4f4802  mov esi,0x1            esi = ITEM id, 1-based
    4f4811  cmp esi,0x22 / jg 4f4a34   ids 35..38 SKIP the charge body (NOT the exit)
    4f4823  call 0x507410          mapper -> (byte index, bit mask) for this item
    4f4837  mov al,[base+0x8c+idx] / 4f4841 and al,mask / 4f484c je 4f4a34
                                   charge only when the base HAS the facility
    4f48a6..4f48bc                 the faction's disabled-item list; a hit jumps to
                                   4f492a `xor eax,eax` and re-enters at 4f48d4 (cost 0)
    4f48c8  lea eax,[esi+esi*2] / 4f48cb shl eax,0x4 / 4f48ce mov eax,[eax+0x984d48]
                                   cost = item table row (stride 48) upkeep dword
    4f48d4  mov ecx,ds:0x985ba0    the price-path gate dword (carried in the save header)
    4f48da  test ecx,ecx / 4f48dc jl 4f4938        negative -> FULL PRICE
    4f48e9  mov dl,[304*ecx+0x95da14]              that base's owner byte
    4f48f1  cmp edx,ebx / 4f48f8 je 4f4938         not `own` -> FULL PRICE
    4f4909  mov ecx,[2095*ebx*4+0x94d430]          block[own]+0
    4f4919  shr edi,0x5 / 4f491c and edi,0x1       carry_in = bit5
    4f491f  add eax,edi                            sum = cost + carry_in
    4f4921  test al,0x1 -> 4f4925 or ecx,0x20 / 4f492e and ecx,0xffffffdf
    4f4931  mov [edx],ecx                          carry_out = sum & 1, written back
    4f4933  cdq / 4f4934 sub eax,edx / 4f4936 sar eax,1   v = trunc(sum/2)
    4f4938  ... 4f4950 sub ecx,eax / 4f4952 store  ENERGY -= v
           4f4958 mov edx,[+0x300] / 4f495e add edx,eax / 4f4962 store   +300 += v

The FULL-PRICE path (4f4938) never touches block+0: the carry survives unchanged.
`ebx` is `BYTE[[ds:0x8f0d60]+4]` (M333 G4); its identity with the charged base's owner is
INFERRED, not measured - the sim therefore keys the carry on the faction it is charging and
says so.  The removal branch at 4f4970 (energy went negative) is M333's OPEN lead (pick (x7))
and is NOT modelled here.
"""
import struct

# --- table geometry (M333 G7: the upkeep dword sits at row+0x10) -------------------------
ITEM_ROW0 = 0x984D38
ITEM_UPKEEP = 0x984D48
ROW = 48
UPKEEP_DWORD_OFF = ITEM_UPKEEP - ITEM_ROW0          # 0x10, MEASURED by M333, asserted by G2

# --- the loop bounds: parsed from the census by G2, never retyped as literals here --------
VISIT_LO_DEFAULT = 1

# --- the block / gate addresses -----------------------------------------------------------
BLK_STRIDE = 8380            # M324: 8 faction blocks of 0x20bc at runtime 0x94d430
BLK0 = 0                     # block+0 carries bit5
BIT5 = 5
OFF_ENERGY = 0x220           # M325
OFF_SPEND = 0x300            # M330: the feeder's own accumulator
G_SEL = 0x985BA0             # the price-path gate dword (M333 G6: no writer in .text)
BASE_STRIDE = 304            # M333 G3: the 304-B base record
BASE_OWNER_BYTE = 0x4
BASE_FAC_BYTES = 0x8C        # completed-facility bitmap; byte item>>3, bit 1<<(item&7)

# --- leg pins: (label, address-as-printed, FIELD TOKEN, committed evidence file) ----------
# G1 requires ONE evidence line to carry BOTH the address and the token claimed for it.
LEG_PINS = (
    ("loop-init", "4f4802", "mov esi,0x1", "evidence/m333_feeder_slot_census.txt"),
    ("charge-bound", "4f4811", "cmp esi,0x22", "evidence/m333_feeder_slot_census.txt"),
    ("skip-to-bottom", "4f4814", "jg 0x4f4a34", "evidence/m333_feeder_slot_census.txt"),
    ("counter-inc", "4f4a34", "inc esi", "evidence/m333_feeder_slot_census.txt"),
    ("range-bound", "4f4a35", "cmp esi,0x27", "evidence/m333_feeder_slot_census.txt"),
    ("back-edge", "4f4a3b", "jl 0x4f480b", "evidence/m333_feeder_slot_census.txt"),
    ("table-read", "4f48ce", "0x984d48", "evidence/m333_feeder_slot_census.txt"),
    ("fold-lea", "4f48c8", "lea eax,[esi+esi*2]", "evidence/m333_feeder_slot_census.txt"),
    ("fold-shl", "4f48cb", "shl eax,0x4", "evidence/m333_feeder_slot_census.txt"),
    ("bitmap-read", "4f4837", "0x95da9c", "evidence/m333_feeder_slot_census.txt"),
    ("not-having-skip", "4f484c", "je 0x4f4a34", "evidence/m333_feeder_slot_census.txt"),
    ("disabled-cmp", "4f48bc", "cmp DWORD PTR [eax],esi",
     "evidence/m333_feeder_slot_census.txt"),
    ("sel-load", "4f48d4", "0x985ba0", "evidence/m333_feeder_slot_census.txt"),
    ("sign-skip", "4f48dc", "jl 0x4f4938", "evidence/m333_feeder_slot_census.txt"),
    ("owner-byte", "4f48e9", "0x95da14", "evidence/m333_feeder_slot_census.txt"),
    ("owner-cmp", "4f48f1", "cmp edx,ebx", "evidence/m333_feeder_slot_census.txt"),
    ("owner-skip", "4f48f8", "je 0x4f4938", "evidence/m333_feeder_slot_census.txt"),
    ("bit5-read", "4f4919", "shr edi,0x5", "evidence/m333_feeder_slot_census.txt"),
    ("bit5-mask", "4f491c", "and edi,0x1", "evidence/m333_feeder_slot_census.txt"),
    ("carry-add", "4f491f", "add eax,edi", "evidence/m333_feeder_slot_census.txt"),
    ("parity-test", "4f4921", "test al,0x1", "evidence/m333_feeder_slot_census.txt"),
    ("bit5-set", "4f4925", "or ecx,0x20", "evidence/m333_feeder_slot_census.txt"),
    ("bit5-clear", "4f492e", "and ecx,0xffffffdf", "evidence/m333_feeder_slot_census.txt"),
    ("bit5-store", "4f4931", "mov DWORD PTR [edx],ecx",
     "evidence/m333_feeder_slot_census.txt"),
    ("quotient", "4f4936", "sar eax,1", "evidence/m333_feeder_slot_census.txt"),
    ("energy-sub", "4f4950", "ENERGY-=v", "evidence/m330_block300_census.txt"),
    ("energy-store", "4f4952", "DISP94D650", "evidence/m325_block220_census.txt"),
    ("spend-add", "4f495e", "+300+=v", "evidence/m330_block300_census.txt"),
    ("spend-store", "4f4962", "0x94d730", "evidence/m330_block300_census.txt"),
    # the deliberately-bogus CONTROL pin ships inside the same list so it is measured in the
    # same pass: it must hit NOTHING (an evidence grep that cannot fail greps nothing).
    ("CONTROL-bogus", "4f49ff", "zzz-not-a-real-token-zzz",
     "evidence/m333_feeder_slot_census.txt"),
)


def trunc_div2(x):
    """4f4933-4f4936: `cdq` / `sub eax,edx` / `sar eax,1` - signed divide by 2 truncating
    TOWARD ZERO (a plain `sar` floors; the two differ on every negative odd value)."""
    return (x - (-1 if x < 0 else 0)) >> 1        # cdq, then sub, then sar (Python >> floors)


def bit5(v):
    """4f4919-4f491c: the carried half-unit out of block+0."""
    return (v >> BIT5) & 1


def set_bit5(v, b):
    """4f4925 / 4f492e: write the parity back into the SAME bit, leave the rest alone."""
    return (v | (1 << BIT5)) if b else (v & ~(1 << BIT5))


def fac_bit(bitmap_bytes, item):
    """4f4823's mapper output applied to the base record: byte item>>3, bit 1<<(item&7)."""
    by, bi = item >> 3, item & 7
    return (bitmap_bytes[by] >> bi) & 1 if 0 <= by < len(bitmap_bytes) else 0


def price_path(sel, owner_bytes, own):
    """4f48d4-4f48f8: halve only when the gate dword is non-negative AND the base it selects
    is owned by `own`.  Two distinct skips, both to the FULL-PRICE path."""
    if sel < 0:
        return False, "sign"
    if owner_bytes[sel] != own:
        return False, "owner"
    return True, ""


def charge_item(cost, carry, halve):
    """One item's charge.  Returns (v, carry_out).

    The full-price path (4f4938) never reads or writes block+0: carry_out == carry_in.
    """
    if not halve:
        return cost, carry
    s = cost + carry                      # 4f491f
    return trunc_div2(s), s & 1           # 4f4936 / 4f4921->4f4931


def charge_base(table, bitmap_bytes, carry, halve, disabled, visit_lo, charge_hi, visit_hi):
    """FUN_004f47f0's loop for ONE base.  Returns (total, carry_out, charged_ids).

    The three bounds are PARAMETERS, never literals: G2 parses them out of the census and every
    caller passes the parsed values, so a drift between this file and the evidence cannot hide.

    VISITS ids visit_lo..visit_hi; ids above charge_hi skip the charge body at the TOP test
    (4f4811/4f4814) and are never charged; an id the base does not have skips at 4f484c.
    A disabled id re-enters the price-path gate with cost 0 (4f492a -> 4f48d4), so it still
    passes through the carry read/write - with cost 0 that cannot change the bit, and the
    loop models it that way rather than skipping the body.
    """
    total, charged = 0, []
    for item in range(visit_lo, visit_hi + 1):
        if item > charge_hi:                       # 4f4811 / 4f4814
            continue
        if not fac_bit(bitmap_bytes, item):        # 4f4837 / 4f484c
            continue
        cost = 0 if item in disabled else table[item]
        v, carry = charge_item(cost, carry, halve)
        total += v
        charged.append((item, cost, v))
    return total, carry, charged


def read_sel(data, mem2file):
    """The gate dword read out of the CONTAINER (it lives in the carried state header)."""
    off = mem2file(G_SEL)
    return struct.unpack_from("<i", data, off)[0], off


def read_bit5_octet(data, block_a_off):
    """bit5 of block+0 for the eight faction blocks, read out of a container."""
    return [bit5(struct.unpack_from("<I", data, block_a_off + BLK_STRIDE * f)[0])
            for f in range(8)]


def read_block0_octet(data, block_a_off):
    return [struct.unpack_from("<I", data, block_a_off + BLK_STRIDE * f)[0]
            for f in range(8)]
