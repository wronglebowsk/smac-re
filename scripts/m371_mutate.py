#!/usr/bin/env python3
"""M371 mutation harness - every VERIFIED row of scripts/m371_war_contact.py names a mutant.

A mutant is KILLED when its named gate turns red in a REAL run of the tool.

  TEXT   rewrites ONE instruction line of the objdump cache (M371_TEXT): the
         DISASSEMBLY is the input and the tool must notice.
  LAB    rewrites ONE line of programs/labels.txt (M371_LABELS).
  ALG    rewrites ONE line of the tool (a temp copy): the instrument itself.

A NO-OP mutant (target text absent) is reported and never counted.

    python3 scripts/m371_mutate.py
"""
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
LABELS = os.path.join(ROOT, "programs/labels.txt")
TOOL = os.path.join(ROOT, "scripts/m371_war_contact.py")
ADDR = re.compile(r"^(\s*)([0-9a-f]{6,8}):")

# (name, addr, old, new, gate, claim)
TEXT_MUT = [
    ("MU1", 0x551ABF, "test bl,0x10", "test bl,0x8", "G2a",
     "the 0x80000108 OR lives inside the test-bl-0x10 (war) branch"),
    ("MU2", 0x551B11, "or ebx,0x80000108", "or ebx,0x80000100", "G2a",
     "the war branch sets bit 8 through 0x80000108"),
    ("MU3", 0x551A88, "and edx,0xffee7faf", "and edx,0xffee7fae", "G2c",
     "the peace clear mask keeps bit 8"),
    ("MU4", 0x551B17, "and edx,0xfaeef378", "and edx,0xfaeef370", "G2c",
     "the war clear mask keeps bit 8 (it clears pact/treaty/truce)"),
    ("MU5", 0x554E84, "push 0x18", "push 0x10", "G1a",
     "the atrocity host writes mask 0x18 (war + contact)"),
    ("MU6", 0x50764C, "push 0x80000018", "push 0x80000010", "G1a",
     "the aid host writes mask 0x80000018"),
    ("MU7", 0x554406, "push 0x88000008", "push 0x88000018", "G1a",
     "FUN_00554350's vendetta-pending write is 0x88000008 (no war bit)"),
    ("MU8", 0x555667, "push 0x88000008", "push 0x88000018", "G1a",
     "FUN_005551e0's pending-vendetta writes carry no war bit"),
    ("MU9", 0x507ABC, "push 0x10", "push 0x18", "G3b",
     "one declare-path exit requests war ALONE (mask 0x10)"),
    ("MU10", 0x507C6D, "push 0x10", "push 0x8", "G3b",
     "the second declare-path exit is also a war-alone request"),
    ("MU11", 0x507D1A, "push 0x8010", "push 0x8018", "G3b",
     "FUN_00507ce0 requests war (0x8010) without contact"),
    ("MU12", 0x523F38, "push 0x50", "push 0x58", "G3b",
     "mask 0x50 is a war-alone request (the 16th)"),
    ("MU13", 0x56F5A9, "push 0x8", "push 0x18", "G4a",
     "the goody pod writes contact alone (exact mask 8)"),
    ("MU14", 0x429993, "push 0x8", "push 0x18", "G4a",
     "the council sweep writes contact alone"),
    ("MU15", 0x5A7C06, "push 0x8", "push 0x18", "G4a",
     "the new-game host writes contact alone"),
    ("MU16", 0x555491, "and eax,0x40018", "and eax,0x40010", "G4b",
     "the AI war gate masks 0x40018 and requires == 8 (contact, no war)"),
    ("MU17", 0x555502, "and edx,0x18", "and edx,0x10", "G4b",
     "the third-faction test masks 0x18 and compares to 8"),
    ("MU18", 0x554E6B, "test al,0x10", "test al,0x8", "G4c",
     "the atrocity host tests the WAR bit 0x10 before writing 0x18"),
]

# (name, 0-based labels.txt line, replacement, gate, claim)
LAB_MUT = [
    ("MU19", 885, b"CommlinkX", "G5a", "id 0x8 -> element 875 -> line 886 'Commlink'"),
    ("MU20", 656, b"VendettaX", "G5a", "id 0x10 -> element 646 -> line 657 'Vendetta'"),
]

