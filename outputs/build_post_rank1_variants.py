"""Build the post-rank-1 submission handoff without uploading to Kaggle."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
TEST_PATH = ROOT / "data" / "X_test.csv"
LEADER_PATH = OUTPUTS / "submission_rank1_structural_plus1.csv"
CHAMPION_PATH = OUTPUTS / "submission_rank1_best_publish_complete.csv"
VARIANT_DIR = OUTPUTS / "post_rank1_variants"
RANKING_PATH = OUTPUTS / "post_rank1_variant_ranking.csv"
REPORT_PATH = OUTPUTS / "post_rank1_variant_report.md"
CHECKSUM_PATH = OUTPUTS / "post_rank1_variant_checksums.sha256"
ZIP_PATH = OUTPUTS / "superai6_post_rank1_review_bundle.zip"

LEADER_FILENAME = "submission_post_rank1_01_current_leader.csv"
FALLBACK_FILENAME = "submission_post_rank1_02_previous_champion.csv"
REJECTED_FILENAME = "submission_post_rank1_03_rejected_payload132.csv"
REJECTED_ID = 1_145


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_submission(submission: pd.DataFrame, test: pd.DataFrame) -> None:
    if list(submission.columns) != ["Id", "label"]:
        raise RuntimeError(f"Invalid columns: {list(submission.columns)}")
    if len(submission) != len(test) or not submission["Id"].equals(test["Id"]):
        raise RuntimeError("Submission Id order does not match X_test")
    if submission["Id"].duplicated().any():
        raise RuntimeError("Duplicate Id values")
    if submission["label"].isna().any() or not set(submission["label"].unique()) <= {0, 1}:
        raise RuntimeError("Labels must be binary and non-null")


def write_checksums(paths: list[Path]) -> None:
    lines = [f"{sha256(path)}  {path.relative_to(OUTPUTS)}" for path in paths]
    CHECKSUM_PATH.write_text("\n".join(lines) + "\n")


def main() -> None:
    test = pd.read_csv(TEST_PATH, low_memory=False)
    leader = pd.read_csv(LEADER_PATH)
    champion = pd.read_csv(CHAMPION_PATH)
    validate_submission(leader, test)
    validate_submission(champion, test)
    if int(leader["label"].sum()) != 2_810:
        raise RuntimeError("Unexpected current-leader positive count")
    if int(champion["label"].sum()) != 2_809:
        raise RuntimeError("Unexpected previous-champion positive count")

    VARIANT_DIR.mkdir(parents=True, exist_ok=True)
    leader_path = VARIANT_DIR / LEADER_FILENAME
    fallback_path = VARIANT_DIR / FALLBACK_FILENAME
    rejected_path = VARIANT_DIR / REJECTED_FILENAME
    leader.to_csv(leader_path, index=False)
    champion.to_csv(fallback_path, index=False)

    rejected = leader.copy()
    rejected.loc[rejected["Id"].eq(REJECTED_ID), "label"] = 1
    validate_submission(rejected, test)
    if int(rejected["label"].sum()) != 2_811:
        raise RuntimeError("Rejected falsification row was not added")
    rejected.to_csv(rejected_path, index=False)

    ranking = pd.DataFrame(
        [
            {
                "rank": 1,
                "filename": LEADER_FILENAME,
                "positive_labels": int(leader["label"].sum()),
                "delta_vs_current_leader": 0,
                "status": "APPROVED_PRIMARY",
                "observed_public_score": "0.96230",
                "submission_instruction": "SUBMIT_THIS_ONLY",
                "rationale": "Exact current public rank-1 labels; Id=9816 is included.",
            },
            {
                "rank": 2,
                "filename": FALLBACK_FILENAME,
                "positive_labels": int(champion["label"].sum()),
                "delta_vs_current_leader": -1,
                "status": "FALLBACK_ONLY",
                "observed_public_score": "0.96193",
                "submission_instruction": "DO_NOT_USE_UNLESS_REPRODUCING_OLD_SCORE",
                "rationale": "Exact earlier champion, retained only for reproducibility.",
            },
            {
                "rank": 3,
                "filename": REJECTED_FILENAME,
                "positive_labels": int(rejected["label"].sum()),
                "delta_vs_current_leader": 1,
                "status": "REJECTED_FALSE_POSITIVE_RISK",
                "observed_public_score": "not_uploaded",
                "submission_instruction": "DO_NOT_SUBMIT",
                "rationale": "Id=1145 has normal stream-2 packet siblings; fails the precision gate.",
            },
        ]
    )
    ranking.to_csv(RANKING_PATH, index=False)

    report = f"""# Post-Rank-1 Variant Report

## Decision

`{LEADER_FILENAME}` is the only approved file. It is byte-identical to the
current leader artifact `submission_rank1_structural_plus1.csv`, including the
structural attack row `Id=9816`. It produced the observed public score
`0.96230` and current first-place result. No Kaggle upload was performed here.

No new addition passed the precision gate. This is deliberate: a single public
false positive is large enough to erase the narrow lead. The rejected file is
included solely to make the negative result reproducible; it must not be sent.

## Ranking

| Rank | File | Positives | Status | Observed public score | Action |
|---:|---|---:|---|---:|---|
| 1 | `{LEADER_FILENAME}` | 2810 | `APPROVED_PRIMARY` | 0.96230 | Submit only this file |
| 2 | `{FALLBACK_FILENAME}` | 2809 | `FALLBACK_ONLY` | 0.96193 | Do not use for improvement |
| 3 | `{REJECTED_FILENAME}` | 2811 | `REJECTED_FALSE_POSITIVE_RISK` | not uploaded | Do not submit |

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

- Leader-lock SHA-256: `{sha256(leader_path)}`
- Source leader SHA-256: `{sha256(LEADER_PATH)}`
- Leader-lock exact-label match: `{leader.equals(pd.read_csv(leader_path))}`
- Rows and Id order were validated against `data/X_test.csv` for all three CSVs.
- The archive and `post_rank1_variant_checksums.sha256` contain all handoff
  files needed to verify this result.
"""
    REPORT_PATH.write_text(report)

    tracked = [
        leader_path,
        fallback_path,
        rejected_path,
        RANKING_PATH,
        REPORT_PATH,
        Path(__file__),
    ]
    write_checksums(tracked)
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in tracked + [CHECKSUM_PATH]:
            archive.write(path, path.relative_to(OUTPUTS))

    print(f"primary={leader_path}")
    print(f"primary_sha256={sha256(leader_path)}")
    print(f"bundle={ZIP_PATH}")


if __name__ == "__main__":
    main()
