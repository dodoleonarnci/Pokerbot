# Hand analyzer report
| Measure | Value |
| --- | --- |
| hands | 138444 |
| errors | 0 |
| conservation_failures | 0 |
| decisions | 337827 |
| excluded_decisions | 47890 |
| path_nodes | 47015 |
| path_nodes_20 | 1371 |
| path_nodes_200 | 158 |
| node_class_cells | 35047 |
| node_class_cells_20 | 392 |
| node_class_cells_200 | 11 |
| show_nodes | 182 |
| show_nodes_20 | 155 |
| show_nodes_200 | 65 |
| split_cells | 75590 |
| split_cells_20 | 802 |
| split_cells_200 | 12 |
| postflop_decisions | 158786 |
| postflop_share_in_usable_cells | 0.2342 |
| nodes_holding_half_of_decisions | 85 |
| preflop_classes_seen | 0 |

Malformed lines skipped: 0 {}

## Top 30 nodes by chips at stake

Chips at stake = decisions x average pot (BB).

| Street | Line | Pos | Players | Depth | So far | Path | n | Pot BB | Chips |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| preflop | unopened | BTN | 3 | d20-40 | PF | (start) | 37167 | 1.5 | 55565 |
| preflop | unopened | CO | 4 | d40-80 | PF | (start) | 16920 | 1.5 | 25289 |
| preflop | unopened | SB | 2 | d<10 | PF | (start) | 16681 | 1.5 | 24891 |
| preflop | vs_open | BB | 2 | d<10 | PF | BTN:rX | 955 | 19.0 | 18134 |
| preflop | vs_3bet | BTN | 2 | d<10 | PF | BTN:r3 BB:rx5 | 378 | 47.5 | 17955 |
| preflop | unopened | HJ | 5 | d40-80 | PF | (start) | 11281 | 1.5 | 16883 |
| preflop | vs_open | BB | 2 | d10-20 | PF | BTN:r3 | 3649 | 3.9 | 14410 |
| flop | donk | BB | 2 | d20-40 | SRP | BTN:r3 BB:c / | 2314 | 5.6 | 12904 |
| preflop | unopened | LJ | 6 | d80+ | PF | (start) | 7929 | 1.5 | 11880 |
| preflop | vs_open | SB | 2 | d<10 | PF | SB:c BB:rX | 220 | 53.6 | 11787 |
| preflop | vs_open | BTN | 2 | d<10 | PF | BTN:c SB:rX | 153 | 70.5 | 10783 |
| preflop | vs_3bet | BTN | 2 | d<10 | PF | BTN:r3 SB:rx5 | 133 | 69.8 | 9277 |
| preflop | vs_open | BB | 2 | d<10 | PF | SB:rX | 345 | 24.1 | 8322 |
| preflop | vs_open | BB | 2 | d10-20 | PF | BTN:r2 | 2384 | 3.4 | 8129 |
| preflop | vs_3bet | BTN | 2 | d<10 | PF | BTN:r2 BB:rx5 | 254 | 31.1 | 7906 |
| preflop | vs_3bet | CO | 2 | d<10 | PF | CO:r3 SB:rx5 | 96 | 81.7 | 7846 |
| preflop | unopened | UTG | 8 | d80+ | PF | (start) | 5151 | 1.5 | 7719 |
| preflop | vs_3bet | CO | 2 | d<10 | PF | CO:r3 BTN:rx5 | 78 | 98.8 | 7707 |
| preflop | vs_limp | BB | 2 | d<10 | PF | BTN:c | 3446 | 2.2 | 7666 |
| preflop | vs_open | SB | 3 | d20-40 | PF | BTN:r3 | 1755 | 4.1 | 7184 |
| flop | donk | BB | 2 | d20-40 | SRP | BTN:r2 BB:c / | 1501 | 4.6 | 6970 |
| preflop | vs_3bet | CO | 2 | d<10 | PF | CO:r3 BB:rx5 | 119 | 57.3 | 6817 |
| flop | vs_bet | BTN | 2 | d20-40 | SRP | BTN:r3 BB:c / BB:bM | 746 | 9.0 | 6734 |
| preflop | vs_limp | BB | 2 | d20-40 | PF | SB:c | 3266 | 2.0 | 6527 |
| flop | cbet | BTN | 2 | d20-40 | SRP | BTN:r3 BB:c / BB:x | 1139 | 5.6 | 6401 |
| preflop | vs_open | BB | 2 | d20-40 | PF | CO:r3 | 1525 | 4.1 | 6271 |
| preflop | vs_open | BB | 2 | d20-40 | PF | SB:r3 | 1709 | 3.7 | 6248 |
| preflop | vs_open | BTN | 2 | d<10 | PF | BTN:c BB:rX | 235 | 26.3 | 6178 |
| flop | donk | BB | 2 | d20-40 | SRP | CO:r3 BB:c / | 1033 | 5.7 | 5903 |
| preflop | vs_3bet | SB | 2 | d<10 | PF | SB:r2 BB:rx5 | 103 | 57.2 | 5892 |

