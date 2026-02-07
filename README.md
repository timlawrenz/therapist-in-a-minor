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

The tool offers three commands: `discover`, `extract`, and `process` (recommended).

### 1. Discovery
Recursively scans a source directory for documents (PDFs) and creates a structured scaffolding in the target directory.

```bash
python -m extractor.cli discover --source /path/to/source --target /path/to/target
```

### 2. Extraction
Extracts text, layouts, and images from the documents using **Docling**. It also performs AI enrichment on extracted images (descriptions, embeddings, and faces).

```bash
python -m extractor.cli extract --source /path/to/source --target /path/to/target
```

### 3. Process (recommended)
Runs discovery + extraction in a single step.

```bash
python -m extractor.cli process --source /path/to/source --target /path/to/target
```

### 4. Export to FollowTheMoney (Stream A: Factual)
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

### 5. Infer FollowTheMoney (Stream B: Inferred)
Generate a probabilistic/inferred NDJSON stream by asking an LLM (Ollama) to interpret the factual stream.

```bash
python scripts/infer_followthemoney.py --target /path/to/target
# reads:  /path/to/target/followthemoney.ndjson
# writes: /path/to/target/followthemoney.inferred.ndjson

# show progress:
python scripts/infer_followthemoney.py --target /path/to/target --verbose

# override inputs/outputs:
python scripts/infer_followthemoney.py --target /path/to/target --factual /path/to/followthemoney.ndjson --out /path/to/inferred.ndjson
```

The inferred stream emits entities like `Person`, `Address`, and `Event` (and other whitelisted schemata). Output is written incrementally as each evidence item is processed (useful for large corpora).

Each inferred entity includes:
- `proof`: link back to the originating factual `Document` or `Image` id
- inference metadata: JSON including `confidence` and a short `evidence` quote, stored in `notes` when available (otherwise `description`/`summary`)

### Extractor CLI Options
-   `--source <path>`: (Required) Path to the source directory containing the DOJ files.
-   `--target <path>`: (Required) Path where the processed dataset will be created.
-   `--force`: Force overwrite of existing processed documents.
-   `--verbose`: Enable verbose logging (DEBUG level). This is a global option and must be passed before the command, e.g. `python -m extractor.cli --verbose extract ...`.

## Configuration

Configuration is managed via `config.yaml` in the project root. You can customize the models used for extraction and enrichment.

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

### 3. Image Enrichment Metadata
A sidecar JSON file (`images/image_metadata.json`) containing AI-derived analysis for every extracted image:

-   **`description`:** A detailed natural language description of the image content (generated via Ollama/VLM).
-   **`embeddings`:** High-dimensional vector representations for semantic search:
    -   **DINOv2:** Self-supervised vision features (e.g., from `facebook/dinov2-base`).
    -   **CLIP:** Semantic text-image features (e.g., from `openai/clip-vit-base-patch32`).

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
        └── image_metadata.json
```