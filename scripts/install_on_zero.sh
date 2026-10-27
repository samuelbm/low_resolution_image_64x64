#!/usr/bin/env bash
# Copy the system files kept in this repo to where the Pi Zero 2W reads them,
# and make the system use them. systemd and friends never read from the repo,
# so git pull alone changes nothing: run this after a pull that touched any
# file listed below. Safe to run again: it only overwrites with the same files.
#
# Usage (Pi Zero 2W, from the repo root, or with the full path from anywhere):
#   scripts/install_on_zero.sh
# Asks for the admin password (sudo): the targets belong to root.
#
# To add a file later: add a "source target" line to FILES, and the command
# that makes the system reload it at the end.
set -euo pipefail

# Work from the repo root (one level above scripts/), wherever the script is
# started from.
cd "$(dirname "$0")/.."

# Each line: file in the repo, then where it must go on the Zero.
FILES=(
  "systemd/rgbmatrix-display.service /etc/systemd/system/rgbmatrix-display.service"
)

for entry in "${FILES[@]}"; do
  read -r source target <<<"$entry"
  # install instead of cp: the copy is always root-owned and mode 644, as
  # systemd expects, whoever owns the repo file.
  sudo install -m 644 -o root -g root "$source" "$target"
  echo "installed $source -> $target"
done

# systemd reads unit files only on daemon-reload; enable is a no-op when the
# service already starts at boot; restart picks up the new unit and loop.env.
sudo systemctl daemon-reload
sudo systemctl enable rgbmatrix-display
sudo systemctl restart rgbmatrix-display
systemctl --no-pager status rgbmatrix-display