## Deviation verdicts

Usable cells only (20+ samples, |z| >= 2). A bet size with under 200 samples is pulled toward its pooled spot. Edge is in pots; chips = edge x pot (BB). Depth, players and so-far columns show each node's commonest spot.

Fold thresholds allow for the k players still to answer: each must fold alpha^(1/k) for a bet to work. Class-mix verdicts must hold for every way the unknown hands could fall; Observed is the bound that decided it.

### Folds too much: 531 flagged, top 30

| Street | Line | Pos | Players | Depth | So far | Path | Size | n | Observed | Threshold | z | Edge | Chips |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| preflop | vs_3bet | BB | 3 | d40-80 | PF | LJ:r3 CO:rx5 | rx5 | 26 | 0.962 | 0.666 | 3.2 | 0.865 | 279.25 |
| preflop | vs_3bet | BB | 3 | d80+ | PF | CO:r3 BTN:rx5 | rx5 | 86 | 0.965 | 0.630 | 6.4 | 0.886 | 142.15 |
| preflop | vs_3bet | BB | 3 | d20-40 | PF | HJ:r3 BTN:rx5 | rx5 | 43 | 0.977 | 0.735 | 3.6 | 0.900 | 102.61 |
| preflop | vs_3bet | SB | 4 | d80+ | PF | CO:r3 BTN:rx5 | rx5 | 87 | 0.954 | 0.774 | 4.0 | 0.755 | 78.59 |
| preflop | vs_3bet | CO | 2 | d<10 | PF | CO:r2 BTN:rx5 | rx5 | 42 | 0.905 | 0.274 | 9.2 | 0.869 | 74.01 |
| preflop | vs_3bet | HJ | 2 | d<10 | PF | HJ:r2 CO:rx5 | rx5 | 26 | 0.731 | 0.324 | 4.4 | 0.602 | 72.65 |
| preflop | vs_3bet | SB | 4 | d40-80 | PF | HJ:r3 BTN:rx5 | rx5 | 47 | 0.957 | 0.804 | 2.7 | 0.746 | 71.72 |
| preflop | vs_3bet | CO | 2 | d<10 | PF | CO:r3 BTN:rx5 | rx5 | 78 | 0.821 | 0.362 | 8.4 | 0.719 | 71.01 |
| preflop | vs_3bet | BB | 3 | d<10 | PF | HJ:r2 CO:rx5 | rx5 | 23 | 0.957 | 0.581 | 3.7 | 0.873 | 68.30 |
| preflop | vs_3bet | BB | 3 | d10-20 | PF | HJ:r3 SB:rx5 | rx5 | 52 | 0.923 | 0.741 | 3.0 | 0.672 | 67.40 |
| preflop | vs_3bet | SB | 4 | d80+ | PF | LJ:r3 CO:rx5 | rx5 | 25 | 1.000 | 0.773 | 2.7 | 1.000 | 64.38 |
| preflop | vs_3bet | SB | 4 | d80+ | PF | HJ:r2 CO:rx5 | rx5 | 23 | 1.000 | 0.758 | 2.7 | 1.000 | 60.96 |
| preflop | vs_3bet | CO | 2 | d<10 | PF | CO:r3 SB:rx5 | rx5 | 96 | 0.823 | 0.306 | 11.0 | 0.745 | 60.86 |
| preflop | vs_3bet | SB | 4 | d40-80 | PF | HJ:r3 CO:rx5 | rx5 | 52 | 0.962 | 0.858 | 2.1 | 0.699 | 59.06 |
| preflop | vs_open | BB | 3 | d<10 | PF | CO:rX BTN:c | rX | 64 | 0.891 | 0.327 | 9.6 | 0.838 | 55.63 |
| preflop | vs_open | BB | 3 | d<10 | PF | LJ:rX BTN:c | rX | 23 | 0.913 | 0.352 | 5.6 | 0.866 | 55.52 |
| preflop | vs_open | BTN | 2 | d<10 | PF | BTN:c SB:rX | rX | 153 | 0.837 | 0.258 | 16.3 | 0.780 | 54.95 |
| preflop | vs_3bet | BB | 3 | d80+ | PF | LJ:r3 BTN:rx5 | rx5 | 36 | 0.917 | 0.764 | 2.2 | 0.617 | 53.89 |
| preflop | vs_3bet | LJ | 2 | d<10 | PF | LJ:r3 BTN:rx5 | rx5 | 30 | 0.800 | 0.534 | 2.9 | 0.571 | 51.33 |
| preflop | vs_open | BB | 3 | d<10 | PF | HJ:rX CO:c | rX | 20 | 0.900 | 0.353 | 5.1 | 0.846 | 49.41 |
| preflop | vs_3bet | BB | 3 | d<10 | PF | CO:r2 BTN:rx5 | rx5 | 39 | 0.974 | 0.555 | 5.3 | 0.928 | 47.37 |
| preflop | vs_open | SB | 4 | d80+ | PF | LJ:rX BTN:c | rX | 25 | 0.960 | 0.609 | 3.6 | 0.875 | 47.16 |
| preflop | vs_open | SB | 2 | d<10 | PF | SB:c BB:rX | rX | 220 | 0.905 | 0.227 | 24.0 | 0.877 | 46.96 |
| preflop | vs_3bet | BTN | 2 | d<10 | PF | BTN:r3 SB:rx5 | rx5 | 133 | 0.789 | 0.368 | 10.1 | 0.667 | 46.51 |
| preflop | vs_open | LJ | 2 | d<10 | PF | LJ:c HJ:rX | rX | 44 | 0.864 | 0.566 | 4.0 | 0.686 | 45.98 |
| preflop | vs_3bet | HJ | 2 | d<10 | PF | HJ:r2 BB:rx5 | rx5 | 26 | 0.769 | 0.432 | 3.5 | 0.594 | 45.71 |
| preflop | vs_open | CO | 2 | d<10 | PF | CO:c BB:rX | rX | 56 | 0.875 | 0.314 | 9.0 | 0.818 | 45.63 |
| preflop | vs_open | CO | 5 | d80+ | PF | LJ:rX | rX | 455 | 0.963 | 0.887 | 5.1 | 0.630 | 44.46 |
| preflop | vs_open | BTN | 5 | d80+ | PF | HJ:rX CO:c | rX | 31 | 0.968 | 0.709 | 3.2 | 0.854 | 44.40 |
| preflop | vs_3bet | SB | 2 | d<10 | PF | SB:r2 BB:rx5 | rx5 | 103 | 0.825 | 0.319 | 11.0 | 0.744 | 42.53 |

