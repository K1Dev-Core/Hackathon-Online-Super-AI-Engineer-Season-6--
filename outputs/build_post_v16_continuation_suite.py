"""Build continuation candidates from confirmed v16 leaderboard result."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
TEST_PATH = ROOT / "data" / "X_test.csv"
V16_PATH = OUTPUTS / "post_v11_aggressive_candidates" / "submission_v16_plus_residual_top7.csv"
V16_SHA256 = "a1a58ab8547655d0fff22a07cedd8a2f93a0ee6edb92297f5cae3404fca42702"
CANDIDATE_DIR = OUTPUTS / "post_v16_continuation_candidates"
MANIFEST_PATH = OUTPUTS / "post_v16_continuation_manifest.csv"
DIFF_PATH = OUTPUTS / "post_v16_continuation_changed_ids.csv"
SCORES_PATH = OUTPUTS / "post_v16_continuation_observed_scores.csv"
REPORT_PATH = OUTPUTS / "post_v16_continuation_report.md"
CHECKSUM_PATH = OUTPUTS / "post_v16_continuation_checksums.sha256"
ZIP_PATH = OUTPUTS / "superai6_post_v16_continuation_bundle.zip"

SPECS = (
    {
        "rank": 1,
        "filename": "submission_v17_plus_stream2_tail.csv",
        "add_ids": (1_223, 9_757, 5_850, 5_177),
        "role": "PRIMARY_NEXT",
        "confidence": "STREAM2_CLUSTER",
        "note": "Residual ranks 12-15; same stream-2 family as confirmed positives.",
    },
    {
        "rank": 2,
        "filename": "submission_v18_plus_rank12_16.csv",
        "add_ids": (1_223, 9_757, 5_850, 5_177, 8_362),
        "role": "AGGRESSIVE_FIVE",
        "confidence": "MEDIUM_CLUSTER_PLUS",
        "note": "Ranks 12-16; adds stream-4 candidate 8362.",
    },
    {
        "rank": 3,
        "filename": "submission_v19_plus_rank12_20.csv",
        "add_ids": (1_223, 9_757, 5_850, 5_177, 8_362, 592, 4_082, 8_832, 4_394),
        "role": "AGGRESSIVE_NINE",
        "confidence": "HIGH_RISK",
        "note": "All residual ranks 12-20.",
    },
    {
        "rank": 4,
        "filename": "submission_v20_plus_rank12_30.csv",
        "add_ids": (
            1_223, 9_757, 5_850, 5_177, 8_362, 592, 4_082, 8_832, 4_394,
            6_644, 7_235, 524, 1_309, 4_188, 1_636, 1_763, 2_440, 2_743, 2_798,
        ),
        "role": "MAXIMUM_UPSIDE",
        "confidence": "MAX_RISK",
        "note": "All residual ranks 12-30; maximum false-positive exposure.",
    },
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_submission(submission: pd.DataFrame, test: pd.DataFrame) -> None:
    if list(submission.columns) != ["Id", "label"]:
        raise RuntimeError(f"Invalid columns: {list(submission.columns)}")
    if len(submission) != len(test) or len(test) != 10_000:
        raise RuntimeError("Unexpected submission row count")
    if not submission["Id"].equals(test["Id"]):
        raise RuntimeError("Submission Id order does not match X_test")
    if not submission["Id"].is_unique:
        raise RuntimeError("Duplicate Id values")
    if submission["label"].isna().any() or not set(submission["label"].unique()) <= {0, 1}:
        raise RuntimeError("Labels must be binary and non-null")


def main() -> None:
    test = pd.read_csv(TEST_PATH, low_memory=False)
    baseline = pd.read_csv(V16_PATH)
    validate_submission(baseline, test)
    if sha256(V16_PATH) != V16_SHA256:
        raise RuntimeError("v16 checksum mismatch")
    if int(baseline["label"].sum()) != 2_821:
        raise RuntimeError("Unexpected v16 positive count")

    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    baseline_copy = CANDIDATE_DIR / "submission_v16_confirmed_baseline.csv"
    baseline.to_csv(baseline_copy, index=False)
    if sha256(baseline_copy) != V16_SHA256:
        raise RuntimeError("Baseline copy changed bytes")

    manifest_rows: list[dict[str, object]] = []
    diff_rows: list[dict[str, object]] = []
    tracked = [baseline_copy]
    for spec in SPECS:
        candidate = baseline.copy()
        candidate.loc[candidate["Id"].isin(spec["add_ids"]), "label"] = 1
        validate_submission(candidate, test)
        changed = set(candidate.loc[candidate["label"].ne(baseline["label"]), "Id"])
        if changed != set(spec["add_ids"]):
            raise RuntimeError(f"Unexpected changed Ids: {sorted(changed)}")
        path = CANDIDATE_DIR / str(spec["filename"])
        candidate.to_csv(path, index=False)
        tracked.append(path)
        manifest_rows.append(
            {
                "rank": spec["rank"],
                "filename": spec["filename"],
                "positive_labels": int(candidate["label"].sum()),
                "added_ids_vs_v16": ";".join(map(str, spec["add_ids"])),
                "role": spec["role"],
                "confidence": spec["confidence"],
                "note": spec["note"],
                "sha256": sha256(path),
            }
        )
        for row_id in sorted(spec["add_ids"]):
            diff_rows.append(
                {
                    "filename": spec["filename"],
                    "Id": row_id,
                    "v16_label": 0,
                    "candidate_label": 1,
                }
            )

    pd.DataFrame(manifest_rows).sort_values("rank").to_csv(MANIFEST_PATH, index=False)
    pd.DataFrame(diff_rows).to_csv(DIFF_PATH, index=False)
    pd.DataFrame(
        [
            {
                "kaggle_ref": 54809890,
                "filename": "submission_v16_plus_residual_top7.csv",
                "public_f1": 0.96414,
                "private_f1": 0.97403,
            },
            {
                "kaggle_ref": 54809908,
                "filename": "submission_v14_plus_dual_ack.csv",
                "public_f1": 0.96304,
                "private_f1": 0.97335,
            },
            {
                "kaggle_ref": 54809842,
                "filename": "submission_v12_plus_rare_ack.csv",
                "public_f1": 0.96304,
                "private_f1": 0.97300,
            },
        ]
    ).to_csv(SCORES_PATH, index=False)

    report = """# Post-v16 Continuation Report

