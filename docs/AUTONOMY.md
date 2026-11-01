# Autonomous runs

How agents work without the owner in the loop (decisions 22 and 23). The orchestrator is `tools/orchestrate.py`;
agents talk to each other only through files: reports in `docs/reviews/`, tasks in `docs/queue.json`, questions for
the owner in `docs/OWNER-INBOX.md`.

## Policy: one-way doors go to the owner, two-way doors are decided by agents (decision 23)

The test is not how big or how wide a change is, but **whether it can be undone cheaply**. Before a board is ordered,
almost every design change is a git commit that the gates check and a revert undoes: a two-way door. Agents decide
those and say so; the owner can undo any of them. Only one-way doors wait for the owner.

**One-way door – the owner decides.** Any of these:

1. **Money:** an order or purchase (PCBs, parts, assembly), or a change to a board that has been ordered (see
   "Ordered boards").
2. **The owner's rulings:** the fix would change or contradict a decision that is confirmed, **[proposed]** or open
   in `docs/decisions.md` (decisions marked **auto** are the agents' own and may be changed).
3. **Safety:** the fix removes or weakens protection or safety-relevant behaviour: bilge pumps, navigation lights,
   anything that can trap or burn, and invariants 1 (switch works without the MCU), 2 (no relays), 6 (no path to the
   hull) and 8 (float switch independent of the PDM). Changing or relaxing any invariant in `ARCHITECTURE.md`.
4. **Facts only the owner has:** measurements on Vega, how the boat is used, preferences – a question without a
   sensible default.
5. **CRITICAL findings:** the agent proposes the fix; the owner confirms it.

When in doubt whether something can be undone cheaply, it is a one-way door.

**Two-way door – an agent decides.** Everything else, for example: component values, part swaps (also to an extended
part), shared-sheet changes made identically on both boards in one run, pin-map changes that the netlist gates check,
cost levers that keep every must-stay function, connector pinouts before the order, layout rules, documentation. A
question that has a sensible default is answered with that default and the assumption is stated.

Every two-way decision is recorded and shown to the owner in the **digest** of `docs/OWNER-INBOX.md`, one line each
with its undo command. A design decision an agent makes goes into `docs/decisions.md` with status **auto**. The owner
undoes one with `python3 tools/orchestrate.py undo T-0012`: it comes back as a question (and, once fixes are applied
by agents, its commit is reverted).

**Ordered boards.** When a board is ordered, the door closes: list it under `"ordered"` in `docs/queue.json`
(e.g. `"ordered": ["pdm-4ch"]`). From then on every change to that board, and every `system` change, is a one-way
door until the next revision is opened.

## Finding block (every reviewer report)

Every report in `docs/reviews/` ends with one machine-readable block. The orchestrator reads only this block; the
prose above it is for people.

````
<!-- findings:begin -->
```json
[
  {
    "id": "E1",
    "kind": "finding",
    "severity": "MAJOR",
    "board": "pdm-4ch",
    "location": "analog_sw: SW1 input, R12/C7",
    "summary": "one line: what is wrong",
    "fix": "one line: what would resolve it",
    "door": "two-way",
    "reason": "why it can or cannot be undone cheaply (policy item)",
    "touches": [],
    "cost_delta_usd": 0.0
  },
  {
    "id": "E2",
    "kind": "question",
    "severity": "INFO",
    "board": "system",
    "summary": "Which cable length should the switch inputs be rated for?",
    "default": "10 m, the longest run on a 20 m boat",
    "door": "two-way",
    "reason": "a sensible default exists; the filter values can be changed later",
    "touches": []
  }
]
```
<!-- findings:end -->
````

- `kind`: `finding` (a problem), `lever` (cost saving or improvement) or `question`.
- `severity`: `CRITICAL`, `MAJOR`, `MINOR` or `INFO` (levers and questions: `INFO` unless they fix a problem).
- `board`: `pdm-4ch`, `pdm-hc2` or `system`.
- `door`: `two-way` or `one-way` under the policy above; `reason` names the policy item.
- `default`: for a question, the answer the agents will assume. A question without `default` goes to the owner.
- `touches`: what **the fix would change**, from `money`, `decision:<N>` (only when the fix changes or contradicts
  decision N), `safety`, `invariant` (the fix changes or relaxes an invariant), `owner-fact`, and for information
  `shared-sheet`, `pin-map`, `budget`, `connector`, `protection`, `new-extended-part`, `mechanical`, `firmware`.
  Empty if none.
- `cost_delta_usd`: change per board at 10 units if known, otherwise omit.
- An empty review still writes `[]`.

The orchestrator does not take the reviewer's word for `two-way`. It makes a finding one-way when it is CRITICAL, a
question without `default`, touches `money`, `safety`, `invariant` or `owner-fact`, touches `decision:<N>` for a
decision the owner holds (confirmed, **[proposed]** or open), or concerns an ordered board (or `system` while any
board is ordered).

## Queue and inbox

- `docs/queue.json` – tasks: `id`, `role`, `scope`, `state` (`ready`, `running`, `done`, `failed`,
  `blocked-owner`, `parked`), `door`, `depends_on`, `source` (the report and finding that created it). Two-way
  findings become `board-fix` tasks (`parked` during the pilot, approved to run); two-way questions are answered with
  their default (`done`, ruling `assumed: …`); one-way items become `blocked-owner` tasks with an inbox question.
- `docs/OWNER-INBOX.md` – open questions first (`Q-0001` …): the owner writes the ruling after **Answer:** (`yes`,
  `no`, or text) or uses `/inbox`; the next run moves answered tasks on: `yes` or a text ruling → `ready`/`parked`
  (the ruling is passed to the agent and becomes a confirmed decision in its handoff), `no` → `done`. Then the digest
  of agent decisions with undo commands, then answered questions.

## Unattended fixes (stage 2, decision 24)

Approved items – the owner's rulings and the agents' two-way decisions (`parked` in the queue) – are applied by
agents without the owner:

1. **Planner** (`.claude/agents/planner.md`) runs when approved items wait and no review is pending. It groups them
   into small work packages (scope `pdm-4ch`, `pdm-hc2` or `shared`), defers what cannot be done yet
   (`system-mechanical`, `pcb`, `prototype`, `firmware`, `order`, `owner`) and drafts decision rows for the owner's
   rulings; the orchestrator appends those to `docs/decisions.md` as **confirmed**.
2. **Board-fixer** (`.claude/agents/board-fixer.md`) applies one package in its own worktree: part facts from
   datasheets, scripted edits with `tools/ksch.py`, ERC and netlist, `STATUS.md`, design notes and failure-mode notes.
   It stops at one-way doors (they come back as owner questions). Its own design choices become **auto** decisions.
3. **Gates** – checked by the orchestrator, not the agent; any failure and nothing is merged (the report is kept
   as `…-rejected.md`):
   - only files in the package's scope changed (`hardware/<board>/`, both boards for `shared`, `lib/`,
     `docs/design-notes.md`, `README.md`; `docs/ARCHITECTURE.md` only for `shared`); no PDFs;
   - ERC on both boards: no more errors and no more warnings than before;
   - netlist on both boards: every part or connection that changed is in the agent's declared `refs`;
   - every new or changed part has an `LCSC` code or is DNP;
   - the shared sheets are identical on both boards (apart from the project name).
4. **Merge** into `auto/pilot`; the items are `done` and listed under "Applied by agents" in the inbox.
   `orchestrate.py undo <item>` reverts the whole package and turns its items into questions.
5. **Re-check:** after a board's packages, a validator reviews it again; its findings go through the door rules, and
   the next planning round picks up what it approves (`run --rounds`, default 2 per run).

One board-fixer per board at a time (a `shared` package holds both). `run --no-fixes` runs reviews only. The owner
merges `auto/pilot` into `main`, and reviews it before any order – ordering is a one-way door.
