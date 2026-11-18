"""Read-only setup check. Does not install packages or download model weights."""
import importlib.metadata as metadata
import os
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    failed = False
    print('FaceMatch setup check')
    print(f'Python: {platform.python_version()} / {platform.machine()}')
    if sys.version_info[:2] != (3,11):
        print('ERROR: use CPython 3.11, the tested version for this project.')
        failed = True
    for name in ['deepface','retina-face','numpy','opencv-contrib-python-headless','onnxruntime','pandas','Pillow']:
        try:print(f'{name}: {metadata.version(name)}')
        except metadata.PackageNotFoundError:
            print(f'ERROR: missing {name}; install requirements.txt in your virtual environment.');failed=True
    try:
        metadata.version('opencv-python')
        print('WARNING: multiple OpenCV distributions are installed; preserve the old environment, but use only requirements.txt in a clean one.')
    except metadata.PackageNotFoundError:pass
    weights=Path(os.environ.get('DEEPFACE_HOME',str(Path.home())))/'.deepface'/'weights'
    print('Model-weight directory exists:',weights.is_dir())
    print('First recognition may download pretrained weights and needs internet until those weights are cached.')
    private=Path(os.environ.get('FACEMATCH_DATA_DIR',str(ROOT))).expanduser().resolve()
    print('Private storage root:',private)
    print('Use FACEMATCH_DATA_DIR to isolate a demonstration from existing records.')
    if platform.system()=='Darwin':
        print('Keep the project, virtual environment and model weights downloaded locally; iCloud-only files can stall imports.')
    return 1 if failed else 0


if __name__=='__main__':raise SystemExit(main())
