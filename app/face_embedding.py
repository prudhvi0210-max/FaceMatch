
from pathlib import Path
import numpy as np
from deepface import DeepFace
from settings import MODEL_NAME, DETECTOR_BACKEND, NORMALIZATION

PROJECT_DIR = Path(__file__).resolve().parent.parent
IMAGE_PATH = PROJECT_DIR / "sample_images" / "test.jpg"


def generate_embedding(image_path):
    results = DeepFace.represent(
        img_path=str(image_path),
        model_name=MODEL_NAME,
        detector_backend=DETECTOR_BACKEND,
        align=True,
        normalization=NORMALIZATION,
        enforce_detection=True
    )

    if len(results) != 1:
        raise ValueError(
            "Expected exactly one face in the photograph."
        )

    embedding = np.asarray(results[0]["embedding"], dtype=float)
    if embedding.shape != (512,) or not np.isfinite(embedding).all():
        raise ValueError("FaceNet512 returned an invalid embedding.")
    if np.linalg.norm(embedding) == 0:
        raise ValueError("FaceNet512 returned an empty embedding.")
    return embedding.tolist()


if __name__ == "__main__":
    print("Generating face embedding...")

    embedding = generate_embedding(IMAGE_PATH)

    print("\nEmbedding generated successfully!")
    print("Number of values:", len(embedding))
    print("First 10 values:", embedding[:10])
