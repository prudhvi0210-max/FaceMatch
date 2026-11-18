# FaceMatch for Windows — build candidate

**Status:** Windows app source, freezer specification, installer and manual build
workflow are implemented. The source/support tests run on the development Mac.
A Windows executable, installer compilation, interactive Windows GUI and actual
Windows model inference have **not** been verified yet. Do not describe the source
as an already tested downloadable Windows release.

## Intended experience for friends

After a successful Windows build and interactive QA:

1. Download `FaceMatch-Setup-Windows-x64.exe` from a release/download you provide.
2. Run Setup. If the Microsoft Visual C++ x64 runtime is missing, Setup offers to
   open Microsoft's official instructions; install it and rerun Setup. WebView2
   is installed by its Microsoft bootstrapper when missing, requiring internet.
3. Optionally select “Create a Desktop shortcut.”
4. Open **FaceMatch** from the Start menu or shortcut. No Python, Terminal commands,
   project folder or separate browser address is needed.
5. Register their own consented reference photographs and compare images visually.

Initial target: **Windows 11 x64 on Intel/AMD PCs**. Windows ARM, 32-bit Windows and
Windows 10 are not supported claims. The installer enforces Windows 11 minimum.
The app uses CPU inference; it does not require CUDA or an NVIDIA GPU.

Each user starts with an empty directory. No photos, your database, embeddings or
model weights are shipped. Uncached pretrained weights download on first recognition;
a loading message is shown and the first operation can take longer. Internet access
is required until the model cache is ready. Review the model terms before distribution.

## Privacy and local storage

Records, copied references, model cache and a bounded desktop diagnostic log live
under `%LOCALAPPDATA%\FaceMatch` by default. Optional `FACEMATCH_DATA_DIR` and
`DEEPFACE_HOME` overrides are retained. Mutable data never belongs in the installed
program folder or frozen resource directory. Query uploads are temporary; references
remain until deliberately removed by the owner. All other consent/privacy notes in
ETHICS_AND_DATA.md apply. Reinstall/uninstall does not deliberately erase user data.

The window loads only the shared loopback API. The existing host/origin/token checks
remain in use. Private browser mode is enabled. Closing during a comparison asks
whether to interrupt it. The native Mac shell, thresholds and reference set are unchanged. A shared image
loader now decodes Unicode-path images as BGR arrays, avoiding DeepFace’s ASCII-only
filename restriction; ASCII paths retain the previous loading behavior. Shared UI text now says “this computer” rather than incorrectly labelling
a Windows PC as a Mac.

## Build without owning a Windows PC

The repository includes `.github/workflows/windows-build.yml`, triggered **manually
only**. It has read-only repository permissions and does not publish a Release.
It must first be committed/pushed with your authorization. Then use GitHub → Actions
→ Build FaceMatch for Windows → Run workflow. GitHub Actions usage/storage may count
against the repository's allowances.

The Windows job:

- Sets up x64 CPython 3.11 and installs the pinned runtime/build packages.
- Runs the application/support regression tests.
- Freezes the executable and UI assets using PyInstaller, without private data.
- Runs a frozen backend smoke check and cold-loads FaceNet512/RetinaFace models into
  disposable storage. This requires downloading pretrained weights.
- Compiles Setup using Inno Setup, checks silent installation, and verifies that
  uninstall preserves a disposable user-data marker.
- Uploads only the candidate installer, portable ZIP, checksums and check reports
  as a development artifact retained for 14 days.

It does not upload local photographs, local model caches, enrollment records or
secrets. An instructor/friend needs an explicitly shared download after QA; merely
committing this workflow does not create an installer or public release.

## Build on a Windows development PC

Developer instructions (friends using the installer do not run these commands):

```powershell
py -3.11 -m venv .venv-windows
.\.venv-windows\Scripts\Activate.ps1
python -m pip install -r desktop/windows/requirements-build.txt
python -m pip check
python -B -m unittest discover -s tests -v
python scripts/build_windows_app.py --load-models
```

Use x64 Python 3.11 and Inno Setup 6. The Microsoft Visual C++ x64 runtime must be
installed on the build machine. The build refuses macOS cross-compilation and refuses
to overwrite an existing output directory. Artifacts go under ignored `dist/`.
`--portable-only` builds the ZIP without compiling Setup. A portable user must keep
the entire extracted folder together and already have the Microsoft prerequisites.

No FaceMatch code-signing certificate is configured: outputs are unsigned development
builds, not SmartScreen-reputation-tested public releases. Production signing and
review of third-party redistribution terms remain release-owner tasks. The WebView2
bootstrapper's Microsoft signature is checked on Windows before installer compilation.
The Visual C++ redistributable is not rehosted in this package; users obtain it from
Microsoft if needed.

## Required Windows verification before sharing widely

The headless CI test checks packaged imports, local assets/API, fresh enrollment
storage, private-route blocking and optional model loading. It does not exercise the
native window, file picker, consent form, close confirmation or actual recognition
against photographs. On an actual Windows 11 PC, check:

- Clean install, Start menu/Desktop launch and no console window.
- Empty directory, single-face enrollment and persistence after reopening.
- Distinct known/unknown images, blank/corrupt images and multiple-face rejection.
- File-picker selection/preview, directory search and close-during-processing warning.
- First-run downloads, restricted/offline network failures and Windows paths with spaces.
- Reinstall/uninstall preserves only intended user data; user can find it for deliberate removal.

Use consented local data only. Do not reuse a Mac screenshot as evidence of Windows QA.
Until a Windows build and those interactive checks run, this remains a build candidate.

## Sources

- [PyInstaller cross-platform build requirements](https://pyinstaller.org/en/stable/operating-mode.html)
- [pywebview Windows requirements](https://pywebview.flowrl.com/guide/installation.html)
- [Microsoft WebView2 deployment](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution)
- [ONNX Runtime Windows prerequisites](https://onnxruntime.ai/docs/install/)
- [Microsoft Visual C++ runtime](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)

## Local verification on 18 November 2026

- All 43 application/support regression checks pass on the Mac, including isolated
  storage, service shutdown, private-file rejection in bundle scanning and Unicode
  image loading. This is not a Windows GUI test.
- A real FaceNet512/RetinaFace check produced matching embeddings and face regions
  for identical image bytes stored under ASCII and Unicode filenames on the Mac.
- Published wheels compatible with Windows x64 / Python 3.11 were found for all
  26 pinned core/build package versions. This checks availability, not a complete
  Windows dependency installation; platform-specific transitive dependencies still
  need the native Windows build.
- Python, freezer-specification and shared JavaScript syntax checks pass locally.
- No Windows `.exe` or Setup installer has been generated or tested yet. No remote
  workflow, code push, public release or Windows screenshot is claimed.
