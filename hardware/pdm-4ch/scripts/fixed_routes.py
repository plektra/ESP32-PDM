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
# area (tracks may only enter the small escapes around foreign pads). 5 %: decision 172 (signal vias in VS-In2).
POUR_LOSS_MAX = 0.05

# GND/GND_CAN stitching grid (mm); a via is added only where all four layers are fill of that net.
STITCH_PITCH_MM = 5.0

# Fixed tracks: {'net': '/SW1', 'layer': 'F.Cu', 'width': 0.2, 'pts': [(x, y), ...]}
TRACKS = []
# Fixed vias: {'net': '/SW1', 'at': (x, y), 'size': 0.6, 'drill': 0.3}
VIAS = []


def T(net, layer, *pts, w=0.2):
    TRACKS.append({'net': net, 'layer': layer, 'width': w, 'pts': list(pts)})


def V(net, x, y, size=0.6, drill=0.3):
    VIAS.append({'net': net, 'at': (x, y), 'size': size, 'drill': drill})


# ---- CAN pair (T-0210): U5 -> FL1 (choke) -> D9 (ESD) -> J4, R71/R72 choke bypass. All on the CAN side over the
# GND_CAN planes (In1 solid); H and L run side by side on F.Cu, the two crossings the pin order forces drop to B.Cu
# (CANH_BUS, D9.1/R71.1 -> J4.3) and In2 (CANL_XCVR under the choke). Nothing crosses the CAN barrier.
CH, CL, CHX, CLX = '/CAN/CANH_BUS', '/CAN/CANL_BUS', '/CAN/CANH_XCVR', '/CAN/CANL_XCVR'
T(CHX, 'F.Cu', (76.83, 55.87), (78.02, 55.87), (79.78, 57.62))                 # U5.7 -> FL1.2
T(CHX, 'F.Cu', (79.78, 57.62), (79.78, 56.5), (84.24, 56.5), (84.65, 56.09), (85.2, 56.09))  # FL1.2 -> R71.2
T(CLX, 'F.Cu', (76.83, 57.13), (77.47, 57.13), (78.06, 57.73))                 # U5.6 -> via
V(CLX, 78.06, 57.73)
T(CLX, 'In2.Cu', (78.06, 57.73), (83.26, 57.73), (84.25, 58.72))               # under the choke
V(CLX, 84.25, 58.72)
T(CLX, 'F.Cu', (84.25, 58.72), (83.42, 57.89), (83.42, 57.62))                 # -> FL1.3
T(CLX, 'F.Cu', (86.4, 56.09), (85.8, 56.6))                                    # R72.2 down between R71/R72:
T(CLX, 'F.Cu', (85.8, 56.6), (85.8, 57.6), w=0.15)    # 0.15 neck: the slot between the 0402 pads is 0.56 mm
T(CLX, 'F.Cu', (85.8, 57.6), (85.8, 58.72), (84.25, 58.72))                     # -> via
T(CH, 'F.Cu', (79.78, 55.38), (81.78, 55.38), (83.70, 53.45), (86.0, 53.45), (87.96, 53.45))  # FL1.1 -> D9.1
V(CH, 86.0, 53.45)
T(CH, 'B.Cu', (86.0, 53.45), (88.83, 56.28), (93.3, 56.28))                    # D9.1 -> J4.3 under the L pair
T(CH, 'F.Cu', (85.2, 57.11), (85.1, 58.05))                                    # R71.1 -> via
V(CH, 85.1, 58.05)
T(CH, 'B.Cu', (85.1, 58.05), (87.5, 58.05), (89.27, 56.28))
T(CL, 'F.Cu', (83.42, 55.38), (83.73, 55.07), (86.78, 55.07), (87.11, 55.35), (87.96, 55.35))  # FL1.4 -> D9.2
T(CL, 'F.Cu', (87.96, 55.35), (87.96, 54.89), (90.38, 52.47), (93.3, 52.47))   # D9.2 -> J4.4
T(CL, 'F.Cu', (86.4, 57.11), (87.08, 56.43), (87.08, 55.32))                   # R72.1 -> L


