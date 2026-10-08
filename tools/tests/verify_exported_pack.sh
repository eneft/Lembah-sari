#!/usr/bin/env bash
set -euo pipefail
PACK_PATH="$(realpath "${1:?Pass the exported PCK}")"
GODOT_BIN="$(command -v godot)"
ISOLATED_DIR="$(mktemp -d)"
# No source project or import cache may satisfy missing exported resources.
cd "${ISOLATED_DIR}"
for CHECK in verify_player_house verify_player_locomotion verify_hybrid_environment verify_foreground_plants verify_volumetric_grass verify_grounded_landscape; do
  timeout 40s "${GODOT_BIN}" --headless --path "${ISOLATED_DIR}" --main-pack "${PACK_PATH}" --fixed-fps 60 --script "res://tools/tests/${CHECK}.gd"
done
rmdir "${ISOLATED_DIR}"
echo 'ISOLATED_EXPORTED_PACK_VALIDATED source_fallback=false'
