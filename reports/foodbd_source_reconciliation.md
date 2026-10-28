# FoodBD source reconciliation

Tanggal pemeriksaan: 2026-10-27. Pemeriksaan baca-saja. Dataset asli, metadata sumber, arsip ZIP, eksperimen ECUSTFD, manifest, checkpoint, dan laporan terdahulu tidak diubah. Tidak ada manifest baru atau training.

## Ringkasan

Ditemukan paket FoodBD lokal yang sebelumnya belum tercatat pada audit proyek: `C:\Users\user\Downloads\FoodBD A Polygon-Annotated Meal Image Dataset of B.zip` beserta ekstraknya di folder `...\root`. Paket ini berisi `FoodBD_Meta_data.csv`, `FoodBD/data.yaml`, `MealNutrition1837_All.csv`, serta 3.523 JPG dan 3.523 TXT. ZIP memiliki 7.049 entri; tidak ada README, changelog, checksum rilis, versi dataset, atau format anotasi sumber lain yang dapat menetapkan provenance revisi.

Perbandingan baca-saja menunjukkan semua 3.523 JPG dan 3.523 TXT pada arsip ZIP identik byte-per-byte dengan file di `C:\TA\data\raw\FoodBD`. `data.yaml`, metadata CSV, dan CSV nutrisi dalam ZIP juga cocok byte-per-byte dengan salinan ekstrak yang diperiksa. Jadi ZIP tidak menyediakan salinan anotasi alternatif untuk menjelaskan hitungan polygon: baik ZIP maupun folder proyek memiliki **13.485 baris polygon**, sedangkan laporan publik yang sebelumnya dirujuk menyebut 12.575. Paket lokal memastikan asal hitungan lokal, tetapi tidak menjelaskan selisih 910.

Metadata CSV berisi kolom `filename`, `instances`, `Environmental conditions`, `preprocessing `, `types`; 3.523 baris dan hitungan split-nya sama dengan file proyek. `instances` adalah daftar nama kelas per gambar, bukan ID polygon/objek. Metadata tidak memiliki ID anotasi, ID sesi/pengambilan, atau kolom penghubung ke baris nutrisi. Ada 3 filename yang masing-masing tercatat dua kali, sekali train dan sekali valid. Empat ID nutrisi yatim tidak terdapat dalam metadata tersebut.

## Bukti metadata dan split

Metadata lokal menyatakan semua gambar `indoor`, preprocessing `resized to 1024x1024`, serta 2.473 train, 697 valid, dan 353 test. Data ini memberi dukungan lokal atas split dan kategori per gambar. Namun metadata tidak menjelaskan mengapa nama file tertentu tidak cocok dengan folder, apakah dua berkas bernama sama adalah satu objek/pengambilan, atau hubungan nutrisi ke polygon tertentu.

Pencocokan basename persis metadata terhadap folder menemukan anomali berikut; tidak ada pemetaan otomatis yang dibuat:

| Split | Terdaftar metadata tetapi tidak ada dengan basename persis di folder | Ada di folder tetapi tidak terdaftar dengan basename persis |
|---|---|---|
| train | `FoodBD-3301.rf.7f3254b2c7fbe0861f40fa4be65c3cbd.jpg.jpg`; `FoodBD-8003jpg`; `FoodBD-8114jpg`; `FoodBD-8543jpg` | `FoodBD-8003.jpg`; `FoodBD-8114.jpg`; `FoodBD-8301.jpg`; `FoodBD-8543.jpg` |
| test | `FoodBD-8083.jpg`; `FoodBD-8652.jpg` | `FoodBD-1652.jpg`; `FoodBD-3083.jpg` |
| valid | Tidak ada | Tidak ada |

Kemiripan angka atau potongan nama tidak membuktikan pasangan. `FoodBD-3301...` juga tidak dipasangkan ke file bernomor 3301 tanpa provenance. Pada test, metadata tidak mencantumkan `FoodBD-3083.jpg` yang ada di folder. Perlu file manifest/canonical ID mapping dari rilis untuk menetapkan apakah ini salah nama, file tambahan, atau perbedaan revisi.

## Contact sheet dan audit visual

- [Kasus geometri polygon](foodbd_source_diagnostics/polygon_geometry_cases.png): setiap baris menampilkan gambar asli dan overlay polygon berwarna menurut class ID. Label `Lx/Cy` mengidentifikasi nomor baris lokal TXT dan class ID; sumber **tidak** menyediakan annotation ID stabil.
- [Pasangan ID lintas split](foodbd_source_diagnostics/split_id_visual_comparison.png): gambar source A/B berdampingan, panel selisih pixel yang dinormalisasi kontras untuk inspeksi, dan blend 50/50. Normalisasi selisih hanya untuk visualisasi dan bukan ukuran jarak yang dibandingkan secara kuantitatif.

