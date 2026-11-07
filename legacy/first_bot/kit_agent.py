"""Upload entry point for the official kit: packed as agent.py once the SDK is available.

Before the kit exists the SDK import fails, and sim/kit_harness.py supplies a stand-in Action.
"""
import gc
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from bot import kit  # noqa: E402

try:
    from poker_agent_sdk import Action
    from poker_agent_sdk import Agent as KitAgent
except ImportError:
    Action, KitAgent = None, object

gc.collect()
gc.freeze()
gc.disable()  # garbage collection must never run mid-decision


class Agent(KitAgent):
    action_type = Action

    def act(self, state, memory):
        return kit.play(state, memory, self.action_type)
