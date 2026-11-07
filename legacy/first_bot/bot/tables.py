"""M4: load precomputed tables at import. Falls back to a heuristic if they are missing."""
import json
import os
import pathlib
from array import array

from .evaluator import CLASS_COMBOS, CLASSES, RANK_PAIRS, board_keys, class_of

DATA = pathlib.Path(os.environ.get("FIRST_BOT_DATA", pathlib.Path(__file__).resolve().parent.parent / "data"))
N = len(CLASSES)


def _load_array(name, code):
    values = array(code)
    values.frombytes((DATA / name).read_bytes())
    return values


def _heuristic_strength(index):
    """Rough 0-1 hand strength, used only while the table jobs are still running."""
    high, low, kind = CLASSES[index]
    if kind == 0:
        return 0.55 + low * 0.035
    value = (high * 0.6 + low * 0.3) / 12 * 0.6
    value += 0.04 if kind == 1 else 0.0
    value += max(0, 3 - (high - low)) * 0.012
    return value


class Tables:
    def __init__(self):
        self.ready = False
        self.board_offset = {key: i * RANK_PAIRS for i, key in enumerate(board_keys())}
        try:
            self.rank_table = _load_array("rank_table.bin", "i")
            self.matrix = _load_array("class_matrix.bin", "f")
            self.versus_top_flat = _load_array("versus_top.bin", "f")
            with open(DATA / "preflop.json") as f:
                meta = json.load(f)
            with open(DATA / "postflop_keys.json") as f:
                self.postflop = json.load(f)
            self.order = meta["order"]
            self.field = meta["field"]
            self.ready = True
        except (OSError, ValueError, KeyError):
            self.rank_table = None
            self.order = sorted(range(N), key=_heuristic_strength, reverse=True)
            self.field = None
            self.postflop = {}

        self.percentile = [0.0] * N  # lower is stronger; the cumulative % of combos
        combos = 0
        for index in self.order:
            combos += CLASS_COMBOS[index]
            self.percentile[index] = 100 * combos / 1326
        # top[p] is the list of classes in the top p% of combos.
        self.top = [[] for _ in range(101)]
        for percent in range(1, 101):
            self.top[percent] = [i for i in self.order if self.percentile[i] <= percent]
            if not self.top[percent]:
                self.top[percent] = [self.order[0]]
        self.top[0] = self.top[1]

    def percentile_of(self, a, b):
        return self.percentile[class_of(a, b)]

    def versus_top(self, index, percent):
        """Equity of a class against the top percent% of hands."""
        percent = max(1, min(100, int(percent + 0.5)))
        if self.ready:
            return self.versus_top_flat[index * 100 + percent - 1]
        return min(0.85, 0.35 + _heuristic_strength(index) * 0.5 + (percent / 100) * 0.1)

    def field_equity(self, index, opponents):
        if self.field:
            return self.field[index][max(1, min(7, opponents)) - 1]
        return _heuristic_strength(index)

    def row_offset(self, board):
        return self.board_offset[tuple(sorted(c >> 2 for c in board))]


TABLES = Tables()
