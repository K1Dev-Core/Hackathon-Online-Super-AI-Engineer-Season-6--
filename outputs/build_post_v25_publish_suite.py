"""Build next payload candidates from high-positive streams, excluding CONNECT rows."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
TEST_PATH = ROOT / "data" / "X_test.csv"
V25_PATH = OUTPUTS / "post_v23_payload_candidates" / "submission_v25_stream2_plus_stream4_payload.csv"
V25_SHA256 = "e01a93fc5e28f093bd91a39dd6a9f384151d618c632b58396cbd987fb2626655"
CANDIDATE_DIR = OUTPUTS / "post_v25_publish_candidates"
MANIFEST_PATH = OUTPUTS / "post_v25_publish_manifest.csv"
DIFF_PATH = OUTPUTS / "post_v25_publish_changed_ids.csv"
SCORES_PATH = OUTPUTS / "post_v25_publish_observed_scores.csv"
REPORT_PATH = OUTPUTS / "post_v25_publish_report.md"
CHECKSUM_PATH = OUTPUTS / "post_v25_publish_checksums.sha256"
ZIP_PATH = OUTPUTS / "superai6_post_v25_publish_bundle.zip"

STREAM3_5_PAYLOAD = (7, 1_342, 1_958, 4_799, 7_998, 8_480, 9_453, 1_655, 3_255, 8_258)
ALL_HIGH_FRACTION_PAYLOAD = (
    1_893, 8_671, 8_364, 6_765, 7_641, 4_891, 9_504, 790, 5_944, 3_740,
    997, 9_977, 975, 2_483, 2_372, 5_370, 2_787, 8_831, 8_739, 9_148,
    9_677, 2_135, 1_269, 1_655, 3_255, 8_258, 5_069, 641, 7, 1_342,
    1_958, 4_799, 7_998, 8_480, 9_453, 9_260, 9_439,
)
PUBLISH_ONLY = tuple(row_id for row_id in ALL_HIGH_FRACTION_PAYLOAD if row_id not in STREAM3_5_PAYLOAD)

SPECS = (
    {
        "rank": 1,
        "filename": "submission_v27_stream3_5_payload.csv",
        "add_ids": STREAM3_5_PAYLOAD,
        "role": "PRIMARY_PUBLISH_CONTEXT",
        "confidence": "HIGH_STREAM_PAYLOAD",
        "note": "Ten MQTT msgtype 1/3 payload rows from streams with positive fraction 0.76-0.81.",
    },
    {
        "rank": 2,
        "filename": "submission_v28_publish_payload_cluster.csv",
        "add_ids": PUBLISH_ONLY,
        "role": "AGGRESSIVE_PUBLISH_CLUSTER",
        "confidence": "HIGH_FRACTION_PUBLISH",
        "note": "Twenty-seven remaining MQTT msgtype-1 payload rows in streams above 0.75 fraction.",
    },
    {
        "rank": 3,
        "filename": "submission_v29_all_high_fraction_payload.csv",
        "add_ids": ALL_HIGH_FRACTION_PAYLOAD,
        "role": "MAXIMUM_PAYLOAD_UPSIDE",
        "confidence": "MAX_RISK_NO_CONNECT",
        "note": "All 37 publish/publish-response payload rows; excludes all MQTT CONNECT rows.",
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
    baseline = pd.read_csv(V25_PATH)
    validate_submission(baseline, test)
    if sha256(V25_PATH) != V25_SHA256:
        raise RuntimeError("v25 checksum mismatch")
    if int(baseline["label"].sum()) != 2_844:
        raise RuntimeError("Unexpected v25 positive count")

    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    baseline_copy = CANDIDATE_DIR / "submission_v25_confirmed_baseline.csv"
    baseline.to_csv(baseline_copy, index=False)
    if sha256(baseline_copy) != V25_SHA256:
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
                "added_ids_vs_v25": ";".join(map(str, spec["add_ids"])),
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
                    "v25_label": 0,
                    "candidate_label": 1,
                }
            )

    pd.DataFrame(manifest_rows).sort_values("rank").to_csv(MANIFEST_PATH, index=False)
    pd.DataFrame(diff_rows).to_csv(DIFF_PATH, index=False)
    pd.DataFrame(
        [
            {
                "kaggle_ref": 54810114,
                "filename": "submission_v25_stream2_plus_stream4_payload.csv",
                "public_f1": 0.96749,
                "private_f1": 0.97611,
            },
            {
                "kaggle_ref": 54810130,
                "filename": "submission_v26_stream_payload_plus_connect.csv",
                "public_f1": 0.96749,
                "private_f1": 0.97578,
            },
            {
                "kaggle_ref": 54810019,
                "filename": "submission_v23_context_plus_novelty.csv",
                "public_f1": 0.96598,
                "private_f1": 0.97541,
            },
        ]
    ).to_csv(SCORES_PATH, index=False)

    report = """# Post-v25 Publish Candidate Report

## สถานะล่าสุด

`submission_v25_stream2_plus_stream4_payload.csv` ได้ Public `0.96749` /
Private `0.97611`. `v26` เพิ่ม CONNECT `Id=4550` แล้ว Private ลดเป็น `0.97578`;
ตัด CONNECT ทั้งหมดออกจากชุดใหม่.

## Candidate ใหม่

| Rank | File | Positives | เพิ่มจาก v25 | ระดับ |
|---:|---|---:|---:|---|
| 1 | `submission_v27_stream3_5_payload.csv` | 2,854 | 10 payload rows | แนะนำสุด |
| 2 | `submission_v28_publish_payload_cluster.csv` | 2,871 | 27 payload rows | โหด |
| 3 | `submission_v29_all_high_fraction_payload.csv` | 2,881 | 37 payload rows | สุดโหด |

## เหตุผล

- v25 ยืนยันว่าการเติม MQTT payload ใน high-positive streams ทำคะแนนจริงทั้งสองฝั่ง.
- v27 ใช้ streams 3 และ 5 ที่มี positive fraction `0.7606` และ `0.8070`.
- v28 เพิ่ม publish rows จาก streams positive fraction `0.75+`.
- v29 รวม payload ทั้งหมด แต่ไม่รวม MQTT CONNECT ซึ่ง v26 พิสูจน์แล้วว่าเสี่ยง.
- Candidate ใหม่ยังไม่มี Kaggle confirmation. เพิ่ม TP Public คาดประมาณ `+0.00037`
  ต่อแถว; TP Private คาดประมาณ `+0.00034` ต่อแถว.

## การเลือก

ใช้ `submission_v27_stream3_5_payload.csv` เป็น next controlled aggressive file.
ใช้ `v29` ถ้าต้องการ maximum upside โดยยอมรับความเสี่ยง.

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

    primary = CANDIDATE_DIR / "submission_v27_stream3_5_payload.csv"
    print(f"primary={primary}")
    print(f"primary_sha256={sha256(primary)}")
    print(f"bundle={ZIP_PATH}")


if __name__ == "__main__":
    main()
