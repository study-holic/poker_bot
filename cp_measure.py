"""Measure a Model's preflop action distribution (HU, 25bb). Usage:
python cp_measure.py module:Class seed1 seed2 ..."""
import sys, importlib, collections
from card_utils import Card
from game_state import GameState, GameStateView
from player_action import PlayerAction
import pokerlib as P

RANKS = "23456789TJQKA"


def classes():
    out = []
    for i in range(13):
        for j in range(13):
            hi, lo = RANKS[max(i, j)], RANKS[min(i, j)]
            if i == j:
                out.append(((hi + "S", lo + "H"), 6))
            elif i > j:
                out.append(((hi + "S", lo + "S"), 4))
            else:
                out.append(((hi + "S", lo + "H"), 12))
    return out


def kind(act, gs):
    if act.kind == "fold":
        return "fold"
    if act.kind == "call":
        return "limp/call" if gs.call_amount > 0 else "check"
    if act.amount >= gs.max_raise_to:
        return "shove"
    return "raise"


def run(cls, scen, seed):
    P._RNG.seed(seed)
    tally = collections.Counter()
    sizes = collections.Counter()
    for (c1, c2), w in classes():
        m = cls()
        st = GameState([500, 500], teams=["me", "opp"]) if True else None
        st.setup_hand([500, 500], button=0, teams=["me", "opp"])
        hand = [Card.parse(c1), Card.parse(c2)]
        acts = []
        if scen == "sb":
            me = 0
        else:
            me = 1
            if scen == "bb_vs_limp":
                a = PlayerAction.call(0)
            elif scen == "bb_vs_2.5x":
                a = PlayerAction.raise_to(0, 50)
            elif scen == "bb_vs_shove":
                a = PlayerAction.raise_to(0, 500)
            st.process_action(a)
            acts = [a]
        m.seed(hand, me)
        gs = GameStateView(st)
        act = m.run(acts, gs)
        k = kind(act, gs)
        tally[k] += w
        if k == "raise":
            sizes[act.amount] += w
    return tally, sizes


if __name__ == "__main__":
    mod, name = sys.argv[1].split(":")
    cls = getattr(importlib.import_module(mod), name)
    seeds = [int(s) for s in sys.argv[2:]] or [1]
    for scen in ["sb", "bb_vs_limp", "bb_vs_2.5x", "bb_vs_shove"]:
        for s in seeds:
            t, sz = run(cls, scen, s)
            tot = sum(t.values())
            print(scen, "seed", s, {k: round(v / tot, 3) for k, v in sorted(t.items())}, "raise sizes", dict(sz))
