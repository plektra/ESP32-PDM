#!/bin/bash
# tmux session for unattended agent runs (decision 22): the orchestrator, a refreshing status and the combined live
# trace side by side; the orchestrator adds a window `workers` with one pane per running agent; a window `inbox` for
# answering the owner inbox. Detach with prefix-d; the run keeps going.
#
#   tools/agents-tmux.sh                  open (or reattach to) the session; start a run by hand in the left pane
#   tools/agents-tmux.sh --budget 85      open it and start `orchestrate.py run --budget 85` (3 agents at once)
#   tools/agents-tmux.sh --parallel 2 --budget 40
#   tools/agents-tmux.sh --kill           close the session (stops a running agent)
set -euo pipefail
REPO=$(cd "$(dirname "$0")/.." && pwd)
LOGS="$REPO/.claude/worktrees/auto-logs"
S=pdm-agents
ORCH="python3 tools/orchestrate.py"

if [ "${1:-}" = --kill ]; then
  tmux kill-session -t "$S"
  exit
fi

if ! tmux has-session -t "$S" 2>/dev/null; then
  mkdir -p "$LOGS"
  touch "$LOGS/live.log"
  if [ $# -gt 0 ]; then
    start="caffeinate -i $ORCH run $(printf '%q ' "$@")"
  else
    start="echo 'Start a run:  caffeinate -i $ORCH run [--budget 85]'"
  fi
  orch=$(tmux new-session -d -s "$S" -n agents -c "$REPO" -P -F '#{pane_id}')
  # right: the dashboard; bottom left: what all agents say (narration and findings, no tool noise)
  tmux split-window -h -l 60% -t "$orch" -c "$REPO" "$ORCH watch"
  tmux split-window -v -l 70% -t "$orch" -c "$REPO" "$ORCH follow"
  tmux send-keys -t "$orch" "$start" C-m
  tmux select-pane -t "$orch"
  inbox=$(tmux new-window -d -t "$S" -n inbox -c "$REPO" -P -F '#{pane_id}')
  tmux send-keys -t "$inbox" "echo 'Answer the questions: claude, then /inbox.   Apply the answers: $ORCH inbox'" C-m
fi

if [ -n "${TMUX:-}" ]; then
  tmux switch-client -t "$S"
else
  tmux attach -t "$S"
fi
