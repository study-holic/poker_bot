# Subagent guardrails and contracts

## Coordinator

Own the hard deadline, isolate worktrees, merge only tested code, make Git commits and pushes, package clean submission, and verify Google Form status. Every 10-15 minutes update user with actual evidence, never filler.

## 1 Preflop ablation (reads v4)

Output: `candidate_preflop.py` and short `reports/preflop_ablation.md` with opening-shove frequencies by default stacks and several alternative q priors, list of hands affected, and seeded official-engine comparison. Do not rewrite postflop, or change unrelated RNG/equity samples between comparison arms.

## 2 Blind independent baseline (no v4 code until candidate frozen)

Output: `candidate_independent.py`, optionally a flat `independent_tables.py`, and `reports/independent.md`. Cover button first action, BB facing limp/raise, preflop all-in, flop betting, river value and bluff, min-raise legalities, state reset and serialize. Use public fields only. Do not assume hand category equals win probability.

## 3 Adversarial tests / statistics

Output: `reports/benchmark.md` and CSV; test adversaries kept developer-side, not shipped as dependencies. Match all candidates under same seeds and opponents, report confidence intervals, faults, and worst opponent. Protect a fresh holdout and disclose whether it was peeked at.

## 4 Read-only bug hunter

Output: `reports/code_audit.md` with severity, exact file:line, example state and reproducible failure/falsifier; do NOT edit candidates. Make an early critical-fault announcement as soon as evidence exists.

All subagents: no protected engine changes, no files/network inside contestant model, no contest score manipulation or extra submission accounts, no force push, no deleting uncommitted work, no fabricated numbers, no installing giant packages under time pressure.
