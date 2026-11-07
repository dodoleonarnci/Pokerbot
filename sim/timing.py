import random, sys, time
sys.path.insert(0, sys.argv[1])
import agent as A
from poker_agent_sdk import GameState
from poker_agent_protocol.game import Seat, TableConfig, BlindLevel, LegalAction, Event
cfg = TableConfig("t", 0, 8, "flop_discard_reveal", 2000, (BlindLevel(10, 20),), 20, 250, (50, 30, 20), 1, 65536, 100)
def make(phase, ncards, nboard, raise_allin=False):
    deck = A.DECK[:]; random.shuffle(deck)
    cards = tuple(deck[:ncards]); board = tuple(deck[ncards:ncards + nboard])
    seats = tuple(Seat(i, 1500 + 100 * i, 0, "active") for i in range(8))
    hist = (Event("blind", 1, 10), Event("blind", 2, 20))
    legal = (LegalAction("fold"), LegalAction("call"), LegalAction("raise", 40, 1500))
    to_call = 20
    if raise_allin:
        seats = seats[:4] + (Seat(4, 0, 1900, "all_in"),) + seats[5:]
        hist = hist + (Event("raise", 4, 1900),); to_call = 1500
        legal = (LegalAction("fold"), LegalAction("call"))
    if phase == "select":
        legal = (LegalAction("select"),); to_call = 0
    return GameState(events=(), hand_number=5, seat=0, cards=cards, board=board, pot=230, to_call=to_call,
        legal_actions=legal, history=hist, seats=seats, button=5, blind_level=0, blinds=BlindLevel(10, 20),
        hands_until_next_level=5, players_remaining=8, bust_order=(), config=cfg, phase=phase, time_bank_ms=100)
agent = A.Agent()
for name, args in [("select", ("select", 3, 3)), ("pre", ("betting", 3, 0)), ("pre_allin_icm", ("betting", 3, 0, True)),
                   ("flop", ("betting", 2, 3)), ("river", ("betting", 2, 5))]:
    states = [make(*args) for _ in range(400)]
    times = []
    for s in states:
        t = time.perf_counter_ns(); agent.act(s, b""); times.append((time.perf_counter_ns() - t) / 1000)
    times.sort(); n = len(times)
    print(f"{name:14s} p50 {times[n//2]:6.0f}us  p99 {times[int(n*.99)]:6.0f}us  max {times[-1]:6.0f}us")
