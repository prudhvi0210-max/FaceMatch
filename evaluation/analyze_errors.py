
import csv
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent / "results_arcface.csv"
THRESHOLD = 0.35


def main():
    false_matches = []
    missed_matches = []

    with CSV_PATH.open("r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            image1 = row["image_1"]
            image2 = row["image_2"]

            actual_same = (
                row["same_person"].strip().lower() == "true"
            )

            similarity = float(row["similarity"])
            predicted_same = similarity >= THRESHOLD

            if not actual_same and predicted_same:
                false_matches.append(
                    (image1, image2, similarity)
                )

            elif actual_same and not predicted_same:
                missed_matches.append(
                    (image1, image2, similarity)
                )

    print("\n--- FaceMatch Error Analysis ---")
    print(f"Threshold: {THRESHOLD:.2f}")

    print("\n--- False Matches ---")

    if not false_matches:
        print("No false matches found.")

    for image1, image2, score in sorted(
        false_matches,
        key=lambda item: item[2],
        reverse=True
    ):
        print(
            f"{image1} vs {image2} "
            f"| Similarity: {score:.4f}"
        )

    print("\n--- Missed Matches ---")

    if not missed_matches:
        print("No missed matches found.")

    for image1, image2, score in sorted(
        missed_matches,
        key=lambda item: item[2]
    ):
        print(
            f"{image1} vs {image2} "
            f"| Similarity: {score:.4f}"
        )

    print("\n--- Error Summary ---")
    print(f"False matches: {len(false_matches)}")
    print(f"Missed matches: {len(missed_matches)}")


if __name__ == "__main__":
    main()
