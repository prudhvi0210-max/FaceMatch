
import csv
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent / "results.csv"

THRESHOLD = 0.50


def main():
    tp = 0  # True Positive
    tn = 0  # True Negative
    fp = 0  # False Positive
    fn = 0  # False Negative

    with CSV_PATH.open("r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            actual_same = row["same_person"].strip().lower() == "true"
            similarity = float(row["similarity"])

            predicted_same = similarity >= THRESHOLD

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
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0
    )

    false_match_rate = fp / (fp + tn) if (fp + tn) else 0
    false_non_match_rate = fn / (fn + tp) if (fn + tp) else 0

    print("\n--- FaceMatch Evaluation Metrics ---")
    print(f"Similarity threshold: {THRESHOLD:.2f}")

    print(f"\nTrue Positives (TP): {tp}")
    print(f"True Negatives (TN): {tn}")
    print(f"False Positives (FP): {fp}")
    print(f"False Negatives (FN): {fn}")

    print(f"\nAccuracy: {accuracy:.2%}")
    print(f"Precision: {precision:.2%}")
    print(f"Recall: {recall:.2%}")
    print(f"F1 Score: {f1:.2f}")
    print(f"False Match Rate: {false_match_rate:.2%}")
    print(f"False Non-Match Rate: {false_non_match_rate:.2%}")


if __name__ == "__main__":
    main()
