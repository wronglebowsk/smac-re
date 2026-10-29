#!/usr/bin/env python3
"""M101 - what FEEDS the research-multiplier block (the inputs of FUN_005a15a0's slot 10)?

M100 proved [fac*8380+0x94d6a4] is slot 10 (the last) of the 11-dword array A at
&DAT_0094d67c + fac*0x20bc, rebuilt from ZERO every round by FUN_005a15a0 (called by
FUN_005a1830(fac), a stage of the per-player turn sequence at 0x520904).

This milestone answers WHERE THE VALUES COME FROM, by instruction bytes + a live model:

  FUN_005a15a0(param_1 = &DAT_0094d658+fac*0x20bc, param_2 = array, param_3 = fac, -, param_5)
  (shard_015.c:17034-17103; the strides are the BYTES at 0x5a15d3-0x5a15ec, not Ghidra's
  display scale - and they agree with Ghidra's 0xd4 / 0x2c):
    0x5a15b3  rep stosd [edi],eax(0)            -> A[0..10] = 0
    0x5a15d3  edx = *(param_1 + cat*4)          -> the record INDEX that category uses
    0x5a15ec  lea eax,[ebx+eax*4+0x92babc]      -> row = 0x92babc + cat*212 + idx*44
                (cat: *3*9*2 - cat = 53, *4 = 212 = 0xd4;  idx: *5, + 2* = 11, <<2 = 44 = 0x2c;
                 4 records per category: live idx values run 0..3 and 4*44 = 176 <= 212)
    per slot i:  v = row[i];  if (v >= 0) A[i] += v            (0x5a16d9 store)
                 if (v < 0)  the leg block 0x5a160a-0x5a16d0 (project scan, base-owner skips)
    0x5a1792  lea ecx,[ecx*4+0x94d700]; 0x5a179e add [eax],edi
                                              -> A[i] += D[i]  (D = &DAT_0094d700+fac*0x20bc)
    0x5a17bb  count = *(0x927a9c+fac*1436); 0x5a17c5 esi = 0x927ac0+fac*1436;
              type = [esi-0x20] (= 0x927aa0+fac*1436+i*4), slot = [esi]
                type 4  -> A[slot] = clamp(A[slot], 0, 999)     (0x5a1807)
                type 10 -> if (A[slot] < 0) A[slot] = A[slot]/2 (C trunc toward zero)
    (param_5 != 0 skips the +1/+2 legs, the D-add and the clamps - that is array C.)

PREDICTIONS computed from live /proc BEFORE any conclusion (no gdb, no poke, no boundary):
  MODEL : A[10] = (sum of the 4 category rows' dword 10, legs included) + D[10], clamps after.
  NULL1 : A[10] == D[10] alone (the category rows do not feed it)
  NULL2 : A[10] == the 4-row sum alone (array D does not feed it)
  NULL3 : A[10] is always 0 (a vacuous block)
The four disagree on the live data (mults {0,-2,0,2,0,0,-2,0}) -> the shape discriminates.

  python3 scripts/m101_block_feed.py --tag m101feed1
"""
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import m55_boundary as M  # noqa: E402  (find_pid only)

STRIDE = 8380
IDX, PREV, FLAG = 0x94d658, 0x94d668, 0x94d678
A0, B0, C0, D0 = 0x94d67c, 0x94d6a8, 0x94d6d4, 0x94d700
SLOT10 = 0x28
ROWTAB, ROW_CAT, ROW_REC, ROW_MAX = 0x92babc, 212, 44, 3
PROJ, PROJ_STRIDE = 0x927a88, 1436
G_B9C, G_B90, G_B70, G_B98 = 0x985b9c, 0x985b90, 0x985b70, 0x985b98
BASEOWN = 0x95da14          # byte at BASEOWN + base*304 == the base's faction
ROUND, CP = 0x985afc, 0x985dcc
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
INSN = re.compile(r"^\s*[0-9a-f]{6,8}:\t")
WRITERS = {"mov", "add", "sub", "and", "or", "xor", "adc", "sbb", "inc", "dec", "neg",
           "shl", "shr", "rep", "xchg"}


