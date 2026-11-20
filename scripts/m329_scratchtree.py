#!/usr/bin/env python3
"""M329 - pick (viii): NAME FUN_0041a8f0 and the ds:0x99aa38 scratch tree behind it.

Footing it stands on (re-measured here where cited, never re-derived):
  * M178/M179 (s174, `docs/named-archive-m89-m221.md:414-424`): the 0x41a9xx block of
    FUN_0041a8f0 is a 19-bit pack/unpack through the staging dword ds:0x99aa38; `and
    ecx,0xf000000` (0x41abdc) keeps bits 24-27; the rebuilt dword is published to
    [fac*8380+0x94d600] at 0x41ad94; ds:0x99aa38 is field +0x1c of the 65-B record at
    ds:0x99aa1c; `call 0x6267a5` is the tagged save writer and "GOVOPTIONS = FUN_0041a8f0".
  * M321 (s297, `NAMED ## M321`, `evidence/m321_memo_owners.txt:47-81`): the field is
    base_array+0x38 (fold 304*idx + 0x95da10); bit 6's only OR-setter image-wide is 0x41ac34
    inside this tree; FUN_0041a8f0 is one of the 3 "arrival" sites; 47 whole-dword stores to
    +0x38 have untraced SOURCES.
  * s109/s110 + skill `references/production-queue.md:305,613,644`: the queue widget is the
    static BSS object 0x6a9480; `[+0x3ff3c]` = the index the pane SHOWS, `[+0x3ff5c]` = the
    cursor row.
  * `docs/field-atlas-faction.md` header: the per-faction block is 8,380 B at 0x94d104 and the
    folded `[reg*4+0x94dXXX]` idiom carries reg = f*2095.
  * M222 (`docs/sessions/sessions-186-186.md:12`) / M175: ds:0x91b5b4 = the current faction.

STATIC, ZERO BOX. Everything is COMPUTED from scratch/m574/text.txt (objdump .text, with the
raw encoding bytes) + ghidra_out/index.csv (function bounds) + the PE section table of
programs/terran.exe read as data (the exe is never run). Tables print FIRST, then the gates
assert the numbers just printed. Every gate names its mutant in scripts/m329_mutate.py.

  python3 -u scripts/m329_scratchtree.py
"""
import hashlib
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M329_TEXT", os.path.join(REPO, "scratch", "m574", "text.txt"))
IDX = os.environ.get("M329_INDEX", os.path.join(REPO, "ghidra_out", "index.csv"))
EXE = os.environ.get("M329_EXE", os.path.join(REPO, "programs", "terran.exe"))
EV = os.environ.get("M329_EV", REPO)

FN = 0x41A8F0
SEL = 0x99AA38            # the scratch / staging dword
FIELD = 0x94D600          # the published per-faction dword
BLOKBASE = 0x94D104       # faction block base (atlas header)
STRIDE = 8380             # per-faction block size (atlas header) - an INDEPENDENT constant
WIDGET = 0x6A9480         # queue-widget singleton (s109/s110)
SHOW = 0x3FF3C            # widget: the index the pane SHOWS
CURSOR = 0x3FF5C          # widget: the cursor row
BARRAY = 0x95DA10         # 304-B records (NAMED ## M321)
BSTRIDE = 304             # its record size (NAMED ## M321; unit stride is 52 - M327)
UNITSTRIDE = 52
CURFACTION = 0x91B5B4     # ds: current faction (M222/M175)
OBSERVE = 0x985AE8        # ds: bit 7 = "look at another faction's base" escape
TAGWRITER = 0x6267A5      # the tagged save writer (M179)
CTXOPEN = 0x626634        # the save-band context opener (M172/M185)
GONAME = 0x6899EC         # "GOVOPTIONS" in the exe name table (M179)
BANDREC = 0x99AA1C        # the 65-B staging record whose +0x1c is SEL (M179)
TAGSIZE = 0x41            # 65 B
ARRIVE = 0x40             # M321's bit 6 of [rec+0x38]
SPILLSLOT = "[ebp-0x8]"   # the frame slot the thiscall object is spilled to

# ---- pins: measured in this round from the objdump windows (a mutant reddens them) ----
PIN_CALLS = {0x41E3BD, 0x49B306, 0x4A9E0E, 0x5120D0}
PIN_OWNERS = {"FUN_0041e160", "FUN_0049af50", "FUN_004a99e0", "FUN_00512020"}
PIN_SHOW_READS = 3
PIN_STORES = 20
PIN_ZEROSTORE = 0x41A9B7
PIN_FIRSTLEG_STORE = 0x41A9D2
PIN_LEGS = 19
PIN_CHAINS = 3
PIN_SELREADS = 19
PIN_PUBLISH = 0x41AD94
PIN_ARRIVAL = 0x41ADE4
PIN_XORTRIO = 0x41ADEA
PIN_PUBMASK = 0x0F000000
PIN_CONSTS = {0xDFBE41, 0xC0DFBE41}
PIN_WRITERS = 3
PIN_READERS = 5
PIN_CREATOR = 0x4E494C          # base-creator leg that reads FIELD (M282/s98)
PIN_REFUSES = 3
PIN_FIELD_OFF = FIELD - BLOKBASE  # 0x4fc
PIN = os.environ.get("M329_PIN", "757e40a7ed04abda")

REGS = ("eax", "ecx", "edx", "ebx", "esp", "ebp", "esi", "edi",
        "ax", "cx", "dx", "bx", "si", "di", "bp", "sp",
        "al", "cl", "dl", "bl", "ah", "ch", "dh", "bh")

out = []
G = []


def W(s=""):
    out.append(s)


def norm(t):
    return re.sub(r"[ \t]+", " ", t).strip().lower()


def gate(gid, cond, detail):
    G.append((gid, bool(cond), detail))
    W("%s %s %s" % (gid, "PASS" if cond else "FAIL", detail))


