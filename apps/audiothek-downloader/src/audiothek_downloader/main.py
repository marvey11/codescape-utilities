#! /usr/bin/env python3

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path  # noqa: TC003
from typing import Annotated, cast

import requests
import typer
from jsonpath_ng import parse as jp_parse
from requests.adapters import HTTPAdapter
from rich.console import Console
from urllib3.util.retry import Retry

app = typer.Typer(add_completion=False)
console = Console()
error_console = Console(stderr=True)

PODCAST_TEMPLATE = "https://api.ardaudiothek.de/programsets/{podcast_urn}"
EPISODE_QUERY = jp_parse("$.data.programSet.items.nodes[*]")

type PodcastMetadata = dict[str, dict[str, str]]
type EpisodeManifest = dict[str, dict[str, dict[str, str]]]
type JSONObject = dict[str, object]

retry_strategy = Retry(
    total=5,
    connect=5,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
)


def slugify(text: str) -> str:
    """Return a filesystem-friendly version of a string."""
    return re.sub(r"[^\w\s-]", "", text).strip().replace(" ", "_")


def get_safe_filename(date_str: str, title: str) -> str:
    """Return a ``YYYY-MM-DD_Title.mp3`` filename."""
    date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    return f"{date:%Y-%m-%d}_{slugify(title)}.mp3"


def atomic_write_json(file_path: Path, data: object) -> None:
    """Write JSON atomically so an interrupted write cannot corrupt the file."""
    file_path.parent.mkdir(exist_ok=True, parents=True)
    fd, temp_path = tempfile.mkstemp(dir=file_path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        os.replace(temp_path, file_path)
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise


def download_file(
    url: str,
    local_path: Path,
    session: requests.Session | None = None,
) -> Path:
    """Download a file to ``local_path`` using an atomic temporary file."""
    local_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = local_path.with_suffix(".tmp")
    download_session = session or requests.Session()
    try:
        with download_session.get(url, stream=True, timeout=(10, 30)) as response:
            response.raise_for_status()
            with temp_path.open("wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
            temp_path.replace(local_path)
            return local_path
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise
    finally:
        if session is None:
            download_session.close()


def get_service_file_paths(application_data_dir: Path) -> tuple[Path, Path]:
    """Return metadata and manifest paths for the application data directory."""
    application_data_dir.mkdir(exist_ok=True, parents=True)
    return (
        (application_data_dir / "metadata.json").resolve(),
        (application_data_dir / "manifest.json").resolve(),
    )


def _string_value(value: object, default: str = "") -> str:
    return value if isinstance(value, str) else default


def _audio_url(value: object) -> str | None:
    if not isinstance(value, list) or not value:
        return None
    audio = value[0]
    if not isinstance(audio, dict):
        return None
    return (
        _string_value(audio.get("downloadUrl"))
        or _string_value(audio.get("url"))
        or None
    )


def process_podcast(
    podcast_urn: str,
    download_dir: Path,
    manifest_path: Path,
) -> None:
    """Fetch and download new episodes for one podcast."""
    download_dir.mkdir(exist_ok=True, parents=True)
    manifest: EpisodeManifest = {}
    if manifest_path.exists():
        with manifest_path.open(encoding="utf-8") as file:
            manifest = cast("EpisodeManifest", json.load(file))
    episodes = manifest.setdefault(podcast_urn, {})

    with requests.Session() as session:
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PodcastDownloader/1.0"
                )
            }
        )
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        response = session.get(PODCAST_TEMPLATE.format(podcast_urn=podcast_urn))
        response.raise_for_status()
        if response.encoding is None or response.encoding == "ISO-8859-1":
            response.encoding = "utf-8"

        matches = EPISODE_QUERY.find(response.json())
        for match in matches:
            episode = cast("JSONObject", match.value)
            episode_urn = _string_value(episode.get("publicationId"))
            if not episode_urn or episode_urn in episodes:
                continue

            title = _string_value(episode.get("title"), "Unknown Title")
            date_str = _string_value(episode.get("publicationStartDateAndTime"))
            audio_url = _audio_url(episode.get("audios"))
            if not date_str or not audio_url:
                continue

            destination = download_dir / get_safe_filename(date_str, title)
            console.print(f"Downloading: {destination.name}...")
            try:
                download_file(audio_url, destination, session=session)
            except requests.RequestException as error:
                error_console.print(f"Failed to download {episode_urn}: {error}")
                continue

            episodes[episode_urn] = {
                "file_path": str(destination),
                "title": title,
                "synopsis": _string_value(episode.get("synopsis")),
                "downloaded_at": datetime.now().isoformat(),
            }
            atomic_write_json(manifest_path, manifest)


def run(application_data_dir: Path, podcast_storage_dir: Path) -> None:
    """Run the downloader using explicit application and storage directories."""
    metadata_path, manifest_path = get_service_file_paths(application_data_dir)
    if not metadata_path.exists():
        raise FileNotFoundError(f"No metadata file found at {metadata_path}")

    with metadata_path.open(encoding="utf-8") as file:
        podcast_metadata = cast("PodcastMetadata", json.load(file))

    for urn, metadata in podcast_metadata.items():
        target_dir = metadata.get("target_dir")
        if not target_dir:
            error_console.print(f"Skipping {urn}: metadata has no target_dir")
            continue
        process_podcast(urn, podcast_storage_dir / target_dir, manifest_path)


@app.command()
def main(
    application_data_dir: Annotated[
        Path,
        typer.Option(
            "--application-data-dir",
            help="Directory containing metadata.json and manifest.json.",
            exists=True,
            file_okay=False,
            resolve_path=True,
        ),
    ],
    podcast_storage_dir: Annotated[
        Path,
        typer.Option(
            "--podcast-storage-dir",
            help="Base directory where podcast files are stored.",
            file_okay=False,
            resolve_path=True,
        ),
    ],
) -> None:
    """Download new Audiothek podcast episodes."""
    try:
        run(application_data_dir, podcast_storage_dir)
    except (OSError, requests.RequestException, json.JSONDecodeError) as error:
        error_console.print(f"Downloader failed: {error}")
        raise typer.Exit(code=1) from error


if __name__ == "__main__":
    app()
