#!/usr/bin/env bash
set -euo pipefail
OUT="assets/models/player_character_lembah_sari.glb"
mkdir -p "$(dirname "$OUT")"
python3 - <<'PY'
from pathlib import Path
import base64, hashlib, json, lzma, struct
source=Path("assets/source")
parts=[source/f"player_stylized_boy_clean2048.xz.b64.part{i:02d}" for i in range(31)]
missing=[str(p) for p in parts if not p.is_file()]
if missing: raise SystemExit("Missing clean stylized boy payload parts: "+", ".join(missing))
payload="".join(p.read_text().strip() for p in parts)
raw=lzma.decompress(base64.b64decode(payload,validate=True))
expected_size=2701020
expected_sha="c61b4738e49b03b541e553a8e397cda550a1953224fd09b365816ef02db16ac0"
actual=hashlib.sha256(raw).hexdigest()
if len(raw)!=expected_size: raise SystemExit(f"Unexpected GLB size: {len(raw)}")
if actual!=expected_sha: raise SystemExit(f"Clean GLB SHA mismatch: {actual}")
if raw[:4]!=b"glTF": raise SystemExit("Not a GLB")
_,version,total=struct.unpack_from("<4sII",raw,0)
if version!=2 or total!=len(raw): raise SystemExit("Invalid GLB header")
o=12; doc=None
while o<total:
    n,t=struct.unpack_from("<II",raw,o); o+=8
    if t==0x4E4F534A:
        doc=json.loads(raw[o:o+n].decode("utf-8")); break
    o+=n
if doc is None: raise SystemExit("Missing GLB JSON")
prim=doc["meshes"][0]["primitives"][0]
pos=doc["accessors"][prim["attributes"]["POSITION"]]
skin=doc["skins"][0]
anims=[a.get("name","") for a in doc.get("animations",[])]
if pos["count"]!=33575: raise SystemExit(f"Unexpected vertex count: {pos['count']}")
if len(skin.get("joints",[]))!=65: raise SystemExit(f"Unexpected joint count: {len(skin.get('joints',[]))}")
if "walk.001" not in anims: raise SystemExit(f"walk.001 missing: {anims}")
Path(OUT if False else "assets/models/player_character_lembah_sari.glb").write_bytes(raw)
print(f"STYLIZED_BOY_CLEAN_ASSEMBLED bytes={len(raw)} sha256={actual} vertices=33575 bones=65 texture=2048 animation=walk.001")
PY
test -s "$OUT"
ls -lh "$OUT"
