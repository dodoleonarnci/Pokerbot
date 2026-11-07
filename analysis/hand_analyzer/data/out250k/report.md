# Hand analyzer report
| Measure | Value |
| --- | --- |
| hands | 250000 |
| errors | 0 |
| conservation_failures | 0 |
| decisions | 1605473 |
| excluded_decisions | 0 |
| path_nodes | 472136 |
| path_nodes_20 | 6217 |
| path_nodes_200 | 565 |
| node_class_cells | 858887 |
| node_class_cells_20 | 8166 |
| node_class_cells_200 | 143 |
| show_nodes | 184 |
| show_nodes_20 | 182 |
| show_nodes_200 | 166 |
| split_cells | 581525 |
| split_cells_20 | 3254 |
| split_cells_200 | 13 |
| postflop_decisions | 916603 |
| postflop_share_in_usable_cells | 0.1467 |
| nodes_holding_half_of_decisions | 3254 |
| preflop_classes_seen | 1755 |

Malformed lines skipped: 0 {}

## Top 30 nodes by chips at stake

Chips at stake = decisions x average pot (BB).

| Street | Line | Pos | Players | Depth | So far | Path | n | Pot BB | Chips |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| preflop | unopened | UTG | 8 | d80+ | PF | (start) | 40532 | 1.5 | 60798 |
| preflop | unopened | LJ | 6 | d80+ | PF | (start) | 39025 | 1.5 | 58538 |
| preflop | unopened | HJ | 5 | d80+ | PF | (start) | 35904 | 1.5 | 53856 |
| preflop | unopened | UTG+1 | 7 | d80+ | PF | (start) | 33368 | 1.5 | 50052 |
| preflop | unopened | CO | 4 | d80+ | PF | (start) | 32470 | 1.5 | 48705 |
| preflop | unopened | BTN | 3 | d80+ | PF | (start) | 28462 | 1.5 | 42693 |
| preflop | unopened | SB | 2 | d40-80 | PF | (start) | 14230 | 1.5 | 21345 |
| preflop | vs_open | HJ | 6 | d80+ | PF | LJ:r3 | 4639 | 4.5 | 20876 |
| preflop | vs_open | CO | 5 | d80+ | PF | HJ:r3 | 4572 | 4.5 | 20574 |
| preflop | vs_open | BTN | 4 | d80+ | PF | CO:r3 | 4247 | 4.5 | 19112 |
| preflop | vs_open | SB | 3 | d80+ | PF | BTN:r3 | 3940 | 4.5 | 17730 |
| preflop | vs_open | UTG+1 | 8 | d80+ | PF | UTG:r3 | 3907 | 4.5 | 17582 |
| preflop | vs_open | LJ | 7 | d80+ | PF | UTG+1:r3 | 3698 | 4.5 | 16641 |
| preflop | vs_open | CO | 5 | d80+ | PF | LJ:r3 | 3414 | 4.5 | 15363 |
| preflop | vs_open | LJ | 7 | d80+ | PF | UTG:r3 | 3334 | 4.5 | 15003 |
| preflop | vs_open | BTN | 4 | d80+ | PF | HJ:r3 | 3195 | 4.5 | 14378 |
| flop | donk | SB | 2 | d40-80 | SRP | BTN:r3 SB:c / | 2048 | 7.0 | 14336 |
| preflop | vs_open | SB | 3 | d80+ | PF | CO:r3 | 2990 | 4.5 | 13455 |
| flop | donk | BB | 2 | d40-80 | SRP | BTN:r3 BB:c / | 1997 | 6.5 | 12980 |
| preflop | vs_open | BB | 2 | d40-80 | PF | BTN:r3 | 2743 | 4.5 | 12344 |
| preflop | vs_open | HJ | 6 | d80+ | PF | UTG+1:r3 | 2658 | 4.5 | 11961 |
| flop | cbet | CO | 2 | d40-80 | SRP | CO:r3 BTN:c / | 1556 | 7.5 | 11670 |
| preflop | vs_open | BTN | 4 | d80+ | PF | LJ:r3 | 2396 | 4.5 | 10782 |
| flop | donk | SB | 2 | d40-80 | SRP | CO:r3 SB:c / | 1522 | 7.0 | 10654 |
| preflop | vs_open | HJ | 6 | d80+ | PF | UTG:r3 | 2338 | 4.5 | 10521 |
| flop | donk | BB | 2 | d40-80 | SRP | CO:r3 BB:c / | 1585 | 6.5 | 10302 |
| preflop | vs_open | HJ | 6 | d80+ | PF | LJ:r2 | 2914 | 3.5 | 10199 |
| preflop | vs_open | BB | 2 | d40-80 | PF | CO:r3 | 2234 | 4.5 | 10053 |
| preflop | vs_open | SB | 3 | d80+ | PF | HJ:r3 | 2230 | 4.5 | 10035 |
| preflop | vs_open | CO | 5 | d80+ | PF | HJ:r2 | 2838 | 3.5 | 9933 |

