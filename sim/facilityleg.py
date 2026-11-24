"""sim.facilityleg - rung B33's RUN and its GATES (BUILD_SPINE §B33).

B32 scored the completion law per leg on the game's own recorded run: 4/4 unit heads gain
exactly the mapper bit, 0/2 facility-range heads do - and DECLARED the divergence unmodeled
("the facility path's own branch to the shared OR is not walked here").  This rung walks it.

The stamp lives at `or BYTE PTR [eax],cl` @0x4f0ec0 inside FUN_004ef6d0, the function that
already decodes the queue head at 0x4ef88b (`head < 0` = negated unit type, `>= 0` = facility
item, `-38` sentinel).  The rung reads a committed census of that whole function (every
instruction's mnemonic, every branch with target and fall-through, every [ebp-..] memory ref
with its read/write direction - `scripts/b33_extract.py` derives it from the .text dump),
builds the CFG at instruction granularity, and asks the GRAPH which leg reaches the stamp:

  * reachability from the function entry, from the unit branch (0x4ef8a4) and from the
    facility branch (0x4efa2c);
  * the stamp block's entry edges and the branch that guards them;
  * the single write site of the gate local [ebp-0x30] - the census decides whether the
    "shared" OR is shared;
  * each leg's SPEND site, which the census must show as two different addresses.

The walk is then SCORED on the recorded six boundaries (B31/B32's trace): unit head -> stamp
at the mapper byte, facility head -> no stamp; the Virgin Soil row is the anchor.  Rivals
(the shared OR; an off-map mapper refusal; the after-pop head) are scored on the same printed
numbers and must fail.

`build()` returns the measured model, `gates(model)` the conditions over it (scripts/b33_mutate.py
mutates that model), `report(model)` the tables.  Nothing is asserted before it is printed.

DECLARED UNMODELED: whether a facility completion stamps +0x8c ANYWHERE (M342's other OR
sites 0x4e4528 / 0x4f3ebc / 0x4f3f4c are outside this function and are not followed here);
the meaning of the 52-byte 0x98adb8 + 0x34*i row; which recorded loss is a raze/sale.

Zero box, zero /proc, zero gdb, no game-binary load.
"""
import hashlib
import os
import sys

from . import facoracle as fa
from . import unitoracle as un

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENSUS = os.path.join(ROOT, "evidence", "fixtures", "b33_fun4ef6d0_census.txt")
KEYS = os.path.join(ROOT, "evidence", "fixtures", "b33_key_sites.txt")

LO = 0x4ef6d0            # FUN_004ef6d0 entry (ghidra_out/index.csv)
SIZE = 12298             # its size in bytes, same row
HI = LO + SIZE
ENTRY = LO
UNIT_IN = 0x4ef8a4       # `mov [ebp-0x30],ecx` - the negated head, unit branch
FAC_IN = 0x4efa2c        # `mov ebx,[eax+0x50]` - the head >= 0 branch
STAMP = 0x4f0e90         # first instruction of the block that ORs the mapper byte
OR_SITE = 0x4f0ec0       # `or BYTE PTR [eax],cl`
GATE = 0x4f0b80          # `jg` on [ebp-0x30] > 0 - the block's only entry
BLOCK = 0x4f0ca1         # the spend+stamp block (unit leg only)
SPEND_FAC = (0x4efed8, 0x4efedb, 0x4efedd)   # load [ecx+0x40] / sub esi,edi / store back
SPEND_UNIT = (0x4f0ca1, 0x4f0ca4, 0x4f0ca6)  # load [edx+0x40] / sub esi,edi / store back
GATE_LOCAL = "[ebp-0x30]"
FB = 8                   # eight-byte bitmap window (B30's +0x8c..+0x8f is four; B32 pinned 8)
FBASE = 0x8c

JCC = {"je", "jne", "jl", "jle", "jg", "jge", "jb", "jbe", "ja", "jae",
       "js", "jns", "jo", "jno", "jp", "jnp", "jz", "jnz"}

