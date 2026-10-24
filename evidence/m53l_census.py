
import gzip, csv, bisect, re, collections
# function map
fns=[]
with open('ghidra_out/index.csv') as f:
    for row in csv.reader(f):
        if len(row)>=2:
            try: a=int(row[0],16)
            except: continue
            fns.append((a,row[1]))
fns.sort()
addrs=[a for a,_ in fns]
def fnof(v):
    i=bisect.bisect_right(addrs,v)-1
    return fns[i][1] if i>=0 else '?'
# disps of interest: raw +0x48/+0xc0/+0xcc and loop-ptr(base+4)-shifted +0x44/+0xbc/+0xc8
TARGET={0x48:'f48',0x44:'f44or48?',0xbc:'fbcor c0?',0xc0:'f c0',0xc8:'fc8orcc?',0xcc:'fcc'}
store_re=re.compile(r'^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2} )+\s*(mov|add|sub|and|or|xor|adc|sbb|movzx|movsx)\s+(DWORD|WORD|BYTE|FWORD)?\s*PTR\s+\[([^\]]+)\],(.*)$',re.I)
single_re=re.compile(r'^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2} )+\s*(inc|dec|neg|not)\s+(DWORD|WORD|BYTE)?\s*PTR\s+\[([^\]]+)\]$',re.I)
disp_re=re.compile(r'([+-])0x([0-9a-f]+)$')
out=open('evidence/m53l_stores_disp.txt','w')
percounts=collections.Counter(); perfn=collections.Counter()
mask=open('evidence/m53l_mask_refs.txt','w'); maskc=0
era=open('evidence/m53l_era_refs.txt','w'); erac=0
eraaec=0; era68=0
with gzip.open('evidence/m53j_text.txt.gz','rt') as f:
    for line in f:
        if '985b10' in line:
            mask.write(line); maskc+=1
        if '985aec' in line:
            era.write(line); eraaec+=1
        elif '68cbb8' in line:
            era.write(line); era68+=1
        m=store_re.match(line) or single_re.match(line)
        if not m: continue
        va=int(m.group(1),16); bracket=m.group(m.re.groups-2 if False else (4 if m.re.pattern.count('(')>=4 else 3))
        # robust: groups are (va, mn, size, bracket, rest) for first; (va,mn,size,bracket) for second
        g=m.groups()
        va=int(g[0],16)
        bracket=g[3]
        d=disp_re.search(bracket.strip())
        if not d: continue
        sign=1 if d.group(1)=='+' else -1
        val=sign*int(d.group(2),16)
        if val in TARGET:
            name=fnof(va)
            out.write(f"{va:06x} {name} {TARGET[val]} {line.strip()}\n")
            percounts[TARGET[val]]+=1; perfn[(name,TARGET[val])]+=1
out.close(); mask.close(); era.close()
print("STORE-DISP counts:",dict(percounts))
print("TOP fns:")
for (n,t),c in perfn.most_common(14): print(f"  {c:3d} {t:10s} {n}")
print(f"mask 0x985b10 refs: {maskc}; era refs 985aec: {eraaec}, 68cbb8: {era68}")