## Deviation verdicts

Usable cells only (20+ samples, |z| >= 2). A bet size with under 200 samples is pulled toward its pooled spot. Edge is in pots; chips = edge x pot (BB). Depth, players and so-far columns show each node's commonest spot.

Fold thresholds allow for the k players still to answer: each must fold alpha^(1/k) for a bet to work. Class-mix verdicts must hold for every way the unknown hands could fall; Observed is the bound that decided it.

### Folds too much: 1488 flagged, top 30

| Street | Line | Pos | Players | Depth | So far | Path | Size | n | Observed | Threshold | z | Edge | Chips |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| preflop | vs_3bet | LJ | 5 | d80+ | PF | LJ:r3 HJ:rx3 CO:c BTN:c BB:c | rx3 | 23 | 0.652 | 0.152 | 6.7 | 0.590 | 23.30 |
| preflop | vs_4bet+ | BTN | 3 | d40-80 | PF | CO:r3 BTN:rx3 BB:rx3 CO:c | rx3 | 21 | 0.524 | 0.283 | 2.4 | 0.335 | 21.30 |
| preflop | vs_3bet | BTN | 4 | d80+ | PF | CO:r3 BTN:c SB:rx3 BB:c CO:c | rx3 | 21 | 0.762 | 0.200 | 6.4 | 0.702 | 21.07 |
| preflop | vs_3bet | UTG | 4 | d80+ | PF | UTG:r3 CO:rx3 BTN:c SB:c | rx3 | 22 | 0.727 | 0.194 | 6.3 | 0.662 | 20.52 |
| preflop | vs_3bet | UTG | 4 | d40-80 | PF | UTG:r3 BTN:rx3 SB:c BB:c | rx3 | 28 | 0.714 | 0.200 | 6.8 | 0.643 | 19.29 |
| preflop | vs_3bet | UTG+1 | 4 | d40-80 | PF | UTG+1:r3 HJ:rx3 BTN:c SB:c | rx3 | 22 | 0.682 | 0.194 | 5.8 | 0.605 | 18.77 |
| preflop | vs_3bet | HJ | 3 | d40-80 | PF | HJ:r4 BTN:rx3 BB:c | rx3 | 20 | 0.750 | 0.281 | 4.7 | 0.652 | 18.59 |
| turn | vs_bet | CO | 2 | d40-80 | SRP-b | HJ:r3 CO:c / HJ:bS CO:c / HJ:bM | bM | 21 | 0.952 | 0.374 | 5.5 | 0.924 | 18.36 |
| preflop | vs_3bet | HJ | 5 | d40-80 | PF | HJ:r3 CO:rx3 BTN:c SB:c BB:c | rx3 | 38 | 0.526 | 0.154 | 6.4 | 0.440 | 17.17 |
| preflop | vs_3bet | LJ | 4 | d40-80 | PF | LJ:r3 CO:rx3 SB:c BB:c | rx3 | 32 | 0.656 | 0.200 | 6.5 | 0.570 | 17.11 |
| preflop | vs_open | SB | 5 | d80+ | PF | LJ:rX CO:c BTN:c | rX | 20 | 0.950 | 0.531 | 3.8 | 0.864 | 16.85 |
| preflop | vs_3bet | UTG+1 | 4 | d80+ | PF | UTG+1:r3 CO:rx3 SB:c BB:c | rx3 | 31 | 0.645 | 0.200 | 6.2 | 0.556 | 16.69 |
| preflop | vs_open | BB | 4 | d80+ | PF | HJ:rX BTN:c SB:c | rX | 21 | 0.905 | 0.263 | 6.7 | 0.871 | 16.54 |
| preflop | vs_3bet | HJ | 3 | d40-80 | PF | HJ:r3 BTN:rx4 BB:c | rx4 | 22 | 0.727 | 0.327 | 4.0 | 0.595 | 16.35 |
| preflop | vs_3bet | CO | 4 | d80+ | PF | CO:r3 BTN:rx3 SB:c BB:c | rx3 | 93 | 0.634 | 0.200 | 10.5 | 0.543 | 16.29 |
| preflop | vs_3bet | UTG+1 | 3 | d40-80 | PF | UTG+1:r3 HJ:rx3 BTN:c | rx3 | 23 | 0.783 | 0.267 | 5.6 | 0.704 | 15.83 |
| preflop | vs_3bet | HJ | 4 | d80+ | PF | HJ:r3 CO:rx3 BTN:c BB:c | rx3 | 41 | 0.610 | 0.197 | 6.7 | 0.514 | 15.68 |
| preflop | vs_3bet | LJ | 4 | d80+ | PF | LJ:r3 HJ:rx3 BTN:c SB:c | rx3 | 32 | 0.594 | 0.194 | 5.7 | 0.496 | 15.38 |
| preflop | vs_3bet | LJ | 4 | d80+ | PF | LJ:r3 HJ:rx3 SB:c BB:c | rx3 | 28 | 0.607 | 0.200 | 5.4 | 0.509 | 15.27 |
| preflop | vs_3bet | HJ | 4 | d80+ | PF | HJ:r3 BTN:rx3 SB:c BB:c | rx3 | 66 | 0.606 | 0.200 | 8.2 | 0.508 | 15.23 |
| preflop | vs_3bet | LJ | 4 | d40-80 | PF | LJ:r2 HJ:rx3 CO:c BTN:c | rx3 | 24 | 0.750 | 0.186 | 7.1 | 0.693 | 14.90 |
| flop | vs_bet | BTN | 3 | d80+ | SRP | CO:r3 BTN:c SB:c / SB:bM CO:c | bM | 21 | 0.762 | 0.273 | 5.0 | 0.673 | 14.80 |
| preflop | vs_3bet | LJ | 4 | d80+ | PF | LJ:r3 BTN:rx3 SB:c BB:c | rx3 | 54 | 0.593 | 0.200 | 7.2 | 0.491 | 14.72 |
| turn | vs_bet | CO | 2 | d40-80 | SRP-b | CO:r3 SB:c / SB:bS CO:c / SB:bM | bM | 23 | 0.870 | 0.375 | 4.9 | 0.791 | 14.69 |
| preflop | vs_3bet | LJ | 4 | d40-80 | PF | LJ:r3 HJ:rx3 CO:c BTN:c | rx3 | 23 | 0.565 | 0.190 | 4.6 | 0.463 | 14.58 |
| preflop | vs_3bet | LJ | 4 | d40-80 | PF | LJ:r3 CO:rx3 BTN:c BB:c | rx3 | 38 | 0.579 | 0.197 | 5.9 | 0.476 | 14.51 |
| turn | vs_bet | BTN | 2 | d40-80 | SRP-b | HJ:r3 BTN:c / HJ:bS BTN:c / HJ:bS | bS | 26 | 0.885 | 0.247 | 7.5 | 0.847 | 13.97 |
| preflop | vs_3bet | LJ | 4 | d80+ | PF | LJ:r3 HJ:rx3 BTN:c BB:c | rx3 | 32 | 0.562 | 0.197 | 5.2 | 0.455 | 13.89 |
| preflop | vs_open | BB | 5 | d80+ | PF | LJ:r4 HJ:c CO:c BTN:c | r4 | 22 | 0.818 | 0.171 | 8.0 | 0.781 | 13.66 |
| preflop | vs_3bet | UTG+1 | 4 | d40-80 | PF | UTG+1:r3 CO:rx3 BTN:c SB:c | rx3 | 35 | 0.543 | 0.194 | 5.2 | 0.433 | 13.43 |

