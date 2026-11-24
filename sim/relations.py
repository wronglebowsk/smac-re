"""sim.relations - rung B36: the FACTION-RELATIONS STATE MACHINE (transitions, not masks).

The 13 bits were named by M367/M368/M369/M370.  What was never executable is the thing the
game actually runs: the setter `FUN_00551a20` (530 B, 161 insns), which every diplomacy
action funnels through, and the same-state classifier inside `FUN_005076d0`
(0x507961..0x5079a7) that reads a word and says whether it is the state the caller wanted.

Both are extracted from the SAME .text dump the static milestones used, so this rung is
parity against a recorded artifact - zero box, zero /proc, zero gdb.

  writer contract (0x94d448, stride 0x82f dwords = (a*0x82f + b)*4, both directions)
  ------------------------------------------------------------------------------
  P  mask & 7        -> clear {0x10,0x40,0x8000,0x10000,0x100000} both ways; if a or b is the
                        human faction and the (a,b) word held 0x10, clear 0x7485b4 bit0
  U  mask & 1        -> mask |= 2      (pact IMPLIES treaty: the only upgrade in 781,429 insns)
  W  mask & 0x10     -> if the (a,b) word holds any of 1|2|4, zero the 0x94d5dc slot dwords;
                        mask |= 0x80000108 (bit31 | commlink | 0x100);
                        clear {1,2,4,0x80,0x400,0x800,0x10000,0x100000,0x1000000,0x4000000};
                        if human involved: 0x7485b4 |= 1 and call 0x447620(0xcc)
  L  mask & 0x17     -> clear 0x800000 both ways (the "lock/proposal" bit, name OPEN)
  O  words |= mask   (post-upgrade, post-war OR)
  R  human involved and mask & 0x1f and 0x7f82fc -> call 0x5e4afc (redraw)

Two READ-ONLY takeaways that only fall out of running it: the ladder bits ACCUMULATE
(truce then treaty leaves 0x6 - nothing clears the lower rung), so "the current relation" is
defined by the CLASSIFIER's precedence (1 then 2 then 4, ordered EQUALITY, M368's law), not
by mutual exclusion; and only the war write clears the ladder.  Bit 0x8 (commlink) and 0x100
SURVIVE war and peace alike - contact is not a relation state.

Commands:  python3 -u -m sim.relations            (acceptance)
           python3 -u -m sim.relations --pin      (print the anchors to pin)
           python3 -u -m sim.relations --quiet    (relay mode used by sim.selftest --b36)
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("B36_TEXT") or os.path.join(ROOT, "scratch/m574/text.txt")
EXE = os.environ.get("B36_EXE") or os.path.join(ROOT, "programs/terran.exe")

FN_START, FN_END = 0x551A20, 0x551C32          # FUN_00551a20: 530 bytes
CLS_START, CLS_END = 0x507975, 0x5079A7        # FUN_005076d0's same-state block
PAIR_STRIDE = 0x82F                            # dword stride, M365/M368

PACT, TREATY, TRUCE, COMMLINK, AT_WAR = 0x1, 0x2, 0x4, 0x8, 0x10
WAR_RECORD = 0x20          # INF: M366's "human-branch war record"
NAMES = {0x1: "PACT", 0x2: "TREATY", 0x4: "TRUCE", 0x8: "COMMLINK", 0x10: "AT_WAR",
         0x20: "WAR_RECORD?", 0x40: "?", 0x100: "0x100", 0x8000: "?", 0x10000: "?",
         0x100000: "?", 0x800000: "LOCK?", 0x80000000: "HIGH"}
LADDER = (PACT, TREATY, TRUCE)

# Immediates of FUN_00551a20 - the sim uses these LITERALS; G1 asserts each one equals the
# instruction byte the dump carries, so a typo here cannot survive a run.
PEACE_CLEAR = 0xEE7FAF | 0xFF000000        # 0xffee7faf
WAR_CLEAR = 0xFAEEF378
UNLOCK_CLEAR = 0xFF7FFFFF
UPGRADE = 0x2
WAR_SET = 0x80000108

ACTIONS = {"contact": COMMLINK, "truce": TRUCE, "treaty": TREATY, "pact": PACT,
           "vendetta": AT_WAR}
POSTER = {TRUCE: "ENEMYTRUCE", TREATY: "ENEMYTREATY", PACT: None}
POSTER_SITES = [0x553C41, 0x553F10, 0x554165]   # the three peace writers in FUN_005537d0
LADDER_MASK = PACT | TREATY | TRUCE

# Every op of the writer with its address - the independent expectation of the parse: six `and`
# clears, two `or ebx` mask upgrades (0x2 and 0x80000108, neither stores) and two `or edx,ebx`
# writes.  The six ands and two writes are the 8 dword stores (one per op, one op per direction).
OPS_PINNED = [(0x551A88, "and", 0xEE7FAF | 0xFF000000), (0x551AAF, "and", 0xEE7FAF | 0xFF000000),
              (0x551ABC, "mask_or", 0x2), (0x551B11, "mask_or", 0x80000108),
              (0x551B17, "and", 0xFAEEF378), (0x551B42, "and", 0xFAEEF378),
              (0x551B98, "and", 0xFF7FFFFF), (0x551BBF, "and", 0xFF7FFFFF),
              (0x551BE6, "or_eff", None), (0x551C09, "or_eff", None)]

# Pinned on the first real run (G10 asserts a fresh decode still reproduces them).
ANCHOR = "b20f5818dee2d861"
TRANSCRIPT_DIGEST = "ac8c2caad0d71d55"

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


def bits(x, width=32):
    """Every set bit of x, low first.  Applied to ~imm this prints what an AND CLEARS."""
    return [1 << b for b in range(width) if x >> b & 1]


def load(path=TEXT):
    out = []
    with open(path, errors="replace") as fh:
        for ln in fh:
            m = INSN.match(ln)
            if m:
                out.append([int(m.group(1), 16), m.group(2), (m.group(3) or "").strip()])
    return out


def window(ins, lo, hi):
    return [r for r in ins if lo <= r[0] < hi]


def pe_sections(path=EXE):
    """[(name, va, vsize, raw_ptr, raw_size)] and the image base, from the PE header itself -
    never the `vma-0x400000` assumption."""
    import struct
    with open(path, "rb") as fh:
        data = fh.read(0x400)
    e = struct.unpack_from("<I", data, 0x3C)[0]
    if data[e:e + 4] != b"PE\0\0":
        raise RuntimeError("not a PE: %s" % path)
    nsec = struct.unpack_from("<H", data, e + 6)[0]
    optsz = struct.unpack_from("<H", data, e + 20)[0]
    base = struct.unpack_from("<I", data, e + 24 + 0x1C)[0]
    secs = []
    with open(path, "rb") as fh:
        fh.seek(e + 24 + optsz)
        for _i in range(nsec):
            h = fh.read(40)
            vsize, va, rawsize, rawptr = struct.unpack_from("<IIII", h, 8)
            secs.append((h[:8].rstrip(b"\0").decode("latin-1"), va, vsize, rawptr, rawsize))
    return secs, base


def cstr_at(vma, secs, base, path=EXE):
    """The NUL-terminated C string at absolute address `vma`, via its section's raw pointer."""
    rva = vma - base
    for name, va, vsize, rawptr, rawsize in secs:
        if va <= rva < va + max(vsize, rawsize) and rva - va < rawsize:
            with open(path, "rb") as fh:
                fh.seek(rawptr + (rva - va))
                return fh.read(64).split(b"\0")[0].decode("latin-1")
    return None


