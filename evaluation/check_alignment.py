
from pathlib import Path

import numpy as np
from PIL import Image
from deepface import DeepFace

EVALUATION_DIR = Path(__file__).resolve().parent
DATASET_DIR = EVALUATION_DIR / "dataset"
IMAGE_PATH = DATASET_DIR / "person_03" / "test4.jpg"
OUTPUT_PATH = DATASET_DIR / "aligned_person03_test4.png"


def main():
    print("Extracting and aligning face...")

    faces = DeepFace.extract_faces(
        img_path=str(IMAGE_PATH),
        detector_backend="retinaface",
        enforce_detection=True,
        align=True,
        color_face="rgb",
        normalize_face=True
    )

    print(f"Faces detected: {len(faces)}")

    if len(faces) != 1:
        print("Expected exactly one face. Stopping.")
        return

    face = faces[0]["face"]

    # Convert normalized pixel values to an image
    face_pixels = np.clip(face * 255, 0, 255).astype("uint8")

    Image.fromarray(face_pixels).save(OUTPUT_PATH)

    print(f"Aligned face saved to: {OUTPUT_PATH}")
    print(f"Aligned face dimensions: {face_pixels.shape}")


if __name__ == "__main__":
    main()
