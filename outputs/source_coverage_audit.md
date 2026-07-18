# Source Coverage Audit

## Input

- Submission: `submission_rank1_structural_plus1.csv`
- Submission SHA256: `fa357be08880f7dbdf32e61052ad01eeae251c8706d2bc077818efaa7d9a73d7`
- Positive labels: `2810`
- Match key: frame length, TCP stream, RTT rounded to 6 decimals, TCP length, window, SYN, RST, ACK.

## Result

- Exact source/test union: `229` rows.
- Already labeled attack: `229` rows.
- Candidate additions: `0` rows.
- Decision: No source-supported additions were found.

## Per Source

| source_csv | source_rows | exact_test_matches | matched_current_attack | matched_current_normal |
| --- | --- | --- | --- | --- |
| BF1_DDoS_AD_1.csv | 314979 | 214 | 214 | 0 |
| BF1_DoS_AD_12.csv | 306918 | 215 | 215 | 0 |
| Delay_DDoS_AD_1.csv | 309554 | 211 | 211 | 0 |
| Delay_DoS_AD_11.csv | 291988 | 214 | 214 | 0 |
| SYN_DDoS-AD_1.csv | 497611 | 210 | 210 | 0 |
| SYN_DoS_AD_1.csv | 103828 | 216 | 216 | 0 |
| Sub_DDoS_AD_1.csv | 181190 | 215 | 215 | 0 |
| Sub_DoS_AD_11.csv | 109150 | 207 | 207 | 0 |
| WILL_DDoS_AD_1.csv | 156055 | 220 | 220 | 0 |
| WILL_DoS_AD_11.csv | 114474 | 216 | 216 | 0 |
| UNION | 2385747 | 229 | 229 | 0 |

This audit is evidence for precision only. It does not estimate Kaggle score and does not upload a submission.
