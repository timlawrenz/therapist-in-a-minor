import json
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from extractor.cli import cli


def test_cli_missing_arguments():
    runner = CliRunner()
    result = runner.invoke(cli, ["process"])
    assert result.exit_code != 0
    assert "Missing option '--source'" in result.output


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "process" in result.output


def test_cli_process_empty_dir(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    target_dir = tmp_path / "target"
    target_dir.mkdir()

    runner = CliRunner()
    result = runner.invoke(
        cli, ["process", "--source", str(source_dir), "--target", str(target_dir)]
    )

    assert result.exit_code == 0
    assert "Successfully processed:   0" in result.output


def test_cli_process_skips_complete_pdf(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "doc1.pdf").touch()

    target_dir = tmp_path / "target"
    doc_dir = target_dir / "doc1"
    doc_dir.mkdir(parents=True)
    (doc_dir / "manifest.json").write_text(json.dumps({"images": []}))
    (doc_dir / "doc1.md").touch()
    (doc_dir / "doc1.json").touch()

    with patch("extractor.cli.DoclingEngine") as MockEngine:
        mock_docling = MockEngine.return_value
        runner = CliRunner()
        result = runner.invoke(
            cli, ["process", "--source", str(source_dir), "--target", str(target_dir)]
        )

    assert result.exit_code == 0
    mock_docling.convert.assert_not_called()
    assert "Skipped (already exists): 1" in result.output


def test_cli_process_force_reprocesses(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    pdf_path = source_dir / "doc1.pdf"
    pdf_path.touch()

    target_dir = tmp_path / "target"
    doc_dir = target_dir / "doc1"
    doc_dir.mkdir(parents=True)
    (doc_dir / "manifest.json").write_text(json.dumps({"images": []}))
    (doc_dir / "doc1.md").touch()
    (doc_dir / "doc1.json").touch()

    with patch("extractor.cli.DoclingEngine") as MockEngine:
        mock_docling = MockEngine.return_value
        mock_docling.convert.return_value = MagicMock()
        mock_docling.save_images.return_value = []

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "process",
                "--source",
                str(source_dir),
                "--target",
                str(target_dir),
                "--force",
            ],
        )

    assert result.exit_code == 0
    mock_docling.convert.assert_called_once()


def test_cli_process_error_counts(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "test.pdf").touch()

    target_dir = tmp_path / "target"
    target_dir.mkdir()

    with patch("extractor.scaffolding.Scaffolder.write_manifest") as mock_manifest:
        mock_manifest.side_effect = Exception("Disk full")
        runner = CliRunner()
        result = runner.invoke(
            cli, ["process", "--source", str(source_dir), "--target", str(target_dir)]
        )

    assert result.exit_code == 0
    assert "Disk full" in result.output
    assert "Errors encountered:       1" in result.output
