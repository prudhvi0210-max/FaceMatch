# Run on 64-bit Windows with Python 3.11. Never collect the project tree or user cache.
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules, copy_metadata

ROOT=Path(SPECPATH).resolve().parents[1]
work=Path(DISTPATH).resolve().parent
icon=work/'FaceMatch.ico'
datas=[(str(ROOT/'app/web'),'web'),(str(icon),'.')]
binaries=[]
hidden=['ui','ui_service','settings','database','photo_storage','face_utils','face_embedding','recognize_face','image_input','windows_runtime']
for package in ['deepface','retinaface']:
    datas += collect_data_files(package,excludes=['**/*.jpg','**/*.jpeg','**/*.png','**/*.onnx','**/*.h5','**/*.pkl'])
    hidden += collect_submodules(package)
web_data,web_binaries,web_hidden=collect_all('webview')
datas += [(source,target) for source,target in web_data if Path(source).suffix.lower() not in {'.png','.jpg','.jpeg','.onnx','.h5','.pkl','.npy','.npz'}]
binaries += web_binaries;hidden += web_hidden
for distribution in ['deepface','retina-face','pywebview']:
    datas += copy_metadata(distribution,recursive=True)

analysis=Analysis([str(ROOT/'desktop/windows_launcher.py')],pathex=[str(ROOT/'app'),str(ROOT/'desktop')],binaries=binaries,datas=datas,hiddenimports=hidden,hookspath=[],hooksconfig={},runtime_hooks=[],excludes=['tensorflow','torch','PyQt5','PyQt6','PySide2','PySide6','webview.platforms.cocoa','webview.platforms.gtk','webview.platforms.qt','webview.platforms.cef'],noarchive=False)
pyz=PYZ(analysis.pure)
exe=EXE(pyz,analysis.scripts,[],exclude_binaries=True,name='FaceMatch',debug=False,bootloader_ignore_signals=False,strip=False,upx=False,console=False,icon=str(icon),version=str(ROOT/'desktop/windows/version_info.txt'))
collect=COLLECT(exe,analysis.binaries,analysis.datas,strip=False,upx=False,name='FaceMatch')
