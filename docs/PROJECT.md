# Pokerbot — NO LIMIT '26 (Sequoia), team Wentworth's Finest, Bay Area

## What this is

A bot for the NO LIMIT '26 tournament: a Python `Agent` whose `act(state, memory)` plays
8-player sit-and-go tables, scored by average points per table. Organizer guide:
`Getting started - NO LIMIT ’26.pdf` in this folder.

## Where things live

- **Build machine** (`ssh no-limit-2026-build`, user `ubuntu`, 54.91.36.158): an EC2 box set
  up like the tournament's machines. Code is in `~/work`, grouped by purpose since event night
  (full map and rules in `~/work/REFACTOR.md`):
  - `~/work/bots/` — every uploadable bot (`dr_bot`…`dr_bot4`, each with its zip).
  - `~/work/analysis/` — hand histories, `fetch_history.py`, `hand_analyzer/`, `pineapple_em/`,
    `dr_offline/` (preflop table builder, aggression CSVs), `preflop_ranking/`, and the dashboard
    sources in `visualization/`.
  - `~/work/sim/` — practice opponents (`sim_bots/`), `timing.py`, `dr_timed/`.
  - `~/work/legacy/` — the pre-event `first_bot` (layered hold'em bot), its backup, and `practice/`.
  - `~/work/starter-kit/` — the official kit, unmoved. Old top-level paths remain as temporary symlinks.
- **Local mirror**: `bots/`, `analysis/`, `sim/`, `legacy/` and `REFACTOR.md` in this folder are a
  git-tracked copy of the build machine's `~/work` (no venvs, no files over 5 MB, no `first_bot`
  backup). The build machine stays the place to work; pull it down at checkpoints with
  `rsync -a --max-size=5m --exclude=.venv --exclude=__pycache__ --exclude=first_bot.bak-20261106 --exclude=times.log no-limit-2026-build:work/{bots,analysis,sim,legacy,REFACTOR.md} .`
  `CLAUDE.md` at the project root imports `REFACTOR.md`, so every Claude Code session here starts
  with the layout and its rules.
- **This computer**: API key in `~/.config/no-limit-2026/api-key`; SSH alias in `~/.ssh/config`
  using `~/.ssh/runpod`; setup skill at `~/.claude/skills/no-limit-2026-setup/SKILL.md`.

## Kit interface (written 2026-11-06, before the kit was released)

The strategy (`bot/policy.py`) reads a practice-engine dict through `bot/view.py` and keeps
its table knowledge (opponent stats, hand tracker, range estimates) on the `Policy` object.
The tournament gives no such continuity: any copy of the bot may answer any table, and only
the per-table `memory` bytes (64 KB cap) carry over. Carrying data between tables is against
the rules.

- `bot/kit.py` rebuilds the practice dict from the official state (fields as documented in
  the guide), pickles the whole `Policy` into `memory` after each decision and restores it
  on the next, and maps the reply to an offered `Action`. Randomness is reseeded per decision
  from the table, hand number and history length, so nothing outside memory is relied on.
  Any exception keeps the old memory and checks or folds.
- `kit_agent.py` is the future upload entry point (packed as `agent.py`); it subclasses
  `poker_agent_sdk.Agent` when the SDK is importable. The original `agent.py` stays for the
  practice sim and tests.
- `sim/kit_harness.py` replays practice tables through that path with a fresh `Agent` per
  decision, checks the rebuilt state against the engine's, and reports timing and memory size.

Results on the build machine (450 tables, ~67k decisions): rebuilt state identical every
time, zero errors or illegal actions, and identical decisions to the original path given the
same random numbers. Decision time p50 0.2 ms, p99 ~0.45 ms against a 1 ms limit; memory
~1.5 KB typical, ~2 KB max.

### Layered engine and variant seam (added 2026-11-06 afternoon)

`bot/kit.py` `play` now runs layers in order: safety (0.4 ms budget, fallback check/fold/
automatic), extra decisions (`decide_<kind>` hooks on the active `VariantSpec` in
`bot/variant.py`), rules (`bot/rules.py`, flags in `PARAMS["RULES"]`), the hold'em policy, and
a generic equity engine (`bot/generic.py`) for variants the policy cannot play or when it
raises. Each decision is counted by layer. `sim/ab.py` A/B-tests settings on identical
seeds; `tests/test_layers.py` covers the hooks, rules, adapter, fallback and latency. The
event-day runbook and the list of every place a variant touches are in the bot's own
`~/work/legacy/first_bot/README.md`, where Codex/Astra will read them at the event.

### Assumptions to verify against the real SDK

- Seat numbers increase clockwise; `seats[i].stack` excludes the chips in `seats[i].bet`;
  `state.pot` includes current bets.
- `state.history` holds this hand's events including `blind` and `board`; `raise` carries the
  round total and `call` the chips added (both as the guide states).
