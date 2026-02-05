import pytest
from pathlib import Path
from unittest.mock import patch
from click.testing import CliRunner
from extractor.cli import cli

def test_cli_missing_arguments():
    runner = CliRunner()
    result = runner.invoke(cli, ['discover'])
    assert result.exit_code != 0
    assert "Missing option '--source'" in result.output or "Missing option '--target'" in result.output

def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert "Usage:" in result.output

def test_cli_discover_arguments(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    
    runner = CliRunner()
    result = runner.invoke(cli, ['discover', '--source', str(source_dir), '--target', str(target_dir)])
    assert result.exit_code == 0
    assert f"Discovering from {source_dir} to {target_dir}" in result.output

def test_cli_nonexistent_source(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ['discover', '--source', 'nonexistent_path', '--target', str(tmp_path)])
    assert result.exit_code != 0
    assert "does not exist" in result.output

def test_cli_source_is_file(tmp_path):
    test_file = tmp_path / "file.txt"
    test_file.touch()
    runner = CliRunner()
    result = runner.invoke(cli, ['discover', '--source', str(test_file), '--target', str(tmp_path)])
    assert result.exit_code != 0
    assert "is a file" in result.output

def test_cli_error_during_processing(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "test.pdf").touch()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    
    with patch("extractor.scaffolding.Scaffolder.create_scaffold") as mock_scaffold:
        mock_scaffold.side_effect = Exception("Disk full")
        runner = CliRunner()
        result = runner.invoke(cli, ['discover', '--source', str(source_dir), '--target', str(target_dir)])
        
        assert result.exit_code == 0
        assert "Error processing" in result.output
        assert "Disk full" in result.output
        assert "Errors encountered:       1" in result.output

def test_cli_skips_existing_manifest(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "test.pdf").touch()
    
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    
    # Pre-create target manifest
    doc_target = target_dir / "test"
    doc_target.mkdir()
    (doc_target / "manifest.json").touch()
    
    runner = CliRunner()
    result = runner.invoke(cli, ['discover', '--source', str(source_dir), '--target', str(target_dir)])
    
    assert result.exit_code == 0
    assert "Skipped (already exists): 1" in result.output
    assert "Successfully processed:   0" in result.output

def test_cli_force_overwrites_existing_manifest(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "test.pdf").touch()
    
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    
    # Pre-create target manifest
    doc_target = target_dir / "test"
    doc_target.mkdir()
    (doc_target / "manifest.json").write_text("old")
    
    runner = CliRunner()
    # Run with --force
    result = runner.invoke(cli, ['discover', '--source', str(source_dir), '--target', str(target_dir), '--force'])
    
    assert result.exit_code == 0
    assert "Successfully processed:   1" in result.output
    assert "Skipped (already exists): 0" in result.output
    # Verify it was overwritten (manifest.json should now be JSON from write_manifest, not "old")
    assert (doc_target / "manifest.json").read_text() != "old"