Pada empat pasangan split, susunan hidangan dan framing tampak sangat serupa pada contact sheet; panel selisih menunjukkan perbedaan pixel menyebar yang mungkin mencakup kompresi/encoding serta perbedaan kecil lainnya. Ini mendukung perlakuan konservatif sebagai kelompok kandidat terkait agar tidak terpisah lintas split, tetapi tidak membuktikan apakah file berasal dari exposure yang sama, foto yang diedit, atau dua foto terpisah. Hash JPG berbeda dan TXT-nya sama persis pada setiap pasangan.

### Polygon dengan geometri identik

| ID | Bukti berkas dan visual | Batas kesimpulan |
|---|---|---|
| `FoodBD-1633` | `test/labels/FoodBD-1633.txt`, baris 2 dan 4: class 26 (`fish`), geometri dan baris mentah identik. Gambar/overlay ada di contact sheet. | Metadata hanya menyebut kelas `fish`; tidak memiliki ID objek atau aturan duplikasi. Belum diketahui apakah polygon berulang disengaja atau duplikat anotasi. |
| `FoodBD-1652` | `test/labels/FoodBD-1652.txt`, baris 2 dan 4: class 50 (`potato`), geometri dan baris mentah identik. | Sama: terlihat overlay bertumpuk, tetapi gambar saja tidak menetapkan aturan anotasi atau apakah baris harus digabung/dipertahankan. |
| `FoodBD-1533` | `train/labels/FoodBD-1533.txt`, baris 4 class 63 (`vaji`) dan baris 6 class 64 (`vegetable`): koordinat/geometri identik, label berbeda. Overlay menunjukkan region yang sama diberi dua label. | Metadata per gambar mencantumkan kelas `vaji` dan `vegetable` namun tidak menghubungkan kelas ke baris/objek, tidak menerangkan sinonim/hierarki, dan tidak menetapkan apakah overlap lintas kelas sah. Jangan hapus atau gabungkan. |

## Audit baris nutrisi

CSV lokal dan salinan dalam ZIP sama byte-per-byte. Header dipertahankan persis: `FoodImage`, `CHO`, `Protein`, `Fat`, `Fiber`, `Calorie`, `GL`. Ada satu baris masing-masing untuk ID di bawah. Pencarian basename persis pada metadata gambar tidak menemukan keempat ID; kandidat gambar tidak ada dalam tiga folder image lokal.

| ID dari CSV nutrisi | Baris nutrisi | Metadata gambar | Hasil aman |
|---|---:|---|---|
| `FoodBD-2282.jpg` | 1 | Tidak ada | Unmatched; minta mapping resmi, jangan tebak berdasarkan nomor. |
| `FoodBD-2383.jpg` | 1 | Tidak ada | Unmatched; minta mapping resmi. |
| `FoodBD-3381.jpg` | 1 | Tidak ada | Unmatched; minta mapping resmi. |
| `FoodBD-3508.jpg` | 1 | Tidak ada | Unmatched; minta mapping resmi. |
| `FoodBD-3083.jpg` | 1 | Satu row metadata, split `valid`, instances `beef,ruti` | Folder memiliki valid **dan** test dengan basename yang sama; metadata hanya mendukung valid. Label TXT kedua file sama, tetapi JPG berbeda. Pasangan nutrisi hanya memiliki basename dan tidak dapat secara pasti dipautkan ke file tertentu atau ke objek beef/ruti. Jangan gunakan kandidat test atau menetapkan relasi level objek. |

Kolom nutrisi adalah record keyed by image, bukan object/polygon ID; metadata lokal tidak menawarkan join key tambahan. Nama kolom dan unit dipertahankan sebagaimana tersedia; tidak ada unit gram yang ditambahkan atau disimpulkan.

## Tabel rekonsiliasi akhir

