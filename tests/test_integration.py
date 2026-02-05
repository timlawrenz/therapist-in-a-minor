import pytest
import json
from pathlib import Path
from click.testing import CliRunner
from extractor.cli import cli

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
    
    # Run CLI
    runner = CliRunner()
    result = runner.invoke(cli, ['discover', '--source', str(source_root), '--target', str(target_root)])
    
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
