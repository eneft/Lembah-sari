#!/usr/bin/env bash
set -euo pipefail

OUT="assets/models/player_character_lembah_sari.glb"
mkdir -p "$(dirname "$OUT")"

python3 - <<'PY'
from pathlib import Path
import base64
import hashlib
import lzma
import json
import struct
import zlib

source = Path("assets/source")
parts = [source / f"player_stylized_boy_hq2048.xz.b64.part{i:02d}" for i in range(42)]
missing = [str(p) for p in parts if not p.is_file()]
if missing:
    raise SystemExit("Missing HQ stylized boy payload parts: " + ", ".join(missing))

payload = "".join(p.read_text(encoding="utf-8").strip() for p in parts)
compressed = base64.b64decode(payload, validate=True)
raw = lzma.decompress(compressed)

expected_size = 2701028
expected_sha = "4a52f92dc3569a79e7252a3bb21fc6e8d18f701cd5ef85a61e7c8a9cfce3db96"
actual_sha = hashlib.sha256(raw).hexdigest()
if len(raw) != expected_size:
    raise SystemExit(f"Unexpected HQ stylized boy GLB size: {len(raw)} != {expected_size}")
if actual_sha != expected_sha:
    raise SystemExit(f"HQ stylized boy GLB SHA256 mismatch: {actual_sha}")
if raw[:4] != b"glTF":
    raise SystemExit("Reassembled HQ player asset is not a GLB.")

# The compact HQ repack preserved the mesh/texture but its inverse-bind matrix
# buffer was corrupted. Restore the authoritative 65-bone bind matrices from
# the original Tripo/Mixamo asset before Godot imports the GLB.
ORIGINAL_IBM_ZLIB_B64 = """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"""
ibm_bytes = zlib.decompress(base64.b64decode(ORIGINAL_IBM_ZLIB_B64))
if len(ibm_bytes) != 4160 or hashlib.sha256(ibm_bytes).hexdigest() != "eff8892cba06e416ce36b4dd81819dcc7c2a030286f9e88c87bfa8ea8d523787":
    raise SystemExit("Authoritative inverse-bind matrix payload failed validation.")

patched = bytearray(raw)
_, version, total_length = struct.unpack_from("<4sII", patched, 0)
offset = 12
json_doc = None
bin_data_offset = None
while offset < total_length:
    chunk_length, chunk_type = struct.unpack_from("<II", patched, offset)
    offset += 8
    if chunk_type == 0x4E4F534A:
        json_doc = json.loads(bytes(patched[offset:offset + chunk_length]).decode("utf-8"))
    elif chunk_type == 0x004E4942:
        bin_data_offset = offset
    offset += chunk_length

if json_doc is None or bin_data_offset is None:
    raise SystemExit("HQ player GLB is missing JSON or BIN chunk.")
skin = json_doc["skins"][0]
accessor = json_doc["accessors"][skin["inverseBindMatrices"]]
buffer_view = json_doc["bufferViews"][accessor["bufferView"]]
if accessor["componentType"] != 5126 or accessor["count"] != 65 or accessor["type"] != "MAT4":
    raise SystemExit("Unexpected HQ player inverse-bind matrix accessor layout.")
if buffer_view["byteLength"] != len(ibm_bytes):
    raise SystemExit("Unexpected HQ player inverse-bind matrix buffer size.")

ibm_offset = bin_data_offset + buffer_view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
patched[ibm_offset:ibm_offset + len(ibm_bytes)] = ibm_bytes
raw = bytes(patched)

fixed_sha = hashlib.sha256(raw).hexdigest()
expected_fixed_sha = "83be93a1a04c6159f172d6719811ab314983a85174c1d3a9de8b095a18f60db4"
if fixed_sha != expected_fixed_sha:
    raise SystemExit(f"Rig-repaired HQ stylized boy SHA256 mismatch: {fixed_sha}")

out = Path("assets/models/player_character_lembah_sari.glb")
out.write_bytes(raw)
print(f"STYLIZED_BOY_RIG_BIND_REPAIRED bytes={len(raw)} sha256={fixed_sha} bones=65")
print(f"STYLIZED_BOY_HQ_ASSEMBLED bytes={len(raw)} sha256={fixed_sha} vertices=33575 texture=2048")
PY

test -s "$OUT"
echo "HQ stylized boy player GLB ready:"
ls -lh "$OUT"