### Calls too much: 19 flagged; 3 withheld, unknown hands could overturn them, top 30

| Street | Line | Pos | Players | Depth | So far | Path | Size | n | Observed | Threshold | z | Edge | Chips |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flop | vs_bet | HJ | 3 | d40-80 | SRP | HJ:r3 CO:c SB:c / SB:bM | bM | 48 | 0.591 | 0.500 | -3.4 | 0.375 | 6.00 |
| flop | vs_bet | BB | 3 | d80+ | SRP | HJ:r3 SB:c BB:c / SB:bM | bM | 35 | 0.810 | 0.500 | -2.6 | 0.344 | 4.95 |
| flop | vs_bet | SB | 3 | d80+ | SRP | BTN:r3 SB:c BB:c / SB:x BB:x BTN:bM | bM | 42 | 0.792 | 0.500 | -2.4 | 0.306 | 4.41 |
| flop | vs_bet | BB | 3 | d80+ | SRP | CO:r3 SB:c BB:c / SB:bM | bM | 69 | 0.694 | 0.500 | -3.0 | 0.298 | 4.28 |
| flop | vs_bet | CO | 3 | d80+ | SRP | HJ:r3 CO:c BTN:c / HJ:bS | bS | 45 | 0.879 | 0.500 | -3.7 | 0.263 | 3.67 |
| flop | vs_bet | HJ | 3 | d40-80 | SRP | HJ:r3 CO:c BB:c / BB:bS | bS | 50 | 0.564 | 0.500 | -4.5 | 0.286 | 3.61 |
| flop | vs_bet | CO | 3 | d80+ | SRP | CO:r3 BTN:c BB:c / BB:bS | bS | 63 | 0.543 | 0.500 | -4.4 | 0.263 | 3.32 |
| flop | vs_bet | BB | 3 | d80+ | SRP | HJ:r3 SB:c BB:c / SB:bS | bS | 40 | 0.536 | 0.500 | -3.4 | 0.261 | 3.13 |
| flop | vs_bet | HJ | 3 | d80+ | SRP | HJ:r3 CO:c SB:c / SB:bS | bS | 33 | 0.682 | 0.500 | -2.6 | 0.231 | 3.07 |
| flop | vs_bet | UTG+1 | 3 | d80+ | SRP | UTG+1:r3 CO:c BB:c / BB:bS | bS | 30 | 0.524 | 0.500 | -2.5 | 0.234 | 2.96 |
| flop | vs_bet | BTN | 3 | d80+ | SRP | HJ:r3 BTN:c SB:c / SB:x HJ:bS | bS | 34 | 0.636 | 0.500 | -2.4 | 0.215 | 2.86 |
| flop | vs_bet | CO | 3 | d80+ | SRP | HJ:r2 CO:c SB:c / SB:x HJ:bS | bS | 24 | 0.700 | 0.500 | -3.2 | 0.292 | 2.72 |
| flop | vs_bet | BTN | 3 | d80+ | SRP | CO:r3 BTN:c SB:c / SB:x CO:bS | bS | 41 | 0.520 | 0.500 | -2.3 | 0.196 | 2.61 |
| flop | vs_bet | HJ | 3 | d40-80 | SRP | HJ:r2 CO:c BB:c / BB:bS | bS | 29 | 0.636 | 0.500 | -3.1 | 0.270 | 2.33 |
| flop | vs_bet | BTN | 3 | d80+ | SRP | CO:r3 BTN:c BB:c / BB:x CO:bS | bS | 52 | 0.588 | 0.500 | -2.2 | 0.169 | 2.14 |
| flop | vs_bet | BB | 3 | d80+ | SRP | CO:r3 SB:c BB:c / SB:bS | bS | 61 | 0.579 | 0.500 | -2.4 | 0.171 | 2.05 |
| flop | vs_bet | CO | 3 | d80+ | SRP | CO:r2 BTN:c SB:c / SB:bS | bS | 40 | 0.720 | 0.500 | -2.2 | 0.188 | 1.75 |
| flop | vs_bet | CO | 3 | d80+ | SRP | CO:r2 BTN:c BB:c / BB:bS | bS | 36 | 0.667 | 0.500 | -2.3 | 0.203 | 1.75 |
| flop | vs_bet | BB | 3 | d80+ | SRP | BTN:r2 SB:c BB:c / SB:bS | bS | 46 | 0.517 | 0.500 | -2.6 | 0.205 | 1.63 |

