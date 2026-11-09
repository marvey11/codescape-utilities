from __future__ import annotations

import json
from contextlib import contextmanager, nullcontext
from importlib import import_module
from typing import TYPE_CHECKING, Self

import pytest
import requests
from typer.testing import CliRunner

from audiothek_downloader.main import (
    app,
    atomic_write_json,
    download_file,
    get_safe_filename,
    get_service_file_paths,
)

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from pytest_mock import MockerFixture

runner = CliRunner()
downloader = import_module("audiothek_downloader.main")


def _null_context(_: str) -> nullcontext[None]:
    return nullcontext(None)


def test_get_safe_filename() -> None:
    assert get_safe_filename("2026-01-02T03:04:05Z", "A title: now!") == (
        "2026-01-02_A_title_now.mp3"
    )


def test_slugify_removes_punctuation_and_normalizes_whitespace() -> None:
    assert downloader.slugify("  Héllo, world!  ") == "Héllo_world"


def test_get_safe_filename_rejects_invalid_date() -> None:
    with pytest.raises(ValueError):
        get_safe_filename("not-a-date", "Title")


def test_get_service_file_paths_creates_application_data_dir(tmp_path: Path) -> None:
    metadata_path, manifest_path = get_service_file_paths(tmp_path / "data")

    assert metadata_path == (tmp_path / "data" / "metadata.json").resolve()
    assert manifest_path == (tmp_path / "data" / "manifest.json").resolve()
    assert (tmp_path / "data").is_dir()


def test_atomic_write_json_writes_utf8_json(tmp_path: Path) -> None:
    file_path = tmp_path / "nested" / "data.json"

    atomic_write_json(file_path, {"title": "café"})

    assert file_path.read_text(encoding="utf-8") == '{\n    "title": "café"\n}'
    assert list(file_path.parent.iterdir()) == [file_path]


