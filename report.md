# Hand analyzer report
| Measure | Value |
| --- | --- |
| hands | 137298 |
| errors | 0 |
| conservation_failures | 0 |
| decisions | 363186 |
| path_nodes | 52331 |
| path_nodes_20 | 1415 |
| path_nodes_200 | 179 |
| node_class_cells | 53336 |
| node_class_cells_20 | 549 |
| node_class_cells_200 | 22 |
| show_nodes | 181 |
| show_nodes_20 | 158 |
| show_nodes_200 | 75 |
| split_cells | 78724 |
| split_cells_20 | 973 |
| split_cells_200 | 19 |
| postflop_decisions | 175696 |
| postflop_share_in_usable_cells | 0.2739 |
| nodes_holding_half_of_decisions | 91 |
| preflop_classes_seen | 1464 |

Malformed lines skipped: 0 {}

## Top 30 nodes by chips at stake

Chips at stake = decisions x average pot (BB).

| Street | Line | Pos | Players | Depth | So far | Path | n | Pot BB | Chips |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| preflop | unopened | BTN | 3 | d80+ | PF | (start) | 37541 | 1.5 | 56088 |
| preflop | unopened | SB | 2 | d80+ | PF | (start) | 17927 | 1.5 | 26704 |
| preflop | unopened | CO | 4 | d40-80 | PF | (start) | 17120 | 1.5 | 25584 |
| preflop | vs_3bet | BTN | 2 | d<10 | PF | BTN:r3 BB:rx5 | 349 | 59.0 | 20580 |
| preflop | unopened | HJ | 5 | d80+ | PF | (start) | 11688 | 1.5 | 17493 |
| preflop | vs_open | BB | 2 | d<10 | PF | BTN:rX | 893 | 18.3 | 16342 |
| preflop | vs_open | BB | 2 | d40-80 | PF | BTN:r3 | 3763 | 3.9 | 14722 |
| flop | donk | BB | 2 | d20-40 | SRP | BTN:r3 BB:c / | 2532 | 5.5 | 13928 |
| preflop | unopened | LJ | 6 | d80+ | PF | (start) | 8026 | 1.5 | 12029 |
| preflop | vs_limp | BB | 2 | d80+ | PF | BTN:c | 3958 | 2.2 | 8864 |
| preflop | vs_3bet | SB | 2 | d<10 | PF | SB:r3 BB:rx5 | 117 | 71.9 | 8413 |
| preflop | vs_limp | BB | 2 | d80+ | PF | SB:c | 4158 | 2.0 | 8308 |
| preflop | vs_open | BB | 2 | d40-80 | PF | BTN:r2 | 2390 | 3.4 | 8187 |
| flop | cbet | BTN | 2 | d20-40 | SRP | BTN:r3 BB:c / BB:x | 1480 | 5.5 | 8148 |
| preflop | vs_3bet | BTN | 2 | d<10 | PF | BTN:r2 BB:rx5 | 188 | 41.1 | 7735 |
| preflop | vs_open | BB | 2 | d<10 | PF | SB:rX | 267 | 28.6 | 7633 |
| preflop | vs_open | BTN | 2 | d<10 | PF | BTN:c BB:rX | 227 | 33.3 | 7560 |
| flop | vs_bet | BB | 2 | d80+ | SRP | BTN:r3 BB:c / BB:x BTN:bM | 847 | 8.8 | 7466 |
| flop | vs_bet | BTN | 2 | d<10 | SRP | BTN:r3 BB:c / BB:bM | 839 | 8.8 | 7421 |
| preflop | vs_open | SB | 2 | d80+ | PF | SB:c BB:rX | 175 | 41.6 | 7285 |
| flop | donk | BB | 2 | d40-80 | SRP | BTN:r2 BB:c / | 1563 | 4.7 | 7281 |
| preflop | unopened | UTG | 8 | d80+ | PF | (start) | 4851 | 1.5 | 7272 |
| preflop | vs_3bet | BTN | 2 | d<10 | PF | BTN:r3 SB:rx5 | 93 | 77.3 | 7188 |
| preflop | vs_3bet | CO | 2 | d<10 | PF | CO:r3 SB:rx5 | 68 | 100.9 | 6859 |
| preflop | vs_3bet | CO | 2 | d<10 | PF | CO:r3 BB:rx5 | 86 | 77.2 | 6639 |
| flop | cbet | SB | 2 | d20-40 | SRP | SB:r3 BB:c / | 1241 | 5.3 | 6566 |
| preflop | vs_open | SB | 3 | d80+ | PF | BTN:r3 | 1578 | 4.1 | 6469 |
| flop | stab | BB | 2 | d80+ | LP | BTN:c BB:x / | 2867 | 2.3 | 6469 |
| flop | donk | BB | 2 | d40-80 | SRP | CO:r3 BB:c / | 1132 | 5.7 | 6448 |
| preflop | vs_open | BB | 2 | d40-80 | PF | SB:r3 | 1749 | 3.7 | 6392 |

