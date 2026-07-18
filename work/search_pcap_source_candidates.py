"""Search raw external PCAP chunks for exact competition-test fingerprints."""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import tempfile
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from kaggle import KaggleApi
from pandas.util import hash_pandas_object


ROOT = Path(__file__).resolve().parents[1]
DATASET = "alaaalatram/dosddos-mqtt-iot"
KEY_COLUMNS = [
    "frame.len",
    "tcp.stream",
    "tcp.analysis.initial_rtt",
    "tcp.len",
    "tcp.window_size",
    "tcp.flags.syn",
    "tcp.flags.reset",
    "tcp.flags.ack",
]


def key_hashes(frame: pd.DataFrame) -> np.ndarray:
    values = frame[KEY_COLUMNS].apply(pd.to_numeric, errors="coerce").astype("float64")
    values["tcp.analysis.initial_rtt"] = values["tcp.analysis.initial_rtt"].round(6)
    return hash_pandas_object(values.fillna(-999_999.0), index=False).to_numpy(dtype="uint64")


def natural_key(value: str) -> list[int | str]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", value)]


def list_pcaps(mode: str) -> list[tuple[str, int]]:
    api = KaggleApi()
    api.authenticate()
    token: str | None = None
    files: list[tuple[str, int]] = []
    while True:
        response = api.dataset_list_files(DATASET, page_size=100, page_token=token)
        for item in response.files:
            name = item.name
            if not name.lower().endswith(".pcap") or "/Pcap Files/" not in name:
                continue
            is_normal = "/NormalData/" in name
            if (mode == "normal") != is_normal:
                continue
            files.append((name, int(item.total_bytes)))
        token = response.next_page_token
        if not token:
            break
    return sorted(files, key=lambda item: natural_key(item[0]))


def source_metadata(source_name: str) -> tuple[str, str]:
    parts = source_name.split("/")
    if "/NormalData/" in source_name:
        return "Normal", "Normal"
    family = parts[1] if len(parts) > 1 else "Unknown"
    traffic_mode = parts[2] if len(parts) > 2 else "Unknown"
    return family, traffic_mode


def extract_matches(
    pcap_path: Path,
    tshark: str,
    test_hash_set: set[int],
) -> tuple[set[int], int]:
    command = [
        tshark,
        "-r",
        str(pcap_path),
        "-Y",
        "tcp",
        "-T",
        "fields",
        "-E",
        "header=y",
        "-E",
        "separator=,",
    ]
    for column in KEY_COLUMNS:
        command.extend(["-e", column])

    with tempfile.NamedTemporaryFile(mode="w+b", suffix=".csv") as extracted:
        result = subprocess.run(command, stdout=extracted, stderr=subprocess.PIPE, check=False)
        if result.returncode != 0:
            error = result.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"tshark exited {result.returncode}: {error}")
        extracted.flush()
        extracted.seek(0)
        matched: set[int] = set()
        row_count = 0
        for chunk in pd.read_csv(extracted.name, chunksize=100_000, low_memory=False):
            row_count += len(chunk)
            chunk_hashes = set(key_hashes(chunk).tolist())
            matched.update(chunk_hashes.intersection(test_hash_set))
    return matched, row_count


def download_and_scan(
    source_name: str,
    expected_bytes: int,
    tshark: str,
    test_hash_set: set[int],
    retries: int,
) -> dict[str, int | str]:
    family, traffic_mode = source_metadata(source_name)
    last_error = ""
    for attempt in range(1, retries + 1):
        try:
            with tempfile.TemporaryDirectory(prefix="superai6-pcap-search-") as temporary:
                temporary_path = Path(temporary)
                api = KaggleApi()
                api.authenticate()
                api.dataset_download_file(DATASET, source_name, path=temporary_path, force=True, quiet=True)
                archives = list(temporary_path.glob("*.zip"))
                if len(archives) != 1:
                    raise RuntimeError(f"expected one zip, found {len(archives)}")
                with zipfile.ZipFile(archives[0]) as archive:
                    bad_member = archive.testzip()
                    if bad_member is not None:
                        raise RuntimeError(f"corrupt zip member: {bad_member}")
                    pcap_members = [name for name in archive.namelist() if name.lower().endswith(".pcap")]
                    if len(pcap_members) != 1:
                        raise RuntimeError(f"expected one PCAP member, found {len(pcap_members)}")
                    archive.extract(pcap_members[0], path=temporary_path)
                    pcap_path = temporary_path / pcap_members[0]
                if expected_bytes and pcap_path.stat().st_size != expected_bytes:
                    raise RuntimeError(
                        f"PCAP size {pcap_path.stat().st_size} != manifest {expected_bytes}"
                    )
                matched_hashes, tcp_rows = extract_matches(pcap_path, tshark, test_hash_set)
                return {
                    "source_pcap": source_name,
                    "family": family,
                    "traffic_mode": traffic_mode,
                    "pcap_bytes": pcap_path.stat().st_size,
                    "tcp_rows": tcp_rows,
                    "matched_hashes": "|".join(str(value) for value in sorted(matched_hashes)),
                    "exact_hash_matches": len(matched_hashes),
                    "status": "OK",
                    "attempts": attempt,
                    "error": "",
                }
        except Exception as error:  # noqa: BLE001 - each source failure must be recorded and retried.
            last_error = str(error)
            if attempt < retries:
                time.sleep(2**attempt)
    return {
        "source_pcap": source_name,
        "family": family,
        "traffic_mode": traffic_mode,
        "pcap_bytes": expected_bytes,
        "tcp_rows": 0,
        "matched_hashes": "",
        "exact_hash_matches": 0,
        "status": "ERROR",
        "attempts": retries,
        "error": last_error,
    }