### Calls too much: 0 flagged; 5 withheld, unknown hands could overturn them, top 30

| Street | Line | Pos | Players | Depth | So far | Path | Size | n | Observed | Threshold | z | Edge | Chips |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

### Bluffs too much: 0 flagged; 13 withheld, unknown hands could overturn them, top 30

| Street | Line | Pos | Players | Depth | So far | Path | Size | n | Observed | Threshold | z | Edge | Chips |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

### Value bets too much: 0 flagged; 57 withheld, unknown hands could overturn them, top 30

| Street | Line | Pos | Players | Depth | So far | Path | Size | n | Observed | Threshold | z | Edge | Chips |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Pool rates

### Unopened, by position

| Pos | n | Open | Limp |
| --- | --- | --- | --- |
| BB | 252 | 0.000 | 0.000 |
| BTN | 78718 | 0.405 | 0.067 |
| CO | 52631 | 0.268 | 0.053 |
| HJ | 42889 | 0.209 | 0.054 |
| LJ | 32404 | 0.185 | 0.060 |
| SB | 31853 | 0.403 | 0.116 |
| UTG | 23638 | 0.154 | 0.063 |
| UTG+1 | 7936 | 0.164 | 0.069 |

### Facing raises

| Spot | n | Fold | Call | Raise |
| --- | --- | --- | --- | --- |
| vs_open | 212168 | 0.805 | 0.138 | 0.057 |
| vs_3bet | 24219 | 0.785 | 0.155 | 0.060 |
| vs_4bet+ | 3243 | 0.329 | 0.356 | 0.315 |

