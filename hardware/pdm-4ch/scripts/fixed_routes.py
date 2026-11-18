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

# Router clearance between two fixed pads (um, T-0241 clean export): pads never move, KiCad DRC (0.2 mm) checks them;
# 190 absorbs Freerouting's polygon approximation of the 0.2 mm-gap J3 pads. Pin<->wire/via keeps the class values.
PIN_PIN_UM = 190
# Hole around fixed copper in a router keep-out (mm beyond the item): the smallest class clearance (signal 0.2 mm)
# + 0.05. A class-clearance hole (1.05 mm round VS copper) let signal wires, which keep only their own 0.2 mm in
# Freerouting, run inside a VS pour outline (T-0241 build 1: VS-B-spine -11 %, VS-In2 -16 %).
KEEPOUT_HOLE_MM = 0.25

# Pour check: a power pour fails when it has more islands than before routing or lost more than this share of its
# area (tracks may only enter the small escapes around foreign pads). 5 %: decision 172 (signal vias in VS-In2).
POUR_LOSS_MAX = 0.05

# In2 corridor (Q-0071): VS-In2 may lose up to 15 % of its 1190.7 mm2 baseline (T-0236) and must stay one island;
# the router keep-out stays over each PROFET's thermal-via field (pad THERMAL_PAD PTH vias) plus THERMAL_KEEP_MM.
# Decision 218 (within decision 215 (6)): VS-In2 may be cut into several pieces by signal runs. A piece without a VS
# via is removed by the fill (island removal), so every piece left is tied to VS; all 40 PROFET thermal vias must
# still sit in copper (thermal_check) and the pour keeps >= 75 % of its 1190.7 mm2 baseline (was 85 %, one island).
CORRIDOR_MIN_MM2 = {'VS-In2': round(1190.7 * 0.75, 1)}
THERMAL_PAD = '15'
THERMAL_KEEP_MM = 1.0
# corridor runs stay this far inside the VS-In2 outline (router keep-out band; maze_route.py CORRIDOR_BAND)
CORRIDOR_BAND_MM = 1.5
# The one marked exit (owner ruling Q-0075, T-0276): inside this window (x0, y0, x1, y1 mm) the band does not block the
# west-pocket In2 runs of EXIT_NETS, so they may cross the VS-In2 east edge (x 56.5) into a via column at x 56.3-57.
# The window covers only the east-edge band: x from the band's inner edge (56.5 - 1.5) to 57.0 (the via column limit;
# the band still blocks In2 at x 57-58, so a run must drop to a via there), y from the north-edge band (4.95 + 1.5) to
# 20. Every other place keeps the 1.5 mm band. The notch in the VS-In2 outline is VS_IN2_NOTCH (routing_build.prep).
EXIT_WINDOW_MM = (55.0, 6.45, 57.0, 20.0)
EXIT_NETS = ('/SW_IN1', '/SW_IN4', '/IO2', '/IO5', '/DEN')
# The notch (x0, y0, x1, y1 mm) cut from the VS-In2 outline by routing_build.prep (idempotent): the three column vias at
# x 56.45, y 15.7/16.6/17.5 (r 0.3) and the In2 runs into them (y 15.7-17.9, w 0.2) plus the 0.5 mm VS-In2 zone
# clearance: x 56.45 - 0.3 - 0.5 = 55.65 -> 55.6, y 15.7 - 0.8 = 14.9 to 17.9 + 0.1 + 0.5 = 18.5. The fill cannot use
# this copper anyway; x1 56.6 lies past the edge (x 56.5) so the cut is clean. Nothing else of the outline changes.
VS_IN2_NOTCH = (55.6, 14.9, 56.6, 18.3)   # T-0281: grown for the IO2/IO5 column vias (y 16.6/17.5 + 0.8)

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
# CANH flow-through (EMC E23, 2026-11-17): J4.3 reaches D9.1 first and only one track leaves D9.1 toward the
# transceiver; R71 (and FL1) are tapped behind the clamp at the via (86.0, 53.45). Was: a T at x 88.8-89.3 on B.Cu
# with D9 on a 6 mm side branch.
T(CH, 'F.Cu', (79.78, 55.38), (81.78, 55.38), (83.70, 53.45), (86.0, 53.45), (87.96, 53.45))  # FL1.1 <- D9.1
V(CH, 86.0, 53.45)
T(CH, 'B.Cu', (93.3, 56.28), (91.0, 56.28), (91.0, 53.8), (89.6, 52.4), (88.6, 52.4))  # J4.3 -> via N of D9.1
V(CH, 88.6, 52.4)
T(CH, 'F.Cu', (88.6, 52.4), (88.6, 53.45), (87.96, 53.45))                     # via -> D9.1 (enters the pad)
T(CH, 'F.Cu', (85.2, 57.11), (85.1, 58.05))                                    # R71.1 -> via
V(CH, 85.1, 58.05)
T(CH, 'B.Cu', (85.1, 58.05), (86.0, 57.15), (86.0, 53.45))                     # R71.1 <- behind D9
T(CL, 'F.Cu', (83.42, 55.38), (83.73, 55.07), (86.78, 55.07), (87.11, 55.35), (87.96, 55.35))  # FL1.4 -> D9.2
T(CL, 'F.Cu', (87.96, 55.35), (87.96, 54.89), (90.38, 52.47), (93.3, 52.47))   # D9.2 -> J4.4
T(CL, 'F.Cu', (86.4, 57.11), (87.08, 56.43), (87.08, 55.32))                   # R72.1 -> L
# C70 (DNP barrier cap) logic-side GND: its 0.5 mm track ends at x 67.40 and relied on the GND-F fill, which signal
# runs west of it can cut off (E22/E23 reroute, 2026-11-17: SW4/IO8). Its own via to In1, inside the logic side
# (barrier keep-out from x 67.5).
T('GND', 'F.Cu', (67.40, 61.70), (67.10, 61.70), w=0.5)
V('GND', 67.10, 61.70)
# Own GND vias for pads that relied on fill or on grid stitching vias (lost in the E22/E23 reroute, 2026-11-17):
# D52.1 (LED_K3 TVS) south of the pad, C14.2/C15.2 (SW1/SW2 filter caps) north of the pad.
T('GND', 'F.Cu', (78.8, 19.43), (78.8, 21.05), w=0.4)
V('GND', 78.8, 21.05)
T('GND', 'F.Cu', (66.82, 42.29), (66.82, 41.35), w=0.3)
V('GND', 66.82, 41.35)
T('GND', 'F.Cu', (66.82, 46.10), (66.82, 45.15), w=0.3)
V('GND', 66.82, 45.15)
# R1.2 (GND) to the R38.2 GND via of the router (pf_routes.json): the IO8/SW2 runs cut it off from the fill
T('GND', 'F.Cu', (65.25, 64.10), (65.71, 64.71), w=0.3)

# ---- Decision 222 (U30 -> LM74502H-Q1): pad 8 (SRC) takes the VBAT_FL track to the pour, pad 5 its own VBAT_FL via
# (to VBAT_FL-B), pad 7 (OV) to GND. Drawn on the board in that session; kept here so the build reproduces it.
T('/VBAT_FL', 'F.Cu', (41.2, 40.275), (40.25, 40.275), (40.25, 44.2), w=0.3)
V('/VBAT_FL', 40.25, 38.325)
T('GND', 'F.Cu', (41.2, 39.625), (39.55, 39.625), w=0.3)
V('GND', 39.55, 39.625)


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
# decision 215: the via sits straight above A5 (was 16.7, 6.85), so the VBUS pin A4/B9 can leave north between it and
# the J3 peg hole (18.09, 6.8); it is still 1.0 mm from the D+ top track and 0.56 mm from B8.
T(CC1, 'F.Cu', (16.45, 8.24), (16.45, 6.75))
V(CC1, 16.45, 6.75)
T(CC1, 'In2.Cu', (16.45, 6.75), (16.7, 7.0), (16.7, 9.0), (19.4, 11.7), (19.7, 12.0), (19.7, 13.95))
V(CC1, 19.7, 13.95)
T(CC1, 'F.Cu', (19.7, 13.95), (19.7, 13.01))

