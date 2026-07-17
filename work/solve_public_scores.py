import math


SCORES = {
    "first": (0.54898, 1160),
    "improved": (0.93152, 2636),
    "control": (0.95649, 2788),
    "pair": (0.91143, 3071),
    "final": (0.95834, 2799),
    "rank1": (0.95971, 2794),
}


def score_options(score: float, max_predictions: int, positives: int) -> list[tuple[int, int]]:
    options = []
    for predicted in range(max_predictions + 1):
        true_positive = round(score * (positives + predicted) / 2)
        if true_positive > min(positives, predicted):
            continue
        exact = 2 * true_positive / (positives + predicted)
        # Kaggle's displayed value may be truncated rather than rounded.
        if score - 0.0000051 <= exact < score + 0.0000101:
            options.append((predicted, true_positive))
    return options


def overlap_feasible(
    pair_count: int,
    pair_positive: int,
    final_count: int,
    final_positive: int,
) -> bool:
    for overlap_count in range(8):
        pair_only_count = pair_count - overlap_count
        final_only_count = final_count - overlap_count
        if not (0 <= pair_only_count <= 276 and 0 <= final_only_count <= 4):
            continue
        for overlap_positive in range(overlap_count + 1):
            pair_only_positive = pair_positive - overlap_positive
            final_only_positive = final_positive - overlap_positive
            if (
                0 <= pair_only_positive <= pair_only_count
                and 0 <= final_only_positive <= final_only_count
            ):
                return True
    return False


def count_z(count: int, group_size: int) -> float:
    if group_size == 0:
        return 0.0
    return (count - group_size / 2) / math.sqrt(group_size / 4)


def main() -> None:
    solutions = []
    for positives in range(900, 2001):
        options = {
            name: score_options(score, max_predictions, positives)
            for name, (score, max_predictions) in SCORES.items()
        }
        if any(not values for values in options.values()):
            continue

        for first_count, first_positive in options["first"]:
            for improved_count, improved_positive in options["improved"]:
                added_count = improved_count - first_count
                added_positive = improved_positive - first_positive
                if not (0 <= added_count <= 1476 and 0 <= added_positive <= added_count):
                    continue
                for control_count, control_positive in options["control"]:
                    control_added_count = control_count - improved_count
                    control_added_positive = control_positive - improved_positive
                    if not (
                        0 <= control_added_count <= 152
                        and 0 <= control_added_positive <= control_added_count
                    ):
                        continue
                    for pair_count, pair_positive in options["pair"]:
                        pair_added_count = pair_count - control_count
                        pair_added_positive = pair_positive - control_positive
                        if not (
                            0 <= pair_added_count <= 283
                            and 0 <= pair_added_positive <= pair_added_count
                        ):
                            continue
                        for final_count, final_positive in options["final"]:
                            final_added_count = final_count - control_count
                            final_added_positive = final_positive - control_positive
                            if not (
                                0 <= final_added_count <= 11
                                and 0 <= final_added_positive <= final_added_count
                            ):
                                continue
                            if not overlap_feasible(
                                pair_added_count,
                                pair_added_positive,
                                final_added_count,
                                final_added_positive,
                            ):
                                continue
                            for rank1_count, rank1_positive in options["rank1"]:
                                removed_count = final_count - rank1_count
                                removed_positive = final_positive - rank1_positive
                                if not (0 <= removed_count <= 5 and 0 <= removed_positive <= removed_count):
                                    continue
                                z2 = sum(
                                    count_z(count, size) ** 2
                                    for count, size in [
                                        (first_count, 1160),
                                        (added_count, 1476),
                                        (control_added_count, 152),
                                        (pair_added_count, 283),
                                        (final_added_count, 11),
                                        (removed_count, 5),
                                    ]
                                )
                                solutions.append(
                                    (
                                        z2,
                                        positives,
                                        (first_count, first_positive),
                                        (improved_count, improved_positive),
                                        (control_count, control_positive),
                                        (pair_count, pair_positive),
                                        (final_count, final_positive),
                                        (rank1_count, rank1_positive),
                                    )
                                )

    solutions.sort()
    print(f"solutions={len(solutions)}")
    for first_fp_limit in [0, 1, 5, 10, 20, 30]:
        filtered = [
            solution
            for solution in solutions
            if solution[2][0] - solution[2][1] <= first_fp_limit
        ]
        if filtered:
            print(f"best_first_fp_le_{first_fp_limit}={filtered[0]}")
    for control_fp_limit in [0, 1, 2, 4]:
        filtered = [
            solution
            for solution in solutions
            if (solution[4][0] - solution[3][0])
            - (solution[4][1] - solution[3][1])
            <= control_fp_limit
        ]
        if filtered:
            print(f"best_control_fp_le_{control_fp_limit}={filtered[0]}")
    for solution in solutions[:50]:
        z2, positives, first, improved, control, pair, final, rank1 = solution
        print(
            f"z2={z2:.3f} P={positives} "
            f"first={first} improved={improved} control={control} "
            f"pair={pair} final={final} "
            f"rank1={rank1} "
            f"control_add=({control[0]-improved[0]},{control[1]-improved[1]}) "
            f"pair_add=({pair[0]-control[0]},{pair[1]-control[1]}) "
            f"final_add=({final[0]-control[0]},{final[1]-control[1]})"
            f" removed=({final[0]-rank1[0]},{final[1]-rank1[1]})"
        )


if __name__ == "__main__":
    main()
