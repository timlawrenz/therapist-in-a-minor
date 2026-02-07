import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from click.testing import CliRunner
from extractor.cli import cli
import json

@patch("extractor.cli.DoclingEngine")
@patch("extractor.cli.Scanner")
def test_full_pipeline_resume(MockScanner, MockDocling, tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "doc1.pdf").touch()
    target_dir = tmp_path / "target"
    
    # Mock Scanner
    mock_scanner = MockScanner.return_value
    mock_scanner.scan.side_effect = [[source_dir / "doc1.pdf"], [source_dir / "doc1.pdf"]] # Called twice
    
    # Mock Docling
    mock_docling_instance = MockDocling.return_value
    mock_docling_instance.convert.return_value = MagicMock()
    
    # First run: should extract
    # We need to simulate save_images creating files so next run sees them
    def side_effect_save_images(result, images_dir):
        images_dir.mkdir(parents=True, exist_ok=True)
        # Create image file
        (images_dir / "img1.png").touch()
        
        return [{"filename": "img1.png", "path": str(images_dir / "img1.png")}]

    mock_docling_instance.save_images.side_effect = side_effect_save_images    
    def side_effect_save_markdown(result, output_path):
        with open(output_path, "w") as f: f.write("md")
        
    def side_effect_save_json(result, output_path):
        with open(output_path, "w") as f: f.write("{}")
        
    mock_docling_instance.save_markdown.side_effect = side_effect_save_markdown
    mock_docling_instance.save_json.side_effect = side_effect_save_json
    
    # Mock generate_manifest to actually write the file
    def side_effect_generate_manifest(result, output_path, image_metadata):
        with open(output_path, "w") as f:
            json.dump({"images": image_metadata}, f)
            
    mock_docling_instance.generate_manifest.side_effect = side_effect_generate_manifest
    
    runner = CliRunner()
    
    # Run 1
    result1 = runner.invoke(cli, ['process', '--source', str(source_dir), '--target', str(target_dir)])
    
    if result1.exit_code != 0:
        print(result1.output)
        print(result1.exception)
        
    assert result1.exit_code == 0
    assert "Successfully processed:   1" in result1.output
    
    # Verify files created
    doc_dir = target_dir / "doc1"
    assert (doc_dir / "manifest.json").exists()
    assert (doc_dir / "doc1.md").exists()
    assert (doc_dir / "doc1.json").exists()
    assert (doc_dir / "images" / "image_metadata.json").exists()
    assert (doc_dir / "images" / "img1.png").exists()
    
    # Check manifest content
    with open(doc_dir / "manifest.json") as f:
        m = json.load(f)
    assert len(m["images"]) == 1
    assert m["images"][0]["filename"] == "img1.png"
    
    # Run 2
    result2 = runner.invoke(cli, ['process', '--source', str(source_dir), '--target', str(target_dir)])
    
    if result2.exit_code != 0:
        print(result2.output)
        
    assert result2.exit_code == 0
    # assert "Skipping already processed" in result2.output # Logging might not be captured by CliRunner
    assert "Skipped (already exists): 1" in result2.output
    assert "Successfully processed:   0" in result2.output