### Bluffs too much: 9 flagged; 45 withheld, unknown hands could overturn them, top 30

| Street | Line | Pos | Players | Depth | So far | Path | Size | n | Observed | Threshold | z | Edge | Chips |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| turn | stab | BB | 2 | d40-80 | SRP-x | BTN:r3 BB:c / BB:x BTN:x / | bS | 109 | 0.281 | 0.198 | 2.2 | 0.248 | 1.61 |
| flop | stab | CO | 2 | d40-80 | SRP | LJ:r3 CO:c / LJ:x | bS | 69 | 0.308 | 0.198 | 2.3 | 0.148 | 1.11 |
| flop | stab | CO | 2 | d40-80 | SRP | HJ:r3 CO:c / HJ:x | bS | 99 | 0.307 | 0.198 | 2.7 | 0.148 | 1.11 |
| flop | stab | CO | 2 | d40-80 | SRP | UTG+1:r3 CO:c / UTG+1:x | bS | 45 | 0.330 | 0.198 | 2.2 | 0.148 | 1.11 |
| flop | donk | SB | 2 | d40-80 | SRP | CO:r3 SB:c / | bS | 206 | 0.291 | 0.198 | 3.3 | 0.148 | 1.03 |
| flop | donk | BB | 2 | d40-80 | SRP | HJ:r3 BB:c / | bS | 164 | 0.269 | 0.198 | 2.3 | 0.149 | 0.97 |
| flop | donk | SB | 2 | d40-80 | SRP | HJ:r2 SB:c / | bS | 102 | 0.280 | 0.199 | 2.0 | 0.147 | 0.74 |
| flop | donk | SB | 2 | d40-80 | SRP | CO:r2 SB:c / | bS | 134 | 0.268 | 0.199 | 2.0 | 0.147 | 0.74 |
| flop | donk | BB | 2 | d40-80 | SRP | BTN:r2 BB:c / | bS | 166 | 0.284 | 0.198 | 2.8 | 0.149 | 0.67 |