# ---- USB D+/D- pair (T-0210): J3 -> D5/D6 (ESD, at the connector) -> U1 fan-out vias (69.25,16.8)/(70.10,18.0).
# The VS block is closed on In2 (VS-In2) and B (VS spine) east of x 46.5, so the pair crosses it on F.Cu in the gap
# between U12/D201 and U13 (y 20.5/21.15), runs west on B.Cu in the free band y 19-19.5 (between VS-B-front and
# VS-B-rear), and uses In2 only where In2 is the GND plane (x < 26.5 and x > 56.5). Vias sit outside the power
# outlines or at their edge (clearance holes only; no pour is cut through).
DN, DP = '/USB_DN', '/USB_DP'
# J3 end: DP joins A6/B6 over the top, DN joins A7/B7 below the pads; no via under J3 (OUT1-B is on B.Cu there)
T(DP, 'F.Cu', (14.45, 8.24), (14.45, 7.49), (14.72, 7.22), (15.18, 7.22), (15.45, 7.49), (15.45, 8.24))
T(DP, 'F.Cu', (14.45, 8.24), (14.45, 9.18), (15.42, 10.15), (17.5, 10.15), (18.0, 10.15))   # -> D5.2
T(DP, 'F.Cu', (17.5, 10.15), (17.25, 10.4), (17.25, 13.6))                                   # past D5.1/D6.1
V(DP, 17.25, 13.6)
T(DN, 'F.Cu', (14.95, 8.24), (14.95, 9.08), (15.15, 9.28), (15.69, 9.28))
T(DN, 'F.Cu', (15.95, 8.24), (15.95, 9.02), (15.69, 9.28), (15.96, 9.55), (18.55, 9.55), (18.75, 9.75),
  (18.75, 11.85), (18.55, 12.2))                    # under A5/B8/A4, between D5 and D4, into D6.2 (stays off OUT1-B)
V(DN, 18.85, 13.35)
T(DN, 'F.Cu', (18.55, 12.2), (18.85, 13.35))                                                # D6.2 -> via
# GND for D5.1/D6.1, walled in by the pair: one via between the two pair vias
T('GND', 'F.Cu', (18.0, 10.85), (17.85, 12.2), (18.05, 13.0), w=0.3)
V('GND', 18.05, 13.0)
# GND for D4.1/R12.2/J3 A1-B12 east of D-: a via below OUT1-B (y > 11.6) and above OUT2-F (y < 14.1); without it
# the build's island tie-in put a via inside OUT1-B and the pour check failed (T-0210 build 3)
T('GND', 'F.Cu', (19.5, 10.85), (19.7, 11.99), (20.55, 12.25), w=0.3)
V('GND', 20.55, 12.25)
# B.Cu run west -> east
T(DP, 'B.Cu', (17.25, 13.6), (17.25, 19.5), (44.15, 19.5), (46.15, 21.5))
T(DN, 'B.Cu', (18.85, 13.35), (18.85, 19.0), (44.65, 19.0), (46.15, 20.5))
V(DP, 46.15, 21.5)
V(DN, 46.15, 20.5)
# F.Cu through the U12/U13 gap
T(DN, 'F.Cu', (46.15, 20.5), (57.5, 20.5))
T(DP, 'F.Cu', (46.15, 21.5), (46.5, 21.15), (58.4, 21.15))
V(DN, 57.5, 20.5)        # west of x 59.5, so IO4 keeps its B.Cu lane at x 60.35
V(DP, 58.4, 21.15)
# In2 (GND plane east of x 56.5; VS-In2 keeps >= 0.9 mm) under U1 to the fan-out vias
T(DN, 'F.Cu', (69.25, 19.3), (69.25, 16.8))     # U1.23/U1.24 fan-out (was T-0208 copper, now defined here)
V(DN, 69.25, 16.8)
T(DP, 'F.Cu', (70.1, 19.3), (70.1, 18.0))
V(DP, 70.1, 18.0)
T(DN, 'In2.Cu', (57.5, 20.5), (57.5, 18.95), (69.25, 18.95), (69.25, 16.8))
T(DP, 'In2.Cu', (58.4, 21.15), (58.4, 19.4), (69.65, 19.4), (70.1, 18.95), (70.1, 18.0))

# ---- J3 CC1 (T-0210): A5 sits between the pair; it leaves above the pads (via clear of the J3 NPTH and of OUT1-B),
# runs on In2 (GND plane, x < 26.5) past the pair vias and comes up beside R12.1.
CC1 = 'Net-(J3-CC1)'
T(CC1, 'F.Cu', (16.45, 8.24), (16.45, 7.3), (16.7, 6.85))
V(CC1, 16.7, 6.85)
T(CC1, 'In2.Cu', (16.7, 6.85), (16.7, 9.0), (19.4, 11.7), (19.7, 12.0), (19.7, 13.95))
V(CC1, 19.7, 13.95)
T(CC1, 'F.Cu', (19.7, 13.95), (19.7, 13.01))
