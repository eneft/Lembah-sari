# Lembah Sari

Prototype cozy farming/life-sim tropis Indonesia, dibangun dengan Godot 4.

## Version 0.0.1

Milestone pertama berfokus pada rasa dasar dunia dan kontrol:

- world 3D stylized sederhana
- kamera 3/4 fixed-follow
- player movement + collision
- layout awal rumah dan kebun pemain
- jalan desa
- Warung Bu Ratih
- sungai + jembatan
- sawah Pak Wiryo + saluran irigasi
- kontrol keyboard
- virtual joystick mobile + action button
- renderer GL Compatibility untuk fondasi iOS/mobile

## Menjalankan

1. Install Godot 4.3+.
2. Buka `project.godot` dari Godot Project Manager.
3. Tekan **F6/F5** untuk menjalankan project.

### Kontrol desktop

- WASD / arrow keys: bergerak
- Shift: lari
- E / Space: interaksi (fondasi untuk sistem berikutnya)

### Mobile

UI prototype menyediakan joystick kiri dan tombol aksi kanan. Build iOS final membutuhkan macOS + Xcode dan signing Apple.

## Struktur

```text
scenes/
  Main.tscn
  Player.tscn
scripts/
  player.gd
  world_builder.gd
  mobile_joystick.gd
  mobile_controls.gd
ui/
  MobileControls.tscn
assets/
data/
```

## Roadmap terdekat

- 0.0.2: farming grid, hoe, seed, watering, crop state
- 0.0.3: game time + sunrise/night + weather
- 0.0.4: NPC schedule/dialog (Pak Wiryo, Bu Ratih, Laras)
- 0.0.5: irrigation + fishing + inventory/selling
- 0.1.0: satu hari playable end-to-end + save persistence
