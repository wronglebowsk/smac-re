#!/usr/bin/env python3
"""Linear-disassemble terran.exe .text with capstone, cache it, and report
call sites (with preceding push arguments) for target functions.
Run with the rea-pwntools python (has capstone):
  /home/n100/.hermes/venvs/rea-pwntools/bin/python xref_scan.py <hex-target> [more...]
"""
import json, os, struct, sys, collections
sys.path.insert(0, '/home/n100/reverse/smac')
import exe_strings as S
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

CACHE = '/home/n100/reverse/smac/.text_insns.json'
TEXT_VA = 0x401000
TEXT_LEN = 2_552_820 - 0x1000

def insns():
    if os.path.exists(CACHE):
        return json.load(open(CACHE))
    exe = open('/home/n100/reverse/smac/terran.exe', 'rb').read()
    off = S.va2off(TEXT_VA)
    code = exe[off:off + TEXT_LEN]
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = False
    out = []
    for i in md.disasm(code, TEXT_VA):
        out.append((i.address, i.size, i.mnemonic, i.op_str))
    json.dump(out, open(CACHE, 'w'))
    return out

def main(targets):
    L = insns()
    idx = {a: k for k, (a, sz, m, o) in enumerate(L)}
    calls = collections.defaultdict(list)   # target -> [(site, [mnemonics before])]
    callers = collections.defaultdict(list)
    for k, (a, sz, m, o) in enumerate(L):
        if m == 'call' and o.startswith('0x'):
            t = int(o, 16)
            calls[t].append(a)
    for t in targets:
        sites = calls.get(t, [])
        print(f"== calls to 0x{t:x}: {len(sites)}")
        groups = collections.defaultdict(list)
        for site in sites:
            k = idx.get(site)
            if k is None:
                groups['<unmapped>'].append(site); continue
            args = []
            j = k - 1
            for _ in range(8):
                if j < 0: break
                aa, ss, mm, oo = L[j]
                if mm == 'push':
                    args.append(oo if oo else '?')
                    j -= 1
                elif mm in ('nop',):
                    j -= 1
                else:
                    break
            args.reverse()
            groups[tuple(args[:4])].append(site)
        for g, ssites in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            print(f"   args {g}: {len(ssites)}  {[hex(x) for x in ssites[:6]]}")
    return calls

if __name__ == '__main__':
    ts = [int(x, 16) for x in sys.argv[1:]]
    calls = main(ts)
    json.dump({str(k): [hex(x) for x in v] for k, v in calls.items()},
              open('/home/n100/reverse/smac/.callmap.json', 'w'))
