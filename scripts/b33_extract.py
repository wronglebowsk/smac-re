#!/usr/bin/env python3
"""scripts/b33_extract.py - the B33 census fixture, derived from the .text dump.

B33 (BUILD_SPINE) asks which of FUN_004ef6d0's two completion legs can reach the bitmap OR
at 0x4f0ec0.  The rung must answer it from a committed artifact, not from scratch/, so this
script writes two fixtures:

  evidence/fixtures/b33_fun4ef6d0_census.txt   every instruction of the function:
                                               `addr len mnemonic operand`, where operand is
                                               a DIRECT branch/call target, else 'ind' for a
                                               register/memory control transfer, else the
                                               [ebp-..] memory ref tagged r (read) or w
                                               (write) by the instruction's own mnemonic,
                                               else '-'.  The length column lets the rung
                                               assert the census is CONTIGUOUS and spans
                                               exactly Ghidra's size.
  evidence/fixtures/b33_key_sites.txt          the raw dump lines at the addresses the rung
                                               names in prose (gates read them back).

Function span: ghidra_out/index.csv row `0x004ef6d0,FUN_004ef6d0,12298,...` -> 12298 bytes.

    python3 scripts/b33_extract.py            # regenerate both fixtures
    python3 scripts/b33_extract.py --check    # re-derive and diff against the committed files
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
OUT_CENSUS = os.path.join(ROOT, "evidence", "fixtures", "b33_fun4ef6d0_census.txt")
OUT_KEYS = os.path.join(ROOT, "evidence", "fixtures", "b33_key_sites.txt")

LO, SIZE = 0x4ef6d0, 12298
HI = LO + SIZE
ADR = re.compile(r"^\s*([0-9a-f]{6,8}):\s+(.*)$")
BYTES = re.compile(r"^((?:[0-9a-f]{2}[ \t]+)+)(.*)$")
JCC = {"jmp", "je", "jne", "jl", "jle", "jg", "jge", "jb", "jbe", "ja", "jae",
       "js", "jns", "jo", "jno", "jp", "jnp", "jz", "jnz"}
# Mnemonics whose FIRST operand is a destination.  Anything else (cmp, test, push, lea,
# call, jcc...) only READS the memory operand - the s333 review's L-write defect.
WRITE_MNEM = {"mov", "movzx", "movsx", "movsxd", "add", "sub", "adc", "sbb", "and", "or",
              "xor", "inc", "dec", "shl", "shr", "sar", "sal", "neg", "not", "imul",
              "xchg", "movnti", "stos"}
KEYS = [0x4ef88b, 0x4ef88e, 0x4ef891, 0x4ef897, 0x4ef899, 0x4ef89f, 0x4ef8a4,
        0x4efa2c, 0x4efadc, 0x4efed1, 0x4efed8, 0x4efedb, 0x4efedd, 0x4efe41, 0x4efe44,
        0x4f0a37, 0x4f0a3d, 0x4f0b7b, 0x4f0b7e, 0x4f0b80, 0x4f0ca1, 0x4f0ca4, 0x4f0ca6,
        0x4f0d1d, 0x4f0d8f, 0x4f0d94, 0x4f0e90, 0x4f0ea2, 0x4f0ebd, 0x4f0ec0, 0x4f0ec2]


def parse():
    rows = []                       # [addr, length, mnem, operands, raw body]
    with open(TEXT, "r", errors="replace") as fh:
        for line in fh:
            m = ADR.match(line)
            if not m:
                continue
            a = int(m.group(1), 16)
            if not (LO <= a < HI):
                continue
            rest = m.group(2)
            b = BYTES.match(rest)
            if b:
                length = len(b.group(1).split())
                tail = b.group(2).strip()
            else:
                length, tail = 0, rest.strip()
            if not tail:                       # objdump wraps long instructions: continuation bytes
                if rows and rows[-1][0] + rows[-1][1] == a:
                    rows[-1][1] += length
                    continue
                raise SystemExit("orphan continuation line at 0x%06x" % a)
            parts = tail.split(None, 1)
            mnem = parts[0].lower()
            operands = parts[1] if len(parts) > 1 else ""
            rows.append([a, length, mnem, operands, tail])
    rows.sort(key=lambda r: r[0])
    return [tuple(r) for r in rows]


def operand_token(mnem, operands):
    if mnem.startswith("j") or mnem == "call":
        op = operands.strip()
        if re.fullmatch(r"0x[0-9a-f]+", op):
            return op
        return "ind"
    if mnem == "ret":
        return "-"
    ebp = re.search(r"\[ebp[^\]]*\]", operands)
    if ebp:
        first = operands.split(",")[0]
        write = mnem in WRITE_MNEM and ebp.group(0) in first
        return ("w" if write else "r") + ebp.group(0)
    return "-"


def render(rows):
    out = ["# B33 census - FUN_004ef6d0 0x%06x..0x%06x (size %d, ghidra_out/index.csv)" % (LO, HI, SIZE),
           "# addr len mnemonic operand  (operand: direct branch/call target, 'ind' = register/"
           "memory, 'r[ebp-..]'/'w[ebp-..]' = read/write by the instruction's mnemonic, else '-')"]
    for a, length, mnem, operands, body in rows:
        out.append("%06x %2d %-8s %s" % (a, length, mnem, operand_token(mnem, operands)))
    return "\n".join(out) + "\n"


def render_keys(rows):
    by = {r[0]: r[4] for r in rows}
    out = ["# B33 key sites - raw dump lines (scratch/m574/text.txt), one per address the rung names"]
    for a in KEYS:
        if a not in by:
            raise SystemExit("missing key site 0x%06x in the dump window" % a)
        out.append("%06x  %s" % (a, by[a]))
    return "\n".join(out) + "\n"


def main(argv):
    rows = parse()
    if not rows:
        raise SystemExit("no instructions parsed: %s" % TEXT)
    covered = sum(r[1] for r in rows)
    if covered != SIZE:
        raise SystemExit("byte coverage %d != Ghidra size %d" % (covered, SIZE))
    census, keys = render(rows), render_keys(rows)
    if "--check" in argv:
        for path, want in ((OUT_CENSUS, census), (OUT_KEYS, keys)):
            with open(path, encoding="utf-8") as fh:
                got = fh.read()
            if got != want:
                raise SystemExit("DIFF %s" % path)
        print("OK %d instructions, %d B, both fixtures reproduce" % (len(rows), covered))
        return 0
    with open(OUT_CENSUS, "w", encoding="utf-8") as fh:
        fh.write(census)
    with open(OUT_KEYS, "w", encoding="utf-8") as fh:
        fh.write(keys)
    print("wrote %s (%d instr, %d B, %d B census) and %s (%d keys)"
          % (os.path.relpath(OUT_CENSUS, ROOT), len(rows), covered, len(census),
             os.path.relpath(OUT_KEYS, ROOT), len(KEYS)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
