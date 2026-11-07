"""Monte Carlo equity of each retained-hand bucket against each other bucket, by street."""
import random

import numpy as np

from .cards import N_BUCKETS, BoardView, bucket, evaluate

STREET_BOARD = {"flop": 3, "turn": 4, "river": 5}


def bucket_equity(samples=150000, seed=3):
    rng = random.Random(seed)
    tables = {}
    for street, seen in STREET_BOARD.items():
        wins = np.zeros((N_BUCKETS, N_BUCKETS))
        games = np.zeros((N_BUCKETS, N_BUCKETS))
        for _ in range(samples):
            cards = rng.sample(range(52), 9)
            ours, theirs, board = cards[0:2], cards[2:4], cards[4:9]
            view = BoardView(board[:seen])
            a, b = bucket(ours[0], ours[1], view), bucket(theirs[0], theirs[1], view)
            mine, other = evaluate(ours + board), evaluate(theirs + board)
            result = 1.0 if mine > other else 0.5 if mine == other else 0.0
            wins[a, b] += result
            games[a, b] += 1
            wins[b, a] += 1.0 - result
            games[b, a] += 1
        equity = np.round(wins / np.maximum(games, 1), 3)
        tables[street] = {"equity": [[float(e) if g else None for e, g in zip(er, gr)] for er, gr in zip(equity, games)],
                          "samples": games.astype(int).tolist()}
    return tables
