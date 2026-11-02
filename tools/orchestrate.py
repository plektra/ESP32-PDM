#!/usr/bin/env python3
"""Orchestrator for unattended agent runs (decisions 22–23, docs/AUTONOMY.md).

Runs queued tasks in parallel (--parallel, default 3) as headless Claude Code sessions (`claude -p --agent <role>`),
each in a fresh context and its own throwaway worktree (`../<repo>-auto-<task>`) cut from the branch `auto/pilot`.
After every task it checks the result itself instead of trusting the agent: only the expected report in
docs/reviews/ may change, the report must end with a valid finding block. Under one lock it then copies the report
to the `auto/pilot` worktree (`../<repo>-auto`) and sorts the findings by the policy in docs/AUTONOMY.md (decision 23):
two-way doors are decided by agents (approved `board-fix` tasks, questions answered with their default; listed in
the inbox digest, `undo` takes one back), one-way doors become owner questions in docs/OWNER-INBOX.md. Each task is
committed on `auto/pilot`; the owner merges. Inside tmux every running agent gets a pane in the window `workers`.

Pilot: only the reviewer roles run (validator, emc-reviewer, cost-controller).

Examples:
  python3 tools/orchestrate.py status
  python3 tools/orchestrate.py run --dry-run
  python3 tools/orchestrate.py run --max-tasks 4 --budget 60 --parallel 3
  python3 tools/orchestrate.py run --task T-0003
  python3 tools/orchestrate.py add validator pdm-hc2 --focus hc_channel --deep
  python3 tools/orchestrate.py inbox          # apply the owner's answers only
  python3 tools/orchestrate.py retry T-0002

Environment: CLAUDE_BIN (default `claude`), KICAD_BIN_DIR (default the macOS KiCad app).
"""
import argparse
import datetime
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
import shlex
import tempfile
import threading
import time
import xml.etree.ElementTree as ET
from collections import Counter
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BRANCH = 'auto/pilot'
# Outside the repo and outside any .claude/ folder: Claude Code refuses agent writes under .claude/ as sensitive.
WORKTREE = REPO.parent / f'{REPO.name}-auto'
LOGS = REPO / '.claude' / 'worktrees' / 'auto-logs'  # raw agent output per task, git-ignored
QUEUE = Path('docs/queue.json')
INBOX = Path('docs/OWNER-INBOX.md')
REVIEWS = Path('docs/reviews')
CLAUDE_BIN = os.environ.get('CLAUDE_BIN', 'claude')
KICAD_BIN_DIR = os.environ.get('KICAD_BIN_DIR', '/Applications/KiCad/KiCad.app/Contents/MacOS')

BOARDS = ('pdm-4ch', 'pdm-hc2')
SCOPES = BOARDS + ('system',)
FIX_SCOPES = BOARDS + ('shared',)  # a shared package changes both boards identically
BOARD_SCH = {'pdm-4ch': 'hardware/pdm-4ch/ESP32-PDM-4CH.kicad_sch', 'pdm-hc2': 'hardware/pdm-hc2/ESP32-PDM-HC2.kicad_sch'}
SHARED_SHEETS = ('analog_sw', 'can', 'power-usb')
DECISIONS = Path('docs/decisions.md')
# Runnable roles: report name, model and per-task budget (USD) for normal and deep runs; `edits`: may change the
# design (gated by fix_gates and merged into auto/pilot), otherwise only its report is kept.
ROLES = {
    'validator': dict(kind='validate', model=('sonnet', 'opus'), budget=(8.0, 25.0)),
    'emc-reviewer': dict(kind='emc', model=('sonnet', 'opus'), budget=(8.0, 25.0)),
    'cost-controller': dict(kind='cost', model=('sonnet', 'opus'), budget=(8.0, 25.0)),
    'planner': dict(kind='plan', model=('opus', 'opus'), budget=(6.0, 6.0)),
    'board-fixer': dict(kind='fix', model=('opus', 'opus'), budget=(20.0, 20.0), edits=True),
}
REVIEWERS = ('validator', 'emc-reviewer', 'cost-controller')
FIX_ROLES = ('planner', 'board-fixer')  # off with `run --no-fixes`
TASK_TIMEOUT = 90 * 60  # seconds
# Never allowed to an unattended agent, whatever its tool list says. Roles without `edits` also lose Edit.
DENIED_TOOLS = ['Bash(git commit:*)', 'Bash(git push:*)', 'Bash(git reset:*)', 'Bash(git checkout:*)',
                'Bash(git merge:*)', 'Bash(git rebase:*)', 'Bash(git stash:*)', 'Bash(git worktree:*)',
                'Bash(git revert:*)', 'Bash(rm -rf:*)', 'Bash(sudo:*)', 'Agent']
SEVERITIES = ('CRITICAL', 'MAJOR', 'MINOR', 'INFO')
# Agent output that means the API was not available (usage limit, rate limit, overload), not that the task failed.
INTERRUPTED = ('aborted_streaming', 'aborted', 'interrupted')  # terminal reasons of an agent cut off mid-run
MAX_ATTEMPTS = 3
UNAVAILABLE = re.compile(r'hit your .*limit|usage limit|rate limit|overloaded|\b529\b', re.I)
KINDS = ('finding', 'lever', 'question')
STATE = threading.Lock()  # guards the queue, the inbox and git while agents run in parallel
RESERVED = set()  # report paths handed to running agents


def today():
    return datetime.date.today().isoformat()


def git(*args, cwd=None, check=True):
    r = subprocess.run(['git', *args], cwd=cwd or WORKTREE, capture_output=True, text=True)
    if check and r.returncode:
        raise SystemExit(f'git {" ".join(args)} failed:\n{r.stderr.strip()}')
    return r.stdout.strip()


# ---------------------------------------------------------------- state

def state_root():
    """Queue and inbox live in the orchestrator's worktree once it exists."""
    return WORKTREE if WORKTREE.exists() else REPO


def load_queue(root):
    return json.loads((root / QUEUE).read_text())


def save_queue(root, q):
    tmp = root / f'{QUEUE}.tmp'  # atomic, so `watch` never reads half a file
    tmp.write_text(json.dumps(q, indent=2, ensure_ascii=False) + '\n')
    os.replace(tmp, root / QUEUE)


def new_id(q, prefix):
    n = q['next'][prefix]
    q['next'][prefix] = n + 1
    return f'{prefix}-{n:04d}'


def find_task(q, tid):
    for t in q['tasks']:
        if t['id'] == tid:
            return t
    raise SystemExit(f'no task {tid}')


def deps_done(q, t):
    """A verify validator also runs after a failed package (it re-checks whatever was merged)."""
    finished = ('done', 'failed') if t.get('verify') else ('done',)
    return all(find_task(q, d)['state'] in finished for d in t.get('depends_on', []))


def runnable(q):
    return [t for t in q['tasks'] if t['state'] == 'ready' and t['role'] in ROLES and deps_done(q, t)]


def task_locks(t):
    """One board-fixer per board at a time (a shared package holds both); one planner at a time."""
    if t['role'] == 'board-fixer':
        return set(BOARDS) if t['scope'] == 'shared' else {t['scope']}
    return {'plan'} if t['role'] == 'planner' else set()


# ---------------------------------------------------------------- inbox

INBOX_HEAD = """# Owner inbox

One-way doors the agents may not decide themselves (decision 23, `docs/AUTONOMY.md`). Write your ruling on each
question's Answer line – `yes` (do the proposed fix), `no` (drop it) or your own ruling in words – or use `/inbox`.
The next `tools/orchestrate.py run` (or `inbox`) applies the answers. Below the questions: what the agents decided
(two-way doors), each with its undo command. This file is regenerated from `docs/queue.json`: only the Answer
lines are read; other edits are lost.
"""
DIGEST_MAX = 60  # agent decisions listed in the inbox, newest first


def read_answers(root):
    """{question id: answer text} for every non-empty Answer in the inbox."""
    path = root / INBOX
    if not path.exists():
        return {}
    answers = {}
    for block in re.split(r'^## ', path.read_text(), flags=re.M)[1:]:
        m = re.match(r'(Q-\d+)', block)
        a = re.search(r'^\*\*Answer:\*\*[ \t]*(.*?)(?=^\*\*|^---|\Z)', block, flags=re.M | re.S)
        if m and a and a.group(1).strip():
            answers[m.group(1)] = a.group(1).strip()
    return answers


def agent_decided(t):
    """Two-way doors the agents took: approved fixes waiting to be applied, and questions answered by default."""
    return t.get('finding') and not t.get('question') and (
        t['state'] == 'parked' or (t['state'] == 'done' and str(t.get('ruling', '')).startswith('assumed:')))


