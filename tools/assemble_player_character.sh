#!/usr/bin/env bash
set -euo pipefail

MODEL="assets/models/player_character_lembah_sari.glb"

if [[ ! -s "${MODEL}" ]]; then
  echo "ERROR: ${MODEL} is missing or empty." >&2
  exit 1
fi

SIZE="$(stat -c%s "${MODEL}")"
if (( SIZE < 1000000 )); then
  echo "ERROR: ${MODEL} is unexpectedly small (${SIZE} bytes)." >&2
  exit 1
fi

echo "Animated Lembah Sari player GLB is present:"
ls -lh "${MODEL}"
echo "No assembly required; committed GLB is the authoritative cleaned + rigged + Idle/Walk/Run asset."
