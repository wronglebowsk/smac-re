#!/usr/bin/env python3
"""M306 (s264, STATIC, zero box): the function the Ghidra export NEVER MODELLED at 0x4f35e0.

M305 (merged, dc8efa6) proved index.csv is not a total function map: the call site 0x4f3e08
(a call to FUN_0051dcb0) sits outside its nearest index owner FUN_004f34b0 (0x4f34b0+298 ends
0x4f35da). This milestone answers, from the RAW objdump dump only (no Ghidra body exists):
  (a) BOUNDS: true start/end, justified from code (prologue, ret/epilogue census, nop padding,
      CFG reachability) — never from "the next index entry".
  (b) IDENTITY: callee census, data refs, and the guard on the FUN_0051dcb0 call at 0x4f3e08
      (what precedes it, what the predicate reads).
  (c) CALLERS: dump-wide xref census (call/jmp/jcc targets) + containment naming + the M305
      A11 stored-LE-dword scan of programs/terran.exe for an indirect entry.
  (d) WHY THE EXPORT MISSED IT — concrete checkable statements.
  (e) UNKNOWNs.

METHOD: every number printed is COMPUTED from scratch/m574/text.txt (objdump .text dump),
ghidra_out/index.csv, ghidra_out/shard_012.c and programs/terran.exe bytes; the table prints
first, then asserts; rival hypotheses are scored against the SAME printed numbers and FAIL.
stdout mirrors to evidence/m306_owner.txt. Run:  python3 scripts/m306_owner.py  (exit 0 = all hold)
"""
import bisect
import collections
import csv
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
INDEX = os.path.join(ROOT, "ghidra_out/index.csv")
SHARD12 = os.path.join(ROOT, "ghidra_out/shard_012.c")
GHDIR = os.path.join(ROOT, "ghidra_out")
EXE = os.path.join(ROOT, "programs/terran.exe")
EVID = os.path.join(ROOT, "evidence", "m306_owner.txt")

FN = 0x4F35E0             # the unmodelled candidate entry
NEIGHBOR = 0x4F4060       # next index.csv start after the gap
PREV_END = 0x4F35DA       # FUN_004f34b0 end (0x4f34b0 + 298)
CB = 0x4F3E08             # the FUN_0051dcb0 call site inside the gap (M305 finding)
CB_CALLEE = 0x51DCB0
JMP_SITE = 0x4F4133       # the single jmp into FN found in the dump

LINE_RX = re.compile(r"^ +([0-9a-f]{6,8}):\t([0-9a-f ]+?)\t\s*(.+?)\s*$")
CALL_RX = re.compile(r"^call\s+(?:0x)?([0-9a-f]{6,8})(?:\s|$)")
JCC_RX = re.compile(r"^(je|jne|jl|jge|jg|jle|jb|jae|ja|jbe|js|jns|jo|jno|jc|jnc)\s+(?:0x)?([0-9a-f]{4,8})$")
JMP_RX = re.compile(r"^jmp\s+(?:0x)?([0-9a-f]{4,8})$")
DSRX = re.compile(r"\bds:\[?(0x[0-9a-f]+)\]?")


class Out:
    def __init__(self, path):
        self.f = open(path, "w")

    def p(self, s=""):
        self.f.write(s + "\n")
        print(s)

    def close(self):
        self.f.close()


def load_dump():
    ins, raw, addrs, seen = {}, {}, [], set()
    with open(TEXT, errors="replace") as fh:
        for ln in fh:
            m = LINE_RX.match(ln)
            if not m:
                continue
            a = int(m.group(1), 16)
            if a not in seen:
                seen.add(a)
                ins[a] = m.group(3)
                raw[a] = m.group(2).replace(" ", "")
                addrs.append(a)
    addrs.sort()
    return ins, raw, addrs


def load_index():
    funcs = []
    with open(INDEX) as fh:
        for row in csv.DictReader(fh):
            funcs.append((int(row["addr"], 16), row["name"], int(row["size_bytes"]),
                          int(row["n_callers"]), row["shard"]))
    funcs.sort()
    return funcs


def owner_of(funcs, a):
    return ["%s @0x%x+%d" % (n, st, sz) for st, n, sz, nc, sh in funcs if st <= a < st + sz]


