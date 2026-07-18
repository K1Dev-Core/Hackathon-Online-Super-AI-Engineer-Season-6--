"""Validate protocol payload candidates after v23."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
CANDIDATES = OUTPUTS / "post_v23_payload_candidates"
V23_SHA256 = "d5f4779d6687b5d40948063a1ebf149b3837fe0a7e5d9dffbf8494a029efd4b6"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    test = pd.read_csv(ROOT / "data" / "X_test.csv", low_memory=False)
    baseline_path = CANDIDATES / "submission_v23_confirmed_baseline.csv"
    baseline = pd.read_csv(baseline_path)
    assert digest(baseline_path) == V23_SHA256
    assert int(baseline["label"].sum()) == 2_832

    stream2 = {778, 2_704, 5_804, 6_155, 6_546, 6_572, 6_803, 7_784, 7_935}
    stream4 = {4_475, 7_661, 8_393}
    expected = {
        "submission_v24_stream2_mqtt_payload.csv": (stream2, 2_841),
        "submission_v25_stream2_plus_stream4_payload.csv": (stream2 | stream4, 2_844),
        "submission_v26_stream_payload_plus_connect.csv": (stream2 | stream4 | {4_550}, 2_845),
    }
    for filename, (ids, positives) in expected.items():
        candidate = pd.read_csv(CANDIDATES / filename)
        assert list(candidate.columns) == ["Id", "label"]
        assert len(candidate) == len(test) == 10_000
        assert candidate["Id"].equals(test["Id"])
        assert candidate["Id"].is_unique
        assert set(candidate["label"].unique()) <= {0, 1}
        assert not candidate["label"].isna().any()
        changed = set(candidate.loc[candidate["label"].ne(baseline["label"]), "Id"])
        assert changed == ids
        assert int(candidate["label"].sum()) == positives
        for confirmed_id in [4456, 5516, 6011, 4057, 4933, 1980, 5475, 1805, 55, 4082]:
            assert int(candidate.loc[candidate["Id"].eq(confirmed_id), "label"].iloc[0]) == 1

    manifest = pd.read_csv(OUTPUTS / "post_v23_payload_manifest.csv")
    assert manifest["rank"].tolist() == [1, 2, 3]
    assert manifest.iloc[0]["filename"] == "submission_v24_stream2_mqtt_payload.csv"
    for row in manifest.itertuples(index=False):
        assert digest(CANDIDATES / row.filename) == row.sha256

    scores = pd.read_csv(OUTPUTS / "post_v23_payload_observed_scores.csv")
    assert scores["kaggle_ref"].tolist() == [54810019, 54809954]
    assert scores["public_f1"].tolist() == [0.96598, 0.96461]
    assert scores["private_f1"].tolist() == [0.97541, 0.97412]

    checksums: dict[str, str] = {}
    for line in (OUTPUTS / "post_v23_payload_checksums.sha256").read_text().splitlines():
        checksum, relative = line.split("  ", 1)
        checksums[relative] = checksum
        assert digest(OUTPUTS / relative) == checksum

    with zipfile.ZipFile(OUTPUTS / "superai6_post_v23_payload_bundle.zip") as archive:
        names = set(archive.namelist())
        for relative, checksum in checksums.items():
            assert relative in names
            assert hashlib.sha256(archive.read(relative)).hexdigest() == checksum

    print(f"validated_candidates={len(expected)}")
    print(f"primary_sha256={digest(CANDIDATES / manifest.iloc[0]['filename'])}")


if __name__ == "__main__":
    main()
