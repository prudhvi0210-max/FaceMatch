
import csv
import sys
from itertools import combinations
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = PROJECT_DIR / "evaluation" / "dataset"

sys.path.insert(0, str(PROJECT_DIR / "app"))

from face_embedding import generate_embedding
from recognize_face import cosine_similarity


def main():
    # Find all labelled photographs
    images = []

    for person_dir in sorted(DATASET_DIR.iterdir()):
        if not person_dir.is_dir():
            continue

        for image_path in sorted(person_dir.iterdir()):
            if image_path.suffix.lower() in (".jpg", ".jpeg", ".png"):
                images.append((person_dir.name, image_path))

    print(f"Found {len(images)} photographs.")

    if len(images) < 2:
        print("At least two photographs are required.")
        return

    # Generate embeddings once per photograph
    embeddings = {}

    for person, image_path in images:
        print(f"Generating embedding: {person}/{image_path.name}")
        embeddings[image_path] = generate_embedding(image_path)

    # Generate all unique image pairs
    csv_path = PROJECT_DIR / "evaluation" / "results.csv"

    same_count = 0
    different_count = 0

    with csv_path.open("w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([
            "image_1",
            "image_2",
            "same_person",
            "similarity"
        ])

        print("\n--- FaceMatch Evaluation Results ---")

        for (person1, image1), (person2, image2) in combinations(images, 2):
            same_person = person1 == person2

            score = cosine_similarity(
                embeddings[image1],
                embeddings[image2]
            )

            writer.writerow([
                f"{person1}/{image1.name}",
                f"{person2}/{image2.name}",
                same_person,
                round(score, 4)
            ])

            if same_person:
                same_count += 1
            else:
                different_count += 1

            label = "SAME" if same_person else "DIFFERENT"

            print(
                f"{image1.name} vs {image2.name} | "
                f"Label: {label} | Similarity: {score:.4f}"
            )

    print("\n--- Evaluation Summary ---")
    print(f"Total photographs: {len(images)}")
    print(f"Same-person comparisons: {same_count}")
    print(f"Different-person comparisons: {different_count}")
    print(f"Total comparisons: {same_count + different_count}")
    print(f"Results saved to: {csv_path}")


if __name__ == "__main__":
    main()
