# Quilter trial – handoff (pdm-4ch, 2026-11-14)

**Status 2026-11-17 (owner):** pdm-4ch is fully routed by other means (decision 219), so no Quilter copper is needed
on it and trial 3 needs no follow-up. This file and `hardware/pdm-4ch/scripts/quilter_export.py` are **kept on
purpose**: the owner wants to try Quilter on `pdm-hc2` when its layout starts. What to carry over from the three
trials below:
- Give Quilter the placement too. On pdm-4ch it got every part and 2000 tracks locked, and only the leftover links.
- It has no isolation or creepage rule and reads only board-wide minimums: every such rule goes in as a keep-out,
  one zone per outline (KiCad saves only a zone's first outline).
- It routes at the board minimum and does not honour Net Widths reliably: set the minimum to the narrowest track
  wanted (0.2 mm), and check widths on import.
- Its candidates are checked like any other copper: `docs/ARCHITECTURE.md`, "PCB layout rules", and KiCad DRC.
- The "What blocks the last 37" analysis below is superseded: no pad was sealed; see decision 215 and
  `hardware/pdm-4ch/STATUS.md`.

Owner's idea: try Quilter's free tier (AI place-and-route) on the 37 open pdm-4ch connections. Decision 213. The routing
method of decisions 163/181 and the decision-212 work (moving the ch2/ch3 resistor blocks) go on unchanged. Taking
Quilter copper into the board amends 163/181 and needs the owner's ruling.

## State

- **Done:** `hardware/pdm-4ch/scripts/quilter_export.py` writes a locked upload copy plus `UPLOAD.md` (step-by-step
  upload settings, preserved pours, net widths, the 37 open items). Last export: `~/Downloads/pdm-4ch-quilter-upload`,
  DRC 0 errors, parity 0, 37 unconnected. Repo board unchanged (0 errors, 37 unconnected).
- **Uploaded and submitted 2026-11-14 22:08** (Quilter UI/API 1.51, project "pdm-4ch trial", job
  `6af8bcc35e1a5ebf382790ec`, Full layout): the seven files from the 21:30 export (unchanged since; copied to a
  scratch folder only because the browser upload cannot read `~/Downloads`). KiCad 10 parsed. Settings as in
  `UPLOAD.md`: stackup from the file with "Preserve copper on internal layers" on; minimums 0.15/0.2/0.5/0.3 mm,
  margin 0.5 mm read from the file; USB diff pair, 72 bypass entries removed (no crystals/converters detected);
  power pour off on all 5 power nets; GND primary; 20 preserved pours; 12 net-width rows (4 nets x F/In2/B).
  Review page: 226 parts, 0 to place, 237 pins to route. Preview showed the keep-outs (antenna, holes, CAN barrier
  L-band, edge band, pour keep-outs). `UPLOAD.md` text in `quilter_export.py` updated for the 1.51 wizard (internal
  copper toggle, Floorplan "Optimize", per-layer net widths, pre-filled pour list).
- **Not done:** no candidate yet (Quilter emails when ready). The import step (`quilter_import.py`) is not written.
- Commits: 9ceed23 (export, decision 213), 0447e22 (CAN barrier, physics constraints), faf4efc (pour keep-outs,
  minimums, net widths; `routing_build.pour_keepout()` extracted from `prep`, output verified identical).

Regenerate the upload folder (KiCad closed, from the repo root):
```
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 -I \
  hardware/pdm-4ch/scripts/quilter_export.py ~/Downloads/pdm-4ch-quilter-upload
```

## What the export does, and why

| Change in the copy | Reason (Quilter docs) |
|---|---|
| All parts, tracks, vias, zones locked; dangling signal copper pruned (`routing_build.prune`, found none) | Parts inside the outline and pre-routed copper are never changed; orphan segments are not deleted and would block |
| In1.Cu user name `GND` | Plane layers are detected by the names "ground"/"gnd", "power"/"pwr" |
| Rule area: no tracks on In1 | Build rule (decision 165), not in the board file |
| Rule area: no tracks/vias on In1/In2 under the antenna | The module's own keep-out covers F/B only |
| The build's router keep-outs on all layers: `antenna`, `can-barrier`, `can-barrier-top`, `jp30`, `jp1`, `edge0-3` | Quilter has **no isolation/creepage rule**; the two barrier bands seal the GND_CAN side |
| `pour-<name>` keep-out over each of the 15 power pours (`routing_build.pour_keepout`) | A preserved pour keeps its fill, not its outline; tracks in the voids would be cut by our refill (decision 164). VS-In2: only thermal-via fields + edge band, exit window open (decisions 172/176/199) |
| Holes round fixed copper inside those keep-outs (`routing_build.clear_fixed`, 232); zone fills allowed in them | Otherwise the existing copper and pours violate the keep-outs (13 DRC errors) |
| Board minimums: clearance 0.2 mm, track 0.15 mm (repo board: 0 / 0) | Quilter reads only the board-wide minimums as absolute limits, not net classes. 0.15 because a locked CANL_XCVR neck at a pad is 0.15 mm |
| Preserve list: all VS/VBAT/OUT pours, GND-In1, GND_CAN-F/B/In1/In2. Not: GND-F, GND-B, GND-In2 | Only pours ticked in the "Preserved pours" table survive; leaving outer GND free lets Quilter route through it (our build refills GND) |
| `UPLOAD.md` Net Widths: +3V3 0.3, GND 0.4, Net-(D3-A) 0.4, Net-(F2-Pad1) 0.4 mm | Open nets whose build class (`fixed_routes.CLASSES`) is > 0.2 mm; docs say use Net Widths sparingly |

UI settings (all in `UPLOAD.md`): upload files one by one (no zip); stackup **and** fabricator profile from the input
file (a stock stackup deletes the inner-layer copper, and the In2 routes live there); untick "power pour" on every net;
remove detected differential pairs, bypass-cap, crystal and switching-converter entries; no impedance or placement
regions; check the "Pours" preview layer.

## Quilter facts (docs read via the `quilter` MCP: getPage)

Read in full: design-parameters (overview, fabricators, stackups, fabricator constraints, pre-placed components,
placement regions, single-sided placement, pre-routed traces, preserved pours, keepouts, net widths) and
physics-constraints (overview, power nets, single-ended impedance, differential pairs, timing-sensitive, bypass
capacitors, crystal oscillators, switching converters), plus upload / prepare input / submit / download pages.

- Inputs: board (required), schematic(s), project. No zip. Output comes back in the same format, several
  candidates; 15 min to 24 h.
- Pre-placed parts and pre-routed traces/vias are never changed; incomplete pre-routed segments get finished.
- Inner-layer copper and pours are deleted unless the stackup from the input file is used.
- Pours: kept only if named (KiCad) and ticked in "Preserved pours"; auto-preserving locked pours is "near future".
- Fabricator constraints from the file: min trace, clearance, drill, annular ring, edge clearance only.
- Power nets: detected by name or a "Power" netclass; default 200 mA (< 3 V) / 500 mA (> 3 V); IPC width calculation
  per stackup.
- Differential pairs: netclass `differentialpair` plus a suffix (+/-, P/N, P/M, A/B, t/c); H/L (CAN) not detected;
  only 100/85 ohm.
- Bypass caps, crystals and buck converters are placement constraints; placement regions are KiCad rule areas with
  every keep-out item unticked (ours all have some ticked, so they stay keep-outs).
- Free tier: personal, academic and eligible exploratory R&D (< 10 people, < 50 k$ revenue); input files may be used
  for training; Terms restrict sharing Output with third parties. **Check that before Quilter copper goes into the
  MIT repo.**

**Asked with the MCP's `askQuestion` (2026-11-14), answers checked against the cited pages:**
1. KiCad 10 file support (format 20260206): **not documented.** The docs say only "KiCad"; the CAD compatibility
   overview page is a stub. Only the upload can tell; `UPLOAD.md` says to stop and note it if the parser refuses.
2. Pre-routed copper that breaks the minimums, keep-outs with holes or over copper: **not documented.** Moot for the
   minimums: the export copy passes DRC with clearance 0.2 / track 0.15 mm (0 errors besides the 37 unconnected).
   The holed keep-outs stay a risk only the upload shows (watch for refused or ignored keep-outs in the preview).
3. Fully routed nets / widening narrow locked tracks: Quilter routes what is "not already routed" and never changes
   a pre-routed trace's path or position; **whether it may change a locked track's width is not documented.**
   Consequence for the import: match locked copper by net, layer and endpoints and ignore width, and keep our own
   widths; take only geometry that is new.
4. Placement constraints vs pre-placed parts: **answered.** Pre-placed parts are never moved or rotated, even if the
   layout then cannot complete. `UPLOAD.md` still says to remove the bypass/crystal/converter entries (they would
   only add failing checks).
5. Net Widths vs Power Nets: **precedence not documented**; Net Widths "are not always respected". Net Widths are
   checked by the Invalid Width Span PRC (±10 % of nominal). The import gate (reject tracks narrower than their
   `fixed_routes.CLASSES` width) already covers this; `UPLOAD.md` now says so.

Docs bugs seen (could go to the MCP's `sendFeedback`, ask the owner first; not sent): net-widths page "How to
specify" says "To specify a preserved pour"; the CAD compatibility overview page is a two-line stub ("overview of
status", "link to view/vote on cad tool support") and no page lists supported KiCad versions.

## Candidates (first look, 2026-11-15)

Two candidates, 1_1 and 1_2 (board + stripped project file each), kept outside the repo in the owner's downloads.
Checked in a scratch copy only; nothing is imported.

- Output format: space-indented; locked copper keeps its UUIDs; new tracks/vias have **no UUID** (KiCad assigns
  fresh ones on load), so "new" = any track/via whose UUID is not in the export copy. GND-F/B/In2 are dropped (66 ->
  63 zones), so raw unconnected counts include GND links our build's refill restores.
- Both: all 2000 locked tracks/vias kept, none changed; nothing new on In1.
- **1_2: out.** 491 new items; after refill still 6 shorts, 4 track crossings, 47 keep-out violations, 18
  copper-to-edge, 50 clearance errors.
- **1_1: clean but too narrow.** 595 new items (342 F.Cu, 110 B.Cu, 94 In2, 49 vias). Raw DRC 361 errors; after a
  zone refill only the 199 track-width errors remain (no clearance, no keep-out, no short). New signal tracks are
  0.150 mm (the board minimum we gave it), +3V3 0.158 mm: the 0.3 mm Net Width was ignored. Only the 0.4 mm widths
  (GND, D3-A, F2) were kept. Widening every new track to its class (0.2; +3V3 0.3) and refilling leaves 44 errors
  (32 clearance, 11 keep-out, 1 old width) spread over ~15 net pairs.
- Lesson: Quilter routes at the board-wide minimum and does not honour Net Widths reliably. The 0.15 mm board
  minimum (chosen for the locked CANL_XCVR neck, `fixed_routes.py` line 89) is what made the candidates too narrow.

## Trial 2 (submitted 2026-11-15 09:03)

Owner: rerun with a 0.2 mm board track minimum. `quilter_export.py` now sets track min = clearance min = 0.2 mm
(`MIN_MM`); the copy has 1 DRC error, the locked 0.15 mm CANL_XCVR neck, and 37 unconnected (parity: only the
FL30 DNP warning, as before). Quilter parsed it without complaint and showed trace min 0.2 mm. Same settings as
trial 1. Job "pdm-4ch trial 2 (min track 0.2)", `6af9577205fb4066882662d9`, in the same project. Download the
candidates to a new folder (e.g. `~/Downloads/pdm-4ch-quilter-candidates-2/`), outside the repo.

First candidate (1_2, downloaded 2026-11-15 12:46 while the router was at 14/18 steps; Quilter showed 96 % routed,
15 incomplete nets, 206 padstack collisions, 9 boundary violations). Locked copper intact (2000 kept, 0 gone); 710
new items, none on In1. Widths: 347 at 0.2 mm, 266 at 0.4 mm (GND, Net-(D3-A), Net-(F2-Pad1) Net Widths honoured), 2
at 0.32 mm. After a zone refill: 18 unconnected (from 37), but 27 shorts (+3V3–GND, VS–GND, IO17/IO39/IO0/SW4–GND,
signal–signal), 10 tracks_crossing, 43 keep-out hits (36 GND), 98 clearance, 6 hole clearance, 2 copper-to-edge, 7
mask bridges. Not usable; wait for the finished candidates.

## Next steps

1. Done: open points asked (see above); `UPLOAD.md` updated, upload folder regenerated (37 unconnected, DRC errors
   only the 37 unconnected, same warnings as the repo board plus the 9 `lib_footprint_issues`).
2. Done: uploaded and submitted (job `6af8bcc35e1a5ebf382790ec`). Next: when Quilter's email arrives, download the
   best candidates (fewest unrouted) as KiCad files into one folder.
3. Write `hardware/pdm-4ch/scripts/quilter_import.py`: load candidate and export copy, take only new tracks/vias
   (geometric diff against the locked copper by net, layer and endpoints, ignoring width; ignore Quilter pours
   and its stackup edits), reject tracks narrower
   than their net's `fixed_routes.CLASSES` width or on In1, emit them as a generated block for `fixed_routes.py`.
4. Run `hardware/pdm-4ch/scripts/build_routing.sh`; accept only with 0 DRC errors, parity 0, fewer unconnected,
   pour gates (decisions 166, 172, 212), GND fragments with >= 2 ties, VS-In2 one island >= 1012.1 mm² with 40/40
   thermal vias, heat budget at 40 °C (`tools/heat_budget.py`).
5. If it wins: owner ruling to amend decisions 163/181, then land.

## Gotchas from this session

- MCP servers added mid-session do not appear as tools; start a new session. In the old session the server was used
  through plain JSON-RPC over HTTP (initialize, notifications/initialized, tools/call with the `Mcp-Session-Id`
  header).
- In a worktree session, any Bash command containing the substring "git" (even the `~gitbook` URL) is refused as a
  complex git command: keep git commands plain and separate, and put such URLs in a script file.
- KiCad tools: Python `/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3`
  (run with `-I`), CLI `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli` (not on PATH).
- `routing_build.prep` writes segments in a different order each run: compare outputs as sorted lines.
- The export's 9 extra `lib_footprint_issues` warnings come from the copied `fp-lib-table` pointing at `../../lib`;
  harmless (footprints are embedded in the board).

## What blocks the last 37 (analysis 2026-11-15, corrected)

A first pass (0.2 mm clearance to everything, vias allowed in pads) said "22 of 34 blocked, 32 free with all tracks
removed". Wrong: it allowed via-in-pad and ignored the router's real rules. Redone on `maze_route.py`'s own masks
(geometry from `geom_export.py` on the board; pads, pour outlines + zone-clearance rings, keep-outs, class
clearances hard; every foreign track/via crossable at a penalty; scripts in the session scratchpad, not in the repo):

- **14 links are sealed even with every track removed.** 12 of them join a part west of a wall to one east of it:
  the VS block (pours on F/In2/B, their keep-out rings, and the 1.0 mm VS/VBAT_IN clearance of EMC rule 7 round
  every VS pad, track and via) plus the J6 pin column (x 54-56, y 57-75) run edge to edge at x ~46-56. West of it sit
  logic parts: the analog/switch dividers R2, R4, R7, R8, R31, R33, R38, D23 (x 44-53, y 61-73), SW_RESET1, SW_BOOT1
  and TH1. Their partners (U1, R35-R37, D15-D19, J5) are east. Links: SW1 (R38), SW2_IO, SW4_IO, SW4, SWIN2, SWIN3,
  SWIN4, IO11 x2, EN, IO0, NTC. With the item clearances at 0.2 mm (no 1.0 mm rule) these get a path, but every one
  squeezes through the same gap in the VS block across a VS via: not a real gate. The other three: VBAT_SENSE (R60
  sits inside VS-F-drain, decision 174; R60.2 is also within 1.0 mm of R60.1 by construction) and F2-Pad1 x2 (J3).
- **20 links are blocked by tracks only** (each tested alone): D3-A (C4-Pad1 power copper), SW_IN1-4, +3V3, IO6 x2,
  IO7, IO17 x2, IO18, Q4-B x2, Q4-E, Q5-E, SW1 (track end), SW1_IO, DEN. Recurring blockers: the J6 In2 verticals
  /IO42, /RXD0, /IO37 (x 60-63, earlier-stage locked copper) in 7 links; harvested T-0236 copper (/SW2 B, /IO8 B,
  /SW3_IO B/via, /R3-Pad2 B, the U12/U13 IN/DEN/IS links) in most; Q3-C/Q3-B/Q5-B/Q5-C round the Q3-Q6 block;
  /IO3 and /IO39 (T-0271). USB_DP In2 once.
- Quilter never got the 1.0 mm rule (only the pours' zone clearance). Trial-1 1_1's new tracks come within 1.0 mm of
  VS/VBAT_IN copper on F/B for +3V3, SW4_IO, VBAT_SENSE and GND: KiCad DRC does not see it; any import must check it.

Rule sensitivity (same search): VS/VBAT_IN item clearance 0.6 mm instead of 1.0, with or without the VS pour zone
clearance also at 0.6: still 15 sealed, none opened. The 1.0 mm only on F/B (0.2 on In2): no gain either. Only at
0.2 mm do the 12 wall links pass, and then through the VS block across a VS via. Relaxing the creepage rule does not
open the wall.

So the wall is the floorplan: about a dozen logic parts are on the power side of a VS/J6 wall that has no free gate.
Rip-up helps only the 20 track-blocked links. The 12 wall links need a gate (a part move, a planned crossing of the
VS block, a J6 move) or a ruling on where the 1.0 mm rule applies: one-way doors for the owner.

## Trial 3 (submitted 2026-11-16 22:19)

Trial 2 ended with the one candidate checked above (not usable). Both trials ran without two keep-outs they were
meant to have: KiCad saves only a zone's first outline, and after `clear_fixed()` punched holes the VS-F-drain,
VS-B-spine and VS-In2 pour keep-outs had several outlines, so the files held a 0.7 mm diamond instead
(`split_rule_areas()` in `quilter_export.py` now writes one zone per outline). That likely explains trial 2's VS-GND
shorts and keep-out hits.

Trial 3 starts from the decision 214 board (29 unconnected: router fixes, the west divider block moved east, rip-up).
New in the export: `pour-creepage-F.Cu`/`-B.Cu`, 1.0 mm round all VS/VBAT_IN copper on the outer layers (EMC rule 7,
which trial 1 broke on 4 nets), with 0.5 mm escapes round foreign pads. Settings as before: stackup from the file,
internal copper preserved, minimums 0.2/0.2, diff pair and the 72 bypass entries removed, no power pour, GND primary,
20 preserved pours, Net Widths 0.4 mm for GND, D3-A, F2-Pad1 on every layer (12 rows). 223 pins to route.
Job "pdm-4ch trial 3 (moved parts, creepage keep-outs)", `6afb63a9dfae511781423da6`, same project. Export in
`~/Downloads/pdm-4ch-quilter-upload-3`. Download candidates to `~/Downloads/pdm-4ch-quilter-candidates-3/`; any import
must still pass `build_routing.sh` and amends 163/181 (owner).
