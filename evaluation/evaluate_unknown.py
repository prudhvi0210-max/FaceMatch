
import csv
from pathlib import Path

import numpy as np
from deepface import DeepFace

BASE_DIR = Path(__file__).resolve().parent
REFERENCE_DIR = BASE_DIR / "dataset"
UNKNOWN_DIR = BASE_DIR / "unknown_dataset"

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
            f"Expected one face in {image_path}, "
            f"found {len(results)}"
        )

    return np.asarray(results[0]["embedding"], dtype=float)


def cosine_similarity(a, b):
    denominator = np.linalg.norm(a) * np.linalg.norm(b)

    if denominator == 0:
        raise ValueError("Cannot compare zero-length embeddings")

    return float(np.dot(a, b) / denominator)


def evaluate_model(model_name, threshold, references, unknowns):
    print(f"\n--- Evaluating {model_name} ---")

    reference_embeddings = []

    for person, image_path in references:
        print(f"Reference: {person}/{image_path.name}")

        embedding = generate_embedding(image_path, model_name)

        reference_embeddings.append(
            (person, image_path, embedding)
        )

    correctly_rejected = 0
    falsely_identified = 0

    rows = []

    for unknown_person, image_path in unknowns:
        print(f"\nTesting: {unknown_person}/{image_path.name}")

        test_embedding = generate_embedding(
            image_path,
            model_name
        )

        person_scores = {}

        for ref_person, ref_path, ref_embedding in reference_embeddings:
            score = cosine_similarity(
                test_embedding,
                ref_embedding
            )

            if (
                ref_person not in person_scores
                or score > person_scores[ref_person][0]
            ):
                person_scores[ref_person] = (
                    score,
                    ref_path
                )

        
        ranked = sorted(
            person_scores.items(),
            key=lambda item: item[1][0],
            reverse=True
        )

        print("\nSimilarity scores by registered identity:")

        for person, (score, reference_path) in ranked:
            print(
                f"  {person}: {score:.4f} "
                f"(reference: {reference_path.name})"
            )

        if len(ranked) >= 2:
            best_score = ranked[0][1][0]
            second_score = ranked[1][1][0]
            score_margin = best_score - second_score

            print(f"Best identity: {ranked[0][0]}")
            print(f"Second-best identity: {ranked[1][0]}")
            print(f"Score margin: {score_margin:.4f}")



        best_person = ranked[0][0]
        best_score = ranked[0][1][0]

        if best_score < threshold:
            prediction = "Unknown"
            correctly_rejected += 1
            status = "CORRECT REJECTION"
        else:
            prediction = best_person
            falsely_identified += 1
            status = "FALSE IDENTIFICATION"

        category = (
            "sunglasses"
            if image_path.name.lower().startswith("sunglasses")
            else "normal"
        )

        print(f"Prediction: {prediction}")
        print(f"Highest similarity: {best_score:.4f}")
        print(f"Result: {status}")

        rows.append({
            "test_image": f"{unknown_person}/{image_path.name}",
            "predicted_person": prediction,
            "best_score": round(best_score, 4),
            "threshold": threshold,
            "category": category,
            "correct_rejection": prediction == "Unknown"
        })

    total = len(unknowns)

    rejection_rate = (
        correctly_rejected / total if total else 0
    )

    false_identification_rate = (
        falsely_identified / total if total else 0
    )

    output_file = (
        BASE_DIR / f"unknown_results_{model_name.lower()}.csv"
    )

    with output_file.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "test_image",
                "predicted_person",
                "best_score",
                "threshold",
                "category",
                "correct_rejection"
            ]
        )

        writer.writeheader()
        writer.writerows(rows)

    print(f"\n--- {model_name} Unknown Detection Summary ---")
    print(f"Total unknown photographs: {total}")
    print(f"Correctly rejected: {correctly_rejected}")
    print(f"Falsely identified: {falsely_identified}")
    print(f"Unknown rejection rate: {rejection_rate:.2%}")
    print(
        f"False identification rate: "
        f"{false_identification_rate:.2%}"
    )
    print(f"Results saved to: {output_file}")


def main():
    references = load_images(REFERENCE_DIR)
    unknowns = load_images(UNKNOWN_DIR)

    print(f"Registered reference photographs: {len(references)}")
    print(f"Unknown test photographs: {len(unknowns)}")

    if not references or not unknowns:
        raise ValueError("Reference or unknown dataset is empty")

    registered_people = {person for person, _ in references}
    unknown_people = {person for person, _ in unknowns}

    if registered_people & unknown_people:
        raise ValueError(
            "Registered and unknown person labels overlap."
        )

    for model_name, threshold in MODELS.items():
        evaluate_model(
            model_name,
            threshold,
            references,
            unknowns
        )

    print("\n--- Unknown-Person Evaluation Completed ---")


if __name__ == "__main__":
    main()
