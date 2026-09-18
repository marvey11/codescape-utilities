#! /usr/bin/env bash

set -euo pipefail

mkdir -p ~/.config/systemd/user/

# Symlink unit files so updates in the repository are reflected automatically
ln -s "$(pwd)/apps/audiothek-downloader/systemd/audiothek-downloader.service" ~/.config/systemd/user/
ln -s "$(pwd)/apps/audiothek-downloader/systemd/audiothek-downloader.timer" ~/.config/systemd/user/

systemctl --user daemon-reload
systemctl --user enable --now audiothek-downloader.timer
