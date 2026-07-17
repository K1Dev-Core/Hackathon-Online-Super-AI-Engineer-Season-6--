from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer


ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data" / "X_train.csv"
TEST = ROOT / "data" / "X_test.csv"
CURRENT = ROOT / "outputs" / "submission_final_probe.csv"
CONTROL = ROOT / "outputs" / "submission_control_novelty.csv"
PAIR = ROOT / "outputs" / "submission_pair_novelty.csv"
OUTPUT = ROOT / "work" / "pseudo_model_scores.csv"

FEATURES = [
    "frame.len",
    "frame.protocols",
    "tcp.stream",
    "tcp.analysis.initial_rtt",
    "tcp.len",
    "tcp.window_size",
    "tcp.flags.syn",
    "tcp.flags.reset",
    "tcp.flags.ack",
    "mqtt.msgtype",
    "mqtt.qos",
    "mqtt.conflag.qos",
    "mqtt.conflag.cleansess",
    "mqtt.kalive",
    "mqtt.username_len",
    "mqtt.passwd_len",
    "mqtt.retain",
    "mqtt.conflag.retain",
    "mqtt.conflag.willflag",
    "mqtt.topic_len",
    "mqtt.len",
    "mqtt.conack.val",
]


def normalize(frame: pd.DataFrame) -> pd.DataFrame:
    mapped = frame[FEATURES].copy()
    mapped["frame.protocols"] = mapped["frame.protocols"].str.endswith(":mqtt").astype("int8")
    return mapped


def main() -> None:
    train = pd.read_csv(TRAIN, low_memory=False)
    test = pd.read_csv(TEST, low_memory=False)
    current = pd.read_csv(CURRENT)["label"].astype(bool)
    control = pd.read_csv(CONTROL)["label"].astype(bool)
    pair = pd.read_csv(PAIR)["label"].astype(bool)

    normal = train.loc[train["tcp.stream"].le(test["tcp.stream"].max())]
    normal_x = normalize(normal)
    positive_x = normalize(test.loc[control])
    train_x = pd.concat([normal_x, positive_x], ignore_index=True)
    train_y = np.concatenate(
        [np.zeros(len(normal_x), dtype="int8"), np.ones(len(positive_x), dtype="int8")]
    )
    imputer = SimpleImputer(strategy="constant", fill_value=-1)
    train_values = imputer.fit_transform(train_x)
    test_values = imputer.transform(normalize(test))

    models = {
        "extra": ExtraTreesClassifier(
            n_estimators=500,
            min_samples_leaf=2,
            max_features=0.9,
            class_weight="balanced",
            n_jobs=-1,
            random_state=20260717,
        ),
        "forest": RandomForestClassifier(
            n_estimators=350,
            min_samples_leaf=2,
            max_features=0.8,
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=20260717,
        ),
        "hist": HistGradientBoostingClassifier(
            learning_rate=0.06,
            max_iter=350,
            max_leaf_nodes=31,
            l2_regularization=2.0,
            class_weight="balanced",
            random_state=20260717,
        ),
    }
    result = test[["Id"] + FEATURES].copy()
    for name, model in models.items():
        model.fit(train_values, train_y)
        result[name] = model.predict_proba(test_values)[:, 1]
    result["ensemble"] = result[["extra", "forest", "hist"]].mean(axis=1)
    result["current"] = current.astype("int8")
    result["final_added"] = (current & ~control).astype("int8")
    result["pair_bad"] = (pair & ~control).astype("int8")
    result.to_csv(OUTPUT, index=False)

    print(f"normal_reference={len(normal)} positive_reference={len(positive_x)}")
    print(f"output={OUTPUT}")
    for group_name, mask in {
        "control_positive": control,
        "remaining": ~current,
        "final_added": current & ~control,
        "pair_bad": pair & ~control,
    }.items():
        print(group_name, result.loc[mask, ["extra", "forest", "hist", "ensemble"]].describe().to_string())
    columns = ["Id", "ensemble", "extra", "forest", "hist"] + FEATURES
    print(result.loc[~current, columns].sort_values("ensemble", ascending=False).head(200).to_string(index=False))


if __name__ == "__main__":
    main()
