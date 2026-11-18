
import csv
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent / "results.csv"

THRESHOLDS = [0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90]


def load_results():
    results = []

    with CSV_PATH.open("r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            results.append({
                "same_person": row["same_person"].strip().lower() == "true",
                "similarity": float(row["similarity"])
            })

    return results


def evaluate_threshold(results, threshold):
    tp = tn = fp = fn = 0

    for result in results:
        actual_same = result["same_person"]
        predicted_same = result["similarity"] >= threshold

        if actual_same and predicted_same:
            tp += 1
        elif not actual_same and not predicted_same:
            tn += 1
        elif not actual_same and predicted_same:
            fp += 1
        else:
            fn += 1

    total = tp + tn + fp + fn

    accuracy = (tp + tn) / total if total else 0
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    false_match_rate = fp / (fp + tn) if (fp + tn) else 0

    return accuracy, precision, recall, false_match_rate, tp, fp, fn


def main():
    results = load_results()

    print(f"\nLoaded {len(results)} labelled comparisons.")
    print("\n--- FaceMatch Threshold Comparison ---")

    print(
        f"{'Threshold':<12}"
        f"{'Accuracy':<12}"
        f"{'Precision':<12}"
        f"{'Recall':<12}"
        f"{'FMR':<12}"
        f"{'TP':<6}"
        f"{'FP':<6}"
        f"{'FN':<6}"
    )

    print("-" * 78)

    for threshold in THRESHOLDS:
        accuracy, precision, recall, fmr, tp, fp, fn = (
            evaluate_threshold(results, threshold)
        )

        print(
            f"{threshold:<12.2f}"
            f"{accuracy:<12.2%}"
            f"{precision:<12.2%}"
            f"{recall:<12.2%}"
            f"{fmr:<12.2%}"
            f"{tp:<6}"
            f"{fp:<6}"
            f"{fn:<6}"
        )


if __name__ == "__main__":
    main()
