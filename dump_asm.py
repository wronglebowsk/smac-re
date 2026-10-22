#!/usr/bin/env python3
"""Dump REA assembly for functions: python3 dump_asm.py <addr> [more...] -> <name>.asm.txt"""
import sys, json, re
sys.path.insert(0, '/home/n100/reverse/smac')
import rea_fifo as F

OUTDIR = '/home/n100/reverse/smac'

def name_of(target):
    e = F.tool("procedure_info", {"procedure": target}, timeout=120)
    rr = e.get("raw_result") or {}
    v = rr.get("value") if isinstance(rr, dict) else None
    if isinstance(v, dict):
        p = v.get("procedure") or v
        return p.get("name")
    return None

def dump(target):
    e = F.tool("procedure_assembly", {"procedure": target}, timeout=600)
    rr = e.get("raw_result")
    val = rr.get("value") if isinstance(rr, dict) else rr
    lines = []
    if isinstance(val, dict):
        ins = val.get("instructions") or val.get("assembly") or []
        for i in ins:
            if isinstance(i, dict):
                lines.append(f'{i.get("address")}  {i.get("mnemonic")} {i.get("operands","")}'.strip())
            else:
                lines.append(str(i))
    elif isinstance(val, list):
        for i in val:
            if isinstance(i, dict):
                lines.append(f'{i.get("address")}  {i.get("mnemonic")} {i.get("operands","")}'.strip())
            else:
                lines.append(str(i))
    elif isinstance(val, str):
        lines = val.split("\n")
    if not lines:
        print(target, "NO ASSEMBLY:", json.dumps(e)[:250]); return
    nm = name_of(target) or target
    fn = f"{OUTDIR}/{nm}.asm.txt"
    open(fn, 'w').write("\n".join(lines))
    print(f"{target} -> {nm}: {len(lines)} instr -> {fn}")

if __name__ == "__main__":
    for t in sys.argv[1:]:
        dump(t)
