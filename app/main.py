"""FaceMatch local academic prototype. Run with python app/main.py."""
from pathlib import Path
import sqlite3

from database import connect, create_table, register_person, get_all_persons
from face_utils import detect_faces
from photo_storage import save_person_photo
from face_embedding import generate_embedding
from recognize_face import compare_with_registered_faces, classify_results


def ask(prompt):
    value = input(prompt).strip()
    return None if value.lower() in {'exit', 'cancel', 'back'} else value


def ask_photo():
    value = ask('Enter photograph path (or cancel): ')
    if value is None:
        return None
    if not value:
        print('A photograph is required.')
        return None
    # Accept quoted paths copied from Finder.
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    path = Path(value).expanduser().resolve()
    faces = detect_faces(path)
    if faces is None:
        print('Invalid or unreadable photograph.')
        return None
    if len(faces) != 1:
        print('The photograph must contain exactly one detected face.')
        return None
    return path


def register():
    person_id = ask('Enter Person ID (or cancel): ')
    if person_id is None:
        return
    name = ask('Enter Person Name (or cancel): ')
    if name is None:
        return
    if not person_id or not name or len(person_id) > 80 or len(name) > 160:
        print('Enter a nonempty ID (up to 80 characters) and name (up to 160 characters).')
        return
    with connect() as conn:
        exists = conn.execute('SELECT id FROM persons WHERE id = ?', (person_id,)).fetchone()
    if exists:
        print('This Person ID is already registered.')
        return
    path = ask_photo()
    if path is None:
        return
    # Verify the actual recognition model can use this photo before saving it.
    generate_embedding(path)
    saved = save_person_photo(person_id, path)
    try:
        success = register_person(person_id, name, saved)
    except Exception:
        Path(saved).unlink(missing_ok=True)
        raise
    if success:
        print('Person registered successfully! Photograph saved in private storage.')
    else:
        Path(saved).unlink(missing_ok=True)
        print('Registration failed: Person ID already exists.')


def recognize():
    path = ask_photo()
    if path is None:
        return
    results = compare_with_registered_faces(path)
    decision, best = classify_results(results)
    if decision == 'unavailable':
        print('No usable registered photographs available for comparison.')
        return
    if decision == 'unknown':
        print('\nUnknown person: no match meets the experimental threshold.')
    elif decision == 'ambiguous':
        print('\nAmbiguous result: duplicate references or tied scores prevent choosing one identity.')
    else:
        print(f"\nPossible match: {best['name']} (ID: {best['person_id']}).")
    print('\n--- Face Similarity Results ---')
    for row in results:
        print(f"ID: {row['person_id']} | Name: {row['name']} | Similarity: {row['similarity']:.4f}")
    print('\nNote: Similarity scores are not proof of identity.')


def main():
    try:
        create_table()
    except sqlite3.Error as error:
        print(f'Could not open the database: {error}')
        return
    while True:
        print('\n' + '=' * 40 + '\n       Welcome to FaceMatch\n' + '=' * 40)
        print('1. Register Person\n2. Recognize Face\n3. View Registered Persons\n4. Exit')
        try:
            choice = input('\nEnter your choice (1-4): ').strip().lower()
            if choice in {'4', 'exit', 'quit'}:
                print('Thank you for using FaceMatch!')
                break
            if choice == '1':
                register()
            elif choice == '2':
                recognize()
            elif choice == '3':
                persons = get_all_persons()
                if not persons:
                    print('No persons registered yet.')
                for person_id, name in persons:
                    print(f'ID: {person_id} | Name: {name}')
            else:
                print('Invalid choice. Please enter 1, 2, 3, or 4.')
        except (EOFError, KeyboardInterrupt):
            print('\nThank you for using FaceMatch!')
            break
        except Exception as error:
            print(f'Operation failed: {error}')
            print('Returning to the main menu.')


if __name__ == '__main__':
    main()
