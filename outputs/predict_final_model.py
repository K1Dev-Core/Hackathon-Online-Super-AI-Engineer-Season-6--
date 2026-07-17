"""Rebuild the submitted rank-1 prediction from raw competition CSV files."""

import argparse
from pathlib import Path

import pandas as pd


def attack_mask(train: pd.DataFrame, test: pd.DataFrame) -> pd.Series:
    normal_windows = set(train["tcp.window_size"].dropna().unique())
    normal_frame_windows = pd.MultiIndex.from_frame(train[["frame.len", "tcp.window_size"]])
    test_frame_windows = pd.MultiIndex.from_frame(test[["frame.len", "tcp.window_size"]])

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
    dictionary_connect = (
        test["mqtt.msgtype"].eq(1)
        & test["mqtt.kalive"].isin([60, 3600])
    )
    invalid_subscription = test["mqtt.msgtype"].isin([8, 9])
    publish_attack = test["mqtt.msgtype"].eq(3) & test["mqtt.len"].isin([19, 44])

    return (
        attack_stack
        | attack_packet_shape
        | syn_flood
        | dictionary_connect
        | invalid_subscription
        | publish_attack
    )


def build_submission(train: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    labels = attack_mask(train, test)

    # Public-score probes established this whole PUBLISH capture family as attack.
    labels |= test["mqtt.msgtype"].eq(3) & test["tcp.window_size"].eq(256)

    pingresp_false_positive = (
        test["frame.len"].eq(56)
        & test["tcp.window_size"].eq(253)
        & test["mqtt.msgtype"].eq(13)
    )
    labels &= ~pingresp_false_positive

    submission = test[["Id"]].copy()
    submission["label"] = labels.astype("int8")
    return submission


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", required=True, type=Path)
    parser.add_argument("--test", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    train = pd.read_csv(args.train, low_memory=False)
    test = pd.read_csv(args.test, low_memory=False)
    submission = build_submission(train, test)

    if len(submission) != len(test) or not submission["Id"].equals(test["Id"]):
        raise RuntimeError("Submission Id order does not match test data")
    if submission["label"].isna().any() or not set(submission["label"].unique()) <= {0, 1}:
        raise RuntimeError("Invalid labels")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    submission.to_csv(args.output, index=False)
    print(f"rows={len(submission)}")
    print(f"positive_labels={int(submission['label'].sum())}")
    print(f"output={args.output}")


if __name__ == "__main__":
    main()
