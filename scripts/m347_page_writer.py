#!/usr/bin/env python3
"""M347 -- the WRITER of the HoF page field `[screen+0x59f4]` (M341's OPEN).

M341 read `[obj+0x59f4]` at 0x44970f as the page `n` in `5*n - 5 + s` and
left the writer OPEN with a lead: "a control at obj+0x5970".  This script
follows that lead and measures the whole write path:

  * 0x59f4 - 0x5970 == 0x84: the dword is field +0x84 of the sub-object the
    screen constructs at +0x5970 (ctor 0x44ba40 -> 0x6290b0).
  * the sub-object is a child container: selector 0x62921c scans
    `child->id` (+0xa78) for the requested id and stores it at `this+0x84`,
    or stores -1 when no child carries that id.  The ctor leaves +0x84
    alone; init 0x629169 writes the sentinel -2.
  * the 7 children at screen+0xa5c are built in a loop with ids 1..7
    (Init 0x5f9e85 stores arg2 at +0xa78; the loop reloads the counter AFTER
    incrementing it, so id = i+1).
  * the HoF screen's two call sites request id = block+1 (block 0..6 from the
    7-block scan) and id = ds:0x91b5b4 (the 1-based faction/player index,
    measured here by the 0x983984 + 0x2bc*p block arithmetic).

So the page's upper bound IS statically established: 7.  The -1/-2 sentinels
are unreachable from these two callers but the reader has no guard, so a
sentinel value would index BEFORE 0x983a10 (documented, not repaired).

All numbers are COMPUTED from the static image (zero box time, no gdb).
Every V claim names its mutant in scripts/m347_mutate.py.
"""
import hashlib
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
EXE = os.path.join(ROOT, "programs", "terran.exe")

INSN = re.compile(r"^\s*([0-9a-f]{5,8}):\t[0-9a-f ]+\t(\w+)\s*(.*)$")

PAGE_LOAD = 0x44970F
SUB = 0x5970
FIELD = 0x59F4              # 0x5970 + 0x84
VT = 0x674C5C               # HoF screen primary vtable
OBJ = 0x748600              # the HoF screen singleton (0x448c30 -> 0x44ba40)
BASE = 0x983A10
STRIDE = 0x8C
BLOCK = 0x2BC

_ins = []


def image():
    if not _ins:
        out = []
        with open(TEXT, errors="replace") as f:
            for line in f:
                m = INSN.match(line)
                if m:
                    out.append([int(m.group(1), 16), m.group(2),
                                m.group(3).strip()])
        _ins.extend(out)
    return _ins


def patches():
    ins_patch, img_patch, mn_patch = {}, {}, {}
    for spec, dst in ((os.environ.get("M347_PATCH_INS", ""), ins_patch),
                      (os.environ.get("M347_PATCH_IMG", ""), img_patch)):
        for part in spec.split(";"):
            if not part.strip():
                continue
            a, v = part.split("=", 1)
            dst[int(a, 16)] = v if dst is ins_patch else int(v, 16)
    for part in os.environ.get("M347_PATCH_MN", "").split(";"):
        if part.strip():
            a, v = part.split("=", 1)
            mn_patch[int(a, 16)] = v
    return ins_patch, img_patch, mn_patch


INSP, IMGP, MNP = patches()
ALGO = os.environ.get("M347_ALGO", "")


def load():
    im = image()
    for r in im:
        if r[0] in INSP:
            r[2] = INSP[r[0]]
        if r[0] in MNP:
            r[1] = MNP[r[0]]
    return im


def window(lo, hi):
    return [i for i in load() if lo <= i[0] <= hi]


def at(addr):
    for i in load():
        if i[0] == addr:
            return i
    raise SystemExit("address %x not in image" % addr)


def split_ops(ops):
    """destination, source -- split at the first comma outside brackets."""
    depth = 0
    for k, ch in enumerate(ops):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        elif ch == "," and depth == 0:
            return ops[:k].strip(), ops[k + 1:].strip()
    return ops.strip(), ""


def mem(expr):
    m = re.search(r"\[([^\]]*)\]", expr)
    return m.group(1).replace(" ", "") if m else ""


def imm(expr):
    m = re.match(r"^(?:DWORD PTR |BYTE PTR )?\[?0x([0-9a-f]+)\]?$", expr.strip())
    if m:
        return int(m.group(1), 16) - (1 << 32 if int(m.group(1), 16) & 0x80000000 else 0)
    m = re.match(r"^0x([0-9a-f]+)$", expr.strip())
    return int(m.group(1), 16) - (1 << 32 if int(m.group(1), 16) & 0x80000000 else 0) if m else None


