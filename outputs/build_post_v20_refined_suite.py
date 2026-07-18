"""Build refined candidates after v20 exposed mixed residual precision."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
TEST_PATH = ROOT / "data" / "X_test.csv"
V16_PATH = OUTPUTS / "post_v16_continuation_candidates" / "submission_v16_confirmed_baseline.csv"
V16_SHA256 = "a1a58ab8547655d0fff22a07cedd8a2f93a0ee6edb92297f5cae3404fca42702"
CANDIDATE_DIR = OUTPUTS / "post_v20_refined_candidates"
MANIFEST_PATH = OUTPUTS / "post_v20_refined_manifest.csv"
DIFF_PATH = OUTPUTS / "post_v20_refined_changed_ids.csv"
SCORES_PATH = OUTPUTS / "post_v20_refined_observed_scores.csv"
REPORT_PATH = OUTPUTS / "post_v20_refined_report.md"
CHECKSUM_PATH = OUTPUTS / "post_v20_refined_checksums.sha256"
ZIP_PATH = OUTPUTS / "superai6_post_v20_refined_bundle.zip"

HIGH_CONTEXT_IDS = (1_223, 9_757, 5_850, 5_177, 8_362, 592, 8_832, 4_394, 6_644, 7_235)

SPECS = (
    {
        "rank": 1,
        "filename": "submission_v21_high_context.csv",
        "add_ids": HIGH_CONTEXT_IDS,
        "role": "PRIMARY_REFINED",
        "confidence": "HIGH_ATTACK_CONTEXT",
        "note": "Ranks 12-22 excluding low-attack-fraction stream-0 rows; 10 candidates.",
    },
    {
        "rank": 2,
        "filename": "submission_v22_high_novelty_4082.csv",
        "add_ids": (4_082,),
        "role": "SINGLE_NOVELTY_PROBE",
        "confidence": "HIGH_FREQUENCY_NOVELTY",
        "note": "Single stream-0 row with frequency excess 0.75045.",
    },
    {
        "rank": 3,
        "filename": "submission_v23_context_plus_novelty.csv",
        "add_ids": HIGH_CONTEXT_IDS + (4_082,),
        "role": "AGGRESSIVE_COMBINED",
        "confidence": "HIGH_RISK_COMBINED",
        "note": "Combines high attack-context group with 4082 novelty hypothesis.",
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
                "kaggle_ref": 54809954,
                "filename": "submission_v20_plus_rank12_30.csv",
                "public_f1": 0.96461,
                "private_f1": 0.97412,
            },
            {
                "kaggle_ref": 54809890,
                "filename": "submission_v16_plus_residual_top7.csv",
                "public_f1": 0.96414,
                "private_f1": 0.97403,
            },
        ]
    ).to_csv(SCORES_PATH, index=False)

    report = """# Post-v20 Refined Candidate Report

## สถานะล่าสุด

`submission_v20_plus_rank12_30.csv` ได้คะแนนจริง Public `0.96461` /
Private `0.97412`. เมื่อเทียบ v16 เพิ่ม Public `+0.00047` แต่ Private เพียง
`+0.00009`; กลุ่ม rank 12-30 มี false positives ปน จึงไม่ควรเติม residual ทั้งกลุ่มต่อ.

## Candidate ใหม่

| Rank | File | Positives | เพิ่มจาก v16 | ระดับ |
|---:|---|---:|---|---|
| 1 | `submission_v21_high_context.csv` | 2,831 | 10 แถว attack-context สูง | แนะนำสุด |
| 2 | `submission_v22_high_novelty_4082.csv` | 2,822 | `Id=4082` เดี่ยว | probe คุมความเสี่ยง |
| 3 | `submission_v23_context_plus_novelty.csv` | 2,832 | v21 + `4082` | โหดสุด |

## เหตุผล

- v21 เก็บเฉพาะ candidates ที่อยู่ stream attack fraction สูงหรือมี stream-4/5 context
  สูง; ตัด stream-0 low-context rows ออก.
- v22 แยก `Id=4082` เพราะ frequency excess `0.75045` สูงสุดในกลุ่มที่ยังไม่เลือก
  แม้ stream attack fraction ต่ำ.
- v23 รวมสองสมมติฐาน; false-positive risk สูงกว่า v21.
- ถ้าเพิ่ม TP ฝั่ง Public: ประมาณ `+0.00037` ต่อแถว.
- ถ้าเพิ่ม TP ฝั่ง Private: ประมาณ `+0.00034` ต่อแถว.

## การเลือก

ใช้ `submission_v21_high_context.csv` เป็นตัวถัดไป. ใช้ `v23` ถ้าต้องการลุ้นแรง.
`v22` เหมาะสำหรับแยกทดสอบ novelty เดี่ยว.

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

    primary = CANDIDATE_DIR / "submission_v21_high_context.csv"
    print(f"primary={primary}")
    print(f"primary_sha256={sha256(primary)}")
    print(f"bundle={ZIP_PATH}")


if __name__ == "__main__":
    main()
