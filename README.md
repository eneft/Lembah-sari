# Lembah Sari

Prototype cozy farming/life-sim tropis Indonesia, dibangun dengan Godot 4.

## Version 0.0.7 — Visual Overhaul

Milestone 0.0.7 membekukan penambahan fitur baru sementara dan fokus membentuk identitas visual **Lembah Sari**.

### Visual world baru

- lingkungan desa tropis dibuat lebih berlapis, tidak lagi sekadar bidang hijau datar
- jalan desa memiliki tepi dan pemisahan area yang lebih jelas
- sungai dibuat sebagai channel dengan dasar, tepian tanah, rumput pinggir air, batu, dan jembatan kayu berplank
- rumah pemain dibuat menjadi rumah desa tropis dengan teras, atap miring, jendela, kusen, tiang teras, halaman, dan bunga
- Warung Bu Ratih mendapat kanopi, bukaan warung, counter, bangku, tiang, tanaman, dan signage
- sawah Pak Wiryo sekarang terdiri dari petak sawah berair, lumpur, pematang, rumpun padi, dan saluran irigasi
- vegetasi lebih beragam: pohon rindang, kelapa, pisang, semak, bunga liar, batu, pagar, dan lampu jalan desa
- bukit stylized ditambahkan di sisi utara untuk memberikan rasa lembah dan depth pada background
- signage desa **Lembah Sari** ditambahkan pada area jalan utama

### Character visual

- player tidak lagi berupa capsule sederhana
- player sekarang memiliki torso, celana, kaki, sepatu, tangan, kepala stylized, rambut, dan tas kecil
- kamera 3/4 dipoles lebih dekat agar terasa lebih intimate/cozy
- Pak Wiryo, Bu Ratih, dan Laras mendapat siluet karakter yang berbeda
- Pak Wiryo memakai topi petani
- Bu Ratih memiliki apron dan sanggul
- Laras memiliki rambut panjang dan sling bag

### Lighting dan UI

- pagi lebih hangat
- siang lebih bersih/natural
- sore memakai golden tone
- malam memakai ambient biru lembut
- hujan membuat langit dan cahaya lebih dingin/desaturated
- HUD dibungkus card transparan agar lebih ringan di layar
- quickbar dipadatkan
- joystick dan tombol AKSI otomatis disembunyikan saat bermain di desktop/PC
- kontrol touch tetap tersedia di Android/iOS

Semua gameplay 0.0.6 tetap dipertahankan: farming, waktu/cuaca, NPC/dialog, irigasi, memancing, inventory, penjualan, stamina, rumah/tidur, dan transisi hari.

## Menjalankan di PC

1. Buka GitHub Desktop.
2. Pada repository `eneft/Lembah-sari`, pilih **Fetch origin → Pull origin**.
3. Buka `project.godot` di Godot.
4. Tekan **F5 / Run Project**.
5. Pastikan HUD menampilkan **Lembah Sari 0.0.7**.

### Kontrol desktop

- WASD / Arrow Keys: bergerak
- Shift: lari
- E / Space: interaksi / gunakan alat
- 1: Cangkul
- 2: Benih
- 3: Siram
- 4: Panen
- 5: Pancing
- 6: Jual

## Yang perlu dicek pada visual pass 0.0.7

1. Dunia harus langsung terlihat lebih padat saat game mulai.
2. Rumah pemain di kanan bawah harus memiliki bentuk rumah yang jelas, bukan balok sederhana.
3. Warung Bu Ratih harus terlihat berbeda dari rumah pemain.
4. Sungai harus punya tepian dan jembatan kayu yang lebih terbaca.
5. Sawah Pak Wiryo harus terlihat sebagai petak sawah berair dengan pematang dan rumpun padi.
6. Background utara harus memiliki bentuk bukit/lembah.
7. Player dan tiga NPC utama harus memiliki bentuk karakter stylized yang lebih jelas.
8. Di PC, joystick kiri dan tombol AKSI mobile tidak boleh tampil.
9. HUD tetap menampilkan hari, waktu, inventory, uang, stamina, dan quickbar tanpa terlalu menutupi world.
10. Biarkan waktu berjalan untuk memeriksa perubahan pencahayaan pagi → siang → sore → malam dan cuaca hujan.

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

Untuk sementara fitur baru tetap **freeze** sampai arah visual 0.0.7 dianggap cukup enak dilihat.

Setelah visual disetujui:

- save/load persistence
- tutorial Day 1
- objective sederhana
- polishing animasi karakter dan interaction feedback
- 0.1.0: satu hari playable end-to-end yang dapat ditutup dan dilanjutkan kembali