| Kasus | Bukti lokal | Bukti metadata sumber (tersedia lokal) | Status | Tindakan aman berikutnya |
|---|---|---|---|---|
| Asal hitungan 13.485 polygon | 3.523 TXT; 13.485 baris; semua TXT di ZIP dan proyek identik | Metadata rilis lokal tidak memuat hitungan polygon; ZIP tidak memuat README/changelog atau anotasi alternatif | **requires source metadata** untuk menjelaskan selisih dengan angka publikasi 12.575 | Dapatkan manifest/checksum rilis dan catatan/protokol anotasi resmi atau dump anotasi canonical; jangan hapus 910 baris. |
| ID `0888`, `1103`, `1217` di train+valid | Gambar byte berbeda; TXT persis sama; tampilan visual sangat mirip | Masing-masing memiliki row metadata train dan valid dengan nama instance sama | **resolved** bahwa split overlap tercatat dalam metadata lokal; **requires source metadata** untuk identitas/provenance pasangan | Kelompokkan basename sebagai satu grup konservatif setelah sumber menjelaskan canonical IDs; jangan pisahkan antar-split. |
| ID `3083` valid+test | Dua JPG berbeda, TXT sama; satu baris nutrisi `FoodBD-3083.jpg` | Metadata memiliki hanya row valid (`beef,ruti`); tidak memiliki row test untuk basename itu | **requires source metadata** untuk file test dan join nutrisi | Minta canonical image manifest/ID map; sementara pertahankan dua file dan exclude key nutrisi ambigu dari split model. |
| Nama metadata vs file lokal | Daftar exact-name mismatch train/test di atas | CSV metadata memang berisi nama-nama yang tidak ditemukan persis dan tidak mencantumkan beberapa nama file aktual | **requires source metadata** | Minta correction table/filename provenance dari penerbit; jangan mengoreksi nama otomatis. |
| Polygon duplikat `1633`, `1652` | Baris polygon same-class identik; overlay region bertumpuk | Tidak ada annotation ID atau duplicate policy | **unresolved** | Minta anotasi sumber dan kebijakan instance deduplication; simpan seluruh baris asli. |
| Geometri lintas-kelas `1533` | Baris 4/6 geometri sama, class berbeda; overlay region sama | `instances` mencantumkan kedua nama kelas pada tingkat gambar saja | **requires source metadata** untuk aturan label/objek | Minta taxonomy/hierarchy dan anotasi instance asli; jangan ubah label. |
| Nutrisi IDs `2282`, `2383`, `3381`, `3508` | Masing-masing satu row CSV, tidak ada JPG dengan basename cocok | Tidak ada entry pada metadata gambar | **requires source metadata** | Minta image-key crosswalk/file yang hilang atau koreksi ID dari sumber. |
| Join nutrisi `3083` | Dua kandidat image (valid/test), label polygon sama, hash beda | Metadata mendukung entry valid saja | **requires source metadata** untuk penguncian file | Jangan memilih otomatis berdasarkan kelas/nama; gunakan hanya setelah crosswalk resmi. |
| Metadata lokal vs versi resmi | Metadata lokal mencatat filename, class presence, kondisi, preprocessing, split | Paket/CSV tidak menyatakan versi rilis, revision, image IDs canonical, checksum atau annotation IDs | **requires source metadata** | Dapatkan versi/manifest/checksum sumber dan penjelasan revisi sebelum membuat manifest train/validation/test. |

## Masalah yang terpecahkan dan yang masih terbuka

**Terpecahkan secara lokal:** sumber langsung hitungan 13.485 adalah baris nonkosong dalam 3.523 TXT; ZIP dan folder proyek merupakan salinan byte-identik untuk seluruh JPG/TXT; metadata lokal berisi 3.523 row dengan split count yang sesuai; `0888`, `1103`, `1217` memang tercatat di train dan valid pada metadata; metadata hanya mencatat `3083` sebagai valid; empat key nutrisi yatim memang tidak tercantum di metadata; kasus geometri dan nomor barisnya terverifikasi.

**Belum terselesaikan / memerlukan metadata sumber:** mengapa publikasi menyebut 12.575; apakah tiga polygon same-geometry bermasalah atau sah; provenance dan identitas foto lintas split; file test `3083`; filename mismatch; empat key nutrisi yatim; versi dan checksum paket. Bukti yang ada tidak cukup untuk menyatakan file salah, anotasi salah, atau gambar duplikat semantik.

### Metadata yang perlu diminta/diunduh manual dari sumber resmi

- Manifest/checksum dan nomor versi/revisi untuk paket persis yang memuat `FoodBD_Meta_data.csv` dan split YOLO tersebut.
- Daftar canonical `image ID ↔ filename ↔ split` berikut correction map untuk filename mismatch dan ID `3083`.
- Sumber anotasi instance asli (dengan stable annotation/object IDs bila ada) atau dokumentasi aturan anotasi polygon, duplikasi, dan hubungan class `vaji`/`vegetable`.
- Catatan revisi atau export yang menerangkan jumlah 12.575 vs berkas polygon release; bila jumlah publikasi memakai definisi hitung berbeda, dokumentasi definisinya.
- Crosswalk resmi `FoodImage` nutrisi ke canonical image ID/file, termasuk empat ID unmatched dan penetapan gambar untuk `FoodBD-3083.jpg`.

Sampai informasi tersebut cocok dengan file lokal, jangan membuat manifest training final atau memindahkan file antar-split. Tetap perlakukan collision ID sebagai satu grup konservatif untuk mencegah kebocoran, dan jangan gunakan label nutrisi `3083` pada pasangan yang belum dipastikan.
