# Lembah Sari

Prototype cozy farming/life-sim tropis Indonesia, dibangun dengan Godot 4.

## Version 0.0.5

Milestone ini menambahkan loop ekonomi dan aktivitas desa di atas farming, waktu/cuaca, serta NPC:

- world 3D stylized + kamera 3/4
- movement + collision
- farming 20 petak: Cangkul → Benih → Siram → Panen
- waktu Pagi → Siang → Sore → Malam
- cuaca Cerah / Hujan
- NPC: Pak Wiryo, Bu Ratih, Laras + jadwal + dialog
- **irigasi interaktif** di pintu air
- irigasi menyiram seluruh tanaman aktif sekaligus, maksimal sekali per hari
- **mancing** di spot sungai
- ikan prototype: Wader, Lele Sungai, Nila
- **inventory/tas** untuk cabai dan ikan
- hasil panen cabai otomatis masuk tas
- **jual hasil** di depan Warung Bu Ratih
- uang hasil penjualan tampil di HUD
- quickbar: Cangkul, Benih, Siram, Panen, Pancing, Jual

## Menjalankan di PC

1. Buka GitHub Desktop.
2. **Fetch origin → Pull origin** pada repository `eneft/Lembah-sari`.
3. Buka `project.godot` dari Godot Project Manager.
4. Tekan **F6/F5** atau tombol Play.
5. Pastikan kiri atas tertulis **Lembah Sari 0.0.5**.

### Kontrol desktop

- WASD / arrow keys: bergerak
- Shift: lari
- E / Space: interaksi / gunakan alat
- 1: Cangkul
- 2: Benih
- 3: Siram
- 4: Panen
- 5: Pancing
- 6: Jual
- tombol HUD **+ HARI**: lompat ke pagi hari berikutnya

## Tes 0.0.5

### A. Inventory dan panen

1. Cangkul → tanam Benih → Siram.
2. Gunakan **+ HARI** sampai cabai matang.
3. Pilih **Panen** lalu tekan **E/Space/AKSI**.
4. Cabai harus bertambah pada indikator **Tas** di kanan atas.

### B. Irigasi

1. Tanam beberapa cabai tetapi jangan siram manual.
2. Jalan ke **Pintu Irigasi** dekat sawah Pak Wiryo.
3. Dekati label `Pintu Irigasi • E / AKSI`.
4. Tekan **E/Space/AKSI**.
5. Semua tanaman aktif harus berubah menjadi tersiram.
6. Irigasi hanya dapat dipakai sekali pada hari yang sama.

### C. Mancing

1. Tekan **5** atau pilih **Pancing** di quickbar.
2. Jalan ke label `Spot Mancing • pilih Pancing` di tepi sungai.
3. Tekan **E/Space/AKSI**.
4. Ikan hasil tangkapan masuk ke Tas.

### D. Jual hasil

1. Pastikan Tas berisi cabai dan/atau ikan.
2. Tekan **6** atau pilih **Jual**.
3. Jalan ke label `Jual Hasil • pilih Jual` di depan Warung Bu Ratih.
4. Tekan **E/Space/AKSI**.
5. Isi Tas yang dapat dijual menjadi 0 dan uang bertambah.

Harga prototype:
- Cabai: Rp5.000
- Wader: Rp8.000
- Lele Sungai: Rp12.000
- Nila: Rp15.000

## NPC prototype

- Pak Wiryo: sawah → pintu irigasi → warung → pulang
- Bu Ratih: warung → pulang malam
- Laras: sungai → jalan desa → warung → pulang

Dekati NPC lalu tekan **E/Space/AKSI** untuk berbicara. Interaksi aktivitas khusus seperti Pancing/Jual dan Pintu Irigasi diproses sebelum farming.

## Menjalankan di iPhone/iPad dengan Xogot

1. Update/download project dari GitHub di Xogot.
2. Buka `project.godot`.
3. Tekan Play.
4. Pastikan HUD menunjukkan **Lembah Sari 0.0.5**.

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
  activity_manager.gd
  inventory_manager.gd
  mobile_joystick.gd
  mobile_controls.gd
ui/
  MobileControls.tscn
```

## Roadmap terdekat

- 0.0.6: rumah, tidur, transisi hari, stamina dasar
- 0.0.7: kualitas hasil, toko/warung lebih lengkap, ekonomi dasar
- 0.1.0: satu hari playable end-to-end + save persistence