# (The J6 In2 bundle, the Freerouting harvest of the signal nets and the maze passes were removed with decision 215;
# what is left below of those blocks is GND and power copper.)
# ---- Routed copper of the T-0236 build 2 board (T-0246, Q-0072). Freerouting is no longer part of the build
# (decision 163 as amended by Q-0072): the copper the last Freerouting build left on the board (unlocked tracks and
# vias, incl. its GND stitching vias) is kept here verbatim as fixed routes, so the build reproduces the board
# without the router. Generated by harvest (KiCad python, unlocked items -> T/V lines, nm precision); the T-0241
# generated bus (made on a base without this copper) is dropped. Remaining connections are added below by
# maze_route.py.
T('GND', 'F.Cu', (52.700000, 60.190000), (53.525000, 60.190000), w=0.400)
T('GND', 'F.Cu', (65.000000, 5.300000), (64.150000, 5.300000), w=0.400)
T('GND', 'F.Cu', (36.000000, 57.875000), (36.000000, 56.972300), w=0.400)
T('GND', 'F.Cu', (46.480000, 8.171100), (46.480000, 8.500000), w=0.400)
T('GND', 'F.Cu', (67.600000, 15.120400), (67.600000, 13.950000), w=0.400)
T('GND', 'F.Cu', (9.716700, 4.224900), (9.016800, 3.525000), w=0.400)
T('GND', 'F.Cu', (42.283700, 70.921200), (43.610500, 70.921200), w=0.400)
T('GND', 'F.Cu', (62.990000, 53.800000), (61.850000, 53.800000), w=0.400)
T('GND', 'F.Cu', (23.483900, 6.724300), (24.250700, 6.724300), w=0.400)
T('GND', 'F.Cu', (62.250000, 7.200000), (63.051700, 7.200000), w=0.400)
T('GND', 'F.Cu', (49.537700, 18.378300), (46.425000, 15.265599), w=0.400)
T('GND', 'F.Cu', (80.615000, 11.360000), (81.475000, 10.500000), w=0.400)
T('GND', 'F.Cu', (62.250000, 5.300000), (61.448300, 5.300000), w=0.400)
T('GND', 'F.Cu', (69.250000, 5.300000), (68.400000, 5.300000), w=0.400)
T('GND', 'F.Cu', (40.781200, 66.950700), (42.249300, 66.950700), w=0.400)
T('GND', 'F.Cu', (54.650000, 5.600000), (54.400000, 5.850000), w=0.400)
T('GND', 'F.Cu', (71.743500, 15.057499), (71.637700, 14.951700), w=0.400)
T('GND', 'F.Cu', (71.800000, 5.300000), (70.950000, 5.300000), w=0.400)
T('GND', 'F.Cu', (65.480000, 26.800000), (65.010000, 26.800000), w=0.400)
T('GND', 'F.Cu', (57.444800, 32.844800), (56.600000, 32.000000), w=0.400)
T('GND', 'F.Cu', (67.600000, 10.650000), (69.250000, 10.650000), w=0.400)
T('GND', 'F.Cu', (66.820000, 38.480000), (66.820000, 37.655000), w=0.400)
T('GND', 'F.Cu', (59.956200, 9.124800), (58.812700, 9.124800), w=0.400)
T('GND', 'F.Cu', (75.200000, 5.300000), (76.250000, 5.300000), w=0.400)
T('GND', 'F.Cu', (11.395500, 8.799500), (11.950000, 8.245000), w=0.400)
T('GND', 'F.Cu', (70.900000, 10.650000), (70.900000, 9.648300), w=0.400)
T('GND', 'F.Cu', (70.900000, 12.300000), (71.901700, 12.300000), w=0.400)
T('GND', 'F.Cu', (67.075400, 9.648300), (67.600000, 9.648300), w=0.400)
T('GND', 'F.Cu', (63.300000, 5.300000), (62.250000, 5.300000), w=0.400)
T('GND', 'F.Cu', (8.204100, 6.490000), (9.100000, 6.490000), w=0.400)
T('GND', 'F.Cu', (78.800000, 19.430000), (77.181700, 19.430000), w=0.400)
T('GND', 'F.Cu', (24.232500, 70.470000), (24.562500, 70.800000), w=0.400)
T('GND', 'F.Cu', (63.360000, 56.450000), (63.900000, 56.990000), w=0.400)
T('GND', 'F.Cu', (64.150000, 45.196400), (64.150000, 46.100000), w=0.400)
T('GND', 'F.Cu', (57.030200, 22.068600), (48.665600, 22.068600), w=0.400)
T('GND', 'F.Cu', (70.100000, 5.300000), (69.250000, 5.300000), w=0.400)
T('GND', 'F.Cu', (64.630000, 59.090000), (63.900000, 59.090000), w=0.400)
T('GND', 'F.Cu', (23.500000, 47.980000), (23.500000, 49.750600), w=0.400)
T('GND', 'F.Cu', (88.775000, 10.500000), (88.775000, 9.515300), w=0.400)
T('GND', 'F.Cu', (74.310000, 26.280000), (74.100000, 26.490000), w=0.400)
T('GND', 'F.Cu', (63.051700, 6.350000), (63.051700, 7.200000), w=0.400)
T('GND', 'F.Cu', (65.850000, 5.300000), (65.000000, 5.300000), w=0.400)
T('GND', 'F.Cu', (24.250700, 6.724300), (24.575000, 6.400000), w=0.400)
T('GND', 'F.Cu', (55.305200, 32.844800), (54.400000, 33.750000), w=0.400)
T('GND', 'F.Cu', (64.550000, 22.700000), (64.120000, 22.270000), w=0.400)
T('GND', 'F.Cu', (68.400000, 5.300000), (67.550000, 5.300000), w=0.400)
T('GND', 'F.Cu', (70.900000, 9.648300), (71.814000, 9.648300), w=0.400)
T('GND', 'F.Cu', (52.414400, 67.948100), (52.362500, 68.000000), w=0.400)
T('GND', 'F.Cu', (58.812700, 9.124800), (58.550000, 9.387500), w=0.400)
T('GND', 'F.Cu', (86.763500, 16.783500), (85.600000, 15.619999), w=0.400)
T('GND', 'F.Cu', (65.010000, 26.800000), (65.010000, 25.600000), w=0.400)
T('GND', 'F.Cu', (80.150000, 11.360000), (80.615000, 11.360000), w=0.400)
T('GND', 'F.Cu', (56.100000, 18.378300), (57.025300, 18.378300), w=0.400)
T('GND', 'F.Cu', (70.900000, 13.950000), (70.900000, 14.951700), w=0.400)
T('GND', 'F.Cu', (58.309700, 5.552800), (58.262500, 5.600000), w=0.400)
T('GND', 'F.Cu', (85.600000, 23.240000), (85.600000, 21.824000), w=0.400)
T('GND', 'F.Cu', (63.850000, 40.940000), (63.490000, 40.940000), w=0.400)
T('GND', 'F.Cu', (47.200000, 68.350000), (46.367900, 67.517900), w=0.400)
T('GND', 'F.Cu', (35.400000, 31.750000), (35.850000, 31.750000), w=0.400)
T('GND', 'F.Cu', (56.100000, 18.378300), (49.537700, 18.378300), w=0.400)
T('GND', 'F.Cu', (38.150000, 19.850000), (37.500000, 20.500000), w=0.400)
T('GND', 'F.Cu', (74.310000, 25.300000), (74.310000, 26.280000), w=0.400)
T('GND', 'F.Cu', (83.512500, 5.350000), (83.512500, 6.330700), w=0.400)
T('GND', 'F.Cu', (71.637700, 14.951700), (70.900000, 14.951700), w=0.400)
T('GND', 'F.Cu', (16.725000, 69.885700), (16.725000, 68.900000), w=0.400)
T('GND', 'F.Cu', (66.820000, 34.670000), (66.820000, 35.727800), w=0.400)
T('GND', 'F.Cu', (66.820000, 43.157800), (66.820000, 42.290000), w=0.400)
T('GND', 'F.Cu', (56.100000, 18.378300), (56.100000, 19.300000), w=0.400)
T('GND', 'F.Cu', (78.510000, 30.900000), (78.550000, 30.860000), w=0.400)
T('GND', 'F.Cu', (9.537400, 8.347100), (9.989800, 8.799500), w=0.400)
T('GND', 'F.Cu', (76.942100, 41.732100), (77.500000, 42.290000), w=0.400)
T('GND', 'F.Cu', (74.100000, 26.490000), (74.041200, 26.548800), w=0.400)
T('GND', 'F.Cu', (63.400000, 61.450000), (60.987500, 61.450000), w=0.400)
T('GND', 'F.Cu', (42.000000, 59.108000), (42.000000, 57.875000), w=0.400)
T('GND', 'F.Cu', (65.080000, 59.500000), (66.175000, 58.405000), w=0.400)
T('GND', 'F.Cu', (87.516300, 11.666300), (88.450000, 12.600000), w=0.400)
T('GND', 'F.Cu', (63.490000, 40.940000), (62.980000, 41.450000), w=0.400)
T('GND', 'F.Cu', (73.500000, 5.300000), (72.650000, 5.300000), w=0.400)
T('GND', 'F.Cu', (48.665600, 22.068600), (46.480000, 24.254200), w=0.400)
T('GND', 'F.Cu', (62.500000, 66.450000), (62.500000, 67.409500), w=0.400)
T('GND', 'F.Cu', (26.700000, 2.925000), (25.250000, 2.925000), w=0.400)
T('GND', 'F.Cu', (67.600000, 10.650000), (67.600000, 9.648300), w=0.400)
T('GND', 'F.Cu', (85.600000, 30.860000), (85.600000, 32.280900), w=0.400)
T('GND', 'F.Cu', (64.550000, 22.700000), (64.550000, 23.965900), w=0.400)
T('GND', 'F.Cu', (62.250000, 6.350000), (63.051700, 6.350000), w=0.400)
T('GND', 'F.Cu', (81.604500, 7.470500), (82.259700, 7.470500), w=0.400)
T('GND', 'F.Cu', (67.600000, 13.950000), (69.250000, 13.950000), w=0.400)
T('GND', 'F.Cu', (53.475400, 67.948100), (52.414400, 67.948100), w=0.400)
T('GND', 'F.Cu', (62.000000, 56.450000), (61.176600, 55.626600), w=0.400)
T('GND', 'F.Cu', (75.200000, 5.300000), (74.350000, 5.300000), w=0.400)
T('GND', 'F.Cu', (72.650000, 5.300000), (71.800000, 5.300000), w=0.400)
T('GND', 'F.Cu', (60.987500, 61.450000), (60.900000, 61.537500), w=0.400)
T('GND', 'F.Cu', (68.500000, 27.990000), (67.559400, 27.049400), w=0.400)
T('GND', 'F.Cu', (66.700000, 5.300000), (65.850000, 5.300000), w=0.400)
T('GND', 'F.Cu', (76.250000, 8.050000), (77.051700, 8.050000), w=0.400)
T('GND', 'F.Cu', (85.600000, 38.480000), (85.600000, 37.053400), w=0.400)
T('GND', 'F.Cu', (78.550000, 30.860000), (78.550000, 32.582600), w=0.400)
T('GND', 'F.Cu', (78.715400, 25.151500), (77.500000, 26.366900), w=0.400)
T('GND', 'F.Cu', (76.710000, 30.900000), (76.710000, 29.700000), w=0.400)
T('GND', 'F.Cu', (61.176600, 54.473400), (61.850000, 53.800000), w=0.400)
T('GND', 'F.Cu', (72.029000, 12.427300), (71.901700, 12.300000), w=0.400)
T('GND', 'F.Cu', (61.900000, 25.837500), (62.935500, 26.873000), w=0.400)
T('GND', 'F.Cu', (80.150000, 16.410000), (80.565000, 16.410000), w=0.400)
T('GND', 'F.Cu', (78.550000, 32.582600), (78.745300, 32.777900), w=0.400)
T('GND', 'F.Cu', (81.175000, 7.900000), (81.604500, 7.470500), w=0.400)
T('GND', 'F.Cu', (9.016800, 3.525000), (8.900000, 3.525000), w=0.400)
T('GND', 'F.Cu', (64.120000, 22.270000), (64.120000, 21.000000), w=0.400)
T('GND', 'F.Cu', (41.562500, 19.850000), (38.150000, 19.850000), w=0.400)
T('GND', 'F.Cu', (14.475000, 67.500000), (14.475000, 66.085400), w=0.400)
T('GND', 'F.Cu', (47.900000, 63.962200), (47.900000, 64.790000), w=0.400)
T('GND', 'F.Cu', (59.522000, 5.552800), (58.309700, 5.552800), w=0.400)
T('GND', 'F.Cu', (22.400000, 62.950000), (22.400000, 62.850000), w=0.400)
T('GND', 'F.Cu', (86.763500, 17.089500), (86.763500, 16.783500), w=0.400)
T('GND', 'F.Cu', (76.250000, 8.900000), (75.331200, 8.900000), w=0.400)
T('GND', 'F.Cu', (25.000000, 1.726800), (25.000000, 2.675000), w=0.400)
T('GND', 'F.Cu', (59.900000, 15.600000), (59.900000, 15.487500), w=0.400)
T('GND', 'F.Cu', (70.950000, 5.300000), (70.100000, 5.300000), w=0.400)
T('GND', 'F.Cu', (64.150000, 46.100000), (64.150000, 47.000000), w=0.400)
T('GND', 'F.Cu', (84.204400, 44.704400), (85.600000, 46.100000), w=0.400)
T('GND', 'F.Cu', (62.250000, 5.300000), (62.250000, 6.350000), w=0.400)
T('GND', 'F.Cu', (76.250000, 19.300000), (77.051700, 19.300000), w=0.400)
T('GND', 'F.Cu', (46.425000, 15.265599), (46.425000, 15.100000), w=0.400)
T('GND', 'F.Cu', (75.300000, 22.990000), (76.500000, 22.990000), w=0.400)
T('GND', 'F.Cu', (77.500000, 26.366900), (77.500000, 27.050000), w=0.400)
T('GND', 'F.Cu', (64.150000, 5.300000), (63.300000, 5.300000), w=0.400)
T('GND', 'F.Cu', (62.000000, 56.450000), (63.360000, 56.450000), w=0.400)
T('GND', 'F.Cu', (8.000000, 60.875000), (8.000000, 59.982700), w=0.400)
T('GND', 'F.Cu', (23.943900, 1.414700), (22.677200, 1.414700), w=0.400)
T('GND', 'F.Cu', (59.527000, 73.492700), (58.902700, 73.492700), w=0.400)
T('GND', 'F.Cu', (66.650000, 27.420000), (67.020600, 27.049400), w=0.400)
T('GND', 'F.Cu', (76.710000, 30.900000), (78.510000, 30.900000), w=0.400)
T('GND', 'F.Cu', (77.181700, 19.430000), (77.051700, 19.300000), w=0.400)
T('GND', 'F.Cu', (76.250000, 8.900000), (77.051700, 8.900000), w=0.400)
T('GND', 'F.Cu', (61.850000, 53.800000), (61.650000, 53.600000), w=0.400)
T('GND', 'F.Cu', (63.400000, 61.450000), (64.242300, 62.292300), w=0.400)
T('GND', 'F.Cu', (9.989800, 8.799500), (11.395500, 8.799500), w=0.400)
T('GND', 'F.Cu', (65.040000, 59.500000), (65.080000, 59.500000), w=0.400)
T('GND', 'F.Cu', (28.300000, 47.189500), (28.300000, 46.055000), w=0.400)
T('GND', 'F.Cu', (74.350000, 5.300000), (73.500000, 5.300000), w=0.400)
T('GND', 'F.Cu', (46.480000, 24.254200), (46.480000, 24.500000), w=0.400)
T('GND', 'F.Cu', (66.100000, 27.420000), (66.650000, 27.420000), w=0.400)
T('GND', 'F.Cu', (74.041200, 26.548800), (73.264500, 26.548800), w=0.400)
T('GND', 'F.Cu', (81.475000, 23.150000), (81.475000, 21.713500), w=0.400)
T('GND', 'F.Cu', (41.562500, 3.250000), (35.400000, 3.250000), w=0.400)
T('GND', 'F.Cu', (77.500000, 34.670000), (77.500000, 36.103400), w=0.400)
T('GND', 'F.Cu', (59.900000, 15.487500), (58.550000, 14.137500), w=0.400)
T('GND', 'F.Cu', (75.300000, 22.990000), (74.454700, 22.144700), w=0.400)
T('GND', 'F.Cu', (64.150000, 46.100000), (66.820000, 46.100000), w=0.400)
T('GND', 'F.Cu', (22.600000, 63.150000), (22.400000, 62.950000), w=0.400)
T('GND', 'F.Cu', (23.190000, 70.470000), (24.232500, 70.470000), w=0.400)
T('GND', 'F.Cu', (51.000000, 73.000000), (52.362500, 73.000000), w=0.400)
T('GND', 'F.Cu', (2.000000, 59.993800), (2.000000, 60.875000), w=0.400)
T('GND', 'F.Cu', (65.040000, 59.500000), (64.630000, 59.090000), w=0.400)
T('GND', 'F.Cu', (75.711100, 41.732100), (76.942100, 41.732100), w=0.400)
T('GND', 'F.Cu', (64.800000, 40.940000), (63.850000, 40.940000), w=0.400)
T('GND', 'F.Cu', (61.176600, 55.626600), (61.176600, 54.473400), w=0.400)
T('GND', 'F.Cu', (66.100000, 27.420000), (65.480000, 26.800000), w=0.400)
T('GND', 'F.Cu', (58.902700, 73.492700), (58.710000, 73.300000), w=0.400)
T('GND', 'F.Cu', (77.051700, 8.900000), (77.051700, 8.050000), w=0.400)
T('GND', 'F.Cu', (19.800000, 63.337500), (19.800000, 63.200000), w=0.400)
T('GND', 'F.Cu', (67.550000, 5.300000), (66.700000, 5.300000), w=0.400)
T('GND', 'F.Cu', (57.444800, 32.844800), (55.305200, 32.844800), w=0.400)
T('GND', 'F.Cu', (67.559400, 27.049400), (67.020600, 27.049400), w=0.400)
T('GND', 'F.Cu', (69.250000, 12.300000), (70.900000, 12.300000), w=0.400)
T('GND', 'F.Cu', (65.010000, 26.800000), (64.980000, 26.800000), w=0.400)
T('GND', 'F.Cu', (42.249300, 66.950700), (42.600000, 66.600000), w=0.400)
T('GND', 'F.Cu', (45.910600, 7.601700), (46.480000, 8.171100), w=0.400)
T('GND', 'F.Cu', (38.317500, 23.837500), (37.680000, 23.200000), w=0.400)
T('GND', 'F.Cu', (67.600000, 12.300000), (69.250000, 12.300000), w=0.400)
T('GND', 'F.Cu', (61.342200, 5.406100), (61.448300, 5.300000), w=0.400)
T('GND', 'F.Cu', (60.562500, 21.850000), (61.368700, 21.043800), w=0.400)
T('GND', 'F.Cu', (35.850000, 31.750000), (37.600000, 30.000000), w=0.400)
T('GND', 'F.Cu', (80.565000, 16.410000), (81.475000, 15.500000), w=0.400)
T('GND', 'F.Cu', (22.677200, 1.414700), (22.500000, 1.237500), w=0.400)
T('GND', 'F.Cu', (25.250000, 2.925000), (25.000000, 2.675000), w=0.400)
T('GND', 'F.Cu', (42.200000, 70.837500), (42.283700, 70.921200), w=0.400)
T('GND', 'F.Cu', (58.262500, 5.600000), (54.650000, 5.600000), w=0.400)
V('GND', 27.500000, 52.500000, size=0.600, drill=0.300)
V('GND', 57.030200, 22.068600, size=0.600, drill=0.300)
V('GND', 23.483900, 6.724300, size=0.600, drill=0.300)
V('GND', 78.745300, 32.777900, size=0.600, drill=0.300)
V('GND', 61.368700, 21.043800, size=0.600, drill=0.300)
V('GND', 53.475400, 67.948100, size=0.600, drill=0.300)
V('GND', 16.725000, 69.885700, size=0.600, drill=0.300)
V('GND', 67.020600, 27.049400, size=0.600, drill=0.300)
V('GND', 12.500000, 52.500000, size=0.600, drill=0.300)
V('GND', 37.777366, 6.848300, size=0.600, drill=0.300)
V('GND', 66.820000, 35.727800, size=0.600, drill=0.300)
V('GND', 87.516300, 11.666300, size=0.600, drill=0.300)
V('GND', 2.000000, 59.993800, size=0.600, drill=0.300)
V('GND', 75.331200, 8.900000, size=0.600, drill=0.300)
V('GND', 28.300000, 47.189500, size=0.600, drill=0.300)
V('GND', 84.204400, 44.704400, size=0.600, drill=0.300)
V('GND', 42.000000, 59.108000, size=0.600, drill=0.300)
V('GND', 47.900000, 63.962200, size=0.600, drill=0.300)
V('GND', 85.600000, 37.053400, size=0.600, drill=0.300)
V('GND', 82.259700, 7.470500, size=0.600, drill=0.300)
V('GND', 71.814000, 9.648300, size=0.600, drill=0.300)
V('GND', 23.500000, 49.750600, size=0.600, drill=0.300)
V('GND', 9.716700, 4.224900, size=0.600, drill=0.300)
V('GND', 61.342200, 5.406100, size=0.600, drill=0.300)
V('GND', 86.763500, 17.089500, size=0.600, drill=0.300)
V('GND', 66.820000, 37.655000, size=0.600, drill=0.300)
V('GND', 40.781200, 66.950700, size=0.600, drill=0.300)
V('GND', 73.264500, 26.548800, size=0.600, drill=0.300)
V('GND', 72.029000, 12.427300, size=0.600, drill=0.300)
V('GND', 53.525000, 60.190000, size=0.600, drill=0.300)
V('GND', 64.550000, 23.965900, size=0.600, drill=0.300)
V('GND', 25.000000, 1.726800, size=0.600, drill=0.300)
V('GND', 23.943900, 1.414700, size=0.600, drill=0.300)
V('GND', 59.522000, 5.552800, size=0.600, drill=0.300)
V('GND', 71.743500, 15.057499, size=0.600, drill=0.300)
V('GND', 74.454700, 22.144700, size=0.600, drill=0.300)
V('GND', 59.956200, 9.124800, size=0.600, drill=0.300)
V('GND', 8.204100, 6.490000, size=0.600, drill=0.300)
V('GND', 85.600000, 32.280900, size=0.600, drill=0.300)
V('GND', 36.000000, 56.972300, size=0.600, drill=0.300)
V('GND', 57.025300, 18.378300, size=0.600, drill=0.300)
V('GND', 62.500000, 67.409500, size=0.600, drill=0.300)
V('GND', 36.192643, 11.700500, size=0.600, drill=0.300)
V('GND', 59.527000, 73.492700, size=0.600, drill=0.300)
V('GND', 43.610500, 70.921200, size=0.600, drill=0.300)
V('GND', 67.600000, 15.120400, size=0.600, drill=0.300)
V('GND', 67.075400, 9.648300, size=0.600, drill=0.300)
V('GND', 56.776978, 25.300000, size=0.600, drill=0.300)   # T-0276: C301.2 GND via up 0.16 mm (was y 25.4582) so R302.1 leaves through the north gap
V('GND', 64.242300, 62.292300, size=0.600, drill=0.300)
V('GND', 77.500000, 36.103400, size=0.600, drill=0.300)
V('GND', 85.600000, 21.824000, size=0.600, drill=0.300)
V('GND', 8.000000, 59.982700, size=0.600, drill=0.300)
V('GND', 62.935500, 26.873000, size=0.600, drill=0.300)
V('GND', 9.537400, 8.347100, size=0.600, drill=0.300)
V('GND', 14.475000, 66.085400, size=0.600, drill=0.300)
V('GND', 57.444800, 32.844800, size=0.600, drill=0.300)
V('GND', 46.367900, 67.517900, size=0.600, drill=0.300)
V('GND', 83.512500, 6.330700, size=0.600, drill=0.300)
V('GND', 66.820000, 43.157800, size=0.600, drill=0.300)
V('GND', 63.850000, 40.940000, size=0.600, drill=0.300)
V('GND', 64.150000, 45.196400, size=0.600, drill=0.300)
V('GND', 61.176600, 55.626600, size=0.600, drill=0.300)
V('GND', 75.711100, 41.732100, size=0.600, drill=0.300)
V('GND', 81.475000, 21.713500, size=0.600, drill=0.300)
V('GND', 88.775000, 9.515300, size=0.600, drill=0.300)
V('GND', 78.715400, 25.151500, size=0.600, drill=0.300)
T('Net-(D2-K)', 'F.Cu', (31.249999, 68.000000), (31.249999, 65.500000), w=0.600)
T('Net-(D3-K)', 'F.Cu', (25.100000, 58.000000), (25.100000, 58.300000), w=0.600)
T('Net-(D3-K)', 'F.Cu', (22.600000, 61.250000), (22.600000, 61.060000), w=0.600)
T('Net-(D3-K)', 'F.Cu', (25.000000, 60.700000), (25.000000, 60.725000), w=0.600)
T('Net-(D3-K)', 'F.Cu', (26.750000, 68.000000), (26.750000, 68.600000), w=0.600)
T('Net-(D3-K)', 'F.Cu', (23.600000, 68.575000), (23.600000, 68.600000), w=0.600)
T('Net-(D3-K)', 'F.Cu', (19.800000, 61.062500), (20.750000, 61.062500), w=0.600)
# T-0276 (Q-0073 step, supersedes T-0271): the ch3 links shift one gap south so the north gap (y 25.95) is free for
# R302.1 (/DEN), whose far end (the DEN lane at x 56.36, T-0276 exit) is now reachable; SW_IN3's D14.3 is walled in
# near J6 (no route), so freeing R301.1 gained nothing. U13.5 -> middle gap (y 27.3) -> R302.2 from below;
# U13.4 -> south gap (y 28.7) -> R301.2 from below. Clearances >= 0.28 mm to R301.1/R302.1/R305 and U13.3.
T('Net-(U3-SW)', 'F.Cu', (15.450000, 62.200000), (16.629900, 61.020100), w=0.500)
T('Net-(U3-SW)', 'F.Cu', (17.300000, 61.020100), (17.300000, 61.020000), w=0.500)
T('Net-(U3-SW)', 'F.Cu', (16.629900, 61.020100), (17.300000, 61.020100), w=0.500)
T('Net-(U3-SW)', 'F.Cu', (18.850000, 61.062500), (18.850000, 61.060000), w=0.500)
T('Net-(U3-SW)', 'F.Cu', (19.200000, 66.737500), (19.200000, 65.950000), w=0.500)
T('Net-(U3-SW)', 'F.Cu', (19.262500, 66.800000), (19.200000, 66.737500), w=0.500)
T('Net-(F1-Pad2)', 'F.Cu', (46.062500, 62.200000), (46.062000, 62.200000), w=0.600)
T('Net-(C22-Pad2)', 'F.Cu', (23.175000, 65.625000), (22.900000, 65.900000), w=0.600)
T('Net-(C22-Pad2)', 'F.Cu', (21.637500, 70.800000), (21.637500, 70.362500), w=0.600)
T('Net-(C22-Pad2)', 'F.Cu', (21.637500, 70.362500), (21.900000, 70.100000), w=0.600)
T('Net-(C22-Pad2)', 'F.Cu', (23.600000, 65.625000), (23.175000, 65.625000), w=0.600)
T('/Analog interface/SW_SUPPLY', 'F.Cu', (81.966400, 29.343600), (88.083600, 29.343600), w=0.600)
T('/Analog interface/SW_SUPPLY', 'F.Cu', (63.575600, 38.817500), (62.370000, 38.817500), w=0.600)
T('/Analog interface/SW_SUPPLY', 'F.Cu', (88.083600, 29.343600), (89.600000, 30.860000), w=0.600)
T('/Analog interface/SW_SUPPLY', 'F.Cu', (93.300000, 30.860000), (89.600000, 30.860000), w=0.600)
T('/Analog interface/SW_SUPPLY', 'F.Cu', (80.450000, 30.860000), (81.966400, 29.343600), w=0.600)
T('/Analog interface/SW_SUPPLY', 'F.Cu', (62.370000, 38.817500), (62.337500, 38.850000), w=0.600)
V('/Analog interface/SW_SUPPLY', 63.575600, 38.817500, size=0.600, drill=0.300)
T('/Analog interface/SW_SUPPLY', 'In2.Cu', (74.891800, 36.435100), (71.238400, 36.435100), w=0.600)
T('/Analog interface/SW_SUPPLY', 'In2.Cu', (65.701700, 36.691400), (63.575600, 38.817500), w=0.600)
T('/Analog interface/SW_SUPPLY', 'In2.Cu', (70.982100, 36.691400), (65.701700, 36.691400), w=0.600)
T('/Analog interface/SW_SUPPLY', 'In2.Cu', (86.161800, 37.998200), (76.454900, 37.998200), w=0.600)
T('/Analog interface/SW_SUPPLY', 'In2.Cu', (76.454900, 37.998200), (74.891800, 36.435100), w=0.600)
T('/Analog interface/SW_SUPPLY', 'In2.Cu', (93.300000, 30.860000), (86.161800, 37.998200), w=0.600)
T('/Analog interface/SW_SUPPLY', 'In2.Cu', (71.238400, 36.435100), (70.982100, 36.691400), w=0.600)
T('Net-(F4-Pad2)', 'F.Cu', (61.635000, 36.562500), (59.937500, 38.260000), w=0.600)
T('Net-(F4-Pad2)', 'F.Cu', (63.500000, 36.562500), (61.635000, 36.562500), w=0.600)
T('/CAN/CANH_BUS', 'F.Cu', (79.775000, 55.375000), (79.780000, 55.380000), w=0.200)
T('/CAN/CANH_BUS', 'F.Cu', (87.960000, 53.450000), (87.962500, 53.450000), w=0.200)
T('/CAN/CANH_XCVR', 'F.Cu', (76.830000, 55.870000), (76.825000, 55.865000), w=0.200)
T('/CAN/CANH_XCVR', 'F.Cu', (79.775000, 57.625000), (79.780000, 57.620000), w=0.200)
T('/CAN/CANL_XCVR', 'F.Cu', (76.825000, 57.135000), (76.830000, 57.130000), w=0.200)
T('GND_CAN', 'F.Cu', (76.825000, 58.405000), (76.825000, 59.219700), w=0.400)
T('GND_CAN', 'F.Cu', (78.430200, 62.169800), (79.750000, 60.850000), w=0.400)
T('GND_CAN', 'F.Cu', (87.589100, 71.029100), (87.960000, 71.400000), w=0.400)
T('GND_CAN', 'F.Cu', (89.837500, 54.400000), (89.837500, 55.241100), w=0.400)
T('GND_CAN', 'F.Cu', (80.094200, 67.635800), (79.180000, 68.550000), w=0.400)
T('GND_CAN', 'F.Cu', (84.233200, 71.029100), (87.589100, 71.029100), w=0.400)
T('GND_CAN', 'F.Cu', (81.055000, 51.920000), (81.900000, 51.920000), w=0.400)
T('GND_CAN', 'F.Cu', (78.281100, 62.169800), (78.430200, 62.169800), w=0.400)
T('GND_CAN', 'F.Cu', (80.475000, 52.500000), (81.055000, 51.920000), w=0.400)
V('GND_CAN', 84.233200, 71.029100, size=0.600, drill=0.300)
V('GND_CAN', 87.500000, 67.500000, size=0.600, drill=0.300)
V('GND_CAN', 89.837500, 55.241100, size=0.600, drill=0.300)
V('GND_CAN', 80.094200, 67.635800, size=0.600, drill=0.300)
V('GND_CAN', 87.500000, 72.500000, size=0.600, drill=0.300)
V('GND_CAN', 78.281100, 62.169800, size=0.600, drill=0.300)
V('GND_CAN', 76.825000, 59.219700, size=0.600, drill=0.300)
T('Net-(U5-VCC2)', 'F.Cu', (78.925000, 52.500000), (76.830000, 54.595000), w=0.400)
T('Net-(U5-VCC2)', 'F.Cu', (81.900000, 53.535100), (81.900000, 52.880000), w=0.400)
T('Net-(U5-VCC2)', 'F.Cu', (81.714300, 53.720800), (81.900000, 53.535100), w=0.400)
T('Net-(U5-VCC2)', 'F.Cu', (81.660000, 73.680000), (80.468100, 72.488100), w=0.400)
T('Net-(U5-VCC2)', 'F.Cu', (76.830000, 54.595000), (76.825000, 54.595000), w=0.400)
T('Net-(U5-VCC2)', 'F.Cu', (80.145800, 53.720800), (78.925000, 52.500000), w=0.400)
T('Net-(U5-VCC2)', 'F.Cu', (81.714300, 53.720800), (80.145800, 53.720800), w=0.400)
V('Net-(U5-VCC2)', 80.468100, 72.488100, size=0.600, drill=0.300)
V('Net-(U5-VCC2)', 81.714300, 53.720800, size=0.600, drill=0.300)
T('Net-(U5-VCC2)', 'B.Cu', (81.714300, 71.241900), (80.468100, 72.488100), w=0.400)
T('Net-(U5-VCC2)', 'B.Cu', (81.714300, 53.720800), (81.714300, 71.241900), w=0.400)
# T-0271 (Q-0073 step): U12.5 -> R202.2 through the middle gap (y 11.3) between R202 and R201, into R202.2 from below;
# the north gap (y 9.9) is then free for R202.1 (/DEN) to leave toward U1 (was the wrap above R202).
T('/OUT1', 'F.Cu', (25.775000, 12.300000), (25.775000, 12.500000), w=0.600)
T('Net-(J3-CC1)', 'F.Cu', (16.450000, 8.240000), (16.450000, 8.245000), w=0.200)
T('/USB_DP', 'F.Cu', (14.450000, 8.245000), (14.450000, 8.240000), w=0.200)
T('/USB_DP', 'F.Cu', (15.450000, 8.245000), (15.450000, 8.240000), w=0.200)
T('Net-(D11-K)', 'F.Cu', (79.180000, 70.450000), (79.051300, 70.450000), w=0.600)
T('Net-(D11-K)', 'F.Cu', (77.825900, 69.224600), (77.825900, 67.674100), w=0.600)
T('Net-(D11-K)', 'F.Cu', (77.825900, 67.674100), (79.100000, 66.400000), w=0.600)
T('Net-(D11-K)', 'F.Cu', (80.330000, 70.450000), (81.660000, 69.120000), w=0.600)
T('Net-(D11-K)', 'F.Cu', (79.180000, 70.450000), (80.330000, 70.450000), w=0.600)
T('Net-(D11-K)', 'F.Cu', (79.051300, 70.450000), (77.825900, 69.224600), w=0.600)
T('Net-(J4-Pin_2)', 'F.Cu', (93.300000, 60.090000), (91.397500, 60.090000), w=0.600)
T('Net-(J4-Pin_2)', 'F.Cu', (91.397500, 60.090000), (90.637500, 60.850000), w=0.600)
T('Net-(F3-Pad1)', 'F.Cu', (90.512500, 65.000000), (86.362500, 60.850000), w=0.600)
T('Net-(F3-Pad1)', 'F.Cu', (90.562500, 65.000000), (90.512500, 65.000000), w=0.600)

