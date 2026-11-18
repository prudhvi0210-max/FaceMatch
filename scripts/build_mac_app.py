"""Build a local FaceMatch.app with a native window. Does not bundle private data."""
import argparse
from datetime import datetime
from pathlib import Path
import platform
import plistlib
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def build(project,output,cache):
    if platform.system()!='Darwin':raise SystemExit('The native app builder requires macOS and Apple Command Line Tools.')
    if output.exists():raise SystemExit(f'Output already exists; choose a new path: {output}')
    if not (project/'app/ui.py').is_file():raise SystemExit('Choose the FaceMatch project folder containing app/ui.py.')
    contents=output/'Contents';binary=contents/'MacOS';resources=contents/'Resources'
    binary.mkdir(parents=True);resources.mkdir()
    machine=platform.machine()
    subprocess.run(['xcrun','swiftc','-parse-as-library','-swift-version','5','-module-cache-path',str(cache),'-target',f'{machine}-apple-macos14.0','-O','-framework','Cocoa','-framework','WebKit','-framework','UniformTypeIdentifiers',str(project/'desktop/FaceMatch.swift'),'-o',str(binary/'FaceMatch')],check=True)
    with tempfile.TemporaryDirectory(prefix='facematch-icon-') as folder:
        iconset=Path(folder)/'FaceMatch.iconset'
        icon_binary=Path(folder)/'MakeIcon'
        subprocess.run(['xcrun','swiftc','-swift-version','5','-module-cache-path',str(cache),'-target',f'{machine}-apple-macos14.0',str(project/'desktop/MakeIcon.swift'),'-o',str(icon_binary)],check=True)
        subprocess.run([str(icon_binary),str(iconset)],check=True)
        subprocess.run(['iconutil','-c','icns',str(iconset),'-o',str(resources/'FaceMatch.icns')],check=True)
    info=dict(CFBundleName='FaceMatch',CFBundleDisplayName='FaceMatch',CFBundleExecutable='FaceMatch',CFBundleIdentifier='org.facematch.prototype',CFBundleVersion='2',CFBundleShortVersionString='1.1',CFBundlePackageType='APPL',CFBundleIconFile='FaceMatch.icns',LSMinimumSystemVersion='14.0',NSHighResolutionCapable=True,NSPrincipalClass='NSApplication',NSAppTransportSecurity=dict(NSAllowsLocalNetworking=True),FaceMatchProjectPath=str(project))
    with (contents/'Info.plist').open('wb') as stream:plistlib.dump(info,stream)
    # Finder/iCloud metadata is not valid in a signed app resource. Clear only
    # these two attributes on our newly generated bundle, never quarantine flags.
    for attribute in ['com.apple.FinderInfo','com.apple.ResourceFork']:
        subprocess.run(['/usr/bin/xattr','-dr',attribute,str(output)],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,check=False)
    subprocess.run(['codesign','--force','--sign','-','--identifier','org.facematch.prototype',str(output)],check=True)
    subprocess.run(['codesign','--verify','--strict',str(output)],check=True)
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root',type=Path,default=ROOT)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--install',action='store_true',help='Install for this Mac user without replacing an existing app silently.')
    parser.add_argument('--desktop-shortcut',action='store_true',help='Add a Desktop shortcut if no file with that name exists.')
    parser.add_argument('--cache',type=Path,help='Optional reusable Swift module cache.')
    args=parser.parse_args();project=args.project_root.expanduser().resolve()
    stamp=datetime.now().strftime('%Y%m%d_%H%M%S')
    output=(args.output or project/'dist'/('mac_'+stamp)/'FaceMatch.app').expanduser().resolve()
    with tempfile.TemporaryDirectory(prefix='facematch-build-cache-') as folder:
        app=build(project,output,args.cache or Path(folder))
    print('Built:',app)
    if args.install:
        installed=Path.home()/'Applications/FaceMatch.app';installed.parent.mkdir(parents=True,exist_ok=True)
        if installed.exists():
            backup=installed.with_name('FaceMatch.previous-'+stamp+'.app')
            if backup.exists():raise SystemExit('Backup already exists; retry later.')
            installed.rename(backup);print('Previous app preserved:',backup)
        shutil.copytree(app,installed);app=installed;print('Installed:',app)
    if args.desktop_shortcut:
        desktop=Path.home()/'Desktop';shortcut=desktop/'FaceMatch.app'
        if desktop.is_dir() and not shortcut.exists() and not shortcut.is_symlink():
            shortcut.symlink_to(app,target_is_directory=True);print('Desktop shortcut:',shortcut)
        else:print('Desktop shortcut not changed: location missing or name already in use.')
    print('Open FaceMatch from Finder. No Terminal window is needed.')


if __name__=='__main__':main()
