#!/usr/bin/env bash
set -euo pipefail

OUT="assets/models/player_character_lembah_sari.glb"
mkdir -p "$(dirname "$OUT")"

python3 - <<'PY'
from pathlib import Path
import base64
import hashlib
import lzma

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

out = Path("assets/models/player_character_lembah_sari.glb")
out.write_bytes(raw)
print(f"STYLIZED_BOY_HQ_ASSEMBLED bytes={len(raw)} sha256={actual_sha} vertices=33575 texture=2048")
PY

test -s "$OUT"
echo "HQ stylized boy player GLB ready:"
ls -lh "$OUT"
