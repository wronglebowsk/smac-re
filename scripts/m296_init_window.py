#!/usr/bin/env python3
"""M296 - byte windows for the best-init chain 0x563820-0x5638a9 and the
accept-store/loop-tail segment 0x563c96-0x563cbd of FUN_0055f650 (terran.exe
.text via the shipped objdump window helper semantics). Pins asserted."""
import os, re, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, "terran.exe")
OUT = os.path.join(ROOT, "evidence", "m296_init_window.txt")
def win(lo, hi):
    r = subprocess.run(["objdump", "-M", "intel", "--start-address", hex(lo),
                        "--stop-address", hex(hi), "-d", EXE],
                       capture_output=True, text=True).stdout
    return [ln for ln in r.splitlines() if re.match(r"^ +[0-9a-f]+:", ln)]
PINS = [(0x563836, "cmp    esi,0x8"), (0x563839, "mov    DWORD PTR [ebp-0x24],0x0"),
        (0x563845, "cmp    BYTE PTR [ebx+0x933289],0x18"),
        (0x56384e, "movsx  eax,WORD PTR [ebx+0x933294]"),
        (0x56385b, "movsx  esi,WORD PTR [ebx+0x93328c]"),
        (0x563886, "movsx  edx,WORD PTR [ebx+0x933294]"),
        (0x56388d, "movsx  eax,WORD PTR [ebx+0x93328c]"),
        (0x563896, "call   0x46e770"), (0x56389f, "mov    DWORD PTR [ebp-0x24],eax"),
        (0x563caa, "mov    DWORD PTR [ebp-0x24],esi"),
        (0x563cbd, "jl     0x5638a9")]
lines = []
ok = 1
for seg in ((0x563820, 0x5638aa), (0x563c96, 0x563cc4)):
    lines.append("== window %s-%s ==" % (hex(seg[0]), hex(seg[1])))
    lines += win(*seg)
txt = "\n".join(lines)
for addr, needle in PINS:
    got = [ln.strip() for ln in lines if ln.strip().startswith("%x:" % addr)]
    hit = bool(got) and needle in got[0]
    ok = ok and hit
    print("PIN %#x %-40s %s  %s" % (addr, needle, "OK" if hit else "MISS",
                                    got[0] if got else ""))
open(OUT, "w").write("M296 init-leg + accept-store windows (FUN_0055f650, terran.exe .text)\n"
                     + txt + "\n" +
                     "\n".join("PIN %s %s" % (hex(a), n) for a, n in PINS) + "\n"
                     + "all pins asserted: %d\n" % ok)
print("evidence ->", OUT, "ALL_PINS_OK" if ok else "PIN_FAIL")
sys.exit(0 if ok else 1)
