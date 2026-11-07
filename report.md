# Hand analyzer report
| Measure | Value |
| --- | --- |
| conservation_failures | 0 |
| decisions | 324388 |
| errors | 0 |
| excluded_decisions | 48140 |
| hands | 139662 |
| node_class_cells | 30363 |
| node_class_cells_20 | 277 |
| node_class_cells_200 | 2 |
| nodes_holding_half_of_decisions | 71 |
| path_nodes | 43401 |
| path_nodes_20 | 1284 |
| path_nodes_200 | 155 |
| phase_seconds_cumulative | {'map': 62.2, 'merge': 62.4, 'report': 62.9, 'write': 63.2} |
| postflop_decisions | 144941 |
| postflop_share_in_usable_cells | 0.2247 |
| preflop_classes_seen | 0 |
| seconds | 63.2 |
| show_nodes | 180 |
| show_nodes_20 | 151 |
| show_nodes_200 | 55 |
| split_cells | 69609 |
| split_cells_20 | 728 |
| split_cells_200 | 9 |

Malformed lines skipped: 0 {}

## Top 30 nodes by chips at stake

Chips at stake = decisions x average pot (BB).

| Street | Line | Pos | Players | Depth | So far | Path | n | Pot BB | Chips |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| preflop | unopened | BTN | 3 | d15-40 | PF | (start) | 37525 | 1.5 | 56118 |
| preflop | unopened | SB | 2 | d15-40 | PF | (start) | 17114 | 1.5 | 25553 |
| preflop | unopened | CO | 4 | d40-100 | PF | (start) | 17074 | 1.5 | 25528 |
| preflop | vs_open | BB | 2 | d<=10 | PF | BTN:rX | 1017 | 18.0 | 18356 |
| preflop | unopened | HJ | 5 | d40-100 | PF | (start) | 12184 | 1.5 | 18251 |
| preflop | vs_open | BB | 2 | d15-40 | PF | BTN:r3 | 3944 | 3.9 | 15430 |
| preflop | vs_3bet | BTN | 2 | d<=10 | PF | BTN:r3 BB:rx5 | 439 | 32.6 | 14323 |
| flop | donk | BB | 2 | d15-40 | SRP | BTN:r3 BB:c / | 2341 | 5.5 | 12819 |
| preflop | unopened | LJ | 6 | d40-100 | PF | (start) | 8311 | 1.5 | 12449 |
| preflop | vs_3bet | BTN | 2 | d<=10 | PF | BTN:r2 BB:rx5 | 365 | 29.2 | 10662 |
| preflop | vs_open | BB | 2 | d<=10 | PF | SB:rX | 390 | 24.5 | 9566 |
| preflop | vs_open | BB | 2 | d15-40 | PF | BTN:r2 | 2753 | 3.4 | 9470 |
| preflop | unopened | UTG | 8 | d40-100 | PF | (start) | 5493 | 1.5 | 8235 |
| preflop | vs_3bet | SB | 2 | d<=10 | PF | SB:r3 BB:rx5 | 191 | 42.8 | 8169 |
| flop | donk | BB | 2 | d15-40 | SRP | BTN:r2 BB:c / | 1629 | 4.7 | 7617 |
| preflop | vs_open | BB | 2 | d15-40 | PF | CO:r3 | 1779 | 4.1 | 7269 |
| preflop | vs_open | SB | 3 | d15-40 | PF | BTN:r3 | 1764 | 4.1 | 7196 |
| flop | vs_bet | BTN | 2 | d15-40 | SRP | BTN:r3 BB:c / BB:bM | 783 | 8.9 | 6975 |
| preflop | vs_open | BB | 2 | d15-40 | PF | SB:r3 | 1922 | 3.6 | 6957 |
| flop | donk | BB | 2 | d40-100 | SRP | CO:r3 BB:c / | 1177 | 5.7 | 6666 |
| preflop | vs_3bet | SB | 2 | d<=10 | PF | SB:r2 BB:rx5 | 185 | 35.5 | 6567 |
| flop | cbet | SB | 2 | d15-40 | SRP | SB:r3 BB:c / | 1111 | 5.3 | 5883 |
| preflop | vs_limp | BB | 2 | d15-40 | PF | BTN:c | 2633 | 2.2 | 5770 |
| flop | cbet | BTN | 2 | d15-40 | SRP | BTN:r3 BB:c / BB:x | 985 | 5.5 | 5447 |
| flop | vs_bet | BTN | 2 | d15-40 | SRP | BTN:r2 BB:c / BB:bM | 701 | 7.5 | 5249 |
| flop | vs_bet | BB | 2 | d15-40 | SRP | BTN:r3 BB:c / BB:x BTN:bM | 582 | 8.8 | 5106 |
| preflop | vs_3bet | BTN | 2 | d<=10 | PF | BTN:r3 SB:rx5 | 155 | 32.7 | 5065 |
| preflop | vs_limp | BB | 2 | d15-40 | PF | SB:c | 2517 | 2.0 | 5030 |
| preflop | vs_open | SB | 2 | d<=10 | PF | SB:c BB:rX | 185 | 26.8 | 4957 |
| preflop | vs_open | SB | 3 | d40-100 | PF | CO:r3 | 1212 | 4.1 | 4946 |

## Deviation verdicts

A verdict needs its 95% interval to clear the line. Results are split by effective stack (10bb or less, 10-15, 15-40, above 40bb) wherever a group has 20+ samples.

- **Folds and calls:** the fold rate against 1 - MDF, which is B/(P+B) in chips. Where the data has tournament points, the line is the same break-even in points (ICM), and Chip line shows the chip version. With k players still to answer, each needs line^(1/k).
- **Bluffs and value:** a bet is a bluff when the bettor's hand has under 50% equity against our range, estimated by the EM. The share is compared with B/(P+2B), in points where available. These are estimates, and their intervals include refitting the model.
- **Edge:** per decision. For folds and calls, what a bluff earns; for bluffs and value, what the right response earns. Total = edge x spots.
- **Preflop:** only players defending their own earlier action, or a blind against one raise. 579 cold-call spots have no verdict, since folding there is not a leak.
- **Not tested:** 198 bet spots had too few sampled bets for an equity estimate.

### Folds too much: 582 flagged, top 30

