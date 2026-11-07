# High-information testing protocol (developer-side only)

Main objective: select *one* competition-eligible model before 17:50 GMT, not produce an unreliable leaderboard of hundreds of variants.

## Candidates

- **CONTROL_V4**: exact user-provided code, frozen and validated separately; keep its hash.
- **V4_PREFLOP**: v4 postflop unchanged, only position/stack-aware preflop logic modified; test it as a clean ablation.
- **INDEPENDENT**: new conceptual starting-point policy, no access to v4 thresholds until first implementation tested.

Optional, ONLY after shortlist: a bounded exploit layer on strongest verified fixed model. Do not allocate time to full solver/CFR/RL training.

## Opponents and sample independence

Use official `fold`, `call`, `random`, `shove`, `tight`, `equity` as a basic checkpoint. Add a small separate adversarial set: tight calling range, loose/passive station, big 3bet pressure, wide button open + small c-bet, conservative equity. Do not make every adversary an approximate clone of v4. Avoid hand-picked seed stories.

Use same officially supported paired duplicate deals and same opponent set for each candidate. Separate development seeds from held-out final seeds. Repeated evals on same seeds can still be overfit; do not select hundreds of models by one leaderboard. Evaluate each candidate's worst-opponent matchup as well as mean.

Target if speed permits:
- smoke 100–150 paired deals (fault detection, coarse loss);
- screening 300–500 paired deals across diverse opponents (only large differences matter);
- fresh finalist 1,000+ paired deals (uncertainty still matters).

Do not call a 10–20 bb/100 lead 'significant' from a few hundred hands. Report CIs with units and analysis method. If CLI emits intervals, report them verbatim; if paired bootstrap is implemented, bootstrap duplicate DEAL units and keep paired correlations, not isolated actions/turns. A wide CI is informative uncertainty.

## Official commands (verify actual CLI help first)

Linux/macOS: `.venv/bin/python`; Windows: `.venv\Scripts\python.exe`.

```
python -m pytest tests/test_model.py -q
python -m evals --model candidate_preflop:Model --opponents tight equity call shove random --deals 300 --table
python -m evals --model candidate_independent:Model --opponents tight equity call shove random --deals 300 --table
python -m submit --team YOUR_ACTUAL_TEAM_NAME
```

IMPORTANT: `submit` imports `model.Model`, not arbitrary `candidate_*.Model`. In staging copy the chosen verified candidate to root `model.py` and make all imports flat and deployable, then rerun the official tests and `submit`. If using a model variant that relies on renamed module, confirm pickled class references and manifest. Test the generated pickle in a clean working directory before upload. Make sure saved .py and .pkl match exactly.

For testing candidate against incumbent, `evals --opponents` can accept a pickled model path according to official docs. Build a valid v4 pickle and include it, rather than comparing candidate only to dummies. The frozen original is a control, not automatically the final submission.

## Required record per experiment

Candidate module, commit SHA/hash, seed or repeat setting, opponent, deals, paired rotations, bb/100, interval, crashes/illegal actions/timeouts, max walltime, run commands, elapsed duration, and notable losing sequences. Use `RESULTS_TEMPLATE.csv`.

## Reject criteria and safety

- Model touches protected API, uses prohibited operations, incorrect serialization, raises outside legal range, fails clean worker validation, or times out: reject until fixed.
- Unsupported statistical conclusion: not a reason to switch.
- Great results against fold bot and poor results versus legitimate tight/equity/shove opponents: reject or diagnose, don't hide via aggregate mean.
- Excessive local opponent tuning without holdout: discount likely overfit.
- At 17:35 freeze: one proven model, no more strategic changes.
