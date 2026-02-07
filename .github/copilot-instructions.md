# Copilot instructions (therapist-in-a-minor)

## Build / setup
- Create and activate a venv:
  - `python3 -m venv .venv && source .venv/bin/activate`
- Install deps:
  - `pip install -r requirements.txt`

## Run the pipeline
- Discovery (scaffold + initial manifest + symlink to source):
  - `python -m extractor.cli discover --source /path/to/source --target /path/to/target`
- Extraction (Docling + images + optional enrichment):
  - `python -m extractor.cli extract --source /path/to/source --target /path/to/target`
- Common flags:
  - `--force` re-process even if artifacts already exist
  - `--verbose` enables DEBUG logging

## Tests
- Run all tests:
  - `python -m pytest`
- Run a single test:
  - `python -m pytest tests/test_cli.py::test_cli_help -q`
- Run a subset by keyword:
  - `python -m pytest -k enrichment -q`
- Coverage (pytest-cov is in requirements):
  - `python -m pytest --cov=extractor --cov-report=term-missing`

## High-level architecture
- `extractor/cli.py`: Click CLI entrypoint (`discover`, `extract`).
- `extractor/discovery.py` (`Scanner`): recursively scans a source path, skipping any files under hidden path components; supports PDFs + common image/video extensions.
- `extractor/scaffolding.py` (`Scaffolder`):
  - discovery-time scaffold (`create_scaffold`, `link_source`, `write_manifest`)
  - extraction resumption gate (`is_extraction_complete`) used by `extract` to skip completed docs unless `--force`.
- `extractor/docling_engine.py` (`DoclingEngine`): wraps Docling `DocumentConverter` and writes:
  - `<doc_id>.md` (Docling `export_to_markdown()`)
  - `<doc_id>.json` (Docling `export_to_dict()` / `model_dump()`)
  - extracted images under `images/` and a new `manifest.json` describing models + image provenance.
- `extractor/enrichment_engine.py` (`EnrichmentEngine`):
  - descriptions via `ollama.Client(...).generate()`
  - embeddings via local Hugging Face Transformers (lazy-loaded DINOv2 + CLIP).
- `extractor/utils.py`: `load_config()` loads root `config.yaml` (used by Docling + enrichment).

## Data/model conventions that affect correctness
- Target output layout (directory mode): `target/<relative_parent>/<doc_id>/...`.
  - `extract` mirrors the source tree; `discover` uses `Scaffolder.get_target_folder()` (same concept).
- `discover` writes an initial `manifest.json` with file metadata + `processing_history`; `extract` later overwrites `manifest.json` with the Docling/extraction manifest.
- Resumption semantics are defined by `Scaffolder.is_extraction_complete()` (manifest + `<doc_id>.md` + `<doc_id>.json` + images listed in manifest + `images/image_metadata.json` when images exist). Update this check if you add/remove required artifacts.

## Configuration conventions
`config.yaml` (repo root) keys used in code:
- `docling.ocr_model`, `docling.layout_model`
- `enrichment.ollama_host`, `enrichment.description_model`, `enrichment.embedding_model_dino`, `enrichment.embedding_model_clip`

## Repo-specific workflow conventions (conductor/)
- Project workflow is documented in `conductor/` (product goals, tech stack, and a prescriptive task lifecycle).
- Track plans (`conductor/tracks/**/plan.md` and `conductor/archive/**/plan.md`) use:
  - task state markers `[ ]` → `[~]` → `[x]` and append the short commit SHA when completed
  - phase headings may include `[checkpoint: <sha>]`
  - `conductor/workflow.md` expects task summaries/verification reports to be attached via `git notes`.

## Other AI workflow artifacts
- OpenSpec artifacts live under `openspec/`.
- This repo includes OpenSpec prompts/skills under `.github/prompts/` and `.github/skills/` (opsx/openspec-*).
