#!/usr/bin/env python3
"""Parse m53p_recon_a output incl. mask_in/processed; print stats for one or two files."""
import re, sys, collections

def parse(path):
    data = {}; cur = None
    for ln in open(path):
        m = re.match(r'idx (\d+) fac (\d+) pop (\d+) flag (\d+) budget (\d+)->(\d+) mask_in (\S+) processed (\S+)', ln)
        if m:
            cur = int(m.group(1))
            data[cur] = dict(fac=int(m.group(2)), pop=int(m.group(3)), flag=int(m.group(4)),
                             b0=int(m.group(5)), b1=int(m.group(6)),
                             mask_in=m.group(7), processed=m.group(8))
            continue
        m = re.match(r'\s+(bc|c0|c4|c8) model=(-?\d+)\s+obs=(-?\d+)\s+delta=(-?\d+)', ln)
        if m and cur is not None:
            data[cur][m.group(1)] = int(m.group(4))
    return data

def stats(path, label):
    d = parse(path)
    cnt = collections.Counter(); bad = []
    for i in sorted(d):
        r = d[i]
        nf = [f for f in ('bc', 'c0', 'c4', 'c8') if r[f] != 0]
        for f in nf: cnt[f] += 1
        if nf: bad.append((i, r['fac'], nf))
        r['selfcons'] = (r['mask_in'] == r['processed'])
    sc = [i for i in sorted(d) if d[i]['selfcons']]
    sc_bad = [(i, d[i]['fac'], [(f, d[i][f]) for f in ('bc','c0','c4','c8') if d[i][f] != 0]) for i in sc if any(d[i][f] for f in ('bc','c0','c4','c8'))]
    print(f"== {label}: rows {len(d)} full-match {len(d)-len(bad)} mismatch bc {cnt['bc']} c0 {cnt['c0']} c4 {cnt['c4']} c8 {cnt['c8']}")
    print(f"   self-consistent rows ({len(sc)}): {sc}")
    print(f"   self-consistent AND mismatching ({len(sc_bad)}):")
    for x in sc_bad: print("   ", x)
    for probe in (61, 70):
        if probe in d:
            r = d[probe]
            print(f"   probe idx {probe}: selfcons={r['selfcons']} mask_in={r['mask_in']} processed={r['processed']} deltas bc={r['bc']} c0={r['c0']} c4={r['c4']} c8={r['c8']}")
    return d

if __name__ == '__main__':
    ds = {}
    for p, l in ((sys.argv[1], sys.argv[2]), (sys.argv[3], sys.argv[4])) if len(sys.argv) > 4 else ((sys.argv[1], sys.argv[2]),):
        ds[l] = stats(p, l)
    if len(ds) == 2:
        a, b = list(ds.values())
        keys = list(ds.keys())
        print("== delta A->B ==")
        for i in sorted(set(a) | set(b)):
            ra, rb = a.get(i), b.get(i)
            if ra is None or rb is None:
                print(f"   idx {i}: only in {keys[0] if rb is None else keys[1]}")
                continue
            da = {f: ra[f] for f in ('bc','c0','c4','c8')}
            db = {f: rb[f] for f in ('bc','c0','c4','c8')}
            sa, sb = ra['selfcons'], rb['selfcons']
            if da != db or (ra['mask_in'], ra['processed']) != (rb['mask_in'], rb['processed']) or sa != sb:
                print(f"   idx {i}: deltas {da} -> {db}; selfcons {sa}->{sb}; mask_in {ra['mask_in']}->{rb['mask_in']} processed {ra['processed']}->{rb['processed']}")
