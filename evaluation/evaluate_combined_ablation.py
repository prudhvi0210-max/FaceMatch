
import csv
from pathlib import Path

import numpy as np
from deepface import DeepFace

BASE_DIR = Path(__file__).resolve().parent

REFERENCE_DIR = BASE_DIR / "dataset"
REGISTERED_DIR = BASE_DIR / "test_dataset"
UNKNOWN_DIR = BASE_DIR / "unknown_dataset"

MODELS = {
    "Facenet512": 0.50,
    "ArcFace": 0.35,
}

EXPERIMENTS = {
    "A_baseline": set(),
    "B_without_photo2": {"person_03/photo2.jpg"},
    "C_without_test4": {"person_03/test4.jpg"},
    "D_without_both": {
        "person_03/photo2.jpg",
        "person_03/test4.jpg",
    },
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
        align=True,
    )

    if len(results) != 1:
        raise ValueError(
            f"Expected one face in {image_path}, "
            f"found {len(results)}"
        )

    return np.asarray(results[0]["embedding"], dtype=float)


def cosine_similarity(a, b):
    denominator = np.linalg.norm(a) * np.linalg.norm(b)

    if denominator == 0:
        raise ValueError("Cannot compare zero-length embeddings")

    return float(np.dot(a, b) / denominator)


def evaluate_model(model_name, threshold, references, tests):
    print(f"\n========== {model_name} ==========")

    reference_embeddings = []

    for person, image_path in references:
        print(f"Reference: {person}/{image_path.name}")

        embedding = generate_embedding(image_path, model_name)

        reference_embeddings.append((
            person,
            f"{person}/{image_path.name}",
            embedding,
        ))

    test_embeddings = []

    for actual_person, image_path, category in tests:
        print(f"Test: {actual_person}/{image_path.name}")

        embedding = generate_embedding(image_path, model_name)

        test_embeddings.append((
            actual_person,
            image_path.name,
            category,
            embedding,
        ))

    summary_rows = []
    detail_rows = []

    for experiment_name, excluded in EXPERIMENTS.items():
        active_references = [
            item for item in reference_embeddings
            if item[1] not in excluded
        ]

        registered_correct = 0
        registered_wrong = 0
        registered_rejected = 0
        unknown_correct = 0
        unknown_false = 0

        print(f"\n--- {experiment_name} ---")
        print(f"Active references: {len(active_references)}")

        for actual_person, image_name, category, test_embedding in test_embeddings:
            person_scores = {}

            for ref_person, ref_path, ref_embedding in active_references:
                score = cosine_similarity(
                    test_embedding,
                    ref_embedding
                )

                if (
                    ref_person not in person_scores
                    or score > person_scores[ref_person]
                ):
                    person_scores[ref_person] = score

            best_person = max(person_scores, key=person_scores.get)
            best_score = person_scores[best_person]

            prediction = (
                best_person if best_score >= threshold
                else "Unknown"
            )

            if category == "registered":
                if prediction == actual_person:
                    registered_correct += 1
                    result = "CORRECT"
                elif prediction == "Unknown":
                    registered_rejected += 1
                    result = "FALSE REJECTION"
                else:
                    registered_wrong += 1
                    result = "WRONG IDENTITY"
            else:
                if prediction == "Unknown":
                    unknown_correct += 1
                    result = "CORRECT REJECTION"
                else:
                    unknown_false += 1
                    result = "FALSE IDENTIFICATION"

            print(
                f"{actual_person}/{image_name}: "
                f"{prediction} ({best_score:.4f}) - {result}"
            )

            detail_rows.append({
                "model": model_name,
                "experiment": experiment_name,
                "test_category": category,
                "actual_person": actual_person,
                "image": image_name,
                "prediction": prediction,
                "best_score": round(best_score, 4),
                "result": result,
            })

        registered_total = (
            registered_correct
            + registered_wrong
            + registered_rejected
        )

        unknown_total = unknown_correct + unknown_false

        registered_accuracy = (
            registered_correct / registered_total
            if registered_total else 0
        )

        unknown_rejection_rate = (
            unknown_correct / unknown_total
            if unknown_total else 0
        )

        print(
            f"Registered identification accuracy: "
            f"{registered_accuracy:.2%}"
        )
        print(
            f"Unknown rejection rate: "
            f"{unknown_rejection_rate:.2%}"
        )
        print(f"Wrong registered identities: {registered_wrong}")
        print(f"Registered false rejections: {registered_rejected}")
        print(f"Unknown false identifications: {unknown_false}")

        summary_rows.append({
            "model": model_name,
            "experiment": experiment_name,
            "active_references": len(active_references),
            "registered_total": registered_total,
            "registered_correct": registered_correct,
            "registered_wrong": registered_wrong,
            "registered_rejected": registered_rejected,
            "registered_accuracy": round(registered_accuracy, 4),
            "unknown_total": unknown_total,
            "unknown_correct": unknown_correct,
            "unknown_false": unknown_false,
            "unknown_rejection_rate": round(
                unknown_rejection_rate, 4
            ),
        })

    return summary_rows, detail_rows


def main():
    references = load_images(REFERENCE_DIR)
    registered = load_images(REGISTERED_DIR)
    unknowns = load_images(UNKNOWN_DIR)

    tests = (
        [(person, path, "registered") for person, path in registered]
        + [(person, path, "unknown") for person, path in unknowns]
    )

    print(f"Reference photographs: {len(references)}")
    print(f"Registered test photographs: {len(registered)}")
    print(f"Unknown test photographs: {len(unknowns)}")

    if not references or not registered or not unknowns:
        raise ValueError("One or more datasets are empty")

    registered_labels = {person for person, _ in references}
    test_labels = {person for person, _ in registered}
    unknown_labels = {person for person, _ in unknowns}

    if not test_labels.issubset(registered_labels):
        raise ValueError("Registered test labels do not match references")

    if unknown_labels & registered_labels:
        raise ValueError("Unknown labels overlap registered identities")

    all_summary = []
    all_details = []

    for model_name, threshold in MODELS.items():
        summary, details = evaluate_model(
            model_name,
            threshold,
            references,
            tests,
        )

        all_summary.extend(summary)
        all_details.extend(details)

    summary_file = BASE_DIR / "combined_ablation_summary.csv"
    detail_file = BASE_DIR / "combined_ablation_details.csv"

    with summary_file.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(all_summary[0].keys()),
        )
        writer.writeheader()
        writer.writerows(all_summary)

    with detail_file.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(all_details[0].keys()),
        )
        writer.writeheader()
        writer.writerows(all_details)

    print("\n--- Combined Ablation Completed ---")
    print(f"Summary saved to: {summary_file}")
    print(f"Details saved to: {detail_file}")


if __name__ == "__main__":
    main()
