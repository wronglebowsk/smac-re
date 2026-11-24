"""sim.treaty - rung B37: the TREATY LIFECYCLE - arm, count down, expire, (status clear).

B36 modelled the WORD: an action is a mask, FUN_00551a20 applies it, FUN_005076d0 classifies it.
It could not model TIME.  M375 measured that exactly one relations bit owns a clock: `0x40` (SET
TREATY).  Every store that leaves `0x40` set writes `0x32` (50) to the parallel cell at
`0x94d4c8`, and the upkeep pass at `0x5552b6` decrements it and clears `0x40` on the tick that
reaches zero.

This rung extracts that countdown block from the SAME .text dump the static milestones used and
RUNS it (a 10-instruction interpreter, not a description), against an independent `Lifecycle`
written from the immediates.  The lifecycle is then closed end to end:

  arm     `0x40` arrives three ways and each is proved on the bytes: a caller mask carrying 0x40
          (0x551d22, guarded by `test cl,0x40`), and two literal `and 0xfffdfbff` / `or 0x840`
          stores inside FUN_005551e0 (0x5553f3, 0x5556eb).  All four arms write 50.
  tick    one upkeep pass over one pair: cell==0 -> NO store at all; else cell-=1, store, and
          ONLY if the new value is 0 clear the word's bit 6 (`and al,0xbf`).
  expire  the 50th tick after an arm.  A re-arm is a fresh 50-tick lease from its own tick.
  clear   a STATUS WRITE clears 0x40 from the word but touches no cell: 0 of the 11 cell
          references lie inside the status writer (0x551a20..0x551c32), so the countdown survives
          the peace and its later expiry stores the word back byte-identical - a NULL write.

0x800000 (TREATY ON, M375) is the other half of the lifecycle: every `mask & 0x17` status write
clears it, and the expiry's byte mask cannot restore it (0xbf holds no bit 23).

Commands:  python3 -u -m sim.treaty            (acceptance)
           python3 -u -m sim.treaty --pin      (print the anchors to pin)
           python3 -u -m sim.treaty --quiet    (relay mode used by sim.selftest --b37)
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("B37_TEXT") or os.path.join(ROOT, "scratch/m574/text.txt")
EXE = os.environ.get("B37_EXE") or os.path.join(ROOT, "programs/terran.exe")

CELL, WORD = 0x94D4C8, 0x94D448
TICK_LO, TICK_HI = 0x5552B6, 0x5552D4          # the countdown block: load .. word store
STATUS_LO, STATUS_HI = 0x551A20, 0x551C32      # FUN_00551a20, the status writer
ARM_CELL_VALUE = 0x32                          # 50 ticks
EXPIRE_BYTE = 0xBF                             # and al,0xbf - bit 6, low byte only
SET_TREATY, TREATY_ON = 0x40, 0x800000
LADDER_BITS = 0x17
PEACE_CLEAR = 0xEE7FAF | 0xFF000000            # any mask & 7
WAR_CLEAR = 0xFAEEF378                         # any mask & 0x10
UNLOCK_CLEAR = 0xFF7FFFFF                      # any mask & 0x17

ANCHOR = "5dd4119bd1882d1d"
ARM_DIGEST = "7511618271d4a713"
TRACE_DIGEST = "a068538690fbe406"

FAIL = []
INSN = re.compile(r"^\s+([0-9a-f]{4,8}):\t[0-9a-f ]+\t(\S+)(?:\s+(.*))?$")


def gate(gid, cond, msg):
    ok = bool(cond)
    print("%s %s %s" % ("ok  " if ok else "BAD ", gid, msg))
    if not ok:
        FAIL.append(gid)
    return ok


def sha16(rows):
    h = hashlib.sha256()
    for r in rows:
        h.update(repr(r).encode("utf-8"))
    return h.hexdigest()[:16]


def load(path=TEXT):
    out = []
    with open(path, errors="replace") as fh:
        for ln in fh:
            m = INSN.match(ln)
            if m:
                out.append((int(m.group(1), 16), m.group(2), (m.group(3) or "").strip()))
    return out


def window(ins, lo, hi):
    return [r for r in ins if lo <= r[0] < hi]


# --------------------------------------------------------------------- the dump's countdown block
def run_tick_block(block, cell, word):
    """Interpret the extracted 10-instruction block over real register/memory semantics.

    Raises on any op it was not written for, so a dump drift reddens a gate instead of silently
    modelling something else.  Returns (cell, word, stores) where stores is [(address, value)].
    """
    mem = {CELL: cell & 0xFFFFFFFF, WORD: word & 0xFFFFFFFF}
    stores = []
    regs = {"eax": 0}
    zf = False
    by = {a: (mn, op) for a, mn, op in block}
    pc = block[0][0]
    steps = 0
    while pc in by:
        steps += 1
        if steps > 64:
            raise RuntimeError("tick block did not terminate")
        mn, op = by[pc]
        jump = None
        if mn == "mov" and op == "eax,DWORD PTR [edi+0x94d4c8]":
            regs["eax"] = mem[CELL]
        elif mn == "mov" and op == "eax,DWORD PTR [edi+0x94d448]":
            regs["eax"] = mem[WORD]
        elif mn == "test" and op == "eax,eax":
            zf = regs["eax"] == 0
        elif mn == "dec" and op == "eax":
            regs["eax"] = (regs["eax"] - 1) & 0xFFFFFFFF
        elif mn == "mov" and op == "DWORD PTR [edi+0x94d4c8],eax":
            mem[CELL] = regs["eax"]
            stores.append((pc, mem[CELL]))
        elif mn == "mov" and op == "DWORD PTR [edi+0x94d448],eax":
            mem[WORD] = regs["eax"]
            stores.append((pc, mem[WORD]))
        elif mn == "and" and op == "al,0xbf":
            regs["eax"] = (regs["eax"] & ~0xFF) | (regs["eax"] & EXPIRE_BYTE)
        elif mn in ("je", "jne"):
            taken = zf if mn == "je" else not zf
            if taken:
                jump = int(op, 16)
        else:
            raise RuntimeError("unmodelled op in the tick block: %08x %s %s" % (pc, mn, op))
        if jump is None:
            pc = _next_addr(block, pc)
        elif jump not in by:
            break                                   # the single exit 0x5552d9 leaves the block
        else:
            pc = jump
    return mem[CELL], mem[WORD], stores


def _next_addr(block, pc):
    idx = [i for i, r in enumerate(block) if r[0] == pc][0]
    return block[idx + 1][0] if idx + 1 < len(block) else -1


# ------------------------------------------------------------------------- the independent model
class Lifecycle(object):
    """The treaty lease, written from the immediates, never from the dump."""

    def __init__(self, word=0, cell=0):
        self.word, self.cell = word & 0xFFFFFFFF, cell & 0xFFFFFFFF

    def arm(self):
        self.word |= SET_TREATY
        self.cell = ARM_CELL_VALUE

    def tick(self):
        """One upkeep pass over one pair.  Returns True when the block stored anything."""
        if self.cell == 0:
            return False
        self.cell -= 1
        if self.cell == 0:
            self.word &= ~SET_TREATY
        return True

    def status(self, mask):
        """B36's writer, reduced to the three clears the lifecycle needs (order as measured)."""
        if mask & LADDER_BITS:
            self.word &= UNLOCK_CLEAR
        if mask & 0x7:
            self.word &= PEACE_CLEAR
        if mask & 0x10:
            self.word &= WAR_CLEAR
        self.word = (self.word | mask) & 0xFFFFFFFF
        return self.word


