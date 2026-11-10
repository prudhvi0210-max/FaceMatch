
import cv2
from pathlib import Path


def detect_faces(image_path):
    image_path = Path(image_path).expanduser()

    # Check whether the photograph exists
    if not image_path.is_file():
        print("Error: Photograph not found.")
        return None

    # Load the photograph
    image = cv2.imread(str(image_path))

    if image is None:
        print("Error: Could not read the photograph.")
        return None

    # Convert photograph to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Load the pretrained Haar Cascade detector
    cascade_path = (
        cv2.data.haarcascades
        + "haarcascade_frontalface_default.xml"
    )

    detector = cv2.CascadeClassifier(cascade_path)

    if detector.empty():
        print("Error: Face detector could not be loaded.")
        return None

    # Detect faces with scores
    faces, reject_levels, weights = detector.detectMultiScale3(
        gray,
        scaleFactor=1.05,
        minNeighbors=8,
        minSize=(60, 60),
        outputRejectLevels=True
    )

    # Experimental score threshold
    valid_faces = []

    for face, weight in zip(faces, weights):
        if weight >= 5.0:
            valid_faces.append(face)

    return valid_faces
