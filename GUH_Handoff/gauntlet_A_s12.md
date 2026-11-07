# Gauntlet seed=12 deals=150 (x2 seats per deal)

bb/100 ± 95% CI per opponent (evals duplicate scoring).

| model | tight | equity | call | shove | random | adv_station | adv_maniac | adv_jammer | adv_nit3bet | adv_smallball | v4 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| model:Model | +60.1 ± 31.9 | +158.8 ± 77.8 | +316.1 ± 107.1 | +24.7 ± 142.9 | +155.4 ± 106.8 | +317.4 ± 104.5 | +80.4 ± 107.0 | +6.8 ± 62.9 | +63.5 ± 35.0 | +39.5 ± 50.1 | +0.0 ± 0.0 |
| candidate_preflop:Model | +71.9 ± 38.2 | +236.9 ± 85.7 | +379.1 ± 97.8 | +53.6 ± 136.3 | +191.3 ± 108.0 | +343.8 ± 99.5 | +27.8 ± 113.5 | -20.1 ± 61.6 | +50.8 ± 43.8 | +97.2 ± 55.0 | -23.8 ± 48.2 |

| model | mean bb/100 | ± 95% CI | worst matchup | faults | max latency s | errors | cpu-wall s |
|---|---|---|---|---|---|---|---|
| model:Model | +122.3 | 28.4 | adv_jammer (+6.8) | 0 | 0.80 | 0 | 880 |
| candidate_preflop:Model | +128.0 | 26.1 | v4 (-23.8) | 0 | 0.93 | 0 | 770 |

Difference vs model:Model (same seed => same decks; CI below is the conservative unpaired one, sqrt(SE_a^2+SE_b^2)):

| model | mean diff | ± 95% CI (unpaired, conservative) |
|---|---|---|
| candidate_preflop:Model | +5.8 | 38.5 |

Total wall time 198s with --jobs 11.