def write_inbox(root, q):
    answers = read_answers(root)  # typed but not yet applied: keep them
    open_q = [t for t in q['tasks'] if t.get('question') and t['state'] == 'blocked-owner']
    done_q = [t for t in q['tasks'] if t.get('question') and t['state'] != 'blocked-owner']
    out = [INBOX_HEAD, f'\n## Open ({len(open_q)})\n' if open_q else '\nNo open questions.\n']
    for t in open_q:
        f = t['finding']
        out.append(f"\n## {t['question']} · {f['severity']} · {f['board']} · {f['kind']}\n\n"
                   f"- **From:** `{t['source']['report']}` {f['id']} ({f.get('location', '')}); task {t['id']}\n"
                   f"- **Summary:** {f['summary']}\n"
                   f"- **Proposed:** {f.get('fix') or f.get('default') or '–'}\n"
                   f"- **Why it needs you:** {'; '.join(t['why_big'])}\n\n"
                   f"**Answer:** {answers.get(t['question'], '')}\n\n---\n")
    decided = [t for t in q['tasks'] if agent_decided(t)][::-1]
    if decided:
        out.append(f'\n## Decided by agents ({len(decided)}) – two-way doors\n\n'
                   f'Undo any of them with `python3 tools/orchestrate.py undo <task>`: it comes back above as a '
                   f'question.\n\n')
        for t in decided[:DIGEST_MAX]:
            f = t['finding']
            what = (f"assumed {t['ruling'][len('assumed:'):].strip()}" if f['kind'] == 'question'
                    else f.get('fix') or '–')
            out.append(f"- {t['id']} · {f['severity']} · {f['board']} · {f['summary']} → {what}\n")
        if len(decided) > DIGEST_MAX:
            out.append(f'- … {len(decided) - DIGEST_MAX} older ones in `docs/queue.json`\n')
    fixed = [t for t in q['tasks'] if t.get('finding') and t.get('merged')][::-1]
    if fixed:
        out.append(f'\n## Applied by agents ({len(fixed)})\n\n'
                   f'Undo with `python3 tools/orchestrate.py undo <task>`: reverts the whole work package.\n\n')
        out += [f"- {t['id']} · {t['finding']['board']} · {t['finding']['summary']} → {t['fixed_by']} "
                f"(`{t['merged'][:8]}`)\n" for t in fixed[:DIGEST_MAX]]
    later = [t for t in q['tasks'] if t.get('finding') and t['state'] == 'deferred']
    if later:
        out.append(f'\n## Deferred ({len(later)})\n\n')
        out += [f"- {t['id']} · {t['finding']['board']} · {t['finding']['summary']} → until {t.get('until')}: "
                f"{t.get('reason', '')}\n" for t in later]
    if done_q:
        out.append(f'\n## Answered ({len(done_q)})\n\n')
        out += [f"- {t['question']} ({t['finding']['board']}): {t['finding']['summary']} → **{t.get('ruling', '')}**"
                f" ({t['state']})\n" for t in done_q]
    (root / INBOX).write_text(''.join(out))


def apply_answers(root, q):
    answers = read_answers(root)
    applied = 0
    for t in q['tasks']:
        a = answers.get(t.get('question'))
        if t['state'] != 'blocked-owner' or not a:
            continue
        t['ruling'] = a
        t['answered'] = today()
        if a.lower().rstrip('.') == 'no':
            t['state'] = 'done'
        else:
            t['state'] = 'ready' if t['role'] in ROLES else 'parked'
        applied += 1
    write_inbox(root, q)
    return applied


# ---------------------------------------------------------------- triage

def parse_block(text):
    m = re.search(r'<!-- findings:begin -->\s*```(?:json)?\s*(.*?)```\s*<!-- findings:end -->', text, re.S)
    if not m:
        raise ValueError('no finding block')
    items = json.loads(m.group(1))
    if not isinstance(items, list):
        raise ValueError('finding block is not a list')
    for i, f in enumerate(items):
        for key in ('id', 'kind', 'severity', 'board', 'summary'):
            if key not in f:
                raise ValueError(f'entry {i}: missing {key}')
        if f['kind'] not in KINDS or f['severity'] not in SEVERITIES or f['board'] not in SCOPES:
            raise ValueError(f"entry {f['id']}: bad kind, severity or board")
        if 'door' not in f:  # reports written before decision 23 say small/big
            f['door'] = 'two-way' if f.get('class') == 'small' else 'one-way'
    return items


def owner_decisions(root):
    """Decision numbers only the owner may change: confirmed, [proposed] and open (not auto, not superseded)."""
    held = set()
    for line in (root / 'docs' / 'decisions.md').read_text().splitlines():
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) >= 5 and cells[0].isdigit():
            status = cells[-1].lower()
            if not status.startswith('auto') and 'replaced' not in status and 'superseded' not in status:
                held.add(int(cells[0]))
    return held


ONE_WAY_TOUCHES = ('money', 'safety', 'invariant', 'owner-fact')


def why_one_way(f, held, ordered):
    """Policy reasons that make a finding a one-way door (the owner decides); empty: two-way (docs/AUTONOMY.md)."""
    why = []
    if f['door'] != 'two-way':
        why.append('reviewer: one-way door' + (f" ({f['reason']})" if f.get('reason') else ''))
    if f['severity'] == 'CRITICAL':
        why.append('CRITICAL')
    if f['kind'] == 'question' and not f.get('default'):
        why.append('a question without a sensible default')
    touches = f.get('touches') or []
    why += [f'touches {x}' for x in touches if x in ONE_WAY_TOUCHES]
    why += [f'changes your decision {x.split(":")[1]}' for x in touches
            if x.startswith('decision:') and x.split(':')[1].isdigit() and int(x.split(':')[1]) in held]
    if f['board'] in ordered or (f['board'] == 'system' and ordered):
        why.append(f"{f['board'] if f['board'] in ordered else 'a board'} is ordered")
    return why


def triage(q, report, items, root=None):
    """Turn findings into tasks and questions. Returns (agent-decided, for the owner, duplicates, critical)."""
    held = owner_decisions(root or WORKTREE)
    ordered = set(q.get('ordered', []))
    seen = {(t['finding']['board'], t['finding'].get('location'), t['finding']['summary'])
            for t in q['tasks'] if t.get('finding') and t['state'] not in ('done', 'failed')}
    agent = owner = dup = crit = 0
    for f in items:
        key = (f['board'], f.get('location'), f['summary'])
        if key in seen:
            dup += 1
            continue
        seen.add(key)
        why = why_one_way(f, held, ordered)
        role = 'board-fix' if f['board'] in BOARDS and f['kind'] != 'question' else 'system'
        t = dict(id=new_id(q, 'T'), role=role, scope=f['board'], created=today(), finding=f,
                 source=dict(report=str(report), finding=f['id']), door='one-way' if why else 'two-way')
        if why:
            t.update(state='blocked-owner', question=new_id(q, 'Q'), why_big=why)
            owner += 1
        elif f['kind'] == 'question':
            t.update(state='done', ruling=f"assumed: {f['default']}")
            agent += 1
        else:
            t.update(state='parked')
            agent += 1
        crit += f['severity'] == 'CRITICAL'
        q['tasks'].append(t)
    return agent, owner, dup, crit


# ---------------------------------------------------------------- running one task

def agent_tools(role):
    m = re.search(r'^tools:\s*(.+)$', (WORKTREE / '.claude' / 'agents' / f'{role}.md').read_text(), re.M)
    return [s.strip() for s in m.group(1).split(',')]


def report_path(t):
    name = (f"{today()}-{ROLES[t['role']]['kind']}-{t['scope']}" + (f"-{t['focus']}" if t.get('focus') else '')
            + (f"-{t['id']}" if t['role'] in FIX_ROLES else ''))
    path, n = REVIEWS / f'{name}.md', 2
    while (WORKTREE / path).exists() or path in RESERVED:
        path, n = REVIEWS / f'{name}-{n}.md', n + 1
    return path


NARRATE = ("The owner watches your progress live: before each step write one short line saying what you do and why, "
           "and when you find a problem write one line `FINDING (SEVERITY): what is wrong`.\n")
TOOLS_HINT = ("For datasheets use `$PDM_PDF_PYTHON -I` (a ready Python with pypdf, pypdfium2 and Pillow; do not build "
              "your own venv). Keep scripts in `$CLAUDE_JOB_DIR/scripts/` with names that do not shadow Python modules "
              "(never inspect.py, json.py, …); `rm -rf` is not available to you.\n")
PDF_VENV = Path.home() / '.cache' / 'esp32-pdm' / 'pdf-venv'
PDF_PY = ''  # set by cmd_run


def pdf_python():
    """A shared venv with the PDF tools agents need, built once; '' if it cannot be built."""
    py = PDF_VENV / 'bin' / 'python3'
    if not py.exists():
        subprocess.run([sys.executable, '-m', 'venv', str(PDF_VENV)], capture_output=True)
        subprocess.run([str(py), '-m', 'pip', 'install', '-q', 'pypdf', 'pypdfium2', 'pillow'], capture_output=True)
    ok = py.exists() and subprocess.run([str(py), '-I', '-c', 'import pypdf, pypdfium2, PIL'],
                                        capture_output=True).returncode == 0
    return str(py) if ok else ''


