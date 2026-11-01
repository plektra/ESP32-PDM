#!/usr/bin/env python3
"""Orchestrator for unattended agent runs (decision 22, docs/AUTONOMY.md).

Runs queued tasks in parallel (--parallel, default 3) as headless Claude Code sessions (`claude -p --agent <role>`),
each in a fresh context and its own throwaway worktree (`../<repo>-auto-<task>`) cut from the branch `auto/pilot`.
After every task it checks the result itself instead of trusting the agent: only the expected report in
docs/reviews/ may change, the report must end with a valid finding block. Under one lock it then copies the report
to the `auto/pilot` worktree (`../<repo>-auto`) and sorts the findings by the policy in docs/AUTONOMY.md: small ones
become parked `board-fix` tasks, big ones become owner questions in docs/OWNER-INBOX.md. Each task is committed on
`auto/pilot`; the owner merges. Inside tmux every running agent gets a pane in the window `workers`.

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
# Runnable roles: report name, model and per-task budget (USD) for normal and deep runs.
ROLES = {
    'validator': dict(kind='validate', model=('sonnet', 'opus'), budget=(8.0, 25.0)),
    'emc-reviewer': dict(kind='emc', model=('sonnet', 'opus'), budget=(8.0, 25.0)),
    'cost-controller': dict(kind='cost', model=('sonnet', 'opus'), budget=(8.0, 25.0)),
}
PARKED_ROLES = ('board-fix', 'system')  # queued, but run with the owner during the pilot
SMALL_COST_LIMIT = 0.50  # USD per board at 10 units (docs/AUTONOMY.md)
TASK_TIMEOUT = 90 * 60  # seconds
# Never allowed to an unattended agent, whatever its tool list says.
DENIED_TOOLS = ['Bash(git commit:*)', 'Bash(git push:*)', 'Bash(git reset:*)', 'Bash(git checkout:*)',
                'Bash(git merge:*)', 'Bash(git rebase:*)', 'Bash(git stash:*)', 'Bash(git worktree:*)',
                'Bash(rm -rf:*)', 'Bash(sudo:*)', 'Agent', 'Edit']
SEVERITIES = ('CRITICAL', 'MAJOR', 'MINOR', 'INFO')
# Agent output that means the API was not available (usage limit, rate limit, overload), not that the task failed.
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
    (root / QUEUE).write_text(json.dumps(q, indent=2, ensure_ascii=False) + '\n')


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
    return all(find_task(q, d)['state'] == 'done' for d in t.get('depends_on', []))


def runnable(q):
    return [t for t in q['tasks'] if t['state'] == 'ready' and t['role'] in ROLES and deps_done(q, t)]


# ---------------------------------------------------------------- inbox

INBOX_HEAD = """# Owner inbox

