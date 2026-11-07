"""Every strategy number lives here, so tuning never touches logic.

Names follow the spec's PARAMS table. Anything marked ASSUMED is not in the spec,
or depends on the kit, and should be replaced once the kit is available.
"""

PARAMS = {
    # Preflop (S2)
    "OPEN_PCT": {"UTG": 12, "UTG+1": 14, "MP": 17, "LJ": 20, "HJ": 25, "CO": 30,
                 "BTN": 45, "SB": 40,
                 "BB": 20, "HU_BTN": 70, "HU_BB": 30},  # BB and HU values are ASSUMED
    "OPEN_BB": 2.5,
    "THREEBET_IP": 3.0,
    "THREEBET_OOP": 3.5,
    "FOURBET_JAM_BB": 40,
    "FOURBET_X": 2.3,  # ASSUMED: 4-bet size when deeper than FOURBET_JAM_BB
    "PRE_CALL_MARGIN_IP": 0.04,
    "PRE_CALL_MARGIN_OOP": 0.08,
    "MULTIWAY_TIGHTEN": 0.03,
    "JAM_BB": 15,
    # Assumed preflop ranges for opponents' other actions. ASSUMED until Table C exists.
    "THEIR_3BET_PCT": 8,
    "THEIR_4BET_PCT": 3,
    "THEIR_JAM_PCT": 2,
    "THEIR_CALL_PCT": 15,
    "THEIR_LIMP_PCT": 35,
    # Sizes (S4)
    "FLOP_SIZE": 0.33,
    "F_MAX": 1.25,
    "F_MIN": 0.25,
    "RAISE_X": 3.0,
    "RAISE_JAM_SPR": 1.5,
    # Value and bluffs (S6, S7)
    "VALUE_EQ": {"flop": 0.50, "turn": 0.55, "river": 0.50},
    "RAISE_VALUE_EQ": 0.50,
    "DRAW_OUTS": 8,
    "DRAW_SHARE": 0.15,
    "MULTIWAY_BLUFF": {2: 1.0, 3: 0.5},  # bluff multiplier by players in the pot; 0 beyond
    # ICM (S8, M6)
    "RISK_STACK_FRAC": 0.30,
    "RISK_MAX": 0.10,  # ASSUMED: largest equity penalty added to a threshold
    # Exploits (S10)
    "K": 12,
    "DECAY": 0.98,
    "MAX_SHIFT": 0.15,
    "MAX_BLUFF_MULT": 2.0,
    "LOSS_BUDGET": 400,
    "SEAT_MIN_HANDS": 25,
    "K_POOL": 200,
    "MIN_SAMPLES": 100,
    "BLUFF_MARGIN": 0.05,
    "SIZES": (0.33, 0.5, 0.75, 1.0, 1.5, "all-in"),
    # Exploration (M8)
    "EXPLORE": 0.0,  # the scored bot may use up to 0.03
    "PROBE_RATE": 0.20,  # practice probe builds only
    # Safety shell (M1)
    "SLOW_PATH_S": 0.0006,  # practice agent.py only; the kit path uses DECISION_BUDGET_S
    # Layered engine (bot/kit.py)
    "DECISION_BUDGET_S": 0.0004,
    # Rules layer (bot/rules.py): enable flags, then shared thresholds
    "RULES": {"steal_vs_folders": True, "versus_maniac": True},
    "RULE_MIN_SAMPLE": 6,
    "RULE_PRIOR_FOLDS": 1.0,  # Beta prior: one fold in two trials
    "RULE_PRIOR_TRIALS": 2.0,
    "STEAL_FOLD_RATE": 0.85,
    "MANIAC_RAISE_RATE": 0.70,
    "MANIAC_SHOVE_EQUITY": 0.62,
    "MANIAC_CALL_MARGIN": 0.02,
    "RULE_EQUITY_S": 0.00025,
    # Generic engine (bot/generic.py), for variants the hold'em policy cannot play
    "GENERIC_SAMPLES": 120,
    "GENERIC_SHOVE_BB": 12,
    "GENERIC_SHOVE_EDGE": 0.08,
    "GENERIC_RAISE_EDGE": 0.30,
    "GENERIC_CALL_MARGIN": 0.04,
    "GENERIC_BET_EDGE": 0.20,
    "GENERIC_BET_POT": 0.6,
}

# ASSUMED: use the kit's payout table and blind schedule once they are available.
PAYOUTS = (100, 65, 45, 30, 20, 10, 5, 0)  # finishing-position points, 1st to 8th
BLIND_LEVELS = ((10, 20), (15, 30), (25, 50), (40, 80), (60, 120),
                (100, 200), (150, 300), (250, 500))
HANDS_PER_LEVEL = 25
MAX_HANDS = 200
STARTING_STACK = 2000
TABLE_SIZE = 8