def prompt_for(t, report, inputs=None):
    kind = ROLES[t['role']]['kind']
    common = (f"Unattended run, task {t['id']}. Today is {today()}. Follow your instructions, CLAUDE.md and "
              f"docs/AUTONOMY.md (decision 23). Nobody will answer questions.\n{NARRATE}{TOOLS_HINT}")
    if kind == 'plan':
        return (common + f"The approved items to plan are in `{inputs}` (JSON). Write your report to exactly "
                f"`{report}` and end it with the plan block. Change no other file in the repository. Your final "
                f"message: the report path and the number of packages, deferred items and decision rows.")
    if kind == 'fix':
        return (common + f"Work package {t['id']}: {t.get('title', '')} (scope {t['scope']}).\n"
                f"Brief from the planner:\n{t.get('brief', '')}\n"
                f"The items with their findings and the owner's rulings are in `{inputs}` (JSON).\n"
                f"Write your report to exactly `{report}` and end it with the fix block; list every reference "
                f"designator you touched in `refs`. Your final message: the report path and what was done or "
                f"blocked.")
    focus = f" Focus: {t['focus']}." if t.get('focus') else ''
    ruling = f" The owner ruled on this task: {t['ruling']}." if t.get('ruling') else ''
    return (f"Unattended run, task {t['id']}. Scope: {t['scope']}.{focus}{ruling} Today is {today()}.\n"
            f"Follow your instructions, CLAUDE.md and docs/AUTONOMY.md. Nobody will answer questions: put them in the "
            f"finding block as kind \"question\" and carry on.\n"
            f"The owner watches your progress live: before each new check write one short line saying what you check "
            f"and why, and when you find a problem write one line `FINDING (SEVERITY): what is wrong`.\n{TOOLS_HINT}"
            f"Write your report to exactly `{report}` and end it with the finding block. Change no other file in "
            f"the repository; scratch work goes in $CLAUDE_JOB_DIR. Your final message: the report path and counts "
            f"per severity.")


def changed_paths(cwd=None):
    out = subprocess.run(['git', 'status', '--porcelain', '-z', '--untracked-files=all'], cwd=cwd or WORKTREE,
                         capture_output=True, text=True, check=True).stdout
    paths, entries = [], iter(out.split('\0'))
    for e in entries:
        if e:
            paths.append(e[3:])
            if e[0] in 'RC':  # renames carry the old path as the next entry
                next(entries, None)
    return paths


def task_worktree(t):
    """Each running agent gets its own throwaway worktree next to the repo (never under .claude/)."""
    return REPO.parent / f"{REPO.name}-auto-{t['id']}"


def tmux(*args):
    return subprocess.run(['tmux', *args], capture_output=True, text=True)


def tmux_pane(t, log):
    """Inside tmux: one pane per running agent in the window `workers`, tailing its trace. Best effort."""
    if not os.environ.get('TMUX'):
        return None
    log.touch()
    tail = f"{shlex.quote(sys.executable)} {shlex.quote(str(Path(__file__).resolve()))} follow {t['id']}"
    with STATE:
        r = tmux('split-window', '-d', '-t', 'workers', '-P', '-F', '#{pane_id}', tail)
        if r.returncode:
            r = tmux('new-window', '-d', '-n', 'workers', '-P', '-F', '#{pane_id}', tail)
            tmux('set-option', '-w', '-t', 'workers', 'pane-border-status', 'top')
        if r.returncode:
            return None
        pane = r.stdout.strip()
        tmux('select-pane', '-t', pane, '-T', f"{t['id']} {t['role']} {t['scope']}{' deep' if t.get('deep') else ''}")
        tmux('select-layout', '-t', 'workers', 'tiled')
    return pane


def tmux_close(pane, linger=120):
    """Leave a finished agent's pane up for a while, then close it."""
    if pane:
        tmux('run-shell', '-b', f'sleep {linger}; tmux kill-pane -t {pane}; tmux select-layout -t workers tiled')


def describe(event):
    """Readable lines for one stream-json event: tool calls, agent text, tool errors, start and end."""
    kind = event.get('type')
    message = event.get('message')  # a dict for assistant/user events; some system events carry a plain string
    content = message.get('content') if isinstance(message, dict) else None
    content = [c for c in content if isinstance(c, dict)] if isinstance(content, list) else []
    if kind == 'system' and event.get('subtype') == 'init':
        return [f"● started on {event.get('model')}"]
    if kind == 'assistant':
        lines = []
        for c in content:
            if c.get('type') == 'tool_use':
                i = c.get('input') if isinstance(c.get('input'), dict) else {}
                fp = i.get('file_path') or i.get('path')
                arg = (i.get('description') or (Path(fp).name if fp else None) or i.get('pattern') or i.get('url')
                       or i.get('query') or i.get('command') or json.dumps(i, ensure_ascii=False))
                name = c['name'].split('__')[-1]  # mcp__pcbparts__jlc_get_part -> jlc_get_part
                lines.append(f"▸ {name}: {' '.join(str(arg).split())[:160]}")
            elif c.get('type') == 'text' and c['text'].strip():
                lines.append('“ ' + ' '.join(c['text'].split())[:240])
        return lines
    if kind == 'user':
        return ['  ✗ ' + ' '.join(str(c.get('content')).split())[:160] for c in content if c.get('is_error')]
    if kind == 'result':
        return [f"■ {event.get('terminal_reason') or event.get('subtype')}, "
                f"{float(event.get('total_cost_usd') or 0):.2f} USD"]
    return []


def run_streaming(cmd, env, tag, task_log, cwd, on_init=None):
    """Run one agent, writing a readable trace to its log and to live.log (tail it in tmux); return the result
    event, or an error dict shaped like one. on_init gets the session id as soon as the agent starts."""
    proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    timed_out = threading.Event()
    timer = threading.Timer(TASK_TIMEOUT, lambda: (timed_out.set(), proc.kill()))
    timer.daemon = True  # a leftover timer must never keep the orchestrator from exiting
    timer.start()
    out, other = None, []
    try:
        with open(task_log, 'a') as tl, open(LOGS / 'live.log', 'a') as live:
            for line in proc.stdout:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    other.append(line.strip())
                    continue
                if not isinstance(event, dict):
                    continue
                if event.get('type') == 'result':
                    out = event
                if on_init and event.get('type') == 'system' and event.get('subtype') == 'init':
                    on_init(event.get('session_id'))
                try:
                    lines = describe(event)
                except Exception as e:  # the trace is for people; it must never stop a run
                    lines = [f'(unreadable event {event.get("type")}: {e!r})']
                for text in lines:
                    stamped = f'{datetime.datetime.now():%H:%M:%S} {tag} {text}\n'
                    tl.write(stamped)
                    live.write(stamped)
                tl.flush()
                live.flush()
    except BaseException:
        proc.kill()  # never leave an agent running that nobody will check or merge
        raise
    finally:
        proc.wait()
        timer.cancel()
    if out is None:
        out = dict(is_error=True, result=f'timeout after {TASK_TIMEOUT} s' if timed_out.is_set() else
                   f"exit {proc.returncode}: {' '.join(other)[-300:]}")
    return out


def task_budget(t, budget_left):
    return min(ROLES[t['role']]['budget'][bool(t.get('deep'))], budget_left)


# ---------------------------------------------------------------- design gates (board-fixer)

def kicad_check(wt, board, scratch):
    """ERC (errors, warnings) and the netlist of one board in a worktree; None when kicad-cli fails."""
    sch, name = wt / BOARD_SCH[board], board
    erc_out, nl_out = scratch / f'{name}-erc.json', scratch / f'{name}-net.xml'
    env = dict(os.environ, PATH=f"{KICAD_BIN_DIR}:{os.environ.get('PATH', '')}")
    a = subprocess.run(['kicad-cli', 'sch', 'erc', '--format', 'json', '-o', str(erc_out), str(sch)],
                       capture_output=True, text=True, env=env)
    b = subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadxml', '-o', str(nl_out), str(sch)],
                       capture_output=True, text=True, env=env)
    if a.returncode not in (0, 5) or b.returncode or not erc_out.exists() or not nl_out.exists():
        return None  # kicad-cli exits 5 when ERC finds violations
    sev = Counter(v['severity'] for s in json.loads(erc_out.read_text())['sheets'] for v in s['violations'])
    root = ET.parse(nl_out).getroot()
    comps = {}
    for c in root.iter('comp'):
        fields = {f.get('name'): (f.text or '') for f in c.iter('field')}
        dnp = any(p.get('name') == 'dnp' for p in c.iter('property')) or 'DNP' in (c.findtext('value') or '')
        comps[c.get('ref')] = (c.findtext('value'), c.findtext('footprint'), fields.get('LCSC', ''), dnp)
    nets = [(n.get('name'), [(x.get('ref'), x.get('pin')) for x in n.iter('node')]) for n in root.iter('net')]
    return dict(errors=sev['error'], warnings=sev['warning'], comps=comps, nets=nets)


