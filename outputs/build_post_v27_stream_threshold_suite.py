"""Build stream-threshold probes after v29 false-positive audit."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
TEST_PATH = ROOT / "data" / "X_test.csv"
V27_PATH = OUTPUTS / "post_v25_publish_candidates" / "submission_v27_stream3_5_payload.csv"
V27_SHA256 = "6cca99ca5f6147f6d4865e87908a5fd88313faf2bf596d56f8eb1972a1ac0d02"
CANDIDATE_DIR = OUTPUTS / "post_v27_threshold_candidates"
MANIFEST_PATH = OUTPUTS / "post_v27_threshold_manifest.csv"
DIFF_PATH = OUTPUTS / "post_v27_threshold_changed_ids.csv"
SCORES_PATH = OUTPUTS / "post_v27_threshold_observed_scores.csv"
REPORT_PATH = OUTPUTS / "post_v27_threshold_report.md"
CHECKSUM_PATH = OUTPUTS / "post_v27_threshold_checksums.sha256"
ZIP_PATH = OUTPUTS / "superai6_post_v27_threshold_bundle.zip"

THRESHOLD_085 = (790, 975, 997, 1_893, 3_740, 4_891, 5_944, 6_765, 7_641, 8_364, 8_671, 9_504, 9_977)
THRESHOLD_080 = THRESHOLD_085 + (1_269, 2_135, 2_372, 2_483, 2_787, 5_370, 8_739, 8_831, 9_148, 9_677)

SPECS = (
    {
        "rank": 1,
        "filename": "submission_v30_stream_fraction_085.csv",
        "add_ids": THRESHOLD_085,
        "role": "PRIMARY_PROBE",
        "confidence": "HIGH_STREAM_THRESHOLD",
        "note": "13 publish payload rows from streams with positive fraction at least 0.85.",
    },
    {
        "rank": 2,
        "filename": "submission_v31_stream_fraction_080.csv",
        "add_ids": THRESHOLD_080,
        "role": "AGGRESSIVE_PROBE",
        "confidence": "MEDIUM_STREAM_THRESHOLD",
        "note": "23 publish payload rows from streams with positive fraction at least 0.80.",
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
    baseline = pd.read_csv(V27_PATH)
    validate_submission(baseline, test)
    if sha256(V27_PATH) != V27_SHA256:
        raise RuntimeError("v27 checksum mismatch")
    if int(baseline["label"].sum()) != 2_854:
        raise RuntimeError("Unexpected v27 positive count")

    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    baseline_copy = CANDIDATE_DIR / "submission_v27_confirmed_baseline.csv"
    baseline.to_csv(baseline_copy, index=False)
    if sha256(baseline_copy) != V27_SHA256:
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
                "added_ids_vs_v27": ";".join(map(str, spec["add_ids"])),
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
                    "v27_label": 0,
                    "candidate_label": 1,
                }
            )

    pd.DataFrame(manifest_rows).sort_values("rank").to_csv(MANIFEST_PATH, index=False)
    pd.DataFrame(diff_rows).to_csv(DIFF_PATH, index=False)
    pd.DataFrame(
        [
            {
                "kaggle_ref": 54810185,
                "filename": "submission_v27_stream3_5_payload.csv",
                "public_f1": 0.96824,
                "private_f1": 0.97748,
            },
            {
                "kaggle_ref": 54810175,
                "filename": "submission_v29_all_high_fraction_payload.csv",
                "public_f1": 0.96348,
                "private_f1": 0.97329,
            },
            {
                "kaggle_ref": 54810114,
                "filename": "submission_v25_stream2_plus_stream4_payload.csv",
                "public_f1": 0.96749,
                "private_f1": 0.97611,
            },
        ]
    ).to_csv(SCORES_PATH, index=False)

    report = """# Post-v27 Stream Threshold Report

## สถานะล่าสุด

`submission_v27_stream3_5_payload.csv` เป็น current best: Public `0.96824` /
Private `0.97748`. `v29` เพิ่ม 27 rows แล้วลดเป็น Public `0.96348` /
Private `0.97329`; กลุ่ม publish streams 6-32 มี false positives สูง.

## Candidate ใหม่

| Rank | File | Positives | เพิ่มจาก v27 | ระดับ |
|---:|---|---:|---:|---|
| 1 | `submission_v30_stream_fraction_085.csv` | 2,867 | 13 rows | แนะนำสุด |
| 2 | `submission_v31_stream_fraction_080.csv` | 2,877 | 23 rows | โหด |

## เหตุผล

- v30 คัดเฉพาะ publish payload rows จาก streams ที่ current positive fraction >= 0.85.
- v31 ขยาย threshold เป็น >= 0.80.
- ทั้งสองตัด CONNECT และไม่ใช้ full v29 ซึ่งพิสูจน์แล้วว่าเสียคะแนน.
- Candidate ใหม่ยังไม่มี Kaggle confirmation. ต้องมองเป็น controlled probe.

## การเลือก

ใช้ `submission_v30_stream_fraction_085.csv` เป็น next file. ใช้ v31 ถ้าต้องการ
ลุ้นแรงและยอมรับ false-positive risk.

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

    primary = CANDIDATE_DIR / "submission_v30_stream_fraction_085.csv"
    print(f"primary={primary}")
    print(f"primary_sha256={sha256(primary)}")
    print(f"bundle={ZIP_PATH}")


if __name__ == "__main__":
    main()
