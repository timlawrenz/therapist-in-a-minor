# Implementation Plan: Image Enrichment

### Phase 1: Environment and Setup [checkpoint: 3cb22a9]
- [x] Task: Update `requirements.txt` to include `llm-adapter`. [2517537]
- [x] Task: Update `config.yaml` to include Ollama and `llm-adapter` settings (base URL, model names). [2518593]
- [x] Task: Update `extractor/utils.py` to load new configuration settings. [verified-existing]
- [x] Task: Conductor - User Manual Verification 'Phase 1: Environment and Setup' (Protocol in workflow.md)

### Phase 2: Enrichment Engine Core [checkpoint: 8926449]
- [x] Task: Create `extractor/enrichment_engine.py` to handle communication with Ollama. [86d91fa]
- [x] Task: Implement TDD for `EnrichmentEngine`: Write failing tests for description and embedding generation (mocking Ollama API). [2525380]
- [x] Task: Implement `EnrichmentEngine` methods using `llm-adapter` to generate descriptions and embeddings. [2525893]
- [x] Task: Update `requirements.txt` with `transformers` and `torch`. [2537156]
- [x] Task: Refactor `EnrichmentEngine` to use `transformers` for DINOv2 and CLIP embeddings. [2540348]
- [x] Task: Verify tests pass and refine implementation. [verified]
- [x] Task: Conductor - User Manual Verification 'Phase 2: Enrichment Engine Core' (Protocol in workflow.md)
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Enrichment Engine Core' (Protocol in workflow.md)

### Phase 3: CLI Integration and Storage [checkpoint: 0d56a92]
- [x] Task: Update `extractor/docling_engine.py` or `extractor/cli.py` to invoke `EnrichmentEngine` after image extraction. [2542612]
- [x] Task: Implement TDD for metadata storage: Write failing tests for `image_metadata.json` generation and structure. [2544310]
- [x] Task: Implement logic to aggregate and save enrichment data into `image_metadata.json` for each image folder. [2544310]
- [x] Task: Verify tests pass and ensure error handling (warning logs on Ollama failure). [verified]
- [x] Task: Conductor - User Manual Verification 'Phase 3: CLI Integration and Storage' (Protocol in workflow.md)

### Phase 4: Integration Testing and Validation [checkpoint: cb5f7f6]
- [x] Task: Create integration tests in `tests/test_enrichment_integration.py` to verify the full pipeline with a mock Ollama server. [2547131]
- [x] Task: Perform a manual verification run with a live local Ollama instance and sample PDF. [verified]
- [x] Task: Conductor - User Manual Verification 'Phase 4: Integration Testing and Validation' (Protocol in workflow.md)
