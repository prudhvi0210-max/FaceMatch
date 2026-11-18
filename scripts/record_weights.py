"""Record hashes of current pretrained cache files without redistributing weights."""
import argparse
import hashlib
import json
import os
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    home=Path(os.environ.get('DEEPFACE_HOME',str(Path.home())))/'.deepface'/'weights'
    result=[]
    for name in ['facenet512_weights.onnx','arcface_weights.onnx','retinaface.onnx']:
        path=home/name
        if path.is_file():
            h=hashlib.sha256()
            with path.open('rb') as stream:
                for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
            result.append(dict(filename=name,bytes=path.stat().st_size,sha256=h.hexdigest()))
        else:result.append(dict(filename=name,status='not present at expected cache location'))
    args.output.write_text(json.dumps(dict(note='Hashes of currently available cache files; historical experiments did not record hashes. Weights are not redistributed.',files=result),indent=2))
    print('Recorded model-cache provenance:',args.output)


if __name__=='__main__':main()
