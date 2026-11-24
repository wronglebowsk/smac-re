#!/usr/bin/env python3
"""M336 — ds:0x8f0090: the difficulty BYTE's sibling cell — who consumes it, and is
difficulty index 6 reachable?

PICK: NEXT_PROMPT.md (x6) remaining clauses, first one (`0x8f0090`'s consumer).
Prior footing: `NAMED ## M332` (`evidence/m332_difficulty_census.txt:104`) ends its
clean-copy map at 0x8f0090 (0x8f0c11 -> 0x8f0090 at 0x488847/0x48884d) and leaves
"the consumer of the byte cell 0x8f0090" OPEN; `NAMED ## M335` — the six `#DIFF`
names live at 0x94d2ac (end 0x94d2c4) and the only clamp FUN_00423af0(0,6) is
INCLUSIVE at the array end.

Every number below is COMPUTED from the static image `scratch/m574/text.txt`
(objdump .text, Intel syntax) plus `ghidra_out/index.csv` (function extents).
Zero box time.

GATES (printed first, then asserted; every V row names a mutant in
scripts/m336_mutate.py):
  G1  direct-displacement census of 0x8f0090: exactly one referencing instruction,
      a STORE, zero loads => the one-form census is complete *for that form* and
      shows the cell is write-only if you only look at this form.
  G2  the frame and the stride read out of the instruction operands (not script
      constants): field+0 disp 0x8eff18, imul imm 0x176, walk count 8, and
      FRAME + 8*STRIDE == 0x8f0ac8 (the cell the reset routine zeroes) => TARGET is
      record 1, byte +2.
  G3  the CONSUMER: the only LOAD from [reg+0x8eff1a] in .text is 0x486788; its index
      is STRIDE*(k+1) with k initialised 0 (0x4865dc) and bounded by
      movsx BYTE ds:0x8f0c10 (0x4865ee) => k=0 is the first iteration, so the
      computed address is EXACTLY 0x8f0090. The byte then feeds [b*4+0x94d2ac]
      (0x48678f), the six-row #DIFF label table.
  G4  the WRITE set in THREE address forms: one direct store, four stride-indexed
      stores at field+2, and one pointer walk (8 iterations from 0x8eff1a by 0x176)
      whose SECOND iteration writes TARGET as [eax] => four routines write the cell
      and the walk alias is DEFINITE, not possible.
  G5  the table the consumer indexes: base 0x94d2ac, loader end 0x94d2c4 => 6 rows;
      b=5 -> 0x94d2c0 (last row), b=6 -> 0x94d2c4 (the end pointer, one past).
  G6  the clamp census on the difficulty byte ds:0x8f0c11: all refs classified
      (6 writes / 6 reads); exactly ONE read is clamp-guarded (0x486f30) and that
      clamp is INCLUSIVE at both ends by its own branch chain, so clamp(6,0,6)=6;
      no write site compares the stored value against 5 => index 6 is admissible on
      the whole path.
  G7  RIVALS, measured and killed: (a) "0x8f0090 is dead storage (1 ref, 1 write)"
      dies in G3 (one reachable load, address-equal at k=0); (b) "0x8eff1a is the
      record base, so TARGET is record 1 offset 0 and offset 0 is never initialised"
      dies on 0x525c42 (mov edi,0x8f008e = FRAME+STRIDE) and the field+0 accesses
      at 0x8eff18 => TARGET is FRAME+1*STRIDE+2.
"""
import csv
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
IDX = os.path.join(ROOT, "ghidra_out/index.csv")

TARGET = 0x8F0090
DIFF = 0x8F0C11          # the difficulty byte (M332/M335)
FRAME = 0x8EFF18         # record base, field +0
FIELD2 = 0x8EFF1A        # record base + 2 = the difficulty byte
STRIDE = 0x176
ARRAY_END = 0x8F0AC8
TABLE = 0x94D2AC
TABLE_END = 0x94D2C4

LINE = re.compile(r"^\s*([0-9a-f]{6,8}):\s+((?:[0-9a-f]{2} )+)\s*\t(.*)$")
HX = re.compile(r"0x[0-9a-f]+")
MUT = os.environ.get("M336_MUT", "")


