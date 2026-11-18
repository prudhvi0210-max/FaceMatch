"""Build a Windows x64 app/installer on Windows. No personal data is bundled."""
import argparse
from datetime import datetime
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[1]
BOOTSTRAPPER_URL='https://go.microsoft.com/fwlink/p/?LinkId=2124703'


def make_icon(path):
    from PIL import Image, ImageDraw
    image=Image.new('RGBA',(1024,1024),(0,0,0,0));draw=ImageDraw.Draw(image)
    draw.rounded_rectangle((55,55,969,969),radius=210,fill='#215e47')
    white='#edf7de'
    for x,y,sx,sy in [(250,250,1,1),(774,250,-1,1),(250,774,1,-1),(774,774,-1,-1)]:
        draw.line([(x,y+sy*100),(x,y),(x+sx*100,y)],fill=white,width=29)
    draw.ellipse((419,345,605,572),outline=white,width=23)
    draw.arc((341,535,683,805),180,360,fill=white,width=23)
    image.save(path,format='ICO',sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])


def check_bundle(folder):
    exe=folder/'FaceMatch.exe'
    if not exe.is_file():raise ValueError('FaceMatch.exe is missing from the bundle.')
    banned={'dataset','test_dataset','unknown_dataset','unknown_originals','validation_dataset','sample_images','registered_faces','database','private_embedding_cache','.git','.venv','outputs'}
    forbidden={'.jpg','.jpeg','.png','.db','.sqlite','.sqlite3','.npy','.npz','.onnx','.h5','.env','.bak'}
    for path in folder.rglob('*'):
        relative=path.relative_to(folder)
        if path.is_symlink():raise ValueError('Unexpected symlink in Windows bundle: '+str(relative))
        if path.is_file() and (set(relative.parts)&banned or path.suffix.lower() in forbidden or path.name.startswith('.env')):
            raise ValueError('Unexpected private-data/model file in Windows bundle: '+str(relative))
    return sum(1 for path in folder.rglob('*') if path.is_file())


def download_webview_bootstrapper(destination):
    with urllib.request.urlopen(BOOTSTRAPPER_URL,timeout=120) as response:
        data=response.read(5*1024*1024+1)
    if len(data)>5*1024*1024 or not data.startswith(b'MZ'):
        raise ValueError('Unexpected WebView2 bootstrapper response.')
    destination.write_bytes(data)
    # Verify the actual publisher on Windows; never disable certificate checks.
    escaped=str(destination).replace("'","''")
    command=f"$s=Get-AuthenticodeSignature -LiteralPath '{escaped}'; if ($s.Status -ne 'Valid' -or $s.SignerCertificate.Subject -notmatch 'Microsoft Corporation') {{ throw 'WebView2 bootstrapper signature is not valid Microsoft software' }}"
    subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',command],check=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--portable-only',action='store_true')
    parser.add_argument('--load-models',action='store_true',help='Also verify frozen model loading; downloads weights into disposable smoke-test storage.')
    args=parser.parse_args()
    if sys.platform!='win32' or platform.machine().lower() not in {'amd64','x86_64'} or sys.maxsize<=2**32:
        parser.error('Build on x64 Windows with x64 Python 3.11; macOS cross-compilation is not supported.')
    if sys.version_info[:2]!=(3,11):parser.error('Use the project’s supported Python 3.11 build environment.')
    output=(args.output or ROOT/'dist'/('windows_'+datetime.now().strftime('%Y%m%d_%H%M%S'))).resolve()
    output.mkdir(parents=True,exist_ok=False)
    make_icon(output/'FaceMatch.ico')
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--distpath',str(output/'bundle'),'--workpath',str(output/'work'),str(ROOT/'desktop/windows/FaceMatch.spec')],check=True,cwd=ROOT)
    bundle=output/'bundle/FaceMatch'
    check_bundle(bundle)
    artifacts=output/'artifacts';artifacts.mkdir()
    report_path=artifacts/'frozen-smoke.json'
    command=[str(bundle/'FaceMatch.exe'),'--smoke-test',str(report_path)]
    if args.load_models:command.append('--load-models')
    subprocess.run(command,check=True,timeout=900,cwd=bundle)
    if not report_path.is_file() or json.loads(report_path.read_text())['status']!='passed':
        raise ValueError('Frozen executable did not produce a passing smoke report.')
    (bundle/'START-HERE.txt').write_text('FaceMatch for Windows 11 x64\n\nOpen FaceMatch.exe. Keep the entire extracted folder together.\nPython is bundled; no Terminal or Python installation is needed.\nMicrosoft Edge WebView2 Runtime is required. Use the installer if it is missing.\nInternet is needed for uncached model weights. Photos are processed locally.\nYour records and model cache are under %LOCALAPPDATA%\\FaceMatch.\nNo personal records or photographs are included.\nThis is an academic prototype, not proof of identity.\n',encoding='utf-8')
    count=check_bundle(bundle)
    portable=artifacts/'FaceMatch-Windows-x64.zip'
    with zipfile.ZipFile(portable,'w',zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(bundle.rglob('*')):
            if file.is_file():archive.write(file,Path('FaceMatch')/file.relative_to(bundle))
    if not args.portable_only:
        bootstrapper=output/'MicrosoftEdgeWebview2Setup.exe';download_webview_bootstrapper(bootstrapper)
        iscc=shutil.which('ISCC.exe') or str(Path(os.environ.get('ProgramFiles(x86)',r'C:\Program Files (x86)'))/'Inno Setup 6/ISCC.exe')
        if not Path(iscc).is_file():raise SystemExit('Install Inno Setup 6, or use --portable-only for a ZIP without the installer.')
        subprocess.run([iscc,'/Qp','/DBundleDir='+str(bundle),'/DOutputDir='+str(artifacts),'/DWebViewBootstrapper='+str(bootstrapper),str(ROOT/'desktop/windows/FaceMatch.iss')],check=True)
    (artifacts/'requirements-resolved-windows.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True))
    manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts.iterdir() if p.suffix.lower() in {'.exe','.zip'}}
    (artifacts/'SHA256SUMS.txt').write_text(''.join(f'{checksum}  {name}\n' for name,checksum in sorted(manifest.items())))
    (artifacts/'BUILD-INFO.json').write_text(json.dumps(dict(target='Windows 11 x64',python=sys.version,pyinstaller=metadata.version('pyinstaller'),pywebview=metadata.version('pywebview'),bundle_files=count,private_data_check='passed',frozen_backend_smoke='passed',model_load_check='passed' if args.load_models else 'not run',native_gui='requires separate Windows interactive verification',code_signing='FaceMatch executable and setup are unsigned development builds'),indent=2))
    print('Windows build artifacts:',artifacts)


if __name__=='__main__':main()
