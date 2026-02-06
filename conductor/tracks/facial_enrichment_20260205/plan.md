# Implementation Plan: Facial Detection and Embedding

### Phase 1: Environment and Setup [checkpoint: bd5563c]
- [x] Task: Update `requirements.txt` to include `deepface`, `retina-face`, and `tf-keras` (Switched to `insightface` and `onnxruntime` due to TF issues on Py3.14). [verified]
- [x] Task: Update `config.yaml` to include an `enrichment.facial` section with toggle and model selection. [verified]
- [x] Task: Conductor - User Manual Verification 'Phase 1: Environment and Setup' (Protocol in workflow.md)

### Phase 2: Facial Enrichment Engine
- [ ] Task: Create `extractor/facial_engine.py` to wrap RetinaFace and FaceNet.
- [ ] Task: Implement TDD for `FacialEngine`: Write failing tests for face detection and embedding generation (mocking model weights).
- [ ] Task: Implement `FacialEngine` methods to detect faces and generate embeddings.
- [ ] Task: Verify tests pass and refine implementation.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Facial Enrichment Engine' (Protocol in workflow.md)

### Phase 3: Integration and Storage
- [ ] Task: Update `extractor/cli.py` to invoke `FacialEngine` during the enrichment loop.
- [ ] Task: Update `image_metadata.json` saving logic to include the `faces` key.
- [ ] Task: Implement TDD for integrated enrichment: Write failing tests in `tests/test_facial_integration.py` to verify full metadata output.
- [ ] Task: Verify tests pass and ensure cases with zero faces are handled (empty list).
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Integration and Storage' (Protocol in workflow.md)

### Phase 4: Validation and Documentation
- [ ] Task: Perform a manual verification run with a sample image containing multiple faces.
- [ ] Task: Update `README.md` to document the new facial detection data points.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Validation and Documentation' (Protocol in workflow.md)
