---
description: Run the independent validator on a board, a sheet or the whole system
argument-hint: <pdm-4ch|pdm-hc2|system> [sheet or focus] [deep]
---

Launch the `validator` sub-agent with this scope: $ARGUMENTS. If the arguments contain `deep`, drop the word and run
it on the `opus` model (full board before layout or before an order); otherwise Sonnet. Pass the scope unchanged and
add nothing from this conversation's reasoning. When it returns, give the report path, counts per severity and the
CRITICAL and MAJOR findings with one line each on what would resolve them. Do not fix anything; offer to add the
findings to the board's `STATUS.md` and handle them one at a time in `/board` or `/system`.
