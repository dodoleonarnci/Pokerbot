# ~/work layout (reorganized 2026-11-06, Bay Area event night)

Read this before adding or moving files in `~/work`. Everything is grouped by purpose:

```
~/work/
├── bots/          everything that gets uploaded: one folder per bot version, plus its packed zip
├── analysis/      hand histories, data analysis, offline table builders, dashboard sources
├── sim/           local simulation and testing: practice opponents, timing harnesses
├── legacy/        pre-event hold'em work, kept whole (not used for the Bay Area variant)
├── starter-kit/   official kit and its venv; never move it (its venv has absolute paths)
└── REFACTOR.md    this file
```

## Rules for new work

- **New bot version** → `bots/dr_botN/` (`agent.py` + data files only; nothing else, because the
  whole folder is packed). Pack into the same group:
  `cd ~/work && source starter-kit/.venv/bin/activate && poker-agent pack bots/dr_botN bots/dr_botN.zip`.
  Anything a bot imports (e.g. `analysis/hand_analyzer/spot.py`) must be *copied* into its folder.
- **New analysis, report or dashboard** → `analysis/` (dashboard page sources in `analysis/visualization/<name>/`).
- **New practice opponent, harness or local match output** → `sim/`.
- Use absolute paths (`~/work/starter-kit/.venv/bin/python`, `~/work/bots/dr_bot4`). Relative `..`
  from inside a group folder now lands in the group, not in `~/work`.

## What is where

### bots/ (uploads)
| Path | What it is |
| --- | --- |
| `dr_bot/`, `dr_bot.zip` | v1, first upload |
| `dr_bot2/` | v2: preflop table, flop keep/expose, postflop by hand class |
| `dr_bot3/` | v3: v2 + per-table aggressiveness factor |
| `dr_bot4/` | v4: v3 + equity on postflop calls and ICM; **active bot as of T1** (the server is the truth: `GET /api/teams/<team>/submissions`) |
| `dr_bot6/` | v6: v4 + wider preflop (~30% VPIP, the round-1 top-20% bots' average) + exploration raises at rarely-visited nodes (light 3-bets, raises facing postflop bets). Not uploaded. (`dr_bot5/` is another session's spot.py-based bot.) |
| `dr_bot7/` | v7: v6 preflop/selection + new postflop: Monte Carlo equity vs live opponents (exposed cards used), ICM-adjusted call price and bubble factor, MDF defence heads-up when ICM pressure is low, equity-sized value bets/raises, bluffs skewed 1.25x for an overfolding field; 0.45 ms equity time guard. Uploaded 19:15 PT. |
| `dr_bot8/` | v8: v7 preflop/selection/ICM + postflop from `analysis/exploit_rules` (ships `rules.json` and `cards.py`): spot keys, hand buckets, value bets first, bluffs only in `bluff` spots (per-seat fold rates in memory), bettor-key call lists, default-mix EV fallback, ICM margin and bluff cap near the money. **Uploaded 19:28 PT, active.** |

Each folder is `agent.py` + `preflop3.json` (built by `analysis/dr_offline/build_preflop.py`).

### analysis/
| Path | What it is |
| --- | --- |
| `fetch_history.py` | Downloads round hand histories. Runs **on the Mac** (API key there); `--copy-to-build` copies to `analysis/hand-histories/` |
| `hand-histories/` | Official round downloads (`hands-R*-*.jsonl.gz`) |
| `hh/` | Local practice-match histories and results (`practice_21/22.*`, `smoke.jsonl.gz`), plus derived `practice_tree.json` and `dash_practice/` (leak-map rows) |
| `hand_analyzer/` | Pool action rates and deviation report. Own `.venv`; run from inside it: `.venv/bin/python analyze.py HANDS.jsonl --out DIR`; `adapter.py` converts official downloads; `generate.py` + `tests/` are its synthetic self-tests |
| `pineapple_em/` | EM over opponents' hidden card, game-tree leak stats, dashboard row export. Run from `analysis/`: `.venv/bin/python -m pineapple_em.report FILES --out X.json`, `... -m pineapple_em.export_rows X.json --out-dir DIR`, `... -m pineapple_em.run_synthetic` |
| `exploit_rules/` | Handoff for the bot builder: `README.md` (MDF/EM method, spot keys, decision rules, rules converted from `full_report.md`, generated tables) and `rules.json`. Rebuild: `.venv/bin/python -m pineapple_em.rules hh/<ROUND>_tree.json --out exploit_rules/rules.json --readme exploit_rules/README.md` |
| `.venv/` | NumPy venv for `pineapple_em` (moved from `first_bot/offline/.venv`) |
| `dr_offline/` | `build_preflop.py` (builds `preflop3.json`), `aggression_data.py HISTORY OUT_PREFIX` (per-table/hand CSVs by aggressiveness factor) |
| `preflop_ranking/` | C equity engine (`eq.c`) ranking all 1,755 three-card hands; `build.py` writes `ranking.csv` and a `preflop3.json` with the same keys; `check_*.py` validate it |
| `visualization/leak_map/` | Source of the "Bot leak map" dashboard (https://claude.ai/artifact/MPfnJ5kUQKmZTJAhgqFMHh); data rows are `hh/dash_practice/*.json` |
| `visualization/preflop_map/` | Source of the 3D "Three-Card Preflop Map" (https://claude.ai/artifact/DLdCpawxJRF6YkgXsWK7f5): `prep.py PREFLOP3.json triples.json`, then put triples.json in place of `__DATA__` in `template.html` → `index.html` |

### sim/
| Path | What it is |
| --- | --- |
| `sim_bots/overbluffer`, `sim_bots/overfolder` | Deliberately leaky practice opponents |
| `timing.py` | Decision-latency check: `~/work/starter-kit/.venv/bin/python ~/work/sim/timing.py ~/work/bots/dr_bot4` |
| `dr_timed/` | Wrapper agent that logs per-decision time to `sim/dr_timed/times.log` |

Local matches use the kit simulator, e.g.
`cd ~/work/starter-kit && source .venv/bin/activate && poker-agent play ~/work/bots/dr_bot4 ~/work/bots/dr_bot3 ~/work/sim/sim_bots/overfolder examples/min_raiser examples/check_or_fold --tables 300 --seed 21 --history ~/work/analysis/hh/practice_21.jsonl.gz`.

### legacy/
`first_bot/` (layered hold'em bot with its own `sim/`, `tests/`, `offline/`; possible base for the
finals variant), `first_bot.bak-20261106/`, `practice/` (pre-kit stand-in engine; `first_bot/offline/gates.py`
needs it as a sibling). `first_bot/offline/pineapple_em` and `.venv` are links into `analysis/`.

## Compatibility links (temporary)

Old top-level names still work as symlinks (`~/work/dr_bot4`, `~/work/hh`, `~/work/hand_analyzer`,
`~/work/first_bot`, `~/work/fetch_history.py`, …) so sessions running during the event don't break.
`~/work/dr_offline/` is a real folder of per-file links (its contents were split between analysis and sim).
Don't create new files through these old paths; a `sed -i` or `rm` + rewrite through a link replaces
the link with a stray copy. After the event, remove them with:

```
cd ~/work && find . -maxdepth 1 -type l -delete && rm -r dr_offline
```
