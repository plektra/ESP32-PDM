---
description: Start a focused session on one board and one phase
argument-hint: <pdm-4ch|pdm-hc2> [phase, e.g. schematic, pcb, firmware]
---

Start a focused work session on: $ARGUMENTS

1. Resolve the board folder `hardware/<board>/`. If it does not exist, list the boards from
   `docs/CONTINUE-FROM-HERE.md` and stop.
2. Read only: `docs/CONTINUE-FROM-HERE.md`, `docs/decisions.md`, from `docs/ARCHITECTURE.md` the sections
   "Invariants", the pin map and the budgets, the board's `STATUS.md`, and from `docs/design-notes.md` only the
   sections the phase needs.
3. Reply briefly: where the board stands, **[proposed]** items waiting for the owner, and the next step for the phase.
4. Raise the first open topic: a recommendation with alternatives, one topic at a time. Change files only after the
   owner answers.

A choice that changes a shared sheet, the pin map, an invariant or a budget needs `/system`: note it under
"For /system" in the board's `STATUS.md`. Stay on this board; note other boards' items in their `STATUS.md`. Use
sub-agents only when the owner asks, through `part-facts` or `stock-check`.