| Street | Line | Pos | Players | Depth | So far | Path | Size | n | Observed (95% CI) | Line | Chip line | Edge (95% CI) | Total | Basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| preflop | vs_open | BB | 2 | d15-40 | PF | BTN:r3 | r3 | 5734 | 0.700 (0.688-0.712) | 0.410 | 0.461 | 0.397 (0.381-0.413) pts | 2277.2 | observed |
| preflop | vs_open | BB | 2 | d10-15 | PF | BTN:r3 | r3 | 2370 | 0.715 (0.696-0.733) | 0.416 | 0.520 | 0.596 (0.559-0.632) pts | 1412.6 | observed |
| preflop | vs_open | BB | 2 | d15-40 | PF | CO:r3 | r3 | 2588 | 0.723 (0.705-0.739) | 0.396 | 0.426 | 0.498 (0.471-0.524) pts | 1288.8 | observed |
| preflop | vs_open | BB | 2 | d15-40 | PF | BTN:r2 | r2 | 3332 | 0.655 (0.639-0.671) | 0.346 | 0.392 | 0.379 (0.359-0.399) pts | 1263.4 | observed |
| preflop | vs_open | SB | 3 | d15-40 | PF | BTN:r3 | r3 | 4308 | 0.838 (0.827-0.849) | 0.744 | 0.745 | 0.265 (0.232-0.297) pts | 1141.7 | observed |
| preflop | vs_open | BB | 2 | d15-40 | PF | SB:r3 | r3 | 3061 | 0.724 (0.708-0.739) | 0.455 | 0.535 | 0.353 (0.332-0.374) pts | 1081.5 | observed |
| preflop | vs_open | SB | 3 | d15-40 | PF | CO:r3 | r3 | 2942 | 0.851 (0.838-0.864) | 0.723 | 0.745 | 0.352 (0.313-0.389) pts | 1034.8 | observed |
| preflop | vs_open | BB | 2 | d<=10 | PF | CO:r3 | r3 | 823 | 0.796 (0.767-0.822) | 0.423 | 0.416 | 1.240 (1.144-1.327) pts | 1020.9 | observed |
| preflop | vs_open | SB | 3 | d<=10 | PF | BTN:r3 | r3 | 1583 | 0.878 (0.861-0.893) | 0.770 | 0.722 | 0.600 (0.500-0.691) pts | 949.8 | observed |
| preflop | vs_open | BB | 2 | d10-15 | PF | BTN:r2 | r2 | 1488 | 0.687 (0.663-0.710) | 0.347 | 0.421 | 0.599 (0.557-0.640) pts | 891.7 | observed |
| preflop | vs_open | BB | 2 | d15-40 | PF | HJ:r3 | r3 | 1677 | 0.743 (0.722-0.763) | 0.393 | 0.447 | 0.502 (0.471-0.531) pts | 841.5 | observed |
| preflop | vs_open | BB | 2 | d<=10 | PF | CO:rX | rX | 1048 | 0.872 (0.851-0.891) | 0.818 | 0.812 | 0.725 (0.438-0.976) pts | 760.1 | observed |
| preflop | vs_open | BB | 2 | d10-15 | PF | CO:r3 | r3 | 821 | 0.767 (0.737-0.795) | 0.400 | 0.494 | 0.856 (0.786-0.920) pts | 702.8 | observed |
| preflop | vs_open | SB | 3 | d15-40 | PF | HJ:r3 | r3 | 1885 | 0.864 (0.848-0.879) | 0.720 | 0.734 | 0.363 (0.319-0.404) pts | 684.1 | observed |
| preflop | vs_open | BB | 2 | d15-40 | PF | CO:r2 | r2 | 1374 | 0.669 (0.644-0.693) | 0.329 | 0.349 | 0.488 (0.452-0.523) pts | 670.5 | observed |
| preflop | vs_open | SB | 3 | d<=10 | PF | CO:r3 | r3 | 837 | 0.879 (0.856-0.900) | 0.717 | 0.714 | 0.797 (0.670-0.908) pts | 667.0 | observed |
| preflop | vs_open | BB | 3 | d<=10 | PF | BTN:rX SB:c | rX | 151 | 0.874 (0.812-0.918) | 0.658 | 0.423 | 4.374 (3.114-5.258) pts | 660.5 | observed |
| preflop | vs_open | BB | 2 | d<=10 | PF | CO:r2 | r2 | 502 | 0.709 (0.668-0.747) | 0.324 | 0.369 | 1.197 (1.069-1.315) pts | 601.0 | observed |
| preflop | vs_open | SB | 3 | d15-40 | PF | CO:r2 | r2 | 1569 | 0.833 (0.814-0.851) | 0.681 | 0.700 | 0.382 (0.329-0.431) pts | 598.8 | observed |
| preflop | vs_open | SB | 3 | d15-40 | PF | BTN:r2 | r2 | 2544 | 0.812 (0.796-0.826) | 0.728 | 0.726 | 0.230 (0.185-0.273) pts | 584.1 | observed |
| preflop | vs_open | BB | 2 | d15-40 | PF | SB:r2 | r2 | 1646 | 0.668 (0.645-0.690) | 0.374 | 0.454 | 0.342 (0.315-0.368) pts | 563.5 | observed |
| preflop | vs_open | BB | 2 | d10-15 | PF | SB:r3 | r3 | 964 | 0.753 (0.725-0.779) | 0.456 | 0.585 | 0.579 (0.524-0.630) pts | 557.9 | observed |
| preflop | vs_open | BB | 2 | d40-100 | PF | BTN:r3 | r3 | 2785 | 0.682 (0.664-0.699) | 0.393 | 0.401 | 0.195 (0.183-0.207) pts | 543.1 | observed |
| preflop | vs_open | SB | 3 | d10-15 | PF | BTN:r3 | r3 | 1374 | 0.847 (0.827-0.865) | 0.756 | 0.755 | 0.387 (0.298-0.469) pts | 531.7 | observed |
| preflop | vs_open | SB | 3 | d<=10 | PF | CO:r2 | r2 | 515 | 0.885 (0.855-0.910) | 0.685 | 0.669 | 0.942 (0.784-1.075) pts | 485.3 | observed |
| preflop | vs_open | SB | 3 | d<=10 | PF | BTN:r2 | r2 | 870 | 0.843 (0.817-0.865) | 0.752 | 0.675 | 0.544 (0.383-0.690) pts | 473.1 | observed |
| preflop | vs_open | BB | 2 | d40-100 | PF | CO:r3 | r3 | 2273 | 0.691 (0.672-0.710) | 0.389 | 0.387 | 0.207 (0.194-0.220) pts | 470.2 | observed |
| preflop | vs_open | BB | 3 | d15-40 | PF | BTN:r3 SB:c | r3 | 389 | 0.776 (0.732-0.815) | 0.311 | 0.268 | 1.194 (1.081-1.293) pts | 464.4 | observed |
| preflop | vs_open | BB | 2 | d10-15 | PF | SB:r2 | r2 | 671 | 0.741 (0.706-0.772) | 0.374 | 0.568 | 0.677 (0.614-0.736) pts | 454.6 | observed |
| preflop | vs_open | BB | 2 | d<=10 | PF | BTN:r3 | r3 | 2605 | 0.745 (0.728-0.762) | 0.718 | 0.497 | 0.167 (0.062-0.267) pts | 435.1 | observed |

### Calls too much: 71 flagged, top 30

| Street | Line | Pos | Players | Depth | So far | Path | Size | n | Observed (95% CI) | Line | Chip line | Edge (95% CI) | Total | Basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| preflop | vs_open | BB | 2 | d<=10 | PF | BTN:rX | rX | 6671 | 0.848 (0.839-0.856) | 0.911 | 0.783 | -1.198 (-1.365--1.040) pts | -7994.6 | observed |
| preflop | vs_open | SB | 3 | d15-40 | PF | BTN:rX | rX | 674 | 0.893 (0.868-0.914) | 0.962 | 0.924 | -2.354 (-3.190--1.645) pts | -1586.4 | observed |
| preflop | vs_open | BB | 2 | d<=10 | PF | BTN:r4 | r4 | 575 | 0.741 (0.704-0.775) | 0.884 | 0.634 | -2.493 (-3.142--1.900) pts | -1433.6 | observed |
| preflop | vs_open | BB | 2 | d<=10 | PF | BTN:r2 | r2 | 1754 | 0.647 (0.624-0.669) | 0.742 | 0.427 | -0.685 (-0.848--0.526) pts | -1201.6 | observed |
| preflop | vs_open | SB | 3 | d<=10 | PF | BTN:rX | rX | 1404 | 0.905 (0.889-0.920) | 0.929 | 0.888 | -0.596 (-0.997--0.242) pts | -836.3 | observed |
| preflop | vs_open | SB | 3 | d10-15 | PF | BTN:rX | rX | 487 | 0.912 (0.883-0.934) | 0.956 | 0.922 | -1.683 (-2.736--0.846) pts | -819.8 | observed |
| preflop | vs_3bet | BTN | 2 | d<=10 | PF | BTN:r2 BB:rx5 | rx5 | 362 | 0.815 (0.772-0.852) | 0.878 | 0.746 | -1.215 (-2.042--0.515) pts | -439.9 | observed |
| preflop | vs_3bet | BTN | 2 | d<=10 | PF | BTN:r3 BB:rx5 | rx5 | 438 | 0.817 (0.778-0.851) | 0.858 | 0.735 | -0.767 (-1.491--0.144) pts | -335.7 | observed |
| preflop | vs_3bet | BTN | 2 | d<=10 | PF | BTN:r3 BB:rx2 | rx2 | 67 | 0.537 (0.419-0.651) | 0.758 | 0.302 | -4.540 (-6.975--2.188) pts | -304.2 | observed |
| turn | vs_bet | BTN | 2 | d<=10 | SRP-b | BTN:r3 BB:c / BB:bM BTN:c / BB:bM | bM | 52 | 0.308 (0.199-0.443) | 0.634 | 0.370 | -5.786 (-7.712--3.391) pts | -300.9 | observed |
| preflop | vs_open | BB | 3 | d15-40 | PF | BTN:c SB:rX | rX | 22 | 0.591 (0.387-0.767) | 0.953 | 0.854 | -11.948 (-16.198--6.831) pts | -262.9 | observed |
| preflop | vs_open | SB | 3 | d40-100 | PF | BTN:rX | rX | 193 | 0.907 (0.857-0.940) | 0.966 | 0.954 | -1.351 (-2.416--0.594) pts | -260.7 | observed |
| preflop | vs_3bet | BTN | 2 | d<=10 | PF | BTN:r3 BB:rx4 | rx4 | 64 | 0.703 (0.582-0.801) | 0.847 | 0.584 | -3.700 (-6.809--1.183) pts | -236.8 | observed |
| flop | vs_bet | BTN | 2 | d<=10 | SRP | BTN:r3 BB:c / BB:bM | bM | 136 | 0.412 (0.333-0.496) | 0.582 | 0.384 | -1.535 (-2.251--0.775) pts | -208.8 | observed |
| turn | vs_bet | BTN | 2 | d<=10 | SRP-b | BTN:r2 BB:c / BB:bM BTN:c / BB:bM | bM | 42 | 0.333 (0.210-0.484) | 0.635 | 0.363 | -4.627 (-6.515--2.310) pts | -194.3 | observed |
| river | vs_bet | BTN | 2 | d<=10 | SRP-b-b | BTN:r2 BB:c / BB:bM BTN:c / BB:bM BTN:c / BB:bM | bM | 28 | 0.357 (0.207-0.542) | 0.604 | 0.297 | -5.798 (-9.327--1.458) pts | -162.3 | observed |
| preflop | vs_open | BB | 2 | d<=10 | PF | SB:r4 | r4 | 173 | 0.751 (0.682-0.810) | 0.825 | 0.587 | -0.902 (-1.752--0.185) pts | -156.0 | observed |
| river | vs_bet | BTN | 2 | d<=10 | SRP-b-b | BTN:r3 BB:c / BB:bM BTN:c / BB:bM BTN:c / BB:bM | bM | 21 | 0.143 (0.050-0.346) | 0.497 | 0.309 | -6.227 (-7.861--2.653) pts | -130.8 | observed |
| preflop | vs_3bet | BTN | 2 | d<=10 | PF | BTN:r2 BB:rx4 | rx4 | 40 | 0.725 (0.572-0.839) | 0.851 | 0.578 | -3.239 (-7.174--0.316) pts | -129.6 | observed |
| preflop | vs_open | BTN | 2 | d<=10 | PF | BTN:c BB:r2 | r2 | 34 | 0.382 (0.239-0.550) | 0.808 | -0.393 | -3.711 (-4.960--2.255) pts | -126.2 | observed |
| preflop | vs_3bet | BTN | 2 | d<=10 | PF | BTN:r2 BB:rx3 | rx3 | 58 | 0.690 (0.562-0.794) | 0.807 | 0.484 | -2.139 (-4.464--0.243) pts | -124.1 | observed |
| turn | vs_bet | BTN | 2 | d<=10 | SRP-b | BTN:r2 BB:c / BB:bM BTN:c / BB:bL | bL | 22 | 0.409 (0.233-0.613) | 0.750 | 0.483 | -5.521 (-8.381--2.223) pts | -121.5 | observed |
| flop | vs_bet | BTN | 2 | d<=10 | SRP | BTN:r3 BB:c / BB:bS | bS | 33 | 0.212 (0.107-0.378) | 0.560 | 0.215 | -3.624 (-4.722--1.900) pts | -119.6 | observed |
| preflop | vs_3bet | CO | 2 | d<=10 | PF | CO:r2 SB:rx5 | rx5 | 63 | 0.683 (0.560-0.784) | 0.791 | 0.747 | -1.845 (-3.935--0.113) pts | -116.3 | observed |
| flop | vs_bet | BTN | 2 | d<=10 | SRP | BTN:r3 BB:c / BB:bO | bO | 24 | 0.625 (0.427-0.788) | 0.866 | 0.845 | -4.766 (-8.687--1.529) pts | -114.4 | observed |
| flop | vs_bet | BB | 2 | d40-100 | 3BP | SB:r3 BB:rx3 SB:c / SB:bM | bM | 20 | 0.150 (0.052-0.360) | 0.637 | 0.375 | -5.659 (-6.795--3.212) pts | -113.2 | observed |
| preflop | vs_3bet | BTN | 2 | d<=10 | PF | BTN:r2 BB:rx2 | rx2 | 66 | 0.576 (0.456-0.688) | 0.714 | 0.546 | -1.685 (-3.145--0.326) pts | -111.2 | observed |
| turn | vs_bet | BTN | 2 | d<=10 | LP-b | BTN:c BB:x / BB:bM BTN:c / BB:bM | bM | 36 | 0.167 (0.079-0.319) | 0.594 | 0.381 | -2.875 (-3.467--1.850) pts | -103.5 | observed |
| turn | vs_bet | BB | 2 | d<=10 | SRP-b | SB:r3 BB:c / SB:bM BB:c / SB:bM | bM | 23 | 0.261 (0.125-0.465) | 0.576 | 0.384 | -4.291 (-6.132--1.518) pts | -98.7 | observed |
| preflop | vs_open | SB | 3 | d40-100 | PF | LJ:rX | rX | 86 | 0.884 (0.799-0.936) | 0.965 | 0.979 | -1.110 (-2.168--0.410) pts | -95.5 | observed |