def undeclared_changes(before, after, declared):
    """Refs whose part or connections changed but which the agent did not declare. Named nets are compared by
    name; auto-named nets by their members other than declared refs, so adding a declared part does not implicate
    its neighbours."""
    def keys(nl):
        k = {}
        for name, nodes in nl['nets']:
            auto = 'Net-(' in name or 'unconnected-(' in name
            key = frozenset(n for n in nodes if n[0] not in declared) if auto else name
            for n in nodes:
                k[n] = key
        return k
    bad = {r for r in set(before['comps']) | set(after['comps'])
           if before['comps'].get(r) != after['comps'].get(r) and r not in declared}
    kb, ka = keys(before), keys(after)
    bad |= {n[0] for n in set(kb) | set(ka) if n[0] not in declared and kb.get(n) != ka.get(n)}
    return bad


def shared_sheets_equal(wt):
    """Shared sheets must be the same on both boards apart from the project name in their instance blocks."""
    def norm(board):
        return [(wt / f'hardware/{board}/{s}.kicad_sch').read_text().replace(
            f'"{Path(BOARD_SCH[board]).stem}"', '"PROJECT"') for s in SHARED_SHEETS]
    return [s for s, a, b in zip(SHARED_SHEETS, norm('pdm-4ch'), norm('pdm-hc2')) if a != b]


def fix_allowed(path, scope):
    boards = BOARDS if scope == 'shared' else (scope,)
    ok = ['docs/design-notes.md', 'README.md', 'lib/'] + [f'hardware/{b}/' for b in boards]
    if scope == 'shared':
        ok.append('docs/ARCHITECTURE.md')
    return any(path == p or (p.endswith('/') and path.startswith(p)) for p in ok)


def fix_gates(wt, t, base, after, block, changed, report):
    """Everything a board-fixer change must pass before it is merged. Returns the list of failures."""
    fails, declared = [], set(block.get('refs') or [])
    for p in changed:
        if p == report or p.endswith('.kicad_prl'):
            continue
        tracked = bool(git('ls-files', '--', p, cwd=wt))
        if p.lower().endswith('.pdf'):
            fails.append(f'adds a PDF ({p}); public repo')
        elif tracked and not fix_allowed(p, t['scope']):
            fails.append(f'changed {p}, outside the package scope {t["scope"]}')
    for b in BOARDS:
        if after[b] is None:
            fails.append(f'{b}: kicad-cli could not read the schematic')
            continue
        if after[b]['errors'] > base[b]['errors'] or after[b]['warnings'] > base[b]['warnings']:
            fails.append(f"{b}: ERC {after[b]['errors']} errors/{after[b]['warnings']} warnings "
                         f"(was {base[b]['errors']}/{base[b]['warnings']})")
        bad = undeclared_changes(base[b], after[b], declared)
        if bad:
            fails.append(f"{b}: undeclared netlist changes on {', '.join(sorted(bad)[:15])}")
        new = [r for r, c in after[b]['comps'].items() if base[b]['comps'].get(r) != c]
        missing = [r for r in new if not after[b]['comps'][r][2] and not after[b]['comps'][r][3]]
        if missing:
            fails.append(f"{b}: no LCSC code (and not DNP) on {', '.join(sorted(missing)[:15])}")
    differ = shared_sheets_equal(wt)
    if differ:
        fails.append('shared sheets differ between the boards: ' + ', '.join(differ))
    return fails


def parse_tagged(text, tag):
    m = re.search(rf'<!-- {tag}:begin -->\s*```(?:json)?\s*(.*?)```\s*<!-- {tag}:end -->', text, re.S)
    if not m:
        raise ValueError(f'no {tag} block')
    return json.loads(m.group(1))


def add_decisions(root, rows):
    """Append decision rows after the last row of the table; returns their numbers."""
    path = root / DECISIONS
    lines = path.read_text().splitlines()
    last = max(i for i, line in enumerate(lines) if re.match(r'\|\s*\d+\s*\|', line))
    n = max(int(re.match(r'\|\s*(\d+)', line).group(1)) for line in lines if re.match(r'\|\s*\d+\s*\|', line))
    new = []
    for i, (area, text, status) in enumerate(rows, 1):
        clean = ' '.join(str(text).split()).replace('|', '\\|')
        new.append(f'| {n + i} | {today()} | {area} | {clean} | {status} |')
    path.write_text('\n'.join(lines[:last + 1] + new + lines[last + 1:]) + '\n')
    return list(range(n + 1, n + 1 + len(new)))


# ---------------------------------------------------------------- planning and fixing

def approved_items(q):
    """Approved, not yet planned: owner-approved rulings and agents' two-way fixes waiting to be applied."""
    return [t for t in q['tasks'] if t.get('finding') and t['state'] == 'parked' and not t.get('package')]


def maybe_plan(q):
    """Queue a planner when approved items wait, no planner is pending and no review is still to run."""
    if any(t['role'] == 'planner' and t['state'] in ('ready', 'running') for t in q['tasks']):
        return False
    if any(t['role'] in REVIEWERS and (t['state'] == 'running' or (t['state'] == 'ready' and deps_done(q, t)))
           for t in q['tasks']):
        return False
    if not approved_items(q):
        return False
    q['tasks'].append(dict(id=new_id(q, 'T'), role='planner', scope='system', state='ready', created=today(),
                           depends_on=[]))
    return True


def item_view(t):
    f = t['finding']
    return dict(task=t['id'], board=f['board'], severity=f['severity'], kind=f['kind'], location=f.get('location'),
                summary=f['summary'], fix=f.get('fix') or f.get('default'), report=t['source']['report'],
                ruling=t.get('ruling'), question=t.get('question'), door=t.get('door', 'two-way'))


def apply_plan(q, t, plan):
    """Planner result: packages become board-fixer tasks, deferred items wait, owner rulings become decisions,
    and each touched board gets a verify validator after its packages."""
    items = {i: find_task(q, i) for i in t.get('items', [])}
    seen, pkg_ids = set(), {}
    for p in plan.get('packages', []):
        if p.get('scope') not in FIX_SCOPES:
            raise ValueError(f"package {p.get('id')}: bad scope {p.get('scope')}")
        tasks = [i for i in p.get('tasks', []) if i in items and i not in seen]
        if not tasks:
            continue
        seen |= set(tasks)
        pkg = dict(id=new_id(q, 'T'), role='board-fixer', scope=p['scope'], state='ready', created=today(),
                   title=p.get('title', ''), brief=p.get('brief', ''), items=tasks, plan=t['id'], depends_on=[])
        pkg_ids[p.get('id')] = pkg
        q['tasks'].append(pkg)
        for i in tasks:
            items[i]['package'] = pkg['id']
    for p in plan.get('packages', []):
        if p.get('id') in pkg_ids:
            pkg_ids[p['id']]['depends_on'] = [pkg_ids[a]['id'] for a in p.get('after', []) if a in pkg_ids]
    deferred = 0
    for d in plan.get('deferred', []):
        if d.get('task') in items and d['task'] not in seen:
            seen.add(d['task'])
            items[d['task']].update(state='deferred', until=d.get('until', 'later'), reason=d.get('reason', ''))
            deferred += 1
    rows = []
    for d in plan.get('decisions', []):
        text = (f"Amends decision {d['amends']}: " if d.get('amends') else '') + d.get('text', '')
        rows.append((d.get('area', 'system'), f"{text} (owner: {', '.join(d.get('from') or [])})", 'confirmed'))
    numbers = add_decisions(WORKTREE, rows) if rows else []
    for board in BOARDS:  # re-check each board once its packages are merged
        deps = [p['id'] for p in pkg_ids.values() if p['scope'] in (board, 'shared')]
        if deps:
            q['tasks'].append(dict(id=new_id(q, 'T'), role='validator', scope=board, state='ready', created=today(),
                                   depends_on=deps, verify=True))
    left = [i for i in items if i not in seen]
    return dict(packages=len(pkg_ids), deferred=deferred, decisions=numbers, unplanned=left)


