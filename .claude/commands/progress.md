---
description: Compact progress overview of the boards and what to do next
argument-hint: [pdm-4ch|pdm-hc2]
model: sonnet
---

Read-only overview. Scope: $ARGUMENTS (empty = all boards). Read `docs/CONTINUE-FROM-HERE.md`, the `STATUS.md` of
each board in scope, the **[proposed]** and open rows of `docs/decisions.md`, `git branch --no-merged main` and
`git log -1 --format='%h %ad %s' --date=short`. Reply in at most ~20 lines:

**Boards**: table Board | Schematic | PCB | Blocked by (a few words per cell).
**Next**: 3–5 numbered items, each with the command to start it (for example `/emc system`).
**Waiting on you**: proposed and open decisions, one line each.
**Flags**: "For /system" items and unmerged branches (omit if none).
Last line: the last commit.
