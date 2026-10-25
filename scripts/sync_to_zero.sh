#!/usr/bin/env bash
# Copy object_files/ (prepared images, GIFs, ...) from the host to the Pi Zero 2W,
# keeping the folder structure. These files are git-ignored (D-011), so
# git pull on the Zero does not bring them.
#
# Usage (host, from the repo root, or with the full path from anywhere):
#   scripts/sync_to_zero.sh             copy new and changed files
#   scripts/sync_to_zero.sh --dry-run   only list what would be copied
#   scripts/sync_to_zero.sh --delete    also remove files on the Zero that were
#                                       deleted on the host (check with --dry-run first)
# Any other rsync option is passed through as well.
set -euo pipefail

ZERO="${ZERO:-admin@rgbmatrix.local}"
# Relative to the Zero user's home: where the repo was cloned.
REMOTE_DIR="${REMOTE_DIR:-low_resolution_image_64x64}"

# Work from the repo root (one level above scripts/), wherever the script is
# started from.
cd "$(dirname "$0")/.."

# Trailing slashes: copy the contents of object_files/ into object_files/ on
# the Zero, instead of nesting a second object_files/ inside it.
rsync -av "$@" object_files/ "$ZERO:$REMOTE_DIR/object_files/"
