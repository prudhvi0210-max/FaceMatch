
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from settings import DB_PATH




@contextmanager
def connect():
    """Commit/rollback each operation and always release the SQLite connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    try:
        with conn:
            yield conn
    finally:
        conn.close()



def create_table():
    with connect() as conn:
        # Create the table if it does not exist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS persons (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                photo_path TEXT
            )
        """)

        # Check existing database columns
        columns = conn.execute(
            "PRAGMA table_info(persons)"
        ).fetchall()

        column_names = [column[1] for column in columns]

        # Add photo_path to an existing table
        if "photo_path" not in column_names:
            conn.execute(
                "ALTER TABLE persons ADD COLUMN photo_path TEXT"
            )
            print("Database updated: photo_path column added.")



def register_person(person_id, name, photo_path=None):
    if not isinstance(person_id, str) or not isinstance(name, str):
        raise ValueError("Person ID and name must be text.")
    person_id, name = person_id.strip(), name.strip()
    if not person_id or not name or len(person_id) > 80 or len(name) > 160:
        raise ValueError("Enter a nonempty ID (up to 80 characters) and name (up to 160 characters).")
    if photo_path is not None:
        photo_path = str(photo_path)
    with connect() as conn:
        try:
            conn.execute(
                """
                INSERT INTO persons (id, name, photo_path)
                VALUES (?, ?, ?)
                """,
                (person_id, name, photo_path)
            )
            return True
        except sqlite3.IntegrityError:
            return False



def get_all_persons():
    with connect() as conn:
        return conn.execute(
            "SELECT id, name FROM persons ORDER BY id"
        ).fetchall()
