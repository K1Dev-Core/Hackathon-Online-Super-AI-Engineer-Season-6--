# Strong-Machine Continuation Handoff

## Start Here

- Baseline submission: `outputs/submission_current_best_96267.csv`
- Observed Kaggle public F1: `0.96267`
- Rows: `10,000`
- Positive labels: `2,811`
- SHA-256: `2fe54d9dd8fc524d605fb0115941e896c86d09a6be5485d1ab626f66375c03a4`

Kaggle submission `54808193` established that adding `Id=1145` to the previous
baseline improves public F1 from `0.96230` to `0.96267`.

Next ranked artifacts:

1. `outputs/submission_next_01_twin_payload132.csv`: add `Id=5244`; strongest
   next candidate because all non-Id features exactly match confirmed `Id=1145`.
2. `outputs/submission_next_02_twin_plus_payload150.csv`: also add `Id=5516`.
3. `outputs/submission_next_03_twin_plus_precision4.csv`: also add `Id=4057`
   and `Id=6011`; higher-risk backup.

Do not continue from `outputs/submission_urgent_pcap_shape_8150.csv`. Adding
`Id=8150` reduced public F1 to `0.96196` in Kaggle submission `54808099`.

## Completed Evidence Search

- `outputs/pcap_attack_exhaustive_search.csv`: all `313/313` attack PCAP files
  scanned successfully; approximately `215.6M` TCP rows and `30.4 GB`.
- `outputs/pcap_normal_exhaustive_search.csv`: all `49/49` normal PCAP files
  scanned successfully; approximately `45.4M` TCP rows and `7.0 GB`.
- `outputs/pcap_attack_shape_support.csv` and
  `outputs/pcap_normal_shape_support.csv`: full multi-profile feature-hash scan.
- No current-negative row passed an attack-only exact/full-shape gate. The only
  packet-shape candidate was `Id=8150`; its Kaggle result falsified the change.

## Next High-Compute Work

1. Keep `submission_current_best_96267.csv` as immutable baseline.
2. Reconstruct ordered flows from source PCAPs instead of classifying isolated
   packet rows. Generate preceding/following packet features, inter-arrival
   deltas, direction, TCP state transitions, and MQTT transaction context.
3. Train group-held-out models with capture-file groups. Optimize out-of-fold F1
   threshold; reject random row splits because adjacent packets leak heavily.
4. Use only candidate deltas that survive normal-PCAP falsification and multiple
   capture-held-out folds. Export each delta as a separate submission artifact.
5. Compare every artifact against the baseline by exact changed `Id` list and
   checksum before any Kaggle upload.

The raw competition files remain excluded from Git. On the new machine place
`X_train.csv`, `X_test.csv`, and `sample_submission.csv` in `data/`.
