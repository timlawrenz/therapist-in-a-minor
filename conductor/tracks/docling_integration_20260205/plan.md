# Implementation Plan: Docling Integration

## Phase 1: Environment and Setup [checkpoint: 30b502e]
- [x] Task: Update `requirements.txt` with `docling` and necessary AI/ML dependencies. [4bae7f8]
- [x] Task: Design and implement `config.yaml` to store model paths and extraction settings. [151715c]
- [x] Task: Implement a configuration loader in `extractor/utils.py` to read settings. [ba26571]
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Environment and Setup' (Protocol in workflow.md)

## Phase 2: Docling Engine Core [checkpoint: 986663f]
- [x] Task: Create `extractor/docling_engine.py` (or update `discovery.py`) to wrap Docling's `DocumentConverter`. [8540f0a]
- [x] Task: Configure `DocumentConverter` to use GLM-OCR and Heron-101 models as specified in `config.yaml`. [e90c458]
- [x] Task: Implement a basic extraction method that takes a PDF path and returns a Docling `ConversionResult`. [3f16cf2]
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Docling Engine Core' (Protocol in workflow.md)

## Phase 3: Extraction, Lineage, and Mirrored Storage
- [x] Task: Implement JSON and high-fidelity Markdown export using Docling's native serializers. [60d33c3]
- [x] Task: Implement image extraction logic and saving to a mirrored directory structure. [5e2ac6b]
- [x] Task: Implement lineage mapping to capture page numbers and coordinates for all extracted assets. [c935a29]
- [ ] Task: Implement the manifest/metadata generator to tie all assets together with their source PDF.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Extraction, Lineage, and Mirrored Storage' (Protocol in workflow.md)

## Phase 4: CLI Integration and Validation
- [ ] Task: Refactor `extractor/cli.py` to use the Docling engine by default in the `extract` command.
- [ ] Task: Update integration tests in `tests/test_integration.py` to verify the full Docling pipeline.
- [ ] Task: Perform a sample extraction on a representative DOJ PDF and verify the mirrored structure.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: CLI Integration and Validation' (Protocol in workflow.md)
