#!/usr/bin/env python3
"""Land the current branch on origin/main (decision 129): the one place all work ends up.

Used by every Claude session before it ends (CLAUDE.md, /handoff) and by tools/orchestrate.py after each merged
package and at the end of a run. Run it from the worktree whose HEAD should land:

  python3 tools/land.py            # fetch, merge origin/main, check, push HEAD to main
  python3 tools/land.py --check    # only fetch, merge and check; push nothing

Steps:
1. Refuse if tracked files have uncommitted changes (commit first).
2. `git fetch origin main`, then merge origin/main into HEAD. STATUS.md and decisions.md merge with `union`
   (.gitattributes), so parallel appends do not stop the merge. Any other conflict: the merge is aborted and the
   conflicting files are listed (exit 2) - resolve them in a normal merge, then run this again.
3. Duplicate decision numbers after the merge (two sessions took the same next number): exit 3 with the numbers.
   Renumber the newer row (and its references), commit, run again.
4. `git push origin HEAD:main` (a fast-forward, since origin/main is merged in).
5. Fast-forward the local main checkout if it is clean, so the owner's folder shows the result; delete the remote
   branch of a `worktree-*` session branch, which has now landed.
Exit 0 = landed (or nothing to land).
"""
import argparse
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path


def git(*args, cwd=None, check=True):
    r = subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True)
    if check and r.returncode:
        sys.exit(f'land: git {" ".join(args)} failed:\n{(r.stderr or r.stdout).strip()}')
    return r


def duplicate_decisions(root):
    p = Path(root) / 'docs' / 'decisions.md'
    if not p.exists():
        return []
    nums = Counter(m.group(1) for m in re.finditer(r'^\| (\d+) \|', p.read_text(), re.M))
    return sorted((n for n, c in nums.items() if c > 1), key=int)


def main_checkout():
    """Path of the worktree that has main checked out, or None."""
    out = git('worktree', 'list', '--porcelain').stdout
    path = None
    for line in out.splitlines():
        if line.startswith('worktree '):
            path = line.split(' ', 1)[1]
        elif line == 'branch refs/heads/main':
            return path
    return None


def land(check_only=False, quiet=False):
    say = (lambda *a: None) if quiet else print
    root = git('rev-parse', '--show-toplevel').stdout.strip()
    branch = git('rev-parse', '--abbrev-ref', 'HEAD').stdout.strip()
    if git('status', '--porcelain', '--untracked-files=no').stdout.strip():
        sys.exit('land: uncommitted changes to tracked files; commit them first')
    git('fetch', '-q', 'origin', 'main')
    r = git('merge', '--no-edit', '-m', f'Merge origin/main into {branch}', 'origin/main', check=False)
    if r.returncode:
        conflicts = git('diff', '--name-only', '--diff-filter=U').stdout.split()
        git('merge', '--abort', check=False)
        print(f'land: merging origin/main conflicts in: {", ".join(conflicts) or "(unknown)"}', file=sys.stderr)
        sys.exit(2)
    dups = duplicate_decisions(root)
    if dups:
        print(f'land: decision numbers used twice after the merge: {", ".join(dups)}; renumber the newer rows',
              file=sys.stderr)
        sys.exit(3)
    ahead = int(git('rev-list', '--count', 'origin/main..HEAD').stdout.strip())
    if check_only:
        say(f'land: check ok, {ahead} commit(s) would land')
        return 0
    if ahead:
        git('push', '-q', 'origin', 'HEAD:main')
        say(f'land: {ahead} commit(s) pushed to origin/main ({git("rev-parse", "--short", "HEAD").stdout.strip()})')
    else:
        say('land: nothing to land, origin/main already has HEAD')
    git('fetch', '-q', 'origin', 'main')
    mc = main_checkout()
    if mc and Path(mc).resolve() != Path(root).resolve():
        if git('status', '--porcelain', '--untracked-files=no', cwd=mc).stdout.strip():
            say(f'land: {mc} has uncommitted changes; not updated (run `git pull --ff-only` there later)')
        elif git('merge', '-q', '--ff-only', 'origin/main', cwd=mc, check=False).returncode:
            say(f'land: {mc} could not fast-forward (local commits or untracked files in the way); not updated')
        else:
            say(f'land: {mc} fast-forwarded to origin/main')
    if branch.startswith('worktree-'):
        if git('ls-remote', '--exit-code', '--heads', 'origin', branch, check=False).returncode == 0:
            git('push', '-q', 'origin', '--delete', branch, check=False)
            say(f'land: deleted the remote branch {branch} (it has landed)')
    return 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true', help='fetch, merge and check only; push nothing')
    sys.exit(land(check_only=ap.parse_args().check))
