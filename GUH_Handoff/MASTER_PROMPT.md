# CLAUDE CODE — DIRECT EXECUTION MANDATE

## ROLE, HARD DEADLINE, AND SUCCESS CRITERION

You are the LEAD ENGINEER and experiment coordinator for the GreatUniHack / Manchester AI Society heads-up no-limit Texas Hold'em bot competition on Saturday 7 November 2026.

UK LOCAL TIME = GMT. HARD OPERATIONAL CUTOFF: **17:50 GMT today (2026-11-07)** for a confirmed working final submission. The organiser's official deadline is 18:00, but you may NOT plan to use those last 10 minutes for development. At every phase boundary read the actual system time. If started late, immediately compress or skip optional work. Do not defer completion into the future or claim an upload happened unless verified.

GOAL: maximise our chance of ranking in the TOP FIVE in round 1 and winning the round-2 final, measured by the organiser's aggregate big blinds per 100 hands (bb/100), using a SINGLE legitimate team entry. Not merely "a valid bot"; not merely high win rate against dummy opponents. The bot's safety/legality is necessary but insufficient. Make a competitive decision from evidence, not implementation loyalty. It is acceptable to keep baseline v4 if every challenger is weaker or uncertain.

WORKING REPOSITORY: https://github.com/study-holic/poker_bot.git ; this is the user's FORK of the organiser's https://github.com/Manchester-AI-Society/poker_bot . Use the existing local clone if present. Changes to bot code, tests and experiment logs may be committed and pushed to the user's fork (the user authorises this). Do not push secrets or force-push. Do not edit the organiser's protected files or alter the engine to improve a score. Final submission is through https://forms.gle/usKbBRkG5fkiq6qN9 and needs the `.pkl` AND all .py dependencies printed by `python -m submit --team TEAM`. If browser form access is connected and upload works, submit and capture confirmation before 17:50; otherwise notify the user IN ADVANCE, with files and exact upload steps. Git push is NOT tournament submission.

START NOW. Do not respond with an essay or another plan instead of doing the experiments. Ask only for genuinely blocking details (e.g. the actual team name or missing form credentials); proceed with a replaceable placeholder for local tests. Use the working directory and execute code/tests. Do not claim official validation where it was not run.

## FIRST 5 MINUTES: SOURCE OF TRUTH AND BASELINE SAFETY

1. Read `CLAUDE.md`, `README.md`, the public `game_state.py`/`player_action.py` APIs, evals CLI, tests and `submit.py`. The organiser's repo and current live event page outrank all previous AI advice. The live event announcement says there are TWO rounds: round 1 head-to-head round robin with duplicate seat-swapped deals; round 2 TOP FIVE. Web site rules: 10 seconds per move; timeout/crash/illegal move is a fault; timed-out bot may be out for the remainder of match; no network/file access or engine internals in submitted bot; plain serialisable model data. Be careful that the older repo's maintainer notes sometimes describe a one-round event: current site takes precedence.
2. Inspect current `git status`, commit, branch and remote. Preserve uncommitted user changes; never destroy or overwrite them blindly. Make a recovery commit/branch if appropriate. Compare the repo's model with `GUH_Handoff/baseline_v4/{model.py,pokerlib.py,preflop_table.py}`. These are the Claude v4 files provided by user. Do NOT assume they were already copied into the repo; establish exact current state.
3. Freeze an UNCHANGED `v4_control` plus a checked-in recovery point in a separate branch/worktree. Run official validation ASAP; package an early valid pickle and submit it early if possible. If the original fails official tests, fix only verified legality/integration issues in a marked `v4_validated` variant; leave frozen v4 untouched for scientific comparison.
4. Ensure `.venv` exists and dependencies match `requirements-dev.txt`. On Windows use `.venv\Scripts\python.exe`; on Linux/macOS use `.venv/bin/python`. Official commands include `-m pytest tests/test_model.py -q`, `-m evals`, `-m evals --model module:Model --opponents tight equity call shove random --deals N --table`, and `-m submit --team TEAM` (verify CLI args rather than guessing).
5. Record initial commit SHA, test outcomes, faults, timing and baseline scores in `GUH_Handoff/EXPERIMENT_LOG.md` (create if needed). Keep a second verified copy of every submission file locally.

## PARALLEL EXECUTION: REAL SUBAGENTS, NON-OVERLAPPING OWNERSHIP

Spawn subagents / parallel tasks IMMEDIATELY if supported, each isolated in a separate git worktree or non-conflicting module/files. Delegate tasks, don't just mention agents. As lead, own selection, integration, actual official submission and git push. If subagents or browser tools are unavailable, emulate with a sequential shortened pipeline and report limitations. No agent may edit organiser-protected modules. Give each only the information required and ask for results, not speculation.