def load_insns(path):
    """(addr, bytes, text) with continuation byte-lines folded into their instruction.
    M329_PATCH ("0xADDR|old text|new text", several joined by ';;') rewrites an instruction
    LINE IN MEMORY - a mutation-harness device; a spec that does not match exactly aborts."""
    ins = []
    with open(path) as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            parts = line.split("\t")
            m = re.match(r"^\s*([0-9a-f]{6,8}):$", parts[0])
            if not m:
                continue
            addr = int(m.group(1), 16)
            bytestr = parts[1].strip() if len(parts) > 1 else ""
            text = norm(parts[2]) if len(parts) > 2 and parts[2].strip() else ""
            if text:
                ins.append([addr, bytestr, text])
            elif ins:  # continuation of the previous instruction's encoding
                ins[-1][1] = (ins[-1][1] + " " + bytestr).strip()
    patch = os.environ.get("M329_PATCH")
    if patch:
        for spec in patch.split(";;"):
            if not spec.strip():
                continue
            a_s, old, new = spec.split("|", 2)
            a = int(a_s, 0)
            hit = [x for x in ins if x[0] == a]
            if not hit:
                raise SystemExit("M329_PATCH: no insn at %s" % a_s)
            if hit[0][2] != norm(old):
                raise SystemExit("M329_PATCH: %#x holds %r, spec expected %r" %
                                 (a, hit[0][2], norm(old)))
            hit[0][2] = norm(new)
    return ins


def parse_mem(text):
    """Every [..] in a line -> (base, index, scale, disp). Handles [i+i*8], [r*4+0x..],
    [esp+0x10+eax*4] and negative displacements ([ecx-0x8])."""
    res = []
    for inner in re.findall(r"\[([^\]]+)\]", text):
        base = index = None
        scale = 1
        disp = 0
        for term in [t.strip() for t in inner.replace("-", "+-").split("+")]:
            if not term:
                continue
            neg = term.startswith("-")
            term = term.lstrip("-")
            sign = -1 if neg else 1
            if re.match(r"^(0x[0-9a-f]+|\d+)$", term):
                disp += sign * int(term, 0)
            elif re.match(r"^[a-z][a-z0-9]*\*(\d+)$", term):
                r, s = term.split("*")
                index, scale = r, sign * int(s)
            elif term in REGS:
                if base is None:
                    base = term
                else:
                    index, scale = term, sign
        res.append((base, index, scale, disp))
    return res


def ops(text):
    """(mnemonic, [operands]) with operand commas respected (no nested commas in mem)."""
    m = re.match(r"^(\S+)\s*(.*)$", text)
    mn, rest = m.group(1), m.group(2)
    res, depth, cur = [], 0, ""
    for ch in rest:
        if ch in "[(":
            depth += 1
        elif ch in "])":
            depth -= 1
        if ch == "," and depth == 0:
            res.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        res.append(cur.strip())
    return mn, res


def field_disp(mem_list):
    """displacements of any [reg+0x38] style access to the record field."""
    return [d for (_b, _i, _s, d) in mem_list if d in (0x38, 0x95DA48 - BARRAY)]