def apply_fix(q, t, block, merged):
    """Board-fixer result: done items are closed, one-way blocks become owner questions, two-way blocks wait,
    items it did not touch go back to the planner; its design choices become auto decisions."""
    mine = set(t.get('items', []))
    done = [i for i in block.get('done', []) if i in mine]
    for i in done:
        find_task(q, i).update(state='done', fixed_by=t['id'], merged=merged)
    blocked = 0
    for b in block.get('blocked', []):
        if b.get('task') not in mine:
            continue
        s = find_task(q, b['task'])
        if b.get('door') == 'one-way':
            s.update(state='blocked-owner', question=new_id(q, 'Q'), door='one-way',
                     why_big=[f"found while fixing ({t['id']}): {b.get('reason', '')}"],
                     finding=dict(s['finding'], fix=b.get('question') or s['finding'].get('fix'),
                                  default=b.get('default')))
        else:
            s.update(state='deferred', until='later', reason=f"{t['id']}: {b.get('reason', '')}")
        blocked += 1
    for i in mine - set(done) - {b.get('task') for b in block.get('blocked', [])}:
        find_task(q, i).pop('package', None)  # untouched: planned again
    rows = [(d.get('area', t['scope']), f"{d.get('text', '')} ({t['id']})", 'auto') for d in block.get('decisions', [])]
    numbers = add_decisions(WORKTREE, rows) if rows else []
    return dict(done=len(done), blocked=blocked, decisions=numbers, merged=merged)


# ---------------------------------------------------------------- running one task

def run_task(q, t, budget_left, dry_run=False):
    """Run one agent in its own worktree, then (under STATE) check it and bring its result to auto/pilot:
    reviewers' findings are triaged, a planner's plan becomes tasks, a board-fixer's change is gated and merged.
    Thread-safe: several run at once."""
    spec = ROLES[t['role']]
    deep = bool(t.get('deep'))
    model = t.get('model') or spec['model'][deep]
    budget = task_budget(t, budget_left)
    with STATE:
        report = report_path(t)
        RESERVED.add(report)
        if spec['kind'] == 'plan':
            t['items'] = [i['id'] for i in approved_items(q)]
            payload = [item_view(i) for i in approved_items(q)]
        elif spec['kind'] == 'fix':
            payload = [item_view(find_task(q, i)) for i in t.get('items', [])]
        else:
            payload = None
    scratch = Path(tempfile.mkdtemp(prefix=f"pdm-{t['id']}-"))
    inputs = None
    if payload is not None:
        inputs = scratch / 'items.json'
        inputs.write_text(json.dumps(payload, indent=1, ensure_ascii=False))
    denied = DENIED_TOOLS + ([] if spec.get('edits') else ['Edit'])
    cmd = [CLAUDE_BIN, '-p', prompt_for(t, report, inputs), '--agent', t['role'], '--model', model,
           '--max-budget-usd', f'{budget:.2f}', '--output-format', 'stream-json', '--verbose',
           '--add-dir', str(scratch), '--allowedTools', *agent_tools(t['role']), 'Write',
           '--disallowedTools', *denied]
    print(f"→ {t['id']} {t['role']} {t['scope']}{' deep' if deep else ''} ({model}, ≤ {budget:.2f} USD) → {report}")
    if dry_run:
        print('  ' + ' '.join(c if ' ' not in c else repr(c[:60] + '…') for c in cmd))
        shutil.rmtree(scratch, ignore_errors=True)
        return 0.0, None
    wt = task_worktree(t)
    with STATE:
        if wt.exists():
            git('worktree', 'remove', '--force', str(wt), check=False)
        git('worktree', 'add', '--detach', str(wt), 'HEAD')
        head = git('rev-parse', 'HEAD', cwd=wt)
        t.update(state='running', started=datetime.datetime.now().isoformat(timespec='seconds'), model=model)
        save_queue(WORKTREE, q)
        LOGS.mkdir(parents=True, exist_ok=True)
    (wt / REVIEWS).mkdir(parents=True, exist_ok=True)  # empty folders are not in git
    gate_dir = Path(tempfile.mkdtemp(prefix=f"pdm-gate-{t['id']}-"))
    base = {b: kicad_check(wt, b, gate_dir) for b in BOARDS} if spec.get('edits') else None
    log = LOGS / f"{t['id']}-{datetime.datetime.now():%Y%m%d-%H%M%S}.json"
    env = dict(os.environ, CLAUDE_JOB_DIR=str(scratch), PATH=f"{KICAD_BIN_DIR}:{os.environ.get('PATH', '')}",
               PDM_PDF_PYTHON=PDF_PY or 'python3')
    (scratch / 'scripts').mkdir(exist_ok=True)
    pane = tmux_pane(t, log.with_suffix('.log'))

    def on_init(session):  # recorded at once so `attach` works while the agent runs
        with STATE:
            t['session'] = session
            save_queue(WORKTREE, q)
    try:
        out = run_streaming(cmd, env, t['id'], log.with_suffix('.log'), wt, on_init)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
        tmux_close(pane)
    log.write_text(json.dumps(dict(cmd=cmd, output=out), indent=2, ensure_ascii=False))
    cost = float(out.get('total_cost_usd') or 0)
    notes = []
    if out.get('permission_denials'):
        denied_calls = sorted({d.get('tool_name', '?') for d in out['permission_denials']})
        notes.append(f"{len(out['permission_denials'])} tool calls denied ({', '.join(denied_calls)}); log {log.name}")
    keep = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=wt, capture_output=True, text=True).stdout.strip() != head
    changed = changed_paths(wt)
    new_reports = [p for p in changed if p.startswith(f'{REVIEWS}/') and p.endswith('.md')]
    got = str(report) if str(report) in changed else (new_reports[0] if len(new_reports) == 1 else None)
    text = (wt / got).read_text() if got else None
    # Board-fixer gates run outside the lock (kicad-cli takes a while); other agents keep working meanwhile.
    gate_fails, block = [], None
    if spec.get('edits') and got and not keep:
        try:
            block = parse_tagged(text, 'fix')
            after = {b: kicad_check(wt, b, gate_dir) for b in BOARDS}
            if any(base[b] is None for b in BOARDS):
                gate_fails.append('kicad-cli could not read the schematics before the change')
            else:
                gate_fails = fix_gates(wt, t, base, after, block, changed, got)
        except (ValueError, json.JSONDecodeError) as e:
            gate_fails.append(f'report {got}: {e}')
    shutil.rmtree(gate_dir, ignore_errors=True)

    with STATE:
        t['cost_usd'] = round(t.get('cost_usd', 0) + cost, 4)
        t['attempts'] = t.get('attempts', 0) + 1
        if keep:  # the agent moved its worktree's HEAD: keep it for inspection
            notes.append(f'agent changed HEAD (was {head[:8]}); inspect {wt}')
            got = None
        result, commit_paths = None, [str(QUEUE), str(INBOX)]
        if got is None:
            notes.append(f"no report written ({out.get('terminal_reason') or out.get('subtype') or 'unknown'}): "
                         f"{str(out.get('result', ''))[:200]}")
        elif spec.get('edits'):
            result, merge_note = finish_fix(q, t, wt, changed, got, block, gate_fails, model, cost)
            notes += merge_note
            commit_paths.append(str(DECISIONS))
        else:
            if any(p != got for p in changed):
                notes.append('dropped ' + ', '.join(p for p in changed if p != got))
            try:
                if (WORKTREE / got).exists():  # another agent took the name meanwhile
                    got = str(Path(got).with_name(f"{Path(got).stem}-{t['id']}.md"))
                if spec['kind'] == 'plan':
                    result = apply_plan(q, t, parse_tagged(text, 'plan'))
                    commit_paths.append(str(DECISIONS))
                else:
                    agent, owner, dup, crit = triage(q, got, parse_block(text))
                    result = dict(agent=agent, owner=owner, duplicates=dup, critical=crit)
                (WORKTREE / got).parent.mkdir(parents=True, exist_ok=True)
                (WORKTREE / got).write_text(text)
                commit_paths.append(got)
                result['report'] = got
            except (ValueError, json.JSONDecodeError, KeyError, SystemExit) as e:
                notes.append(f'report {got}: {e}')
                result = None
        # A usage limit or API outage is not the task's fault: leave it ready and let the caller stop the run.
        # An interrupted agent (killed, stream cut) is queued again, up to MAX_ATTEMPTS.
        paused = result is None and not keep and (out.get('terminal_reason') == 'api_error'
                                                  or bool(UNAVAILABLE.search(str(out.get('result', '')))))
        interrupted = (result is None and not keep and not paused and out.get('terminal_reason') in INTERRUPTED
                       and t['attempts'] < MAX_ATTEMPTS)
        summary = 'interrupted, queued again' if interrupted else summarize(spec['kind'], result, paused)
        t.update(state='done' if result else 'ready' if paused or interrupted else 'failed', finished=today(),
                 note='; '.join(notes) or None, summary=summary, interrupted=interrupted or None)
        if result:
            t['report'] = result['report']
        write_inbox(WORKTREE, q)
        save_queue(WORKTREE, q)
        git('add', '--', *commit_paths)
        git('commit', '-m', f"Auto: {t['role']} {t['scope']} ({t['id']}): {summary}\n\n"
            f"Unattended run by tools/orchestrate.py, model {model}, {cost:.2f} USD.\n\n"
            f"Co-Authored-By: Claude <noreply@anthropic.com>")
        if not keep:
            git('worktree', 'remove', '--force', str(wt), check=False)
        RESERVED.discard(report)
        print(f"  {t['id']} {t['state']}: {summary}; {cost:.2f} USD" + (f"; {t['note']}" if t.get('note') else ''),
              flush=True)
    return cost, result


