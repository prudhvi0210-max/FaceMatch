"""Local UI operations; reuse the existing model, database and storage."""
import base64
import binascii
from contextlib import contextmanager, redirect_stdout
import hashlib
import io
from pathlib import Path
import tempfile

from database import connect, register_person
from photo_storage import save_person_photo

MAX_IMAGE_BYTES = 20 * 1024 * 1024


def people():
    with connect() as conn:
        rows = conn.execute('SELECT id, name, photo_path FROM persons ORDER BY id').fetchall()
    records, hashes = [], {}
    for person_id, name, photo in rows:
        status = 'No reference photo'
        digest = None
        if photo:
            try:
                digest = hashlib.sha256(Path(photo).read_bytes()).hexdigest()
                status = 'Ready'
            except OSError:
                status = 'Reference unavailable'
        item = dict(id=person_id, name=name, status=status)
        records.append(item)
        if digest:
            hashes.setdefault(digest, []).append(item)
    for group in hashes.values():
        if len(group) > 1:
            for item in group:
                item['status'] = 'Duplicate reference'
    return records


@contextmanager
def uploaded_photo(payload):
    name = payload.get('filename', '')
    encoded = payload.get('image', '')
    if not isinstance(name, str) or not isinstance(encoded, str):
        raise ValueError('Choose a JPG or PNG photograph.')
    suffix = Path(name).suffix.lower()
    if suffix not in {'.jpg', '.jpeg', '.png'}:
        raise ValueError('Choose a JPG or PNG photograph.')
    if len(encoded) > (MAX_IMAGE_BYTES * 4 // 3 + 8):
        raise ValueError('The photograph must be smaller than 20 MB.')
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error):
        raise ValueError('The photograph could not be read.') from None
    if not raw or len(raw) > MAX_IMAGE_BYTES:
        raise ValueError('Choose a nonempty photograph smaller than 20 MB.')
    if not (raw.startswith(b'\xff\xd8\xff') or raw.startswith(b'\x89PNG\r\n\x1a\n')):
        raise ValueError('The file contents must be a JPG or PNG image.')
    with tempfile.TemporaryDirectory(prefix='facematch-query-') as folder:
        path = Path(folder) / ('photo' + suffix)
        path.write_bytes(raw)
        yield path


def validate_face(path):
    from face_utils import detect_faces
    with redirect_stdout(io.StringIO()):
        faces = detect_faces(path)
    if faces is None:
        raise ValueError('This photograph could not be read. Please choose another JPG or PNG.')
    if len(faces) == 0:
        raise ValueError('No usable face was detected. Choose a clear photograph containing one face.')
    if len(faces) > 1:
        raise ValueError('More than one face was detected. Choose a photograph of one person.')


def recognize(payload):
    from recognize_face import compare_with_registered_faces, classify_results
    with uploaded_photo(payload) as path:
        validate_face(path)
        with redirect_stdout(io.StringIO()):
            results = compare_with_registered_faces(path)
    decision, best = classify_results(results)
    return dict(decision=decision, best=best, results=results)


def register(payload):
    person_id, name = payload.get('person_id'), payload.get('name')
    if not isinstance(person_id, str) or not isinstance(name, str):
        raise ValueError('Enter a person ID and name.')
    person_id, name = person_id.strip(), name.strip()
    if not person_id or not name or len(person_id) > 80 or len(name) > 160:
        raise ValueError('Enter an ID (up to 80 characters) and name (up to 160 characters).')
    if payload.get('consent') is not True:
        raise ValueError('Confirm permission to store this person’s photograph.')
    with connect() as conn:
        if conn.execute('SELECT 1 FROM persons WHERE id = ?', (person_id,)).fetchone():
            raise ValueError('This ID is already registered. Use a different ID.')
    from face_embedding import generate_embedding
    with uploaded_photo(payload) as path:
        validate_face(path)
        generate_embedding(path)
        saved = save_person_photo(person_id, path)
        try:
            if not register_person(person_id, name, saved):
                raise ValueError('This ID is already registered.')
        except Exception:
            Path(saved).unlink(missing_ok=True)
            raise
    return dict(message=f'{name} was registered successfully.')
