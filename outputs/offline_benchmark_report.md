# Offline Benchmark Report

## Winner

`submission_offline_01_scoremax_structural.csv` ranks first. Same labels as `submission_rank1_structural_plus1.csv`: champion plus `Id=9816`.

Structural probability stress value: `0.995349`. Null coincidence rate comes from one extra standard stream among 215 candidates matching the only missing SYN stream.

## Score Scenarios

- Recorded public champion baseline: `0.96193`
- Champion full-test F1 under 3,000 attacks and zero champion false positives: `0.967120`
- Structural file if `Id=9816` is attack: `0.967298`
- Structural file if `Id=9816` is normal: `0.966954`
- Monte Carlo expected gain over champion: `+0.00017609`
- Public-delta proxy: `0.96210609`; decision heuristic only
- Monte Carlo runs: `20,000`; fixed attack count: `3,000`
- Conservative sensitivity: score-max wins `15/15` scenarios across 2,900-3,100 attacks and structural probability 0.50-0.995349

## Ranked Results

| Rank | File | Positive | Mean F1 | Public proxy | Win vs champion | Win vs score-max | Verdict |
|---:|---|---:|---:|---:|---:|---:|---|
| 1 | `submission_offline_01_scoremax_structural.csv` | 2810 | 0.96729608 | 0.96210609 | 0.9951 | 0.0000 | `SCORE_MAX_WINNER` |
| 2 | `submission_offline_02_hedge_payload132.csv` | 2811 | 0.96716792 | 0.96197793 | 0.9954 | 0.1113 | `CHAMPION_BEATING_BACKUP` |
| 3 | `submission_offline_03_hedge_payload150.csv` | 2811 | 0.96716789 | 0.96197790 | 0.9954 | 0.1112 | `CHAMPION_BEATING_BACKUP` |
| 4 | `submission_offline_04_hedge_rare_ack.csv` | 2811 | 0.96716259 | 0.96197260 | 0.9957 | 0.0958 | `CHAMPION_BEATING_BACKUP` |
| 5 | `submission_offline_05_hedge_stream5_ack.csv` | 2811 | 0.96716204 | 0.96197205 | 0.9958 | 0.0942 | `CHAMPION_BEATING_BACKUP` |
| 6 | `submission_offline_11_champion_control.csv` | 2809 | 0.96711999 | 0.96193000 | 0.0000 | 0.0049 | `CONTROL` |
| 7 | `submission_offline_06_plus_micro3.csv` | 2813 | 0.96691271 | 0.96172272 | 0.2989 | 0.0346 | `LOSES_OFFLINE` |
| 8 | `submission_offline_07_plus_top10.csv` | 2820 | 0.96597768 | 0.96078769 | 0.0017 | 0.0017 | `LOSES_OFFLINE` |
| 9 | `submission_offline_08_plus_context40.csv` | 2850 | 0.96180272 | 0.95661273 | 0.0000 | 0.0000 | `LOSES_OFFLINE` |
| 10 | `submission_offline_09_plus_pu64.csv` | 2874 | 0.95862525 | 0.95343526 | 0.0000 | 0.0000 | `LOSES_OFFLINE` |
| 11 | `submission_offline_10_target3000.csv` | 3000 | 0.94178170 | 0.93659171 | 0.0000 | 0.0000 | `LOSES_OFFLINE` |

## Winner Files

- `submission_offline_01_scoremax_structural.csv`: `SCORE_MAX_WINNER`; primary; mean F1 `0.96729608`
- `submission_offline_02_hedge_payload132.csv`: `CHAMPION_BEATING_BACKUP`; backup only; mean F1 `0.96716792`
- `submission_offline_03_hedge_payload150.csv`: `CHAMPION_BEATING_BACKUP`; backup only; mean F1 `0.96716789`
- `submission_offline_04_hedge_rare_ack.csv`: `CHAMPION_BEATING_BACKUP`; backup only; mean F1 `0.96716259`
- `submission_offline_05_hedge_stream5_ack.csv`: `CHAMPION_BEATING_BACKUP`; backup only; mean F1 `0.96716204`

## Guardrails

- Semi-supervised model rejected: it assigned about 0.99 attack probability to known hard-negative PUBLISH window-253 rows.
- Large residual additions lose because required added precision is about 0.486 and observed residual evidence remains far lower.
- Public-delta proxy transfers only the modeled score difference onto 0.96193; it is not a Kaggle prediction.
- Backup hedges beat the champion expectation but lose to score-max in about 89-91% of simulations.
- Benchmark is offline inference, not Kaggle ground truth.
- No Kaggle submission performed.
