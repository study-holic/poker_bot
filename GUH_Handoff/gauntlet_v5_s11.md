# Gauntlet seed=11 deals=150 (x2 seats per deal)

bb/100 ± 95% CI per opponent (evals duplicate scoring).

| model | tight | equity | call | shove | random | adv_station | adv_maniac | adv_jammer | adv_nit3bet | adv_smallball | v4 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| model:Model | +67.1 ± 31.7 | +148.3 ± 73.0 | +474.5 ± 111.5 | +210.5 ± 143.3 | +172.8 ± 94.3 | +399.0 ± 116.6 | +179.9 ± 122.0 | +21.0 ± 69.5 | +33.6 ± 38.8 | +117.3 ± 53.0 | +0.0 ± 0.0 |
| candidate_v5:Model | +51.8 ± 39.5 | +134.0 ± 79.8 | +463.1 ± 101.3 | +170.8 ± 137.9 | +246.0 ± 93.6 | +380.9 ± 105.2 | +173.0 ± 121.5 | -11.3 ± 64.8 | +62.0 ± 37.2 | +33.1 ± 56.1 | -26.6 ± 55.8 |
| candidate_v5:V4Post | +67.1 ± 31.7 | +148.3 ± 73.0 | +474.5 ± 111.5 | +210.5 ± 143.3 | +172.8 ± 94.3 | +399.0 ± 116.6 | +195.7 ± 121.0 | +21.0 ± 69.5 | +38.3 ± 38.9 | +145.8 ± 50.6 | +25.3 ± 27.5 |
| candidate_preflop:Model | +54.2 ± 32.7 | +125.0 ± 79.7 | +463.1 ± 101.3 | +123.2 ± 140.0 | +248.4 ± 92.6 | +390.8 ± 103.5 | +124.5 ± 125.1 | -3.3 ± 61.6 | +59.5 ± 43.3 | +33.5 ± 59.4 | -33.7 ± 52.3 |

| model | mean bb/100 | ± 95% CI | worst matchup | faults | max latency s | errors | cpu-wall s |
|---|---|---|---|---|---|---|---|
| model:Model | +182.4 | 29.3 | adv_jammer (+21.0) | 0 | 1.27 | 0 | 1041 |
| candidate_v5:Model | +152.4 | 26.3 | v4 (-26.6) | 0 | 1.27 | 0 | 808 |
| candidate_v5:V4Post | +172.6 | 26.7 | adv_jammer (+21.0) | 0 | 1.53 | 0 | 863 |
| candidate_preflop:Model | +144.1 | 26.4 | v4 (-33.7) | 0 | 0.98 | 0 | 480 |

Difference vs model:Model (same seed => same decks; CI below is the conservative unpaired one, sqrt(SE_a^2+SE_b^2)):

| model | mean diff | ± 95% CI (unpaired, conservative) |
|---|---|---|
| candidate_v5:Model | -30.0 | 39.4 |
| candidate_v5:V4Post | -9.8 | 39.6 |
| candidate_preflop:Model | -38.3 | 39.4 |

Total wall time 311s with --jobs 12.