### Value bets too much: 5 flagged; 78 withheld, unknown hands could overturn them, top 30

| Street | Line | Pos | Players | Depth | So far | Path | Size | n | Observed | Threshold | z | Edge | Chips |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flop | stab | BB | 2 | d40-80 | SRP | SB:r3 BB:c / SB:x | bL | 42 | 0.172 | 0.333 | -2.2 | 0.411 | 2.46 |
| turn | barrel | SB | 2 | d40-80 | LP-b | SB:c BB:x / SB:bM BB:c / | bM | 41 | 0.126 | 0.272 | -2.1 | 0.384 | 1.60 |
| turn | stab | LJ | 2 | d40-80 | LP-x | LJ:c BB:x / BB:x LJ:x / BB:x | bL | 23 | 0.097 | 0.333 | -2.4 | 0.491 | 1.23 |
| turn | stab | UTG+1 | 2 | d40-80 | LP-x | UTG+1:c BB:x / BB:x UTG+1:x / BB:x | bM | 44 | 0.111 | 0.273 | -2.4 | 0.358 | 0.89 |
| flop | stab | SB | 2 | d40-80 | LP | SB:c BB:x / | bL | 80 | 0.156 | 0.333 | -3.4 | 0.230 | 0.46 |

## Pool rates

### Unopened, by position

