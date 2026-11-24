#!/usr/bin/env python3
"""M365 mutation harness — every VERIFIED row of scripts/m365_pair_slot.py names a mutant here.

A mutant is KILLED when its named gate turns red in a real run of the tool.  Two kinds:

  TEXT  rewrites ONE instruction line of the objdump cache (the tool reads it via M365_TEXT),
        i.e. the DISASSEMBLY is mutated and the tool must notice.
  SRC   rewrites ONE line of the tool's own algorithm (the linear-form tracer), i.e. the
        instrument is mutated and its self-test must notice.

Gate coverage is MEASURED: the gate ids are read from the tool's own PASS/FAIL line and its
"[ok]/[XX] <id>" rows, not authored here.  A NO-OP mutant (target text absent) is reported,
never counted as killed.

    python3 scripts/m365_mutate.py            # all mutants, one temp cache per mutant
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
TOOL = os.path.join(ROOT, "scripts/m365_pair_slot.py")

# (name, addr, old, new, gate that must go red, claim)
TEXT_MUT = [
    ("MU1", 0x4DA604, "mov    DWORD PTR [edx*4+0x94d5dc],ebx",
     "mov    DWORD PTR [edx*4+0x94d5d8],ebx", "G1a",
     "the census counts 23 instructions that name 0x94d5dc; one moved off the slot is 22"),
    ("MU2", 0x551AF6, "mov    DWORD PTR [edx*4+0x94d5dc],0x0",
     "mov    DWORD PTR [edx*4+0x94d5dc],0x1", "G4b",
     "the ONLY constant ever stored at the slot is 0 (a stored 1 falsifies it)"),
    ("MU3", 0x5049C5, "inc    edx", "xor    edx,edx", "G5c",
     "at paired sites BOTH dwords get the same delta class (here both ++)"),
    ("MU4", 0x4DA6B8, "mov    DWORD PTR [edx*4+0x94d5bc],ebx",
     "mov    DWORD PTR [edx*4+0x94d5d8],ebx", "G5a",
     "5 of the 8 stores carry an 0x94d5bc sibling in the same block"),
    ("MU5", 0x53200C, "sar    edx,0x4", "sar    edx,0x2", "G6a",
     "the round fraction is exactly /50 (magic 0x51eb851f, sar 4), not /12"),
    ("MU6", 0x53201C, "lea    eax,[eax+edx*1+0x1]", "lea    eax,[eax+edx*1+0x0]", "G6b",
     "both deadlines carry the small addend (+1 for 0x94d5dc, +2 for 0x94d5bc)"),
    ("MU7", 0x54A36F, "cmp    ecx,eax", "mov    eax,ecx", "G6c",
     "4 distinct cmp instructions consume the slot (one per direction pair)"),
    ("MU8", 0x4DA5E0, "mov    DWORD PTR [edx*4+0x94d5bc],ebx",
     "mov    DWORD PTR [edx*4+0x94d58c],ebx", "G2b",
     "the five sibling arrays are exactly 0x20 apart with 0x94d5dc last"),
    ("MU9", 0x50609F, "shl    eax,0x6", "shl    eax,0x5", "G3b",
     "the folded sites build the 0x82f stride with a shl 6 first"),
    ("MU10", 0x4DA604, "mov    DWORD PTR [edx*4+0x94d5dc],ebx",
     "mov    DWORD PTR [edx*4+0x94d5dc],0xfaeef378", "R2",
     "no bit-mask constant is ever stored at this slot (that is 0x94d448's shape)"),
    ("MU11", 0x551B01, "mov    DWORD PTR [eax+0x94d5dc],0x0",
     "mov    DWORD PTR [eax+0x94d5dc],0xffffffff", "R3",
     "the slot is only ever zeroed, never stamped -1 (no 'unset' sentinel)"),
    ("MU12", 0x506C88, "mov    DWORD PTR [eax+0x94d5bc],edi",
     "mov    DWORD PTR [eax+0x94d5b8],edi", "R4",
     "0x94d5bc and 0x94d5dc are two arrays 0x20 apart, both written by the same blocks"),
    ("MU13", 0x574423, "mov    ecx,DWORD PTR [eax+0x94d5dc]",
     "mov    ecx,DWORD PTR [eax*4+0x94d5dc]", "G3d",
     "every one of the 23 sites is either folded (0x82f) or a plain record pointer (0 unknown)"),
    ("MU16", 0x574423, "mov    ecx,DWORD PTR [eax+0x94d5dc]",
     "mov    DWORD PTR [eax+0x94d5dc],ecx", "G1b",
     "8 writes / 15 reads: a load turned into a store breaks the split"),
    ("MU17", 0x551B01, "mov    DWORD PTR [eax+0x94d5dc],0x0",
     "mov    DWORD PTR [eax*4+0x94d5dc],0x0", "G1c",
     "4 absolute-indexed + 19 base+disp: moving one store to the absolute form breaks it"),
    ("MU18", 0x551AF6, "mov    DWORD PTR [edx*4+0x94d5dc],0x0",
     "mov    DWORD PTR [edx*4+0x94d5ec],0x0", "G1d",
     "the per-function census (1,2,2,2,2,6,8) depends on where the sites are"),
    ("MU20", 0x5060A2, "add    eax,ebx", "mov    eax,ebx", "G3d",
     "every site is either folded (0x82f) or a plain record pointer (0 unknown)"),
    ("MU24", 0x5049D2, "inc    ecx", "add    ecx,0x2", "G4a",
     "the 8 stores split 2 zero / 2 carry / 3 single-step ++ / 1 scaled-byte delta"),
    ("MU21", 0x506C97, "mov    DWORD PTR [eax+0x94d5dc],esi",
     "mov    DWORD PTR [ecx+0x94d5dc],esi", "G5b",
     "the paired stores use the SAME base register (one pair index), not two"),
    ("MU22", 0x507F8B, "add    ecx,eax", "mov    ecx,eax", "R1",
     "the pair index is not a per-faction scalar: 12 folded sites carry a unit companion"),
]

# (name, [(addr, old, new), ...], gate that must go red, claim) — the displacement appears
# TWICE inside FUN_004da2c0's two store loops, so removing it takes two edits.
MULTI_MUT = [
    ("MU8", [(0x4DA5E0, "mov    DWORD PTR [edx*4+0x94d5bc],ebx",
              "mov    DWORD PTR [edx*4+0x94d58c],ebx"),
             (0x4DA6B8, "mov    DWORD PTR [edx*4+0x94d5bc],ebx",
              "mov    DWORD PTR [edx*4+0x94d58c],ebx")], "G2b",
     "the five per-target slots are exactly 0x20 apart with 0x94d5dc last"),
    ("MU19", [(0x4DA5E0, "mov    DWORD PTR [edx*4+0x94d5bc],ebx",
               "mov    DWORD PTR [edx*4+0x94d594],ebx"),
              (0x4DA6B8, "mov    DWORD PTR [edx*4+0x94d5bc],ebx",
               "mov    DWORD PTR [edx*4+0x94d594],ebx")], "G2c",
     "0x94d5bc is present in the family and sits exactly one slot before 0x94d5dc"),
]

# (name, old source line, new source line, gate that must go red, claim)
SRC_MUT = [
    ("MU14", "f = _add(f, _mul(g, int(m.group(3))))", "f = _add(f, g)", "G3a",
     "the tracer applies the lea scale factor (self-test 4 pins it) — an algorithm mutant"),
    ("MU15", "            return {k: (v // 4 if v % 4 == 0 else v) for k, v in f.items()}",
     "            return dict(f)", "G3b",
     "byte forms (0x20bc) are divided back to dwords (0x82f) before the stride is claimed"),
    ("MU23", '        sc = 4 if re.search(r"\\[[a-z]{2,3}\\*4\\+", INS[n]["arg"]) else 1',
     "        sc = 1", "G3b",
     "the site's OWN addressing scale is part of its form: absolute forms index x4, so they "
     "carry 0x20bc/4 not 0x82f directly"),
]

GATE_RE = re.compile(r"^\s*\[(ok|XX)\]\s+(G\d[a-d]|R\d)\s", re.M)


def gate_state(txt):
    """{gate id: 'ok'|'XX'} from the tool's own printed rows (status, id) -> id-first."""
    return {g: s for s, g in GATE_RE.findall(txt)}


