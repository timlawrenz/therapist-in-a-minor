# Specification: Image Enrichment (Descriptions and Embeddings)

### Overview
This track enhances the extraction pipeline by automatically enriching every extracted image with a text description and two types of embeddings: DINOv2 and CLIP. This process will utilize a local Ollama instance accessed via the `llm-adapter` library, with all settings configurable through `config.yaml`.

### Functional Requirements
- **Integration:** Integrate the enrichment process directly into the existing `extract` command.
- **Text Description:** Generate a natural language description of each extracted image using a VLM (e.g., LLaVA, Gemma 3) via Ollama.
- **Embeddings:** Generate both DINOv2 and CLIP embeddings for each image using Hugging Face `transformers` library.
- **Configurable Models:** Allow the user to specify:
    - Ollama model name for descriptions (e.g., `gemma3:27b`).
    - Hugging Face model IDs for DINOv2 and CLIP embeddings in `config.yaml`.
- **Storage:** For every directory containing extracted images, generate a single `image_metadata.json` file.
    - This file should map each image filename to its description and embedding vectors (or references to them).
- **Error Handling:** Ensure that failures in enrichment (e.g., Ollama offline) are logged but do not halt the primary text extraction process.

### Non-Functional Requirements
- **Unified Infrastructure:** Leverage Ollama as the single backend for both vision-language tasks and embedding generation.
- **Efficiency:** Process enrichments immediately after an image is saved to minimize redundant IO.

### Acceptance Criteria
- [ ] `config.yaml` includes settings for Ollama and `llm-adapter`.
- [ ] The `extract` command successfully calls Ollama to generate descriptions and embeddings.
- [ ] An `image_metadata.json` file is created in the images folder of each processed document.
- [ ] The metadata file contains valid descriptions and high-dimensional vectors for both DINOv2 and CLIP.
- [ ] The system handles missing Ollama connections gracefully with clear warning logs.

### Out of Scope
- Implementing a vector database for storage.
- Support for remote LLM APIs (OpenAI, Anthropic) in this specific track.
- Re-processing images already extracted in previous runs (unless `--force` is used).