| Pos | n | Open | Limp |
| --- | --- | --- | --- |
| BTN | 68701 | 0.364 | 0.050 |
| CO | 101171 | 0.271 | 0.050 |
| HJ | 137075 | 0.212 | 0.050 |
| LJ | 176100 | 0.171 | 0.050 |
| SB | 40239 | 0.304 | 0.050 |
| UTG | 237439 | 0.121 | 0.050 |
| UTG+1 | 176111 | 0.140 | 0.049 |

### Facing raises

| Spot | n | Fold | Call | Raise |
| --- | --- | --- | --- | --- |
| vs_open | 758998 | 0.720 | 0.200 | 0.080 |
| vs_3bet | 179166 | 0.549 | 0.352 | 0.100 |
| vs_4bet+ | 63149 | 0.452 | 0.500 | 0.047 |

### Postflop bet frequency by class (no bet to face)

Class known on 0.950 of these bets. Rates need 80%: below that they describe hands that got shown.

| Class | Known n | Bet |
| --- | --- | --- |
| air | 178273 | 0.150 |
| draw | 34639 | 0.349 |
| strong | 133892 | 0.749 |
| top | 62767 | 0.548 |
| weak | 141124 | 0.249 |

### Flop fold rate by bet size and class

Rates need 80% of the folds to have known cards, since a folded hand is rarely shown.

| Size | Class | Known n | Folds with known cards | Fold |
| --- | --- | --- | --- | --- |
| big | air | 11199 | 0.949 | 0.843 |
| big | draw | 1928 | 0.949 | 0.552 |
| big | strong | 3172 | 0.949 | 0.052 |
| big | top | 3052 | 0.949 | 0.301 |
| big | weak | 7008 | 0.949 | 0.701 |
| small | air | 25337 | 0.949 | 0.552 |
| small | draw | 4397 | 0.949 | 0.245 |
| small | strong | 7299 | 0.949 | 0.020 |
| small | top | 6829 | 0.949 | 0.099 |
| small | weak | 15565 | 0.949 | 0.348 |

### Fold rate facing a first bet, by the previous street (two-street lines)

| Street | Previous street | n | Fold |
| --- | --- | --- | --- |
| flop | pre | 149475 | 0.462 |
| river | bL-c | 3308 | 0.236 |
| river | bL-r | 236 | 0.114 |
| river | bM-c | 11935 | 0.274 |
| river | bM-r | 864 | 0.117 |
| river | bO-c | 1014 | 0.246 |
| river | bO-r | 60 | 0.217 |
| river | bS-c | 15429 | 0.293 |
| river | bS-r | 1055 | 0.138 |
| river | x | 27440 | 0.425 |
| turn | bL-c | 4990 | 0.273 |
| turn | bL-r | 454 | 0.156 |
| turn | bM-c | 19400 | 0.313 |
| turn | bM-r | 1382 | 0.158 |
| turn | bO-c | 1587 | 0.285 |
| turn | bO-r | 119 | 0.176 |
| turn | bS-c | 26553 | 0.800 |
| turn | bS-r | 1628 | 0.181 |
| turn | x | 46080 | 0.456 |

