---
description: Run the EMC and robustness reviewer on a board, the whole system or a layout
argument-hint: <pdm-4ch|pdm-hc2|system> [layout] [deep]
---

Launch the `emc-reviewer` sub-agent with this scope: $ARGUMENTS. If the arguments contain `deep`, drop the word and
run it on the `opus` model; otherwise Sonnet. Add nothing from this conversation's reasoning. When it returns, give
the report path, counts per severity, the CRITICAL and MAJOR findings, and the number of layout rules. Change
nothing; offer to put the findings in the boards' `STATUS.md` (schematic fixes) and the layout rules in
`docs/design-notes.md`, and handle fixes one at a time in `/board` or `/system`.
