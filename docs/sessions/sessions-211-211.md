# Session notes archive — sessions 211-211

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 211 (2026-11-05, ANALYSE, M272 PASS) - FUN_0057ecf0 does NOT run on a LOAD; the .SAV restore chain is live-proven; the box-debt is paid
- Pick was the first BOX pick (box DOWN at open). Cold relaunch was FAST this time (~6 s to title,
  not >9 min) - the >9 min figure is stale.
- Box lesson (cost 4 failed launches): wine reparents terran.exe to systemd (PPID 1889) even when the
  launching harness is ALIVE, so the tracked-job ancestry escape is DEAD. Working shape:
  `sudo -n sh -c 'echo 0 > /proc/sys/kernel/yama/ptrace_scope' && DISPLAY=:99 python3 <harness>; \
  sudo -n sh -c 'echo 1 > ...'` - harness stays uid 1000. Running the harness under sudo fails
  (wine: "prefix is not owned by you" -> "no terran.exe after relaunch"); capsh --add-ambient absent.
- `scripts/m272_gen_load_watch.py --relaunch --tag m272w9`: 14 bps (GEN entry + 4 caller entries +
  4 gen call sites + 4 controls incl. a CONDITIONAL bp on the fread wrapper 0x64cc00 keyed to
  dest 0x927590). Live run 11/12 (only FAIL: parser). `python3 scripts/m272_acceptance.py` ->
  **ACCEPTANCE M272 PASS 5/5** offline over `evidence/m272w9.gdblog` (deterministic; the shipped gate).
- FINDING: in a sentinel-valid LOAD window (ROUND poked -39 -> 50 read back; counts == m104 image):
  the .SAV opener 0x597ee0 fires AT round=-39 (ret 0x5992f2), then the read wrapper fires at
  round=50 ret 0x596edb INSIDE FUN_00596850 = the M106 in-place body-loader chain, live.
  0 events at FUN_005b2970 (generator), its 4 call sites, and all 4 caller entries => NO.
  Pitfall: entry bps at 0x597ee0/0x596850 NEVER fire although the chain is proven by the call-site
  return addresses - execution enters these loaders MID-BODY; prove a chain by rets, not entries.
- Boot window: 0x5791c0 x7 (bps live at process start); GEN 0 there is NOT a control (attach ~3.5 s
  after launch, generator may precede it). New-game generation and save-load are DISJOINT paths -
  the B6 headless spine never regenerates on load.
