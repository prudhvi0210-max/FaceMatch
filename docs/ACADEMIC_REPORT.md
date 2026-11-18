# FaceMatch: a local face-comparison prototype

**Prepared against provisional requirements.** No assignment rubric, required
report template, course identifier or submission format was supplied. Student name,
course, instructor, student number and any required declaration must be completed
by the student before submission. Prepared 14 November 2026.

## Abstract

FaceMatch compares a photograph with locally enrolled reference records. The
application uses RetinaFace for detection and alignment, FaceNet512 embeddings,
cosine similarity and SQLite storage. It provides a browser interface and a
terminal menu. A fresh experiment reproduced all eight archived ablation summaries
and all 112 recorded decisions. With nine references, FaceNet512 correctly
identified 9 of 10 registered queries but rejected only 2 of 4 unknown queries.
Removing one reference during an exploratory experiment improved unknown rejection
to 4 of 4. This candidate was not independently validated and was not applied to
the application. The result is a functional academic prototype, not evidence that
faces establish criminal identity or guilt.

## 1. Problem and objective

A simple highest-score search always finds a closest record, even when the person
is not enrolled. The project therefore needs an unknown result, readable failure
messages and a clear account of uncertainty. The objective is to implement and
evaluate a small local workflow: enroll a consenting participant, load one face,
compare it with enrolled references, and show a possible match or a cautious
alternative. Public deployment, criminal identification, guilt assessment, live
surveillance and webcam capture are outside the implemented scope.

## 2. Approach

Face embeddings represent photographs numerically so that similar faces can be
compared. FaceNet introduced an embedding approach for verification, recognition
and clustering [1]. This project uses DeepFace's FaceNet512 implementation rather
than training a network. RetinaFace supplies face detection and landmarks used in
alignment [2]. ArcFace is included as a comparative embedding model [3]. DeepFace
provides the inference interface [4]. The original papers' benchmark results are
not FaceMatch results and are not copied into this report as project accuracy.

The image must contain exactly one detected face. Detection remains enforced.
DeepFace handles cropping/alignment; base normalization is explicit. The application
checks that the embedding contains 512 finite values and is nonzero. Similarity is

```text
cosine(a,b) = dot(a,b) / (norm(a) * norm(b))
```

The maximum usable score is compared with the fixed experimental threshold 0.50.
Below threshold, the result is unknown. At or above it, the result is only a
possible match. Duplicate reference photographs assigned to different IDs, or tied
best scores, make the identity ambiguous. Unavailable comparisons are reported
separately from unknown people. Scores are not probabilities.

## 3. Implementation

Python modules separate storage, database operations, detection, embeddings and
comparison. SQLite stores ID, name and reference path; photographs are kept in a
private folder. Parameterized SQL is used. Duplicate IDs do not overwrite records.
Connections commit or roll back and close after each operation. Older databases
without a photo-path column are migrated without removing records. A failed copy
or database insertion cleans up only the newly created reference.

The browser has overview, photo comparison, enrollment, directory search and
explanation pages. JPG/PNG uploads are limited to 20 MB. Query files are temporary;
only explicit registration saves a reference. The local HTTP server binds to
127.0.0.1 and checks the host, origin and a per-server token. It serves only explicit
assets, not project directories. The original terminal menu remains usable.
`FACEMATCH_DATA_DIR` isolates demonstration records from the existing database.

The audit found five existing database records, three with photographs; two IDs
share one exact reference. These records were preserved. They are not the same
experimental enrollment as the nine-reference evaluation folder. The code flags
this ambiguity instead of choosing one ID arbitrarily.

## 4. Experimental method

Available labelled data comprise nine references for three enrolled labels, ten
registered-person queries for those labels, and four unknown queries for two other
labels. Each enrolled label has three references; query counts are 4, 2 and 4.
There are six normal and four sunglasses registered queries, and three normal and
one sunglasses unknown queries. The directory labels are supplied ground truth,
not independently verified real-world identities.

Only images directly in labelled person directories are used. Five aligned
root-level diagnostic crops are excluded. Exact byte and decoded-pixel checks found
no overlap between reference, registered-query and unknown-query splits. This does
not rule out near duplicates or photographs from the same session. Independent
validation folders contain no photographs.

FaceNet512 uses 0.50 and ArcFace 0.35, frozen before this reproduction. A reference-only
development sweep used 36 unique pairs (9 genuine and 27 impostor) and thresholds
0.00–1.00 in 0.05 increments. FaceNet512 0.50 and 0.55 tied for maximum pair accuracy;
ArcFace 0.35 was the maximum. This supports retaining the pre-existing operating
points for a reproducible experiment. It does not establish calibrated production
thresholds, and the small development set has already been explored historically.

Identification selects the highest score per identity over its active references.
Four configurations are evaluated without editing images: baseline, omit
`person_03/photo2.jpg`, omit `person_03/test4.jpg`, and omit both. Registered
accuracy counts correct identity decisions over all ten registered queries.
Unknown rejection counts correct unknown decisions over all four unknown queries.
Wrong identity, rejection, ambiguity and processing failure are separate outcomes.
The new runner retains failed queries in those denominators and saves new outputs;
none of the original CSVs are overwritten. There were no inference failures in
this reproduction: 46 embeddings were generated across 23 images and two models.

## 5. Reproduced results

