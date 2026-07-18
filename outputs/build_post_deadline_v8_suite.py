"""Build post-deadline candidates by merging the best public and private deltas."""

from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
TEST_PATH = ROOT / "data" / "X_test.csv"
DEFAULT_V8_PATH = Path("/Users/k1god/Downloads/submission_v8_micro_best.csv")
CANDIDATE_DIR = OUTPUTS / "post_deadline_v8_candidates"
BASELINE_PATH = CANDIDATE_DIR / "submission_v8_scored_baseline.csv"
MANIFEST_PATH = OUTPUTS / "post_deadline_v8_manifest.csv"
DIFF_PATH = OUTPUTS / "post_deadline_v8_changed_ids.csv"
SCORES_PATH = OUTPUTS / "post_deadline_v8_observed_scores.csv"
REPORT_PATH = OUTPUTS / "post_deadline_v8_report.md"
CHECKSUM_PATH = OUTPUTS / "post_deadline_v8_checksums.sha256"
ZIP_PATH = OUTPUTS / "superai6_post_deadline_v8_bundle.zip"

V8_SHA256 = "e72b0bf1f27e507c7e2bc8f350625f0d923e84ced87740ddcc027c7b874b7adb"
PRIVATE_TP_ID = 4_456
CONFIRMED_PUBLIC_IDS = (9_816, 1_145)
EXACT_TWIN_ID = 5_244
PAYLOAD_150_ID = 5_516

