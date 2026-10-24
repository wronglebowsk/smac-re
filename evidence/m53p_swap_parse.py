import re, collections, sys
# Census parser for scripts/m53p_recon_a.py output.
# Header: idx N fac F pop P flag F budget B0->B1 mask_in 0xHEX processed 0xHEX
# `sc` (self-consistent) == mask_in == processed: the only rows whose deltas can be a rule
# gap; every other row carries a stale per-visit mask (DAT_008f0d30 is rebuilt per 4e78e0
# entry -> it describes only the base in DAT_0068cbb0). See evidence/m53p_mask_findings.md.
def parse(path):
    data=collections.defaultdict(dict); cur=None
    for ln in open(path):
        m=re.match(r'idx (\d+) fac (\d+) pop (\d+) flag (\d+) budget (\d+)->(\d+) mask_in (\S+) processed (\S+)',ln)
        if m:
            cur=int(m.group(1))
            mi=int(m.group(7),16); pr=int(m.group(8),16)
            data[cur].update(fac=int(m.group(2)),pop=int(m.group(3)),flag=int(m.group(4)),
                             b0=int(m.group(5)),b1=int(m.group(6)),mask_in=mi,processed=pr,
                             sc=(mi==pr),tokens='')
        m=re.match(r'\s+(bc|c0|c4|c8) model=(-?\d+)\s+obs=(-?\d+)\s+delta=(-?\d+)\s+seed=\S+\s+sum=\S+\s*(.*)',ln)
        if m and cur is not None: data[cur][m.group(1)]=int(m.group(4)); data[cur][m.group(1)+'_tok']=m.group(5)
    return data
def report(path, label):
    data=parse(path); cnt=collections.Counter(); bad=[]; scrows=[]; scbad=[]
    for i,d in sorted(data.items()):
        nf=[f for f in ('bc','c0','c4','c8') if d[f]!=0]
        row=(i,d['fac'],d['pop'],'f%d'%d['flag'],'b%d>%d'%(d['b0'],d['b1']),[(f,d[f]) for f in nf])
        for f in nf: cnt[f]+=1
        if nf: bad.append(row)
        if d.get('sc'):
            scrows.append(i)
            if nf: scbad.append(row)
    print('== %s: rows %d  full-match %d  mismatches bc %d c0 %d c4 %d c8 %d'%(label,len(data),len(data)-len(bad),cnt['bc'],cnt['c0'],cnt['c4'],cnt['c8']))
    print('   self-consistent (mask_in==processed): %d rows, %d exact, %d residual'%(len(scrows),len(scrows)-len(scbad),len(scbad)))
    return data,bad,scrows,scbad
if __name__=='__main__':
    rep=report(sys.argv[1], sys.argv[2] if len(sys.argv)>2 else sys.argv[1])
    if '--sc' in sys.argv:
        for x in rep[3]: print('  SC residual',x)
    else:
        for x in rep[1]: print(x)
