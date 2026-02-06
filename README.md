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

### Options
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