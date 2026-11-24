# NAMED.md `## M286` - ROTATED VERBATIM (byte-exact) by scripts/m376_named_rotate.py

<!-- ## M286 sha1 25eb67cd987ee7825bf1f90568f4b056ebae42c9 len 1465 -->
## M286 (s231) REALLYQUIT message dialog IS family (0x67164c) but does NOT dispatch +0x4c on clicks (static 5/5, live STATE 4 measured-negative w/ falsifier)
- **LIVE HALF INSTRUMENT-INVALID (s240/M293):** the SITE guard
  `if $reg >= 0x1000000` excluded every image-range vtable (the five family
  vtables 0x67164c/0x6717cc/0x6728c0/0x675cc4/0x6776c8 are all < 0x1000000),
  so a real family dispatch printed NOTHING: the live 0-fired rows here are
  instrument-silence, RETRACTED as evidence (static claims stand; guard now
  >= 0x400000; a re-armed census is an open lead).

- The +0x4c slot (FUN_005f6aa3) is the dialog ROW-CLICK dispatcher
  (76-B body: FUN_005e7917 row finder over 0x18-stride rows, idx/-1, then
  (**(code **)(*ecx + 0xa8))(local_c)) - so a family dialog click SHOULD
  enter one of the 12 sites with slot 0x5f6aa3.
- Live: raised REALLYQUIT (Escape on bare HUD after closing base display),
  read the dialog vptr AT the click: obj 0x014d7458 -> vptr 0x67164c FAMILY;
  clicked the safe 'oops' row + OK; pump FUN_005f1394 ran (1), wndproc
  LBUTTONDOWN 2, pane closed (DIALOG_CUR 0).  Sites 0/12, ENTRY 0.
- Conclusion: the message OK/CANCEL class (0x67164c) click path dispatches
  the row callback INLINE in the pump, NOT via the +0x4c slot.  M284+M285+
  M286 = three live paths, zero observed +0x4c dispatch.
- Evidence: evidence/m286_reallyquit_dispatch.txt; script
  scripts/m286_reallyquit_dispatch.py (--static 5/5, --live STATE 4).