def test_atomic_write_json_removes_temp_file_when_replace_fails(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    file_path = tmp_path / "data.json"
    mocker.patch.object(downloader.os, "replace", side_effect=OSError("disk full"))

    with pytest.raises(OSError, match="disk full"):
        atomic_write_json(file_path, {"value": 1})

    assert not file_path.exists()
    assert list(tmp_path.iterdir()) == []


def test_download_file_writes_chunks_and_preserves_caller_session(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    session = requests.Session()
    response = requests.Response()
    response.status_code = 200
    mocker.patch.object(response, "raise_for_status")
    mocker.patch.object(response, "close")
    mocker.patch.object(
        response, "iter_content", return_value=iter([b"first", b"", b"second"])
    )
    get = mocker.patch.object(session, "get", return_value=response)
    close = mocker.spy(session, "close")
    destination = tmp_path / "nested" / "episode.mp3"

    result = download_file("https://example.test/episode", destination, session)

    assert result == destination
    assert destination.read_bytes() == b"firstsecond"
    get.assert_called_once_with(
        "https://example.test/episode", stream=True, timeout=(10, 30)
    )
    close.assert_not_called()
    session.close()


def test_download_file_closes_owned_session(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    session = requests.Session()
    response = requests.Response()
    response.status_code = 200
    mocker.patch.object(response, "raise_for_status")
    mocker.patch.object(response, "close")
    mocker.patch.object(response, "iter_content", return_value=iter([b"episode"]))
    mocker.patch.object(session, "get", return_value=response)
    close = mocker.patch.object(session, "close")
    mocker.patch.object(downloader.requests, "Session", return_value=session)
    destination = tmp_path / "episode.mp3"

    assert download_file("https://example.test/episode", destination) == destination

    close.assert_called_once_with()
    assert destination.read_bytes() == b"episode"


def test_download_file_removes_partial_file_on_request_error(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    session = requests.Session()
    response = requests.Response()
    mocker.patch.object(response, "close")
    mocker.patch.object(
        response,
        "raise_for_status",
        side_effect=requests.HTTPError("not found"),
    )
    mocker.patch.object(session, "get", return_value=response)
    destination = tmp_path / "episode.mp3"

    with pytest.raises(requests.HTTPError, match="not found"):
        download_file("https://example.test/missing", destination, session)

    assert not destination.exists()
    assert not destination.with_suffix(".tmp").exists()
    session.close()


def test_download_file_removes_partial_file_on_stream_error(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    session = requests.Session()
    response = requests.Response()
    response.status_code = 200
    mocker.patch.object(response, "raise_for_status")
    mocker.patch.object(response, "close")
    mocker.patch.object(
        response,
        "iter_content",
        side_effect=OSError("connection interrupted"),
    )
    mocker.patch.object(session, "get", return_value=response)
    destination = tmp_path / "episode.mp3"

    with pytest.raises(OSError, match="connection interrupted"):
        download_file("https://example.test/episode", destination, session)

    assert not destination.exists()
    assert not destination.with_suffix(".tmp").exists()
    session.close()


def test_string_value_and_audio_url_fallbacks() -> None:
    assert downloader._string_value("title") == "title"
    assert downloader._string_value(42, "fallback") == "fallback"
    assert downloader._audio_url(None) is None
    assert downloader._audio_url([]) is None
    assert downloader._audio_url([None]) is None
    assert downloader._audio_url([{"downloadUrl": "download"}]) == "download"
    assert downloader._audio_url([{"downloadUrl": "", "url": "fallback"}]) == (
        "fallback"
    )
    assert downloader._audio_url([{"url": 42}]) is None


def test_process_podcast_downloads_new_episodes_and_updates_manifest(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    def return_destination(
        url: str, local_path: Path, session: requests.Session | None = None
    ) -> Path:
        return local_path

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        '{"podcast-1": {"already-downloaded": {"title": "Existing"}}}',
        encoding="utf-8",
    )
    episodes = [
        {"title": "No publication ID"},
        {"publicationId": "already-downloaded"},
        {
            "publicationId": "missing-date",
            "audios": [{"url": "https://example.test/missing-date"}],
        },
        {
            "publicationId": "missing-audio",
            "publicationStartDateAndTime": "2026-02-03T04:05:06Z",
        },
        {
            "publicationId": "episode-1",
            "title": "Episode: one",
            "publicationStartDateAndTime": "2026-02-03T04:05:06Z",
            "audios": [{"downloadUrl": "https://example.test/episode-1"}],
            "synopsis": "First synopsis",
        },
        {
            "publicationId": "episode-2",
            "publicationStartDateAndTime": "2026-02-04T04:05:06Z",
            "audios": [{"url": "https://example.test/episode-2"}],
        },
    ]
    response = mocker.MagicMock()
    response.encoding = None
    response.json.return_value = {
        "data": {"programSet": {"items": {"nodes": episodes}}}
    }
    session = mocker.MagicMock()
    session.__enter__.return_value = session
    session.get.return_value = response
    mocker.patch.object(downloader.requests, "Session", return_value=session)
    mocker.patch.object(downloader, "HTTPAdapter")
    downloads = mocker.patch.object(
        downloader,
        "download_file",
        side_effect=return_destination,
    )
    download_dir = tmp_path / "podcasts" / "show"

    downloaded_count = downloader.process_podcast(
        "podcast-1", download_dir, manifest_path
    )

    assert downloaded_count == 2
    response.raise_for_status.assert_called_once_with()
    assert response.encoding == "utf-8"
    assert downloads.call_count == 2
    assert downloads.call_args_list[0].args[0] == "https://example.test/episode-1"
    assert downloads.call_args_list[1].args[0] == "https://example.test/episode-2"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["podcast-1"]["already-downloaded"]["title"] == "Existing"
    assert manifest["podcast-1"]["episode-1"]["title"] == "Episode: one"
    assert manifest["podcast-1"]["episode-1"]["synopsis"] == "First synopsis"
    assert manifest["podcast-1"]["episode-2"]["title"] == "Unknown Title"
    assert manifest["podcast-1"]["episode-2"]["synopsis"] == ""


def test_process_podcast_continues_after_download_request_error(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    episode = {
        "publicationId": "episode-1",
        "title": "Episode",
        "publicationStartDateAndTime": "2026-02-03T04:05:06Z",
        "audios": [{"url": "https://example.test/episode-1"}],
    }
    response = mocker.MagicMock()
    response.encoding = "utf-8"
    response.json.return_value = {
        "data": {"programSet": {"items": {"nodes": [episode]}}}
    }
    session = mocker.MagicMock()
    session.__enter__.return_value = session
    session.get.return_value = response
    mocker.patch.object(downloader.requests, "Session", return_value=session)
    mocker.patch.object(downloader, "HTTPAdapter")
    mocker.patch.object(
        downloader,
        "download_file",
        side_effect=requests.RequestException("network unavailable"),
    )
    manifest_path = tmp_path / "manifest.json"

    downloaded_count = downloader.process_podcast(
        "podcast-1", tmp_path / "podcasts", manifest_path
    )

    assert downloaded_count == 0
    assert not manifest_path.exists()


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


def test_cli_reports_invalid_metadata_json(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    mocker.patch("audiothek_downloader.main.telemetry_context", _null_context)
    (tmp_path / "metadata.json").write_text("{invalid", encoding="utf-8")

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
    assert "Downloader failed" in result.output


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
    def telemetry_scope(_: str) -> Generator[FakeTelemetryClient]:
        yield telemetry

    mocker.patch("audiothek_downloader.main.telemetry_context", telemetry_scope)
    monkeypatch.setenv("SERVICE_RUN_ID", "8d4b64d8-7e28-42f8-8cb8-3b4d202d3d83")

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "metadata.json").write_text("{}", encoding="utf-8")

    downloader.run(data_dir, tmp_path / "podcasts")

    assert telemetry.metrics == {
        "success_count": 0,
        "skipped_count": 0,
        "downloaded_count": 0,
    }


def test_run_counts_processed_and_skipped_podcasts(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    class FakeTelemetryClient:
        def __init__(self) -> None:
            self.metrics: dict[str, int] = {}

        def set_metric(self, key: str, value: int) -> None:
            self.metrics[key] = value

    telemetry = FakeTelemetryClient()

    @contextmanager
    def telemetry_scope(_: str) -> Generator[FakeTelemetryClient]:
        yield telemetry

    mocker.patch("audiothek_downloader.main.telemetry_context", telemetry_scope)
    process = mocker.patch(
        "audiothek_downloader.main.process_podcast", side_effect=[2, 3]
    )
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "metadata.json").write_text(
        '{"missing-target": {}, "show-1": {"target_dir": "shows/one"}, '
        '"show-2": {"target_dir": "shows/two"}}',
        encoding="utf-8",
    )

    downloader.run(data_dir, tmp_path / "podcasts")

    assert process.call_count == 2
    assert process.call_args_list[0].args == (
        "show-1",
        tmp_path / "podcasts" / "shows" / "one",
        data_dir / "manifest.json",
    )
    assert telemetry.metrics == {
        "success_count": 2,
        "skipped_count": 1,
        "downloaded_count": 5,
    }


def test_run_does_not_report_metrics_when_processing_fails(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    class FakeTelemetryClient:
        def __init__(self) -> None:
            self.metrics: dict[str, int] = {}

        def set_metric(self, key: str, value: int) -> None:
            self.metrics[key] = value

    telemetry = FakeTelemetryClient()

    @contextmanager
    def telemetry_scope(_: str) -> Generator[FakeTelemetryClient]:
        yield telemetry

    mocker.patch("audiothek_downloader.main.telemetry_context", telemetry_scope)
    mocker.patch(
        "audiothek_downloader.main.process_podcast",
        side_effect=OSError("manifest write failed"),
    )
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "metadata.json").write_text(
        '{"show": {"target_dir": "show"}}', encoding="utf-8"
    )

    with pytest.raises(OSError, match="manifest write failed"):
        downloader.run(data_dir, tmp_path / "podcasts")

    assert telemetry.metrics == {}


def test_run_without_orchestrator_run_id_skips_telemetry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("SERVICE_RUN_ID", raising=False)

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "metadata.json").write_text("{}", encoding="utf-8")

    downloader.run(data_dir, tmp_path / "podcasts")
