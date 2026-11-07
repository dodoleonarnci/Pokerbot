# First bot: rehearsal build

Built from `No_Limit_Pokerbot_First_Bot_Build_Spec.md`, against a practice simulator, because the
starter kit is not available yet. The bot makes every decision from lookups and closed-form formulas.

## Layout

| Path | What it is |
| --- | --- |
| `kit_agent.py` | **Upload entry point** for the official kit (packed as `agent.py`) |
| `bot/kit.py` | **Adapter + layered engine**: official state in, Action and memory out |
| `bot/variant.py` | **VariantSpec**: cards, streets, evaluator, equity, payouts, extra-decision hooks |
| `bot/rules.py` | Rules layer: high-confidence exceptions with enable flags and fire counters |
| `bot/generic.py` | Generic engine: variant equity vs pot odds, for games the policy cannot play |
| `agent.py` | M1 safety shell and entry point for the practice sim and old tests |
| `bot/view.py` | M2 state adapter: a new kit interface changes this file |
| `bot/evaluator.py` | M3 hand ranking: replace with the kit's evaluator if it is fast enough |
| `bot/tables.py`, `bot/features.py` | M4 table loading, draw outs and hand keys |
| `bot/policy.py` | M5 strategy, S1 to S10 (hold'em only) |
| `bot/params.py` | All tunable numbers, rule flags, the assumed payouts and blind schedule |
| `bot/icm.py` | M6 ICM values, chart lookups and the risk penalty |
| `bot/opponent.py`, `bot/spots.py` | M7 pool tables, per-seat layer and spot keys |
| `offline/build_tables.py` | Builds the M3 and M4 data files |
| `offline/build_icm.py` | Solves the M6 jam/fold charts (about 6 s) |
| `offline/pipeline.py` | M8: collect, build, resolve, check, ship |
| `offline/gates.py` | The spec's testing gates |
| `sim/` | Practice simulator and bots; `kit_harness.py` and `ab.py` test the kit path |

## How a decision is made (`bot/kit.py`, `play`)

The first layer that answers wins, and each decision is counted under its layer in
`kit.diagnostics["layers"]` (and logged per decision if `kit.decision_log` is a list).

1. **safety**: try/except around everything, budget `DECISION_BUDGET_S` (0.4 ms). On any
   error the old memory is kept and the bot checks, else folds, else takes the automatic choice.
2. **extra**: a non-betting decision (any kind other than fold/check/call/raise, or a phase other
   than `betting`) goes to `ACTIVE.decide_<kind>()` in `bot/variant.py`; no hook means `automatic`.
3. **rule:<name>**: `bot/rules.py`, in priority order, if enabled in `PARAMS["RULES"]`.
4. **policy**: the hold'em strategy, when `ACTIVE.uses_holdem_policy` is true.
5. **generic** / **generic-after-error**: `bot/generic.py`, when the variant turns the policy off or
   the policy raises.

The whole policy state travels in `memory` (pickled, ~1.5 KB), because any copy of the bot
may answer any table. Randomness is reseeded per decision from table, hand and history length.

## Event-day runbook (60-minute build; T1 starts when it ends)

Times are targets. Submit a safe v1 by minute 45 whatever happens.

1. **Read (0–5 min).** `RULES.md` in the kit, the points table and the format page. Answer:
   same 52-card deck, hole cards, streets and hand ranks? Any new action kinds or phases?
   Payouts and blind schedule?
2. **Install the kit (5–10).** `/no-limit-2026-setup` or `$no-limit-2026-setup`, or download from
   the team page; then in the kit folder build the venv as its README says.
3. **Map the adapter (10–20).** Open the kit's SDK and compare it with every `field(...)` read in
   `bot/kit.py` and the assumptions below. Fix names in `practice_state`, `table_order`,
   `blind_sizes`, `replay_history`, `kind_name`; fix action building at `TODO(kit)` in
   `extra_decision`. Check `kit_agent.py` imports (`poker_agent_sdk.Agent`, `Action`).
4. **Plug in the variant (20–35).** In `bot/variant.py`, subclass `HoldemSpec`, change only what the
   rules change, and set `ACTIVE = YourSpec()`:
   - new action kind or phase → add `decide_<kind>(self, ctx)` returning `Choice(kind, value)`;
     `to_kit()` converts card values back to strings.
   - different deck, hole-card count, streets or hand ranks → set `deck`, `hole_cards`,
     `board_streets`, `board_size`, `evaluate`, and **set `uses_holdem_policy = False`** (the
     generic engine then plays every betting decision).
   - payout modifiers → `payouts()`, and copy the table into `PAYOUTS` in `bot/params.py`.
5. **Regenerate (35–40).** Put the announced `PAYOUTS`, `BLIND_LEVELS`, `HANDS_PER_LEVEL`,
   `MAX_HANDS`, `STARTING_STACK` in `bot/params.py`, then
   `offline/.venv/bin/python offline/build_icm.py` (about 6 s). `offline/build_tables.py` only if
   the deck or evaluator changed for hold'em-style play (not timed; minutes).
6. **Sanity (40–45).** `python3.12 -m unittest discover -s tests`; the kit's
   `poker-agent check` and `poker-agent play` with `kit_agent.py` as `agent.py`; look for zero
   failed decisions.
7. **Submit v1 (by 45).** Upload folder = `kit_agent.py` renamed `agent.py`, `bot/`, `data/`.
   `poker-agent pack DIR bot.zip`, then
   `curl -fsS -X POST -H "Authorization: Bearer $(cat ~/.config/no-limit-2026/api-key)" -H "Content-Type: application/octet-stream" --data-binary @bot.zip "https://pokerbot.sequoiacap.com/tournament/api/teams/<team>/submissions?filename=bot.zip"`
   and poll `GET .../submissions` until `ready` (read `rejection_reason`, `check_log` if not).
   The cooldown is 30 s.
8. **Iterate (between rounds).** Tune `bot/params.py`, A/B with `sim/ab.py`, resubmit. After T1,
   build pool tables from its hand history (`offline/pipeline.py`, excluding our own seat).

## Every place a variant touches

| Where | What changes |
| --- | --- |
| `bot/variant.py` `HoldemSpec` / `ACTIVE` | cards, hole count, streets, evaluator, equity, hand class, payouts, extra-decision hooks, `uses_holdem_policy` |
| `bot/kit.py` `BETTING_KINDS`, `extra_decision` | which kinds are betting; how a variant action is built (`TODO(kit)`) |
| `bot/kit.py` `practice_state`, `replay_history` | event kinds and amounts if the variant changes betting events |
| `bot/params.py` | `PAYOUTS`, `BLIND_LEVELS`, `HANDS_PER_LEVEL`, `MAX_HANDS`, `STARTING_STACK`, rule flags, `GENERIC_*` |
| `bot/icm.py` + `offline/build_icm.py` | push/fold charts from payouts and blinds (rerun) |
| `bot/evaluator.py`, `bot/tables.py`, `offline/build_tables.py`, `bot/features.py` | hold'em hand ranks and precomputed tables (policy only) |
| `bot/policy.py`, `bot/spots.py` | hold'em streets and two hole cards (policy only; off via `uses_holdem_policy`) |
| `offline/pipeline.py` `parse_hand` | the official hand-history format |
| `sim/` | hold'em practice engine; use the kit's simulator for anything variant-specific |

Assumptions in `bot/kit.py` to check against the SDK: seat numbers increase clockwise;
`seats[i].stack` excludes `seats[i].bet`; `state.pot` includes current bets; `state.history`
holds this hand's events including `blind` and `board`; `raise` carries the round total and
`call` the chips added; the shape of `state.blinds`; whether `hand_number` starts at 0 or 1.

## Commands

Run these from this folder.

```bash
python3.12 offline/build_tables.py
offline/.venv/bin/python offline/build_icm.py
python3.12 -m unittest discover -s tests
python3.12 sim/kit_harness.py --tables 100 --field mixed
python3.12 sim/ab.py --tables 200 --fields mixed checkers --b RULES.steal_vs_folders=false
python3.12 sim/ab.py --tables 200 --fields mixed --b-generic
python3.12 offline/pipeline.py collect --tables 300 --round round0
python3.12 offline/pipeline.py build --round round0
python3.12 offline/pipeline.py resolve
python3.12 offline/pipeline.py check --tables 2000
python3.12 offline/gates.py 200 500 2000
python3.12 offline/pipeline.py ship --with-pool
```
