# Specification - Discovery and Scaffolding Engine

## Overview
The Discovery and Scaffolding Engine is the entry point of the extraction pipeline. Its primary responsibility is to scan a source directory recursively, identify supported media types (PDF, Image, Video), and create a mirrored, high-fidelity directory structure in the target location. Each discovered document will have its own dedicated directory containing the original source file and an initial JSON manifest.

## Functional Requirements

### 1. Recursive Document Discovery
- Scan a user-provided source directory recursively.
- Identify documents based on file extensions:
    - **PDF:** `.pdf`
    - **Image:** `.jpg`, `.jpeg`, `.png`, `.tiff`, `.bmp`
    - **Video:** `.mp4`, `.avi`, `.mov`, `.mkv`
- Handle large datasets efficiently (thousands of files).

### 2. Scaffolding Generation
- For each unique document discovered, create a dedicated folder in the target directory named after the document ID.
- The document ID is currently assumed to be the filename without extension (e.g., `EFTA00003850`).
- The scaffold structure for a document `ID` should be:
    ```
    target/
    └── <relative_path_from_source>/
        └── <ID>/
            ├── <ID>.<ext> (Symlink or Copy of source)
            └── manifest.json
    ```

### 3. Initial Manifest Creation
- Generate a `manifest.json` file for each document with the following initial metadata:
    - `document_id`: The unique ID.
    - `source_path`: Absolute path to the original file.
    - `file_type`: PDF, Image, or Video.
    - `file_size`: In bytes.
    - `hash`: SHA-256 hash of the original file for integrity.
    - `creation_date`: File creation timestamp.
    - `processing_history`: An array to track pipeline steps (e.g., `[{"step": "discovery", "timestamp": "...", "status": "success"}]`).

### 4. CLI Interface
- Provide a command-line interface to trigger the discovery:
    ```bash
    python -m extractor.cli discover --source <path> --target <path>
    ```

## Technical Constraints
- **Language:** Python 3.10+
- **Lineage:** Must maintain a clear link to the source path.
- **Robustness:** Gracefully handle permission errors or missing files during the scan.
- **Portability:** Use path handling that works across different OSs (though primary target is Linux).
