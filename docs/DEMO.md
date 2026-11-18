# Controlled FaceMatch demonstration

Prepared against provisional requirements. Two minutes are allocated to the live
application in the 10-minute outline. Rehearse and prepare before that interval.
Never display a person's photograph without permission for classroom display.
The archive intentionally has no private photos; this script's photo paths apply
to the existing private working project on the student's Mac.

## Before class

1. Confirm permission for local biometric processing and showing the chosen face.
   A processing permission does not automatically permit recording or publishing it.
2. Use the verified Python 3.11 environment outside iCloud. Keep source and model
   weights downloaded locally. Run `doctor.py` and tests before the presentation.
3. Stop any previous demo server. Use the new timestamped data root below; do not
   use the original enrollment database, which has duplicate references.
4. Preload the model with a rehearsal enrollment and query if time permits. Stop
   that rehearsal and start a fresh timestamped demonstration root for class.
5. Keep `evaluation/results/summary.csv` and ACADEMIC_REPORT.md available as an
   honestly labelled fallback if inference fails. Do not claim the fallback is live.

## Exact Terminal commands on this Mac

```bash
cd ~/Documents/FaceMatch
source ~/.venvs/facematch-university/bin/activate
python scripts/doctor.py
python -m unittest discover -s tests -v
mkdir -p outputs
python -c "import cv2,numpy as np; assert cv2.imwrite('outputs/demo-no-face.png',np.full((400,400,3),255,dtype=np.uint8))"
export FACEMATCH_DATA_DIR="$PWD/outputs/demo-$(date +%Y%m%d-%H%M%S)"
python app/ui.py --port 8766
```

Open http://127.0.0.1:8766. The new directory initially contains zero people. Keep
Terminal open. Model downloads may be needed if the weight cache is empty; that
empty-cache scenario was not verified during final testing.

In the Mac file picker, press Command-Shift-G to enter a path beginning with `~/`.

## Timed live segment — approximately 2 minutes

**0:00–0:15 — Introduce the scope.** Show the overview. Say: “This is an isolated
local database. It compares photographs with enrolled records; it does not prove identity.”

**0:15–0:50 — Register.** Choose Register a person. Use ID `demo-01`, name
`Consenting demo participant`, and this reference:

```text
~/Documents/FaceMatch/evaluation/dataset/person_01/test.jpg
```

Confirm permission only if you actually have it. Submit. Show the success message
and directory entry. This operation saves a reference only in the isolated demo root.

**0:50–1:15 — Check a distinct photograph.** Choose Check a photo and select:

```text
~/Documents/FaceMatch/evaluation/test_dataset/person_01/normal_01.jpg
```

Expected for this one-reference setup: a possible match around **0.6407**.
Say: “This score is cosine similarity, not a probability.” This is a previously
used exploratory example, not an unseen independent-validation example.

**1:15–1:35 — Show unknown.** Remove the selected photo and choose:

```text
~/Documents/FaceMatch/evaluation/unknown_dataset/unknown_01/normal_01.jpg
```

Expected for this one-reference setup: unknown, best score around **0.1747**.
Explain that this subset demonstration does not contradict the full baseline
result of only 2/4 unknown rejections with all nine references.

**1:35–1:50 — Show a clear error.** Select:

```text
~/Documents/FaceMatch/outputs/demo-no-face.png
```

Expected: no usable face, with the app remaining usable. Do not follow library
suggestions to disable enforced detection.

**1:50–2:00 — Close.** Show the directory and note the stored demo record.
Stop the server with Control-C in Terminal. Explain that closing the browser alone
does not stop Python. If required, restart the same data-root server to demonstrate
that the record persists; this cross-process persistence was also checked automatically.

```bash
unset FACEMATCH_DATA_DIR
```

Do not delete the demo root or any dataset during class unless explicitly requested.

## Extra checks outside the timed segment

- Duplicate ID: try `demo-01` again; it must be rejected without replacing the record.
- Multiple faces: use a separately authorized group photo. Automated live checks
  already rejected a synthetic side-by-side two-face fixture; a natural group photo
  remains an additional detector test, not a claimed accuracy measurement.
- Terminal interface: run `python app/main.py`; enter `3`, then `4`. With a fresh
  demo root, it should show the local records (or an empty-list message) and exit.
- Missing file: in the terminal recognition prompt, enter a nonexistent path;
  the application must return a readable error and stay usable.
- Camera: no webcam capture is implemented or required; photographs are selected
  from disk. Do not claim camera testing.
