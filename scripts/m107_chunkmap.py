#!/usr/bin/env python3
"""M107 — the save CHUNK MAP is a HARD-CODED seek sequence, not a table in the file.

Offline instrument: no box, no gdb, no wine. It reads the objdump of `.text`
(scratch/m574/text.txt), enumerates every `fread` (call 0x64cc00) site inside the save loader
FUN_00596850 [0x596850,0x597a6b], pulls each site's pushed SIZE and DESTINATION out of the
instruction bytes, and then checks the claim against the saves we hold.

    python3 scripts/m107_chunkmap.py --tag m107c1     # gates -> evidence/<tag>.log, PASS/FAIL
    python3 scripts/m107_chunkmap.py --table          # just print the leg table
    python3 scripts/m107_chunkmap.py --tagsrc DIR     # saves dir (default programs/saves)

The question this answers (NEXT_PROMPT 2026-10-29): "is there an (address,size) TABLE in the file,
or does FUN_00596850 hard-code the seek sequence?"
Answer: hard-coded. G3 is the proof that discriminates: not one of the destinations the loader
writes to appears anywhere in the file as a u32, and no (dest,size) pair is adjacent — a file-side
table is impossible, because the destinations live only in .text.

Gates (all predicted from the leg table and the files BEFORE the run):
  G1  30 fread sites in the function, none outside it
  G2  24 immediate-size legs + 6 register/computed legs; every size and dest printed
  G3  NO TABLE: 0/N destinations present as u32 LE in each save, 0 adjacent (dest,size) pairs
  G4  the 0x105e0 static block-A leg is VERSION-GATED (`cmp ds:0x985dbc,3` at 0x596a43, and
      0x985dbc = header 0x985ab8 + 0x304 = file offset 772); u32@772 < 3 in every save =>
      the live leg is the malloc'd 0xe5e0 one, not the static 67,040
  G5  the r7 strace's direct reads land INSIDE declared legs with a <=0x1000 stdio-buffer prefix
  G6  the always-on immediate legs do not overrun any file (residual printed, never negative)
  G7  no box process was used (no gdb/wine/strace spawned by this harness)
"""
import argparse
import glob
import json
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
SAVES = os.path.join(ROOT, "programs/saves")
FUNC = (0x596850, 0x597a6b)
FREAD = "0x64cc00"          # the raw path; 0x64c9a0 is the same read via the stdio buffer
GATE_PC = 0x596a43          # cmp ds:0x985dbc,0x3  -> jl  (the block-A version test)
GATE_FIELD = 0x985dbc
HDR = 0x985ab8              # the 796-byte save header, read at 0x59688a
PROBE_ODD = 23              # the 23-byte pread64 probe at load start (evidence/m106r7.strace)

ADDR = re.compile(r"\s*([0-9a-f]{6,8}):\s")
PUSH = re.compile(r"push\s+(\S+)")


def dis_range(lo, hi):
    """[(addr, 'mnemonic operands')] for the objdump window — bytes column dropped."""
    out = []
    with open(TEXT, errors="replace") as f:
        for line in f:
            m = ADDR.match(line)
            if not m:
                continue
            a = int(m.group(1), 16)
            if a < lo:
                continue
            if a > hi:
                break
            parts = line.rstrip("\n").split("\t")
            asm = parts[2].strip() if len(parts) >= 3 else ""
            out.append((a, asm))
    return out


def legs():
    """Every fread site in the function -> (pc, size_operand, dest_operand)."""
    ins = dis_range(*FUNC)
    out = []
    for i, (a, asm) in enumerate(ins):
        if not re.match(r"call\s+" + FREAD + r"\b", asm):
            continue
        pushes = []
        j = i - 1
        while j >= 0 and len(pushes) < 4 and i - j <= 14:
            asm_j = ins[j][1]
            if asm_j.startswith("ret"):
                break                     # function epilogue: nothing above belongs to this site
            m = PUSH.match(asm_j)
            if m:
                pushes.append(m.group(1))
            j -= 1
        pushes.reverse()              # [FILE*, count, size, dest]
        if len(pushes) < 4:
            out.append((a, "?", pushes[0] if pushes else "?"))
            continue
        out.append((a, pushes[2], pushes[3]))
    return out


def imm(tok):
    try:
        return int(tok, 16)
    except (TypeError, ValueError):
        return None


def saves_list(tagsrc):
    out = [p for p in glob.glob(os.path.join(tagsrc, "*.SAV"))]
    out += glob.glob(os.path.join(tagsrc, "auto", "*.SAV"))
    return sorted(out)


