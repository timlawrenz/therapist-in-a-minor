# Implementation Plan: Image Enrichment

### Phase 1: Environment and Setup
- [ ] Task: Update `requirements.txt` to include `llm-adapter`.
- [ ] Task: Update `config.yaml` to include Ollama and `llm-adapter` settings (base URL, model names).
- [ ] Task: Update `extractor/utils.py` to load new configuration settings.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Environment and Setup' (Protocol in workflow.md)

### Phase 2: Enrichment Engine Core
- [ ] Task: Create `extractor/enrichment_engine.py` to handle communication with Ollama.
- [ ] Task: Implement TDD for `EnrichmentEngine`: Write failing tests for description and embedding generation (mocking Ollama API).
- [ ] Task: Implement `EnrichmentEngine` methods using `llm-adapter` to generate descriptions and embeddings.
- [ ] Task: Verify tests pass and refine implementation.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Enrichment Engine Core' (Protocol in workflow.md)

### Phase 3: CLI Integration and Storage
- [ ] Task: Update `extractor/docling_engine.py` or `extractor/cli.py` to invoke `EnrichmentEngine` after image extraction.
- [ ] Task: Implement TDD for metadata storage: Write failing tests for `image_metadata.json` generation and structure.
- [ ] Task: Implement logic to aggregate and save enrichment data into `image_metadata.json` for each image folder.
- [ ] Task: Verify tests pass and ensure error handling (warning logs on Ollama failure).
- [ ] Task: Conductor - User Manual Verification 'Phase 3: CLI Integration and Storage' (Protocol in workflow.md)

### Phase 4: Integration Testing and Validation
- [ ] Task: Create integration tests in `tests/test_enrichment_integration.py` to verify the full pipeline with a mock Ollama server.
- [ ] Task: Perform a manual verification run with a live local Ollama instance and sample PDF.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Integration Testing and Validation' (Protocol in workflow.md)