def flatten(prog):
    """Every op in ADDRESS order with its block predicate, no block grouping."""
    flat = []
    for blk in prog:
        for kind, imm, a in blk["ops"]:
            flat.append((a, blk["pred"], kind, imm))
    return sorted(flat)


# --------------------------------------------------------------------------- writer program
def extract_program(win):
    """The WORD-relevant program of FUN_00551a20, in ADDRESS ORDER, keyed by the `test bl,imm`
    that gates it.  Each block's ops are its `or ebx,imm` (mask upgrade), `and edx,imm` (clear)
    and `or edx,ebx` (write the effective mask) in encounter order; the predicate is evaluated
    on the CURRENT ebx low byte, exactly as `test bl` does."""
    prog, cur = [], None
    stores = 0
    for a, mn, ops in win:
        if mn == "test" and re.match(r"^bl,0x[0-9a-f]+$", ops):
            cur = {"at": a, "pred": int(ops.split(",")[1], 16), "ops": []}
            prog.append(cur)
            continue
        if cur is None:
            continue
        if mn == "or" and re.match(r"^ebx,0x[0-9a-f]+$", ops):
            cur["ops"].append(("mask_or", int(ops.split(",")[1], 16), a))
        elif mn == "and" and re.match(r"^edx,0x[0-9a-f]+$", ops):
            cur["ops"].append(("and", int(ops.split(",")[1], 16), a))
        elif mn == "or" and ops == "edx,ebx":
            cur["ops"].append(("or_eff", None, a))
        elif mn == "mov" and re.match(r"^DWORD PTR \[.+\],edx$", ops):
            stores += 1
    # The tail OR is UNCONDITIONAL: it begins at the `je` target of the last predicated block
    # that is not itself a `test bl` block (0x551bc7, the join the 0x17 clear jumps over).
    by = {a: (mn, ops) for a, mn, ops in win}
    starts = set(b["at"] for b in prog)
    order = sorted(by)
    tail = None
    for b in prog:
        after = [a for a in order if a > b["at"] and by[a][0] in ("je", "jne")]
        if not after:
            continue
        t = int(by[after[0]][1], 16)
        if t not in starts and t <= win[-1][0]:
            tail = t if tail is None else min(tail, t)
    if tail is not None:
        tailblk = {"at": tail, "pred": None, "ops": []}
        for b in prog:
            tailblk["ops"] += [o for o in b["ops"] if o[2] >= tail]
            b["ops"] = [o for o in b["ops"] if o[2] < tail]
        prog.append(tailblk)
    return prog, stores


