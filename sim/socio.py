"""sim.socio - B38: alpha's `#SOCIO` 4x4x11 social-engineering matrix, executable.

M376 proved `0x92babc` is the grid FUN_0057a070 builds from `programs/alpha.txt` `#SOCIO`:
16 cells (4 categories x 4 choices) of 11 dwords (one per effect keyword), each dword the
signed count of the choice's `+`/`-` prefix on that keyword's token, and each cell's
"signature" (`+0x594`) the first POSITIVE column.  M379 proved the only readers of that
signature are two AI scorers that ADD on `>0` and REJECT on `<0`.

This module loads the matrix from the rules file the exe itself reads, applies a faction's four
settings, runs the bit-24 agenda consumer over the result, and gates the whole thing against the
numbers M376 measured off the disassembly.

`python3 -u -m sim.socio` prints the tables, then asserts them, then one PASS/FAIL line.
No box time, no /proc, no gdb.
"""

import hashlib
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALPHA_JSON = os.path.join(ROOT, "data", "alpha.json")
TEXT = os.environ.get("B38_TEXT", os.path.join(ROOT, "scratch", "m574", "text.txt"))
EVID = os.path.join(ROOT, "evidence", "m376_socio_grid.txt")
NROWS, NCELLS = 4, 4
ADDR = re.compile(r"^\s*([0-9a-f]{6,8}):\s+((?:[0-9a-f]{2} )+)\s*\t(.*)$")
GEOM_ADDRS = (0x52B822, 0x52B82C, 0x52B832, 0x52B847, 0x52B84D, 0x5A11F3, 0x5A1203)
MIL_LO, MIL_HI = 0x557980, 0x5579EA
GRID_DIGEST = "e0bb2deb53ecb96c"
IDS = ("G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8")


class SocioError(Exception):
    pass


def sha16(rows):
    return hashlib.sha1("\n".join(rows).encode("utf-8")).hexdigest()[:16]


def imm(pattern, text):
    m = re.search(pattern, text)
    if m is None:
        raise SystemExit("FAIL B38: %r does not match %r" % (pattern, text))
    return int(m.group(1), 16)


def load_dump():
    ins, order = {}, []
    with open(TEXT, "r", errors="replace") as f:
        for line in f:
            m = ADDR.match(line.rstrip("\n"))
            if not m:
                continue
            a = int(m.group(1), 16)
            ins[a] = m.group(3).strip()
            order.append(a)
    order.sort()
    return ins, order


def token_value(tok):
    """(signed value, keyword) from a `#SOCIO` effect token: one point per prefix char."""
    i = sign = 0
    while i < len(tok) and tok[i] in "+-":
        sign += 1 if tok[i] == "+" else -1
        i += 1
    return sign, tok[i:].strip()


class Cell:
    __slots__ = ("row", "idx", "name", "tech", "tokens", "vec")

    def __init__(self, row, idx, name, tech, tokens, vec):
        self.row, self.idx, self.name, self.tech = row, idx, name, tech
        self.tokens, self.vec = tokens, tuple(vec)

    def signature(self):
        for i, v in enumerate(self.vec):
            if v > 0:
                return i
        return -1


