# Consent, biometric data and appropriate use

This is a local academic prototype for comparing a face with enrolled records.
It must not be described as establishing criminal identity, guilt or a person's
legal identity, nor used to make consequential decisions about someone.

## Permission and provenance

Before processing, establish that the participant or authorized data provider has
permitted this educational use. Before presenting a photograph, separately confirm
permission to show it to the intended classroom audience. Recording, sharing and
publishing require their own permission. Participation should be voluntary, with
clear explanation of the purpose, limitations, storage and withdrawal process.

The project includes no signed consent forms, and their existence has not been
verified. Folder names and previous access to an image are not proof of consent.
The registration checkbox is an operator confirmation, not a complete consent
management system. Use institutional guidance and any approved forms rather than
treating this document as a legal approval or compliance assessment.

A private participant record should identify the data source, purpose, permission
date, allowed audience, retention period, withdrawal contact and whether recording
is allowed. Keep such records outside the code repository and submission archive.
Never invent a participant's permission or mark an unsigned form as completed.

## What is stored

- Enrollment: SQLite ID, name and reference-photo path; a private local photo copy.
- Query: a temporary local file during comparison, removed after the operation.
- Model: pretrained downloaded weights, not participant data trained by this project.
- Evaluation: local image files, per-image scores/manifests, and cached embeddings.
  Embeddings remain biometric data; they are not anonymous just because they are numbers.
- Submission: reviewed aggregate counts/metrics, source and documentation only.
  No personal photos, enrollment database, model weights or embeddings are included.

The app does not encrypt its database or photo folder. Use a protected user account,
appropriate device encryption/backups and access controls. Do not expose its local
server through a tunnel or on public interfaces. The app has no multi-user login,
audit/retention management or automatic participant-deletion interface.

## Retention and withdrawal

Agree a retention period before collecting new photos. The app does not expire
enrollments or evaluation caches automatically. A withdrawal requires the project
owner to deliberately review and remove the relevant record, reference, evaluation
copies, caches and any backups under their control. There is no automatic removal
claim. No original data was removed during project completion.

## Demonstration and submission

Use an isolated demo root and authorized photographs. Avoid displaying the private
production directory unnecessarily. The submission archive deliberately starts
with no personal enrollment data. Reproducibility for an instructor can use their
own consented local photographs or separately approved private access; do not add
private images to a public repository to make a demo convenient.

Research limitations include small reused data, imperfect labels, false matches,
false rejections, no liveness/anti-spoofing protection and no demographic fairness
study. Similarity scores are not confidence probabilities. A human review label
alone does not make an inappropriate high-stakes deployment acceptable.