def run_program(prog, wab, wba, mask):
    """Execute the extracted program on a symmetric pair.  Returns (post_ab, post_ba, eff)."""
    ebx = mask
    for blk in prog:
        if blk["pred"] is not None and not ((ebx & 0xFF) & blk["pred"]):
            continue
        for kind, imm, _a in blk["ops"]:
            if kind == "mask_or":
                ebx |= imm
            elif kind == "and":
                wab &= imm
                wba &= imm
            elif kind == "or_eff":
                wab |= ebx
                wba |= ebx
    return wab, wba, ebx


def flat_exec(flat, wab, wba, mask):
    """The same ops executed from the FLAT address-ordered list - no block segmentation, so a
    mis-grouped extractor cannot hide behind its own grouping."""
    ebx = mask
    for _a, pred, kind, imm in flat:
        if pred is not None and not ((ebx & 0xFF) & pred):
            continue
        if kind == "mask_or":
            ebx |= imm
        elif kind == "and":
            wab &= imm
            wba &= imm
        elif kind == "or_eff":
            wab |= ebx
            wba |= ebx
    return wab, wba


# --------------------------------------------------------------------------- the state machine
class Relations(object):
    """The R1 relations state: one word per ordered faction pair, a slot word per pair
    (0x94d5dc), and the two global flags the setter touches (0x7485b4, 0x7f82fc)."""

    def __init__(self, n=13, human=0):
        self.n = n
        self.human = human
        self.w = {}
        self.slot = {}
        self.war_visible = 0      # 0x7485b4 bit0
        self.war_flag = 0         # 0x7485b4 bit1 - set by the war write (OR 1)
        self.refresh_gate = 1     # 0x7f82fc
        self.refresh_calls = 0    # 0x5e4afc
        self.cc_calls = 0         # 0x447620(0xcc)
        self.log = []

    def get(self, a, b):
        return self.w.get((a, b), 0)

    def set(self, a, b, mask):
        """FUN_00551a20's transition, written independently of extract_program()."""
        wab, wba = self.get(a, b), self.get(b, a)
        eff = mask
        ev = {"peace_pre": False, "upgrade": False, "war": False, "unlock": False,
              "slots_zeroed": False, "war_visible_cleared": False}
        if mask & (PACT | TREATY | TRUCE):
            ev["peace_pre"] = True
            if self.human in (a, b) and (wab & AT_WAR):
                self.war_visible &= ~1
                ev["war_visible_cleared"] = True
            wab &= PEACE_CLEAR
            wba &= PEACE_CLEAR
        if mask & PACT:
            eff |= UPGRADE
            ev["upgrade"] = True
        if mask & AT_WAR:
            ev["war"] = True
            if wab & (PACT | TREATY | TRUCE):
                self.slot[(a, b)] = 0
                self.slot[(b, a)] = 0
                ev["slots_zeroed"] = True
            eff |= WAR_SET
            wab &= WAR_CLEAR
            wba &= WAR_CLEAR
            if self.human in (a, b):
                self.war_flag |= 1
                self.cc_calls += 1
        if eff & 0x17:
            ev["unlock"] = True
            wab &= UNLOCK_CLEAR
            wba &= UNLOCK_CLEAR
        wab |= eff
        wba |= eff
        if self.human in (a, b) and (eff & 0x1F) and self.refresh_gate:
            self.refresh_calls += 1
        self.w[(a, b)], self.w[(b, a)] = wab, wba
        self.log.append((a, b, mask, wab, ev))
        return wab

    # --- classifiers and labels -----------------------------------------------------------
    @staticmethod
    def classify(cur, want):
        """FUN_005076d0 @0x507975..0x50798f: ordered EQUALITY on 1, 2, 4.

        The FIRST ladder bit set in `cur` (precedence 1 then 2 then 4) decides; the caller's
        `want` byte matches only if it carries that same bit.  A word with no ladder bit at
        all is a no-opinion (True).  Bits outside 1|2|4 are invisible to it."""
        cl = cur & 0xFF
        for bit in LADDER:
            if cl & bit:
                return bool(want & bit)
        return True

    @staticmethod
    def ladder(cur):
        """The rung the classifier would name, by its own precedence (None = unaligned)."""
        for bit in LADDER:
            if cur & bit:
                return bit
        return None

    @staticmethod
    def poster(mask):
        return POSTER.get(mask)

    def act(self, a, b, name):
        return self.set(a, b, ACTIONS[name])