def trunc2(v):
    """C's /2 on a signed int: toward zero."""
    return v // 2 if v >= 0 else -((-v) // 2)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m101feed1")
    a = ap.parse_args()

    pid = M.find_pid()
    mem = open(f"/proc/{pid}/mem", "rb", 0)

    def rd(addr, n):
        try:
            mem.seek(addr)
            b = mem.read(n)
        except OSError:
            b = b""
        if len(b) < n:
            raise SystemExit(f"EIO reading {addr:#x} ({len(b)}/{n} bytes)")
        return b

    def i32(addr):
        return struct.unpack("<i", rd(addr, 4))[0]

    def u8(addr):
        return rd(addr, 1)[0]

    rnd, cp = i32(ROUND), i32(CP)
    g = {k: i32(v) for k, v in (("b9c", G_B9C), ("b90", G_B90), ("b70", G_B70), ("b98", G_B98))}

    def owner(base):
        if base is None or base < 0:
            return -1
        return u8(BASEOWN + base * 304)

    print(f"pid {pid} round {rnd} cp {cp} globals b9c={g['b9c']} b90={g['b90']} "
          f"b70={g['b70']} b98={g['b98']}", flush=True)

    tab = rd(ROWTAB, 4 * ROW_CAT)          # the 4 category blocks, 848 bytes

    def row10(cat, idx):
        off = cat * ROW_CAT + idx * ROW_REC + SLOT10
        return struct.unpack("<i", tab[off:off + 4])[0]

    F = {}
    for f in range(8):
        b = f * STRIDE
        idxs = [i32(IDX + b + c * 4) for c in range(4)]
        prevs = [i32(PREV + b + c * 4) for c in range(4)]
        flag = i32(FLAG + b)
        A = [i32(A0 + b + i * 4) for i in range(11)]
        B = [i32(B0 + b + i * 4) for i in range(11)]
        C = [i32(C0 + b + i * 4) for i in range(11)]
        D = [i32(D0 + b + i * 4) for i in range(11)]
        cnt = max(0, min(8, i32(PROJ + f * PROJ_STRIDE + 20)))
        ents = [(i32(PROJ + f * PROJ_STRIDE + 24 + i * 4),        # type
                 i32(PROJ + f * PROJ_STRIDE + 56 + i * 4),        # field / slot
                 i32(PROJ + f * PROJ_STRIDE + 88 + i * 4))        # record index
                for i in range(cnt)]
        F[f] = dict(idx=idxs, prev=prevs, flag=flag, A=A, B=B, C=C, D=D, cnt=cnt, ents=ents)

    print("--- live block (per faction) ---", flush=True)
    for f in range(8):
        d = F[f]
        rows = [row10(c, d["idx"][c]) if 0 <= d["idx"][c] <= ROW_MAX else None
                for c in range(4)]
        print(f"  fac{f} idx={d['idx']} prev={d['prev']} flag={d['flag']} "
              f"row10={rows} D10={d['D'][10]} A10={d['A'][10]} "
              f"A[2,5]={d['A'][2]},{d['A'][5]} B10={d['B'][10]} C10={d['C'][10]} "
              f"nproj={d['cnt']} ents={d['ents']}", flush=True)

    def model(f, use_rows=True, use_D=True):
        """FUN_005a15a0's slot 10 for faction f, from the live inputs. Returns (val, legs)."""
        d = F[f]
        acc, legs = 0, []
        if use_rows:
            for c in range(4):
                idx = d["idx"][c]
                if not (0 <= idx <= ROW_MAX):
                    legs.append(f"c{c}:idx{idx}!range")
                    continue
                v = row10(c, idx)
                if v >= 0:
                    acc += v
                    continue
                # negative-dword leg (0x5a160a-0x5a16d0)
                skip = False
                if c != 3:
                    if c == 2 and idx == 1 and g["b9c"] >= 0 and owner(g["b9c"]) == f:
                        skip = True
                        legs.append(f"c{c}:skip(b9c)")
                else:
                    if idx == 3:
                        if g["b9c"] >= 0 and owner(g["b9c"]) == f:
                            skip = True
                            legs.append(f"c{c}:skip(b9c)")
                    elif idx == 1:
                        legs.append("c3:%s(b90)" % ("plainadd" if not (
                            g["b90"] < 0 or owner(g["b90"]) != f) else "scan+add"))
                    else:
                        legs.append(f"c{c}:scan+add")
                if skip:
                    continue
                for (ty, fld, ri) in d["ents"]:
                    if fld == c and ri == idx:
                        if ty == 5:
                            acc -= v
                            legs.append(f"c{c}:sub{idx}")
                        elif ty == 6:
                            acc += v
                            legs.append(f"c{c}:add{idx}")
                acc += v
                legs.append(f"c{c}:add{idx}")
        if use_D:
            acc += d["D"][10]
            for (ty, fld, ri) in d["ents"]:
                if fld == 10 and ty == 4:
                    acc = max(0, min(999, acc))
                    legs.append("clamp4")
                elif fld == 10 and ty == 10 and acc < 0:
                    acc = trunc2(acc)
                    legs.append("half10")
        return acc, legs

    print("--- MODEL (rows+legs+D+clamps) vs live, and the three NULLS ---", flush=True)
    res, n1, n2, n3 = [], [], [], []
    for f in range(8):
        val, legs = model(f)
        live = F[f]["A"][10]
        d10 = F[f]["D"][10]
        rows = sum(row10(c, F[f]["idx"][c]) for c in range(4)
                   if 0 <= F[f]["idx"][c] <= ROW_MAX)
        ok = (val == live)
        res.append((f, val, live, ok, legs))
        n1.append((live == d10, f"live {live} vs D10 {d10}"))
        n2.append((live == rows, f"live {live} vs rows {rows}"))
        n3.append((live == 0, f"live {live}"))
        print(f"  fac{f}: model {val:>4}  live {live:>4}  {'OK' if ok else 'MISMATCH'}  "
              f"legs={legs or '-'}  (rows={rows} D10={d10})", flush=True)

    # static census: who STORES to each field by displacement form (pointer-form stores
    # through a copied register / rep stos evade this grep - that is exactly M100's finding)
    sites = {"0x94d6a4": [], "0x94d700": [], "0x94d658": []}
    census_ok = os.path.exists(TEXT)
    if census_ok:
        with open(TEXT, "r", errors="replace") as fh:
            for ln in fh:
                if not INSN.match(ln):
                    continue
                body = ln.strip().split("\t")
                if len(body) < 3 or "PTR" not in body[2]:
                    continue
                for disp in sites:
                    if disp in body[2]:
                        ops = body[2].split(None, 1)
                        mnem = ops[0].strip() if ops else ""
                        tail = ops[1] if len(ops) > 1 else ""
                        first = tail.split(",")[0]
                        # a cmp/test whose first operand is memory is NOT a store (m101feed2 G8)
                        kind = "STORE" if (disp in first and mnem in WRITERS) else "load"
                        sites[disp].append((body[0].rstrip(":"), kind, body[2].strip()))
    else:
        print("  (scratch/m574/text.txt absent - static census OPEN)", flush=True)
    print("--- static store census (.text, displacement form only) ---", flush=True)
    for disp, rows_ in sites.items():
        st = sorted({(pc, txt) for pc, k, txt in rows_ if k == "STORE"})
        ld = sorted({pc for pc, k, _ in rows_ if k == "load"})
        print(f"  {disp}: {len(rows_)} refs, {len(st)} STORE sites, {len(ld)} load pcs",
              flush=True)
        for pc, txt in st:
            print(f"     {pc}  {txt}", flush=True)

    nz = [f for f in range(8) if F[f]["A"][10] != 0]
    pos = [f for f in range(8) if F[f]["A"][10] > 0]
    neg = [f for f in range(8) if F[f]["A"][10] < 0]
    g1 = True
    g2 = all(ok for _f, _v, _l, ok, _lg in res)
    g3 = bool(pos) and bool(neg) and len(nz) >= 2
    g4 = sum(1 for ok, _s in n1 if not ok) >= 1
    g5 = sum(1 for ok, _s in n2 if not ok) >= 1
    g6 = sum(1 for ok, _s in n3 if not ok) >= 1
    g7 = census_ok and len(sites["0x94d6a4"]) > 0 and not [
        1 for _p, k, _t in sites["0x94d6a4"] if k == "STORE"]
    g8 = census_ok and len({pc for pc, k, _t in sites["0x94d700"] if k == "STORE"}) == 2
    g9 = census_ok and len({pc for pc, k, _t in sites["0x94d658"] if k == "STORE"}) == 1
    g10 = all(0 <= F[f]["idx"][c] <= ROW_MAX for f in range(8) for c in range(4))
    gates = [("G1_reads", g1), ("G2_model_equals_live_8of8", g2), ("G3_nonvacuous_signs", g3),
             ("G4_null_Donly_fails", g4), ("G5_null_rowsonly_fails", g5),
             ("G6_null_zero_fails", g6), ("G7_no_direct_store_to_mult", g7),
             ("G8_D_has_exactly_2_add_sites", g8), ("G9_index_block_1_store_site", g9),
             ("G10_indices_in_range", g10)]
    for n, v in gates:
        print(f"  {n}: {v}", flush=True)
    ok = all(v for _n, v in gates)
    print(f"ACCEPTANCE {a.tag}: {'PASS' if ok else 'FAIL'} "
          f"({sum(1 for _n, v in gates if v)}/{len(gates)}) model "
          f"{[(f, v, l) for f, v, l, _o, _g in res]} "
          f"nulls Donly={[s for ok_, s in n1 if not ok_][:3]} "
          f"rowsonly={[s for ok_, s in n2 if not ok_][:3]} "
          f"stores={ {k: sorted({pc for pc, kk, _ in v if kk == 'STORE'}) for k, v in sites.items()} }",
          flush=True)


if __name__ == "__main__":
    main()