### Postflop bet frequency by class (no bet to face)

Class known on 0.454 of these bets. Rates need 80%: below that they describe hands that got shown.

| Class | Known n | Bet |
| --- | --- | --- |
| air | 14628 | withheld |
| draw | 2396 | withheld |
| strong | 15681 | withheld |
| top | 7840 | withheld |
| weak | 13375 | withheld |

### Flop fold rate by bet size and class

Rates need 80% of the folds to have known cards, since a folded hand is rarely shown.

| Size | Class | Known n | Folds with known cards | Fold |
| --- | --- | --- | --- | --- |
| big | air | 82 | 0.000 | withheld |
| big | draw | 24 | 0.000 | withheld |
| big | strong | 201 | 0.000 | withheld |
| big | top | 177 | 0.000 | withheld |
| big | weak | 162 | 0.000 | withheld |
| small | air | 230 | 0.000 | withheld |
| small | draw | 60 | 0.000 | withheld |
| small | strong | 205 | 0.000 | withheld |
| small | top | 292 | 0.000 | withheld |
| small | weak | 334 | 0.000 | withheld |

### Fold rate facing a first bet, by the previous street (two-street lines)

| Street | Previous street | n | Fold |
| --- | --- | --- | --- |
| flop | pre | 27708 | 0.518 |
| river | bL-c | 287 | 0.307 |
| river | bL-r | 16 | 0.125 |
| river | bM-c | 4054 | 0.276 |
| river | bM-r | 344 | 0.160 |
| river | bO-c | 19 | 0.105 |
| river | bO-r | 1 | 0.000 |
| river | bS-c | 1043 | 0.338 |
| river | bS-r | 70 | 0.214 |
| river | x | 3012 | 0.668 |
| turn | bL-c | 462 | 0.247 |
| turn | bL-r | 48 | 0.146 |
| turn | bM-c | 7057 | 0.299 |
| turn | bM-r | 842 | 0.160 |
| turn | bO-c | 57 | 0.333 |
| turn | bO-r | 6 | 0.000 |
| turn | bS-c | 1595 | 0.377 |
| turn | bS-r | 122 | 0.164 |
| turn | x | 3605 | 0.639 |

## Show and discard

Kept cards are known for 39401 of 82469 players who reached the flop (0.478). Below 80%, these rates describe hands that reached showdown, not every flop.

| Measure | Spots | Rate |
| --- | --- | --- |
| Shows the card that pairs the flop, when one kept card does | 11558 | 0.244 |
| Keeps the best pair, when the pairs differ | 0 | - |

### Show leaks by position and class

How often the player shows the kept card that pairs the flop, when exactly one does: the choice that gives the hand away. Grouped without the public bucket, because bucket P means the shown card pairs the flop by definition. 20+ spots only.