# ---- maze_route.py routes (T-0246 group 1: short local links, Q3-Q6 block, U1 IO, IO2-IO5, SW_IN lanes, J3 VBUS/D3-A), on the
# T-0236 copper above; geom_export.py on the board, then maze_route.py geo.json <nets> (order as listed below).
T('/Analog interface/SW_SUPPLY', 'In2.Cu', (65.90, 36.30), (65.90, 36.20))
V('/Analog interface/SW_SUPPLY', 65.90, 36.20)
T('/Analog interface/SW_SUPPLY', 'F.Cu', (65.90, 36.20), (65.90, 35.70), (66.00, 35.60), (66.00, 34.40), (66.20, 34.20), (66.20, 34.10), (66.90, 33.40), (67.40, 33.40), (67.50, 33.30), (67.60, 33.30), (68.50, 32.40), (68.50, 32.30), (68.60, 32.20), (68.60, 32.10), (69.40, 31.30))

# ---- T-0253 (T-0250/T-0251): maze legs that stopped up to 0.1 mm outside their own pad (maze_route.py took goal
# cells from the rasterised copper edge) are finished with one segment into the pad. The rest of the dangling
# maze/harvest copper is removed by routing_build.py prune() in finish(). +3V3 maze copper above is 0.3 mm (v3 class).

