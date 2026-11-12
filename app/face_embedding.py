
from pathlib import Path
from deepface import DeepFace

PROJECT_DIR = Path(__file__).resolve().parent.parent
IMAGE_PATH = PROJECT_DIR / "sample_images" / "test.jpg"


def generate_embedding(image_path):
    results = DeepFace.represent(
        img_path=str(image_path),
        model_name="Facenet512",
        detector_backend="retinaface",
        enforce_detection=True
    )

    if len(results) != 1:
        raise ValueError(
            "Expected exactly one face in the photograph."
        )

    return results[0]["embedding"]


if __name__ == "__main__":
    print("Generating face embedding...")

    embedding = generate_embedding(IMAGE_PATH)

    print("\nEmbedding generated successfully!")
    print("Number of values:", len(embedding))
    print("First 10 values:", embedding[:10])
