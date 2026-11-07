"""EM over each opponent's one hidden retained card, for the Bay Area three-card variant."""
from dataclasses import dataclass

import numpy as np

from .cards import N_BUCKETS, BoardView, bucket

RANK_GROUP = (0,) * 6 + (1,) * 4 + (2,) * 3
HIDDEN_HIGHER, HIDDEN_LOWER, HIDDEN_SAME_RANK = range(3)
SELECTION_CELLS_PER_LINE = N_BUCKETS * 3 * 3


@dataclass(frozen=True)
class Observation:
    line: int
    exposed: int
    board: tuple
    blocked: frozenset
    decisions: tuple
    hidden: int | None


@dataclass
class Model:
    policy: np.ndarray
    selection: np.ndarray
    iterations: int = 0
    log_likelihood: float = 0.0


def selection_cell(line, flop_bucket, exposed, hidden):
    if hidden >> 2 > exposed >> 2:
        order = HIDDEN_HIGHER
    elif hidden >> 2 < exposed >> 2:
        order = HIDDEN_LOWER
    else:
        order = HIDDEN_SAME_RANK
    return ((line * N_BUCKETS + flop_bucket) * 3 + order) * 3 + RANK_GROUP[hidden >> 2]


def candidates_for(exposed, board, blocked):
    excluded = set(board) | {exposed} | set(blocked)
    return [card for card in range(52) if card not in excluded]


@dataclass
class Arrays:
    starts: np.ndarray
    row_instance: np.ndarray
    row_cell: np.ndarray
    row_allowed: np.ndarray
    dec_row: np.ndarray
    dec_node: np.ndarray
    dec_bucket: np.ndarray
    dec_action: np.ndarray
    dec_group: np.ndarray
    groups: list


def build(observations):
    starts, instance, cells, allowed = [], [], [], []
    dec_row, dec_node, dec_bucket, dec_action, dec_group, groups = [], [], [], [], [], []
    row = 0
    for index, obs in enumerate(observations):
        candidates = candidates_for(obs.exposed, obs.board, obs.blocked)
        n = len(candidates)
        flop_view = BoardView(obs.board[:3])
        flop_buckets = [bucket(obs.exposed, h, flop_view) for h in candidates]
        starts.append(row)
        instance.append(np.full(n, index, np.int32))
        cells.append(np.array([selection_cell(obs.line, b, obs.exposed, h)
                               for b, h in zip(flop_buckets, candidates)], np.int32))
        streets = {street for _, _, street in obs.decisions}
        views = {street: BoardView(obs.board[:3 + street]) for street in streets if street}
        if obs.hidden is not None:
            known = candidates.index(obs.hidden)
            mask = np.zeros(n, bool)
            mask[known] = True
            allowed.append(mask)
            for position, (node, action, street) in enumerate(obs.decisions):
                strength = flop_buckets[known] if street == 0 else bucket(obs.exposed, obs.hidden, views[street])
                dec_group.append(np.array([len(groups)], np.int32))
                groups.append((index, position))
                dec_row.append(np.array([row + known], np.int32))
                dec_node.append(np.array([node], np.int16))
                dec_bucket.append(np.array([strength], np.int8))
                dec_action.append(np.array([action], np.int8))
        else:
            allowed.append(np.ones(n, bool))
            per_street = {0: np.array(flop_buckets, np.int8)}
            for street, view in views.items():
                per_street[street] = np.array([bucket(obs.exposed, h, view) for h in candidates], np.int8)
            rows = np.arange(row, row + n, dtype=np.int32)
            for position, (node, action, street) in enumerate(obs.decisions):
                dec_group.append(np.full(n, len(groups), np.int32))
                groups.append((index, position))
                dec_row.append(rows)
                dec_node.append(np.full(n, node, np.int16))
                dec_bucket.append(per_street[street])
                dec_action.append(np.full(n, action, np.int8))
        row += n
    return Arrays(np.array(starts), np.concatenate(instance), np.concatenate(cells),
                  np.concatenate(allowed), np.concatenate(dec_row), np.concatenate(dec_node),
                  np.concatenate(dec_bucket), np.concatenate(dec_action), np.concatenate(dec_group), groups)


