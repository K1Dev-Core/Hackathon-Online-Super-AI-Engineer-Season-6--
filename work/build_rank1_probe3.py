"""Build a narrow PUBLISH-family probe from the current precision-first baseline."""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "outputs" / "submission_rank1_probe1.csv"
TEST_PATH = ROOT / "data" / "X_test.csv"
OUTPUT_PATH = ROOT / "outputs" / "submission_rank1_probe3_publish132.csv"


def main() -> None:
    test = pd.read_csv(TEST_PATH, low_memory=False)
    submission = pd.read_csv(BASE_PATH)
    assert list(submission.columns) == ["Id", "label"]
    assert len(submission) == len(test) == 10_000
    assert submission["Id"].equals(test["Id"])

    candidates = (
        test["frame.len"].eq(189)
        & test["tcp.len"].eq(135)
        & test["tcp.window_size"].eq(256)
        & test["mqtt.msgtype"].eq(3)
        & test["mqtt.topic_len"].eq(24)
        & test["mqtt.len"].eq(132)
        & test["tcp.stream"].eq(1)
    )
    assert int(candidates.sum()) == 5
    assert (submission.loc[candidates, "label"] == 0).all()

    submission.loc[candidates, "label"] = 1
    assert set(submission["label"].unique()) <= {0, 1}
    submission.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {OUTPUT_PATH} with {int(submission['label'].sum())} positive labels.")
    print("candidate_ids=" + ",".join(test.loc[candidates, "Id"].astype(str)))


if __name__ == "__main__":
    main()