- `state.blinds` shape, how action kinds are represented, the `Action(kind, amount)`
  constructor, and whether `hand_number` starts at 0 or 1.

## Using tournament hand histories

Official rules (`Official Rules, No Limit_ A Bot Building Tournament.pdf`): 60-minute build,
then six scored tournaments T1–T6 twenty minutes apart, weighted 1–6, so T3–T6 carry 86% of
the score. Each is 10,000 eight-bot sit-and-gos (2,000 chips, blinds from 10/20 rising every
25 hands, 200-hand cap). Opponents are anonymized in play (rule 3.8) but named in the
downloadable hand histories.

Plan: population-level frequencies only. `offline/pipeline.py build` already turns hand
histories into the pool tables the bot reads (`data/pool_tables.json`, loaded by
`bot/opponent.py`): fold/call/raise rates facing bets by spot (Table A), bettor strength
from showdowns (Table B) and preflop open/3-bet/call/jam widths (Table C). It reads the
practice log format, so on kit day it needs a converter from the official format, much
like `replay_history` in `bot/kit.py`. It parses ~5,000 hands/s on one core of the build
machine. No per-team profiles: the bot cannot tell opponents apart, and fingerprinting
them would go against rule 3.8. The current `dist/bot.zip` ships without pool tables.

Discrepancies between the two PDFs: uploads every 5 minutes (rules) vs every 30 s (guide);
the competition API reports `submission_cooldown_seconds: 30`, so the guide is current.
Size limit 100 MB (rules) vs 50 MB uploaded (guide): plan for 50 MB. Uploads go to
`POST /api/teams/<team>/submissions?filename=…`, so submitting can be scripted.

Hand histories have no endpoint in the site's front-end code yet and no tournaments exist
before the event, so the download route is unknown until T1 finishes. Expect it as a link
in the round or team data, like the kit's `links.download`. Fallback: download in the
browser and `scp` to the build machine. When building tables, exclude our own bot's seat
(it is named in the histories), or the field's averages will include our own play.

### Reading opponents' bets in the Bay Area variant (added 2026-11-06, build phase)

The variant (`~/work/starter-kit/RULES.md`) is hold'em with three hole cards. After the
flop, every player still in chooses at the same time which card to discard face down and
which of the other two to expose. So after the flop each opponent has one hidden card, about
45 possibilities, and the discard is never shown, not even at showdown. A Gamemaster
confirmed at the event that agents other than Codex may be used during the build.

Judging bets from showdown hands alone is biased, because which hands reach showdown depends
on how they were played. `~/work/analysis/pineapple_em/` (formerly in `first_bot/offline/`) fits the population
instead, using standard library plus NumPy:

- `em.py` holds the fit. For each opponent it treats the hidden card as unknown and learns
  two things together. The first is a betting model: how likely each action is, given the
  opponent's hand bucket (air, weak draw, strong draw, weak pair, top pair, strong) and the
  spot. The second is a selection model: given the card they exposed and the flop, how
  likely each hidden card is, which captures how players choose what to keep and show. Hands
  shown at showdown count as fully known. `hidden_card_posterior` is the play-time Bayes
  step: the probability of each possible hidden card, given the exposed card, the flop, the
  observer's own three cards and the actions so far.
- `world.py` is a heads-up synthetic version of the variant with a known population.
  `run_synthetic.py` fits three ways and scores each against the truth: EM on realistic
  visibility, showdown hands only (the naive method), and full visibility (the best
  possible).

Results (40k training hands, 20k test hands, 41 s on the build machine): EM recovers the
betting policy almost as well as full visibility. Its "is the bettor behind me on the flop"
probability is calibrated to within about 1 point. The showdown-only fit under-calls bluffs
by 3–5 points in the decision range (predicted 15–40% bluff) in the base world, and by 7
points in a world where bluffs fire again on later streets (`--world barreling`). Ignoring
the betting model and only counting cards is far worse (log loss 0.49 against 0.37). The
posterior costs about 0.1 ms per call with NumPy on the build machine.

Still needed before it can run on real histories: a converter from the official hand-history
format (events `select`, `reveal`, `show`; our own cards in the private record) to
`em.Observation`, with spot and action ids for 8-handed play (raises, multiway, sizes).

## Kit-day checklist

1. Rerun `/no-limit-2026-setup` on a small model; it installs the kit on the build machine.
2. Read `RULES.md` (the variant) and check the assumptions above against the SDK.
3. Run `sim/kit_harness.py` style checks against the kit's real simulator, then assemble an
   upload folder (`kit_agent.py` as `agent.py`, `bot/`, `data/`) and run `poker-agent check`,
   `poker-agent play` and `poker-agent pack`.
4. Upload (once every 30 s per team); the upload test match has no time bank.

## Bay Area variant bot (event night, 2026-11-06)

