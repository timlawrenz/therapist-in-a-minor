import pytest
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
    # We expect it to fail currently because discover command logic isn't implemented, 
    # but the argument parsing should succeed (exit code might be 0 if we mock the logic, or non-zero if logic fails)
    # For now, let's just check if it accepts the arguments. 
    # Since we haven't implemented the command yet, this test will fail on import.
    # But following TDD, I write the test first.
    # I'll assert exit_code 0 assuming I'll implement a stub.
    assert result.exit_code == 0
    assert f"Discovering from {source_dir} to {target_dir}" in result.output
