"""FaceMatch for Windows: a windowed executable, not a console launcher."""
import argparse
import ctypes
import importlib.metadata as metadata
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys
import tempfile
import urllib.request

# PyInstaller stores bundled modules/assets under its internal resource directory.
HERE = Path(__file__).resolve().parent
if not getattr(sys, 'frozen', False):
    sys.path.insert(0, str(HERE.parents[0]/'app'))
    sys.path.insert(0, str(HERE))
from windows_runtime import configure_storage, start_service, stop_service


def error_dialog(message):
    if sys.platform == 'win32':
        ctypes.windll.user32.MessageBoxW(None, message, 'FaceMatch', 0x10)
    elif sys.stderr is not None:
        print(message, file=sys.stderr)


def smoke_test(output, load_models=False):
    """Frozen-executable verification without private photographs or a GUI."""
    if output.exists():raise ValueError('Smoke report already exists; use a new path.')
    saved = {key:os.environ.get(key) for key in ['FACEMATCH_DATA_DIR','DEEPFACE_HOME']}
    try:
        with tempfile.TemporaryDirectory(prefix='facematch-windows-smoke-') as folder:
            os.environ['FACEMATCH_DATA_DIR'] = folder
            os.environ['DEEPFACE_HOME'] = folder
            configure_storage()
            import cv2, numpy, onnxruntime
            from deepface import DeepFace
            server, thread = start_service()
            try:
                for route, kind in [('/', 'text/html'),('/app.js','text/javascript'),('/app.css','text/css')]:
                    with urllib.request.urlopen(server.origin+route, timeout=15) as response:
                        assert response.status==200 and kind in response.headers['Content-Type']
                with urllib.request.urlopen(server.origin+'/api/state', timeout=15) as response:
                    state=json.load(response)
                assert state['people']==[] and state['threshold']==0.50
                try:urllib.request.urlopen(server.origin+'/database/facematch.db',timeout=15)
                except urllib.error.HTTPError as error:assert error.code==404
                else:raise AssertionError('Private database route was exposed')
                if load_models:
                    assert DeepFace.build_model('Facenet512') is not None
                    assert DeepFace.build_model('retinaface', task='face_detector') is not None
                result=dict(status='passed',python=sys.version,packages={name:metadata.version(name) for name in ['deepface','retina-face','numpy','onnxruntime','pywebview']},empty_database=True,assets_loaded=True,private_routes_blocked=True,models_loaded=load_models,gui='not tested by this headless check')
            finally:stop_service(server,thread)
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(result,indent=2))
        return 0
    finally:
        for key,value in saved.items():
            if value is None:os.environ.pop(key,None)
            else:os.environ[key]=value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--smoke-test',type=Path,metavar='NEW_REPORT_JSON')
    parser.add_argument('--load-models',action='store_true')
    args=parser.parse_args()
    if sys.platform!='win32':
        parser.error('This launcher is for Windows. Use the native Mac app on macOS.')
    if sys.stdout is None:sys.stdout=open(os.devnull,'w',encoding='utf-8')
    if sys.stderr is None:sys.stderr=open(os.devnull,'w',encoding='utf-8')
    if args.smoke_test:
        # No dialogs in automated builds. A failure report makes a windowed crash visible.
        try:return smoke_test(args.smoke_test,args.load_models)
        except Exception as error:
            args.smoke_test.parent.mkdir(parents=True,exist_ok=True)
            if not args.smoke_test.exists():args.smoke_test.write_text(json.dumps(dict(status='failed',error_type=type(error).__name__,message=str(error)),indent=2))
            return 1
    try:
        root=configure_storage()
        logger=logging.getLogger('facematch.desktop');logger.setLevel(logging.ERROR)
        handler=RotatingFileHandler(root/'desktop.log',maxBytes=262144,backupCount=1,encoding='utf-8')
        logger.addHandler(handler)
    except OSError:
        error_dialog('FaceMatch cannot open its private application-data folder. Check that your Windows account can write to its Local AppData folder, then try again.')
        return 1
    server=thread=None
    try:
        import webview
        server,thread=start_service()
        window=webview.create_window('FaceMatch',url=server.origin,width=1200,height=850,min_size=(820,620),background_color='#f7f8f4',text_select=True)
        def can_close():
            if server.operation.locked():
                return window.create_confirmation_dialog('A photograph is still processing','Quitting now interrupts this operation. Quit FaceMatch anyway?')
            return True
        window.events.closing += can_close
        icon=Path(getattr(sys,'_MEIPASS',str(HERE)))/'FaceMatch.ico'
        webview.start(gui='edgechromium',debug=False,private_mode=True,icon=str(icon) if icon.is_file() else None)
        return 0
    except Exception:
        logger.exception('Desktop startup/window failure')
        error_dialog('FaceMatch could not open its window. Make sure Microsoft Edge WebView2 Runtime is installed, then try again. If the problem continues, the local desktop.log in your FaceMatch application-data folder contains diagnostic details.')
        return 1
    finally:
        if server is not None:stop_service(server,thread)
        handler.close();logger.removeHandler(handler)
        # Do not close stdout/stderr while a third-party atexit handler might use it.


if __name__=='__main__':raise SystemExit(main())
