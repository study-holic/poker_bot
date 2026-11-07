"""
Adversary bots for the gauntlet (Subagent C). Each is small, legal, fast and
deliberately one-dimensional, so that it punishes one specific leak:

    Station   calls almost everything, rarely raises   -> punishes bluffing
    Maniac    raises/pots very often on every street   -> punishes overfolding
    Jammer    shoves top ~50% preflop, else folds      -> punishes loose opens / bad call-off ranges
    Nit3bet   tight, 3/4-bets strong, c-bets 33% pot   -> punishes weak postflop defence / over-calling
    SmallBall min-raises wide, bets 25-33% pot often   -> punishes overfolding to small bets
              folds to big raises

Flat imports, plain-data attributes (a random.Random is picklable), so the
classes pickle by reference as adv_bots.<Name>.
"""

import random

from card_utils import evaluate
from player_action import PlayerAction


# ---------------------------------------------------------------- preflop
def _chen(hi, lo, suited):
    """Bill Chen's starting-hand score (hi >= lo, card values 2..14)."""
    top = {14: 10, 13: 8, 12: 7, 11: 6}.get(hi, hi / 2)
    if hi == lo:
        return max(5, 2 * top)
    s = top + (2 if suited else 0)
    gap = hi - lo - 1
    s -= {0: 0, 1: 1, 2: 2, 3: 4}.get(gap, 5)
    if gap <= 1 and hi < 12:
        s += 1
    return s


def _build_percentiles():
    """(hi, lo, suited) -> fraction of the 1326 combos at least as strong
    (0.0 = best, 1.0 = worst)."""
    classes = []
    for hi in range(2, 15):
        for lo in range(2, hi + 1):
            if hi == lo:
                classes.append(((hi, lo, False), 6))
            else:
                classes.append(((hi, lo, True), 4))
                classes.append(((hi, lo, False), 12))
    classes.sort(key=lambda c: -(_chen(*c[0]) + 0.01 * c[0][0] + 0.001 * c[0][1]))
    out, seen = {}, 0
    for key, combos in classes:
        seen += combos
        out[key] = seen / 1326
    return out


_PCT = _build_percentiles()


def preflop_pct(hand):
    """Top-x fraction of this hand (0.0 best .. 1.0 worst)."""
    a, b = hand
    hi, lo = max(a.value, b.value), min(a.value, b.value)
    return _PCT[(hi, lo, hi != lo and a.suit == b.suit)]


# --------------------------------------------------------------- postflop
def made_level(hand, board):
    """0 air, 1 weak pair, 2 top pair / overpair, 3 two pair, 4 trips+,
    only counting what uses a hole card."""
    cat = evaluate(list(hand) + list(board))[0]
    bvals = [c.value for c in board]
    hvals = [c.value for c in hand]
    if cat >= 3:
        # trips or better: make sure it is not purely the board
        if len(board) == 5 and evaluate(list(board)) >= evaluate(list(hand) + list(board)):
            return 1
        return 4
    if cat == 2:
        paired_with_hole = sum(v in bvals for v in hvals)
        if paired_with_hole >= 1 or hvals[0] == hvals[1]:
            return 3
        return 1
    if cat == 1:
        if hvals[0] == hvals[1]:
            return 2 if hvals[0] > max(bvals) else 1
        if max(bvals) in hvals:
            return 2
        if any(v in bvals for v in hvals):
            return 1
        return 0  # board pair only
    return 0


def has_draw(hand, board):
    """Flush draw (4 to a suit using a hole card) or open-ended-ish."""
    if len(board) >= 5:
        return False
    cards = list(hand) + list(board)
    for suit in "CDHS":
        if sum(c.suit == suit for c in cards) == 4 and any(c.suit == suit for c in hand):
            return True
    vals = set(c.value for c in cards)
    if 14 in vals:
        vals.add(1)
    for lo in range(1, 11):
        window = set(range(lo, lo + 5))
        if len(window & vals) == 4 and any(c.value in window for c in hand):
            return True
    return False


