#!/usr/bin/env python3
"""Run the orchestrator's merge gates on the current worktree before handing in a work package.

Same checks as tools/orchestrate.py applies after a board-fixer finishes: files only in the package scope, no PDFs,
ERC not worse on either board, netlist changes only on the declared refs, LCSC (or DNP) on every new or changed part,
shared sheets identical on both boards. Also prints how much the change grows each board.

  python3 tools/fix_check.py --scope shared --refs C14,R12
  python3 tools/fix_check.py --scope pdm-hc2 --refs Q2,R101 --base <commit>     (default: $PDM_BASE, else HEAD)
"""
import argparse
import importlib.util
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('orchestrate', ROOT / 'tools' / 'orchestrate.py')
o = importlib.util.module_from_spec(spec)
spec.loader.exec_module(o)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--scope', required=True, choices=o.FIX_SCOPES)
    ap.add_argument('--refs', default='', help='comma-separated reference designators you changed')
    ap.add_argument('--base', default=os.environ.get('PDM_BASE', 'HEAD'), help='commit the package started from')
    a = ap.parse_args()
    o.WORKTREE = ROOT  # git and the base snapshot come from this worktree
    d = Path(tempfile.mkdtemp(prefix='fix-check-'))
    try:
        base_tree = o.base_tree(o.git('rev-parse', a.base), d)
        before = {b: o.kicad_check(base_tree, b, d) for b in o.BOARDS}
        after = {b: o.kicad_check(ROOT, b, d) for b in o.BOARDS}
        block = dict(refs=[r.strip() for r in a.refs.split(',') if r.strip()])
        fails = o.fix_gates(ROOT, dict(scope=a.scope), before, after, block, o.changed_paths(ROOT), None)
        for b in o.BOARDS:
            if before[b] and after[b]:
                s, n = o.board_size(before[b]), o.board_size(after[b])
                print(f"{b}: ERC {after[b]['errors']} errors/{after[b]['warnings']} warnings; "
                      f"{n['parts']} parts ({n['parts'] - s['parts']:+d}), {n['dnp']} DNP ({n['dnp'] - s['dnp']:+d}), "
                      f"{n['unique']} unique ({n['unique'] - s['unique']:+d})")
    finally:
        shutil.rmtree(d, ignore_errors=True)
    if fails:
        print('NOT READY – the orchestrator would reject this:')
        print('\n'.join(f'  - {f}' for f in fails))
        sys.exit(1)
    print('OK – passes the merge gates')


if __name__ == '__main__':
    main()
