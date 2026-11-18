"""Isolated control-flow tests: no private photos, real DB, or model downloads."""
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
# Stub only the external model; exercise the application's real logic.
sys.modules['deepface'] = types.SimpleNamespace(DeepFace=types.SimpleNamespace())
import database
import face_embedding
import face_utils
import main
import recognize_face as recognition


class SafetyTests(unittest.TestCase):
    def test_decisions(self):
        row = lambda score, **kw: dict(person_id='1', name='A', similarity=score, **kw)
        self.assertEqual(recognition.classify_results([])[0], 'unavailable')
        self.assertEqual(recognition.classify_results([row(.49)])[0], 'unknown')
        self.assertEqual(recognition.classify_results([row(.50)])[0], 'possible')
        self.assertEqual(recognition.classify_results([row(.7, ambiguous=True)])[0], 'ambiguous')
        self.assertEqual(recognition.classify_results([row(.7), row(.7)])[0], 'ambiguous')
        self.assertEqual(recognition.classify_results([row(float('nan'))])[0], 'unavailable')

    def test_invalid_vectors(self):
        for a, b in [([0, 0], [1, 0]), ([float('nan')], [1]), ([1], [1, 2]), ([], [])]:
            with self.assertRaises(ValueError):
                recognition.cosine_similarity(a, b)
        self.assertAlmostEqual(recognition.cosine_similarity([1, 0], [1, 0]), 1)

    def test_duplicate_references_are_ambiguous(self):
        with tempfile.TemporaryDirectory() as tmp:
            photo = Path(tmp) / 'photo.jpg'
            photo.write_bytes(b'fixture')
            with patch.object(database, 'DB_PATH', Path(tmp) / 'test.db'):
                database.create_table()
                database.register_person('1', 'A', str(photo))
                database.register_person('2', 'B', str(photo))
                database.register_person('3', 'Missing', str(photo) + '.missing')
                with patch.object(recognition, 'generate_embedding', return_value=[1, 0]):
                    results = recognition.compare_with_registered_faces(photo)
                self.assertEqual(len(results), 1)
                self.assertEqual(recognition.classify_results(results)[0], 'ambiguous')

    def test_detection_failure_and_multiple_faces(self):
        for faces in [None, [], [(0, 0, 1, 1), (1, 1, 1, 1)]]:
            with patch('builtins.input', return_value='/tmp/fixture.jpg'), patch.object(main, 'detect_faces', return_value=faces):
                self.assertIsNone(main.ask_photo())

    def test_cancel_does_not_detect(self):
        with patch('builtins.input', return_value='exit'), patch.object(main, 'detect_faces') as detect:
            self.assertIsNone(main.ask_photo())
            detect.assert_not_called()

    def test_registration_rolls_back_copied_photo(self):
        with tempfile.TemporaryDirectory() as tmp:
            copied = Path(tmp) / 'copied.jpg'
            copied.write_bytes(b'fixture')
            with patch.object(database, 'DB_PATH', Path(tmp) / 'test.db'):
                database.create_table()
                with patch('builtins.input', side_effect=['1', 'A']), patch.object(main, 'ask_photo', return_value=Path('/tmp/input.jpg')), patch.object(main, 'generate_embedding'), patch.object(main, 'save_person_photo', return_value=str(copied)), patch.object(main, 'register_person', side_effect=RuntimeError('DB failure')):
                    with self.assertRaises(RuntimeError):
                        main.register()
                self.assertFalse(copied.exists())

    def test_menu_recovers_and_exits(self):
        with patch.object(main, 'create_table'), patch('builtins.input', side_effect=['2', '4']), patch.object(main, 'recognize', side_effect=ValueError('fixture failure')):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                main.main()
            self.assertIn('Returning to the main menu.', output.getvalue())

    def test_model_contract(self):
        fake = types.SimpleNamespace(represent=lambda **kwargs: [{'embedding': [1] * 512}])
        with patch.object(face_embedding, 'DeepFace', fake):
            self.assertEqual(len(face_embedding.generate_embedding('fixture')), 512)
        fake.represent = lambda **kwargs: [{'embedding': [1] * 3}]
        with patch.object(face_embedding, 'DeepFace', fake), self.assertRaises(ValueError):
            face_embedding.generate_embedding('fixture')


if __name__ == '__main__':
    unittest.main()
