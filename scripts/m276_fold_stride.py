#!/usr/bin/env python3
"""M276 - the fold's coefficient IS the faction stride: 2*region + 8380*arg.

M275 (s215) narrowed the row slot [ebp-0x18]'s reaching def at the read-site feeder load
0x55844b to ONE writer - the fold at 0x558038 - and then declared the fold's arithmetic
`esi = 2*region + 130*edi` IRRECONCILABLE with M273's live rows (which differ by whole
faction strides of 8380): "8380 mod 130 = 60 != 0 -> the missing writer is an unmodeled
alias/leg", and queued a box pick (hw-watchpoint the frame slot).

M275's G6 never evaluated the chain. It hand-wrote the expression at the MIDPOINT of the
fold (`add eax,edi` = 65*edi, doubled = 130) and stopped there. The chain continues:
    mov eax,edi; shl eax,0x6; add eax,edi          eax =   65*edi
    lea eax,[edi+eax*2]                            eax =  131*edi
    shl eax,0x4;  sub eax,edi                      eax = 2095*edi
    lea esi,[ecx+eax*2];  shl esi,1                esi = 2*ecx + 8380*edi
2095 is the per-faction block's DWORD count (2095*4 = 8380, the stride `f*8380` the field
atlas already records), so the fold multiplies the ARGUMENT by the FACTION STRIDE and there
is no missing writer at all.

Method (this file): SYMBOLIC evaluation of the window, not prose. Each register carries a
linear form (coef_edi, coef_ecx, const) mod 2**32; a write through an unknown clobbers it to
None; the gate asserts the FORM at the store. Then the whole thing is replayed against M273's
RECORDED live log (no box time): every UNSCALED event's slot value must equal
2*region + 8380*faction with faction == cp, and the same rows must REFUTE the two published
coefficients (130 and 188) - a discriminating fit, not a shape the rival models also pass.
Gates print every number; the SUMMARY line is the acceptance. Exit 0 = measured.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
LOG = os.path.join(ROOT, "evidence", "m273w3.gdblog")
ATLAS = os.path.join(ROOT, "docs", "field-atlas-faction.md")
NAMED = os.path.join(ROOT, "NAMED.md")
M275 = os.path.join(ROOT, "scripts", "m275_rowslot_defuse.py")

FUN, FUN_END = 0x556690, 0x556690 + 14349
FOLD = 0x558038              # mov DWORD PTR [ebp-0x18],esi
SLOT = "[ebp-0x18]"
STRIDE = 8380                # the per-faction block stride (2095 dwords)
PUBLISHED = {"M275 (130)": 130, "M274 G6 (188)": 188}
M32 = 1 << 32
ATOMS = {"edi": (1, 0, 0), "ecx": (0, 1, 0)}
W32 = re.compile(r"^[de]?(a|b|c|d)??x$")


def body():
    """The full body of FUN_00556690 from the ALIGNED cache (skill law: never an
    objdump --start-address that can land mid-instruction)."""
    ins, pat = [], re.compile(r"\s+([0-9a-f]+):\t([0-9a-f ]+)\t(\S+)\s?(.*)")
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
    addr = {a: (op, ar) for a, op, ar in ins}
    assert addr.get(0x557FE7, ("",))[0] == "jmp", "cache misaligned at 0x557fe7"
    assert addr.get(FOLD, ("",))[0:2] == ("mov", "DWORD PTR %s,esi" % SLOT), \
        "cache/fold mismatch at %#x" % FOLD
    return ins, addr


def full(r):
    """Map any register spelling to its 32-bit container."""
    r = r.strip().rstrip("s")
    base = {"eax": "eax", "ax": "eax", "al": "eax", "ah": "eax",
            "ecx": "ecx", "cx": "ecx", "cl": "ecx", "ch": "ecx",
            "edx": "edx", "dx": "edx", "dl": "edx", "dh": "edx",
            "ebx": "ebx", "bx": "ebx", "bl": "ebx",
            "esi": "esi", "si": "esi", "sil": "esi",
            "edi": "edi", "di": "edi", "dil": "edi",
            "ebp": "ebp", "bp": "ebp", "esp": "esp", "sp": "esp"}.get(r)
    return base


def lin(v):
    return None if v is None else v


def add(a, b, sign=1):
    if a is None or b is None:
        return None
    return ((a[0] + sign * b[0]) % M32, (a[1] + sign * b[1]) % M32,
            (a[2] + sign * b[2]) % M32)


def scale(a, n):
    if a is None:
        return None
    return ((a[0] << n) % M32, (a[1] << n) % M32, (a[2] << n) % M32)


def parse_atom(tok):
    """'edi' / '0x10' -> linear form (or ('reg', name) for a bare register)."""
    tok = tok.strip()
    if "*" in tok:
        r, n = tok.split("*")
        return scale(parse_atom(r), 0) if False else mul(parse_atom(r.strip()), int(n, 0))
    m = re.fullmatch(r"(-?)0x([0-9a-f]+)|(-?)(\d+)", tok)
    if m:
        v = int((m.group(1) or "") + (m.group(2) or m.group(4)), 16 if m.group(2) else 10)
        return (0, 0, v % M32)
    f = full(tok)
    return f  # a register: caller resolves it in the state


def mul(a, n):
    if a is None:
        return None
    return ((a[0] * n) % M32, (a[1] * n) % M32, (a[2] * n) % M32)


def resolve(tok, st):
    """Operand -> linear form; None if it involves anything unmodeled."""
    tok = tok.strip()
    if tok.startswith("["):
        return None
    m = re.fullmatch(r"(\w+)(\s*\*\s*(0x[0-9a-f]+|\d+))?", tok)
    if not m:
        return None
    f = full(m.group(1))
    if f is None:
        return None
    v = st.get(f, ("unknown",))
    if v == "unknown" or v is None:
        return None
    if m.group(2):
        return mul(v, int(m.group(3), 0))
    return v


def dst_regs(op, args):
    """Which 32-bit containers this instruction writes."""
    a = args.split(",")
    out = []
    first = a[0].strip()
    if first.startswith("[") or op in ("cmp", "test", "push", "pop", "jmp", "jcc", "sete",
                                       "setne", "setl", "setge", "nop", "lea") and False:
        pass
    if op.startswith("c") and op[1:] in ("mp",) or op in ("test", "cmp"):
        return out
    if op in ("push", "pop", "call", "jmp", "ret", "nop"):
        return ["esp"] if op in ("push", "pop") else out
    if op.startswith("set"):
        return out
    if op in ("lea",):
        tgt = first
    else:
        tgt = first
    if tgt.startswith("["):
        return out
    f = full(tgt)
    return [f] if f else out


def evaluate(ins, addr, lo, hi):
    """Symbolic linear-form evaluation of [lo,hi]; returns (state, trace, unknown_writes)."""
    st = {k: "unknown" for k in ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp")}
    for k, v in ATOMS.items():
        st[k] = v
    trace, unknown = [], []
    a = lo
    order = sorted(addr)
    while a <= hi:
        if a not in addr:
            a = min((x for x in order if x > a), default=hi + 1)
            continue
        op, args = addr[a]
        ops = args.split(",")
        lhs = ops[0].strip()
        rhs = ops[1].strip() if len(ops) > 1 else None
        val = None
        if op == "mov":
            val = resolve(rhs, st) if not rhs.startswith("[") else None
        elif op == "xor":
            f1, f2 = full(lhs), full(rhs)
            val = (0, 0, 0) if f1 == f2 and f1 else None
        elif op == "shl":
            n = int(rhs, 0)
            val = scale(st.get(full(lhs)), n) if full(lhs) else None
        elif op == "add":
            r = resolve(lhs, st)
            s = resolve(rhs, st)
            val = add(r, s) if r is not None and s is not None else None
        elif op == "sub":
            r = resolve(lhs, st)
            s = resolve(rhs, st)
            val = add(r, s, -1) if r is not None and s is not None else None
        elif op == "lea":
            inner = rhs.strip()[1:-1]
            acc = (0, 0, 0)
            ok = True
            for term in inner.split("+"):
                m = re.fullmatch(r"(\w+)(\*(0x[0-9a-f]+|\d+))?", term.strip())
                if not m:
                    ok = False
                    break
                f = full(m.group(1))
                v = st.get(f) if f else None
                if v == "unknown" or v is None:
                    # a term referencing an unmodeled register: only allowed if it is the
                    # memory base, which lea [reg+disp] would make opaque
                    ok = False
                    break
                t = v if not m.group(2) else mul(v, int(m.group(3), 0))
                acc = add(acc, t)
            val = acc if ok else None
        for r in dst_regs(op, args):
            if r is None:
                continue
            if op in ("cmp", "test"):
                continue
            st[r] = "unknown" if val is None else val
            if val is None and r in ("edi", "ecx"):
                unknown.append((hex(a), op, args))
        if op not in ("nop",):
            trace.append((hex(a), op, args, st.get("esi"), st.get("eax")))
        a = min((x for x in order if x > a), default=hi + 1)
    return st, trace, unknown


def main():
    ins, addr = body()
    results = []

    def gate(n, ok, text):
        results.append(ok)
        print("G%d %s: %s" % (n, "PASS" if ok else "FAIL", text))

    # ---- locate the fold chain: nearest preceding `mov eax,edi` before the store
    chain_start = max(a for a, op, ar in ins if a < FOLD and (op, ar) == ("mov", "eax,edi"))
    gate(1, chain_start == 0x557FFD,
         "fold chain starts at %#x (`mov eax,edi`), store at %#x - %d insns in the window"
         % (chain_start, FOLD, sum(1 for a, _, _ in ins if chain_start <= a <= FOLD)))

    # ---- G2: the window writes NEITHER atom (edi, ecx), so the form is exact
    st, trace, unknown = evaluate(ins, addr, chain_start, FOLD)
    gate(2, not unknown,
         "atoms edi/ecx are written 0 times inside the chain (opaque writes to them: %d) - "
         "the linear form is exact, not inferred" % len(unknown))

    # ---- G3: the form AT THE STORE
    esi = st.get("esi")
    ce, cc, k = esi if esi else (None, None, None)
    print("    chain:")
    for a, op, args, s_esi, s_eax in trace:
        if op in ("mov", "shl", "add", "sub", "lea") and args.split(",")[0].strip() in (
                "eax", "esi"):
            print("      %s %s %s -> esi=%s eax=%s" % (a, op, args, s_esi, s_eax))
    form = "esi = %d*edi + %d*ecx + %d" % (ce, cc, k)
    gate(3, esi is not None and ce == STRIDE and cc == 2 and k == 0,
         "the store's value, evaluated symbolically: %s  ==  2*region + 8380*arg "
         "(2095 dwords x 4 = 8380, the per-faction block stride)" % form)

    # ---- G4: what the atoms ARE (last writer before the chain)
    def last_writer(reg, before):
        f = full(reg)
        for a, op, args in sorted((i for i in ins if i[0] < before), key=lambda x: -x[0]):
            if f in [x for x in dst_regs(op, args) if x]:
                return a, op, args
        return None, None, None
    wa, wop, war = last_writer("edi", chain_start)
    ca, cop, car = last_writer("ecx", chain_start)
    loop_cmp = [a for a, op, args in ins if op == "cmp" and args == "ecx,0x80"]
    gate(4, wa is not None and "[ebp+0x8]" in (war or "") and ca is not None
         and bool(loop_cmp),
         "arg atom: last edi writer %#x `%s %s` = the function ARGUMENT; region atom: last ecx "
         "writer %#x `%s %s`; the loop bound `cmp ecx,0x80` sits at %s"
         % (wa, wop, war, ca, cop, car, [hex(x) for x in loop_cmp]))

    # ---- G5: the constant is the ALREADY-RECORDED faction stride (cross-check, computed)
    atlas = open(ATLAS, errors="replace").read() if os.path.exists(ATLAS) else ""
    gate(5, 2095 * 4 == STRIDE and ("8,380" in atlas or "8380" in atlas),
         "2095 dwords x 4 = %d, and docs/field-atlas-faction.md already records %s as the "
         "per-faction block stride - the fold's coefficient is THAT constant"
         % (STRIDE, "8,380"))

    # ---- G6/G7: replay M273's RECORDED live rows against the three models
    kv = re.compile(r"^M273S UNSCALED "
                    r"((?:[a-z][a-z0-9_]*=-?\S+ )+)(round=-?\d+) (cp=\d+)\s*$")
    ev = []
    for ln in open(LOG, errors="replace"):
        m = kv.match(ln.strip())
        if not m:
            continue
        d = {k: int(v, 0) for k, v in
             (p.split("=", 1) for p in m.group(1).split())}
        d["cp"] = int(m.group(3).split("=")[1])
        d["round"] = int(m.group(2).split("=")[1])
        ev.append(d)
    print("    live rows (evidence/m273w3.gdblog, %d UNSCALED events):" % len(ev))
    fit8380, ref = [], []
    for e in ev:
        q, r = divmod(e["s18"] - 2 * e["s10"], STRIDE)
        ok = (r == 0 and q == e["cp"])
        fit8380.append(ok)
        ref.append("      row=%-6d cp=%d  s18 = 2*%d + 8380*%d  %s"
                   % (e["row"], e["cp"], e["s10"], q, "OK" if ok else "MISMATCH"))
    print("\n".join(ref))
    deltas = [b["s18"] - a["s18"] for a, b in zip(ev, ev[1:])]
    gate(6, len(ev) >= 7 and all(fit8380),
         "LIVE FIT %d/%d: every recorded slot value == 2*region + 8380*cp (cp = the faction "
         "index in cur_player); successive deltas %s are whole 8380 strides"
         % (sum(fit8380), len(ev), sorted(set(deltas))))
    rivals = {}
    for label, coef in PUBLISHED.items():
        hits = sum(1 for e in ev if (e["s18"] - 2 * e["s10"]) % coef == 0)
        rivals[label] = hits
        print("      %s fits %d/%d live rows" % (label, hits, len(ev)))
    gate(7, all(h == 0 for h in rivals.values()),
         "DISCRIMINATOR: the two published coefficients fit %s of %d live rows - the fit above "
         "is not a shape all models share (skill law: refuse a shape your model and the null "
         "agree on)" % (list(rivals.values()), len(ev)))

    # ---- G8: the registry and the superseded instrument carry the correction
    named = open(NAMED, errors="replace").read()
    m275src = open(M275, errors="replace").read()
    m274blk = named.split("## M274")[1].split("## M275")[0] if "## M274" in named else ""
    m275blk = named.split("## M275")[1].split("## B7")[0] if "## M275" in named else ""
    need = "M276 CORRECTION" in m274blk and "M276 CORRECTION" in m275blk
    fixed_m275 = "SUPERSEDES the hand-written 130" in m275src and "== 130" not in m275src
    cpath = os.path.join(ROOT, "SESSION_CURSOR.md")
    cur = open(cpath, errors="replace").read() if os.path.exists(cpath) else ""
    closed = ("CLOSED UNRUNNED by M276" in m275blk) or ("CLOSED UNRUNNED" in cur and "M276" in cur)
    gate(8, need and fixed_m275 and closed,
         "registry corrected: NAMED.md M274 block carries 8380 (%s), m275 script no longer "
         "asserts 130 (%s), the queued box pick marked CLOSED by M276 (%s)"
         % (need, fixed_m275, closed))

    n_ok = sum(results)
    print("SUMMARY: ACCEPTANCE M276 %s %d/%d - the fold's coefficient is the faction stride "
          "%d; M275's irreconcilable-static-vs-live is a HAND-WRITTEN expression at the chain's "
          "midpoint, and the queued frame-slot watchpoint pick is CLOSED with no box time"
          % ("PASS" if n_ok == len(results) else "FAIL", n_ok, len(results), STRIDE))
    return 0 if n_ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