## Deviation verdicts

Usable cells only (20+ samples, |z| >= 2). A bet size with under 200 samples is pulled toward its pooled spot. Edge is in pots; chips = edge x pot (BB).

### Folds too much: 794 flagged, top 30

| Street | Line | Pos | Players | Depth | So far | Path | Size | n | Observed | Threshold | z | Edge | Chips |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| preflop | vs_open | BB | 3 | d80+ | PF | LJ:c CO:rX | rX | 24 | 0.917 | 0.467 | 4.4 | 0.844 | 186.12 |
| preflop | vs_open | BTN | 5 | d80+ | PF | LJ:rX CO:c | rX | 21 | 0.952 | 0.442 | 4.7 | 0.915 | 184.30 |
| preflop | vs_3bet | BB | 3 | d80+ | PF | CO:r3 BTN:rx5 | rx5 | 67 | 0.896 | 0.414 | 8.0 | 0.822 | 148.96 |
| preflop | vs_open | SB | 4 | d80+ | PF | LJ:rX CO:c | rX | 20 | 0.900 | 0.385 | 4.7 | 0.837 | 135.34 |
| preflop | vs_open | HJ | 2 | d<10 | PF | HJ:c CO:rX | rX | 29 | 0.931 | 0.323 | 7.0 | 0.898 | 128.13 |
| preflop | vs_3bet | BB | 3 | d80+ | PF | CO:r3 SB:rx5 | rx5 | 75 | 0.933 | 0.380 | 9.9 | 0.893 | 121.80 |
| preflop | vs_open | CO | 6 | d80+ | PF | LJ:rX HJ:c | rX | 20 | 0.900 | 0.328 | 5.4 | 0.851 | 104.12 |
| preflop | vs_3bet | SB | 4 | d80+ | PF | LJ:r3 CO:rx5 | rx5 | 21 | 0.905 | 0.552 | 3.2 | 0.787 | 95.74 |
| preflop | vs_3bet | BB | 3 | d40-80 | PF | LJ:r3 SB:rx5 | rx5 | 23 | 0.957 | 0.694 | 2.7 | 0.858 | 93.53 |
| preflop | vs_open | BTN | 5 | d40-80 | PF | LJ:c CO:rX | rX | 30 | 0.933 | 0.645 | 3.3 | 0.812 | 87.82 |
| preflop | vs_open | HJ | 6 | d10-20 | PF | LJ:rX | rX | 404 | 0.941 | 0.635 | 12.8 | 0.837 | 84.32 |
| preflop | vs_3bet | SB | 4 | d<10 | PF | HJ:r2 BTN:rx5 | rx5 | 22 | 0.955 | 0.586 | 3.5 | 0.890 | 79.01 |
| preflop | vs_open | SB | 4 | d80+ | PF | LJ:rX BTN:c | rX | 20 | 0.900 | 0.359 | 5.0 | 0.844 | 78.96 |
| preflop | vs_3bet | SB | 4 | d80+ | PF | CO:r3 BTN:rx5 | rx5 | 70 | 0.943 | 0.415 | 9.0 | 0.902 | 73.87 |
| preflop | vs_open | CO | 2 | d<10 | PF | CO:c BB:rX | rX | 54 | 0.907 | 0.312 | 9.4 | 0.865 | 71.36 |
| preflop | vs_3bet | CO | 2 | d<10 | PF | CO:r3 SB:rx5 | rx5 | 68 | 0.809 | 0.354 | 7.8 | 0.704 | 71.02 |
| preflop | vs_open | BTN | 5 | d<10 | PF | HJ:rX CO:c | rX | 27 | 1.000 | 0.325 | 7.5 | 1.000 | 65.53 |
| preflop | vs_open | CO | 3 | d<10 | PF | CO:c BTN:rX | rX | 46 | 0.804 | 0.291 | 7.7 | 0.724 | 64.21 |
| preflop | vs_open | SB | 4 | d<10 | PF | HJ:rX BTN:c | rX | 21 | 0.857 | 0.436 | 3.9 | 0.747 | 64.09 |
| preflop | vs_open | BTN | 4 | d<10 | PF | LJ:rX | rX | 350 | 0.926 | 0.607 | 12.2 | 0.811 | 63.83 |
| flop | vs_bet | BB | 2 | d<10 | SRP | BTN:r2 BB:c / BB:x BTN:bO | bO | 21 | 0.857 | 0.540 | 2.9 | 0.689 | 63.30 |
| preflop | vs_open | CO | 5 | d<10 | PF | LJ:rX | rX | 380 | 0.921 | 0.615 | 12.3 | 0.795 | 63.28 |
| preflop | vs_open | SB | 4 | d<10 | PF | HJ:rX CO:c | rX | 27 | 0.963 | 0.315 | 7.2 | 0.946 | 62.87 |
| preflop | vs_3bet | BB | 3 | d80+ | PF | HJ:r3 BTN:rx5 | rx5 | 44 | 1.000 | 0.441 | 7.5 | 1.000 | 62.32 |
| preflop | vs_3bet | BTN | 5 | d80+ | PF | LJ:r3 CO:rx5 | rx5 | 22 | 0.955 | 0.511 | 4.2 | 0.907 | 61.07 |
| preflop | vs_open | HJ | 2 | d80+ | PF | HJ:c BB:rX | rX | 25 | 0.960 | 0.464 | 5.0 | 0.925 | 60.76 |
| preflop | vs_open | SB | 4 | d80+ | PF | HJ:c CO:rX | rX | 37 | 0.919 | 0.407 | 6.3 | 0.863 | 59.95 |
| preflop | vs_3bet | CO | 2 | d<10 | PF | CO:r3 BB:rx5 | rx5 | 86 | 0.860 | 0.392 | 8.9 | 0.770 | 59.48 |
| flop | vs_bet | BB | 2 | d20-40 | LP | BTN:c BB:x / BB:x BTN:bO | bO | 22 | 1.000 | 0.557 | 4.2 | 1.000 | 59.14 |
| preflop | vs_open | SB | 4 | d80+ | PF | LJ:c CO:rX | rX | 28 | 0.893 | 0.525 | 3.9 | 0.774 | 57.78 |

