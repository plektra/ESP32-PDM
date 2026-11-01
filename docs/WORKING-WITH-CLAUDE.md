# Working with Claude Code on ESP32-PDM

Sessions stay small and nothing is lost between them: the files carry the project, not the chat.

## Where things live

| What | Where |
|---|---|
| Rules for Claude, start here | `CLAUDE.md` |
| Which board is where, order of work | `docs/CONTINUE-FROM-HERE.md` |
| Every decision with status | `docs/decisions.md` |
| Shared sheets, pin map, invariants, budgets | `docs/ARCHITECTURE.md` |
| Rationale, calculations, sources | `docs/design-notes.md` |
| One board's status and next steps | `hardware/<board>/STATUS.md` |
| Reviewer reports (validator, cost, EMC) | `docs/reviews/` |
| Commands and sub-agents | `.claude/commands/`, `.claude/agents/` |

Boards: `pdm-4ch`, `pdm-hc2`.

## Roles

| Role | How to start | Owns | Decides? |
|---|---|---|---|
| **Board designer** (schematic / PCB) | `/board <board> [phase]` | that board's files and `STATUS.md` | proposes; you decide |
| **Architect** | `/system [topic]` | `docs/ARCHITECTURE.md`, shared sheets, pin map, mechanics, order of work | proposes; you decide |
| **Architecture reviewer** | runs in `/handoff` when shared things changed (sub-agent `architect`) | nothing | no; reports conflicts |
| **Validator** | `/validate <scope> [deep]` (sub-agent `validator`) | its reports | no; findings by severity |
| **Cost controller** | `/cost <scope> [deep]` (sub-agent `cost-controller`) | its reports | no; proposes cost levers |
| **EMC reviewer** | `/emc <scope> [deep]` (sub-agent `emc-reviewer`) | its reports | no; findings and layout rules |
| **Helpers** | on request (sub-agents `part-facts`, `stock-check`) | nothing | no; facts and tables |
| **You** | | every decision | yes |

- The **board designer** stays on one board. A choice that touches a shared sheet, the pin map, an invariant or a
  budget is noted under "For /system" in the board's `STATUS.md`.
- The **architect** picks up those flags, records system decisions and tells the affected boards via `STATUS.md`.
- The **validator**, **cost controller** and **EMC reviewer** work from the files and datasheets only, never edit the
  design, and write dated reports to `docs/reviews/`. Their findings become topics in `/board` or `/system` sessions.

## Session loop

1. **Start** with `/board <board> [phase]` or `/system [topic]`. Claude reads only what the task needs, sums up where
   things stand and raises the first open topic.
2. **One board and one phase per session.** One topic at a time: a recommendation with alternatives; you decide.
3. **End** with `/handoff`: status, decisions and order of work into the files, commit, push to `main`.
4. **`/clear`** before the next task.

## When to run what

- `/progress` – any time: where each board stands and what is next.
- `/emc <board|system>` – before layout, and after changes to connectors, inputs or outputs.
- `/cost <board|system> [deep]` – before layout and before each order.
- `/validate <board> deep` – when a schematic is complete, and again before ordering PCBs.
- `/system` – when a `STATUS.md` has "For /system" items, or before a new board or phase.

## Models

| Work | Model |
|---|---|
| `/board`, `/system` (design choices with you) | the session's model |
| `architect`, `validator`, `cost-controller`, `emc-reviewer`, `part-facts`, `/progress` | Sonnet |
| `deep` reviews (before layout or an order) | Opus |
| `stock-check` | Haiku |

## Unattended runs (pilot)

Policy, finding format, queue and inbox: `docs/AUTONOMY.md` (decision 23). Agents decide two-way doors (cheap to
undo: listed in the inbox digest, `orchestrate.py undo <task>` brings one back to you); one-way doors (money, your
rulings, safety, facts only you have, CRITICAL findings) wait for you.

```
python3 tools/orchestrate.py status            # queue, spend, inbox
python3 tools/orchestrate.py run --dry-run     # show the agent commands
python3 tools/orchestrate.py run               # ≤ 4 tasks, ≤ 60 USD; stops on CRITICAL or 2 failures
/inbox                                         # answer the questions, then: orchestrate.py inbox
```

**Parallel:** `--parallel N` (default 3) runs N agents at once, each in its own throwaway worktree
`../ESP32-PDM-auto-<task>`; the script checks each one and commits its report on `auto/pilot` under a lock. The run
budget is shared (a new agent gets what is left after the running agents' caps). A stop condition starts nothing new
and lets running agents finish. N agents use the 5-hour usage limit N times faster; a limit pauses the run and
leaves the tasks ready.

**In tmux:** `tools/agents-tmux.sh --budget 85` opens the session `pdm-agents` and starts the run: orchestrator
(top left), what all agents say – narration and `FINDING` lines, no tool noise (bottom left, `orchestrate.py
follow`), and the dashboard (right, `orchestrate.py watch`: progress, run budget, each running agent's current step
and findings, finished results, inbox). Window `workers` gets one titled pane per running agent
(`orchestrate.py follow <task>`: narration, findings, tool calls folded into one counting line), closed 2 minutes
after it finishes. Window `inbox` is for `claude` → `/inbox`.

**Talk to an agent:** `python3 tools/orchestrate.py attach T-0004` opens an interactive Claude session on that
agent's conversation (in tmux: a new window). While it runs you get a copy (`--fork-session`), so the agent is not
disturbed; after it finishes you continue its own session – ask why it judged something the way it did, or have it
explain a finding. The headless agents themselves take no input. Detach with prefix-d; the run continues; run the script again to
reattach; `--kill` closes it. Per-task traces and raw results: `.claude/worktrees/auto-logs/`. A usage limit
pauses the run and leaves the task ready.

Each task is a fresh headless session (`claude -p --agent <role>`) in the sibling worktree `../ESP32-PDM-auto` (outside `.claude/`, where agent writes are refused) on branch
`auto/pilot`. The script, not the agent, checks the result: a reviewer may change nothing but its new report, which
must carry a valid finding block. Since decision 24 approved items are also applied unattended: a planner groups
them into work packages, board-fixer agents make the schematic changes, and the script gates every change (scope,
ERC, netlist against declared refs, LCSC, shared sheets equal) before merging it; a validator then re-checks the
board (`docs/AUTONOMY.md`, "Unattended fixes"). Merge `auto/pilot` into `main` when you have read the result –
`git log --stat main..auto/pilot`. `run --no-fixes` runs reviews only.

## Parallel sessions

Shared files conflict easily: `lib/`, `docs/decisions.md`, the shared sheets. Run parallel sessions in separate
worktrees; `/handoff` merges each into `main` in turn.
