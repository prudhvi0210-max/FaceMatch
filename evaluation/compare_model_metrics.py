
import csv
from pathlib import Path

EVALUATION_DIR = Path(__file__).resolve().parent

MODEL_FILES = {
    "FaceNet512": EVALUATION_DIR / "results_facenet512.csv",
    "ArcFace": EVALUATION_DIR / "results_arcface.csv"
}

THRESHOLDS = [round(i / 100, 2) for i in range(0, 101, 5)]


def load_results(csv_path):
    results = []

    with csv_path.open("r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            results.append({
                "same_person": row["same_person"].strip().lower() == "true",
                "similarity": float(row["similarity"])
            })

    return results


def calculate_metrics(results, threshold):
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
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    fmr = fp / (fp + tn) if fp + tn else 0
    fnmr = fn / (fn + tp) if fn + tp else 0

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0
    )

    return {
        "threshold": threshold,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fmr": fmr,
        "fnmr": fnmr,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn
    }


def main():
    for model_name, csv_path in MODEL_FILES.items():
        print(f"\n--- {model_name} Threshold Evaluation ---")

        results = load_results(csv_path)
        print(f"Loaded {len(results)} comparisons.")

        metrics_list = [
            calculate_metrics(results, threshold)
            for threshold in THRESHOLDS
        ]

        print(
            f"{'Threshold':<11}"
            f"{'Accuracy':<11}"
            f"{'Precision':<11}"
            f"{'Recall':<11}"
            f"{'F1':<9}"
            f"{'FMR':<11}"
            f"{'FNMR':<11}"
        )
        print("-" * 75)

        for m in metrics_list:
            print(
                f"{m['threshold']:<11.2f}"
                f"{m['accuracy']:<11.2%}"
                f"{m['precision']:<11.2%}"
                f"{m['recall']:<11.2%}"
                f"{m['f1']:<9.2f}"
                f"{m['fmr']:<11.2%}"
                f"{m['fnmr']:<11.2%}"
            )

        # Exploratory maximum accuracy on this dataset.
        best = max(metrics_list, key=lambda m: m["accuracy"])

        print(f"\nHighest observed accuracy for {model_name}:")
        print(f"Threshold: {best['threshold']:.2f}")
        print(f"Accuracy: {best['accuracy']:.2%}")
        print(f"False matches: {best['fp']}")
        print(f"Missed matches: {best['fn']}")

    print("\n--- Model Metrics Comparison Completed ---")
    print("These are exploratory, in-sample results.")
    print("Do not use these thresholds as production settings.")


if __name__ == "__main__":
    main()