def program_classify(cwin, cur, want):
    """The classifier WALKED off the dump's own chain (0x507975..0x5079a7), not a copy of the
    sim's rule: a tiny interpreter over `test`/`je`/`jne`/`jmp` that stops at the match block
    (0x5079a1) or at the `mov DWORD PTR [ebp-0x8],0x1` mismatch store (0x50799a)."""
    by = {a: (mn, ops) for a, mn, ops in cwin}
    order = sorted(by)
    nxt = {a: order[i + 1] for i, a in enumerate(order[:-1])}
    pc = CLS_START
    zero = 0
    for _step in range(64):
        mn, ops = by[pc]
        if mn == "test":
            imm = int(ops.split(",")[1], 16) if re.search(r",0x[0-9a-f]+$", ops) else 0
            if ops.startswith("cl,"):
                zero = ((cur & 0xFF) & imm) == 0
            elif "ebp-0xc" in ops:
                zero = ((want & 0xFF) & imm) == 0
            else:
                zero = True
            pc = nxt[pc]
        elif mn in ("je", "jne"):
            take = zero if mn == "je" else (not zero)
            pc = int(ops, 16) if take else nxt[pc]
        elif mn == "jmp":
            pc = int(ops, 16)
        elif mn == "mov" and ops.startswith("DWORD PTR [ebp-0x8],0x1"):
            return False
        elif mn == "inc":
            return True
        else:
            pc = nxt[pc]
    raise RuntimeError("classifier chain did not terminate from 0x%x" % CLS_START)


# --------------------------------------------------------------------------- transcript
def transcript():
    """A 16-event diplomatic timeline between three factions, authored to exercise every
    transition the writer can make: contact, the ladder accumulating, a war that clears it,
    peace after war, and a second pair that must stay independent."""
    T = [
        (1, 2, "contact"), (1, 2, "truce"), (1, 2, "treaty"), (1, 2, "pact"),
        (1, 3, "contact"), (1, 3, "pact"), (2, 3, "contact"), (2, 3, "truce"),
        (1, 2, "vendetta"), (1, 2, "vendetta"), (1, 2, "truce"), (1, 2, "treaty"),
        (1, 3, "vendetta"), (1, 3, "contact"), (2, 3, "pact"), (1, 2, "pact"),
    ]
    return T


