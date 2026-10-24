
import sys
sys.path.insert(0,'scripts')
import m53p_recon_a as M
M.init()
G=M.G; s32=M.s32; sdiv=M.sdiv
NB=G["nbases"]
def E(fac,bidx,x,y,fb):
    t=M.tile_idx(x,y); r=M.terr(t)
    u9=r["u9"]; uc=r["uc"]; raw0=r["raw0"]; b=r["b"]
    land=(raw0&0xE0)<0x60
    if (b[8]&1)==0: u6=-1
    else:
        u6=b[2]&0xF
        if u6>7: u6=-1
    z=M.code5831a0(x,y)
    v4=M.s32v("g926",0x926c10)   # DAT_00926c10
    i5=M.s32v("g926",0x926bf0)
    u8v=uc
    b3 = ((uc&0x80000002)==2 and M.ashr(M.s32v("terrain",M.BLOB_BASE["terrain"]+t*0x2c+0xC),0x18)<9) or (uc&0x80000008)==8 or (uc&0x80000400)==0x400 or (uc&0x80000800)==0x800
    loc=0
    if u6<0:
        if (u9&0x2000)==0:
            if (u9&0x1000000)==0:
                if (u9&0x20) and ((raw0&0xE0)>0x3F):
                    loc=M.u32("facrec",0x94D698+fac*0x20BC)
                    if M.s32(loc)<-3: loc=0xFFFFFFFD
                    else: loc=loc & ((0<M.s32(loc))-1) & 0xFFFFFFFF
                    loc=M.s32(M.s32v("facrec",0x94D74C+fac*0x20BC)+M.s32(loc))
                    if M.s32(loc)<0: loc=0
                    elif M.s32(loc)>99: loc=99
                    return fin(loc)
                if land:
                    if (raw0&0xE0)==0x40:
                        loc=M.s32v("g926",0x926be0)
                        if (u9&0x40) or False: loc=M.s32v("g926",0x926be0)+M.s32v("g926",0x926c40)
                    if u9&0x200000: loc=M.s32(loc)-1
                elif (u9&0x200000)==0:
                    u8v=(raw0>>5)-2
                    if (u9&0x1800040) or False: loc=u8v & ((M.s32(u8v)<0)-1) & 0xFFFFFFFF
                    else: loc=0
                    if u9&0x40:
                        cnt=0
                        for k in range(8):
                            nx=M.s32v("offs",0x6784a0+k*4)+x
                            if (G["wrap"]&1)==0:
                                if nx<0: nx=M.s32(G["map_w"]+nx)
                                elif nx>=G["map_w"]: nx=M.s32(nx-G["map_w"])
                            ny=M.s32v("offs",0x6784c4+k*4)+y
                            if -1<ny<G["map_h"] and -1<nx<G["map_w"]:
                                nt=M.tile_idx(nx,ny); nr=M.terr(nt)
                                if (nr["u9"]&0x800000) and nr["b7"]==M.u8("bases",M.BLOB_BASE["bases"]+bidx*0x130+4):
                                    loc=M.s32(loc)+1
                        loc=M.s32(loc)
                else:
                    loc=v4
                    if -1<bidx:
                        if fb[0xE]: loc=v4+1
            else: loc=M.s32v("g926",0x926c60)
        else: loc=M.s32v("g926",0x926c50)
    else:
        if fb[1]: i5=M.s32(i5)+1
        loc=i5
        if bidx<0: i5=0
        else:
            if fb[3] or fb[0x1a]: loc=M.s32(i5)+M.s32v("g926",0x926c20)
            else:
                if (M.u8("bases",M.BLOB_BASE["bases"]+bidx*0x130+0x30)&4)==0: i5=0; 
                else: i5=1
            if not (fb[3] or fb[0x1a]):
                pass
            else:
                if (M.u8("bases",M.BLOB_BASE["bases"]+bidx*0x130+0x30)&4)==0: i5=0
                else: i5=1
        # recompute i5 branch exactly (see note below)
        if bidx>=0:
            if fb[3] or fb[0x1a]:
                loc=M.s32(M.s32v("g926",0x926bf0)+(1 if fb[1] else 0))+M.s32v("g926",0x926c20)
            else:
                loc=M.s32v("g926",0x926bf0)+(1 if fb[1] else 0)
            if (M.u8("bases",M.BLOB_BASE["bases"]+bidx*0x130+0x30)&4)==0: i5=0
            else: i5=1
        else: i5=0
        i5=M.s32(M.frec(0x94D67C,fac)+i5)
        if i5<0:
            if (not fb[1]) or i5<-1 or M.frec(0x94E488,fac)==1: i5=i5+1
        elif i5>1:
            if i5<2: i5=2
            elif i5>4: i5=4
            i5=i5*2-4
        loc=M.s32(loc)+i5
        if G["k85bc0"]==fac: loc=M.s32(loc)+1
    if (u9&0x80) and not land: loc=M.s32(loc)+1
    if z==3: loc=M.s32(loc)+M.s32v("g926",0x926c00)
    if b3: loc=M.s32(loc)+1
    if bidx<0: i10=0
    else:
        if G["k85b48"]==bidx: loc=M.s32(loc)+1
        i10=1 if (M.u8("bases",M.BLOB_BASE["bases"]+bidx*0x130+0x30)&4) else 0
    if M.s32(M.frec(0x94D67C,fac)+i10)>1: loc=M.s32(loc)+1
    if u6<0:
        if M.s32(loc)>2 and M.tech_avail(G["t_cap2"],fac)==False and z!=3:
            M.cc8(M.s32(loc)-2); loc=2
    else:
        if M.s32(loc)<0: loc=0
        else:
            if M.s32(loc)>99: loc=99
    # LAB_004e7586
    if -1<bidx:
        d=M.base_dword(bidx,0x34)
        if d&0x2000: loc=M.s32(loc)+1
        if (d&0x4000) and loc!=0: loc=M.s32(loc)-1
    if G["k85db8"] and loc!=0: loc=M.s32(loc)-1
    sel=(G["k85dc4"]&1) if G["g91c628"]==0 else (G["k85dc4"]&2)
    return M.s32(loc*3) if sel else M.s32(loc)
def fin(v):
    if -1<0: pass
    return v
diff=0
for i in range(NB):
    R=M.row(i); fac=R["fac"]; fb=M.fac_bits(i)
    for s in range(21):
        if not (R["d78"]>>s)&1: continue
        x=M.wrap_x(R["x"]+M.XOFF[s]); y=R["y"]+M.YOFF[s]
        if not (-1<y<G["map_h"] and -1<x<G["map_w"]): continue
        a=E(fac,i,x,y,fb); b=M.disp(2,fac,i,x,y,fb)
        if a!=b:
            diff+=1
            if diff<25: print("DIFF idx",i,"s",s,"x",x,"y",y,"mine",a,b)
print("total tile-level energy diffs:",diff)