# ------------------------------------------------------------------------------ arm-site reading
ALIASES = {"eax": ("eax", "al"), "edx": ("edx", "dl"), "ecx": ("ecx", "cl"), "edi": ("edi", "dil")}


def word_store_before(ins, addr, span=14):
    """The nearest preceding store to the relations word, with the ops that fed its register."""
    idx = [i for i, r in enumerate(ins) if r[0] == addr][0]
    for j in range(idx - 1, max(0, idx - span) - 1, -1):
        a, mn, op = ins[j]
        if mn == "mov" and re.match(r"^DWORD PTR \[[^\]]*0x94d448\],[a-z]{2,3}$", op):
            reg = op.split(",")[-1]
            if reg not in ALIASES:
                return None
            return {"store": a, "reg": reg, "ops": ins[max(0, j - 10):j]}
    return None


def chain_carries_40(rec):
    """Does this store's mask chain set bit 6 - literally, or via a caller mask guarded by a
    `test cl,0x40`?  Evaluated from the instructions, never from the address."""
    wide, narrow = ALIASES[rec["reg"]]
    for a, mn, op in rec["ops"]:
        if mn == "test" and op in ("cl,0x40", "dl,0x40", "al,0x40"):
            return ("conditional", a, None)
    for a, mn, op in reversed(rec["ops"]):
        m = re.match(r"^(%s|%s),(0x[0-9a-f]+)$" % (wide, narrow), op)
        if mn == "or" and m:
            imm = int(m.group(2), 16)
            if imm & SET_TREATY:
                return ("literal", a, imm)
            return ("clear-only", a, imm)
    return ("none", None, None)


