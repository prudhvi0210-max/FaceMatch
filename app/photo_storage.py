
from pathlib import Path
import shutil
import uuid

# Main FaceMatch project folder
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Private photograph storage
STORAGE_DIR = PROJECT_DIR / "data" / "registered_faces"


def save_person_photo(person_id, source_path):
    source = Path(source_path).expanduser().resolve()

    if not source.is_file():
        raise FileNotFoundError("Photograph not found.")

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    # Generate a unique filename
    filename = f"{uuid.uuid4().hex}{source.suffix.lower()}"

    destination = STORAGE_DIR / filename

    # Copy the photograph
    shutil.copy2(source, destination)

    return str(destination)