# Pinned on the first real run (s330); a dump, decode or arithmetic drift reddens G12.
CENSUS_ANCHOR = "f8442b847c68016d"
CFG_ANCHOR = "e1304fc33c09e349"
REACH_ANCHOR = "cead75d5e443057d"
SCORE_ANCHOR = "6000c87277dcb198"
VS_ANCHOR = "462f20b2da918c6b"


def _sha(rows):
    h = hashlib.sha256()
    for r in rows:
        h.update(repr(r).encode("utf-8"))
    return h.hexdigest()[:16]


# --- the census, the CFG, the reachability ------------------------------------------------
def load_census(path=CENSUS):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            p = line.split()
            rows.append((int(p[0], 16), p[1], p[2] if len(p) > 2 else "-"))
    return rows


def load_keys(path=KEYS):
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            a, body = line.split(None, 1)
            out[int(a, 16)] = body.strip()
    return out


def _direct(op):
    if op.startswith("0x") and all(c in "0123456789abcdef" for c in op[2:]):
        return int(op, 16)
    return None


class CFG:
    """Instruction-granularity CFG: jcc = taken + fall-through, jmp = taken, ret = wall,
    call returns to the next instruction.  Targets outside the span are counted, not hidden."""

    def __init__(self, rows):
        self.addr = [a for a, _m, _o in rows]
        self.ins = {a: (m, o) for a, m, o in rows}
        self.edges = {}
        self.external = 0
        self.indirect = 0
        for i, a in enumerate(self.addr):
            m, o = self.ins[a]
            nxt = self.addr[i + 1] if i + 1 < len(self.addr) else None
            if m == "ret":
                s = []
            elif m == "jmp" or m in JCC:
                t = _direct(o)
                if t is None:
                    self.indirect += 1
                    s = [nxt] if (m in JCC and nxt is not None) else []
                elif t not in self.ins:
                    self.external += 1
                    s = []
                else:
                    s = [t] + ([nxt] if (m in JCC and nxt is not None) else [])
            else:
                s = [nxt] if nxt is not None else []
            self.edges[a] = s
        self.preds = {a: set() for a in self.addr}
        for a, ss in self.edges.items():
            for s in ss:
                self.preds[s].add(a)

    def reach(self, entry):
        seen, todo = set(), [entry]
        while todo:
            a = todo.pop()
            if a in seen or a not in self.ins:
                continue
            seen.add(a)
            todo.extend(self.edges[a])
        return seen


def writes(census, ref=GATE_LOCAL):
    return [a for a, _m, o in census if o == "w" + ref]


# --- the recorded rows -------------------------------------------------------------------
def rows_of(samples=None):
    samples = fa.load_trace() if samples is None else samples
    rows = []
    for r in fa.deltas(samples):
        si, idx, name = r[0], r[3], r[4] or ""
        key = (idx, name)
        before = un._record(samples, si - 1, key)
        after = un._record(samples, si, key)
        if before is None or after is None:
            continue
        head = fa.head_of(before)
        kind, item, by, bit = un.head_bit(head)
        rows.append(dict(si=si, idx=idx, name=name, head=head, head_after=fa.head_of(after),
                         kind=kind, item=item, by=by, bit=bit,
                         gain=set(r[7]), loss=set(r[8]),
                         win_b=before[FBASE:FBASE + FB].hex(),
                         win_a=after[FBASE:FBASE + FB].hex(),
                         st_b=fa.st_of(before), st_a=fa.st_of(after)))
    return rows


def score_projection(rows):
    """The single digest surface for the score table (both passes hash this, not the dicts)."""
    return [(r["idx"], r["head"], r["kind"], tuple(sorted(r["gain"])),
             tuple(sorted(r["loss"])), r["win_b"], r["win_a"]) for r in rows]


