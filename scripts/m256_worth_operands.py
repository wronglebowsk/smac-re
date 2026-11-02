#!/usr/bin/env python3
"""M256/M257/M258: the worth test's operands, and the per-region array family that feeds them.

Static only: terran.exe .text via objdump + ghidra_out/index.csv containment. No box, no /proc, no gdb.

From M253: the verdict byte DAT_0094eda8[region + fac*0x20bc] takes 7 or 8 from `sete dl; add dl,0x7`
at 0x558516, and the sete consumes the flags of the worth test. The operands were left unnamed, as were
the sibling per-region arrays 0x94e4a8 / 0x94e628 / 0x94e7a8 / 0x94eaa8.

Gates (each prints its own numbers; the SUMMARY line is the acceptance):
  G1  worth-test span: 13 pinned pcs decoded inside FUN_00556690, from the 0x94eca8 byte load to the
      two 0x94eaa8 reads
  G2  the test is cmp edx,ecx at 0x5584b4 -> jle skip -> leg2 -> sete dl; add dl,0x7 -> the 7/8 store
  G3  LHS operand provenance: ([block+0x94d810]-[block+0x94d818]+[ebp-0x60]) * [ebp-0x3c] * 2, with the
      [ebp-0x60] store that is live at the load pinned and its inputs named
  G4  RHS operand provenance: WORD[0x94eaa8 + 2*region] + WORD[0x94eaa8 + row], the row register's
      single writer, and the array's whole-image reference list
  G5  the row address: esi = 2*region + 188*arg1, region 1..127 (cmp ecx,0x80), arg1 = the pushed
      faction; the 188 B row vs 2 B/region spill is reported as the OPEN stride conflict
  G6  the 8-slot fold's sources: the per-region arrays 0x950764 (word) and 0x950664 (byte), stepped by
      the faction stride 0x20bc over 8 slots, and its three accumulators
  G7  the fold's two rows are 0x200 apart (0x950764 and 0x950564) and 0x950564 is its own table base;
      both are past the file image, so their extents are NOT statically readable
  G8  the sibling family 0x94e4a8..0x94ee28: 12 per-region arrays whose every gap (0x80 or 0x100)
      matches the observed operand width, zero DWORD accesses, 128 entries from the region bound
"""
import subprocess, sys, csv, re, struct, bisect, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXE = ROOT / "programs" / "terran.exe"
INDEX = ROOT / "ghidra_out" / "index.csv"
OUTFILE = ROOT / "evidence" / "m256_worth_operands.txt"

FUN = 0x556690
FAC_STRIDE = 0x20BC          # 8380: the per-faction block, in bytes
ROW_STRIDE = 188             # 94 rows of 2 B: the per-region table's per-faction row
REGIONS = 0x80               # the region loop bound, cmp ecx,0x80
SPAN_BASE = 0x94e4a8
SPAN_WORDS = 12 * 128        # 12 arrays x 128 regions, in dwords of 2 B? -> see g8 (it is in WORDS)

results = []
LOG = []


def gate(n, ok, text):
    results.append(ok)
    line = "G%d %s: %s" % (n, "PASS" if ok else "FAIL", text)
    print(line)
    LOG.append(line)
    return ok


def load_index():
    fns = []
    with INDEX.open() as f:
        for row in csv.DictReader(f):
            fns.append((int(row["addr"], 16), row["name"], int(row["size_bytes"])))
    fns.sort()
    return fns


FNS = None


def fn_of(pc):
    a = [f[0] for f in FNS]
    i = bisect.bisect_right(a, pc) - 1
    if i < 0:
        return None
    addr, name, size = FNS[i]
    return name if pc < addr + size else None


INS = None


def disasm():
    out = subprocess.run(['objdump', '-d', '-M', 'intel', '--section=.text', str(EXE)],
                         capture_output=True, text=True).stdout
    return out.replace("\\t", "\t")