### Calls too much: 12 flagged, top 30

| Street | Line | Pos | Players | Depth | So far | Path | Size | n | Observed | Threshold | z | Edge | Chips |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| river | vs_bet | BB | 2 | d<10 | SRP-b-b | SB:r2 BB:c / SB:bM BB:c / SB:bM BB:c / SB:bM | bM | 43 | 0.625 | 0.500 | -3.3 | 0.378 | 12.48 |
| turn | vs_bet | SB | 2 | d20-40 | SRP-b | HJ:r3 SB:c / SB:x HJ:bM SB:c / SB:x HJ:bM | bM | 30 | 0.522 | 0.500 | -2.3 | 0.329 | 7.16 |
| turn | vs_bet | SB | 2 | d20-40 | SRP-b | CO:r3 SB:c / SB:x CO:bM SB:c / SB:x CO:bM | bM | 45 | 0.571 | 0.500 | -2.2 | 0.260 | 5.85 |
| turn | vs_bet | BB | 2 | d40-80 | SRP-b | SB:r2 BB:c / SB:bM BB:c / SB:bM | bM | 82 | 0.600 | 0.500 | -4.4 | 0.376 | 5.57 |
| turn | vs_bet | BB | 2 | d<10 | SRP-b | SB:r3 BB:c / SB:bM BB:c / SB:bM | bM | 196 | 0.561 | 0.500 | -4.6 | 0.255 | 4.74 |
| turn | vs_bet | BB | 2 | d10-20 | SRP-b | CO:r3 BB:c / BB:x CO:bM BB:c / BB:x CO:bM | bM | 90 | 0.517 | 0.500 | -2.1 | 0.174 | 3.51 |
| turn | vs_bet | BB | 2 | d40-80 | SRP-b | BTN:r3 BB:c / BB:x BTN:bM BB:c / BB:x BTN:bM | bM | 175 | 0.713 | 0.500 | -3.0 | 0.174 | 3.41 |
| river | vs_bet | BTN | 2 | d20-40 | LP-b-b | BTN:c BB:x / BB:bM BTN:c / BB:bM BTN:c / BB:bM | bM | 80 | 0.512 | 0.500 | -2.2 | 0.185 | 3.24 |
| turn | vs_bet | CO | 2 | d20-40 | LP-b | CO:c BB:x / BB:bM CO:c / BB:bM | bM | 57 | 0.556 | 0.500 | -3.2 | 0.335 | 2.98 |
| turn | vs_bet | BTN | 2 | d80+ | LP-b | BTN:c BB:x / BB:bM BTN:c / BB:bM | bM | 208 | 0.558 | 0.500 | -5.2 | 0.278 | 2.17 |
| turn | vs_bet | BB | 2 | d20-40 | LP-b | SB:c BB:x / SB:bM BB:c / SB:bM | bM | 240 | 0.634 | 0.500 | -4.9 | 0.250 | 1.76 |
| turn | vs_bet | BB | 2 | d10-20 | LP-b | BTN:c BB:x / BB:x BTN:bM BB:c / BB:x BTN:bM | bM | 79 | 0.609 | 0.500 | -2.1 | 0.189 | 1.61 |