class Socio:
    """The 4x4x11 grid plus the one operation the game performs on it: sum over categories."""

    def __init__(self, path=ALPHA_JSON):
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        recs = doc["SOCIO"]
        self.path = path
        self.keywords = [s.strip() for s in recs[0]["fields"]]
        if [s.strip() for s in recs[1]["fields"]] != self.keywords:
            raise SocioError("#SOCIO: the two keyword lines disagree")
        self.categories = [s.strip() for s in recs[2]["fields"]]
        body = recs[3:]
        if len(self.categories) != NROWS or len(body) != NROWS * NCELLS:
            raise SocioError("#SOCIO: %d categories and %d choice records, want %dx%d"
                             % (len(self.categories), len(body), NROWS, NCELLS))
        self.rows = []
        for r in range(NROWS):
            row = []
            for c in range(NCELLS):
                fields = [s.strip() for s in body[r * NCELLS + c]["fields"]]
                if len(fields) < 2:
                    raise SocioError("#SOCIO[%d][%d]: %r has no name/tech pair" % (r, c, fields))
                row.append(Cell(r, c, fields[0], fields[1], fields[2:], self._vector(fields[2:])))
            self.rows.append(row)
        self.shape = (len(self.rows), len(self.rows[0]), len(self.keywords))

    def _vector(self, tokens):
        v = [0] * len(self.keywords)
        for tok in tokens:
            val, kw = token_value(tok)
            if not val:
                raise SocioError("#SOCIO: token %r carries no +/- prefix" % tok)
            try:
                v[self.keywords.index(kw)] += val
            except ValueError:
                raise SocioError("#SOCIO: token %r names %r, not one of the 11 keywords"
                                 % (tok, kw)) from None
        return v

    def cells(self):
        for row in self.rows:
            for cell in row:
                yield cell

    def apply(self, settings):
        """settings = one choice index per category, in category order -> 11 totals."""
        if len(settings) != NROWS:
            raise SocioError("apply: %d settings for %d categories" % (len(settings), NROWS))
        out = [0] * len(self.keywords)
        for r, c in enumerate(settings):
            for i, v in enumerate(self.rows[r][c].vec):
                out[i] += v
        return tuple(out)

    def reference_apply(self, settings):
        """A second implementation: accumulate keyword -> delta in a dict, then project."""
        acc = {}
        for r, c in enumerate(settings):
            for tok in self.rows[r][c].tokens:
                val, kw = token_value(tok)
                acc[kw] = acc.get(kw, 0) + val
        return tuple(acc.get(kw, 0) for kw in self.keywords)

    def digest(self):
        rows = ["%d,%d,%s,%s" % (c.row, c.idx, c.name, ",".join(str(x) for x in c.vec))
                for c in self.cells()]
        return sha16(rows)


# ---------------------------------------------------------------- gates

FAIL = []


def gate(gid, cond, text):
    print("  %s   %s   %s" % ("ok " if cond else "BAD", gid, text))
    if not cond:
        FAIL.append(gid)


