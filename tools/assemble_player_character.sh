#!/usr/bin/env bash
set -euo pipefail

MODEL="assets/models/player_character_lembah_sari.glb"
SOURCE_DIR="assets/models/player_stylized_boy_source"
PART_GLOB="${SOURCE_DIR}/player_stylized_boy.glb.xz.b64.part*"
EXPECTED_SHA256="261a068f706d076b93497ee24c9d1f2b369c2487d7f366fb6671d162c4aa6451"

shopt -s nullglob
PARTS=( ${PART_GLOB} )
shopt -u nullglob
if (( ${#PARTS[@]} == 0 )); then
  echo "ERROR: stylized-boy source payload is missing (${PART_GLOB})." >&2
  exit 1
fi

TMP_B64="$(mktemp)"
TMP_XZ="$(mktemp)"
TMP_GLB="$(mktemp)"
trap 'rm -f "${TMP_B64}" "${TMP_XZ}" "${TMP_GLB}"' EXIT

cat "${PARTS[@]}" > "${TMP_B64}"
base64 --decode "${TMP_B64}" > "${TMP_XZ}"
xz -dc "${TMP_XZ}" > "${TMP_GLB}"

ACTUAL_SHA256="$(sha256sum "${TMP_GLB}" | awk '{print $1}')"
if [[ "${ACTUAL_SHA256}" != "${EXPECTED_SHA256}" ]]; then
  echo "ERROR: stylized-boy SHA256 mismatch: ${ACTUAL_SHA256}" >&2
  exit 1
fi

python3 - "${TMP_GLB}" <<'PY'
import json, struct, sys
p = sys.argv[1]
data = open(p, "rb").read()
if len(data) < 500_000:
    raise SystemExit(f"character GLB unexpectedly small: {len(data)}")
magic, version, total = struct.unpack_from("<III", data, 0)
if magic != 0x46546C67 or version != 2 or total != len(data):
    raise SystemExit("invalid GLB header")
json_len, json_type = struct.unpack_from("<II", data, 12)
doc = json.loads(data[20:20 + json_len].rstrip(b" \x00"))
animations = [a.get("name", "") for a in doc.get("animations", [])]
if "walk.001" not in animations:
    raise SystemExit(f"walk.001 missing: {animations}")
if not doc.get("skins"):
    raise SystemExit("rig/skin missing")
print(f"Stylized boy source validated: bytes={len(data)} skins={len(doc.get('skins', []))} animations={animations}")
PY

mkdir -p "$(dirname "${MODEL}")"
cp "${TMP_GLB}" "${MODEL}"
test -s "${MODEL}"
echo "Stylized boy player assembled:"
ls -lh "${MODEL}"