The variant was "flop discard and reveal": three hole cards, normal preflop betting, then on
the flop every player discards one card and exposes one of the two they keep. The kit's table
rules differ from the rules PDF: blinds rise every 20 hands, the cap is 250 hands, and places
pay 50/30/20 by default (the bot reads `state.config.payouts`, since a round may change it).

The event bot is a fresh single-file agent, not the layered `first_bot`: `~/work/bots/dr_bot2` on
the build machine (`agent.py` plus `preflop3.json`). `~/work/bots/dr_bot` is the first upload, kept
as-is. The preflop table was built by `~/work/analysis/dr_offline/build_preflop.py`, which simulates
all 1,755 distinct three-card hands (5,000 trials each) and stores a strength percentile,
equity against a random hand, and equity against the top 20% of hands.

- Preflop: open, push/fold and calling thresholds by position and stack depth, tightened near
  the money; calls of all-ins compare estimated equity with the ICM break-even equity.
- Flop selection: keeps the pair of cards with the best simulated equity on that flop, then
  exposes the stronger kept card half the time (the "strong branch") and the weaker one
  otherwise; pocket pairs hide the card that carries a flush draw.
- Postflop: bet/raise probability by branch and hand class (two pair or better, top pair or
  overpair, weaker pair, high card), with a bonus for draws.

Uploads go to `POST /api/teams/<team>/submissions?filename=…` with the zip as the body; the
status is in `GET /api/teams/<team>/submissions` (`items[].status`, `ready` when its test
match passes). Both uploads reached `ready`; `dr_bot2.zip` is the active bot for T1. Decision
time on the build machine: worst case about 0.33 ms.

### Aggressiveness factor and round data (version 3)

`~/work/bots/dr_bot3` is `dr_bot2` plus one aggressiveness factor per table, in [0, 1). The bot
sets it at its first decision at a table, as a SHA-256 hash of that hand's number and its
sorted dealt cards, and keeps it in memory. The postflop bet/raise probabilities are scaled
by 0.4–1.6×, preflop open and 3-bet widths by 0.7–1.3×, short-stack shove widths by
0.85–1.15×. Every decision still rolls its own dice. Calls, including ICM all-in calls, don't
change. A factor of 0.5 plays like `dr_bot2`.

Memory is not in hand histories, so the factor is rebuilt from what is:
`~/work/analysis/dr_offline/aggression_data.py HISTORY OUT_PREFIX` finds the first hand where our seat
made a decision that wasn't automatic, recomputes the factor, and writes `-tables.csv` (factor,
points, raise share, action counts) and `-hands.csv` (factor, branch, chip change, showdown,
action counts). In a 150-table local test, raise share by factor third was 18% / 24% / 29%.

Hand histories download from `GET /api/teams/<team>/tournaments/<tournament>/hands`; rounds
are listed at `GET /api/competitions/<competition>/tournaments`. The download script is
`~/work/analysis/fetch_history.py` (same copy in the session scratchpad); it must run on the Mac,
where the API key is. The event clock (`/api/competitions/<c>/redzone`) put the end of the
Bay Area build phase at 7:21 PM PT.

### Leak map: where opponents fold or bluff too much (event night)

`~/work/analysis/pineapple_em/` also turns participant hand histories into game-tree statistics.
`history.py` replays each hand's events into decisions at abstract spots (street, heads-up or
multiway, the actor's role, lead/after-a-check/facing-a-bet, bet size as a share of the pot).
`tree.py` computes, for opponents only, how often a bet makes everyone fold against its
break-even rate, river bluff shares from called bets (always shown) against the balanced
rate, EM-corrected flop and turn hand mixes, and the heads-up postflop game tree.
`report.py FILES --out summary.json` runs it all (75k hands in about 23 s on the build
machine), and `export_rows.py` writes the row files the "Bot leak map" dashboard reads
(https://claude.ai/artifact/MPfnJ5kUQKmZTJAhgqFMHh). The first version shows a 600-table
local practice round (`~/work/analysis/hh/practice_*.jsonl.gz`: our two uploads, the kit's examples
and two deliberately leaky stand-ins in `~/work/sim/sim_bots`). The competition API exposes no
hand-history link, so a real round's file has to come from the round page.

### Exploit rules handoff (event night, after practice round 3)

`analysis/exploit_rules/README.md` and `rules.json` turn the leak analysis into rules a bot
builder can follow directly: spot keys computed from the game state, MDF and pot-odds formulas,
bluff spots where the field overfolds, call thresholds from EM and river showdowns, equity
tables by hand bucket, the `hand_analyzer` report's findings converted to preflop, value-bet and
exposed-card rules, and concrete changes from V7 to V8. `pineapple_em.rules` regenerates the
tables after each round. The fold-through numbers before this point were wrong: bets that made
everyone fold were dropped from the count, so every bluff looked unprofitable. Fixed in
`history.py`/`tree.py`. The leak map now shows practice round 3 (first 1,000 tables).
