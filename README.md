# SuperAI6 IoT Attack Detection

Reproducible solution for the Super AI Engineer Season 6 IoT attack detection competition. The strongest recorded submission currently has public F1 **0.96267**.

## Final Artifacts

- `docs/SuperAI6_IoT_Attack_Detection_Design_Report_TH.docx`: Thai Design Report built from retained Design Report template.
- `docs/SuperAI6_IoT_Attack_Detection_Design_Report_TH.pdf`: rendered Design Report with Thai glyph support.
- `docs/SuperAI6_IoT_Attack_Detection_Report_TH.pdf`: detailed Thai technical report.
- `presentation/SuperAI6_IoT_Attack_Detection_Presentation_TH.pptx`: 17-slide Thai presentation with speaker notes.
- `presentation/SuperAI6_IoT_Attack_Detection_Presentation_TH.pdf`: presentation-ready PDF export.
- `outputs/predict_final_model.py`: standalone deterministic inference script.
- `outputs/submission_current_best_96267.csv`: exact strongest scored submission.
- `outputs/submission_next_01_twin_payload132.csv`: highest-confidence next submission candidate.
- `outputs/submission_rank1_best_publish_complete.csv`: exact scored submission.
- `outputs/rank1_model_bundle_audited.zip`: portable audited model bundle.
- `outputs/offline_benchmark_candidates/submission_offline_01_scoremax_structural.csv`: highest-ranked unsubmitted challenger.
- `outputs/offline_benchmark_report.md`: 20,000-run ranking and sensitivity report.
- `outputs/strong_machine_handoff.md`: current baseline, rejected probe, completed PCAP scans, and next high-compute work.
- `outputs/superai6_offline_benchmark_bundle.zip`: all 11 offline variants, winner list, checksums, and benchmark source.
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
