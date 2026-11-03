# Running the agents – short guide

How to run the unattended agents day to day. Background and rules: `docs/AUTONOMY.md`, `docs/WORKING-WITH-CLAUDE.md`.
Run every command from the repo folder.

## See what is planned and done

- **What to do next:** `python3 tools/orchestrate.py next` – your next steps, most urgent first, each with the command
  to run (answer the inbox, look at a failed task, start a run, merge `auto/pilot`, `/system`). The same list heads
  the dashboard and `status`, is printed at the end of every run, and the run's notification names the first step.
- **`docs/ROADMAP.md`** – what the agents will change next (every item, your ruling, the planner's brief), what they
  changed, how much the boards grew, what waits for you and what is deferred. Regenerated at every change, in the
  orchestrator's copy `../ESP32-PDM-auto/docs/ROADMAP.md` while a run is going.
- **Dashboard** (right pane in tmux, or `python3 tools/orchestrate.py watch`) – live: running agents, up next, board
  size, inbox.
- **What changed in the schematics:** `git log --stat main..auto/pilot`; open `../ESP32-PDM-auto/hardware/…` in KiCad
  to look (don't save there while agents run).

## Start

| Situation | Do this |
|---|---|
| No tmux session (after a reboot) | `tools/agents-tmux.sh --wait-for-limit --budget 120` |
| tmux session already open | in its top-left pane: `caffeinate -i python3 tools/orchestrate.py run --wait-for-limit --budget 120` (or ↑ Enter) |
| Just merged orchestrator updates | `tools/agents-tmux.sh --kill`, then start as after a reboot |

`--wait-for-limit` sleeps through the 5-hour usage limit and carries on. `--budget` is the most this run may spend.
To try a cheaper model on one package: `python3 tools/orchestrate.py run --task T-0068 --fixer-model sonnet`, then
compare model, cost and result in the "Done" table of `docs/ROADMAP.md`.
Running `tools/agents-tmux.sh` with options while the session is open only reattaches – it does **not** start a run.

## While it runs

- **Answer questions:** window `inbox` (Ctrl-a `2`): `claude`, then `/inbox`; afterwards
  `python3 tools/orchestrate.py inbox`. Or write `yes`/`no`/your ruling on the Answer lines in
  `../ESP32-PDM-auto/docs/OWNER-INBOX.md`.
- **Take back an agent decision or an applied fix:** `python3 tools/orchestrate.py undo <task>`.
- **Ask an agent why:** `python3 tools/orchestrate.py attach <task>`.
- **Leave it running:** Ctrl-a `d` (detach). Come back with `tools/agents-tmux.sh`.

## Stop

| You want to | Do this |
|---|---|
| Stop gently (agents finish their package first) | `python3 tools/orchestrate.py pause` from any terminal |
| Stop now | Ctrl-C **once** in the top-left pane and wait for the prompt – running agents resume next time |
| Shut down the computer | Stop now (above), then shut down. Nothing else is needed |
| Close the tmux session | Only after the run has stopped: `tools/agents-tmux.sh --kill` |

Never close tmux or the terminal while a run is going: the running agents' progress is lost (they start over).

## Finish

When you are happy with the result: `git merge auto/pilot && git push` in the main checkout.

## tmux keys (prefix Ctrl-a)

| Do this | Keys |
|---|---|
| Next / previous window | Ctrl-a `n` / Ctrl-a `p` |
| Window 1 agents, 2 inbox, 3 workers | Ctrl-a `1` / `2` / `3` |
| Pick a window from a list | Ctrl-a `w` |
| Move between panes | click, or Option + arrow keys |
| Zoom a pane in / out | Ctrl-a `z` |
| Scroll back | mouse wheel or Ctrl-a `[`; `q` to leave |
| Detach (leave running) | Ctrl-a `d` |
| Copy text | hold Option (iTerm2) or Fn (Terminal) while dragging, then Cmd-C |
