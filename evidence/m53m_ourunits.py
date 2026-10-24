
import struct
pid = int(open('/tmp/m53m_pid.txt').read().strip())
with open('/proc/%d/mem' % pid,'rb',0) as f:
    f.seek(0x933278); raw = f.read(339*52)
    f.seek(0x963150); b = f.read(0x130)
    bx, by = struct.unpack('<HH', b[0:4])
    f.seek(0x92ae14)
    out = ['base70 x=%d y=%d owner=%d pop=%d min=%d' % (bx, by, b[4], b[6], struct.unpack('<i', b[0x40:0x44])[0])]
    for i in range(339):
        r = raw[i*52:i*52+52]
        if r[14] != 3: continue
        x, y = struct.unpack('<HH', r[0:4]); typ = struct.unpack('<H', r[10:12])[0]
        order = r[17]; bidx = struct.unpack('<h', r[46:48])[0]
        ti = y*40 + (x>>1)
        f.seek(0x92ae14 + ti*0x2c); t8 = f.read(1)[0]; t2 = f.read(1)[0]  # +8 then +9? no:
        f.seek(0x92ae14 + ti*0x2c + 8); t8 = f.read(1)[0]
        f.seek(0x92ae14 + ti*0x2c + 2); t2 = f.read(1)[0]
        out.append('u%-3d x=%2d y=%2d typ=%-3d ord=%-3d bidx=%-4d terr8=0x%02x lvl=%d %s' % (i,x,y,typ,order,bidx,t8,t2&0xf,'YIELD-OK' if (not (t8&1)) or (t2&0xf)>7 else 'good'))
print('\n'.join(out))
