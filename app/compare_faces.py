
import numpy as np
from pathlib import Path
from face_embedding import generate_embedding


def cosine_similarity(vector1, vector2):
    a = np.array(vector1)
    b = np.array(vector2)

    denominator = np.linalg.norm(a) * np.linalg.norm(b)

    if denominator == 0:
        raise ValueError("Cannot compare zero-length embeddings.")

    return float(np.dot(a, b) / denominator)


if __name__ == "__main__":
    project_dir = Path(__file__).resolve().parent.parent

    image1 = project_dir / "sample_images" / "test.jpg"
    image2 = project_dir / "sample_images" / "test3.jpg"
    
    print("Generating first embedding...")
    embedding1 = generate_embedding(image1)

    print("Generating second embedding...")
    embedding2 = generate_embedding(image2)

    similarity = cosine_similarity(embedding1, embedding2)

    print("\nCosine similarity:", round(similarity, 4))
