
from pathlib import Path
from deepface import DeepFace


def detect_faces(image_path):
    """Detect faces in a photograph using RetinaFace."""

    image_path = Path(image_path).expanduser()

    # Check whether the photograph exists
    if not image_path.is_file():
        print("Error: Photograph not found.")
        return None

    try:
        # Detect faces using RetinaFace
        detected_faces = DeepFace.extract_faces(
            img_path=str(image_path),
            detector_backend="retinaface",
            enforce_detection=True,
            align=True
        )

        # Return face coordinates in the original format
        faces = []

        for face in detected_faces:
            region = face["facial_area"]

            x = region["x"]
            y = region["y"]
            w = region["w"]
            h = region["h"]

            faces.append((x, y, w, h))

        return faces

    except ValueError as error:
        print(f"Face detection failed: {error}")
        return []

    except Exception as error:
        print(f"Face detection error: {error}")
        return []