def load():
    ins = []
    with open(TEXT, errors="replace") as f:
        for line in f:
            m = LINE.match(line.rstrip("\n"))
            if not m:
                continue
            a = int(m.group(1), 16)
            bs = bytes.fromhex(m.group(2).replace(" ", ""))
            txt = m.group(3).strip()
            parts = txt.split(None, 1)
            ins.append({"a": a, "bs": bs, "mn": parts[0],
                        "ops": parts[1] if len(parts) > 1 else ""})
    ins.sort(key=lambda x: x["a"])
    return ins


def patch(i, old, new):
    """Rewrite an operand value in BOTH the bytes and the disassembled text."""
    ob, nb = old.to_bytes(4, "little"), new.to_bytes(4, "little")
    k = i["bs"].find(ob)
    if k >= 0:
        i["bs"] = i["bs"][:k] + nb + i["bs"][k + 4:]
    o, n = f"0x{old:x}", f"0x{new:x}"
    if o in i["ops"]:
        i["ops"] = i["ops"].replace(o, n, 1)
    else:   # 1-byte immediates (push imm8)
        o1, n1 = f"0x{old & 0xff:x}", f"0x{new & 0xff:x}"
        i["ops"] = i["ops"].replace(o1, n1, 1)
        k = i["bs"].find(bytes([old & 0xff]))
        if k >= 0:
            i["bs"] = i["bs"][:k] + bytes([new & 0xff]) + i["bs"][k + 1:]


def apply_mut(ins):
    """Mutants perturb the measured INPUT (the instruction stream), never a threshold."""
    if not MUT:
        return ins, []
    by = {i["a"]: i for i in ins}
    done = []
    if MUT == "drop_reader":
        ins = [i for i in ins if i["a"] != 0x486788]
        done.append(0x486788)
    elif MUT == "stride_175":
        patch(by[0x4866D2], STRIDE, 0x175); done.append(0x4866D2)
    elif MUT == "stride_175b":
        patch(by[0x486782], STRIDE, 0x175); done.append(0x486782)
    elif MUT == "direct_moved":
        patch(by[0x48884D], TARGET, 0x8F0091); done.append(0x48884D)
    elif MUT == "count7":
        patch(by[0x4E2495], 8, 7); done.append(0x4E2495)
    elif MUT == "clamp_hi5":
        patch(by[0x486F2C], 6, 5); done.append(0x486F2C)
    elif MUT == "clamp_exclusive":
        i = by[0x423B14]
        if i["mn"] != "jle":
            raise SystemExit("mutant: 0x423b14 is not jle")
        i["mn"] = "jl"; done.append(0x423B14)
    elif MUT == "value_src":
        patch(by[0x487E81], DIFF, 0x8F0C12); done.append(0x487E81)
    elif MUT == "table_end_moved":        # the loader's end cmp 0x94d2c4 -> 0x94d2c0
        patch(by[0x57AC88], TABLE_END, 0x94D2C0); done.append(0x57AC88)
    elif MUT == "naive_alias":
        done.append("algorithm")      # handled in the alias resolvers
    else:
        raise SystemExit(f"unknown mutant {MUT}")
    return ins, done


def hexes(s):
    return [int(x, 16) for x in HX.findall(s)]


def disp(i):
    """Memory displacement of the first memory operand (inside [...] or ds:)."""
    m = re.search(r"\[([^\]]+)\]", i["ops"])
    if m:
        h = hexes(m.group(1))
        return h[-1] if h else None
    m = re.search(r"ds:(0x[0-9a-f]+)", i["ops"])
    return int(m.group(1), 16) if m else None


def imm(i):
    """Last immediate operand (outside brackets)."""
    outside = re.sub(r"\[[^\]]*\]", "", i["ops"])
    outside = re.sub(r"ds:0x[0-9a-f]+", "", outside)
    h = hexes(outside)
    return h[-1] if h else None