### Bluffs too much: 5 flagged, top 30

| Street | Line | Pos | Players | Depth | So far | Path | Size | n | Observed | Threshold | z | Edge | Chips |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flop | cbet | BTN | 2 | d40-80 | SRP | BTN:r2 SB:c / SB:x | bS | 22 | 0.383 | 0.194 | 2.2 | 0.129 | 0.68 |
| turn | barrel | SB | 2 | d40-80 | SRP-b | SB:r2 BB:c / SB:bS BB:c / | bS | 24 | 0.406 | 0.199 | 2.5 | -0.087 | -0.64 |
| flop | cbet | CO | 2 | d80+ | SRP | CO:r2 BB:c / BB:x | bS | 23 | 0.529 | 0.197 | 4.0 | 0.123 | 0.59 |
| flop | cbet | BTN | 2 | d<10 | SRP | BTN:r2 BB:c / BB:x | bS | 36 | 0.535 | 0.199 | 5.1 | 0.119 | 0.54 |
| flop | stab | BB | 2 | d40-80 | LP | SB:c BB:x / SB:x | bM | 278 | 0.327 | 0.268 | 2.2 | 0.238 | 0.48 |

### Value bets too much: 97 flagged, top 30

| Street | Line | Pos | Players | Depth | So far | Path | Size | n | Observed | Threshold | z | Edge | Chips |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| river | barrel | HJ | 2 | d80+ | SRP-b-b | HJ:r3 CO:c / HJ:bM CO:c / HJ:bM CO:c / | bM | 20 | 0.072 | 0.279 | -2.1 | 0.935 | 31.46 |
| river | barrel | CO | 2 | d20-40 | SRP-b-b | CO:r3 BTN:c / CO:bM BTN:c / CO:bM BTN:c / | bM | 27 | 0.024 | 0.275 | -2.9 | 0.939 | 30.94 |
| river | barrel | SB | 2 | d<10 | SRP-b-b | BTN:r3 SB:c / SB:bM BTN:c / SB:bM BTN:c / | bM | 40 | 0.023 | 0.277 | -3.6 | 0.995 | 30.30 |
| river | barrel | CO | 2 | d80+ | SRP-b-b | CO:r3 BB:c / BB:x CO:bM BB:c / BB:x CO:bM BB:c / BB:x | bM | 28 | 0.055 | 0.279 | -2.6 | 1.065 | 30.10 |
| river | barrel | SB | 2 | d<10 | SRP-b-b | CO:r3 SB:c / SB:bM CO:c / SB:bM CO:c / | bM | 30 | 0.024 | 0.271 | -3.0 | 0.949 | 28.44 |
| river | barrel | BTN | 2 | d40-80 | SRP-b-b | BTN:r3 BB:c / BB:x BTN:bM BB:c / BB:x BTN:bM BB:c / BB:x | bM | 43 | 0.089 | 0.278 | -2.8 | 1.060 | 28.31 |
| river | barrel | BB | 2 | d10-20 | SRP-b-b | LJ:r3 BB:c / BB:bM LJ:c / BB:bM LJ:c / | bM | 21 | 0.054 | 0.282 | -2.3 | 0.959 | 27.67 |
| river | barrel | SB | 2 | d40-80 | SRP-b-b | SB:r3 BB:c / SB:bM BB:c / SB:bM BB:c / | bM | 60 | 0.034 | 0.278 | -4.2 | 1.019 | 25.74 |
| river | barrel | BB | 2 | d40-80 | SRP-b-b | CO:r2 BB:c / BB:bM CO:c / BB:bM CO:c / | bM | 23 | 0.067 | 0.278 | -2.3 | 0.877 | 22.55 |
| river | barrel | BB | 2 | d<10 | SRP-b-b | CO:r3 BB:c / BB:bM CO:c / BB:bM CO:c / | bM | 76 | 0.068 | 0.271 | -4.0 | 0.757 | 20.63 |
| river | barrel | SB | 2 | d40-80 | SRP-b-b | SB:r2 BB:c / SB:bM BB:c / SB:bM BB:c / | bM | 36 | 0.021 | 0.275 | -3.4 | 0.979 | 20.05 |
| river | barrel | BB | 2 | d10-20 | SRP-b-b | BTN:r2 BB:c / BB:bM BTN:c / BB:bM BTN:c / | bM | 42 | 0.054 | 0.272 | -3.2 | 0.779 | 17.74 |
| river | barrel | BB | 2 | d20-40 | SRP-b-b | BTN:r3 BB:c / BB:bM BTN:c / BB:bM BTN:c / | bM | 91 | 0.057 | 0.275 | -4.7 | 0.627 | 16.81 |
| turn | barrel | HJ | 2 | d20-40 | SRP-b | HJ:r3 BTN:c / HJ:bM BTN:c / | bM | 41 | 0.062 | 0.276 | -3.1 | 0.996 | 14.66 |
| river | barrel | SB | 2 | d20-40 | SRP-b-b | BTN:r2 SB:c / SB:bM BTN:c / SB:bM BTN:c / | bM | 23 | 0.016 | 0.272 | -2.8 | 0.564 | 14.58 |
| river | barrel | BB | 2 | d20-40 | LP-b-b | CO:c BB:x / BB:bM CO:c / BB:bM CO:c / | bM | 24 | 0.066 | 0.287 | -2.4 | 1.093 | 14.39 |
| flop | vs_bet | BTN | 2 | d40-80 | SRP | BTN:r3 SB:c / SB:bM | rM | 24 | 0.052 | 0.290 | -2.6 | 0.969 | 13.48 |
| turn | barrel | CO | 2 | d20-40 | SRP-b | CO:r3 BTN:c / CO:bM BTN:c / | bM | 48 | 0.084 | 0.279 | -3.0 | 0.879 | 12.97 |
| turn | barrel | CO | 2 | d20-40 | SRP-b | CO:r3 SB:c / SB:x CO:bM SB:c / SB:x | bM | 34 | 0.076 | 0.280 | -2.6 | 0.910 | 12.50 |
| flop | vs_bet | HJ | 2 | d80+ | SRP | HJ:r3 BB:c / BB:bM | rM | 20 | 0.067 | 0.290 | -2.2 | 0.985 | 12.39 |
| turn | barrel | SB | 2 | d80+ | SRP-b | CO:r2 SB:c / SB:bM CO:c / | bM | 22 | 0.053 | 0.272 | -2.3 | 1.031 | 11.96 |
| turn | barrel | HJ | 2 | d20-40 | SRP-b | HJ:r3 BB:c / BB:x HJ:bM BB:c / BB:x | bM | 35 | 0.055 | 0.279 | -3.0 | 0.941 | 11.96 |
| turn | barrel | CO | 2 | d10-20 | SRP-b | CO:r3 BB:c / BB:x CO:bM BB:c / BB:x | bM | 64 | 0.088 | 0.277 | -3.4 | 0.951 | 11.84 |
| turn | barrel | BB | 2 | d20-40 | SRP-b | LJ:r3 BB:c / BB:bM LJ:c / | bM | 28 | 0.095 | 0.278 | -2.2 | 0.905 | 11.39 |
| turn | barrel | SB | 2 | d10-20 | SRP-b | CO:r3 SB:c / SB:bM CO:c / | bM | 63 | 0.086 | 0.276 | -3.4 | 0.805 | 11.03 |
| turn | barrel | BTN | 2 | d80+ | SRP-b | BTN:r3 BB:c / BB:x BTN:bM BB:c / BB:x | bM | 109 | 0.099 | 0.277 | -4.1 | 0.903 | 10.90 |
| turn | stab | BTN | 2 | d<10 | SRP-b | BTN:r3 BB:c / BB:bM BTN:c / BB:x | bM | 31 | 0.085 | 0.276 | -2.4 | 0.931 | 10.74 |
| turn | barrel | SB | 2 | d10-20 | SRP-b | HJ:r3 SB:c / SB:bM HJ:c / | bM | 43 | 0.093 | 0.274 | -2.7 | 0.772 | 10.53 |
| turn | barrel | HJ | 2 | d80+ | SRP-b | HJ:r3 CO:c / HJ:bM CO:c / | bM | 35 | 0.120 | 0.280 | -2.1 | 0.694 | 10.47 |
| flop | vs_bet | CO | 2 | d80+ | SRP | CO:r3 BB:c / BB:bM | rM | 31 | 0.024 | 0.294 | -3.3 | 0.841 | 10.38 |