### Too many bluffs: 51 flagged, top 30

| Street | Line | Pos | Players | Depth | So far | Path | Size | n | Observed (95% CI) | Line | Chip line | Edge (95% CI) | Total | Basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flop | donk | BB | 2 | d15-40 | SRP | BTN:r3 BB:c / | bS | 59 | 0.673 (0.635-0.698) | 0.191 | 0.187 | 1.447 (1.332-1.521) pts | 120.1 | EM vs our range |
| flop | donk | BB | 2 | d<=10 | SRP | BTN:r3 BB:c / | bS | 26 | 0.669 (0.641-0.691) | 0.162 | 0.165 | 2.989 (2.823-3.122) pts | 116.6 | EM vs our range |
| flop | donk | BB | 2 | d15-40 | SRP | BTN:r3 BB:c / | bM | 61 | 0.344 (0.316-0.367) | 0.282 | 0.276 | 0.250 (0.136-0.343) pts | 91.5 | EM vs our range |
| flop | stab | SB | 2 | d15-40 | LP | SB:c BB:x / | bM | 60 | 0.470 (0.440-0.487) | 0.272 | 0.269 | 0.316 (0.268-0.344) pts | 86.9 | EM vs our range |
| flop | cbet | SB | 2 | d15-40 | SRP | SB:r2 BB:c / | bS | 66 | 0.670 (0.641-0.711) | 0.206 | 0.202 | 1.160 (1.086-1.261) pts | 83.5 | EM vs our range |
| flop | cbet | BTN | 2 | d15-40 | SRP | BTN:r3 BB:c / BB:x | bM | 22 | 0.368 (0.345-0.394) | 0.278 | 0.273 | 0.349 (0.259-0.447) pts | 83.1 | EM vs our range |
| flop | donk | BB | 2 | d15-40 | SRP | BTN:r2 BB:c / | bS | 48 | 0.677 (0.643-0.702) | 0.182 | 0.181 | 1.217 (1.133-1.278) pts | 77.9 | EM vs our range |
| flop | stab | BTN | 2 | d<=10 | LP | BTN:c BB:x / BB:x | bM | 31 | 0.458 (0.430-0.481) | 0.292 | 0.271 | 0.624 (0.519-0.711) pts | 77.4 | EM vs our range |
| flop | stab | SB | 2 | d<=10 | LP | SB:c BB:x / | bM | 31 | 0.460 (0.421-0.477) | 0.298 | 0.268 | 0.634 (0.483-0.702) pts | 75.5 | EM vs our range |
| flop | stab | BB | 2 | d15-40 | LP | BTN:c BB:x / | bM | 55 | 0.476 (0.436-0.501) | 0.274 | 0.274 | 0.312 (0.250-0.352) pts | 69.9 | EM vs our range |
| flop | cbet | SB | 2 | d15-40 | SRP | SB:r3 BB:c / | bM | 34 | 0.357 (0.334-0.386) | 0.282 | 0.271 | 0.300 (0.208-0.415) pts | 69.1 | EM vs our range |
| flop | donk | BB | 2 | d<=10 | SRP | BTN:r2 BB:c / | bS | 22 | 0.670 (0.637-0.692) | 0.174 | 0.174 | 2.358 (2.204-2.462) pts | 66.0 | EM vs our range |
| flop | cbet | BTN | 2 | d15-40 | SRP | BTN:r2 BB:c / BB:x | bS | 47 | 0.631 (0.594-0.681) | 0.209 | 0.206 | 1.133 (1.035-1.268) pts | 64.6 | EM vs our range |
| flop | stab | BB | 2 | d<=10 | LP | BTN:c BB:x / | bM | 27 | 0.456 (0.424-0.467) | 0.295 | 0.270 | 0.538 (0.432-0.576) pts | 64.1 | EM vs our range |
| flop | donk | BB | 2 | d15-40 | SRP | CO:r3 BB:c / | bS | 27 | 0.669 (0.635-0.689) | 0.182 | 0.177 | 1.498 (1.395-1.560) pts | 59.9 | EM vs our range |
| flop | donk | BB | 2 | d10-15 | SRP | BTN:r3 BB:c / | bS | 21 | 0.660 (0.627-0.677) | 0.179 | 0.177 | 2.050 (1.911-2.122) pts | 59.4 | EM vs our range |
| flop | donk | BB | 2 | d15-40 | SRP | BTN:r2 BB:c / | bM | 49 | 0.348 (0.315-0.375) | 0.281 | 0.275 | 0.232 (0.119-0.327) pts | 55.2 | EM vs our range |
| flop | cbet | BTN | 2 | d15-40 | SRP | BTN:r2 BB:c / BB:x | bM | 24 | 0.354 (0.334-0.380) | 0.275 | 0.272 | 0.257 (0.192-0.345) pts | 55.0 | EM vs our range |
| flop | cbet | SB | 2 | d15-40 | SRP | SB:r2 BB:c / | bM | 23 | 0.369 (0.336-0.396) | 0.285 | 0.275 | 0.300 (0.184-0.396) pts | 53.7 | EM vs our range |
| flop | stab | SB | 2 | d10-15 | LP | SB:c BB:x / | bM | 28 | 0.465 (0.440-0.485) | 0.281 | 0.274 | 0.478 (0.413-0.528) pts | 51.7 | EM vs our range |
| turn | barrel | BB | 2 | d15-40 | SRP-b | BTN:r3 BB:c / BB:bS BTN:c / | bS | 25 | 0.615 (0.572-0.652) | 0.169 | 0.171 | 1.678 (1.516-1.819) pts | 50.3 | EM vs our range |
| flop | cbet | BTN | 2 | d<=10 | SRP | BTN:r2 BB:c / BB:x | bS | 20 | 0.633 (0.604-0.674) | 0.216 | 0.186 | 2.380 (2.217-2.614) pts | 50.0 | EM vs our range |
| river | barrel | BB | 2 | d15-40 | SRP-b-b | BTN:r2 BB:c / BB:bS BTN:c / BB:bS BTN:c / | bS | 25 | 0.531 (0.481-0.562) | 0.158 | 0.162 | 1.948 (1.685-2.107) pts | 48.7 | EM vs our range |
| flop | donk | BB | 2 | d10-15 | SRP | BTN:r3 BB:c / | bM | 25 | 0.343 (0.322-0.376) | 0.280 | 0.271 | 0.356 (0.238-0.540) pts | 44.8 | EM vs our range |
| flop | stab | BTN | 2 | d15-40 | LP | BTN:c BB:x / BB:x | bM | 43 | 0.444 (0.402-0.462) | 0.272 | 0.272 | 0.269 (0.203-0.296) pts | 42.4 | EM vs our range |
| flop | donk | BB | 2 | d15-40 | SRP | CO:r3 BB:c / | bM | 31 | 0.351 (0.317-0.390) | 0.291 | 0.278 | 0.268 (0.117-0.443) pts | 42.1 | EM vs our range |
| flop | stab | BTN | 2 | d10-15 | LP | BTN:c BB:x / BB:x | bM | 23 | 0.449 (0.421-0.468) | 0.271 | 0.271 | 0.407 (0.343-0.451) pts | 41.6 | EM vs our range |
| flop | stab | BB | 2 | d15-40 | LP | SB:c BB:x / SB:x | bM | 37 | 0.465 (0.433-0.483) | 0.276 | 0.273 | 0.296 (0.245-0.324) pts | 39.9 | EM vs our range |
| flop | donk | BB | 2 | d40-100 | SRP | BTN:r3 BB:c / | bS | 46 | 0.675 (0.645-0.696) | 0.178 | 0.178 | 0.680 (0.638-0.709) pts | 38.7 | EM vs our range |
| flop | cbet | BTN | 2 | d10-15 | SRP | BTN:r2 BB:c / BB:x | bS | 23 | 0.633 (0.606-0.679) | 0.217 | 0.213 | 1.540 (1.441-1.709) pts | 37.0 | EM vs our range |

