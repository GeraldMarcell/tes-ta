# Audit selisih anotasi FoodBD

Tanggal: 2026-10-27. Audit bersifat baca-saja. Tidak ada gambar, TXT, metadata, nutrisi, atau eksperimen ECUSTFD yang diubah. Tidak ada manifest atau training.

## Kesimpulan utama

Tidak ditemukan anotasi alternatif per objek/polygon dalam arsip FoodBD v2. Arsip memuat 3.523 JPG, 3.523 TXT, dua CSV, satu YAML, dan lima PNG dokumentasi; tidak ada berkas JSON/XML/GeoJSON atau ekspor anotasi kedua. JPG/TXT arsip yang diekstrak cocok byte-per-byte dengan dataset proyek.

TXT proyek memiliki 13.485 baris polygon. Hitungan lokal kelas berbeda dari angka pada `Class_Distribution_Chart.png` yang tersedia dalam paket: angka chart berjumlah 12.575. Perbedaan agregatnya +910 lokal, terdiri dari `ruti` +900 dan net +10 pada sembilan kelas lain. Namun chart mencantumkan 198 untuk `ruti`, sedangkan CSV metadata mencantumkan `ruti` pada **1.088 gambar** yang cocok dengan split/nama lokal; TXT lokal memiliki 1.098 polygon `ruti` pada gambar-gambar tersebut. Karena metadata menyatakan presence kelas tetapi chart mengklaim jumlah anotasi, angka 198 tidak dapat dijelaskan sebagai jumlah instance per polygon dari himpunan gambar yang sama tanpa keterangan scope/revisi yang tidak tersedia. Chart menguatkan bahwa angka 12.575 pernah disajikan, tetapi **tidak menetapkan jumlah canonical atau menjelaskan polygon mana yang menyumbang selisih**.

Karena tidak ada hitungan polygon per gambar di metadata dan tidak ada anotasi alternatif, identitas polygon yang berbeda tetap **unresolved**. Jangan menghapus atau mengubah 910 baris.

## Sumber dan metode

Sumber label yang dihitung: `C:\TA\data\raw\FoodBD\{train,valid,test}\labels\*.txt`; setiap baris nonkosong dihitung sebagai polygon, class ID diambil dari token pertama. Nama kelas berasal dari `data.yaml` lokal. Metadata dibaca dari `C:\TA\data\source_archives\FoodBD_v2\root\FoodBD_Meta_data.csv` dan dibandingkan per pasangan tepat `(types/split, filename)`.

Geometri dinormalisasi dengan membaca koordinat numerik dan membandingkan titik polygon secara siklik, termasuk urutan terbalik, dengan toleransi representasi 12 desimal. Pengelompokan dilakukan hanya di dalam gambar yang sama. Ini mendeteksi geometri vertex-identik; bukan pencocokan near-duplicate atau pemeriksaan kualitas semua mask.

Perbandingan aggregate chart menggunakan 67 angka yang tercetak pada PNG sumber. Transkripsi kelas/angka tersedia di CSV diagnostik; chart tidak menyediakan table machine-readable atau breakdown per gambar.

## Hitungan keseluruhan

| Split | Gambar dan TXT lokal | Polygon lokal |
|---|---:|---:|
| train | 2.473 | 9.364 |
| valid | 697 | 2.748 |
| test | 353 | 1.373 |
| **Total** | **3.523** | **13.485** |

Distribusi per kelas dan per gambar tersedia di [source_chart_vs_txt_class_counts.csv](foodbd_annotation_diff_diagnostics/source_chart_vs_txt_class_counts.csv), [per_image_class_polygon_counts.csv](foodbd_annotation_diff_diagnostics/per_image_class_polygon_counts.csv), dan [affected_image_class_counts.csv](foodbd_annotation_diff_diagnostics/affected_image_class_counts.csv). File per-image mencatat metadata class-presence bila baris `(split,filename)` cocok; kolom `metadata_polygon_count` sengaja berisi “not provided”, sebab CSV metadata tidak mempunyai count per kelas atau ID polygon.

## Perbandingan angka chart dan TXT

