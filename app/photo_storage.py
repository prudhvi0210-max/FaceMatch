
from pathlib import Path
import shutil
import uuid

from settings import STORAGE_DIR


def save_person_photo(person_id, source_path):
    source = Path(source_path).expanduser().resolve()

    if not source.is_file():
        raise FileNotFoundError("Photograph not found.")

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    # Generate a unique filename
    filename = f"{uuid.uuid4().hex}{source.suffix.lower()}"

    destination = STORAGE_DIR / filename

    # Copy the photograph
    try:
        shutil.copy2(source, destination)
    except Exception:
        destination.unlink(missing_ok=True)
        raise

    return str(destination)
