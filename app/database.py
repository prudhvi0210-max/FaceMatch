
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "facematch.db"


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)



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
