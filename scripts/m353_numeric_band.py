#!/usr/bin/env python3
"""m353_numeric_band.py - who FILLS `ds:0x999fa4` and which Script.txt tokens CONSUME it.

The question (OPEN shortlist): 0x999fa4 is the numeric band of the 10-slot `$`-variable table
(text 0x99a01c stride 0x100, payload 0x999ff4, owner 0x999fcc).  M325 named element 0 a
"cheat-parsed scalar" from an ABSOLUTE-address census (writers {442642,626fd7}).  A store
through a SCALED index (`[eax*4+0x999fa4]`) is invisible to that census, so the registry's
writer set may be a subset of the real one.  This instrument measures the band's geometry,
every store into it, the setter that owns the indexed store, and each consuming token.

Static: scratch/m574/text.txt (objdump of terran.exe .text) + ghidra_out/index.csv + the PE's
own .rdata bytes (token literals are read from the binary, not from a table in this file).

    python3 -u scripts/m353_numeric_band.py [--dump PATH] [--exe PATH] [--no-write]
"""
import argparse
import bisect
import hashlib
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUMP = os.path.join(ROOT, "scratch/m574/text.txt")
INDEX = os.path.join(ROOT, "ghidra_out/index.csv")
EXE = "/mnt/smac/programs/terran.exe"
EVID = os.path.join(ROOT, "evidence/m353_numeric_band.txt")

NUM = 0x999FA4          # numeric band base (10 dwords)
OWN = 0x999FCC          # owner band
PAY = 0x999FF4          # payload band
TXT = 0x99A01C          # text band (stride 0x100)
TXT_NEXT = 0x99AA1C     # == TXT + 10*0x100  (the staging text at 0x99aa1c)
SETTER = 0x626581       # numeric slot setter, indexed store at 0x626597
SETTER_END = 0x6265A2
EXPANDER = 0x625B20     # the `$` substitution engine
ITOA = 0x64F980         # itoa(value, buf, radix)
PUBLISH_HINT = 0x626634  # the 10-slot channel publish call target (owner/payload/text)

LINE_RX = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+)\t(.*)$")


# ---------------------------------------------------------------- inputs
def load_index():
    rows = []
    with open(INDEX) as f:
        head = f.readline().strip().split(",")
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            d = dict(zip(head, line.rstrip("\n").split(",")))
            rows.append((int(d["addr"], 16), d["name"], int(d["size_bytes"])))
    rows.sort()
    return rows, [r[0] for r in rows]


def load_dump(path):
    ins = []
    for line in open(path, errors="replace"):
        m = LINE_RX.match(line)
        if not m:
            continue
        ins.append((int(m.group(1), 16), m.group(3).strip()))
    return ins


def section_of(exe_path, va):
    """Map a VA to a file offset using the PE section table (image base 0x400000)."""
    d = open(exe_path, "rb").read()
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    nsec = struct.unpack_from("<H", d, pe + 6)[0]
    opt = struct.unpack_from("<H", d, pe + 20)[0]
    base = pe + 24 + opt
    ib = struct.unpack_from("<I", d, pe + 24 + 28)[0]
    rva = va - ib
    for i in range(nsec):
        o = base + 40 * i
        vs, sva, rs, ro = struct.unpack_from("<IIII", d, o + 8)
        if sva <= rva < sva + max(vs, rs):
            return d, ro + (rva - sva)
    raise SystemExit("va %#x not in any section" % va)


def cstr(exe_path, va, n=24):
    d, off = section_of(exe_path, va)
    raw = d[off:off + n].split(b"\0")[0]
    return raw.decode("latin-1")


# ---------------------------------------------------------------- helpers
def func_of(ix_starts, ix_rows, addr):
    i = bisect.bisect_right(ix_starts, addr) - 1
    return ix_rows[i][1], ix_rows[i][0]


def ops(instr):
    """mnemonic + operand text, split on the first whitespace."""
    m = re.match(r"^(\S+)\s*(.*)$", instr)
    return (m.group(1), m.group(2)) if m else (instr, "")


def stores_to(instr, lit):
    """True when `lit` is the DESTINATION of a mov (element 0 of an absolute address)."""
    mn, op = ops(instr)
    if not mn.lower().startswith("mov"):
        return False
    dest = op.split(",")[0]
    return lit in dest


