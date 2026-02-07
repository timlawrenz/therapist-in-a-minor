import json
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from extractor.cli import cli


@patch("extractor.cli.DoclingEngine")
@patch("extractor.cli.Scanner")
def test_process_writes_raw_image_metadata(MockScanner, MockDoclingEngine, tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    pdf_path = source_dir / "test.pdf"
    pdf_path.touch()

    target_dir = tmp_path / "target"

    mock_scanner = MockScanner.return_value
    mock_scanner.scan.return_value = [pdf_path]

    mock_docling = MockDoclingEngine.return_value
    mock_docling.convert.return_value = MagicMock()

    images_dir = target_dir / "test" / "images"
    image_metadata = [
        {
            "filename": "img1.png",
            "page_no": 1,
            "bbox": [0, 0, 10, 10],
            "path": str(images_dir / "img1.png"),
        }
    ]
    mock_docling.save_images.return_value = image_metadata

    runner = CliRunner()
    result = runner.invoke(cli, ["process", "--source", str(source_dir), "--target", str(target_dir)])

    assert result.exit_code == 0

    meta_path = target_dir / "test" / "images" / "image_metadata.json"
    assert meta_path.exists()

    data = json.loads(meta_path.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["filename"] == "img1.png"
    assert "description" not in data[0]
    assert "embeddings" not in data[0]
    assert "faces" not in data[0]