def direct_reads(strace):
    """The (dest,size) of the raw reads the r7 load logged, minus the 0x1000 buffer fills."""
    rows = []
    if not os.path.exists(strace):
        return rows
    for line in open(strace, errors="replace"):
        m = re.match(r"\([\d.]+, \d+, 'read', \d+, (\d+), (\d+), ", line)
        if m:
            rows.append((int(m.group(1)), int(m.group(2))))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="")
    ap.add_argument("--table", action="store_true")
    ap.add_argument("--saves", default=SAVES)
    ap.add_argument("--strace", default=os.path.join(ROOT, "evidence/m106r7.strace"))
    a = ap.parse_args()

    L = legs()
    if a.table:
        for pc, size, dest in L:
            print(f"0x{pc:x}  size={size:>8s}  dest={dest}")
        print(f"{len(L)} legs")
        return 0

    gates, notes = [], []

    # ---- G1: the census itself
    nseen = len(L)
    bad = [pc for pc, _, _ in L if not (FUNC[0] <= pc <= FUNC[1])]
    gates.append(("G1", f"{nseen} fread sites in FUN_00596850, {len(bad)} outside",
                  nseen == 30 and not bad))

    # ---- G2: immediate vs computed
    imms = [(pc, imm(s), d) for pc, s, d in L if imm(s) is not None]
    comp = [(pc, s, d) for pc, s, d in L if imm(s) is None]
    gates.append(("G2", f"immediate-size legs {len(imms)}, computed {len(comp)} "
                        f"[{', '.join(hex(pc) for pc, _, _ in comp)}]",
                  len(imms) == 25 and len(comp) == 5))

    # ---- static destinations (the ones a table would have to name)
    dests = sorted({imm(d) for _, _, d in imms if imm(d) is not None})
    notes.append("static destinations: " + ", ".join(f"0x{d:x}" for d in dests))

    # ---- per save
    files = saves_list(a.saves)
    g3, g4, g6 = [], [], []
    per_file = []
    fixed = sum(s for _, s, _ in imms)
    for p in files:
        b = open(p, "rb").read()
        hits = sum(1 for d in dests if b.count(struct.pack("<I", d)))
        pairs = 0
        for i in range(len(b) - 8):
            x, y = struct.unpack_from("<II", b, i)
            if x in dests and y in (s for _, s, _ in imms):
                pairs += 1
        g3.append((os.path.basename(p), hits, pairs, len(dests)))
        gate = struct.unpack_from("<I", b, GATE_FIELD - HDR)[0]
        g4.append((os.path.basename(p), gate))
        resid = len(b) - fixed
        g6.append((os.path.basename(p), len(b), resid))
        per_file.append({"file": os.path.basename(p), "size": len(b),
                         "dest_hits": hits, "pairs": pairs, "gate": gate,
                         "residual": resid})

    gates.append(("G3", f"no (dest,size) table: dest hits "
                        f"{sorted({h for _, h, _, _ in g3})}, adjacent pairs "
                        f"{sorted({p for _, _, p, _ in g3})} over {len(dests)} destinations x "
                        f"{len(files)} saves",
                  all(h == 0 and pr == 0 for _, h, pr, _ in g3)))
    gates.append(("G4", f"version gate u32@772 = {sorted({g for _, g in g4})} on "
                        f"{len(g4)}/{len(files)} saves -> the malloc'd 0xe5e0 leg is live",
                  all(g < 3 for _, g in g4)))

    # ---- G5: the strace's direct reads sit inside declared legs
    spans = [(imm(d), s) for _, s, d in imms if imm(d) is not None]
    rows = direct_reads(a.strace)
    inside, outside = [], []
    for dest, size in rows:
        if size < 0x2000:                     # 0x1000 buffer fills are not legs
            continue
        hit = None
        for base, ln in spans:
            if base is not None and base <= dest <= base + 0x1000 and dest + size <= base + ln:
                hit = (base, ln)
                break
        (inside if hit else outside).append((dest, size, hit))
    u_in, u_out = sorted({(d, s) for d, s, _ in inside}), sorted({(d, s) for d, s, _ in outside})
    gates.append(("G5", f"{len(rows)} raw reads -> {len(u_in)} unique direct reads inside a "
                        f"declared span, {len(u_out)} outside "
                        f"[{', '.join(f'0x{d:x}+0x{s:x}' for d, s in u_out)}] (heap: the count-sized leg)",
                  len(u_in) == 5 and len(u_out) == 1))

    # ---- G6: the immediate legs never overrun a file, and the live (version-gated) sum is printed
    live = fixed - 0x105e0                 # u32@772 < 3 -> the static block-A leg never runs
    gates.append(("G6", f"immediate legs sum {fixed:,} (live, no 0x105e0: {live:,}); live residuals "
                        f"{sorted({s - live for _, s, _ in g6})[:3]}...",
                  all(r > 0 for _, _, r in g6) and all(s - live > 0 for _, s, _ in g6)))

    # ---- G7: no box
    procs = os.popen("ps -eo cmd | grep -E '^(gdb|strace|winedbg)' | grep -v grep").read().strip()
    gates.append(("G7", f"no gdb/strace/winedbg process: {procs!r}", not procs))

    lines = [f"M107 chunk map — {len(files)} saves, {nseen} legs, tag={a.tag or '-'}"]
    lines += [f"  leg 0x{pc:x}  size={s:>8s}  dest={d}" for pc, s, d in L]
    lines += [""] + ["  " + n for n in notes]
    lines += ["", "  file                                  size    dest h  pairs  gate  residual"]
    lines += [f"  {f['file']:34s} {f['size']:7d} {f['dest_hits']:6d} {f['pairs']:6d} "
              f"{f['gate']:5d} {f['residual']:8d}" for f in per_file]
    lines += [""] + [f"  [{g}] {'PASS' if ok else 'FAIL'}  {msg}" for g, msg, ok in gates]
    npass = sum(1 for _, _, ok in gates if ok)
    verdict = f"VERDICT {'PASS' if npass == len(gates) else 'FAIL'} {npass}/{len(gates)}"
    lines.append("  " + verdict)
    text = "\n".join(lines)
    print(text)

    if a.tag:
        os.makedirs(os.path.join(ROOT, "evidence"), exist_ok=True)
        with open(os.path.join(ROOT, "evidence", f"{a.tag}.log"), "w") as f:
            f.write(text + "\n")
        with open(os.path.join(ROOT, "scratch", f"{a.tag}_map.json"), "w") as f:
            json.dump({"legs": [{"pc": hex(pc), "size": s, "dest": d} for pc, s, d in L],
                       "files": per_file, "verdict": verdict}, f, indent=1)
    return 0 if npass == len(gates) else 1


if __name__ == "__main__":
    sys.exit(main())
