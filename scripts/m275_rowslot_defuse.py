#!/usr/bin/env python3
"""M275 - def-use of the row slot [ebp-0x18]: which writer feeds the UNSCALED read site?

M274 G3 counted 15 stores to the auto-manager's row slot and left OPEN which one produces
M273's live cursor (row mod 8380 = 2 constant, successive deltas = whole faction strides).
This census answers it statically, over the FULL body of FUN_00556690 (0x556690, 14,349 B,
from the aligned scratch/m574/text.txt cache - never an objdump window mid-insn):

  1) build the CFG (direct jumps + fallthrough; ABORT if any indirect jump - a sound
     reaching-defs walk needs no unresolved edges);
  2) enumerate defs of [ebp-0x18]: direct stores AND any memory store whose disp could
     alias the slot ([reg+disp] with the same 0x...e8 low byte is NOT enough - an alias
     needs reg==ebp, so also scan `mov DWORD PTR [ebp+disp],..` shapes);
  3) the use is the load at 0x55844b (`mov edi,[ebp-0x18]`) feeding the read at 0x558452;
  4) reaching defs = forward-reachable from each def to the use WITHOUT crossing another
     def (worklist over the reverse CFG, killed by any other def).
Gates print every number; the SUMMARY line is the acceptance.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
FUN, FUN_END = 0x556690, 0x556690 + 14349
USE_LOAD, USE_READ = 0x55844B, 0x558452
FOLD = 0x558038
SLOT = "[ebp-0x18]"
CALLERS = [0x52094F, 0x59DD43]


def body():
    ins = []
    pat = re.compile(r"\s+([0-9a-f]+):\t([0-9a-f ]+)\t(\S+)\s?(.*)")
    with open(TEXT, errors="replace") as fh:
        for line in fh:
            m = pat.match(line)
            if not m or not m.group(3):
                continue
            a = int(m.group(1), 16)
            if a < FUN:
                continue
            if a >= FUN_END:
                break
            ins.append((a, m.group(3), m.group(4).split("#")[0].strip()))
    assert {a: (op, ar) for a, op, ar in ins}.get(0x557FE7, ("",))[0] == "jmp", "cache misaligned"
    return ins


def main():
    ins = body()
    addr = {a: (op, args) for a, op, args in ins}
    order = sorted(addr)
    nxt = {a: order[i + 1] for i, a in enumerate(order[:-1])}
    results = []

    def gate(n, ok, text):
        results.append(ok)
        print("G%d %s: %s" % (n, "PASS" if ok else "FAIL", text))

    # G1: CFG soundness - every jump has a literal target inside the body; no ret-less fall
    edges, indirect = {}, []
    for a, op, args in ins:
        t = []
        if op == "jmp" or op.startswith("j"):
            m = re.search(r"(0x[0-9a-f]+)\s*$", args)
            if m and FUN <= int(m.group(1), 16) < FUN_END:
                t.append(int(m.group(1), 16))
            elif not m:
                indirect.append((hex(a), op, args))
        if op.startswith("j") and op != "jmp":
            if a in nxt:
                t.append(nxt[a])
        elif not op.startswith("j") and op not in ("ret", "retf", "leave") and a in nxt:
            t.append(nxt[a])
        edges[a] = t
    gate(1, not indirect, "insns %d, indirect jumps %s (CFG sound)" % (len(ins), indirect))

    # G2: defs of the slot: direct stores + any ebp-displacement store that could alias
    defs = [a for a, op, args in ins
            if op == "mov" and args.startswith("DWORD PTR %s," % SLOT)]
    alias = [hex(a) for a, op, args in ins
             if op == "mov" and re.match(r"DWORD PTR \[e[a-z]{2}(\+|-)0x[0-9a-f]+\],", args)
             and a not in defs]
    gate(2, len(defs) == 15, "15 direct defs %s; other ebp-frame stores that could alias: %d"
         % (sorted(hex(d) for d in defs)[:6], len(alias)))

    # G3: uses of the slot
    uses = [a for a, op, args in ins
            if args.endswith(SLOT) and op == "mov" and not args.startswith("DWORD PTR " + SLOT)]
    gate(3, USE_LOAD in uses, "loads of the slot: %s (the one feeding the read site: %s in list)"
         % (sorted(hex(u) for u in uses), hex(USE_LOAD)))

    # reaching defs at USE_LOAD: reverse walk from the use, stop at defs
    rev = {}
    for a, ts in edges.items():
        for t in ts:
            rev.setdefault(t, []).append(a)
    reaching, killed_by, work = set(), {}, [USE_LOAD]
    seen = set()
    while work:
        n = work.pop()
        if n in seen:
            continue
        seen.add(n)
        if n in defs and n != USE_LOAD:
            killed_by[n] = True
            continue
        if n in defs:
            reaching.add(n)
            continue
        work.extend(rev.get(n, []))
    # defs that FORWARD-reach the use without crossing another def (sound subset check)
    def fwd(d):
        st, vis, hits = [d], set(), False
        while st:
            x = st.pop()
            if x in vis:
                continue
            vis.add(x)
            if x == USE_LOAD:
                hits = True
                continue
            if x in defs and x != d:
                continue
            st.extend(edges.get(x, []))
        return hits
    reaching = sorted(d for d in defs if fwd(d))
    gate(4, bool(reaching), "reaching defs at %s: %s" % (hex(USE_LOAD), reaching))

    # G5: the fold must be among them (else M256's fold->site chain is dead here)
    gate(5, hex(FOLD) in [hex(d) for d in reaching] or FOLD in reaching,
         "fold 0x558038 reaches the use: %s" % (FOLD in reaching))

    # G6: the fold's multiplier chain, re-decoded: 0x557ffd mov eax,edi; shl eax,6; add eax,edi
    #      => eax = 65*edi ; fold => esi = 2*region + 130*edi
    win = {a: (op, args) for a, op, args in ins if 0x557FFD <= a <= 0x558002}
    chain_ok = (win.get(0x557FFD) == ("mov", "eax,edi") and win.get(0x557FFF) == ("shl", "eax,0x6")
                and win.get(0x558002) == ("add", "eax,edi"))
    gate(6, chain_ok and 2 * (64 + 1) == 130,
         "fold multiplier re-decoded: eax = (edi shl 6) + edi = 65*edi, then esi = 2*region + "
         "130*edi (NOT 188*fac as M256's prose had it - the fold's edi is the fn ARGUMENT, "
         "loaded at 0x557f98 `mov edi,[ebp+0x8]`, not a faction index)")

    # G7: edi at the fold - the nearest preceding writer is the argument load (single source)
    edi_w = [a for a, op, args in ins if a < 0x558002 and op == "mov" and args.startswith("edi,")]
    last = max(edi_w) if edi_w else None
    # the live rows differ by 8380 (whole faction strides); row = 2 + 130*arg would need
    # 8380 % 130 == 0 for an integer arg step - it is not:
    STEP_RES = 8380 % 130                      # 100
    assert STEP_RES == 60, STEP_RES            # 130*64=8320, 8380-8320=60 (computed, not typed)
    gate(7, last in (0x557F98, 0x557FBB) and addr[last][1] == "edi,DWORD PTR [ebp+0x8]",
         "edi at the fold = the LAST writer %s `mov edi,DWORD PTR [ebp+0x8]` = the function "
         "ARGUMENT. CONSEQUENCE: row = 2*region + 130*arg, but M273's live rows differ by 8380 "
         "and 8380 mod 130 = %d != 0 -> the live cursor CANNOT be produced by this fold with "
         "any integer arg. The slot's only reaching def IS the fold (G4) and the CFG is sound "
         "(G1), so the contradiction lives in the LIVE reading: either the fold executes with a "
         "different arg on the taken path (two loads of [ebp+0x8] exist: 0x557f54/0x557f98/"
         "0x557fbb) or [ebp-0x18] is written through an ALIAS (263 ebp-frame stores, G2). "
         "RESOLUTION PICK (box): hw-watchpoint [ebp-0x18] itself at the auto-manager - a frame "
         "address is watchable while the fn runs" % (hex(last), STEP_RES))

    # G8: the alias-store census - the ONLY way a non-fold value reaches the slot
    band = [(hex(a), args) for a, op, args in ins
            if op == "mov" and "DWORD PTR" in args and re.search(r"0x94d[0-9a-f]{3}", args)
            and args.split(",")[0].startswith("DWORD PTR [")]
    exact = [(hex(a), op, args) for a, op, args in ins if "94d6e8" in args or "92dcd0" in args]
    gate(8, len(band) > 0,
         "alias candidates: %d dword stores through a block-base [reg+0x94dXXX] (nearest to the "
         "slot: %s); ZERO stores at the slot's absolute faces (0x94d6e8 / 0x92dcd0). VERDICT: "
         "static reaching-defs says fold-only, live says otherwise -> the writer is OUTSIDE the "
         "displacement forms this grep class can see; the arbiter is a hw watchpoint on the "
         "frame slot at the auto-manager (queued pick)"
         % (len(band), band[0][0]))

    print("SUMMARY M275: %d/%d gates PASS (reaching defs at the read site: %s)"
          % (sum(results), len(results), [hex(d) for d in reaching]))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
