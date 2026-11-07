"""M1: safety shell and the bot's entry point.

Provisional entry point: the kit's interface may need a different name or return format.
Any error or slow path returns a legal action, so a bug can only cost a check or a fold.
"""
import gc
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from bot.params import PARAMS  # noqa: E402
from bot.policy import Policy  # noqa: E402
from bot.view import make_view  # noqa: E402

gc.collect()
gc.freeze()
gc.disable()  # garbage collection must never run mid-decision


def legal_action(state, action):
    """Clamp any action into the legal set ourselves; never rely on the engine."""
    kind = action[0]
    free = state["to_call"] == 0
    if kind == "raise":
        if not state["can_raise"]:
            return "check" if free else "call"
        target = max(state["min_raise_to"], min(int(action[1]), state["max_raise_to"]))
        return ("raise", target)
    if kind == "call":
        return "check" if free else "call"
    if kind == "check":
        return "check" if free else "fold"
    return "check" if free else "fold"


class Agent:
    def __init__(self, seed=None, use_pool=True, use_exploits=True, probe_rate=0.0):
        self.policy = Policy(seed, use_pool, use_exploits, probe_rate)
        self.errors = 0
        self.last_error = None

    def __call__(self, state):
        start = time.perf_counter()
        try:
            view = make_view(state)
            action = self.policy.decide(view, start + PARAMS["SLOW_PATH_S"])
            return legal_action(state, action)
        except Exception as error:  # any bug falls back to check or fold
            self.errors += 1
            self.last_error = repr(error)
            return "check" if state.get("to_call", 1) == 0 else "fold"


act = Agent()
