#!/usr/bin/env bash
set -euo pipefail

MODEL="assets/models/player_character_lembah_sari.glb"
SOURCE_DIR="assets/models/player_stylized_boy_source"
PART_GLOB="${SOURCE_DIR}/player_stylized_boy.glb.gz.b64.part*"

shopt -s nullglob
PARTS=( ${PART_GLOB} )
shopt -u nullglob
if (( ${#PARTS[@]} == 0 )); then
  echo "ERROR: stylized-boy source payload is missing (${PART_GLOB})." >&2
  exit 1
fi

TMP_B64="$(mktemp)"
TMP_GZ="$(mktemp)"
TMP_GLB="$(mktemp)"
trap 'rm -f "${TMP_B64}" "${TMP_GZ}" "${TMP_GLB}"' EXIT

cat "${PARTS[@]}" > "${TMP_B64}"
base64 --decode "${TMP_B64}" > "${TMP_GZ}"
gzip -dc "${TMP_GZ}" > "${TMP_GLB}"

python3 - "${TMP_GLB}" <<'PY'
import hashlib, json, struct, sys
p = sys.argv[1]
data = open(p, "rb").read()
if len(data) < 1_800_000:
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
digest = hashlib.sha256(data).hexdigest()
expected = "bbfba0e1887f5d54d061dff457bc0361d5d9191a867a2a977f457cabaeb43b99"
if digest != expected:
    raise SystemExit(f"unexpected stylized-boy SHA256: {digest}")
print(f"Stylized boy source validated: bytes={len(data)} sha256={digest} skins={len(doc.get('skins', []))} animations={animations}")
PY

mkdir -p "$(dirname "${MODEL}")"
cp "${TMP_GLB}" "${MODEL}"
test -s "${MODEL}"
echo "Stylized boy player assembled:"
ls -lh "${MODEL}"