# (name, old, new, gate, claim)
ALG_MUT = [
    ("MU21", "WINDOW = 14", "WINDOW = 3", "G1a",
     "the argument-push lookback window is 14 instructions (0x554426 proves it)"),
    ("MU22", "ln = 11 + off // 4", "ln = 10 + off // 4", "G5a",
     "the label line is 11+elem (line 10 is the count) - tracer mutated"),
    ("MU23", "if m is not None and (m & 0x18)", "if m is not None and (m & 0x10)", "G1a",
     "the host-call classifier selects bit 8 or war 0x10"),
    ("MU24", "if (mask_at(ins, idx, a)[0] or 0) & 0x10", "if (mask_at(ins, idx, a)[0] or 0) & 0x40", "G3b",
     "the war-alone classifier selects 0x10, not 0x18"),
    ("MU25", "return [i for i in range(32) if m >> i & 1]", "return [i for i in range(32) if m >> i & 1][:2]", "G2b",
     "the bit decomposer enumerates the whole mask (3 bits for 0x80000108)"),
    ("MU0", "NO-SUCH-TEXT-EVER", "x", "", "the NO-OP control: target absent, nothing may change"),
]


def run_tool(env, tool=TOOL):
    p = subprocess.run([sys.executable, "-u", tool], capture_output=True, text=True, env=env)
    fails = set(re.findall(r"FAIL M371: .*failed \[([^\]]*)\]", p.stdout))
    red = set()
    for chunk in fails:
        red |= {x.strip().strip("'") for x in chunk.split(",")}
    ok = p.returncode in (0, 1) and ("PASS M371" in p.stdout or "FAIL M371" in p.stdout)
    return ok, red, p.stdout, p.stderr


def mutant_text(addr, old, new, work):
    src = open(TEXT, "r", errors="replace").read().split("\n")
    pat = re.compile(r"\s+".join(re.escape(t) for t in old.split()))
    for i, line in enumerate(src):
        m = ADDR.match(line)
        if m and int(m.group(2), 16) == addr and pat.search(line):
            src[i] = pat.sub(new, line, count=1)
            p = os.path.join(work, "text.txt")
            open(p, "w").write("\n".join(src))
            return p
    return None


def main():
    base_env = dict(os.environ)
    work = tempfile.mkdtemp(prefix="m371_mut_")
    results = []

    ok, red, out, err = run_tool(base_env)
    control_green = ok and not red and "PASS M371" in out
    pm = re.search(r"PASS M371: [^\n]*", out)
    line = pm.group(0) if pm else (err.strip()[-200:] or "?")
    print("CONTROL  unbiased run: %s (%s)" % ("PASS" if control_green else "FAIL", line))
    if not control_green:
        print("refusing to score mutants on a red control")
        return 1

    for name, addr, old, new, gate, claim in TEXT_MUT:
        p = mutant_text(addr, old, new, work)
        if p is None:
            results.append((name, gate, "NO-OP", claim))
            continue
        ok, red, out, err = run_tool(dict(base_env, M371_TEXT=p))
        results.append((name, gate, "KILLED" if gate in red else ("SURVIVED" if ok else "CRASH"), claim))
        os.unlink(p)

    lab_src = open(LABELS, "rb").read().split(b"\n")
    for name, idx, repl, gate, claim in LAB_MUT:
        if idx >= len(lab_src):
            results.append((name, gate, "NO-OP", claim))
            continue
        lines = list(lab_src)
        lines[idx] = repl
        p = os.path.join(work, "labels.txt")
        open(p, "wb").write(b"\n".join(lines))
        ok, red, out, err = run_tool(dict(base_env, M371_LABELS=p))
        results.append((name, gate, "KILLED" if gate in red else ("SURVIVED" if ok else "CRASH"), claim))
        os.unlink(p)

    tool_src = open(TOOL, "r").read()
    alg_path = os.path.join(ROOT, "scripts", "_m371_alg_tmp.py")
    for name, old, new, gate, claim in ALG_MUT:
        if old not in tool_src:
            results.append((name, gate, "NO-OP", claim))
            continue
        open(alg_path, "w").write(tool_src.replace(old, new, 1))
        ok, red, out, err = run_tool(base_env, alg_path)
        results.append((name, gate, "KILLED" if gate in red else ("SURVIVED" if ok else "CRASH"), claim))
    if os.path.exists(alg_path):
        os.unlink(alg_path)

    say = ["M371 mutation harness - %d mutants" % (len(results) - 1),
           "  %-6s %-6s %-9s %s" % ("mutant", "gate", "verdict", "claim")]
    killed = 0
    for name, gate, verdict, claim in results:
        if verdict == "KILLED":
            killed += 1
        say.append("  %-6s %-6s %-9s %s" % (name, gate, verdict, claim))
    scored = [r for r in results if r[2] != "NO-OP"]
    say.append("")
    say.append("killed %d/%d scored (1 NO-OP control reported, never counted)" % (killed, len(scored)))
    print("\n".join(say))
    if killed == len(scored) and control_green:
        print("\nPASS M371-MUT: %d/%d" % (killed, len(scored)))
        return 0
    print("\nFAIL M371-MUT: %d/%d" % (killed, len(scored)))
    return 1


if __name__ == "__main__":
    sys.exit(main())
