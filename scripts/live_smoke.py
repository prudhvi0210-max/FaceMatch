"""Opt-in real-model checks using authorized local photos and disposable enrollment."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,required=True,help='Private evaluation folder containing dataset/test_dataset/unknown_dataset.')
    parser.add_argument('--output',type=Path,required=True,help='New private result directory; must not exist.')
    parser.add_argument('--authorized-test-data',action='store_true',help='Confirm that these photos may be processed locally for this test.')
    args=parser.parse_args()
    if not args.authorized_test_data:parser.error('Confirm permission with --authorized-test-data before processing photos.')
    paths=[args.data_root/'dataset/person_01/test.jpg',args.data_root/'test_dataset/person_01/normal_01.jpg',args.data_root/'unknown_dataset/unknown_01/normal_01.jpg']
    if not all(p.is_file() for p in paths):parser.error('Required private test photographs are unavailable. See the demo script for manual checks.')
    args.output.mkdir(parents=True,exist_ok=False)
    checks=[];start=time.time()
    def record(name,passed,**observed):
        checks.append(dict(check=name,passed=bool(passed),**observed));print(name,'PASS' if passed else 'FAIL',flush=True)
    def rejected(name,fn,expected=ValueError,contains=None):
        try:fn()
        except expected as error:record(name,contains is None or contains in str(error),message=str(error))
        else:record(name,False,message='Unexpected success')
    def payload(path):return dict(filename=path.name,image=base64.b64encode(path.read_bytes()).decode())
    with tempfile.TemporaryDirectory(prefix='facematch-live-') as folder:
        os.environ['FACEMATCH_DATA_DIR']=folder
        sys.path.insert(0,str(ROOT/'app'))
        import cv2
        import numpy as np
        import database,ui_service,face_utils
        from face_embedding import generate_embedding
        from deepface import DeepFace
        database.create_table()
        try:
            record('fresh_database_empty',ui_service.people()==[])
            missing=Path(folder)/'missing.jpg'
            record('missing_path_rejected',face_utils.detect_faces(missing) is None)
            broken=Path(folder)/'broken.jpg';broken.write_bytes(b'not an image')
            record('unreadable_image_rejected',face_utils.detect_faces(broken) is None)
            blank=Path(folder)/'blank.png';cv2.imwrite(str(blank),np.full((400,400,3),255,dtype=np.uint8))
            rejected('no_face_rejected',lambda:ui_service.recognize(payload(blank)))
            valid_query=payload(paths[1])
            record('empty_gallery_unavailable',ui_service.recognize(valid_query)['decision']=='unavailable')
            registration=dict(payload(paths[0]),person_id='smoke-01',name='Smoke-test participant',consent=True)
            rejected('permission_required',lambda:ui_service.register(dict(registration,consent=False)))
            result=ui_service.register(registration)
            record('real_registration',len(ui_service.people())==1 and 'successfully' in result['message'])
            env=dict(os.environ,PYTHONPATH=str(ROOT/'app'))
            persisted=json.loads(subprocess.check_output([sys.executable,'-B','-c',"import json;from database import get_all_persons;print(json.dumps(get_all_persons()))"],env=env,text=True))
            record('persistence_across_processes',persisted==[['smoke-01','Smoke-test participant']])
            rejected('duplicate_id_rejected',lambda:ui_service.register(dict(registration,name='Must not replace')))
            record('duplicate_did_not_overwrite',ui_service.people()[0]['name']=='Smoke-test participant')
            vector=generate_embedding(paths[1]);record('valid_embedding',len(vector)==512 and bool(np.isfinite(vector).all()))
            faces=DeepFace.extract_faces(img_path=str(paths[0]),detector_backend='retinaface',align=True,enforce_detection=True)
            crop=faces[0]['face'];record('aligned_face_crop_returned',len(faces)==1 and crop.ndim==3 and crop.shape[0]>0 and crop.shape[1]>0,crop_shape=list(crop.shape))
            matched=ui_service.recognize(valid_query)
            record('known_person_possible_match',matched['decision']=='possible' and matched['best']['person_id']=='smoke-01',decision=matched['decision'],score=matched['results'][0]['similarity'])
            unknown=ui_service.recognize(payload(paths[2]))
            record('unknown_person_rejected',unknown['decision']=='unknown',decision=unknown['decision'],best_score=unknown['results'][0]['similarity'])
            original=cv2.imread(str(paths[0]));height=600;width=round(original.shape[1]*height/original.shape[0])
            panel=cv2.resize(original,(width,height));gap=np.full((height,100,3),255,dtype=np.uint8)
            multi=Path(folder)/'synthetic_two_faces.png';cv2.imwrite(str(multi),np.concatenate([panel,gap,panel],axis=1))
            rejected('synthetic_two_face_input_rejected',lambda:ui_service.recognize(payload(multi)),contains='More than one face')
            with database.connect() as conn:saved=Path(conn.execute('SELECT photo_path FROM persons').fetchone()[0])
            # Delete only the disposable copy created by this test, never the input photo.
            assert saved.resolve().is_relative_to(Path(folder).resolve())
            saved.unlink()
            record('missing_reference_flagged',ui_service.people()[0]['status']=='Reference unavailable')
            record('missing_reference_unavailable',ui_service.recognize(valid_query)['decision']=='unavailable')
        except Exception as error:
            record('unexpected_exception',False,error_type=type(error).__name__,message=str(error))
    report=dict(timestamp=datetime.now(timezone.utc).isoformat(),python=sys.version,checks=checks,all_passed=all(x['passed'] for x in checks),seconds=round(time.time()-start,2),notes=['All enrollment and synthetic image fixtures were disposable and removed.','Original private photographs and enrolled production records were not edited.','The two-face test used a synthetic side-by-side duplicate; natural group-photo detection and independent accuracy remain separate.'])
    (args.output/'live_smoke.json').write_text(json.dumps(report,indent=2))
    if not report['all_passed']:raise SystemExit('Some checks failed; inspect live_smoke.json.')


if __name__=='__main__':main()
