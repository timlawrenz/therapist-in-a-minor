import pytest
import json
from pathlib import Path
from click.testing import CliRunner
from extractor.cli import cli
from unittest.mock import patch, MagicMock

def test_full_pipeline_discovery_and_scaffolding(tmp_path):
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()

    # Create mock dataset
    (source_root / "doc1.pdf").write_text("doc1 content")

    subdir = source_root / "subdir"
    subdir.mkdir()
    (subdir / "image1.png").write_text("image1 content")

    nested = subdir / "nested"
    nested.mkdir()
    (nested / "video1.mp4").write_text("video1 content")

    with patch("extractor.cli.DoclingEngine") as MockEngine:
        mock_instance = MockEngine.return_value
        mock_instance.convert.return_value = MagicMock()
        mock_instance.save_images.return_value = []

        runner = CliRunner()
        result = runner.invoke(
            cli, ["process", "--source", str(source_root), "--target", str(target_root)]
        )

    assert result.exit_code == 0

    # Verify Scaffolding
    # 1. doc1.pdf
    doc1_folder = target_root / "doc1"
    assert doc1_folder.exists()
    assert (doc1_folder / "doc1.pdf").is_symlink()
    assert (doc1_folder / "manifest.json").exists()

    # 2. image1.png
    image1_folder = target_root / "subdir" / "image1"
    assert image1_folder.exists()
    assert (image1_folder / "image1.png").is_symlink()

    # 3. video1.mp4
    video1_folder = target_root / "subdir" / "nested" / "video1"
    assert video1_folder.exists()
    assert (video1_folder / "video1.mp4").is_symlink()

    # Verify Manifest content for one file
    with open(doc1_folder / "manifest.json", "r") as f:
        data = json.load(f)
    assert data["document_id"] == "doc1"
    assert data["file_type"] == "PDF"
    assert data["source_path"] == str((source_root / "doc1.pdf").absolute())

def test_full_pipeline_extraction(tmp_path):
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    
    # Create mock PDF
    pdf_path = source_root / "test.pdf"
    pdf_path.touch()
    
    # Mock DoclingEngine to avoid actual heavy processing
    with patch("extractor.cli.DoclingEngine") as MockEngine:
        mock_instance = MockEngine.return_value
        
        # Setup mock result
        mock_result = MagicMock()
        mock_instance.convert.return_value = mock_result
        
        # Setup save_images to return list
        mock_instance.save_images.return_value = []
        
        runner = CliRunner()
        result = runner.invoke(cli, ['process', '--source', str(source_root), '--target', str(target_root)])
        
        assert result.exit_code == 0
        
        # Verify calls
        mock_instance.convert.assert_called_with(pdf_path)
        
        output_dir = target_root / "test"
        
        # Check save_markdown call
        mock_instance.save_markdown.assert_called()
        args, _ = mock_instance.save_markdown.call_args
        assert args[1] == output_dir / "test.md"
        
        # Check save_json call
        mock_instance.save_json.assert_called()
        args, _ = mock_instance.save_json.call_args
        assert args[1] == output_dir / "test.json"
        
        # Check manifest call
        mock_instance.generate_manifest.assert_called()