# --------------------------------------------------------------------------- acceptance
def accept(quiet=False):
    ins = load()
    win = window(ins, FN_START, FN_END)
    prog, stores = extract_program(win)

    # ---- G0 decode anchors -------------------------------------------------------------
    print("dumping FUN_00551a20 @0x%x..0x%x: %d insns, %d dword stores into 0x94d448"
          % (FN_START, FN_END, len(win), stores))
    anchors = [
        (0x551A88, "and", "edx,0xffee7faf"),
        (0x551AB7, "test", "bl,0x1"),
        (0x551ABC, "or", "ebx,0x2"),
        (0x551ABF, "test", "bl,0x10"),
        (0x551B11, "or", "ebx,0x80000108"),
        (0x551B17, "and", "edx,0xfaeef378"),
        (0x551B74, "test", "bl,0x17"),
        (0x551B98, "and", "edx,0xff7fffff"),
        (0x551BE6, "or", "edx,ebx"),
    ]
    by = {a: (mn, ops) for a, mn, ops in win}
    print("  anchor instructions: %d" % len(anchors))
    for a, mn, ops in anchors:
        print("    %08x %-6s %s  %s" % (a, by.get(a, ("?", "?"))[0], by.get(a, ("?", "?"))[1],
                                        "ok" if by.get(a) == (mn, ops) else "MISMATCH"))
    win_d = sha16(win)
    win2_d = sha16(window(load(), FN_START, FN_END))
    stored_ops = sum(1 for b in prog for k, _i, _a in b["ops"] if k in ("and", "or_eff"))
    print("  stores: %d measured, %d stored ops (and/or_eff) - one store per op, the two mask "
          "upgrades store nothing" % (stores, stored_ops))
    gate("G0", len(win) == 161 and stores == 8 and stores == stored_ops
         and all(by.get(a) == (mn, ops) for a, mn, ops in anchors) and win_d == win2_d,
         "161 insns, %d stores == the 8 stored ops (one per direction), 9/9 anchors byte-exact, "
         "window digest %s twice (%s)" % (stores, win_d, win_d == win2_d))

    # ---- G1 the program, with its clear sets COMPUTED from the immediates ----------------
    print("extracted rule program: %d `test bl` blocks" % len(prog))
    for blk in prog:
        ops = ", ".join("%s%s" % (k, "" if i is None else "0x%x" % i) for k, i, _a in blk["ops"])
        print("  @%08x pred=%-8s ops: %s"
              % (blk["at"], "ANY" if blk["pred"] is None else "0x%x" % blk["pred"], ops or "(none)"))
    clears = []
    for blk in prog:
        for kind, imm, _a in blk["ops"]:
            if kind == "and" and (not clears or clears[-1] != imm):
                clears.append(imm)
    print("  AND clears (from ~imm):")
    for imm in clears:
        print("    0x%08x clears %s" % (imm, ", ".join("0x%x" % b for b in bits(~imm & 0xFFFFFFFF))))
    preds = [b["pred"] for b in prog]
    flat = flatten(prog)
    tail = prog[-1]
    print("  structure: %d blocks, preds %s, tail @%08x pred=%s with %d or_eff ops"
          % (len(prog), ["ANY" if p is None else "0x%x" % p for p in preds], tail["at"],
             tail["pred"], len([o for o in tail["ops"] if o[0] == "or_eff"])))
    got_ops = [(a, k, i) for a, _p, k, i in flat]
    ops_ok = got_ops == OPS_PINNED
    print("  ops vs the pinned address table: %d/%d match"
          % (sum(1 for g, w in zip(got_ops, OPS_PINNED) if g == w), len(OPS_PINNED)))
    gate("G1", preds == [0x7, 0x1, 0x10, 0x17, 0x1F, None] and tail["at"] == 0x551BC7
         and len([o for o in tail["ops"] if o[0] == "or_eff"]) == 2 and ops_ok
         and clears == [PEACE_CLEAR, WAR_CLEAR, UNLOCK_CLEAR]
         and set(bits(~PEACE_CLEAR & 0xFFFFFFFF)) == {0x10, 0x40, 0x8000, 0x10000, 0x100000}
         and set(bits(~WAR_CLEAR & 0xFFFFFFFF)) >= {PACT, TREATY, TRUCE}
         and bits(~UNLOCK_CLEAR & 0xFFFFFFFF) == [0x800000],
         "SIX blocks: predicates 0x7/0x1/0x10/0x17/0x1f then an UNCONDITIONAL tail @0x551bc7; "
         "the flat op list equals the pinned 10-entry address table; peace clears exactly the 5 "
         "war bits; war clears the ladder; the 0x17 block clears 0x800000")

    # ---- G2 parity: sim vs the extracted program over the mask lattice -------------------
    states = [0x0, 0x1, 0x2, 0x4, 0x3, 0x6, 0x7, 0x8, 0x18, 0x20, 0x108,
              0x80000118, 0x80001000, 0x10000040, 0x800000, 0xFFFFFFFF]
    low_bits = [0x1, 0x2, 0x4, 0x8, 0x10, 0x20, 0x40, 0x80]
    highs = [0x0, 0x800000, 0x80000000, 0x100, 0x8000, 0x10000, 0x100000,
             0x80000108, 0x1000000, 0x4000000]
    masks = []
    for hi in highs:
        for sub in range(256):
            m = hi
            for i, bit in enumerate(low_bits):
                if sub >> i & 1:
                    m |= bit
            masks.append(m)
    pairs = bad = 0
    for w0 in states:
        for m in masks:
            pab, pba, _eff = run_program(prog, w0, w0, m)
            s = Relations()
            s.w[(0, 1)] = s.w[(1, 0)] = w0
            sab = s.set(0, 1, m)
            pairs += 1
            if (sab, s.get(1, 0)) != (pab, pba):
                bad += 1
    bad_flat = 0
    for w0 in states:
        for m in masks[:512]:
            fab, fba = flat_exec(flat, w0, w0, m)
            pab, pba, _eff = run_program(prog, w0, w0, m)
            if (fab, fba) != (pab, pba):
                bad_flat += 1
    print("parity sweep: %d states x %d masks = %d pairs, %d disagreements" % (len(states), len(masks), pairs, bad))
    print("flat executor (no block grouping): %d pairs, %d disagreements with the block executor"
          % (len(states) * 512, bad_flat))
    gate("G2", pairs == len(states) * len(masks) and bad == 0 and bad_flat == 0,
         "the hand-written setter equals the dump-extracted program on all %d (state,mask) pairs, "
         "and the FLAT address-ordered executor reproduces the block executor on %d more"
         % (pairs, len(states) * 512))

    # ---- G3 the named transition laws ---------------------------------------------------
    def fresh(w0=0):
        s = Relations()
        s.w[(0, 1)] = s.w[(1, 0)] = w0
        return s
    laws = []
    for pre, m, want in [(0, PACT, 0x3), (0, TREATY, 0x2), (0, TRUCE, 0x4), (0, COMMLINK, 0x8),
                         (PACT | TREATY | TRUCE | COMMLINK, AT_WAR, 0x80000118),
                         (0x80000118, TRUCE, 0x8000010C), (0, PACT | AT_WAR, 0x8000011B)]:
        # the EXPECTED value comes from the DUMP program; the sim is compared to it separately by G2
        pab, _pba, _e = run_program(prog, pre, pre, m)
        got = fresh(pre).set(0, 1, m)
        laws.append(("pre 0x%x mask 0x%x" % (pre, m), got, pab, want,
                     (pre & LADDER_MASK) != 0, (m & LADDER_MASK) == 0 and bool(m & AT_WAR)))
    for name, got, prog_want, lit, pre_ladder, war_only in laws:
        print("  %-24s -> 0x%08x (program 0x%08x, literal 0x%08x) %s"
              % (name, got, prog_want, lit, "ok" if got == prog_want == lit else "DIFF"))
    in_ladder = [r for r in laws if r[4]]
    print("  pre-states carrying a ladder bit: %d; war-only masks: %d"
          % (len(in_ladder), len([r for r in laws if r[5]])))
    gate("G3", len(in_ladder) >= 1 and len([r for r in laws if r[5]]) >= 1
         and all(g == p == w for _n, g, p, w, _pl, _wo in laws),
         "every named transition equals BOTH the dump program and its pinned literal; the "
         "war-on-a-ladder-word law is measured on a pre-state that carries 0x7|commlink with a "
         "war-only mask, so the clear is what produces the result")

    # ---- G4 transcript replay: sim vs program at EVERY step -----------------------------
    T = transcript()
    print("transcript: %d events" % len(T))
    s = Relations(human=0)
    rows = []
    oksteps = 0
    for i, (a, b, name) in enumerate(T):
        pre = s.get(a, b)
        post = s.act(a, b, name)
        pair = (pre, ACTIONS[name], post)
        pab, pba, _eff = run_program(prog, pre, pre, ACTIONS[name])
        good = post == pab == s.get(b, a) == pba
        oksteps += good
        rows.append(pair)
        print("  %2d (%d,%d) %-8s 0x%08x --0x%02x--> 0x%08x  ladder=%-6s %s"
              % (i, a, b, name, pre, ACTIONS[name], post,
                 NAMES.get(s.ladder(post), "-"), "ok" if good else "DIFF"))
    td = sha16(rows)
    gate("G4", oksteps == len(T),
         "%d/%d steps agree with the extracted program and are symmetric; transcript digest %s"
         % (oksteps, len(T), td))

    # ---- G5 invariants over every step of the sweep and the transcript ------------------
    viol = []
    seen = war_class = 0
    allw = [(w0, m) for w0 in states for m in masks] + [(r[0], r[1]) for r in rows]
    for w0, m in allw:
        s2 = Relations()
        s2.w[(0, 1)] = s2.w[(1, 0)] = w0
        post = s2.set(0, 1, m)
        seen += 1
        war_only = bool(m & AT_WAR) and not (m & LADDER_MASK)
        war_class += war_only
        if (m & PACT) and (post & PACT) and not post & TREATY:
            viol.append(("pact write without the treaty upgrade", w0, m, post))
        if war_only and (post & LADDER_MASK):
            viol.append(("war-only write left a ladder bit", w0, m, post))
        if s2.get(1, 0) != post:
            viol.append(("asymmetric", w0, m, post))
        again = s2.set(0, 1, m)
        if again != post:
            viol.append(("not idempotent", w0, m, again))
    print("invariants: %d transitions checked (%d of them war-only: 0x10 set, no ladder bit in "
          "the mask), %d violations" % (seen, war_class, len(viol)))
    for v in viol[:6]:
        print("   %s: pre 0x%08x mask 0x%x -> 0x%08x" % v)
    gate("G5", seen > 30000 and war_class > 2000 and not viol,
         "pact=>treaty keyed on the write, the %d war-only writes (mask carries 0x10 and no "
         "ladder bit) all leave the ladder empty, and every one of the %d transitions is "
         "symmetric and idempotent" % (war_class, seen))

    # ---- G6 classifier parity: dump chain vs sim.classify -------------------------------
    cwin = window(ins, CLS_START, CLS_END)
    tests = [(a, ops) for a, mn, ops in cwin if mn == "test" and ops.startswith("cl,")]
    wants = [(a, ops) for a, mn, ops in cwin if mn == "test" and ops.startswith("BYTE PTR [ebp-0xc],")]
    print("classifier window @0x%x..0x%x: %d insns incl. the mismatch store and the scored inc, "
          "ladder tests %s, want tests %s"
          % (CLS_START, CLS_END, len(cwin), [o.split(",")[1] for _a, o in tests],
             [o.split(",")[1] for _a, o in wants]))
    cb = cs = 0
    inter = []
    for cur in range(256):
        for want in range(256):
            p = program_classify(cwin, cur, want)
            q = Relations.classify(cur, want)
            cb += 1
            if p != q:
                cs += 1
    for cur, want in [(0x3, 0x2), (0x3, 0x1), (0x6, 0x2), (0x6, 0x4), (0x0, 0x1), (0x8, 0x0)]:
        inter.append((cur, want, Relations.classify(cur, want), Relations.ladder(cur)))
    for cur, want, r, ld in inter:
        print("  cur 0x%02x want 0x%02x -> %-5s (ladder rung %s)" % (cur, want, r, NAMES.get(ld, "-")))
    gate("G6", len(cwin) == 16 and len(tests) == 3 and len(wants) == 3 and cs == 0 and cb == 65536
         and Relations.classify(0x3, TREATY) is False and Relations.classify(0x3, PACT) is True
         and Relations.classify(0x6, TRUCE) is False,
         "3 ladder tests on 1/2/4; sim.classify == the dump chain on %d (cur,want) pairs; "
         "pact+treaty does NOT satisfy a want of treaty (ordered EQUALITY, M368's law)" % cb)

    # ---- G7 the action layer and the poster keys, decoded ------------------------------
    sc = {a: (mn, ops) for a, mn, ops in ins if a in POSTER_SITES}
    pushes = {}
    for site in POSTER_SITES:
        idx = next(i for i, r in enumerate(ins) if r[0] == site)
        back = [int(r[2], 16) for r in ins[max(0, idx - 4):idx]
                if r[1] == "push" and re.match(r"^0x[0-9a-f]+$", r[2])]
        pushes[site] = back
    keys = {}
    for site, pl in pushes.items():
        mask = pl[-1]
        key = None
        j = next(i for i, r in enumerate(ins) if r[0] == site)
        blk = ins[max(0, j - 10):j]
        if any(r[1] == "call" and r[2] == "0x483470" for r in blk):
            key = next((int(q[2], 16) for q in reversed(blk)
                        if q[1] == "push" and re.match(r"^0x[0-9a-f]+$", q[2])
                        and int(q[2], 16) > 0x10000), None)
        keys[site] = (mask, key)
    # the poster KEY operand is a VA: resolve it through the PE section table and read the bytes
    secs, base = pe_sections()
    print("PE: image base 0x%x, %d sections (first %s @0x%x)"
          % (base, len(secs), secs[0][0], secs[0][1]))
    texts = {}
    for site in POSTER_SITES:
        mask, key = keys[site]
        texts[site] = cstr_at(key, secs, base) if key else None
    print("peace-host sites: %s" % ", ".join(
        "%08x mask=0x%x key=%s text=%s" % (s, keys[s][0],
                                          "0x%x" % keys[s][1] if keys[s][1] else "none",
                                          repr(texts[s]))
        for s in POSTER_SITES))
    want_pairs = {TRUCE: 0x691144, TREATY: 0x691150, PACT: None}
    okq = all(keys[s] == (m, want_pairs[m]) for s, m in zip(POSTER_SITES, [TRUCE, TREATY, PACT]))
    labels_ok = (POSTER[TRUCE] == texts[POSTER_SITES[0]] == "ENEMYTRUCE"
                 and POSTER[TREATY] == texts[POSTER_SITES[1]] == "ENEMYTREATY"
                 and POSTER[PACT] is None and texts[POSTER_SITES[2]] is None)
    s3 = Relations()
    words = [s3.act(0, 1, n) for n in ("pact", "treaty", "truce", "vendetta", "contact")]
    print("action layer words: %s" % ", ".join("0x%x" % w for w in words))
    gate("G7", okq and labels_ok and words[0] == 0x3 and words[3] == 0x80000118,
         "mask->poster at 0x553c41/0x553f10/0x554165 = (4,0x691144)/(2,0x691150)/(1,none), and the "
         "BYTES at those VAs (resolved through the PE table, not vma-0x400000) read ENEMYTRUCE / "
         "ENEMYTREATY / nothing; pact acts as 0x3, vendetta clears to 0x80000118")

    # ---- G8 rivals FAIL on the printed numbers ----------------------------------------
    def rival_words(kind, w0, m):
        eff = m | (UPGRADE if (kind != "no_imply" and m & PACT) else 0)
        if kind == "no_imply":
            return w0 | m, w0 | m
        if kind == "replace":
            return eff, eff
        if kind == "war_plain":
            return w0 | eff, w0 | eff
        if kind == "order_swapped":     # OR first, then the clears: they eat the new bits
            w = w0 | eff
            if eff & 0x7:
                w &= PEACE_CLEAR
            if eff & 0x10:
                w &= WAR_CLEAR
            return w, w
        return w0, w0
    rivals = [("independent flags (no pact=>treaty)", "no_imply"),
              ("a set REPLACES the word", "replace"),
              ("war is just another OR bit", "war_plain"),
              ("the clears run AFTER the OR", "order_swapped")]
    rscore = {}
    for label, kind in rivals:
        diff = 0
        for w0 in states:
            for m in masks[:256]:
                pab, _pba, _e = run_program(prog, w0, w0, m)
                r1, _ = rival_words(kind, w0, m)
                if r1 != pab:
                    diff += 1
        rscore[label] = diff
        print("  rival %-38s differs on %5d / %d cases" % (label, diff, len(states) * 256))
    rk = 0
    for cur in range(256):
        for want in range(256):
            rank = None
            for bit in LADDER:
                if want & bit:
                    rank = bit
                    break
            if rank is not None:
                got = bool(cur & rank)
                if got != Relations.classify(cur, want):
                    rk += 1
    print("  rival %-38s differs on %5d / 65536 (cur,want) pairs" % ("classifier by numeric rank", rk))
    gate("G8", all(v > 0 for v in rscore.values()) and rk > 0,
         "all four writer rivals and the rank rival differ on the printed sweep "
         "(min %d); none can be the game's rule" % min(list(rscore.values()) + [rk]))

    # ---- G9 pinned anchors -------------------------------------------------------------
    print("anchors: window %s, transcript %s" % (win_d, td))
    pin_ok = (ANCHOR == "PIN") or (ANCHOR == win_d and TRANSCRIPT_DIGEST == td)
    gate("G9", pin_ok and len(win) == 161,
         "window digest %s and transcript digest %s reproduced on a second decode%s"
         % (win_d, td, "" if ANCHOR != "PIN" else " (PIN)"))

    print("")
    ids = ("G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9")
    total = len([g for g in ids if g not in FAIL])
    code = "PASS B36: %d/%d gates  digest %s" % (total, len(ids), win_d)
    if FAIL:
        code = "FAIL B36: %d/%d gates  red=%s  digest %s" % (total, len(ids), ",".join(FAIL), win_d)
        print(code)
        return 1
    print(code)
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--pin" in argv:
        ins = load()
        win = window(ins, FN_START, FN_END)
        s = Relations()
        rows = []
        for a, b, name in transcript():
            rows.append((s.get(a, b), ACTIONS[name], s.act(a, b, name)))
        print('ANCHOR = "%s"' % sha16(win))
        print('TRANSCRIPT_DIGEST = "%s"' % sha16(rows))
        return 0
    return accept("--quiet" in argv)


if __name__ == "__main__":
    sys.exit(main())
