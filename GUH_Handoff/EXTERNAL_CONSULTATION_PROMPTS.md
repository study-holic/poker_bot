# Claude Chrome consultation prompts — use IN PARALLEL if available

These are DIFFERENT reviews. Keep them blinded from each other; don't paste another model's answer into a prompt as "consensus". Each reply should give a decisive, testable improvement under the actual remaining minutes. User authorises consultation via Claude Chrome if connected. If no browser/session, do not block the build.

## A. DeepSeek — adversarial code/poker critique (show baseline v4)

We are competing TODAY in the Manchester AI Society heads-up no-limit Texas Hold'em bot contest, 25bb default stacks (500 chips, 10/20 blinds), round-robin duplicate deals scored bb/100, top 5 qualify for final. Python `Model` has only a public read-only GameStateView and `PlayerAction`, 10s/move; no network/files/engine internals in submitted code. We have less than 90 minutes until an internal 17:50 GMT submission stop. I have a baseline v4 with range-conditioned Monte Carlo and a first-action button EV comparator (`open`/`limp`/`shove`/`fold`). A prior reviewer claimed it open-shoves ~23–27% combos under default priors and that shove terminal EV is calculated more exactly than non-all-in raise continuations. Please independently audit the ACTUAL provided code, not this claim. Identify the single most financially damaging strategic or code bug, an adversarial opponent that exploits it, the smallest direct ablation and what result would falsify your diagnosis. No big rewrite, no ungrounded thresholds or fabricated test results. Return a precise patch hypothesis and test protocol. I can share model.py, pokerlib.py, preflop_table.py and the official README/CLAUDE.md.

## B. ChatGPT — experimental design / selection (no obligation to agree)

We have roughly 60–90 minutes to choose a strong heads-up poker bot. Tournament: round-robin against unknown Python bots, seat-swapped duplicate decks, bb/100 score; top 5 then play round 2. 25bb effective stacks (normally), each action 10s, 18:00 public deadline but HARD 17:50 internal submission cutoff. Candidates: frozen Monte Carlo heuristic v4, v4 with preflop ablated, independently created solid positional 25bb baseline. We can run the official `python -m evals` with opponent pickles and dummy strategies. Design an efficient *adaptive experimental tournament*, using common seeds, per-opponent results, robust risk criteria and holdouts. Estimate what comparisons are possible with sparse 200–1000 paired deals; tell us when NOT to conclude a winner. Recommend a short decision rule for top-five qualification and small round-2 final where one catastrophic matchup may matter. Avoid proposing large new code systems. Challenge the premise if necessary.

## C. Independent Claude Chat — BLIND conceptual strategy review (DO NOT SHOW v4)

Independently propose the strongest implementable tournament poker policy you can in one hour for this contest: heads-up no-limit Texas hold'em, default 500 chips, 10/20 blinds (25bb), seat-swapped duplicate deals, aggregate bb/100, unknown mixed-strength opponent bots, top 5 qualify for round 2. Python `Model.seed/run/end_game`, strict 10s decision time, only public GameStateView, no network/file access in submitted code. Design preflop ranges by position and effective stack, 3bet/jam policy, flop-turn-river value/bluff/bet-size choices, and simple opponent exploitation with conservative observation thresholds. What ONE unusual but high-EV exploit might less experienced tournament bots miss? Give precise candidate policy, assumptions, worst opponents and fast tests. Do not give generic 'aggression is good'; do not use an untrained neural model or full solver. You are NOT told the incumbent bot's architecture or results; treat this as a clean-sheet proposal.

### Reviewer output format

1. Concrete hypothesis (one sentence).
2. Mechanism: where chips are gained/lost.
3. Minimal change to test and maximum implementation complexity.
4. Adversary that punishes the idea.
5. Official-engine test to confirm or reject, including failure threshold.
6. Confidence: what was observed vs merely guessed.

When results arrive, compare disagreements and schedule one high-information test. Reviewer opinions are not substitute for game data.
