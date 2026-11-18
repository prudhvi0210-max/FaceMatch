
from pathlib import Path
from deepface import DeepFace
import cv2
from settings import DETECTOR_BACKEND
from image_input import face_image_input


def detect_faces(image_path):
    """Detect faces in a photograph using RetinaFace."""

    image_path = Path(image_path).expanduser()

    # Check whether the photograph exists
    if not image_path.is_file():
        print("Error: Photograph not found.")
        return None

    try:
        source = face_image_input(image_path)
        preview = cv2.imread(source) if isinstance(source, str) else source
        if preview is None:
            raise ValueError("Unreadable photograph")
    except (OSError, ValueError, cv2.error):
        print("Error: Photograph is unreadable. Choose a valid JPG or PNG image.")
        return None

    try:
        # Detect faces using RetinaFace
        detected_faces = DeepFace.extract_faces(
            img_path=source,
            detector_backend=DETECTOR_BACKEND,
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
        if "face could not be detected" in str(error).lower():
            print("Face detection failed: no face was detected in the photograph.")
            return []
        raise RuntimeError("Face detection could not run. Check the model setup and cached weights.") from error

    except Exception as error:
        raise RuntimeError("Face detection could not run. Check the model setup and cached weights.") from error
