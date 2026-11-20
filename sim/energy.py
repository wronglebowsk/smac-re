"""sim.energy - ONE round's faction ENERGY flow as an executable law (BUILD_SPINE rung B27).

Every leg is a RECORDED one, pinned by address in chain 2's censuses (M325 / M326 / M328 / M330);
this module evaluates those laws and nothing else - it invents no leg and settles no noun.
`sim/composedenergy.py` runs it over a container's own eight faction blocks.

The pinned order inside FUN_00520540 (the upkeep vector) is
    entry-zero 52056d  <  debt settle (called 520605, body 520b0e-520b22)
                     <  SNAPSHOT 52065d  <  refund adds 520743/520770  <  residue 52078f
                     <  ledger stores (reader 52082c)
and the feeder FUN_004f47f0 (ROUND>1 only) debits ENERGY at 4f4950-52 while accumulating into
+300 at 4f495e-62.  The income add 4f5c8c (B4's SUM base+0xfc) and the feeder are COMMUTATIVE
adds on every fixture this rung runs; their relative order is NOT pinned and is declared.
"""
import struct

# --- the faction block, as M324 pinned it: 8 blocks of 0x20bc at runtime 0x94d430 ---------
BLKBASE = 0x94d430
BLK_STRIDE = 8380            # 0x20bc (M324 G3: fread 596a91, sz 0x105e0 = 8 * 0x20bc)
NFACTION = 8

# block-relative offsets of the fields the round touches
OFF_ENERGY = 0x220           # M325: faction ENERGY
OFF_DEBT = 0x224             # M326: deferred HURRY payment (settled at upkeep)
OFF_F2FC = 0x2FC             # M330: ledger input, noun OPEN
OFF_SPEND = 0x300            # M330: upkeep spend accumulator
OFF_F308 = 0x308             # M330: ledger input, noun OPEN
OFF_F30C = 0x30C             # M330: ledger store  = +308 - +300 + +2fc
OFF_F310 = 0x310             # M330: ledger store  = +2fc
OFF_F3F8 = 0x3F8             # M330: entry-zeroed, noun OPEN

ENTRY_ZERO = (OFF_F2FC, OFF_SPEND, OFF_F308, OFF_F3F8)
# What this rung's writer MODELS: the three the round mutates plus the two ledger stores.
# +2fc / +308 / +3f8 are entry-zeroed by the game but their mid-round writer is UNMODELED
# (M330 lists them OPEN), so the rung leaves them pass-through and MEASURES that.
MODELED_FIELDS = (OFF_ENERGY, OFF_DEBT, OFF_SPEND, OFF_F30C, OFF_F310)
PASSTHROUGH_FIELDS = (OFF_F2FC, OFF_F308, OFF_F3F8)
ALL_FIELDS = MODELED_FIELDS + PASSTHROUGH_FIELDS

# Difficulty dword (M308/M330: ds:0x985aec, noun INFERRED) - inside the carried state header.
G_DIFF = 0x985AEC

# leg pins: (label, address-or-operand literal, committed evidence file). G1 greps each one.
LEG_PINS = (
    ("entry-zero", "52056d", "evidence/m330_block300_census.txt"),
    ("feeder-E-sub", "4f4950", "evidence/m330_block300_census.txt"),
    ("feeder-load", "4f4958", "evidence/m330_block300_census.txt"),
    ("feeder-acc", "4f495e", "evidence/m330_block300_census.txt"),
    ("feeder-store", "4f4962", "evidence/m330_block300_census.txt"),
    ("upkeep-charge", "4f4952", "evidence/m326_block224_census.txt"),
    ("income-add", "4f5c8c", "evidence/m325_block220_census.txt"),
    ("settle-call", "520605", "evidence/m328_hurry_globals.txt"),
    ("settle-body", "520b0e", "evidence/m326_block224_census.txt"),
    ("settle-zero", "520b22", "evidence/m326_block224_census.txt"),
    ("energy-field", "0x94d650", "evidence/m325_block220_census.txt"),
    ("debt-field", "0x94d654", "evidence/m326_block224_census.txt"),
    ("spend-field", "0x94d730", "evidence/m330_block300_census.txt"),
    ("snapshot", "52065d", "evidence/m328_hurry_globals.txt"),
    ("refund-load", "52071e", "evidence/m330_block300_census.txt"),
    ("refund-add", "520743", "evidence/m328_hurry_globals.txt"),
    ("refund-add2", "520749", "evidence/m330_block300_census.txt"),
    ("refund-magic", "55555556", "evidence/m330_block300_census.txt"),
    ("refund-residue", "52078f", "evidence/m330_block300_census.txt"),
    ("refund-diff", "0x985aec", "evidence/m330_block300_census.txt"),
    ("refund-mask", "0x985b10", "evidence/m330_block300_census.txt"),
    ("ledger-read", "52082c", "evidence/m330_block300_census.txt"),
    ("block-base", "0x94d430", "evidence/m328_hurry_globals.txt"),
)

