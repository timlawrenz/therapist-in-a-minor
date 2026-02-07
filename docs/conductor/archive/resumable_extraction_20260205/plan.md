# Implementation Plan: Resumable Extraction

### Phase 1: Completeness Verification Logic [checkpoint: c96e320]
- [x] Task: Implement `Scaffolder.is_extraction_complete(target_folder, doc_stem)` in `extractor/scaffolding.py`. [verified]
    - [x] This method will read `manifest.json` and check for the existence of the MD, JSON, images, and image metadata.
- [x] Task: Implement TDD for verification logic: Write failing tests in `tests/test_scaffolding_resume.py` covering: [verified]
    - [x] Success (all files exist).
    - [x] Failure (missing MD/JSON).
    - [x] Failure (missing image from manifest).
    - [x] Failure (missing `image_metadata.json` when images are present).
- [x] Task: Implement the logic to pass the tests. [verified]
- [x] Task: Conductor - User Manual Verification 'Phase 1: Completeness Verification Logic' (Protocol in workflow.md)

### Phase 2: CLI Integration [checkpoint: bd0092c]
- [x] Task: Update `extractor/cli.py` `extract` command to utilize the new skip logic. [verified]
- [x] Task: Ensure the `--force` flag correctly bypasses the check. [verified]
- [x] Task: Implement TDD for CLI resume: Write failing tests in `tests/test_cli_resume.py` to verify skipped counts and force behavior. [verified]
- [x] Task: Update logging to provide clear feedback on skipped documents. [verified]
- [x] Task: Conductor - User Manual Verification 'Phase 2: CLI Integration' (Protocol in workflow.md)

### Phase 3: Integration Validation [checkpoint: 79923c5]
- [x] Task: Create a full pipeline test in `tests/test_integration_resume.py` that runs extraction twice and confirms the second run skips all files. [verified]
- [x] Task: Perform manual verification on the DOJ dataset (e.g., process 2 files, stop, run again). [verified]
- [x] Task: Conductor - User Manual Verification 'Phase 3: Integration Validation' (Protocol in workflow.md)
