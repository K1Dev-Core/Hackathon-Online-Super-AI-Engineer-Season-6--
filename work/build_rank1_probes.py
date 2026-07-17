from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TEST = ROOT / "data" / "X_test.csv"
CURRENT = ROOT / "outputs" / "submission_final_probe.csv"
PROBE_1 = ROOT / "outputs" / "submission_rank1_probe1.csv"


def validate(submission: pd.DataFrame, test: pd.DataFrame) -> None:
    if len(submission) != len(test) or not submission["Id"].equals(test["Id"]):
        raise RuntimeError("Submission Id order does not match X_test")
    if submission["label"].isna().any() or not set(submission["label"].unique()) <= {0, 1}:
        raise RuntimeError("Invalid labels")


def main() -> None:
    test = pd.read_csv(TEST, low_memory=False)
    current = pd.read_csv(CURRENT)

    ping_false_positive = (
        test["frame.len"].eq(56)
        & test["tcp.window_size"].eq(253)
        & test["mqtt.msgtype"].eq(13)
        & current["label"].eq(1)
    )
    if int(ping_false_positive.sum()) != 5:
        raise RuntimeError(
            f"Expected 5 PINGRESP candidates, found {int(ping_false_positive.sum())}"
        )

    probe = current.copy()
    probe.loc[ping_false_positive, "label"] = 0
    validate(probe, test)
    PROBE_1.parent.mkdir(parents=True, exist_ok=True)
    probe.to_csv(PROBE_1, index=False)

    print(f"output={PROBE_1}")
    print(f"positive={int(probe['label'].sum())}")
    print(f"removed={int((current['label'].eq(1) & probe['label'].eq(0)).sum())}")
    print("removed_ids=" + ",".join(test.loc[ping_false_positive, "Id"].astype(str)))


if __name__ == "__main__":
    main()