# ---- T-0259 maze pass 1 (merge-fixed maze_route.py: later legs start from the copper already laid). Board export,
# all open signal nets; 0.1 mm no-op legs onto connected fragments dropped.

# ---- T-0259 placement move (Q-0073, decision 184): ch1/ch4 signal parts. R101/R102 (R401/R402) turn 180 deg, so the
# PROFET-side pad faces its U11/U14 pin (straight link) and the SW_IN/DEN pad faces east toward U1; R103/R107
# (R403/R407) turn to 270 deg, so their IS pads sit on top next to R104 (R404) and the IS track no longer runs down
# x 38.9 across the pocket. That frees x 38-39.4 east of the SW_IN/DEN pads for vias to the In2 corridor.
# routing_build.prep() applies PLACE, then deletes the board copper of DROP_NETS and the DROP_GND segments (they ended
# on the old top GND pads) before the fixed routes go in, so the build reproduces the move.
PLACE = {'R101': (37.2, 9.2, 180), 'R102': (37.2, 7.93, 180), 'R103': (40.3, 8.7, 270), 'R107': (42.9, 8.7, 270),
         'R401': (37.2, 25.8, 180), 'R402': (37.2, 24.53, 180), 'R403': (40.3, 25.3, 270), 'R407': (42.9, 25.3, 270)}
