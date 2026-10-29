M97 RUNNING (session 152) | m97credit1 FAIL 9/10 (G10 only: 2 `[New LWP]` attach banners
not whitelisted — parse fix, floor untouched) | merged? no | milestone/m97
DATA: 26 events, 3 on CREDIT +0xd0, all pc 0x4e955d (store 0x4e9557 in FUN_004e93f0),
callers ret 0x4f5ad7/0x4f5b4b (FUN_004f5a70), credit 0->-1->0->-1, c0-f0-e0 == new 3/3.
NEXT: python3 scripts/m97_credit_watch.py --tag m97credit2 --boundaries 2 (box alive r52)
on University Base row 0x95da10 +0xd0 = 0x95dae0, credit; instrument self-check = poke +0xd0
from gdb and confirm the watchpoint reports it). Name writer by containment via
ghidra_out/index.csv; read credit back from /proc. Static first: dis 0x4ef7d0-0x4ef810 (income
add 0x4ef7f6) and 0x4efef0-0x4eff40 (clamp 0x4eff20) to see which writes +0xd0.
Box: m54b_clean r66, screen stuck base/quit-prompt loop (normalize_screen False -> relaunch),
credit -1, pending 0, q0 stale 2, storage 0, ebc 0x1a0e, mask 8.