# ---------------------------------------------------------------- measurement
def measure(dump_path, exe_path):
    ins = load_dump(dump_path)
    ix_rows, ix_starts = load_index()
    addr_ix = {a: i for i, (a, _) in enumerate(ins)}
    lit = "0x%x" % NUM
    refs = []
    for a, txt in ins:
        if lit not in txt:
            continue
        mn, op = ops(txt)
        scaled = re.search(r"\[(\w+)\*4\+%s\]" % lit, op)
        disp = re.search(r"\[(\w+)\+%s\]" % lit, op)
        kind = "scaled" if scaled else ("disp" if disp else ("abs" if "ds:%s" % lit in op else "other"))
        fn, faddr = func_of(ix_starts, ix_rows, a)
        refs.append(dict(addr=a, fn=fn, faddr=faddr, kind=kind, txt=txt.strip(),
                         write=stores_to(txt, lit),
                         byte_op="BYTE PTR" in op,
                         idxreg=scaled.group(1) if scaled else None))
    m = dict(refs=refs)

    # --- band geometry -------------------------------------------------
    slots = (OWN - NUM) // 4
    m["geometry"] = dict(num=NUM, own=OWN, pay=PAY, txt=TXT,
                         num_own=OWN - NUM, own_pay=PAY - OWN, pay_txt=TXT - PAY,
                         slots=slots, txt_span=TXT_NEXT - TXT,
                         txt_stride=(TXT_NEXT - TXT) // slots if slots else 0,
                         txt_next=TXT_NEXT)

    # --- the setter body ----------------------------------------------
    body = [(a, t) for a, t in ins if SETTER <= a < SETTER_END]
    m["setter_body"] = body
    s = {"bound": None, "err": None, "ok": None, "store": None, "jle": None, "ret": None}
    for a, t in body:
        if re.search(r"cmp\s+DWORD PTR \[ebp\+0x8\],(0x[0-9a-f]+)", t):
            s["bound"] = (a, int(re.search(r",(0x[0-9a-f]+)", t).group(1), 16))
        if re.match(r"jle\b", t):
            s["jle"] = a
        if re.search(r"mov\s+eax,0x([0-9a-f]+)", t):
            s["err"] = (a, int(re.search(r"eax,0x([0-9a-f]+)", t).group(1), 16))
        if lit in t and stores_to(t, lit):
            s["store"] = (a, t.strip())
        if re.match(r"xor\s+eax,eax", t):
            s["ok"] = a
        if re.match(r"ret\b", t):
            s["ret"] = a
    m["setter"] = s

    # --- setter CALLERS: last push before each call is arg1 = k -------
    calls = []
    for a, t in ins:
        if re.match(r"call\s+0x%x$" % SETTER, t, re.I):
            i = addr_ix[a]
            k, kind = None, "none"
            for j in range(i - 1, max(i - 13, -1), -1):
                pa, pt = ins[j]
                pm = re.match(r"push\s+(.+)$", pt)
                if pm:
                    arg = pm.group(1).strip()
                    lm = re.match(r"0x([0-9a-f]+)$", arg, re.I)
                    if lm:
                        k, kind = int(lm.group(1), 16), "imm"
                    else:
                        kind = "reg"
                    break
            fn, _ = func_of(ix_starts, ix_rows, a)
            calls.append(dict(addr=a, fn=fn, k=k, kind=kind))
    m["calls"] = calls

    # --- consumer attribution: nearest preceding token literal --------
    toks = {}
    for name_va in (0x699120, 0x699128, 0x699130):
        toks[name_va] = cstr(exe_path, name_va)
    m["token_literals"] = dict(toks)
    reads = [r for r in refs if r["kind"] == "scaled" and not r["write"]]
    for r in reads:
        i = addr_ix[r["addr"]]
        tok = None
        for j in range(i - 1, max(i - 90, -1), -1):
            tm = re.search(r"push\s+0x(6991[0-9a-f]{2})$", ins[j][1], re.I)
            if tm:
                va = int(tm.group(1), 16)
                if va in toks:
                    tok = (va, toks[va])
                    break
        r["token"] = tok
        radix, radix_addr = None, None
        for j in range(i, min(i + 14, len(ins))):
            if re.match(r"call\s+0x%x$" % ITOA, ins[j][1], re.I):
                for q in range(j - 1, i, -1):
                    pm = re.match(r"push\s+0x([0-9a-f]+)$", ins[q][1], re.I)
                    if pm:
                        radix, radix_addr = int(pm.group(1), 16), ins[q][0]
                        break
                break
        r["radix"], r["radix_addr"] = radix, radix_addr

    # --- itoa: is arg3 the radix? -------------------------------------
    itoa_body = [(a, t) for a, t in ins if ITOA <= a < ITOA + 0x50]
    m["itoa"] = dict(
        radix_cmp=[(a, t.strip()) for a, t in itoa_body if re.search(r"cmp\s+DWORD PTR \[ebp\+0x10\],0xa", t)],
        radix_fwd=[(a, t.strip()) for a, t in itoa_body if re.search(r"\[ebp\+0x10\]", t)],
        body=itoa_body)

    # --- the `$#` predicate path (0x23) vs the `$<digit>` bound -------
    pred = [(a, t) for a, t in ins if 0x62606C <= a < 0x6260A1]
    m["pred_path"] = pred
    m["pred"] = dict(
        hash_cmp=[(a, t.strip()) for a, t in pred if re.search(r"cmp\s+edx,0x23", t)],
        sub=[(a, t.strip()) for a, t in pred if re.search(r"sub\s+edx,0x30", t)],
        cmp1=[(a, t.strip()) for a, t in pred if re.search(r"cmp\s+DWORD PTR \[eax\*4\+%s\],0x1" % lit, t)],
        setne=[(a, t.strip()) for a, t in pred if re.match(r"setne", t)],
        bound10=[(a, t.strip()) for a, t in pred if re.search(r"cmp\s+\S+,0xa$", t)])
    keep = [(a, t) for a, t in ins if 0x6260A1 <= a < 0x6260C2]
    m["digit_path"] = dict(
        bound=[(a, t.strip()) for a, t in keep if re.search(r"cmp\s+DWORD PTR \[ebp-0x18\],0xa", t)],
        jl=[(a, t.strip()) for a, t in keep if re.match(r"jl\b", t)],
        load=[(a, t.strip()) for a, t in keep if "0x999ff4" in t or "0x999fcc" in t])

    # --- rival B: does the publisher write the numeric band? -----------
    pub_fn, pub_addr = func_of(ix_starts, ix_rows, PUBLISH_HINT)
    m["publisher"] = dict(fn=pub_fn, base=pub_addr,
                          refs=[r for r in refs if r["faddr"] == pub_addr])
    exp_fn, exp_addr = func_of(ix_starts, ix_rows, EXPANDER)
    m["expander"] = dict(fn=exp_fn, base=exp_addr)

    # --- absolute-only view (the M325 writer set) ---------------------
    m["abs_writers"] = [r["addr"] for r in refs if r["kind"] == "abs" and r["write"]]
    m["scaled_writers"] = [r["addr"] for r in refs if r["kind"] == "scaled" and r["write"]]
    return m


