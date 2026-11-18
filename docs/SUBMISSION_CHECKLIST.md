# Provisional submission requirements and readiness

No course-specific assignment/rubric, required report format, deadline, slide template,
author details or declaration was found in the project or the nearby assignment-file
search. These materials address the user's listed scope as provisional requirements.

| Requirement | Implementation / evidence | Status |
|---|---|---|
| Registration, detection, recognition, directory, exit | UI + terminal; 32 regression and 17 live checks | Implemented and tested |
| Cropping/alignment and embeddings | Enforced RetinaFace, explicit base normalization, finite 512 values; live crop/embedding checks | Implemented and tested |
| Invalid input, duplicates, missing records, unknown/failure | Readable outcomes, no overwrite, rollback, unavailable distinct from unknown | Implemented and tested |
| Justified fixed threshold | Preserved 0.50; tied best reference-only grid value, no evaluation tuning | Experimental justification documented |
| Database persistence | SQLite migration/connection cleanup; second-process live read | Tested |
| Evaluation and ablations | Audit + fresh 46 embeddings; 8 rows / 112 archived decisions reproduced | Tested on exploratory available data |
| Image/reference split checks | Byte and decoded-pixel audit; no cross-split overlap | Tested; near duplicates not ruled out |
| Independent accuracy validation | New validation folders empty | Not performed; limitation explicitly disclosed |
| Clean setup | Two Python 3.11 installations, locked dependencies, pip check | Tested on Apple Silicon macOS |
| Empty-cache model download | Existing pretrained cache reused | Not tested |
| README, academic report | README + ACADEMIC_REPORT.md | Prepared under provisional requirements |
| 10-minute presentation | Timed outline + full speaker notes | Prepared; no course slide template supplied |
| Demonstration | Isolated data root, exact steps, fallback, expected observed examples | Prepared; rehearsal by presenter still recommended |
| Consent/data handling | ETHICS_AND_DATA.md; private data excluded | Documented; actual consent records not verified |
| Clean code/docs/results archive | Allowlist, manifest and ZIP check | Prepared and checked during final handover |
| Course rubric and required file formats | Not supplied | Student/instructor confirmation required |
| Student/course metadata and declarations | Not supplied | Student completion required |
| Remote publication/university submission | Neither requested nor authorized | Not performed |

## Readiness statement

**Implemented:** the local upload-based prototype, evaluation runner, setup tools and
submission materials. **Tested:** the explicitly listed automated, real-model,
clean-install, reproduction and package checks. **Ready to demonstrate:** with
cached weights, the verified runtime, and authorized local photographs.

**Ready for unconditional university submission: not claimed.** The code/docs
package is prepared for review against provisional requirements. Before submitting:

1. Check the actual assignment/rubric and required file formats. Export/format the
   report or presentation only as required; Markdown sources are the current deliverables.
2. Enter student/course/instructor identifiers and complete required declarations,
   including any permitted-AI-use statement. Do not sign or fabricate these automatically.
3. Confirm permission to process/show each demonstration photograph.
4. Keep independent-validation limitations in the report. Collect new data only if
   required by the rubric or needed to make stronger performance claims.
5. Review the clean archive, then submit it yourself through the university's approved channel.
