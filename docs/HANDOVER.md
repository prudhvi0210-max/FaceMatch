# Final handover — FaceMatch university prototype

Prepared 14 November 2026 against provisional requirements. Read this with
SUBMISSION_CHECKLIST.md before deciding whether to submit.

## What is implemented

The browser and terminal connect enrollment, single-face detection/alignment,
FaceNet512 embeddings, cautious comparison, the enrolled directory and exit.
Additional fixes include closed database connections, old-schema migration,
no-overwrite duplicate IDs, partial-copy rollback, configurable private storage,
portable relative-reference handling and separate image/model failure outcomes.
The threshold remains 0.50; existing references and production records are preserved.

`evaluation/reproduce.py` supersedes the destructive-output behavior of historical
scripts. It audits splits, caches embeddings privately, records failures, retains
query denominators and runs both model baselines plus all existing reference
ablations into new output directories. Validation mode uses fixed baseline only,
canonical split keys, and checks for reused development images when available.

A verified runtime is installed outside iCloud in `~/.venvs/facematch-university`.
The old `.venv` remains untouched. Both a direct-pinned dependency file and a full
lockfile are included; neither requires overlapping OpenCV distributions.

## Verified evidence

- 32 automated tests pass in the clean runtime.
- 17 live model/workflow checks pass in disposable enrollment, including persistence
  in a separate process and rejection of a synthetic two-face image.
- All 46 embeddings in the two-model reproduction succeeded.
- All eight archived ablation summaries and 112 decisions were reproduced.
- Baseline FaceNet512: registered correct 9/10; unknown rejected 2/4. Exploratory
  reference removal: 9/10 and 4/4; not applied or independently validated.
- No exact byte/decoded-pixel leakage found across the available three splits.
- Clean installs from direct pins and the full lockfile succeeded; pip check passes.
- Portable syntax, CLI list/exit, empty-validation refusal and package checks are
  verified during final handover. Package extraction includes no personal enrollment.

The machine is Apple Silicon, macOS 26.6.2, CPython 3.11.18. Existing pretrained
weights were reused. Model-cache hashes are recorded without shipping weights.

## Deliverables

- `README.md`: setup, usage, architecture, results and troubleshooting.
- `docs/ACADEMIC_REPORT.md`: concise report with verified results and primary sources.
- `docs/PRESENTATION.md`: timed 10-minute outline and speaker notes.
- `docs/DEMO.md`: isolated demonstration, exact commands and expected observed examples.
- `docs/ETHICS_AND_DATA.md`: consent, retention, biometric storage and appropriate use.
- `docs/VALIDATION.md`: precise verification evidence and unverified cases.
- `docs/SUBMISSION_CHECKLIST.md`: provisional requirements and readiness matrix.
- `evaluation/results/`: reviewed aggregate evidence, successful live-check record,
  audit, environment and current model-cache hashes. No face embeddings.
- `scripts/build_submission.py`: allowlisted packaging with SHA-256 manifest and ZIP check.
- Working-project package: `submission/FaceMatch_University_20261114/FaceMatch.zip`
  with an extracted `FaceMatch/` beside it and `PACKAGE_CHECK.json`.
- Private detailed reproduction/cache/live logs remain under ignored `outputs/`.
  Completion backups are there too; they are not part of the submission.

## Exact launch commands

```bash
cd ~/Documents/FaceMatch
source ~/.venvs/facematch-university/bin/activate
python scripts/doctor.py
python app/ui.py
```

Open http://127.0.0.1:8765. Control-C in Terminal stops the server. An already-running
instance can be used as printed, or run a second one with `--port 8766`. The Mac
launcher also chooses the verified runtime. No public service is deployed.

## What is not claimed ready

The local application is implemented and verified for controlled demonstration.
The archive is prepared for review under provisional requirements. **Unconditional
university submission readiness is not claimed:** the actual rubric, required
file formats and student/course declarations were not supplied. Actual consent
records were not inspected. The student must confirm permission before showing faces.

Independent accuracy folders are empty. Results remain exploratory; natural group
photographs, empty-cache weight downloads, Intel/other OS support and population
fairness are not verified. Webcam capture, anti-spoofing and public multi-user
hosting are outside this prototype. No remote push, publication or university
submission was performed.