def is_write(i):
    dst = i["ops"].split(",", 1)[0]
    return ("BYTE PTR" in dst or "DWORD PTR" in dst or "WORD PTR" in dst
            or "ds:0x" in dst or dst.strip().startswith("["))


def mem_refs(ins, val):
    """Instructions addressing `val`: as a displacement (direct) or as an immediate."""
    out = []
    for i in ins:
        d = disp(i)
        im = imm(i)
        if d == val or (im == val):
            out.append(i)
    return out


def access_sites(ins, val):
    """The census. The `naive_alias` ALGORITHM mutant keeps only ds:<val> direct forms,
    i.e. the model that produced M332's 'one write, no reader' count."""
    if MUT == "naive_alias":
        pat = re.compile(rf"ds:0x{val:x}\b")
        return [i for i in ins if pat.search(i["ops"])]
    return mem_refs(ins, val)


def source_cell(ins, site):
    """Nearest preceding load of a byte inside the same run of straight-line code."""
    prev_call = max([x["a"] for x in ins if x["mn"] == "call" and x["a"] < site["a"]]
                    or [0])
    win = [x for x in ins if prev_call < x["a"] < site["a"]]
    for x in reversed(win):
        if x["mn"] in ("cmp", "call", "ret", "jmp"):
            continue
        if "BYTE PTR" in x["ops"] and not is_write(x):
            return disp(x)
    return None


def fnof(addr, rows):
    for r in rows:
        b = int(r["addr"], 16)
        if b <= addr < b + int(r["size_bytes"]):
            return r["name"]
    return "?"


