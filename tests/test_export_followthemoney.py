import json
import subprocess
import sys
from pathlib import Path


def test_export_followthemoney_ndjson(tmp_path):
    target = tmp_path / "target"
    doc_dir = target / "doc1"
    images_dir = doc_dir / "images"
    images_dir.mkdir(parents=True)

    source_pdf = tmp_path / "source" / "doc1.pdf"
    source_pdf.parent.mkdir(parents=True)
    source_pdf.write_bytes(b"%PDF-1.4\n")

    # Minimal manifest with lineage
    manifest = {
        "document_id": "doc1",
        "source_path": str(source_pdf.absolute()),
        "hash": "abc123",
        "timestamp": "2026-02-06T00:00:00",
        "models": {"ocr_model": "ocr", "layout_model": "layout"},
        "images": [{"filename": "page_1_img_1.png", "page_no": 1, "bbox": [0, 0, 10, 10]}],
    }
    (doc_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (doc_dir / "doc1.md").write_text("hello", encoding="utf-8")

    (images_dir / "page_1_img_1.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    image_metadata = [
        {
            "filename": "page_1_img_1.png",
            "page_no": 1,
            "bbox": [0, 0, 10, 10],
            "description": "a test image",
        }
    ]
    (images_dir / "image_metadata.json").write_text(
        json.dumps(image_metadata), encoding="utf-8"
    )

    out_path = tmp_path / "out.ndjson"
    script_path = (
        Path(__file__).resolve().parent.parent / "scripts" / "export_followthemoney.py"
    )

    subprocess.run(
        [sys.executable, str(script_path), "--target", str(target), "--out", str(out_path)],
        check=True,
    )

    lines = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines()]
    assert len(lines) >= 2

    docs = [e for e in lines if e.get("schema") == "Document"]
    images = [e for e in lines if e.get("schema") == "Image"]
    assert len(docs) == 1
    assert len(images) == 1

    doc = docs[0]
    img = images[0]

    assert doc["id"] == "doc-abc123"

    assert "proof" in img.get("properties", {})
    assert doc["id"] in img["properties"]["proof"]