| Class ID | Kelas | Chart sumber | TXT lokal | Selisih lokal − chart | Makna yang dapat dipastikan |
|---:|---|---:|---:|---:|---|
| 57 | ruti | 198 | 1.098 | +900 | Metadata mencantumkan kelas ini pada 1.088 gambar yang cocok; jumlah polygon lokal 1.098 (1.078 gambar satu polygon, 10 gambar dua polygon). Chart bukan breakdown per gambar. |
| 12 | cauliflower | 105 | 106 | +1 | Perbedaan agregat saja; metadata tidak memberi multiplicity. |
| 20 | daal | 517 | 519 | +2 | Perbedaan agregat saja. |
| 21 | dates | 399 | 400 | +1 | Perbedaan agregat saja. |
| 26 | fish | 587 | 589 | +2 | Perbedaan agregat saja. |
| 40 | mango | 21 | 20 | −1 | TXT lokal satu lebih sedikit. |
| 50 | potato | 452 | 454 | +2 | Perbedaan agregat saja. |
| 55 | rice | 1.535 | 1.536 | +1 | Perbedaan agregat saja. |
| 60 | shim | 63 | 64 | +1 | Perbedaan agregat saja. |
| 62 | tomato | 79 | 80 | +1 | Perbedaan agregat saja. |
| — | 57 kelas lain | 8.619 | 8.619 | 0 | Angka aggregate chart sama dengan TXT setelah transkripsi. |
| **—** | **Total** | **12.575** | **13.485** | **+910** | **Tidak mengidentifikasi baris polygon penyebab.** |

Chart menulis `ruti = 198`, sementara metadata per gambar mencatat `ruti` pada 1.088 dari 3.517 pasangan metadata-file yang cocok. Jika chart dimaksudkan menghitung polygon dari file yang sama, 198 lebih kecil dari jumlah gambar positif kelas tersebut dan tidak konsisten dengan interpretasi “satu atau lebih polygon per gambar”. Bisa jadi chart memakai scope/versi/definisi berbeda, atau angkanya bermasalah; bukti lokal tidak membedakan kemungkinan itu. Nama folder `FoodBD_v2` tidak disertai version manifest atau checksum rilis.

Untuk 3.517 pasangan `(split, filename)` yang tersedia tepat di metadata, class presence pada `instances` cocok dengan set class ID TXT pada **semua 3.517 pasangan**. Ada enam entri metadata yang tidak cocok dengan nama file split lokal dan enam file lokal tanpa entri metadata tepat; detailnya ada di [metadata_split_filename_reconciliation.csv](foodbd_annotation_diff_diagnostics/metadata_split_filename_reconciliation.csv). Ketidakcocokan filename itu belum dipetakan.

## Polygon berulang dan geometri bersama

Audit koordinat seluruh TXT menemukan hanya tiga kelompok geometri vertex-identik dalam gambar yang sama:

| Image ID | Split | Baris TXT | Class ID/nama | Kategori temuan |
|---|---|---|---|---|
| `FoodBD-1633` | test | 2, 4 | 26 `fish` / 26 `fish` | Dua baris mentah dan geometri sama persis. |
| `FoodBD-1652` | test | 2, 4 | 50 `potato` / 50 `potato` | Dua baris mentah dan geometri sama persis. |
| `FoodBD-1533` | train | 4, 6 | 63 `vaji` / 64 `vegetable` | Geometri sama, label berbeda. |

Dengan hitungan berdasarkan `(gambar, class ID, geometri)`, terdapat 2 pengulangan same-class tambahan dan satu pasangan geometri yang dipakai dua class. Jika class diabaikan, ada 3 pengulangan geometri di atas; tidak ditemukan kelompok exact-geometry lain. Ini hanya audit geometri identik; tidak menentukan apakah anotasi duplikat itu salah atau apakah dua label pada `1533` disengaja.

[repeated_geometry_local.csv](foodbd_annotation_diff_diagnostics/repeated_geometry_local.csv) mencatat nomor baris dan raw line untuk semua tiga kelompok. Arsip v2 hanya mengulang TXT yang sama; tidak tersedia object/annotation IDs atau sumber alternatif untuk validasi.

## Visual diagnostik

