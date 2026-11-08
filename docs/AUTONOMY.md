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
4. **Merge** into `auto/pilot`. The orchestrator first merges the newest `auto/pilot` into the agent's worktree
   (outside the lock); a conflict only in Markdown docs (design notes, `STATUS.md`) goes back to the agent to
   resolve, any other conflict re-queues the package to be rebuilt on the new base (up to 3 attempts). The items are `done` and listed under "Applied by agents" in the inbox.
   `orchestrate.py undo <item>` reverts the whole package and turns its items into questions.
5. **Re-check:** after a board's packages, a validator reviews it again; after all design packages of a plan, a
   cost controller prices the change (when any package changed a part) and an EMC reviewer checks it (when a
   connector, ferrite, inductor, diode/TVS, fuse or switch changed) – both limited to the diff, otherwise closed as
   skipped without an agent; their findings go through the door rules, and
   the next planning round picks up what it approves (`run --rounds`, default 2 per run).

**System sync (decision 71).** Interactive `/system` sessions keep the choices; the bookkeeping they used to
collect runs unattended. A board-fixer package with scope `sync` changes no design: it may edit only
`docs/ARCHITECTURE.md` (not the Invariants section), `docs/design-notes.md`, the boards' `STATUS.md` and the inputs
of `tools/heat_budget.py`, to match what is already merged and decided (a part an ARCHITECTURE row still names, a
decision cross-reference, a tool default the design notes prove). The planner plans such items as `sync`; once the
fixes of a run have settled, the orchestrator also queues a sweep of the "For /system" lists whenever they changed.
The sweep syncs the bookkeeping items and leaves every choice – mechanics, terminals, firmware, pin map, invariants,
money, safety and installation rules, owner facts – word for word for `/system`. Gates as above (files, netlists
unchanged on both boards), plus: the Invariants section is unchanged word for word and `tools/heat_budget.py` still
runs. A sync package holds both boards.

**Self-repair.** A problem the agent can fix itself never fails the task at once: a missing or malformed block,
a report at the wrong path or a failed gate is sent back to the agent's own session with the exact problem (up to
2 repairs, same worktree, while budget is left). Only then is the task `failed`; its report is kept as
`…-rejected.md` and a notification goes out at once. Usage limits and cut-off agents pause and resume as before.

**Restraint (against over-engineering).**
- Board-fixers make the smallest change that meets each item: a value change before a new part, a part already on
  the BOM before a new one, nothing "while I'm here" (ideas go to the report as suggestions). The planner plans only
  what the items ask. Reviewers report only findings with a concrete failure mechanism for this product and give the
  cheapest fix.
- The gates measure every package's growth – parts, DNP parts and unique fitted parts per board – and
  `docs/ROADMAP.md` and the dashboard show it per package and since the agents started.
- A re-check after fixes reviews only what changed (`git diff` since the plan), not the whole board again, so
  rounds converge instead of finding new work each time.

**Tools and cost.** Most of an agent's cost is re-reading its own growing conversation on every step, so agents keep
it small and short:
- `tools/part_facts.py <LCSC> "<what>"` – part facts from `docs/part-facts/` (each datasheet read once, text with
  citations, no PDFs), else a Sonnet `part-facts` agent reads the datasheet in its own session (≤ 1.50 USD, at most
  15 lookups per agent attempt; the cost counts toward the task and the run budget).
- `tools/sch_query.py <board> parts|ref|net|erc` – a sheet's parts, a part's connections or a net in one call.
- `tools/fix_check.py --scope … --refs …` – the merge gates, run by the board-fixer before it hands in.
- `tools/report_check.py` – the orchestrator's check of the report's block (finding, plan or fix), run by every
  agent before it hands in; a report with nothing to report still ends with an empty block.
- `run --fixer-model sonnet` runs board-fixers on Sonnet (default Opus); the roadmap's "Done" table shows model and
  cost per package for comparison.

One board-fixer per board at a time (a `shared` package holds both). `run --no-fixes` runs reviews only. Each
task lands on `main` right after it is committed (`tools/land.py`, decision 129): landing is a two-way door (a revert
or `undo` takes it back). The owner reviews `main` before any order – ordering is a one-way door.

## PCB layout (decision 130)

`python3 tools/orchestrate.py pcb <board>` queues the layout of one board as six `pcb-fixer` stages, each after the
previous: connectors and holes; power path and output channels; logic half and all remaining parts; power copper;
routing; silkscreen and a clean DRC. Then an EMC review (focus layout) and a deep validator review (focus pcb) run.
The planner may also send a layout-only item to a `pcb-fixer` package (`"role": "pcb-fixer"`).

A pcb-fixer edits only the board file with `tools/kpcb.py` (KiCad 10's own Python), plus `STATUS.md` and
design-notes. **Gates** (the same as `tools/fix_check.py --role pcb-fixer`), checked by the orchestrator:
- the schematic is unchanged (ERC and netlist as before, no refs may differ);
- schematic parity 0 (`kicad-cli pcb drc --schematic-parity`; a symbol without a footprint, such as FL30, is not
  counted);
- 0 DRC errors on the board (parts still parked beside it are not judged yet);
- outline and hole keep-outs unchanged (decisions 123, 128); no SMT part on the bottom (decision 122); no part in a
  hole keep-out;
- from the third stage on no part may stay off the board; in the routing and silkscreen stages nothing may stay
  unconnected.
Placement, copper and routing are two-way doors (a revert takes them back). A bottom-side part, an outline, hole or
connector-edge change, or anything that weakens an invariant is a one-way door for the owner. Ordering boards stays
the owner's.
