---
description: Record the session's outcome in the status and decision files, then commit and push to main
argument-hint: [optional note]
---

Wrap up so the next session can start from the files alone. Note from the owner: $ARGUMENTS

1. Update every touched board's `STATUS.md`: where it stands, waiting for the owner, next steps, "For /system";
   today's date on "Updated". Remove finished items; keep it short.
2. Decisions made this session: add rows to `docs/decisions.md` (next free number, date, area, short ruling,
   status). Unconfirmed ones are **[proposed]**; confirmed proposals lose the marker. Put calculations and sources
   in `docs/design-notes.md`.
3. If a board's status or the order of work changed, update `docs/CONTINUE-FROM-HERE.md` and the README status line.
4. If parts or values changed: make sure every new part has its `LCSC` field, and rerun `tools/heat_budget.py` for
   changed outputs.
5. Run `git status --short` and `git diff --stat`. If the changes touch `docs/ARCHITECTURE.md`, a shared sheet,
   `lib/` or the pin map, launch the `architect` sub-agent and report its CONFLICT / UPDATE NEEDED items; fix
   documentation updates now; stop and ask the owner on a CONFLICT. Otherwise say "architecture review skipped".
6. Never commit `*.kicad_prl`, backups or files the session did not make. Commit with a short message
   (`<board or System>: <what changed> (decisions N-M)`) and the attribution lines from the session's instructions.
7. Land: `python3 tools/land.py` (decision 126; works in a worktree and on `main`). Exit 2 = a merge conflict:
   merge `origin/main` by hand (for KiCad files take main's version and redo the scripted edit, then ERC), commit,
   run it again. Exit 3 = a decision number used twice: renumber the newer row and its references, commit, run
   again.
8. Report the commit on `main` and say `/clear` is safe.
