# Gauntlet seed=11 deals=150 (x2 seats per deal)

bb/100 ± 95% CI per opponent (evals duplicate scoring).

| model | tight | equity | call | shove | random | adv_station | adv_maniac | adv_jammer | adv_nit3bet | adv_smallball | v4 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| candidate_independent:Model | +64.3 ± 25.1 | +117.6 ± 68.7 | +274.4 ± 83.5 | +192.8 ± 147.6 | +100.1 ± 79.6 | +256.8 ± 85.9 | +145.5 ± 121.5 | -57.2 ± 74.4 | +23.8 ± 15.5 | +20.6 ± 48.0 | +11.2 ± 62.5 |

| model | mean bb/100 | ± 95% CI | worst matchup | faults | max latency s | errors | cpu-wall s |
|---|---|---|---|---|---|---|---|
| candidate_independent:Model | +104.5 | 24.8 | adv_jammer (-57.2) | 0 | 0.23 | 0 | 140 |

Total wall time 59s with --jobs 6.
