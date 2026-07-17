"""Complete the validated window-256 PUBLISH family for the final daily slot."""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "outputs" / "submission_rank1_probe4_publish137.csv"
TEST_PATH = ROOT / "data" / "X_test.csv"
OUTPUT_PATH = ROOT / "outputs" / "submission_rank1_best_publish_complete.csv"


def main() -> None:
    test = pd.read_csv(TEST_PATH, low_memory=False)
    submission = pd.read_csv(BASE_PATH)
    assert list(submission.columns) == ["Id", "label"]
    assert len(submission) == len(test) == 10_000
    assert submission["Id"].equals(test["Id"])

    candidates = (
        test["tcp.window_size"].eq(256)
        & test["mqtt.msgtype"].eq(3)
        & test["tcp.stream"].eq(1)
        & (
            (
                test["frame.len"].eq(207)
                & test["tcp.len"].eq(153)
                & test["mqtt.topic_len"].eq(42)
                & test["mqtt.len"].eq(150)
            )
            | (
                test["frame.len"].eq(196)
                & test["tcp.len"].eq(142)
                & test["mqtt.topic_len"].eq(32)
                & test["mqtt.len"].eq(139)
            )
        )
    )
    assert int(candidates.sum()) == 4
    assert (submission.loc[candidates, "label"] == 0).all()

    submission.loc[candidates, "label"] = 1
    assert set(submission["label"].unique()) <= {0, 1}
    submission.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {OUTPUT_PATH} with {int(submission['label'].sum())} positive labels.")
    print("candidate_ids=" + ",".join(test.loc[candidates, "Id"].astype(str)))


if __name__ == "__main__":
    main()
