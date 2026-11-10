
import cv2
from pathlib import Path

# Locate the FaceMatch project folder
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Input and output image paths
IMAGE_PATH = PROJECT_DIR / "sample_images" / "test.jpg"
OUTPUT_PATH = PROJECT_DIR / "outputs" / "detected_face.jpg"

# Load the photograph
image = cv2.imread(str(IMAGE_PATH))

if image is None:
    print("Error: Could not load test.jpg")
    raise SystemExit(1)

# Convert image to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Load OpenCV's pretrained face detector
cascade_path = (
    cv2.data.haarcascades
    + "haarcascade_frontalface_default.xml"
)

face_detector = cv2.CascadeClassifier(cascade_path)

if face_detector.empty():
    print("Error: Face detector could not be loaded.")
    raise SystemExit(1)

# Detect faces and retrieve detection scores
faces, reject_levels, weights = face_detector.detectMultiScale3(
    gray,
    scaleFactor=1.05,
    minNeighbors=8,
    minSize=(60, 60),
    outputRejectLevels=True
)

print(f"\nNumber of faces detected: {len(faces)}")

# Display detection details and draw rectangles
for i, ((x, y, w, h), weight) in enumerate(
    zip(faces, weights), start=1
):
    if weight < 5.0:
        continue
    print(f"\nFace {i}:")
    print(f"  X coordinate: {x}")
    print(f"  Y coordinate: {y}")
    print(f"  Width: {w}")
    print(f"  Height: {h}")
    print(f"  Detection score: {weight:.2f}")

    # Draw a green rectangle around the detected face
    cv2.rectangle(
        image,
        (x, y),
        (x + w, y + h),
        (0, 255, 0),
        3
    )

    # Label each detected face
    cv2.putText(
        image,
        f"Face {i}: {weight:.2f}",
        (x, max(y - 10, 20)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2
    )

# Save the resulting photograph
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

if cv2.imwrite(str(OUTPUT_PATH), image):
    print(f"\nResult saved to: {OUTPUT_PATH}")
else:
    print("Error: Could not save the result.")
