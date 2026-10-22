# Digest — evidence/m50a_watch.log

258 lines, 17 KB. Read this instead of the log; open windows with `evidence.py show m50a_watch.log:<line>`.

## Line kinds

- `SITE` × 162
- `PIPE` × 28
- `Breakpoint` × 20
- `[New` × 16
- `UNIT` × 7
- `Hardware` × 4
- `WP` × 4
- `(blank)` × 2
- `SELFTEST` × 2
- `This` × 1
- `<https://debuginfod.ubuntu.com>` × 1
- `Enable` × 1

## Samples (first 3 of each kind)

- `SITE 1 IGATE base=0x95dda0 own=4 d0=47 q50=-29 f30=0x3004020 min40=49 ours=0`
- `SITE 2 IADD base=0x95dda0 own=4 added=6 newmin40=55 ours=0`
- `SITE 3 QGATE base=0x95dda0 own=4 q50=4 ours=0`
- `PIPE n=1 base=0x95dda0 own=4 x=77 y=13 min40=49 3c=47 cc=2 d0=6 q50=-29 ours=0`
- `PIPE n=2 base=0x95e260 own=4 x=79 y=17 min40=38 3c=0 cc=0 d0=6 q50=-29 ours=0`
- `PIPE n=3 base=0x95ef70 own=4 x=9 y=15 min40=34 3c=22 cc=1 d0=10 q50=265 ours=0`
- `Breakpoint 1 at 0x51f554`
- `Breakpoint 2 at 0x4ef6d0`
- `Breakpoint 3 at 0x4ef7db`
- `[New LWP 2124645]`
- `[New LWP 2124644]`
- `[New LWP 2124643]`
- `UNIT idx=178 type=2 x=45 y=11 order=0 mpused=0 home=71`
- `UNIT idx=180 type=2 x=45 y=11 order=0 mpused=0 home=71`
- `UNIT idx=266 type=2 x=45 y=11 order=0 mpused=0 home=71`
- `Hardware watchpoint 17: *(int *)0x962ea0`
- `Hardware watchpoint 18: *(int *)0x962eb0`
- `Hardware watchpoint 19: *(int *)0x962f30`
- `WP 1 D0 eip=0x4e955d new=-1 c0=6 f0=7 e0=0 min40=200`
- `WP 2 ENERGY eip=0x4f5c92 new=21 eax=0x15 ecx=0x962e60 esi=0x6234 edi=0x3`
- `WP 3 ENERGY eip=0x4f4958 new=20 eax=0x1 ecx=0x14 esi=0x6 edi=0x6234`
- ``
- ``

last line: `[Inferior 1 (process 2124624) detached]`