## Show and discard

Kept cards are known for 356136 of 374943 players who reached the flop (0.950). 

| Measure | Spots | Rate |
| --- | --- | --- |
| Shows the card that pairs the flop, when one kept card does | 110643 | 0.596 |
| Keeps the best pair, when the pairs differ | 225160 | 0.900 |

### Show leaks by position and class

How often the player shows the kept card that pairs the flop, when exactly one does: the choice that gives the hand away. Grouped without the public bucket, because bucket P means the shown card pairs the flop by definition. 20+ spots only.

| Pos | Class | n | Spots | Shows strong card |
| --- | --- | --- | --- | --- |
| LJ | strong | 5461 | 1417 | 0.615 |
| UTG | weak | 5780 | 3305 | 0.614 |
| HJ | top | 6036 | 4396 | 0.612 |
| BTN | weak | 14377 | 9475 | 0.604 |
| BB | top | 8622 | 6684 | 0.604 |
| BTN | strong | 8573 | 2345 | 0.603 |
| HJ | weak | 10818 | 6724 | 0.603 |
| BTN | top | 7788 | 5814 | 0.599 |
| BB | strong | 10060 | 2923 | 0.598 |
| CO | strong | 7418 | 2003 | 0.598 |
| UTG+1 | weak | 6282 | 3768 | 0.597 |
| SB | strong | 8520 | 2340 | 0.597 |
| UTG+1 | top | 3748 | 2668 | 0.594 |
| UTG | top | 3554 | 2474 | 0.593 |
| BB | weak | 17731 | 12638 | 0.593 |
| HJ | strong | 6301 | 1682 | 0.591 |
| CO | top | 6885 | 5077 | 0.591 |
| LJ | weak | 9050 | 5445 | 0.590 |
| SB | weak | 14732 | 10060 | 0.590 |
| UTG | strong | 3556 | 884 | 0.588 |
| LJ | top | 5247 | 3773 | 0.587 |
| SB | top | 7412 | 5583 | 0.587 |
| CO | weak | 12866 | 8179 | 0.587 |
| UTG+1 | strong | 3917 | 986 | 0.581 |

### Bad discards by position and best available class

Grouped by the best pair the player could have kept, because a kept class of air with a better option is a bad discard by definition. Needs the three dealt cards, so it is empty when only opponents are counted. 20+ spots only.

| Pos | Best available | Spots | Bad discard |
| --- | --- | --- | --- |
| CO | top | 7398 | 0.109 |
| LJ | draw | 2484 | 0.108 |
| HJ | top | 6432 | 0.106 |
| SB | draw | 4181 | 0.105 |
| HJ | strong | 6356 | 0.104 |
| BTN | draw | 3957 | 0.104 |
| CO | strong | 7558 | 0.104 |
| BB | weak | 18222 | 0.103 |
| BB | top | 9204 | 0.102 |
| SB | weak | 15097 | 0.101 |
| CO | weak | 13010 | 0.101 |
| BTN | top | 8293 | 0.101 |
| SB | top | 7900 | 0.101 |
| LJ | top | 5567 | 0.100 |
| UTG | weak | 5778 | 0.100 |
| HJ | draw | 2935 | 0.100 |
| UTG | strong | 3546 | 0.100 |
| UTG+1 | top | 3990 | 0.099 |
| HJ | weak | 10909 | 0.099 |
| BTN | strong | 8679 | 0.099 |
| LJ | strong | 5522 | 0.099 |
| UTG | top | 3764 | 0.099 |
| UTG | draw | 1445 | 0.098 |
| LJ | weak | 9047 | 0.098 |
| CO | draw | 3443 | 0.098 |
| UTG+1 | strong | 3943 | 0.097 |
| BTN | weak | 14537 | 0.097 |
| SB | strong | 8616 | 0.097 |
| BB | strong | 10201 | 0.096 |
| UTG+1 | weak | 6277 | 0.093 |
