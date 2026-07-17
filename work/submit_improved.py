from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data" / "X_train.csv"
TEST = ROOT / "data" / "X_test.csv"
SAMPLE = ROOT / "data" / "sample_submission.csv"
OUTPUT = ROOT / "outputs" / "submission_control_novelty.csv"


def attack_mask(train: pd.DataFrame, test: pd.DataFrame) -> pd.Series:
    normal_windows = set(train["tcp.window_size"].dropna().unique())
    normal_frame_windows = pd.MultiIndex.from_frame(train[["frame.len", "tcp.window_size"]])
    test_frame_windows = pd.MultiIndex.from_frame(test[["frame.len", "tcp.window_size"]])

    # The attack captures use a different TCP stack. This also recovers ACK,
    # reset, and broker-response packets belonging to an attack flow.
    attack_stack = ~test["tcp.window_size"].isin(normal_windows)
    attack_packet_shape = (
        ~test_frame_windows.isin(normal_frame_windows)
        & test["mqtt.msgtype"].ne(3)
    )

    syn_flood = (
        test["frame.len"].eq(54)
        & test["tcp.window_size"].eq(512)
        & test["tcp.flags.syn"].eq(1)
        & test["tcp.flags.ack"].eq(0)
    )
    bad_connect = test["mqtt.msgtype"].eq(1) & test["mqtt.kalive"].isin([60, 3600])
    invalid_subscription = test["mqtt.msgtype"].isin([8, 9])
    publish_attack = test["mqtt.msgtype"].eq(3) & test["mqtt.len"].isin([19, 44])

    return attack_stack | attack_packet_shape | syn_flood | bad_connect | invalid_subscription | publish_attack


def main() -> None:
    train = pd.read_csv(TRAIN, low_memory=False)
    test = pd.read_csv(TEST, low_memory=False)
    sample = pd.read_csv(SAMPLE)

    train_labels = attack_mask(train, train)
    if int(train_labels.sum()) != 0:
        raise RuntimeError(f"Rules flagged {int(train_labels.sum())} normal training rows")

    labels = attack_mask(train, test).astype("int8")
    submission = sample[["Id"]].copy()
    submission["label"] = labels.to_numpy()

    if len(submission) != len(test) or not submission["Id"].equals(test["Id"]):
        raise RuntimeError("Submission Id order does not match X_test")
    if submission["label"].isna().any() or not set(submission["label"].unique()) <= {0, 1}:
        raise RuntimeError("Invalid labels")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    submission.to_csv(OUTPUT, index=False)
    print(f"output={OUTPUT}")
    print(f"rows={len(submission)}")
    print(f"positive={int(submission['label'].sum())}")
    print(f"negative={int((submission['label'] == 0).sum())}")


if __name__ == "__main__":
    main()
