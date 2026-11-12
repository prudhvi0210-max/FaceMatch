
import hashlib
from pathlib import Path

import numpy as np

from database import connect
from face_embedding import generate_embedding


def cosine_similarity(embedding1, embedding2):
    """Calculate similarity between two face embeddings."""
    vector1 = np.array(embedding1, dtype=float)
    vector2 = np.array(embedding2, dtype=float)

    denominator = np.linalg.norm(vector1) * np.linalg.norm(vector2)

    if denominator == 0:
        return 0.0

    return float(np.dot(vector1, vector2) / denominator)


def compare_with_registered_faces(photo_path):
    """Compare a photograph with registered photographs."""

    print("Generating query face embedding...")
    query_embedding = generate_embedding(str(photo_path))

    with connect() as conn:
        persons = conn.execute(
            "SELECT id, name, photo_path FROM persons "
            "WHERE photo_path IS NOT NULL"
        ).fetchall()

        results = []
    seen_photos = {}

    for person_id, name, registered_path in persons:
        if not Path(registered_path).is_file():
            print(f"Skipping {person_id}: photograph not found.")
            continue
            

        photo_hash = hashlib.sha256(
            Path(registered_path).read_bytes()
        ).hexdigest()

        if photo_hash in seen_photos:
            print(
                f"Skipping duplicate photograph: "
                f"ID {person_id} has the same photograph "
                f"as ID {seen_photos[photo_hash]}."
            )
            continue

        seen_photos[photo_hash] = person_id

        print(f"Comparing with registered ID {person_id}...")

        try:
            registered_embedding = generate_embedding(
                str(registered_path)
            )

            similarity = cosine_similarity(
                query_embedding,
                registered_embedding
            )

            results.append({
                "person_id": person_id,
                "name": name,
                "similarity": similarity
            })

        except Exception as error:
            print(f"Could not compare ID {person_id}: {error}")

    results.sort(
        key=lambda result: result["similarity"],
        reverse=True
    )
    return results