def ins():
    """(pc, opcode bytes, mnemonic, operands). objdump pads the opcode column to 7 bytes and prints
    AT MOST 7 of them, so an 8+-byte instruction emits a continuation line at pc+7 whose opcode field
    is the leftover bytes and whose mnemonic is empty; those are collected onto the owning instruction
    (skill static-store-census 16 says 6 - on THIS build the padded width is 21 chars = 7 bytes, and
    the mnemonic-less line is the tell either way)."""
    out = []
    pend = None
    for ln in disasm().splitlines():
        m = re.match(r'^\s+([0-9a-f]{6,8}):\t((?:[0-9a-f]{2} ){1,7})(.*)$', ln)
        if not m:
            continue
        pc = int(m.group(1), 16)
        bs = m.group(2).split()
        rest = m.group(3).strip()
        if rest == "" and pend is not None and pc == pend[0] + pend[4]:
            pend[1].extend(bs)
            pend[4] += len(bs)
            continue
        if pend is not None:
            out.append((pend[0], bytes.fromhex("".join(pend[1])), pend[2], pend[3]))
            pend = None
        if rest == "":
            continue                          # orphan continuation
        mm = re.match(r'^([a-z][0-9a-z.]*)(?:\s+(.*))?$', rest)
        if not mm:
            continue
        pend = [pc, list(bs), mm.group(1), (mm.group(2) or "").strip(), len(bs)]
    if pend is not None:
        out.append((pend[0], bytes.fromhex("".join(pend[1])), pend[2], pend[3]))
    return out


PCS = None
PC2I = None


def setup():
    global FNS, INS, PCS, PC2I
    FNS = load_index()
    INS = ins()
    PCS = [i[0] for i in INS]
    PC2I = {p: k for k, p in enumerate(PCS)}


def at(pc):
    k = PC2I.get(pc)
    return None if k is None else INS[k]


def txt(pc):
    i = at(pc)
    return "<missing>" if i is None else ("%s %s" % (i[2], i[3])).strip()


def window(pc, back=0, fwd=0):
    k = PC2I.get(pc)
    if k is None:
        return []
    return INS[max(0, k - back):k + fwd + 1]


def find(pattern, lo=0, hi=1 << 40):
    """instruction pcs whose text matches pattern, within an address range"""
    rx = re.compile(pattern)
    return [p for p, _, m, o in INS if lo <= p < hi and rx.match(("%s %s" % (m, o)).strip())]


def token_sites(tok, text_re=None):
    """all instructions whose text carries the 6-digit global token"""
    rx = re.compile(text_re) if text_re else None
    hits = []
    for p, _, m, o in INS:
        t = ("%s %s" % (m, o)).strip()
        if tok in t and (rx is None or rx.match(t)):
            hits.append((p, t, fn_of(p)))
    return hits


def stores_of(tok):
    """stores whose DESTINATION operand carries tok, in any of objdump's three print forms"""
    rx = re.compile(r'^(?:[a-z]+ ptr )?d?s?:0x[0-9a-f]+$')
    out = []
    for p, t, f in token_sites(tok):
        parts = t.split(None, 1)
        if len(parts) < 2:
            continue
        mn, ops = parts[0], parts[1]
        if mn.split('.')[0] not in ("mov", "or", "and", "xor", "add", "sub", "adc", "sbb",
                                    "shl", "shr", "inc", "dec", "not", "neg", "btc", "btr", "bsf"):
            continue
        dest = ops.split(',')[0].strip()
        if '[' in dest or rx.match(dest):
            out.append((p, t, f))
    return out


def img():
    return EXE.read_bytes()


def le32(b, va):
    return struct.unpack_from('<I', b, va - 0x400000)[0]


# ---------------------------------------------------------------- gates

WORTH_PCS = [0x55844b, 0x558452, 0x558459, 0x558460, 0x558466, 0x558469, 0x55846b, 0x55846e,
             0x558472, 0x55848f, 0x558495, 0x5584a2, 0x5584aa]


def g1():
    got = [(p, txt(p), fn_of(p)) for p in WORTH_PCS]
    missing = [p for p, t, f in got if t == "<missing>"]
    outside = [p for p, t, f in got if f != "FUN_00556690"]
    ok = (not missing) and (not outside)
    gate(1, ok, "%d/%d pinned pcs decoded, %d outside FUN_00556690 (%s); first %s last %s" %
         (len(got) - len(missing), len(WORTH_PCS), len(outside),
          ",".join(hex(p) for p in outside) or "-", txt(WORTH_PCS[0]), txt(WORTH_PCS[-1])))


