# Push/fold chart (15bb or less)

Built from 137356 hands of one round. A shove is in the chart when its chip EV beats folding. Everything is first-in: everyone before you has folded and no one limped. Chip EV only, with no ICM or bubble adjustment. Full lists by hand class are in push_fold_chart.json.

## Share of all hands to shove first-in

| Position | 5bb | 7bb | 10bb | 13bb | 15bb |
| --- | --- | --- | --- | --- | --- |
| UTG | 56% | 36% | 24% | 62% | 53% |
| UTG+1 | 72% | 43% | 29% | 69% | 60% |
| LJ | 92% | 57% | 37% | 69% | 60% |
| HJ | 100% | 82% | 48% | 80% | 68% |
| CO | 100% | 99% | 75% | 96% | 85% |
| BTN | 100% | 100% | 97% | 100% | 95% |
| SB | 100% | 100% | 100% | 100% | 100% |
| HU | 100% | 100% | 100% | 100% | 100% |

## Weakest hands still worth shoving, by position

Smallest positive EV in each size group, as ranks plus suits: s3 all one suit, s2 two suited, r rainbow.

| Position | Stack | Classes | Examples at the edge |
| --- | --- | --- | --- |
| UTG | 7bb | 660 | A75s3, A98r, QJ7s3, A87s2, KJ9s2, KJ9s2 |
| UTG | 13bb | 1114 | J64s3, 962s2, 983s2, T83s3, Q74s3, Q98s3 |
| UTG+1 | 7bb | 789 | T98s3, K82s3, J97s3, JT6s2, QJ8s2, JT7s2 |
| UTG+1 | 13bb | 1247 | 873s2, J75s2, K82s3, J84s2, 642s2, T97s3 |
| LJ | 7bb | 1041 | J93s3, K98s2, JT5r, 873s2, J87s2, J53s3 |
| LJ | 13bb | 1247 | 873s2, J75s2, K82s3, J84s2, 642s2, T97s3 |
| HJ | 7bb | 1487 | 432r, Q84s2, 832s3, QT5r, Q82s2, 852s2 |
| HJ | 13bb | 1453 | 653s3, J73s2, T98s2, J42r, J73r, 863r |
| CO | 7bb | 1740 | T52r, 743s3, Q54s2, Q52r, T54r, 954s2 |
| CO | 13bb | 1689 | J87s2, 875r, J32r, T53r, 843s2, 987s2 |
| BTN | 7bb | 1755 | 952r, 943r, 952s2, 943s2, 952s3, 943s2 |
| BTN | 13bb | 1752 | 852r, 742s2, 832s2, 732s2, 732s2, 754s2 |
| SB | 7bb | 1755 | 952r, 943r, 952s2, 943s2, 952s3, 943s2 |
| SB | 13bb | 1755 | 832r, 732r, 732s2, 852r, 742s2, 832s2 |
| HU | 7bb | 1755 | 952r, 943r, 952s2, 943s2, 952s3, 943s2 |
| HU | 13bb | 1755 | 832r, 732r, 732s2, 852r, 742s2, 832s2 |

## Calling a shove from the blinds (everyone else folded)

Share of all hands that beat folding.

| Position | 5bb | 7bb | 10bb | 13bb | 15bb |
| --- | --- | --- | --- | --- | --- |
| BB | 86% | 65% | 51% | 64% | 61% |
| SB | 68% | 55% | 44% | 58% | 55% |

## Measured fold rates to a first-in shove (95% CI)

| Responder | <=10bb | 10-15bb |
| --- | --- | --- |
| UTG | - | - |
| UTG+1 | 0.96 (0.80-0.99) n=24 | 0.88 (0.53-0.98) n=8 |
| LJ | 0.90 (0.83-0.94) n=113 | 1.00 (0.92-1.00) n=44 |
| HJ | 0.90 (0.87-0.93) n=361 | 0.95 (0.90-0.98) n=126 |
| CO | 0.90 (0.88-0.92) n=861 | 0.94 (0.91-0.96) n=314 |
| BTN | 0.91 (0.90-0.92) n=1942 | 0.96 (0.94-0.97) n=654 |
| SB | 0.88 (0.87-0.89) n=4083 | 0.90 (0.88-0.92) n=1219 |
| BB | 0.78 (0.77-0.79) n=7900 | 0.87 (0.86-0.88) n=2428 |

Thin cells (under 40) borrow from: position, position group.

## Called hands used

| Group | Available | Used | Source |
| --- | --- | --- | --- |
| <=10 blind | 2016 | 200 | as measured |
| <=10 other | 240 | 200 | as measured |
| 10-15 blind | 401 | 200 | as measured |
| 10-15 other | 445 | 200 | pooled over callers |
| shover <=10 | 2220 | 200 | shovers' shown hands |
| shover 10-15 | 710 | 200 | shovers' shown hands |

## Check against our own shoves in this round

Our bot's first-in shoves, by what the chart predicted for each. Realized is the actual chip result against folding, in BB. Same round as the fit, so this is a consistency check, not out-of-sample.

| Group | Shoves | Predicted EV (BB) | Realized (95% CI) |
| --- | --- | --- | --- |
| 10-15bb | 33 | 1.31 | 1.62 (0.85 to 2.40) |
| <=10bb | 1479 | 1.34 | 1.14 (0.99 to 1.30) |
| chart: shove | 1512 | 1.34 | 1.15 (1.00 to 1.31) |