def add_test_evidence(results: pd.DataFrame, test: pd.DataFrame, labels: pd.Series) -> pd.DataFrame:
    test_hashes = key_hashes(test)
    hash_to_ids: dict[int, list[int]] = {}
    for row_hash, test_id in zip(test_hashes, test["Id"], strict=True):
        hash_to_ids.setdefault(int(row_hash), []).append(int(test_id))
    label_by_id = dict(zip(test["Id"].astype(int), labels.astype(int), strict=True))

    attack_ids: list[str] = []
    normal_ids: list[str] = []
    for hashes in results["matched_hashes"].fillna(""):
        ids: set[int] = set()
        for value in str(hashes).split("|"):
            if value:
                ids.update(hash_to_ids.get(int(value), []))
        attack = sorted(test_id for test_id in ids if label_by_id[test_id] == 1)
        normal = sorted(test_id for test_id in ids if label_by_id[test_id] == 0)
        attack_ids.append("|".join(str(value) for value in attack))
        normal_ids.append("|".join(str(value) for value in normal))
    results["matched_current_attack_ids"] = attack_ids
    results["matched_current_normal_ids"] = normal_ids
    results["matched_current_attack"] = results["matched_current_attack_ids"].map(
        lambda value: 0 if not value else len(value.split("|"))
    )
    results["matched_current_normal"] = results["matched_current_normal_ids"].map(
        lambda value: 0 if not value else len(value.split("|"))
    )
    return results


def write_candidates(results: pd.DataFrame, output: Path) -> None:
    evidence: dict[int, list[str]] = {}
    for row in results.itertuples(index=False):
        if row.status != "OK" or not row.matched_current_normal_ids:
            continue
        for value in row.matched_current_normal_ids.split("|"):
            evidence.setdefault(int(value), []).append(row.source_pcap)
    candidates = pd.DataFrame(
        [
            {
                "Id": test_id,
                "source_file_count": len(files),
                "source_pcaps": "|".join(sorted(files)),
            }
            for test_id, files in sorted(evidence.items())
        ]
    )
    if candidates.empty:
        candidates = pd.DataFrame(columns=["Id", "source_file_count", "source_pcaps"])
    output.parent.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(output, index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["attack", "normal"], required=True)
    parser.add_argument("--test", default=ROOT / "data" / "X_test.csv", type=Path)
    parser.add_argument(
        "--submission",
        default=ROOT / "outputs" / "submission_rank1_structural_plus1.csv",
        type=Path,
    )
    parser.add_argument("--test-ids", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--candidate-output", required=True, type=Path)
    parser.add_argument("--tshark", default="tshark")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    test = pd.read_csv(args.test, low_memory=False)
    submission = pd.read_csv(args.submission)
    if not submission["Id"].equals(test["Id"]):
        raise RuntimeError("Submission Id order does not match test data")
    labels = submission["label"].astype("int8")
    if args.test_ids:
        selected_ids = set(pd.read_csv(args.test_ids)["Id"].astype(int))
        selected = test["Id"].isin(selected_ids)
        test = test.loc[selected].reset_index(drop=True)
        labels = labels.loc[selected].reset_index(drop=True)

    existing = pd.DataFrame()
    processed: set[str] = set()
    if args.output.exists():
        existing = pd.read_csv(args.output, low_memory=False)
        processed = set(existing.loc[existing["status"].eq("OK"), "source_pcap"])

    manifest = list_pcaps(args.mode)
    pending = [item for item in manifest if item[0] not in processed]
    pending = pending[args.start :]
    if args.limit is not None:
        pending = pending[: args.limit]
    test_hash_set = set(key_hashes(test).tolist())
    print(
        f"mode={args.mode} manifest={len(manifest)} processed={len(processed)} "
        f"pending={len(pending)} test_rows={len(test)}",
        flush=True,
    )

    new_rows: list[dict[str, int | str]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                download_and_scan,
                source_name,
                expected_bytes,
                args.tshark,
                test_hash_set,
                args.retries,
            ): source_name
            for source_name, expected_bytes in pending
        }
        for completed, future in enumerate(as_completed(futures), start=1):
            row = future.result()
            new_rows.append(row)
            current = pd.concat([existing, pd.DataFrame(new_rows)], ignore_index=True)
            current = add_test_evidence(current, test, labels)
            current = current.sort_values("source_pcap").reset_index(drop=True)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            current.to_csv(args.output, index=False)
            write_candidates(current, args.candidate_output)
            print(
                f"progress={completed}/{len(pending)} status={row['status']} "
                f"hash_matches={row['exact_hash_matches']} source={row['source_pcap']}",
                flush=True,
            )

    final = pd.concat([existing, pd.DataFrame(new_rows)], ignore_index=True)
    if not final.empty:
        final = add_test_evidence(final, test, labels)
        final = final.sort_values("source_pcap").reset_index(drop=True)
        final.to_csv(args.output, index=False)
        write_candidates(final, args.candidate_output)
    candidate_count = len(pd.read_csv(args.candidate_output)) if args.candidate_output.exists() else 0
    print(f"candidate_rows={candidate_count}", flush=True)
    print(f"output_sha256={hashlib.sha256(args.output.read_bytes()).hexdigest()}", flush=True)


if __name__ == "__main__":
    main()
