---
description: Run the cost controller on a board or the whole system
argument-hint: <pdm-4ch|pdm-hc2|system> [focus] [deep]
---

Launch the `cost-controller` sub-agent with this scope: $ARGUMENTS. If the arguments contain `deep`, drop the word
and run it on the `opus` model (before layout, before an order, or when new levers are wanted); otherwise Sonnet.
Add nothing from this conversation's reasoning. When it returns, give the report path, the totals per board and
quantity, and the largest levers with saving and trade-off. Change nothing; offer to add accepted levers to the
boards' `STATUS.md` and handle each as a topic in `/board` or `/system`.
