"""sim.units — unit position, the 8-direction step, and the movement-point economy (rung B5).

Everything here is a copy of a committed measurement, with the source named:

  * the delta ring     `evidence/m248_region_values.txt:2-3` — the int tables read out of the
                       running image: 0x67850c/0x678990 centre-first ((0,0) at index 0) and
                       0x6784a0/0x6784c4 the SAME nine offsets ring-first. FUN_00529090 (the
                       solo arrow path, ghidra_out shard_013) adds `(&DAT_006784a0)[dir]` to
                       the unit's x and `(&DAT_006784c4)[dir]` to its y, so the ring-first
                       table is the one the player's arrow key uses.
  * wrap and bounds    FUN_00502c40 (shard_012) wraps x by DAT_0092a378 with `if (x<0) x+=w
                       else if (w<=x) x-=w` and never wraps y; FUN_005ab320 bounds-checks y
                       with `-1 < y < DAT_0092a37c`. The tile record is
                       `(w/2)*y + (x>>1)` at 44 B with the column in the record's low or high
                       22 B by `x&1` (sim/save.py `Save.tile`, M240).
  * the MP scale       `data/alpha.json` #RULES field 0 = 3, the file's own "Movement rate
                       along roads"; FUN_005ac550 ends `return DAT_0092a278 * moves`, i.e. the
                       game's movement points are a loaded scale times a move count.
  * the measured economy  NAMED.md (M27): one step spends 3, the turn budget is 6;
                       FUN_005acc00 admits a move iff `total - spent > 0`.
  * the trace          `evidence/m27_solowrap.log` + `evidence/m27_solowrap2.log`, the game's
                       own SOLOWRAP / EXEC / SETTILE lines.

ASSUMED, and queued as census picks (BUILD_SPINE grading rule 5): the per-tile cost is a
uniform 3 — alpha.txt's #TERRAIN section is the terraform-improvement table, not a movement
cost table, and no per-terrain cost has been decoded; and the move count that makes
FUN_005ac550 return 6 for the recorded units (alpha #CHASSIS lists Infantry Speed = 1, so the
second move is a bonus the decompile has not named).
"""

import re

STEP_MP = 3                 # one lattice step, measured (NAMED.md, M27)
MP_PER_TURN = 6             # one unit's budget for one round, measured (NAMED.md, M27)
MOVES_PER_TURN = MP_PER_TURN // STEP_MP

# 0x6784a0 / 0x6784c4, ring-first (evidence/m248_region_values.txt:3). dir is the value the
# key router hands FUN_00529090; the trace's dir=1 is east, and index 1 is (+2, 0).
DIR_DX = (1, 2, 1, 0, -1, -2, -1, 0)
DIR_DY = (-1, 0, 1, 2, 1, 0, -1, -2)

# the same nine offsets centre-first at 0x67850c/0x678990 (evidence/m248_region_values.txt:2)
RING_CENTRE_FIRST = ((0, 0), (1, -1), (2, 0), (1, 1), (0, 2),
                     (-1, 1), (-2, 0), (-1, -1), (0, -2))

ASSUMED = ("per-tile movement cost is uniform %d (no per-terrain cost table decoded; "
           "alpha #TERRAIN is the terraform table)" % STEP_MP,
           "moves = 2 for the recorded units (FUN_005ac550 returns scale*moves; alpha "
           "#CHASSIS Infantry Speed = 1, the second move's source is unnamed)")


def delta(d):
    return DIR_DX[d], DIR_DY[d]


def ring(d):
    """dir -> the entry of the centre-first table that the ring-first table's dir indexes."""
    return RING_CENTRE_FIRST[d + 1]


def wrap_x(x, width):
    """FUN_00502c40's exact branches: one width added or subtracted, x-only."""
    if x < 0:
        x += width
    elif width <= x:
        x -= width
    return x


def y_in_bounds(y, height):
    return -1 < y < height


def tile_record(x, y, width):
    """(record index, half) for a 44-B tile record packing two 22-B columns (M240)."""
    return (width // 2) * y + (x >> 1), x & 1


def mp_scale(rules_doc):
    """alpha.txt #RULES field 0 — the loaded movement scale FUN_005ac550 multiplies by."""
    return int(str(rules_doc.section("RULES")[0]["fields"][0]).strip())


class Unit(object):
    """The parts of a unit record movement needs: x, y, spent (record +0/+2/+40)."""

    def __init__(self, i, x, y, spent=0, faction=0, utype=0):
        self.i, self.x, self.y = i, x, y
        self.spent, self.faction, self.utype = spent, faction, utype

    @property
    def budget(self):
        return MP_PER_TURN

    def can_act(self):
        """FUN_005acc00: total - spent > 0."""
        return self.budget - self.spent > 0

    def step(self, d, width, height):
        """One arrow press: refuse if no MP, else move exactly one lattice step and pay 3."""
        if not self.can_act():
            return None
        dx, dy = delta(d)
        ny = self.y + dy
        if not y_in_bounds(ny, height):
            return None
        self.x, self.y = wrap_x(self.x + dx, width), ny
        self.spent += STEP_MP
        return self.x, self.y


EVENT_RE = re.compile(
    r"^(SOLOWRAP|EXEC|SETTILE) idx=(-?\d+)(?: dir=(-?\d+) mode=(-?\d+)| x=(-?\d+) y=(-?\d+))$")


def parse_trace(path):
    """The gdb log as events; only the three tagged lines are ever present."""
    out = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = EVENT_RE.match(line.strip())
            if not m:
                continue
            kind, idx, d, mode, x, y = m.groups()
            out.append({"kind": kind, "idx": int(idx),
                        "dir": None if d is None else int(d),
                        "mode": None if mode is None else int(mode),
                        "x": None if x is None else int(x),
                        "y": None if y is None else int(y)})
    return out


def moves(events):
    """Group the events: one dict per SOLOWRAP, with its EXEC mode and its SETTILE stamps.

    A press stamps the moved unit with the sentinel (-2,-2) first, then its real tile; the
    other units of the tile it left are stamped (-3,-3) then re-stamped at their own tile.
    """
    out = []
    for e in events:
        if e["kind"] == "SOLOWRAP":
            out.append({"idx": e["idx"], "dir": e["dir"], "exec": None, "stamps": []})
        elif e["kind"] == "EXEC" and out:
            out[-1]["exec"] = (e["idx"], e["dir"], e["mode"])
        elif e["kind"] == "SETTILE" and out:
            out[-1]["stamps"].append((e["idx"], e["x"], e["y"]))
    for mv in out:
        mv["dest"] = [(i, x, y) for i, x, y in mv["stamps"] if x >= 0 and y >= 0
                      and i == mv["idx"]]
        mv["restamp"] = [(i, x, y) for i, x, y in mv["stamps"] if x >= 0 and y >= 0
                         and i != mv["idx"]]
        mv["sentinel"] = [(i, x, y) for i, x, y in mv["stamps"] if x < 0 or y < 0]
    return out