[Contact sheet kasus polygon](foodbd_annotation_diff_diagnostics/representative_annotation_cases.png) menampilkan gambar asli dan overlay untuk:

- Dua polygon `ruti` pada `train/FoodBD-0965` serta satu polygon `ruti` pada `train/FoodBD-0002` (class ID 57 ditandai merah).
- `FoodBD-1633` dan `FoodBD-1652` dengan line/class ID yang sama pada region bertumpuk.
- `FoodBD-1533` dengan baris 4/class 63 dan baris 6/class 64 pada geometri sama.

Gambar memperlihatkan lokasi dan overlap label, tetapi tidak menetapkan maksud anotasi. [Crop chart ruti](foodbd_annotation_diff_diagnostics/chart_ruti_crop.png) disimpan untuk dokumentasi nilai sumber yang dibandingkan.

## Tabel status rekonsiliasi

| Kasus | Bukti lokal | Bukti metadata sumber | Hasil/status | Bukti tambahan yang dibutuhkan |
|---|---|---|---|---|
| Total polygon 13.485 vs chart/publikasi 12.575 | TXT: 13.485; 9.364/2.748/1.373 per split | Chart 67 kelas berjumlah 12.575, tetapi `ruti=198` bertentangan dengan metadata presence 1.088 gambar | **Unresolved** | Ekspor anotasi canonical per image/instance, versi/checksum file yang menghasilkan chart, dan definisi perhitungan chart. |
| Kelas `ruti` +900 | 1.098 polygon pada 1.088 gambar; sepuluh gambar punya dua polygon | Metadata `instances` menyebut ruti di 1.088 gambar; chart menyebut 198 agregat | **Unresolved**; belum dapat menunjuk gambar penyumbang 900 karena tidak ada target count per gambar | Daftar hitungan anotasi per canonical image ID atau data source yang dipakai untuk membuat chart. |
| Selisih aggregate 9 kelas lain, net +10 | Count per class ID pada TXT tercatat di CSV diagnostik | Chart menyajikan hanya angka per kelas; metadata CSV hanya keberadaan kelas per gambar | **Unresolved** per polygon | Crosswalk instance/label canonical per gambar. |
| Dua geometri same-class | `1633` fish dan `1652` potato masing-masing memiliki pasangan line identik | Metadata hanya presence class pada tingkat gambar | **Unresolved** maksud/validitas | Annotation IDs dan aturan deduplikasi/penggandaan instance dari sumber. |
| Geometri `vaji`/`vegetable` | `1533` baris 4/6 berbagi koordinat | Metadata menyebut kedua class di image, tanpa hubungan ke baris/object | **Unresolved** aturan taxonomy/instance | Anotasi sumber ber-ID dan taxonomy/policy label. |
| Adanya anotasi alternatif dalam ZIP | Ekstrak berisi TXT saja untuk label; tidak ada JSON/XML/format polygon alternatif | Dua ZIP punya 7.049 file sama identik dan lima PNG dokumentasi tambahan pada arsip baru | **Resolved** untuk inventaris paket lokal; tidak ada alternatif yang bisa dibandingkan | Jika ada export anotasi asli terpisah, perlu diberikan/diunduh manual. |

## Rekomendasi

Anotasi cukup untuk eksperimen awal **hanya dengan batasan eksplisit**: gunakan TXT lokal apa adanya, jangan menghapus atau menormalkan baris, pertahankan kelompok ID lintas-split agar tidak bocor, dan sebut hasil sebagai eksperimen pada salinan lokal yang hitungan anotasinya belum direkonsiliasi. Jangan memakai chart 12.575 sebagai dasar memilih atau membuang polygon.

Untuk klaim hasil yang merepresentasikan anotasi FoodBD canonical, atau untuk membangun manifest evaluasi yang dapat dipertanggungjawabkan, metadata sumber tambahan masih wajib: per-image/per-instance counts atau ekspor annotation canonical yang menjelaskan `ruti`, 910 selisih, dan tiga konflik geometri; beserta versi/checksum dan correction map split/filename. Tanpa itu, identitas polygon pembentuk selisih tetap unresolved. Tidak ada manifest dibuat dan tidak ada training dijalankan.