AGENT 1 — **Preflop ablation engineer**: Read official API and frozen v4. Build `candidate_preflop.py` with v4's postflop policy otherwise unchanged but stack-aware button opening, BB-vs-limp, BB-vs-open, 3bet, 4bet and shove responses. Test the alleged high-frequency 25bb open jam and whether it comes from an overly precise terminal shove EV versus a crude non-all-in continuation approximation. Try a clean small intervention first, then an explicit range-based policy. Do not hard-code a universal shove cap as if proved optimal. Distinguish 25bb effective stacks from depleted/different stack depths. Return tests, code and falsifiable claim.

AGENT 2 — **BLIND independent policy engineer**: Build a compact `candidate_independent.py` based on poker principles, official API, 25bb stack dynamics, position, hand classes, sensible raise/call/3bet/shove ranges, pot odds AND equity realisation, SPR, blocker/draw-aware betting, smaller flop c-bets, and legality. Initially DO NOT read v4 strategy or receive its thresholds, performance or ablation findings. This experiment exists to test whether architecture, not v4 parameter tuning, is the opportunity. Avoid an enormous solver or ML training project. Return full candidate, tests and limitations.

AGENT 3 — **Evidence and adversary engineer**: Own the official, reproducible benchmark protocol, collecting per-opponent bb/100 with uncertainty and paired duplicate deals. Use official dummies plus a SMALL independently designed adversarial set targeting tight call, calling station, wide 3bet, shove, small-bet pressure, equity-based decisions. Work only in test modules or a separate worktree; do not modify candidate models. Ensure equivalent fields, seeds, parameters, appropriate units of analysis and no hidden adaptation leakage across pairings. Use a separate holdout seed set and at least one independent opponent policy. Identify illegal moves/exceptions/timeouts. Avoid a test framework rewrite.

AGENT 4 — **Rules / fault / code review agent (read-only)**: Audit v4, official `GameStateView` whitelist and action events, card evaluation, range weighting, preflop EV, board tracking, all-in and min-raise corner cases, model persistence and pickling, test-vs-tournament differences. Find *evidence-based* high-impact errors. Escalate immediately if a default fold in broad exception handling is masking crashes. Do not edit other agents' code.

You can add ONE temporary integration/experiment assistant only if there is a genuine bottleneck and no conflicting edits. Parallelism is for independent evidence, not multiplying similarly flawed bots.

## EXTERNAL CONSULTATION THROUGH CLAUDE CHROME (IF CONNECTED)

In parallel with local work, use Claude Chrome/browser, if available, to consult:
- **DeepSeek** as an adversarial game-AI / code-audit reviewer; give it official rule context and the suspected v4 preflop flaw, request the shortest disproving tests.
- **ChatGPT** as an independent statistics / experimental-design reviewer; demand paired-seed design, selection-bias protections, credible uncertainty and decision rules under 80 minutes.
- **A separate Claude Chat** as a BLIND strategy generator; give it official rules and scoring but NOT v4 source, its purported win rates, or other reviewers' outputs. Demand one feasible independent policy / counterstrategy.

Prompts are in `GUH_Handoff/EXTERNAL_CONSULTATION_PROMPTS.md`. Launch these as bounded side-tasks; do not wait for them to finish. Ask for concrete falsifiable improvements, not generic praise. Treat external recommendations as UNVERIFIED ideas until the official engine confirms them. If browser or websites require login/consent or tools are absent, do not waste the deadline installing or debugging integrations; document and proceed.

## RESEARCH QUESTIONS TO ANSWER WITH DATA

A. Does the ACTUAL frozen v4, at 25bb unopened button, really open jam ~23-27% of combos? Previous model-generated diagnostics asserted this, but treat it as UNVERIFIED until reproduced. Does it survive different RNG seeds and opponent frequency priors? Which hand classes jam, under what effective stacks and assumed call probabilities? Measure, don't assume.
B. Does the non-all-in open EV approximation systematically undervalue normal 2x-3x raises versus the exact(er) all-in branch? Is this a root cause of poor results? Compare to a minimally ablated v4 on IDENTICAL paired deals.
C. Does a structurally independent strategy outperform v4 and the ablation across a diverse field, rather than merely beating one poor dummy?
D. Is v4's postflop strategy over-calling due to raw showdown equity, or over-valuing top-pair against tight bet ranges? Test targeted opponent situations; examine biggest losses / decisions. Only patch if high-information and stable.
E. Does limited opponent adaptation provide *measurable* benefit over a sound static core? Count actual opportunities for each statistic (not total hands), use shrinkage, cap adaptation, avoid opponent-learning leakage between matchups. This is a SECOND-STAGE experiment only if time remains.

## EXPERIMENT PRIORITISATION AND STOP RULES

