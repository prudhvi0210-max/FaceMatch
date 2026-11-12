
from pathlib import Path

from database import create_table, register_person, get_all_persons
from face_utils import detect_faces
from photo_storage import save_person_photo
from face_embedding import generate_embedding
from recognize_face import compare_with_registered_faces


def main():
    create_table()

    while True:
        print("\n" + "=" * 40)
        print("       Welcome to FaceMatch")
        print("=" * 40)

        print("1. Register Person")
        print("2. Recognize Face")
        print("3. View Registered Persons")
        print("4. Exit")

        choice = input("\nEnter your choice (1-4): ")

        if choice == "1":
            print("\n--- Register Person ---")

            person_id = input("Enter Person ID: ").strip()
            name = input("Enter Person Name: ").strip()

            if not person_id or not name:
                print("ID and name cannot be empty.")
                continue

            # Ask for a photograph
            photo_path = input(
                "Enter photograph path: "
            ).strip()

            if not photo_path:
                print("A photograph is required.")
                continue

            # Convert the path to an absolute path
            photo_path = Path(photo_path).expanduser().resolve()

            # Check that the photograph contains one face
            faces = detect_faces(photo_path)

            if faces is None:
                print("Registration failed: Invalid photograph.")
                continue

            if len(faces) != 1:
                print(
                    "Registration failed: "
                    "The photograph must contain exactly one detected face."
                )
                continue

            # Check whether the person ID already exists
            from database import connect

            with connect() as conn:
                existing_person = conn.execute(
                    "SELECT id FROM persons WHERE id = ?",
                    (person_id,)
                ).fetchone()

            if existing_person:
                print("This Person ID is already registered.")
                continue

            # Copy the photograph into private storage
            try:
                saved_photo_path = save_person_photo(
                    person_id,
                    photo_path
                )
            except (OSError, ValueError) as error:
                print(f"Could not save photograph: {error}")
                continue

            # Register the person
            if register_person(
                person_id,
                name,
                saved_photo_path
            ):
                print("Person registered successfully!")
                print("Photograph saved in private storage.")
            else:
                Path(saved_photo_path).unlink(missing_ok=True)
                print("Registration failed: Person ID already exists.")

        elif choice == "2":
            print("\n--- Recognize Face ---")

            photo_path = input(
                "Enter photograph path: "
            ).strip()

            if not photo_path:
                print("A photograph is required.")
                continue

            photo_path = Path(photo_path).expanduser().resolve()

            # Check whether the photograph contains exactly one face
            faces = detect_faces(photo_path)

            if faces is None:
                print("Recognition failed: Invalid photograph.")
                continue

            if len(faces) != 1:
                print(
                    "Recognition failed: "
                    "The photograph must contain exactly one detected face."
                )
                continue

            print("Photograph validated successfully!")
            print("\nComparing with registered photographs...")

            try:
                results = compare_with_registered_faces(photo_path)
            except Exception as error:
                print(f"Comparison failed: {error}")
                continue

            if not results:
                print("No registered photographs available for comparison.")
                continue

            print("\n--- Face Similarity Results ---")

            for result in results:
                print(
                    f"ID: {result['person_id']} | "
                    f"Name: {result['name']} | "
                    f"Similarity: {result['similarity']:.4f}"
                )

            print(
                "\nNote: Similarity scores are not proof of identity."
            )

        elif choice == "3":
            print("\n--- Registered Persons ---")

            persons = get_all_persons()

            if not persons:
                print("No persons registered yet.")
            else:
                for person_id, name in persons:
                    print(f"ID: {person_id} | Name: {name}")

        elif choice == "4":
            print("Thank you for using FaceMatch!")
            break

        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()
