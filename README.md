# DOJ Disclosures HR4405 Derivative Dataset Tool

## Vision
This project aims to create a high-fidelity, machine-readable derivative of the DOJ Disclosures of HR4405 (The Epstein Files). The tool extracts text and images from the source PDFs while preserving absolute lineage, enabling modern data analysis, research, and machine learning workflows.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd therapist-in-a-minor
    ```

2.  **Set up a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Linux/macOS
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

The primary command is `discover`, which recursively scans a source directory for documents (PDFs, Images, Videos) and creates a structured scaffolding in the target directory.

### Basic Discovery

```bash
python -m extractor.cli discover --source /path/to/source --target /path/to/target
```

### Options

-   `--source <path>`: (Required) Path to the source directory containing the DOJ files.
-   `--target <path>`: (Required) Path where the processed dataset will be created.
-   `--force`: Force overwrite of existing processed documents. By default, the tool skips documents that already have a `manifest.json` in the target folder.
-   `--verbose`: Enable verbose logging (DEBUG level) to see detailed processing information.
-   `--help`: Show the help message and exit.

### Example

```bash
python -m extractor.cli --verbose discover --source ./source_data --target ./derived_dataset
```

## Dataset Structure

Each discovered document is given its own directory in the target location, mirroring the source hierarchy:

```
target/
└── relative/path/to/document_id/
    ├── document_id.pdf (Symlink to source)
    └── manifest.json (Metadata and lineage)
```

The `manifest.json` contains core metadata including file hashes, size, and a processing history for full traceability.
