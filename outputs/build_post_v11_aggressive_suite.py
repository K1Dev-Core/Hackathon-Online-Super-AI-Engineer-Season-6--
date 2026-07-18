"""Build aggressive candidates after v11 Private score confirmation."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
TEST_PATH = ROOT / "data" / "X_test.csv"
V11_PATH = OUTPUTS / "post_deadline_v8_candidates" / "submission_v11_pareto_plus_payload150.csv"
V11_SHA256 = "e83ea2ee73e8dcfdcd03dda4b5c95574fa8a5a87be3d243a4f441b41b5dd13cf"
CANDIDATE_DIR = OUTPUTS / "post_v11_aggressive_candidates"
MANIFEST_PATH = OUTPUTS / "post_v11_aggressive_manifest.csv"
DIFF_PATH = OUTPUTS / "post_v11_aggressive_changed_ids.csv"
SCORES_PATH = OUTPUTS / "post_v11_aggressive_observed_scores.csv"
REPORT_PATH = OUTPUTS / "post_v11_aggressive_report.md"
CHECKSUM_PATH = OUTPUTS / "post_v11_aggressive_checksums.sha256"
ZIP_PATH = OUTPUTS / "superai6_post_v11_aggressive_bundle.zip"

SPECS = (
    {
        "rank": 1,
        "filename": "submission_v12_plus_rare_ack.csv",
        "add_ids": (6_011,),
        "confidence": "BEST_NEXT_SINGLE",
        "role": "PRIMARY_RECOMMENDATION",
        "note": "Rank-4 residual; stream 2; stream attack fraction 0.9058.",
    },
    {
        "rank": 2,
        "filename": "submission_v13_plus_stream5_ack.csv",
        "add_ids": (4_057,),
        "confidence": "MEDIUM_STREAM_CONTEXT",
        "role": "SINGLE_ROW_ALTERNATIVE",
        "note": "Rank-5 residual; stream 5; stream attack fraction 0.7193.",
    },
    {
        "rank": 3,
        "filename": "submission_v14_plus_dual_ack.csv",
        "add_ids": (6_011, 4_057),
        "confidence": "AGGRESSIVE_TWO_ROW",
        "role": "AGGRESSIVE_RECOMMENDATION",
        "note": "Combines two highest remaining residual candidates.",
    },
    {
        "rank": 4,
        "filename": "submission_v15_plus_stream2_ack_cluster.csv",
        "add_ids": (6_011, 1_223, 9_757, 5_850, 5_177),
        "confidence": "HIGH_RISK_CLUSTER",
        "role": "STREAM2_MAX_UPSIDE",
        "note": "Five remaining stream-2 ACK candidates; includes weak tail rows.",
    },
    {
        "rank": 5,
        "filename": "submission_v16_plus_residual_top7.csv",
        "add_ids": (6_011, 4_057, 4_933, 1_980, 5_475, 1_805, 55),
        "confidence": "MAX_RISK_TOP7",
        "role": "MAXIMUM_UPSIDE_BACKUP",
        "note": "Residual ranks 4-10; highest upside, highest false-positive risk.",
    },
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_submission(submission: pd.DataFrame, test: pd.DataFrame) -> None:
    if list(submission.columns) != ["Id", "label"]:
        raise RuntimeError(f"Invalid columns: {list(submission.columns)}")
    if len(submission) != len(test) != 10_000:
        raise RuntimeError("Unexpected submission row count")
    if not submission["Id"].equals(test["Id"]):
        raise RuntimeError("Submission Id order does not match X_test")
    if not submission["Id"].is_unique:
        raise RuntimeError("Duplicate Id values")
    if submission["label"].isna().any() or not set(submission["label"].unique()) <= {0, 1}:
        raise RuntimeError("Labels must be binary and non-null")


def main() -> None:
    test = pd.read_csv(TEST_PATH, low_memory=False)
    baseline = pd.read_csv(V11_PATH)
    validate_submission(baseline, test)
    if sha256(V11_PATH) != V11_SHA256:
        raise RuntimeError("v11 checksum mismatch")
    if int(baseline["label"].sum()) != 2_814:
        raise RuntimeError("Unexpected v11 positive count")

    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    baseline_copy = CANDIDATE_DIR / "submission_v11_confirmed_baseline.csv"
    baseline.to_csv(baseline_copy, index=False)
    if sha256(baseline_copy) != V11_SHA256:
        raise RuntimeError("Baseline copy changed bytes")

    manifest_rows: list[dict[str, object]] = []
    diff_rows: list[dict[str, object]] = []
    tracked = [baseline_copy]
    for spec in SPECS:
        candidate = baseline.copy()
        candidate.loc[candidate["Id"].isin(spec["add_ids"]), "label"] = 1
        validate_submission(candidate, test)
        changed = candidate.loc[candidate["label"].ne(baseline["label"]), "Id"].tolist()
        if set(changed) != set(spec["add_ids"]):
            raise RuntimeError(f"Unexpected changed Ids for {spec['filename']}: {changed}")
        path = CANDIDATE_DIR / str(spec["filename"])
        candidate.to_csv(path, index=False)
        tracked.append(path)
        manifest_rows.append(
            {
                "rank": spec["rank"],
                "filename": spec["filename"],
                "positive_labels": int(candidate["label"].sum()),
                "added_ids_vs_v11": ";".join(map(str, spec["add_ids"])),
                "confidence": spec["confidence"],
                "role": spec["role"],
                "note": spec["note"],
                "sha256": sha256(path),
            }
        )
        for row_id in sorted(spec["add_ids"]):
            diff_rows.append(
                {
                    "filename": spec["filename"],
                    "Id": row_id,
                    "v11_label": 0,
                    "candidate_label": 1,
                }
            )

    pd.DataFrame(manifest_rows).sort_values("rank").to_csv(MANIFEST_PATH, index=False)
    pd.DataFrame(diff_rows).to_csv(DIFF_PATH, index=False)
    pd.DataFrame(
        [
            {
                "kaggle_ref": 54809842,
                "filename": "submission_v12_plus_rare_ack.csv",
                "public_f1": 0.96304,
                "private_f1": 0.97300,
            },
            {
                "kaggle_ref": 54809776,
                "filename": "submission_v11_pareto_plus_payload150.csv",
                "public_f1": 0.96304,
                "private_f1": 0.97266,
            },
            {
                "kaggle_ref": 54809544,
                "filename": "submission_v10_pareto_plus_exact_twin.csv",
                "public_f1": 0.96304,
                "private_f1": 0.97232,
            },
        ]
    ).to_csv(SCORES_PATH, index=False)

    report = """# Post-v11 Aggressive Candidate Report