def arm_table(ins):
    arms = [a for a, mn, op in ins if mn == "mov" and "0x94d4c8" in op
            and op.endswith(",0x%x" % ARM_CELL_VALUE)]
    rows = []
    for a in arms:
        rec = word_store_before(ins, a)
        k = chain_carries_40(rec) if rec else ("none", None, None)
        rows.append((a, k[0], k[1], k[2], rec["store"] if rec else 0))
    return arms, rows


def transcript(word=0x80000108):
    """Turn 0 arms.  Every turn then runs ONE upkeep tick, and an arm or a status write in that
    turn happens BEFORE it (the writer and the upkeep are different functions - policy, declared
    UNMODELED).  Re-arm t30, treaty status t40, run to t120.  Returns (trace, expiry_ticks)."""
    lc = Lifecycle(word)
    lc.arm()
    trace = [(0, "arm", lc.word, lc.cell)]
    expired = []
    for t in range(1, 121):
        ev = "tick"
        if t == 30:
            lc.arm(); ev = "arm"
        elif t == 40:
            lc.status(0x2); ev = "treaty-status"
        prev = lc.cell
        lc.tick()
        if prev == 1 and lc.cell == 0:
            expired.append(t)
        trace.append((t, ev, lc.word, lc.cell))
    return trace, expired


# ------------------------------------------------------------------------------------ rivals
def run_seq(word, cell, ticks, arm_at=None, status_at=None, status_mask=0,
            status_clears_cell=False, no_rearm=False, dec_all=False,
            arm_value=ARM_CELL_VALUE, expiry_clears_on=False, expiry_low_byte=False):
    """A rival lifecycle.  Each flag is one competing reading of the dump.  Returns
    (word, cell, first_tick_0x40_went_clear) so a rival that merely re-times the lease cannot
    pass by landing on the same end state."""
    w, c = word & 0xFFFFFFFF, cell & 0xFFFFFFFF
    clear = None
    rows = []
    for t in range(1, ticks + 1):
        was = w & SET_TREATY
        if arm_at is not None and t == arm_at:
            if not (no_rearm and c):
                w |= SET_TREATY
                c = arm_value
        if status_at is not None and t == status_at:
            if status_clears_cell:
                c = 0
            if status_mask & LADDER_BITS:
                w &= UNLOCK_CLEAR
            if status_mask & 0x7:
                w &= PEACE_CLEAR
            if status_mask & 0x10:
                w &= WAR_CLEAR
            w = (w | status_mask) & 0xFFFFFFFF
        if dec_all:
            c = (c - 1) & 0xFFFFFFFF
            if c == 0:
                w &= ~SET_TREATY
        elif c:
            c -= 1
            if c == 0:
                if expiry_clears_on:
                    w &= ~TREATY_ON
                if expiry_low_byte:
                    w &= ~0xFF
                else:
                    w &= ~SET_TREATY
        if was and not w & SET_TREATY and clear is None:
            clear = t
        rows.append((w, c))
    return w & 0xFFFFFFFF, c, clear, sha16(rows)


def run_lifecycle(word, cell, ticks, arm_at=None, status_at=None, status_mask=0):
    """The same event schedule run through `Lifecycle` - the reference the rivals must miss."""
    lc = Lifecycle(word, cell)
    clear = None
    rows = []
    for t in range(1, ticks + 1):
        was = lc.word & SET_TREATY
        if arm_at == t:
            lc.arm()
        if status_at == t:
            lc.status(status_mask)
        lc.tick()
        if was and not lc.word & SET_TREATY and clear is None:
            clear = t
        rows.append((lc.word, lc.cell))
    return lc.word, lc.cell, clear, sha16(rows)


