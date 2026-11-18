#!/usr/bin/env python3
"""M317 (s288, STATIC zero-box): what does the goal engine FUN_00556690 DECIDE?

Pick (iii') post-M316 (NEXT_PROMPT OPEN shortlist). Settled footing - NAMED.md
## M250 / M252 / M274 / M275 / M276 / M310 (grep before re-deriving):
  - 14,349 B / 4,235 insns; called from exactly 2 sites: 0x52094f (FUN_005208f0)
    and 0x59dd43 (FUN_0059ce10, M94 per-player upkeep walker)      [M252 G7]
  - sole consumer of the coarse region map; FUN_00582340 called at 0x55878a +
    0x558812, both inside the engine                               [M252 G6/G7]
  - region-map stores: engine x5 (0x557fdf=8, 0x558516=dl, 0x558549=0,
    0x55855e=2, 0x55856b=7), values {0,2,7,8}                      [M250 G5]
  - ONE region bound cmp ecx,0x80 @0x558b1c; zero capacity clamps  [M274 G1]
  - ZERO indirect jumps -> CFG sound, reaching-defs decidable      [M275 G1]
  - entry fold edx = 8380*arg -> [ebp-0xc]; BYTE arrays e5a8/e628/eca8/ed28/eda8
    index block*8380 + region                                      [M276 G4]
  - goal band 0x94ee28, 75 x 16 B records; engine holds 35/65 band refs, is the
    ONLY +0C owner-field reader; knockout helper FUN_0056d690's ONLY caller is
    0x559e8e INSIDE the engine                                     [M310 A8/A11]

QUESTION (OPEN at NAMED ## M310): what the engine DECIDES. Method: census its
action vocabulary (call targets), its output vocabulary (memory stores), and
its decision inputs (conditional branches + the cmp/test that feeds each),
then the two caller contexts. Shared engine: m308_site_list.parse_text over
scratch/m574/text.txt (the m53j gz is pruned). Prints tables FIRST, asserts
every printed number. Skeleton stage: G1-G3 baseline + C1 call census.

    python3 -u scripts/m317_engine_decides.py   # stdout -> evidence/m317_engine_decides.txt
"""
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m308_site_list as M

ENG = 0x556690
SIZE = 14349
N_INSNS = 4235
N_CALLEES = 41
CALLERS_EXPECTED = {0x52094F: "FUN_005208f0", 0x59DD43: "FUN_0059ce10"}
HEXTOK = re.compile(r"0x[0-9a-f]+$")


def call_target(ops):
    """Direct target iff the FIRST operand token is a bare hex VA (far-call
    '0x43:0x...' and register/indirect forms fail fullmatch -> None)."""
    tok = ops.split()[0] if ops.split() else ""
    return int(tok, 16) if HEXTOK.fullmatch(tok) else None