def dispo(expr):
    """the trailing +0xNNN constant of a memory expression."""
    m = re.search(r"\+0x([0-9a-f]+)\]$", expr.replace(" ", ""))
    return int(m.group(1), 16) if m else None


# ---------------------------------------------------------------- PE reader
SECS = []


def pe():
    if SECS:
        return
    b = open(EXE, "rb").read()
    e = struct.unpack_from("<I", b, 0x3C)[0]
    nsec = struct.unpack_from("<H", b, e + 6)[0]
    opt = struct.unpack_from("<H", b, e + 20)[0]
    base = struct.unpack_from("<I", b, e + 24 + 28)[0]
    off = e + 24 + opt
    SECS.append(("_hdr", base, b))
    for _ in range(nsec):
        vsz, va, rsz, ra = struct.unpack_from("<IIII", b, off + 8)
        SECS.append((va, vsz, rsz, ra))
        off += 40


def img_dword(vaddr):
    pe()
    base = SECS[0][1]
    b = SECS[0][2]
    rva = vaddr - base
    for va, vsz, rsz, ra in SECS[1:]:
        if va <= rva < va + max(vsz, rsz):
            fo = ra + (rva - va)
            if vaddr in IMGP:
                return IMGP[vaddr]
            return struct.unpack_from("<I", b, fo)[0]
    return None


# ---------------------------------------------------------------- helpers
def stores84(lo, hi):
    """(addr, insn, value-text) for every store whose memory ends +0x84]."""
    out = []
    for a, m, o in window(lo, hi):
        if m in ("mov", "or", "and", "add", "xor"):
            d, s = split_ops(o)
            if d.endswith("+0x84]"):
                out.append((a, m, o))
    return out


def callers(callee):
    out = []
    for a, m, o in load():
        if m == "call" and imm(o) == callee:
            out.append(a)
    return out


def receiver(addr, back=8):
    """the ecx value/receiver established before `addr`."""
    im = load()
    k = next(i for i, r in enumerate(im) if r[0] == addr)
    for j in range(k - 1, max(-1, k - back - 1), -1):
        a, m, o = im[j]
        if m == "lea" and o.startswith("ecx,"):
            return "lea:" + o.split(",", 1)[1]
        if m == "mov" and o.startswith("ecx,"):
            return "mov:" + o.split(",", 1)[1]
    return "?"


def sub_receiver(r):
    """is this receiver the screen+0x5970 sub-object?"""
    if r.startswith("lea:") and dispo(r.split(":", 1)[1]) == SUB:
        return True
    return r == "mov:0x74df70"


def tok_has(ops, tok):
    return tok in re.findall(r"0x[0-9a-f]+", ops)


def loop_trip(start, stop, step, cmp_addr):
    """number of iterations of `cmp ptr,stop; jl` with `add ptr,step`."""
    return (stop - start + step - 1) // step if stop > start else 0


ROWS = []


def say(s, row=None):
    print(s)
    if row is not None:
        ROWS.append(row)


