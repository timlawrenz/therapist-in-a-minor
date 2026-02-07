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

The extractor CLI offers a single command: `process`.

### 1. Process
Scans the source tree, creates a per-file scaffold in the target (folder + symlink + `manifest.json`), and for PDFs runs **Docling** to extract markdown/json and images.

Note: `process` performs **raw extraction only** (no AI enrichment).

```bash
python -m extractor.cli process --source /path/to/source --target /path/to/target
```

### 2. Export to FollowTheMoney (Stream A: Factual)
After extraction, export a FollowTheMoney entity stream (**NDJSON**) from a target folder:

```bash
python scripts/export_followthemoney.py --target /path/to/target
# writes: /path/to/target/followthemoney.ndjson

# or choose output path:
python scripts/export_followthemoney.py --target /path/to/target --out /path/to/out.ndjson

# optionally include embeddings (can be very large):
python scripts/export_followthemoney.py --target /path/to/target --include-embeddings
```

The exporter emits:
- one `Document` entity per document folder (`manifest.json`)
- one `Image` entity per extracted image (`images/image_metadata.json`), linked to the Document via `Image.proof`

### 3. Infer FollowTheMoney (Stream B: Inferred)
Generate a probabilistic/inferred NDJSON stream by asking an LLM (Ollama) to interpret the factual stream.

This is also where **image analysis** happens: unless you pass `--no-image-enrichment`, the script will generate per-image descriptions/embeddings/faces and persist them to `images/image_enrichment.json` for use as Image evidence.

```bash
python scripts/infer_followthemoney.py --target /path/to/target
# reads:  /path/to/target/followthemoney.ndjson
# writes: /path/to/target/followthemoney.inferred.ndjson

# show progress:
python scripts/infer_followthemoney.py --target /path/to/target --verbose

# disable inference-time image enrichment (no image descriptions/embeddings/faces):
python scripts/infer_followthemoney.py --target /path/to/target --no-image-enrichment

# override inputs/outputs:
python scripts/infer_followthemoney.py --target /path/to/target --factual /path/to/followthemoney.ndjson --out /path/to/inferred.ndjson
```

The inferred stream emits entities like `Person`, `Address`, and `Event` (and other whitelisted schemata). Output is written incrementally as each evidence item is processed (useful for large corpora).

Each inferred entity includes:
- `proof`: link back to the originating factual `Document` or `Image` id
- inference metadata: JSON including `confidence` and a short `evidence` quote, stored in `notes` when available (otherwise `description`/`summary`)

### 4. Deduplicate inferred entities (Stream C: Secondary)
Stream B intentionally produces *mention-level* entities (often many duplicates like 5x `Company` named “EFTA”, each with a different `proof`). Stream C is a secondary pass that merges duplicates into canonical entities and aggregates all `proof` links.

```bash
python scripts/dedup_followthemoney.py --target /path/to/target
# reads:  /path/to/target/followthemoney.inferred.ndjson
# writes: /path/to/target/followthemoney.inferred.dedup.ndjson

# show progress:
python scripts/dedup_followthemoney.py --target /path/to/target --verbose
```

The deduplicator currently uses exact-match canonicalization (case/whitespace normalization) for common schemata like `Person`, `Company`, and `Address`, and rewrites entity references (e.g. `Event.involved`) to point at the canonical IDs.

### Extractor CLI Options
-   `--source <path>`: (Required) Path to the source directory containing the DOJ files.
-   `--target <path>`: (Required) Path where the processed dataset will be created.
-   `--force`: Force overwrite of existing processed documents.
-   `--verbose`: Enable verbose logging (DEBUG level). This is a global option and must be passed before the command, e.g. `python -m extractor.cli --verbose process ...`.

## Configuration

Configuration is managed via `config.yaml` in the project root. You can customize the models used for Docling extraction and inference-time enrichment.

```yaml
docling:
  ocr_model: "https://huggingface.co/zai-org/GLM-OCR"
  layout_model: "https://huggingface.co/docling-project/docling-layout-heron-101"

enrichment:
  # Connection to local Ollama instance for image descriptions
  ollama_host: "http://localhost:11434"
  description_model: "llava"  # e.g., 'llava', 'gemma3:27b'
  
  # Hugging Face model IDs for embeddings (runs locally via Transformers)
  embedding_model_dino: "facebook/dinov2-base"
  embedding_model_clip: "openai/clip-vit-base-patch32"
```

## Data Model & Extracted Fields

For every processed PDF document, the following artifacts are generated in its target directory:

### 1. Text & Layout
-   **Markdown (`<doc_id>.md`):** High-fidelity text extraction preserving headers, tables, and lists.
-   **Structured JSON (`<doc_id>.json`):** Full document tree representation provided by Docling, including paragraphs, headers, tables, and their bounding box coordinates.

### 2. Extracted Images
All figures, photos, and charts detected in the PDF are saved as individual PNG files in the `images/` subdirectory.

### 3. Image Extraction Metadata (raw)
A sidecar JSON file (`images/image_metadata.json`) containing **raw** extraction metadata for each extracted image (e.g. filename, page number, bounding box).

Inference-time AI outputs are persisted separately to `images/image_enrichment.json` (descriptions, embeddings, faces) when running `scripts/infer_followthemoney.py`.

### 4. Lineage Manifest (`manifest.json`)
The central record for the document, linking all assets:
-   **`timestamp`:** When the extraction occurred.
-   **`models`:** Which OCR and Layout models were used.
-   **`images`:** List of extracted images with their provenance (page number, bounding box).

## Dataset Structure

```
target/
└── relative/path/to/document_id/
    ├── document_id.pdf (Symlink to source)
    ├── document_id.md
    ├── document_id.json
    ├── manifest.json
    └── images/
        ├── page_1_img_1.png
        ├── image_metadata.json
        └── image_enrichment.json  # created by inference (optional)
```