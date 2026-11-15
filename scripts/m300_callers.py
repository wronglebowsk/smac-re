#!/usr/bin/env python3
"""M300 (s255, STATIC, zero box): census of the callers of FUN_005832b0 (0x5832b0).

QUESTION (the s254 open lead "0x5832b0's other 23 callers", NAMED.md ## M299 line 3):
every call site of the pure lattice/occupancy predicate FUN_005832b0 in .text - its
address, its containing function (containment ALWAYS via ghidra_out/index.csv, never an
objdump window at an arbitrary address), and whether that caller's path can reach the
slot [+4] visit-counter write M299 identified: `inc ecx` 0x51e01a + `mov [esi+0x989cec],
ecx` 0x51e01b inside FUN_0051dcb0, gated by `test eax,eax` 0x51e005 / `je 0x51e11d`
0x51e007 on the call at 0x51dffd. Each site is classified by WHICH GATE THE CALLER
SUPPLIES (how eax is consumed right after the call) and by its containing function's
reachability to FUN_0051dcb0, the owner of the counter write.

METHOD (every number printed is COMPUTED here and asserted at the end):
  S1 every `call 0x5832b0` in the full-.text dump scratch/m574/text.txt (the dump M299
     graded 13/13 constants against Ghidra); cross-check the count against
     ghidra_out/index.csv n_callers (independent toolchain) and prove the address appears
     in .text ONLY inside call rel32 (no lea/push of the pointer -> no indirect/vtable use).
  S2 containment per site by bisecting index.csv (addr, size_bytes).
  S3 per-site consumption window (post-call instructions to the next unconditional
     jmp/ret, cap 16): the gate the caller supplies, classified; raw windows printed as
     the classification witness.
  S4 whole-dump sweep of every mention of the slot-base immediates 0x989ce8 / 0x989cec,
     operand role store/load/lea -> which code can touch the counter dword at all.
  S5 re-pin of the M299 gate chain (test/je/inc/store bytes still in place).
  S6 function->function direct-call graph from the dump; reverse BFS from FUN_0051dcb0 =
     exactly the functions whose path can reach the write; per caller function reach class.
stdout is mirrored to evidence/m300_callers.txt.

Run:  python3 scripts/m300_callers.py            (exit 0 = all assertions hold)
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
EVID = os.path.join(ROOT, "evidence", "m300_callers.txt")

PRED = 0x5832B0             # FUN_005832b0
WRITER = 0x51DCB0           # FUN_0051dcb0, owner of the [+4] counter store
CALL_IN_WRITER = 0x51DFFD   # M299's pinned call whose result gates the store
GATE_TEST = 0x51E005        # test eax,eax
GATE_JE = 0x51E007          # je 0x51e11d
INC_INSN = 0x51E01A         # inc ecx
STORE_INSN = 0x51E01B       # mov [esi+0x989cec],ecx
SLOT_IMMS = ("0x989ce8", "0x989cec")

LINE_RX = re.compile(r"^ +([0-9a-f]{6,8}):\t([0-9a-f ]+)\t\s*(.+?)\s*$")
CALL_RX = re.compile(r"^call\s+(?:0x)?([0-9a-f]{4,8})(?:\s|$)")
JCC_RX = re.compile(r"^(?:je|jne|jl|jge|jg|jle|jb|jae|ja|jbe|js|jns|jo|jno|jc|jnc)\s")
ARITH = r"(?:neg|sbb|add|sub|or|and|xor|inc|dec|imul|not|adc|sbb)"


class Out:
    """mirror every printed line to stdout and the evidence file."""

    def __init__(self, path):
        self.f = open(path, "w")

    def p(self, s=""):
        self.f.write(s + "\n")
        print(s)

    def close(self):
        self.f.close()


def load_dump():
    ins = {}
    with open(TEXT, errors="replace") as f:
        for ln in f:
            m = LINE_RX.match(ln)
            if m:
                a = int(m.group(1), 16)
                if a not in ins:
                    ins[a] = m.group(3)
    return ins, sorted(ins)


def load_index():
    funcs = []
    with open(INDEX) as f:
        for row in csv.DictReader(f):
            funcs.append((int(row["addr"], 16), row["name"], int(row["size_bytes"]),
                          int(row["n_callers"])))
    funcs.sort()
    return funcs


def contain(funcs, faddrs, A):
    i = bisect.bisect_right(faddrs, A) - 1
    a, n, sz, _ = funcs[i]
    return n, (a <= A < a + sz)


def window(ins, addrs, a, cap=16):
    """records strictly after a, to the next unconditional jmp/ret (inclusive), a >16 B
    gap (data island) or cap."""
    i = bisect.bisect_right(addrs, a)
    out = []
    while i < len(addrs) and len(out) < cap:
        if addrs[i] - addrs[i - 1] > 16:
            break
        w, t = addrs[i], ins[addrs[i]]
        out.append((w, t))
        if t.split(None, 1)[0] in ("jmp", "ret"):
            break
        i += 1
    return out


def split(t):
    p = t.split(None, 1)
    return p[0], (p[1] if len(p) > 1 else "")


def classify_site(ins, addrs, a):
    """(win, class, note) - WHICH GATE the caller supplies: every form in which the
    predicate's eax is consumed before it dies, the window fence, or a reassignment.
    The raw window (S3w) is the witness; the class is a label computed from it."""
    win = window(ins, addrs, a)
    eff = []                                     # drop callee-cleanup of the 2 args
    for w, t in win:
        if not re.match(r"^(?:add|sub)\s+esp,0x[0-9a-f]+$", t):
            eff.append((w, t))
    forms, notes = [], []
    held = None                                  # reg holding eax after mov reg,eax
    dead_at = None
    for k, (w, t) in enumerate(eff):
        mk, rk = split(t)
        if (mk in ("mov", "lea") and re.match(r"^(?:mov|lea)\s+eax,", t)) or mk == "call":
            dead_at = k                          # eax written / caller-saved clobber
            break
        if "eax" not in rk:
            if mk == "ret":                      # fence with eax still the result
                forms.append("returned-upward")
                notes.append("ret @0x%x with eax carrying the result" % w)
                break
            continue                             # insn does not touch eax
        if mk == "test" and rk.strip() == "eax,eax":
            nxt = eff[k + 1] if k + 1 < len(eff) else None
            if nxt and JCC_RX.match(nxt[1]):
                forms.append("truth-branch")
                notes.append("test @0x%x; %s" % (w, nxt[1]))
            else:
                forms.append("test")
                notes.append("test eax,eax @0x%x (no immediate jcc)" % w)
            continue
        if mk == "cmp" and re.search(r"\beax\b", rk):
            nxt = eff[k + 1] if k + 1 < len(eff) else None
            if nxt and JCC_RX.match(nxt[1]):
                forms.append("value-branch")
                notes.append("%s @0x%x; %s" % (t, w, nxt[1]))
            else:
                forms.append("value-compare")
                notes.append("%s @0x%x" % (t, w))
            continue
        if mk == "mov":
            mm = re.match(r"^mov\s+(e(?:a|b|c|d)x|esi|edi|ebp),\s*eax$", t)
            if mm:
                held = mm.group(1)
                forms.append("into-" + held)
                notes.append("%s @0x%x" % (t, w))
                continue
            if re.match(r"^mov\s+[^,]*PTR[^,]*,\s*eax$", t):
                forms.append("stored-to-memory")
                notes.append("%s @0x%x" % (t, w))
                continue
        if mk == "push" and rk.strip() in ("eax",) or \
           (mk == "push" and held and rk.strip() == held):
            forms.append("pushed-as-arg")
            notes.append("%s @0x%x" % (t, w))
            continue
        if mk in ("neg", "sbb", "add", "sub", "or", "and", "xor", "inc", "dec",
                  "imul", "adc") and re.search(r"\b(eax|%s)\b" % (held or "e?x"), rk):
            forms.append("value-arith")
            notes.append("%s @0x%x" % (t, w))
            continue
        if mk == "mov" and held and re.match(r"^mov\s+%s," % held, t):
            dead_at = k                          # the held copy dies
            break
    cls = "+".join(dict.fromkeys(forms)) if forms else "ignored"
    return win, cls, "; ".join(notes[:3]) if notes else (
        "eax not read before %s" % ("reassignment 0x%x" % eff[dead_at][0] if dead_at
                                     else "window end"))


def main():
    if not os.path.exists(TEXT):
        sys.exit("FATAL: %s missing - regenerate the full-.text dump (skill: "
                 "ghidra-batch-export)" % TEXT)
    O = Out(EVID)
    ins, addrs = load_dump()
    funcs = load_index()
    faddrs = [f[0] for f in funcs]
    pred_row = [f for f in funcs if f[0] == PRED]
    assert pred_row, "FUN_005832b0 not in index.csv"
    ghidra_ncall = pred_row[0][3]
    writer_name = [f[1] for f in funcs if f[0] == WRITER][0]

    O.p("M300 (s255) STATIC - census of the callers of FUN_005832b0. Zero box, zero gdb.")
    O.p("dump scratch/m574/text.txt: %d instruction records; index.csv: %d functions."
        % (len(addrs), len(funcs)))

    # ---- S1 -----------------------------------------------------------------------
    sites, mentions = [], []
    for a in addrs:
        t = ins[a]
        m = CALL_RX.match(t)
        if m and int(m.group(1), 16) == PRED:
            sites.append(a)
        if "5832b0" in t:
            mentions.append((a, t))
    non_call = [(a, t) for a, t in mentions
                if not (CALL_RX.match(t) and int(CALL_RX.match(t).group(1), 16) == PRED)]
    O.p("\n== S1: `call 0x5832b0` in the dump: %d; Ghidra index.csv n_callers: %d; "
        "mentions NOT a direct call: %d ==" % (len(sites), ghidra_ncall, len(non_call)))
    for a, t in non_call:
        O.p("   NON-CALL MENTION 0x%x: %s" % (a, t))

    # ---- S2/S0: containment, call-graph reach, per-site table ----------------------
    edges_rev = collections.defaultdict(set)   # callee -> callers (direct edges only)
    for a in addrs:
        m = CALL_RX.match(ins[a])
        if not m:
            continue
        tgt = int(m.group(1), 16)
        fsrc, ok1 = contain(funcs, faddrs, a)
        ftgt, ok2 = contain(funcs, faddrs, tgt)
        if ok1 and ok2 and tgt in faddrs and fsrc != ftgt:
            edges_rev[ftgt].add(fsrc)
    reach = {writer_name: 0}                   # fn -> min call-depth to the writer
    frontier = [writer_name]
    while frontier:
        nxt = []
        for f in frontier:
            for c in edges_rev.get(f, ()):
                if c not in reach:
                    reach[c] = reach[f] + 1
                    nxt.append(c)
        frontier = nxt

    def reach_class(f):
        if f == writer_name:
            return "IN-WRITER"
        if reach.get(f) == 1:
            return "REACHES(direct-call)"
        if f in reach:
            return "REACHES(depth-%d)" % reach[f]
        return "CANNOT-REACH"

    rows = []
    for a in sites:
        fn, inside = contain(funcs, faddrs, a)
        win, cls, note = classify_site(ins, addrs, a)
        if a == CALL_IN_WRITER:
            cls += "|THE-COUNTER-GATE"
        rows.append(dict(addr=a, fn=fn, inside=inside, cls=cls, note=note, win=win,
                         reach=reach_class(fn)))
    O.p("\n== S2/S3: per-site table (containment via index.csv; class = the gate the "
        "caller supplies;")
    O.p("    reach = can the CONTAINING function's path reach %s, owner of the [+4] "
        "write) ==" % writer_name)
    O.p("%-11s %-17s %-28s %-19s %s" %
        ("call@VA", "function", "class", "reach", "eax consumption"))
    for r in rows:
        O.p("0x%-9x %-17s %-28s %-19s %s" %
            (r["addr"], r["fn"], r["cls"], r["reach"], r["note"]))

    # ---- S3 witness windows ---------------------------------------------------------
    O.p("\n== S3w: raw post-call windows (call + following insns to jmp/ret, cap 16) "
        "==")
    for r in rows:
        O.p("0x%x in %s:" % (r["addr"], r["fn"]))
        O.p("   0x%x\t%s" % (r["addr"], ins[r["addr"]]))
        for w, t in r["win"]:
            O.p("   0x%x\t%s" % (w, t))

    # ---- S4 -----------------------------------------------------------------------
    sweep = []
    for a in addrs:
        t = ins[a]
        if any(im in t for im in SLOT_IMMS):
            fn, _ = contain(funcs, faddrs, a)
            first = t.split(None, 1)
            dst = first[1].split(",")[0].strip() if len(first) > 1 else ""
            if first[0] == "lea":
                role = "lea"
            elif first[0] in ("mov",) and dst.startswith("DWORD PTR") and \
                    any(im in dst for im in SLOT_IMMS):
                role = "STORE"
            elif first[0] in ("inc", "dec", "add", "sub", "or", "and", "xor"):
                role = "STORE" if any(im in dst for im in SLOT_IMMS) else "load"
            else:
                role = "load"
            sweep.append((a, fn, role, t))
    stores_cec = [a for a, fn, role, t in sweep if "0x989cec" in t and role == "STORE"]
    fns_cec = sorted({fn for a, fn, role, t in sweep if "0x989cec" in t})
    O.p("\n== S4: every dump line mentioning %s (slot stride 28B at 0x989ce8, counter "
        "at base+4) ==" % " / ".join(SLOT_IMMS))
    for a, fn, role, t in sweep:
        O.p("   0x%-9x %-17s %-6s %s" % (a, fn, role, t))
    O.p("   writes (STORE-role) to 0x989cec: %s; functions mentioning 0x989cec: %s"
        % (["0x%x" % a for a in stores_cec], fns_cec))

    # ---- S5 -----------------------------------------------------------------------
    O.p("\n== S5: the write gate (M299 L1 re-pinned; je target must skip the store) ==")
    O.p("   0x51e005\t%s" % ins[GATE_TEST])
    O.p("   0x51e007\t%s" % ins[GATE_JE])
    je_tgt = int(ins[GATE_JE].split()[-1], 16)
    O.p("   0x51e01a\t%s" % ins[INC_INSN])
    O.p("   0x51e01b\t%s" % ins[STORE_INSN])
    O.p("   je target 0x%x past store 0x%x: %s" % (je_tgt, STORE_INSN,
                                                   je_tgt > STORE_INSN))

    # ---- S6 -----------------------------------------------------------------------
    call_sites_of_writer = sorted(
        a for a in addrs if (m := CALL_RX.match(ins[a])) and
        int(m.group(1), 16) == WRITER)
    O.p("\n== S6: reverse-BFS over the DIRECT-call graph from %s (the write's owner); "
        "indirect (register/memory) calls NOT in the graph ==" % writer_name)
    O.p("   direct call sites of 0x%x: %d" % (WRITER, len(call_sites_of_writer)))
    for a in call_sites_of_writer:
        O.p("     0x%x in %s" % (a, contain(funcs, faddrs, a)[0]))
    caller_fns = sorted({r["fn"] for r in rows})
    O.p("   distinct caller functions of the predicate: %d; min call-depth to %s: %s"
        % (len(caller_fns), writer_name,
           {f: reach.get(f, "NO") for f in caller_fns}))
    O.p("\n== S7: per-caller-function rollup ==")
    O.p("%-17s %-5s %-19s %s" % ("function", "nsit", "reach class", "site classes"))
    by_fn = collections.Counter(r["fn"] for r in rows)
    for f in caller_fns:
        cls = sorted({r["cls"] for r in rows if r["fn"] == f})
        O.p("%-17s %-5d %-19s %s" % (f, by_fn[f], reach_class(f), cls))

    # ---- assertions ----------------------------------------------------------------
    in_writer = [r["addr"] for r in rows if r["fn"] == writer_name]
    tally = collections.Counter(r["cls"] for r in rows)
    reach_tally = collections.Counter(r["reach"] for r in rows)
    checks = [
        ("S1 sites == Ghidra n_callers == 24",
         len(sites) == ghidra_ncall == 24,
         "%d sites / %d ghidra" % (len(sites), ghidra_ncall)),
        ("S1 predicate address pointer never taken (0 non-call mentions)",
         len(non_call) == 0, "found %d" % len(non_call)),
        ("S2 all sites contained in index.csv functions",
         all(r["inside"] for r in rows),
         "%d uncontained" % sum(1 for r in rows if not r["inside"])),
        ("S2 distinct caller functions == 13 (24 sites)",
         len(caller_fns) == 13 and sum(by_fn.values()) == 24,
         "%d fns / %d sites" % (len(caller_fns), sum(by_fn.values()))),
        ("S2 exactly one site IN-WRITER (the 0x51dffd gate) and 6 sites CANNOT-REACH",
         reach_tally["IN-WRITER"] == 1 and reach_tally["CANNOT-REACH"] == 6,
         str(dict(reach_tally))),
        ("S4 lone 0x989cec writer == 0x51e01b",
         stores_cec == [STORE_INSN], str(["0x%x" % a for a in stores_cec])),
        ("S4 0x989cec touched only by %s" % writer_name, fns_cec == [writer_name],
         str(fns_cec)),
        ("S5 je skips the store whole", je_tgt > STORE_INSN, "0x%x" % je_tgt),
        ("S5 gate insns are test/je/inc/store",
         ins[GATE_TEST].startswith("test") and ins[GATE_JE].startswith("je") and
         ins[INC_INSN].startswith("inc") and "0x989cec" in ins[STORE_INSN] and
         ins[STORE_INSN].startswith("mov"),
         "%s|%s|%s|%s" % (ins[GATE_TEST], ins[GATE_JE], ins[INC_INSN], ins[STORE_INSN])),
        ("S2 exactly one DIRECT-gate site (0x51dffd)",
         in_writer == [CALL_IN_WRITER], str(["0x%x" % a for a in in_writer])),
        ("S3 every site got a class; tallies cover every site",
         all(r["cls"] for r in rows) and sum(tally.values()) == len(sites) and
         sum(reach_tally.values()) == len(sites),
         "%d/%d" % (sum(tally.values()), len(sites))),
        ("S3 gate census: 21 truth-branch / 2 stored-to-memory / 1 into-ebx",
         sum(c for k, c in tally.items() if "truth-branch" in k) == 21 and
         sum(c for k, c in tally.items() if k.startswith("stored-to-memory")) == 2 and
         sum(c for k, c in tally.items() if k.startswith("into-")) == 1,
         str(dict(tally))),
    ]
    O.p("\n== ASSERTIONS ==")
    bad = 0
    for name, ok, detail in checks:
        O.p("  %-58s %-4s %s" % (name, "PASS" if ok else "FAIL", detail))
        bad += not ok
    O.p("\nclass tally: %s" % dict(tally))
    O.p("reach tally: %s" % dict(reach_tally))
    O.p("\n%s M300: %d/%d gates" % ("PASS" if bad == 0 else "FAIL",
                                    len(checks) - bad, len(checks)))
    O.close()
    sys.exit(0 if bad == 0 else 1)


if __name__ == "__main__":
    main()
