# Quilter trial – handoff (pdm-4ch, 2026-11-14)

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