### Too much value: 18 flagged, top 30

| Street | Line | Pos | Players | Depth | So far | Path | Size | n | Observed (95% CI) | Line | Chip line | Edge (95% CI) | Total | Basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flop | donk | BB | 2 | d15-40 | SRP | BTN:r3 BB:c / | bL | 55 | 0.228 (0.192-0.267) | 0.339 | 0.329 | 0.633 (0.414-0.840) pts | 34.8 | EM vs our range |
| flop | donk | BB | 2 | d15-40 | SRP | BTN:r2 BB:c / | bL | 45 | 0.220 (0.179-0.252) | 0.337 | 0.326 | 0.562 (0.409-0.760) pts | 25.3 | EM vs our range |
| flop | donk | BB | 2 | d10-15 | SRP | BTN:r3 BB:c / | bL | 23 | 0.215 (0.172-0.246) | 0.338 | 0.325 | 0.953 (0.713-1.281) pts | 21.9 | EM vs our range |
| flop | cbet | BTN | 2 | d15-40 | SRP | BTN:r3 BB:c / BB:x | bL | 39 | 0.250 (0.233-0.285) | 0.339 | 0.327 | 0.462 (0.281-0.546) pts | 19.0 | EM vs our range |
| flop | vs_bet | BTN | 2 | d15-40 | SRP | BTN:r2 BB:c / BB:bM | rM | 20 | 0.178 (0.159-0.197) | 0.290 | 0.271 | 0.773 (0.644-0.908) pts | 17.8 | EM vs our range |
| flop | donk | BB | 2 | d15-40 | SRP | CO:r2 BB:c / | bL | 22 | 0.228 (0.181-0.275) | 0.349 | 0.327 | 0.672 (0.409-0.933) pts | 14.8 | EM vs our range |
| flop | cbet | SB | 2 | d15-40 | SRP | SB:r3 BB:c / | bL | 42 | 0.275 (0.255-0.305) | 0.344 | 0.328 | 0.344 (0.193-0.442) pts | 14.8 | EM vs our range |
| flop | stab | BB | 2 | d<=10 | LP | BTN:c BB:x / | bL | 27 | 0.274 (0.245-0.311) | 0.346 | 0.325 | 0.412 (0.203-0.578) pts | 11.1 | EM vs our range |
| flop | donk | BB | 2 | d40-100 | SRP | BTN:r3 BB:c / | bL | 27 | 0.221 (0.179-0.268) | 0.336 | 0.329 | 0.304 (0.180-0.417) pts | 8.2 | EM vs our range |
| flop | cbet | BTN | 2 | d15-40 | SRP | BTN:r2 BB:c / BB:x | bL | 22 | 0.259 (0.244-0.287) | 0.337 | 0.328 | 0.306 (0.196-0.364) pts | 6.7 | EM vs our range |
| flop | donk | BB | 2 | d40-100 | SRP | CO:r3 BB:c / | bL | 22 | 0.228 (0.183-0.269) | 0.340 | 0.333 | 0.289 (0.184-0.403) pts | 6.4 | EM vs our range |
| flop | donk | BB | 2 | d40-100 | SRP | HJ:r3 BB:c / | bL | 21 | 0.218 (0.172-0.255) | 0.335 | 0.328 | 0.301 (0.205-0.417) pts | 6.3 | EM vs our range |
| flop | stab | SB | 2 | d15-40 | LP | SB:c BB:x / | bL | 39 | 0.268 (0.241-0.300) | 0.336 | 0.330 | 0.141 (0.074-0.197) pts | 5.5 | EM vs our range |
| flop | cbet | SB | 2 | d40-100 | SRP | SB:r3 BB:c / | bL | 31 | 0.275 (0.251-0.303) | 0.339 | 0.331 | 0.169 (0.097-0.234) pts | 5.2 | EM vs our range |
| flop | stab | BB | 2 | d15-40 | LP | BTN:c BB:x / | bL | 35 | 0.278 (0.244-0.312) | 0.330 | 0.327 | 0.103 (0.035-0.170) pts | 3.6 | EM vs our range |
| flop | stab | BB | 2 | d10-15 | LP | BTN:c BB:x / | bL | 21 | 0.281 (0.245-0.323) | 0.324 | 0.324 | 0.130 (0.004-0.237) pts | 2.7 | EM vs our range |
| flop | stab | BB | 2 | d15-40 | LP | SB:c BB:x / SB:x | bL | 22 | 0.290 (0.255-0.326) | 0.335 | 0.329 | 0.110 (0.024-0.197) pts | 2.4 | EM vs our range |
| flop | stab | SB | 2 | d40-100 | LP | SB:c BB:x / | bL | 21 | 0.275 (0.242-0.308) | 0.331 | 0.329 | 0.057 (0.023-0.092) pts | 1.2 | EM vs our range |

## Pool rates

Rates show a 95% interval in brackets, treating decisions as independent.

### Unopened, by position

| Pos | n | Open | Limp |
| --- | --- | --- | --- |
| BB | 242 | 0.000 (0.000-0.016) | 0.000 (0.000-0.016) |
| BTN | 77608 | 0.429 (0.425-0.432) | 0.055 (0.053-0.056) |
| CO | 54344 | 0.287 (0.283-0.291) | 0.027 (0.026-0.028) |
| HJ | 47894 | 0.227 (0.223-0.231) | 0.027 (0.026-0.029) |
| LJ | 37116 | 0.193 (0.189-0.197) | 0.031 (0.029-0.032) |
| SB | 31105 | 0.450 (0.445-0.456) | 0.095 (0.092-0.099) |
| UTG | 27834 | 0.164 (0.159-0.168) | 0.034 (0.032-0.036) |
| UTG+1 | 10006 | 0.181 (0.174-0.189) | 0.044 (0.040-0.048) |

### Facing raises

| Spot | n | Fold | Call | Raise |
| --- | --- | --- | --- | --- |
| vs_open | 237448 | 0.815 (0.813-0.816) | 0.124 (0.122-0.125) | 0.062 (0.061-0.063) |
| vs_3bet | 30546 | 0.788 (0.784-0.793) | 0.152 (0.148-0.156) | 0.060 (0.057-0.063) |
| vs_4bet+ | 4071 | 0.329 (0.315-0.344) | 0.338 (0.324-0.353) | 0.333 (0.318-0.347) |

### Postflop bet frequency by class (no bet to face)

Class known on 0.378 of these bets. Rates need 80%: below that they describe hands that got shown.

| Class | Known n | Bet |
| --- | --- | --- |
| air | 11216 | withheld |
| draw | 1791 | withheld |
| strong | 11958 | withheld |
| top | 6435 | withheld |
| weak | 10352 | withheld |

### Flop fold rate by bet size and class

Rates need 80% of the folds to have known cards, since a folded hand is rarely shown.

