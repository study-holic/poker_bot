"""Independent heads-up NLHE bot (25bb deep, blinds 10/20).

Preflop: hand classes ordered by equity vs a random hand (ci_tables);
ranges are "top w of the 1326 combos" in that order. Opening, defending
and all-in calls are decided by Monte Carlo equity vs the opponent's
estimated range, compared with pot odds.
Postflop: Monte Carlo equity vs the opponent's preflop range, filtered by
their aggression (weakest current hands removed when they bet/raise),
compared with pot odds times an equity-realisation factor.
Opponent model: per-team counts with prior shrinkage (plain dicts).
"""

import random

from ci_eval import ev, card_to_int
from ci_tables import EQ_VS_RANDOM
from player_action import PlayerAction, DEALER

RANKS = "23456789TJQKA"


def _class_key(a, b):
    ra, rb = a >> 2, b >> 2
    if ra < rb:
        ra, rb = rb, ra
    if ra == rb:
        return RANKS[ra] + RANKS[rb]
    return RANKS[ra] + RANKS[rb] + ("s" if (a & 3) == (b & 3) else "o")


def _shrink(count, n, prior, k):
    return (count + prior * k) / (n + k)


def _has_draw(hole, board):
    """Flush draw (4 to a suit using a hole card) or open-ended straight draw."""
    cards = hole + board
    for s in range(4):
        n = 0
        hole_in = False
        for c in cards:
            if c & 3 == s:
                n += 1
        for c in hole:
            if c & 3 == s:
                hole_in = True
        if n == 4 and hole_in:
            return True
    mask = 0
    for c in cards:
        mask |= 1 << (c >> 2)
    if mask & (1 << 12):
        mask |= 1 << 13  # ace low handled loosely
    hm = 0
    for c in hole:
        hm |= 1 << (c >> 2)
    for lo in range(0, 10):
        w = 0b1111 << lo
        if mask & w == w and hm & w and lo >= 1 and lo + 4 <= 12:
            return True
    return False


