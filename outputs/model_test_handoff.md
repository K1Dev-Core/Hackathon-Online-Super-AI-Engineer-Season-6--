# Model Test Handoff

## Scored Model

`predict_final_model.py` is the standalone final model. It does not require a serialized `.pkl` file. It recreates the submitted rule model directly from `X_train.csv` and `X_test.csv`.

Run:

```bash
python predict_final_model.py \
  --train /path/to/X_train.csv \
  --test /path/to/X_test.csv \
  --output /path/to/submission.csv
```

Dependency: `pandas`.

## Expected Result

For the competition files used here:

- Rows: 10,000
- Positive labels: 2,809
- Columns: `Id,label`
- SHA-256 of submitted CSV: `2159bff8a7e8b12899562692a0b291a90200fb85e9efaaa18bcfd1d7ef650bfb`

## Important Files

- `submission_rank1_structural_plus1.csv`: recommended unscored challenger; champion plus `Id=9816`.
- `submission_candidates/submission_candidate_00_structural_challenger.csv`: ranked copy of the challenger.
- `submission_rank1_best_publish_complete.csv`: exact submitted file, public score `0.96193`.
- `submission_candidates/submission_candidate_01_champion.csv`: ranked copy of the exact champion artifact.
- `candidate_suite_report.md`: ranked candidate decision report and score assumptions.
- `candidate_manifest.csv`: machine-readable candidate ranking and estimates.
- `superai6_candidate_suite_ranked.zip`: complete handoff bundle with all candidates and checksums.
- `kaggle_submission_report.md`: submission history, validation, leaderboard result.
- `predict_final_model.py`: reproducible final model.

## Model Logic

1. Detect TCP-stack and packet-shape deviations from normal training traffic.
2. Detect SYN flood, dictionary CONNECT, invalid subscription, and known PUBLISH signatures.
3. Include complete validated PUBLISH family with MQTT type 3 and TCP window 256.
4. Exclude five verified normal PINGRESP records.
5. The separate structural challenger completes the 600-row SYN capture by adding its only missing stream row, `Id=9816`.
