# FaceMatch: 10-minute presentation outline and speaker notes

Prepared against provisional requirements. This is a presentation outline, not a
claim that a particular university slide template or assessment rubric was met.
Use the results in `evaluation/results/`; do not replace them with library benchmarks.

## 1. Problem and question — 0:00–0:45 (45 seconds)

On screen: “Can we compare a single face with enrolled records while showing uncertainty?”

Speaker notes: “A nearest-score system always finds something, even if the person
is not enrolled. My goal was to build a small, understandable prototype that can
also say unknown, ambiguous, or unavailable. It does not establish criminal identity
or guilt.”

## 2. Scope and user workflow — 0:45–1:30 (45 seconds)

On screen: enroll → select photo → compare → review result.

Speaker notes: “The application runs locally on my Mac. I implemented enrollment,
a searchable directory, photo comparison and a retained terminal menu. The browser
requires one JPG or PNG with one detected face. This is an upload-based prototype,
not a surveillance or webcam system.”

## 3. Architecture — 1:30–2:30 (60 seconds)

On screen: browser/terminal → service → RetinaFace → FaceNet512 → cosine score;
SQLite and private photo storage below the service.

Speaker notes: “RetinaFace detects and aligns the face. DeepFace returns a 512-value
FaceNet embedding. I validate finite values and vector size before comparing.
SQLite stores IDs, names and reference paths, while photographs stay in private
local storage. The interface and terminal reuse the same recognition logic.”

## 4. Safe decisions and enrollment — 2:30–3:30 (60 seconds)

On screen: possible match / unknown / ambiguous / unavailable; threshold 0.50.

Speaker notes: “Scores below 0.50 are unknown. Higher scores are possible matches,
not probabilities. Shared duplicate references or tied best scores are ambiguous.
Missing references can make comparison unavailable. Duplicate IDs cannot overwrite
existing people. Registration validates the actual model before saving a record,
and a failed insertion cleans up its new photo.”

## 5. Evaluation design and threshold — 3:30–4:45 (75 seconds)

On screen: 9 references, 10 registered queries, 4 unknown queries; 3 enrolled labels,
2 unknown labels; no exact cross-split image overlap.

Speaker notes: “The reference images and query images have separate files. I checked
byte hashes and decoded pixels, but cannot exclude near duplicates or common
capture sessions. A reference-only threshold sweep supported keeping 0.50 for
FaceNet512 and 0.35 for ArcFace. No threshold was changed during reproduction.
These data have already been explored, and independent validation folders are empty.”

## 6. Baseline results — 4:45–5:45 (60 seconds)

On screen:

| Model | Registered correct | Unknown rejected |
|---|---:|---:|
| FaceNet512 | 9/10 | 2/4 |
| ArcFace | 7/10 | 2/4 |

Speaker notes: “FaceNet512 identified more registered queries in this small dataset.
However, baseline unknown rejection was only two out of four. I distinguish this
from the one-record UI demonstration. Pair verification is also different from
identification; I report its separate confusion counts in the written report.
Thirty-two regression tests and seventeen real-model workflow checks passed.”

## 7. Reference ablation — 5:45–6:30 (45 seconds)

On screen: FaceNet512 baseline 9 refs: 9/10 and 2/4; omit photo2: 8 refs: 9/10 and 4/4.

Speaker notes: “Removing one reference temporarily changed unknown rejection to four
out of four. This is an exploratory candidate because the same queries helped us
investigate it. I reproduced all eight ablation summaries and 112 decisions. I did
not permanently delete a reference or present the candidate as independent validation.”

## 8. Controlled live demonstration — 6:30–8:30 (120 seconds)

On screen: local UI using an isolated demonstration database. Follow DEMO.md.

Speaker notes and actions: “This database is separate from my existing records.”
Enroll the authorized demo participant, check a different photograph for a possible
match, then check the selected unknown photograph. Show a blank-image error and
browse the persisted directory record. Explain that the demo uses a subset of
references and is a functional example, not a new accuracy experiment. If the
model is unavailable, show the checked result files and label the demo as a fallback,
rather than pretending to have run inference.

## 9. Consent and data handling — 8:30–9:15 (45 seconds)

On screen: local processing, permission, temporary query, excluded private data.

Speaker notes: “Photos and embeddings are biometric data. Query uploads are removed
after processing; enrolled references remain local until deliberately managed by
the operator. The archive contains no personal photos, databases or embeddings.
Permission must be confirmed before showing a person's face, and a checkbox alone
is not a full consent record.”

## 10. Limitations and next step — 9:15–10:00 (45 seconds)

On screen: small exploratory data → new fixed-protocol validation.

Speaker notes: “The prototype works, but the dataset is small and reused. Four unknown
images cannot establish general reliability. The next step is genuinely new
consented validation with fixed references and threshold. Natural group photographs,
liveness, demographic fairness and public deployment require further work. My
contribution is a working local application, cautious decisions and reproducible,
honestly limited experiments.”

## Likely questions

- **Why 0.50?** It preserves the established experimental baseline and is among the
  best values in a reference-only development sweep; it is not a calibrated universal threshold.
- **Why not automatically delete the poor reference?** Selection was based on the
  same queries; removal requires independent validation and a deliberate data decision.
- **Does 4/4 mean 100% accurate?** Only on those four exploratory unknown images.
- **Did you train FaceNet?** No. The project integrates pretrained models and evaluates the workflow.
- **Where are the photos in the archive?** Deliberately excluded; an authorized demo uses local private data.
