# Specification: Facial Detection and Embedding

## Overview
This track enhances the image enrichment pipeline by adding facial detection and recognition capabilities. For every extracted image, the tool will identify human faces using RetinaFace and generate unique embedding vectors for each face using FaceNet. All facial data will be stored within the existing `image_metadata.json` to maintain a strict lineage to the source document.

## Functional Requirements
- **Face Detection:** Integrate RetinaFace to detect all human faces in extracted images.
- **Face Embedding:** For every detected face, generate a high-dimensional embedding vector using FaceNet.
- **Metadata Augmentation:** Update the `image_metadata.json` structure for each document.
    - Add a `faces` key to each image object.
    - Each face entry must include:
        - `bbox`: The bounding box coordinates `[x, y, w, h]` relative to the extracted image.
        - `embedding`: The FaceNet vector representation.
- **Configurability:**
    - Models should be configurable in `config.yaml` under an `enrichment.facial` section.
    - Users should be able to toggle facial detection on/off.
- **Integration:** This process must run automatically as part of the `extract` command, following the general image enrichment (description/DINO/CLIP).

## Non-Functional Requirements
- **Performance:** Ensure that face detection and embedding do not significantly bottleneck the overall extraction pipeline. Consider batching or hardware acceleration (GPU) if available.
- **Robustness:** Handle cases with no faces gracefully (empty `faces` list).

## Acceptance Criteria
- [ ] `config.yaml` includes options for RetinaFace and FaceNet.
- [ ] Processing an image with faces results in a "faces" key in `image_metadata.json`.
- [ ] Facial bounding boxes are accurate and traceable to the image.
- [ ] FaceNet embeddings are generated and stored as lists of floats.
- [ ] Processing an image without faces results in an empty "faces" list in the metadata.
- [ ] Automated tests verify detection and embedding logic with mock/sample images.

## Out of Scope
- Face matching/clustering across multiple images (this is a foundation for future work).
- High-fidelity face cropping and storage (only bounding boxes and embeddings are stored).
- Identification of specific individuals (unsupervised embedding generation only).