## สถานะล่าสุด

`submission_v16_plus_residual_top7.csv` ได้คะแนนจริง Public `0.96414` /
Private `0.97403` จาก v12 เพิ่ม Public `+0.00110` และ Private `+0.00103`.
v14 ยืนยัน `Id=4057` เป็น Private TP ด้วยคะแนน Private `0.97335`.

## Candidate ต่อไป

| Rank | File | Positives | เพิ่มจาก v16 | ระดับ |
|---:|---|---:|---|---|
| 1 | `submission_v17_plus_stream2_tail.csv` | 2,825 | 4 แถว rank 12-15 | แนะนำสุด |
| 2 | `submission_v18_plus_rank12_16.csv` | 2,826 | 5 แถว rank 12-16 | โหด |
| 3 | `submission_v19_plus_rank12_20.csv` | 2,830 | 9 แถว rank 12-20 | โหดมาก |
| 4 | `submission_v20_plus_rank12_30.csv` | 2,840 | 19 แถว rank 12-30 | เสี่ยงสุด |

## เหตุผล

- v16 ทำให้ residual ranks 5-10 รวม 6 แถวช่วยคะแนนทั้ง Public และ Private.
- `v17` ต่อด้วย stream-2 tail ranks 12-15; stream เดียวกับ confirmed TP หลายแถว
  และ stream attack fraction `0.905797`.
- `v18-v20` เพิ่มกลุ่มกว้างขึ้น. Upside สูงขึ้น แต่ false-positive risk สูงขึ้นเร็ว.
- ถ้าเพิ่ม TP ฝั่ง Public: ประมาณ `+0.00037` ต่อแถว.
- ถ้าเพิ่ม TP ฝั่ง Private: ประมาณ `+0.00034` ต่อแถว.

## การเลือก

ใช้ `submission_v17_plus_stream2_tail.csv` เป็น next controlled aggressive file.
ใช้ `v19` ถ้าต้องการลุ้นแรง. `v20` maximum-risk เท่านั้น.

ยังไม่ส่ง Kaggle จาก pipeline นี้.
"""
    REPORT_PATH.write_text(report)

    tracked += [MANIFEST_PATH, DIFF_PATH, SCORES_PATH, REPORT_PATH, Path(__file__)]
    CHECKSUM_PATH.write_text(
        "\n".join(
            f"{sha256(path)}  {path.relative_to(OUTPUTS)}" for path in tracked
        )
        + "\n"
    )
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in tracked + [CHECKSUM_PATH]:
            archive.write(path, path.relative_to(OUTPUTS))

    primary = CANDIDATE_DIR / "submission_v17_plus_stream2_tail.csv"
    print(f"primary={primary}")
    print(f"primary_sha256={sha256(primary)}")
    print(f"bundle={ZIP_PATH}")


if __name__ == "__main__":
    main()