def main():
    ins = load_insns(TEXT)
    pos = {a: i for i, a in enumerate([x[0] for x in ins])}
    fns = []
    with open(IDX) as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            p = line.rstrip("\n").split(",")
            if len(p) < 3 or not p[0].startswith("0x"):
                continue
            try:
                fns.append((int(p[0], 16), p[1], int(p[2])))
            except ValueError:
                pass
    fns.sort()

    def owner(a):
        best = None
        for st, nm, sz in fns:
            if st <= a < st + sz:
                best = (nm, st, sz)
        return best

    entry = [x for x in fns if x[0] == FN][0]
    lo, hi = FN, FN + entry[2]
    frame = [x for x in ins if lo <= x[0] < hi]

    W("== M329: NAME of FUN_0041a8f0 and its ds:0x99aa38 scratch tree ==")
    W("source: %s (%d insns decoded) | frame %s [%#x,%#x) size=%d insns=%d"
      % (os.path.relpath(TEXT, REPO), len(ins), entry[1], lo, hi, entry[2], len(frame)))
    W("index: %s | exe(read-only data): %s" % (os.path.relpath(IDX, REPO),
                                                os.path.relpath(EXE, REPO)))

    # ---------------- T1 callers ----------------
    W("")
    W("T1 every call of FUN_0041a8f0 in .text, found by DECODING the rel32 encoding "
      "(not by grepping the printed target):")
    sites = []
    decoded = 0
    for a, by, t in ins:
        mn, oo = ops(t)
        if mn != "call" or not oo:
            continue
        bb = [int(x, 16) for x in by.split()] if by else []
        tgt_dec = None
        if bb and bb[0] == 0xE8 and len(bb) >= 5:
            rel = int.from_bytes(bytes(bb[1:5]), "little", signed=True)
            tgt_dec = a + 5 + rel
            decoded += 1
        mtxt = re.match(r"0x([0-9a-f]+)", oo[0])
        tgt_txt = int(mtxt.group(1), 16) if mtxt else None
        if tgt_dec == FN:
            sites.append((a, tgt_txt == tgt_dec, t))
    W("  e8-call insns decoded image-wide=%d; sites targeting %#x=%d" % (decoded, FN, len(sites)))
    rows = []
    for a, agree, t in sites:
        i = pos[a]
        this, thishow = None, None
        for j in range(i - 1, max(i - 9, 0), -1):
            mn, oo = ops(ins[j][2])
            if mn == "mov" and oo and oo[0] == "ecx":
                this, thishow = oo[1], ins[j][0]
                break
        args = []
        for j in range(i - 1, max(i - 8, 0), -1):
            mn, oo = ops(ins[j][2])
            if mn == "call":
                break
            if mn == "push" and oo:
                args.append(oo[0])
        ret_use = None
        for j in range(i + 1, min(i + 5, len(ins))):
            mn, oo = ops(ins[j][2])
            if mn == "test" and oo and oo[0] == "eax" and oo[-1] == "eax":
                ret_use = ins[j][0]
                break
        ow = owner(a)
        rows.append((a, agree, ow[0], this, thishow, tuple(args), ret_use))
        W("  site %#x decoded==printed=%s owner=%-14s ecx<-%-10s (@%#x)  pushes=%s  "
          "return tested@%s" % (a, agree, ow[0], this, thishow,
                                ",".join(args) or "-", hex(ret_use) if ret_use else "-"))
    constthis = [r for r in rows if r[3] == hex(WIDGET)]
    regthis = [r for r in rows if r[3] and r[3] != hex(WIDGET)]
    retused = [r for r in rows if r[6]]
    W("  owners=%d distinct; this=const %#x at %d sites; this=register at %d; "
      "return value tested at %d" % (len({r[2] for r in rows}), WIDGET, len(constthis),
                                     len(regthis), len(retused)))
    spill = [x[0] for x in frame[:8] if ops(x[2])[0] == "mov" and len(ops(x[2])[1]) == 2 and
             ops(x[2])[1][0].split()[-1] == SPILLSLOT]
    reload = [x[0] for x in frame if x[2] == "mov ecx,dword ptr " + SPILLSLOT]
    thisload = [x[0] for x in frame[:8] if x[2] == "mov edi,ecx"]
    rets4 = [x[0] for x in frame if x[2] == "ret 0x4"]
    W("  entry: %s | this spilled to %s at %s, reloaded into ecx at %s | `ret 0x4` sites=%d" %
      (frame[0][2], SPILLSLOT, " ".join(hex(x) for x in spill),
       " ".join(hex(x) for x in reload), len(rets4)))

    # ---------------- T2 the object it runs on ----------------
    W("")
    W("T2 the widget fields this function touches, read out of the ENCODINGS "
      "(disp32 little-endian in the raw bytes):")
    show_reads, cur_reads, disp_bytes = [], [], 0
    for a, by, t in frame:
        for _b, _i, _s, d in parse_mem(t):
            if d in (SHOW, CURSOR):
                le = int.from_bytes(bytes([int(x, 16) for x in by.split()])[-4:], "little") \
                    if len(by.split()) >= 4 else None
                ok = (le == d)
                disp_bytes += ok
                (show_reads if d == SHOW else cur_reads).append((a, ok))
    W("  reads of [this+%#x] (the pane's SHOWN index): %d  %s" %
      (SHOW, len(show_reads), ",".join(hex(a) for a, _ in show_reads)))
    W("  reads of [this+%#x] (the CURSOR row):        %d  %s" %
      (CURSOR, len(cur_reads), ",".join(hex(a) for a, _ in cur_reads)))
    W("  displacements whose disp32 bytes match the printed operand: %d/%d" %
      (disp_bytes, len(show_reads) + len(cur_reads)))

    # ---------------- T3 row -> record, and the owner gate ----------------
    W("")
    W("T3 the multiply chains that turn the shown index into an array offset, SIMULATED:")

    def fold_at(i):
        try:
            return _fold_at(i)
        except (KeyError, IndexError, TypeError, ValueError):
            return None, None

    def _fold_at(i):
        a, by, t = ins[i]
        mn, oo = ops(t)
        for b, ix, sc, d in parse_mem(oo[1]):
            if b == ix:
                base = b
                break
        else:
            return None, None
        env = {base: None}
        vals = {}
        for sample in (1, 5, 17):
            e = {base: sample}
            k = i
            for _ in range(3):
                m2, o2 = ops(ins[k][2])
                if m2 == "lea":
                    dst, src = o2[0], o2[1]
                    val = 0
                    for b2, ix2, sc2, d2 in parse_mem(src):
                        if b2 and ix2 == b2:
                            val += e[b2] * (1 + sc2)
                        elif b2 and ix2:
                            val += e[b2] + e.get(ix2, 0) * sc2
                        elif ix2:
                            val += e.get(ix2, 0) * sc2
                        else:
                            val += e.get(b2, 0)
                        val += d2
                    e[dst] = val
                elif m2 == "shl":
                    e[o2[0]] = e[o2[0]] << int(o2[1], 0)
                else:
                    return None, None
                k += 1
            dstreg = ops(ins[i + 2][2])[1][0]
            vals[sample] = e[dstreg]
        mult = (vals[17] - vals[1]) // 16
        seq = [ins[j][2] for j in (i, i + 1, i + 2)]
        return mult, seq

    chains = []
    for i, (a, by, t) in enumerate(ins):
        mn, oo = ops(t)
        if mn == "lea" and len(oo) > 1:
            for b, ix, sc, d in parse_mem(oo[1]):
                if b and b == ix and sc == 8:
                    mult, seq = fold_at(i)
                    if mult:
                        nxt = ins[i + 3][2] if i + 3 < len(ins) else ""
                        mem = parse_mem(nxt)
                        tgt = [dd for (_bb, _ii, _sc, dd) in mem]
                        chains.append((a, mult, seq, nxt, tgt))
    inframe = [c for c in chains if lo <= c[0] < hi]
    for a, mult, seq, nxt, tgt in inframe:
        W("  chain @%#x %s | evaluates to %d * i | feeds: %s" % (a, " ; ".join(seq), mult, nxt))
    W("  chains in the frame=%d image-wide=%d" % (len(inframe), len(chains)))
    addrs = sorted({t for c in inframe for t in c[4] if t and t >= 0x900000})
    W("  absolute globals addressed by those chains: %s" % ", ".join(hex(x) for x in addrs))
    fields = {x - BARRAY for x in addrs if BARRAY <= x < BARRAY + 0x100}
    W("  as displacements into the %d-B record at %#x: %s | record %% unit-stride(%d) = %d"
      % (BSTRIDE, BARRAY, ", ".join("%#x" % f for f in sorted(fields)), UNITSTRIDE,
         BSTRIDE % UNITSTRIDE))
    gate("G3", len(inframe) == PIN_CHAINS and all(c[1] == BSTRIDE for c in inframe) and
         {0x78, 0x04} >= fields and BSTRIDE % UNITSTRIDE != 0,
         "%d chains in the frame all fold to %d (the base_array stride of NAMED ## M321); the "
         "addressed globals resolve to record fields %s; %d %% %d = %d != 0 so it is NOT the "
         "unit array of M327" % (len(inframe), BSTRIDE, sorted(hex(f) for f in fields), BSTRIDE,
                                  UNITSTRIDE, BSTRIDE % UNITSTRIDE))

    W("")
    W("T3b the ownership gate (whose base is selected?):")
    gate_seq = []
    for i, (a, by, t) in enumerate(frame):
        if re.search(r"cmp\s+ecx,eax", t):
            back = [frame[j][2] for j in range(max(0, i - 4), i + 3)]
            if any(hex(CURFACTION) in x for x in back):
                gate_seq.append((a, back))
    for a, back in gate_seq:
        W("  @%#x %s" % (a, " | ".join(back)))
    refuses = []
    for i, (a, by, t) in enumerate(frame):
        if t == "mov eax,0x1":
            ahead = [frame[j][2] for j in range(i + 1, min(i + 8, len(frame)))]
            if any(x.startswith("ret") for x in ahead):
                refuses.append(a)
    W("  `mov eax,1` + ret (refused) at %s | success return: %s" %
      (", ".join(hex(x) for x in refuses),
       ", ".join(hex(x[0]) for x in frame if x[2] == "xor eax,eax")))
    escape = [x[0] for x in frame if re.search(r"test\s+byte ptr ds:%#x,0x80" % OBSERVE, x[2])
              or re.search(r"f6 05", x[2]) and hex(OBSERVE) in x[2]]
    curf = [x[0] for x in frame if hex(CURFACTION) in x[2]]
    W("  compare vs ds:%s at %s | escape test on ds:%s bit 7 at %s" %
      (hex(CURFACTION), ", ".join(hex(x) for x in curf), hex(OBSERVE),
       ", ".join(hex(x) for x in escape)))
    caller_pair = []
    for a, by, t in ins:
        if 0x41E160 <= a < 0x41E6CF and (hex(CURFACTION) in t or
                                         re.search(r"test byte ptr ds:%#x,0x80" % OBSERVE, t)):
            caller_pair.append((a, t))
    W("  the same two globals in caller FUN_0041e160: %d insns %s" %
      (len(caller_pair), " ; ".join("%s %s" % (hex(x), y) for x, y in caller_pair[:4])))

    gate("G1", {r[0] for r in rows} == PIN_CALLS and len(rows) == len(PIN_CALLS) and
         all(r[1] for r in rows) and {r[2] for r in rows} == PIN_OWNERS and
         len(constthis) == 3 and len(regthis) == 1 and len(retused) == 2 and
         spill and thisload and len(reload) == 1 and len(rets4) == PIN_REFUSES + 1,
         "exactly %d call sites %s found by rel32 decode (decoded target == printed target on "
         "every one), %d distinct owners, this=%#x at %d sites and a register this at %d, the "
         "return value is tested at %d, the frame is thiscall (ecx->edi at %s, edi spilled to "
         "%s at %s and reloaded into ecx at %s for the vtable call; %d `ret 0x4` = %d refusals "
         "+ 1 success)" % (len(rows), sorted(hex(x) for x in PIN_CALLS),
                           len(PIN_OWNERS), WIDGET, len(constthis), len(regthis),
                           len(retused), hex(thisload[0]) if thisload else "-", SPILLSLOT,
                           hex(spill[0]) if spill else "-",
                           hex(reload[0]) if reload else "-", len(rets4), PIN_REFUSES))
    gate("G2", len(show_reads) == PIN_SHOW_READS and len(cur_reads) == 0 and
         disp_bytes == len(show_reads) and all(ok for _, ok in show_reads),
         "the widget field read %d times in the frame is [this+%#x] = the index the pane SHOWS "
         "(skill production-queue.md:305/613), never the cursor [this+%#x] = %d reads; all %d "
         "displacements verified from the disp32 encoding bytes" %
         (len(show_reads), SHOW, CURSOR, len(cur_reads), disp_bytes))
    gate("G4", len(gate_seq) >= 1 and len(refuses) == PIN_REFUSES and curf and escape and
         len(caller_pair) >= 4,
         "the gate compares the record's owner byte with ds:%s (current faction, M222) and "
         "escapes on ds:%s bit 7; %d refusal returns (%s) and the tail returns 0; the caller "
         "FUN_0041e160 repeats the same two-global test at %d insns before it calls in" %
         (hex(CURFACTION), hex(OBSERVE), len(refuses),
          ",".join(hex(x) for x in refuses), len(caller_pair)))

    # ---------------- T4 the scratch tree ----------------
    W("")
    W("T4 the tree that writes ds:%#x inside the frame (stores, with the leg that built the "
      "value):" % SEL)
    stores = []
    for i, (a, by, t) in enumerate(frame):
        mn, oo = ops(t)
        if mn == "mov" and oo and hex(SEL) in oo[0] and "ds:" in oo[0]:
            stores.append((i, a, oo[1]))
    W("  stores=%d first=%s last=%s" % (len(stores), hex(stores[0][1]), hex(stores[-1][1])))
    publish = [x[0] for x in frame if re.search(r"mov\s+dword ptr \[[a-z]+\*4\+%#x\],ecx" % FIELD,
                                                x[2])]
    pub_i = pos[publish[0]]
    W("  publish insn @%s" % hex(publish[0]))
    legs = []
    FAMILY = {"al": "eax", "ah": "eax", "ax": "eax", "eax": "eax",
              "cl": "ecx", "ch": "ecx", "cx": "ecx", "ecx": "ecx",
              "dl": "edx", "dh": "edx", "dx": "edx", "edx": "edx",
              "bl": "ebx", "bh": "ebx", "bx": "ebx", "ebx": "ebx",
              "si": "esi", "esi": "esi", "di": "edi", "edi": "edi",
              "bp": "ebp", "ebp": "ebp", "sp": "esp", "esp": "esp"}
    SUBPOS = {"al": 0, "ah": 8, "ax": 0, "eax": 0, "cl": 0, "ch": 8, "cx": 0, "ecx": 0,
              "dl": 0, "dh": 8, "dx": 0, "edx": 0, "bl": 0, "bh": 8, "bx": 0, "ebx": 0,
              "esi": 0, "edi": 0, "ebp": 0, "esp": 0}
    SUBWID = {"al": 0xFF, "ah": 0xFF, "ax": 0xFFFF, "eax": 0xFFFFFFFF,
              "cl": 0xFF, "ch": 0xFF, "cx": 0xFFFF, "ecx": 0xFFFFFFFF,
              "dl": 0xFF, "dh": 0xFF, "dx": 0xFFFF, "edx": 0xFFFFFFFF,
              "bl": 0xFF, "bh": 0xFF, "bx": 0xFFFF, "ebx": 0xFFFFFFFF}

    def rec_def(reg, upto):
        """the nearest preceding frame insn that loads reg's family from the record's +0x38"""
        fam = FAMILY[reg]
        j = upto - 1
        while j >= 0 and upto - j <= 12:
            mn, oo = ops(frame[j][2])
            if len(oo) == 2 and mn.startswith("mov") and FAMILY.get(oo[0]) == fam:
                return frame[j][2] if re.search(r"\+0x38\]", oo[1]) else None
            j -= 1
        return None

    def hoisted_const(reg, upto):
        """the immediate this mask register was last loaded with, and where. Only writes
        (a destination operand) reset the trail - test/cmp/jmp do not touch it."""
        WRITERS = ("mov", "movzx", "movsx", "lea", "shl", "shr", "and", "or", "add", "sub",
                   "xor", "inc", "dec", "not", "neg", "sbb", "adc", "sete", "setne")
        j = upto - 1
        while j >= 0 and upto - j <= 80:
            mn, oo = ops(frame[j][2])
            if len(oo) == 2 and mn == "mov" and oo[0] == reg and re.match(r"^0x[0-9a-f]+$", oo[1]):
                return int(oo[1], 0), frame[j][0]
            if mn in WRITERS and oo and FAMILY.get(oo[0], oo[0]) == FAMILY.get(reg, reg):
                return None, frame[j][0]
            j -= 1
        return None, None

    for n in range(1, len(stores)):
        i0 = stores[n - 1][0] + 1
        i1 = stores[n][0]
        leg = frame[i0:i1 + 1]
        rec_mask = None
        idiom = None
        sbit = None
        andop = orop = None
        accfam = FAMILY[stores[n][2]]
        if any(x[2].startswith("sbb") for x in leg):      # the 0/1 materialisation leg
            for k in range(i0, i1 + 1):
                mn, oo = ops(frame[k][2])
                if mn == "and" and len(oo) == 2 and re.match(r"^0x[0-9a-f]+$", oo[1]) and \
                        rec_def(oo[0], k):
                    rec_mask = int(oo[1], 0)
                    idiom = "sbb-dance"
            sbit = 0x1
            legs.append((stores[n][1], rec_mask, sbit, idiom, True))
            continue
        for k in range(i0, i1 + 1):
            a, by, t = frame[k]
            mn, oo = ops(t)
            if mn == "test" and len(oo) == 2 and hex(SEL) not in t:
                recs = [o for o in oo if o in SUBPOS and rec_def(o, k)]
                rest = [o for o in oo if o not in recs]
                if recs and rest:
                    shift = SUBPOS[recs[0]]
                    mo = rest[0]
                    if re.match(r"^0x[0-9a-f]+$", mo):
                        rec_mask = int(mo, 0) << shift
                        idiom = ("dh-mask" if shift else "dword-mask") if \
                            recs[0] in ("edx", "dh", "ecx", "eax") else "byte-mask"
                    else:
                        hv, haddr = hoisted_const(mo, k)
                        if hv is not None:
                            rec_mask = hv
                            idiom = "hoisted %s@%s" % (mo, hex(haddr))
            elif mn == "and" and len(oo) == 2 and FAMILY.get(oo[0]) == accfam and \
                    re.match(r"^0x[0-9a-f]+$", oo[1]):
                andop = ((~int(oo[1], 0)) & SUBWID[oo[0]]) << SUBPOS[oo[0]]
            elif mn == "or" and len(oo) == 2 and FAMILY.get(oo[0]) == accfam:
                if re.match(r"^0x[0-9a-f]+$", oo[1]):
                    orop = int(oo[1], 0) << SUBPOS[oo[0]]
                else:
                    orop = hoisted_const(oo[1], k)[0]
        if andop is not None and (andop & (andop - 1)) == 0:
            sbit = andop
        elif orop is not None:
            sbit = orop
        legs.append((stores[n][1], rec_mask, sbit, idiom,
                     (orop is not None and andop is not None and orop == andop)))
    for a, rm, sb, idiom, agree in legs:
        W("  leg store@%s  record bit=%s via %-9s -> scratch bit=%-10s  or/and agree=%s" %
          (hex(a), hex(rm) if rm else "REG?", idiom, hex(sb) if sb else "?", agree))
    rmask = [l[1] for l in legs]
    sbits = [l[2] for l in legs]
    W("  legs=%d | distinct record masks=%d | distinct scratch bits=%d | all masks+bits known=%s"
      % (len(legs), len(set(rmask)), len(set(sbits)),
         all(x is not None for x in rmask + sbits)))
    ident = sum(1 for rm, sb in zip(rmask, sbits) if rm and sb and rm.bit_length() == sb.bit_length())
    W("  legs that are the identity permutation: %d/%d (a straight bit-copy would be %d/%d)"
      % (ident, len(legs), len(legs), len(legs)))
    # the write-back side: every read of SEL between the last pack store and the publish
    wb = []
    last_i = stores[-1][0]
    reads = [(k, x[0], x[2]) for k, x in enumerate(frame)
             if last_i < k < pub_i and hex(SEL) in x[2]]
    W("  reads of ds:%s between the last pack store (%s) and the publish (%s): %d" %
      (hex(SEL), hex(stores[-1][1]), hex(publish[0]), len(reads)))
    for q, (k, a, t) in enumerate(reads):
        m = re.match(r"^test\s+(byte|dword) ptr ds:%#x,(0x[0-9a-f]+|[a-z]+)$" % SEL, t)
        bit = None
        if m:
            v = m.group(2)
            bit = int(v, 0) if v.startswith("0x") else hoisted_const(v, k)[0]
        nxt = reads[q + 1][0] if q + 1 < len(reads) else pub_i
        op = None
        for j in range(k + 1, min(nxt, len(frame))):
            a2, by2, t2 = frame[j]
            m2 = re.match(r"^(or|and)\s+(byte|dword) ptr \[([a-z]+)\+0x38\],(0x[0-9a-f]+)$", t2)
            if m2:
                op = (m2.group(1), int(m2.group(4), 0), a2)
                break
        wb.append((a, bit, op, t))
    W("  write-back legs (`test ds:%s,bit` / read of the scratch, then an op on [rec+0x38]): %d"
      % (hex(SEL), len(wb)))
    for a, bit, op, t in wb:
        W("    @%s %-42s scratch bit %-10s -> %s" %
          (hex(a), t, hex(bit) if bit else "in-leg",
           ("%s %#x @%s" % (op[0], op[1], hex(op[2]))) if op else "no direct op"))
    restored = {op[1] for _a, _b, op, _t in wb if op and op[0] == "or"}
    outside = sorted(hex(x) for x in restored if x not in set(rmask))
    W("  record bits restored by a resolved write-back=%d; those outside the 19 read masks=%s"
      % (len(restored & set(rmask)), outside or "-"))
    andmask = [x for x in frame if re.match(r"^and\s+ecx,0x[0-9a-f]+$", x[2])]
    pmask = int(andmask[0][2].split(",")[1], 0) if andmask else 0
    W("  the publish mask at %s: %s = bits %s" %
      (hex(andmask[0][0]) if andmask else "?", hex(pmask) if pmask else "?",
       ",".join(str(b) for b in range(32) if pmask and (pmask >> b) & 1)))

    gate("G5", len(stores) == PIN_STORES and stores[0][1] == PIN_ZEROSTORE and
         stores[1][1] == PIN_FIRSTLEG_STORE and publish[0] == PIN_PUBLISH,
         "%d stores to ds:%s in the frame: the zero-init at %#x then one after each leg, the "
         "last before the publish at %#x (%s)" %
         (len(stores), hex(SEL), PIN_ZEROSTORE, PIN_PUBLISH, hex(publish[0])))
    span = max(b for b in range(32) if any(s and (s >> b) & 1 for s in sbits)) if sbits else -1
    gate("G6", len(legs) == PIN_LEGS and len(set(rmask)) == PIN_LEGS and
         len(set(sbits)) == PIN_LEGS and all(x is not None for x in rmask + sbits) and
         all(l[4] for l in legs) and ident < PIN_LEGS and len(reads) == PIN_SELREADS and
         not outside and span == PIN_LEGS - 1,
         "%d legs each contribute one distinct record mask and one distinct scratch bit "
         "(%d/%d distinct on both sides, the scratch band spanning bits 0..%d); every leg's "
         "or-op agrees bit-for-bit with its and-op; only %d/%d legs are the identity, so the "
         "tree is a PERMUTATION not a bit-copy; %d reads of the scratch between the last pack "
         "store and the publish match the %d pack legs leg-for-leg, and every record bit a "
         "write-back restores is one of the %d the tree read" %
         (len(legs), len(set(rmask)), PIN_LEGS, span, ident, PIN_LEGS, len(reads), PIN_LEGS,
          PIN_LEGS))
    gate("G7", pmask == PIN_PUBMASK and bin(pmask).count("1") == 4 and
         all((x & pmask) == 0 for x in restored),
         "the publish mask is %#x (%d bits: %s) read straight off the `and ecx,mask` at %s, and "
         "NO write-back op touches a bit inside it: the packed policy bits this tree round-trips "
         "and the 4-bit window the faction block keeps are DISJOINT halves of [rec+0x38]" %
         (pmask, bin(pmask).count("1"), ",".join(str(b) for b in range(32) if (pmask >> b) & 1),
          hex(andmask[0][0])))

    # ---------------- T5 the field itself ----------------
    W("")
    W("T5 image-wide census of the field %#x (block+%#x):" % (FIELD, PIN_FIELD_OFF))
    refs = []
    for a, by, t in ins:
        if hex(FIELD) in t:
            mn, oo = ops(t)
            wr = mn in ("mov",) and hex(FIELD) in oo[0] or mn in ("and", "or", "add", "sub") and \
                hex(FIELD) in oo[0]
            consts = re.findall(r"0x[0-9a-f]{6,8}", t)
            refs.append((a, "W" if wr else "R", t))
    for a, k, t in refs:
        W("  %s @%s %s" % (k, hex(a), t))
    writers = [r for r in refs if r[1] == "W"]
    readers = [r for r in refs if r[1] == "R"]
    consts_written = sorted({int(t.split(",")[1], 0) for _a, _k, t in writers if t.count(",") and
                             re.search(r",0x[0-9a-f]{6,8}$", t)})
    dynW = [w for w in writers if lo <= w[0] < hi]
    creW = [w for w in writers if not (lo <= w[0] < hi)]
    W("  writers=%d (dynamic, inside FUN_0041a8f0=%d; constants outside=%d: %s) readers=%d" %
      (len(writers), len(dynW), len(creW),
       ", ".join("0x%x@0x%x" % (int(t.split(",")[1], 0), a) for a, _k, t in creW),
       len(readers)))
    rd_owners = sorted({owner(a)[0] for a, _k, _t in readers})
    W("  readers live in: %s" % ", ".join(rd_owners))
    # the stride of the folded publish form, SIMULATED
    fold = None
    for i, (a, by, t) in enumerate(frame):
        if a == publish[0]:
            j = i - 1
            seq = []
            while j >= 0 and len(seq) < 12:
                t2 = frame[j][2]
                seq.append(t2)
                if t2.startswith("mov edx,ecx") and \
                        any(x.startswith("mov ecx,dword ptr [ebp") for x in seq):
                    break
                j -= 1
            seq.reverse()
            # simulate the straight-line chain on two samples of the faction index;
            # memory loads are opaque (they sit outside the arithmetic chain)
            vals = {}
            for sample in (3, 7):
                e = {"ecx": sample}
                for t2 in seq:
                    mn, oo = ops(t2)
                    if mn != "lea" and any("[" in x for x in oo):
                        continue
                    if mn in ("mov",) and len(oo) == 2:
                        e[oo[0]] = e.get(oo[1], 0)
                    elif mn == "shl":
                        e[oo[0]] <<= int(oo[1], 0)
                    elif mn == "add":
                        e[oo[0]] += e[oo[1]]
                    elif mn == "lea":
                        val = 0
                        for b2, ix2, sc2, d2 in parse_mem(oo[1]):
                            val += e.get(b2, 0) + (e.get(ix2, 0) * sc2 if ix2 else 0) + d2
                        e[oo[0]] = val
                    elif mn == "sub":
                        e[oo[0]] -= e[oo[1]]
                vals[sample] = e["edx"]
            dwords = (vals[7] - vals[3]) // 4
            fold = (dwords, dwords * 4, vals, seq)
    if fold:
        W("  publish address fold, simulated on faction index f in {3,7}: %s -> edx(f) is "
          "%d dwords = %d bytes per faction (the atlas says the block is %d B)" %
          (", ".join("f=%d:%d" % (k, v) for k, v in sorted(fold[2].items())),
           fold[0], fold[1], STRIDE))
    else:
        W("  publish address fold: NOT RESOLVED")
    if fold:
        W("  chain: %s" % " ; ".join(fold[3]))
    gate("G8", fold and fold[1] == STRIDE and FIELD - BLOKBASE == PIN_FIELD_OFF,
         "the publish form [%s*4+%#x] folds to %d dwords = %d bytes per faction, which is the "
         "atlas block size %d; the field sits at block+%#x" %
         ("edx", FIELD, fold[0], fold[1], STRIDE, PIN_FIELD_OFF))
    gate("G9", len(refs) == PIN_WRITERS + PIN_READERS and len(writers) == PIN_WRITERS and
         len(readers) == PIN_READERS and len(dynW) == 1 and len(creW) == 2 and
         set(consts_written) == PIN_CONSTS and PIN_CREATOR in [r[0] for r in readers] and
         all((c & pmask) == 0 for c in consts_written),
         "exactly %d refs to the field: %d writers (ONE dynamic writer - this function - and "
         "the two faction-create defaults %s) and %d readers; NEITHER default has a bit inside "
         "the %#x publish window, so the two writers occupy disjoint halves of this dword; %#x "
         "is a reader (the base creator of M282 copies the field into a NEW base's +0x38 per "
         "docs/sessions/sessions-98-98.md)" %
         (len(refs), len(writers), sorted(hex(c) for c in consts_written), len(readers), pmask,
          PIN_CREATOR))

    # ---------------- T6 the mode split ----------------
    W("")
    W("T6 the arg branch and the two phases:")
    mode = [x for x in frame if re.match(r"^mov\s+ecx,dword ptr \[ebp\+0x8\]$", x[2])]
    br = [x for x in frame if x[0] > (mode[0][0] if mode else hi) and
          re.match(r"^jne\s+0x41ae3c$", x[2])]
    W("  `mov ecx,[ebp+0x8]` @%s ; `jne 0x41ae3c` @%s" %
      (hex(mode[0][0]) if mode else "?", hex(br[0][0]) if br else "?"))
    arrive = [x for x in frame if re.match(r"^test\s+byte ptr \[eax\+0x38\],0x40$", x[2])]
    W("  M321's arrival test `test BYTE PTR [eax+0x38],0x40` in this frame at %s (after the "
      "publish at %#x: %s)" % (", ".join(hex(a) for a, _b, _t in arrive), PIN_PUBLISH,
                               all(a > publish[0] for a, _b, _t in arrive)))
    trio = []
    for x in frame:
        m = re.match(r"^mov\s+dword ptr \[[a-z]+\+(0x78|0x7c|0x80)\],ecx$", x[2])
        if m:
            trio.append((x[0], int(m.group(1), 0)))
    W("  the trio stores fed by one `xor ecx,ecx` (at %s): %s" %
      (hex(PIN_XORTRIO), ", ".join("%s:%#x" % (hex(a), d) for a, d in trio)))
    vcall = [x for x in frame if re.match(r"^call\s+dword ptr \[edx\+0xf0\]$", x[2])]
    W("  virtual call [edx+0xf0] (the widget's own vtable) at %s -> in the arg!=0 phase: %s" %
      (", ".join(hex(x[0]) for x in vcall),
       all(x[0] > 0x41AE3C for x in vcall) if vcall else None))
    callees = [(x[0], ops(x[2])[1][0]) for x in frame if ops(x[2])[0] == "call"]
    W("  callees: %d %s" % (len(callees), ", ".join("%s>%s" % (hex(a), b) for a, b in callees)))
    gate("G10", mode and br and len(arrive) == 1 and arrive[0][0] == PIN_ARRIVAL and
         arrive[0][0] > publish[0] and len(trio) == 3 and
         {d for _a, d in trio} == {0x78, 0x7C, 0x80} and len(vcall) == 1,
         "the function splits on its single arg ([ebp+0x8]); the bit-%#x arrival test of NAMED "
         "## M321 sits inside it at %#x, AFTER the publish, in the arg==0 phase together with "
         "the trio stores to +0x78/+0x7c/+0x80; the arg!=0 phase ends with a call through the "
         "widget's own vtable slot +0xf0 (a pane refresh)" % (ARRIVE, PIN_ARRIVAL))

    # ---------------- T7 the tag, the record, the rivals ----------------
    W("")
    W("T7 what the tree is FOR: the tagged save record it writes.")
    tw = [x for x in frame if re.match(r"^call\s+%s$" % hex(TAGWRITER), x[2])]
    pushes = []
    for x in tw:
        i = pos[x[0]]
        for j in range(i - 1, i - 5, -1):
            mn, oo = ops(ins[j][2])
            if mn == "push":
                pushes.append(int(oo[0], 0))
        W("  @%s call %#x with pushed immediates %s" % (hex(x[0]), TAGWRITER,
                                                        ", ".join(hex(p) for p in pushes)))
    try:
        name = read_va(EXE, GONAME, 12).split(b"\0")[0].decode("ascii", "replace")
    except Exception as e:  # noqa
        name = "ERR %s" % e
    W("  bytes at %#x in terran.exe (PE section walk, read-only): %r" % (GONAME, name))
    off = SEL - BANDREC
    W("  the staging dword sits at +%#x of the %#x-B record at %#x (fits: %s)" %
      (off, TAGSIZE, BANDREC, 0 <= off < TAGSIZE))
    ctx = [x for x in frame if re.match(r"^call\s+%s$" % hex(CTXOPEN), x[2])]
    W("  save-band context call %#x at %s" % (CTXOPEN, ", ".join(hex(x[0]) for x in ctx)))
    mstride = inframe[0][1] if inframe else None
    r_free = not (spill and thisload and reload)
    r_cursor = len(cur_reads) > 0
    r_unit = mstride != BSTRIDE
    r_whole = any((c & pmask) for c in consts_written)
    r_sole = len(writers) == 1
    r_notag = len(tw) != 1
    W("  RIVAL 1 'a free function, no thiscall object': %s (ecx->edi at %s, edi spilled to %s "
      "at %s, used as a base at [edi+%#x] and reloaded into ecx at %s for the vtable call)" %
      (r_free, hex(thisload[0]) if thisload else "-", SPILLSLOT,
       hex(spill[0]) if spill else "-", SHOW, hex(reload[0]) if reload else "-"))
    W("  RIVAL 2 'driven by the CURSOR row': %s (%d cursor reads vs %d shown-index reads)" %
      (r_cursor, len(cur_reads), len(show_reads)))
    W("  RIVAL 3 'the array it indexes is the unit array (stride %d)': %s (the chain measures "
      "%s bytes per record)" % (UNITSTRIDE, r_unit, mstride))
    W("  RIVAL 4 'the block keeps the whole dword, defaults and packer in one field': %s "
      "(%d of the faction-create defaults %s have a bit inside the %#x publish window)" %
      (r_whole, sum(1 for c in consts_written if c & pmask),
       sorted(hex(c) for c in consts_written), pmask))
    W("  RIVAL 5 'the packer is the field's only writer': %s (%d writers = %d dynamic + %d "
      "faction-create constants)" % (r_sole, len(writers), len(dynW), len(creW)))
    W("  RIVAL 6 'the record is emitted some other way': %s (%d calls of the tagged writer %s "
      "in the frame)" % (r_notag, len(tw), hex(TAGWRITER)))
    gate("G11", name == "GOVOPTIONS" and len(tw) == 1 and GONAME in pushes and TAGSIZE in pushes
         and 0 <= off < TAGSIZE and len(ctx) == 1,
         "the tree ends in ONE tagged-writer call %#x with pushed (%#x=%r, %#x=%d B, 0), i.e. "
         "the scratch dword this tree builds IS field +%#x of the %d-B GOVOPTIONS record at "
         "%#x, opened by %#x one insn earlier" %
         (TAGWRITER, GONAME, name, TAGSIZE, TAGSIZE, off, TAGSIZE, BANDREC, CTXOPEN))
    gate("G12", not (r_free or r_cursor or r_unit or r_whole or r_sole or r_notag),
         "6 rivals all False on the printed numbers (no-thiscall %s; cursor-driven %s; "
         "unit-array %s; defaults-and-packer-share-the-window %s; sole-writer %s; "
         "no-tagged-writer %s)" % (r_free, r_cursor, r_unit, r_whole, r_sole, r_notag))

    detail = "\n".join(l for l in out
                       if not l.startswith(("G", "DIGEST", "== M329:")))
    dig = hashlib.sha256(detail.encode()).hexdigest()[:16]
    W("DIGEST %s" % dig)
    ok = (dig == PIN)
    gate("G13", ok, "digest==PIN %s measured=%s (any drift in the measured rows reddens this)"
         % (PIN, dig))
    n = sum(1 for _x, c, _d in G if c)
    W("== M329: %d/%d ==" % (n, len(G)))
    txt = "\n".join(out) + "\n"
    sys.stdout.write(txt)
    dst = os.path.join(EV, "evidence/m329_scratchtree.txt")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "w").write(txt)
    return 0 if n == len(G) else 1


def read_va(path, va, n):
    blob = open(path, "rb").read()
    pe = int.from_bytes(blob[0x3C:0x40], "little")
    nsec = int.from_bytes(blob[pe + 6:pe + 8], "little")
    optsz = int.from_bytes(blob[pe + 20:pe + 22], "little")
    opt = pe + 24
    magic = int.from_bytes(blob[opt:opt + 2], "little")
    imagebase = int.from_bytes(blob[opt + 28:opt + 32], "little") if magic == 0x10B \
        else int.from_bytes(blob[opt + 24:opt + 32], "little")
    sec = opt + optsz
    for i in range(nsec):
        s = sec + 40 * i
        va0 = imagebase + int.from_bytes(blob[s + 12:s + 16], "little")
        raw = int.from_bytes(blob[s + 20:s + 24], "little")
        vsz = int.from_bytes(blob[s + 8:s + 12], "little")
        rsz = int.from_bytes(blob[s + 16:s + 20], "little")
        if va0 <= va < va0 + max(vsz, rsz):
            off = raw + (va - va0)
            return blob[off:off + n]
    raise ValueError("VA %#x outside every section" % va)


if __name__ == "__main__":
    sys.exit(main())
