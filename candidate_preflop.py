"""Candidate preflop policies on top of v4 (model.py). Postflop is v4's,
unchanged: only the preflop decision path is overridden.

ModelMin: smallest fix. v4's _sb_first scores 'shove' with full-stack
showdown EV but 'open' with a 2*open_to pot plus a 15% implied term, so the
open-jam branch dominates for any hand with decent equity vs a 45% calling
range (24-26% of combos jam at 25bb). ModelMin keeps v4's EV numbers but only
allows the jam when effective stacks are <= 12bb and never limps.

Model: stack-aware range policy (HU, button = SB):
  SB first in  : eff <= 12bb push/fold (top f(eff)); otherwise open to 2.25bb
                 with the top ~82% (100% vs habitual folders), never limp.
  BB vs limp   : raise to 3.5bb with top 28%, else check.
  BB vs open   : 3bet to 3x (value top 12% + suited bluff band), call when
                 equity vs the opener's range * realisation > pot odds.
  vs all-in    : call iff equity vs an estimated jamming range > pot odds
                 (unknown first-in jammer: at least top 40%; widened to the
                 observed jam frequency).
  SB vs 3bet   : jam with equity >= 0.55 vs the 3bet range, call by pot
                 odds, else fold; committed -> pot odds.
Everything else falls back to v4's _preflop.
"""

import model as V4
import pokerlib as P
from player_action import PlayerAction

_PF_PCT = V4._PF_PCT
_COMBOS = V4._COMBOS


def _push_frac(eff_bb):
    """Approximate HU SB Nash push frequency by effective stack (bb)."""
    if eff_bb <= 4:
        return 1.0
    if eff_bb <= 6:
        return 0.85
    if eff_bb <= 8:
        return 0.72
    if eff_bb <= 10:
        return 0.62
    return 0.55  # 10-12bb


class ModelMin(V4.Model):
    def _sb_first(self, gs, team, my_pct):
        me = self.player_id
        bb = gs.big_blind
        sb_in = gs.bets[me]
        stack = gs.stacks[me] + sb_in
        opp_total = gs.stacks[self.opp] + gs.bets[self.opp]
        eff = min(stack, opp_total)
        V4.Model._sb_first(self, gs, team, my_pct)  # fills self.last_ev
        ev = dict(self.last_ev)
        ev.pop("limp", None)
        if eff > 12 * bb:
            ev.pop("shove", None)
        best = max(ev, key=ev.get)
        if best == "open":
            return self._raise(gs, int(2.5 * bb))
        if best == "shove":
            return self._raise(gs, gs.max_raise_to)
        return PlayerAction.fold(me)


