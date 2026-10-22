#!/usr/bin/env python3
"""Offline call graph over the saved capstone dump of terran.exe .text.

Source: ~/reverse/smac/.text_insns.json  = [[addr, size, mnem, ops], ...]
(runtime base 0x400000 == Ghidra VA, so addresses are directly comparable to FUN_xxx).

Builds:
  CALLS  : target_int -> sorted set of caller-site addrs (E8 rel32 + FF /2 indirect)
  RETS   : func_start -> list of call sites inside it (approximate: derived from
           basic-block starts / epilogue reachability is overkill; we use the
           Ghidra function-boundary list from .func_bounds.json if present)

Usage:
  python3 callgraph.py callers 0x520e70 [0x52bce0 ...]
  python3 callgraph.py callees 0x520e70
  python3 callgraph.py who      0x520e70   # callers' containing funcs
"""
import json, os, sys, bisect

BASE = os.path.dirname(os.path.abspath(__file__))
INSN = os.path.join(BASE, '.text_insns.json')

_cache = {}

STARTS = os.path.join(BASE, '.func_starts.json')   # authoritative Ghidra function
NAMES = os.path.join(BASE, '.func_names.json')     # entrypoints (see build_starts.py)

def load():
    if 'insns' in _cache:
        return _cache['insns'], _cache['starts']
    with open(INSN) as f:
        insns = json.load(f)
    _cache['insns'] = insns
    _cache['addrs'] = [i[0] for i in insns]
    if os.path.exists(STARTS):
        starts = json.load(open(STARTS))          # exact (Ghidra function manager)
    else:                                         # fallback heuristic
        starts = sorted({a for a, s, m, o in insns
                         if m == 'push' and o.strip().lower() == 'ebp'})
    _cache['starts'] = starts
    if os.path.exists(NAMES):
        _cache['names'] = json.load(open(NAMES))
    return insns, starts


def fname(a):
    if a is None:
        return '?'
    return _cache.get('names', {}).get(hex(a), f'FUN_{a:06x}')

def containing_func(a):
    insns, starts = load()
    i = bisect.bisect_right(starts, a) - 1
    return starts[i] if i >= 0 else None

def build_calls():
    if 'CALLS' in _cache:
        return _cache['CALLS']
    insns, _ = load()
    calls = {}
    for idx, (a, sz, mn, ops) in enumerate(insns):
        tgt = None
        if mn == 'call':
            o = ops.strip()
            if o.startswith('0x'):
                try:
                    tgt = int(o.split()[0], 16)
                except ValueError:
                    tgt = None
            if tgt is None and idx + 1 < len(insns):
                pass
        elif mn == 'jmp' and ops.strip().lower().startswith('*'):
            pass
        if tgt is not None:
            calls.setdefault(tgt, set()).add(a)
    _cache['CALLS'] = calls
    return calls

def callers(t):
    calls = build_calls()
    return sorted(calls.get(t, ()))

def callees(f):
    """Direct call targets from sites whose containing function == f."""
    insns, _ = load()
    out = []
    for a, sz, mn, ops in insns:
        if mn != 'call':
            continue
        o = ops.strip()
        if not o.startswith('0x'):
            continue
        if containing_func(a) == f:
            out.append((a, int(o.split()[0], 16)))
    return out

def callers_of_func(f):
    """Sites outside f that call f."""
    out = []
    for site in callers(f):
        cf = containing_func(site)
        if cf != f:
            out.append((site, cf))
    return out

if __name__ == '__main__':
    mode = sys.argv[1]
    for spec in sys.argv[2:]:
        a = int(spec, 0)
        if mode == 'callers':
            cs = callers_of_func(a)
            print(f'== callers of {a:#x} ({fname(a)}) — {len(cs)} sites')
            from collections import Counter
            c = Counter(cf for _, cf in cs)
            for cf, n in c.most_common(40):
                print(f'  {fname(cf)}  ({cf:#07x})  x{n}')
        elif mode == 'callees':
            cs = callees(a)
            print(f'== callees of {a:#x} ({fname(a)}) — {len(cs)} calls')
            from collections import Counter
            c = Counter(t for _, t in cs)
            for t, n in c.most_common(60):
                print(f'  -> {fname(t)} ({t:#07x})  x{n}')
        elif mode == 'up':
            depth = int(os.environ.get('DEPTH', '4'))
            seen = {a: 0}
            frontier = [a]
            lvl = 0
            while frontier and lvl < depth:
                lvl += 1
                nxt = []
                for f in frontier:
                    ups = sorted({cf for _, cf in callers_of_func(f)})
                    print(f'  L{lvl}: {f:#07x} {fname(f)} <- '
                          + ', '.join(f'{fname(u)}({u:#07x})' for u in ups[:25])
                          + (f' (+{len(ups)-25})' if len(ups) > 25 else ''))
                    for u in ups:
                        if u not in seen:
                            seen[u] = lvl
                            nxt.append(u)
                frontier = nxt
        else:
            print(hex(a), containing_func(a))