# ------------------------------------------------------------------ base
class _Adv:
    def __init__(self):
        self.hand = []
        self.player_id = None
        self.rng = random.Random(0xC0FFEE)

    def seed(self, hand, player_id):
        self.hand = list(hand)
        self.player_id = player_id

    def _call(self):
        return PlayerAction.call(self.player_id)

    def _check_fold(self, gs):
        if gs.call_amount == 0:
            return PlayerAction.call(self.player_id)
        return PlayerAction.fold(self.player_id)

    def _raise_to(self, gs, total):
        if not gs.can_raise:
            return PlayerAction.call(self.player_id)
        low, high = gs.raise_range
        return PlayerAction.raise_to(self.player_id, int(min(high, max(low, total))))

    def _shove(self, gs):
        return self._raise_to(gs, gs.max_raise_to if gs.can_raise else 0)

    def _bet_frac(self, gs, frac):
        """Bet/raise to current_bet + frac * (pot after calling)."""
        pot_after_call = gs.pot + gs.call_amount
        return self._raise_to(gs, gs.current_bet + frac * pot_after_call)

    def _facing_frac(self, gs):
        """Size of what we face, as a fraction of the pot before it."""
        if gs.call_amount == 0:
            return 0.0
        before = max(1, gs.pot - gs.call_amount)
        return gs.call_amount / before


# ---------------------------------------------------------------- Station
class Station(_Adv):
    """Calls almost everything; raises only with monsters (AA/KK preflop to
    3x, sets+ postflop). Folds only true air to overbets on the river and
    the very worst hands to big preflop raises."""

    def run(self, actions, gs):
        if gs.street == "preflop":
            pct = preflop_pct(self.hand)
            if pct <= 0.01 and gs.current_bet <= gs.big_blind * 3:
                return self._raise_to(gs, 3 * max(gs.current_bet, gs.big_blind))
            if pct > 0.92 and gs.call_amount > 4 * gs.big_blind:
                return PlayerAction.fold(self.player_id)
            return self._call()
        lvl = made_level(self.hand, gs.board)
        if lvl >= 4 and self.rng.random() < 0.5:
            return self._bet_frac(gs, 0.66)
        if gs.call_amount == 0:
            return self._call()
        if lvl == 0 and not has_draw(self.hand, gs.board):
            if gs.street == "river" and self._facing_frac(gs) > 0.9:
                return PlayerAction.fold(self.player_id)
        return self._call()


# ----------------------------------------------------------------- Maniac
class Maniac(_Adv):
    """Raises 85% of hands preflop (3.5x open, 3x re-raise), bets pot 75% of
    the time when checked to, raises 35% of bets, calls with any pair or
    draw, folds air to big bets half of the time."""

    def run(self, actions, gs):
        r = self.rng.random()
        if gs.street == "preflop":
            pct = preflop_pct(self.hand)
            if pct <= 0.85 and r < 0.9:
                if gs.current_bet <= gs.big_blind:
                    return self._raise_to(gs, 3.5 * gs.big_blind)
                if gs.current_bet < 0.5 * (gs.current_bet + gs.stacks[self.player_id]):
                    return self._raise_to(gs, 3 * gs.current_bet)
                return self._call() if pct <= 0.5 else self._check_fold(gs)
            if gs.call_amount <= 3 * gs.big_blind:
                return self._call()
            return self._check_fold(gs)
        lvl = made_level(self.hand, gs.board)
        draw = has_draw(self.hand, gs.board)
        if gs.call_amount == 0:
            if r < 0.75 or lvl >= 2:
                return self._bet_frac(gs, 1.0)
            return self._call()
        if r < 0.35 or lvl >= 3:
            return self._bet_frac(gs, 1.0)
        if lvl >= 1 or draw:
            return self._call()
        if self._facing_frac(gs) < 0.6 or r < 0.67:
            return self._call()
        return PlayerAction.fold(self.player_id)


# ----------------------------------------------------------------- Jammer
class Jammer(_Adv):
    """Preflop: with the top ~50% of hands, shoves over anything (open or
    re-shove); otherwise folds (checks when free). Postflop (only after a
    limped/checked pot): shoves pair+, otherwise check/fold."""

    def run(self, actions, gs):
        if gs.street == "preflop":
            if preflop_pct(self.hand) <= 0.50:
                if gs.can_raise:
                    return self._shove(gs)
                return self._call()
            return self._check_fold(gs)
        if made_level(self.hand, gs.board) >= 1:
            if gs.can_raise:
                return self._shove(gs)
            return self._call()
        return self._check_fold(gs)


