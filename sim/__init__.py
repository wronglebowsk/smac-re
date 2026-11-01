"""sim/ — R1: a headless SMAC turn loop built from decoded data (see BUILD_SPINE.md).

Rules for this package: never read /proc, never spawn gdb, never load a game binary,
never import the Wine harness. It may import scripts/decode_map.py and scripts/parse_alpha.py.
"""
