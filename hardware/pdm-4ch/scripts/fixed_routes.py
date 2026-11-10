"""Fixed routing for the pdm-4ch routing build (decision 163). Hand-made routing lives here, not on the board.

Coordinates: mm from the board's top-left outline corner (x right, y down), same as `tools/kpcb.py`.
Every item here is added LOCKED by `routing_build.py prep` (skipped if an identical item is already on the board),
so Freerouting treats it as fixed copper and later builds keep it.
"""

# Router net classes: name -> (width um, clearance um, layers or None for all four).
# Signals never use In1.Cu (solid GND/GND_CAN plane, EMC rule 3); the buck SW/CB nets stay on F.Cu.
CLASSES = {
    'hv':   (500, 1000, ('F.Cu', 'In2.Cu', 'B.Cu')),
    'p6':   (600, 300, ('F.Cu', 'In2.Cu', 'B.Cu')),
    'p4':   (400, 250, ('F.Cu', 'In2.Cu', 'B.Cu')),
    'buck': (500, 250, ('F.Cu',)),
    'gnd':  (400, 200, None),
    'v3':   (300, 200, ('F.Cu', 'In2.Cu', 'B.Cu')),
    'sig':  (200, 200, ('F.Cu', 'In2.Cu', 'B.Cu')),
}

# Escape around a foreign pad, via or track end inside a power-zone outline (mm). The rest of the outline is a
# keep-out for every other net, so the refilled power pours cannot be cut.
ESCAPE_MM = 0.5

# Keep-out strip along the board edge for the router (mm); with the 0.2 mm clearance it keeps copper >= 0.5 mm
# from the edge (board rule).
EDGE_STRIP_MM = 0.35

# Pour check: a power pour fails when it has more islands than before routing or lost more than this share of its
# area (tracks may only enter the small escapes around foreign pads).
POUR_LOSS_MAX = 0.02

# GND/GND_CAN stitching grid (mm); a via is added only where all four layers are fill of that net.
STITCH_PITCH_MM = 5.0

# Fixed tracks: {'net': '/SW1', 'layer': 'F.Cu', 'width': 0.2, 'pts': [(x, y), ...]}
TRACKS = [
]

# Fixed vias: {'net': '/SW1', 'at': (x, y), 'size': 0.6, 'drill': 0.3}
VIAS = [
]