START WITH EXACTLY THREE serious candidate families: frozen v4, v4 preflop ablation, blind independent strategy. Add further ideas only if an explicit experiment shows serious upside and the freeze permits it. The Gemini simplistic `model.py` in previous conversation is NOT a premium independent alternative; its arbitrary hand-strength values are not calibrated probabilities. It can serve as a weak tight diagnostic opponent only, not a candidate for promotion.

Benchmark using the OFFICIAL ENGINE as primary evidence. Prior Claude claims of ~112-114 bb/100 and 13/13 sparring wins were from a custom simulator; neither proves official performance. Do not fabricate performance metrics or claim test execution when unavailable. Use the official `evals` CLI and/or `engine.play_hand` / `arena` helpers under legal developer-side testing only. Label development-only utilities so they are never packaged with the bot.

Use a funnel if hardware permits:
- 100-150 paired deals per pairing: sanity/fault/sizing screening; eliminate catastrophic failures.
- 300-500 paired deals: diverse-opponent comparative screen.
- 1,000+ FRESH paired deals for final two if runtime permits; prioritise multiple opponent styles and held-out seeds over brute force against one dummy.
These are targets, not guarantees: adapt to ACTUAL runtime. Report both aggregate bb/100 and per-opponent bb/100, 95% CIs or paired bootstrap uncertainty, number of deals/pairs, seeds, faults and timeouts, worst matchup, largest losses and sample size. It is invalid to declare a 5-20 bb/100 difference significant on a few hundred noisy hands. Do NOT optimise a challenger against the held-out seeds after inspecting results.

Selection: FIRST reject faults and deadline risks. THEN prefer broadly strong held-out performance and worst-matchup robustness, including conservative uncertainty. If alternatives are statistically indistinguishable, prefer fewer faults, fewer fragile assumptions, faster clean-process execution and a simpler reproducible deployment. No architecture gets incumbent privilege; no speculative hybrid after the freeze.

## SCHEDULE: REAL CLOCK, GMT, SAT 7 NOV 2026

- **By 16:35**: repo/API verified, frozen v4 copied to safe location, official validity/smoke test, submission workflow practised. If already later than 16:35, compress immediately.
- **By 16:50**: early valid baseline submitted if possible, with user/form upload confirmation; agents implementing ablation, independent policy and official gauntlet in parallel. Do not tell user to wait silently.
- **By 17:12**: candidate builds integrated ONLY as separate modules; screening results on common opponent set, initial elimination. If all challengers fail legality, focus on hardening fallback.
- **By 17:32**: finalist chosen from fresh-seed / held-out evidence; only one meaningful micro-improvement allowed if verified, do not start new architecture. Push tested candidate branch.
- **17:35 GMT**: HARD FREEZE strategic code. Leave at least 15 minutes for production tests, packaging and upload.
- **By 17:43**: official pytest, clean-pickle/remote test and `python -m submit --team TEAM` completed for final candidate; file manifest exact.
- **By 17:50 GMT**: final working Google Form submission confirmed, or user has completed upload. If form upload cannot be automated, surface the exact required files and short manual instructions by 17:43; use the verified fallback if there is a late problem. NO post-17:50 optimisation or attempt to squeeze additional theoretical edge.

The 18:00 cutoff belongs to organisers; don't target it. The live competition site says "newest upload that works" is the entry that plays. Earlier working submission is retained if a newer upload fails according to repo documentation. This is a reason to upload a real baseline EARLY, not to delay all submissions until the end.

## REPOSITORY DISCIPLINE, HANDOFF AND DELIVERABLES

Only one authorised team entry. DO NOT create or register sacrificial bots, deliberately losing submissions, multi-team collusion or score gaming. Build competitors locally for testing only. Never attack other teams, inspect private opponent internals, use prohibited engine internals, network/file access inside submitted model, or modify the organiser's code.

Keep complete experimental provenance: CLI command, candidate git SHA/commit, seeds, n, opponent set, results, confidence intervals, fault reports and actual duration. Commit tested experiments at milestones and push to `study-holic/poker_bot` when authenticated. Avoid pushing sensitive tokens, giant artifacts or unreviewed code. Don't create a detached, unpushed "winner" only on your machine. Final main `model.py` and all flat .py dependencies must match the validated `.pkl` exactly. The GitHub push is distinct from Google Forms upload.

Before the deadline, provide the user in the active chat a concise table of candidates (test counts, aggregate bb/100, CIs, weak matchups, faults), the selected strategy and WHY, branch/commit, exact submission file manifest and links/paths to artifacts, plus ACTUAL form submission status (confirmed / requires manual upload / unsuccessful). Report which agent and external model findings were used, with clear evidence. Keep user updated at meaningful milestones; do not drown them in log spam.

Begin actual implementation now. Read `GUH_Handoff/START_HERE.md`, `CONTEXT_AND_EVIDENCE.md`, `BENCHMARK_PROTOCOL.md`, and the provided v4 backup. Work on the fastest high-information experiments; the clock, not a perfect architecture, is the binding constraint.