# The pinned branch tuples of the refund switch, transcribed from
# evidence/m330_block300_census.txt G5 (the "G5 switch:" line). G6 parses that line and
# asserts these tuples appear in it IN ORDER, then derives the thresholds from the parsed
# operands instead of typing them a second time.
REFUND_SWITCH = (
    ("mov", "eax,ds:0x985aec"),
    ("cmp", "eax,0x3"),
    ("jle", "0x520795"),
    ("cmp", "eax,0x4"),
    ("jne", "0x520758"),
    ("cmp", "ecx,ebx"),
    ("je", "0x520795"),
)


def field_file_off(block_a_off, field, faction, stride=BLK_STRIDE):
    """Where one faction block's field lives in the container (M324: block A IS the array)."""
    return block_a_off + field + stride * faction


def read_blocks(data, block_a_off):
    """The eight faction blocks' economy fields, straight out of the container."""
    out = []
    for f in range(NFACTION):
        blk: dict = {"faction": f, "base_off": block_a_off + BLK_STRIDE * f}
        for off in ALL_FIELDS:
            blk[off] = struct.unpack_from("<i", data, field_file_off(block_a_off, off, f))[0]
        out.append(blk)
    return out


def read_energy_octet(data, block_a_off):
    return [struct.unpack_from("<I", data, field_file_off(block_a_off, OFF_ENERGY, f))[0]
            for f in range(NFACTION)]


def read_spend_octet(data, block_a_off):
    return [struct.unpack_from("<I", data, field_file_off(block_a_off, OFF_SPEND, f))[0]
            for f in range(NFACTION)]


def read_debt_octet(data, block_a_off):
    return [struct.unpack_from("<I", data, field_file_off(block_a_off, OFF_DEBT, f))[0]
            for f in range(NFACTION)]


def read_difficulty(data, mem2file):
    """The ds:0x985aec dword, carried inside the state header (M324: hdr RW -> 0x985ab8, 0x31c B)."""
    return struct.unpack_from("<I", data, mem2file(G_DIFF))[0]


# --- the laws ---------------------------------------------------------------------------
def k_of(difficulty, skip_max=3, k1=4):
    """The refund multiplier table, from the pinned branch thresholds (cmp 0x3/jle, cmp 0x4/jne)."""
    if difficulty <= skip_max:
        return 0
    return 1 if difficulty == k1 else 2


def trunc_div3(n):
    """The game's own trunc-toward-zero /3 (magic 0x55555556 + sign fix, M330 G4)."""
    return -((-n) // 3) if n < 0 else n // 3


def refund(spend, difficulty, skip_max=3, k1=4):
    """520714-52078f: r = trunc(k*spend/3), ENERGY += r, spend -= r (RESIDUE KEPT, M330 G4).
    The mask gate (bit in ds:0x985b10) is VACUOUS - cl=8 -> dl=0 - so it never blocks."""
    if spend == 0:
        return 0, spend
    k = k_of(difficulty, skip_max, k1)
    if k == 0:
        return 0, spend
    r = trunc_div3(k * spend)
    return r, spend - r


def settle(energy, debt, clamp=True):
    """520b0e-520b22: ENERGY -= debt, debt := 0, floor 0 (M326 G4)."""
    e = energy - debt
    if clamp and e < 0:
        e = 0
    return e, 0


def ledger(f2fc, f308, spend):
    """52081a-841 as pinned by M330 G7-9: +310 = +2fc ; +30c = +308 - +300 + +2fc."""
    return {OFF_F310: f2fc, OFF_F30C: f308 - spend + f2fc}


def round_legs(blk, gross, feed, difficulty, rnd, b8, clamp=True):
    """One faction's round, in the pinned order. `feed` is the feeder's charge for the round
    (FUN_004f47f0, ROUND>1 only); `gross` is B4's income add; `b8` is the block's +8 dword,
    which gates the feeder's floor-0.  Returns the leg table and the field writes."""
    out: dict = {"faction": blk.get("faction", -1), "legs": []}
    e = blk[OFF_ENERGY]
    spend = 0                                   # entry-zero 52056d zeroes +300
    out["legs"].append(("entry-zero", 0, e, 0, blk[OFF_DEBT]))
    if rnd > 1:                                 # the feeder runs only past round 1
        e1 = e - feed
        if e1 < 0 and b8 <= 1 and clamp:
            e1 = 0
        spend += feed
        e = e1
    out["legs"].append(("feeder", feed, e, spend, blk[OFF_DEBT]))
    e += gross
    out["legs"].append(("income", gross, e, spend, blk[OFF_DEBT]))
    e, debt = settle(e, blk[OFF_DEBT], clamp=clamp)
    out["legs"].append(("settle", blk[OFF_DEBT], e, spend, debt))
    snap = e                                    # SNAPSHOT 52065d reads the post-settle pool
    out["legs"].append(("snapshot", snap, e, spend, debt))
    r, resid = refund(spend, difficulty)
    e += r
    spend = resid
    out["legs"].append(("refund", r, e, spend, debt))
    led = ledger(blk[OFF_F2FC], blk[OFF_F308], spend)
    out["legs"].append(("ledger", led[OFF_F30C], e, spend, debt))
    out["energy_next"] = e
    out["refund_amount"] = r
    out["snapshot"] = snap
    out["spend_next"] = spend
    out["debt_next"] = debt
    out["writes"] = {OFF_ENERGY: e, OFF_DEBT: debt, OFF_SPEND: spend, **led}
    return out
