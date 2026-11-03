#!/usr/bin/env python3
"""Check a report's machine-readable block exactly as the orchestrator will, before handing it in.

Reviewer reports end with the finding block, planner reports with the plan block, board-fixer reports with the fix
block (format: docs/AUTONOMY.md). A report with nothing to report still needs the block (an empty list for findings).
In an unattended run the report path and block come from $PDM_REPORT and $PDM_BLOCK; otherwise name them.

  python3 tools/report_check.py
  python3 tools/report_check.py docs/reviews/2026-11-03-validate-pdm-4ch.md --block finding
"""
import argparse
import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('orchestrate', ROOT / 'tools' / 'orchestrate.py')
o = importlib.util.module_from_spec(spec)
spec.loader.exec_module(o)
KIND = {'finding': 'validate', 'plan': 'plan', 'fix': 'fix'}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('report', nargs='?', default=os.environ.get('PDM_REPORT'))
    ap.add_argument('--block', choices=KIND, default=os.environ.get('PDM_BLOCK', 'finding'))
    a = ap.parse_args()
    if not a.report:
        ap.error('name the report (no $PDM_REPORT set)')
    path = Path(a.report) if Path(a.report).is_absolute() else Path.cwd() / a.report
    if not path.exists():
        print(f'NOT READY – no report at {a.report}')
        sys.exit(1)
    problems = o.check_report(KIND[a.block], path.read_text())
    if problems:
        print('NOT READY – the orchestrator would reject this report:')
        print('\n'.join(f'  - {p}' for p in problems))
        if a.block == 'finding':
            print('  (no findings? end the report with: <!-- findings:begin --> ```json [] ``` <!-- findings:end -->'
                  ' on separate lines)')
        sys.exit(1)
    print(f'OK – {a.report} has a valid {a.block} block')


if __name__ == '__main__':
    main()