def pred_window(win_b, by, item):
    """The stamp: OR the mapper mask into the mapper byte of the BEFORE window."""
    if by is None or item is None or not (0 <= by < FB):
        return None
    b = bytearray(bytes.fromhex(win_b))
    b[by] |= 1 << (item & 7)
    return b.hex()


# --- the measured model -------------------------------------------------------------------
def agg(rows):
    """Every aggregate the gates read, computed FROM the rows (so a mutant that edits a row is
    measured, not skipped)."""
    unit = [r for r in rows if r["kind"] == "UNIT"]
    fac = [r for r in rows if r["kind"] != "UNIT"]
    after_hits = 0
    for r in rows:
        k, i, by, bit = un.head_bit(r["head_after"])
        after_hits += int(bit is not None and bit in r["gain"])
    vs = [r for r in rows if "Virgin" in r["name"]]
    return dict(
        unit_n=len(unit), fac_n=len(fac),
        unit_hits=sum(1 for r in unit if r["bit"] is not None and r["bit"] in r["gain"]),
        fac_hits=sum(1 for r in fac if not (r["bit"] is not None and r["bit"] in r["gain"])),
        model_hits=sum(1 for r in rows
                       if (r["kind"] == "UNIT") == (r["bit"] is not None and r["bit"] in r["gain"])),
        shared_exact=sum(1 for r in rows
                         if pred_window(r["win_b"], r["by"], r["item"]) == r["win_a"]),
        off_map=[r for r in rows if r["by"] is None or not (0 <= r["by"] < FB)],
        after_hits=after_hits,
        vs=vs[0] if vs else None)


def build(census=None, keys=None, samples=None):
    census = load_census() if census is None else census
    keys = load_keys() if keys is None else keys
    samples = fa.load_trace() if samples is None else samples
    cfg = CFG(census)
    rows = rows_of(samples)
    m = dict(census=census, keys=keys, cfg=cfg, rows=rows, samples=samples)
    m["gate_writes"] = writes(census)
    m["r_entry"] = cfg.reach(ENTRY)
    m["r_unit"] = cfg.reach(UNIT_IN)
    m["r_fac"] = cfg.reach(FAC_IN)
    m["fac_gate_writes"] = [a for a in m["gate_writes"] if a in m["r_fac"]]
    m.update(agg(rows))
    m["d_census"] = _sha(census)
    m["d_cfg"] = _sha([(a, tuple(cfg.edges[a])) for a in cfg.addr])
    m["d_reach"] = _sha([(len(m["r_entry"]), len(m["r_unit"]), len(m["r_fac"])),
                         sorted("0x%06x" % a for a in (m["r_entry"] & {STAMP, OR_SITE})),
                         sorted("0x%06x" % a for a in (m["r_fac"] & {STAMP, OR_SITE}))])
    m["d_score"] = _sha(score_projection(rows))
    m["d_vs"] = _sha(m["vs"] if m["vs"] else [])
    return m


# --- output ------------------------------------------------------------------------------
GATES = []


def p(line=""):
    print(line)