| Size | Class | Known n | Folds with known cards | Fold |
| --- | --- | --- | --- | --- |
| big | air | 142 | 0.000 | withheld |
| big | draw | 32 | 0.000 | withheld |
| big | strong | 279 | 0.000 | withheld |
| big | top | 367 | 0.000 | withheld |
| big | weak | 283 | 0.000 | withheld |
| small | air | 163 | 0.000 | withheld |
| small | draw | 57 | 0.000 | withheld |
| small | strong | 153 | 0.000 | withheld |
| small | top | 203 | 0.000 | withheld |
| small | weak | 252 | 0.000 | withheld |

### Fold rate facing a first bet, by the previous street (two-street lines)

| Street | Previous street | n | Fold |
| --- | --- | --- | --- |
| flop | pre | 29040 | 0.539 (0.533-0.544) |
| river | bL-c | 569 | 0.306 (0.269-0.345) |
| river | bL-r | 35 | 0.114 (0.045-0.260) |
| river | bM-c | 3453 | 0.348 (0.332-0.364) |
| river | bM-r | 245 | 0.200 (0.155-0.255) |
| river | bO-c | 29 | 0.310 (0.173-0.492) |
| river | bO-r | 1 | 0.000 (0.000-0.793) |
| river | bS-c | 774 | 0.424 (0.389-0.459) |
| river | bS-r | 41 | 0.244 (0.138-0.393) |
| river | x | 2301 | 0.714 (0.695-0.732) |
| turn | bL-c | 1071 | 0.309 (0.282-0.337) |
| turn | bL-r | 91 | 0.099 (0.053-0.177) |
| turn | bM-c | 7001 | 0.355 (0.343-0.366) |
| turn | bM-r | 696 | 0.190 (0.162-0.220) |
| turn | bO-c | 65 | 0.431 (0.318-0.552) |
| turn | bO-r | 6 | 0.000 (0.000-0.390) |
| turn | bS-c | 1353 | 0.398 (0.372-0.424) |
| turn | bS-r | 68 | 0.176 (0.104-0.284) |
| turn | x | 3022 | 0.671 (0.654-0.688) |

## Show and discard

Kept cards are known for 35266 of 80454 players who reached the flop (0.438). Below 80%, these rates describe hands that reached showdown, not every flop.

| Measure | Spots | Rate |
| --- | --- | --- |
| Shows the card that pairs the flop, when one kept card does | 10264 | 0.205 (0.198-0.213) |
| Keeps the best pair, when the pairs differ | 0 | - |

### Show leaks by position and class

How often the player shows the kept card that pairs the flop, when exactly one does: the choice that gives the hand away. Grouped without the public bucket, because bucket P means the shown card pairs the flop by definition. 20+ spots only.

| Pos | Class | n | Spots | Shows strong card |
| --- | --- | --- | --- | --- |
| LJ | weak | 460 | 155 | 0.310 (0.242-0.386) |
| SB | weak | 1584 | 797 | 0.297 (0.267-0.330) |
| BB | weak | 2869 | 1637 | 0.296 (0.275-0.319) |
| UTG+1 | weak | 158 | 62 | 0.290 (0.192-0.413) |
| UTG | weak | 250 | 83 | 0.289 (0.203-0.394) |
| CO | weak | 958 | 405 | 0.281 (0.240-0.327) |
| HJ | weak | 620 | 233 | 0.258 (0.206-0.317) |
| BTN | weak | 1910 | 946 | 0.241 (0.215-0.269) |
| LJ | strong | 422 | 76 | 0.184 (0.113-0.286) |
| CO | strong | 811 | 131 | 0.176 (0.120-0.250) |
| SB | top | 1534 | 817 | 0.174 (0.149-0.201) |
| BB | strong | 1997 | 469 | 0.171 (0.139-0.207) |
| CO | top | 1085 | 503 | 0.163 (0.133-0.198) |
| SB | strong | 1231 | 265 | 0.162 (0.123-0.211) |
| UTG | top | 381 | 153 | 0.157 (0.108-0.223) |
| UTG | strong | 279 | 48 | 0.146 (0.072-0.272) |
| BB | top | 2395 | 1359 | 0.145 (0.127-0.165) |
| BTN | strong | 1476 | 306 | 0.141 (0.106-0.184) |
| LJ | top | 598 | 259 | 0.139 (0.102-0.186) |
| UTG+1 | top | 180 | 73 | 0.137 (0.076-0.234) |
| BTN | top | 1829 | 999 | 0.132 (0.113-0.155) |
| HJ | top | 832 | 366 | 0.131 (0.100-0.170) |
| HJ | strong | 599 | 92 | 0.120 (0.068-0.202) |
| UTG+1 | strong | 140 | 30 | 0.100 (0.035-0.256) |

### Bad discards by position and best available class

Grouped by the best pair the player could have kept, because a kept class of air with a better option is a bad discard by definition. Needs the three dealt cards, so it is empty when only opponents are counted. 20+ spots only.

| Pos | Best available | Spots | Bad discard |
| --- | --- | --- | --- |

---

# What opponents folded and how often they bluff (EM estimate)

Opponents only: 65765 lines, 144941 postflop decisions, 26038 folds, of which 0 have known cards. The EM stopped after 53 iterations. These are model estimates, not observed cards.

Brackets and CI columns are 95% intervals from 10 refits, resampling 1009 tables. With this few refits the interval ends are approximate.

## Fold rate by hand class and bet size faced

| Street | Size | n | All | All CI | air | draw | weak | top | strong |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flop | S | 3191 | 0.296 | 0.284 to 0.307 | 0.557 (0.515 to 0.573) | 0.198 (0.115 to 0.289) | 0.223 (0.193 to 0.285) | 0.124 (0.091 to 0.153) | 0.063 (0.017 to 0.080) |
| flop | M | 21996 | 0.521 | 0.511 to 0.526 | 0.779 (0.769 to 0.788) | 0.523 (0.487 to 0.557) | 0.508 (0.480 to 0.524) | 0.208 (0.195 to 0.228) | 0.077 (0.046 to 0.086) |
| flop | L | 5177 | 0.653 | 0.642 to 0.661 | 0.874 (0.857 to 0.884) | 0.719 (0.667 to 0.793) | 0.649 (0.633 to 0.660) | 0.321 (0.273 to 0.344) | 0.132 (0.082 to 0.223) |
| flop | O | 1197 | 0.707 | 0.677 to 0.718 | 0.900 (0.886 to 0.916) | 0.845 (0.710 to 0.939) | 0.730 (0.688 to 0.765) | 0.493 (0.415 to 0.513) | 0.223 (0.111 to 0.296) |
| turn | S | 2078 | 0.209 | 0.197 to 0.222 | 0.497 (0.437 to 0.527) | 0.252 (0.177 to 0.317) | 0.198 (0.176 to 0.233) | 0.081 (0.062 to 0.108) | 0.044 (0.015 to 0.070) |
| turn | M | 9706 | 0.413 | 0.402 to 0.418 | 0.705 (0.686 to 0.723) | 0.697 (0.617 to 0.728) | 0.416 (0.399 to 0.433) | 0.192 (0.174 to 0.201) | 0.049 (0.031 to 0.062) |
| turn | L | 2247 | 0.474 | 0.462 to 0.491 | 0.738 (0.714 to 0.782) | 0.791 (0.751 to 0.825) | 0.497 (0.481 to 0.532) | 0.286 (0.254 to 0.334) | 0.083 (0.047 to 0.104) |
| turn | O | 565 | 0.618 | 0.579 to 0.632 | 0.893 (0.853 to 0.942) | 0.734 (0.655 to 0.823) | 0.656 (0.574 to 0.667) | 0.544 (0.479 to 0.616) | 0.163 (0.091 to 0.248) |
| river | S | 1534 | 0.245 | 0.226 to 0.260 | 0.502 (0.466 to 0.545) | - | 0.251 (0.212 to 0.298) | 0.160 (0.092 to 0.168) | 0.061 (0.032 to 0.080) |
| river | M | 4688 | 0.468 | 0.455 to 0.483 | 0.756 (0.742 to 0.764) | - | 0.493 (0.477 to 0.530) | 0.229 (0.199 to 0.239) | 0.179 (0.144 to 0.198) |
| river | L | 1194 | 0.526 | 0.516 to 0.542 | 0.764 (0.719 to 0.818) | - | 0.557 (0.530 to 0.578) | 0.377 (0.346 to 0.451) | 0.243 (0.215 to 0.303) |
| river | O | 527 | 0.660 | 0.619 to 0.687 | 0.872 (0.831 to 0.915) | - | 0.673 (0.650 to 0.704) | 0.517 (0.473 to 0.615) | 0.408 (0.286 to 0.506) |

## What the folded hands were

