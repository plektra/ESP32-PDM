#!/usr/bin/env python3
"""Part facts from the shared cache, or from the part-facts agent on Sonnet (docs/AUTONOMY.md, "Tools and cost").

Prints the verified facts of one part. If docs/part-facts/<ID>.md exists it is printed and no model is called.
Otherwise the part-facts agent reads the maker's datasheet in its own session (the PDF text never enters the
caller's context), writes the facts file with citations and the file is printed. --more asks it to add answers to
an existing file. Never stores PDFs (public repo).

  python3 tools/part_facts.py C19077549 "pinout, VBR/VC at 1 A, Ipp, package"
  python3 tools/part_facts.py C19077549 --more "clamp voltage at 10 A"

Environment set by tools/orchestrate.py for unattended agents: PDM_COST_LEDGER (cost of each lookup is appended
for the run budget), PDM_FACTS_MAX (lookups allowed per task). CLAUDE_BIN, PDM_FACTS_MODEL (default sonnet).
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

FACTS = Path('docs/part-facts')
MODEL = os.environ.get('PDM_FACTS_MODEL', 'sonnet')
BUDGET_USD = 1.50  # per lookup
TOOLS = ['Read', 'Grep', 'Glob', 'Bash', 'WebFetch', 'WebSearch', 'mcp__pcbparts__jlc_get_part',
         'mcp__pcbparts__jlc_search', 'mcp__pcbparts__jlc_get_pinout']


def ledger_entries(ledger):
    return [json.loads(line) for line in Path(ledger).read_text().splitlines() if line.strip()] \
        if ledger and Path(ledger).exists() else []


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('part', help='LCSC code (C…) or maker part number')
    ap.add_argument('needed', nargs='?', default='pinout, package, absolute maximum ratings, key electrical limits')
    ap.add_argument('--more', metavar='QUESTIONS', help='add answers to an existing facts file')
    args = ap.parse_args()
    part = re.sub(r'[^A-Za-z0-9._-]', '_', args.part)
    path = FACTS / f'{part}.md'
    if path.exists() and not args.more:
        print(path.read_text())
        return
    ledger, cap = os.environ.get('PDM_COST_LEDGER'), int(os.environ.get('PDM_FACTS_MAX', '15'))
    if len(ledger_entries(ledger)) >= cap:
        sys.exit(f'part_facts: limit of {cap} lookups for this task reached; use what you have or stop with a '
                 f'blocked item')
    FACTS.mkdir(parents=True, exist_ok=True)
    ask = args.more or args.needed
    prompt = (f"Look up part {args.part}. Needed: {ask}.\n"
              f"{'Add the answers to' if args.more else 'Write'} the facts file `{path}` in the format of "
              f"`{FACTS}/README.md`: every figure with document, revision and page; UNVERIFIED where no primary "
              f"source. Download the datasheet to $CLAUDE_JOB_DIR (never into the repository) and read it with "
              f"`$PDM_PDF_PYTHON -I` (pypdf, pypdfium2). Change no other file. Your final message: the facts file.")
    allowed = TOOLS + [f'Write({path})', f'Edit({path})']
    cmd = [os.environ.get('CLAUDE_BIN', 'claude'), '-p', prompt, '--agent', 'part-facts', '--model', MODEL,
           '--max-budget-usd', f'{BUDGET_USD:.2f}', '--output-format', 'json', '--no-session-persistence',
           '--allowedTools', *allowed, '--disallowedTools', 'Agent', 'Bash(git:*)', 'Bash(rm -rf:*)']
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        out = json.loads(r.stdout)
    except json.JSONDecodeError:
        out = dict(is_error=True, result=(r.stderr or r.stdout)[-300:])
    if ledger:
        with open(ledger, 'a') as fh:
            fh.write(json.dumps(dict(part=args.part, cost_usd=out.get('total_cost_usd') or 0,
                                     ok=path.exists())) + '\n')
    if path.exists():
        print(path.read_text())
    else:
        sys.exit(f"part_facts: no facts file written for {args.part}: {str(out.get('result'))[:300]}")


if __name__ == '__main__':
    main()