def g2():
    cmp_ = txt(0x5584b4)
    jle_ = txt(0x5584b6)
    sete = txt(0x55850e)
    addd = txt(0x558511)
    store = txt(0x558516)
    leg2 = txt(0x5584d8)
    leg2skip = txt(0x5584da)
    ok = (cmp_ == "cmp edx,ecx" and jle_.startswith("jle 0x5584e3") and sete == "sete dl"
          and addd == "add edx,0x7" and store == "mov BYTE PTR [esi+edi*1+0x94eda8],dl"
          and leg2 == "cmp eax,ecx" and leg2skip.startswith("jge 0x5584e3"))
    gate(2, ok, "cmp=%s | %s | leg2 %s (%s) | %s; %s; %s" %
         (cmp_, jle_, leg2, leg2skip, sete, addd, store))


def g3():
    stores = find(r'^mov DWORD PTR \[ebp-0x60\],\w+$', FUN, FUN + 14349)
    live = [p for p in stores if p < 0x55849b]
    expect = {
        0x5583b8: "mov edx,DWORD PTR ds:0x985b30",
        0x5583c0: "mov bl,BYTE PTR [esi+edi*1+0x94eca8]",
        0x5583c8: "call 0x531090",
        0x558406: "setg dl",
        0x558409: "add edx,ecx",
        0x55840d: "cmp DWORD PTR ds:0x985afc,0x4b",
        0x558414: "setg cl",
        0x558417: "add edx,eax",
        0x55841b: "lea edx,[ecx+edx*1+0x3]",
        0x558424: "mov DWORD PTR [ebp-0x60],edx",
        0x55848f: "mov edx,DWORD PTR [ecx+0x94d810]",
        0x558495: "sub edx,DWORD PTR [ecx+0x94d818]",
        0x55849b: "mov ecx,DWORD PTR [ebp-0x60]",
        0x55849e: "add edx,ecx",
        0x5584a2: "imul edx,edi",
        0x5584a8: "shl edx,1",
    }
    bad = [(hex(p), txt(p), w) for p, w in expect.items() if txt(p) != w]
    ok = (not bad) and bool(live) and live[-1] == 0x558424
    gate(3, ok, "LHS = 2 * (([block+0x94d810] - [block+0x94d818] + [ebp-0x60]) * [ebp-0x3c]); "
         "[ebp-0x60] has %d stores in FUN_00556690 (%s); the last one before the 0x55849b load is %s "
         "(%s) whose value is 3 + (ds:0x985afc > 75) + %s(ds:0x985b30, 0) adjusted by the base count "
         "[block+0x94e488] > 4 and the byte [block+region+0x94eca8] < 4, + the fold count [ebp-0x68]; "
         "%d pinned pcs mismatched: %s" %
         (len(stores), ",".join(hex(p) for p in stores), hex(live[-1]) if live else "-",
          txt(0x558424) if live else "-", txt(0x5583c8), len(bad),
          "; ".join("%s got %r want %r" % b for b in bad)))


def g4():
    scaled = txt(0x5584aa)
    unscaled = txt(0x558452)
    add = txt(0x5584b2)
    zeroed = txt(0x5584a0)
    ok = (scaled == "mov cx,WORD PTR [edi*2+0x94eaa8]" and unscaled == "mov ax,WORD PTR [edi+0x94eaa8]"
          and add == "add ecx,eax" and zeroed == "xor ecx,ecx")
    # the two reads address the same slot: edi = [ebp-0x18] = esi = 2*region + 188*arg (unscaled,
    # the row address is already scaled) and edi = [ebp-0x10] = region (scaled by 2 here)
    row = txt(0x558038)
    ok = ok and row == "mov DWORD PTR [ebp-0x18],esi"
    refs = token_sites("0x94eaa8")
    gate(4, ok, "RHS = %s + %s -> %s (ecx zeroed at 0x5584a0 by %s); row slot from %s; "
         "0x94eaa8 refs image-wide = %d: %s" %
         (scaled, unscaled, add, zeroed, row, len(refs),
          "; ".join("%s %s [%s]" % (hex(p), t, f or "?") for p, t, f in refs)))


