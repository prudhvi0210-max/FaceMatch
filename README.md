# FaceMatch

A university prototype that compares one face with enrolled records. Python,
SQLite, RetinaFace detection/alignment, DeepFace FaceNet512 embeddings, cosine
similarity, and a local browser interface. It does not establish criminal identity,
guilt, or a person's legal identity.

**Status:** implemented and tested as a local prototype. Submission materials use
provisional requirements because no course rubric, template, deadline, or required
file format was supplied. See [handover](docs/HANDOVER.md) and
[submission checklist](docs/SUBMISSION_CHECKLIST.md).

## Run on this MacBook Air

A verified environment is installed outside iCloud-synced Documents. The original
`.venv` and all existing records are preserved.

```bash
cd ~/Documents/FaceMatch
source ~/.venvs/facematch-university/bin/activate
python scripts/doctor.py
python app/ui.py
```

Open http://127.0.0.1:8765. Keep Terminal open; Control-C stops the app. Closing a
browser tab does not stop Python. You can also double-click **Start FaceMatch.command**.
The launcher prefers the environment above, then the old project `.venv`.
`FACEMATCH_PYTHON` can select another Python executable.

For the terminal menu:

```bash
python app/main.py
```

Choose registration, recognition, viewing records, or exit. `cancel`, `back`, or
`exit` at an input prompt returns to the menu. Menu option 4 or Control-C exits.

## Fresh installation

Verified using **CPython 3.11.18, macOS 26.6.2, Apple Silicon arm64**. The pinned
NumPy, ONNX Runtime and Pillow versions require Python >=3.11; 3.11 is the tested
project version. Intel Macs, other Python versions and other operating systems
have not been tested. Current arm64 NumPy/ONNX wheels used here require macOS 14+.

First install Python 3.11 from a trusted source if `python3.11 --version` is missing.
Then, from this project's folder (or the extracted submission's FaceMatch folder):

```bash
python3.11 -m venv ~/.venvs/facematch-university
source ~/.venvs/facematch-university/bin/activate
python -m pip install -r requirements-lock.txt
python -m pip check
python scripts/doctor.py
python -m unittest discover -s tests -v
python app/ui.py
```

Use a new environment name if that environment already contains unrelated work.
`requirements.txt` lists the directly pinned packages; `requirements-lock.txt`
contains the complete verified dependency set. `requirements-recognition.txt`
remains a compatibility entry point. Use **only one OpenCV distribution**:
`opencv-contrib-python-headless`. The UI needs no GUI OpenCV functions, TensorFlow,
Flask, Streamlit, JavaScript build tools, or additional web packages.

The clean install and dependency check succeeded. The live tests reused already
cached pretrained weights; an empty model-weight cache download has not been
verified in this pass. DeepFace/RetinaFace may download pretrained model files on
first use. Internet is needed for package installation and uncached weights.
Model files are normally under `~/.deepface/weights`; `DEEPFACE_HOME` changes their
parent home. No face photograph is sent to a cloud recognition API.

## Use the interface

- **Overview:** enrolled-record counts and reference issues.
- **Check a photo:** select/drop one JPG or PNG, up to 20 MB. See a possible match,
  unknown, ambiguous, or unavailable result with raw cosine similarity scores.
- **Register a person:** unique ID (80 characters max), name (160 max), one-face
  reference photo and permission confirmation. Duplicate IDs never overwrite.
- **People directory:** search name/ID; see missing and duplicate references.
- **About & validation:** decision rules, privacy and limitations.

Recognition uploads are temporary and removed after processing. Registration
validates detection and a finite 512-value embedding before saving a reference.
Failure to insert the record removes its newly copied reference. Existing records
are not automatically changed, merged or deleted. Missing/unreadable references
are skipped. No usable references is **unavailable**, distinct from **unknown**.

## Storage and isolated demonstrations

Default: `database/facematch.db` and `data/registered_faces/` relative to the project.
Paths are derived from the source location, not a developer's home directory.
Set `FACEMATCH_DATA_DIR` to another root to isolate records and stored photos:

```bash
export FACEMATCH_DATA_DIR="$PWD/outputs/demo-$(date +%Y%m%d-%H%M%S)"
python app/ui.py --port 8766
```

This starts an empty demo database without changing existing enrollment. After
stopping it, `unset FACEMATCH_DATA_DIR` returns to default storage.
See [the demonstration script](docs/DEMO.md) for exact steps and private input paths.

## Architecture and decision policy

```text
Browser / terminal -> image loading -> RetinaFace detection + alignment
  -> FaceNet512 embedding -> cosine comparison -> cautious decision
  -> SQLite records + private reference photographs
```

`app/settings.py` centralizes the fixed model, detector, normalization and **0.50**
cosine threshold. It is an experimental operating point, not a confidence score.
It was preserved and checked against 36 reference-only development pairs: 0.50
and 0.55 tied for the highest grid accuracy (0.05 increments). No threshold was
chosen using the registered/unknown evaluation photographs in this completion pass.
Historic development already reused these small datasets, so none is described as
independent validation. Scores below 0.50 are unknown; higher scores are only possible
matches. Shared duplicate references or a tied best score produce ambiguity.

