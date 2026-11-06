# Pokerbot — NO LIMIT '26 (Sequoia), team Wentworth's Finest, Bay Area

## What this is

A bot for the NO LIMIT '26 tournament: a Python `Agent` whose `act(state, memory)` plays
8-player sit-and-go tables, scored by average points per table. Organizer guide:
`Getting started - NO LIMIT ’26.pdf` in this folder.

## Where things live

- **Build machine** (`ssh no-limit-2026-build`, user `ubuntu`, 54.91.36.158): an EC2 box set
  up like the tournament's machines. Code is in `~/work`.
  - `~/work/first_bot` — the team's bot (standard library only). `bot/` is the strategy,
    `data/` its precomputed tables, `sim/` a practice tournament, `offline/` the table builders.
  - `~/work/practice` — a stand-in hold'em engine, used until the official kit exists.
  - `~/work/first_bot.bak-20261106` — backup taken before the kit-interface work.
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

## Kit-day checklist

1. Rerun `/no-limit-2026-setup` on a small model; it installs the kit on the build machine.
2. Read `RULES.md` (the variant) and check the assumptions above against the SDK.
3. Run `sim/kit_harness.py` style checks against the kit's real simulator, then assemble an
   upload folder (`kit_agent.py` as `agent.py`, `bot/`, `data/`) and run `poker-agent check`,
   `poker-agent play` and `poker-agent pack`.
4. Upload (once every 30 s per team); the upload test match has no time bank.