## Pool rates

### Unopened, by position

| Pos | n | Open | Limp |
| --- | --- | --- | --- |
| BB | 358 | 0.000 | 0.000 |
| BTN | 93809 | 0.343 | 0.057 |
| CO | 61450 | 0.235 | 0.044 |
| HJ | 49534 | 0.193 | 0.043 |
| LJ | 36094 | 0.174 | 0.048 |
| SB | 40917 | 0.328 | 0.105 |
| UTG | 23518 | 0.154 | 0.052 |
| UTG+1 | 7223 | 0.170 | 0.056 |

### Facing raises

| Spot | n | Fold | Call | Raise |
| --- | --- | --- | --- | --- |
| vs_open | 213854 | 0.800 | 0.143 | 0.057 |
| vs_3bet | 27110 | 0.748 | 0.169 | 0.083 |
| vs_4bet+ | 7983 | 0.204 | 0.300 | 0.496 |

### Postflop bet frequency by class (no bet to face)

| Class | n | Bet |
| --- | --- | --- |
| air | 18007 | 0.164 |
| draw | 3129 | 0.268 |
| strong | 18454 | 0.691 |
| top | 10119 | 0.597 |
| weak | 17370 | 0.294 |

### Flop fold rate by bet size and class

| Size | Class | n | Fold |
| --- | --- | --- | --- |
| big | air | 168 | 0.506 |
| big | draw | 33 | 0.212 |
| big | strong | 170 | 0.065 |
| big | top | 161 | 0.012 |
| big | weak | 198 | 0.348 |
| small | air | 349 | 0.246 |
| small | draw | 66 | 0.000 |
| small | strong | 227 | 0.000 |
| small | top | 333 | 0.000 |
| small | weak | 408 | 0.000 |

