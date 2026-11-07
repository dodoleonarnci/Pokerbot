"""Fit EM on synthetic Bay Area hands and score it against the known truth."""
import argparse
import time

import numpy as np

from . import em
from .cards import BUCKET_NAMES, N_BUCKETS, BoardView, bucket, evaluate
from .world import (A_OPEN, BET_BIG, BET_SIZE, BET_SMALL, CALLER, N_ACTIONS, N_LINES, N_NODES,
                    RAISER, WORLDS, BayAreaWorld, node_id, observations)

BAND = (0.15, 0.40)
CALIBRATION_EDGES = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0001)


def generate(count, seed, policy):
    world = BayAreaWorld(seed, policy=policy)
    return [world.hand() for _ in range(count)]


def raiser_flop_bucket(hand):
    seat = hand.seats[RAISER]
    return bucket(seat.exposed, seat.hidden, BoardView(hand.board[:3]))


def flop_bets(hands):
    for hand in hands:
        role, node, action, street = hand.events[0]
        if action in (BET_SMALL, BET_BIG):
            yield hand, node, action


def mix(values, weights=None):
    counts = np.bincount(values, weights=weights, minlength=N_BUCKETS)
    return counts / counts.sum()


def row(label, values, width=9, fmt="{:.2f}"):
    return f"  {label:<24}" + "".join(f"{fmt.format(v):>{width}}" for v in values)


def selection_bias(train):
    everything = [raiser_flop_bucket(h) for h, _, _ in flop_bets(train)]
    shown = [raiser_flop_bucket(h) for h, _, _ in flop_bets(train) if h.showdown]
    print("\nRaiser's flop bets, true hand mix (training data)")
    print(row("", BUCKET_NAMES, 12, "{}"))
    print(row(f"all bets (n={len(everything)})", mix(everything), 12))
    print(row(f"shown later (n={len(shown)})", mix(shown), 12))


def fit_all(train):
    models = {}
    for name, visibility in (("full visibility", "full"), ("EM", "realistic"), ("showdown only", "showdown")):
        started = time.perf_counter()
        arrays = em.build(list(observations(train, visibility)))
        built = time.perf_counter()
        model = em.fit(arrays, N_NODES, N_ACTIONS, N_LINES)
        print(f"  {name:<16} rows {len(arrays.row_cell):>9,}  build {built - started:5.1f}s  "
              f"fit {time.perf_counter() - built:5.1f}s  iterations {model.iterations}")
        models[name] = model
    models["no betting model"] = em.flat_model(N_NODES, N_ACTIONS, N_LINES)
    return models


def policy_recovery(train, models, true_policy):
    visits = np.zeros((N_NODES, N_BUCKETS))
    for hand in train:
        for role, node, action, street in hand.events:
            seat = hand.seats[role]
            visits[node, bucket(seat.exposed, seat.hidden, BoardView(hand.board[:3 + street]))] += 1
    flop_open = node_id(0, A_OPEN)
    print("\nRaiser's flop bet rate by true hand bucket (P(bet small or big))")
    print(row("", BUCKET_NAMES, 12, "{}"))
    print(row("truth", 1 - true_policy[flop_open, :, 0], 12))
    for name in ("full visibility", "EM", "showdown only"):
        print(row(name, 1 - models[name].policy[flop_open, :, 0], 12))
    print("\nMean absolute error of every action probability, weighted by how often the spot occurs")
    weights = visits / visits.sum()
    for name in ("full visibility", "EM", "showdown only"):
        error = np.abs(models[name].policy - true_policy).sum(2) / 2
        print(f"  {name:<24}{float((error * weights).sum()):.4f}")