`database.py` handles parameterized SQLite statements, migration and connection
cleanup; `photo_storage.py` handles private copies; `face_utils.py` handles image
loading/detection; `face_embedding.py` validates embeddings; `recognize_face.py`
handles similarity and decisions; `ui_service.py` connects UI operations; `ui.py`
serves local assets and JSON endpoints. The HTTP server binds only to 127.0.0.1,
checks host/origin/session tokens, limits uploads, and never serves arbitrary files.
It is not intended for public or multi-user deployment.

## Evaluation and actual results

Freshly reproduced: **9 references / 3 labelled enrolled people**, **10 registered
queries**, **4 unknown queries / 2 labelled unknown people**. No byte or decoded-pixel
overlap between those splits. Root-level aligned diagnostic crops are excluded
because only person-labelled subdirectories are loaded. Near duplicates and shared
capture sessions cannot be excluded by that audit. No model/detection failures
occurred in the full 46-embedding reproduction.

| Configuration | Registered correct | Wrong / rejected | Unknown rejected |
|---|---:|---:|---:|
| FaceNet512 baseline, 9 refs, 0.50 | 9/10 | 0 / 1 | 2/4 |
| FaceNet512 exploratory removal of person_03/photo2.jpg, 8 refs | 9/10 | 0 / 1 | 4/4 |
| ArcFace baseline, 9 refs, 0.35 | 7/10 | 3 / 0 | 2/4 |
| ArcFace exploratory removal of person_03/test4.jpg, 8 refs | 8/10 | 1 / 1 | 4/4 |

All 8 ablation summaries and 112 decisions match archived results. The candidate
improvement is exploratory and has **not** been applied to production references.
With only four unknown photographs, 4/4 is not a reliable population guarantee.
Application enrollment and evaluation-folder identities are separate: the existing
local database has five records, only three with photos, including duplicate references.
Do not equate a one-record UI demonstration with the nine-reference evaluation.

Reproduce safely; outputs get a new timestamped directory, not the old CSV paths:

```bash
python evaluation/reproduce.py --audit-only
python evaluation/reproduce.py
```

Supply `--data-root /path/to/private/evaluation` when using separately stored data.
`--validation` reads `validation_dataset/registered` and `validation_dataset/unknown`
and evaluates the fixed baseline only. Those folders are currently empty; the runner
stops rather than inventing results. The archive excludes all photographs, so a
recipient can run tests/UI immediately after setup but needs authorized local data
for real recognition/evaluation. Historical scripts are preserved for provenance;
use `reproduce.py` because some historical scripts overwrite their CSV outputs.

See [evaluation protocol](evaluation/README.md), [results](evaluation/results/summary.csv),
[academic report](docs/ACADEMIC_REPORT.md), and [verification](docs/VALIDATION.md).
Private caches contain biometric embeddings and remain under ignored `outputs/`.
They are not included in the submission.

## Verification

```bash
python -m unittest discover -s tests -v
python -m pip check
```

32 automated tests pass, covering migration/persistence, duplicate IDs, rollback,
invalid embeddings/images, unknown/ambiguous results, input cancellation, failed
model calls, split leakage, metric denominators, and local HTTP protections.
17 opt-in real-model checks also passed using a disposable database, including
registration, persistence across processes, a distinct known query, an unknown
query, a real blank PNG, a synthetic two-face input and a missing reference.

The repeatable live-check command processes private images only after explicit permission:

```bash
python scripts/live_smoke.py --data-root evaluation \
  --output outputs/my-new-live-check --authorized-test-data
```

That output directory must not already exist. Existing datasets/results are never
replaced. The script deletes only its own disposable enrollment and synthetic fixtures.
A natural group photograph, independent accuracy dataset, empty-cache model downloads,
and any webcam workflow are not claimed as verified. Webcam capture is not implemented
or required for the current upload-based scope.

## Submission materials and packaging

- [Concise academic report](docs/ACADEMIC_REPORT.md)
- [10-minute presentation with speaker notes](docs/PRESENTATION.md)
- [Demonstration script](docs/DEMO.md)
- [Consent and biometric handling](docs/ETHICS_AND_DATA.md)
- [Requirements/status matrix](docs/SUBMISSION_CHECKLIST.md)
- [Final handover](docs/HANDOVER.md)

Build a new private-data-free package:

```bash
python scripts/build_submission.py
```

The allowlisted folder/ZIP excludes environments, caches, secrets, original photos,
databases, model weights and private embedding caches. It includes source, tests,
documentation and verified aggregate results. A SHA-256 manifest and package check
are generated. Nothing is published, pushed or submitted automatically.

## Troubleshooting

- **Port in use:** stop the previous FaceMatch terminal with Control-C, or use
  `python app/ui.py --port 8766` and the printed URL.
- **Long startup in old .venv:** iCloud-only dependency files stalled imports during
  the audit. Use the verified environment outside Documents; keep source and
  model weights downloaded locally. No original environment files were removed.
- **Model processing fails:** run `doctor.py`, check internet/weight cache on first
  use and keep the printed terminal available. Missing weights are not an unknown face.
- **No face / multiple faces:** use a clear, well-lit single-face photograph.
- **Unreadable image:** convert/export a genuine JPG/PNG; renaming a file is insufficient.
- **Ambiguous:** review duplicate references in the directory. No automatic deletion.
- **Request denied after restart:** refresh the browser to obtain the new session token.
- **No known match in a fresh package:** the submission intentionally contains no
  personal enrollment data. Register an authorized reference first.