| Pos | Class | n | Spots | Shows strong card |
| --- | --- | --- | --- | --- |
| UTG+1 | weak | 138 | 48 | 0.521 |
| UTG | weak | 327 | 124 | 0.403 |
| HJ | weak | 706 | 277 | 0.372 |
| BB | weak | 3225 | 1821 | 0.338 |
| LJ | weak | 497 | 172 | 0.337 |
| SB | weak | 1870 | 925 | 0.316 |
| UTG | strong | 284 | 37 | 0.297 |
| CO | weak | 1026 | 444 | 0.288 |
| LJ | strong | 483 | 87 | 0.287 |
| BTN | weak | 2134 | 1108 | 0.277 |
| SB | strong | 1422 | 291 | 0.223 |
| BB | strong | 2237 | 541 | 0.222 |
| LJ | top | 586 | 268 | 0.213 |
| UTG+1 | strong | 140 | 24 | 0.208 |
| CO | strong | 876 | 183 | 0.208 |
| UTG | top | 354 | 164 | 0.201 |
| BB | top | 2456 | 1507 | 0.196 |
| BTN | strong | 1707 | 343 | 0.190 |
| SB | top | 1665 | 910 | 0.182 |
| HJ | strong | 639 | 90 | 0.178 |
| CO | top | 1184 | 588 | 0.175 |
| HJ | top | 802 | 394 | 0.152 |
| BTN | top | 1980 | 1139 | 0.147 |
| UTG+1 | top | 166 | 73 | 0.137 |

### Bad discards by position and best available class

Grouped by the best pair the player could have kept, because a kept class of air with a better option is a bad discard by definition. Needs the three dealt cards, so it is empty when only opponents are counted. 20+ spots only.

| Pos | Best available | Spots | Bad discard |
| --- | --- | --- | --- |

---

# What opponents folded (EM estimate)

Opponents only: 68369 lines, 158786 postflop decisions, 24990 folds, of which 0 have known cards. EM stopped after 44 iterations. These are model estimates, not observed cards.

## Fold rate by hand class and bet size faced

| Street | Size | n | All | air | draw | weak | top | strong |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flop | S | 4199 | 0.318 | 0.613 | 0.264 | 0.256 | 0.078 | 0.052 |
| flop | M | 23271 | 0.511 | 0.783 | 0.535 | 0.465 | 0.192 | 0.036 |
| flop | L | 2314 | 0.593 | 0.853 | 0.658 | 0.555 | 0.322 | 0.079 |
| flop | O | 1242 | 0.699 | 0.926 | 0.834 | 0.741 | 0.424 | 0.165 |
| turn | S | 2528 | 0.157 | 0.454 | 0.239 | 0.118 | 0.050 | 0.019 |
| turn | M | 11354 | 0.399 | 0.723 | 0.696 | 0.377 | 0.147 | 0.063 |
| turn | L | 1200 | 0.445 | 0.760 | 0.777 | 0.469 | 0.237 | 0.086 |
| turn | O | 386 | 0.591 | 0.809 | 0.773 | 0.691 | 0.483 | 0.165 |
| river | S | 1874 | 0.197 | 0.454 | - | 0.197 | 0.121 | 0.053 |
| river | M | 6860 | 0.418 | 0.746 | - | 0.420 | 0.225 | 0.111 |
| river | L | 775 | 0.493 | 0.810 | - | 0.496 | 0.416 | 0.143 |
| river | O | 341 | 0.657 | 0.904 | - | 0.712 | 0.599 | 0.278 |

## What the folded hands were

| Street | Size | Folds | air | draw | weak | top | strong | Shown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flop | S | 1334 | 0.670 | 0.051 | 0.206 | 0.055 | 0.018 | 0 |
| flop | M | 11889 | 0.601 | 0.065 | 0.258 | 0.072 | 0.005 | 0 |
| flop | L | 1372 | 0.538 | 0.070 | 0.279 | 0.103 | 0.010 | 0 |
| flop | O | 868 | 0.485 | 0.066 | 0.303 | 0.125 | 0.020 | 0 |
| turn | S | 397 | 0.553 | 0.107 | 0.244 | 0.075 | 0.022 | 0 |
| turn | M | 4528 | 0.432 | 0.144 | 0.331 | 0.072 | 0.021 | 0 |
| turn | L | 534 | 0.349 | 0.121 | 0.391 | 0.110 | 0.029 | 0 |
| turn | O | 228 | 0.276 | 0.107 | 0.398 | 0.172 | 0.046 | 0 |
| river | S | 369 | 0.447 | 0.000 | 0.359 | 0.132 | 0.062 | 0 |
| river | M | 2865 | 0.481 | 0.000 | 0.378 | 0.092 | 0.049 | 0 |
| river | L | 382 | 0.401 | 0.000 | 0.396 | 0.150 | 0.054 | 0 |
| river | O | 224 | 0.336 | 0.000 | 0.430 | 0.154 | 0.081 | 0 |