def report(m):
    cfg, rows, keys, vs = m["cfg"], m["rows"], m["keys"], m["vs"]
    p("B33 - the facility leg's branch to the shared OR, walked and scored on the recorded run")
    p("census: %s  (%d instructions, 0x%06x..0x%06x)" %
      (os.path.relpath(CENSUS, ROOT), len(m["census"]), LO, HI))
    p("")

    p("TABLE 1  the three entries and what each can reach (instruction addresses)")
    for name, rs in (("function entry 0x%06x" % ENTRY, m["r_entry"]),
                     ("unit branch    0x%06x" % UNIT_IN, m["r_unit"]),
                     ("facility branch 0x%06x" % FAC_IN, m["r_fac"])):
        p("  %-24s reachable=%4d  stamp_0x%06x=%s  spend_site=%d/%d" %
          (name, len(rs), STAMP, STAMP in rs,
           sum(1 for a in SPEND_FAC if a in rs), sum(1 for a in SPEND_UNIT if a in rs)))
    p("")

    p("TABLE 2  the stamp block's door")
    p("  preds(0x%06x) = %s" % (STAMP, sorted("0x%06x" % a for a in cfg.preds[STAMP])))
    p("  preds(0x%06x) = %s" % (BLOCK, sorted("0x%06x" % a for a in cfg.preds[BLOCK])))
    for a in (0x4f0b7b, 0x4f0b7e, GATE, OR_SITE):
        p("  0x%06x  %s" % (a, keys.get(a, "<missing>")))
    p("  writes to %s anywhere in the function: %s" %
      (GATE_LOCAL, ["0x%06x" % a for a in m["gate_writes"]]))
    p("  of those reachable from the facility branch: %s" %
      (["0x%06x" % a for a in m["fac_gate_writes"]] or "none"))
    p("")

    p("TABLE 3  the two spend sites (both on ds:0x8f0d60 + 0x40)")
    for a in SPEND_FAC:
        p("  facility 0x%06x  %s" % (a, keys.get(a, "<missing>")))
    for a in SPEND_UNIT:
        p("  unit     0x%06x  %s" % (a, keys.get(a, "<missing>")))
    p("")

    p("TABLE 4  the model scored on the six recorded boundaries")
    for r in rows:
        stamp = r["kind"] == "UNIT"
        pred = pred_window(r["win_b"], r["by"], r["item"]) if stamp else r["win_b"]
        p("  base %-2d %-22s head=%-5d %-9s item=%-4s mapper=(%s,%s) -> %-11s "
          "gain=%-6s loss=%-6s  %s -> %s" %
          (r["idx"], r["name"][:22], r["head"], r["kind"], r["item"], r["by"],
           1 << (r["item"] & 7) if r["item"] is not None else "-",
           "stamp" if stamp else "no stamp", sorted(r["gain"]), sorted(r["loss"]),
           r["win_b"], r["win_a"]))
        p("       predicted window %-18s recorded %-18s" % (pred, r["win_a"]))
    p("  unit %d/%d   facility-range %d/%d   model %d/%d" %
      (m["unit_hits"], m["unit_n"], m["fac_hits"], m["fac_n"], m["model_hits"], len(rows)))
    p("")

    p("TABLE 5  the Virgin Soil anchor")
    if vs:
        p("  base %d %s head=%d %s item=%s  bitmap %s -> %s  gain=%s loss=%s  st %d -> %d" %
          (vs["idx"], vs["name"], vs["head"], vs["kind"], vs["item"], vs["win_b"],
           vs["win_a"], sorted(vs["gain"]), sorted(vs["loss"]), vs["st_b"], vs["st_a"]))
        p("  a stamp of item %s would predict %s" %
          (vs["item"], pred_window(vs["win_b"], vs["by"], vs["item"])))
    else:
        p("  <no Virgin Soil row>")
    p("")

    p("TABLE 6  rivals on the same printed numbers")
    p("  R1 the OR is shared (every head stamps)   -> windows match %d/%d; Virgin Soil predicts %s" %
      (m["shared_exact"], len(rows),
       pred_window(vs["win_b"], vs["by"], vs["item"]) if vs else "-"))
    p("  R2 an off-map mapper refusal explains it  -> rows it can refuse %d/%d; Virgin Soil off-map=%s"
      % (len(m["off_map"]), len(rows),
         bool(vs) and (vs["by"] is None or not (0 <= vs["by"] < FB))))
    p("  R3 the stamp reads the AFTER-pop head     -> bit in gains %d/%d" % (m["after_hits"], len(rows)))
    p("")