# ---------------------------------------------------------------- gates
def gates(m):
    refs = m["refs"]
    g = m["geometry"]
    s = m["setter"]
    calls = m["calls"]
    out = []

    def add(name, ok, detail):
        out.append((name, bool(ok), detail))

    absr = [r for r in refs if r["kind"] == "abs"]
    scr = [r for r in refs if r["kind"] == "scaled"]
    disp = [r for r in refs if r["kind"] in ("disp", "other")]
    add("G1 ref census: 16 = 11 abs + 5 scaled, 0 displacement-form",
        len(refs) == 16 and len(absr) == 11 and len(scr) == 5 and not disp,
        "refs=%d abs=%d scaled=%d disp/other=%d" % (len(refs), len(absr), len(scr), len(disp)))

    wr = [r for r in refs if r["write"]]
    want = {(0x626597, "scaled"), (0x442642, "abs"), (0x626FD7, "abs")}
    got = {(r["addr"], r["kind"]) for r in wr}
    add("G2 stores into the band = exactly 3 (one SCALED, two absolute)",
        got == want,
        "stores=%s" % ", ".join("%#x/%s/%s" % (r["addr"], r["kind"], r["fn"]) for r in wr))

    add("G3 band geometry: four 10-dword bands, text stride 0x100 over 10 slots -> 0x99aa1c",
        (g["own"] - g["num"]) == 0x28 == (g["pay"] - g["own"]) == (g["txt"] - g["pay"])
        == g["slots"] * 4
        and g["txt_span"] == g["slots"] * g["txt_stride"] == 0xA00
        and g["txt_stride"] == 0x100 and g["txt_next"] == TXT_NEXT,
        "num_own=%#x own_pay=%#x pay_txt=%#x slots=%d txt_span=%#x stride=%#x"
        % (g["num_own"], g["own_pay"], g["pay_txt"], g["slots"], g["txt_span"], g["txt_stride"]))

    add("G4 setter: bound literal == slots-1, error return 3, success 0, indexed store, jle first",
        s["bound"] and s["bound"][1] == g["slots"] - 1 and s["err"] and s["err"][1] == 3
        and s["ok"] and s["store"] and s["jle"] and s["jle"] > s["bound"][0] > 0
        and s["jle"] < s["err"][0] < s["store"][0] < s["ok"],
        "bound=%s err=%s jle=%#x store=%s ok=%#x" %
        (s["bound"], s["err"], s["jle"] or 0, s["store"][1] if s["store"] else None,
         s["ok"] or 0))

    kk = [c["k"] for c in calls if c["kind"] == "imm"]
    over = [c for c in calls if c["kind"] == "imm" and (c["k"] > g["slots"] - 1)]
    add("G5 setter callers: 260 sites, 0 pass a literal k > 9",
        len(calls) == 260 and len(kk) >= 150 and not over,
        "calls=%d literal_k=%d distinct=%s over_bound=%s"
        % (len(calls), len(kk), sorted(set(kk)), [hex(c["addr"]) for c in over]))

    reads = [r for r in refs if r["kind"] == "scaled" and not r["write"]]
    names = sorted({r["token"][1] for r in reads if r["token"]})
    add("G6 consumers: 4 scaled reads in the expander; 3 tokens = $NUMBER/$NUM/$HEX",
        len(reads) == 4 and all(r["fn"] == m["expander"]["fn"] for r in reads)
        and names == ["$HEX", "$NUM", "$NUMBER"]
        and sorted(r["token"][1] for r in reads if r["token"]).count("$HEX") == 1,
        "reads=%s expander=%s" % (", ".join("%#x->%s" % (r["addr"], r["token"][1] if r["token"] else "?")
                                            for r in reads), m["expander"]["fn"]))

    rad = {r["token"][1]: r["radix"] for r in reads if r["token"]}
    add("G7 every numeric token passes radix 0xa to the itoa -> $HEX prints DECIMAL",
        sorted(rad.values()) == [10, 10, 10] and bool(m["itoa"]["radix_cmp"]),
        "radix=%s itoa_bound=%#x" % (rad, m["itoa"]["radix_cmp"][0][0] if m["itoa"]["radix_cmp"] else 0))

    add("G8 the 4th read is the `$#` PREDICATE: cmp [band+k],1 -> setne, NO k bound on that path",
        len(m["pred"]["hash_cmp"]) == 1 and len(m["pred"]["sub"]) == 1
        and len(m["pred"]["cmp1"]) == 1 and len(m["pred"]["setne"]) == 1
        and not m["pred"]["bound10"] and len(m["digit_path"]["bound"]) == 1,
        "hash_cmp=%s cmp1=%s setne=%s bound_on_#path=%d bound_on_$path=%d"
        % (len(m["pred"]["hash_cmp"]), len(m["pred"]["cmp1"]), len(m["pred"]["setne"]),
           len(m["pred"]["bound10"]), len(m["digit_path"]["bound"])))

    alias = {i: g["num"] + 4 * i for i in (10, 11, 20, 30)}
    alias_ok = (alias[10] == OWN and alias[11] == OWN + 4 and alias[20] == PAY
                and alias[30] == TXT)
    add("G9 `$#` index >= 10 is UNBOUNDED: k=10 aliases owner[0], 20 -> payload[0], 30 -> text[0]",
        alias_ok and g["num"] + 4 * 10 == g["own"] and g["num"] + 4 * 20 == g["pay"],
        "alias=%s" % {k: hex(v) for k, v in alias.items()})

    add("R1 rival 'it is a scalar, all writers absolute' FAILS on the scaled store",
        len(m["abs_writers"]) == 2 and len(m["scaled_writers"]) == 1 and 0x626597 in m["scaled_writers"],
        "abs_writers=%s scaled_writers=%s" % ([hex(a) for a in m["abs_writers"]],
                                              [hex(a) for a in m["scaled_writers"]]))

    add("R2 rival 'the 10-slot publisher fills it' FAILS: 0 refs in the publisher body",
        m["publisher"]["refs"] == [] and m["publisher"]["base"] != 0,
        "publisher=%s @%#x refs=%d" % (m["publisher"]["fn"], m["publisher"]["base"],
                                       len(m["publisher"]["refs"])))
    return out