| Street | Size | Folds | air | draw | weak | top | strong | Shown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flop | S | 945 | 0.638 (0.565 to 0.683) | 0.039 (0.024 to 0.058) | 0.207 (0.179 to 0.261) | 0.095 (0.071 to 0.111) | 0.022 (0.006 to 0.028) | 0 |
| flop | M | 11465 | 0.570 (0.557 to 0.590) | 0.061 (0.056 to 0.066) | 0.277 (0.260 to 0.291) | 0.082 (0.078 to 0.090) | 0.010 (0.006 to 0.012) | 0 |
| flop | L | 3379 | 0.516 (0.497 to 0.534) | 0.058 (0.055 to 0.063) | 0.325 (0.315 to 0.333) | 0.092 (0.079 to 0.101) | 0.010 (0.006 to 0.017) | 0 |
| flop | O | 846 | 0.468 (0.448 to 0.495) | 0.063 (0.055 to 0.074) | 0.291 (0.278 to 0.312) | 0.153 (0.138 to 0.166) | 0.025 (0.012 to 0.034) | 0 |
| turn | S | 434 | 0.470 (0.406 to 0.533) | 0.085 (0.061 to 0.107) | 0.319 (0.285 to 0.361) | 0.094 (0.068 to 0.130) | 0.033 (0.012 to 0.049) | 0 |
| turn | M | 4012 | 0.399 (0.383 to 0.418) | 0.139 (0.126 to 0.146) | 0.347 (0.340 to 0.365) | 0.100 (0.089 to 0.106) | 0.015 (0.010 to 0.019) | 0 |
| turn | L | 1064 | 0.329 (0.312 to 0.344) | 0.112 (0.101 to 0.124) | 0.404 (0.397 to 0.438) | 0.135 (0.118 to 0.159) | 0.020 (0.011 to 0.024) | 0 |
| turn | O | 349 | 0.300 (0.277 to 0.350) | 0.091 (0.074 to 0.105) | 0.381 (0.343 to 0.395) | 0.190 (0.164 to 0.213) | 0.037 (0.021 to 0.056) | 0 |
| river | S | 376 | 0.427 (0.414 to 0.462) | 0.000 (0.000 to 0.000) | 0.389 (0.349 to 0.435) | 0.132 (0.076 to 0.131) | 0.052 (0.028 to 0.076) | 0 |
| river | M | 2192 | 0.431 (0.421 to 0.452) | 0.000 (0.000 to 0.000) | 0.422 (0.407 to 0.445) | 0.088 (0.078 to 0.093) | 0.059 (0.047 to 0.067) | 0 |
| river | L | 628 | 0.358 (0.333 to 0.383) | 0.000 (0.000 to 0.000) | 0.428 (0.407 to 0.449) | 0.148 (0.134 to 0.180) | 0.066 (0.058 to 0.087) | 0 |
| river | O | 348 | 0.354 (0.339 to 0.368) | 0.000 (0.000 to 0.000) | 0.420 (0.379 to 0.442) | 0.135 (0.115 to 0.166) | 0.091 (0.075 to 0.116) | 0 |

## Folded hands by position (50+ folds)

