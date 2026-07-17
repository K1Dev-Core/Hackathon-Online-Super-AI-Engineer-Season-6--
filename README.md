# SuperAI6 IoT Attack Detection

Reproducible solution for the Super AI Engineer Season 6 IoT attack detection competition. The final rule model reached a public leaderboard score of **0.96193** and was tied for first place when last verified on 2026-07-18.

## Final Artifacts

- `outputs/predict_final_model.py`: standalone deterministic inference script.
- `outputs/submission_rank1_best_publish_complete.csv`: exact scored submission.
- `outputs/rank1_model_bundle_audited.zip`: portable audited model bundle.
- `outputs/optimization_audit.md`: final evidence and optimization audit.
- `outputs/kaggle_submission_report.md`: submission history and recorded scores.

## Reproduce

Python 3.10 or newer is recommended.

```bash
python -m pip install -r requirements.txt
python outputs/predict_final_model.py \
  --train data/X_train.csv \
  --test data/X_test.csv \
  --output outputs/submission_reproduced.csv
shasum -a 256 outputs/submission_reproduced.csv
```

Expected result for the original competition files:

- Rows: `10000`
- Positive predictions: `2809`
- SHA-256: `2159bff8a7e8b12899562692a0b291a90200fb85e9efaaa18bcfd1d7ef650bfb`

## Data

Competition datasets are intentionally excluded from Git. Place `X_train.csv`, `X_test.csv`, and `sample_submission.csv` in `data/` before running the scripts. No Kaggle or GitHub credential is stored in this repository.

## Layout

- `outputs/`: final predictor, submissions, reports, and audited bundle.
- `work/`: analysis, probe construction, and validation scripts.
- `data/`: local competition files; ignored by Git.