def g5():
    fold = [txt(p) for p in (0x558002, 0x55800d, 0x558013, 0x558016, 0x558021, 0x558026)]
    expect = ["add eax,edi", "lea eax,[edi+eax*2]", "shl eax,0x4", "sub eax,edi",
              "lea esi,[ecx+eax*2]", "shl esi,1"]
    bound = txt(0x558b1c)
    inc = txt(0x558b1b)
    back = txt(0x558b25)
    init = txt(0x557f9e)
    arg = txt(0x557fbb)
    ok = (fold == expect and bound == "cmp ecx,0x80" and inc == "inc ecx"
          and back.startswith("jl 0x557fb8") and init == "mov DWORD PTR [ebp-0x10],0x1"
          and arg == "mov edi,DWORD PTR [ebp+0x8]")
    gate(5, ok, "row = %s -> esi = 2*region + 188*arg1; %s, %s, %s (region loop 1..127, init %s); "
         "188 B per faction row vs 2 B per region means region 94..127 spills past its own row "
         "(max offset 188*7 + 254 = %d), so the row reading is a STRIDE CONFLICT the image cannot "
         "settle - OPEN (one live read of both indexings settles it)" %
         ("; ".join(fold), inc, bound, back, init, 188 * 7 + 254))


def g6():
    a = txt(0x558069)
    b = txt(0x558060)
    w = txt(0x55807f)
    by = txt(0x558094)
    step = txt(0x558397)
    cnt = txt(0x5583a0)
    gate(6, a == "lea eax,[ecx*2+0x950764]" and b == "lea eax,[ecx+0x950664]"
         and w == "mov cx,WORD PTR [eax]" and by == "mov al,BYTE PTR [ecx]"
         and step == "mov ecx,0x20bc" and cnt == "cmp eax,0x8",
         "the 8-slot fold walks %s (word per region) and %s (byte per region), stepped by %s == the "
         "faction stride 0x20bc over %s slots (counter [ebp-0x14], init 1 at 0x558047, tested at "
         "0x5583a0); per-slot reads %s / %s; the shifted halves accumulate into [ebp-0x6c] "
         "(0x5580aa-0x5580af) and [ebp-0x60] (0x5580b2-0x5580b9), the nonzero count into [ebp-0x68] "
         "(0x5580be-0x5580c5)" % (a, b, step, cnt, w, by))


def g7():
    lo, hi = txt(0x558082), txt(0x55807f)
    step, hi_init, lo_init = txt(0x558397), txt(0x558069), txt(0x558060)
    other = txt(0x4f7a0a)
    ok = (hi == "mov cx,WORD PTR [eax]" and lo == "mov bx,WORD PTR [eax-0x200]"
          and step == "mov ecx,0x20bc" and hi_init == "lea eax,[ecx*2+0x950764]"
          and lo_init == "lea eax,[ecx+0x950664]" and 0x950764 - 0x200 == 0x950564
          and other == "lea esi,[esi*2+0x950564]")
    gate(7, ok, "the folded pair is %s (0x200 BELOW the cursor) vs %s (AT it); cursor = %s, so the "
         "pair is 0x950764 + 2*region and 0x950564 + 2*region; 0x950564 is itself a table base at "
         "0x4f7a0a (%s); step %s; byte row %s. 0x950564 is past the file image (%d B -> the image "
         "ends at VA 0x%x): runtime data, its row count is NOT readable statically - OPEN" %
         (lo, hi, hi_init, other, step, lo_init, len(img()), 0x400000 + len(img())))


