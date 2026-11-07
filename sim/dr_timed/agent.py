import importlib.util, os, time
spec = importlib.util.spec_from_file_location("dr_agent", os.path.expanduser("~/work/bots/dr_bot/agent.py"))
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
LOG = open(os.path.expanduser("~/work/sim/dr_timed/times.log"), "a", buffering=1)
class Agent(mod.Agent):
    def act(self, state, memory):
        t = time.perf_counter_ns()
        out = super().act(state, memory)
        kind = state.phase if state.phase != "betting" else ("pre" if not state.board else "post")
        LOG.write(f"{kind} {(time.perf_counter_ns()-t)/1000:.0f} {len(out[1])}\n")
        return out
