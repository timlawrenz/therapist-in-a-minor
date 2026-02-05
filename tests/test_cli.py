import pytest
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
        assert "Errors encountered:     1" in result.output