| Street | Pos | Size | Folds | air | draw | weak | top | strong |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flop | BB | S | 315 | 0.699 (0.636 to 0.749) | 0.042 (0.027 to 0.062) | 0.190 (0.154 to 0.236) | 0.055 (0.034 to 0.064) | 0.014 (0.003 to 0.021) |
| flop | BB | M | 3841 | 0.606 (0.590 to 0.625) | 0.062 (0.057 to 0.070) | 0.268 (0.251 to 0.284) | 0.057 (0.052 to 0.063) | 0.007 (0.005 to 0.008) |
| flop | BB | L | 918 | 0.567 (0.553 to 0.575) | 0.063 (0.056 to 0.073) | 0.295 (0.290 to 0.308) | 0.068 (0.056 to 0.076) | 0.007 (0.004 to 0.015) |
| flop | BB | O | 247 | 0.534 (0.514 to 0.565) | 0.069 (0.060 to 0.089) | 0.264 (0.248 to 0.283) | 0.116 (0.102 to 0.126) | 0.018 (0.008 to 0.030) |
| flop | BTN | S | 178 | 0.606 (0.523 to 0.652) | 0.037 (0.022 to 0.066) | 0.229 (0.199 to 0.283) | 0.107 (0.074 to 0.130) | 0.021 (0.004 to 0.026) |
| flop | BTN | M | 2275 | 0.527 (0.515 to 0.543) | 0.059 (0.056 to 0.066) | 0.295 (0.283 to 0.309) | 0.102 (0.096 to 0.116) | 0.016 (0.009 to 0.019) |
| flop | BTN | L | 729 | 0.481 (0.461 to 0.504) | 0.052 (0.048 to 0.061) | 0.344 (0.329 to 0.357) | 0.113 (0.093 to 0.124) | 0.011 (0.007 to 0.017) |
| flop | BTN | O | 156 | 0.420 (0.377 to 0.443) | 0.055 (0.045 to 0.079) | 0.320 (0.302 to 0.348) | 0.160 (0.135 to 0.163) | 0.045 (0.021 to 0.065) |
| flop | CO | S | 112 | 0.570 (0.468 to 0.647) | 0.028 (0.015 to 0.049) | 0.251 (0.201 to 0.327) | 0.113 (0.077 to 0.138) | 0.039 (0.008 to 0.052) |
| flop | CO | M | 1283 | 0.533 (0.514 to 0.559) | 0.056 (0.049 to 0.063) | 0.286 (0.260 to 0.306) | 0.111 (0.105 to 0.124) | 0.013 (0.007 to 0.014) |
| flop | CO | L | 395 | 0.458 (0.431 to 0.491) | 0.053 (0.043 to 0.061) | 0.359 (0.347 to 0.372) | 0.119 (0.105 to 0.129) | 0.011 (0.005 to 0.024) |
| flop | CO | O | 98 | 0.405 (0.390 to 0.459) | 0.057 (0.044 to 0.068) | 0.320 (0.289 to 0.361) | 0.185 (0.147 to 0.203) | 0.034 (0.013 to 0.045) |
| flop | HJ | S | 86 | 0.596 (0.487 to 0.654) | 0.043 (0.018 to 0.074) | 0.194 (0.163 to 0.267) | 0.135 (0.099 to 0.173) | 0.032 (0.007 to 0.052) |
| flop | HJ | M | 911 | 0.541 (0.518 to 0.564) | 0.062 (0.054 to 0.075) | 0.274 (0.247 to 0.291) | 0.110 (0.101 to 0.123) | 0.014 (0.008 to 0.019) |
| flop | HJ | L | 297 | 0.490 (0.452 to 0.511) | 0.057 (0.051 to 0.073) | 0.317 (0.293 to 0.329) | 0.122 (0.101 to 0.142) | 0.015 (0.007 to 0.025) |
| flop | HJ | O | 75 | 0.397 (0.364 to 0.426) | 0.074 (0.062 to 0.108) | 0.313 (0.267 to 0.339) | 0.203 (0.161 to 0.245) | 0.014 (0.006 to 0.028) |
| flop | LJ | S | 60 | 0.582 (0.501 to 0.615) | 0.037 (0.020 to 0.063) | 0.215 (0.172 to 0.279) | 0.144 (0.111 to 0.182) | 0.022 (0.007 to 0.030) |
| flop | LJ | M | 676 | 0.525 (0.510 to 0.547) | 0.062 (0.059 to 0.071) | 0.286 (0.267 to 0.294) | 0.115 (0.102 to 0.135) | 0.012 (0.006 to 0.014) |
| flop | LJ | L | 252 | 0.479 (0.457 to 0.494) | 0.055 (0.042 to 0.063) | 0.350 (0.335 to 0.360) | 0.104 (0.100 to 0.123) | 0.011 (0.008 to 0.020) |
| flop | LJ | O | 54 | 0.466 (0.426 to 0.511) | 0.052 (0.027 to 0.077) | 0.242 (0.194 to 0.291) | 0.217 (0.174 to 0.255) | 0.023 (0.007 to 0.035) |
| flop | SB | S | 134 | 0.687 (0.619 to 0.702) | 0.040 (0.021 to 0.061) | 0.171 (0.160 to 0.241) | 0.088 (0.067 to 0.119) | 0.014 (0.002 to 0.018) |
| flop | SB | M | 1827 | 0.622 (0.608 to 0.641) | 0.063 (0.054 to 0.072) | 0.257 (0.242 to 0.266) | 0.055 (0.051 to 0.059) | 0.004 (0.002 to 0.005) |
| flop | SB | L | 569 | 0.558 (0.539 to 0.579) | 0.065 (0.062 to 0.077) | 0.309 (0.296 to 0.324) | 0.062 (0.050 to 0.071) | 0.005 (0.002 to 0.009) |
| flop | SB | O | 144 | 0.510 (0.479 to 0.536) | 0.062 (0.048 to 0.077) | 0.291 (0.262 to 0.315) | 0.121 (0.105 to 0.160) | 0.016 (0.006 to 0.023) |
| flop | UTG | M | 415 | 0.523 (0.499 to 0.556) | 0.053 (0.048 to 0.060) | 0.320 (0.289 to 0.342) | 0.092 (0.082 to 0.099) | 0.012 (0.007 to 0.014) |
| flop | UTG | L | 127 | 0.495 (0.471 to 0.533) | 0.042 (0.027 to 0.059) | 0.347 (0.309 to 0.376) | 0.104 (0.087 to 0.127) | 0.011 (0.003 to 0.021) |
| flop | UTG | O | 52 | 0.423 (0.367 to 0.479) | 0.068 (0.040 to 0.098) | 0.284 (0.259 to 0.322) | 0.193 (0.136 to 0.232) | 0.031 (0.010 to 0.057) |
| flop | UTG+1 | M | 237 | 0.538 (0.530 to 0.572) | 0.061 (0.039 to 0.069) | 0.285 (0.252 to 0.304) | 0.104 (0.092 to 0.121) | 0.011 (0.006 to 0.015) |
| flop | UTG+1 | L | 92 | 0.471 (0.415 to 0.512) | 0.059 (0.050 to 0.087) | 0.346 (0.313 to 0.387) | 0.106 (0.084 to 0.116) | 0.018 (0.005 to 0.052) |
| turn | BB | S | 124 | 0.517 (0.455 to 0.574) | 0.099 (0.074 to 0.126) | 0.296 (0.257 to 0.371) | 0.055 (0.036 to 0.083) | 0.033 (0.007 to 0.060) |
| turn | BB | M | 1365 | 0.434 (0.409 to 0.456) | 0.151 (0.133 to 0.157) | 0.337 (0.323 to 0.354) | 0.068 (0.061 to 0.077) | 0.010 (0.007 to 0.015) |
| turn | BB | L | 300 | 0.381 (0.367 to 0.397) | 0.115 (0.097 to 0.140) | 0.402 (0.391 to 0.420) | 0.089 (0.071 to 0.103) | 0.013 (0.007 to 0.022) |
| turn | BB | O | 102 | 0.361 (0.328 to 0.439) | 0.100 (0.080 to 0.125) | 0.365 (0.301 to 0.394) | 0.133 (0.095 to 0.168) | 0.040 (0.023 to 0.066) |
| turn | BTN | S | 83 | 0.389 (0.325 to 0.467) | 0.105 (0.064 to 0.136) | 0.356 (0.328 to 0.401) | 0.119 (0.082 to 0.180) | 0.031 (0.006 to 0.034) |
| turn | BTN | M | 771 | 0.370 (0.344 to 0.395) | 0.132 (0.110 to 0.149) | 0.354 (0.350 to 0.372) | 0.127 (0.110 to 0.142) | 0.018 (0.010 to 0.026) |
| turn | BTN | L | 215 | 0.290 (0.251 to 0.313) | 0.103 (0.077 to 0.115) | 0.415 (0.393 to 0.486) | 0.163 (0.125 to 0.229) | 0.029 (0.017 to 0.033) |
| turn | BTN | O | 69 | 0.249 (0.221 to 0.292) | 0.098 (0.077 to 0.138) | 0.404 (0.360 to 0.398) | 0.205 (0.174 to 0.272) | 0.044 (0.016 to 0.088) |
| turn | CO | S | 54 | 0.477 (0.398 to 0.560) | 0.052 (0.023 to 0.076) | 0.308 (0.256 to 0.362) | 0.150 (0.091 to 0.250) | 0.013 (0.002 to 0.022) |
| turn | CO | M | 458 | 0.365 (0.327 to 0.387) | 0.128 (0.117 to 0.140) | 0.355 (0.336 to 0.392) | 0.134 (0.123 to 0.144) | 0.018 (0.009 to 0.023) |
| turn | CO | L | 134 | 0.287 (0.267 to 0.307) | 0.099 (0.087 to 0.100) | 0.426 (0.388 to 0.482) | 0.166 (0.129 to 0.199) | 0.021 (0.011 to 0.033) |
| turn | HJ | M | 294 | 0.380 (0.361 to 0.409) | 0.107 (0.089 to 0.119) | 0.372 (0.349 to 0.401) | 0.121 (0.101 to 0.139) | 0.020 (0.010 to 0.028) |
| turn | HJ | L | 102 | 0.287 (0.270 to 0.356) | 0.110 (0.097 to 0.135) | 0.392 (0.338 to 0.458) | 0.174 (0.142 to 0.184) | 0.036 (0.013 to 0.041) |
| turn | LJ | M | 266 | 0.369 (0.360 to 0.415) | 0.126 (0.103 to 0.135) | 0.345 (0.328 to 0.376) | 0.141 (0.096 to 0.152) | 0.019 (0.011 to 0.030) |
| turn | LJ | L | 73 | 0.286 (0.258 to 0.347) | 0.087 (0.060 to 0.122) | 0.400 (0.372 to 0.453) | 0.196 (0.164 to 0.270) | 0.030 (0.008 to 0.047) |
| turn | SB | S | 92 | 0.527 (0.439 to 0.582) | 0.075 (0.040 to 0.092) | 0.279 (0.221 to 0.324) | 0.079 (0.051 to 0.136) | 0.039 (0.013 to 0.091) |
| turn | SB | M | 638 | 0.428 (0.413 to 0.453) | 0.149 (0.130 to 0.167) | 0.335 (0.326 to 0.363) | 0.078 (0.063 to 0.080) | 0.011 (0.006 to 0.017) |
| turn | SB | L | 166 | 0.391 (0.363 to 0.404) | 0.124 (0.108 to 0.140) | 0.376 (0.357 to 0.401) | 0.104 (0.088 to 0.116) | 0.006 (0.003 to 0.006) |
| turn | SB | O | 50 | 0.347 (0.295 to 0.402) | 0.105 (0.050 to 0.124) | 0.451 (0.391 to 0.475) | 0.088 (0.067 to 0.110) | 0.009 (0.005 to 0.021) |
| turn | UTG | M | 148 | 0.356 (0.335 to 0.398) | 0.154 (0.125 to 0.177) | 0.353 (0.329 to 0.381) | 0.120 (0.095 to 0.136) | 0.017 (0.006 to 0.031) |
| turn | UTG+1 | M | 72 | 0.316 (0.317 to 0.388) | 0.139 (0.083 to 0.148) | 0.394 (0.352 to 0.444) | 0.133 (0.107 to 0.156) | 0.018 (0.008 to 0.025) |
| river | BB | S | 129 | 0.498 (0.456 to 0.537) | 0.000 (0.000 to 0.000) | 0.372 (0.345 to 0.417) | 0.094 (0.055 to 0.105) | 0.035 (0.033 to 0.063) |
| river | BB | M | 783 | 0.452 (0.426 to 0.473) | 0.000 (0.000 to 0.000) | 0.432 (0.409 to 0.464) | 0.065 (0.056 to 0.075) | 0.051 (0.041 to 0.058) |
| river | BB | L | 206 | 0.412 (0.374 to 0.442) | 0.000 (0.000 to 0.000) | 0.436 (0.377 to 0.458) | 0.090 (0.073 to 0.121) | 0.061 (0.049 to 0.083) |
| river | BB | O | 118 | 0.367 (0.338 to 0.399) | 0.000 (0.000 to 0.000) | 0.416 (0.365 to 0.434) | 0.117 (0.099 to 0.160) | 0.099 (0.066 to 0.143) |
| river | BTN | S | 65 | 0.385 (0.348 to 0.441) | 0.000 (0.000 to 0.000) | 0.391 (0.341 to 0.468) | 0.151 (0.095 to 0.165) | 0.073 (0.028 to 0.125) |
| river | BTN | M | 390 | 0.378 (0.358 to 0.408) | 0.000 (0.000 to 0.000) | 0.441 (0.424 to 0.466) | 0.098 (0.079 to 0.100) | 0.083 (0.062 to 0.098) |
| river | BTN | L | 101 | 0.270 (0.246 to 0.304) | 0.000 (0.000 to 0.000) | 0.432 (0.391 to 0.491) | 0.225 (0.166 to 0.287) | 0.073 (0.050 to 0.094) |
| river | BTN | O | 58 | 0.313 (0.255 to 0.369) | 0.000 (0.000 to 0.000) | 0.386 (0.305 to 0.409) | 0.156 (0.115 to 0.217) | 0.145 (0.094 to 0.194) |
| river | CO | M | 252 | 0.415 (0.381 to 0.473) | 0.000 (0.000 to 0.000) | 0.384 (0.367 to 0.436) | 0.126 (0.098 to 0.151) | 0.074 (0.055 to 0.095) |
| river | CO | L | 63 | 0.336 (0.239 to 0.359) | 0.000 (0.000 to 0.000) | 0.412 (0.367 to 0.494) | 0.184 (0.148 to 0.264) | 0.068 (0.051 to 0.098) |
| river | HJ | M | 168 | 0.424 (0.402 to 0.468) | 0.000 (0.000 to 0.000) | 0.406 (0.364 to 0.430) | 0.115 (0.094 to 0.136) | 0.056 (0.039 to 0.076) |
| river | LJ | M | 117 | 0.407 (0.386 to 0.451) | 0.000 (0.000 to 0.000) | 0.399 (0.383 to 0.433) | 0.137 (0.104 to 0.151) | 0.057 (0.034 to 0.073) |
| river | SB | S | 73 | 0.424 (0.383 to 0.508) | 0.000 (0.000 to 0.000) | 0.463 (0.421 to 0.507) | 0.065 (0.023 to 0.067) | 0.048 (0.021 to 0.074) |
| river | SB | M | 374 | 0.479 (0.448 to 0.503) | 0.000 (0.000 to 0.000) | 0.420 (0.389 to 0.455) | 0.056 (0.042 to 0.065) | 0.045 (0.029 to 0.059) |
| river | SB | L | 112 | 0.411 (0.373 to 0.450) | 0.000 (0.000 to 0.000) | 0.441 (0.386 to 0.452) | 0.087 (0.066 to 0.123) | 0.061 (0.045 to 0.099) |
| river | SB | O | 61 | 0.380 (0.329 to 0.415) | 0.000 (0.000 to 0.000) | 0.473 (0.401 to 0.517) | 0.080 (0.066 to 0.108) | 0.067 (0.050 to 0.103) |
| river | UTG | M | 72 | 0.377 (0.345 to 0.428) | 0.000 (0.000 to 0.000) | 0.428 (0.378 to 0.473) | 0.155 (0.132 to 0.189) | 0.040 (0.030 to 0.049) |

