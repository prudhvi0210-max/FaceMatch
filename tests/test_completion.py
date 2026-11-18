"""Persistence, numerical safety, detector errors and evaluation protocol regression checks."""
import importlib.util
from pathlib import Path
import sqlite3
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
sys.modules.setdefault('deepface',types.SimpleNamespace(DeepFace=types.SimpleNamespace()))
import database
import face_utils
import recognize_face
import photo_storage
sys.path.insert(0,str(ROOT/'evaluation'))
import reproduce


class PersistenceTests(unittest.TestCase):
    def test_schema_migration_and_persistence(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(database,'DB_PATH',Path(folder)/'old.db'):
            conn=sqlite3.connect(database.DB_PATH);conn.execute('CREATE TABLE persons (id TEXT PRIMARY KEY, name TEXT NOT NULL)');conn.execute("INSERT INTO persons VALUES ('old','Existing')");conn.commit();conn.close()
            database.create_table()
            self.assertTrue(database.register_person('new','New','reference.jpg'))
            self.assertFalse(database.register_person('new','Replacement','other.jpg'))
            with database.connect() as conn:
                self.assertEqual(conn.execute('SELECT name,photo_path FROM persons WHERE id=?',('new',)).fetchone(),('New','reference.jpg'))
                self.assertEqual(conn.execute('SELECT name FROM persons WHERE id=?',('old',)).fetchone(),('Existing',))
            with self.assertRaises(sqlite3.ProgrammingError):conn.execute('SELECT 1')

    def test_invalid_ids(self):
        for person_id,name in [('', 'A'),('1',''),(None,'A'),('x'*81,'A')]:
            with self.assertRaises(ValueError):database.register_person(person_id,name)

    def test_partial_copy_cleanup(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(photo_storage,'STORAGE_DIR',Path(folder)/'private'):
            source=Path(folder)/'source.jpg';source.write_bytes(b'fixture')
            def fail(source,destination):
                destination.write_bytes(b'partial');raise OSError('disk full fixture')
            with patch.object(photo_storage.shutil,'copy2',side_effect=fail),self.assertRaises(OSError):
                photo_storage.save_person_photo('1',source)
            self.assertEqual(list(photo_storage.STORAGE_DIR.iterdir()),[])

    def test_empty_gallery_does_not_infer(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(database,'DB_PATH',Path(folder)/'empty.db'):
            database.create_table()
            with patch.object(recognize_face,'generate_embedding') as model:
                self.assertEqual(recognize_face.compare_with_registered_faces('/missing'),[])
                model.assert_not_called()

    def test_unsorted_and_nonfinite_results(self):
        rows=[dict(person_id='1',similarity=.2),dict(person_id='2',similarity=.6)]
        decision,best=recognize_face.classify_results(rows)
        self.assertEqual(decision,'possible');self.assertEqual(best['person_id'],'2')
        rows.append(dict(person_id='3',similarity=float('nan')))
        self.assertEqual(recognize_face.classify_results(rows)[0],'unavailable')

    def test_unreadable_image(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'broken.jpg';path.write_bytes(b'not a photograph')
            self.assertIsNone(face_utils.detect_faces(path))

    def test_model_value_error_not_reported_as_no_face(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'photo.jpg';path.write_bytes(b'fixture')
            fake=types.SimpleNamespace(extract_faces=lambda **kw: (_ for _ in ()).throw(ValueError('invalid model fixture')))
            with patch.object(face_utils.cv2,'imread',return_value=object()),patch.object(face_utils,'DeepFace',fake),self.assertRaisesRegex(RuntimeError,'model setup'):
                face_utils.detect_faces(path)

    def test_model_failure_not_reported_as_no_face(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'photo.jpg';path.write_bytes(b'fixture')
            fake=types.SimpleNamespace(extract_faces=lambda **kw: (_ for _ in ()).throw(RuntimeError('model unavailable')))
            with patch.object(face_utils.cv2,'imread',return_value=object()),patch.object(face_utils,'DeepFace',fake),self.assertRaisesRegex(RuntimeError,'model setup'):
                face_utils.detect_faces(path)


class EvaluationTests(unittest.TestCase):
    def test_validation_uses_canonical_keys(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            path=root/'validation_dataset/registered/p/a.png'
            path.parent.mkdir(parents=True);path.write_bytes(b'fixture')
            rows=reproduce.load_datasets(root,validation=True)
            self.assertEqual(rows['test_dataset'][0]['split'],'test_dataset')

    def test_pair_metrics(self):
        m=reproduce.metrics([(True,.9),(True,.1),(False,.9),(False,.1)],.5)
        self.assertEqual((m['tp'],m['tn'],m['fp'],m['fn']),(1,1,1,1));self.assertEqual(m['f1'],.5)
        self.assertIsNone(reproduce.metrics([],.5)['accuracy'])

    def test_failed_queries_stay_in_denominator(self):
        ref=dict(person='p',relative='p/a',sha256='a')
        queries=[dict(split='test_dataset',relative='p/b',person='p'),dict(split='test_dataset',relative='p/c',person='p'),dict(split='unknown_dataset',relative='u/a',person='u')]
        vectors={('test_dataset','p/b'):[1.,0.],('unknown_dataset','u/a'):[0.,1.]}
        summary,details=reproduce.summarize([(ref,[1.,0.])],queries,vectors,.5)
        self.assertEqual(summary['registered_total'],2);self.assertEqual(summary['registered_accuracy'],.5);self.assertEqual(summary['registered_failure'],1)
        self.assertEqual(summary['unknown_rejection_rate'],1)

    def test_duplicate_and_tied_references(self):
        one=dict(person='a',relative='a/x',sha256='same');two=dict(person='b',relative='b/x',sha256='same')
        self.assertEqual(reproduce.predict([(one,[1,0]),(two,[1,0])],[1,0],.5)[0],'Ambiguous')
        self.assertEqual(reproduce.predict([], [1,0], .5)[0],'Unavailable')

    def test_split_leakage(self):
        import cv2,numpy as np
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for split,person in [('dataset','p'),('test_dataset','p'),('unknown_dataset','u')]:
                dest=root/split/person;dest.mkdir(parents=True)
                cv2.imwrite(str(dest/'a.png'),np.zeros((10,10,3),dtype=np.uint8))
            splits={name:reproduce.load_split(root,name) for name in ['dataset','test_dataset','unknown_dataset']}
            audit=reproduce.audit_splits(splits)
            self.assertTrue(audit['errors']);self.assertTrue(audit['overlaps'])


if __name__=='__main__':unittest.main()
