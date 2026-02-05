import pytest
import json
from unittest.mock import MagicMock, patch
from pathlib import Path
from click.testing import CliRunner
from extractor.cli import cli

@patch("extractor.cli.EnrichmentEngine")
@patch("extractor.cli.DoclingEngine")
@patch("extractor.cli.Scanner")
def test_extract_command_skips_processed(MockScanner, MockDoclingEngine, MockEnrichmentEngine, tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "doc1.pdf").touch()
    
    target_dir = tmp_path / "target"
    doc_dir = target_dir / "doc1"
    doc_dir.mkdir(parents=True)
    
    # Create complete processing artifacts
    (doc_dir / "manifest.json").write_text(json.dumps({"images": []}))
    (doc_dir / "doc1.md").touch()
    (doc_dir / "doc1.json").touch()
    
    # Mock Scanner
    mock_scanner = MockScanner.return_value
    mock_scanner.scan.return_value = [source_dir / "doc1.pdf"]
    
    # Mock DoclingEngine
    mock_docling = MockDoclingEngine.return_value
    
    runner = CliRunner()
    result = runner.invoke(cli, ['extract', '--source', str(source_dir), '--target', str(target_dir)])
    
    assert result.exit_code == 0
    # Should NOT have called convert
    mock_docling.convert.assert_not_called()
    # Check log output (might need caplog if using logging module, but click.echo might be used)
    # The spec says "message should be logged at INFO level". 
    # Current CLI uses logger.debug for skips in discover. 
    # We should check logs.
    
@patch("extractor.cli.EnrichmentEngine")
@patch("extractor.cli.DoclingEngine")
@patch("extractor.cli.Scanner")
def test_extract_command_force_reprocesses(MockScanner, MockDoclingEngine, MockEnrichmentEngine, tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "doc1.pdf").touch()
    
    target_dir = tmp_path / "target"
    doc_dir = target_dir / "doc1"
    doc_dir.mkdir(parents=True)
    
    # Create artifacts
    (doc_dir / "manifest.json").write_text(json.dumps({"images": []}))
    (doc_dir / "doc1.md").touch()
    (doc_dir / "doc1.json").touch()
    
    mock_scanner = MockScanner.return_value
    mock_scanner.scan.return_value = [source_dir / "doc1.pdf"]
    
    mock_docling = MockDoclingEngine.return_value
    mock_docling.convert.return_value = MagicMock()
    mock_docling.save_images.return_value = []
    
    runner = CliRunner()
    # Pass --force
    result = runner.invoke(cli, ['extract', '--source', str(source_dir), '--target', str(target_dir), '--force'])
    
    assert result.exit_code == 0
    # Should HAVE called convert
    mock_docling.convert.assert_called_once()