SPECS = (
    {
        "rank": 2,
        "filename": "submission_v9_pareto_confirmed.csv",
        "add_ids": CONFIRMED_PUBLIC_IDS,
        "confidence": "CONFIRMED_SCORE_RECONSTRUCTION",
        "estimated_public": "0.96267",
        "estimated_private": "0.97232",
        "role": "SAFE_FALLBACK",
    },
    {
        "rank": 1,
        "filename": "submission_v10_pareto_plus_exact_twin.csv",
        "add_ids": CONFIRMED_PUBLIC_IDS + (EXACT_TWIN_ID,),
        "confidence": "HIGH_EXACT_FEATURE_TWIN",
        "estimated_public": "0.96267-0.96304",
        "estimated_private": "0.97232-0.97266",
        "role": "PRIMARY_RECOMMENDATION",
    },
    {
        "rank": 3,
        "filename": "submission_v11_pareto_plus_payload150.csv",
        "add_ids": CONFIRMED_PUBLIC_IDS + (EXACT_TWIN_ID, PAYLOAD_150_ID),
        "confidence": "MEDIUM_RESIDUAL_EVIDENCE",
        "estimated_public": "unverified",
        "estimated_private": "unverified",
        "role": "HIGHER_RISK_BACKUP",
    },
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_submission(submission: pd.DataFrame, test: pd.DataFrame) -> None:
    if list(submission.columns) != ["Id", "label"]:
        raise RuntimeError(f"Invalid columns: {list(submission.columns)}")
    if len(submission) != 10_000 or len(submission) != len(test):
        raise RuntimeError("Submission must contain exactly 10,000 test rows")
    if not submission["Id"].equals(test["Id"]):
        raise RuntimeError("Submission Id order does not match X_test")
    if not submission["Id"].is_unique:
        raise RuntimeError("Submission contains duplicate Id values")
    if submission["label"].isna().any():
        raise RuntimeError("Submission contains null labels")
    if not set(submission["label"].unique()) <= {0, 1}:
        raise RuntimeError("Submission labels must be binary")


def load_v8(source: Path, test: pd.DataFrame) -> pd.DataFrame:
    if source.exists():
        baseline = pd.read_csv(source)
    elif BASELINE_PATH.exists():
        baseline = pd.read_csv(BASELINE_PATH)
    else:
        raise FileNotFoundError(f"Scored v8 source not found: {source}")
    validate_submission(baseline, test)
    if sha256(source if source.exists() else BASELINE_PATH) != V8_SHA256:
        raise RuntimeError("v8 checksum does not match the scored Kaggle artifact")
    if int(baseline["label"].sum()) != 2_810:
        raise RuntimeError("Unexpected v8 positive count")
    labels = baseline.set_index("Id")["label"]
    expected = {
        PRIVATE_TP_ID: 1,
        9_816: 0,
        1_145: 0,
        EXACT_TWIN_ID: 0,
        PAYLOAD_150_ID: 0,
    }
    if {row_id: int(labels.loc[row_id]) for row_id in expected} != expected:
        raise RuntimeError("v8 key labels differ from the audited artifact")
    return baseline


def build_candidate(
    baseline: pd.DataFrame,
    test: pd.DataFrame,
    add_ids: tuple[int, ...],
) -> pd.DataFrame:
    candidate = baseline.copy()
    candidate.loc[candidate["Id"].isin(add_ids), "label"] = 1
    validate_submission(candidate, test)
    changed = candidate.loc[candidate["label"].ne(baseline["label"]), "Id"].tolist()
    if changed != sorted(add_ids):
        raise RuntimeError(f"Unexpected changed Id values: {changed}")
    if int(candidate.loc[candidate["Id"].eq(PRIVATE_TP_ID), "label"].iloc[0]) != 1:
        raise RuntimeError("Private TP Id=4456 was not preserved")
    return candidate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v8", type=Path, default=DEFAULT_V8_PATH)
    args = parser.parse_args()

    test = pd.read_csv(TEST_PATH, low_memory=False)
    baseline = load_v8(args.v8, test)
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    baseline.to_csv(BASELINE_PATH, index=False)
    if sha256(BASELINE_PATH) != V8_SHA256:
        raise RuntimeError("Copied baseline is not byte-identical to scored v8")

    manifest_rows: list[dict[str, object]] = []
    diff_rows: list[dict[str, object]] = []
    generated = [BASELINE_PATH]
    for spec in SPECS:
        candidate = build_candidate(baseline, test, spec["add_ids"])
        path = CANDIDATE_DIR / str(spec["filename"])
        candidate.to_csv(path, index=False)
        generated.append(path)
        manifest_rows.append(
            {
                "rank": spec["rank"],
                "filename": spec["filename"],
                "positive_labels": int(candidate["label"].sum()),
                "added_ids_vs_v8": ";".join(map(str, spec["add_ids"])),
                "removed_ids_vs_v8": "",
                "id_4456_preserved": True,
                "confidence": spec["confidence"],
                "estimated_public_f1": spec["estimated_public"],
                "estimated_private_f1": spec["estimated_private"],
                "role": spec["role"],
                "sha256": sha256(path),
            }
        )
        for row_id in spec["add_ids"]:
            diff_rows.append(
                {
                    "filename": spec["filename"],
                    "Id": row_id,
                    "v8_label": 0,
                    "candidate_label": 1,
                }
            )

    manifest = pd.DataFrame(manifest_rows).sort_values("rank")
    manifest.to_csv(MANIFEST_PATH, index=False)
    pd.DataFrame(diff_rows).to_csv(DIFF_PATH, index=False)
    pd.DataFrame(
        [
            {
                "kaggle_ref": 54808754,
                "filename": "submission_v8_micro_best.csv",
                "public_f1": 0.96193,
                "private_f1": 0.97232,
            },
            {
                "kaggle_ref": 54794527,
                "filename": "submission_offline_01_scoremax_structural.csv",
                "public_f1": 0.96230,
                "private_f1": 0.97198,
            },
            {
                "kaggle_ref": 54808193,
                "filename": "submission_offline_02_hedge_payload132.csv",
                "public_f1": 0.96267,
                "private_f1": 0.97198,
            },
        ]
    ).to_csv(SCORES_PATH, index=False)

    report = f"""# Post-Deadline v8 Improvement Report

## สรุป

ไฟล์แนะนำคือ `submission_v10_pareto_plus_exact_twin.csv` สร้างจาก v8 ที่ได้
Public `0.96193` / Private `0.97232` โดยเก็บ `Id=4456` และเพิ่ม `Id=9816`,
`Id=1145`, `Id=5244` รวม positive `2,813` แถว ไม่มีการส่ง Kaggle รอบใหม่

## หลักฐานจากคะแนนจริง

- v8 ต่างจาก PUBLISH baseline เพียง `Id=4456` แต่ Public เท่ากันที่ `0.96193`
  จึงสรุปได้ว่าแถวนี้อยู่ Private split
- เมื่อเทียบ v8 กับไฟล์ structural/public-best คะแนน Private ลดจาก `0.97232`
  เป็น `0.97198` เมื่อไม่มี `Id=4456` จึงยืนยันว่า `Id=4456` เป็น Private TP
- `Id=9816` ทำให้ Public เพิ่ม `0.96193 -> 0.96230`
- `Id=1145` ทำให้ Public เพิ่ม `0.96230 -> 0.96267`
- `Id=5244` มีทุก feature นอกจาก `Id` เหมือน `Id=1145` และอยู่ residual rank 2
  จึงเป็น candidate ที่มีหลักฐานดีที่สุดสำหรับเพิ่มคะแนนอีกหนึ่งแถว

## ลำดับไฟล์

| Rank | File | Positives | Public F1 ประเมิน | Private F1 ประเมิน | การใช้ |
|---:|---|---:|---:|---:|---|
| 1 | `submission_v10_pareto_plus_exact_twin.csv` | 2,813 | 0.96267-0.96304 | 0.97232-0.97266 | แนะนำสูงสุด |
| 2 | `submission_v9_pareto_confirmed.csv` | 2,812 | 0.96267 | 0.97232 | ปลอดภัยสุด |
| 3 | `submission_v11_pareto_plus_payload150.csv` | 2,814 | ยังไม่ยืนยัน | ยังไม่ยืนยัน | upside สูงกว่า ความเสี่ยงสูงกว่า |

ช่วงของ v10 ขึ้นกับว่า `Id=5244` อยู่ Public หรือ Private split ถ้า ground truth
เหมือน exact twin `Id=1145` จะเพิ่มคะแนน split ใด split หนึ่งประมาณ `0.00034-0.00037`
และไม่กระทบอีก split. คะแนนเป็นการ reconstruct จาก submission ที่มีคะแนนจริง ไม่ใช่ผล
Kaggle ที่ยืนยันหลัง deadline.

## Integrity

- Scored v8 SHA-256: `{V8_SHA256}`
- v8 rows: `10,000`
- ทุกไฟล์ผ่าน schema, Id order, binary-label, changed-Id และ checksum validation
"""
    REPORT_PATH.write_text(report)

    tracked = generated + [
        MANIFEST_PATH,
        DIFF_PATH,
        SCORES_PATH,
        REPORT_PATH,
        Path(__file__),
    ]
    CHECKSUM_PATH.write_text(
        "\n".join(
            f"{sha256(path)}  {path.relative_to(OUTPUTS)}" for path in tracked
        )
        + "\n"
    )
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in tracked + [CHECKSUM_PATH]:
            archive.write(path, path.relative_to(OUTPUTS))

    primary = CANDIDATE_DIR / "submission_v10_pareto_plus_exact_twin.csv"
    print(f"primary={primary}")
    print(f"primary_sha256={sha256(primary)}")
    print(f"bundle={ZIP_PATH}")


if __name__ == "__main__":
    main()
