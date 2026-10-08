# Foreground GLB plants — Lembah Sari

Unggah **keempat** GLB hasil pemisahan aset pengguna ke folder ini pada branch `visual/rebuild-vs01-v2`:

- `01_Pohon_Rindang_Besar.glb`
- `02_Semak_Rimbun.glb`
- `03_Palem_Lengkung.glb`
- `04_Rumput_Tinggi.glb`

Scene loader `scripts/village_foreground_plants.gd` hanya mengaktifkan 11 instance 3D yang terseleksi jika keempat file lengkap. Jika belum lengkap, card/image hybrid lama tetap dipakai. Jangan pindahkan vegetasi background ke geometri.

Smoke test: `tools/tests/verify_foreground_plants.gd`; isolated Web PCK also validates the scene via `tools/tests/verify_exported_pack.sh`.