## Folded hands by position (50+ folds)

| Street | Pos | Size | Folds | air | draw | weak | top | strong |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flop | BB | S | 410 | 0.702 | 0.046 | 0.197 | 0.043 | 0.012 |
| flop | BB | M | 3704 | 0.635 | 0.061 | 0.253 | 0.048 | 0.004 |
| flop | BB | L | 476 | 0.566 | 0.081 | 0.264 | 0.082 | 0.008 |
| flop | BB | O | 241 | 0.516 | 0.067 | 0.306 | 0.093 | 0.019 |
| flop | BTN | S | 289 | 0.665 | 0.043 | 0.202 | 0.063 | 0.027 |
| flop | BTN | M | 2475 | 0.567 | 0.067 | 0.262 | 0.097 | 0.006 |
| flop | BTN | L | 264 | 0.493 | 0.065 | 0.305 | 0.122 | 0.015 |
| flop | BTN | O | 163 | 0.474 | 0.065 | 0.292 | 0.154 | 0.015 |
| flop | CO | S | 182 | 0.641 | 0.066 | 0.209 | 0.063 | 0.020 |
| flop | CO | M | 1463 | 0.561 | 0.067 | 0.272 | 0.092 | 0.007 |
| flop | CO | L | 154 | 0.512 | 0.061 | 0.292 | 0.122 | 0.013 |
| flop | CO | O | 113 | 0.459 | 0.074 | 0.281 | 0.163 | 0.023 |
| flop | HJ | S | 119 | 0.643 | 0.055 | 0.227 | 0.058 | 0.017 |
| flop | HJ | M | 965 | 0.572 | 0.065 | 0.258 | 0.097 | 0.008 |
| flop | HJ | L | 112 | 0.527 | 0.049 | 0.272 | 0.145 | 0.007 |
| flop | HJ | O | 69 | 0.424 | 0.075 | 0.326 | 0.146 | 0.029 |
| flop | LJ | S | 83 | 0.644 | 0.064 | 0.182 | 0.070 | 0.040 |
| flop | LJ | M | 680 | 0.566 | 0.077 | 0.264 | 0.087 | 0.006 |
| flop | LJ | L | 82 | 0.496 | 0.065 | 0.273 | 0.162 | 0.004 |
| flop | LJ | O | 53 | 0.466 | 0.054 | 0.287 | 0.150 | 0.043 |
| flop | SB | S | 198 | 0.666 | 0.050 | 0.225 | 0.051 | 0.008 |
| flop | SB | M | 2032 | 0.644 | 0.063 | 0.241 | 0.048 | 0.003 |
| flop | SB | L | 225 | 0.581 | 0.073 | 0.269 | 0.072 | 0.005 |
| flop | SB | O | 176 | 0.508 | 0.068 | 0.317 | 0.092 | 0.014 |
| flop | UTG | M | 386 | 0.568 | 0.063 | 0.281 | 0.083 | 0.005 |
| flop | UTG+1 | M | 184 | 0.552 | 0.075 | 0.285 | 0.082 | 0.006 |
| turn | BB | S | 117 | 0.561 | 0.112 | 0.243 | 0.063 | 0.021 |
| turn | BB | M | 1442 | 0.464 | 0.144 | 0.325 | 0.051 | 0.015 |
| turn | BB | L | 174 | 0.390 | 0.138 | 0.369 | 0.076 | 0.027 |
| turn | BB | O | 75 | 0.289 | 0.135 | 0.381 | 0.151 | 0.044 |
| turn | BTN | S | 87 | 0.552 | 0.080 | 0.286 | 0.059 | 0.024 |
| turn | BTN | M | 906 | 0.393 | 0.153 | 0.330 | 0.089 | 0.034 |
| turn | BTN | L | 102 | 0.310 | 0.120 | 0.408 | 0.126 | 0.037 |
| turn | CO | M | 546 | 0.404 | 0.132 | 0.351 | 0.087 | 0.027 |
| turn | CO | L | 54 | 0.381 | 0.105 | 0.411 | 0.075 | 0.029 |
| turn | HJ | M | 345 | 0.391 | 0.149 | 0.351 | 0.088 | 0.021 |
| turn | LJ | M | 263 | 0.443 | 0.137 | 0.303 | 0.093 | 0.025 |
| turn | SB | S | 76 | 0.612 | 0.121 | 0.183 | 0.076 | 0.008 |
| turn | SB | M | 825 | 0.460 | 0.143 | 0.327 | 0.061 | 0.009 |
| turn | SB | L | 108 | 0.338 | 0.124 | 0.377 | 0.130 | 0.032 |
| turn | SB | O | 52 | 0.268 | 0.118 | 0.375 | 0.177 | 0.062 |
| turn | UTG | M | 124 | 0.392 | 0.127 | 0.349 | 0.099 | 0.034 |
| turn | UTG+1 | M | 77 | 0.391 | 0.161 | 0.314 | 0.097 | 0.037 |
| river | BB | S | 110 | 0.495 | 0.000 | 0.366 | 0.090 | 0.049 |
| river | BB | M | 892 | 0.520 | 0.000 | 0.367 | 0.074 | 0.038 |
| river | BB | L | 153 | 0.463 | 0.000 | 0.409 | 0.099 | 0.029 |
| river | BB | O | 79 | 0.370 | 0.000 | 0.422 | 0.116 | 0.092 |
| river | BTN | S | 72 | 0.442 | 0.000 | 0.348 | 0.142 | 0.068 |
| river | BTN | M | 585 | 0.421 | 0.000 | 0.399 | 0.111 | 0.068 |
| river | BTN | L | 55 | 0.320 | 0.000 | 0.410 | 0.207 | 0.064 |
| river | CO | M | 329 | 0.461 | 0.000 | 0.368 | 0.110 | 0.061 |
| river | HJ | M | 228 | 0.472 | 0.000 | 0.351 | 0.129 | 0.048 |
| river | LJ | M | 148 | 0.429 | 0.000 | 0.388 | 0.128 | 0.055 |
| river | SB | S | 74 | 0.490 | 0.000 | 0.355 | 0.119 | 0.036 |
| river | SB | M | 531 | 0.522 | 0.000 | 0.383 | 0.061 | 0.034 |
| river | SB | L | 73 | 0.456 | 0.000 | 0.369 | 0.126 | 0.050 |
| river | UTG | M | 102 | 0.434 | 0.000 | 0.414 | 0.100 | 0.052 |
| river | UTG+1 | M | 50 | 0.465 | 0.000 | 0.354 | 0.111 | 0.071 |

