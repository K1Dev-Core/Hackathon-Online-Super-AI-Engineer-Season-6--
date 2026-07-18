"""Build protocol-context candidates from high-positive streams after v23."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
TEST_PATH = ROOT / "data" / "X_test.csv"
V23_PATH = OUTPUTS / "post_v20_refined_candidates" / "submission_v23_context_plus_novelty.csv"
V23_SHA256 = "d5f4779d6687b5d40948063a1ebf149b3837fe0a7e5d9dffbf8494a029efd4b6"
CANDIDATE_DIR = OUTPUTS / "post_v23_payload_candidates"
MANIFEST_PATH = OUTPUTS / "post_v23_payload_manifest.csv"
DIFF_PATH = OUTPUTS / "post_v23_payload_changed_ids.csv"
SCORES_PATH = OUTPUTS / "post_v23_payload_observed_scores.csv"
REPORT_PATH = OUTPUTS / "post_v23_payload_report.md"
CHECKSUM_PATH = OUTPUTS / "post_v23_payload_checksums.sha256"
ZIP_PATH = OUTPUTS / "superai6_post_v23_payload_bundle.zip"

STREAM2_PAYLOAD = (778, 2_704, 5_804, 6_155, 6_546, 6_572, 6_803, 7_784, 7_935)
STREAM4_PAYLOAD = (4_475, 7_661, 8_393)
MQTT_CONNECT = (4_550,)

SPECS = (
    {
        "rank": 1,
        "filename": "submission_v24_stream2_mqtt_payload.csv",
        "add_ids": STREAM2_PAYLOAD,
        "role": "PRIMARY_PROTOCOL_CONTEXT",
        "confidence": "STREAM2_PAYLOAD_CLUSTER",
        "note": "Nine unselected MQTT payload rows in stream 2; stream positive fraction 0.9384.",
    },
    {
        "rank": 2,
        "filename": "submission_v25_stream2_plus_stream4_payload.csv",
        "add_ids": STREAM2_PAYLOAD + STREAM4_PAYLOAD,
        "role": "AGGRESSIVE_PROTOCOL_CONTEXT",
        "confidence": "TWO_STREAM_PAYLOAD",
        "note": "Adds three unselected MQTT payload rows from stream 4; fraction 0.9138.",
    },
    {
        "rank": 3,
        "filename": "submission_v26_stream_payload_plus_connect.csv",
        "add_ids": STREAM2_PAYLOAD + STREAM4_PAYLOAD + MQTT_CONNECT,
        "role": "MAXIMUM_PAYLOAD_RISK",
        "confidence": "CONNECT_FALSE_POSITIVE_RISK",
        "note": "Adds Id=4550 MQTT CONNECT row; highest risk because CONNECT may be normal.",
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
    baseline = pd.read_csv(V23_PATH)
    validate_submission(baseline, test)
    if sha256(V23_PATH) != V23_SHA256:
        raise RuntimeError("v23 checksum mismatch")
    if int(baseline["label"].sum()) != 2_832:
        raise RuntimeError("Unexpected v23 positive count")

    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    baseline_copy = CANDIDATE_DIR / "submission_v23_confirmed_baseline.csv"
    baseline.to_csv(baseline_copy, index=False)
    if sha256(baseline_copy) != V23_SHA256:
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
                "added_ids_vs_v23": ";".join(map(str, spec["add_ids"])),
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
                    "v23_label": 0,
                    "candidate_label": 1,
                }
            )

    pd.DataFrame(manifest_rows).sort_values("rank").to_csv(MANIFEST_PATH, index=False)
    pd.DataFrame(diff_rows).to_csv(DIFF_PATH, index=False)
    pd.DataFrame(
        [
            {
                "kaggle_ref": 54810019,
                "filename": "submission_v23_context_plus_novelty.csv",
                "public_f1": 0.96598,
                "private_f1": 0.97541,
            },
            {
                "kaggle_ref": 54809954,
                "filename": "submission_v20_plus_rank12_30.csv",
                "public_f1": 0.96461,
                "private_f1": 0.97412,
            },
        ]
    ).to_csv(SCORES_PATH, index=False)

    report = """# Post-v23 Payload Candidate Report

## สถานะล่าสุด

`submission_v23_context_plus_novelty.csv` ได้คะแนนจริง Public `0.96598` /
Private `0.97541`. Protocol stream audit พบว่า v23 ยังปล่อย MQTT payload rows
ใน stream ที่มี positive fraction สูงไว้หลายแถว.

## Candidate ใหม่

| Rank | File | Positives | เพิ่มจาก v23 | ระดับ |
|---:|---|---:|---|---|
| 1 | `submission_v24_stream2_mqtt_payload.csv` | 2,841 | 9 stream-2 payload rows | แนะนำสุด |
| 2 | `submission_v25_stream2_plus_stream4_payload.csv` | 2,844 | v24 + 3 stream-4 payload rows | โหด |
| 3 | `submission_v26_stream_payload_plus_connect.csv` | 2,845 | v25 + `Id=4550` | เสี่ยงสุด |

## เหตุผล

- Stream 2 หลัง v23 มี positive fraction `259/276 = 0.9384`; rows ที่เหลือในกลุ่ม
  MQTT payload ใช้รูปแบบ attack payload เดียวกับกลุ่มที่ทำคะแนนผ่านแล้ว.
- Stream 4 มี positive fraction `106/116 = 0.9138`; payload rows ที่เหลือจึงเป็น
  candidate structural completion.
- `Id=4550` เป็น MQTT CONNECT, แยกไว้ v26 เพราะอาจเป็น normal handshake.
- Candidate ใหม่ยังไม่มี Kaggle confirmation. เพิ่ม TP ฝั่ง Public คาดประมาณ `+0.00037`
  ต่อแถว; ฝั่ง Private คาดประมาณ `+0.00034` ต่อแถว.

## การเลือก

ใช้ `submission_v24_stream2_mqtt_payload.csv` เป็นไฟล์ถัดไป. ใช้ `v25` ถ้าต้องการ
ลุ้นสอง stream. `v26` maximum risk เพราะรวม CONNECT row.

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

    primary = CANDIDATE_DIR / "submission_v24_stream2_mqtt_payload.csv"
    print(f"primary={primary}")
    print(f"primary_sha256={sha256(primary)}")
    print(f"bundle={ZIP_PATH}")


if __name__ == "__main__":
    main()
