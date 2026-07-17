# Final Offline Validation

## Status

- Exact submission artifact: `submission_rank1_best_publish_complete.csv`
- Latest recorded public score: `0.96193` (tied first place when last checked)
- This validation pass made no additional upload.
- No credential or API token is included in this bundle.

## Reproducibility

`predict_final_model.py` recreates the submission directly from `X_train.csv` and
`X_test.csv`; it does not need a serialized model file.

```bash
python predict_final_model.py \
  --train /path/to/X_train.csv \
  --test /path/to/X_test.csv \
  --output /path/to/submission.csv
```

Expected output for the supplied competition data:

- Rows: `10000`
- Columns: `Id,label`
- Labels: only `0` and `1`
- Positive labels: `2809`
- SHA-256: `2159bff8a7e8b12899562692a0b291a90200fb85e9efaaa18bcfd1d7ef650bfb`

## Rule Audit

The final rule union identifies 2,814 candidate attack rows before applying the
verified exception. The model then removes five `PINGRESP` rows that were
validated as false positives, resulting in 2,809 positive predictions.

| Signal | Matches | New rows added to union |
| --- | ---: | ---: |
| TCP window unseen in normal training data | 2,537 | 2,537 |
| Unseen packet shape, excluding PUBLISH | 2,456 | 154 |
| TCP SYN flood signature | 553 | 0 |
| Dictionary CONNECT signature | 175 | 0 |
| Invalid subscription signature | 94 | 0 |
| PUBLISH signature with MQTT length 19 or 44 | 332 | 97 |
| Validated PUBLISH family with TCP window 256 | 123 | 26 |
| Verified PINGRESP false-positive exclusion | 5 | -5 |

## Competition Boundary

The competition specification requires an individually registered, correctly
named team and limits submissions to five per day. This bundle is finalized for
offline testing and should only be used with the registered competition identity.
