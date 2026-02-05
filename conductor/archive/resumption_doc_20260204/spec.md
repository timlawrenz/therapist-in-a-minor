# Specification - Discovery Resumption and Project Documentation

## Overview
This track introduces idempotency to the discovery and scaffolding engine, allowing it to resume interrupted scans or process incremental updates to the source dataset without redundant work. It also adds a project `README.md` to guide users on how to use the tool.

## Functional Requirements

### 1. Discovery Resumption (Idempotency)
- **Existence Check:** Before creating a scaffold directory or manifest, the tool must check if the target document folder and `manifest.json` already exist.
- **Skip Logic:** If the manifest exists, the tool should skip processing for that document by default.
- **Force Overwrite:** Add a `--force` flag to the `discover` command. When this flag is used, existing target folders and manifests will be recreated/overwritten.
- **Summary Reporting:** Update the CLI summary to include the number of skipped documents.
    - `Successfully processed: X`
    - `Skipped (already exists): Y`
    - `Errors encountered: Z`

### 2. Project Documentation
- **README.md Creation:** Create a top-level `README.md` file.
- **Content:**
    - **Vision:** Describe the project's goal of creating a high-fidelity, machine-readable derivative of the DOJ HR4405 Epstein files.
    - **Installation:** Briefly mention setting up the virtual environment and installing requirements.
    - **Usage:** Provide clear examples of the `discover` command, including the new `--force` flag and arguments for `--source` and `--target`.

## Technical Constraints
- **CLI Implementation:** Must continue using the `click` framework in `extractor/cli.py`.
- **Logic Placement:** Resumption logic should reside within the CLI or the `Scaffolder` class as appropriate.

## Acceptance Criteria
- Running `discover` twice on the same dataset results in all files being "skipped" on the second run.
- Running `discover` with `--force` on an existing target directory results in all documents being re-processed.
- The `README.md` is present and accurately describes the tool's purpose and usage.
