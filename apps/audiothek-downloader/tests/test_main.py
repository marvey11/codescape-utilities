from collections.abc import Generator
from contextlib import contextmanager, nullcontext
from importlib import import_module
from pathlib import Path
from typing import Self

import pytest
from audiothek_downloader.main import app, get_safe_filename, get_service_file_paths
from pytest_mock import MockerFixture
from typer.testing import CliRunner

runner = CliRunner()
downloader = import_module("audiothek_downloader.main")


def _null_context(_: str) -> nullcontext[None]:
    return nullcontext(None)


def test_get_safe_filename() -> None:
    assert get_safe_filename("2026-01-02T03:04:05Z", "A title: now!") == (
        "2026-01-02_A_title_now.mp3"
    )


def test_get_service_file_paths_creates_application_data_dir(tmp_path: Path) -> None:
    metadata_path, manifest_path = get_service_file_paths(tmp_path / "data")

    assert metadata_path == (tmp_path / "data" / "metadata.json").resolve()
    assert manifest_path == (tmp_path / "data" / "manifest.json").resolve()
    assert (tmp_path / "data").is_dir()


def test_cli_requires_explicit_directories(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    mocker.patch("audiothek_downloader.main.telemetry_context", _null_context)

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


def test_run_reports_metrics_with_orchestrator_run_id(
    monkeypatch: pytest.MonkeyPatch,
    mocker: MockerFixture,
    tmp_path: Path,
) -> None:
    class FakeTelemetryClient:
        def __init__(self, service_name: str) -> None:
            assert service_name == downloader.SERVICE_NAME
            self.metrics: dict[str, int] = {}

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def set_metric(self, key: str, value: int) -> None:
            self.metrics[key] = value

    telemetry = FakeTelemetryClient(downloader.SERVICE_NAME)

    @contextmanager
    def telemetry_scope(_: str) -> Generator[FakeTelemetryClient, None, None]:
        yield telemetry

    mocker.patch("audiothek_downloader.main.telemetry_context", telemetry_scope)
    monkeypatch.setenv("SERVICE_RUN_ID", "8d4b64d8-7e28-42f8-8cb8-3b4d202d3d83")

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "metadata.json").write_text("{}", encoding="utf-8")

    downloader.run(data_dir, tmp_path / "podcasts")

    assert telemetry.metrics == {"success_count": 0, "skipped_count": 0}


def test_run_without_orchestrator_run_id_skips_telemetry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("SERVICE_RUN_ID", raising=False)

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "metadata.json").write_text("{}", encoding="utf-8")

    downloader.run(data_dir, tmp_path / "podcasts")
