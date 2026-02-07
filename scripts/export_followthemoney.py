#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from followthemoney import model


def _hash_file(path: Path) -> Dict[str, Any]:
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()
    size = 0
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            size += len(chunk)
            sha1.update(chunk)
            sha256.update(chunk)
    return {"sha1": sha1.hexdigest(), "sha256": sha256.hexdigest(), "size": size}


def _stable_id(prefix: str, value: str) -> str:
    h = hashlib.sha1(value.encode("utf-8", errors="ignore")).hexdigest()
    return f"{prefix}-{h}"


def _as_uri(path: Path) -> str:
    try:
        return path.absolute().as_uri()
    except ValueError:
        return f"file://{path.absolute().as_posix()}"


def _find_pdf(doc_dir: Path) -> Optional[Path]:
    pdfs = sorted(doc_dir.glob("*.pdf"))
    return pdfs[0] if pdfs else None


def _write_entity(out, entity) -> None:
    data = entity.to_dict() if hasattr(entity, "to_dict") else dict(entity)
    out.write(json.dumps(data, ensure_ascii=False) + "\n")


def _build_entities(
    doc_dir: Path,
    manifest: Dict[str, Any],
    include_embeddings: bool,
) -> Tuple[Any, List[Any]]:
    doc_stem = manifest.get("document_id") or doc_dir.name

    source_path = manifest.get("source_path")
    pdf_path = Path(source_path) if source_path else None
    if pdf_path is None or not pdf_path.exists():
        pdf_path = _find_pdf(doc_dir)

    sha256 = manifest.get("hash")
    if not sha256 and pdf_path and pdf_path.exists():
        sha256 = _hash_file(pdf_path)["sha256"]

    doc_id = f"doc-{sha256}" if sha256 else _stable_id("doc", str(doc_dir.absolute()))

    doc = model.make_entity("Document")
    doc.id = doc_id

    doc.add("title", doc_stem)
    if pdf_path is not None:
        doc.add("fileName", pdf_path.name)
        mime = mimetypes.guess_type(pdf_path.name)[0] or "application/pdf"
        doc.add("mimeType", mime)
        doc.add("extension", pdf_path.suffix.lstrip(".") or "pdf")
        try:
            hashes = _hash_file(pdf_path)
            doc.add("contentHash", hashes["sha1"])
            doc.add("fileSize", hashes["size"])
            doc.add("notes", f"sha256:{hashes['sha256']}")
        except Exception:
            pass

    if source_path:
        doc.add("sourceUrl", _as_uri(Path(source_path)))

    ts = manifest.get("timestamp")
    if ts:
        doc.add("processedAt", ts)

    doc.add("processingAgent", "therapist-in-a-minor/extractor")

    models = manifest.get("models") or {}
    if isinstance(models, dict):
        ocr = models.get("ocr_model")
        layout = models.get("layout_model")
        if ocr or layout:
            doc.add("generator", f"docling ocr={ocr} layout={layout}")

    md_path = doc_dir / f"{doc_stem}.md"
    if md_path.exists():
        try:
            doc.add("bodyText", md_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    images_dir = doc_dir / "images"
    img_meta_path = images_dir / "image_metadata.json"
    if img_meta_path.exists():
        try:
            images = json.loads(img_meta_path.read_text(encoding="utf-8"))
        except Exception:
            images = []
    else:
        images = manifest.get("images") or []

    image_entities: List[Any] = []
    for img in images:
        if not isinstance(img, dict):
            continue
        filename = img.get("filename")
        if not filename:
            continue

        img_path = images_dir / filename

        img_sha256 = None
        if img_path.exists():
            try:
                img_sha256 = _hash_file(img_path)["sha256"]
            except Exception:
                img_sha256 = None

        img_id = f"img-{img_sha256}" if img_sha256 else _stable_id("img", f"{doc_id}:{filename}")

        image_ent = model.make_entity("Image")
        image_ent.id = img_id

        image_ent.add("fileName", filename)
        mime = mimetypes.guess_type(filename)[0] or "image/png"
        image_ent.add("mimeType", mime)
        image_ent.add("extension", Path(filename).suffix.lstrip("."))

        if img_path.exists():
            image_ent.add("sourceUrl", _as_uri(img_path))
            try:
                hashes = _hash_file(img_path)
                image_ent.add("contentHash", hashes["sha1"])
                image_ent.add("fileSize", hashes["size"])
                image_ent.add("notes", f"sha256:{hashes['sha256']}")
            except Exception:
                pass

        if img.get("description"):
            image_ent.add("description", img.get("description"))

        provenance = {
            "page_no": img.get("page_no"),
            "bbox": img.get("bbox"),
        }
        if img.get("faces"):
            provenance["faces"] = img.get("faces")
        if include_embeddings and img.get("embeddings"):
            provenance["embeddings"] = img.get("embeddings")
        if any(v is not None for v in provenance.values()):
            image_ent.add("notes", json.dumps(provenance, ensure_ascii=False))

        image_ent.add("proof", doc_id)

        image_entities.append(image_ent)

    return doc, image_entities


def export_target(target_dir: Path, out_path: Path, include_embeddings: bool) -> int:
    target_dir = Path(target_dir)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as out:
        for manifest_path in sorted(target_dir.rglob("manifest.json")):
            doc_dir = manifest_path.parent
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                continue

            if not isinstance(manifest, dict):
                continue

            doc, images = _build_entities(doc_dir, manifest, include_embeddings)
            _write_entity(out, doc)
            for image_ent in images:
                _write_entity(out, image_ent)

    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export extracted dataset folders to FollowTheMoney NDJSON"
    )
    parser.add_argument("--target", required=True, type=Path, help="Target root directory")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output NDJSON path (default: <target>/followthemoney.ndjson)",
    )
    parser.add_argument(
        "--include-embeddings",
        action="store_true",
        help="Include embeddings from image_metadata.json (can be very large)",
    )

    args = parser.parse_args(argv)
    out_path = args.out or (args.target / "followthemoney.ndjson")
    return export_target(args.target, out_path, args.include_embeddings)


if __name__ == "__main__":
    raise SystemExit(main())
