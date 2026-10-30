---
description: Go through the owner inbox from unattended runs and record the owner's rulings
argument-hint: [question id, e.g. Q-0003]
---

Owner inbox session (decision 20, `docs/AUTONOMY.md`). Scope: $ARGUMENTS (empty = all open questions).

1. Use the orchestrator's copy: `.claude/worktrees/auto/docs/OWNER-INBOX.md` if it exists, else `docs/OWNER-INBOX.md`.
   Run `python3 tools/orchestrate.py status` for the overview.
2. Take the open questions one at a time, CRITICAL first. For each: read the finding in its report, give a short
   recommendation with alternatives, and ask the owner. Change no design file.
3. Write the owner's ruling after **Answer:** (`yes`, `no` or the ruling in words). Change nothing else in the file.
4. At the end, offer to run `python3 tools/orchestrate.py inbox` to apply the answers and commit them on `auto/pilot`.
