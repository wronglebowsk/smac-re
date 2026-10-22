#!/usr/bin/env python3
"""Dump REA artifacts for the SMAC netcode investigation.
usage: python3 dump_fn.py <address-or-name> [more...]   -> <name>.pseudocode.txt (+ prints heads)
"""
import sys, json, re
sys.path.insert(0, '/home/n100/reverse/smac')
import rea_fifo as F

OUTDIR = '/home/n100/reverse/smac'

def dump(target):
    e = F.tool("procedure_pseudo_code", {"procedure": target}, timeout=600)
    rr = e.get("raw_result")
    pc = None
    name = None
    if isinstance(rr, dict):
        pc = rr.get("value")
    elif isinstance(rr, str):
        pc = rr
    if isinstance(pc, str):
        name = None
        for line in pc.split("\n")[:6]:
            line = line.strip()
            if not line or line.startswith("/*") or line.startswith("*"):
                continue
            m = re.search(r'([A-Za-z_][A-Za-z0-9_]*)\s*\(', line)
            name = m.group(1) if m else None
            break
    if not pc:
        print(target, "NO PSEUDOCODE:", json.dumps(e)[:300])
        return None
    fn = f"{OUTDIR}/{name or ('FN_'+str(target))}.pseudocode.txt"
    open(fn, 'w').write(pc)
    lines = pc.split("\n")
    print(f"{target} -> {name}: {len(lines)} lines -> {fn}")
    return fn

if __name__ == "__main__":
    for t in sys.argv[1:]:
        dump(t)
