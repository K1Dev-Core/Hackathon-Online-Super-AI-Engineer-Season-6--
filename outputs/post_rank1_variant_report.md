# Post-Rank-1 Variant Report

## Decision

`submission_post_rank1_01_current_leader.csv` is the only approved file. It is byte-identical to the
current leader artifact `submission_rank1_structural_plus1.csv`, including the
structural attack row `Id=9816`. It produced the observed public score
`0.96230` and current first-place result. No Kaggle upload was performed here.

No new addition passed the precision gate. This is deliberate: a single public
false positive is large enough to erase the narrow lead. The rejected file is
included solely to make the negative result reproducible; it must not be sent.

## Ranking

| Rank | File | Positives | Status | Observed public score | Action |
|---:|---|---:|---|---:|---|
| 1 | `submission_post_rank1_01_current_leader.csv` | 2810 | `APPROVED_PRIMARY` | 0.96230 | Submit only this file |
| 2 | `submission_post_rank1_02_previous_champion.csv` | 2809 | `FALLBACK_ONLY` | 0.96193 | Do not use for improvement |
| 3 | `submission_post_rank1_03_rejected_payload132.csv` | 2811 | `REJECTED_FALSE_POSITIVE_RISK` | not uploaded | Do not submit |

## New Evidence Audit

- The five available external attack-corpus CSVs were checked using the six
  TCP-core fields shared with the competition data. They matched 422 test rows;
  all 422 are already positive in the current leader, so this audit added no
  safe residual row.
- The SYN source signature is already complete in the leader. The only
  defensible stream-level exception remains `Id=9816`: the sole extra packet in
  the missing SYN stream 194.
- A full same-stream template scan found no additional one-row structural gap.
  The remaining unmatched rows belong to broad normal-capture streams and do
  not support a precision-safe addition.
- `Id=1145` was retained as a falsification control only. Its undecoded
  payload shape has normal stream-2 siblings, so treating it as attack would be
  speculation rather than a score-improving evidence-backed change.

## Integrity

- Leader-lock SHA-256: `fa357be08880f7dbdf32e61052ad01eeae251c8706d2bc077818efaa7d9a73d7`
- Source leader SHA-256: `fa357be08880f7dbdf32e61052ad01eeae251c8706d2bc077818efaa7d9a73d7`
- Leader-lock exact-label match: `True`
- Rows and Id order were validated against `data/X_test.csv` for all three CSVs.
- The archive and `post_rank1_variant_checksums.sha256` contain all handoff
  files needed to verify this result.