def score_flop_bets(test, models):
    names = list(models)
    results = {name: {"p_value": [], "mix": {BET_SMALL: [], BET_BIG: []}} for name in names}
    labels, sizes, truth_buckets = [], [], []
    elapsed = []
    for hand, node, action in flop_bets(test):
        raiser, caller = hand.seats[RAISER], hand.seats[CALLER]
        flop = hand.board[:3]
        caller_score = evaluate([caller.exposed, caller.hidden, *flop])
        raiser_score = evaluate([raiser.exposed, raiser.hidden, *flop])
        labels.append(1.0 if raiser_score > caller_score else 0.5 if raiser_score == caller_score else 0.0)
        sizes.append(action)
        truth_buckets.append(raiser_flop_bucket(hand))
        blocked = set(caller.dealt)
        candidate_scores = None
        for name in names:
            started = time.perf_counter()
            candidates, buckets, p = em.hidden_card_posterior(
                models[name], RAISER, raiser.exposed, flop, blocked, [(node, action)])
            elapsed.append(time.perf_counter() - started)
            if candidate_scores is None:
                candidate_scores = np.array([evaluate([raiser.exposed, h, *flop]) for h in candidates])
            p_value = p[candidate_scores > caller_score].sum() + 0.5 * p[candidate_scores == caller_score].sum()
            results[name]["p_value"].append(p_value)
            results[name]["mix"][action].append(np.bincount(buckets, weights=p, minlength=N_BUCKETS))
    labels, sizes, truth_buckets = np.array(labels), np.array(sizes), np.array(truth_buckets)
    print(f"\nTest set: {len(labels):,} raiser flop bets faced by the caller")
    print(f"  hidden-card posterior: median {np.median(elapsed) * 1e6:.0f} us, "
          f"p99 {np.percentile(elapsed, 99) * 1e6:.0f} us per call on this machine")

    for size, label in ((BET_SMALL, "1/3-pot"), (BET_BIG, "pot-sized")):
        print(f"\nHand mix behind a {label} flop bet (test set, average prediction vs truth)")
        print(row("", BUCKET_NAMES, 12, "{}"))
        print(row("truth", mix(truth_buckets[sizes == size]), 12))
        for name in names:
            print(row(name, np.mean(results[name]["mix"][size], axis=0), 12))

    bluff = 1 - labels
    z = np.array([BET_SIZE[s] for s in sizes])
    threshold = z / (1 + 2 * z)
    call_value = bluff * (1 + z) - (1 - bluff) * z
    print("\nBinary bluff estimator: is the bettor behind the caller's hand on the flop?")
    print(f"  {'':<24}{'log loss':>10}{'Brier':>9}{'band n':>9}{'band pred':>11}{'band true':>11}{'EV/spot':>10}")
    for name in names:
        p_bluff = np.clip(1 - np.array(results[name]["p_value"]), 1e-6, 1 - 1e-6)
        log_loss = -np.mean(bluff * np.log(p_bluff) + (1 - bluff) * np.log(1 - p_bluff))
        brier = np.mean((p_bluff - bluff) ** 2)
        band = (p_bluff >= BAND[0]) & (p_bluff <= BAND[1])
        ev = np.mean(np.where(p_bluff > threshold, call_value, 0.0))
        print(f"  {name:<24}{log_loss:>10.4f}{brier:>9.4f}{band.sum():>9}{p_bluff[band].mean():>11.3f}"
              f"{bluff[band].mean():>11.3f}{ev:>10.4f}")
    print(f"  {'perfect information':<24}{'':>39}{np.mean(np.maximum(call_value, 0)):>10.4f}")
    print(f"  {'always call':<24}{'':>39}{np.mean(call_value):>10.4f}")

    for name in ("EM", "showdown only"):
        p_bluff = 1 - np.array(results[name]["p_value"])
        print(f"\nCalibration, {name}: predicted vs actual bluff rate")
        for lo, hi in zip(CALIBRATION_EDGES, CALIBRATION_EDGES[1:]):
            inside = (p_bluff >= lo) & (p_bluff < hi)
            if inside.sum():
                print(f"  {lo:.1f}-{min(hi, 1):.1f}  n={inside.sum():>6}  predicted {p_bluff[inside].mean():.3f}  "
                      f"actual {bluff[inside].mean():.3f}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type=int, default=40000)
    parser.add_argument("--test", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--world", choices=sorted(WORLDS), default="base")
    args = parser.parse_args()
    started = time.perf_counter()
    policy = WORLDS[args.world]
    train, test = generate(args.train, args.seed, policy), generate(args.test, args.seed + 1000, policy)
    print(f"World {args.world!r}: generated {args.train:,} training and {args.test:,} test hands in {time.perf_counter() - started:.1f}s; "
          f"{np.mean([h.showdown for h in train]):.0%} reach showdown")
    selection_bias(train)
    print("\nFitting")
    models = fit_all(train)
    policy_recovery(train, models, policy)
    score_flop_bets(test, models)


if __name__ == "__main__":
    main()