DROP_NETS = {'Net-(U11-IN)', 'Net-(U11-DEN)', 'Net-(U11-IS)', 'Net-(U14-IN)', 'Net-(U14-DEN)', 'Net-(U14-IS)',
             '/DEN', 'Net-(U12-DEN)', 'Net-(U13-IN)', 'Net-(U13-DEN)'}   # T-0271: U12 DEN and U13 IN links rerouted; T-0266: all /DEN copper is in this file (T-0259 maze pass 2 block)
DROP_GND_VIAS = [(56.776978, 25.4582)]   # T-0276: old C301.2 GND via, moved to y 25.30
DROP_GND = [  # (layer, (x1, y1), (x2, y2)) of the removed GND segments
    ('F.Cu', (40.300000, 23.837500), (38.317500, 23.837500)),
    ('F.Cu', (40.300000, 7.237500), (42.900000, 7.237500)),
    ('F.Cu', (42.900000, 7.237500), (43.264200, 7.601700)),
    ('F.Cu', (42.900000, 23.837500), (40.300000, 23.837500)),
    ('F.Cu', (43.264200, 7.601700), (45.910600, 7.601700)),]
T('GND', 'F.Cu', (40.30, 10.1625), (42.90, 10.1625), (42.90, 11.60), w=0.4)      # R103.2, R107.2 -> GND via
V('GND', 42.90, 11.60)
T('GND', 'F.Cu', (40.30, 26.7625), (42.90, 26.7625), (42.90, 28.20), w=0.4)      # R403.2, R407.2 -> GND via
V('GND', 42.90, 28.20)

