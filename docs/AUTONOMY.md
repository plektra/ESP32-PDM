# Autonomous runs

How agents work without the owner in the loop (decision 20). The orchestrator is `tools/orchestrate.py`; agents talk
to each other only through files: reports in `docs/reviews/`, tasks in `docs/queue.json`, questions for the owner in
`docs/OWNER-INBOX.md`.

## Policy: small decisions are made, big ones go to the owner

An agent may decide a **small** change itself. Everything else is **big**: the agent writes it to the owner inbox and
the task waits. When in doubt, it is big.

**Small** – all of these hold:

- It follows from confirmed decisions; it changes no decision (confirmed or **[proposed]**), invariant, budget or the
  pin map.
- It stays on one board and does not touch a shared sheet (`power-usb`, `can`, `analog_sw`, the controller part of the
  root sheet), `lib/` or `docs/ARCHITECTURE.md`.
- The function stays the same: a passive value (E24/E12), a missing pull-up/pull-down, decoupling, a filter corner, a
  test point, a footprint or symbol correction proven by the datasheet, an equivalent part with the same footprint and
  equal or better ratings, a missing `LCSC` field, documentation and layout rules.
- No new unique extended part; cost change ≤ 0.50 USD per board at 10 units.
- No connector, pole count, pinout or protection topology change; no change to a safety-relevant output (bilge pump,
  navigation lights, anything that can trap or burn).
- Severity below CRITICAL.

**Big** – anything else, for example: new or replaced protection scheme, channel ratings, new part type, connector or
terminal changes, mechanics, firmware architecture, cost levers that trade a feature, every CRITICAL finding.

A small decision an agent makes is recorded in `docs/decisions.md` with status **auto** (decided by an agent under
decision 20). The owner may overturn it at any time; overturning makes it a normal decision.

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
    "class": "small",
    "reason": "which policy line makes it small or big",
    "touches": [],
    "cost_delta_usd": 0.0
  }
]
```
<!-- findings:end -->
````

- `kind`: `finding` (a problem), `lever` (cost saving or improvement) or `question` (only the owner can answer).
- `severity`: `CRITICAL`, `MAJOR`, `MINOR` or `INFO` (levers and questions: `INFO` unless they fix a problem).
- `board`: `pdm-4ch`, `pdm-hc2` or `system`.
- `class`: `small` or `big` under the policy above.
- `touches`: any of `shared-sheet`, `pin-map`, `invariant`, `budget`, `decision:<N>`, `connector`, `protection`,
  `safety`, `new-extended-part`, `mechanical`, `firmware`. Empty if none.
- `cost_delta_usd`: change per board at 10 units if known, otherwise omit.
- An empty review still writes `[]`.

The orchestrator does not take the reviewer's word for `small`: a CRITICAL finding, a `question`, any entry in
`touches`, `board: system`, or a cost change above 0.50 USD makes it big.

## Queue and inbox

- `docs/queue.json` – tasks: `id`, `role`, `scope`, `state` (`ready`, `running`, `done`, `failed`,
  `blocked-owner`, `parked`), `depends_on`, `source` (the report and finding that created it). Small findings become
  `board-fix` tasks; big ones become `blocked-owner` tasks with an inbox item.
- `docs/OWNER-INBOX.md` – one section per question (`Q-0001` …). The owner writes the ruling after **Answer:**
  (`yes`, `no`, or text) or uses `/inbox`. The next orchestrator run moves answered tasks on: `yes` or a text ruling
  → `ready` (the ruling is passed to the agent and becomes a confirmed decision in its handoff), `no` → `done`.

## Pilot (now)

Only the reviewers run unattended: `emc-reviewer`, `cost-controller`, `validator`. They change nothing but
`docs/reviews/`. `board-fix` tasks are queued and `parked`; they run in `/board` sessions with the owner until the pilot
has shown that findings are classified well. Results are committed to the `auto/pilot` branch; the owner merges.
