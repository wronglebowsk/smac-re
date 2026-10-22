# SMAC under Wine — runnability, input, audio

Procedures + findings for running terran.exe (SMAC) under Wine on a headless
Linux box (Xvfb + software GL). Verified reaching a live single-player game.

## Build / prereqs
- Use a **pure 32-bit** Wine build (e.g. Kron4ek wine-10.20-staging-tkg-x86).
  wine-11.x is 64-bit only (no i386); a wine-10.20-amd64 WoW64 prefix stays
  PE32+-only and 32-bit games fail there.
- i386 multiarch host libs, else `could not load kernel32.dll c0000135`:
  `dpkg --add-architecture i386 && apt install libc6:i386 libgl1:i386 libasound2:i386 libgnutls30t64:i386 libgcrypt20:i386`.

## Launch + capture
```
cd ~/reverse/smac/programs
WINEPREFIX=~/.wine-smac32 DISPLAY=:99 WINEDLLOVERRIDES='mscoree,msxml=' \
  ~/tools/wine-10.20-staging-tkg-x86/bin/wine explorer /desktop=smac,800x600 terran.exe
```
- Xvfb: `Xvfb :99 -screen 0 1920x1080x24 -ac -nolisten tcp`.
- Screenshot: `ffmpeg -f x11grab -video_size 800x600 -i :99 -frames:v 1 out.png`.
- Drive with **xdotool** on DISPLAY=:99: window via `xdotool search --name "Alpha
  Centauri"`; the window sits at 0,0 800×600, so screenshot pixels == click coords.
- Kill: `pkill -f terran.exe`. Avoid `pkill -f wineserver` from a shell whose own
  cmdline contains the pattern — it self-matches and SIGKILLs the shell.

## Boot chain + click coords (800×600)
Firaxis splash → "CD-ROM not detected" check (OK ≈487,341) → main menu (START
GAME / QUICK START / SCENARIO / LOAD GAME / MULTIPLAYER / VIEW CREDITS / EXIT
GAME; QUICK START ≈612,198) → "PLANETFALL!" faction intro (OK ≈593,561) → "Enter
a name for your first base" (OK ≈400,171) → live isometric HUD.
HUD buttons: TURN COMPLETE ≈635,410; MENU ≈48,372 (dropdown GAME/HQ/NETWORK/MAP/
ACTION/TERRAFORM/SCENARIO/EDIT MAP/HELP); COMMLINK top-right.
- A boot can land in the **new-game setup wizard** instead of a game (START GAME / MAKE RANDOM
  MAP / PICK A DIFFICULTY LEVEL / CHOOSE YOUR FACTION). There, `Return` advances difficulty →
  planet size → random map → "ENTER A NAME" → live game, and `Escape` walks back one step.
  QUICK START exists only on the main menu, never inside the wizard; do not Escape out of the
  wizard expecting a menu shortcut.

## Audio (DirectSound / mmdevapi)
Host with no soundcard + empty i386 alsa plugin dir → Wine 10.x defaults to the
**winepulse** backend, which needs i386 `libpulse.so.0`; missing →
`mmdevapi:load_driver … c0000135`. Fix: `sudo apt-get install -y libpulse0:i386`
(works when pipewire-pulse is running, so winepulse connects). A null
`~/.asoundrc` alone does NOT fix it (winepulse, not winealsa, is the default path).

## Input routing (exe-verified)
WNDPROC `FUN_005d0c33` dispatches WM_LBUTTONDOWN(0x201)→`FUN_005d1dcf`,
LBUTTONUP(0x202)→`FUN_005d1ec5`, WM_MOUSEMOVE(0x200)→`FUN_005d1cf3`,
WM_PAINT(0xf)→`FUN_005d13c7`, WM_ACTIVATE(0x6)→`FUN_005d1505`.
`FUN_005d1dcf` hit-tests the widget tree via `FUN_005d711a`→recursive
`FUN_005d6a80` (children `w+0x69*4`, count `w+0xff`, flags `w+0x26`/child`+0x98`,
contains-point vtable+0xec, transparent sentinel `DAT_00698be8`, active-control
flag `DAT_00993988`), then calls the widget's **vtable+0x124** press-test: return
**2 or 10–17 ⇒ DRAG/SCROLL** (a map click pans the view instead of issuing a unit
order — this is why blind automation can't move units); otherwise **vtable+0x138**
= the real click action.

## Script.txt dialog geometry (live panes)
OPERATIONS DIRECTOR "units have not moved" confirm: rows at y≈181/196/233 depending on the
build and on whether the centre panel is still typing, **OK bar ≈26 px below the selected row**
(measured y≈222 under the y≈196 row). So locate the row by OCR (`Yes`/`turn` word with
160 ≤ y ≤ 220) and click the bar relative to it — hard-coded y values drift. There is a DEAD
GAP between the row and the bar, so a click in between selects nothing and looks like a hang. The center info panel TYPES its text char-by-char on every selection
change, so a screenshot right after a click catches it mid-render.

## Turn cycle — SOLVED (it was an automation problem)
Turns advance normally in solo under Wine: 100+ turns unattended, Mission Year climbing
2101→2181 at 8–12 s/turn. Every "frozen turn" ever observed was a blocking UI element the
driver never answered (units-not-moved confirm, advisory/speech dialog, NETFLASH,
tech-breakthrough screen, base screen, Secret Project movie) — not a game hang, not
DirectPlay, not Wine. Screen taxonomy, classifier order, memory oracle and the loop:
**`references/wine-headless-harness.md`** — follow that, do not re-derive it.
Unit-move clicks are still eaten by the drag/scroll path (see Input routing) — that is a
separate limitation that matters only once the driver issues orders.
**DirectPlay hypothesis REFUTED at runtime.** Launched with
`WINEDEBUG=+dplayx,+dplay,+loaddll` and drove a full turn: Wine's dplayx loads and does
a one-time startup lobby probe (`DPLAYX_ConstructData` → `DirectPlayLobbyCreateA` →
`IDirectPlayLobby3A` → `GetConnectionSettings` → "Application 0x00000000 is not
lobbied"), then the log stays frozen — **no EnumerateApplications / Connect / CreatePlayer
/ GetMessages / SendData at all**, through reaching the live HUD and attempting a turn.
Wine traces every dplayx entry point, so an absent trace line means the game never made
that call. So **single-player opens no DirectPlay session and pumps no DirectPlay
messages** — turn sync in solo does NOT ride the DirectPlay loopback; the stall is not a
Wine-dplayx problem and DP shims (dgVoodoo2 / nGage / glsmac) won't fix it.

**Reusable diagnostic:** to settle whether a game actually uses a DLL at runtime, run it
under `WINEDEBUG=+<dll>` and grep the log — Wine traces every entry point of that DLL, so
no line for a function ⇒ the app never calls it (absence is evidence). Wine logs the
DirectPlay DLL under the `dplay` trace channel even when the module is DPLAYX.dll.

Next lead (not DirectPlay): the in-process turn loop / "server" tick / threading under
Wine — relaunch with `WINEDEBUG=+winex.win32,+timer,+msg,+seh` and grep around a turn
for a blocking fixme/spin.

## glsmac build deps
`apt install libsdl2-dev libsdl2-image-dev libfreetype-dev` + still needed:
libglew-dev, uuid-dev (ossp-uuid), libyaml-cpp-dev. cmake + ninja present.
