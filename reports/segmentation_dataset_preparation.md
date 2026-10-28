# Persiapan dataset food segmentation

Tanggal: 2026-10-27. Tahap ini hanya menyiapkan spesifikasi dan rencana. Tidak ada training/evaluasi model, unduhan, pembuatan dataset/mask, atau perubahan file recognition, manifest, checkpoint, maupun raw data.

## Hasil pemeriksaan sumber lokal

Pencarian file proyek (di luar virtual environment dan `.git`) menemukan laporan audit dataset, tetapi tidak menemukan arsip, README, dokumentasi primer, lisensi, atau tautan unduhan resmi UNIMIB2016 yang dapat diverifikasi. Audit lokal sebelumnya memastikan `C:\TA\data\raw` hanya berisi ECUSTFD serta direktori `processed` kosong; UNIMIB2016 belum tersedia. ECUSTFD hanya memiliki XML bounding box dengan `<segmented>0`, sehingga tidak dapat dipakai sebagai mask ground truth.

Laporan audit sebelumnya mencatat sebuah referensi publikasi sekunder/akademik: [paper benchmark food segmentation (CVPR 2023)](https://computer-vision-the-wild.github.io/cvpr-2023/static/cvpr2023/accepted_papers/18/CameraReady/CVinW2023_FoodSeg_CR.pdf). Paper itu melaporkan UNIMIB2016 berisi 1.027 gambar dan 73 kategori, serta mask manual berbasis poligon yang menggabungkan makanan menjadi satu kelas. Ini bukan pemeriksaan terhadap file dataset lokal dan bukan bukti lisensi atau provenance salinan yang akan diperoleh. Sumber resmi dataset, syarat penggunaan, rilis/versi, dan detail format masih belum terverifikasi dari berkas proyek.

## Informasi yang harus diverifikasi sebelum dipakai

Saat dataset diperoleh, simpan bukti sumber dan periksa butir berikut sebelum membuat manifest atau kode model:

| Butir | Yang harus dicatat/diverifikasi |
|---|---|
| Sumber asal | URL halaman resmi pemilik/peneliti atau arsip institusi, nama rilis, tanggal akses, sitasi dan checksum arsip. Hindari salinan pihak ketiga tanpa provenance. |
| Lisensi/penggunaan | Lisensi atau izin penggunaan, atribusi, batas redistribusi, dan apakah penggunaan riset/TA diizinkan. |
| Kuantitas | Jumlah gambar unik, jumlah anotasi/mask, jumlah gambar yang benar-benar berpasangan, dan jumlah gagal dibaca. Bandingkan dengan klaim dokumentasi, jangan menganggap jumlah publikasi sebagai hitungan lokal. |
| Jenis anotasi | Apakah mask tersedia sebagai raster atau koordinat poligon; jika poligon, skema koordinat, urutan titik, lubang/komponen terpisah, dan aturan rasterisasi yang ditetapkan anotator. |
| Label mask | Pastikan nilai background dan food dari file aktual. Verifikasi apakah semua makanan satu foreground class (binary) atau ada ID per kelas. Jangan menyimpulkan dari nama file. |
| Format | Ekstensi, mode gambar, tipe data, palette/indexed vs RGB, nilai unik, kompresi, metadata, dan aturan nilai ignore/void. |
| Resolusi/geometri | Lebar/tinggi gambar dan mask, orientasi EXIF, transformasi/crop, serta kesesuaian koordinat anotasi dengan gambar. |
| Struktur/pasangan | Skema nama atau ID penghubung image-mask, daftar resmi, split yang disediakan, jumlah orphan image/mask, serta kelompok tray/sesi/urutan yang saling terkait. |

Jangan mengubah polygon menjadi label sebelum format dan aturan rasterisasi dari rilis yang sah dipahami. Rasterisasi poligon anotasi resmi merupakan konversi format, bukan alasan untuk membuat atau mengira-ngira batas objek.

## Struktur direktori yang diusulkan

Ini rancangan saja; direktori belum dibuat. Dataset segmentasi harus terpisah dari ECUSTFD:

```text
C:\TA\data\raw\UNIMIB2016\
  README_SOURCE.txt       # sumber, versi, lisensi, sitasi, checksum arsip
  original\               # file hasil ekstraksi asli; read-only setelah verifikasi
  images\                 # gambar sumber, bila memang terpisah di rilis
  annotations\            # mask/polygon asli, tanpa edit
  splits\                  # split resmi bila ada, salinan terverifikasi
```

Jangan memindah/menamai ulang berkas asli bila hal itu memutus pasangan image-mask. Setelah layout aktual diketahui, manifest turunan boleh berada di `C:\TA\data\splits\unimib2016_segmentation_train_val.csv`; manifest berisi ID, path relatif, kelompok, dan split, bukan salinan mask. Simpan metadata validasi di `C:\TA\reports\` dan artefak eksperimen di subdirektori khusus, bukan di ECUSTFD.

## Rencana validasi anotasi sebelum training

1. Inventarisasi file per ekstensi dan hitung gambar, anotasi, pasangan lengkap, orphan image, dan orphan annotation. Cocokkan ID secara eksplisit; jangan memasangkan berdasarkan urutan direktori.
2. Baca header/dimensi setiap gambar dan mask. Konfirmasi dimensi cocok setelah memperhitungkan orientasi/metadata yang memang ditentukan sumber. Laporkan ukuran min/median/max dan pasangan mismatch.
3. Untuk raster masks, laporkan mode, dtype, rentang dan semua nilai unik/perkelas. Verifikasi foreground/background/ignore terhadap dokumentasi dan contoh overlay. Untuk poligon, validasi koordinat di batas gambar, bentuk geometri, label, dan jumlah poligon; rasterisasi hanya memakai aturan sumber yang terdokumentasi.
4. Tandai gambar tanpa mask, mask tanpa gambar, file rusak, mask kosong, dan mask seluruh foreground. Tinjau kasus tersebut; jangan membuang atau memperbaiki tanpa aturan yang dicatat.
5. Buat contact sheet overlay transparan untuk sampel acak dan kasus tepi, mask kosong, mask multi-komponen, serta resolusi berbeda. Overlay hanya untuk inspeksi; simpan sebagai artefak audit, jangan menulisnya kembali ke raw data.
6. Tulis ringkasan validasi, versi script/tool, daftar file bermasalah, dan checksum sebelum menyatakan dataset siap. Tidak ada script validasi yang dibuat pada tahap ini.

Untuk target binary yang dilaporkan pada publikasi, representasi yang diharapkan adalah `0=background`, `1=food`, dan nilai void hanya jika sumber memang menyediakannya. Mapping itu baru boleh diterapkan setelah dikonfirmasi pada dokumentasi dan file aktual.

## Rencana split dan pencegahan kebocoran

- Jika rilis memiliki split resmi, inventarisasi dan audit split tersebut lebih dulu. Jangan menganggapnya bebas kebocoran tanpa memeriksa ID/kelompok terkait.
- Bentuk kelompok dari metadata yang tersedia dan tepercaya: ID tray, sesi/pengambilan, rangkaian gambar, atau subjek. Semua gambar dari satu kelompok wajib masuk ke split yang sama. Bila beberapa aturan kelompok beririsan, gabungkan menjadi connected components sebelum split.
- Hitung SHA-256 atas semua gambar untuk menggabungkan duplikat byte-identik ke kelompok yang sama. Hash perceptual dapat menandai kandidat near-duplicate untuk tinjauan manual; ia sendiri tidak membuktikan identitas.
- Jika tidak ada split resmi yang dapat dipakai dan ada cukup kelompok, rencana awal adalah train/validation 80/20, seed 42, group-aware. Pertahankan setidaknya satu kelompok untuk training pada kategori/strata yang hanya punya sedikit kelompok. Catat distribusi gambar dan kelompok; jangan memindah file.
- Jika metadata tak bisa mengidentifikasi hubungan antar gambar, tulis keterbatasan itu. Jangan mengklaim split bebas kebocoran fisik berdasarkan hash atau kesamaan kelas saja.

## Rancangan baseline U-Net binary

Konfigurasi berikut adalah rancangan awal, bukan hasil teruji dan belum diterapkan:

| Komponen | Rancangan awal |
|---|---|
| Task/target | Binary semantic segmentation: food foreground vs background, satu logit per piksel. Berlaku hanya jika mask aktual terverifikasi sebagai binary. |
| Model | U-Net encoder-decoder sederhana; inisialisasi encoder ImageNet hanya jika bobot kompatibel telah tersedia lokal dan versi dicatat. Baseline tetap dapat memakai inisialisasi acak jika tidak ada bobot yang tersedia. |
| Ukuran input | Ubah ukuran gambar dan mask ke 512 x 512 untuk baseline awal; mask memakai nearest-neighbor, gambar memakai interpolasi bilinear. Transformasi spasial harus identik. Pertahankan rasio/aspek atau dokumentasikan distorsi sebelum eksperimen. |
| Batch dan seed | Seed 42; batch size awal 4 pada RTX 3060, naikkan hanya bila memori tervalidasi. Determinisme dan versi library dicatat. |
| Optimizer | AdamW, learning rate awal 1e-3; maksimum 20 epoch, early stopping patience 5 berdasarkan validation Dice. Tetapkan nilai ini sebelum run dan jangan tuning pada test. |
| Loss | `0.5 * BCEWithLogitsLoss + 0.5 * soft Dice loss` untuk menangani foreground/background imbalance. Jika baseline pembanding diperlukan, BCE saja dapat dijalankan sebagai eksperimen terpisah; jangan campur konfigurasi dalam run yang sama. Abaikan label void hanya jika memang dinyatakan dataset. |
| Augmentasi | Awali tanpa augmentasi untuk baseline paling sederhana; bila ditambahkan kemudian, gunakan transformasi ringan yang sama pada image-mask pair dan nearest-neighbor untuk mask. |
| Postprocessing/metric | Sigmoid pada logit, threshold tetap 0.5; laporkan binary IoU dan Dice per gambar serta mean antar gambar, ditambah agregat global bila diperlukan. Kebijakan untuk GT/prediksi kosong harus ditetapkan dan dilaporkan eksplisit. |

Artefak yang direncanakan: config JSON/YAML, seed dan versi library, train/validation manifest, log loss per epoch, validation IoU/Dice per epoch, checkpoint best berdasarkan validation Dice dan checkpoint terakhir, prediksi mask validation, tabel metrik per gambar, ringkasan agregat, contoh overlay, confusion counts pixel-level (TP/FP/FN/TN), serta laporan run. Simpan semuanya pada direktori eksperimen khusus, misalnya `outputs/segmentation/unimib2016_unet_binary/`; belum ada direktori atau file artefak yang dibuat.

## Yang perlu dilakukan secara manual

UNIMIB2016 belum dapat diverifikasi dari berkas lokal. Unduh secara manual dari **sumber resmi/pemilik dataset atau repositori institusi yang dapat diverifikasi**, bukan melalui terminal. Sertakan README/syarat lisensi, sitasi, informasi rilis, dan checksum bila disediakan, lalu letakkan salinan terpisah di `C:\TA\data\raw\UNIMIB2016\original\`. Jangan lanjut ke script training.

Dataset baru dinyatakan siap setelah sumber dan penggunaan diizinkan; jumlah file cocok atau selisihnya dijelaskan; setiap image-mask memiliki pasangan yang dapat dipetakan; dimensi/geometri konsisten; encoding dan nilai mask, empty masks, serta kelas telah dikonfirmasi; contoh overlay lolos inspeksi; masalah/orphan didokumentasikan; dan split berbasis kelompok/duplikasi dapat dibentuk tanpa overlap terukur. Setelah itu barulah pipeline validasi dan script baseline dapat dibuat. Sampai kriteria tersebut dipenuhi, training tetap tertahan.
