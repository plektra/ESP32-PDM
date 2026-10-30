---
description: Architecture session - shared sheets, pin map, invariants, budgets, mechanics, order of work
argument-hint: [topic, e.g. "panel-cable", "mechanical", "firmware", "tidy the handoff"]
---

This is a system (architecture) session. Topic: $ARGUMENTS

You own `docs/ARCHITECTURE.md`, the shared sheets (`power-usb`, `can`, `analog_sw`, the controller part of the
root sheet), the pin map, mechanics, the order of work in `docs/CONTINUE-FROM-HERE.md`, and the rules in `CLAUDE.md`.

1. Read `docs/ARCHITECTURE.md`, `docs/CONTINUE-FROM-HERE.md`, `docs/decisions.md`, every `hardware/*/STATUS.md`,
   and the parts of `docs/design-notes.md` and the reviews in `docs/reviews/` that the topic needs.
2. Reply briefly: "For /system" flags in the `STATUS.md` files, **[proposed]** decisions, budgets still marked
   estimate, then the topic.
3. One topic at a time: a recommendation with alternatives; the owner decides. Record each decision in
   `docs/decisions.md` (next free number), update `ARCHITECTURE.md`, and note follow-ups in every affected
   board's `STATUS.md`. A shared-sheet change is made on both boards in the same session (verify each with ERC and a
   netlist comparison).
4. "Tidy the handoff": prune finished items from the `STATUS.md` files, move confirmed proposals out of
   **[proposed]**, keep `CLAUDE.md` short.

End with `/handoff`.
