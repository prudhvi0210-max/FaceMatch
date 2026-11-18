
import csv
from pathlib import Path

import numpy as np
from deepface import DeepFace

BASE_DIR = Path(__file__).resolve().parent
REFERENCE_DIR = BASE_DIR / "dataset"
TEST_DIR = BASE_DIR / "test_dataset"

MODELS = {
    "Facenet512": 0.50,
    "ArcFace": 0.35
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def get_images(folder):
    images = []

    for person_dir in sorted(folder.iterdir()):
        if not person_dir.is_dir():
            continue

        for path in sorted(person_dir.iterdir()):
            if path.suffix.lower() in IMAGE_EXTENSIONS:
                images.append((person_dir.name, path))

    return images


def get_embedding(path, model_name):
    result = DeepFace.represent(
        img_path=str(path),
        model_name=model_name,
        detector_backend="retinaface",
        enforce_detection=True,
        align=True
    )

    if len(result) != 1:
        raise ValueError(
            f"Expected one face in {path}, found {len(result)}"
        )

    return np.asarray(result[0]["embedding"], dtype=float)


def cosine_similarity(a, b):
    denominator = np.linalg.norm(a) * np.linalg.norm(b)

    if denominator == 0:
        raise ValueError("Cannot compare zero-length embeddings")

    return float(np.dot(a, b) / denominator)


def evaluate_model(model_name, threshold, references, tests):
    print(f"\n--- Evaluating {model_name} ---")

    reference_embeddings = []
    test_embeddings = []

    for person, path in references:
        print(f"Reference: {person}/{path.name}")
        reference_embeddings.append(
            (person, path, get_embedding(path, model_name))
        )

    for person, path in tests:
        print(f"Test: {person}/{path.name}")
        test_embeddings.append(
            (person, path, get_embedding(path, model_name))
        )

    rows = []
    tp = tn = fp = fn = 0

    sunglasses_stats = {
        "normal": {"correct": 0, "total": 0},
        "sunglasses": {"correct": 0, "total": 0}
    }

    for test_person, test_path, test_embedding in test_embeddings:
        category = (
            "sunglasses"
            if test_path.name.lower().startswith("sunglasses")
            else "normal"
        )

        for ref_person, ref_path, ref_embedding in reference_embeddings:
            similarity = cosine_similarity(
                test_embedding,
                ref_embedding
            )

            actual_same = test_person == ref_person
            predicted_same = similarity >= threshold

            correct = actual_same == predicted_same

            sunglasses_stats[category]["total"] += 1
            if correct:
                sunglasses_stats[category]["correct"] += 1

            if actual_same and predicted_same:
                tp += 1
            elif not actual_same and not predicted_same:
                tn += 1
            elif not actual_same and predicted_same:
                fp += 1
            else:
                fn += 1

            rows.append({
                "test_image": f"{test_person}/{test_path.name}",
                "reference_image": f"{ref_person}/{ref_path.name}",
                "category": category,
                "same_person": actual_same,
                "similarity": round(similarity, 4),
                "predicted_same": predicted_same,
                "correct": correct
            })

    output_file = BASE_DIR / f"new_test_{model_name.lower()}.csv"

    with output_file.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "test_image",
                "reference_image",
                "category",
                "same_person",
                "similarity",
                "predicted_same",
                "correct"
            ]
        )
        writer.writeheader()
        writer.writerows(rows)

    total = tp + tn + fp + fn

    accuracy = (tp + tn) / total if total else 0
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    fmr = fp / (fp + tn) if fp + tn else 0
    fnmr = fn / (fn + tp) if fn + tp else 0

    print(f"\n--- {model_name} Results ---")
    print(f"Threshold: {threshold}")
    print(f"Total comparisons: {total}")
    print(f"True positives: {tp}")
    print(f"True negatives: {tn}")
    print(f"False positives: {fp}")
    print(f"False negatives: {fn}")
    print(f"Accuracy: {accuracy:.2%}")
    print(f"Precision: {precision:.2%}")
    print(f"Recall: {recall:.2%}")
    print(f"False match rate: {fmr:.2%}")
    print(f"False non-match rate: {fnmr:.2%}")

    for category, stats in sunglasses_stats.items():
        if stats["total"] > 0:
            category_accuracy = stats["correct"] / stats["total"]
            print(
                f"{category.capitalize()} pair accuracy: "
                f"{category_accuracy:.2%} "
                f"({stats['correct']}/{stats['total']})"
            )

    print(f"Results saved to: {output_file}")


def main():
    references = get_images(REFERENCE_DIR)
    tests = get_images(TEST_DIR)

    print(f"Reference photographs: {len(references)}")
    print(f"New test photographs: {len(tests)}")

    if not references or not tests:
        raise ValueError("Reference or test dataset is empty")

    for model_name, threshold in MODELS.items():
        evaluate_model(
            model_name,
            threshold,
            references,
            tests
        )

    print("\n--- New Dataset Evaluation Completed ---")


if __name__ == "__main__":
    main()
