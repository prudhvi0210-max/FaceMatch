# Verification record — 14 November 2026

This record distinguishes implementation, functional verification and research
validation. No claim of course-rubric compliance or independent accuracy validation
is made. The course rubric and formal submission requirements were not available.

## Automated tests

The clean CPython 3.11 environment passes **32 regression tests**:

- Database creation, old-schema migration, persistence, duplicate IDs, no overwrite,
  invalid fields and connection cleanup.
- Newly copied-photo cleanup on insertion failure and partial-copy failure.
- Missing/unreadable input, detector-runtime failure versus no face, cancellation,
  no/multiple-face control flow, menu recovery and empty-gallery behavior.
- Finite/nonzero/compatible vectors, 512-value model contract, threshold boundary,
  unknown/unavailable/ambiguous decisions and unsorted-score handling.
- UI upload limits/content, permission requirement, success/rollback, missing and
  duplicate reference status, closed-browser response, explicit static routes,
  host/origin/token checks, operation lock and HTTP failure recovery.
- Evaluation confusion counts, failed-query denominators, duplicate/tie handling,
  image split leakage and canonical independent-validation split keys.

Run `python -m unittest discover -s tests -v`. These tests use temporary databases
and fixtures, with model calls stubbed where appropriate. They are not accuracy tests.

## Real-model workflow checks

`evaluation/results/live_smoke.json` records **17 passed checks**. Existing private
reference/query photographs were processed locally. Enrollment used a disposable
root; no production enrollment record or original photo was changed.

Verified: fresh/empty database; missing path; unreadable image; blank-image rejection;
empty-gallery unavailable result; permission confirmation required; real registration;
persistence read in a second Python process; duplicate ID rejection and no overwrite;
512 finite embedding values; a returned face crop with enforced detection/alignment;
a distinct registered query (possible match approximately 0.6407495); an unknown
query (unknown, approximately 0.1747049 with the single test reference); a synthetic
two-face fixture rejected with the specific multiple-face message; a missing reference
flagged in the directory; and unavailable comparison after that disposable reference
was deliberately removed.

The live-check script initially stopped at its own temporary-path safety assertion
because macOS exposes equivalent /var and /private/var paths. The comparison was
corrected to resolve both paths, and the entire live run was repeated successfully.
The failed run remains privately preserved under outputs; only the successful run
is included as submission evidence. This was a test-harness correction, not a
change to the recognition threshold or model.

## Full experiment reproduction

New files were written under `outputs/submission_reproduction_20261114/` in the
working project. Nine references, ten registered queries and four unknown queries
were audited. Cross-split byte and decoded-pixel overlap: none. Five diagnostic
aligned crops at the dataset root were not treated as labelled references.

Both models generated all 23 embeddings successfully (46 total; zero inference
failures). Eight aggregate ablation rows and 112 decisions match the archived
combined experiment. Maximum score difference versus the rounded archive is below
0.00005. Baseline FaceNet512: 9/10 registered correct, 0 wrong, 1 rejected, 2/4
unknown rejected. The exploratory photo2-removal candidate: 9/10 and 4/4. The latter
is not independent validation and is not applied to the app.

The 36-pair reference-only sweep supports retaining 0.50 (tied with 0.55) for
FaceNet512 and 0.35 for ArcFace. No threshold was changed. Fixed-baseline validation
mode detects reused exploratory images when those prior datasets are available
and refuses empty splits. The independent validation folders are currently empty.

## Setup and interface

Fresh CPython 3.11.18 installation with `requirements.txt` succeeded in a temporary
environment, and a second installation from `requirements-lock.txt` succeeded in
`~/.venvs/facematch-university`. `pip check` reports no broken requirements. The
old project environment was preserved; it contains overlapping OpenCV distributions
and iCloud-offloaded files, so it is not the recommended demo runtime.

The prior browser verification exercised responsive overview, photo preview/result
rendering, directory search and reference statuses, and the registration form.
The HTTP/service regression tests are repeatable. JavaScript syntax, launcher syntax,
application Python syntax, CLI list/exit and final installed-project checks are
recorded in the handover evidence after final packaging verification.

Live inference reused existing FaceNet512, ArcFace and RetinaFace weight caches.
A brand-new empty-cache weight download was not verified. The package omits weights.

## Still unverified / not in scope

- Independently acquired accuracy dataset, population reliability and demographic fairness.
- A natural group-photo detector test (synthetic two-face rejection was verified).
- Signed participant-consent records and permission for classroom recording/display.
- Intel Macs, other OS/Python combinations and a fresh empty-cache model download.
- Webcam capture, liveness/anti-spoofing and public/multi-user deployment are not implemented.
- Formal rubric, template, author details, university declaration and permitted AI-use
  requirements must be checked by the student; none was supplied.
