#!/usr/bin/env python3
"""Orchestrator for unattended agent runs (decision 20, docs/AUTONOMY.md).

Runs queued tasks one at a time as headless Claude Code sessions (`claude -p --agent <role>`), each in a fresh
context, in a dedicated worktree on the branch `auto/pilot`. After every task it checks the result itself instead of
trusting the agent: only the expected report in docs/reviews/ may change, the report must end with a valid finding
block. It then sorts the findings by the policy in docs/AUTONOMY.md: small ones become parked `board-fix` tasks, big
ones become owner questions in docs/OWNER-INBOX.md. Each task is committed on `auto/pilot`; the owner merges.

Pilot: only the reviewer roles run (validator, emc-reviewer, cost-controller).

Examples:
  python3 tools/orchestrate.py status
  python3 tools/orchestrate.py run --dry-run
  python3 tools/orchestrate.py run --max-tasks 4 --budget 60
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
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BRANCH = 'auto/pilot'
WORKTREE = REPO / '.claude' / 'worktrees' / 'auto'
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
KINDS = ('finding', 'lever', 'question')


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

Questions the agents may not decide themselves (decision 20, `docs/AUTONOMY.md`). Write your ruling on each
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
    while (WORKTREE / path).exists():
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


def changed_paths():
    out = subprocess.run(['git', 'status', '--porcelain', '-z', '--untracked-files=all'], cwd=WORKTREE,
                         capture_output=True, text=True, check=True).stdout
    paths, entries = [], iter(out.split('\0'))
    for e in entries:
        if e:
            paths.append(e[3:])
            if e[0] in 'RC':  # renames carry the old path as the next entry
                next(entries, None)
    return paths


def revert(paths):
    for p in paths:
        if git('ls-files', '--', p):
            git('checkout', '--', p)
        else:
            (WORKTREE / p).unlink(missing_ok=True)


def run_task(q, t, budget_left, dry_run):
    deep = bool(t.get('deep'))
    spec = ROLES[t['role']]
    model = t.get('model') or spec['model'][deep]
    budget = min(spec['budget'][deep], budget_left)
    report = report_path(t)
    scratch = Path(tempfile.mkdtemp(prefix=f"pdm-{t['id']}-"))
    cmd = [CLAUDE_BIN, '-p', prompt_for(t, report), '--agent', t['role'], '--model', model,
           '--max-budget-usd', f'{budget:.2f}', '--output-format', 'json', '--no-session-persistence',
           '--add-dir', str(scratch), '--allowedTools', *agent_tools(t['role']), 'Write',
           '--disallowedTools', *DENIED_TOOLS]
    print(f"→ {t['id']} {t['role']} {t['scope']}{' deep' if deep else ''} ({model}, ≤ {budget:.2f} USD) → {report}")
    if dry_run:
        print('  ' + ' '.join(c if ' ' not in c else repr(c[:60] + '…') for c in cmd))
        return 0.0, None
    head = git('rev-parse', 'HEAD')
    env = dict(os.environ, CLAUDE_JOB_DIR=str(scratch), PATH=f"{KICAD_BIN_DIR}:{os.environ.get('PATH', '')}")
    t.update(state='running', started=datetime.datetime.now().isoformat(timespec='seconds'), model=model)
    save_queue(WORKTREE, q)
    (WORKTREE / REVIEWS).mkdir(parents=True, exist_ok=True)  # empty folders are not in git
    try:
        r = subprocess.run(cmd, cwd=WORKTREE, env=env, capture_output=True, text=True, timeout=TASK_TIMEOUT)
        out = json.loads(r.stdout)
    except subprocess.TimeoutExpired:
        out = dict(is_error=True, result=f'timeout after {TASK_TIMEOUT} s')
    except json.JSONDecodeError:
        out = dict(is_error=True, result=f'exit {r.returncode}: ' + (r.stderr or r.stdout).strip()[-300:])
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    cost = float(out.get('total_cost_usd') or 0)
    t['cost_usd'] = round(t.get('cost_usd', 0) + cost, 4)
    t['attempts'] = t.get('attempts', 0) + 1
    notes = []
    if out.get('permission_denials'):
        notes.append(f"{len(out['permission_denials'])} tool calls denied")

    # Gate 1: the agent must not have moved the branch.
    if git('rev-parse', 'HEAD') != head:
        t.update(state='failed', note=f'agent changed HEAD (was {head[:8]}); stop and inspect {WORKTREE}')
        save_queue(WORKTREE, q)
        raise SystemExit(t['note'])
    # Gate 2: only one new report in docs/reviews/; everything else is reverted.
    changed = [p for p in changed_paths() if p not in (str(QUEUE), str(INBOX))]
    reports = [p for p in changed if p.startswith(f'{REVIEWS}/') and p.endswith('.md') and not git('ls-files', '--', p)]
    got = str(report) if str(report) in reports else (reports[0] if len(reports) == 1 else None)
    stray = [p for p in changed if p != got]
    if stray:
        revert(stray)
        notes.append('reverted ' + ', '.join(stray))
    # Gate 3: the report carries a valid finding block.
    result = None
    if got is None:
        notes.append('no report written' + (f": {str(out.get('result', ''))[:200]}" if out.get('is_error') else ''))
    else:
        try:
            items = parse_block((WORKTREE / got).read_text())
            small, big, dup, crit = triage(q, got, items)
            result = dict(report=got, small=small, big=big, duplicates=dup, critical=crit)
        except (ValueError, json.JSONDecodeError) as e:
            notes.append(f'report {got}: {e}')
            revert([got])
            got = None
    t.update(state='done' if result else 'failed', finished=today(), note='; '.join(notes) or None)
    if result:
        t['report'] = got
    write_inbox(WORKTREE, q)
    save_queue(WORKTREE, q)
    paths = [str(QUEUE), str(INBOX)] + ([got] if got else [])
    git('add', '--', *paths)
    summary = (f"{result['small']} small, {result['big']} for the owner, {result['duplicates']} duplicates"
               if result else 'failed')
    git('commit', '-m', f"Auto: {t['role']} {t['scope']} ({t['id']}): {summary}\n\n"
        f"Unattended run by tools/orchestrate.py, model {model}, {cost:.2f} USD.\n\n"
        f"Co-Authored-By: Claude <noreply@anthropic.com>")
    print(f"  {t['state']}: {summary}; {cost:.2f} USD" + (f"; {t['note']}" if t.get('note') else ''))
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
    spent, ran, fails, new_q = 0.0, 0, 0, 0
    while ran < args.max_tasks:
        todo = [find_task(q, args.task)] if args.task else runnable(q)
        todo = [t for t in todo if t['state'] == 'ready' and t['role'] in ROLES]
        if not todo:
            break
        if args.budget - spent < 1.0:
            notify(f'Run budget of {args.budget:.0f} USD used up')
            break
        cost, result = run_task(q, todo[0], args.budget - spent, dry_run=False)
        spent += cost
        ran += 1
        fails = 0 if result else fails + 1
        new_q += result['big'] if result else 0
        if result and result['critical']:
            notify(f"CRITICAL finding in {result['report']}: run stopped, see the owner inbox")
            break
        if fails >= 2:
            notify('Two tasks failed in a row: run stopped')
            break
        if args.task:
            break
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
            s.add_argument('--budget', type=float, default=60.0, help='USD for this run (default 60)')
            s.add_argument('--task', help='run only this task')
            s.add_argument('--dry-run', action='store_true', help='print the agent commands, run nothing')
            s.add_argument('--push', action='store_true', help=f'push {BRANCH} to origin afterwards')
    args = ap.parse_args()
    args.fn(args)


if __name__ == '__main__':
    main()