# ---- T-0259 maze pass 2 (after the placement move; re-seeding maze_route.py): DEN R102.1 <-> R402.1 and local IO2/IO5 joins.
# T-0266 (T-0264): the via sat on pad R402.1; moved to (38.60, 25.42): 0.54 mm off R402.1, 0.32 mm off R401.1, 1.0 mm off
# R403.1, so the GND-F neck between R402.1 and R403.1 stays open (a via at 38.80/24.95 cut off a GND-F island). One
# 45-degree F.Cu link back to the pad. '/DEN' is in DROP_NETS so the build drops the old on-pad via and stub.

# ---- T-0271 (T-0218, Q-0073 two-way step): escape from R202.1 (/DEN) through the gap that the
# rerouted U12-DEN and U13-IN links left free (the 0.77 mm gap is below the maze grid's resolution, so these stubs are drawn
# by hand; clearances >= 0.25 mm checked against C201/C301, R202/R302, R203.2 and the U13-IS loop).
# R301.1 (/SW_IN3) is open through the south gap now, but no route to D14.3 was found (maze pass 1); its stub stays
# out of this file until one is, so no dangling copper is built.
# U1.28 (/DEN) is boxed on F by its row neighbours and the Q3-B track under the bottom row (y 20.35); it leaves north,
# past the IO35 fan-out via, to a via under the module (In2 IO40 0.23 mm, B Q3-C 0.24 mm), so Q3-B stays as it is.
# T-0271 maze pass 1 (maze_route.py on the build base with the stubs above): R202.1 stub -> U1.28 stub, In2 under U1
# (GND-In2 side, outside VS-In2; In1 stays the solid reference).
# The In2 drop sits at (59.40, 10.60), right after the stub: with the maze's F leg on to (60.90, 10.50) the GND-F
# fill around C201.2/R203.2 lost its link past the U1 pad column (GND-F 37 -> 38 islands).