def main():
    ins, order = M.parse_text()
    # CODE-mutation channel (mutation harness family 2): rewrite parsed
    # instructions BEFORE any measurement. Format: "addr|mn ops;addr|mn ops"
    patch = os.environ.get("M317_PATCH", "")
    npatched = 0
    if patch:
        for spec in patch.split(";"):
            if not spec.strip():
                continue
            addr_s, repl = spec.split("|", 1)
            a = int(addr_s, 16)
            assert a in ins, "patch target 0x%x does not exist (vacuous mutant)" % a
            mn, _, ops = repl.partition(" ")
            ins[a] = (mn, ops)
            npatched += 1
        print("patches applied: %d/%d" % (npatched, len([s for s in patch.split(';') if s.strip()])))
    M._INS, M._ORDER = ins, order
    idx = M.load_index()
    with open(M.INDEX) as f:
        rows = {int(r["addr"], 16): r for r in csv.DictReader(f)}
    er = rows[ENG]
    lo, hi = ENG, ENG + int(er["size_bytes"])
    win = [(a, ins[a][0], ins[a][1]) for a in order if lo <= a < hi]

    print("== G1 baseline: containment / size / instruction coverage ==")
    print("index row: addr=0x%x name=%s size=%s n_insns=%s n_callers=%s n_callees=%s shard=%s"
          % (ENG, er["name"], er["size_bytes"], er["n_insns"], er["n_callers"],
             er["n_callees"], er["shard"]))
    print("parsed window [0x%x,0x%x): %d insns, first=%s last=%s"
          % (lo, hi, len(win), win[0][1] + " " + win[0][2], win[-1][1] + " " + win[-1][2]))
    assert er["name"] == "FUN_00556690"
    assert int(er["size_bytes"]) == SIZE, "size drift"
    assert int(er["n_insns"]) == N_INSNS, "index n_insns drift"
    assert len(win) == N_INSNS, "parsed coverage != index n_insns"
    assert win[0][0] == ENG and win[-1][0] < hi
    print("G1 PASS")

    print("\n== G2 control flow: indirect jmp/call census (M275 re-pin) ==")
    indirect = [(a, mn, ops) for a, mn, ops in win
                if mn in ("jmp", "call") and call_target(ops) is None]
    rets = [a for a, mn, ops in win if mn == "ret"]
    jcc = [(a, mn, ops) for a, mn, ops in win
           if mn.startswith("j") and mn not in ("jmp",)]
    print("indirect jmp/call: %d   ret sites: %d   conditional branches: %d"
          % (len(indirect), len(rets), len(jcc)))
    for a, mn, ops in indirect:
        print("  INDIRECT 0x%x: %s %s" % (a, mn, ops))
    assert not indirect, "M275 law broken: indirect control flow present"
    print("G2 PASS")

    print("\n== G3 caller census: every direct call to the engine in .text ==")
    callers = {}
    for a in order:
        mn, ops = ins[a]
        if mn == "call" and call_target(ops) == ENG:
            callers[a] = M.contain(idx, a)
    for a in sorted(callers):
        print("  call site 0x%x in %s" % (a, callers[a]))
    assert callers == CALLERS_EXPECTED, "caller set drift: %r" % callers
    print("G3 PASS")

    print("\n== C1 action vocabulary: every call site inside the engine ==")
    sites = []
    for a, mn, ops in win:
        if mn == "call":
            t = call_target(ops)
            assert t is not None  # G2 already proved all calls direct
            sites.append((a, t, M.contain(idx, t)))
    byname = {}
    for a, t, nm in sites:
        byname.setdefault((t, nm), []).append(a)
    print("%d call sites -> %d distinct callees" % (len(sites), len(byname)))
    for (t, nm), addrs in sorted(byname.items()):
        print("  0x%x %-16s x%-2d @ %s" % (t, nm, len(addrs),
              " ".join("0x%x" % a for a in addrs)))
    assert len(byname) == int(er["n_callees"]) == N_CALLEES, \
        "distinct callee count != index n_callees"
    print("C1 PASS")

    print("\n== C2 output vocabulary: memory-store census inside the engine ==")
    STORE_MNS = {"mov", "xchg", "add", "or", "and", "sub", "xor", "inc", "dec", "not", "neg"}
    stores = []
    for a, mn, ops in win:
        if mn not in STORE_MNS:
            continue
        parts = M.split_ops(ops)
        dst = parts[0] if parts else ""
        if "PTR [" not in dst and "ds:0x" not in dst:
            continue
        if "[ebp" in dst or "[esp" in dst:
            kind = "stack-local"
        elif "ds:0x" in dst and "PTR [" not in dst:
            kind = "direct-global"
        else:
            # pointer-relative: an ABSOLUTE displacement (>= image data base
            # 0x400000) names a global array; the base reg carries block*8380
            # or 0. A small displacement is a struct/heap-record field.
            d = re.search(r"\+0x([0-9a-f]+)\]$", dst)
            if d and int(d.group(1), 16) >= 0x400000:
                kind = "global-displacement"
            else:
                kind = "struct-field"
        stores.append((a, mn, ops, kind))
    buckets = {}
    for a, mn, ops, kind in stores:
        buckets.setdefault(kind, []).append((a, mn, ops))
    print("total memory stores: %d  (stack-local %d / direct-global %d / global-displacement %d / struct-field %d)"
          % (len(stores), len(buckets.get("stack-local", [])),
             len(buckets.get("direct-global", [])), len(buckets.get("global-displacement", [])),
             len(buckets.get("struct-field", []))))
    print("-- direct-global stores (address : instruction) --")
    for a, mn, ops in buckets.get("direct-global", []):
        print("  0x%x: %s %s" % (a, mn, ops))
    print("-- global-displacement histogram (the output-array vocabulary) --")
    disp_map = {}
    for a, mn, ops in buckets.get("global-displacement", []):
        d = re.search(r"\+0x([0-9a-f]+)\]$", M.split_ops(ops)[0])
        assert d is not None  # classification matched the same dst string
        disp_map.setdefault("0x" + d.group(1), []).append(a)
    for disp, addrs in sorted(disp_map.items()):
        print("  %s x%-2d @ %s" % (disp, len(addrs), " ".join("0x%x" % a for a in addrs)))
    print("-- struct-field / bare-pointer stores (heap-record writes; def-walk territory) --")
    for a, mn, ops in buckets.get("struct-field", []):
        print("  0x%x: %s %s" % (a, mn, ops))
    # M250 G5 pin: the 5 region-map store sites and their value operands
    # (objdump prints immediates in hex: 0x8, not 8)
    M250_SITES = {0x557FDF: "0x8", 0x558516: "dl", 0x558549: "0x0", 0x55855E: "0x2", 0x55856B: "0x7"}
    smap = {a: (mn, ops) for a, mn, ops, k in stores}
    for a, val in M250_SITES.items():
        assert a in smap, "M250 store site 0x%x missing from census" % a
        mn, ops = smap[a]
        src = M.split_ops(ops)[1] if len(M.split_ops(ops)) > 1 else ""
        assert src == val, "M250 site 0x%x value drift: %r != %r" % (a, src, val)
    print("C2 PASS (M250 five-site pin intact; totals pinned after first clean run)")

    print("\n== C3 decision inputs: what feeds the 605 conditional branches ==")
    FLAG_MNS = {"cmp", "test", "add", "sub", "and", "or", "xor", "inc", "dec", "neg",
                "shl", "shr", "sar", "imul", "mul", "idiv", "div", "btc", "bts", "btr"}
    cls = {"global": [], "stack-local": [], "reg-imm": []}
    unattributed = []
    glob_tests = {}
    for i, (a, mn, ops) in enumerate(win):
        if not (mn.startswith("j") and mn != "jmp"):
            continue
        j = i - 1
        while j >= 0 and win[j][1] not in FLAG_MNS:
            j -= 1
        if j < 0:
            unattributed.append(a)
            continue
        fa, fmn, fops = win[j]
        if "ds:0x" in fops:
            c = "global"
            for tok in re.findall(r"ds:0x[0-9a-f]+", fops):
                glob_tests[tok] = glob_tests.get(tok, 0) + 1
        elif "PTR [ebp" in fops or "[esp" in fops:
            c = "stack-local"
        else:
            c = "reg-imm"
        cls[c].append((a, mn, fa, fmn, fops))
    print("classified: global %d / stack-local %d / reg-imm %d / unattributed %d (population %d)"
          % (len(cls["global"]), len(cls["stack-local"]), len(cls["reg-imm"]),
             len(unattributed), len(jcc)))
    assert len(cls["global"]) + len(cls["stack-local"]) + len(cls["reg-imm"]) + len(unattributed) == len(jcc) == 605
    print("-- globals tested, by branch count (the decision-input vocabulary) --")
    for tok, n in sorted(glob_tests.items(), key=lambda kv: (-kv[1], kv[0])):
        print("  %s x%d" % (tok, n))
    print("C3 PASS (population pinned; per-global counts pinned after first clean run)")

    print("\n== C4 decision OUTPUTS: argument decode at the goal-issue / cancel sites ==")
    issue_sites = [a for a, t, nm in sites if t in (0x56D350, 0x56D690, 0x56D780, 0x56D890)]
    pos = {a: i for i, (a, mn, ops) in enumerate(win)}

    def push_args(i, n=6):
        args, j = [], i - 1
        while j >= 0 and len(args) < n:
            pa, pmn, pops = win[j]
            if pmn in ("call", "ret"):
                break
            if pmn == "push":
                args.append(pops)
            j -= 1
        return list(reversed(args))

    def reg_source(i, reg):
        j = i - 1
        while j >= 0:
            pa, pmn, pops = win[j]
            if pmn in ("call", "ret"):
                return "<crosses-call>"
            d = M.split_ops(pops)[0] if pops else ""
            if pmn in ("mov", "lea", "movsx", "movzx", "pop") and d == reg:
                return "%s %s @0x%x" % (pmn, pops, pa)
            j -= 1
        return "<entry>"

    for a in sorted(issue_sites):
        t = call_target(ins[a][1])
        args = push_args(pos[a])
        print("  0x%x -> %s : %d pushes" % (a, M.contain(idx, t), len(args)))
        for k, arg in enumerate(args):
            extra = ""
            if not HEXTOK.fullmatch(arg) and arg in ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp"):
                extra = "   <- " + reg_source(pos[a], arg)
            print("    arg%d = %s%s" % (k + 1, arg, extra))
    KIND_AT = {0x556820: "0x2", 0x556831: "0x3", 0x55698E: "0x0", 0x556A4A: "0x29",
               0x556AED: "0x2", 0x556E79: "0x6", 0x558ADC: "0x29"}
    n_faction_direct = 0
    for a in sorted(issue_sites):
        t = call_target(ins[a][1])
        args = push_args(pos[a])
        if t == 0x56D350:
            assert len(args) == 6, "AddGoal site 0x%x: %d pushes != 6" % (a, len(args))
            assert args[0] == "0xffffffff", "owner != -1 at 0x%x" % a
            assert args[4] == KIND_AT[a], "kind drift at 0x%x: %s" % (a, args[4])
            src6 = reg_source(pos[a], args[5]) if args[5] in ("eax", "ebx", "ecx", "edx", "esi", "edi") else ""
            if "[ebp+0x8]" in src6:
                n_faction_direct += 1
    assert n_faction_direct >= 6, "block arg not traceably the faction param at >=6 sites"
    # coordinate sources: base x/y at +0/+2; terraform pair at +0x2c/+0x2e
    assert "0x95da10" in reg_source(pos[0x556820], "edi") and "0x95da12" in reg_source(pos[0x556820], "ebx")
    assert "0x95da3c" in reg_source(pos[0x556A4A], "ecx") and "0x95da3e" in reg_source(pos[0x556A4A], "eax")
    # remover: kind 8, (p1,p2) read back from the goal band itself
    rargs = push_args(pos[0x559809])
    assert len(rargs) == 5 and rargs[3] == "0x8"
    assert "0x94ee30" in reg_source(pos[0x559809], rargs[1])
    assert "0x94ee2c" in reg_source(pos[0x559809], rargs[2])
    # knockout: single arg = the faction param
    kargs = push_args(pos[0x559E8E])
    assert len(kargs) == 1 and "[ebp+0x8]" in reg_source(pos[0x559E8E], kargs[0])
    assert len([a for a in issue_sites if call_target(ins[a][1]) == 0x56D350]) == 7
    assert 0x559E8E in issue_sites and 0x559809 in issue_sites  # knockout + remover (M310/M316)
    print("C4 PASS (kinds {0,2,3,6,41} pinned per site; owner=-1 x7; remover kind 8; knockout=faction)")

    print("\n== C5 caller context ==")
    # caller B: the engine call 0x59dd43 sits in the M305-pinned per-player loop
    assert 0x59CE92 <= 0x59DD43 <= 0x59E2A6, "engine call outside the M305 walker loop"
    print("caller B FUN_0059ce10: call 0x59dd43 inside loop [0x59ce92,0x59e2a6] (M305 P1 pin)")
    # caller A: FUN_005208f0 is 785 B / 223 insns - print its call's push args + enclosing span
    ar = rows[0x5208F0]
    alo, ahi = 0x5208F0, 0x5208F0 + int(ar["size_bytes"])
    awin = [(a, ins[a][0], ins[a][1]) for a in order if alo <= a < ahi]
    ai = next(i for i, (a, mn, ops) in enumerate(awin) if a == 0x52094F)
    print("caller A FUN_005208f0 (%s B, %d insns): pushes before the engine call:"
          % (ar["size_bytes"], len(awin)))
    j = ai - 1
    while j >= 0 and awin[j][1] not in ("call", "ret"):
        if awin[j][1] == "push":
            print("    push %s @0x%x" % (awin[j][2], awin[j][0]))
        j -= 1
    print("C5 PASS (caller A context read; loop pin asserted)")

    print("\n== C6 loop inventory: back-edges + walk strides ==")
    back = []
    for a, mn, ops in win:
        if mn.startswith("j"):
            t = ops.split()[0] if ops.split() else ""
            if HEXTOK.fullmatch(t) and int(t, 16) < a:
                back.append((a, mn, int(t, 16)))
    print("back-edges: %d" % len(back))
    strides = {}
    for a, mn, ops in win:
        if mn == "add":
            m2 = re.fullmatch(r"(e[a-z]{2}),0x([0-9a-f]+)", ops)
            if m2 and m2.group(1) != "esp":
                strides.setdefault("0x" + m2.group(2), []).append(a)
    for s, addrs in sorted(strides.items()):
        print("  add reg,%s x%d @ %s" % (s, len(addrs), " ".join("0x%x" % a for a in addrs)))
    assert len(back) == 44
    assert strides.get("0x130") == [0x556BC0, 0x556C17, 0x557763, 0x5582FA, 0x558DD6], "base-array walk stride"
    assert strides.get("0x20bc") == [0x557B69, 0x558BCC], "faction-block walk stride"
    assert strides.get("0x10") == [0x5580D3], "goal-band walk stride"
    assert ins[0x558B1C] == ("cmp", "ecx,0x80"), "M274 region bound drift"
    assert (0x558B25, "jl", 0x557FB8) in back, "region-loop back-edge drift"
    print("C6 PASS (44 back-edges; base 0x130 x5 / block 0x20bc x2 / goal 0x10 x1; region bound 0x80)")

    print("\n== PIN: measured totals (asserted, not prose) ==")
    assert len(stores) == 358
    assert {k: len(v) for k, v in buckets.items()} == {
        "stack-local": 239, "direct-global": 2, "global-displacement": 104, "struct-field": 13}
    assert len(disp_map) == 40
    assert len(cls["global"]) == 18 and len(cls["stack-local"]) == 26 and len(cls["reg-imm"]) == 561
    assert glob_tests == {"ds:0x692184": 5, "ds:0x92a37c": 4, "ds:0x92a378": 2, "ds:0x985af0": 2,
                          "ds:0x91b5b4": 1, "ds:0x92ada0": 1, "ds:0x985ab8": 1,
                          "ds:0x985af4": 1, "ds:0x985b10": 1}
    assert len(sites) == 112
    print("PIN PASS: 358 stores (239/2/104/13), 40 output displacements, 605 branches (18/26/561), 112 call sites")

    print("\nM317 CENSUS GREEN: G1-G3 + C1-C6 + PIN (decision map in evidence header)")
    return 0


if __name__ == "__main__":
    sys.exit(main())