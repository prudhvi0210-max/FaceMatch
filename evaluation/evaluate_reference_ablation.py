
import csv
from pathlib import Path

import numpy as np
from deepface import DeepFace

BASE_DIR = Path(__file__).resolve().parent
REFERENCE_DIR = BASE_DIR / "dataset"
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

    return np.asarray(
        results[0]["embedding"],
        dtype=float
    )


def cosine_similarity(a, b):
    denominator = np.linalg.norm(a) * np.linalg.norm(b)

    if denominator == 0:
        raise ValueError("Cannot compare zero-length embeddings")

    return float(np.dot(a, b) / denominator)


def evaluate_model(model_name, threshold, references, unknowns):
    print(f"\n========== {model_name} ==========")

    # Generate embeddings once per model.
    reference_embeddings = []

    for person, image_path in references:
        print(f"Loading reference: {person}/{image_path.name}")

        embedding = generate_embedding(image_path, model_name)

        relative_path = f"{person}/{image_path.name}"

        reference_embeddings.append(
            (person, relative_path, embedding)
        )

    unknown_embeddings = []

    for person, image_path in unknowns:
        print(f"Loading unknown: {person}/{image_path.name}")

        embedding = generate_embedding(image_path, model_name)

        unknown_embeddings.append(
            (person, image_path.name, embedding)
        )

    rows = []

    for experiment_name, excluded in EXPERIMENTS.items():
        active_references = [
            item
            for item in reference_embeddings
            if item[1] not in excluded
        ]

        if not active_references:
            raise ValueError("No active reference photographs")

        correctly_rejected = 0
        falsely_identified = 0

        print(f"\n--- {experiment_name} ---")
        print(f"Active references: {len(active_references)}")

        for unknown_person, image_name, test_embedding in unknown_embeddings:
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

            best_person = max(
                person_scores,
                key=person_scores.get
            )

            best_score = person_scores[best_person]

            if best_score < threshold:
                prediction = "Unknown"
                correctly_rejected += 1
            else:
                prediction = best_person
                falsely_identified += 1

            print(
                f"{unknown_person}/{image_name}: "
                f"{prediction} (score={best_score:.4f})"
            )

        total = len(unknown_embeddings)

        rejection_rate = correctly_rejected / total
        false_identification_rate = falsely_identified / total

        print(f"Correct rejections: {correctly_rejected}/{total}")
        print(f"False identifications: {falsely_identified}/{total}")
        print(f"Unknown rejection rate: {rejection_rate:.2%}")

        rows.append({
            "model": model_name,
            "experiment": experiment_name,
            "active_references": len(active_references),
            "total_unknown": total,
            "correct_rejections": correctly_rejected,
            "false_identifications": falsely_identified,
            "unknown_rejection_rate": round(rejection_rate, 4),
            "false_identification_rate": round(
                false_identification_rate, 4
            ),
        })

    return rows


def main():
    references = load_images(REFERENCE_DIR)
    unknowns = load_images(UNKNOWN_DIR)

    print(f"Reference photographs: {len(references)}")
    print(f"Unknown photographs: {len(unknowns)}")

    if not references or not unknowns:
        raise ValueError("Reference or unknown dataset is empty")

    all_rows = []

    for model_name, threshold in MODELS.items():
        model_rows = evaluate_model(
            model_name,
            threshold,
            references,
            unknowns,
        )

        all_rows.extend(model_rows)

    output_file = BASE_DIR / "reference_ablation_results.csv"

    with output_file.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "model",
                "experiment",
                "active_references",
                "total_unknown",
                "correct_rejections",
                "false_identifications",
                "unknown_rejection_rate",
                "false_identification_rate",
            ],
        )

        writer.writeheader()
        writer.writerows(all_rows)

    print("\n--- Reference Ablation Completed ---")
    print(f"Results saved to: {output_file}")


if __name__ == "__main__":
    main()