class Model:
    def __init__(self):
        self.hand = []
        self.player_id = None
        # Combos ordered strongest first by equity vs random.
        combos = []
        for a in range(52):
            for b in range(a + 1, 52):
                combos.append((EQ_VS_RANDOM[_class_key(a, b)], a, b))
        combos.sort(key=lambda t: -t[0])
        self.combos = [(a, b) for _, a, b in combos]
        # Percentile (fraction of combos at least as strong) of each class.
        pct = {}
        n = len(combos)
        for i, (eq, a, b) in enumerate(combos):
            pct[_class_key(a, b)] = (i + 1) / n
        self.pct = pct
        self.opp = {}  # team name -> dict of counts
        self.rs = 88172645463325252
        self.h = {}

    # ------------------------------------------------------------ per hand
    def seed(self, hand, player_id):
        self.hand = hand
        self.player_id = player_id
        self.h = {
            "hole": [card_to_int(c) for c in hand],
            "nboard": 0,
            "log": [],  # (street_index, pid, kind, amount)
            "opp_start": 500,
            "my_start": 500,
            "init": False,
            "pf_aggr": None,  # pid of last preflop raiser
            "opp_line": "",  # preflop line of opponent
            "pending_resp": False,
            "opp_name": None,
            "counted": False,
            "opp_btn_recorded": False,
            "resp_open_recorded": False,
            "i_opened": False,
        }

    def _rand(self):
        self.rs = (self.rs * 6364136223846793005 + 1442695040888963407) % (1 << 64)
        return (self.rs >> 11) / float(1 << 53)

    def _stats(self, name):
        st = self.opp.get(name)
        if st is None:
            st = {
                "hands": 0,
                "btn_n": 0, "btn_raise": 0, "btn_fold": 0,
                "vs_open_n": 0, "vs_open_fold": 0, "vs_open_raise": 0,
                "vs_open_shove": 0,
                "pf_shove": 0,
                "sd_aggr_n": 0, "sd_aggr_pct": 0.0,
                "vs_bet_n": 0, "vs_bet_fold": 0,
                "post_act": 0, "post_aggr": 0,
            }
            self.opp[name] = st
        return st

    def _ingest(self, actions, gs):
        h = self.h
        me = self.player_id
        opp = 1 - me if gs.num_players == 2 else None
        if h["opp_name"] is None and opp is not None:
            h["opp_name"] = gs.teams[opp]
        st = self._stats(h["opp_name"]) if h["opp_name"] is not None else None
        if st is not None and not h["counted"]:
            st["hands"] += 1
            h["counted"] = True
        for a in actions:
            if a.kind == "reveal_card":
                if a.player_id == DEALER:
                    h["nboard"] += 1
                elif a.player_id == opp and st is not None:
                    h.setdefault("opp_shown", []).append(card_to_int(a.card))
                continue
            if a.kind == "win":
                continue
            s = 0 if h["nboard"] < 3 else h["nboard"] - 2
            h["log"].append((s, a.player_id, a.kind, a.amount))
            if st is None:
                continue
            if a.player_id == opp:
                if s == 0:
                    btn = gs.button
                    first_opp = sum(1 for x in h["log"] if x[0] == 0 and x[1] == opp) == 1
                    if opp == btn and first_opp and not h["opp_btn_recorded"]:
                        h["opp_btn_recorded"] = True
                        st["btn_n"] += 1
                        if a.kind == "raise":
                            st["btn_raise"] += 1
                        elif a.kind == "fold":
                            st["btn_fold"] += 1
                    if h["i_opened"] and not h["resp_open_recorded"]:
                        h["resp_open_recorded"] = True
                        st["vs_open_n"] += 1
                        if a.kind == "fold":
                            st["vs_open_fold"] += 1
                        elif a.kind == "raise":
                            st["vs_open_raise"] += 1
                            if a.amount >= 0.85 * h["opp_start"]:
                                st["vs_open_shove"] += 1
                    if a.kind == "raise":
                        h["pf_aggr"] = opp
                        if a.amount >= 0.85 * h["opp_start"]:
                            if "opp_shoved" not in h:
                                st["pf_shove"] += 1
                            h["opp_shoved"] = True
                else:
                    st["post_act"] += 1
                    if a.kind == "raise":
                        st["post_aggr"] += 1
                    if h["pending_resp"]:
                        st["vs_bet_n"] += 1
                        if a.kind == "fold":
                            st["vs_bet_fold"] += 1
                h["pending_resp"] = False
            elif a.player_id == me:
                if s == 0 and a.kind == "raise":
                    h["pf_aggr"] = me
                    if gs.button == me and not any(
                        x[0] == 0 and x[1] == me for x in h["log"][:-1]
                    ):
                        h["i_opened"] = True
                if s > 0 and a.kind == "raise":
                    h["pending_resp"] = True

    # ------------------------------------------------------------ ranges
    def _widths(self):
        st = self._stats(self.h["opp_name"]) if self.h["opp_name"] else None
        if st is None:
            return 0.65, 0.65, 0.12, 0.2, 0.5, 0.35
        w_open = _shrink(st["btn_raise"], st["btn_n"], 0.65, 8)
        w_def = _shrink(st["vs_open_n"] - st["vs_open_fold"], st["vs_open_n"], 0.65, 8)
        w_3b = _shrink(st["vs_open_raise"], st["vs_open_n"], 0.12, 8)
        w_shove = _shrink(st["pf_shove"], st["hands"], 0.12, 10)
        if st["sd_aggr_n"] >= 2:
            mean = st["sd_aggr_pct"] / st["sd_aggr_n"]
            w_sd = _shrink(2 * mean * st["sd_aggr_n"], st["sd_aggr_n"], 0.3, 4)
            w_sd = min(1.0, w_sd)
            w_open = max(w_open, w_sd)
            w_3b = max(w_3b, w_sd)
            w_shove = max(w_shove, w_sd)
        fold_bet = _shrink(st["vs_bet_fold"], st["vs_bet_n"], 0.4, 10)
        aggr = _shrink(st["post_aggr"], st["post_act"], 0.3, 15)
        return (min(1, max(0.08, w_open)), min(1, max(0.2, w_def)),
                min(1, max(0.04, w_3b)), min(1, max(0.06, w_shove)),
                fold_bet, aggr)

    def _equity(self, window, board, keep, samples, rng):
        hole = self.h["hole"]
        dead = set(hole) | set(board)
        n = len(self.combos)
        lo = int(window[0] * n)
        hi = max(lo + 30, int(window[1] * n))
        hi = min(n, hi)
        lo = min(lo, hi - 30)
        cands = []
        tries = 0
        target = 160 if keep < 0.999 and board else samples
        while len(cands) < target and tries < target * 4:
            tries += 1
            a, b = self.combos[rng.randrange(lo, hi)]
            if a in dead or b in dead:
                continue
            cands.append((a, b))
        if not cands:
            return 0.5
        if keep < 0.999 and len(board) >= 3:
            scored = []
            draw_floor = (1 << 20) | (6 << 16)
            for a, b in cands:
                k = ev([a, b] + board)
                if k < draw_floor and _has_draw([a, b], board):
                    k = draw_floor
                scored.append((k, a, b))
            scored.sort(key=lambda t: -t[0])
            m = max(8, int(len(scored) * keep))
            cands = [(a, b) for _, a, b in scored[:m]]
        deck = [c for c in range(52) if c not in dead]
        need = 5 - len(board)
        won = 0.0
        nc = len(cands)
        for i in range(samples):
            a, b = cands[i % nc]
            if need:
                run = []
                while len(run) < need:
                    c = deck[rng.randrange(len(deck))]
                    if c != a and c != b and c not in run:
                        run.append(c)
                full = board + run
            else:
                full = board
            mine = ev(hole + full)
            theirs = ev([a, b] + full)
            if mine > theirs:
                won += 1.0
            elif mine == theirs:
                won += 0.5
        return won / samples

    # ------------------------------------------------------------ actions
    def _raise(self, gs, total):
        me = self.player_id
        if not gs.can_raise or gs.raise_range is None:
            return PlayerAction.call(me)
        lo, hi = gs.raise_range
        total = int(total)
        total = min(hi, max(lo, total))
        return PlayerAction.raise_to(me, total)

    def _cf(self, gs):
        me = self.player_id
        if gs.call_amount == 0:
            return PlayerAction.call(me)
        return PlayerAction.fold(me)

    def run(self, actions, game_state):
        try:
            return self._run(actions, game_state)
        except Exception:
            try:
                return self._cf(game_state)
            except Exception:
                return PlayerAction.fold(self.player_id)

    def _run(self, actions, gs):
        me = self.player_id
        self._ingest(actions, gs)
        h = self.h
        opp = 1 - me
        if not h["init"]:
            h["init"] = True
            h["opp_start"] = gs.stacks[opp] + gs.bets[opp]
            h["my_start"] = gs.stacks[me] + gs.bets[me]
        hole = h["hole"]
        board = [card_to_int(c) for c in gs.board]
        seedv = (hole[0] * 53 + hole[1]) * 1000003 + len(board) * 7919 + len(h["log"]) * 131 + (self.rs & 0xFFFF)
        rng = random.Random(seedv)
        self._rand()
        if gs.street == "preflop":
            return self._preflop(gs, rng)
        return self._postflop(gs, board, rng)

    # ------------------------------------------------------------ preflop
    def _preflop(self, gs, rng):
        me = self.player_id
        opp = 1 - me
        h = self.h
        bb = gs.big_blind
        w_open, w_def, w_3b, w_shove, fold_bet, aggr = self._widths()
        my_pct = self.pct[_class_key(*h["hole"])]
        eff = min(gs.stacks[me] + gs.bets[me], gs.stacks[opp] + gs.bets[opp])
        S = eff / bb
        call = gs.call_amount
        pot = gs.pot
        opp_allin = gs.status(opp) == "all_in" or gs.stacks[opp] == 0
        call_allin = call >= gs.stacks[me]
        my_prev = [x for x in h["log"] if x[0] == 0 and x[1] == me]
        opp_raises = [x for x in h["log"] if x[0] == 0 and x[1] == opp and x[2] == "raise"]
        is_btn = gs.button == me

        # Facing an all-in (or a bet that commits us): pure pot-odds call.
        if call > 0 and (opp_allin or call_allin or gs.current_bet >= 0.6 * eff):
            if is_btn and not my_prev:
                w = w_shove  # open-shove by BB? (button facing BB jam can't happen first)
            elif is_btn:
                w = max(w_3b, w_shove) if len(opp_raises) <= 1 else min(w_3b, 0.1)
            else:
                w = max(w_shove, w_open) if len(my_prev) == 0 else min(max(w_shove, 0.08), 0.2)
            w = min(1.0, max(w, 0.06))
            eq = self._equity((0.0, w), [], 1.0, 500, rng)
            need = call / (pot + call)
            if eq >= need + 0.01:
                if gs.can_raise and not opp_allin:
                    return self._raise(gs, gs.max_raise_to)
                return PlayerAction.call(me)
            return PlayerAction.fold(me)

        if is_btn and not my_prev:
            # First action on the button.
            if S <= 12:
                push = min(1.0, 0.5 + (12 - S) * 0.05)
                if my_pct <= push:
                    return self._raise(gs, gs.max_raise_to)
                return PlayerAction.fold(me)
            st = self._stats(h["opp_name"]) if h["opp_name"] else None
            p_jam = 0.1
            if st is not None:
                p_jam = _shrink(st["vs_open_shove"], st["vs_open_n"], 0.1, 6)
            open_w = 0.80
            if p_jam > 0.4:
                # Maniac BB: only open hands that can call their jam.
                eq = self._equity((0.0, max(w_shove, 0.5)), [], 1.0, 300, rng)
                if eq >= 0.48:
                    return self._raise(gs, 2.25 * bb)
                if my_pct <= 0.9 and p_jam < 0.85:
                    return PlayerAction.fold(me)
                return PlayerAction.fold(me)
            if my_pct <= open_w:
                size = 2.25 * bb if my_pct > 0.06 or self._rand() < 0.5 else 2.25 * bb
                return self._raise(gs, size)
            return PlayerAction.fold(me)

        if not is_btn and not my_prev:
            # Big blind, first action.
            if call == 0:
                # Opponent limped.
                if S <= 12:
                    if my_pct <= 0.35:
                        return self._raise(gs, gs.max_raise_to)
                    return PlayerAction.call(me)
                if my_pct <= 0.30:
                    return self._raise(gs, 3.5 * bb)
                return PlayerAction.call(me)
            # Facing an open raise.
            w = w_open
            eq = self._equity((0.0, w), [], 1.0, 400, rng)
            need_call = call / (pot + call)
            open_size = gs.current_bet
            if S <= 14:
                jam_need = (eff - gs.bets[me]) / (2 * eff - gs.bets[me])  # rough
                if eq >= 0.5 or my_pct <= 0.25:
                    return self._raise(gs, gs.max_raise_to)
                if eq * 0.85 >= need_call and open_size <= 2.5 * bb:
                    return PlayerAction.call(me)
                return PlayerAction.fold(me)
            if eq >= 0.60 or (open_size <= 3 * bb and my_pct <= 0.06):
                return self._raise(gs, gs.max_raise_to)
            # A few bluff jams with blockers-ish hands vs wide opens.
            if w >= 0.6 and open_size <= 3 * bb and 0.25 <= my_pct <= 0.40 and self._rand() < 0.25:
                return self._raise(gs, gs.max_raise_to)
            real = 0.75 if eq < 0.45 else 0.88
            if eq * real >= need_call:
                return PlayerAction.call(me)
            return PlayerAction.fold(me)

        # Later preflop decisions (facing a 3-bet / 4-bet that is not all-in).
        if call == 0:
            return PlayerAction.call(me)
        w = w_3b if is_btn else min(w_3b, 0.15)
        eq = self._equity((0.0, max(0.05, w)), [], 1.0, 400, rng)
        jam_need = 0.45
        if eq >= jam_need - 0.04:
            return self._raise(gs, gs.max_raise_to)
        need_call = call / (pot + call)
        if eq * 0.9 >= need_call and call <= 3 * bb:
            return PlayerAction.call(me)
        return PlayerAction.fold(me)

    # ------------------------------------------------------------ postflop
    def _opp_window(self):
        h = self.h
        me = self.player_id
        opp = 1 - me
        w_open, w_def, w_3b, w_shove, _, _ = self._widths()
        pf = [x for x in h["log"] if x[0] == 0]
        opp_r = sum(1 for x in pf if x[1] == opp and x[2] == "raise")
        my_r = sum(1 for x in pf if x[1] == me and x[2] == "raise")
        if opp_r >= 2:
            return (0.0, max(0.06, min(w_3b, 0.2)))
        if opp_r == 1 and my_r >= 1:
            # Either they 3bet and we called, or they opened and called our 3bet.
            return (0.0, max(0.1, min(w_3b if my_r and pf and pf[0][1] == me else 0.3, 1.0)))
        if opp_r == 1:
            return (0.0, w_open)
        if my_r >= 1:
            return (0.03, w_def)
        return (0.05, 1.0)

    def _postflop(self, gs, board, rng):
        me = self.player_id
        opp = 1 - me
        h = self.h
        street_i = len(board) - 2  # 1 flop, 2 turn, 3 river
        w_open, w_def, w_3b, w_shove, fold_bet, aggr = self._widths()
        window = self._opp_window()
        # Aggression filter: each postflop bet/raise by opponent removes weak hands.
        keep = 1.0
        last_s = None
        for (s, pid, kind, amt) in h["log"]:
            if s == 0 or pid != opp:
                continue
            if kind == "raise":
                keep *= 0.6
            elif kind == "call":
                keep *= 0.85
        # Size of current bet facing us relative to pot.
        call = gs.call_amount
        pot = gs.pot
        if call > 0:
            pre = max(1, pot - call)
            f = call / pre
            keep *= max(0.55, 1.0 - 0.2 * min(f, 2.0))
        # Maniacs: aggression carries little information.
        mania = min(1.0, max(0.0, (aggr - 0.35) / 0.4))
        keep = 1.0 - (1.0 - keep) * (1.0 - mania)
        keep = max(0.15, min(1.0, keep))
        eq = self._equity(window, board, keep, 300, rng)

        my_stack = gs.stacks[me]
        opp_stack = gs.stacks[opp] + gs.bets[opp] - gs.bets[me]
        eff = min(my_stack, max(0, opp_stack))
        spr = eff / max(1, pot)
        ip = gs.button == me
        was_aggr = h["pf_aggr"] == me
        draw = street_i < 3 and _has_draw(h["hole"], board)

        if call == 0:
            # Bet or check. Equity vs the full (unfiltered by this street) range.
            if eq >= 0.85 and street_i == 3:
                size = 1.0
            elif eq >= (0.62 if street_i == 1 else 0.64):
                size = 0.5 if street_i == 1 else 0.7
            else:
                size = 0.0
            if size > 0:
                amt = size * pot
                if spr <= 1.5 or amt >= 0.6 * eff:
                    return self._raise(gs, gs.max_raise_to)
                return self._raise(gs, max(gs.big_blind, amt))
            # Non-value: c-bets, semi-bluffs, occasional bluffs.
            station = fold_bet < 0.3
            if draw and not station and self._rand() < 0.55:
                return self._raise(gs, max(gs.big_blind, 0.5 * pot))
            if street_i == 1 and was_aggr and eq >= 0.3:
                freq = 0.65 if fold_bet >= 0.4 else (0.35 if not station else 0.1)
                if self._rand() < freq:
                    return self._raise(gs, max(gs.big_blind, 0.33 * pot))
            if street_i == 3 and eq < 0.25 and fold_bet >= 0.55 and self._rand() < 0.3:
                return self._raise(gs, max(gs.big_blind, 0.66 * pot))
            if street_i == 2 and ip and eq < 0.35 and fold_bet >= 0.55 and self._rand() < 0.25:
                return self._raise(gs, max(gs.big_blind, 0.5 * pot))
            return PlayerAction.call(me)

        # Facing a bet.
        need = call / (pot + call)
        if street_i == 3:
            real = 1.0
        elif ip:
            real = 0.95
        else:
            real = 0.88 if street_i == 1 else 0.92
        raise_thr = {1: 0.78, 2: 0.8, 3: 0.86}[street_i]
        if eq >= raise_thr and gs.can_raise:
            target = gs.current_bet + (pot + call)
            if spr <= 2.0 or target >= 0.55 * (my_stack + gs.bets[me]):
                return self._raise(gs, gs.max_raise_to)
            return self._raise(gs, target)
        if eq * real >= need + 0.02:
            return PlayerAction.call(me)
        # Semi-bluff raise with a draw vs a small bet, if they fold enough.
        if draw and street_i == 1 and call <= 0.5 * (pot - call) and fold_bet >= 0.45 \
                and gs.can_raise and self._rand() < 0.3:
            return self._raise(gs, gs.current_bet * 3)
        return PlayerAction.fold(me)

    # ------------------------------------------------------------ learning
    def end_game(self, actions, game_state):
        try:
            self._ingest(actions, game_state)
            h = self.h
            shown = h.get("opp_shown")
            if shown and len(shown) == 2 and h["opp_name"]:
                st = self._stats(h["opp_name"])
                opp = 1 - self.player_id
                pf_raised = any(x[0] == 0 and x[1] == opp and x[2] == "raise" for x in h["log"])
                if pf_raised:
                    st["sd_aggr_n"] += 1
                    st["sd_aggr_pct"] += self.pct[_class_key(shown[0], shown[1])]
        except Exception:
            pass
