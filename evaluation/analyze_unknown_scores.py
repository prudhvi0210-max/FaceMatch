
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

MODELS = ["facenet512", "arcface"]


def analyze_model(model):
    file_path = BASE_DIR / f"unknown_results_{model}.csv"

    if not file_path.exists():
        print(f"Missing results file: {file_path}")
        return

    with file_path.open(newline="") as file:
        rows = list(csv.DictReader(file))

    correct_scores = []
    false_scores = []

    print(f"\n--- {model.upper()} ---")

    for row in rows:
        score = float(row["best_score"])
        predicted = row["predicted_person"]

        if predicted == "Unknown":
            correct_scores.append(score)
            result = "CORRECT REJECTION"
        else:
            false_scores.append(score)
            result = "FALSE IDENTIFICATION"

        print(
            f"{row['test_image']} | "
            f"Score: {score:.4f} | "
            f"Prediction: {predicted} | "
            f"{result}"
        )

    print("\n--- Score Summary ---")

    if correct_scores:
        print(
            "Correct rejection scores:",
            [round(score, 4) for score in correct_scores]
        )
        print(
            "Highest correctly rejected score:",
            round(max(correct_scores), 4)
        )

    if false_scores:
        print(
            "False identification scores:",
            [round(score, 4) for score in false_scores]
        )
        print(
            "Lowest false identification score:",
            round(min(false_scores), 4)
        )

    print(f"Correct rejections: {len(correct_scores)}")
    print(f"False identifications: {len(false_scores)}")


def main():
    for model in MODELS:
        analyze_model(model)

    print("\n--- Unknown Score Analysis Completed ---")


if __name__ == "__main__":
    main()