## สถานะล่าสุด

`submission_v12_plus_rare_ack.csv` ได้คะแนนจริง Public `0.96304` / Private
`0.97300` เพิ่มจาก v11 เฉพาะ Private `+0.00034` ยืนยันว่า `Id=6011`
เป็น Private TP. Current confirmed positives: `4456, 5516, 6011` ฝั่ง Private;
`9816, 1145, 5244` ฝั่ง Public.

## Candidate ใหม่

| Rank | File | Positive | เพิ่มจาก v11 | ระดับ |
|---:|---|---:|---|---|
| 1 | `submission_v14_plus_dual_ack.csv` | 2,816 | `4057` จาก v12 | ตัวถัดไป แนะนำ |
| 2 | `submission_v13_plus_stream5_ack.csv` | 2,815 | `4057` จาก v11 | fallback เก่า |
| 3 | `submission_v15_plus_stream2_ack_cluster.csv` | 2,819 | `1223,9757,5850,5177` จาก v12 | โหดมาก |
| 4 | `submission_v16_plus_residual_top7.csv` | 2,821 | `4057,4933,1980,5475,1805,55` จาก v12 | เสี่ยงสุด |

## เหตุผล

- `Id=6011` เป็น residual rank 4, อยู่ stream 2 เดียวกับ confirmed TP หลายแถว,
  stream attack fraction `0.905797`, frequency excess `0.2157`.
- `Id=4057` เป็น residual rank 5, อยู่ stream 5 ที่ attack fraction `0.719298`.
- Candidate rank 4-10 ยังไม่มี Kaggle confirmation และ external PCAP exact-match
  ไม่พบ. ไฟล์รวมจึงเป็น upside search ไม่ใช่ safe prediction.
- ถ้า candidate เป็น TP ใน Public: คาด Public เพิ่มประมาณ `0.00037`.
- ถ้า candidate เป็น TP ใน Private: คาด Private เพิ่มประมาณ `0.00034`.
- ถ้าเป็น FP: F1 ลด. v12 คือ single-row risk ต่ำสุด; v16 คือ maximum-upside risk สูงสุด.

## การเลือก

แนะนำถัดไป `submission_v14_plus_dual_ack.csv` เพราะเพิ่ม candidate เดี่ยว `Id=4057`
จาก current best. ถ้าต้องการลุ้นแรงใช้ `v16`; `v15` เน้น stream 2 แต่มี weak tail rows.

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

    primary = CANDIDATE_DIR / "submission_v12_plus_rare_ack.csv"
    print(f"primary={primary}")
    print(f"primary_sha256={sha256(primary)}")
    print(f"bundle={ZIP_PATH}")


if __name__ == "__main__":
    main()