def summarize(kind, result, paused):
    if not result:
        return 'paused, API unavailable' if paused else 'failed'
    if kind == 'plan':
        return (f"{result['packages']} packages, {result['deferred']} deferred, {len(result['decisions'])} decisions"
                + (f", {len(result['unplanned'])} unplanned" if result['unplanned'] else ''))
    if kind == 'fix':
        return f"{result['done']} fixed, {result['blocked']} blocked, merged {result['merged'][:8]}"
    return f"{result['agent']} decided by agents, {result['owner']} for the owner, {result['duplicates']} duplicates"


def finish_fix(q, t, wt, changed, got, block, gate_fails, model, cost):
    """Under STATE: commit a gated board-fixer change in its worktree and merge it into auto/pilot.
    Returns (result or None, notes). On failure nothing is merged; the report is kept for the owner."""
    if gate_fails:
        keep_report = REVIEWS / f"{Path(got).stem}-rejected.md"
        (WORKTREE / keep_report).write_text((wt / got).read_text() + '\n\n## Rejected by the orchestrator\n\n'
                                            + '\n'.join(f'- {f}' for f in gate_fails) + '\n')
        git('add', '--', str(keep_report))
        return None, ['gates failed: ' + '; '.join(gate_fails), f'report kept as {keep_report}']
    paths = [p for p in changed if p == got or (fix_allowed(p, t['scope']) and not p.endswith('.kicad_prl')
                                                and not p.lower().endswith('.pdf'))]
    git('add', '--', *paths, cwd=wt)
    git('commit', '-m', f"{t['scope']}: {t.get('title', 'work package')} ({t['id']})\n\n"
        f"Unattended board-fixer, model {model}, {cost:.2f} USD; gates passed (ERC, netlist, LCSC, shared sheets).\n\n"
        f"Co-Authored-By: Claude <noreply@anthropic.com>", cwd=wt)
    sha = git('rev-parse', 'HEAD', cwd=wt)
    r = subprocess.run(['git', 'merge', '--no-ff', '--no-edit', '-m', f"Auto: merge {t['id']} {t.get('title', '')}",
                        sha], cwd=WORKTREE, capture_output=True, text=True)
    if r.returncode:
        git('merge', '--abort', check=False)
        return None, [f'merge conflict with auto/pilot (retry rebuilds it on the new base): {r.stdout[-200:]}']
    result = apply_fix(q, t, block, git('rev-parse', 'HEAD'))
    result['report'] = got
    return result, [f"not merged: {', '.join(p for p in changed if p not in paths)}"] if set(changed) - set(paths) else []


# ---------------------------------------------------------------- worktree, lock, notify

def ensure_worktree(base):
    if not WORKTREE.exists():
        exists = subprocess.run(['git', 'rev-parse', '--verify', '--quiet', BRANCH], cwd=REPO,
                                capture_output=True).returncode == 0
        git('worktree', 'add', *([str(WORKTREE), BRANCH] if exists else ['-b', BRANCH, str(WORKTREE), base]), cwd=REPO)
    dirty = [p for p in changed_paths() if p not in (str(QUEUE), str(INBOX))]
    if dirty:
        raise SystemExit(f'{WORKTREE} has uncommitted changes: {", ".join(dirty)}')
    if git('status', '--porcelain', '--', str(QUEUE), str(INBOX)):  # owner answers, add, retry
        git('commit', '-m', 'Auto: owner edits to queue and inbox', '--', str(QUEUE), str(INBOX))
    r = subprocess.run(['git', 'merge', '--no-edit', base], cwd=WORKTREE, capture_output=True, text=True)
    if r.returncode:
        git('merge', '--abort', check=False)
        raise SystemExit(f'merging {base} into {BRANCH} conflicts; merge by hand in {WORKTREE}')


def lock():
    common = Path(git('rev-parse', '--git-common-dir', cwd=REPO))
    fh = open((REPO / common if not common.is_absolute() else common) / 'orchestrate.lock', 'w')
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit('another orchestrator run is active')
    return fh


def notify(text):
    print(text)
    if sys.platform == 'darwin':
        subprocess.run(['osascript', '-e', f'display notification {json.dumps(text)} with title "ESP32-PDM agents"'],
                       capture_output=True)


# ---------------------------------------------------------------- views: watch, follow, attach

RUN_INFO = 'run.json'
STYLE = dict(reset='\033[0m', bold='\033[1m', dim='\033[2m', red='\033[31m', green='\033[32m', yellow='\033[33m',
             cyan='\033[36m', magenta='\033[35m')
SEV_STYLE = dict(CRITICAL=('red', 'bold'), MAJOR=('yellow', 'bold'), MINOR=('cyan',), INFO=('dim',))
TRACE = re.compile(r'(\d\d:\d\d:\d\d) (T-\d+) +(\S)\s?(.*)')
FINDING = re.compile(r'FINDING\s*\((CRITICAL|MAJOR|MINOR|INFO)\)', re.I)


def paint(text, *styles):
    return ''.join(STYLE[s] for s in styles) + str(text) + STYLE['reset']


def fit(text, width):
    """Cut a line with colour codes to `width` visible characters."""
    out, n = [], 0
    for part in re.split(r'(\033\[[0-9;]*m)', text):
        if part.startswith('\033['):
            out.append(part)
        else:
            out.append(part[:max(width - n, 0)])
            n += len(part)
    return ''.join(out) + STYLE['reset']


def said(text):
    """Agent narration, coloured by severity when it is a finding."""
    m = FINDING.search(text)
    return paint(text, *SEV_STYLE[m.group(1).upper()]) if m else paint(text, 'bold')


def write_run(info):
    LOGS.mkdir(parents=True, exist_ok=True)
    tmp = LOGS / f'{RUN_INFO}.tmp'
    tmp.write_text(json.dumps(info))
    os.replace(tmp, LOGS / RUN_INFO)


def task_log(tid):
    logs = sorted(LOGS.glob(f'{tid}-*.log'))
    return logs[-1] if logs else None


def read_trace(tid):
    """Tool count, last narration, last tool and findings from a task's latest trace."""
    info = dict(tools=0, said=None, tool=None, findings=[])
    path = task_log(tid)
    for line in (path.read_text(errors='replace').splitlines() if path else []):
        m = TRACE.match(line)
        if not m:
            continue
        mark, rest = m.group(3), m.group(4)
        if mark == '▸':
            info['tools'] += 1
            info['tool'] = rest
        elif mark == '“' and FINDING.search(rest):
            info['findings'].append(rest)
        elif mark == '“':
            info['said'] = rest
    return info


def ago(iso):
    try:
        s = int((datetime.datetime.now() - datetime.datetime.fromisoformat(iso)).total_seconds())
    except (TypeError, ValueError):
        return '?'
    return f'{s // 3600}h{s % 3600 // 60:02d}m' if s >= 3600 else f'{s // 60}m{s % 60:02d}s'


def bar(done, total, width=28):
    full = min(width, round(width * done / total)) if total else 0
    return paint('█' * full, 'green') + paint('░' * (width - full), 'dim')


