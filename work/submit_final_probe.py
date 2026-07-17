from pathlib import Path

import pandas as pd

from submit_improved import attack_mask


ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data" / "X_train.csv"
TEST = ROOT / "data" / "X_test.csv"
SAMPLE = ROOT / "data" / "sample_submission.csv"
OUTPUT = ROOT / "outputs" / "submission_final_probe.csv"


def main() -> None:
    train = pd.read_csv(TRAIN, low_memory=False)
    test = pd.read_csv(TEST, low_memory=False)
    sample = pd.read_csv(SAMPLE)

    labels = attack_mask(train, test)

    packet_columns = [
        column
        for column in test.columns
        if column not in {"Id", "tcp.stream", "tcp.analysis.initial_rtt"}
    ]
    normal_packets = pd.util.hash_pandas_object(train[packet_columns], index=False)
    test_packets = pd.util.hash_pandas_object(test[packet_columns], index=False)
    novel_packet = ~test_packets.isin(set(normal_packets))

    publish_window = test["mqtt.msgtype"].eq(3) & test["tcp.window_size"].eq(256)
    publish_capture_context = publish_window & (novel_packet | test["tcp.stream"].ne(1))
    labels |= publish_capture_context

    submission = sample[["Id"]].copy()
    submission["label"] = labels.astype("int8").to_numpy()
    if len(submission) != len(test) or not submission["Id"].equals(test["Id"]):
        raise RuntimeError("Submission Id order does not match X_test")
    if not set(submission["label"].unique()) <= {0, 1}:
        raise RuntimeError("Invalid labels")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    submission.to_csv(OUTPUT, index=False)
    print(f"output={OUTPUT}")
    print(f"rows={len(submission)}")
    print(f"positive={int(submission['label'].sum())}")
    print(f"publish_context_added={int((publish_capture_context & ~attack_mask(train, test)).sum())}")


if __name__ == "__main__":
    main()
