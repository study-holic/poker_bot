# Experiment log (7 Nov 2026, official engine via `python -m evals`; duplicate seat-swapped deals)

Selected: **v4 + postflop raise cap** (model.py; diff vs frozen v4 = 3 lines: never raise a postflop bet with less than two pair).
Frozen control: branch v4_control (35c8008 / 500b345). Candidates: A_preflop (b7d8b5b), B_indep (9fe80db), C_gauntlet (gauntlet + adversaries).

| Candidate | seed 11 / 150 deals: vs v4 | seed 12 / 300: vs v4 | holdout 777 / 300: vs v4 | field vs v4 control |
|---|---|---|---|---|
| v4 + cap (SELECTED) | +25.3 ± 27.5 | 0.0 ± 0.0 | +11.2 ± 46.2 (clean rerun) | equal or better on 10/10 opps s11; ±10 noise s12/777 |
| A range preflop | -33.7 ± 52.3 | (s12/150: -23.8 ± 48.2) | not run | ~-38 bb/100 mean s11 |
| A preflop + cap + MC | -26.6 ± 55.8 | - | - | ~-30 mean s11 |
| B independent | +11.2 ± 62.5 | - | - | ~-78 mean s11; -57 vs jammer |

Faults: 0 everywhere except 33 in holdout V4Post-vs-v4 under memory/CPU overload (~30 procs, 1.2GB free); clean rerun of the same match: 0 faults.
Final checks: pytest tests/test_model.py 9 passed; `submit --team study-holic` OK; clean-dir unpickle 200 hands 0 faults.
v4 weaknesses (audit D): open-jams ~25% of combos at 25bb (A confirmed, 3 seeds); SB-first decision MC-noisy (n=400);
calls 3-bets on raw equity; worst matchups adv_jammer (+6..+31) and nit3bet. External AI consultations: skipped (time).