### Fold rate facing a first bet, by the previous street (two-street lines)

| Street | Previous street | n | Fold |
| --- | --- | --- | --- |
| flop | pre | 28986 | 0.509 |
| river | bL-c | 227 | 0.194 |
| river | bL-r | 18 | 0.222 |
| river | bM-c | 5444 | 0.216 |
| river | bM-r | 538 | 0.097 |
| river | bO-c | 23 | 0.304 |
| river | bO-r | 1 | 0.000 |
| river | bS-c | 781 | 0.303 |
| river | bS-r | 86 | 0.140 |
| river | x | 3343 | 0.590 |
| turn | bL-c | 277 | 0.173 |
| turn | bL-r | 28 | 0.107 |
| turn | bM-c | 7897 | 0.220 |
| turn | bM-r | 1025 | 0.117 |
| turn | bO-c | 77 | 0.143 |
| turn | bO-r | 4 | 0.000 |
| turn | bS-c | 1360 | 0.353 |
| turn | bS-r | 154 | 0.201 |
| turn | x | 4508 | 0.622 |

## Show and discard

| Measure | Spots | Rate |
| --- | --- | --- |
| Shows the card that pairs the flop | 14567 | 0.252 |
| Keeps the best pair | 6915 | 0.969 |

### Top show-node leaks