def main():
    ins, mutated = apply_mut(load())
    rows = list(csv.DictReader(l for l in open(IDX) if not l.startswith("#")))
    by = {i["a"]: i for i in ins}
    gates = []

    def gate(gid, ok, detail):
        gates.append((gid, bool(ok), detail))

    # ---------------- G1: direct-displacement census ----------------
    refs = mem_refs(ins, TARGET)
    print(f"== G1 direct-displacement census of ds:0x{TARGET:x} ({len(refs)} refs) ==")
    for i in refs:
        print(f"  {i['a']:#08x} {'W' if is_write(i) else 'R'} {i['mn']:7s} {i['ops']}"
              f"   [{fnof(i['a'], rows)}]")
    w1 = [i for i in refs if is_write(i)]
    r1 = [i for i in refs if not is_write(i)]
    print(f"  refs={len(refs)} writes={len(w1)} loads={len(r1)}")
    gate("G1", len(refs) == 1 and len(w1) == 1 and not r1,
         f"direct refs={len(refs)} (W{len(w1)}/R{len(r1)})")

    # ---------------- G2: frame + stride from the operands ----------------
    f0_read = disp(by[0x4866D8])      # movsx edx,BYTE PTR [ecx+0x8eff18]
    f0_write = disp(by[0x487E60])     # mov BYTE PTR [edx+0x8eff18],al
    stride_a = imm(by[0x4866D2])      # imul ecx,ecx,0x176
    stride_b = imm(by[0x487E57])
    count = imm(by[0x4E2495])         # mov edx,0x8
    walk_base = imm(by[0x4E2490])     # mov eax,0x8eff1a
    rec1 = imm(by[0x525C42])          # mov edi,0x8f008e
    end_cell = disp(by[0x4E2482])     # mov ds:0x8f0ac8,eax
    print("\n== G2 frame / stride / record count, read from the operands ==")
    print(f"  field+0 read disp {f0_read:#x}   write disp {f0_write:#x}")
    print(f"  imul immediates  {stride_a:#x} (0x4866d2)   {stride_b:#x} (0x487e57)")
    print(f"  walk base {walk_base:#x} count {count}   record-1 pointer {rec1:#x}")
    print(f"  array end cell {end_cell:#x}")
    print(f"  TARGET - field+2 base = {TARGET - walk_base:#x} = "
          f"{(TARGET - walk_base) / stride_a:.3f} * stride")
    print(f"  record 1 = FRAME + stride = {FRAME + stride_a:#x}  "
          f"(TARGET - record1 = {TARGET - (FRAME + stride_a)})")
    print(f"  FRAME + {count}*stride = {FRAME + count * stride_a:#x}   "
          f"(reset end cell {end_cell:#x})")
    gate("G2", f0_read == FRAME and f0_write == FRAME and stride_a == STRIDE == stride_b
         and count == 8 and rec1 == FRAME + STRIDE and end_cell == FRAME + count * STRIDE
         and TARGET == FRAME + STRIDE + 2 and TARGET == walk_base + STRIDE,
         f"frame={f0_read:#x} stride={stride_a:#x} count={count} "
         f"end={end_cell:#x} rec1={rec1:#x}")

    # ---------------- G3: the one consumer, alias proven ----------------
    band = access_sites(ins, FIELD2)
    band_loads = [i["a"] for i in band if not is_write(i) and "PTR [" in i["ops"]]
    band_stores = [i["a"] for i in band if is_write(i)]
    band_imm = [i["a"] for i in band if "PTR [" not in i["ops"]]
    print(f"\n== G3 accesses through the field+2 displacement 0x{FIELD2:x} ==")
    for i in band:
        print(f"  {i['a']:#08x} {'W' if is_write(i) else 'R'} {i['mn']:7s} {i['ops']}"
              f"   [{fnof(i['a'], rows)}]")
    print(f"  loads={[hex(x) for x in band_loads]}  stores={[hex(x) for x in band_stores]}"
          f"  materialisations={[hex(x) for x in band_imm]}")
    loop_init, loop_inc = by[0x4865DC], by[0x4865E8]
    loop_bound, loop_test = by[0x4865EE], by[0x4865F8]
    idx = imm(by[0x486782])           # imul ecx,ecx,0x176  (after add ecx,1)
    feeds = by[0x48678F]
    tbase = disp(feeds)
    addr_k0 = walk_base + idx
    print(f"  index chain:")
    print(f"    {loop_init['a']:#08x} {loop_init['mn']} {loop_init['ops']}   (k=0)")
    print(f"    {loop_inc['a']:#08x} {loop_inc['mn']} {loop_inc['ops']}   (k=k+1)")
    print(f"    {loop_bound['a']:#08x} {loop_bound['mn']} {loop_bound['ops']}  (bound)")
    print(f"    {loop_test['a']:#08x} {loop_test['mn']} {loop_test['ops']}  (exit)")
    print(f"    0x486782 imul imm={idx:#x}; k=0 -> {walk_base:#x}+{idx:#x} = {addr_k0:#x}"
          f"  equals TARGET: {addr_k0 == TARGET}")
    print(f"  the byte feeds {feeds['a']:#08x} {feeds['mn']} {feeds['ops']} -> table {tbase:#x}")
    # the consumer's containing function and the row copy that proves k is a row index
    rowcopy = by[0x486732]            # shl edx,0x4  (this+0xb54 + k*16)
    print(f"  row index: {rowcopy['a']:#08x} {rowcopy['mn']} {rowcopy['ops']}"
          f"  [{fnof(rowcopy['a'], rows)}]")
    reset_cnt = imm(by[0x4E2444])     # mov BYTE PTR ds:0x8f0c10,0x4
    print(f"  row count: the reset path writes {reset_cnt} to 0x8f0c10 (0x4e2444) => rows "
          f"k=0..{reset_cnt - 1}, i.e. records 1..{reset_cnt} of 8, so record 1 is row 0")
    ok3 = (band_loads == [0x486788] and len(band_stores) == 4
           and loop_init["mn"] == "mov" and "ebp-0x8],0x0" in loop_init["ops"]
           and loop_inc["mn"] == "add" and "0x8f0c10" in loop_bound["ops"]
           and loop_test["mn"] == "jge" and idx == STRIDE and addr_k0 == TARGET
           and tbase == TABLE and rowcopy["mn"] == "shl" and 0 < reset_cnt <= 7)
    gate("G3", ok3, f"only load {[hex(x) for x in band_loads]} idx={idx:#x} "
                    f"k0={addr_k0:#x} feeds table {tbase:#x}")

    # ---------------- G4: the walk (third address form) ----------------
    walk_store = by[0x4E24A2]         # mov BYTE PTR [eax],cl
    walk_add, walk_dec = by[0x4E24AB], by[0x4E24B0]
    walk_jne = by[0x4E24B1]
    iters = [walk_base + n * STRIDE for n in range(count)]
    hit = [n for n, a in enumerate(iters) if a == TARGET]
    print(f"\n== G4 the pointer walk from 0x4e2490 ==")
    for a in (0x4E249C, 0x4E249F, 0x4E24A2, 0x4E24A4, 0x4E24A7, 0x4E24AB, 0x4E24B0, 0x4E24B1):
        i = by[a]
        print(f"  {a:#08x} {i['mn']:5s} {i['ops']}")
    print(f"  addresses {iters[0]:#x} .. {iters[-1]:#x} step {STRIDE:#x}, {count} iterations")
    print(f"  TARGET is iteration {hit} -> the [eax] store writes 0x8f0090 with "
          f"{walk_store['ops'].split(',')[-1]}")
    print(f"  field+2 writers: direct {[hex(i['a']) for i in w1]} + stride-indexed "
          f"{[hex(x) for x in band_stores]} + walk {walk_store['a']:#x}")
    srcs = {s: source_cell(ins, by[s]) for s in band_stores}
    print("  value source of each stride-indexed store (nearest preceding byte load):")
    for s, v in srcs.items():
        print(f"    {s:#08x} <- {'literal 0' if v is None else hex(v)}")
    ok4 = (hit == [1] and walk_store["mn"] == "mov" and walk_add["mn"] == "add"
           and walk_dec["mn"] == "dec" and walk_jne["mn"] == "jne" and len(band_stores) == 4
           and sum(1 for v in srcs.values() if v == DIFF) == 3
           and all(v is None or v == DIFF for v in srcs.values()))
    gate("G4", ok4, f"walk_alias_iter={hit} field+2 store sites={len(band_stores) + 1 + len(w1)} "
                    f"sources={[('lit0' if v is None else hex(v)) for v in srcs.values()]}")

    # ---------------- G5: the table the consumer indexes ----------------
    lwin = [i for i in ins if 0x57AC00 <= i["a"] <= 0x57AD80]
    lb = [i for i in lwin if TABLE in (disp(i), imm(i), disp(i) or 0)]
    le = [i for i in lwin if (imm(i) == TABLE_END or disp(i) == TABLE_END)]
    print(f"\n== G5 the #DIFF table (loader window 0x57ac00-0x57ad80) ==")
    for i in lb + le:
        print(f"  {i['a']:#08x} {i['mn']:7s} {i['ops']}")
    nrows = (TABLE_END - TABLE) // 4
    print(f"  base {TABLE:#x} end {TABLE_END:#x} rows={nrows}")
    for b in (0, 5, 6):
        what = ("first row" if b == 0 else "last row" if b == nrows - 1
                else "interior row" if b < nrows else "END POINTER, one past"
                if b == nrows else "PAST END")
        print(f"  b={b} -> {TABLE + 4 * b:#x}  ({what})")
    gate("G5", bool(lb) and bool(le) and nrows == 6 and TABLE + 20 < TABLE_END
         and TABLE + 24 == TABLE_END,
         f"table {TABLE:#x}..{TABLE_END:#x} rows={nrows} b6={TABLE + 24:#x}")

    # ---------------- G6: clamp census on the difficulty byte ----------------
    drefs = mem_refs(ins, DIFF)
    print(f"\n== G6 every reference to the difficulty byte ds:0x{DIFF:x} ==")
    clamped = []
    for i in drefs:
        kind = "W" if is_write(i) else "R"
        extra = ""
        if kind == "R":
            win = [x for x in ins if i["a"] <= x["a"] <= i["a"] + 16]
            call = [x for x in win if x["mn"] == "call" and "0x423af0" in x["ops"]]
            if call:
                prev = max([x["a"] for x in ins if x["mn"] == "call"
                            and i["a"] - 24 <= x["a"] < i["a"]] or [i["a"] - 24])
                pushing = [x for x in ins if prev < x["a"] < call[0]["a"]
                           and x["mn"] == "push"]
                vals = [imm(x) for x in pushing if imm(x) is not None]
                extra = f"  <clamp args {[hex(v) for v in vals]}>"
                clamped.append(i["a"])
        src = ""
        if kind == "W":
            s = i["ops"].split(",", 1)[1] if "," in i["ops"] else ""
            if "ds:" in s:
                src = f"  src={disp(i) if 'PTR' in s else s.strip()}"
        print(f"  {i['a']:#08x} {kind} {i['mn']:7s} {i['ops']}{src}{extra}"
              f"   [{fnof(i['a'], rows)}]")
    w = [i for i in drefs if is_write(i)]
    r = [i for i in drefs if not is_write(i)]
    print(f"  writes={len(w)} reads={len(r)} clamp-guarded reads={[hex(x) for x in clamped]}")
    print("  FUN_00423af0 (the clamp):")
    for a in (0x423AFC, 0x423AFF, 0x423B04, 0x423B07, 0x423B11, 0x423B14, 0x423B16, 0x423B1B):
        i = by[a]
        print(f"    {a:#08x} {i['mn']:5s} {i['ops']}")
    inclusive = (by[0x423AFF]["mn"] == "jl" and by[0x423B07]["mn"] == "jge"
                 and by[0x423B14]["mn"] == "jle")
    call_hi = imm(by[0x486F2C])
    print(f"  inclusive chain (jl/jge/jle)={inclusive}  clamp hi pushed={call_hi}")
    print(f"  clamp(6,0,{call_hi}) = 6 -> [6*4+{TABLE:#x}] = {TABLE + 24:#x} = the end pointer")
    ok6 = (len(w) == 6 and len(r) == 6 and clamped == [0x486F30] and inclusive
           and call_hi == 6 and TABLE + 4 * call_hi == TABLE_END)
    gate("G6", ok6, f"writes={len(w)} reads={len(r)} clamped={[hex(x) for x in clamped]} "
                    f"hi={call_hi} inclusive={inclusive}")

    # ---------------- G7: the two rivals, measured ----------------
    r1_direct_loads = len(r1)
    alias_dead = (r1_direct_loads == 0 and not band_loads)
    rec1_ok = (rec1 == FRAME + STRIDE) and (TARGET - rec1 == 2)
    print("\n== G7 rivals ==")
    print(f"  R1 'dead cell (1 ref, 1 write, no reader)': direct loads={r1_direct_loads}; "
          f"reachable aliased loads={[hex(x) for x in band_loads]} at k=0 -> "
          f"{'STILL STANDING' if alias_dead else 'KILLED'}")
    print(f"  R2 'TARGET is record 1 offset 0': record1={rec1:#x} "
          f"TARGET-record1={TARGET - rec1} record1-FRAME={rec1 - FRAME:#x} "
          f"(stride {STRIDE:#x}), field+0 touched at 0x8eff18 by 0x4866d8/0x487e60 "
          f"-> {'STILL STANDING' if not rec1_ok else 'KILLED'}")
    ok7 = (not alias_dead) and rec1_ok
    gate("G7", ok7, f"R1 killed by load(s) {[hex(x) for x in band_loads]}; "
                    f"R2 killed: rec1={rec1:#x}, TARGET=rec1+{TARGET - rec1}")

    # ---------------- verdict ----------------
    print("\n== gates ==")
    for gid, ok, detail in gates:
        print(f"  {gid}: {'PASS' if ok else 'FAIL'}  {detail}")
    digest = hashlib.sha256(repr([(g, d) for g, o, d in gates]).encode()).hexdigest()[:16]
    npass = sum(1 for _, ok, _ in gates if ok)
    print(f"\ndigest={digest} gates={npass}/{len(gates)}"
          + (f"  MUT={MUT} ({mutated})" if MUT else ""))
    verdict = "PASS" if npass == len(gates) else "FAIL"
    print(f"{verdict} M336: {npass}/{len(gates)} gates" + (f" [mutant {MUT}]" if MUT else ""))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