def main(argv=None):
    soc = Socio()
    soc2 = Socio()                       # a SECOND decode of the same file
    kw = soc.keywords
    print("B38 the #SOCIO SE-effect matrix as an executable: 4x4x11 grid -> a faction's effects -> "
          "the agenda signature")
    print("tag  what                                                       value")

    ev = {}
    with open(EVID, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^G\d\s+(.+?)\s{2,}(\S.*)$", line.rstrip("\n"))
            if m:
                ev.setdefault(m.group(1).strip(), m.group(2).strip())

    print("G0   alpha.json sha1                                            %s"
          % hashlib.sha1(open(ALPHA_JSON, "rb").read()).hexdigest()[:16])
    print("G0   text dump sha1                                             %s"
          % hashlib.sha1(open(TEXT, "rb").read()).hexdigest()[:16])
    print("G0   #SOCIO keywords                                            %s" % ", ".join(kw))
    print("G0   #SOCIO categories                                          %s"
          % ", ".join(soc.categories))
    print("G0   grid digest (decode 1 / decode 2)                          %s / %s"
          % (soc.digest(), soc2.digest()))
    print("G0   evidence keyword list == model                             %s"
          % (ev.get("keyword list") == ", ".join(kw)))
    print("G0   evidence categories == model                               %s"
          % (ev.get("categories") == ", ".join(soc.categories)))
    gate("G0", soc.digest() == soc2.digest() and len(kw) == 11 and len(soc.categories) == 4
         and ev.get("keyword list") == ", ".join(kw)
         and ev.get("categories") == ", ".join(soc.categories),
         "the rules file's 11 keywords and 4 categories agree with M376's evidence line, and the "
         "grid digest reproduces on a second decode")

    ins, order = load_dump()
    g = {}
    for a in GEOM_ADDRS:
        if a not in ins:
            raise SystemExit("FAIL B38: dump has no instruction at 0x%x" % a)
        g[a] = ins[a]
    TAIL = r",0x([0-9a-f]+)$"
    width_copy = imm(TAIL, g[0x52B822])
    cell_step = imm(TAIL, g[0x52B82C])
    cells_bound = imm(TAIL, g[0x52B832])
    row_step = imm(TAIL, g[0x52B847])
    rows_bound = imm(TAIL, g[0x52B84D])
    lea_disp = imm(r"\+0x([0-9a-f]+)\]$", g[0x5A11F3])
    width_scan = imm(TAIL, g[0x5A1203])
    if "+0x%x]" % lea_disp not in g[0x5A11F3]:
        raise SystemExit("FAIL B38: 0x5a11f3 is not a lea with a +disp operand: %r" % g[0x5A11F3])
    rows = rows_bound // row_step
    cells = cells_bound // cell_step
    print("G1   0x52b822  %-42s %s" % (g[0x52B822], width_copy))
    print("G1   0x52b82c  %-42s %s" % (g[0x52B82C], cell_step))
    print("G1   0x52b832  %-42s %s" % (g[0x52B832], cells_bound))
    print("G1   0x52b847  %-42s %s" % (g[0x52B847], row_step))
    print("G1   0x52b84d  %-42s %s" % (g[0x52B84D], rows_bound))
    print("G1   0x5a11f3  %-42s %s" % (g[0x5A11F3], hex(lea_disp)))
    print("G1   rows = 0x350/0xd4, cells = 0xb0/0x2c, width = 0x2c/4       %d x %d x %d"
          % (rows, cells, cell_step // 4))
    print("G1   row stride minus the 4 cells = the 0x24 row header         0x%x - 0x%x = 0x%x"
          % (row_step, cells_bound, row_step - cells_bound))
    print("G1   model shape                                               %dx%dx%d" % soc.shape)
    print("G1   parse-bound widths agree (0x52b822 vs 0x5a1203)           %d / %d"
          % (width_copy, width_scan))
    gate("G1", (rows, cells, cell_step // 4) == soc.shape == (NROWS, NCELLS, 11)
         and row_step - cells_bound == 0x24 and rows_bound == rows * row_step
         and cells_bound == cells * cell_step
         and width_copy == width_scan == len(kw) and lea_disp == 0x92BABC,
         "the dump's own coefficients give 4 rows x 4 cells x 11 dwords at 0x92babc, row stride "
         "0x24 header + 0xb0, and the model's shape is that shape")

    print("G3   16 cells; vector = signed count per keyword column, in column order")
    for cell in soc.cells():
        print("G3   %d %d  %-16s %-10s %s  sig=%d"
              % (cell.row, cell.idx, cell.name, cell.tech,
                 "[" + ", ".join(str(x) for x in cell.vec) + "]", cell.signature()))
    bad_tok = [(c.name, t) for c in soc.cells() for t in c.tokens if token_value(t)[1] not in kw]
    mags = [abs(x) for c in soc.cells() for x in c.vec]
    dup = [c.name for c in soc.cells()
           if len({token_value(t)[1] for t in c.tokens}) != len(c.tokens)]
    print("G3   cells / tokens / max |value|                              %d / %d / %d"
          % (sum(1 for _ in soc.cells()), sum(len(c.tokens) for c in soc.cells()), max(mags)))
    gate("G3", len(bad_tok) == 0 and max(mags) == 5 and not dup
         and all(len(c.vec) == 11 for c in soc.cells())
         and all(sum(1 for v in c.vec if v) <= len(c.tokens) for c in soc.cells()),
         "every effect token resolves to exactly one of the 11 columns, no cell repeats a "
         "keyword, and no |value| exceeds --5's 5")

    print("G2   parity vectors, model vs evidence/m376_socio_grid.txt:42-43")
    for name in ("Police State", "Free Market"):
        mine = next(c.vec for c in soc.cells() if c.name == name)
        print("G2   %-14s model %-38s evidence %s"
              % (name, "[" + ", ".join(str(x) for x in mine) + "]",
                 ev.get("vector of '%s'" % name, "")))
    empty = [(c.row, c.idx, c.name) for c in soc.cells() if not any(c.vec)]
    firsts = [c.signature() for c in soc.cells() if c.signature() >= 0]
    ps_sig = next(c.signature() for c in soc.cells() if c.name == "Police State")
    print("G2   empty cells                                               %s" % (empty,))
    print("G2   non-empty / first-positive                                %d / %d"
          % (16 - len(empty), len(firsts)))
    print("G2   evidence says (cells parsed, empty, first-positive)       %s / %s / %s"
          % (ev.get("cells parsed"), ev.get("non-empty cells"),
             ev.get("cells with a first-positive effect")))
    print("G2   first-positive of 'Police State' (model / evidence)       %d / %s"
          % (ps_sig, ev.get("first-positive of 'Police State'")))
    mine_ps = next(c.vec for c in soc.cells() if c.name == "Police State")
    mine_fm = next(c.vec for c in soc.cells() if c.name == "Free Market")
    gate("G2", "[%s]" % ", ".join(str(x) for x in mine_ps) == ev.get("vector of 'Police State'")
         and "[%s]" % ", ".join(str(x) for x in mine_fm) == ev.get("vector of 'Free Market'")
         and empty == [(0, 0, "Frontier"), (1, 0, "Simple"), (2, 0, "Survival"), (3, 0, "None")]
         and len(firsts) == int(ev.get("cells with a first-positive effect", "-1")) == 12
         and ps_sig == int(ev.get("first-positive of 'Police State'", "-9")),
         "both vectors M376 measured off the emulated parser are reproduced field for field, and "
         "so are its 4 empty cells, its 12 first-positive cells and Police State's 2")

    settings = (1, 2, 1, 3)   # Police State / Planned / Power / Thought Control
    names = [soc.rows[r][c].name for r, c in enumerate(settings)]
    tot = soc.apply(settings)
    ref = soc.reference_apply(settings)
    print("G4   settings                                                  %s" % " / ".join(names))
    print("G4   totals                                                    [%s]"
          % ", ".join("%s%+d" % (k, v) for k, v in zip(kw, tot)))
    print("G4   same totals from the dict reference                       %s" % (tot == ref))
    sweep_bad = 0
    for pol in range(NCELLS):
        for eco in range(NCELLS):
            for val in range(NCELLS):
                for fut in range(NCELLS):
                    s = (pol, eco, val, fut)
                    if soc.apply(s) != soc.reference_apply(s) or len(soc.apply(s)) != 11:
                        sweep_bad += 1
    print("G4   sweep 4^4 settings, model != reference                     %d" % sweep_bad)
    base = soc.apply((0, 0, 0, 0))
    delta = tuple(a - b for a, b in zip(soc.apply((settings[0], 0, 0, 0)), base))
    print("G4   single-category delta (Politics only)                      [%s]"
          % ", ".join(str(x) for x in delta))
    print("G4   that delta equals the Police State vector, base zero       %s / %s"
          % (delta == soc.rows[0][1].vec, base == tuple([0] * 11)))
    gate("G4", tot == (0, -4, 1, 0, 4, 4, 2, 0, 2, -1, 0) and tot == ref and sweep_bad == 0
         and delta == soc.rows[0][1].vec and base == tuple([0] * 11),
         "a faction's four settings give one 11-vector: the printed totals are the component sum, "
         "every one of 256 settings agrees with the dict-based reference, and one category's "
         "delta is exactly that choice's vector")

    print("G5   bit-24 agenda consumer: stored triple (category, choice, signature)")
    recs = [(c.row, c.idx, c.signature()) for c in soc.cells()]
    print("G5   records                                                   %s" % (recs,))
    adds = [r for r in recs if r[2] >= 0]
    rejects = [r for r in recs if r[2] < 0]
    print("G5   M379 reader polarity: >0 adds / <0 rejects                 %d add, %d reject"
          % (len(adds), len(rejects)))
    gate("G5", len(recs) == 16 and len(adds) == 12 and len(rejects) == 4
         and all(r[2] == -1 for r in rejects)
         and next(r[2] for r in recs if r[0] == 0 and r[1] == 1) == 2
         and all(0 <= r[2] <= 10 for r in adds),
         "every cell stores a signature; the 4 empty cells store -1 (the reader's reject arm) and "
         "the 12 others store a column 0..10 (the add arm), Police State -> 2")

    win = [a for a in order if MIL_LO <= a <= MIL_HI]
    hits = [a for a in win if "92ba" in ins[a]]
    store = [a for a in win if ins[a].startswith("mov") and "DWORD PTR [ebx+0x94e48c]," in ins[a]]
    load = [a for a in win if ins[a].startswith("mov") and ins[a].endswith("DWORD PTR [ebx+0x94e48c]")]
    summ = [a for a in win if ins[a].startswith("add") and "0x94e48c" in ins[a]]
    print("G6   M383 chain window 0x557980..0x5579ea                       %d insns" % len(win))
    print("G6   0x94e48c loads / stores / adds inside the window          %s / %s / %s"
          % (", ".join(hex(a) for a in load) or "none",
             ", ".join(hex(a) for a in store) or "none",
             ", ".join(hex(a) for a in summ) or "none"))
    print("G6   operands naming 0x92babc/0x92ba98 in the window            %d" % len(hits))
    print("G6   SE totals reaching the military sum                       wired: NO (0 operands)")
    gate("G6", len(win) >= 25 and store == [0x5579EA] and load == [0x5579DA]
         and summ == [] and hits == [],
         "the per-unit military sum M383 named (0x94e48c @0x5579ea) sits in a 25+ insn window "
         "with ZERO matrix operands: the SE grid is not an input to it and the model does not "
         "pretend otherwise")

    print("G7   rivals, each on the printed numbers")
    fm = soc.rows[1][1]
    r1 = sum((1 if t[0] == "+" else -1) for t in fm.tokens if token_value(t)[1] == "POLICE")
    order_a = sorted(range(len(kw)), key=lambda i: kw[i])
    r2 = tuple(soc.rows[0][1].vec[order_a.index(i)] for i in range(len(kw)))
    r3 = tuple(sum(c.vec[i] for c in soc.cells()) for i in range(len(kw)))
    r4 = tuple(sum(soc.rows[r][settings[r]].vec[i] for r in range(3)) for i in range(len(kw)))
    r5 = max(i for i, v in enumerate(soc.rows[0][1].vec) if v)
    print("G7   R1 sign-only: Free Market POLICE                          model %+d  rival %+d"
          % (fm.vec[5], r1))
    print("G7   R2 alphabetical columns: Police State vector               model %s  rival %s"
          % (list(soc.rows[0][1].vec), list(r2)))
    print("G7   R3 accumulate all 16 cells: totals                        model %s  rival %s"
          % (list(tot), list(r3)))
    print("G7   R4 Future Society dropped: totals                         model %s  rival %s"
          % (list(tot), list(r4)))
    print("G7   R5 last-positive signature: Police State                  model %d  rival %d"
          % (ps_sig, r5))
    gate("G7", r1 == -1 != fm.vec[5] and r2 != soc.rows[0][1].vec and r3 != tot and r4 != tot
         and r5 == 5 != ps_sig,
         "five rival readings each differ from the model on the printed numbers: sign-only "
         "counting, alphabetical columns, all-cells accumulation, a dropped Future Society row, "
         "and last-positive signatures")

    print("G8   grid digest                                               %s" % soc.digest())
    print("G8   second decode                                             %s" % soc2.digest())
    gate("G8", soc.digest() == soc2.digest() == GRID_DIGEST,
         "the grid digest is pinned and reproduced on a second decode")

    passed = len(IDS) - len(set(FAIL))
    code = ("PASS B38: %d/%d gates  digest %s" % (passed, len(IDS), soc.digest())
            if not FAIL else
            "FAIL B38: %d/%d gates  red=%s  digest %s"
            % (passed, len(IDS), ",".join(sorted(set(FAIL))), soc.digest()))
    print(code)
    return 0 if not FAIL else 1


if __name__ == "__main__":
    raise SystemExit(main())