Questions the agents may not decide themselves (decision 22, `docs/AUTONOMY.md`). Write your ruling on each
question's Answer line – `yes` (do the proposed fix), `no` (drop it) or your own ruling in words – or use `/inbox`.
The next `tools/orchestrate.py run` (or `inbox`) applies the answers. This file is regenerated from
`docs/queue.json`: only the Answer lines are read; other edits are lost.
"""


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


def write_inbox(root, q):
    open_q = [t for t in q['tasks'] if t.get('question') and t['state'] == 'blocked-owner']
    done_q = [t for t in q['tasks'] if t.get('question') and t['state'] != 'blocked-owner']
    out = [INBOX_HEAD, f'\n## Open ({len(open_q)})\n' if open_q else '\nNo open questions.\n']
    for t in open_q:
        f = t['finding']
        out.append(f"\n## {t['question']} · {f['severity']} · {f['board']} · {f['kind']}\n\n"
                   f"- **From:** `{t['source']['report']}` {f['id']} ({f.get('location', '')}); task {t['id']}\n"
                   f"- **Summary:** {f['summary']}\n"
                   f"- **Proposed:** {f.get('fix') or '–'}\n"
                   f"- **Why it needs you:** {'; '.join(t['why_big'])}\n\n"
                   f"**Answer:** \n\n---\n")
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
        for key in ('id', 'kind', 'severity', 'board', 'summary', 'class'):
            if key not in f:
                raise ValueError(f'entry {i}: missing {key}')
        if f['kind'] not in KINDS or f['severity'] not in SEVERITIES or f['board'] not in SCOPES:
            raise ValueError(f"entry {f['id']}: bad kind, severity or board")
    return items


def why_big(f):
    """Policy reasons that make a finding big; empty means small (docs/AUTONOMY.md)."""
    why = []
    if f['class'] != 'small':
        why.append(f"reviewer classed it {f['class']}" + (f": {f['reason']}" if f.get('reason') else ''))
    if f['kind'] == 'question':
        why.append('a question only the owner can answer')
    if f['severity'] == 'CRITICAL':
        why.append('CRITICAL')
    if f['board'] == 'system':
        why.append('affects both boards')
    if f.get('touches'):
        why.append('touches ' + ', '.join(f['touches']))
    if abs(f.get('cost_delta_usd') or 0) > SMALL_COST_LIMIT:
        why.append(f"cost change {f['cost_delta_usd']:+.2f} USD per board")
    return why


def triage(q, report, items):
    """Turn findings into tasks and questions. Returns (small, big, duplicates, critical)."""
    seen = {(t['finding']['board'], t['finding'].get('location'), t['finding']['summary'])
            for t in q['tasks'] if t.get('finding') and t['state'] not in ('done', 'failed')}
    small = big = dup = crit = 0
    for f in items:
        key = (f['board'], f.get('location'), f['summary'])
        if key in seen:
            dup += 1
            continue
        seen.add(key)
        why = why_big(f)
        role = 'board-fix' if f['board'] in BOARDS and f['kind'] != 'question' else 'system'
        t = dict(id=new_id(q, 'T'), role=role, scope=f['board'], created=today(), finding=f,
                 source=dict(report=str(report), finding=f['id']))
        if why:
            t.update(state='blocked-owner', question=new_id(q, 'Q'), why_big=why)
            big += 1
        else:
            t.update(state='parked')
            small += 1
        crit += f['severity'] == 'CRITICAL'
        q['tasks'].append(t)
    return small, big, dup, crit


# ---------------------------------------------------------------- running one task

def agent_tools(role):
    m = re.search(r'^tools:\s*(.+)$', (WORKTREE / '.claude' / 'agents' / f'{role}.md').read_text(), re.M)
    return [s.strip() for s in m.group(1).split(',')]


def report_path(t):
    name = f"{today()}-{ROLES[t['role']]['kind']}-{t['scope']}" + (f"-{t['focus']}" if t.get('focus') else '')
    path, n = REVIEWS / f'{name}.md', 2
    while (WORKTREE / path).exists() or path in RESERVED:
        path, n = REVIEWS / f'{name}-{n}.md', n + 1
    return path


def prompt_for(t, report):
    focus = f" Focus: {t['focus']}." if t.get('focus') else ''
    ruling = f" The owner ruled on this task: {t['ruling']}." if t.get('ruling') else ''
    return (f"Unattended run, task {t['id']}. Scope: {t['scope']}.{focus}{ruling} Today is {today()}.\n"
            f"Follow your instructions, CLAUDE.md and docs/AUTONOMY.md. Nobody will answer questions: put them in the "
            f"finding block as kind \"question\" and carry on.\n"
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
    tail = f'tail -n +1 -F {shlex.quote(str(log))}'
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
    content = (event.get('message') or {}).get('content')
    content = content if isinstance(content, list) else []
    if kind == 'system' and event.get('subtype') == 'init':
        return [f"● started on {event.get('model')}"]
    if kind == 'assistant':
        lines = []
        for c in content:
            if c.get('type') == 'tool_use':
                i = c.get('input') or {}
                arg = (i.get('command') or i.get('file_path') or i.get('pattern') or i.get('url') or i.get('query')
                       or json.dumps(i, ensure_ascii=False))
                lines.append(f"▸ {c['name']}: {' '.join(str(arg).split())[:160]}")
            elif c.get('type') == 'text' and c['text'].strip():
                lines.append('“ ' + ' '.join(c['text'].split())[:240])
        return lines
    if kind == 'user':
        return ['  ✗ ' + ' '.join(str(c.get('content')).split())[:160] for c in content if c.get('is_error')]
    if kind == 'result':
        return [f"■ {event.get('terminal_reason') or event.get('subtype')}, "
                f"{float(event.get('total_cost_usd') or 0):.2f} USD"]
    return []


def run_streaming(cmd, env, tag, task_log, cwd):
    """Run one agent, writing a readable trace to its log and to live.log (tail it in tmux); return the result
    event, or an error dict shaped like one."""
    proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    timed_out = threading.Event()
    timer = threading.Timer(TASK_TIMEOUT, lambda: (timed_out.set(), proc.kill()))
    timer.start()
    out, other = None, []
    with open(task_log, 'a') as tl, open(LOGS / 'live.log', 'a') as live:
        for line in proc.stdout:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                other.append(line.strip())
                continue
            if event.get('type') == 'result':
                out = event
            for text in describe(event):
                stamped = f'{datetime.datetime.now():%H:%M:%S} {tag} {text}\n'
                tl.write(stamped)
                live.write(stamped)
            tl.flush()
            live.flush()
    proc.wait()
    timer.cancel()
    if out is None:
        out = dict(is_error=True, result=f'timeout after {TASK_TIMEOUT} s' if timed_out.is_set() else
                   f"exit {proc.returncode}: {' '.join(other)[-300:]}")
    return out


def task_budget(t, budget_left):
    return min(ROLES[t['role']]['budget'][bool(t.get('deep'))], budget_left)


def run_task(q, t, budget_left, dry_run=False):
    """Run one agent in its own worktree, then (under STATE) check it, triage and commit on auto/pilot.
    Thread-safe: several run at once."""
    deep = bool(t.get('deep'))
    model = t.get('model') or ROLES[t['role']]['model'][deep]
    budget = task_budget(t, budget_left)
    with STATE:
        report = report_path(t)
        RESERVED.add(report)
    scratch = Path(tempfile.mkdtemp(prefix=f"pdm-{t['id']}-"))
    cmd = [CLAUDE_BIN, '-p', prompt_for(t, report), '--agent', t['role'], '--model', model,
           '--max-budget-usd', f'{budget:.2f}', '--output-format', 'stream-json', '--verbose',
           '--no-session-persistence',
           '--add-dir', str(scratch), '--allowedTools', *agent_tools(t['role']), 'Write',
           '--disallowedTools', *DENIED_TOOLS]
    print(f"→ {t['id']} {t['role']} {t['scope']}{' deep' if deep else ''} ({model}, ≤ {budget:.2f} USD) → {report}")
    if dry_run:
        print('  ' + ' '.join(c if ' ' not in c else repr(c[:60] + '…') for c in cmd))
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
    log = LOGS / f"{t['id']}-{datetime.datetime.now():%Y%m%d-%H%M%S}.json"
    env = dict(os.environ, CLAUDE_JOB_DIR=str(scratch), PATH=f"{KICAD_BIN_DIR}:{os.environ.get('PATH', '')}")
    pane = tmux_pane(t, log.with_suffix('.log'))
    try:
        out = run_streaming(cmd, env, t['id'], log.with_suffix('.log'), wt)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
        tmux_close(pane)
    log.write_text(json.dumps(dict(cmd=cmd, output=out), indent=2, ensure_ascii=False))
    cost = float(out.get('total_cost_usd') or 0)
    notes = []
    if out.get('permission_denials'):
        denied = sorted({d.get('tool_name', '?') for d in out['permission_denials']})
        notes.append(f"{len(out['permission_denials'])} tool calls denied ({', '.join(denied)}); log {log.name}")

    with STATE:
        t['cost_usd'] = round(t.get('cost_usd', 0) + cost, 4)
        t['attempts'] = t.get('attempts', 0) + 1
        # Gate 1: the agent must not have moved its worktree's HEAD; keep the worktree for inspection if it did.
        keep = git('rev-parse', 'HEAD', cwd=wt) != head
        if keep:
            notes.append(f'agent changed HEAD (was {head[:8]}); inspect {wt}')
        # Gate 2: only one new report in docs/reviews/; everything else is dropped with the worktree.
        changed = changed_paths(wt)
        reports = [p for p in changed if p.startswith(f'{REVIEWS}/') and p.endswith('.md')
                   and not git('ls-files', '--', p, cwd=wt)]
        got = str(report) if str(report) in reports else (reports[0] if len(reports) == 1 else None)
        if got and keep:
            got = None
        stray = [p for p in changed if p != got]
        if stray:
            notes.append('dropped ' + ', '.join(stray))
        # Gate 3: the report carries a valid finding block; then it moves to auto/pilot.
        result = None
        if got is None:
            notes.append(f"no report written ({out.get('terminal_reason') or out.get('subtype') or 'unknown'}): "
                         f"{str(out.get('result', ''))[:200]}")
        else:
            text = (wt / got).read_text()
            try:
                items = parse_block(text)
                if (WORKTREE / got).exists():  # another agent took the name meanwhile
                    got = str(Path(got).with_name(f"{Path(got).stem}-{t['id']}.md"))
                (WORKTREE / got).parent.mkdir(parents=True, exist_ok=True)
                (WORKTREE / got).write_text(text)
                small, big, dup, crit = triage(q, got, items)
                result = dict(report=got, small=small, big=big, duplicates=dup, critical=crit)
            except (ValueError, json.JSONDecodeError) as e:
                notes.append(f'report {got}: {e}')
                got = None
        # A usage limit or API outage is not the task's fault: leave it ready and let the caller stop the run.
        paused = result is None and not keep and (out.get('terminal_reason') == 'api_error'
                                                  or bool(UNAVAILABLE.search(str(out.get('result', '')))))
        t.update(state='done' if result else 'ready' if paused else 'failed', finished=today(),
                 note='; '.join(notes) or None)
        if result:
            t['report'] = got
        write_inbox(WORKTREE, q)
        save_queue(WORKTREE, q)
        git('add', '--', *([str(QUEUE), str(INBOX)] + ([got] if got else [])))
        summary = (f"{result['small']} small, {result['big']} for the owner, {result['duplicates']} duplicates"
                   if result else 'paused, API unavailable' if paused else 'failed')
        git('commit', '-m', f"Auto: {t['role']} {t['scope']} ({t['id']}): {summary}\n\n"
            f"Unattended run by tools/orchestrate.py, model {model}, {cost:.2f} USD.\n\n"
            f"Co-Authored-By: Claude <noreply@anthropic.com>")
        if not keep:
            git('worktree', 'remove', '--force', str(wt), check=False)
        RESERVED.discard(report)
        print(f"  {t['id']} {t['state']}: {summary}; {cost:.2f} USD" + (f"; {t['note']}" if t.get('note') else ''),
              flush=True)
    return cost, result


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


# ---------------------------------------------------------------- commands

def cmd_status(args):
    root = state_root()
    q = load_queue(root)
    answers = read_answers(root)
    waiting = [t for t in q['tasks'] if t['state'] == 'blocked-owner' and t['question'] in answers]
    order = ('running', 'ready', 'blocked-owner', 'failed', 'parked', 'done')
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
    spent, ran, fails, new_q, stop = 0.0, 0, 0, 0, None
    running = {}  # future -> (task, cap)
    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        while True:
            while not stop and len(running) < args.parallel and ran < limit:
                with STATE:
                    todo = [find_task(q, args.task)] if args.task else runnable(q)
                    todo = [t for t in todo if t['state'] == 'ready' and t['role'] in ROLES]
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
                if not result and t['state'] == 'ready':
                    stop = stop or f"API unavailable ({t['note'][-100:]}); {t['id']} stays ready"
                    continue
                fails = 0 if result else fails + 1
                new_q += result['big'] if result else 0
                if result and result['critical']:
                    stop = stop or f"CRITICAL finding in {result['report']}, see the owner inbox"
                if fails >= 2:
                    stop = stop or 'two tasks failed in a row'
            if stop and running:
                print(f'stopping after the {len(running)} running agent(s) finish: {stop}', flush=True)
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
    s = sub.add_parser('retry', help='set a failed task ready again')
    s.add_argument('task')
    s.set_defaults(fn=cmd_retry)
    for name, fn, text in (('run', cmd_run, 'run ready tasks'), ('inbox', cmd_inbox, 'apply owner answers only')):
        s = sub.add_parser(name, help=text)
        s.add_argument('--base', default='main', help='branch merged into auto/pilot first (default main)')
        s.set_defaults(fn=fn)
        if name == 'run':
            s.add_argument('--max-tasks', type=int, default=4)
            s.add_argument('--parallel', type=int, default=3, help='agents running at once (default 3)')
            s.add_argument('--budget', type=float, default=60.0, help='USD for this run (default 60)')
            s.add_argument('--task', help='run only this task')
            s.add_argument('--dry-run', action='store_true', help='print the agent commands, run nothing')
            s.add_argument('--push', action='store_true', help=f'push {BRANCH} to origin afterwards')
    args = ap.parse_args()
    args.fn(args)


if __name__ == '__main__':
    main()
