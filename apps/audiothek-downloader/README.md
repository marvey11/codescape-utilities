# Audiothek Podcast Downloader

Download new episodes from ARD Audiothek program sets and keep a manifest of
completed downloads.

## Usage

Install the workspace with `uv sync`, then run:

```sh
uv run --package audiothek-downloader audiothek-downloader \
	--application-data-dir /path/to/application-data \
	--podcast-storage-dir /path/to/podcasts
```

The application data directory must contain `metadata.json`. Each metadata entry
uses a podcast URN as its key and a `target_dir` value relative to the podcast
storage directory:

```json
{
	"urn:ard:podcast:example": {
		"target_dir": "Example Podcast"
	}
}
```

The downloader creates `manifest.json` in the application data directory and
records each successfully downloaded episode there. Existing manifest entries
are skipped on later runs.

## Dockerised Application

The application is now also available as a Docker build. Use the image `ghcr.io/marvey11/codescape-utilities/audiothek-downloader:latest`.

## Running as a `systemd` service

The `*.service` and `*.timer` units can be found in the `systemd` folder. Both the storage path for podcasts and the image name and tag can be configured. The service unit expects the configuration in `~/.config/codescape/audiothek-downloader/env`. An example configuration can be found under `systemd/env.example`.

A script `install-systemd.sh` is availble in the `scripts` directory. This should be executed from the **root dir** of the repository.

Further interesting `sysctl` commands:

```shell
# Reload systemd to discover the new unit files
systemctl --user daemon-reload

# Test the service execution manually once
systemctl --user start audiothek-downloader.service

# Check execution logs to verify success
journalctl --user -u audiothek-downloader.service

# Enable and start the weekly timer
systemctl --user enable --now audiothek-downloader.timer

# Check upcoming timer runs
systemctl --user list-timers

# Verify timer status
systemctl --user status audiothek-downloader.timer

# Enable lingering
#
# -> recommended; makes sure that the user-level service also runs if the user is not
# 	 currently logged in
loginctl enable-linger $USER
```
