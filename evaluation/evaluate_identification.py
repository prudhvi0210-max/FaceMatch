
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


def load_images(folder):
    images = []

    for person_dir in sorted(folder.iterdir()):
        if not person_dir.is_dir():
            continue

        for image_path in sorted(person_dir.iterdir()):
            if image_path.suffix.lower() in IMAGE_EXTENSIONS:
                images.append((person_dir.name, image_path))

    return images


def generate_embedding(image_path, model_name):
    results = DeepFace.represent(
        img_path=str(image_path),
        model_name=model_name,
        detector_backend="retinaface",
        enforce_detection=True,
        align=True
    )

    if len(results) != 1:
        raise ValueError(
            f"Expected one face in {image_path}, found {len(results)}"
        )

    return np.asarray(results[0]["embedding"], dtype=float)


def cosine_similarity(a, b):
    denominator = np.linalg.norm(a) * np.linalg.norm(b)

    if denominator == 0:
        raise ValueError("Cannot compare zero-length embeddings")

    return float(np.dot(a, b) / denominator)


def evaluate_model(model_name, threshold, references, tests):
    print(f"\n--- {model_name} Identification Evaluation ---")

    reference_embeddings = []
    test_embeddings = []

    for person, path in references:
        print(f"Loading reference: {person}/{path.name}")
        embedding = generate_embedding(path, model_name)
        reference_embeddings.append((person, path, embedding))

    for person, path in tests:
        print(f"Loading test: {person}/{path.name}")
        embedding = generate_embedding(path, model_name)
        test_embeddings.append((person, path, embedding))

    rows = []
    correct_count = 0
    incorrect_count = 0
    rejected_count = 0

    category_stats = {
        "normal": {"correct": 0, "total": 0},
        "sunglasses": {"correct": 0, "total": 0}
    }

    for actual_person, test_path, test_embedding in test_embeddings:
        scores = []

        for ref_person, ref_path, ref_embedding in reference_embeddings:
            score = cosine_similarity(
                test_embedding,
                ref_embedding
            )

            scores.append((ref_person, ref_path, score))

        # Best score for each registered identity
        person_scores = {}

        for ref_person, ref_path, score in scores:
            if (
                ref_person not in person_scores
                or score > person_scores[ref_person][0]
            ):
                person_scores[ref_person] = (score, ref_path)

        ranked = sorted(
            person_scores.items(),
            key=lambda item: item[1][0],
            reverse=True
        )

        best_person = ranked[0][0]
        best_score = ranked[0][1][0]
        best_reference = ranked[0][1][1]

        second_score = (
            ranked[1][1][0]
            if len(ranked) > 1
            else None
        )

        margin = (
            best_score - second_score
            if second_score is not None
            else None
        )

        if best_score < threshold:
            predicted_person = "Unknown"
            rejected_count += 1
        else:
            predicted_person = best_person

        correct = predicted_person == actual_person

        if correct:
            correct_count += 1
        else:
            incorrect_count += 1

        category = (
            "sunglasses"
            if test_path.name.lower().startswith("sunglasses")
            else "normal"
        )

        category_stats[category]["total"] += 1

        if correct:
            category_stats[category]["correct"] += 1

        print(
            f"{actual_person}/{test_path.name} "
            f"-> {predicted_person} "
            f"(score={best_score:.4f}, "
            f"margin={margin:.4f})"
        )

        rows.append({
            "test_image": f"{actual_person}/{test_path.name}",
            "actual_person": actual_person,
            "predicted_person": predicted_person,
            "best_reference": (
                f"{best_person}/{best_reference.name}"
            ),
            "best_score": round(best_score, 4),
            "second_best_score": (
                round(second_score, 4)
                if second_score is not None
                else ""
            ),
            "margin": (
                round(margin, 4)
                if margin is not None
                else ""
            ),
            "threshold": threshold,
            "category": category,
            "correct": correct
        })

    output_file = (
        BASE_DIR / f"identification_{model_name.lower()}.csv"
    )

    with output_file.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "test_image",
                "actual_person",
                "predicted_person",
                "best_reference",
                "best_score",
                "second_best_score",
                "margin",
                "threshold",
                "category",
                "correct"
            ]
        )

        writer.writeheader()
        writer.writerows(rows)

    total = len(test_embeddings)
    accuracy = correct_count / total if total else 0

    print(f"\n--- {model_name} Summary ---")
    print(f"Total test photographs: {total}")
    print(f"Correct identifications: {correct_count}")
    print(f"Incorrect or rejected: {incorrect_count}")
    print(f"Rejected as Unknown: {rejected_count}")
    print(f"Identification accuracy: {accuracy:.2%}")

    for category, stats in category_stats.items():
        if stats["total"] > 0:
            category_accuracy = (
                stats["correct"] / stats["total"]
            )

            print(
                f"{category.capitalize()} accuracy: "
                f"{category_accuracy:.2%} "
                f"({stats['correct']}/{stats['total']})"
            )

    print(f"Results saved to: {output_file}")


def main():
    references = load_images(REFERENCE_DIR)
    tests = load_images(TEST_DIR)

    print(f"Reference photographs: {len(references)}")
    print(f"Test photographs: {len(tests)}")

    if not references or not tests:
        raise ValueError("Reference or test dataset is empty")

    for model_name, threshold in MODELS.items():
        evaluate_model(
            model_name,
            threshold,
            references,
            tests
        )

    print("\n--- Identification Evaluation Completed ---")


if __name__ == "__main__":
    main()
