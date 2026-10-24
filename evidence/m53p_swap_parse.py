import re, collections, sys
def parse(path):
    data=collections.defaultdict(dict); cur=None
    for ln in open(path):
        m=re.match(r'idx (\d+) fac (\d+) pop (\d+) flag (\d+) budget (\d+)->(\d+) mask_in (\S+) processed (\S+)',ln)
        if m: cur=int(m.group(1)); data[cur].update(fac=int(m.group(2)),pop=int(m.group(3)),flag=int(m.group(4)),b0=int(m.group(5)),b1=int(m.group(6)),tokens='')
        m=re.match(r'\s+(bc|c0|c4|c8) model=(-?\d+)\s+obs=(-?\d+)\s+delta=(-?\d+)\s+seed=\S+\s+sum=\S+\s*(.*)',ln)
        if m and cur is not None: data[cur][m.group(1)]=int(m.group(4)); data[cur][m.group(1)+'_tok']=m.group(5)
    return data
def report(path, label):
    data=parse(path); cnt=collections.Counter(); bad=[]
    for i,d in sorted(data.items()):
        nf=[f for f in ('bc','c0','c4','c8') if d[f]!=0]
        for f in nf: cnt[f]+=1
        if nf: bad.append((i,d['fac'],d['pop'],'f%d'%d['flag'],'b%d>%d'%(d['b0'],d['b1']),[(f,d[f]) for f in nf]))
    print('== %s: rows %d  full-match %d  mismatches bc %d c0 %d c4 %d c8 %d'%(label,len(data),len(data)-len(bad),cnt['bc'],cnt['c0'],cnt['c4'],cnt['c8']))
    return data,bad
if __name__=='__main__':
    d,b=report(sys.argv[1], sys.argv[2] if len(sys.argv)>2 else sys.argv[1])
    for x in b: print(x)
