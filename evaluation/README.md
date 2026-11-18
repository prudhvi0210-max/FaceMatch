# Evaluation protocol

Use `reproduce.py` as the supported non-destructive workflow. Historical scripts and
CSV files in the working project are preserved, but may overwrite their own outputs.

## Private folder structure

```text
evaluation/
  dataset/person_01/ ... person_03/          # 9 reference images total
  test_dataset/person_01/ ... person_03/     # 10 distinct registered queries
  unknown_dataset/unknown_01/ unknown_02/   # 4 unknown queries
  validation_dataset/registered/person_*/  # currently empty
  validation_dataset/unknown/unknown_*/    # currently empty
```

Only images directly inside person-labelled directories are included. Aligned
root-level diagnostic crops are excluded. JPG/JPEG/PNG extensions are supported.
Folder names supply ground-truth labels; they are user labels, not independently
verified identities. Reference and registered-query identity labels intentionally
overlap; their image contents must not. Unknown labels must not be enrolled labels.

## Commands

```bash
python evaluation/reproduce.py --audit-only
python evaluation/reproduce.py
python evaluation/reproduce.py --models Facenet512
python evaluation/reproduce.py --validation
```

`--data-root` chooses a private folder following the structure above. `--output`
chooses a **new**, nonexistent output directory. Default outputs are timestamped
under ignored `outputs/`. An empty or invalid split stops model evaluation. Byte
hash and decoded-pixel overlap across splits also stops it. No files are removed.

For a new validation set, keep references and thresholds fixed, collect new
consented images, and do not tune on those images after viewing results. The
`--validation` mode runs only baseline and does not do a threshold sweep. Evidence
of truly independent acquisition still needs to be recorded by the student.

## Inference and metrics

Both models use RetinaFace, enforced detection, alignment, base normalization,
and finite/nonzero 512-value embeddings. Fixed thresholds: FaceNet512 0.50;
ArcFace 0.35. Identification uses the maximum reference similarity per identity.
Queries below threshold are unknown. Cross-identity duplicate references or tied
best scores produce ambiguity. Per-image failures are recorded, not silently
removed from registered/unknown query denominators. Pair metrics are conditional
on successfully encoded images; consult failure counts if any image fails.

Registered accuracy = correctly identified registered queries / all registered
queries. Unknown rejection rate = correctly rejected unknown queries / all unknown
queries. Wrong identity, false rejection, ambiguous result and processing failure
are counted separately. Unknown false identification rate is false identifications
/ unknown queries. Pair verification uses TP/TN/FP/FN, precision, recall, F1,
FMR = FP/(FP+TN) and FNMR = FN/(FN+TP). Pair comparisons share images and are not
independent statistical samples.

The development threshold sweep evaluates 0.00 to 1.00 in 0.05 increments on
reference-only pairs. On the available 36 pairs, FaceNet512 0.50 and 0.55 tie for
maximum accuracy; ArcFace 0.35 is the maximum. This supports retaining the existing
experimental thresholds, but is not independent calibration. Validation mode
omits this sweep entirely to preserve its fixed-baseline role.

Ablations temporarily omit person_03/photo2.jpg, person_03/test4.jpg, or both from
comparisons. They never delete or alter references. Missing ablation filenames
stop the run rather than silently changing the experiment. The candidate was
investigated using the same small query sets, so its performance is exploratory.

## Outputs and privacy

A private run contains audit, environment, input-content manifest, per-query
results, aggregate/pair metrics, development sweep, failures, and a shared private
embedding cache outside the run directory. Cache keys include image hash, model,
DeepFace version and preprocessing settings. No embeddings are submission data.
Current cached weight hashes are recorded in results/model_weights.json without
redistributing the weights. Historical experiments did not record their weight
hashes, limiting bit-for-bit comparison to those historical cache files.

`evaluation/results/` contains a reviewed snapshot of aggregate reproduction and
verification evidence only. It is safe for the prepared submission scope: no
photographs, enrollment database, face embeddings or personal names are included.
An authorized reviewer needs their own data or private access granted by the
student to repeat the full real-image experiment. Tests use synthetic fixtures.