def _segment_logsumexp(values, arrays):
    peak = np.maximum.reduceat(values, arrays.starts)
    peak = np.where(np.isfinite(peak), peak, 0.0)
    total = np.add.reduceat(np.exp(values - peak[arrays.row_instance]), arrays.starts)
    return np.log(total) + peak


def flat_model(n_nodes, n_actions, n_lines, legal=None):
    if legal is None:
        legal = np.ones((n_nodes, n_actions), bool)
    policy = np.repeat((legal / legal.sum(1, keepdims=True))[:, None, :], N_BUCKETS, axis=1)
    return Model(policy, np.ones(n_lines * SELECTION_CELLS_PER_LINE))


def fit(arrays, n_nodes, n_actions, n_lines, iterations=400, tolerance=1e-7, smoothing=0.5):
    legal = np.zeros((n_nodes, n_actions), bool)
    legal[arrays.dec_node, arrays.dec_action] = True
    legal[~legal.any(1)] = True
    model = flat_model(n_nodes, n_actions, n_lines, legal)
    n_cells = len(model.selection)
    flat_decision = (arrays.dec_node.astype(np.int64) * N_BUCKETS + arrays.dec_bucket) * n_actions + arrays.dec_action
    previous = None
    for iteration in range(1, iterations + 1):
        log_selection = np.log(model.selection)[arrays.row_cell]
        with np.errstate(divide="ignore"):
            log_policy = np.log(model.policy)
        log_likelihood = np.bincount(arrays.dec_row, weights=log_policy[arrays.dec_node, arrays.dec_bucket, arrays.dec_action],
                                     minlength=len(arrays.row_cell))
        joint = np.where(arrays.row_allowed, log_selection + log_likelihood, -np.inf)
        joint_norm = _segment_logsumexp(joint, arrays)
        prior_norm = _segment_logsumexp(log_selection, arrays)
        total = float(np.sum(joint_norm - prior_norm))
        posterior = np.exp(joint - joint_norm[arrays.row_instance])
        prior = np.exp(log_selection - prior_norm[arrays.row_instance])

        counts = np.bincount(flat_decision, weights=posterior[arrays.dec_row],
                             minlength=n_nodes * N_BUCKETS * n_actions).reshape(n_nodes, N_BUCKETS, n_actions)
        counts = (counts + smoothing) * legal[:, None, :]
        policy = counts / counts.sum(2, keepdims=True)
        observed = np.bincount(arrays.row_cell, weights=posterior, minlength=n_cells)
        expected = np.bincount(arrays.row_cell, weights=prior, minlength=n_cells)
        selection = model.selection * (observed + 0.5) / (expected + 0.5)
        model = Model(policy, selection / selection.mean(), iteration, total)
        if previous is not None and total - previous < tolerance * abs(total):
            break
        previous = total
    return model


def decision_bucket_mix(model, arrays):
    """Posterior hand-bucket mix at every recorded decision, using each player's whole line."""
    log_selection = np.log(model.selection)[arrays.row_cell]
    with np.errstate(divide="ignore"):
        log_policy = np.log(model.policy)
    log_likelihood = np.bincount(arrays.dec_row, weights=log_policy[arrays.dec_node, arrays.dec_bucket, arrays.dec_action],
                                 minlength=len(arrays.row_cell))
    joint = np.where(arrays.row_allowed, log_selection + log_likelihood, -np.inf)
    posterior = np.exp(joint - _segment_logsumexp(joint, arrays)[arrays.row_instance])
    flat = arrays.dec_group.astype(np.int64) * N_BUCKETS + arrays.dec_bucket
    return np.bincount(flat, weights=posterior[arrays.dec_row],
                       minlength=len(arrays.groups) * N_BUCKETS).reshape(len(arrays.groups), N_BUCKETS)


def hidden_card_posterior(model, line, exposed, flop, blocked, decisions):
    """P(hidden card) for one opponent given its exposed card and its postflop actions so far."""
    candidates = candidates_for(exposed, flop, blocked)
    view = BoardView(flop)
    buckets = np.array([bucket(exposed, h, view) for h in candidates])
    logp = np.log(model.selection[[selection_cell(line, b, exposed, h) for b, h in zip(buckets, candidates)]])
    for node, action in decisions:
        logp = logp + np.log(model.policy[node, buckets, action])
    weights = np.exp(logp - logp.max())
    return candidates, buckets, weights / weights.sum()
