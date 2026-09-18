from pathlib import Path

from audiothek_downloader.main import app, get_safe_filename, get_service_file_paths
from typer.testing import CliRunner

runner = CliRunner()


def test_get_safe_filename() -> None:
    assert get_safe_filename("2026-01-02T03:04:05Z", "A title: now!") == (
        "2026-01-02_A_title_now.mp3"
    )


def test_get_service_file_paths_creates_application_data_dir(tmp_path: Path) -> None:
    metadata_path, manifest_path = get_service_file_paths(tmp_path / "data")

    assert metadata_path == (tmp_path / "data" / "metadata.json").resolve()
    assert manifest_path == (tmp_path / "data" / "manifest.json").resolve()
    assert (tmp_path / "data").is_dir()


def test_cli_requires_explicit_directories(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "--application-data-dir",
            str(tmp_path),
            "--podcast-storage-dir",
            str(tmp_path / "podcasts"),
        ],
    )

    assert result.exit_code == 1
    assert "No metadata file found" in result.output
