"""v5 candidates (lead integration). Audit-driven micro-fixes on top of v4.

PostCapMixin: when facing a bet postflop, never raise with less than two
pair (v4's action-conditioned range over-discounts passive lines, so one
pair can show e > post_raise_thr and raise all-in; audit finding #3).
Model    = candidate_preflop.Model (range-based preflop) + PostCap + less MC noise.
V4Post   = v4 + PostCap only (isolates the postflop fix).
"""

from card_utils import evaluate
from player_action import PlayerAction

import model as V4
import candidate_preflop as CP


class PostCapMixin:
    def _postflop(self, gs):
        act = super()._postflop(gs)
        try:
            if (act.kind == "raise" and gs.call_amount > 0
                    and evaluate(list(self.hand) + list(gs.board))[0] < 2):
                return PlayerAction.call(self.player_id)
        except Exception:
            pass
        return act


class Model(PostCapMixin, CP.Model):
    def _eq_top(self, lo, hi, n=400):
        return super()._eq_top(lo, hi, n=max(n, 1500))


class V4Post(PostCapMixin, V4.Model):
    pass


class V4PostN(V4Post):
    """V4Post + 1500-sample _eq_top (audit #1: SB-first choice was MC noise)."""
    def _eq_top(self, lo, hi, n=400):
        return super()._eq_top(lo, hi, n=max(n, 1500))
