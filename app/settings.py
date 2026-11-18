"""Shared fixed recognition policy and configurable private storage root."""
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(os.environ.get('FACEMATCH_DATA_DIR', str(PROJECT_DIR))).expanduser().resolve()
DB_PATH = DATA_ROOT / 'database' / 'facematch.db'
STORAGE_DIR = DATA_ROOT / 'data' / 'registered_faces'
MODEL_NAME = 'Facenet512'
DETECTOR_BACKEND = 'retinaface'
NORMALIZATION = 'base'
SIMILARITY_THRESHOLD = 0.50  # Frozen exploratory baseline; not a validated operating point.