def name_at(funcs, a):
    i = bisect.bisect_right([f[0] for f in funcs], a) - 1
    st, n, sz, nc, sh = funcs[i]
    return n if st <= a < st + sz else None


def succ(addrs, idx, a):
    i = idx.get(a)
    return addrs[i + 1] if i is not None and i + 1 < len(addrs) else None


def cfg_walk(ins, addrs, start, cap=40000, limit=None, lo=None):
    """Reachable instruction set from `start` over the linear decode, optionally confined to
    [lo, limit). Branch/JMP edges crossing the bounds are recorded but NOT followed.
    Returns (reach, ret_sites, loop_backs, forward_edges, indirect_sites)."""
    idx = {a: i for i, a in enumerate(addrs)}
    reach, ret_sites, loop_backs, forward, indirect = set(), [], [], [], []
    frontier = [start]
    while frontier:
        pc = frontier.pop()
        while pc is not None and pc not in reach and len(reach) <= cap:
            if (limit is not None and pc >= limit) or (lo is not None and pc < lo):
                break
            reach.add(pc)
            t = ins.get(pc)
            if t is None:
                break
            op0 = t.split(None, 1)[0]
            if op0 in ("ret", "retf"):
                ret_sites.append(pc)
                break
            if op0 == "call":
                if not CALL_RX.match(t):
                    indirect.append(pc)
                pc = succ(addrs, idx, pc)
                continue
            mj = JMP_RX.match(t)
            if mj:
                tgt = int(mj.group(1), 16)
                (loop_backs if tgt <= pc else forward).append((pc, tgt))
                if not _oob(tgt, lo, limit):
                    frontier.append(tgt)
                break
            mjcc = JCC_RX.match(t)
            if mjcc:
                tgt = int(mjcc.group(2), 16)
                if tgt <= pc:
                    loop_backs.append((pc, tgt))
                else:
                    forward.append((pc, tgt))
                if not _oob(tgt, lo, limit):
                    frontier.append(tgt)
                pc = succ(addrs, idx, pc)
                continue
            if op0 == "jmp":
                indirect.append(pc)          # jmp *reg / jmp [mem] / jmp far
                break
            pc = succ(addrs, idx, pc)
    return reach, ret_sites, loop_backs, forward, indirect


def _oob(t, lo, limit):
    return (limit is not None and t >= limit) or (lo is not None and t < lo)


def scan_le(blob, addr):
    needle = addr.to_bytes(4, "little")
    hits, off = [], 0
    while True:
        i = blob.find(needle, off)
        if i < 0:
            return hits
        hits.append(i)
        off = i + 1


