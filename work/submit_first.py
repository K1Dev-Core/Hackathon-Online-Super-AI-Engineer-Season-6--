from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data" / "X_train.csv"
TEST = ROOT / "data" / "X_test.csv"
SAMPLE = ROOT / "data" / "sample_submission.csv"
OUTPUT = ROOT / "outputs" / "submission_first.csv"


def attack_signature_mask(train: pd.DataFrame, test: pd.DataFrame) -> pd.Series:
    # Attack signatures documented by the challenge's MQTT capture setup.
    syn_flood = (
        test["frame.len"].eq(54)
        & test["tcp.window_size"].eq(512)
        & test["tcp.flags.syn"].eq(1)
        & test["tcp.flags.ack"].eq(0)
    )
    bad_connect = test["mqtt.msgtype"].eq(1) & test["mqtt.kalive"].isin([60, 3600])
    invalid_subscription = test["mqtt.msgtype"].isin([8, 9])
    publish_attack = test["mqtt.msgtype"].eq(3) & test["mqtt.len"].isin([19, 44])

    # A few attack payloads are split into TCP rows that Wireshark cannot decode as MQTT.
    novel_fields = np.zeros(len(test), dtype=np.int8)
    for column in train.columns:
        if column in {"Id", "tcp.stream"}:
            continue
        train_values = set(train[column].dropna().tolist())
        novel_fields += (~test[column].isin(train_values) & test[column].notna()).to_numpy()
    undecoded_attack_payload = (
        test["mqtt.msgtype"].isna()
        & test["tcp.len"].gt(0)
        & (novel_fields >= 3)
    )

    return syn_flood | bad_connect | invalid_subscription | publish_attack | undecoded_attack_payload


def main() -> None:
    train = pd.read_csv(TRAIN)
    test = pd.read_csv(TEST)
    sample = pd.read_csv(SAMPLE)

    train_flags = attack_signature_mask(train, train)
    if int(train_flags.sum()) != 0:
        raise RuntimeError(f"Signature rules flagged {int(train_flags.sum())} normal training rows")

    labels = attack_signature_mask(train, test).astype("int8")
    submission = sample[["Id"]].copy()
    submission["label"] = labels.to_numpy()
    if len(submission) != len(test) or not submission["Id"].equals(test["Id"]):
        raise RuntimeError("Submission Id order does not match X_test")
    if submission["label"].isna().any() or not set(submission["label"].unique()).issubset({0, 1}):
        raise RuntimeError("Invalid labels")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    submission.to_csv(OUTPUT, index=False)
    print(f"output={OUTPUT}")
    print(f"rows={len(submission)}")
    print(f"positive={int(submission['label'].sum())}")
    print(f"negative={int((submission['label'] == 0).sum())}")


if __name__ == "__main__":
    main()