## Bluff share behind bets and raises (20+)

A bet is a bluff when the bettor's hand has under 50% equity against our calling range for that street and size. Balance is the share where calling breaks even, B/(P+2B). Class bluff is the older air + draw share, for comparison.

Our range used 70821 of our deals and 7639 of our responses; 18 of 60 response cells lean mostly on the pool.

| Street | Line | Size | Bets | Sampled | Bluff | Bluff CI | Mean equity | Balance | Class bluff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flop | cbet | S | 1126 | 1000 | 0.629 | 0.609 to 0.665 | 0.446 | 0.188 | 0.492 |
| flop | cbet | M | 7979 | 1000 | 0.354 | 0.340 to 0.373 | 0.584 | 0.273 | 0.167 |
| flop | cbet | L | 1027 | 1000 | 0.250 | 0.243 to 0.272 | 0.648 | 0.328 | 0.056 |
| flop | cbet | O | 339 | 339 | 0.276 | 0.223 to 0.307 | 0.641 | 0.431 | 0.079 |
| flop | donk | S | 1376 | 1000 | 0.660 | 0.638 to 0.674 | 0.423 | 0.173 | 0.529 |
| flop | donk | M | 5153 | 1000 | 0.345 | 0.323 to 0.363 | 0.591 | 0.275 | 0.153 |
| flop | donk | L | 721 | 721 | 0.221 | 0.183 to 0.254 | 0.666 | 0.328 | 0.060 |
| flop | donk | O | 356 | 356 | 0.495 | 0.397 to 0.570 | 0.489 | 0.445 | 0.262 |
| flop | stab | S | 418 | 418 | 0.573 | 0.519 to 0.592 | 0.469 | 0.168 | 0.405 |
| flop | stab | M | 3915 | 1000 | 0.448 | 0.425 to 0.456 | 0.540 | 0.272 | 0.199 |
| flop | stab | L | 570 | 570 | 0.274 | 0.246 to 0.301 | 0.628 | 0.328 | 0.059 |
| flop | stab | O | 257 | 257 | 0.384 | 0.343 to 0.450 | 0.563 | 0.463 | 0.188 |
| flop | vs_bet | S | 255 | 255 | 0.186 | 0.132 to 0.206 | 0.698 | 0.171 | 0.077 |
| flop | vs_bet | M | 1343 | 1000 | 0.170 | 0.155 to 0.181 | 0.701 | 0.276 | 0.049 |
| flop | vs_bet | L | 536 | 536 | 0.132 | 0.109 to 0.141 | 0.693 | 0.329 | 0.016 |
| flop | vs_bet | O | 246 | 246 | 0.265 | 0.225 to 0.292 | 0.648 | 0.416 | 0.049 |
| flop | vs_raise | S | 107 | 107 | 0.148 | 0.100 to 0.187 | 0.719 | 0.151 | 0.037 |
| flop | vs_raise | M | 161 | 161 | 0.208 | 0.127 to 0.265 | 0.678 | 0.269 | 0.066 |
| flop | vs_raise | L | 62 | 62 | 0.201 | 0.103 to 0.314 | 0.665 | 0.327 | 0.049 |
| flop | vs_raise | O | 28 | 28 | 0.253 | 0.158 to 0.356 | 0.666 | 0.394 | 0.077 |
| turn | barrel | S | 1269 | 1000 | 0.600 | 0.574 to 0.623 | 0.453 | 0.167 | 0.371 |
| turn | barrel | M | 4753 | 1000 | 0.317 | 0.276 to 0.340 | 0.622 | 0.274 | 0.064 |
| turn | barrel | L | 777 | 777 | 0.234 | 0.216 to 0.254 | 0.665 | 0.329 | 0.058 |
| turn | barrel | O | 245 | 245 | 0.212 | 0.181 to 0.280 | 0.670 | 0.397 | 0.035 |
| turn | donk | S | 206 | 206 | 0.377 | 0.324 to 0.398 | 0.574 | 0.160 | 0.137 |
| turn | donk | M | 938 | 938 | 0.353 | 0.343 to 0.381 | 0.600 | 0.269 | 0.086 |
| turn | donk | L | 99 | 99 | 0.219 | 0.186 to 0.261 | 0.697 | 0.329 | 0.013 |
| turn | donk | O | 53 | 53 | 0.296 | 0.210 to 0.487 | 0.621 | 0.397 | 0.093 |
| turn | stab | S | 369 | 369 | 0.523 | 0.501 to 0.547 | 0.504 | 0.171 | 0.264 |
| turn | stab | M | 2315 | 1000 | 0.349 | 0.336 to 0.365 | 0.599 | 0.273 | 0.142 |
| turn | stab | L | 291 | 291 | 0.286 | 0.240 to 0.337 | 0.652 | 0.328 | 0.108 |
| turn | stab | O | 154 | 154 | 0.268 | 0.189 to 0.304 | 0.636 | 0.428 | 0.109 |
| turn | vs_bet | S | 289 | 289 | 0.157 | 0.119 to 0.188 | 0.734 | 0.146 | 0.033 |
| turn | vs_bet | M | 599 | 599 | 0.185 | 0.158 to 0.200 | 0.707 | 0.268 | 0.031 |
| turn | vs_bet | L | 197 | 197 | 0.155 | 0.109 to 0.181 | 0.715 | 0.327 | 0.027 |
| turn | vs_bet | O | 84 | 84 | 0.283 | 0.216 to 0.344 | 0.662 | 0.398 | 0.035 |
| turn | vs_raise | S | 85 | 85 | 0.209 | 0.136 to 0.272 | 0.696 | 0.123 | 0.046 |
| turn | vs_raise | M | 83 | 83 | 0.227 | 0.140 to 0.253 | 0.694 | 0.268 | 0.073 |
| turn | vs_raise | L | 21 | 21 | 0.253 | 0.163 to 0.392 | 0.669 | 0.328 | 0.049 |
| river | barrel | S | 987 | 987 | 0.493 | 0.458 to 0.521 | 0.505 | 0.147 | 0.194 |
| river | barrel | M | 2312 | 1000 | 0.271 | 0.239 to 0.293 | 0.648 | 0.272 | 0.037 |
| river | barrel | L | 433 | 433 | 0.220 | 0.182 to 0.261 | 0.674 | 0.327 | 0.029 |
| river | barrel | O | 221 | 221 | 0.319 | 0.265 to 0.344 | 0.629 | 0.415 | 0.044 |
| river | donk | S | 132 | 132 | 0.336 | 0.273 to 0.392 | 0.618 | 0.147 | 0.047 |
| river | donk | M | 339 | 339 | 0.409 | 0.381 to 0.446 | 0.567 | 0.268 | 0.113 |
| river | donk | L | 55 | 55 | 0.319 | 0.295 to 0.464 | 0.645 | 0.327 | 0.058 |
| river | donk | O | 27 | 27 | 0.415 | 0.237 to 0.495 | 0.574 | 0.391 | 0.141 |
| river | stab | S | 303 | 303 | 0.604 | 0.564 to 0.652 | 0.439 | 0.166 | 0.290 |
| river | stab | M | 1502 | 1000 | 0.387 | 0.347 to 0.408 | 0.586 | 0.273 | 0.120 |
| river | stab | L | 253 | 253 | 0.248 | 0.182 to 0.300 | 0.679 | 0.329 | 0.064 |
| river | stab | O | 205 | 205 | 0.390 | 0.318 to 0.437 | 0.590 | 0.428 | 0.072 |
| river | vs_bet | S | 157 | 157 | 0.213 | 0.174 to 0.253 | 0.711 | 0.124 | 0.035 |
| river | vs_bet | M | 205 | 205 | 0.288 | 0.240 to 0.317 | 0.661 | 0.269 | 0.026 |
| river | vs_bet | L | 56 | 56 | 0.188 | 0.173 to 0.337 | 0.760 | 0.327 | 0.028 |
| river | vs_bet | O | 21 | 21 | 0.425 | 0.170 to 0.602 | 0.590 | 0.404 | 0.093 |
| river | vs_raise | S | 45 | 45 | 0.222 | 0.082 to 0.273 | 0.710 | 0.123 | 0.022 |
| river | vs_raise | M | 26 | 26 | 0.192 | 0.054 to 0.409 | 0.778 | 0.278 | 0.000 |
