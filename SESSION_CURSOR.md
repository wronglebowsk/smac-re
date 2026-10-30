M113 attempt 1 firing (tag m113map1): scripts/m113_save_map.py --tag m113map1 --relaunch --step 16384 plants 20 markers 0xC0DE0001.. at 16 KB offsets + the 6 candidate section starts in m113map.SAV, loads it, scans memory for each. Deliverable: (file_offset -> dest) anchors = the .SAV map.
PREDICT: consecutive markers chain into sections; an absent marker = a region the loader never restores.
PR #116/#117/#118 merged to main. Do not touch the box until m113map1 exits; then read evidence/m113map1.log.
