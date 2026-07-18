"""Validate the post-rank-1 handoff and its explicit safety ordering."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
VARIANTS = OUTPUTS / "post_rank1_variants"

LEADER = "submission_post_rank1_01_current_leader.csv"
FALLBACK = "submission_post_rank1_02_previous_champion.csv"
REJECTED = "submission_post_rank1_03_rejected_payload132.csv"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    test = pd.read_csv(ROOT / "data" / "X_test.csv", low_memory=False)
    source_leader = pd.read_csv(OUTPUTS / "submission_rank1_structural_plus1.csv")
    source_champion = pd.read_csv(OUTPUTS / "submission_rank1_best_publish_complete.csv")
    primary = pd.read_csv(VARIANTS / LEADER)
    fallback = pd.read_csv(VARIANTS / FALLBACK)
    rejected = pd.read_csv(VARIANTS / REJECTED)

    for submission in [primary, fallback, rejected]:
        assert list(submission.columns) == ["Id", "label"]
        assert len(submission) == len(test) == 10_000
        assert submission["Id"].equals(test["Id"])
        assert submission["Id"].is_unique
        assert set(submission["label"].unique()) <= {0, 1}

    assert primary.equals(source_leader)
    assert fallback.equals(source_champion)
    assert int(primary["label"].sum()) == 2_810
    assert int(fallback["label"].sum()) == 2_809
    additions = rejected.loc[rejected["label"].eq(1) & primary["label"].eq(0), "Id"]
    assert additions.tolist() == [1_145]

    ranking = pd.read_csv(
        OUTPUTS / "post_rank1_variant_ranking.csv",
        dtype={"observed_public_score": str},
    )
    assert ranking["rank"].tolist() == [1, 2, 3]
    assert ranking["filename"].tolist() == [LEADER, FALLBACK, REJECTED]
    assert ranking["status"].tolist() == [
        "APPROVED_PRIMARY",
        "FALLBACK_ONLY",
        "REJECTED_FALSE_POSITIVE_RISK",
    ]
    assert ranking.loc[0, "observed_public_score"] == "0.96230"
    assert ranking.loc[0, "submission_instruction"] == "SUBMIT_THIS_ONLY"

    checksums: dict[str, str] = {}
    for line in (OUTPUTS / "post_rank1_variant_checksums.sha256").read_text().splitlines():
        checksum, relative = line.split("  ", 1)
        checksums[relative] = checksum
        assert digest(OUTPUTS / relative) == checksum

    bundle = OUTPUTS / "superai6_post_rank1_review_bundle.zip"
    with zipfile.ZipFile(bundle) as archive:
        names = set(archive.namelist())
        for relative, checksum in checksums.items():
            assert relative in names
            assert hashlib.sha256(archive.read(relative)).hexdigest() == checksum
        assert "post_rank1_variant_checksums.sha256" in names

    print("validated_post_rank1_variants=3")
    print(f"approved_primary_sha256={digest(VARIANTS / LEADER)}")
    print(f"bundle_sha256={digest(bundle)}")


if __name__ == "__main__":
    main()