def dashboard(width, recent):
    root = state_root()
    q = load_queue(root)
    reviews = [t for t in q['tasks'] if t['role'] in ROLES]
    st = Counter(t['state'] for t in reviews)
    run = json.loads((LOGS / RUN_INFO).read_text()) if (LOGS / RUN_INFO).exists() else {}
    out = [paint(' ESP32-PDM agents ', 'bold', 'magenta') + paint(f'  {datetime.datetime.now():%H:%M:%S}', 'dim'), '']
    out.append(f" Reviews  {bar(st['done'], len(reviews))}  {paint(st['done'], 'bold')}/{len(reviews)} done   "
               f"{paint(str(st['running']) + ' running', 'cyan')}   {st['ready']} queued   "
               + (paint(f"{st['failed']} failed", 'red') if st['failed'] else '0 failed'))
    if run:
        state = (paint('stopped: ' + run['stop'], 'red') if run.get('stop') else
                 paint('finished', 'green') if run.get('finished') else paint('running', 'cyan'))
        out.append(f" Run      {bar(run['spent'], run['budget'])}  {run['spent']:.2f} of {run['budget']:.0f} USD"
                   f" · {run['parallel']} at once · since {run['started'][11:16]} · {state}")
    out.append(paint(f" All runs {sum(t.get('cost_usd', 0) for t in q['tasks']):.2f} USD", 'dim'))

    running = [t for t in reviews if t['state'] == 'running']
    out += ['', paint(f' RUNNING ({len(running)})', 'bold')]
    for t in running:
        tr = read_trace(t['id'])
        out.append(f"  {paint(t['id'], 'cyan', 'bold')} {t['role']} {paint(t['scope'], 'bold')}"
                   f"{' deep' if t.get('deep') else ''}" + paint(
                       f"   {t.get('model', '')} · {ago(t.get('started'))} · {tr['tools']} tool calls · "
                       f"{len(tr['findings'])} findings", 'dim'))
        out.append('    ' + (said(tr['said']) if tr['said'] else paint('starting…', 'dim')))
        if tr['tool']:
            out.append('    ' + paint('▸ ' + tr['tool'], 'dim'))
        out += ['    ' + said(f) for f in tr['findings'][-3:]]
    if not running:
        out.append(paint('  none', 'dim'))

    finished = sorted((t for t in reviews if t['state'] in ('done', 'failed')),
                      key=lambda t: t.get('started') or '', reverse=True)
    out += ['', paint(' FINISHED', 'bold')]
    for t in finished[:recent]:
        name = f"{t['id']} {t['role']} {t['scope']}{' deep' if t.get('deep') else ''}"
        if t['state'] == 'done' and t['role'] not in REVIEWERS:
            out.append(f"  {paint('✓', 'green')} {name} {t.get('title', '')}"
                       + paint(f"   {t.get('cost_usd', 0):.2f} USD · {t.get('summary', '')}", 'dim'))
        elif t['state'] == 'done':
            mine = [x for x in q['tasks'] if (x.get('source') or {}).get('report') == t.get('report')]
            big = sum(1 for x in mine if x.get('question'))
            out.append(f"  {paint('✓', 'green')} {name}" + paint(
                f"   {t.get('cost_usd', 0):.2f} USD · {len(mine) - big} decided by agents · {big} for you · "
                f"{Path(t.get('report', '')).name}", 'dim'))
        else:
            out.append(f"  {paint('✗', 'red')} {name}   " + paint((t.get('note') or '')[:160], 'red'))
    if not finished:
        out.append(paint('  none yet', 'dim'))

    open_q = [t for t in q['tasks'] if t['state'] == 'blocked-owner']
    sev = Counter(t['finding']['severity'] for t in open_q)
    answers = read_answers(root)
    waiting = sum(1 for t in open_q if t.get('question') in answers)
    out += ['', paint(' OWNER INBOX', 'bold')]
    out.append((f'  {len(open_q)} open: ' + ' · '.join(paint(f'{sev[s]} {s}', *SEV_STYLE[s]) for s in SEVERITIES
                                                      if sev[s]) if open_q else '  no open questions')
               + f"   {sum(1 for t in q['tasks'] if agent_decided(t))} decided by agents (see the inbox digest)"
               + (paint(f'   {waiting} answered, applied at the next run', 'green') if waiting else ''))
    out += ['', paint(' talk to an agent: orchestrate.py attach <task> · answer: /inbox', 'dim')]
    return [fit(line, width) for line in out]


def cmd_watch(args):
    sys.stdout.write('\033[2J')
    while True:
        size = shutil.get_terminal_size()
        try:
            frame = dashboard(size.columns, args.recent)
        except (OSError, ValueError, KeyError) as e:  # queue mid-write or not there yet
            frame = [f'waiting for the queue: {e!r}']
        sys.stdout.write('\033[H' + ''.join(line + '\033[K\n' for line in frame[:size.lines - 1]) + '\033[J')
        sys.stdout.flush()
        if args.once:
            return
        time.sleep(args.interval)


def cmd_follow(args):
    """Readable trace: one task (tool calls folded into one counting line) or all tasks (narration only)."""
    while True:
        path = task_log(args.task) if args.task else LOGS / 'live.log'
        if path and path.exists():
            break
        time.sleep(1)
    tools, folded = Counter(), False
    with open(path, errors='replace') as f:
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue
            m = TRACE.match(line.rstrip('\n'))
            if not m:
                continue
            ts, tid, mark, rest = m.groups()
            stamp = paint(ts + ' ', 'dim') + ('' if args.task else paint(tid + ' ', 'cyan'))
            if mark == '▸':
                tools[rest.split(':')[0]] += 1
                if args.task or args.tools:
                    top = ', '.join(f'{k} ×{n}' for k, n in tools.most_common(3))
                    n = sum(tools.values())
                    text = stamp + paint(f"… {n} tool call{'s' if n > 1 else ''} ({top}) – {rest}", 'dim')
                    width = shutil.get_terminal_size().columns
                    sys.stdout.write(('\r\033[K' + fit(text, width - 1)) if args.task else text + '\n')
                    sys.stdout.flush()
                    folded = bool(args.task)
                continue
            if folded:
                sys.stdout.write('\n')
                folded = False
            tools.clear()
            styled = {'“': said(rest), '●': paint('● ' + rest, 'green'), '■': paint('■ ' + rest, 'bold'),
                      '✗': paint('✗ ' + rest, 'red')}.get(mark, rest)
            print(stamp + styled, flush=True)


def cmd_attach(args):
    root = state_root()
    t = find_task(load_queue(root), args.task)
    if not t.get('session'):
        raise SystemExit(f"{t['id']} has no saved session (it ran before sessions were saved, or has not started)")
    wt = task_worktree(t)
    cwd = wt if wt.exists() else root
    cmd = [CLAUDE_BIN, '--resume', t['session']] + (['--model', t['model']] if t.get('model') else [])
    if t['state'] == 'running':
        cmd.append('--fork-session')  # a copy: the running agent is not disturbed
    print(f"{t['id']}: {'a copy of the running session' if t['state'] == 'running' else 'its session'} in {cwd}"
          + ('' if wt.exists() else '\nThe agent is done: ask questions, but edits here would block the next run.'),
          flush=True)
    if os.environ.get('TMUX'):
        tmux('new-window', '-n', f"talk-{t['id']}", '-c', str(cwd), shlex.join(cmd))
    else:
        os.chdir(cwd)
        os.execvp(cmd[0], cmd)


# ---------------------------------------------------------------- commands

def cmd_status(args):
    root = state_root()
    q = load_queue(root)
    answers = read_answers(root)
    waiting = [t for t in q['tasks'] if t['state'] == 'blocked-owner' and t['question'] in answers]
    order = ('running', 'ready', 'blocked-owner', 'failed', 'parked', 'deferred', 'done')
    print(f'State: {root / QUEUE}')
    for state in order:
        ts = [t for t in q['tasks'] if t['state'] == state]
        if not ts:
            continue
        print(f'\n{state} ({len(ts)})')
        for t in ts[:args.limit]:
            what = t['finding']['summary'] if t.get('finding') else (
                f"{t['scope']}{' ' + t['focus'] if t.get('focus') else ''}{' deep' if t.get('deep') else ''}")
            extra = f" [{t['question']}]" if t.get('question') else ''
            extra += f" {t['cost_usd']:.2f} USD" if t.get('cost_usd') else ''
            print(f"  {t['id']} {t['role']:<15} {what[:70]}{extra}")
        if len(ts) > args.limit:
            print(f'  … {len(ts) - args.limit} more')
    spent = sum(t.get('cost_usd', 0) for t in q['tasks'])
    print(f"\nSpent so far: {spent:.2f} USD. Inbox: {root / INBOX}"
          + (f" ({len(waiting)} answered, applied at the next run)" if waiting else ''))


def cmd_add(args):
    if args.role not in ROLES:
        raise SystemExit(f'pilot runs only {", ".join(ROLES)}')
    root = state_root()
    q = load_queue(root)
    t = dict(id=new_id(q, 'T'), role=args.role, scope=args.scope, state='ready', created=today(),
             depends_on=args.after or [])
    if args.focus:
        t['focus'] = args.focus
    if args.deep:
        t['deep'] = True
    q['tasks'].append(t)
    save_queue(root, q)
    print(f"added {t['id']} (not committed; the next run commits it)" if root == WORKTREE else
          f"added {t['id']} to {root / QUEUE}; commit it, the next run merges it in")


def cmd_retry(args):
    root = state_root()
    q = load_queue(root)
    t = find_task(q, args.task)
    t.update(state='ready', note=None)
    save_queue(root, q)
    print(f'{t["id"]} is ready again')


