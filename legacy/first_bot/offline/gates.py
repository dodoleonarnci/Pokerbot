#!/usr/bin/env python3
"""The spec's Testing gates, as far as they can run without the kit. A failure exits non-zero.

Legal cannot run yet: it needs `poker-agent check` from the kit. Everything else uses the
practice simulator, so these results are provisional until the kit's simulator replaces it.
"""
import json
import pathlib
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "sim"), str(ROOT.parent / "practice")]

LIMIT = 0.001
TABLES_ERRORS = int(sys.argv[1]) if len(sys.argv) > 1 else 200
TABLES_STRENGTH = int(sys.argv[2]) if len(sys.argv) > 2 else 500
TABLES_EXPLOIT = int(sys.argv[3]) if len(sys.argv) > 3 else 2000

WORKER = """
import json, random, statistics, sys
sys.path[:0] = ['.', 'sim', '../practice']
import agent
from runner import play
kind, tables, seed, field = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
limit = 0.001
if kind == 'new':
    make = lambda s: agent.Agent(seed=s, use_pool=False)
elif kind == 'exploit_on':
    make = lambda s: agent.Agent(seed=s, use_pool=False, use_exploits=True)
elif kind == 'exploit_off':
    make = lambda s: agent.Agent(seed=s, use_pool=False, use_exploits=False)
elif kind == 'previous':  # the previous build as it would really run, at the 1 ms limit
    import range_bot
    make = lambda s: range_bot.RangeBot()
elif kind == 'previous_unlimited':  # for information: this build could not meet 1 ms
    import range_bot
    make = lambda s: range_bot.RangeBot()
    limit = None
print(json.dumps(play(tables, field, seed, make_hero=make, limit=limit)))
"""


def start(kind, tables, seed, field):
    return subprocess.Popen([sys.executable, "-c", WORKER, kind, str(tables), str(seed), field],
                            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def finish(process):
    out, err = process.communicate()
    if process.returncode:
        raise RuntimeError(err)
    return json.loads(out.strip().splitlines()[-1])


def pair(kind_a, kind_b, tables, field):
    a, b = start(kind_a, tables, 21, field), start(kind_b, tables, 21, field)
    return finish(a), finish(b)


def beats(a, b):
    diff = a["points"] - b["points"]
    err = (a["stderr"] ** 2 + b["stderr"] ** 2) ** 0.5
    return diff, err, diff > 2 * err


results = []


def report(name, passed, detail):
    results.append((name, passed))
    word = {True: "PASS", False: "FAIL", None: "NOT RUN"}[passed]
    print(f"{word:8} {name:13} {detail}", flush=True)


def main():
    report("Legal", None, "needs `poker-agent check agent.py` from the kit")

    run = finish(start("new", TABLES_ERRORS, 21, "mixed"))
    report("Errors", run["errors"] == 0 and run["timeouts"] == 0 and run["failures"] == 0,
           f"{run['tables']} tables: {run['errors']} errors, {run['timeouts']} timeouts, "
           f"{run['failures']} illegal actions, {run['decisions']} decisions")
    report("Speed", run["avg_ms"] < 0.1 and run["p99_ms"] < 0.3 and run["max_ms"] < 0.5,
           f"average {run['avg_ms']:.3f} ms, p99 {run['p99_ms']:.3f} ms, max {run['max_ms']:.3f} ms, "
           f"{100 * run['under_1ms']:.2f}% under 1 ms")

    subprocess.run([sys.executable, "offline/pipeline.py", "ship"], cwd=ROOT, check=True, capture_output=True)
    target = ROOT / "dist" / "bot.zip"
    with zipfile.ZipFile(target) as z:
        infos = z.infolist()
    zipped = target.stat().st_size / 1e6
    unpacked = sum(i.file_size for i in infos) / 1e6
    agent_kb = (ROOT / "agent.py").stat().st_size / 1e3
    report("Size", zipped < 50 and unpacked < 200 and len(infos) < 1000 and agent_kb < 1000,
           f"{zipped:.2f} MB zipped, {unpacked:.2f} MB unpacked, {len(infos)} entries, agent.py {agent_kb:.1f} KB")

    on, off = pair("exploit_on", "exploit_off", TABLES_EXPLOIT, "tight")
    diff, err, ok = beats(on, off)
    report("Exploit check", ok, f"on {on['points']:.2f}, off {off['points']:.2f}, "
           f"difference {diff:+.2f} +/- {err:.2f} over {on['tables']} tables vs tight bots")

    new, previous = pair("new", "previous", TABLES_STRENGTH, "mixed")
    diff, err, ok = beats(new, previous)
    report("Strength", ok, f"this build {new['points']:.2f}, previous (range_bot) {previous['points']:.2f}, "
           f"difference {diff:+.2f} +/- {err:.2f} over {new['tables']} tables")

    unlimited = finish(start("previous_unlimited", TABLES_STRENGTH, 21, "mixed"))
    diff, err, _ = beats(new, unlimited)
    print(f"INFO     Strength      previous with no time limit (not legal in the tournament): "
          f"{unlimited['points']:.2f}, difference {diff:+.2f} +/- {err:.2f}", flush=True)

    print()
    for field in ("allin", "checkers", "switchers", "examples"):
        s = finish(start("new", 40, 7, field))
        print(f"stress {field:10} {s['points']:6.1f} pts, errors {s['errors']}, timeouts {s['timeouts']}, "
              f"illegal {s['failures']}, max {s['max_ms']:.3f} ms")
    edge = subprocess.run([sys.executable, "-c", """
import random,sys
sys.path[:0]=['.','sim','../practice']
import agent
from field_bots import FIELD
from tournament import run_table
errors=0
for name,bots,start in (('2-player endgame',2,2000),('stack under 1 BB',8,15)):
    for seed in range(40):
        rng=random.Random(seed)
        heroes=[agent.Agent(seed=seed,use_pool=False)]
        seats=heroes+[FIELD['tag'](seed+i) for i in range(bots-1)]
        result=run_table(seats,rng,starting=start)
        errors+=heroes[0].errors+result['failures'][0]
    print('stress',name,'errors',errors)
"""], cwd=ROOT, capture_output=True, text=True)
    print(edge.stdout.strip() or edge.stderr[-500:])

    failed = [name for name, passed in results if passed is False]
    print("\nFailed:", ", ".join(failed) if failed else "none")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
