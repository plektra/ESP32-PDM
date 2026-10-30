# CLAUDE.md

Read first, then:

1. `docs/CONTINUE-FROM-HERE.md` – which board is where, order of work
2. `docs/decisions.md` – every decision and its status
3. `docs/ARCHITECTURE.md` – shared sheets, pin map, invariants, budgets (changed only in `/system` sessions)
4. For board work: `hardware/<board>/STATUS.md`; for background `docs/design-notes.md`

Roles and the session loop: `docs/WORKING-WITH-CLAUDE.md` (`/board`, `/system`, `/handoff`, `/progress`,
`/validate`, `/cost`, `/emc`). Work one board and one phase per session; update that board's `STATUS.md` before
ending. Use sub-agents only for bounded jobs through the agents in `.claude/agents/`; design choices stay in the main
conversation with the owner.

## Project

ESP32-PDM: an open, low-cost power distribution module for boats. Solid-state outputs replace relays and are switched
both by ordinary panel switches (in hardware, without the MCU) and over NMEA 2000, with current and fault reporting.
12 V and 24 V systems. Two boards: `pdm-4ch` (PROFET+24V) and `pdm-hc2` (TPS48110A-Q1 + MOSFETs). Designed in KiCad,
assembled by JLCPCB. First user: the tug Vega (24 V).

## How to work

1. **Confirmed vs proposed.** `docs/decisions.md` says what the owner decided. **[proposed]** is not settled. Ask before
   changing a confirmed decision.
2. **Low cost first (decision 2).** JLCPCB basic or preferred parts wherever one fits; E24/E12 values; count unique
   extended parts (each costs a loading fee per order).
3. **Check part facts.** Never invent pinouts, footprints or limits. Read the datasheet (download with curl, extract
   with pypdf in a temporary venv, render drawings to PNG when the text is not enough) and cite it. Custom
   footprints are verified against the package drawing and, before ordering, against the JLCPCB footprint.
4. **Heat budget (decision 9).** Every output change is checked with `tools/heat_budget.py` at 40 °C.
5. **EMC by default.** Every external line is filtered and protected at the connector (`docs/ARCHITECTURE.md`
   invariant 4).
6. **Verify every schematic edit.** Scripted edits use `tools/ksch.py`; after each edit run
   `kicad-cli sch erc` and export the netlist (`kicad-cli sch export netlist --format kicadxml`) and compare nets
   before/after. `kicad-cli` rewrites `*.kicad_prl`; do not commit those (git-ignored).
7. **Safety-relevant outputs** (bilge pumps, navigation lights, anything that can trap or burn) get a failure-mode
   note; remind the owner that a competent person should review them before installation.
8. **Public repo** (MIT): no personal data, credentials or manufacturer PDFs.

## Repo layout

```
CLAUDE.md, README.md, LICENSE
.claude/commands/   /board /system /handoff /progress /validate /cost /emc
.claude/agents/     architect, validator, cost-controller, emc-reviewer, part-facts, stock-check
docs/               CONTINUE-FROM-HERE.md, ARCHITECTURE.md, decisions.md, design-notes.md, WORKING-WITH-CLAUDE.md
  reviews/          validator, cost and EMC reports
hardware/pdm-4ch/   KiCad project + STATUS.md
hardware/pdm-hc2/   KiCad project + STATUS.md
lib/                shared symbols (ESP32-PDM.kicad_sym) and footprints (ESP32-PDM.pretty)
tools/              heat_budget.py, ksch.py (schematic editing), kicad_netlist.py
```
