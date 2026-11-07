# Evidence brief — separate verified facts from earlier AI assertions

## A. User-provided CURRENT arena page (7 Nov 2026)

- Heads-up no-limit Texas Hold'em, Python `Model` submitted as pickle and its .py dependencies.
- 10 seconds per decision, engine checks/folds on fault; a bot timing out is out for remainder of match.
- Submissions open 16:00, end 18:00; user explicitly requires all final work and upload done by 17:50 GMT.
- Round 1: every submitted bot faces each other with seat-swapped deals, ranked by bb/100; top five advance. Round 2: the top five play for the championship. £300 prize pot.
- Keep model data/weights in plain serialisable object initialized in `__init__`. No disk/network/engine-internal access in submitted code.
- Official submission site says the newest working uploaded entry is used. Upload `.pkl` plus files listed by `submit`.
- **Single legitimate team entry only**; no sacrificial multi-entry manipulation. Build local adversaries, not tournament fillers.

## B. Public repository verified (organiser README and CLAUDE.md)

- `Model.seed(hand, player_id)` every hand, `run(actions, game_state)`, optional `end_game(actions, game_state)`; same Model retains memory over hands in a seat rotation.
- `GameStateView` allows only the public whitelisted properties in `CLAUDE.md` including `street`, `board`, `button`, `teams`, `stacks`, `bets`, `acted`, `pot`, `call_amount`, `pot_odds`, `can_raise`, `raise_range`, `spr`, and `effective_stack`; never infer another name.
- Default blinds 10/20, starting stacks 500 (25bb); heads-up button = small blind, acts first preflop. Exact default may be overridden by actual match settings; inspect them.
- `PlayerAction.raise_to(player_id, total)` is the TOTAL STREET BET, not raise increment. `PlayerAction.call` also checks. Strict Pydantic validation.
- The dealer's `reveal_card` has player_id -1; showdown hole cards are also `reveal_card` but carry the seat id.
- Official `.venv` tests, evaluation CLI, submission checks; 6 official dummies listed: fold, call, random, shove, tight, equity.
- Official evaluees may use paired duplicate decks and seats swapped; random luck remains. `evals` outputs 95% intervals. The repo code and CLI must be inspected to confirm that candidate-to-candidate measurements are consistent.
- **Document conflict:** the organiser's older maintainer notes describe a one-round tournament; the live page provided by user says TWO rounds. Treat LIVE PAGE as current event authority; repo is code/API authority.

## C. Earlier Claude v4 supplied by user (UNVERIFIED performance)

Three backed-up v4 files: `baseline_v4/model.py`, `baseline_v4/pokerlib.py`, `baseline_v4/preflop_table.py`. The preceding assistant's account says it trained no solver; it used weighted opponent action priors, hand-range selection and Monte Carlo to choose actions. It reportedly beat 13 synthetic opponents in a custom simulator, 112–114 bb/100 aggregate in a comparison versus v3, and max latency ~29ms. These came from a CUSTOM simulator, **not independently official test results**. Do not claim they predict tournament performance.

Inspection of uploaded v4 `_sb_first` shows:
- `ev['open']` uses predicted fold/call/raise action shares and an approximate continuation EV.
- `ev['shove']` uses predicted shove-call share `q`, a preflop equity versus upper hand range, and showdown-stack-sized EV.
- `ev['limp']` similarly uses approximations.
- It then chooses the largest predicted EV. This is a real model-fidelity mismatch risk: shove may look better partly because open-raise branch is evaluated more pessimistically. It is NOT proof of lost chips; isolate by ablation.

Previous ChatGPT messages said v4 shoves roughly 23-27% of starting combos at 25bb in a randomised diagnostic. No official engine validation of this claim is present. Reproduce with exact version, starting conditions and RNG seeds before relying on that number.

Potential other concerns requiring targeted verification: raw showdown equity vs call odds; postflop draw-bluff assumptions; case of opponent action logs and street resets; broad exception handlers that fold/check silently; variable stack and min-raise behavior; independent quality of preflop equity matrix.

## D. Gemini replacement (REJECT AS A TOP-TIER CANDIDATE)

A separate Gemini proposal uses fixed arbitrary preflop strengths and category-level postflop scores, equating scores with probabilities. It lacks correct heads-up positional opening/defence, a calibrated shove response and opponent modelling. Prior audit estimated its button opening folds ~78.4% of possible combos, unacceptably tight against most heads-up opponents. Treat this as an unverified diagnostic and a possible weak opponent archetype only, not a contestant to copy.

## E. Latest independent critique

`PREVIOUS_REVIEW_UNVERIFIED.txt` is a separate AI critique of a previous four-architecture plan. Its important recommendation: preserve v4, test a narrow preflop ablation first, build ONE independent baseline, run diverse official paired matches, freeze in time. It has NOT independently validated code or actual official tournament results.

## F. What is not known

Live opponent populations, opponent source code, final-round seed structure, exact prize-format mechanics beyond the public page, model performance on official engine, and effective time to run hundreds of match pairs. Do not invent these details; inspect official source and log gaps.