## Bluff share behind bets and raises (20+)

Bluff = air + draw. Balance = B/(P+2B). Shown-only is the same share from hands that reached showdown, the sample the count-based report has.

| Street | Line | Size | n | EM bluff | Shown-only bluff | Shown n | Balance |
| --- | --- | --- | --- | --- | --- | --- | --- |
| flop | cbet | S | 1382 | 0.541 | 0.400 | 452 | 0.184 |
| flop | cbet | M | 7735 | 0.186 | 0.160 | 2764 | 0.272 |
| flop | cbet | L | 718 | 0.097 | 0.083 | 242 | 0.330 |
| flop | cbet | O | 347 | 0.191 | 0.216 | 116 | 0.445 |
| flop | donk | S | 1503 | 0.534 | 0.374 | 545 | 0.170 |
| flop | donk | M | 5036 | 0.182 | 0.125 | 1981 | 0.274 |
| flop | donk | L | 499 | 0.058 | 0.051 | 198 | 0.330 |
| flop | donk | O | 268 | 0.342 | 0.404 | 114 | 0.453 |
| flop | stab | S | 646 | 0.477 | 0.404 | 213 | 0.171 |
| flop | stab | M | 4910 | 0.192 | 0.174 | 1364 | 0.273 |
| flop | stab | L | 511 | 0.070 | 0.051 | 98 | 0.331 |
| flop | stab | O | 288 | 0.321 | 0.382 | 76 | 0.461 |
| flop | vs_bet | S | 324 | 0.133 | 0.064 | 172 | 0.173 |
| flop | vs_bet | M | 1365 | 0.044 | 0.039 | 803 | 0.277 |
| flop | vs_bet | L | 407 | 0.074 | 0.048 | 210 | 0.329 |
| flop | vs_bet | O | 201 | 0.150 | 0.175 | 120 | 0.428 |
| flop | vs_raise | S | 190 | 0.060 | 0.036 | 169 | 0.155 |
| flop | vs_raise | M | 297 | 0.059 | 0.052 | 252 | 0.271 |
| flop | vs_raise | L | 66 | 0.057 | 0.053 | 57 | 0.329 |
| flop | vs_raise | O | 30 | 0.028 | 0.000 | 25 | 0.390 |
| turn | barrel | S | 1508 | 0.358 | 0.258 | 980 | 0.159 |
| turn | barrel | M | 5119 | 0.081 | 0.081 | 3116 | 0.275 |
| turn | barrel | L | 622 | 0.034 | 0.034 | 353 | 0.329 |
| turn | barrel | O | 196 | 0.034 | 0.019 | 105 | 0.404 |
| turn | donk | S | 273 | 0.249 | 0.183 | 180 | 0.144 |
| turn | donk | M | 1123 | 0.102 | 0.083 | 719 | 0.272 |
| turn | donk | L | 104 | 0.063 | 0.062 | 65 | 0.331 |
| turn | donk | O | 32 | 0.176 | 0.130 | 23 | 0.412 |
| turn | stab | S | 385 | 0.255 | 0.283 | 173 | 0.163 |
| turn | stab | M | 2967 | 0.136 | 0.145 | 1031 | 0.273 |
| turn | stab | L | 298 | 0.070 | 0.085 | 94 | 0.330 |
| turn | stab | O | 102 | 0.108 | 0.172 | 29 | 0.428 |
| turn | vs_bet | S | 333 | 0.027 | 0.015 | 272 | 0.150 |
| turn | vs_bet | M | 712 | 0.039 | 0.035 | 541 | 0.271 |
| turn | vs_bet | L | 197 | 0.021 | 0.008 | 119 | 0.328 |
| turn | vs_bet | O | 78 | 0.029 | 0.000 | 43 | 0.395 |
| turn | vs_raise | S | 126 | 0.089 | 0.088 | 113 | 0.138 |
| turn | vs_raise | M | 124 | 0.021 | 0.018 | 113 | 0.270 |
| turn | vs_raise | L | 25 | 0.111 | 0.095 | 21 | 0.328 |
| river | barrel | S | 1163 | 0.211 | 0.173 | 965 | 0.146 |
| river | barrel | M | 2969 | 0.033 | 0.036 | 2281 | 0.274 |
| river | barrel | L | 390 | 0.028 | 0.033 | 271 | 0.330 |
| river | barrel | O | 162 | 0.014 | 0.012 | 83 | 0.408 |
| river | donk | S | 167 | 0.128 | 0.101 | 138 | 0.126 |
| river | donk | M | 572 | 0.073 | 0.067 | 432 | 0.268 |
| river | donk | L | 39 | 0.089 | 0.067 | 30 | 0.330 |
| river | donk | O | 20 | 0.020 | 0.000 | 10 | 0.397 |
| river | stab | S | 306 | 0.254 | 0.250 | 176 | 0.164 |
| river | stab | M | 2184 | 0.089 | 0.093 | 884 | 0.273 |
| river | stab | L | 275 | 0.052 | 0.061 | 82 | 0.332 |
| river | stab | O | 144 | 0.092 | 0.156 | 32 | 0.450 |
| river | vs_bet | S | 230 | 0.056 | 0.054 | 202 | 0.142 |
| river | vs_bet | M | 402 | 0.036 | 0.037 | 325 | 0.273 |
| river | vs_bet | L | 65 | 0.037 | 0.019 | 52 | 0.331 |
| river | vs_bet | O | 38 | 0.035 | 0.000 | 25 | 0.418 |
| river | vs_raise | S | 99 | 0.081 | 0.075 | 93 | 0.148 |
| river | vs_raise | M | 95 | 0.032 | 0.033 | 90 | 0.272 |
