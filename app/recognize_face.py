
import hashlib
from pathlib import Path

import numpy as np

from database import connect
from face_embedding import generate_embedding

from settings import SIMILARITY_THRESHOLD, PROJECT_DIR


def cosine_similarity(embedding1, embedding2):
    """Calculate similarity between two face embeddings."""
    vector1 = np.array(embedding1, dtype=float)
    vector2 = np.array(embedding2, dtype=float)

    if (vector1.ndim != 1 or vector2.ndim != 1
            or vector1.shape != vector2.shape or vector1.size == 0
            or not np.isfinite(vector1).all() or not np.isfinite(vector2).all()):
        raise ValueError("Invalid or incompatible face embeddings.")

    denominator = np.linalg.norm(vector1) * np.linalg.norm(vector2)

    if denominator == 0:
        raise ValueError("Face embedding has zero length.")

    return float(np.clip(np.dot(vector1, vector2) / denominator, -1, 1))


def compare_with_registered_faces(photo_path):
    """Compare a photograph with registered photographs."""

    with connect() as conn:
        persons = conn.execute(
            "SELECT id, name, photo_path FROM persons "
            "WHERE photo_path IS NOT NULL"
            " ORDER BY id"
        ).fetchall()

    if not persons:
        return []
    print("Generating query face embedding...")
    query_embedding = generate_embedding(str(photo_path))
    results = []
    seen_photos = {}

    for person_id, name, registered_path in persons:
        registered_path = Path(registered_path).expanduser()
        if not registered_path.is_absolute():
            registered_path = PROJECT_DIR / registered_path
        if not Path(registered_path).is_file():
            print(f"Skipping {person_id}: photograph not found.")
            continue
            

        try:
            photo_hash = hashlib.sha256(Path(registered_path).read_bytes()).hexdigest()
        except OSError as error:
            print(f"Skipping {person_id}: photograph could not be read: {error}")
            continue

        if photo_hash in seen_photos:
            print(
                f"Skipping duplicate photograph: "
                f"ID {person_id} has the same photograph "
                f"as ID {seen_photos[photo_hash]}."
            )
            for result in results:
                if result["person_id"] == seen_photos[photo_hash]:
                    result["ambiguous"] = True
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
                "similarity": similarity,
                "ambiguous": False
            })

        except Exception as error:
            print(f"Could not compare ID {person_id}: {error}")

    results.sort(
        key=lambda result: result["similarity"],
        reverse=True
    )
    return results

def classify_results(results):
    """Return a cautious decision without changing the experimental threshold."""
    if not results:
        return "unavailable", None
    # Do not assume that external callers have sorted or validated results.
    if any(not np.isfinite(row["similarity"]) for row in results):
        return "unavailable", None
    results = sorted(results, key=lambda row: row["similarity"], reverse=True)
    best = results[0]
    score = best["similarity"]
    if not np.isfinite(score):
        return "unavailable", None
    if score < SIMILARITY_THRESHOLD:
        return "unknown", None
    if best.get("ambiguous") or any(
        np.isclose(score, row["similarity"], rtol=0, atol=1e-12)
        for row in results[1:]
    ):
        return "ambiguous", None
    return "possible", best