# ---- T-0276 (Q-0075): the marked In2 exit. Three west-pocket runs cross the VS-In2 east edge at y 15.7-17.9 (notch
# VS_IN2_NOTCH) into a via column at x 56.45 (B spine edge x 55.0 + 1.0 zone clearance + 0.3 via radius = 56.3; on F
# the only free stretch at x 56.3-57 is y 15.3-17.7, between the D201-A via and the GND track at y 18.38). Column top
# to bottom: DEN, IO2, IO5, in the order the runs arrive from the pocket, so no In2 run crosses another. In2 runs keep
# out of the U12 thermal-via field (box x 49.4-52.6, y 8.4-15.2). East of the column on B: DEN north along x 56.36
# (0.25 mm off the D201-A via, 1.26 mm off the spine) and east between the U12-IS vias at y 12.1 to its In2 drop at
# (59.40, 10.60); IO2 and IO5 east under the U12-IS via (57.70, 16.50) at y 17.15 / 17.60 and north at x 58.33 / 58.78
# to F vias at (60.20, 12.80) / (60.20, 14.00); the F legs to U1.6 / U1.9 are maze_route.py legs.
# DEN: pocket via (42.20, 8.90) -> In2 north-east of the IO2 via -> column top
# R302.1 (/DEN, ch3): north gap -> via (57.45, 25.95) between R302.2, the U13-IS loop (0.24 mm) and R303.2 -> B north,
# east of the moved C301.2 GND via, then x 56.36 (0.27 mm off the GND vias at x 57.03, 1.26 mm off the spine) into
# the DEN column via (56.45, 15.70).
# (T-0281: the R302.1 B lane along x 56.36 into the column is replaced; see the T-0281 block at the end.)

# ---- T-0276 maze pass 1 (geometry exported from the T-0276 DEN build), /SW4 legs only: R41.1 cluster -> the SW4 copper
# by J6 on B (y 72.7-73.3) and a short F join at (66.3, 38.9). The pass's +3V3 legs (B under U1, y 5.4-20) were not
# kept: they split GND-B 19 -> 24 islands; the /IO7 and /NTC legs gained nothing; the other /SW4 legs were pruned.

# ---- T-0281 (Q-0076, decision 206): IO2 and IO5 through the marked exit. Column vias at x 56.50: IO2 y 16.60, IO5
# y 17.50 (DEN keeps 15.70; 0.9 mm pitch; IO5 0.38 mm off the GND track at y 18.38 and the GND via (57.0, 18.35)).
# VS_IN2_NOTCH grows to y 18.3 for them (decision 199: only as much as the runs need). East of the column on B, nested:
# IO2 under the U12-IS via (57.70, 16.50) at y 17.10, north at x 58.40 (0.3 mm off the U12-IS via at (57.70, 13.0)),
# east at y 12.80 to an F via (60.20, 12.80); IO5 at y 17.55, north at x 58.85, east at y 14.00 to (60.20, 14.00).
# The pocket legs (F from D102.3 / D402.3, pocket via, In2 to the column) and the F legs to U1.6 / U1.9 are
# maze_route.py legs. These runs split GND-F/GND-B; the new fragments are stitched to GND-In1 by >= 2 vias
# (routing_build.gnd_fragments, Q-0076).
# R302.1 (/DEN, ch3) is open again (1 unconnected): its B lane into the column is gone (the IO2/IO5 column sits there),
# and the only other way, an In2 leg down from the DEN drop via (59.40, 10.60) under U1, isolates the GND-In2 under U1
# (x 59-73, y 11-26, 78 mm2): that area joins the rest of GND-In2 only through the x 59-60 strip west of the drop
# (T-0281 builds b2/b4/b5: GND-In2 18 -> 19). No F/B path exists (IO5/GND via/IO4 wall at y 14-17). Tried copper:
#   # R302.1 (/DEN, ch3): the north-gap stub and via (57.45, 25.95) stay (T-0276); its B lane into the column is gone (the
#   # IO2/IO5 column sits there). It now joins the DEN In2 drop via (59.40, 10.60) under U1: In2 south along x 59.15
#   # (0.25 mm off the D201-A In2 track at x 58.7 and the GND via (59.9, 15.6)) to a via (59.45, 16.90), B to (59.60, 18.10),
#   # maze B leg south-west to the R302.1 via. The In2 leg leaves from the drop via itself and ends 1.6 mm above the USB
#   # In2 pair (y 19), so GND-In2 flows round both ends (a leg from the DEN run at x 62.2, or one ending at y 18.1 beside
#   # the USB pair, cut off the GND-In2 under U1: 18 -> 19 islands, T-0281 builds b2/b4).
#   T('/DEN', 'F.Cu', (55.69, 26.60), (55.69, 25.95), (57.45, 25.95))
#   V('/DEN', 57.45, 25.95)
#   T('/DEN', 'In2.Cu', (59.40, 10.60), (59.15, 10.85), (59.15, 16.40), (59.45, 16.70), (59.45, 16.90))
#   V('/DEN', 59.45, 16.90)
#   T('/DEN', 'B.Cu', (59.45, 16.90), (59.60, 17.05), (59.60, 18.10))
#   T('/DEN', 'B.Cu', (59.60, 18.10), (59.60, 21.40), (59.50, 21.50), (59.50, 21.60), (59.40, 21.70), (59.40, 21.80), (59.30, 21.90), (59.30, 22.00), (59.20, 22.10), (59.20, 22.20), (59.10, 22.30), (59.10, 22.50), (59.00, 22.60), (59.00, 22.70), (58.90, 22.80), (58.90, 22.90), (58.80, 23.00), (58.80, 23.10), (58.70, 23.20), (58.70, 23.30), (58.60, 23.40), (58.60, 23.60), (58.50, 23.70), (58.50, 23.80), (58.40, 23.90), (58.40, 24.00), (58.30, 24.10), (58.30, 24.20), (58.20, 24.30), (58.20, 24.40), (58.10, 24.50), (58.10, 24.70), (58.00, 24.80), (58.00, 24.90), (57.90, 25.00), (57.90, 25.10), (57.80, 25.20), (57.80, 25.30), (57.40, 25.70))

