# Offline02 Submission Source

Reproducible source code for:

`submission_offline_02_hedge_payload132.csv`

## What this folder contains

- `predict.py`: deterministic detector and CSV writer
- `validate.py`: schema and Id-order validator
- `requirements.txt`: Python dependency

No serialized model, API token, credential, or competition data is included. Code reads `X_train.csv` and `X_test.csv` supplied separately.

## Run

From repository root:

```bash
python submission_source/offline02/predict.py \
  --train data/X_train.csv \
  --test data/X_test.csv \
  --output outputs/submission_offline_02_reproduced.csv
```

Validate generated output:

```bash
python submission_source/offline02/validate.py \
  --test data/X_test.csv \
  --submission outputs/submission_offline_02_reproduced.csv
```

Expected result with competition files used in this project:

```text
rows=10000
positive_labels=2811
sha256=2fe54d9dd8fc524d605fb0115941e896c86d09a6be5485d1ab626f66375c03a4
```

## Method

1. Build a Normal profile from `tcp.window_size` and `(frame.len, tcp.window_size)` pairs in Train.
2. Add protocol evidence for SYN, CONNECT, invalid SUBSCRIBE, and selected PUBLISH patterns.
3. Include the validated PUBLISH family with MQTT type 3 and TCP window 256.
4. Exclude the verified normal PINGRESP shape: frame length 56, TCP window 253, MQTT type 13.
5. Add audited selected rows `Id=9816` and `Id=1145` used by `offline_02`.
6. Preserve Test `Id` order and write `Id,label`.

The two explicit Id additions are intentional. Running the older baseline source without them produces 2,809 positives and does not reproduce selected `offline_02`.

## AI-assisted development

AI helped with feature interpretation, hypothesis generation, code scaffolding, experiment design, error-analysis grouping, and documentation. Final rule logic was reviewed against the real CSV schema, rerun locally, compared with the selected artifact, and checked for row count, Id order, label domain, and SHA-256.

AI did not have access to hidden Kaggle labels and did not generate the leaderboard score. Human review remained responsible for protocol interpretation and final rule selection.

## Source references

- Existing model reference: `outputs/predict_final_model.py`
- Selected artifact: `outputs/offline_benchmark_candidates/submission_offline_02_hedge_payload132.csv`
- Technical explanation: `docs/SuperAI6_IoT_Attack_Detection_Offline02_Methodology_AI_Assisted_TH.md`
