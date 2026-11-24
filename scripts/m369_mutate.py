#!/usr/bin/env python3
"""M369 mutation harness - every VERIFIED row of scripts/m369_commlink.py names a mutant here.

A mutant is KILLED when its named gate turns red in a REAL run of the tool.  Four kinds:

  TEXT   rewrites ONE instruction line of the objdump cache (the tool reads it via M369_TEXT):
         the DISASSEMBLY is mutated and the tool must notice.
  LAB    rewrites ONE line of programs/labels.txt (M369_LABELS).
  SRC    rewrites ONE line of a ghidra shard (M369_SHARDS) - the export is the input.
  ALG    rewrites ONE line of the tool itself (a temp copy): the instrument's algorithm.

Gate coverage is MEASURED from the tool's own PASS/FAIL rows, not authored here.  A NO-OP
mutant (its target text absent) is reported and never counted as killed.

    python3 scripts/m369_mutate.py
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
LABELS = os.path.join(ROOT, "programs/labels.txt")
SHARDS = os.path.join(ROOT, "ghidra_out")
TOOL = os.path.join(ROOT, "scripts/m369_commlink.py")
ADDR = re.compile(r"^(\s*)([0-9a-f]{6,8}):")

# (name, addr, old, new, gate, claim)
TEXT_MUT = [
    ("MU1", 0x442D40, "jne 0x442d7d", "jne 0x442cf5", "G4a",
     "the mask hits jump FORWARD to the accept label; flipped, the guard would disable the option"),
    ("MU2", 0x442D42, "push 0x8", "push 0x9", "G3a",
     "the second ask is mask 8 (the reverse direction)"),
    ("MU3", 0x442D26, "push 0x8", "push 0x10", "G3a",
     "the first ask is mask 8, not the war bit"),
    ("MU4", 0x442D7D, "mov ecx,DWORD PTR [ebp-0x28]", "mov DWORD PTR ds:0x94d448,ecx", "G3b",
     "the block stores nothing into the relations dword"),
    ("MU5", 0x442D78, "jmp 0x442cf5", "jmp 0x442cf6", "G4b",
     "the both-zero fall-through goes to 0x442cf5 (next candidate)"),
    ("MU6", 0x442C1F, "push 0x8", "push 0x9", "G4c",
     "the non-war option (case 7) pairs the same two mask-8 reads"),
    ("MU7", 0x551ABF, "test bl,0x10", "test bl,0x8", "G5a",
     "the 0x80000108 OR is gated by test bl,0x10"),
    ("MU8", 0x551B11, "or ebx,0x80000108", "or ebx,0x80000100", "G5a",
     "the war write sets bit 8 through 0x80000108"),
    ("MU9", 0x551AA8, "mov edx,DWORD PTR [edx*4+0x94d448]", "or ebx,0x80000108", "G5b",
     "the 0x7 (peace) branch never sets 0x8"),
    ("MU10", 0x551A35, "test bl,0x7", "test bl,0x8", "G5c",
     "8 is disjoint from the clear-branch masks (7/1/0x10/0x17)"),
    ("MU11", 0x551BEA, "mov eax,esi", "mov eax,edi", "G6a",
     "the second OR reloads the index from the other register (the reverse direction)"),
    ("MU12", 0x551C09, "or edx,ebx", "or edx,ebp", "G6a",
     "the setter ORs twice, one per direction"),
    ("MU13", 0x507ABC, "push 0x10", "push 0x8", "G10a",
     "the declare path's setter call carries mask 0x10"),
    ("MU14", 0x507C6D, "push 0x10", "push 0x11", "G10a",
     "both exits of the declare path use mask 0x10"),
    ("MU33", 0x551A88, "and edx,0xffee7faf", "and edx,0xffee7fae", "G5b",
     "the peace branch's clear mask is exactly 0x10|0x40|0x8000|0x10000|0x100000"),
    ("MU34", 0x551B17, "and edx,0xfaeef378", "and edx,0xfaeef370", "G5c",
     "no and-mask in the setter clears bit 8 (0xfaeef378 keeps it)"),
    ("MU35", 0x56F5A9, "push 0x8", "push 0x18", "G8a",
     "the pod's pinned site carries the EXACT mask 8, not merely some bit-8 mask"),
    ("MU36", 0x442D4B, "mov eax,DWORD PTR [edx+0xa28]", "mov eax,DWORD PTR [edx+0xa24]", "G3a",
     "the two mask-8 asks use the two different faction operands (one per direction)"),
    ("MU37", 0x442D83, "mov DWORD PTR [ebp-0x28],ecx", "or DWORD PTR ds:0x94d448,ecx", "G3b",
     "the store classifier sees a relations write if one is planted"),
    ("MU38", 0x56F56D, "jne 0x56f692", "jne 0x56f5a9", "G9a",
     "the pod's guard jne jumps PAST the setter call (so the set happens only where the bit was clear)"),
]

# (name, 0-based labels.txt line, replacement, gate, claim)
LAB_MUT = [
    ("MU15", 885, b"CommlinkX", "G2a", "id 0x8 -> element 875 -> 'Commlink'"),
    ("MU16", 656, b"VendettaX", "G2b", "id 0x10 -> element 646 -> 'Vendetta' (a different noun)"),
    ("MU17", 655, b"PactX", "G2a", "id 0x1 -> element 645 -> 'Pact'"),
    ("MU18", 884, b"Commlink", "R2", "the high-dword id 0x80000008 reads 'Fight to the death', not 0x8's text"),
    ("MU19", 904, b"Fix current status as permanentX", "G2a", "id 0x80002000 -> element 894 -> 'Fix current status as permanent'"),
]

# (name, shard file, old, new, gate, claim)
SRC_MUT = [
    ("MU20", "shard_012.c", "uVar5 = 8;", "uVar5 = 0x18;", "G1a", "the first builder row's id is 8"),
    ("MU21", "shard_012.c", "DAT_00997b20 + 0xdac", "DAT_00997b20 + 0xdb0", "G2a",
     "id 8 reads element 875 (0xdac/4)"),
    ("MU22", "shard_012.c", "FUN_00551a20(iVar2,iVar1,8);", "FUN_00551a20(iVar2,iVar1,4);", "G7a",
     "the checkbox commit writes bit 8"),
    ("MU23", "shard_014.c", "FUN_00551a20(uVar13,uVar9,8);", "FUN_00551a20(uVar13,uVar9,4);", "G7a",
     "the pod first-contact write is bit 8"),
    ("MU24", "shard_014.c", "FUN_00551a20(uVar13,uVar9,8);", "FUN_00551a20(uVar13,uVar10,8);", "G9a",
     "the pod sets the bit through the (uVar13, uVar9) pair it just tested"),
    ("MU25", "shard_014.c", "FUN_00551a20(param_1,iVar1,0x18);", "FUN_00551a20(param_1,iVar1,0x10);", "G7a",
     "the AI war path writes 0x18 (8 and 0x10 together)"),
    ("MU26", "shard_001.c",
     "for (local_c = 1; local_c < 8; local_c = local_c + 1) {\n    for (local_8 = 1; local_8 < local_c;",
     "for (local_c = 1; local_c < 7; local_c = local_c + 1) {\n    for (local_8 = 1; local_8 < local_c;",
     "G9b", "the council loop sweeps all 7 rivals"),
    ("MU27", "shard_001.c", "FUN_00551a20(local_c,local_8,8);", "FUN_00551a20(local_c,local_8,0x10);", "G7b",
     "the council sets the CONTACT bit 8, not the war bit"),
    ("MU39", "shard_001.c", "FUN_00551a20(local_c,local_8,8);\n    }\n  }\n", "\n  }\n  }\n", "G9b",
     "the council's loop body actually calls the setter (a removed call reddens the source half of G9b)"),
    ("MU28", "shard_014.c", "s_GOODYPOD_00691820", "s_GOODPOD_00691820", "G9a",
     "the first-contact writer is the goody-pod handler"),
]

# (name, old, new, gate, claim)
ALG_MUT = [
    ("MU29", "ln = 11 + elem", "ln = 10 + elem", "G2a",
     "the label line is 11+elem (line 10 is the count) - the tracer itself is mutated"),
    ("MU30", "s[3] & 8]", "s[3] & 4]", "G7a",
     "the census filter selects bit 8 out of the literal mask"),
    ("MU31", "ACCEPT_PC = 0x442D7D", "ACCEPT_PC = 0x442D40", "G4a",
     "the accept label is 0x442d7d"),
    ("MU32", "(0x56F5AD, 0x8)", "(0x56F5AE, 0x8)", "G8a",
     "the pod's byte site is 0x56f5ad"),
    ("MU0", "NO-SUCH-TEXT-EVER", "x", "", "the NO-OP control: target absent, nothing may change"),
]


def run_tool(env, tool=TOOL):
    p = subprocess.run([sys.executable, "-u", tool], capture_output=True, text=True, env=env)
    fails = set(re.findall(r"FAIL M369: .*failed \[([^\]]*)\]", p.stdout))
    red = set()
    for chunk in fails:
        red |= {x.strip().strip("'") for x in chunk.split(",")}
    ok = p.returncode in (0, 1) and ("PASS M369" in p.stdout or "FAIL M369" in p.stdout)
    return ok, red, p.stdout, p.stderr


def mutant_text(addr, old, new, work):
    src = open(TEXT, "r", errors="replace").read().split("\n")
    pat = re.compile(r"\s+".join(re.escape(t) for t in old.split()))
    hit = 0
    for i, line in enumerate(src):
        m = ADDR.match(line)
        if m and int(m.group(2), 16) == addr and pat.search(line):
            src[i] = pat.sub(new, line, count=1)
            hit += 1
            break
    if not hit:
        return None
    p = os.path.join(work, "text.txt")
    open(p, "w").write("\n".join(src))
    return p


def main():
    base_env = dict(os.environ)
    work = tempfile.mkdtemp(prefix="m369_mut_")
    results = []

    # control: the unmutated tool must be green
    ok, red, out, err = run_tool(base_env)
    control_green = ok and not red and "PASS M369" in out
    print("CONTROL  unbiased run: %s (%s)" % ("PASS" if control_green else "FAIL",
                                              re.search(r"PASS M369: [^\n]*", out).group(0)
                                              if "PASS M369" in out else (err.strip()[-200:] or "?")))
    if not control_green:
        print("refusing to score mutants on a red control")
        return 1

    shard_orig = {}

    for name, addr, old, new, gate, claim in TEXT_MUT:
        p = mutant_text(addr, old, new, work)
        if p is None:
            results.append((name, gate, "NO-OP", claim))
            continue
        env = dict(base_env, M369_TEXT=p)
        ok, red, out, err = run_tool(env)
        results.append((name, gate, "KILLED" if gate in red else ("SURVIVED" if ok else "CRASH"), claim))
        os.unlink(p)

    lab_src = open(LABELS, "rb").read().split(b"\n")

    def mutant_labels(idx, repl, work):
        lines = list(lab_src)
        if idx >= len(lines):
            return None
        lines[idx] = repl
        p = os.path.join(work, "labels.txt")
        open(p, "wb").write(b"\n".join(lines))
        return p

    for name, idx, repl, gate, claim in LAB_MUT:
        p = mutant_labels(idx, repl, work)
        if p is None:
            results.append((name, gate, "NO-OP", claim))
            continue
        env = dict(base_env, M369_LABELS=p)
        ok, red, out, err = run_tool(env)
        results.append((name, gate, "KILLED" if gate in red else ("SURVIVED" if ok else "CRASH"), claim))
        os.unlink(p)

    shard_dir = os.path.join(work, "shards")
    shutil.copytree(SHARDS, shard_dir)
    for name, f, old, new, gate, claim in SRC_MUT:
        p = os.path.join(shard_dir, f)
        if f not in shard_orig:
            shard_orig[f] = open(p, "r", errors="replace").read()
        body = shard_orig[f]
        if old not in body:
            results.append((name, gate, "NO-OP", claim))
            continue
        open(p, "w").write(body.replace(old, new, 1))
        env = dict(base_env, M369_SHARDS=os.path.join(shard_dir, "*.c"))
        ok, red, out, err = run_tool(env)
        results.append((name, gate, "KILLED" if gate in red else ("SURVIVED" if ok else "CRASH"), claim))
        open(p, "w").write(shard_orig[f])

    tool_src = open(TOOL, "r").read()
    alg_path = os.path.join(ROOT, "scripts", "_m369_alg_tmp.py")
    for name, old, new, gate, claim in ALG_MUT:
        if old not in tool_src:
            results.append((name, gate, "NO-OP", claim))
            continue
        open(alg_path, "w").write(tool_src.replace(old, new, 1))
        ok, red, out, err = run_tool(base_env, alg_path)
        results.append((name, gate, "KILLED" if gate in red else ("SURVIVED" if ok else "CRASH"), claim))
    if os.path.exists(alg_path):
        os.unlink(alg_path)

    say = []
    say.append("M369 mutation harness - %d mutants" % (len(results) - 1))
    say.append("  %-6s %-6s %-9s %s" % ("mutant", "gate", "verdict", "claim"))
    killed = 0
    for name, gate, verdict, claim in results:
        if verdict == "KILLED":
            killed += 1
        say.append("  %-6s %-6s %-9s %s" % (name, gate, verdict, claim))
    scored = [r for r in results if r[2] != "NO-OP"]
    say.append("")
    say.append("killed %d/%d scored (1 NO-OP control reported, never counted)" % (killed, len(scored)))
    text = "\n".join(say)
    print(text)
    if killed == len(scored) and control_green:
        print("\nPASS M369-MUT: %d/%d" % (killed, len(scored)))
        return 0
    print("\nFAIL M369-MUT: %d/%d" % (killed, len(scored)))
    return 1


if __name__ == "__main__":
    sys.exit(main())