def g8():
    fam = [0x94e4a8, 0x94e5a8, 0x94e628, 0x94e6a8, 0x94e7a8, 0x94e8a8, 0x94e9a8, 0x94eaa8,
           0x94eba8, 0x94eca8, 0x94ed28, 0x94eda8]
    END = 0x94ee28
    rows, ok = [], True
    for i, t in enumerate(fam):
        gap = (fam[i + 1] - t) if i + 1 < len(fam) else (END - t)
        tok = hex(t)
        hits = token_sites(tok)
        widths = collections.Counter()
        for _p, txt_, _f in hits:
            for w in ("DWORD PTR", "WORD PTR", "BYTE PTR"):
                if w in txt_:
                    widths[w] += 1
        n = len(hits)
        nfns = len(set(p for p, _, _ in hits))
        nst = len(stores_of(tok))
        alias = len(token_sites(hex(t + 1)))
        dw, word, byte = widths["DWORD PTR"], widths["WORD PTR"], widths["BYTE PTR"]
        if gap == 0x80:
            shape_ok, implied = (dw == 0 and word == 0 and byte > 0), "byte x 128"
        else:
            shape_ok, implied = (gap == 0x100 and dw == 0 and word > 0), "word x 128"
        ok = ok and shape_ok and n > 0
        nf = len(set(f for _, _, f in hits))
        rows.append("%s: %d refs in %d pcs / %d funcs, %d stores, +1 alias %d, B=%d W=%d D=%d, "
                    "gap 0x%x -> %s %s"
                    % (tok, n, nfns, nf, nst, alias, byte, word, dw, gap, implied,
                       "OK" if shape_ok else "MISMATCH"))
    gate(8, ok, "0x94e4a8..%s is %d per-region arrays; every gap is 0x80 or 0x100 and matches the "
         "observed operand width (0x80 = byte per region, 0x100 = word per region), with ZERO DWORD "
         "accesses anywhere; cmp ecx,0x80 at 0x558b1c supplies the 128 entries each. %s" %
         (hex(END), len(fam), "; ".join(rows)))


def main():
    setup()
    for f in (g1, g2, g3, g4, g5, g6, g7, g8):
        f()
    n_ok = sum(1 for r in results if r)
    verdict = "PASS" if n_ok == len(results) else "FAIL"
    line = "SUMMARY %s: %d/%d gates on terran.exe (static image, no box)" % (verdict, n_ok, len(results))
    print(line)
    body = ["M256/M257/M258 worth-test operands + per-region array family (static, no box)",
            "command: python3 scripts/m256_worth_operands.py",
            "acceptance: " + line, ""] + LOG
    body += ["", "worth-test span:"] + ["  %s: %s" % (hex(p), txt(p)) for p in WORTH_PCS]
    extra = (0x5584b4, 0x5584b6, 0x5584d8, 0x5584da, 0x5584e3, 0x5584eb, 0x5584fe, 0x558500,
             0x558502, 0x558509, 0x55850b, 0x55850e, 0x558511, 0x558514, 0x558516, 0x55851d,
             0x558b18, 0x558b1b, 0x558b1c, 0x558b22, 0x558b25,
             0x557fbe, 0x558002, 0x55800d, 0x558013, 0x558016, 0x558021, 0x558026, 0x558028,
             0x55802b, 0x558031, 0x558038, 0x55803b, 0x558040, 0x55804e, 0x558053, 0x55805d,
             0x558060, 0x558069, 0x558070, 0x55807f, 0x558082, 0x558094, 0x558096, 0x558098,
             0x5580a0, 0x5580a2, 0x5580aa, 0x5580b2, 0x5580b5, 0x5580b9, 0x5580d6, 0x5580e6,
             0x5580eb, 0x5580ed,
             0x557fc0, 0x557fc8, 0x557fd4, 0x557fdf, 0x557fe7,
             0x5583b2, 0x5583b5, 0x5583b8, 0x5583be, 0x5583c0, 0x5583c7, 0x5583c8, 0x5583cd,
             0x5583d6, 0x5583d9, 0x5583de, 0x5583e5, 0x5583e8, 0x5583ea, 0x5583ec, 0x5583ef,
             0x5583f3, 0x5583f5, 0x5583f7, 0x5583fd, 0x558403, 0x558406, 0x558409, 0x55840b,
             0x55840d, 0x558414, 0x558417, 0x55841b, 0x55841f, 0x558422, 0x558424, 0x558427,
             0x55842d, 0x558432, 0x558439, 0x558440, 0x558444, 0x5584e5, 0x5584e8, 0x5584eb,
             0x5584ed, 0x5584f0, 0x5584f2, 0x5584f5, 0x5584f7, 0x55851b, 0x55851f,
             0x558b03, 0x558b05, 0x558b0a, 0x558b0d, 0x558b0f, 0x558b10, 0x558b15, 0x4f7a0a)
    body += ["", "loop head / region bound / flag-word sites:"]
    body += ["  %s: %s" % (hex(p), txt(p)) for p in extra]
    OUTFILE.write_text("\n".join(body) + "\n")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
