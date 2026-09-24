# Lembah Sari

Prototype cozy farming/life-sim tropis Indonesia, dibangun dengan Godot 4.

## Version 0.0.4

Milestone ini menambahkan NPC hidup dan dialog di atas farming + waktu/cuaca:

- world 3D stylized + kamera 3/4
- movement + collision
- farming 20 petak: Cangkul → Benih → Siram → Panen
- jam game berjalan otomatis mulai 06:30
- periode Pagi → Siang → Sore → Malam
- cuaca Cerah / Hujan + hujan menyiram tanaman
- NPC pertama: **Pak Wiryo, Bu Ratih, Laras**
- NPC berpindah lokasi mengikuti jadwal harian
- nama NPC tampil di atas karakter
- dialog pembuka khusus saat pertama kali berbicara
- dialog berikutnya berubah berdasarkan waktu dan cuaca
- player berhenti saat panel dialog terbuka
- **E / Space / AKSI** memprioritaskan bicara jika NPC berada dekat pemain

## Menjalankan di PC

1. Buka GitHub Desktop.
2. **Fetch origin → Pull origin** pada repository `eneft/Lembah-sari`.
3. Buka `project.godot` dari Godot Project Manager.
4. Tekan **F6/F5** atau tombol Play.
5. Pastikan kiri atas tertulis **Lembah Sari 0.0.4**.

### Kontrol desktop

- WASD / arrow keys: bergerak
- Shift: lari
- E / Space: interaksi / gunakan alat
- 1: Cangkul
- 2: Benih
- 3: Siram
- 4: Panen
- tombol HUD **+ HARI**: lompat ke pagi hari berikutnya

### Tes NPC

Saat game mulai sekitar 06:30:

- **Pak Wiryo** berada di area sawah bagian utara.
- **Bu Ratih** berada di Warung Bu Ratih di sisi kiri jalan desa.
- **Laras** berada dekat sungai/jembatan.

Cara tes:

1. Jalan mendekati salah satu NPC sampai berjarak sekitar 1–2 meter.
2. Hadapkan karakter ke NPC.
3. Tekan **E**, **Space**, atau tombol **AKSI**.
4. Panel dialog akan muncul dan player berhenti bergerak.
5. Tekan **TUTUP** atau **AKSI/E** lagi untuk menutup dialog.
6. Bicara lagi untuk mendapatkan dialog kontekstual berdasarkan waktu/cuaca.
7. Biarkan jam berjalan atau gunakan **+ HARI** untuk melihat NPC berpindah jadwal.

### Jadwal prototype

**Pak Wiryo**
- pagi: sawah
- siang: pintu irigasi
- sore: area warung
- malam: pulang

**Bu Ratih**
- pagi–sore: warung
- malam: pulang

**Laras**
- pagi: sungai
- siang: jalan desa
- sore: area warung
- malam: pulang

## Tes farming + waktu/cuaca

1. Jalan ke kebun dekat rumah.
2. Arahkan karakter ke petak sampai muncul bingkai kuning.
3. Cangkul → tanam Benih → Siram.
4. Perhatikan jam berjalan dan warna dunia berubah menuju sore/malam.
5. Gunakan **+ HARI** untuk mempercepat pertumbuhan tanaman.
6. Jika Hujan, tanaman yang sudah ditanam otomatis menjadi tersiram.
7. Setelah tiga pertumbuhan, pilih Panen lalu gunakan aksi.

## Menjalankan di iPhone/iPad dengan Xogot

1. Update/download project dari GitHub di Xogot.
2. Buka `project.godot`.
3. Tekan Play.
4. Pastikan HUD menunjukkan **Lembah Sari 0.0.4**.

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
  npc_manager.gd
  mobile_joystick.gd
  mobile_controls.gd
ui/
  MobileControls.tscn
```

## Roadmap terdekat

- 0.0.5: irrigation interaktif + fishing + inventory/selling
- 0.0.6: rumah, tidur, transisi hari, stamina dasar
- 0.1.0: satu hari playable end-to-end + save persistence
