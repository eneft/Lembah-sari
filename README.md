# Lembah Sari

Prototype cozy farming/life-sim tropis Indonesia, dibangun dengan Godot 4.

## Version 0.0.6

Milestone ini mulai membentuk loop harian yang utuh:

- world 3D stylized + kamera 3/4
- movement + collision
- farming: Cangkul → Benih → Siram → Panen
- waktu Pagi → Siang → Sore → Malam
- cuaca Cerah / Hujan
- NPC Pak Wiryo, Bu Ratih, dan Laras + jadwal/dialog
- irigasi interaktif
- memancing di sungai
- inventory hasil panen dan ikan
- jual hasil di Warung Bu Ratih
- uang Rupiah
- stamina maksimum 100
- farming, irigasi, mancing, dan lari menguras stamina
- rumah menjadi titik tidur
- tidur normal setelah pukul 18:00
- jika stamina kritis (15 atau kurang), pemain boleh tidur lebih awal
- tidur memulai hari berikutnya dan memulihkan stamina penuh
- transisi layar **Hari Baru** saat tidur

## Menjalankan di PC

1. Buka GitHub Desktop.
2. Pada repository `eneft/Lembah-sari`, pilih **Fetch origin → Pull origin**.
3. Buka `project.godot` di Godot.
4. Tekan **F5 / Run Project**.
5. Pastikan HUD menampilkan **Lembah Sari 0.0.6**.

### Kontrol desktop

- WASD / Arrow Keys: bergerak
- Shift: lari (menguras stamina)
- E / Space: interaksi / gunakan alat
- 1: Cangkul
- 2: Benih
- 3: Siram
- 4: Panen
- 5: Pancing
- 6: Jual
- **+ HARI** pada HUD tetap tersedia sebagai tombol testing cepat

## Biaya stamina prototype

- Cangkul: 5
- Tanam benih: 2
- Siram: 3
- Panen: 2
- Irigasi: 8
- Mancing: 6
- Lari: berkurang terus selama Shift ditekan saat bergerak

Jika stamina habis, pemain tetap dapat berjalan tetapi tidak dapat melakukan aktivitas yang membutuhkan tenaga sampai stamina pulih.

## Tes loop 0.0.6

1. Mulai pagi pukul 06:30 dengan stamina 100/100.
2. Jalan ke kebun dan Cangkul → Benih → Siram beberapa petak.
3. Perhatikan bar stamina berkurang.
4. Tahan Shift sambil berjalan untuk memastikan lari menguras stamina.
5. Coba irigasi atau memancing untuk mengurangi stamina lagi.
6. Setelah pukul 18:00, pulang ke rumah pemain di sisi kanan bawah map.
7. Dekati marker **Rumah • Tidur setelah 18:00** di depan rumah.
8. Tekan **E / Space / AKSI**.
9. Layar **Hari Baru** muncul.
10. Pemain bangun kembali di depan rumah, waktu menjadi 06:30, tanaman diproses ke hari berikutnya, cuaca baru dipilih, dan stamina kembali 100/100.

Jika stamina sudah 15 atau kurang sebelum pukul 18:00, rumah mengizinkan tidur lebih awal.

## Aktivitas lain

### NPC

- Pak Wiryo: pagi di sawah
- Bu Ratih: pagi–sore di warung
- Laras: pagi di area sungai

Dekati NPC, hadapkan karakter, lalu tekan **E / Space / AKSI**.

### Irigasi

Pergi ke pintu irigasi dekat sawah Pak Wiryo. Tekan **E / AKSI**. Semua tanaman aktif akan tersiram sekaligus. Irigasi normal hanya perlu digunakan sekali per hari.

### Mancing

Pilih **Pancing (5)**, cari label **Spot Mancing** di tepi sungai, lalu tekan **E / AKSI**. Ikan Wader, Lele, atau Nila akan masuk ke tas.

### Jual hasil

Pilih **Jual (6)**, datang ke marker di depan Warung Bu Ratih, lalu tekan **E / AKSI**. Semua cabai dan ikan di tas dijual menjadi Rupiah.

## Struktur utama

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
  inventory_manager.gd
  activity_manager.gd
  player_stats_manager.gd
  mobile_joystick.gd
  mobile_controls.gd
ui/
  MobileControls.tscn
```

## Roadmap berikutnya

- 0.0.7: save/load persistence untuk hari, waktu, cuaca, stamina, uang, inventory, dan kebun
- 0.0.8: tutorial Day 1 + objective sederhana
- 0.1.0: satu hari playable end-to-end yang dapat ditutup dan dilanjutkan kembali