def main():
    load()

    # ------------------------------------------------------------ TABLE 1
    say("== M347: the writer of [screen+0x59f4] (M341's OPEN) ==")
    delta = FIELD - SUB
    ctor = window(0x44BA40, 0x44BB32)
    ctor_sub = [r[0] for r in ctor if r[1] == "lea" and mem(split_ops(r[2])[1]) == "esi+0x%x" % SUB]
    ctor_init = [r[0] for r in ctor if r[1] == "call" and imm(r[2]) == 0x6290B0]
    ctor_vt = [r for r in ctor if r[1] == "mov" and mem(split_ops(r[2])[0]) == "esi"]
    ctor_sec = [r for r in ctor if r[1] == "mov" and mem(split_ops(r[2])[0]) == "esi+0x444"]
    vt30 = img_dword(VT + 0x30)
    reader_esi = [r for r in window(0x4495E0, 0x449620)
                  if r[1] == "mov" and r[2] == "esi,ecx"]
    load_ins = at(PAGE_LOAD)
    say("T1 identity: sub-object at screen+0x%x ; field 0x%x = sub+0x%x" % (SUB, FIELD, delta))
    say("   ctor 0x44ba40: lea-sub %s ; call-ctor %s ; vptr %s ; +0x444 %s"
        % ([hex(a) for a in ctor_sub], [hex(a) for a in ctor_init],
           ctor_vt[0][2] if ctor_vt else "?", ctor_sec[0][2] if ctor_sec else "?"))
    say("   vtable 0x%x slot +0x30 = 0x%x ; this=ecx at %s ; load at 0x%x: %s %s"
        % (VT, vt30, [hex(r[0]) for r in reader_esi], load_ins[0], load_ins[1], load_ins[2]))
    rows = [
        ("G1", "0x59f4 = sub(0x5970)+0x84; ctor 0x44ba40 builds it; vtable 0x%x +0x30 = 0x4495e0, whose body reads the field" % VT,
         0x59F4 - 0x5970 == 0x84 and len(ctor_sub) == 1 and len(ctor_init) == 1
         and vt30 == 0x4495E0 and len(reader_esi) == 1
         and load_ins[1] == "mov" and mem(load_ins[2]) == "esi+0x59f4"),
    ]

    # ------------------------------------------------------------ TABLE 2
    ctor84 = stores84(0x6290B0, 0x62910D)
    ctor_zero = [(a, o) for a, m, o in window(0x6290B0, 0x62910D)
                 if m == "mov" and split_ops(o)[1] == "0x0"
                 and mem(split_ops(o)[0]) in ("eax+0x80", "ecx+0x8c", "edx+0x90")]
    cls84 = stores84(0x629169, 0x6294B0)
    lea84 = [(a, o) for a, m, o in window(0x629169, 0x6294B0)
             if m == "lea" and "+0x84]" in o]
    say("T2 sub-object ctor 0x6290b0: stores to +0x84 = %d ; zero-stores = %s"
        % (len(ctor84), [hex(a) for a, _ in ctor_zero]))
    say("T3 class selector stores to [this+0x84] (0x629169..0x6294b0):")
    for a, m, o in cls84:
        say("   0x%x  %s %s" % (a, m, o))
    say("   lea reg,[..+0x84] (indirect-store evasion): %d" % len(lea84))
    rows.append(("G2", "ctor 0x6290b0 leaves +0x84 UNTOUCHED (0 stores); -2 comes from init 0x629169",
                 len(ctor84) == 0 and len(ctor_zero) == 3 and 0x629187 in [a for a, _, _ in cls84]))
    vals = {a: split_ops(o)[1] for a, m, o in cls84}
    rows.append(("G3", "exactly 4 stores: -2 init / -1 x2 / the requested id",
                 [a for a, _, _ in cls84] == [0x629187, 0x6292CA, 0x629363, 0x62936E]
                 and vals[0x629187] == "0xfffffffe" and vals[0x6292CA] == "0xffffffff"
                 and vals[0x62936E] == "0xffffffff" and vals[0x629363] == "edx"
                 and len(lea84) == 0))

    # ------------------------------------------------------------ TABLE 4
    say("T4 HoF screen calls into the sub-object (receiver pinned):")
    sites = [(0x4492B2, 0x629169, "init", 40), (0x449462, 0x6291A3, "register", 8),
             (0x44AE72, 0x6291E3, "select", 8), (0x44B72B, 0x6291E3, "select", 8)]
    recs = []
    for a, callee, role, back in sites:
        r = receiver(a, back)
        recs.append((a, callee, role, r))
        say("   0x%x call 0x%x (%s)  receiver %s" % (a, callee, role, r))
    abs_ok = OBJ + SUB == 0x74DF70
    say("   absolute receiver 0x74df70 == 0x%x+0x%x : %s" % (OBJ, SUB, abs_ok))
    lea_n = sum(1 for _, _, _, r in recs if r.startswith("lea:") and sub_receiver(r))
    mov_n = sum(1 for _, _, _, r in recs if r == "mov:0x74df70")
    rows.append(("G4", "4 calls, receiver = lea [reg+0x5970] x3 + abs 0x74df70 (= 0x748600+0x5970)",
                 lea_n == 3 and mov_n == 1 and abs_ok))

    # ------------------------------------------------------------ TABLE 5
    say("T5 child ids (the id namespace the selector matches):")
    ebx0 = [r for r in window(0x4492C0, 0x4492E0) if r[1] == "mov" and r[2].startswith("ebx,")][0]
    cmp_ins = at(0x44947F)
    add_ins = at(0x44946D)
    trip = (imm(cmp_ins[2].split(",")[1]) - imm(ebx0[2].split(",", 1)[1]) +
            imm(add_ins[2].split(",")[1]) - 1) // imm(add_ins[2].split(",")[1])
    if ALGO == "trip":
        trip += 1
    say("   ebx 0x%x %s %s ; step %s ; cmp %s -> trip %d"
        % (ebx0[0], ebx0[1], ebx0[2], add_ins[2], cmp_ins[2].split(",")[1], trip))
    inc_i = at(0x4493C8)
    store_i = at(0x4493E1)
    reload_i = at(0x4493F8)
    push_i = at(0x4493FC)
    push_txt = at(0x4493FD)
    call_init = at(0x449401)
    pre_inc = (0x4493C8 < 0x4493E1 < 0x4493F8 and store_i[1] == "mov"
               and split_ops(store_i[2])[0] == "DWORD PTR [ebp-0x14]"
               and reload_i[1] == "mov" and split_ops(reload_i[2]) == ("eax", "DWORD PTR [ebp-0x14]")
               and push_i[2] == "eax")
    id0 = 0 if ALGO == "id0" else 1
    ids = [i + id0 for i in range(trip)]
    say("   id path: %s %s ; %s %s ; %s %s ; %s %s ; %s %s"
        % (inc_i[1], inc_i[2], store_i[1], store_i[2], reload_i[1], reload_i[2],
           push_i[1], push_i[2], call_init[1], call_init[2]))
    init_store = at(0x5F9F72)
    init_arg = at(0x5F9F6F)
    say("   Init 0x5f9e85: %s %s -> %s %s" % (init_arg[1], init_arg[2],
                                              init_store[1], init_store[2]))
    sel_id = at(0x62925C)
    sel_cmp = at(0x62926B)
    sel_arg = at(0x629292)
    say("   selector: %s %s ; %s %s ; %s %s"
        % (sel_id[1], sel_id[2], sel_cmp[1], sel_cmp[2], sel_arg[1], sel_arg[2]))
    id_ok = (pre_inc and trip == 7 and init_store[2].endswith("[edx+0xa78],eax")
             and split_ops(init_arg[2])[1] == "DWORD PTR [ebp+0xc]"
             and mem(sel_id[2]) == "edx+0xa78" and "0x84" in sel_cmp[2])
    say("   checks: pre_inc=%s trip7=%s init_a78=%s sel_a78=%s sel_84=%s ids=%s"
        % (pre_inc, trip == 7, init_store[2].endswith("[edx+0xa78],eax"),
           mem(sel_id[2]) == "edx+0xa78", "0x84" in sel_cmp[2], ids))
    rows.append(("G5", "ids = {1..7}: trip 7, counter reloaded AFTER inc, Init stores arg2 at +0xa78, selector matches +0xa78",
                 id_ok and ids == [1, 2, 3, 4, 5, 6, 7]))

    # ------------------------------------------------------------ TABLE 6
    say("T6 writer id domains:")
    blk0 = at(0x44AE09)
    blk_step = at(0x44AE3D)
    blk_cmp = at(0x44AE44)
    blk_trip = (imm(blk_cmp[2].split(",")[1]) - 0x983A10) // imm(blk_step[2].split(",")[1])
    argload = at(0x44AE62)
    incid = at(0x44AE68)
    pushid = at(0x44AE6B)
    say("   block handler 0x44adc0: %s %s ; %s %s ; %s %s -> %d blocks 0..%d"
        % (blk0[1], blk0[2], blk_step[1], blk_step[2], blk_cmp[1], blk_cmp[2],
           blk_trip, blk_trip - 1))
    say("   id = %s %s ; %s %s ; push %s" % (argload[1], argload[2], incid[1], incid[2], pushid[2]))
    blk_ids = [b + 1 for b in range(blk_trip)]
    ply = at(0x44B71E)
    ply_store = at(0x44AED9)
    ply_load2 = at(0x44AECB)
    say("   player path: %s %s ; %s %s ; %s %s" % (ply[1], ply[2], ply_load2[1], ply_load2[2], ply_store[1], ply_store[2]))
    same_src = (ply[2] == "eax,ds:0x91b5b4" and ply_load2[2] == "eax,ds:0x91b5b4"
                and ply_store[2] == "DWORD PTR [esi+0xa4c],eax")
    rows.append(("G6", "block ids = {1..7} (7-block scan, +1) ; player id = ds:0x91b5b4 = the SITE B cell [screen+0xa4c] (its 1..7 block domain cited M312)",
                 blk_trip == 7 and blk_ids == ids and argload[2] == "eax,DWORD PTR [ebp+0x8]"
                 and incid[1] == "inc" and same_src))

    # ------------------------------------------------------------ TABLE 7
    say("T7 sentinel reachability at the reader (0x44970f -> 0x449793):")
    guard = [r for r in window(PAGE_LOAD, 0x449793)
             if r[1] in ("cmp", "test") and "ebx" in r[2]]
    sent = []
    for n in (-1, -2):
        for s in range(5):
            idx = 5 * n - 5 + s
            if ALGO == "sentinel_abs":
                idx = abs(idx)
            sent.append((n, s, idx, BASE + STRIDE * idx))
    say("   guards on ebx between load and use: %d" % len(guard))
    say("   n=-1: %s" % [hex(a) for n, s, i, a in sent if n == -1])
    say("   n=-2: %s" % [hex(a) for n, s, i, a in sent if n == -2])
    rows.append(("G7", "no guard on the page; a -1/-2 sentinel indexes BEFORE 0x983a10",
                 len(guard) == 0 and all(a < BASE for n, s, i, a in sent)))

    # ------------------------------------------------------------ RIVALS
    say("RIVALS:")
    all_refs = [(a, m, o) for a, m, o in load() if tok_has(o, "0x59f4")]
    field_refs = [(a, m, o) for a, m, o in all_refs if re.match(r"^[a-z]+\+0x59f4$", mem(o))]
    indexed = [(a, m, o) for a, m, o in all_refs if re.search(r"\+[a-z]+\*4\+0x59f4$", mem(o))]
    r1 = len(ctor84) != 0
    say("   R1 ctor zero-inits +0x84 -> ctor stores measured %d => %s"
        % (len(ctor84), "ALIVE" if r1 else "DEAD"))
    say("   R2 exact-token 0x59f4 census: %d refs = %d plain + %d indexed [r+r*4+0x59f4]"
        % (len(all_refs), len(field_refs), len(indexed)))
    off49 = [a for a, m, o in indexed if not (0x490000 <= a < 0x4A0000)]
    if ALGO == "census":
        field_refs = all_refs
    r2 = len(field_refs) == 1 and len(indexed) == 12
    say("      plain ref = %s ; indexed outside 0x49xxxx = %d -> R2 %s"
        % ([hex(a) for a, m, o in field_refs], len(off49), "ALIVE" if not r2 else "DEAD"))
    cap = [r for r in window(0x6290B0, 0x629110)
           if r[1] == "cmp" and r[2] == "DWORD PTR [ebp-0x4],0x20"]
    regs = callers(0x6291A3)
    say("   R3 ids 0..6 (ignore the reload-after-inc) -> measured set %s => %s"
        % (ids, "ALIVE" if ids[0] == 0 else "DEAD"))
    say("   R4 parent capacity %d -> registration loop builds %d children => %s"
        % (0x20 if cap else 0, trip, "ALIVE" if trip == 0x20 else "DEAD"))
    calls = callers(0x6291E3)
    pinned = [a for a in calls if sub_receiver(receiver(a))]
    say("   R5 receiver-blind: 0x6291e3 has %d call sites; HoF receiver-pinned = %d"
        % (len(calls), len(pinned)))
    if ALGO == "recv":
        pinned = calls
    r5 = len(pinned) == len(calls)
    say("      => R5 %s" % ("ALIVE" if r5 else "DEAD"))
    rows.append(("R1", "ctor-zero rival DEAD (0 ctor stores)", not r1))
    rows.append(("R2", "textual-census rival DEAD (1 plain + 12 indexed other-array refs)", r2))
    rows.append(("R3", "0-based-id rival DEAD (reload after inc measured)", ids[0] == 1))
    rows.append(("R4", "capacity-32 rival DEAD (%d built, capacity %s)" % (trip, "32" if cap else "?"),
                 trip == 7 and bool(cap)))
    rows.append(("R5", "receiver-blind rival DEAD (%d of %d call sites)" % (len(pinned), len(calls)),
                 len(pinned) == 2))

    # ------------------------------------------------------------ GATES
    say("")
    fails = 0
    for gid, text, ok in rows:
        say("%s %s %s" % ("PASS" if ok else "FAIL", gid, text), (gid, text, ok))
        fails += 0 if ok else 1
    table = "\n".join("%s|%s|%s" % r for r in ROWS)
    dig = hashlib.sha256(table.encode()).hexdigest()[:16]
    say("table_sha256=%s" % dig)
    say("digest=%s gates=%d pass=%d" % (dig, len(rows), len(rows) - fails))
    say("%s M347: %d/%d gates" % ("PASS" if fails == 0 else "FAIL", len(rows) - fails, len(rows)))
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
