"""Create a fresh allowlisted submission folder and ZIP; never package private data."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def selected_files():
    files=[]
    for name in ['README.md','.gitignore','requirements.txt','requirements-lock.txt','requirements-recognition.txt','Start FaceMatch.command']:
        files.append(ROOT/name)
    for folder,suffixes in [('app',{'.py','.html','.css','.js'}),('tests',{'.py'}),('scripts',{'.py'}),('evaluation',{'.py'})]:
        for path in (ROOT/folder).rglob('*'):
            if path.is_file() and path.suffix in suffixes and '__pycache__' not in path.parts and not path.is_symlink():
                # Evaluation scripts only; datasets/manifests/caches are never selected.
                if folder=='evaluation' and path.parent!=ROOT/'evaluation':continue
                files.append(path)
    for name in ['ACADEMIC_REPORT.md','PRESENTATION.md','DEMO.md','ETHICS_AND_DATA.md','VALIDATION.md','SUBMISSION_CHECKLIST.md','PROJECT_REPORT.md','THIRD_PARTY_NOTICES.md','HANDOVER.md']:
        files.append(ROOT/'docs'/name)
    files.append(ROOT/'evaluation/README.md')
    results=ROOT/'evaluation/results'
    if results.exists():
        for name in ['summary.csv','pair_metrics.csv','development_threshold_sweep.csv','audit.json','archive_comparison.json','environment.json','live_smoke.json','model_weights.json','handover_checks.json']:
            if (results/name).is_file():files.append(results/name)
    return sorted(set(files))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'submission'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    package=args.output/'FaceMatch';package.mkdir()
    manifest=[]
    for source in selected_files():
        if source.is_symlink():raise SystemExit(f'Symlink not allowed: {source.name}')
        relative=source.relative_to(ROOT)
        dest=package/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
        manifest.append(hashlib.sha256(dest.read_bytes()).hexdigest()+'  '+relative.as_posix())
    (package/'MANIFEST.sha256').write_text('\n'.join(manifest)+'\n')
    archive=args.output/'FaceMatch.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for file in sorted(package.rglob('*')):
            if file.is_file():z.write(file,Path('FaceMatch')/file.relative_to(package))
    with zipfile.ZipFile(archive) as z:
        names=z.namelist()
        banned={'.venv','.git','data','database','sample_images','outputs','__pycache__','dataset','test_dataset','unknown_dataset','unknown_originals','validation_dataset'}
        for name in names:
            path=Path(name)
            if set(path.parts)&banned or path.suffix.lower() in {'.jpg','.jpeg','.png','.db','.sqlite','.npy','.npz','.onnx','.env','.bak'} or path.name.startswith('.env'):
                raise SystemExit('Unexpected private/runtime file in archive: '+name)
        if z.testzip() is not None:raise SystemExit('ZIP integrity check failed')
    report=dict(files=len(names),archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),private_file_check='passed',zip_integrity='passed',requirements='provisional; no course rubric supplied')
    (args.output/'PACKAGE_CHECK.json').write_text(json.dumps(report,indent=2))
    print('Submission folder:',package)
    print('Archive:',archive)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