def main():
    out = Out(EVID)
    ins, raw, addrs = load_dump()
    funcs = load_index()
    out.p("M306 owner 0x%x — dump insns=%d index functions=%d" % (FN, len(addrs), len(funcs)))
    A = []

    def chk(label, cond):
        A.append((label, bool(cond)))
        out.p("A%-2d %s : %s" % (len(A), "OK " if cond else "FAIL", label))

    # ------------------------------------------------------------- (a) BOUNDS
    idx_all = {a: i for i, a in enumerate(addrs)}
    n1 = succ(addrs, idx_all, FN)
    n2 = succ(addrs, idx_all, n1)
    out.p("prologue @0x%x: %s | @0x%x %s | @0x%x %s" % (FN, ins[FN], n1, ins[n1], n2, ins[n2]))
    reach, ret_sites, loop_backs, forward, indirect = cfg_walk(ins, addrs, FN)
    rs = sorted(reach)
    end_ret = max(ret_sites)
    out.p("CFG from entry: reachable=%d insns  span=[0x%x..0x%x]  rets=%d  back-edges=%d  "
          "forward-edges=%s  indirect-jmp=%d"
          % (len(reach), rs[0], rs[-1], len(ret_sites), len(loop_backs),
             [(hex(a), hex(b)) for a, b in forward], len(indirect)))
    pad_after = [a for a in addrs if end_ret < a < NEIGHBOR]
    pad_nop = [a for a in pad_after if ins[a].startswith("nop")]
    pad_before = [a for a in addrs if PREV_END <= a < FN]
    pad_before_nop = [a for a in pad_before if ins[a].startswith("nop")]
    out.p("padding after last ret: %d insns (%d nop) 0x%x..0x%x" %
          (len(pad_after), len(pad_nop), pad_after[0], pad_after[-1]))
    out.p("padding before entry:   %d insns (%d nop) 0x%x..0x%x" %
          (len(pad_before), len(pad_before_nop), pad_before[0], pad_before[-1]))
    out.p("tail: %s" % " | ".join(ins[a] for a in rs[-5:]))
    out.p("epilogue census in span: leave=%d pop esi=%d pop ebx=%d pop edi=%d 'mov esp,ebp'=%d ret=%d"
          % (sum(1 for a in reach if ins[a].startswith("leave")),
             sum(1 for a in reach if ins[a].startswith("pop    esi")),
             sum(1 for a in reach if ins[a].startswith("pop    ebx")),
             sum(1 for a in reach if ins[a].startswith("pop    edi")),
             sum(1 for a in reach if ins[a].startswith("mov    esp,ebp")), len(ret_sites)))
    gaps = [(rs[i], rs[i + 1]) for i in range(len(rs) - 1) if rs[i + 1] - rs[i] > 16]
    out.p("largest unreachable gap inside span: %s" % (gaps[:4] or "none <=16B"))

    # ------------------------------------------------------------- (b) IDENTITY
    callees = collections.Counter()
    callee_sites = collections.defaultdict(list)
    for a in reach:
        if not ins[a].startswith("call"):
            continue
        mc = CALL_RX.match(ins[a])
        if mc:
            t = int(mc.group(1), 16)
            callees[t] += 1
            callee_sites[t].append(a)
    out.p("callee census (%d distinct callees, %d call sites):" % (len(callees), sum(callees.values())))
    for t, c in sorted(callees.items(), key=lambda kv: (-kv[1], kv[0])):
        out.p("  -> %s (0x%x) x%-2d @ %s" % (name_at(funcs, t) or "UNKNOWN", t, c,
               " ".join(hex(s) for s in sorted(callee_sites[t]))))
    dsrefs = collections.Counter()
    for a in reach:
        for m in DSRX.finditer(ins[a]):
            dsrefs[int(m.group(1), 16)] += 1
    out.p("ds: global refs (%d distinct): %s" % (len(dsrefs),
           " ".join("%s x%d" % (hex(g), c) for g, c in sorted(dsrefs.items()))))
    near = [a for a in addrs if a <= CB][-6:]
    out.p("the FUN_0051dcb0 call 0x%x, preceding 5 insns:" % CB)
    for a in near:
        out.p("  %s: %s" % (hex(a), ins[a]))
    preds = [(a, ins[a]) for a in reach
             if (JCC_RX.match(ins[a]) and int(JCC_RX.match(ins[a]).group(2), 16) == CB)
             or (JMP_RX.match(ins[a]) and int(JMP_RX.match(ins[a]).group(1), 16) == CB)]
    out.p("branch predecessors of 0x%x: %s" % (CB, [(hex(a), t) for a, t in preds] or "NONE (fall-through only)"))
    out.p("loop back-edges: %s" % [(hex(a), hex(t)) for a, t in loop_backs])
    out.p("loop-exit predicate (0x4f3de0..0x4f3df2):")
    for a in addrs:
        if 0x4F3DE0 <= a <= 0x4F3DF2:
            out.p("  %s: %s%s" % (hex(a), ins[a], "" if a in reach else "   [NOT reachable from entry]"))

    # ------------------------------------------------------------- (c) CALLERS
    pat = "%x" % FN
    call_sites, jmp_sites, other = [], [], []
    for a in addrs:
        if a == FN or pat not in ins[a]:
            continue
        t = ins[a]
        mc, mj, mjcc = CALL_RX.match(t), JMP_RX.match(t), JCC_RX.match(t)
        if mc and int(mc.group(1), 16) == FN:
            call_sites.append(a)
        elif (mj and int(mj.group(1), 16) == FN) or (mjcc and int(mjcc.group(2), 16) == FN):
            jmp_sites.append(a)
        else:
            other.append((a, t))
    out.p("dump-wide xref census for 0x%x: call=%d jmp/jcc-targets=%d other=%d" %
          (FN, len(call_sites), len(jmp_sites), len(other)))
    for a, t in [(a, ins[a]) for a in jmp_sites] + other:
        out.p("  ref @0x%x in %s : %s" % (a, "; ".join(owner_of(funcs, a)) or "outside any index fn", t))
    jp = [(a, ins[a]) for a in addrs
          if (JMP_RX.match(ins[a]) and int(JMP_RX.match(ins[a]).group(1), 16) == JMP_SITE)
          or (JCC_RX.match(ins[a]) and int(JCC_RX.match(ins[a]).group(2), 16) == JMP_SITE)]
    out.p("branch predecessors of jmp-site 0x%x: %s" % (JMP_SITE, [(hex(a), t) for a, t in jp]))
    blob = open(EXE, "rb").read()
    hits, hits2 = scan_le(blob, FN), scan_le(blob, NEIGHBOR)
    # positive controls so the scan can never pass vacuously: VAs of script strings that the
    # export demonstrably dereferences by pointer — stored dwords the scan MUST find.
    hc = {k: scan_le(blob, v) for k, v in
          {"s_baseobl_sm_pcx@0x68d180": 0x68D180, "s_DRONEREVOLT@0x68d190": 0x68D190,
           "PTR_s_SCRIPT@0x693b68": 0x693B68}.items()}
    out.p("terran.exe stored-LE-dword scan: 0x%x hits=%d %s | control-fn 0x%x hits=%d %s | "
          "positive controls: %s" %
          (FN, len(hits), [hex(h) for h in hits[:8]], NEIGHBOR, len(hits2), [hex(h) for h in hits2[:8]],
           {k: len(v) for k, v in hc.items()}))
    c1 = [a for a in addrs if CALL_RX.match(ins[a]) and int(CALL_RX.match(ins[a]).group(1), 16) == NEIGHBOR]
    out.p("jmp-site 0x%x sits in %s ; direct callers of 0x%x: %s" %
          (JMP_SITE, "; ".join(owner_of(funcs, JMP_SITE)) or "NONE", NEIGHBOR,
           [(hex(a), "; ".join(owner_of(funcs, a))) for a in c1]))

    # ------------------------------------------------------------- (d) WHY
    shard = open(SHARD12, errors="replace").read()
    b0 = shard.index("// ==== FUN_004f4060")
    b1 = shard.index("// ==== FUN_004f41f0")
    body = shard[b0:b1]
    body_calls = sorted(set(re.findall(r"FUN_004f3\w+", body)))
    # the decompiler fingerprint of THIS region inside the neighbour's body: the exact triad
    # (row-table call; zero-rebuild call) + the 21-iteration exit constant + the table count read
    triad = re.search(r"FUN_005a2ae0\([^)]*\);\s*\n\s*FUN_0051dcb0\(\);", body)
    fp_54 = len(re.findall(r"< 0x54\)", body))
    fp_af0 = body.count("DAT_00985af0")
    fp_af4 = body.count("DAT_00985af4")
    out.p("shard_012 FUN_004f4060 body %d chars; FUN_004f3xx names inside it: %s" %
          (len(body), body_calls or "NONE"))
    out.p("region fingerprint INSIDE the neighbour body: triad(FUN_005a2ae0;FUN_0051dcb0)=%s "
          "'< 0x54'=%d DAT_00985af0=%d DAT_00985af4=%d" % (bool(triad), fp_54, fp_af0, fp_af4))
    if triad:
        ls = body[:triad.start()].count("\n")
        out.p("triad at body-line %d:\n%s" % (ls, "\n".join(body.splitlines()[ls - 3:ls + 2])))
    mentions = sum(open(os.path.join(GHDIR, f), errors="replace").read().count("4f35e0")
                   for f in sorted(os.listdir(GHDIR)) if f.startswith("shard_"))
    out.p("export-wide mentions of '4f35e0' across all shards: %d ; index rows in (0x4f35da,0x4f4060): %d" %
          (mentions, sum(1 for st, n, sz, nc, sh in funcs if PREV_END < st < NEIGHBOR)))

    # ------------------------------------------------------------- ASSERTS
    chk("A1 entry 0x%x = push ebp; mov ebp,esp; sub esp,0x34" % FN,
        ins[FN].startswith("push   ebp") and ins[n1].startswith("mov    ebp,esp")
        and ins[n2].startswith("sub    esp,0x34"))
    chk("A2 CFG reaches %d insns; last reachable = ret @0x%x" % (len(reach), end_ret),
        len(reach) > 600 and rs[-1] == end_ret and ins[end_ret] == "ret")
    chk("A3 no forward CFG edge leaves [0x%x,0x%x): %s" % (FN, NEIGHBOR, [(hex(a), hex(b)) for a, b in forward]),
        all(FN <= b < NEIGHBOR for _, b in forward))
    chk("A4 contiguous body: %d unreached >16B gaps inside span; min reachable = 0x%x" % (len(gaps), rs[0]),
        not gaps and rs[0] == FN)
    chk("A5 boundary from code: %d insns after the ret@0x%x (ret=1B), all nop, ending 0x%x, then prologue at 0x%x" %
        (len(pad_after), end_ret, pad_after[-1], NEIGHBOR),
        ins[end_ret] == "ret" and len(raw[end_ret]) == 2 and end_ret == 0x4F4050 and
        len(pad_after) == 15 and len(pad_nop) == 15 and pad_after[-1] == 0x4F405F and
        all(ins[a].startswith("nop") for a in pad_after))
    chk("A6 %d nops 0x%x..0x%x close FUN_004f34b0 and align the entry 0x%x" %
        (len(pad_before_nop), PREV_END, FN - 1, FN), len(pad_before) == 6 and len(pad_before_nop) == 6)
    chk("A7 ret census=%d, all reachable; exactly 3 epilogues (pop ebx/esi/edi + mov esp,ebp each)" %
        len(ret_sites), len(ret_sites) == 3 and all(a in reach for a in ret_sites) and
        sum(1 for a in reach if ins[a].startswith("pop    ebx")) == 3 and
        sum(1 for a in reach if ins[a].startswith("pop    esi")) == 3 and
        sum(1 for a in reach if ins[a].startswith("pop    edi")) == 3 and
        sum(1 for a in reach if ins[a].startswith("mov    esp,ebp")) == 3)
    chk("A8 the FUN_0051dcb0 call site 0x%x is reachable inside this CFG (%s)" % (CB, CB in reach), CB in reach)
    chk("A9 call 0x%x has NO branch predecessor (preds=%d) — unconditional once its loop exits" % (CB, len(preds)),
        len(preds) == 0)
    chk("A10 dump-wide `call 0x%x` = %d (zero direct callers)" % (FN, len(call_sites)), len(call_sites) == 0)
    chk("A11 dump-wide refs to 0x%x = exactly one jmp @0x%x (jmp/jcc=%d other=%d)" %
        (FN, JMP_SITE, len(jmp_sites), len(other)), jmp_sites == [JMP_SITE] and not other)
    chk("A12 that jmp sits INSIDE the modelled neighbour [%s]; the entry is reached by an in-body tail-jump edge"
        % "; ".join(owner_of(funcs, JMP_SITE)), NEIGHBOR <= JMP_SITE < NEIGHBOR + 3058)
    n_ctrl = sum(len(v) for v in hc.values())
    chk("A13 stored-LE-dword scan (live: %d stored string-VA control hits %s): 0x%x hits=%d, 0x%x hits=%d "
        "— no static stored-pointer entry for either" % (n_ctrl, {k: len(v) for k, v in hc.items()},
                                                         FN, len(hits), NEIGHBOR, len(hits2)),
        n_ctrl >= 1 and len(hits) == 0 and len(hits2) == 0)
    chk("A14 neighbour body calls no FUN_004f35xx (%s) — the gap is NOT inlined into it" % body_calls,
        "FUN_004f35e0" not in body_calls)
    chk("A15 export mentions '4f35e0' %d times across all shards; index rows inside the gap = 0" % mentions,
        mentions == 0)
    chk("A16 index.csv has no function start in (0x4f35da, 0x4f4060) — the gap is a single owner",
        not any(PREV_END < st < NEIGHBOR for st, n, sz, nc, sh in funcs))
    chk("RIVAL1 FAILS 'the whole gap [0x4f35da,0x4f4060) is one function body': %d aligner nops + a fresh "
        "push-ebp/mov-esp/sub-esp prologue at 0x%x split it, and the CFG from 0x4f35e0 ends at ret 0x%x, "
        "never at 0x4f35da-style exits" % (len(pad_before_nop), FN, end_ret),
        len(pad_before_nop) == 6 and rs[-1] == end_ret)
    reach2, ret2, lb2, fwd2, _ = cfg_walk(ins, addrs, NEIGHBOR, limit=NEIGHBOR + 3058, lo=NEIGHBOR)
    fold_edges = []
    for a in reach2:
        mj, mc_ = JMP_RX.match(ins[a]), JCC_RX.match(ins[a])
        tgt = int(mj.group(1), 16) if mj else (int(mc_.group(2), 16) if mc_ else None)
        if tgt is not None and tgt < NEIGHBOR:
            fold_edges.append((a, tgt))
    out.p("control CFG from 0x%x confined to its own span: %d insns, %d rets; edges LEAVING the span "
          "downward: %s (region insns among them: %d)" %
          (NEIGHBOR, len(reach2), len(ret2), [(hex(a), hex(b)) for a, b in fold_edges],
           sum(1 for _, b in fold_edges if FN <= b <= end_ret)))
    out_edge_ct = sum(1 for a in reach if a in idx_all and (succ(addrs, idx_all, a) or 0) >= NEIGHBOR)
    chk("RIVAL2 FAILS 'region and 0x%x are ONE contiguous body (no real boundary)': the region is "
        "self-contained — own prologue, 3 rets, 15 nop pad, ZERO CFG edges from the region "
        "into the neighbour span (out-edges=%d); the connection is exactly %d one-way fold edge(s) %s — two complete "
        "functions joined by one tail-jump" % (NEIGHBOR, out_edge_ct, len(fold_edges),
                                               [(hex(a), hex(b)) for a, b in fold_edges]),
        not any(a >= NEIGHBOR for a in reach) and len(fold_edges) == 1 and fold_edges[0] == (JMP_SITE, FN))
    chk("RIVAL3 FAILS 'multiple jump-table/branch entries': calls=%d jcc-targets=%d jmp-targets=%d (total 1)" %
        (len(call_sites), len(jmp_sites) - 1, 1), len(call_sites) == 0 and len(jmp_sites) == 1 and not other)
    chk("RIVAL4 FAILS 'the 0x%x call carries its own guard predicate': branch preds=%d; the only gate is the "
        "enclosing loop's jl" % (CB, len(preds)), len(preds) == 0)
    chk("A17 ABSORPTION: the region's code is DECOMPILED inside the neighbour's body — "
        "triad(FUN_005a2ae0;FUN_0051dcb0)=%s, '< 0x54' loop-exit=%d, DAT_00985af0=%d, DAT_00985af4=%d"
        % (bool(triad), fp_54, fp_af0, fp_af4),
        bool(triad) and fp_54 >= 1 and fp_af0 >= 1 and fp_af4 >= 1)
    chk("RIVAL5 FAILS 'the 0x4f4133 jmp is dead code / never followed': its target's code is present in the "
        "neighbour's decompiled body (triad=%s) — Ghidra followed the edge and FOLDED the target, which is "
        "why no separate function was ever created" % bool(triad), bool(triad))

    out.p("== UNKNOWN ==")
    out.p("U1 exact semantics of the body (23 callees / 36 sites, _rand x3, script-string args at "
          "0x4f4042): only the census is settled; no per-branch meaning claimed.")
    out.p("U2 whether the entry executes in the live game: ZERO box time; static reachability via the "
          "0x4f4133 fold-edge only.")
    out.p("U3 the meaning of the 0x54 (21-iteration) cap and the FUN_005a2ae0 args [ebp-0x14]/[ebp-0x4].")
    out.p("U4 Ghidra's exact folding rule (tail-jump absorption into the containing function when the "
          "target has no symbol): INFERRED from A17+A11+A15, not re-derived by re-running Ghidra.")
    n_ok = sum(1 for _, c in A if c)
    out.p("== M306 acceptance: %d/%d OK ==" % (n_ok, len(A)))
    for label, c in A:
        if not c:
            out.p("  FAILED: %s" % label)
    out.close()
    sys.exit(0 if n_ok == len(A) else 1)


if __name__ == "__main__":
    main()
