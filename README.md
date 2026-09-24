# Lembah Sari

Prototype cozy farming/life-sim tropis Indonesia, dibangun dengan Godot 4.

## Version 0.0.3

Milestone ini menambahkan waktu dunia dan cuaca di atas farming 0.0.2:

- world 3D stylized + kamera 3/4
- movement + collision
- farming 20 petak: Cangkul → Benih → Siram → Panen
- jam game berjalan otomatis mulai 06:30
- satu hari playable sekitar 15 menit real-time
- periode Pagi → Siang → Sore → Malam
- warna langit, ambient light, dan matahari berubah sepanjang hari
- cuaca Cerah / Hujan
- visual hujan sederhana di sekitar pemain
- hari hujan otomatis menyiram tanaman yang sudah ditanam
- HUD menampilkan Hari, hasil panen, jam, periode, dan cuaca
- tombol **+ HARI** tetap tersedia untuk mempercepat testing
- joystick touch tetap kompatibel dengan Xogot/iPhone

## Menjalankan di PC

1. Clone/pull repository `eneft/Lembah-sari` dengan GitHub Desktop.
2. Buka `project.godot` dari Godot Project Manager.
3. Tekan **F6/F5** atau tombol Play.
4. Pastikan kiri atas tertulis **Lembah Sari 0.0.3**.

### Kontrol desktop

- WASD / arrow keys: bergerak
- Shift: lari
- E / Space: gunakan alat
- 1: Cangkul
- 2: Benih
- 3: Siram
- 4: Panen
- tombol HUD **+ HARI**: lompat ke pagi hari berikutnya

### Tes farming + waktu/cuaca

1. Jalan ke kebun dekat rumah.
2. Arahkan karakter ke petak sampai muncul bingkai kuning.
3. Cangkul → tanam Benih → Siram.
4. Perhatikan jam berjalan dari 06:30 dan warna dunia berubah menuju sore/malam.
5. Gunakan **+ HARI** untuk mempercepat pertumbuhan tanaman.
6. Saat hari baru berganti, cuaca dipilih ulang (Cerah/Hujan).
7. Jika Hujan, tanaman yang sudah ditanam otomatis menjadi tersiram.
8. Setelah tiga pertumbuhan, pilih Panen lalu gunakan aksi.

## Menjalankan di iPhone/iPad dengan Xogot

1. Update/download project dari GitHub di Xogot.
2. Buka `project.godot`.
3. Tekan Play.
4. Pastikan HUD menunjukkan **Lembah Sari 0.0.3**.

## Struktur

```text
scenes/
  Main.tscn
  Player.tscn
scripts/
  player.gd
  world_builder.gd
  farm_manager.gd
  game_time_manager.gd
  mobile_joystick.gd
  mobile_controls.gd
ui/
  MobileControls.tscn
```

## Roadmap terdekat

- 0.0.4: NPC schedule/dialog (Pak Wiryo, Bu Ratih, Laras)
- 0.0.5: irrigation interaktif + fishing + inventory/selling
- 0.1.0: satu hari playable end-to-end + save persistence