class Model(V4.Model):
    OPEN_FRAC = 0.82
    OPEN_BB = 2.25
    REALISE = 0.88

    def _my_pct(self):
        return _PF_PCT[_COMBOS.index(tuple(sorted(self.hole)))]

    def _obs(self, team, key):
        c = self._stat(team)[key]
        return c[0] + c[1] + c[2]

    def _eff(self, gs):
        me = self.player_id
        return min(gs.stacks[me] + gs.bets[me], gs.stacks[self.opp] + gs.bets[self.opp])

    def _preflop(self, gs):
        me = self.player_id
        team = self._opp_team(gs)
        bb = gs.big_blind
        call = gs.call_amount
        pot = gs.pot
        my_pct = self._my_pct()
        is_sb = me == self.sb_seat
        if is_sb and self.pf_raises == 0 and not gs.acted[me]:
            return self._sb_first(gs, team, my_pct)
        opp_allin = gs.stacks[self.opp] == 0
        if call == 0 and not is_sb and self.pf_raises == 0:
            return self._bb_vs_limp(gs, my_pct)
        if call > 0 and (opp_allin or not gs.can_raise):
            return self._vs_allin(gs, team, call, pot)
        if not is_sb and self.pf_raises == 1 and call > 0:
            return self._bb_vs_open(gs, team, my_pct, call, pot)
        if is_sb and self.pf_raises == 2 and call > 0:
            return self._sb_vs_3bet(gs, team, my_pct, call, pot)
        return V4.Model._preflop(self, gs)

    # -- spots ------------------------------------------------------------
    def _sb_first(self, gs, team, my_pct):
        me = self.player_id
        bb = gs.big_blind
        eff_bb = self._eff(gs) / bb
        if eff_bb <= 12:
            if my_pct >= 1.0 - _push_frac(eff_bb):
                return self._raise(gs, gs.max_raise_to)
            return PlayerAction.fold(me)
        frac = self.OPEN_FRAC
        f, c, r, _ = self.freq(team, "pf_vs_open")
        if self._obs(team, "pf_vs_open") >= 8 and f > 0.55:
            frac = 1.0
        if my_pct >= 1.0 - frac:
            return self._raise(gs, int(self.OPEN_BB * bb))
        return PlayerAction.fold(me)

    def _bb_vs_limp(self, gs, my_pct):
        if my_pct >= 0.72 and gs.can_raise:
            return self._raise(gs, int(3.5 * gs.big_blind))
        return PlayerAction.call(self.player_id)

    def _jam_range(self, team, key, floor):
        f, c, r, bigs = self.freq(team, key)
        return min(1.0, max(floor, r * bigs))

    def _vs_allin(self, gs, team, call, pot):
        me = self.player_id
        po = call / (pot + call)
        if self.pf_raises <= 1:
            frac = self._jam_range(team, "pf_open", 0.40)
        elif self.pf_raises == 2:
            frac = self._jam_range(team, "pf_vs_open", 0.15)
        else:
            frac = self._jam_range(team, "pf_vs_3bet", 0.08)
        e = self._eq_top(0, frac, n=700)
        if e > po:
            return PlayerAction.call(me)
        return PlayerAction.fold(me)

    def _bb_vs_open(self, gs, team, my_pct, call, pot):
        me = self.player_id
        bb = gs.big_blind
        cur = gs.current_bet
        my_total = gs.stacks[me] + gs.bets[me]
        po = call / (pot + call)
        f, c, r, _ = self.freq(team, "pf_open")
        open_frac = min(1.0, max(0.3, r))
        # bigger opens -> tighter assumed range
        if cur > 3 * bb:
            open_frac = min(open_frac, 0.35)
        e = self._eq_top(0, open_frac, n=600)
        value = my_pct >= 0.88
        suited = (self.hole[0] & 3) == (self.hole[1] & 3)
        bluff = suited and 0.50 <= my_pct < 0.66 and self._coin(0.5)
        if gs.can_raise and (value or bluff):
            total = 3 * cur
            if total >= 0.4 * my_total:
                if value:
                    return self._raise(gs, gs.max_raise_to)
            else:
                return self._raise(gs, total)
        stack_after = gs.stacks[me] - call
        if stack_after < 0.6 * (pot + call):
            return PlayerAction.call(me) if e > po else PlayerAction.fold(me)
        if e * self.REALISE > po:
            return PlayerAction.call(me)
        return PlayerAction.fold(me)

    def _sb_vs_3bet(self, gs, team, my_pct, call, pot):
        me = self.player_id
        po = call / (pot + call)
        f, c, r, bigs = self.freq(team, "pf_vs_open")
        frac = min(1.0, max(0.12, r))
        e = self._eq_top(0, frac, n=600)
        stack_after = gs.stacks[me] - call
        if stack_after < 0.6 * (pot + call):
            if e > po:
                if gs.can_raise and stack_after > 0:
                    return self._raise(gs, gs.max_raise_to)
                return PlayerAction.call(me)
            return PlayerAction.fold(me)
        if e >= 0.55 and gs.can_raise:
            return self._raise(gs, gs.max_raise_to)
        if e * 0.95 > po:
            return PlayerAction.call(me)
        return PlayerAction.fold(me)