# ---------------------------------------------------------------- Nit3bet
class Nit3bet(_Adv):
    """Opens top 30% to 2.5x; facing a raise 3/4-bets top 8% (3x, shoving
    once that commits a third of the stack), calls top 20%, else folds.
    Postflop: c-bets 33% pot on 85% of flops when checked to / first in,
    bets 50% on turn/river with top pair+; facing a bet calls top pair+,
    raises two pair+, else folds (calls tiny bets with a weak pair)."""

    def run(self, actions, gs):
        me = self.player_id
        if gs.street == "preflop":
            pct = preflop_pct(self.hand)
            facing_raise = gs.current_bet > gs.big_blind
            if not facing_raise:
                if pct <= 0.30:
                    return self._raise_to(gs, 2.5 * gs.big_blind)
                return self._check_fold(gs)
            if pct <= 0.08:
                target = 3 * gs.current_bet
                if target >= (gs.stacks[me] + gs.bets[me]) / 3:
                    return self._shove(gs)
                return self._raise_to(gs, target)
            if pct <= 0.20 and gs.call_amount <= 0.25 * gs.stacks[me]:
                return self._call()
            return self._check_fold(gs)
        lvl = made_level(self.hand, gs.board)
        r = self.rng.random()
        if gs.call_amount == 0:
            if gs.street == "flop":
                if r < 0.85 or lvl >= 2:
                    return self._bet_frac(gs, 0.33)
                return self._call()
            if lvl >= 2:
                return self._bet_frac(gs, 0.5)
            return self._call()
        if lvl >= 3:
            return self._bet_frac(gs, 0.75)
        if lvl >= 2:
            return self._call()
        if lvl == 1 and gs.pot_odds < 0.2:
            return self._call()
        return PlayerAction.fold(me)


# -------------------------------------------------------------- SmallBall
class SmallBall(_Adv):
    """Min-raises 80% of hands preflop and min-3-bets the top 15%; folds to a
    big raise (>= 4 bb to call, or over a quarter of the stack) unless top
    10%. Postflop: bets 25-33% pot 70% of the time; calls bets up to half
    pot liberally; folds to bigger bets/raises without two pair+."""

    def run(self, actions, gs):
        me = self.player_id
        r = self.rng.random()
        if gs.street == "preflop":
            pct = preflop_pct(self.hand)
            big = gs.call_amount >= 4 * gs.big_blind or gs.call_amount > 0.25 * gs.stacks[me]
            if big:
                if pct <= 0.10:
                    return self._call()
                return PlayerAction.fold(me)
            if gs.current_bet <= gs.big_blind:
                if pct <= 0.80:
                    return self._raise_to(gs, gs.min_raise_to if gs.can_raise else 0)
                return self._check_fold(gs)
            if pct <= 0.15:
                return self._raise_to(gs, gs.min_raise_to if gs.can_raise else 0)
            if pct <= 0.75:
                return self._call()
            return self._check_fold(gs)
        lvl = made_level(self.hand, gs.board)
        draw = has_draw(self.hand, gs.board)
        if gs.call_amount == 0:
            if r < 0.70 or lvl >= 2:
                return self._bet_frac(gs, 0.25 + 0.08 * self.rng.random())
            return self._call()
        frac = self._facing_frac(gs)
        if lvl >= 3:
            return self._call() if frac > 0.5 else self._bet_frac(gs, 0.33)
        if frac <= 0.5:
            if lvl >= 1 or draw or r < 0.5:
                return self._call()
            return PlayerAction.fold(me)
        if lvl >= 2 and frac <= 0.8:
            return self._call()
        return PlayerAction.fold(me)


ADVERSARIES = {
    "station": Station,
    "maniac": Maniac,
    "jammer": Jammer,
    "nit3bet": Nit3bet,
    "smallball": SmallBall,
}
