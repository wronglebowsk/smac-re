"""sim.economy - the per-round faction economy: gross, upkeep, net (BUILD_SPINE rung B4).

The model is the recorded pipeline, not an invention (docs/named-archive-m32-m84e.md M46/M47):

  gross  = SUM over the faction's bases of base+0xfc
           (aggregator 0x445900 writes the HUD "Gross Income" row 0x745734 with exactly this sum;
            the income store 0x4f5c8c adds the same field to the faction's energy pool)
  upkeep = SUM over the faction's completed facilities of item_upkeep(item, faction)
           (0x4f4760: 0 when the item is on the faction's disabled list, else the item table
            0x984d48 + item*0x30 int0; charged straight out of energy at 0x4f4952, and summed
            into the HUD "Total Costs" row 0x744f28 with per-base detail at 0x744f2c[base])
  net    = gross - upkeep        (HUD "NET INCOME" row 0x7457dc; gifts are 0 on an idle round)
  energy_next = max(0, energy + net - ledger)
           (0x5208f0 tail: `energy -= faction+4; faction+4 = 0; clamp >= 0`; the ledger is 0 on a
            round with no research/gift/terraform action, which is what an idle replay is)

Item upkeep comes from data/alpha.json `#FACILITIES` column 3 - the same table the exe loads
(alpha.txt:590 `#FACILITIES`, field order name, cost, upkeep, tech, tech2, effect).  Runtime item
id = alpha line index + 1 (m32-m84e.md:270).  Rung B4 verifies that mapping where a recorded live
read pins it and prints where it does not hold.
"""
from .base import ITEM_COUNT

FACILITIES = "FACILITIES"
UPKEEP_COL = 2               # alpha.txt #FACILITIES: name, cost, UPKEEP, tech, tech2, effect
ALPHA_SHIFT = 1              # runtime item id = alpha line index + 1 (m32-m84e.md:270)


def upkeep_table(rules, shift=ALPHA_SHIFT):
    """runtime item id -> per-round energy upkeep, read out of the alpha rules tables."""
    rows = rules.section(FACILITIES)
    table = [0] * ITEM_COUNT
    for item in range(ITEM_COUNT):
        line = item - shift
        if 0 <= line < len(rows):
            table[item] = int(rows[line]["fields"][UPKEEP_COL])
    return table


def item_name(rules, item, shift=ALPHA_SHIFT):
    """The facility name a runtime item id maps to under the same indexing."""
    line = item - shift
    rows = rules.section(FACILITIES)
    return rows[line]["fields"][0] if 0 <= line < len(rows) else None


def item_upkeep(table, item, disabled=()):
    """0x4f4760: the disabled list wins over the table (m32-m84e.md:272)."""
    return 0 if item in disabled else table[item]


def base_upkeep(rec, table, disabled=()):
    """0x4f47f0: one base's per-round upkeep = sum over its completed facilities."""
    return sum(item_upkeep(table, i, disabled) for i in rec.get("facilities", ()))


def faction_round(faction, bases, table, disabled=()):
    """One idle round for one faction: the HUD triple plus the two detail arrays the
    aggregator writes (0x744f2c[base] per-base upkeep, 0x745738[39] item counts).

    `bases` is a list of decoded records (sim.base) or of trace-normalised dicts carrying
    "owner", "gross" and, for the faction's own bases, "facilities"."""
    ours = [b for b in bases if b["owner"] == faction]
    gross = sum(b["gross"] for b in ours)
    per_base = [base_upkeep(b, table, disabled) if b["owner"] == faction else 0
                for b in bases]
    counts = [0] * ITEM_COUNT
    for b in ours:
        for i in b.get("facilities", ()):
            counts[i] += 1
    upkeep = sum(per_base)
    return {"faction": faction, "n_bases": len(ours), "gross": gross, "upkeep": upkeep,
            "net": gross - upkeep, "per_base_upkeep": per_base, "item_counts": counts}


def apply_round(energy, net, ledger=0):
    """0x5208f0's tail: income lands, the round's ledger is debited and zeroed, floor 0."""
    return max(0, energy + net - ledger)


def base_from_trace(rec):
    """Adapt one base the live harness recorded (scripts/m46_econ.py's field names) to this
    module's names, decoding the record's own 76-dword dump for the facility bitmap."""
    from .base import decode_dwords
    full = rec.get("full")
    d = decode_dwords(full) if full else {"facilities": ()}
    d.update({"i": rec["idx"], "owner": rec["owner"], "gross": rec["prod_fc"]})
    return d