Showing the strong card (the kept card that pairs the flop) and bad discards (a better pair was available). Show nodes with 20+ samples only.

| Pos | Class | Public bucket | n | Shows strong card | Bad discard |
| --- | --- | --- | --- | --- | --- |
| BB | air | S | 2317 | - | 1.000 |
| BB | strong | P | 1315 | 1.000 | 0.000 |
| BB | top | P | 468 | 1.000 | 0.032 |
| BB | weak | P | 751 | 1.000 | 0.008 |
| BTN | strong | P | 883 | 1.000 | 0.000 |
| BTN | top | P | 275 | 1.000 | 0.045 |
| BTN | weak | P | 344 | 1.000 | 0.000 |
| CO | strong | P | 471 | 1.000 | 0.000 |
| CO | top | P | 165 | 1.000 | 0.000 |
| CO | weak | P | 151 | 1.000 | 0.043 |
| HJ | strong | P | 327 | 1.000 | 0.000 |
| HJ | top | P | 106 | 1.000 | 0.000 |
| HJ | weak | P | 104 | 1.000 | - |
| LJ | top | P | 59 | 1.000 | 0.032 |
| LJ | weak | P | 98 | 1.000 | - |
| SB | strong | P | 721 | 1.000 | 0.000 |
| SB | top | P | 265 | 1.000 | 0.039 |
| SB | weak | P | 354 | 1.000 | 0.000 |
| UTG+1 | top | P | 20 | 1.000 | - |
| UTG | top | P | 39 | 1.000 | 0.050 |
| UTG | weak | P | 43 | 1.000 | - |
| CO | draw | F | 180 | - | 0.143 |
| SB | draw | F | 307 | - | 0.132 |
| BTN | draw | F | 345 | - | 0.125 |
| BB | draw | F | 581 | - | 0.096 |
| SB | draw | S | 189 | - | 0.083 |
| BTN | draw | S | 199 | - | 0.074 |
| BTN | top | F | 257 | 0.000 | 0.071 |
| BTN | top | B | 232 | 0.000 | 0.050 |
| BB | draw | S | 391 | - | 0.025 |
