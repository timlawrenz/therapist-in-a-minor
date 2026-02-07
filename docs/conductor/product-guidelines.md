# Product Guidelines - DOJ Disclosures HR4405 Derivative Dataset

## Documentation and Metadata Style
- **Tone:** Clinical and Objective.
- **Style:** All generated descriptions (VLM) and transcriptions (OCR) must focus strictly on visual and textual facts. Avoid interpretive language, speculation, or narrative summaries.
- **Language:** English (US) unless the source document is in another language.

## Asset Management and Naming
- **Directory Structure:** Each unique source document (e.g., `EFTA00003850.pdf`) must reside in its own dedicated directory named after the document ID (e.g., `EFTA00003850/`).
- **Derivative Placement:** All extracted text, images, and enrichment manifests must be stored within the document's dedicated directory in a structured manner.
- **Naming Convention:** Derivatives should mirror the document ID with clear suffixes (e.g., `EFTA00003850_p1_img1.png`).
- **Uniqueness:** Leverage the fact that document IDs are unique across the entire universe to prevent collisions.

## Data Integrity and Verification
- **Flagging Ambiguity:** Any extraction or enrichment with a low confidence score (as determined by the model/tool) must be explicitly flagged with a `"needs_review": true` property and a confidence score in the sidecar manifest.
- **Lineage Verification:** Every derivative asset must contain a reference to its source PDF, including page number and bounding box coordinates (if applicable).
- **Versioning:** Adopt monolithic versioning where the dataset's state is tied directly to the version of the extraction pipeline/code used.

## AI Enrichment Principles
- **OCR:** Prioritize layout preservation. If a document is scanned, the OCR should attempt to reconstruct the textual flow (columns, headers).
- **VLM Descriptions:** Focus on high-level visual features, readable text within images, and structural components of the image (e.g., "Photocopy of a handwritten note," "Official seal of the DOJ").
- **Embeddings:** When generating DINO or CLIP embeddings, they should be stored alongside the image metadata in the JSON manifest to enable visual similarity search.