def gates(m):
    """Every condition over the measured model, returned as (num, label, ok, detail)."""
    cfg, rows, keys = m["cfg"], m["rows"], m["keys"]
    a = agg(rows)                      # recomputed from the rows: a row mutant is measured
    vs = a["vs"]
    out = []
    f_txt = [keys.get(a, "") for a in SPEND_FAC]
    u_txt = [keys.get(a, "") for a in SPEND_UNIT]
    out.append(("G1", "the census is the WHOLE function: %d instructions, span 0x%06x..0x%06x "
                "== Ghidra size %d" % (len(m["census"]), LO, HI, SIZE),
                len(m["census"]) == 3164 and m["census"][0][0] == LO and m["census"][-1][0] < HI
                and m["census"][0][0] == ENTRY, "digest=%s" % m["d_census"]))
    out.append(("G2", "the CFG is BUILT at instruction granularity - %d nodes, %d edges, "
                "%d external targets, %d indirect jumps: the graph is CLOSED, so reachability is "
                "complete" % (len(cfg.edges), sum(len(s) for s in cfg.edges.values()),
                              cfg.external, cfg.indirect),
                len(cfg.edges) == len(m["census"]) and cfg.indirect == 0 and cfg.external == 0,
                "digest=%s" % m["d_cfg"]))
    out.append(("G3", "reachability: stamp 0x%06x reached from entry (%d) and unit (%d), NOT from "
                "facility (%d)" % (STAMP, len(m["r_entry"]), len(m["r_unit"]), len(m["r_fac"])),
                STAMP in m["r_entry"] and STAMP in m["r_unit"] and STAMP not in m["r_fac"]
                and len(m["r_fac"]) > 40, "digest=%s" % m["d_reach"]))
    out.append(("G4", "the stamp has one entry edge (0x4f0d94) inside a block with one entry "
                "(0x4f0b80 jg), and that branch tests %s" % GATE_LOCAL,
                cfg.preds[STAMP] == {0x4f0d94} and cfg.preds[BLOCK] == {GATE}
                and cfg.ins[GATE][0] == "jg" and _direct(cfg.ins[GATE][1]) == BLOCK
                and "ebp-0x30" in keys.get(0x4f0b7b, "")))
    out.append(("G5", "%s is written at ONE site (%s), in the unit branch and nowhere in the "
                "facility region" % (GATE_LOCAL, ["0x%06x" % a for a in m["gate_writes"]]),
                m["gate_writes"] == [UNIT_IN] and not m["fac_gate_writes"]
                and UNIT_IN in m["r_unit"]))
    out.append(("G6", "the two legs SPEND at different sites: facility 0x%06x/0x%06x/0x%06x, unit "
                "0x%06x/0x%06x/0x%06x" % (SPEND_FAC + SPEND_UNIT),
                "ecx+0x40" in f_txt[0] and f_txt[1].startswith("sub") and "ecx+0x40" in f_txt[2]
                and "edx+0x40" in u_txt[0] and u_txt[1].startswith("sub") and "edx+0x40" in u_txt[2]
                and SPEND_FAC[1] in m["r_fac"] and SPEND_UNIT[1] in m["r_unit"]))
    out.append(("G7", "the model scores %d/%d: unit %d/%d stamp the mapper bit, facility-range "
                "%d/%d do not" % (a["model_hits"], len(rows), a["unit_hits"], a["unit_n"],
                                  a["fac_hits"], a["fac_n"]),
                a["unit_hits"] == a["unit_n"] == 4 and a["fac_hits"] == a["fac_n"] == 2
                and a["model_hits"] == len(rows) == 6, "digest=%s" % m["d_score"]))
    out.append(("G8", "Virgin Soil: facility head 2, %s -> %s (bit 2 absent, bit 4 gained, 27 "
                "lost), st 2 -> 0, a stamp would predict %s"
                % (vs["win_b"], vs["win_a"], pred_window(vs["win_b"], vs["by"], vs["item"]))
                if vs else "G8",
                bool(vs) and vs["kind"] == "FACILITY" and vs["item"] == 2 and vs["head"] == 2
                and vs["win_b"] == "0000000800000000" and vs["win_a"] == "1000000000000000"
                and vs["gain"] == {4} and vs["loss"] == {27} and vs["st_b"] == 2 and vs["st_a"] == 0
                and pred_window(vs["win_b"], vs["by"], vs["item"]) != vs["win_a"]))
    vs_offmap = bool(vs) and (vs["by"] is None or not (0 <= vs["by"] < FB))
    out.append(("G9", "rivals FAIL: shared OR matches %d/%d windows, an off-map refusal covers "
                "%d/%d rows (Virgin Soil in-window), after-pop head %d/%d"
                % (a["shared_exact"], len(rows), len(a["off_map"]), len(rows),
                   a["after_hits"], len(rows)),
                a["shared_exact"] == 4 and len(rows) == 6 and len(a["off_map"]) == 1
                and not vs_offmap and a["after_hits"] == 0))
    out.append(("G10", "the OR instruction itself is unreachable from the facility entry, "
                "reachable from the unit entry, and reads as `or BYTE PTR [eax],cl`",
                OR_SITE not in m["r_fac"] and OR_SITE in m["r_unit"]
                and keys.get(OR_SITE, "").startswith("or ")
                and "BYTE PTR [eax],cl" in keys.get(OR_SITE, "")))
    out.append(("G11", "the facility region writes [ebp-0x20] at 0x4efed1 and the unit block's "
                "read of it (0x4f0d8f) is unreachable from the facility entry",
                0x4efed1 in m["r_fac"] and cfg.ins[0x4efed1][1] == "w[ebp-0x20]"
                and cfg.ins[0x4f0d8f][1] == "r[ebp-0x20]" and 0x4f0d8f not in m["r_fac"]))
    out.append(("G12", "the CFG is CLOSED, two passes agree, every anchor is pinned to a literal",
                cfg.indirect == 0 and cfg.external == 0
                and _sha(score_projection(rows_of(m["samples"]))) == m["d_score"]
                and m["d_census"] == CENSUS_ANCHOR and m["d_cfg"] == CFG_ANCHOR
                and m["d_reach"] == REACH_ANCHOR and m["d_score"] == SCORE_ANCHOR
                and m["d_vs"] == VS_ANCHOR,
                "census=%s cfg=%s reach=%s score=%s vs=%s"
                % (m["d_census"], m["d_cfg"], m["d_reach"], m["d_score"], m["d_vs"])))
    return out


