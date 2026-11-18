
import csv
from itertools import combinations
from pathlib import Path

import numpy as np
from deepface import DeepFace

EVALUATION_DIR = Path(__file__).resolve().parent
DATASET_DIR = EVALUATION_DIR / "dataset"

MODELS = ["Facenet512", "ArcFace"]


def cosine_similarity(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)

    denominator = np.linalg.norm(a) * np.linalg.norm(b)

    if denominator == 0:
        raise ValueError("Cannot compare zero-length embeddings.")

    return float(np.dot(a, b) / denominator)


def load_images():
    images = []

    for person_dir in sorted(DATASET_DIR.iterdir()):
        if not person_dir.is_dir():
            continue

        for image_path in sorted(person_dir.iterdir()):
            if image_path.suffix.lower() in (".jpg", ".jpeg", ".png"):
                images.append((person_dir.name, image_path))

    return images


def evaluate_model(model_name, images):
    print(f"\n--- Evaluating {model_name} ---")

    embeddings = {}

    for person, image_path in images:
        print(f"Generating embedding: {person}/{image_path.name}")

        results = DeepFace.represent(
            img_path=str(image_path),
            model_name=model_name,
            detector_backend="retinaface",
            enforce_detection=True,
            align=True
        )

        if len(results) != 1:
            raise ValueError(
                f"Expected one face in {image_path}, "
                f"found {len(results)}"
            )

        embeddings[image_path] = results[0]["embedding"]

    output_path = EVALUATION_DIR / (
        f"results_{model_name.lower()}.csv"
    )

    same_scores = []
    different_scores = []

    with output_path.open("w", newline="") as file:
        writer = csv.writer(file)

        writer.writerow([
            "image_1",
            "image_2",
            "same_person",
            "similarity"
        ])

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
                same_scores.append(score)
            else:
                different_scores.append(score)

    print(f"\nResults saved to: {output_path}")
    print(f"Same-person pairs: {len(same_scores)}")
    print(f"Different-person pairs: {len(different_scores)}")

    print(f"Mean same-person similarity: {np.mean(same_scores):.4f}")
    print(f"Mean different-person similarity: {np.mean(different_scores):.4f}")

    return output_path


def main():
    images = load_images()

    print(f"Found {len(images)} photographs.")

    if len(images) < 2:
        print("At least two photographs are required.")
        return

    for model_name in MODELS:
        evaluate_model(model_name, images)

    print("\n--- Model Comparison Completed ---")


if __name__ == "__main__":
    main()
