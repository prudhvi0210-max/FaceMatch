"""UI service and local HTTP integration tests. No real photos or databases."""
import base64
from contextlib import contextmanager
import http.client
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch, Mock
import types

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
import database
import ui
import ui_service as service

PHOTO = dict(filename='photo.png', image=base64.b64encode(b'\x89PNG\r\n\x1a\nfixture').decode())


class ServiceTests(unittest.TestCase):
    def test_closed_browser_response_is_safe(self):
        handler = object.__new__(ui.Handler)
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()
        handler.wfile = types.SimpleNamespace(write=Mock(side_effect=BrokenPipeError()))
        handler.reply(200, {'message': 'Registration succeeded.'})

    def test_upload_cleanup_and_validation(self):
        with service.uploaded_photo(PHOTO) as path:
            self.assertTrue(path.is_file())
        self.assertFalse(path.exists())
        for bad in [{}, dict(PHOTO, filename='x.svg'), dict(PHOTO,image='bad'), dict(PHOTO,image=base64.b64encode(b'not an image').decode())]:
            with self.assertRaises(ValueError), service.uploaded_photo(bad):
                pass

    def test_upload_size_limit(self):
        with patch.object(service, 'MAX_IMAGE_BYTES', 8):
            with self.assertRaises(ValueError), service.uploaded_photo(PHOTO):
                pass

    def test_registration_requires_permission(self):
        with self.assertRaises(ValueError):
            service.register(dict(PHOTO, person_id='1',name='Name',consent=False))

    def test_directory_status(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(database,'DB_PATH',Path(folder)/'db.sqlite'):
            database.create_table()
            photo=Path(folder)/'fixture';photo.write_bytes(b'photo')
            database.register_person('1','A',str(photo))
            database.register_person('2','B',str(photo))
            database.register_person('3','C')
            database.register_person('4','D',str(photo)+'.missing')
            people=service.people()
            self.assertEqual([p['status'] for p in people],['Duplicate reference','Duplicate reference','No reference photo','Reference unavailable'])
            self.assertNotIn('photo_path',json.dumps(people))

    def test_registration_cleanup_on_database_failure(self):
        import face_embedding
        with tempfile.TemporaryDirectory() as folder, patch.object(database,'DB_PATH',Path(folder)/'db.sqlite'):
            database.create_table()
            copied=Path(folder)/'copy.png';copied.write_bytes(b'fixture')
            with patch.object(service,'validate_face'), patch.object(face_embedding,'generate_embedding'), patch.object(service,'save_person_photo',return_value=str(copied)), patch.object(service,'register_person',side_effect=RuntimeError('failure')):
                with self.assertRaises(RuntimeError):
                    service.register(dict(PHOTO,person_id='1',name='A',consent=True))
            self.assertFalse(copied.exists())
            self.assertEqual(service.people(),[])

    def test_successful_registration(self):
        import face_embedding
        with tempfile.TemporaryDirectory() as folder, patch.object(database,'DB_PATH',Path(folder)/'db.sqlite'):
            database.create_table()
            copied=Path(folder)/'copy.png';copied.write_bytes(b'fixture')
            with patch.object(service,'validate_face'), patch.object(face_embedding,'generate_embedding'), patch.object(service,'save_person_photo',return_value=str(copied)):
                result=service.register(dict(PHOTO,person_id='1',name='A',consent=True))
            self.assertIn('successfully',result['message'])
            self.assertEqual(service.people()[0]['name'],'A')
            self.assertTrue(copied.exists())


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.dbpatch=patch.object(database,'DB_PATH',Path(self.folder.name)/'db.sqlite');self.dbpatch.start()
        database.create_table()
        self.server=ui.LocalServer(('127.0.0.1',0))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join()
        self.dbpatch.stop();self.folder.cleanup()

    def request(self,method,path,body=None,headers=None):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        conn.request(method,path,body=body,headers=headers or {})
        response=conn.getresponse();data=response.read();status=response.status;meta=dict(response.getheaders());conn.close()
        return status,data,meta

    def headers(self):
        return {'Content-Type':'application/json','Origin':self.server.origin,'X-FaceMatch-Token':self.server.token}

    def test_assets_and_private_paths(self):
        for path in ['/','/app.css','/app.js']:
            status,data,headers=self.request('GET',path)
            self.assertEqual(status,200)
            self.assertEqual(headers['Cache-Control'],'no-store')
        for path in ['/../database/facematch.db','/database/facematch.db','/app/../database/facematch.db']:
            self.assertEqual(self.request('GET',path)[0],404)

    def test_state_and_cross_origin_rejection(self):
        status,body,_=self.request('GET','/api/state')
        self.assertEqual(status,200);self.assertEqual(json.loads(body)['people'],[])
        self.assertEqual(self.request('GET','/api/state',headers={'Host':'evil.example'})[0],403)
        self.assertEqual(self.request('POST','/api/register','{}')[0],403)
        bad=dict(self.headers(),Origin='https://evil.example')
        self.assertEqual(self.request('POST','/api/register','{}',bad)[0],403)

    def test_recognition_response_and_busy(self):
        with patch.object(service,'recognize',return_value=dict(decision='unknown',best=None,results=[])):
            status,body,_=self.request('POST','/api/recognize',json.dumps(PHOTO),self.headers())
            self.assertEqual(status,200);self.assertEqual(json.loads(body)['decision'],'unknown')
        with self.server.operation:
            self.assertEqual(self.request('POST','/api/recognize','{}',self.headers())[0],409)

    def test_validation_and_failure_recovery(self):
        self.assertEqual(self.request('POST','/api/recognize','[1]',self.headers())[0],400)
        with patch.object(service,'recognize',side_effect=RuntimeError('internal secret')):
            status,body,_=self.request('POST','/api/recognize','{}',self.headers())
            self.assertEqual(status,500);self.assertNotIn(b'internal secret',body)
        self.assertFalse(self.server.operation.locked())
        with patch.object(service,'recognize',side_effect=ValueError('No face detected.')):
            self.assertEqual(self.request('POST','/api/recognize','{}',self.headers())[0],400)


if __name__ == '__main__':
    unittest.main()