# ------------------------------------------------------------------------------------ acceptance
def accept(quiet=False):
    ins = load()
    blk = window(ins, TICK_LO, TICK_HI)
    d1 = sha16(blk)
    d2 = sha16(window(load(), TICK_LO, TICK_HI))          # second decode of the same file

    # ---- G0 the block, pinned by shape and by the immediates it carries -------------------
    print("G0  the countdown block %08x..%08x" % (TICK_LO, TICK_HI))
    for a, mn, op in blk:
        print("    %08x %-8s %s" % (a, mn, op))
    cell_st = [a for a, mn, op in blk if mn == "mov" and op == "DWORD PTR [edi+0x94d4c8],eax"]
    word_st = [a for a, mn, op in blk if mn == "mov" and op == "DWORD PTR [edi+0x94d448],eax"]
    imm_bf = [(a, op) for a, mn, op in blk if mn == "and" and op == "al,0xbf"]
    exits = sorted(set(int(op, 16) for a, mn, op in blk if mn in ("je", "jne")))
    print("  insns %d  cell-store %s  word-store %s  and-byte %s  both branches -> %s"
          % (len(blk), " ".join("%08x" % a for a in cell_st), " ".join("%08x" % a for a in word_st),
             "0x%02x@%08x" % (EXPIRE_BYTE, imm_bf[0][0]) if imm_bf else "MISSING",
             " ".join("%08x" % e for e in exits)))
    gate("G0", len(blk) == 10 and len(cell_st) == 1 and len(word_st) == 1 and len(imm_bf) == 1
         and exits == [0x5552D9],
         "10 insns, one cell store and one word store, ONE `and al,0xbf`, and both branches leave "
         "through the SAME exit 0x5552d9 - so the null-cell path stores nothing at all")

    # ---- G1 the arm census over the whole dump -------------------------------------------
    print("\nG1  every reference to the cell 0x%x" % CELL)
    refs = [(a, mn, op) for a, mn, op in ins if "0x94d4c8" in op]
    arms = [a for a, mn, op in refs if mn == "mov" and op.endswith(",0x%x" % ARM_CELL_VALUE)]
    reads = [a for a, mn, op in refs if mn == "mov" and re.match(r"^[a-z]{2,3},DWORD PTR", op)]
    wback = [a for a, mn, op in refs if mn == "mov" and "DWORD PTR [" in op
             and re.match(r"^DWORD PTR \[[^\]]*\],[a-z]{2,3}$", op)]
    leas = [a for a, mn, op in refs if mn == "lea"]
    for a, mn, op in refs:
        print("    %08x %-8s %s" % (a, mn, op))
    print("  %d refs = %d arms(%d) + %d reads + %d write-backs + %d lea"
          % (len(refs), len(arms), len(refs) - len(reads) - len(wback) - len(leas),
             len(reads), len(wback), len(leas)))
    _a, rows = arm_table(ins)
    for r in rows:
        print("  arm %08x  chain %-11s at %s  imm %s  predecessor store %08x"
              % (r[0], r[1], "%08x" % r[2] if r[2] else "-",
                 "0x%x" % r[3] if r[3] else "-", r[4]))
    kinds = sorted(set(r[1] for r in rows))
    ad = sha16(rows)
    gate("G1", len(refs) == 11 and len(arms) == 4 and len(reads) == 3 and len(wback) == 3
         and len(leas) == 1 and kinds == ["conditional", "literal"] and ad == ARM_DIGEST,
         "11 cell references; 4 arms of 0x32 - %d literal `or .,0x840`, %d caller-mask guarded by "
         "`test cl,0x40` - and every arm's preceding word store provably carries 0x40"
         % (len([r for r in rows if r[1] == "literal"]),
            len([r for r in rows if r[1] == "conditional"])))

    # ---- G2 parity: the dump block vs the model ------------------------------------------
    print("\nG2  parity of the extracted block against Lifecycle.tick")
    words = [0x0, 0x40, 0x800000, 0x40 | 0x800000, 0x80000108 | 0x40, 0xFFFFFFFF, 0x41, 0xC0]
    dis = cases = 0
    shape = {}
    for c in range(256):
        for w in words:
            cases += 1
            bc, bw, st = run_tick_block(blk, c, w)
            lc = Lifecycle(w, c)
            lc.tick()
            if (bc, bw) != (lc.cell, lc.word):
                dis += 1
            key = (c == 0, len(st))
            shape[key] = shape.get(key, 0) + 1
    print("  %d (cell,word) pairs, %d disagreements" % (cases, dis))
    print("  stores written: cell==0 -> %d; cell==1 -> %d; cell>=2 -> %d of %d"
          % (shape.get((True, 0), 0), shape.get((False, 2), 0), shape.get((False, 1), 0), cases))
    lc = Lifecycle(0x800000)
    lc.arm()
    expire_tick = None
    for t in range(1, 121):
        lc.tick()
        if lc.cell == 0 and expire_tick is None:
            expire_tick = t
    print("  arm -> cell reaches 0 at tick %s, word 0x%x" % (expire_tick, lc.word))
    gate("G2", dis == 0 and cases == 256 * len(words) and shape.get((True, 0), 0) == len(words)
         and shape.get((False, 2), 0) == len(words) and expire_tick == 50,
         "0 disagreements over %d pairs; a zero cell writes NOTHING (%d of %d cases), a one-cell "
         "writes both stores (%d), and the armed lease expires at tick 50 exactly"
         % (cases, shape.get((True, 0), 0), cases, shape.get((False, 2), 0)))

    # ---- G3 the lifecycle transcript -----------------------------------------------------
    print("\nG3  replayed lifecycle: arm t0, re-arm t30, treaty status t40, run to t120")
    trace, expired = transcript()
    td = sha16(trace)
    for t in (29, 30, 39, 40, 79, 80):
        print("  t%-3d %-13s word 0x%08x cell %d" % (t, trace[t][1], trace[t][2], trace[t][3]))
    print("  ticks that expired the lease: %s   digest %s" % (expired, td))
    gate("G3", trace[29][3] == 21 and trace[29][2] & SET_TREATY and trace[30][3] == 49
         and trace[39][3] == 40 and trace[40][3] == 39 and not trace[40][2] & SET_TREATY
         and trace[79][3] == 0 and expired == [79] and td == TRACE_DIGEST,
         "t29 holds 21 ticks with 0x40; t30 re-arms a fresh 50 whose own upkeep still runs; "
         "t40's status write clears 0x40 with the cell at 39; the lease expires once, at t79")

    # ---- G4 the asymmetry: which status mask leaves the lease running ---------------------
    print("\nG4  status write vs the cell - the null write at expiry (run through the dump block)")
    print("  0xffee7faf & 0x40 = 0x%x (peace CLEARS SET TREATY) ; 0xfaeef378 & 0x40 = 0x%x "
          "(war KEEPS it)" % (PEACE_CLEAR & SET_TREATY, WAR_CLEAR & SET_TREATY))
    nul = {}
    for mask in (0x2, 0x10):
        nul[mask] = 0
        for st in range(1, 50):
            lc = Lifecycle(0)
            lc.arm()
            for t in range(1, 51):
                if t == st:
                    lc.status(mask)
                if lc.cell == 1:
                    _bc, bw, _s = run_tick_block(blk, 1, lc.word)
                    nul[mask] += int(bw == lc.word)
                lc.tick()
    inside = [a for a, mn, op in refs if STATUS_LO <= a < STATUS_HI]
    print("  status writer %08x..%08x contains %d of the %d cell references"
          % (STATUS_LO, STATUS_HI, len(inside), len(refs)))
    print("  peace-status interleavings whose expiry is a NULL write: %d/49 ; war-status: %d/49"
          % (nul[0x2], nul[0x10]))
    gate("G4", inside == [] and nul[0x2] == 49 and nul[0x10] == 0,
         "no status write can reach the cell (0 of 11 refs inside the writer); a PEACE write "
         "clears 0x40 from the word and its lease still expires as a NULL write (49/49), while a "
         "WAR write keeps 0x40 (0x78 has bit 6) and its expiry is a real clear (0/49 null)")

    # ---- G5 TREATY ON: cleared by every 0x17 write, never restored by expiry --------------
    print("\nG5  0x800000 (TREATY ON) across the status masks and the expiry")
    masks = [0x1, 0x2, 0x4, 0x10, 0x8, 0x100, 0x1000]
    with17 = [m for m in masks if m & LADDER_BITS]
    cleared_n = 0
    for m in with17:
        lc = Lifecycle(TREATY_ON)
        lc.status(m)
        cleared_n += int(not lc.word & TREATY_ON)
    print("  masks carrying a 0x17 bit: %s -> TREATY ON cleared %d/%d"
          % (" ".join("0x%x" % m for m in with17), cleared_n, len(with17)))
    print("  0xbf & 0x800000 = 0x%x ; masks with no 0x17 bit keep it: %s"
          % (EXPIRE_BYTE & TREATY_ON,
             " ".join("0x%x" % m for m in masks if not m & LADDER_BITS)))
    lc = Lifecycle(TREATY_ON)
    lc.arm()
    for _t in range(50):
        lc.tick()
    print("  arm+50 from 0x800000 -> word 0x%x (TREATY ON %s)"
          % (lc.word, "SURVIVES" if lc.word & TREATY_ON else "gone"))
    gate("G5", cleared_n == len(with17) == 4 and EXPIRE_BYTE & TREATY_ON == 0
         and lc.word & TREATY_ON,
         "every mask carrying a 0x17 bit clears TREATY ON (4/4) while the ones without it keep "
         "it, and the expiry's byte mask cannot touch bit 23 - TREATY ON survives the lease's "
         "expiry untouched, because expiry is an AND, never an OR")

    # ---- G6 rivals FAIL on the printed numbers -------------------------------------------
    print("\nG6  rivals")
    # R1: a status write disarms the cell ("the cell counts peace-turns, so peace zeroes it")
    r1 = 0
    for st in range(1, 50):
        r1 += int(run_seq(0, ARM_CELL_VALUE, 50, status_at=st, status_mask=0x2,
                          status_clears_cell=True)
                  != run_lifecycle(0, ARM_CELL_VALUE, 50, status_at=st, status_mask=0x2))
    # R2: expiry also clears TREATY ON
    r2 = 0
    for c in range(1, 60):
        r2 += int(run_seq(SET_TREATY | TREATY_ON, c, c, expiry_clears_on=True)
                  != run_lifecycle(SET_TREATY | TREATY_ON, c, c))
    # R3: a re-arm only initialises an unarmed cell
    truth_trace = transcript()[0]
    lc = Lifecycle(0)
    lc.arm()
    r3 = 0
    for t in range(1, 121):
        w, c, _cl, _dg = run_seq(lc.word, lc.cell, 1, arm_at=30, no_rearm=True)
        lc.word, lc.cell = w, c
        r3 += int((w, c) != (truth_trace[t][2], truth_trace[t][3]))
    # R4: the countdown decrements before testing for zero
    r4 = 0
    for c in list(range(0, 4)) + [49, 50]:
        r4 += int(run_seq(SET_TREATY, c, 1, dec_all=True)
                  != run_lifecycle(SET_TREATY, c, 1))
    # R5: the arm value is 49, not 50
    r5 = 0
    for word, cell in ((0, 0), (0x8, 0), (0, 10)):
        r5 += int(run_seq(word, cell, 80, arm_at=1, arm_value=49)[2]
                  != run_lifecycle(word, cell, 80, arm_at=1)[2])
    # R6: the expiry clears the whole low byte instead of bit 6
    r6 = 0
    for c in range(1, 60):
        r6 += int(run_seq(SET_TREATY | 0x8 | 0x100, c, c, expiry_low_byte=True)
                  != run_lifecycle(SET_TREATY | 0x8 | 0x100, c, c))
    scores = [("a status write disarms the cell", r1),
              ("expiry also clears TREATY ON", r2),
              ("a re-arm only initialises an unarmed cell", r3),
              ("the countdown decrements before testing zero", r4),
              ("the arm value is 49, not 50", r5),
              ("expiry clears the whole low byte", r6)]
    for k, v in scores:
        print("  rival %-45s differs on %d configuration(s)" % (k, v))
    gate("G6", all(v > 0 for _k, v in scores),
         "all six rivals differ on the printed sweeps (min %d configurations); none can be the "
         "game's rule" % min(v for _k, v in scores))

    # ---- G7 pinned anchors ---------------------------------------------------------------
    print("\nG7  anchors")
    print("  block %s  arms %s  trace %s" % (d1, ad, td))
    gate("G7", d1 == d2 and d1 == ANCHOR and ad == ARM_DIGEST and td == TRACE_DIGEST,
         "the block digest reproduces on a SECOND decode of the same dump and every anchor is "
         "pinned (%s/%s/%s)" % (ANCHOR[:8], ARM_DIGEST[:8], TRACE_DIGEST[:8]))

    print("")
    ids = ["G%d" % i for i in range(8)]
    total = len([g for g in ids if g not in FAIL])
    code = "PASS B37: %d/%d gates  digest %s" % (total, len(ids), d1)
    if FAIL:
        code = "FAIL B37: %d/%d gates  red=%s  digest %s" % (total, len(ids), ",".join(FAIL), d1)
        print(code)
        return 1
    print(code)
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--pin" in argv:
        ins = load()
        print('ANCHOR = "%s"' % sha16(window(ins, TICK_LO, TICK_HI)))
        _a, rows = arm_table(ins)
        print('ARM_DIGEST = "%s"' % sha16(rows))
        print('TRACE_DIGEST = "%s"' % sha16(transcript()[0]))
        return 0
    return accept("--quiet" in argv)


if __name__ == "__main__":
    sys.exit(main())
