"""Build final handoff from external PCAP evidence without uploading."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
TEST_PATH = ROOT / "data" / "X_test.csv"
SUBMISSION_PATH = OUTPUTS / "submission_rank1_structural_plus1.csv"
PCAP_AUDIT_PATH = OUTPUTS / "pcap_coverage_audit.csv"
LOCK_PATH = OUTPUTS / "submission_pcap_evidence_lock.csv"
REPORT_PATH = OUTPUTS / "pcap_evidence_decision_report.md"
CHECKSUM_PATH = OUTPUTS / "pcap_evidence_checksums.sha256"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_submission(submission: pd.DataFrame, test: pd.DataFrame) -> None:
    if list(submission.columns) != ["Id", "label"]:
        raise RuntimeError("Submission columns must be Id,label")
    if len(submission) != len(test) or not submission["Id"].equals(test["Id"]):
        raise RuntimeError("Submission Id order does not match X_test")
    if submission["Id"].duplicated().any():
        raise RuntimeError("Submission has duplicate Id values")
    if submission["label"].isna().any() or not set(submission["label"].unique()) <= {0, 1}:
        raise RuntimeError("Submission labels must be binary and non-null")


def main() -> None:
    test = pd.read_csv(TEST_PATH, low_memory=False)
    submission = pd.read_csv(SUBMISSION_PATH)
    audit = pd.read_csv(PCAP_AUDIT_PATH)
    validate_submission(submission, test)

    audit_total = audit.loc[audit["source_pcap"].eq("UNION")].iloc[0]
    additions = int(audit_total["matched_current_normal"])
    if additions != 0:
        raise RuntimeError("PCAP audit has unresolved candidate additions")

    shutil.copyfile(SUBMISSION_PATH, LOCK_PATH)
    if sha256(LOCK_PATH) != sha256(SUBMISSION_PATH):
        raise RuntimeError("Evidence lock differs from approved submission")

    report = "\n".join(
        [
            "# PCAP Evidence Decision",
            "",
            "## Current Position",
            "",
            "- Public leaderboard checked 2026-07-18: 0.97261 first, 0.96963 second, 0.96230 this submission third.",
            "- Gap to first: 0.01031.",
            "",
            "## Decision",
            "",
            "- Approved file: `submission_pcap_evidence_lock.csv`.",
            "- It is byte-identical to `submission_rank1_structural_plus1.csv`, the scored 0.96230 submission.",
            "- Do not submit a new file from this audit. No candidate addition is evidence-backed.",
            "- No artifact is claimed to beat 0.97261. That claim would be unsupported.",
            "",
            "## PCAP Audit",
            "",
            f"- Attack PCAPs scanned: `{len(audit) - 1}`.",
            f"- Source bytes scanned: `{int(audit_total['pcap_bytes'])}`.",
            f"- TCP packets scanned: `{int(audit_total['tcp_rows'])}`.",
            f"- Exact test matches: `{int(audit_total['exact_test_matches'])}`.",
            f"- Matched existing attack labels: `{int(audit_total['matched_current_attack'])}`.",
            f"- Candidate additions: `{additions}`.",
            "",
            "## Integrity",
            "",
            f"- Rows: `{len(submission)}`.",
            f"- Positive labels: `{int(submission['label'].sum())}`.",
            f"- SHA256: `{sha256(LOCK_PATH)}`.",
            "- Id order and binary labels were validated against `data/X_test.csv`.",
            "",
        ]
    )
    REPORT_PATH.write_text(report, encoding="ascii")
    CHECKSUM_PATH.write_text(
        "\n".join(
            [
                f"{sha256(LOCK_PATH)}  outputs/{LOCK_PATH.name}",
                f"{sha256(REPORT_PATH)}  outputs/{REPORT_PATH.name}",
                f"{sha256(PCAP_AUDIT_PATH)}  outputs/{PCAP_AUDIT_PATH.name}",
                f"{sha256(ROOT / 'work' / 'audit_pcap_coverage.py')}  work/audit_pcap_coverage.py",
            ]
        )
        + "\n",
        encoding="ascii",
    )
    print(f"lock={LOCK_PATH}")
    print(f"sha256={sha256(LOCK_PATH)}")
    print(f"report={REPORT_PATH}")


if __name__ == "__main__":
    main()
