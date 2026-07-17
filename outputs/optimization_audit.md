# Final Optimization Audit

## Current Position

- Exact submission: `submission_rank1_best_publish_complete.csv`
- Latest public leaderboard score: `0.96193`
- Latest observed position: tied first place; the next score is `0.95934`
- No new submission was made during this audit.

## Revalidation

- Rows: `10000`
- Schema: `Id,label`
- Positive predictions: `2809`
- SHA-256: `2159bff8a7e8b12899562692a0b291a90200fb85e9efaaa18bcfd1d7ef650bfb`
- `predict_final_model.py` regenerates the same prediction deterministically.

## Evidence Review

- `2790` of the `2809` positive rows have a packet-core signature absent from
  the normal training data. The remaining `19` are the validated PUBLISH
  window-256 family.
- CONNECT, SUBSCRIBE/SUBACK, and SYN signatures have no remaining safe
  extension. Their unlabelled variants match normal capture patterns.
- The only PUBLISH families with attack evidence use TCP windows `63`, `256`,
  or `64512`. PUBLISH families with windows `253`, `254`, and `5718-5756`
  are normal-capture families. The broad PUBLISH extension scored `0.91143`,
  so it is explicitly excluded.
- The five `PINGRESP` rows at frame length `56` and window `253` are the only
  confirmed false-positive cluster and are already excluded by the final
  model.
- The `154` packet-shape-only positives were reviewed separately. Apart from
  the excluded PINGRESP cluster, they are consistent TCP/MQTT response shapes
  within the validated attack captures; there is no evidence-supported removal.
- Pseudo-label models fail a held-out check: they rank the verified PINGRESP
  false positives above the later validated PUBLISH additions. Their residual
  rankings are therefore not used.
- The external MQTT reference captures have a material TCP-stack/domain shift
  from the competition data and provide no trustworthy residual candidates.

## Decision

The submitted model is retained unchanged. No candidate group clears the
approximately 48 percent precision needed to improve F1 at the current score,
and changing the prediction would be less reliable than preserving the tied
first-place artifact.