def cmd_undo(args):
    """Take back an agent's two-way decision: it becomes a question in the owner inbox."""
    root = state_root()
    q = load_queue(root)
    t = find_task(q, args.task)
    if t.get('merged'):  # an applied fix: revert the package's merge, all its items come back as questions
        if root != WORKTREE:
            raise SystemExit('applied fixes live on auto/pilot; run a pass first so its worktree exists')
        if git('status', '--porcelain', '--', str(QUEUE), str(INBOX), str(DECISIONS)):
            raise SystemExit(f'commit or apply the pending edits in {WORKTREE} first (orchestrate.py inbox)')
        r = subprocess.run(['git', 'revert', '-m', '1', '--no-edit', t['merged']], cwd=WORKTREE,
                           capture_output=True, text=True)
        if r.returncode:
            git('revert', '--abort', check=False)
            raise SystemExit(f"cannot revert {t['merged'][:8]} cleanly (later changes build on it); undo it in a "
                             f"/board session: {r.stderr.strip()[-200:]}")
        sha = t['merged']
        for s in [x for x in q['tasks'] if x.get('merged') == sha]:
            s.update(state='blocked-owner', question=new_id(q, 'Q'), door='one-way', undone=today(),
                     why_big=[f"you took back the applied fix ({s.get('fixed_by')}, reverted)"])
            s.pop('merged', None)
        write_inbox(root, q)
        save_queue(root, q)
        git('commit', '-m', f'Auto: owner undid {args.task} (reverted {sha[:8]})', '--', str(QUEUE), str(INBOX))
        print(f'reverted {sha[:8]}; its items are open questions in {root / INBOX}')
        return
    if not agent_decided(t):
        raise SystemExit(f"{t['id']} is not an agent decision waiting to be applied (state {t['state']})")
    t.update(state='blocked-owner', question=new_id(q, 'Q'), door='one-way', undone=today(),
             why_big=[f"you took it back from the agents (was: {t.get('ruling') or 'fix approved'})"])
    t.pop('ruling', None)
    write_inbox(root, q)
    save_queue(root, q)
    print(f"{t['id']} is question {t['question']} in {root / INBOX}"
          + (' (committed by the next run)' if root == WORKTREE else ''))


def cmd_inbox(args):
    fh = lock()
    ensure_worktree(args.base)
    q = load_queue(WORKTREE)
    n = apply_answers(WORKTREE, q)
    save_queue(WORKTREE, q)
    if git('status', '--porcelain'):
        git('add', '--', str(QUEUE), str(INBOX))
        git('commit', '-m', f'Auto: apply {n} owner answers')
    print(f'{n} answers applied')
    fh.close()


def cmd_run(args):
    global WORKTREE
    if args.dry_run:  # touch nothing: read the queue where it is
        WORKTREE = state_root()
        q = load_queue(WORKTREE)
        for t in ([find_task(q, args.task)] if args.task else runnable(q))[:args.max_tasks]:
            run_task(q, t, args.budget, dry_run=True)
        return
    fh = lock()
    ensure_worktree(args.base)
    global PDF_PY
    PDF_PY = pdf_python()
    print(f"PDF tools for agents: {PDF_PY or 'not available (agents use python3)'}", flush=True)
    q = load_queue(WORKTREE)
    for t in q['tasks']:
        if t['state'] == 'running':  # left over from an interrupted run; the lock says nobody runs it
            t.update(state='ready', note='interrupted run, requeued')
    answered = apply_answers(WORKTREE, q)
    save_queue(WORKTREE, q)
    if git('status', '--porcelain'):
        git('add', '--', str(QUEUE), str(INBOX))
        git('commit', '-m', f'Auto: apply {answered} owner answers')
    for wt in REPO.parent.glob(f'{REPO.name}-auto-T-*'):  # agent worktrees left by an interrupted run
        git('worktree', 'remove', '--force', str(wt), check=False)
    git('worktree', 'prune', check=False)
    # Up to --parallel agents at once. Each new agent's budget cap is what is left after the caps of the running
    # ones. A stop condition starts nothing new; running agents finish and are committed.
    limit = 1 if args.task else args.max_tasks
    fixes, plans_left = not args.no_fixes, args.rounds
    spent, ran, fails, new_q, stop = 0.0, 0, 0, 0, None
    running = {}  # future -> (task, cap)
    run_info = dict(started=datetime.datetime.now().isoformat(timespec='seconds'), budget=args.budget,
                    parallel=args.parallel, spent=0.0, stop=None, finished=None)
    write_run(run_info)
    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        while True:
            run_info.update(spent=round(spent, 2), stop=stop)
            write_run(run_info)
            while not stop and len(running) < args.parallel and ran < limit:
                with STATE:
                    if fixes and plans_left and not args.task and maybe_plan(q):
                        plans_left -= 1
                        save_queue(WORKTREE, q)
                    held = set().union(*[task_locks(x) for x, _ in running.values()])
                    todo = [find_task(q, args.task)] if args.task else runnable(q)
                    todo = [t for t in todo if t['state'] == 'ready' and t['role'] in ROLES
                            and (fixes or t['role'] not in FIX_ROLES) and not task_locks(t) & held]
                    if not todo:
                        break
                    left = args.budget - spent - sum(cap for _, cap in running.values())
                    if left < 1.0:
                        stop = f'run budget of {args.budget:.0f} USD reserved or used'
                        break
                    t = todo[0]
                    t['state'] = 'running'  # claimed here so the next pick skips it; run_task saves it
                cap = task_budget(t, left)
                running[pool.submit(run_task, q, t, cap)] = (t, cap)
                ran += 1
            if not running:
                break
            done, _ = wait(running, return_when=FIRST_COMPLETED)
            for fut in done:
                t, _ = running.pop(fut)
                try:
                    cost, result = fut.result()
                except Exception as e:  # a crash in one worker must not orphan the others
                    with STATE:
                        t.update(state='failed', note=f'orchestrator error: {e!r}')
                        save_queue(WORKTREE, q)
                    cost, result = 0.0, None
                spent += cost
                if not result and t['state'] == 'ready' and t.get('interrupted'):
                    continue  # queued again; not a failure
                if not result and t['state'] == 'ready':
                    stop = stop or f"API unavailable ({t['note'][-100:]}); {t['id']} stays ready"
                    continue
                fails = 0 if result else fails + 1
                new_q += result.get('owner', 0) if result else 0
                if result and result.get('critical'):
                    stop = stop or f"CRITICAL finding in {result['report']}, see the owner inbox"
                if fails >= 2:
                    stop = stop or 'two tasks failed in a row'
            if stop and running:
                print(f'stopping after the {len(running)} running agent(s) finish: {stop}', flush=True)
    run_info.update(spent=round(spent, 2), stop=stop, finished=datetime.datetime.now().isoformat(timespec='seconds'))
    write_run(run_info)
    if stop:
        notify(f'Run stopped: {stop}')
    if args.push:
        git('push', '-u', 'origin', BRANCH)
    if ran:
        notify(f'{ran} task(s), {spent:.2f} USD, {new_q} new question(s) for the owner')
    else:
        print('nothing to run')
    fh.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('status', help='tasks by state, spend, inbox path')
    s.add_argument('--limit', type=int, default=15)
    s.set_defaults(fn=cmd_status)
    s = sub.add_parser('add', help='queue a review task')
    s.add_argument('role')
    s.add_argument('scope', choices=SCOPES)
    s.add_argument('--focus')
    s.add_argument('--deep', action='store_true', help='run on Opus with the larger budget')
    s.add_argument('--after', nargs='*', help='task ids that must be done first')
    s.set_defaults(fn=cmd_add)
    s = sub.add_parser('watch', help='live dashboard: progress, running agents, findings, inbox')
    s.add_argument('--interval', type=float, default=2.0)
    s.add_argument('--recent', type=int, default=6, help='finished tasks shown')
    s.add_argument('--once', action='store_true')
    s.set_defaults(fn=cmd_watch)
    s = sub.add_parser('follow', help="readable live trace of one task, or of all (narration only)")
    s.add_argument('task', nargs='?')
    s.add_argument('--tools', action='store_true', help='with all tasks: show tool calls too')
    s.set_defaults(fn=cmd_follow)
    s = sub.add_parser('attach', help="talk to an agent: resume its session (a copy while it runs)")
    s.add_argument('task')
    s.set_defaults(fn=cmd_attach)
    s = sub.add_parser('undo', help="take back an agent's two-way decision: it becomes an owner question")
    s.add_argument('task')
    s.set_defaults(fn=cmd_undo)
    s = sub.add_parser('retry', help='set a failed task ready again')
    s.add_argument('task')
    s.set_defaults(fn=cmd_retry)
    for name, fn, text in (('run', cmd_run, 'run ready tasks'), ('inbox', cmd_inbox, 'apply owner answers only')):
        s = sub.add_parser(name, help=text)
        s.add_argument('--base', default='main', help='branch merged into auto/pilot first (default main)')
        s.set_defaults(fn=fn)
        if name == 'run':
            s.add_argument('--max-tasks', type=int, default=12)
            s.add_argument('--no-fixes', action='store_true', help='reviews only: no planner, no board-fixers')
            s.add_argument('--rounds', type=int, default=2,
                           help='planning rounds per run (fix, re-validate, fix again; default 2)')
            s.add_argument('--parallel', type=int, default=3, help='agents running at once (default 3)')
            s.add_argument('--budget', type=float, default=60.0, help='USD for this run (default 60)')
            s.add_argument('--task', help='run only this task')
            s.add_argument('--dry-run', action='store_true', help='print the agent commands, run nothing')
            s.add_argument('--push', action='store_true', help=f'push {BRANCH} to origin afterwards')
    args = ap.parse_args()
    args.fn(args)


if __name__ == '__main__':
    main()