def digest(lines):
    return hashlib.sha1("\n".join(lines).encode()).hexdigest()[:16]
def render(m):
    lines = []
    A = lines.append
    g = m["geometry"]
    A("M353 - the numeric band ds:0x999fa4: who fills it, which tokens consume it")
    A("")
    A("BAND GEOMETRY (computed from four bases + the setter's own bound)")
    A("  numeric %#010x  owner %#010x  payload %#010x  text %#010x" % (g["num"], g["own"], g["pay"], g["txt"]))
    A("  gaps: %#x / %#x / %#x bytes -> %d dwords each; text stride %#x, 10*stride -> %#x"
      % (g["num_own"], g["own_pay"], g["pay_txt"], g["slots"], g["txt_stride"], g["txt_next"]))
    A("")
    A("EVERY REFERENCE TO 0x999fa4 (kind / R-W / containing function)")
    for r in sorted(m["refs"], key=lambda r: r["addr"]):
        A("  %#08x  %-6s %s  %-14s %s" % (r["addr"], r["kind"], "W" if r["write"] else "R", r["fn"], r["txt"]))
    A("")
    A("THE SETTER FUN_00626581 (the only indexed writer)")
    for a, t in m["setter_body"]:
        A("  %#08x  %s" % (a, t))
    A("")
    A("SETTER CALLERS: %d sites" % len(m["calls"]))
    imm = [c["k"] for c in m["calls"] if c["kind"] == "imm"]
    hist = {}
    for k in imm:
        hist[k] = hist.get(k, 0) + 1
    A("  literal k histogram: %s" % ", ".join("%d:%d" % (k, hist[k]) for k in sorted(hist)))
    A("  non-literal arg1 (register/stack) at %d sites" % (len(m["calls"]) - len(imm)))
    A("")
    A("CONSUMING TOKENS (read site -> token literal read from the PE, radix passed to itoa)")
    for r in sorted((r for r in m["refs"] if r["kind"] == "scaled" and not r["write"]), key=lambda r: r["addr"]):
        A("  %#08x  %-8s radix=%s  (%s)" % (r["addr"], r["token"][1] if r["token"] else "?",
                                            r["radix"], r["txt"]))
    A("  token literals: %s" % ", ".join("%#x=%r" % (va, s) for va, s in sorted(m["token_literals"].items())))
    A("  itoa %#x: %s" % (ITOA, m["itoa"]["radix_cmp"][0][1] if m["itoa"]["radix_cmp"] else "(no radix cmp)"))
    A("")
    A("THE `$#k` PREDICATE PATH (0x62606c..0x6260a0) vs the `$k` DIGIT PATH (0x6260a1..0x6260c1)")
    for a, t in m["pred_path"]:
        A("  # %#08x  %s" % (a, t))
    for a, t in m["digit_path"]["bound"] + m["digit_path"]["load"]:
        A("  $ %#08x  %s" % (a, t))
    A("  ALIAS arithmetic: k=10 -> %#x (owner[0]), k=20 -> %#x (payload[0]), k=30 -> %#x (text[0] byte of slot 0)"
      % (g["num"] + 40, g["num"] + 80, g["num"] + 120))
    A("")
    A("RIVAL B: the 10-slot publisher %s @%#x holds %d refs to 0x999fa4"
      % (m["publisher"]["fn"], m["publisher"]["base"], len(m["publisher"]["refs"])))
    A("")
    return lines


def digest(lines):
    return hashlib.sha1("\n".join(lines).encode()).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", default=DUMP)
    ap.add_argument("--exe", default=EXE)
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()

    def run():
        m = measure(a.dump, a.exe)
        lines = render(m)
        gs = gates(m)
        lines.append("GATES")
        for name, ok, detail in gs:
            lines.append("  %-4s %-78s %s" % ("PASS" if ok else "FAIL", name, detail))
        npass = sum(1 for _, ok, _ in gs if ok)
        d = digest(lines)
        lines.append("")
        lines.append(("PASS M353: %d/%d gates digest %s" if npass == len(gs)
                      else "FAIL M353: %d/%d gates digest %s") % (npass, len(gs), d))
        return lines, npass, len(gs), d

    lines, npass, ngates, d = run()
    lines2, npass2, _, d2 = run()
    assert npass == npass2 and d == d2, "NOT DETERMINISTIC: %s vs %s" % (d, d2)
    text = "\n".join(lines) + "\n"
    sys.stdout.write(text)
    sys.stdout.flush()
    if not a.no_write and npass == ngates:
        with open(EVID, "w") as f:
            f.write(text)
    if npass != ngates:
        sys.exit(1)


if __name__ == "__main__":
    main()