# ---- T-0281 maze pass (geometry of build b3): +3V3 legs (5 -> 1 unconnected). They run on B under U1 and split GND-B;
# Q-0076: the new GND-B fragments are kept only when stitched to GND-In1 by >= 2 vias (routing_build.gnd_fragments).

# ---- Decision 214 (owner, 2026-11-15): targeted rip-up. A net in REROUTED_NETS keeps only the copper this file lists
# (routing_build.prep drops the rest of its board copper); scripts/ripup.py removes a few movable nets that block an
# open link, routes the link first and then the removed nets again, and keeps the change only when fewer items stay open.
REROUTED_NETS = ['+3V3', '/Analog interface/SWIN1', '/Analog interface/SWIN2', '/Analog interface/SWIN3', '/Analog interface/SWIN4', '/EN', '/IO11', '/IO7', '/IO8', '/MOD_ID', '/SW1', '/SW2', '/SW2_IO', '/SW3_IO', '/SW4', '/VBAT_SENSE', 'Net-(Q5-E)', 'Net-(Q6-B)']

# R60.2 (/VBAT_SENSE) escape: R60.2 lies just outside the VS-F-drain outline (x 58.3) but inside the router's
# zone-clearance ring round it, so no router leg can leave the pad. A straight stub east to x 59.6 is never nearer the
# pour than the pad itself (the fill keeps its 1.0 mm from both); the router starts from its end.
KEEP_TRACKS = [('/VBAT_SENSE', (58.81, 41.40), (59.60, 41.40))]   # routing_build.prune never removes these

# ---- Decision 214 maze pass 1 (hole keep-out from the drill, UUID clusters, margin 0.08, R60.2 stub; open nets)

# ---- Decision 214 rip-up: Net-(Q5-E) (with Net-(Q6-B)), open clusters 1 -> 0

# ---- Decision 214 part move (owner, 2026-11-16; allowed by decision 212 (1)): the west divider block sat behind J6 and the
# VS block, so every one of its links had to cross the J6 pin gaps. The SWIN2-4 load pairs (R4/R46, R7/R47, R8/R48;
# their midpoints join nothing else) go next to the SWIN rows by D16-D19; the switch/IO resistors R1, R2, R31, R33, R38
# go to the strip x 65-67 west of the CAN barrier, next to the switch column. D23 stays (no SOD-123 spot east; SW4
# is routed). Old copper of the moved pads is pruned by the build (dangling); the midpoint nets are dropped.
PLACE.update({'R4': (76.42, 45.77, 0), 'R46': (81.37, 45.77, 0), 'R7': (76.42, 38.57, 0), 'R47': (81.37, 38.57, 0), 'R8': (85.62, 34.67, 0), 'R48': (85.62, 42.52, 0), 'R38': (65.36, 62.98, 90), 'R31': (66.66, 62.98, 90), 'R1': (65.71, 65.22, 90), 'R2': (65.71, 67.42, 90), 'R33': (65.71, 69.62, 90)})
DROP_NETS |= {'Net-(R4-Pad2)', 'Net-(R47-Pad1)', 'Net-(R48-Pad1)'}

# ---- Decision 214 rip-up: part move (with +3V3, /Analog interface/SWIN1, /Analog interface/SWIN2, /Analog interface/SWIN3, /Analog interface/SWIN4, /EN, /IO7, /IO8, /MOD_ID, /SW1, /SW2, /SW2_IO, /SW3_IO, /SW4, /VBAT_SENSE), open clusters 0 -> 0

# R2.1 (GND) after the part move sits in an unfilled pocket of the strip: tie it to GND-In1 by a via east of the pad
# (x 66.85 stays clear of the CAN barrier keep-out at x 67.5)
T('GND', 'F.Cu', (65.71, 67.92), (66.85, 67.92), w=0.4)
V('GND', 66.85, 67.92)

# ---- Decision 214 rip-up: part move (with +3V3, /Analog interface/SWIN1, /Analog interface/SWIN3, /SW3_IO), open clusters 0 -> 0

# ---- Decision 214 rip-up: part move (with /Analog interface/SWIN3, /SW3_IO), open clusters 0 -> 0


# ---- Decision 214 maze pass 2 (after the part move; all open signal nets, pruned geometry)

# ---- Decision 214 rip-up: +3V3 (with /SW4), open clusters 2 -> 1

# ---- Decision 214 rip-up: part move (with /SW4), open clusters 0 -> 0

# ---- Decision 214 rip-up: /IO11 (with /IO8), open clusters 2 -> 1


REROUTED_NETS = sorted(set(REROUTED_NETS) | {CC1, CH})   # decision 215: CC1 via moved; EMC E23: CANH flow-through via D9.1;
# the board keeps only the copper above for these nets

# ---- Decision 215 (owner, 2026-11-16): one-pass signal routing. scripts/pf_routes.json (written by pf_land.py from a
# pf_export.py + pf_route.py run) holds the part moves and all copper of the routed nets: every signal net except the
# CAN and USB pairs and J3 CC1, plus the two local J3 power links. For those nets every T()/V() entry above this
# point is dropped (the Freerouting harvest, the maze passes, the J6 In2 bundle, the hand steps); only the file's
# copper is built. REROUTED_NETS makes routing_build.prep drop their old board copper too.
import json as _json, os as _os
_pfp = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'pf_routes.json')
if _os.path.exists(_pfp):
    _pf = _json.load(open(_pfp))
    _rip = set(_pf['nets'])
    TRACKS[:] = [_t for _t in TRACKS if _t['net'] not in _rip]
    VIAS[:] = [_v for _v in VIAS if _v['net'] not in _rip]
    for _t in _pf['tracks']:
        T(_t['net'], _t['layer'], *[tuple(_p) for _p in _t['pts']], w=_t['width'])
    for _v in _pf['vias']:
        V(_v['net'], _v['at'][0], _v['at'][1], size=_v['size'], drill=_v['drill'])
    PLACE.update({_k: tuple(_x) for _k, _x in _pf['place'].items()})
    REROUTED_NETS = sorted(set(REROUTED_NETS) | _rip)
    DROP_GND += [(_l, tuple(_a), tuple(_e)) for _l, _a, _e in _pf['drop_gnd']]
    DROP_GND_VIAS += [tuple(_p) for _p in _pf['drop_gnd_vias']]
    # the same GND copper is also listed above as fixed lines (harvest, maze passes): drop those segments and vias too,
    # else add_fixed puts them back on the turned parts' pads (matched to 1 um)
    _um = lambda _p: (round(_p[0] * 1000), round(_p[1] * 1000))
    _dseg = {(_l, *sorted([_um(_a), _um(_e)])) for _l, _a, _e in _pf['drop_gnd']}
    _dvia = [_um(_p) for _p in _pf['drop_gnd_vias']]
    _keep = []
    for _t in TRACKS:
        if _t['net'] != 'GND':
            _keep.append(_t); continue
        _run = [_t['pts'][0]]
        for _a, _e in zip(_t['pts'], _t['pts'][1:]):
            if (_t['layer'], *sorted([_um(_a), _um(_e)])) in _dseg:
                if len(_run) > 1:
                    _keep.append(dict(_t, pts=_run))
                _run = [_e]
            else:
                _run.append(_e)
        if len(_run) > 1:
            _keep.append(dict(_t, pts=_run))
    TRACKS[:] = _keep
    VIAS[:] = [_v for _v in VIAS if _v['net'] != 'GND' or
               not any(abs(_um(_v['at'])[0] - _q[0]) <= 2 and abs(_um(_v['at'])[1] - _q[1]) <= 2 for _q in _dvia)]
