# Specification: Resumable Extraction

## Overview
Batch processing of DOJ PDF files is time-consuming and resource-intensive. This track implements "resumable" logic for the `extract` command, allowing the tool to skip documents that have already been successfully processed in previous runs.

## Functional Requirements
- **Completion Check:** Before starting the Docling conversion for a document, the system must check the target directory for existing artifacts.
- **Robust Verification:** A document is considered "complete" ONLY if:
    - `manifest.json` exists.
    - The high-fidelity Markdown file (`<doc_id>.md`) exists.
    - The structured JSON file (`<doc_id>.json`) exists.
    - If `manifest.json` contains image entries, every image file listed must exist in the `images/` directory.
    - If images exist, the `images/image_metadata.json` (enrichment data) must also exist.
- **Skip Behavior:** If a document is complete, it should be skipped. A message should be logged at the `INFO` level indicating the skip.
- **Force Override:** The `--force` CLI flag must bypass all skip logic and perform a full re-extraction and enrichment.
- **Incremental Processing:** If any mandatory file is missing (e.g., the markdown file exists but the JSON is missing), the entire document process for that file must be re-run to ensure consistency.

## Non-Functional Requirements
- **Performance:** The existence check must be significantly faster than the extraction process itself.

## Acceptance Criteria
- [ ] Running the `extract` command on a directory that has already been processed results in 0 files extracted and all files skipped (verified via logs).
- [ ] Deleting a single mandatory artifact (e.g., the `.json` file) from a target document folder causes that document to be re-processed on the next run.
- [ ] Using the `--force` flag results in all files being re-processed regardless of existing artifacts.
- [ ] Automated tests verify the skip logic for various partial-completion scenarios.

## Out of Scope
- Resuming *inside* a single document (e.g., resuming from page 50 of 100).
- Checksum verification of existing assets (only file existence is required for this track).