| Model / temporary reference configuration | References | Registered correct | Wrong | Rejected | Unknown rejected |
|---|---:|---:|---:|---:|---:|
| FaceNet512 baseline | 9 | 9/10 | 0 | 1 | 2/4 |
| FaceNet512 omit photo2 | 8 | 9/10 | 0 | 1 | 4/4 |
| FaceNet512 omit test4 | 8 | 9/10 | 0 | 1 | 2/4 |
| FaceNet512 omit both | 7 | 9/10 | 0 | 1 | 4/4 |
| ArcFace baseline | 9 | 7/10 | 3 | 0 | 2/4 |
| ArcFace omit photo2 | 8 | 7/10 | 3 | 0 | 2/4 |
| ArcFace omit test4 | 8 | 8/10 | 1 | 1 | 4/4 |
| ArcFace omit both | 7 | 8/10 | 1 | 1 | 4/4 |

All eight aggregate rows and 112 decisions agree with the archived experiment.
The largest difference from rounded archived similarity values is below 0.00005.
No reference is permanently removed. Candidate selection used the same query
photographs, so candidate gains are exploratory, not independently measured gains.

Pair verification on the 90 registered-query/reference comparisons gives:

| Model | TP / TN / FP / FN | Accuracy | Precision | Recall | F1 | FMR | FNMR |
|---|---|---:|---:|---:|---:|---:|---:|
| FaceNet512, 0.50 | 23 / 57 / 3 / 7 | 88.89% | 88.46% | 76.67% | 0.8214 | 5.00% | 23.33% |
| ArcFace, 0.35 | 19 / 55 / 5 / 11 | 82.22% | 79.17% | 63.33% | 0.7037 | 8.33% | 36.67% |

Here, genuine pairs are positives. Precision is TP/(TP+FP), recall is TP/(TP+FN),
FMR is FP/(FP+TN), and FNMR is FN/(FN+TP). Pair verification and identification are
different tasks. These pairs share images and do not constitute 90 independent
people or independent trials. The results cannot establish demographic fairness
or performance in a larger population.

## 6. Verification

A clean Python 3.11 environment installed successfully with the pinned dependencies
and passed `pip check`. Thirty-two automated regression checks cover application,
database, HTTP and evaluation behavior. Seventeen live checks used actual model
calls and disposable enrollment: registration, persistence in a second process,
duplicate ID rejection without replacement, valid embeddings/crops, known-person
comparison, unknown rejection, unreadable/missing files, a blank image, synthetic
two-face rejection and missing-reference behavior. Production records and input
photos were not changed. The synthetic two-face fixture is not a natural group-photo
accuracy study. Further verification details and exact commands are in VALIDATION.md.

## 7. Consent, limitations and future work

### Privacy statement

FaceMatch is designed to protect participants’ privacy through local image
processing and restricted use for the stated academic purpose. Photographs should
be processed only with informed consent; permission to display or share a face
must be obtained separately. Personal photos, enrollment databases and face
embeddings are excluded from the public repository and submission package.
Temporary query-upload copies are removed after processing, while the user’s
original files are unchanged. Enrolled references remain locally stored until the
project owner deliberately removes them. These safeguards reduce privacy risks;
they do not guarantee that privacy can never be affected. The full policy is in
[ETHICS_AND_DATA.md](ETHICS_AND_DATA.md).

### Consent evidence, limitations and future work

Faces and embeddings are biometric data. The submission excludes personal photos,
local enrollment databases and embedding caches. Processing permission and any
required institutional approvals must be confirmed before showing a participant's
face during a demonstration. No signed consent records were supplied or verified.
The UI checkbox records an operator's confirmation for that action; it is not a
complete participant-consent record or a legal compliance assessment.

The data are very small, repeatedly inspected and lack independently collected
validation images. Four unknown queries are especially insufficient for broad
claims: 4/4 after reference selection is not a guarantee. Natural group-photo
behavior, empty-cache weight downloads, Intel hardware and other Python versions
were not verified in this pass. There is no liveness detection, anti-spoofing,
access-control system for public hosting, or demographic-bias study. Local storage
is not encrypted by the application; computer access controls remain important.

Future work should first collect genuinely new consented validation photographs,
freeze the threshold and references, and report false identifications, false
rejections and detection failures with denominators. Additional work could study
lighting and occlusion, improve enrollment quality checks and add a controlled
reference-review workflow. No deployment decision should rely on these exploratory
numbers alone.

## Conclusion

FaceMatch implements a complete local upload-based enrollment and comparison
workflow with cautious decisions and reproducible exploratory evaluation. The
functional prototype is ready for a controlled demonstration. Final university
submission depends on reviewing the missing course-specific requirements and
completing the student's required declarations; accuracy validation remains a
separate, honestly stated research limitation.

## References

1. Schroff, F., Kalenichenko, D., and Philbin, J. (2015). *FaceNet: A Unified Embedding
   for Face Recognition and Clustering*. https://arxiv.org/abs/1503.03832
2. Deng, J. et al. (2019). *RetinaFace: Single-stage Dense Face Localisation in the Wild*.
   https://arxiv.org/abs/1905.00641
3. Deng, J. et al. *ArcFace: Additive Angular Margin Loss for Deep Face Recognition*.
   https://arxiv.org/abs/1801.07698
4. Serengil, S. I. and DeepFace contributors. *DeepFace*, version 0.0.104.
   https://github.com/serengil/deepface and https://pypi.org/project/deepface/0.0.104/