def main(argv=None):
    del argv
    GATES.clear()
    m = build()
    report(m)
    p("GATES")
    for item in gates(m):
        num, label, ok = item[:3]
        detail = item[3] if len(item) > 3 else ""
        GATES.append((num, ok))
        print(("ok   %s %s%s" if ok else "FAIL %s %s%s")
              % (num, label, ("  " + detail) if detail else ""))
    failed = [num for num, ok in GATES if not ok]
    print("")
    print("DIGEST %s gates=%d" % (m["d_census"], len(GATES)))
    if failed:
        print("FAIL B33: %d/%d gates" % (len(GATES) - len(failed), len(GATES)))
        for num in failed:
            print("  red: %s" % num)
        return 1
    print("PASS B33: %d/%d gates" % (len(GATES), len(GATES)))
    print("ANCHORS census=%s cfg=%s reach=%s score=%s vs=%s"
          % (m["d_census"], m["d_cfg"], m["d_reach"], m["d_score"], m["d_vs"]))
    return 0


class _Tee:
    """`--evidence` writes the exact stdout it prints to evidence/b33_facilityleg.txt."""

    def __init__(self, *fhs):
        self.fhs = fhs

    def write(self, s):
        for f in self.fhs:
            f.write(s)

    def flush(self):
        for f in self.fhs:
            f.flush()


if __name__ == "__main__":
    _argv = sys.argv[1:]
    if "--evidence" in _argv:
        _path = os.path.join(ROOT, "evidence", "b33_facilityleg.txt")
        with open(_path, "w", encoding="utf-8") as _fh:
            _old = sys.stdout
            sys.stdout = _Tee(_old, _fh)
            try:
                _rc = main([])
            finally:
                sys.stdout = _old
        sys.exit(_rc)
    sys.exit(main(_argv))
