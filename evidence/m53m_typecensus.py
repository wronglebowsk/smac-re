
import struct
pid = int(open('/tmp/m53m_pid.txt').read().strip())
with open('/proc/%d/mem' % pid,'rb',0) as f:
    f.seek(0x98ad88); tr = f.read(200*52)
hits=[]
for t in range(200):
    r = tr[t*52:t*52+52]
    if all(b==0 for b in r): continue
    plan = r[42]; cost = r[41]
    hits.append((t,plan,cost))
from collections import Counter
print('type rows live=%d ; plan census: %s' % (len(hits), sorted(Counter(h[1] for h in hits).items())))
print('plan==10 types:', [h[0] for h in hits if h[1]==10])
print('plan==10 type detail rows (t, plan, cost):', [h for h in hits if h[1]==10])
