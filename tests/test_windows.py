"""Cross-platform checks of Windows storage, local service and bundle privacy rules.
These are not evidence that a Windows GUI or .exe runs on macOS.
"""
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'desktop'))
sys.path.insert(0,str(ROOT/'app'))
import windows_runtime
spec=importlib.util.spec_from_file_location('windows_builder',ROOT/'scripts/build_windows_app.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)


class UnicodeImageTests(unittest.TestCase):
    def test_ascii_paths_keep_existing_behavior(self):
        from image_input import face_image_input
        self.assertEqual(face_image_input('ordinary-photo.jpg'),'ordinary-photo.jpg')

    def test_unicode_image_decoded_before_model(self):
        import cv2,numpy as np
        from image_input import face_image_input
        import face_embedding
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'participant-é.png'
            path.write_bytes(cv2.imencode('.png',np.zeros((20,30,3),dtype=np.uint8))[1].tobytes())
            pixels=face_image_input(path)
            self.assertEqual(pixels.shape,(20,30,3))
            with patch.object(face_embedding,'DeepFace') as model:
                model.represent.return_value=[{'embedding':[1]*512}]
                face_embedding.generate_embedding(path)
                self.assertIsInstance(model.represent.call_args.kwargs['img_path'],np.ndarray)

    def test_corrupt_unicode_image_rejected(self):
        from image_input import face_image_input
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'é.png';path.write_bytes(b'corrupt')
            with self.assertRaises(ValueError):face_image_input(path)


class WindowsStorageTests(unittest.TestCase):
    def test_local_user_storage_not_install_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            env={'LOCALAPPDATA':str(Path(folder)/'local data')}
            root=windows_runtime.configure_storage(env)
            self.assertEqual(root,Path(folder).resolve()/'local data/FaceMatch')
            self.assertEqual(env['FACEMATCH_DATA_DIR'],str(root));self.assertEqual(env['DEEPFACE_HOME'],str(root))
            self.assertTrue(root.is_dir())

    def test_explicit_root_and_model_home_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            env={'LOCALAPPDATA':str(Path(folder)/'unused'),'FACEMATCH_DATA_DIR':str(Path(folder)/'chosen'),'DEEPFACE_HOME':str(Path(folder)/'models')}
            root=windows_runtime.configure_storage(env)
            self.assertEqual(root,Path(folder).resolve()/'chosen')
            self.assertEqual(env['DEEPFACE_HOME'],str(Path(folder)/'models'))

    def test_home_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            root=windows_runtime.configure_storage({},home=folder)
            self.assertEqual(root,Path(folder).resolve()/'AppData/Local/FaceMatch')

    def test_existing_records_not_removed(self):
        with tempfile.TemporaryDirectory() as folder:
            env={'LOCALAPPDATA':folder}
            root=windows_runtime.configure_storage(env)
            record=root/'existing-record.txt';record.write_text('keep')
            windows_runtime.configure_storage(env)
            self.assertEqual(record.read_text(),'keep')


class WindowsBundleTests(unittest.TestCase):
    def test_private_data_blocked(self):
        for name in ['person.jpg','vectors.npy','model.onnx','database/facematch.db','.env','nested/registered_faces/file.txt']:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as folder:
                root=Path(folder);(root/'FaceMatch.exe').write_bytes(b'MZfixture')
                private=root/name;private.parent.mkdir(parents=True,exist_ok=True);private.write_bytes(b'fixture')
                with self.assertRaises(ValueError):builder.check_bundle(root)

    def test_empty_public_bundle_and_missing_exe(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with self.assertRaises(ValueError):builder.check_bundle(root)
            (root/'FaceMatch.exe').write_bytes(b'MZfixture')
            (root/'_internal').mkdir();(root/'_internal/library.dll').write_bytes(b'MZfixture')
            self.assertEqual(builder.check_bundle(root),2)

    def test_icon_is_windows_ico(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'FaceMatch.ico';builder.make_icon(path)
            with Image.open(path) as image:self.assertEqual(image.format,'ICO')


class WindowsServiceTests(unittest.TestCase):
    def test_service_lifecycle_and_private_routes(self):
        import database
        with tempfile.TemporaryDirectory() as folder,patch.object(database,'DB_PATH',Path(folder)/'test.db'):
            server,thread=windows_runtime.start_service()
            try:
                with urllib.request.urlopen(server.origin+'/api/state',timeout=5) as response:
                    state=json.load(response)
                self.assertEqual(state['people'],[]);self.assertEqual(state['threshold'],.5)
                with urllib.request.urlopen(server.origin,timeout=5) as response:self.assertIn(b'FaceMatch',response.read())
                with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(server.origin+'/database/facematch.db',timeout=5)
                self.assertEqual(error.exception.code,404)
            finally:windows_runtime.stop_service(server,thread)
            self.assertFalse(thread.is_alive())


if __name__=='__main__':unittest.main()