def run(text_path, tool_path):
    env = dict(os.environ, M365_TEXT=text_path)
    p = subprocess.run([sys.executable, "-u", tool_path], capture_output=True,
                       text=True, env=env)
    return p.returncode, p.stdout + p.stderr


def apply_text(src, dst, edits):
    lines = open(src, errors="replace").read().split("\n")
    done = []
    for addr, old, new in edits:
        hit = None
        for i, l in enumerate(lines):
            m = re.match(r"^\s*([0-9a-f]{6,8}):\t", l)
            if m and int(m.group(1), 16) == addr:
                hit = i
                break
        if hit is None or old not in lines[hit]:
            return False, done
        lines[hit] = lines[hit].replace(old, new)
        done.append(addr)
    open(dst, "w").write("\n".join(lines))
    return True, done


def main():
    out, gates_seen = [], set()
    rc, base = run(TEXT, TOOL)
    pg = re.search(r"^(PASS|FAIL) M365: (\d+)/(\d+) gates", base, re.M)
    base_gates = set(GATE_RE.findall(base))
    out.append("M365 mutation harness")
    out.append("baseline: rc=%d %s" % (rc, pg.group(0) if pg else "NO PASS LINE"))
    if not pg or rc != 0:
        out.append("BASELINE NOT GREEN - no mutant can be judged")
        print("\n".join(out))
        return 1
    allg = sorted(g for _, g in base_gates)
    out.append("baseline gates (%d): %s" % (len(allg), " ".join(allg)))

    killed, noop = [], []
    for name, addr, old, new, gate, claim in TEXT_MUT:
        d = tempfile.mkdtemp(prefix="m365mut_")
        tp = os.path.join(d, "text.txt")
        okapply, done = apply_text(TEXT, tp, [(addr, old, new)])
        if not okapply:
            noop.append((name, gate, "text target absent"))
            shutil.rmtree(d, ignore_errors=True)
            continue
        rc2, txt = run(tp, TOOL)
        red = gate_state(txt).get(gate)
        gates_seen.add(gate)
        killed.append((name, gate, red == "XX", claim))
        out.append("  %-5s %-9s red=%-3s %s" % (name, gate, red == "XX", " ".join(claim.split())[:70]))
        shutil.rmtree(d, ignore_errors=True)

    for name, edits, gate, claim in MULTI_MUT:
        d = tempfile.mkdtemp(prefix="m365mul_")
        tp = os.path.join(d, "text.txt")
        okapply, done = apply_text(TEXT, tp, edits)
        if not okapply:
            noop.append((name, gate, "multi target absent after %d edits" % len(done)))
            shutil.rmtree(d, ignore_errors=True)
            continue
        rc2, txt = run(tp, TOOL)
        red = gate_state(txt).get(gate)
        gates_seen.add(gate)
        killed.append((name, gate, red == "XX", claim))
        out.append("  %-5s %-5s red=%-5s rc=%d %s"
                   % (name, gate, red == "XX", rc2, " ".join(claim.split())[:64]))
        shutil.rmtree(d, ignore_errors=True)

    for name, old, new, gate, claim in SRC_MUT:
        src = open(TOOL).read()
        if old not in src:
            noop.append((name, gate, "source target absent"))
            continue
        d = tempfile.mkdtemp(prefix="m365src_")
        tp = os.path.join(os.path.dirname(TOOL), ".m365_src_%s.py" % name)
        open(tp, "w").write(src.replace(old, new, 1))
        rc2, txt = run(TEXT, tp)
        os.unlink(tp)
        red = gate_state(txt).get(gate)
        gates_seen.add(gate)
        killed.append((name, gate, red == "XX", claim))
        out.append("  %-5s %-9s red=%-3s %s" % (name, gate, red == "XX", " ".join(claim.split())[:70]))
        shutil.rmtree(d, ignore_errors=True)

    out.append("")
    nk = sum(1 for _, _, ok, _ in killed if ok)
    out.append("KILLED %d/%d   NO-OP %d" % (nk, len(killed), len(noop)))
    for n, g, why in noop:
        out.append("  noop %s (%s): %s" % (n, g, why))
    missing = [g for g in allg if g not in gates_seen]
    out.append("gate coverage: %d/%d gates have a mutant; unnamed: %s"
               % (len(allg) - len(missing), len(allg), " ".join(missing) or "-"))
    ok = nk == len(killed) and not noop and not missing
    out.append("PASS M365-MUT: %d/%d killed, NO-OP %d, coverage %d/%d"
               % (nk, len(killed), len(noop), len(allg) - len(missing), len(allg)) if ok
               else "FAIL M365-MUT: %d/%d killed, NO-OP %d, coverage %d/%d"
               % (nk, len(killed), len(noop), len(allg) - len(missing), len(allg)))
    print("\n".join(out))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
