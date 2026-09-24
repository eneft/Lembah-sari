# Lembah Sari

Prototype cozy farming/life-sim tropis Indonesia, dibangun dengan Godot 4.

## Version 0.0.2

Milestone ini sudah playable di area kebun:

- world 3D stylized + kamera 3/4
- movement + collision
- joystick touch yang kompatibel dengan Xogot/iPhone
- 20 petak kebun interaktif
- target/highlight petak yang sedang diarahkan pemain
- Cangkul → Benih Cabai → Siram → Ganti Hari → Panen
- tiga tahap pertumbuhan cabai + buah merah saat matang
- tanah berubah visual saat dicangkul dan disiram
- counter hari dan total cabai panen
- quickbar farming mobile
- feedback aksi langsung di HUD

## Menjalankan di iPhone/iPad dengan Xogot

1. Download/update project `eneft/Lembah-sari` dari GitHub di Xogot.
2. Buka `project.godot`.
3. Tekan **Play**.
4. Pastikan kiri atas tertulis **Lembah Sari 0.0.2**.

### Cara tes farming di mobile

1. Gerakkan karakter dengan joystick kiri ke kebun di dekat rumah.
2. Arahkan karakter ke salah satu petak sampai muncul bingkai kuning.
3. Pilih **Cangkul**, lalu tekan **AKSI**.
4. Pilih **Benih**, tekan **AKSI**.
5. Pilih **Siram**, tekan **AKSI**.
6. Tekan **+ HARI** untuk maju satu hari.
7. Siram lagi lalu maju hari sampai cabai matang (3 pertumbuhan).
8. Pilih **Panen**, lalu tekan **AKSI**.

Tanaman hanya bertumbuh pada pergantian hari jika sudah disiram.

## Desktop

- WASD / arrow keys: bergerak
- Shift: lari
- E / Space: gunakan alat
- 1: Cangkul
- 2: Benih
- 3: Siram
- 4: Panen

## Struktur

```text
scenes/
  Main.tscn
  Player.tscn
scripts/
  player.gd
  world_builder.gd
  farm_manager.gd
  mobile_joystick.gd
  mobile_controls.gd
ui/
  MobileControls.tscn
```

## Roadmap terdekat

- 0.0.3: game time + sunrise/night + weather
- 0.0.4: NPC schedule/dialog (Pak Wiryo, Bu Ratih, Laras)
- 0.0.5: irrigation interaktif + fishing + inventory/selling
- 0.1.0: satu hari playable end-to-end + save persistence
