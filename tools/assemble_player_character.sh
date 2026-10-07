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
parts = [source / f"player_stylized_boy_web4.xz.b64.part{i:02d}" for i in range(11)]
missing = [str(p) for p in parts if not p.is_file()]
if missing:
    raise SystemExit("Missing stylized boy payload parts: " + ", ".join(missing))

payload = "".join(p.read_text(encoding="utf-8").strip() for p in parts)
compressed = base64.b64decode(payload, validate=True)
raw = lzma.decompress(compressed)

expected_size = 207560
expected_sha = "507302c98405fbc30eac43361c6657a69eb80ae42edfd9405ef5f1a3ffd3c2f7"
actual_sha = hashlib.sha256(raw).hexdigest()
if len(raw) != expected_size:
    raise SystemExit(f"Unexpected stylized boy GLB size: {len(raw)} != {expected_size}")
if actual_sha != expected_sha:
    raise SystemExit(f"Stylized boy GLB SHA256 mismatch: {actual_sha}")
if raw[:4] != b"glTF":
    raise SystemExit("Reassembled player asset is not a GLB.")

out = Path("assets/models/player_character_lembah_sari.glb")
out.write_bytes(raw)
print(f"STYLIZED_BOY_ASSEMBLED bytes={len(raw)} sha256={actual_sha}")
PY

test -s "$OUT"
echo "Stylized boy player GLB ready:"
ls -lh "$OUT"
